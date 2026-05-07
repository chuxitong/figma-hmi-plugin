"""
Local AI service for the Figma HMI plugin (UI2Code^N or rule-based stand-in).
Wraps the UI2Code^N model into HTTP endpoints.
"""

import base64
import hashlib
import io
import json
import logging
import os
import time
from pathlib import Path
from typing import Annotated, Any, Optional

from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from model_wrapper import (
    effective_prompt_for_logging_edit,
    effective_prompt_for_logging_generate,
    effective_prompt_for_logging_refine,
)
from renderer import render_html_to_png

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parent.parent
_TMP_ROOT = Path("/tmp").resolve()


def _b64_audit(val: Optional[str]) -> dict[str, Any]:
    """Record length + short hash instead of embedding megabyte base64 in logs."""
    if val is None:
        return {"present": False}
    s = str(val)
    h = hashlib.sha256(s.encode("utf-8", errors="replace")).hexdigest()[:32]
    return {"present": True, "char_len": len(s), "sha256_prefix": h}


def _sanitize_experiment_trace_dir(raw: Optional[str]) -> Optional[Path]:
    if raw is None or not str(raw).strip():
        return None
    p = Path(str(raw).strip()).expanduser().resolve()
    for base in (_REPO_ROOT, _TMP_ROOT):
        try:
            p.relative_to(base)
            return p
        except ValueError:
            continue
    logger.warning(
        "Rejecting X-Experiment-Trace-Dir (must be under repo %s or /tmp): %s",
        _REPO_ROOT,
        raw,
    )
    return None


def _write_experiment_trace(
    *,
    operation: str,
    trace_parent: Path,
    effective_prompt: str,
    request_meta: dict[str, Any],
) -> None:
    trace_parent.mkdir(parents=True, exist_ok=True)
    stamp = trace_parent / f"{operation}_{time.time_ns()}"
    stamp.mkdir(parents=False, exist_ok=False)
    (stamp / "effective_prompt.txt").write_text(effective_prompt, encoding="utf-8")
    body = json.dumps(request_meta, ensure_ascii=False, indent=2, default=str)
    (stamp / "request_meta.json").write_text(body, encoding="utf-8")
    # Alias required by thesis reproducibility checklist (same payload audit as request_meta.json).
    (stamp / "request.json").write_text(body, encoding="utf-8")


def _maybe_trace_generate(
    req: "GenerateRequest",
    x_experiment_trace_dir: Optional[str],
) -> None:
    root = _sanitize_experiment_trace_dir(x_experiment_trace_dir)
    if root is None:
        return
    m = get_model()
    ep = effective_prompt_for_logging_generate(
        m,
        frame_name=req.frame_name,
        task_description=req.task_description,
        css_hints=req.css_hints,
        variables=req.variables,
    )
    meta = req.model_dump()
    meta["image_base64"] = _b64_audit(req.image_base64)
    meta["note_en"] = (
        "effective_prompt.txt is English user text (+ optional XML-ish context blocks); "
        "tokenizer chat template wraps it with image tensors (not reproduced here)."
    )
    meta["prompt_profile_env"] = os.environ.get("UI2CODEN_PROMPT_PROFILE", "baseline")
    _write_experiment_trace(
        operation="generate",
        trace_parent=root,
        effective_prompt=ep,
        request_meta={"endpoint": "POST /generate", "payload": meta},
    )


