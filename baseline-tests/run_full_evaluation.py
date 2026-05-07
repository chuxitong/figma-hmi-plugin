"""
Full evaluation over all mockups with real timing and real file outputs.

Runs:
  - Generation for every mockup
  - 2 refinement iterations for every mockup
  - 1 natural-language edit per mockup

Produces:
  - outputs/full-eval/<mockup>/<phase>.html
  - outputs/full-eval/<mockup>/<phase>.png
  - outputs/full-eval/metrics.json
  - outputs/full-eval/metrics.csv
  - outputs/full-eval/summary.md

Uses the rule-based deterministic model so the pipeline is fully reproducible
without GPU. Swap to the real UI2Code^N model by setting USE_REAL_MODEL=1.
"""

from __future__ import annotations

import asyncio
import csv
import json
import os
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LS = ROOT / "local-service"
sys.path.insert(0, str(LS))

from renderer import render_html_to_png, shutdown_renderer  # noqa: E402
from rule_based_model import RuleBasedModel  # noqa: E402


MOCKUPS = [
    ("m1_equipment_status", "Equipment Status Dashboard", "mockups/png/01-equipment-status.png", "simple"),
    ("m2_alarm_event", "Alarm & Event Monitor", "mockups/png/02-alarm-event.png", "simple"),
    ("m3_trend_monitor", "Real-Time Trend Monitor", "mockups/png/03-trend-monitor.png", "medium"),
    ("m4_operator_panel", "Operator Control Panel", "mockups/png/04-operator-panel.png", "medium"),
    ("m5_production_overview", "Production Line Overview", "mockups/png/05-production-overview.png", "medium"),
    ("m6_tank_synoptic", "Tank Farm Synoptic", "mockups/png/06-tank-synoptic.png", "medium-hard"),
    ("m7_energy_dashboard", "Energy Monitoring Dashboard", "mockups/png/07-energy-dashboard.png", "medium-hard"),
    ("m8_batch_recipe", "Batch Recipe Management", "mockups/png/08-batch-recipe.png", "hard"),
]

EDITS = [
    "Make the primary button secondary.",
    "Make the alarm block more prominent.",
    "Reduce padding for the trend card.",
]

TRIALS = 3
REFINE_ITERS = 2


def pick_model():
    if os.environ.get("USE_REAL_MODEL") == "1":
        try:
            from model_wrapper import UI2CodeModel  # type: ignore
            return UI2CodeModel()
        except Exception as exc:
            print(f"[warn] USE_REAL_MODEL=1 but wrapper unavailable: {exc}")
    return RuleBasedModel()


async def timed(awaitable):
    t0 = time.perf_counter()
    result = await awaitable
    return result, time.perf_counter() - t0


async def run_single(model, out_dir: Path, code_id: str, name: str, image_path: Path):
    out_dir.mkdir(parents=True, exist_ok=True)

    image_bytes = image_path.read_bytes()

    timings = {"generate": [], "refine_iter_1": [], "refine_iter_2": [], "edit": []}

    final_code_by_trial: list[str] = []

    for trial in range(1, TRIALS + 1):
        t0 = time.perf_counter()
        code = model.generate(image_bytes, frame_name=name, width=1280, height=720)
        timings["generate"].append(time.perf_counter() - t0)

        if trial == 1:
            (out_dir / "generate.html").write_text(code, encoding="utf-8")
            png, _ = await timed(render_html_to_png(code, 1280, 720))
            (out_dir / "generate.png").write_bytes(png)

        for i in range(1, REFINE_ITERS + 1):
            t0 = time.perf_counter()
            code = model.refine(image_bytes, code)
            timings[f"refine_iter_{i}"].append(time.perf_counter() - t0)
            if trial == 1:
                (out_dir / f"refine_iter{i}.html").write_text(code, encoding="utf-8")
                png, _ = await timed(render_html_to_png(code, 1280, 720))
                (out_dir / f"refine_iter{i}.png").write_bytes(png)

        final_code_by_trial.append(code)

    # One deterministic edit example per mockup, rendered once.
    instruction = EDITS[hash(code_id) % len(EDITS)]
    t0 = time.perf_counter()
    edited = model.edit(final_code_by_trial[0], instruction)
    timings["edit"].append(time.perf_counter() - t0)
    (out_dir / "edit.html").write_text(edited, encoding="utf-8")
    (out_dir / "edit.instruction.txt").write_text(instruction, encoding="utf-8")
    png, _ = await timed(render_html_to_png(edited, 1280, 720))
    (out_dir / "edit.png").write_bytes(png)

    return timings


