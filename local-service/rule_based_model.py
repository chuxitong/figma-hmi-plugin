"""
Rule-based deterministic model for end-to-end pipeline validation.

Purpose: when the real UI2Code^N model is not available (no GPU, offline env),
the project still needs reproducible end-to-end artefacts for weeks 6-9
deliverables. This module produces real, varied HTML for each mockup name
and performs real code transformations for refine/edit, so the full pipeline
(Figma plugin -> local service -> rendered PNG) yields meaningful outputs.

The interface matches the expected UI2CodeModel interface (generate/refine/edit),
so swapping to the real model is a drop-in replacement.
"""

from __future__ import annotations

import re
import time
from typing import Any, Optional


BASE_CSS = """
  :root {
    --bg: #1e1e2e;
    --panel: #2a2a3e;
    --panel-2: #32324a;
    --text: #e6e6ec;
    --muted: #a0a0b0;
    --ok: #4caf50;
    --warn: #ff9800;
    --err: #e53935;
    --info: #2196f3;
    --accent: #00bcd4;
    --border: #44445a;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: Inter, system-ui, Arial, sans-serif; padding: 24px; }
  h1 { font-size: 22px; margin-bottom: 12px; }
  h2 { font-size: 16px; margin: 4px 0 12px; color: var(--muted); font-weight: 500; }
  .grid { display: grid; gap: 16px; }
  .card { background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 16px; }
  .pill { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 12px; }
  .ok { background: rgba(76,175,80,.18); color: var(--ok); }
  .warn { background: rgba(255,152,0,.18); color: var(--warn); }
  .err { background: rgba(229,57,53,.20); color: var(--err); }
  .info { background: rgba(33,150,243,.18); color: var(--info); }
  button.btn { background: var(--accent); color: #001014; border: none; border-radius: 6px; padding: 8px 16px; font-weight: 600; cursor: pointer; }
  button.btn.secondary { background: transparent; color: var(--accent); border: 1px solid var(--accent); }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--border); }
  th { color: var(--muted); font-weight: 500; }
  .kpi { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
  .kpi .card { min-width: 160px; }
  .kpi .v { font-size: 22px; font-weight: 600; }
  .kpi .l { color: var(--muted); font-size: 12px; }
"""


def _html(body: str, title: str = "HMI") -> str:
    return (
        "<!DOCTYPE html>\n"
        f"<html lang=\"en\"><head><meta charset=\"utf-8\"><title>{title}</title>\n"
        f"<style>{BASE_CSS}</style></head><body>\n{body}\n</body></html>\n"
    )


def _equipment_status() -> str:
    cards = []
    items = [
        ("Pump A", "Running", "ok"),
        ("Pump B", "Warning", "warn"),
        ("Valve 01", "Normal", "ok"),
        ("Valve 02", "Fault", "err"),
        ("Mixer 1", "Running", "ok"),
        ("Mixer 2", "Idle", "info"),
    ]
    for name, state, kind in items:
        cards.append(
            f"<div class=\"card\"><div>{name}</div>"
            f"<div class=\"pill {kind}\" style=\"margin-top:8px;\">{state}</div></div>"
        )
    body = (
        "<h1>Equipment Status Dashboard</h1>"
        "<h2>Line 3 / Shift B</h2>"
        "<div class=\"grid\" style=\"grid-template-columns: repeat(3, 1fr);\">"
        + "".join(cards)
        + "</div>"
    )
    return _html(body, "Equipment Status")


def _alarm_event() -> str:
    rows = [
        ("12:04:21", "Tank level high", "warn"),
        ("12:03:10", "Temperature deviation", "err"),
        ("11:58:42", "Pump A vibration", "warn"),
        ("11:42:09", "Flow below setpoint", "info"),
        ("11:30:55", "Communication restored", "ok"),
    ]
    row_html = "".join(
        f"<tr><td>{t}</td><td>{d}</td>"
        f"<td><span class=\"pill {k}\">{k.upper()}</span></td>"
        f"<td><button class=\"btn secondary\">ACK</button></td></tr>"
        for t, d, k in rows
    )
    body = (
        "<h1>Alarm & Event Monitor</h1>"
        "<div class=\"kpi\">"
        "<div class=\"card\"><div class=\"v\">2</div><div class=\"l\">Critical</div></div>"
        "<div class=\"card\"><div class=\"v\">5</div><div class=\"l\">Warning</div></div>"
        "<div class=\"card\"><div class=\"v\">11</div><div class=\"l\">Info</div></div>"
        "</div>"
        "<div class=\"card\"><table>"
        "<thead><tr><th>Time</th><th>Description</th><th>Severity</th><th>Action</th></tr></thead>"
        f"<tbody>{row_html}</tbody></table></div>"
    )
    return _html(body, "Alarm Monitor")


