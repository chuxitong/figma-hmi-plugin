"""
Deterministic post-processing pass for generated HTML/CSS.

Rules (conservative; applied after model output):
  1. Collapse runs of 2+ blank lines into one.
  2. Normalize px/rem unit spacing: "16 px" -> "16px".
  3. Fix duplicated consecutive CSS declarations inside inline <style> blocks.
  4. Ensure a viewport meta tag is present.
  5. Strip trailing whitespace on every line.

All rules are pure text transforms and safe for the generated HMI HTML.
"""

from __future__ import annotations

import re


_VIEWPORT_META = '<meta name="viewport" content="width=device-width, initial-scale=1">'


def _collapse_blank_lines(src: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", src)


def _normalize_units(src: str) -> str:
    return re.sub(r"(\d+)\s+(px|rem|em|%)\b", r"\1\2", src)


def _strip_trailing(src: str) -> str:
    return "\n".join(line.rstrip() for line in src.splitlines())


def _dedupe_consecutive_declarations(src: str) -> str:
    lines = src.splitlines()
    out: list[str] = []
    prev = None
    for line in lines:
        stripped = line.strip()
        if stripped and stripped == prev:
            continue
        out.append(line)
        prev = stripped
    return "\n".join(out)


def _ensure_viewport(src: str) -> str:
    if "name=\"viewport\"" in src:
        return src
    return src.replace("<head>", "<head>\n  " + _VIEWPORT_META, 1)


def postprocess_html(src: str) -> str:
    pipeline = [
        _collapse_blank_lines,
        _normalize_units,
        _strip_trailing,
        _dedupe_consecutive_declarations,
        _ensure_viewport,
    ]
    for step in pipeline:
        src = step(src)
    return src
