"""
Проверка соответствия плана из Чжан Сычэн.docx: файлы, эксперименты, PNG.

Запуск из корня проекта:
  py baseline-tests/verify_deliverables.py

Код выхода 0 — всё найдено; 1 — есть пропуски.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def check_path(rel: str, desc: str) -> bool:
    p = ROOT / rel
    ok = p.is_file() or p.is_dir()
    print(f"{'OK' if ok else 'MISSING'} {desc}: {rel}")
    return ok


def main() -> int:
    failed = False

    def req(rel: str, desc: str) -> None:
        nonlocal failed
        if not check_path(rel, desc):
            failed = True

    # Неделя 1
    req("README.md", "неделя 1 — README")
    req("help/docs/figma-data-extraction.md", "неделя 1 — техзаписка по данным Figma")
    req("figma-plugin/manifest.json", "неделя 1 — манифест плагина")
    req("figma-plugin/dist/code.js", "неделя 5 — собранный code.js")
    req("REPOSITORY.txt", "неделя 1 — ссылка на репозиторий")

    # Неделя 2
    for name in [
        "01-equipment-status.png",
        "02-alarm-event.png",
        "03-trend-monitor.png",
        "04-operator-panel.png",
        "05-production-overview.png",
        "06-tank-synoptic.png",
        "07-energy-dashboard.png",
        "08-batch-recipe.png",
    ]:
        req(f"mockups/png/{name}", "неделя 2 — PNG мокапа")
    req("mockups/mockup-index.md", "неделя 2 — таблица мокапов")

    # Неделя 3
    for t in ("test1", "test2", "test3"):
        req(f"baseline-tests/outputs/{t}-generated.png", "неделя 3 — generate PNG")
    req("baseline-tests/outputs/test1-refined-iter2.png", "неделя 3 — refine PNG")
    req("baseline-tests/outputs/prompts.json", "неделя 3 — prompts.json")

    # Неделя 4
    req("local-service/app.py", "неделя 4 — HTTP-сервис")
    req("help/docs/api-reference.md", "неделя 4 — описание API")

    # Неделя 5
    req("local-service/renderer.py", "неделя 5 — рендер HTML→PNG")
    req("figma-plugin/src/ui.html", "неделя 5 — UI плагина")

    # Недели 6–8
    mids = [
        "m1_equipment_status",
        "m2_alarm_event",
        "m3_trend_monitor",
        "m4_operator_panel",
        "m5_production_overview",
        "m6_tank_synoptic",
        "m7_energy_dashboard",
        "m8_batch_recipe",
    ]
    for mid in mids:
        base = f"baseline-tests/outputs/full-eval/{mid}"
        for phase in ("generate", "refine_iter1", "refine_iter2", "edit"):
            req(f"{base}/{phase}.png", f"недели 6–8 — {mid} {phase}.png")
            req(f"{base}/{phase}.html", f"недели 6–8 — {mid} {phase}.html")

    req("baseline-tests/outputs/full-eval/metrics.json", "неделя 8 — metrics.json")
    req("baseline-tests/outputs/full-eval/metrics.csv", "неделя 8 — metrics.csv")
    req("baseline-tests/outputs/full-eval/summary.md", "неделя 8 — summary.md")

    # Неделя 7 — пять правок
    w7e = ROOT / "baseline-tests" / "outputs" / "week7-edits"
    edit_pngs = sorted(w7e.glob("edit_*.png")) if w7e.is_dir() else []
    if len(edit_pngs) < 5:
        print(f"MISSING неделя 7 — примеры правок PNG (ожидалось >=5, есть {len(edit_pngs)})", file=sys.stderr)
        failed = True
    else:
        print(f"OK неделя 7 — примеры правок PNG: {len(edit_pngs)} файлов")
    for cfg in ("A_image_only", "B_image_variables", "C_image_variables_css"):
        req(f"baseline-tests/outputs/week7-context/{cfg}.png", f"неделя 7 — контекст {cfg}")

    # Неделя 9
    for mid in mids:
        req(f"baseline-tests/outputs/week9-comparison/{mid}/baseline.png", f"неделя 9 — {mid} baseline.png")
        req(f"baseline-tests/outputs/week9-comparison/{mid}/improved.png", f"неделя 9 — {mid} improved.png")
    req("baseline-tests/outputs/week9-comparison/comparison.json", "неделя 9 — comparison.json")
    req("release-notes.md", "неделя 9 — заметки о заморозке")

    # Неделя 10 — текст пояснительной записки ведётся вне репозитория

    for w in range(1, 11):
        req(f"reports/week-{w}.md", f"отчёт неделя {w}")

    # Скриншоты для руководителя
    req("reports/screenshots/week05_plugin_panel.png", "скрин панели плагина")
    req("reports/screenshots/week05_pipeline_demo.gif", "GIF недели 5")
    req("reports/screenshots/week06_m1_reference_generate_refine2.png", "неделя 6 — до/после m1")

    if failed:
        print("\nЗапустите: py baseline-tests/run_all_experiments.py", file=sys.stderr)
        return 1

    metrics = ROOT / "baseline-tests" / "outputs" / "full-eval" / "metrics.json"
    if metrics.is_file():
        data = json.loads(metrics.read_text(encoding="utf-8"))
        n = len(data.get("per_mockup", {}))
        if n != 8:
            print(f"[warn] metrics.json: ожидалось 8 мокапов, найдено {n}", file=sys.stderr)
            return 1

    print("\n[ok] проверка пройдена: артефакты на месте.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
