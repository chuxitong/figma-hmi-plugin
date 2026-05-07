"""
Week-7 deliverables: >= 3 edit examples + A/B/C context comparison.

Edits are applied on the Operator Control Panel baseline. The context comparison
uses the Equipment Status mockup because it is the most sensitive to tokens
(colors and spacing in a grid).

Outputs:
  - outputs/week7-edits/<edit_slug>.html + .png
  - outputs/week7-context/<config>.html + .png
  - outputs/week7-edits/edits.json
  - outputs/week7-context/context.json
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LS = ROOT / "local-service"
sys.path.insert(0, str(LS))

from renderer import render_html_to_png, shutdown_renderer  # noqa: E402
from rule_based_model import RuleBasedModel  # noqa: E402


EDITS = [
    "Make the primary button secondary.",
    "Make the alarm block more prominent.",
    "Reduce padding for the trend card.",
    "Make the card border thicker.",
    "Increase the title to a larger size.",
]


def apply_variables(code: str) -> str:
    """Simulate injecting Figma design tokens: override CSS variables."""
    tokens = (
        ":root {\n"
        "  --bg: #11131a;\n"
        "  --panel: #1b1f2a;\n"
        "  --panel-2: #24293a;\n"
        "  --accent: #29d3c5;\n"
        "  --border: #3b4256;\n"
        "  --text: #eef1f6;\n"
        "  --muted: #9aa3b2;\n"
        "}\n"
    )
    return re.sub(r":root\s*\{[^}]*\}", tokens, code, count=1, flags=re.DOTALL)


def apply_css_hints(code: str) -> str:
    """Simulate Figma getCSSAsync hints: tighter spacing and typography."""
    replacements = [
        (r"body\s*\{[^}]*padding:\s*24px;", lambda m: m.group(0).replace("padding: 24px", "padding: 18px")),
        (r"h1\s*\{\s*font-size:\s*22px", lambda _m: "h1 { font-size: 20px"),
        (r"\.card\s*\{[^}]*padding:\s*16px", lambda m: m.group(0).replace("padding: 16px", "padding: 14px")),
        (r"\.grid\s*\{[^}]*gap:\s*16px", lambda m: m.group(0).replace("gap: 16px", "gap: 12px")),
    ]
    for pattern, repl in replacements:
        code = re.sub(pattern, repl, code, count=1, flags=re.DOTALL)
    return code


async def write_artifact(path: Path, html: str) -> None:
    path.write_text(html, encoding="utf-8")
    png_path = path.with_suffix(".png")
    png = await render_html_to_png(html, 1280, 720)
    png_path.write_bytes(png)


async def run_edits(model, outdir: Path) -> list[dict]:
    outdir.mkdir(parents=True, exist_ok=True)
    base_html = model.generate(b"", frame_name="Operator Control Panel")
    await write_artifact(outdir / "base.html", base_html)

    results = []
    for idx, instruction in enumerate(EDITS, start=1):
        t0 = time.perf_counter()
        edited = model.edit(base_html, instruction)
        dt = time.perf_counter() - t0
        slug = f"edit_{idx:02d}_" + re.sub(r"[^a-z0-9]+", "_", instruction.lower()).strip("_")[:48]
        html_path = outdir / f"{slug}.html"
        await write_artifact(html_path, edited)
        changed = sum(1 for a, b in zip(base_html.splitlines(), edited.splitlines()) if a != b)
        results.append({
            "instruction": instruction,
            "slug": slug,
            "edit_time_s": round(dt, 4),
            "changed_lines": changed,
            "html": str(html_path.relative_to(ROOT)),
            "png": str(html_path.with_suffix(".png").relative_to(ROOT)),
        })
    (outdir / "edits.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    return results


async def run_context(model, outdir: Path) -> list[dict]:
    outdir.mkdir(parents=True, exist_ok=True)
    base_html = model.generate(b"", frame_name="Equipment Status Dashboard")

    configs = [
        ("A_image_only", base_html),
        ("B_image_variables", apply_variables(base_html)),
        ("C_image_variables_css", apply_css_hints(apply_variables(base_html))),
    ]

    results = []
    for name, html in configs:
        path = outdir / f"{name}.html"
        await write_artifact(path, html)
        results.append({
            "config": name,
            "html": str(path.relative_to(ROOT)),
            "png": str(path.with_suffix(".png").relative_to(ROOT)),
            "bytes": len(html.encode("utf-8")),
        })
    (outdir / "context.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    return results


async def main() -> None:
    try:
        model = RuleBasedModel()
        edits_dir = ROOT / "baseline-tests" / "outputs" / "week7-edits"
        context_dir = ROOT / "baseline-tests" / "outputs" / "week7-context"

        edits = await run_edits(model, edits_dir)
        print(f"[done] {len(edits)} edits -> {edits_dir}")

        ctx = await run_context(model, context_dir)
        print(f"[done] {len(ctx)} context configs -> {context_dir}")
    finally:
        await shutdown_renderer()


if __name__ == "__main__":
    asyncio.run(main())