def _trend_monitor() -> str:
    body = (
        "<h1>Real-Time Trend Monitor</h1>"
        "<div class=\"kpi\">"
        "<div class=\"card\"><div class=\"l\">Temperature</div><div class=\"v\">72.4 °C</div></div>"
        "<div class=\"card\"><div class=\"l\">Pressure</div><div class=\"v\">3.21 bar</div></div>"
        "<div class=\"card\"><div class=\"l\">Flow</div><div class=\"v\">184 L/min</div></div>"
        "</div>"
        "<div class=\"card\" style=\"height:280px; position:relative; overflow:hidden;\">"
        "<div style=\"position:absolute; inset:24px; border-left:1px solid var(--border); border-bottom:1px solid var(--border);\">"
        "<svg viewBox=\"0 0 400 160\" width=\"100%\" height=\"100%\" preserveAspectRatio=\"none\">"
        "<polyline fill=\"none\" stroke=\"#00bcd4\" stroke-width=\"2\" points=\"0,120 40,100 80,108 120,70 160,90 200,60 240,80 280,50 320,66 360,40 400,48\"/>"
        "<polyline fill=\"none\" stroke=\"#ff9800\" stroke-width=\"2\" points=\"0,140 40,130 80,124 120,118 160,112 200,108 240,100 280,96 320,94 360,88 400,84\"/>"
        "</svg></div></div>"
    )
    return _html(body, "Trend Monitor")


def _operator_panel() -> str:
    body = (
        "<h1>Operator Control Panel</h1>"
        "<div class=\"grid\" style=\"grid-template-columns: 1fr 1fr;\">"
        "<div class=\"card\"><h2>Actions</h2>"
        "<div style=\"display:flex; gap:10px;\">"
        "<button class=\"btn\" style=\"background: var(--ok);\">START</button>"
        "<button class=\"btn\" style=\"background: var(--err);\">STOP</button>"
        "<button class=\"btn secondary\">RESET</button>"
        "</div>"
        "<h2 style=\"margin-top:16px;\">Mode</h2>"
        "<select style=\"width:100%; background: var(--panel-2); color: var(--text); border: 1px solid var(--border); padding: 8px; border-radius: 6px;\">"
        "<option>Auto</option><option>Manual</option><option>Service</option>"
        "</select>"
        "</div>"
        "<div class=\"card\"><h2>Setpoints</h2>"
        "<label class=\"l\">Temperature</label>"
        "<input value=\"75.0\" style=\"width:100%; background: var(--panel-2); color: var(--text); border: 1px solid var(--border); padding: 8px; border-radius: 6px; margin-bottom: 8px;\">"
        "<label class=\"l\">Flow</label>"
        "<input value=\"180\" style=\"width:100%; background: var(--panel-2); color: var(--text); border: 1px solid var(--border); padding: 8px; border-radius: 6px;\">"
        "<h2 style=\"margin-top:16px;\">Live</h2>"
        "<div class=\"kpi\" style=\"margin-top:6px;\">"
        "<div class=\"card\"><div class=\"l\">Out T</div><div class=\"v\">74.6</div></div>"
        "<div class=\"card\"><div class=\"l\">Out Q</div><div class=\"v\">178</div></div>"
        "</div>"
        "</div></div>"
    )
    return _html(body, "Operator Panel")


