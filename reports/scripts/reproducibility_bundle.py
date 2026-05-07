"""
Automated reproducibility artefacts for thesis / advisor review.

Writes under <deliverables_weekN>/reproducibility_complete/:
  • http_request_bodies/*.full.json.gz — exact UTF-8 JSON bytes the client sent (same as urllib uses)
  • *.full.json.gz.sha256 — SHA-256 of those uncompressed bytes (NOT of the .gz file)
  • HEALTH_at_run_start.json, RUN_META.json, INDEX.json
  • README_REPRODUCIBILITY.zh.md — honest limitations (auto-generated; no manual edits required)
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _try_git_commit(repo_root: Path) -> Optional[str]:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip() or None
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None


@dataclass
class ReproducibilityRecorder:
    """Records each POST body and emits INDEX + README."""

    bundle_root: Path
    week: int
    deliver_name: str
    entries: list[dict[str, Any]] = field(default_factory=list)
    _seq: int = 0
    health_at_start: Optional[dict[str, Any]] = None
    extra_index: dict[str, Any] = field(default_factory=dict)

    def set_health(self, h: dict[str, Any]) -> None:
        self.health_at_start = dict(h)

    def record_post(self, endpoint: str, body: dict[str, Any]) -> None:
        """Record exact wire JSON for POST ``endpoint`` (leading slash, e.g. /generate)."""
        self._seq += 1
        safe = endpoint.replace("/", "_").strip("_") or "api"
        stem = f"{self._seq:03d}_POST_{safe}"
        bodies_dir = self.bundle_root / "http_request_bodies"
        bodies_dir.mkdir(parents=True, exist_ok=True)
        raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
        gz_path = bodies_dir / f"{stem}.full.json.gz"
        with gzip.open(gz_path, "wb", compresslevel=9) as gz:
            gz.write(raw)
        digest = _sha256_bytes(raw)
        note = (
            f"{digest}  ← SHA-256 of UTF-8 JSON bytes BEFORE gzip (not of the .gz file)\n"
        )
        (gz_path.with_name(gz_path.name + ".sha256")).write_text(note, encoding="utf-8")
        self.entries.append(
            {
                "sequence": self._seq,
                "method": "POST",
                "path": endpoint,
                "relative_gzip": str(gz_path.relative_to(self.bundle_root)),
                "sha256_uncompressed_utf8_json": digest,
                "uncompressed_json_bytes": len(raw),
            }
        )

    def finalize(
        self,
        *,
        repo_root: Path,
        api_base: str,
        trace_dir_relative: Optional[str],
        week_extra: dict[str, Any],
        bundle_repo_relative: str,
    ) -> None:
        self.bundle_root.mkdir(parents=True, exist_ok=True)
        if self.health_at_start is not None:
            (self.bundle_root / "HEALTH_at_run_start.json").write_text(
                json.dumps(self.health_at_start, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8",
            )
        srv_prof = None
        if self.health_at_start:
            srv_prof = self.health_at_start.get("ui2coden_prompt_profile")
        client_prof = os.environ.get("UI2CODEN_PROMPT_PROFILE", "baseline").strip().lower()
        run_meta = {
            "iso_utc": datetime.now(timezone.utc).isoformat(),
            "week": self.week,
            "deliver": self.deliver_name,
            "api_base": api_base,
            "git_commit": _try_git_commit(repo_root),
            "server_trace_dir_repo_relative": trace_dir_relative,
            "ui2coden_prompt_profile_observed_via_health_at_start": srv_prof or client_prof,
            "ui2coden_prompt_profile_env_client_shell": client_prof,
            **week_extra,
        }
        (self.bundle_root / "RUN_META.json").write_text(
            json.dumps(run_meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        index: dict[str, Any] = {
            "readme_zh_relative": "README_REPRODUCIBILITY.zh.md",
            "http_posts_recorded": self.entries,
            "extra": self.extra_index,
        }
        (self.bundle_root / "INDEX.json").write_text(
            json.dumps(index, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        readme = _render_readme_zh(
            bundle_repo_relative=bundle_repo_relative,
            week=self.week,
            run_meta_path="RUN_META.json",
            trace_dir_relative=trace_dir_relative,
            n_posts=len(self.entries),
        )
        (self.bundle_root / "README_REPRODUCIBILITY.zh.md").write_text(readme, encoding="utf-8")


def _render_readme_zh(
    *,
    bundle_repo_relative: str,
    week: int,
    run_meta_path: str,
    trace_dir_relative: Optional[str],
    n_posts: int,
) -> str:
    trace_line = (
        f"- **服务端追溯目录（每次 Week 7/8 主流程自动发送 `X-Experiment-Trace-Dir`；可用 `--trace-dir` 改根路径）**：仓库内相对路径 `{trace_dir_relative}`。\n"
        if trace_dir_relative
        else (
            "- **服务端追溯目录**：`RUN_META.json` 中 `server_trace_dir_repo_relative` 为空——通常表示**未跑主流程**"
            "（例如仅 `--replay-week8-figures` 重画图），本次未向服务发送追溯头，故无 `effective_prompt.txt` / `request.json` 审计副本；"
            "请以本目录 **gzip 全文** 为准，或重新执行带 `--week 7|8` 的完整测评。\n"
        )
    )
    return f"""# 可复现材料说明（全部由脚本自动生成，请勿手改本文）

