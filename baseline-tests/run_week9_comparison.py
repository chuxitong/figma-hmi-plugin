"""
Week-9 deliverables: baseline vs improved comparison.

Procedure:
  1. Generate once per mockup with the baseline RuleBasedModel.
  2. Generate once per mockup with the improved pipeline:
       - stronger prompt prelude injected into frame_name;
       - deterministic post-processing of the HTML output.
  3. Render both and save side-by-side artefacts.
  4. Produce comparison.json with per-mockup byte sizes and line-diff counts.

This captures the "what was improved and did it help" artefact requested in
the week 9 plan.
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LS = ROOT / "local-service"
sys.path.insert(0, str(LS))

from renderer import render_html_to_png, shutdown_renderer  # noqa: E402
from rule_based_model import RuleBasedModel  # noqa: E402
from postprocess import postprocess_html  # noqa: E402


MOCKUPS = [
    ("m1_equipment_status", "Equipment Status Dashboard"),
    ("m2_alarm_event", "Alarm & Event Monitor"),
    ("m3_trend_monitor", "Real-Time Trend Monitor"),
    ("m4_operator_panel", "Operator Control Panel"),
    ("m5_production_overview", "Production Line Overview"),
    ("m6_tank_synoptic", "Tank Farm Synoptic"),
    ("m7_energy_dashboard", "Energy Monitoring Dashboard"),
    ("m8_batch_recipe", "Batch Recipe Management"),
]


IMPROVED_PRELUDE = (
    "Industrial HMI, dark theme, high-contrast, ISA-101. "
    "Use semantic HTML5, tight spacing, clear hierarchy. "
)


def improved_generate(model: RuleBasedModel, frame_name: str) -> str:
    """Improved pipeline: enrich the prompt + post-process the output."""
    raw = model.generate(b"", frame_name=IMPROVED_PRELUDE + frame_name)
    return postprocess_html(raw)


async def render_pair(out_dir: Path, baseline: str, improved: str) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "baseline.html").write_text(baseline, encoding="utf-8")
    (out_dir / "improved.html").write_text(improved, encoding="utf-8")

    b_png = await render_html_to_png(baseline, 1280, 720)
    i_png = await render_html_to_png(improved, 1280, 720)
    (out_dir / "baseline.png").write_bytes(b_png)
    (out_dir / "improved.png").write_bytes(i_png)

    b_lines = baseline.splitlines()
    i_lines = improved.splitlines()
    diff_lines = sum(1 for a, b in zip(b_lines, i_lines) if a != b)
    diff_lines += abs(len(b_lines) - len(i_lines))
    return {
        "baseline_bytes": len(baseline.encode("utf-8")),
        "improved_bytes": len(improved.encode("utf-8")),
        "diff_lines": diff_lines,
    }


async def main() -> None:
    try:
        model = RuleBasedModel()
        root_out = ROOT / "baseline-tests" / "outputs" / "week9-comparison"
        root_out.mkdir(parents=True, exist_ok=True)

        report: list[dict] = []
        t_start = time.perf_counter()

        for mid, name in MOCKUPS:
            baseline = model.generate(b"", frame_name=name)
            improved = improved_generate(model, name)
            stats = await render_pair(root_out / mid, baseline, improved)
            report.append({"mockup": mid, "frame_name": name, **stats})
            print(f"[done] {mid} diff_lines={stats['diff_lines']}")

        summary = {
            "elapsed_s": round(time.perf_counter() - t_start, 2),
            "results": report,
        }
        (root_out / "comparison.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        md = ["# Baseline vs Improved Comparison", "", "| Mockup | Baseline (B) | Improved (B) | Changed lines |", "| --- | ---: | ---: | ---: |"]
        for r in report:
            md.append(f"| {r['mockup']} | {r['baseline_bytes']} | {r['improved_bytes']} | {r['diff_lines']} |")
        md.append("")
        md.append(f"Total elapsed: {summary['elapsed_s']} s")
        (root_out / "comparison.md").write_text("\n".join(md), encoding="utf-8")

        print(f"[report] {root_out / 'comparison.json'}")
        print(f"[report] {root_out / 'comparison.md'}")
    finally:
        await shutdown_renderer()


if __name__ == "__main__":
    asyncio.run(main())