def _maybe_trace_refine(
    req: "RefineRequest",
    *,
    has_rendered_pair: bool,
    x_experiment_trace_dir: Optional[str],
) -> None:
    root = _sanitize_experiment_trace_dir(x_experiment_trace_dir)
    if root is None:
        return
    m = get_model()
    ep = effective_prompt_for_logging_refine(
        m,
        current_code=req.current_code,
        has_rendered_pair=has_rendered_pair,
        task_description=req.task_description,
        css_hints=req.css_hints,
        variables=req.variables,
    )

    meta = req.model_dump()
    meta["reference_image_base64"] = _b64_audit(req.reference_image_base64)
    meta["rendered_image_base64"] = _b64_audit(req.rendered_image_base64)
    meta["has_rendered_pair_effective"] = has_rendered_pair
    meta["note_en"] = (
        "If rendered_image_base64 was omitted but server-side rendering succeeded, "
        "has_rendered_pair_effective mirrors the tensors passed into the multimodal prompt."
    )
    meta["prompt_profile_env"] = os.environ.get("UI2CODEN_PROMPT_PROFILE", "baseline")
    _write_experiment_trace(
        operation="refine",
        trace_parent=root,
        effective_prompt=ep,
        request_meta={"endpoint": "POST /refine", "payload": meta},
    )


def _maybe_trace_edit(req: "EditRequest", x_experiment_trace_dir: Optional[str]) -> None:
    root = _sanitize_experiment_trace_dir(x_experiment_trace_dir)
    if root is None:
        return
    m = get_model()
    ep = effective_prompt_for_logging_edit(
        m,
        instruction=req.instruction,
        current_code=req.current_code,
        css_hints=req.css_hints,
        variables=req.variables,
    )
    meta = req.model_dump()
    snippet = meta.get("current_code") or ""
    meta["current_code_len"] = len(snippet)
    meta["current_code_sha256_prefix"] = (
        hashlib.sha256(snippet.encode("utf-8", errors="replace")).hexdigest()[:24]
        if snippet
        else None
    )
    meta.pop("current_code", None)
    meta["prompt_profile_env"] = os.environ.get("UI2CODEN_PROMPT_PROFILE", "baseline")
    _write_experiment_trace(
        operation="edit",
        trace_parent=root,
        effective_prompt=ep,
        request_meta={"endpoint": "POST /edit", "payload": meta},
    )


app = FastAPI(title="Figma HMI Plugin — local service", version="0.1.0")

# Figma's plugin panel runs in a separate secure context; fetch() to
# http://127.0.0.1:8000 is cross-site + "local network" in Chrome, which
# sends a CORS preflight with Access-Control-Request-Private-Network. Without
# allow_private_network, OPTIONS fails and the panel shows no response even
# though a normal browser tab can open /docs (same-origin to the API).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_private_network=True,
)

model = None
# Set on first successful load: "ui2coden" | "rule_based" | "stub"
active_model_kind: Optional[str] = None


@app.on_event("startup")
async def _apply_ui2coden_env_defaults() -> None:
    """Prime HF offline flags and local weight path before any ``transformers`` import."""
    if os.environ.get("USE_REAL_MODEL") == "1":
        from model_wrapper import apply_real_model_env_defaults

        apply_real_model_env_defaults()


@app.on_event("startup")
async def _warm_load_model_if_real() -> None:
    """Load UI2Code^N during startup so /health and first /generate are ready.

    Cloud + Figma flow often goes: user opens tunnel → checks /docs → Generate.
    Without warm-up, ``model`` stays None until first request and health shows
    ``ui2code_n_active: false`` even though the service is up.

    Set ``UI2CODEN_SKIP_WARMUP=1`` to restore lazy load (faster process boot,
    first request pays load cost).
    """
    if os.environ.get("USE_REAL_MODEL") != "1":
        return
    if os.environ.get("UI2CODEN_SKIP_WARMUP", "").strip().lower() in ("1", "true", "yes"):
        logger.info("UI2CODEN_SKIP_WARMUP=1: UI2Code^N will lazy-load on first request.")
        return
    import asyncio

    logger.info("Warming UI2Code^N at startup (async thread; may take several minutes)...")
    try:
        await asyncio.to_thread(get_model)
        logger.info("Startup warm-up finished: model_kind=%s", active_model_kind)
    except Exception as exc:
        logger.warning("Startup warm-up failed (%s); will retry on first request.", exc)


