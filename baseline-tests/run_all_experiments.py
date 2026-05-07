"""
Запускает все экспериментальные скрипты подряд в фиксированном порядке.

Порядок важен для воспроизводимости: сначала базовые тесты (неделя 3),
затем полная оценка (недели 6–8), правки и контекст (неделя 9),
сравнение baseline vs improved (неделя 9).

Использование:
  py baseline-tests/run_all_experiments.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / "baseline-tests"

STEPS = [
    ("run_baseline_tests.py", []),
    ("run_full_evaluation.py", []),
    ("run_edit_and_context.py", []),
    ("run_week9_comparison.py", []),
    ("build_report_screenshots.py", []),
]


def main() -> None:
    for script, extra in STEPS:
        path = BASELINE / script
        if not path.exists():
            print(f"[fail] missing {path}", file=sys.stderr)
            sys.exit(1)
        cmd = [sys.executable, str(path), *extra]
        print(f"[run] {' '.join(cmd)}")
        r = subprocess.run(cmd, cwd=str(ROOT))
        if r.returncode != 0:
            print(f"[fail] {script} exited with {r.returncode}", file=sys.stderr)
            sys.exit(r.returncode)
    print("[ok] all experiment steps finished")


if __name__ == "__main__":
    main()