本目录（相对仓库根）：`{bundle_repo_relative}`
对应周次：**Week {week}**
元数据：`{run_meta_path}`、`HEALTH_at_run_start.json`、`INDEX.json`

---

## 1. 本目录承诺提供什么（与导师要求对齐）

| 内容 | 说明 |
|------|------|
| `http_request_bodies/*.full.json.gz` | 评估脚本 `POST` 时使用的 **完整 JSON UTF-8 字节序列**（与 `urllib` 所用 `json.dumps(..., ensure_ascii=False).encode('utf-8')` 一致），**含完整 `*_base64` 图像**。解压后即为当次请求的 HTTP JSON body。 |
| （**不写入本包**）`POST /render` | 无头渲染预览用，不改变模型 multimodal 输入；为控制体量未 gzip 存档。 |
| `*.full.json.gz.sha256` | 对 **解压后 UTF-8 JSON 原始字节** 的 SHA-256；**不是** `.gz` 文件的哈希。 |
| `HEALTH_at_run_start.json` | 交付物流水线开始后、首次发包前快照的 `GET /health`，用于佐证 **`model_kind` / `ui2code_n_active`**。 |
| `INDEX.json` | 每条 POST 的路径、gzip 相对路径、哈希、字节数。 |

{trace_line}
- **`X-Experiment-Trace-Dir`（完整 Week 7/8 默认总有）**：服务在追溯根目录下按请求建子文件夹，内含 `effective_prompt.txt`（**代入后的英文文本**；多模态时**图像仍以张量进模型**，**不能**单凭此文件声明已包含「模型全部输入」）以及 **`request_meta.json` 与 `request.json`（内容相同）**：为服务端审计副本，**大块 base64 被替换为「长度 + sha256 前缀」**，用于 git 友好与对照；它们**不可替代**本目录 gzip 中的 **完整** 客户端请求体。**两者并存**：**gzip（本目录） = 发包原文**；**trace = prompt 明文 + 脱敏字段审计**（与 gzip 互补，非可选项）。

---

## 2. 诚实边界（避免误导）

1. **输出不唯一**：相同 POST body 在不同驱动 / 随机种子 / cudnn / 权重文件版本 / 服务端环境变量下，模型输出的 HTML 或预览 PNG **可能有差异**。此处固定的是 **输入侧证据链**，而非对输出做全域唯一锁定。  
2. **勿用剧本式 JSON 顶替真实输入**：导师要求的反例——**单独**放一个只描写实验场景的 `prompts.json` 却声称等价于完整模型调用——仍为**禁止**。若引用本仓库，应向导师指明 **`INDEX.json` + `http_request_bodies/*.full.json.gz` +（若存在）服务端 `effective_prompt.txt`**。