def get_model():
    """Lazy-load the active model on first request.

    If USE_REAL_MODEL=1 is set and model weights are available, load the real
    UI2Code^N via :class:`model_wrapper.UI2CodeModel`. Otherwise fall back to
    the deterministic stand-in :class:`rule_based_model.RuleBasedModel`, which
    is fast enough for local development and still produces renderable HMI
    pages end to end.
    """
    global model, active_model_kind
    if model is None:
        if os.environ.get("USE_REAL_MODEL") == "1":
            try:
                from model_wrapper import apply_real_model_env_defaults, UI2CodeModel

                apply_real_model_env_defaults()
                logger.info("Loading real UI2Code^N (first call can take a while)...")
                model = UI2CodeModel()
                active_model_kind = "ui2coden"
                logger.info("UI2Code^N loaded.")
                return model
            except Exception as exc:
                logger.warning("Failed to load UI2Code^N (%s); falling back.", exc)
        try:
            from rule_based_model import RuleBasedModel

            logger.info("Loading rule-based stand-in model.")
            model = RuleBasedModel()
            active_model_kind = "rule_based"
        except Exception:
            logger.warning("No stand-in model available; using minimal stub.")
            model = StubModel()
            active_model_kind = "stub"
    return model


class StubModel:
    """Development stub when the real model is not available."""

    def generate(self, image_bytes: bytes, **kwargs) -> str:
        return (
            "<!DOCTYPE html>\n<html><head><style>\n"
            "  body { background: #1e1e2e; color: #e0e0e0; font-family: sans-serif; "
            "padding: 24px; }\n"
            "  .card { background: #2a2a3e; border-radius: 8px; padding: 16px; "
            "margin: 8px; display: inline-block; width: 200px; }\n"
            "  .status { display: inline-block; width: 12px; height: 12px; "
            "border-radius: 50%; margin-right: 8px; }\n"
            "  .ok { background: #4caf50; }\n"
            "  .warn { background: #ff9800; }\n"
            "</style></head><body>\n"
            "<h2>Equipment Status</h2>\n"
            '<div class="card"><span class="status ok"></span>Pump A — Running</div>\n'
            '<div class="card"><span class="status warn"></span>Pump B — Warning</div>\n'
            "</body></html>"
        )

    def refine(self, reference_bytes: bytes, current_code: str, **kwargs) -> str:
        return current_code.replace("margin: 8px", "margin: 12px")

    def edit(self, current_code: str, instruction: str, **kwargs) -> str:
        if "secondary" in instruction.lower():
            return current_code.replace("background: #2a2a3e", "background: #3a3a4e")
        return current_code


def _ctx_flags(
    css_hints: Optional[dict],
    variables: Optional[dict],
    task_description: Optional[str] = None,
    *,
    label_instruction: bool = False,
) -> dict[str, bool]:
    has_text = bool(task_description and str(task_description).strip())
    out: dict[str, bool] = {
        "css_hints": bool(css_hints),
        "variables": bool(variables),
    }
    if label_instruction:
        out["instruction"] = has_text
    else:
        out["task_description"] = has_text
    return out


def _code_meta(
    operation: str,
    width: int,
    height: int,
    *,
    preview_ok: bool,
    css_hints: Optional[dict] = None,
    variables: Optional[dict] = None,
    task_description: Optional[str] = None,
    instruction_mode: bool = False,
) -> dict[str, Any]:
    global active_model_kind
    return {
        "operation": operation,
        "model_kind": active_model_kind or "unknown",
        "viewport": {"width": width, "height": height},
        "preview_png_embedded": preview_ok,
        "context": _ctx_flags(
            css_hints,
            variables,
            task_description,
            label_instruction=instruction_mode,
        ),
        "next_stage": {
            "suggested": [
                {
                    "endpoint": "POST /edit",
                    "for": "Instruction-based text edits to the current HTML.",
                },
                {
                    "endpoint": "POST /refine",
                    "for": "Visual alignment vs reference: pass reference PNG, current code, and optional rendered PNG.",
                },
                {"endpoint": "POST /render", "for": "Re-render any HTML to PNG (same engine as inline previews)."},
            ]
        },
    }


