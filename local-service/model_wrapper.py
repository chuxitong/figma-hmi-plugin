"""
Wrapper around the real UI2Code^N visual language model.

The model ID is ``zai-org/UI2Code_N``. It is a 9B-parameter VLM built on
GLM-4.1V-9B-Base.

Loading mode is controlled by the ``UI2CODEN_QUANT`` environment variable:

* ``none`` (default) — load full-precision bf16 weights, recommended for
  real measurements on a workstation or cloud GPU (e.g. RTX 4090 24 GB,
  A10/A100). On a single 24 GB card use ``UI2CODEN_DEVICE_MAP=single`` (default);
  for a multi-GPU instance set ``UI2CODEN_DEVICE_MAP=auto``.
* ``8bit`` — load with 8-bit weights via ``bitsandbytes`` (mid-range GPUs).
* ``4bit`` — 4-bit NF4; on Windows, prefer leaving the full model on **one
  GPU** (see ``UI2CODEN_DEVICE_MAP``) to avoid the bitsandbytes + accelerate
  meta-tensor bug when layers spill to CPU.

* ``UI2CODEN_MAX_NEW_TOKENS`` (optional) — cap ``generate`` / ``refine`` /
  ``edit`` output length; lower values speed up local demos on small GPUs.

* **Local snapshot (offline / no access to huggingface.co):** if ``UI2CODEN_MODEL_ID``
  points to a directory, weights are loaded with ``local_files_only=True`` and the
  Hub is never contacted. If it is left at the default repo id
  (``zai-org/UI2Code_N``) and a known data-disk snapshot exists (e.g.
  ``/root/autodl-tmp/UI2Code_N`` on AutoDL, see ``help/docs/DEPLOYMENT_AUTODL.zh.md``),
  the wrapper **automatically** uses that directory unless
  ``UI2CODEN_PREFER_LOCAL_SNAPSHOT=0``. Override the search path with
  ``UI2CODEN_LOCAL_SNAPSHOT_PATH`` (single directory). Set
  ``UI2CODEN_LOCAL_FILES_ONLY=1`` to force local-only when using a custom Hub cache
  layout. With ``USE_REAL_MODEL=1``, :func:`apply_real_model_env_defaults` (called
  from the HTTP app at startup) sets ``HF_HUB_OFFLINE`` and ``TRANSFORMERS_OFFLINE``
  when a local snapshot is used, so no Hugging Face HTTP requests occur. Set
  ``UI2CODEN_SKIP_HF_OFFLINE=1`` to skip those flags if you need Hub side traffic.

Quantisation is therefore opt-in. By default the wrapper does **not**
quantise the model, because published timings and qualitative comparisons
should be taken from the unquantised baseline unless otherwise stated.

The class follows the same ``generate / refine / edit`` interface that the
rule-based stand-in exposes, so it can be dropped into the local HTTP
service and evaluation scripts without changing anything else.
"""

from __future__ import annotations

import io
import json
import logging
import os
from typing import Any, Optional

import torch
from PIL import Image


logger = logging.getLogger(__name__)

_DEFAULT_HUB_ID = "zai-org/UI2Code_N"
_DEFAULT_LOCAL_SNAPSHOT = "/root/autodl-tmp/UI2Code_N"
DEFAULT_QUANT = os.environ.get("UI2CODEN_QUANT", "none").lower()
# Cap generation length (set UI2CODEN_MAX_NEW_TOKENS e.g. 2048 on laptops so /edit does not block the server for hours).
_DEFAULT_MNT = os.environ.get("UI2CODEN_MAX_NEW_TOKENS", "").strip()
# Rich VLM+HMI outputs + React CDN boilerplate can exceed 4k subtokens on dense screens.
# Lower with UI2CODEN_MAX_NEW_TOKENS when debugging on constrained GPUs.
DEFAULT_MAX_NEW_TOKENS = int(_DEFAULT_MNT) if _DEFAULT_MNT.isdigit() else 8192


_GEN_PROMPT = (
    "You are generating code for an industrial HMI screen. "
    "Look at the screenshot and produce a single self-contained HTML page "
    "with inline CSS that reproduces the layout, typography, color palette "
    "and interactive elements. Use semantic HTML. No external assets."
)