def summarize(per_mockup: dict[str, dict]) -> dict:
    summary = {}
    for mid, timings in per_mockup.items():
        summary[mid] = {
            phase: {
                "mean_s": round(statistics.mean(values), 4),
                "min_s": round(min(values), 4),
                "max_s": round(max(values), 4),
                "trials": len(values),
            }
            for phase, values in timings.items()
            if values
        }
    return summary


async def main():
    try:
        model = pick_model()
        print(f"[info] model = {getattr(model, 'name', type(model).__name__)}")

        out_root = ROOT / "baseline-tests" / "outputs" / "full-eval"
        out_root.mkdir(parents=True, exist_ok=True)

        all_timings = {}

        started = datetime.now().isoformat(timespec="seconds")
        print(f"[info] started {started}")

        for mid, name, rel_path, complexity in MOCKUPS:
            image_path = ROOT / rel_path
            if not image_path.exists():
                print(f"[skip] missing image for {mid}: {image_path}")
                continue
            print(f"[run] {mid} ({complexity})")
            timings = await run_single(model, out_root / mid, mid, name, image_path)
            all_timings[mid] = {
                "frame_name": name,
                "complexity": complexity,
                **timings,
            }

        finished = datetime.now().isoformat(timespec="seconds")

        summary = summarize({k: {p: v for p, v in t.items() if isinstance(v, list)} for k, t in all_timings.items()})

        metrics_doc = {
            "model": getattr(model, "name", type(model).__name__),
            "trials_per_phase": TRIALS,
            "refine_iterations": REFINE_ITERS,
            "started_at": started,
            "finished_at": finished,
            "per_mockup": all_timings,
            "summary": summary,
        }

        metrics_path = out_root / "metrics.json"
        metrics_path.write_text(json.dumps(metrics_doc, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[done] metrics -> {metrics_path}")

        # CSV with a flat row per mockup × phase
        csv_path = out_root / "metrics.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["mockup", "complexity", "phase", "mean_s", "min_s", "max_s", "trials"])
            for mid, phases in summary.items():
                complexity = all_timings[mid]["complexity"]
                for phase, stat in phases.items():
                    w.writerow([mid, complexity, phase, stat["mean_s"], stat["min_s"], stat["max_s"], stat["trials"]])
        print(f"[done] csv -> {csv_path}")

        # Markdown summary (Russian, matches weekly reports)
        md = ["# Сводка по полному прогону экспериментов", ""]
        md.append(f"Модель: `{metrics_doc['model']}`  ")
        md.append(f"Триалов на фазу: {TRIALS}  ")
        md.append(f"Итераций уточнения: {REFINE_ITERS}  ")
        md.append(f"Старт: {started}  ")
        md.append(f"Финиш: {finished}  ")
        md.append("")
        md.append("## Средние тайминги (секунды)")
        md.append("")
        md.append("| Мокап | Сложность | Generate | Refine 1 | Refine 2 | Edit |")
        md.append("| --- | --- | ---: | ---: | ---: | ---: |")
        for mid, phases in summary.items():
            complexity = all_timings[mid]["complexity"]
            gen = phases.get("generate", {}).get("mean_s", 0)
            r1 = phases.get("refine_iter_1", {}).get("mean_s", 0)
            r2 = phases.get("refine_iter_2", {}).get("mean_s", 0)
            ed = phases.get("edit", {}).get("mean_s", 0)
            md.append(f"| {mid} | {complexity} | {gen} | {r1} | {r2} | {ed} |")

        md.append("")
        md.append("## Примечания")
        md.append(
            "В таблице — время только вызова модели (или её заместителя); рендер HTML→PNG через Playwright считается отдельно."
        )
        md.append(
            "В каждой папке `baseline-tests/outputs/full-eval/<mockup>/` лежит пара HTML+PNG для фаз `generate`, `refine_iter1`, `refine_iter2`, `edit`."
        )
        (out_root / "summary.md").write_text("\n".join(md), encoding="utf-8")
        print(f"[done] md -> {out_root / 'summary.md'}")
    finally:
        await shutdown_renderer()


if __name__ == "__main__":
    asyncio.run(main())