def _production_overview() -> str:
    segments = "".join(
        f"<div class=\"card\" style=\"min-width:120px; text-align:center;\">"
        f"<div class=\"l\">{n}</div><div class=\"v\">{v}</div>"
        f"<div class=\"pill {k}\" style=\"margin-top:6px;\">{s}</div></div>"
        for n, v, s, k in [
            ("Filler", "98%", "OK", "ok"),
            ("Capper", "96%", "OK", "ok"),
            ("Labeler", "84%", "SLOW", "warn"),
            ("Packer", "92%", "OK", "ok"),
            ("Palletizer", "99%", "OK", "ok"),
        ]
    )
    body = (
        "<h1>Production Line Overview</h1>"
        "<div class=\"kpi\">"
        "<div class=\"card\"><div class=\"l\">OEE</div><div class=\"v\">82.5%</div></div>"
        "<div class=\"card\"><div class=\"l\">Units / h</div><div class=\"v\">12 480</div></div>"
        "<div class=\"card\"><div class=\"l\">Reject</div><div class=\"v\">0.6%</div></div>"
        "</div>"
        "<div style=\"display:flex; gap:12px; overflow:auto;\">" + segments + "</div>"
    )
    return _html(body, "Production Overview")


def _tank_synoptic() -> str:
    body = (
        "<h1>Tank Farm Synoptic</h1>"
        "<div class=\"grid\" style=\"grid-template-columns: repeat(4, 1fr);\">"
        + "".join(
            f"<div class=\"card\" style=\"text-align:center;\">"
            f"<div class=\"l\">{name}</div>"
            f"<div style=\"height:120px; width:64px; margin:8px auto; border:2px solid var(--border); border-radius:6px; position:relative; overflow:hidden;\">"
            f"<div style=\"position:absolute; bottom:0; left:0; right:0; height:{lvl}%; background:{color};\"></div>"
            f"</div>"
            f"<div class=\"v\">{lvl}%</div>"
            f"</div>"
            for name, lvl, color in [
                ("T-101", 72, "var(--ok)"),
                ("T-102", 41, "var(--info)"),
                ("T-103", 88, "var(--warn)"),
                ("T-104", 12, "var(--err)"),
            ]
        )
        + "</div>"
    )
    return _html(body, "Tank Synoptic")


def _energy_dashboard() -> str:
    bars = "".join(
        f"<div style=\"display:flex; align-items:center; gap:8px; margin:6px 0;\">"
        f"<div class=\"l\" style=\"width:120px;\">{z}</div>"
        f"<div style=\"flex:1; background: var(--panel-2); height:10px; border-radius:6px; overflow:hidden;\">"
        f"<div style=\"height:100%; width:{p}%; background: var(--accent);\"></div></div>"
        f"<div style=\"width:60px; text-align:right;\">{p}%</div></div>"
        for z, p in [("Zone A", 62), ("Zone B", 48), ("Zone C", 81), ("Zone D", 35)]
    )
    body = (
        "<h1>Energy Monitoring Dashboard</h1>"
        "<div class=\"kpi\">"
        "<div class=\"card\"><div class=\"l\">Total kWh</div><div class=\"v\">12 845</div></div>"
        "<div class=\"card\"><div class=\"l\">Peak</div><div class=\"v\">742 kW</div></div>"
        "<div class=\"card\"><div class=\"l\">Cost</div><div class=\"v\">€ 1 932</div></div>"
        "</div>"
        "<div class=\"card\">" + bars + "</div>"
    )
    return _html(body, "Energy Dashboard")


def _batch_recipe() -> str:
    steps = "".join(
        f"<tr><td>{i+1}</td><td>{name}</td><td>{dur} min</td>"
        f"<td><span class=\"pill {k}\">{status}</span></td></tr>"
        for i, (name, dur, status, k) in enumerate([
            ("Pre-heat", 10, "DONE", "ok"),
            ("Fill base", 8, "DONE", "ok"),
            ("Mix", 15, "ACTIVE", "info"),
            ("Hold", 20, "PENDING", "warn"),
            ("Cool down", 12, "PENDING", "warn"),
        ])
    )
    body = (
        "<h1>Batch Recipe Management</h1>"
        "<h2>Recipe R-204 • Lot 2026-017</h2>"
        "<div class=\"grid\" style=\"grid-template-columns: 2fr 1fr;\">"
        "<div class=\"card\"><table>"
        "<thead><tr><th>#</th><th>Step</th><th>Duration</th><th>Status</th></tr></thead>"
        f"<tbody>{steps}</tbody></table></div>"
        "<div class=\"card\"><h2>Parameters</h2>"
        "<div class=\"kpi\">"
        "<div class=\"card\"><div class=\"l\">Temp</div><div class=\"v\">65.4</div></div>"
        "<div class=\"card\"><div class=\"l\">pH</div><div class=\"v\">7.1</div></div>"
        "<div class=\"card\"><div class=\"l\">RPM</div><div class=\"v\">240</div></div>"
        "</div></div></div>"
    )
    return _html(body, "Batch Recipe")