_REFINE_PROMPT = (
    "This is an industrial HMI reference. The first image is the target "
    "reference. The second image is the current rendered output of the "
    "attached HTML. Improve the HTML so that its rendered appearance is "
    "closer to the reference: tighten spacing, correct typography "
    "hierarchy, align blocks, preserve the color palette, fix obviously "
    "missing elements visible in the reference but absent from the current "
    "render. Return the full updated HTML."
)

_EDIT_PROMPT_TEMPLATE = (
    "The attached HTML represents an industrial HMI screen. Apply this "
    "instruction and return the full updated HTML, nothing else. "
    "Instruction: {instruction}"
)


def _prompt_profile_extended() -> bool:
    """When UI2CODEN_PROMPT_PROFILE=extended, append stricter industrial HMI instructions."""
    return (
        os.environ.get("UI2CODEN_PROMPT_PROFILE", "baseline").strip().lower()
        == "extended"
    )


_EXTENDED_GENERATE_SUFFIX = (
    "\n\nAdditional engineering constraints for industrial HMI operator views:\n"
    "- Keep alarms, status indicators, and critical metrics visually distinct from decorative chrome.\n"
    "- Prefer predictable layout (flex or grid) with consistent spacing in control panels.\n"
    "- Do not omit major equipment or trend regions that appear in the screenshot.\n"
    "- If multiple buttons are visible, reflect primary vs secondary / neutral roles in styling.\n"
)

_EXTENDED_REFINE_SUFFIX = (
    "\n\nRefinement focus: improve pixel alignment and typography without rebuilding unrelated cards "
    "unless the reference clearly requires it."
)

_EXTENDED_EDIT_SUFFIX = (
    "\n\nEdit focus: apply the user instruction locally; avoid rewriting unrelated sections of the page."
)


def _pil_from_bytes(image_bytes: bytes) -> Image.Image:
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")


def _resolve_pretrained_location(
    model_id: str,
) -> tuple[str, bool]:
    """Return ``(id_or_path, local_files_only)`` for :meth:`from_pretrained`.

    When the default Hub repo is used but this machine has no route to
    ``huggingface.co`` (e.g. AutoDL with weights only on disk), unqualified
    ``from_pretrained("zai-org/UI2Code_N")`` still issues HTTP HEAD/GET to the Hub
    for many small config files, each with multi-second retries, which looks like
    a hung first request. Preferring a local directory avoids that.
    """
    prefer_local = os.environ.get("UI2CODEN_PREFER_LOCAL_SNAPSHOT", "1").lower() not in (
        "0",
        "false",
        "no",
    )
    raw = (model_id or "").strip() or _DEFAULT_HUB_ID
    expanded = os.path.expanduser(raw)
    if os.path.isdir(expanded):
        if not os.path.isfile(os.path.join(expanded, "config.json")):
            logger.warning("UI2CODEN: %s is a directory but has no config.json", expanded)
        return expanded, True
    is_default_repo = raw.replace(os.sep, "/") == _DEFAULT_HUB_ID
    if prefer_local and is_default_repo:
        for candidate in (
            os.path.expanduser(os.environ.get("UI2CODEN_LOCAL_SNAPSHOT_PATH", "").strip()),
            _DEFAULT_LOCAL_SNAPSHOT,
        ):
            if not candidate or not os.path.isdir(candidate):
                continue
            if not os.path.isfile(os.path.join(candidate, "config.json")):
                continue
            logger.info(
                "UI2CODEN: using local weights at %s (no Hub access). "
                "Set UI2CODEN_PREFER_LOCAL_SNAPSHOT=0 to use the online repo id instead.",
                candidate,
            )
            return candidate, True
    local_only = os.environ.get("UI2CODEN_LOCAL_FILES_ONLY", "").lower() in (
        "1",
        "true",
        "yes",
    )
    return raw, local_only


_env_defaults_applied = False