# ── Request / Response models ──


class GenerateRequest(BaseModel):
    image_base64: str
    frame_name: str = "Untitled"
    # Week-4: task / prompt in natural language (optional on the wire; when set, forwarded to the model)
    task_description: Optional[str] = None
    width: int = 1280
    height: int = 720
    css_hints: Optional[dict] = None
    variables: Optional[dict] = None


class RefineRequest(BaseModel):
    reference_image_base64: str
    current_code: str
    rendered_image_base64: Optional[str] = None
    task_description: Optional[str] = None
    width: int = 1280
    height: int = 720
    css_hints: Optional[dict] = None
    variables: Optional[dict] = None


class EditRequest(BaseModel):
    current_code: str
    instruction: str
    width: int = 1280
    height: int = 720
    css_hints: Optional[dict] = None
    variables: Optional[dict] = None


class RenderRequest(BaseModel):
    html_code: str
    width: int = 1280
    height: int = 720


class CodeResponse(BaseModel):
    code: str
    preview_base64: Optional[str] = None
    explanation: Optional[str] = None
    # Suggested /edit vs /refine, viewport, context flags, model kind, etc.
    metadata: dict[str, Any] = Field(default_factory=dict)


class RenderResponse(BaseModel):
    image_base64: str
    explanation: str = "Rasterised HTML to PNG in headless Chromium (same pipeline as preview fields)."
    metadata: dict[str, Any] = Field(default_factory=dict)


# ── Endpoints ──


@app.post("/generate", response_model=CodeResponse)
async def generate(
    req: GenerateRequest,
    x_experiment_trace_dir: Annotated[Optional[str], Header(alias="X-Experiment-Trace-Dir")] = None,
):
    """Generate HTML/CSS code from a UI screenshot."""
    image_bytes = base64.b64decode(req.image_base64)
    m = get_model()

    code = m.generate(
        image_bytes,
        frame_name=req.frame_name,
        width=req.width,
        height=req.height,
        css_hints=req.css_hints,
        variables=req.variables,
        task_description=req.task_description,
    )

    preview_b64 = None
    try:
        preview_bytes = await render_html_to_png(code, req.width, req.height)
        preview_b64 = base64.b64encode(preview_bytes).decode()
    except Exception as e:
        logger.warning(f"Preview rendering failed: {e}")

    expl = "Initial code generated from screenshot (PNG preview server-side via Playwright)."
    if req.task_description and str(req.task_description).strip():
        expl = (
            "Initial code generated from screenshot; user task description was included in the model prompt. "
            f"Preview format: PNG (base64 in preview_base64)."
        )

    _maybe_trace_generate(req, x_experiment_trace_dir)

    return CodeResponse(
        code=code,
        preview_base64=preview_b64,
        explanation=expl,
        metadata=_code_meta(
            "generate",
            req.width,
            req.height,
            preview_ok=preview_b64 is not None,
            css_hints=req.css_hints,
            variables=req.variables,
            task_description=req.task_description,
        ),
    )