_SCREEN_MAP = {
    "equipment": _equipment_status,
    "alarm": _alarm_event,
    "event": _alarm_event,
    "trend": _trend_monitor,
    "operator": _operator_panel,
    "production": _production_overview,
    "tank": _tank_synoptic,
    "energy": _energy_dashboard,
    "batch": _batch_recipe,
    "recipe": _batch_recipe,
}


def _pick_screen(name: str) -> str:
    low = name.lower()
    for key, factory in _SCREEN_MAP.items():
        if key in low:
            return factory()
    return _equipment_status()


class RuleBasedModel:
    """Drop-in replacement for UI2CodeModel using deterministic HTML generation."""

    name = "rule-based-v0.1"

    def __init__(self, seed: int = 0):
        self.seed = seed

    # --- Core interface ------------------------------------------------

    def generate(self, image_bytes: bytes, frame_name: str = "Untitled", **kwargs: Any) -> str:
        """Return an HMI HTML document keyed on the frame name."""
        time.sleep(0.05)
        return _pick_screen(frame_name)

    def refine(
        self,
        reference_bytes: bytes,
        current_code: str,
        rendered_bytes: Optional[bytes] = None,
        **kwargs: Any,
    ) -> str:
        """Apply real deterministic improvements to the code.

        - Tighten spacing and padding;
        - Ensure the visual hierarchy (h1/h2) is preserved;
        - Strengthen panel contrast.

        ``rendered_bytes`` is accepted for interface parity with the real
        UI2Code^N wrapper (which feeds the current rendered screenshot to
        the model). The rule-based replacement does not need the image to
        produce deterministic textual edits, but acknowledging the argument
        keeps the contract identical and lets the same client code drive
        both backends without conditionals.
        """
        time.sleep(0.05)
        code = current_code
        code = re.sub(r"padding:\s*24px", "padding: 20px", code)
        code = re.sub(r"margin:\s*8px", "margin: 12px", code)
        code = re.sub(r"--panel: #2a2a3e;", "--panel: #2d2d42;", code)
        code = re.sub(r"--border: #44445a;", "--border: #4d4d66;", code)
        return code

    def edit(
        self,
        current_code: str,
        instruction: str,
        css_hints: Optional[dict] = None,
        variables: Optional[dict] = None,
        **kwargs: Any,
    ) -> str:
        """Apply the instruction via simple, inspectable rules."""
        time.sleep(0.05)
        low = instruction.lower()
        code = current_code

        if "secondary" in low and "button" in low:
            code = code.replace(
                "<button class=\"btn\">",
                "<button class=\"btn secondary\">",
                1,
            )
        if "title" in low and ("large" in low or "bigger" in low or "increase" in low):
            code = code.replace("h1 { font-size: 22px", "h1 { font-size: 28px")
        if "alarm" in low and ("highlight" in low or "prominent" in low or "visible" in low):
            code = code.replace(
                ".err { background: rgba(229,57,53,.20);",
                ".err { background: rgba(229,57,53,.35); outline: 1px solid var(--err);",
            )
        if "padding" in low and "trend" in low and ("reduce" in low or "smaller" in low):
            code = code.replace("padding: 16px", "padding: 10px")
        if "border" in low and ("thicker" in low or "thick" in low):
            code = code.replace(
                ".card { background: var(--panel); border: 1px solid var(--border);",
                ".card { background: var(--panel); border: 2px solid var(--border);",
            )
        if ("dark" in low or "contrast" in low) and ("stronger" in low or "higher" in low or "increase" in low):
            code = code.replace("--bg: #1e1e2e;", "--bg: #141421;")

        if variables:
            bg = variables.get("--bg") or variables.get("--color-bg")
            if isinstance(bg, str) and bg.startswith("#"):
                code = re.sub(r"--bg:\s*#[0-9a-fA-F]+;", f"--bg: {bg};", code)
            accent = variables.get("--accent") or variables.get("--color-accent")
            if isinstance(accent, str) and accent.startswith("#"):
                code = re.sub(r"--accent:\s*#[0-9a-fA-F]+;", f"--accent: {accent};", code)

        return code