def apply_real_model_env_defaults() -> None:
    """Resolve the on-disk UI2Code^N snapshot and enable Hub offline mode.

    Call once at process start when ``USE_REAL_MODEL=1`` (see ``app`` startup).
    Hugging Face clients may still attempt HTTPS to ``huggingface.co`` (with long
    retries on connection failure) unless ``HF_HUB_OFFLINE`` / ``TRANSFORMERS_OFFLINE``
    are set *before* ``transformers`` is first imported for ``from_pretrained``.
    This function is idempotent.
    """
    global _env_defaults_applied
    if _env_defaults_applied:
        return
    if os.environ.get("USE_REAL_MODEL") != "1":
        return
    _env_defaults_applied = True
    raw = (os.environ.get("UI2CODEN_MODEL_ID") or _DEFAULT_HUB_ID).strip()
    resolved, local_files_only = _resolve_pretrained_location(raw)
    if not (local_files_only and os.path.isdir(resolved)):
        return
    os.environ["UI2CODEN_MODEL_ID"] = resolved
    if os.environ.get("UI2CODEN_SKIP_HF_OFFLINE", "").lower() in (
        "1",
        "true",
        "yes",
    ):
        logger.info(
            "UI2CODEN: local snapshot %s (HF offline flags skipped by UI2CODEN_SKIP_HF_OFFLINE)",
            resolved,
        )
        return
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    logger.info(
        "UI2CODEN: HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 for local snapshot %s",
        resolved,
    )


def _format_context_block(
    css_hints: Optional[dict] = None,
    variables: Optional[dict] = None,
) -> str:
    """Render optional Figma context as a compact, model-readable block.

    The block is appended to the prompt only when at least one of the two
    inputs is provided. Empty dicts are treated as "not provided".
    """
    parts: list[str] = []
    if variables:
        parts.append(
            "<design_variables>\n"
            + json.dumps(variables, ensure_ascii=False, indent=2)
            + "\n</design_variables>"
        )
    if css_hints:
        parts.append(
            "<css_hints>\n"
            + json.dumps(css_hints, ensure_ascii=False, indent=2)
            + "\n</css_hints>"
        )
    return ("\n\n" + "\n\n".join(parts)) if parts else ""


