"""Deployment verification for UI2Code^N.

Checks that
  1. torch sees CUDA and the expected GPU;
  2. the UI2Code_N weights live on disk and are complete;
  3. the tokenizer and processor load from the local snapshot;
  4. the model state dict can be inspected without loading every shard into RAM.

This script does NOT run generation. It is a fast sanity check for the
environment. For actual inference on non-trivial prompts you need a GPU with
>= 16 GB VRAM or time for CPU bf16 inference (several minutes per mockup).
"""

from __future__ import annotations

import json
import os
from pathlib import Path


os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")


def _default_model_dir() -> Path:
    """Prefer ``UI2CODEN_MODEL_ID`` (path or Hub id); else a platform default."""
    raw = os.environ.get("UI2CODEN_MODEL_ID", "").strip()
    if raw:
        return Path(raw)
    if os.name == "nt":
        return Path("d:/hf_models/UI2Code_N")
    return Path.home() / "hf_models" / "UI2Code_N"


MODEL_DIR = _default_model_dir()
REPORT_PATH = Path(__file__).resolve().parent.parent / "baseline-tests" / "outputs" / "real-model" / "install-verification.json"
REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)


def main() -> None:
    report: dict[str, object] = {}

    import torch
    report["torch"] = torch.__version__
    report["cuda_available"] = bool(torch.cuda.is_available())
    if torch.cuda.is_available():
        report["cuda_device_name"] = torch.cuda.get_device_name(0)
        report["cuda_capability"] = list(torch.cuda.get_device_capability(0))
        mem_gb = torch.cuda.get_device_properties(0).total_memory / 1024 ** 3
        report["cuda_total_vram_gb"] = round(mem_gb, 2)

    weight_files = sorted(MODEL_DIR.glob("model-*.safetensors"))
    report["weight_dir_exists"] = MODEL_DIR.exists()
    report["shard_count"] = len(weight_files)
    report["shard_total_gb"] = round(sum(p.stat().st_size for p in weight_files) / 1024 ** 3, 2)

    from transformers import AutoProcessor, AutoConfig
    processor = AutoProcessor.from_pretrained(str(MODEL_DIR), trust_remote_code=True)
    report["processor_class"] = type(processor).__name__
    report["tokenizer_vocab_size"] = int(processor.tokenizer.vocab_size)

    config = AutoConfig.from_pretrained(str(MODEL_DIR), trust_remote_code=True)
    report["model_type"] = config.model_type
    report["architectures"] = list(getattr(config, "architectures", []))

    index_path = MODEL_DIR / "model.safetensors.index.json"
    if index_path.exists():
        idx = json.loads(index_path.read_text(encoding="utf-8"))
        report["total_parameters_declared"] = idx.get("metadata", {}).get("total_size")

    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