@app.post("/refine", response_model=CodeResponse)
async def refine(
    req: RefineRequest,
    x_experiment_trace_dir: Annotated[Optional[str], Header(alias="X-Experiment-Trace-Dir")] = None,
):
    """Refine code to better match the reference mockup.

    The model receives THREE inputs, in line with the UI-polishing protocol:
    the reference screenshot, the current rendered screenshot of the latest
    HTML, and the current HTML itself. If the caller did not pre-render, we
    render here on the server so the model always gets the rendered image.
    """
    ref_bytes = base64.b64decode(req.reference_image_base64)

    if req.rendered_image_base64:
        rendered_bytes = base64.b64decode(req.rendered_image_base64)
    else:
        try:
            rendered_bytes = await render_html_to_png(
                req.current_code, req.width, req.height
            )
        except Exception as e:
            logger.warning(f"Server-side rendering for refine failed: {e}")
            rendered_bytes = b""

    m = get_model()

    code = m.refine(
        ref_bytes,
        req.current_code,
        rendered_bytes=rendered_bytes,
        css_hints=req.css_hints,
        variables=req.variables,
        task_description=req.task_description,
    )

    has_rendered_pair = bool(rendered_bytes)

    preview_b64 = None
    try:
        preview_bytes = await render_html_to_png(code, req.width, req.height)
        preview_b64 = base64.b64encode(preview_bytes).decode()
    except Exception as e:
        logger.warning(f"Preview rendering failed: {e}")

    expl = "Code refined toward the reference image; preview is PNG (base64)."
    if req.task_description and str(req.task_description).strip():
        expl += " Optional task hint was passed to the model."

    _maybe_trace_refine(req, has_rendered_pair=has_rendered_pair, x_experiment_trace_dir=x_experiment_trace_dir)

    return CodeResponse(
        code=code,
        preview_base64=preview_b64,
        explanation=expl,
        metadata=_code_meta(
            "refine",
            req.width,
            req.height,
            preview_ok=preview_b64 is not None,
            css_hints=req.css_hints,
            variables=req.variables,
            task_description=req.task_description,
        ),
    )


@app.post("/edit", response_model=CodeResponse)
async def edit(
    req: EditRequest,
    x_experiment_trace_dir: Annotated[Optional[str], Header(alias="X-Experiment-Trace-Dir")] = None,
):
    """Edit existing code according to a natural-language instruction.

    The optional context (Figma design variables and CSS hints) is forwarded
    to the model so that local edits can take design-system tokens into
    account. The user controls whether this context is sent via the two
    checkboxes in the plugin UI.
    """
    m = get_model()
    code = m.edit(
        req.current_code,
        req.instruction,
        css_hints=req.css_hints,
        variables=req.variables,
    )

    preview_b64 = None
    try:
        preview_bytes = await render_html_to_png(code, req.width, req.height)
        preview_b64 = base64.b64encode(preview_bytes).decode()
    except Exception as e:
        logger.warning(f"Preview rendering failed: {e}")

    _maybe_trace_edit(req, x_experiment_trace_dir)

    return CodeResponse(
        code=code,
        preview_base64=preview_b64,
        explanation=f'Edit applied (PNG preview): instruction was "{req.instruction[:500]}".',
        metadata=_code_meta(
            "edit",
            req.width,
            req.height,
            preview_ok=preview_b64 is not None,
            css_hints=req.css_hints,
            variables=req.variables,
            task_description=req.instruction,
            instruction_mode=True,
        ),
    )


@app.post("/render", response_model=RenderResponse)
async def render(req: RenderRequest):
    """Render HTML code to a PNG screenshot."""
    image_bytes = await render_html_to_png(req.html_code, req.width, req.height)
    b64 = base64.b64encode(image_bytes).decode()
    return RenderResponse(
        image_base64=b64,
        metadata={
            "format": "png",
            "bytes_base64_length": len(b64),
            "viewport": {"width": req.width, "height": req.height},
            "render_engine": "playwright_chromium",
            "llm_not_involved": True,
        },
    )


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model_loaded": model is not None,
        "model_kind": active_model_kind,
        "ui2code_n_active": active_model_kind == "ui2coden",
        # UI2Code^N multimodal prompt template (baseline vs extended); must match process env at uvicorn startup.
        "ui2coden_prompt_profile": os.environ.get(
            "UI2CODEN_PROMPT_PROFILE", "baseline"
        ).strip().lower(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