---

## 3. POST 数量

仅 **`/generate`、 `/refine`、 `/edit`** 计入本节（明细见 `INDEX.json`）。

本条流水共记录 **{n_posts}** 条。

---

## 4. 解压校验示例

```bash
gzip -dc http_request_bodies/001_POST_generate.full.json.gz | sha256sum
# 与对应 .sha256 文件中的前缀一致（对解压后的字节流）。
```

---
*自动生成 / auto-generated*
"""


def wipe_and_create_bundle(deliver_root: Path, *, resume: bool = False) -> Path:
    """
    Prepare ``deliver_root/reproducibility_complete/``.
    When ``resume`` is True the directory is preserved (crash-safe continuation).
    """
    import shutil

    bundle = deliver_root / "reproducibility_complete"
    if resume:
        bundle.mkdir(parents=True, exist_ok=True)
        return bundle
    if bundle.is_dir():
        shutil.rmtree(bundle)
    bundle.mkdir(parents=True, exist_ok=True)
    return bundle


def _gzip_stem_parts(filename: str) -> tuple[int, str] | None:
    if not filename.endswith(".full.json.gz"):
        return None
    stem = filename[: -len(".full.json.gz")]
    if "_POST_" not in stem:
        return None
    left, suf = stem.split("_POST_", 1)
    try:
        return int(left), suf
    except ValueError:
        return None


def _endpoint_from_fname_suffix(tail: str) -> str:
    if tail == "generate":
        return "/generate"
    if tail == "refine":
        return "/refine"
    if tail == "edit":
        return "/edit"
    return "/" + tail.replace("_", "/")


def rebuild_bundle_index_entries(bundle_root: Path) -> list[dict[str, Any]]:
    """After a kill before finalize, rebuild gzip index metadata from filenames + bytes."""
    bodies = bundle_root / "http_request_bodies"
    out: list[dict[str, Any]] = []
    if not bodies.is_dir():
        return out
    for gz_path in sorted(bodies.glob("*_POST_*.full.json.gz")):
        parsed = _gzip_stem_parts(gz_path.name)
        if not parsed:
            continue
        seq, suf = parsed
        try:
            with gzip.open(gz_path, "rb") as gz:
                raw = gz.read()
        except OSError:
            continue
        digest = _sha256_bytes(raw)
        endpoint = _endpoint_from_fname_suffix(suf)
        out.append(
            {
                "sequence": seq,
                "method": "POST",
                "path": endpoint,
                "relative_gzip": str(gz_path.relative_to(bundle_root)),
                "sha256_uncompressed_utf8_json": digest,
                "uncompressed_json_bytes": len(raw),
            }
        )
    out.sort(key=lambda e: int(e["sequence"]))
    return out


def week8_bundle_recorder_loaded(
    bundle_root: Path, *, week: int, deliver_name: str, resume: bool
) -> ReproducibilityRecorder:
    """
    Recorder whose ``entries`` / ``_seq`` continue numbering after INDEX or gzip-scan,
    without duplicating filenames for new posts.
    """
    initial: list[dict[str, Any]] = []
    if resume:
        idx = bundle_root / "INDEX.json"
        if idx.is_file():
            try:
                blob = json.loads(idx.read_text(encoding="utf-8"))
                initial = list(blob.get("http_posts_recorded") or [])
            except json.JSONDecodeError:
                initial = []
        if not initial:
            initial = rebuild_bundle_index_entries(bundle_root)
        mx_seq = max((int(e["sequence"]) for e in initial), default=0)
    else:
        mx_seq = 0
    return ReproducibilityRecorder(
        bundle_root,
        week=week,
        deliver_name=deliver_name,
        entries=list(initial),
        _seq=mx_seq,
    )