class UI2CodeModel:
    """Thin wrapper that exposes ``generate``, ``refine`` and ``edit``."""

    def __init__(
        self,
        model_id: str | None = None,
        max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS,
        quant: str = DEFAULT_QUANT,
    ):
        raw_id = (model_id and str(model_id).strip()) or os.environ.get(
            "UI2CODEN_MODEL_ID", ""
        ).strip() or _DEFAULT_HUB_ID
        resolved, local_files_only = _resolve_pretrained_location(raw_id)
        self.model_id = resolved
        self.max_new_tokens = max_new_tokens
        self.quant = (quant or "none").lower()
        self.name = f"ui2coden-9b-{self.quant}"
        logger.info(
            "loading %s in quant=%s (local_files_only=%s; this may take several minutes on first run)",
            resolved,
            self.quant,
            local_files_only,
        )

        from transformers import AutoModelForImageTextToText, AutoProcessor

        kwargs: dict[str, Any] = {
            "torch_dtype": torch.bfloat16,
            "trust_remote_code": True,
            "local_files_only": local_files_only,
        }

        if self.quant == "none":
            kwargs["low_cpu_mem_usage"] = True
            if not torch.cuda.is_available():
                kwargs["device_map"] = "auto"
            else:
                # Same switch as the quantised path: "single" keeps the full bf16
                # model on one GPU; "auto" uses accelerate to spread across devices
                # (e.g. two 16 GB cards on a cloud node).
                _dm = (os.environ.get("UI2CODEN_DEVICE_MAP") or "single").strip().lower()
                if _dm in {"auto"}:
                    kwargs["device_map"] = "auto"
                elif _dm in {"sequential"}:
                    kwargs["device_map"] = "sequential"
                else:
                    # single, one, gpu0, cuda0, cuda, single-gpu, or unset
                    kwargs["device_map"] = {"": 0}
        elif self.quant in {"4bit", "8bit"}:
            from transformers import BitsAndBytesConfig

            if self.quant == "4bit":
                kwargs["quantization_config"] = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.bfloat16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4",
                )
            else:
                kwargs["quantization_config"] = BitsAndBytesConfig(load_in_8bit=True)
            kwargs["low_cpu_mem_usage"] = True
            # ``device_map="auto"`` often spills 4/8bit layers to CPU; bitsandbytes then
            # hits accelerate hook + meta-tensor bugs on Windows (see project DEPLOYMENT).
            # Default: keep the whole quantized model on **one GPU** (``{"": 0}``) so all
            # bnb modules stay on CUDA. Needs enough VRAM for 4bit UI2Code^N (~6–8+ GB).
            # Optional: UI2CODEN_DEVICE_MAP=auto  -> old behaviour (may fail on 6G laptops).
            _dm = (os.environ.get("UI2CODEN_DEVICE_MAP") or "single").strip().lower()
            if _dm in {"single", "one", "gpu0", "cuda0"} and torch.cuda.is_available():
                kwargs["device_map"] = {"": 0}
            elif torch.cuda.is_available():
                _offload = os.environ.get("UI2CODEN_BNB_CPU_OFFLOAD", "0").lower() in (
                    "1",
                    "true",
                    "yes",
                )
                if self.quant == "4bit":
                    kwargs["quantization_config"] = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=torch.bfloat16,
                        bnb_4bit_use_double_quant=True,
                        bnb_4bit_quant_type="nf4",
                        llm_int8_enable_fp32_cpu_offload=_offload,
                    )
                else:
                    kwargs["quantization_config"] = BitsAndBytesConfig(
                        load_in_8bit=True,
                        llm_int8_enable_fp32_cpu_offload=_offload,
                    )
                kwargs["device_map"] = "auto"
                gi = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                gpu_cap = max(1.0, round(gi - 1.0, 2))
                kwargs["max_memory"] = {0: f"{gpu_cap}GiB", "cpu": "200GiB"}
            else:
                kwargs["device_map"] = "auto"
        else:
            raise ValueError(
                f"Unsupported UI2CODEN_QUANT={self.quant!r}; expected one of "
                "'none', '8bit', '4bit'."
            )

        self.processor = AutoProcessor.from_pretrained(
            resolved, trust_remote_code=True, local_files_only=local_files_only
        )
        self.model = AutoModelForImageTextToText.from_pretrained(resolved, **kwargs)
        self.model.eval()
        logger.info("model loaded: %s (%s)", resolved, self.name)

    # ------------------------------------------------------------------ prompt builders (reproducibility / logging)

    def build_generate_prompt(
        self,
        frame_name: str,
        css_hints: Optional[dict] = None,
        variables: Optional[dict] = None,
        task_description: Optional[str] = None,
    ) -> str:
        prompt = _GEN_PROMPT + f"\nScreen name hint: {frame_name}"
        if task_description and str(task_description).strip():
            prompt += (
                "\nAdditional task / user instruction: "
                + str(task_description).strip()
            )
        prompt += _format_context_block(css_hints=css_hints, variables=variables)
        if _prompt_profile_extended():
            prompt += _EXTENDED_GENERATE_SUFFIX
        return prompt

    def build_refine_prompt(
        self,
        current_code: str,
        *,
        has_rendered_pair: bool,
        css_hints: Optional[dict] = None,
        variables: Optional[dict] = None,
        task_description: Optional[str] = None,
    ) -> str:
        if has_rendered_pair:
            preface = (
                "\n\nFirst image: target reference. "
                "Second image: current render of the attached HTML."
            )
        else:
            preface = (
                "\n\nOnly the reference image was supplied. "
                "Improve the HTML to match it as closely as possible."
            )
        prompt = _REFINE_PROMPT + preface
        if task_description and str(task_description).strip():
            prompt += "\nAdditional focus (user): " + str(task_description).strip()
        prompt += _format_context_block(css_hints=css_hints, variables=variables)
        if _prompt_profile_extended():
            prompt += _EXTENDED_REFINE_SUFFIX
        prompt += "\n\n<previous_html>\n" + current_code + "\n</previous_html>"
        return prompt

    def build_edit_prompt(
        self,
        instruction: str,
        current_code: str,
        css_hints: Optional[dict] = None,
        variables: Optional[dict] = None,
    ) -> str:
        prompt = _EDIT_PROMPT_TEMPLATE.format(instruction=instruction)
        prompt += _format_context_block(css_hints=css_hints, variables=variables)
        if _prompt_profile_extended():
            prompt += _EXTENDED_EDIT_SUFFIX
        prompt += "\n\n<current_html>\n" + current_code + "\n</current_html>"
        return prompt

    # ------------------------------------------------------------------ core

    def _chat(self, images: list[Image.Image], text: str) -> str:
        content: list[dict[str, Any]] = []
        for image in images:
            content.append({"type": "image", "image": image})
        content.append({"type": "text", "text": text})

        messages = [{"role": "user", "content": content}]

        inputs = self.processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt",
        )
        # Works for single- and multi-device (accelerate) loads
        target = next(self.model.parameters()).device
        inputs = inputs.to(target)

        with torch.inference_mode():
            generated = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                temperature=0.0,
            )

        prompt_len = inputs["input_ids"].shape[1]
        raw = self.processor.decode(generated[0][prompt_len:], skip_special_tokens=True)
        return self._clean_html(raw)

    # ------------------------------------------------------------------ api

    def generate(
        self,
        image_bytes: bytes,
        frame_name: str = "Untitled",
        css_hints: Optional[dict] = None,
        variables: Optional[dict] = None,
        task_description: Optional[str] = None,
        **_: Any,
    ) -> str:
        image = _pil_from_bytes(image_bytes)
        prompt = self.build_generate_prompt(
            frame_name,
            css_hints=css_hints,
            variables=variables,
            task_description=task_description,
        )
        return self._chat([image], prompt)

    def refine(
        self,
        reference_bytes: bytes,
        current_code: str,
        rendered_bytes: Optional[bytes] = None,
        css_hints: Optional[dict] = None,
        variables: Optional[dict] = None,
        task_description: Optional[str] = None,
        **_: Any,
    ) -> str:
        images: list[Image.Image] = [_pil_from_bytes(reference_bytes)]
        has_pair = bool(rendered_bytes)
        if rendered_bytes:
            images.append(_pil_from_bytes(rendered_bytes))
        prompt = self.build_refine_prompt(
            current_code,
            has_rendered_pair=has_pair,
            css_hints=css_hints,
            variables=variables,
            task_description=task_description,
        )
        return self._chat(images, prompt)

    def edit(
        self,
        current_code: str,
        instruction: str,
        css_hints: Optional[dict] = None,
        variables: Optional[dict] = None,
        **_: Any,
    ) -> str:
        prompt = self.build_edit_prompt(
            instruction, current_code, css_hints=css_hints, variables=variables
        )
        return self._chat([], prompt)

    # ------------------------------------------------------------------ util

    @staticmethod
    def _clean_html(text: str) -> str:
        """Strip chat markers and isolate the HTML document if present."""
        stripped = text.strip()
        if "```html" in stripped:
            stripped = stripped.split("```html", 1)[1]
            if "```" in stripped:
                stripped = stripped.split("```", 1)[0]
        elif stripped.startswith("```"):
            stripped = stripped.strip("`")
        return stripped.strip()


def effective_prompt_for_logging_generate(
    model: Any,
    *,
    frame_name: str,
    task_description: Optional[str],
    css_hints: Optional[dict],
    variables: Optional[dict],
) -> str:
    """Plain-text user prompt forwarded to UI2Code^N (English). For rule_based/Stub, logs a stub line."""
    if isinstance(model, UI2CodeModel):
        return model.build_generate_prompt(
            frame_name,
            css_hints=css_hints,
            variables=variables,
            task_description=task_description,
        )
    return (
        "# Effective multimodal prompt not serialized for this backend.\n"
        f"# model_type={type(model).__name__}\n"
    )


def effective_prompt_for_logging_refine(
    model: Any,
    *,
    current_code: str,
    has_rendered_pair: bool,
    task_description: Optional[str],
    css_hints: Optional[dict],
    variables: Optional[dict],
) -> str:
    if isinstance(model, UI2CodeModel):
        return model.build_refine_prompt(
            current_code,
            has_rendered_pair=has_rendered_pair,
            css_hints=css_hints,
            variables=variables,
            task_description=task_description,
        )
    return (
        "# Effective multimodal prompt not serialized for this backend.\n"
        f"# model_type={type(model).__name__}\n"
    )


def effective_prompt_for_logging_edit(
    model: Any,
    *,
    instruction: str,
    current_code: str,
    css_hints: Optional[dict],
    variables: Optional[dict],
) -> str:
    if isinstance(model, UI2CodeModel):
        return model.build_edit_prompt(
            instruction,
            current_code,
            css_hints=css_hints,
            variables=variables,
        )
    return (
        "# Effective multimodal prompt not serialized for this backend.\n"
        f"# model_type={type(model).__name__}\n"
    )
