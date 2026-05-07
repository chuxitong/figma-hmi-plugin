"""Render the remaining thesis figures as crisp PNGs via Playwright.

Per the supervisor's latest feedback the six schematic figures (fig-1-1, 1-2,
2-1, 2-2, 2-3, 2-4) have been replaced by running text and are no longer
built. What remains are four synthetic figures rendered from hand-authored
HTML (fig-2-5, 2-8, 2-9, 2-10) and two mockup screenshots rasterised from
the layered SVG sources (fig-2-6, 2-7).

Following the academic caption convention of the sample thesis, the figure
title is NOT baked into the image: the caption appears only as a bold
Times New Roman 14 pt centred paragraph beneath the image in the final
Word document.

Usage:

    python _tools/build_thesis_figures.py
"""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright


REPO = Path(__file__).resolve().parent.parent
FIG_DIR = REPO / "thesis" / "figures"
SRC_DIR = FIG_DIR / "src"
MOCKUPS_SVG = REPO / "mockups" / "layered-svg" / "screens"

FIG_DIR.mkdir(parents=True, exist_ok=True)
SRC_DIR.mkdir(parents=True, exist_ok=True)


BASE_CSS = """
:root {
  --ink: #0f172a;
  --ink-muted: #475569;
  --line: #cbd5e1;
  --line-strong: #64748b;
  --bg: #ffffff;
  --panel: #f8fafc;
  --accent: #1e40af;
  --warn: #c2410c;
  --alarm: #b91c1c;
  --ok: #15803d;
  --muted: #64748b;
  --radius: 10px;
  font-size: 18px;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: var(--bg); color: var(--ink);
  font-family: "Segoe UI", Inter, -apple-system, BlinkMacSystemFont, Roboto, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased; font-smoothing: antialiased;
}
body { padding: 32px; }
.fig { background: var(--bg); }
.box { background: var(--panel); border: 1.5px solid var(--line-strong); border-radius: var(--radius);
  padding: 16px 18px; line-height: 1.35; color: var(--ink);
}
.box h3 { margin: 0 0 4px 0; font-size: 17px; font-weight: 700; letter-spacing: .1px; }
.box .muted { color: var(--ink-muted); font-size: 14px; }
.pill { display: inline-block; padding: 2px 10px; border-radius: 999px;
  font-size: 12px; font-weight: 600; letter-spacing: .2px; }
.pill.ok   { background: #dcfce7; color: #166534; }
.pill.warn { background: #ffedd5; color: #9a3412; }
.pill.alarm{ background: #fee2e2; color: #991b1b; }
.pill.off  { background: #e2e8f0; color: #475569; }
"""


def html_wrap(title: str, body: str, width: int, height: int) -> str:
    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
{BASE_CSS}
html, body {{ width: {width}px; min-height: {height}px; }}
body {{ padding: 0; }}
.fig {{ width: {width}px; height: {height}px; padding: 28px 36px; }}
</style>
</head>
<body>
<div class="fig">
{body}
</div>
</body>
</html>"""


# -------- individual figures (captions live in Word, not in the image) --------

def fig_2_5_layers(width=1500, height=760) -> str:
    layers = [
        ("Valve [Component Set]", "state = normal | warning | alarm | closed", True),
        ("  state = normal", "Variant", False),
        ("    body", "Vector", False),
        ("    outline", "Vector", False),
        ("    state-fill", "Vector  ·  color/ok", False),
        ("    state-badge", '"OK"  ·  Text', False),
        ("    state-shape", "Vector", False),
        ("    indicator", "Vector", False),
        ("    connector-left", "Vector", False),
        ("    connector-right", "Vector", False),
        ("    label", '"V-201"  ·  Text', False),
        ("  state = warning", "Variant", False),
        ("  state = alarm", "Variant", False),
        ("  state = closed", "Variant", False),
    ]
    rows = "".join(
        f'<div style="display:flex;gap:10px;padding:6px 10px;border-bottom:1px solid #e2e8f0;'
        f'{"background:#f1f5f9;font-weight:700;" if bold else ""}">'
        f'<div style="flex:1;white-space:pre;font-family:ui-monospace,Consolas,monospace;">{name}</div>'
        f'<div class="muted" style="font-size:13px;">{kind}</div></div>'
        for name, kind, bold in layers
    )
    body = f"""
    <div style="display:grid;grid-template-columns:1.1fr 1.4fr;gap:28px;align-items:start;">

      <div class="box" style="padding:16px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
            <b>Превью символа</b>
            <span class="pill ok">OK</span>
        </div>
        <div style="background:white;border:1px solid var(--line);border-radius:8px;padding:18px;
                    display:flex;justify-content:center;align-items:center;height:300px;">
          <svg width="320" height="230" viewBox="0 0 320 230" xmlns="http://www.w3.org/2000/svg">
            <rect x="10"  y="107" width="100" height="16" fill="#94a3b8"/>
            <rect x="210" y="107" width="100" height="16" fill="#94a3b8"/>
            <polygon points="110,70 160,115 110,160" fill="#15803d" stroke="#0f172a" stroke-width="2"/>
            <polygon points="210,70 160,115 210,160" fill="#15803d" stroke="#0f172a" stroke-width="2"/>
            <rect x="148" y="30" width="24" height="40" fill="#0f172a"/>
            <circle cx="160" cy="115" r="6" fill="#0f172a"/>
          </svg>
        </div>
        <div class="muted" style="margin-top:10px;font-size:13px;">
            body / outline / state-fill / indicator / connector-left / connector-right / label
        </div>
      </div>

      <div class="box" style="padding:0;overflow:hidden;">
        <div style="padding:10px 14px;background:#0f172a;color:#e2e8f0;font-weight:700;">
            Layers · Figma
        </div>
        {rows}
      </div>

    </div>
    """
    return html_wrap("fig-2-5", body, width, height)


def fig_2_8_plugin_panel(width=1400, height=820) -> str:
    body = """
    <div style="max-width:420px;margin:24px auto 0 auto;border:1px solid var(--line-strong);
                border-radius:12px;overflow:hidden;background:#ffffff;">

      <div style="padding:14px 16px;background:#0f172a;color:#e2e8f0;display:flex;
                  justify-content:space-between;align-items:center;">
        <div style="font-weight:700;">HMI → Code</div>
        <div style="font-size:12px;opacity:.7;">v0.7.0</div>
      </div>

      <div style="padding:16px;display:flex;flex-direction:column;gap:12px;">
        <label style="display:flex;align-items:center;gap:10px;">
            <input type="checkbox" checked style="transform:scale(1.2);"> Include design variables
        </label>
        <label style="display:flex;align-items:center;gap:10px;">
            <input type="checkbox" checked style="transform:scale(1.2);"> Include CSS hints
        </label>

        <button style="padding:12px;background:#1e40af;color:white;border:none;border-radius:8px;
                       font-size:15px;font-weight:600;">Generate Code</button>
        <button style="padding:12px;background:#334155;color:white;border:none;border-radius:8px;
                       font-size:15px;font-weight:600;">Make It Closer to the Mockup</button>

        <div>
          <div style="font-size:13px;color:var(--ink-muted);margin-bottom:4px;">Edit instruction</div>
          <textarea style="width:100%;min-height:64px;border:1px solid var(--line);border-radius:8px;
                           padding:8px;font-family:inherit;"
            >выделить блок аварий контуром</textarea>
        </div>
        <button style="padding:10px;background:#f1f5f9;color:#0f172a;border:1px solid var(--line-strong);
                       border-radius:8px;font-size:14px;font-weight:600;">Apply Edit</button>

        <div>
          <div style="font-size:13px;color:var(--ink-muted);margin-bottom:4px;">Generated HTML</div>
          <pre style="margin:0;padding:10px;background:#0f172a;color:#e2e8f0;border-radius:8px;
                      font-size:11px;max-height:140px;overflow:hidden;"><code>&lt;!doctype html&gt;
&lt;html lang="ru"&gt;
  &lt;head&gt;
    &lt;meta charset="utf-8"&gt;
    &lt;title&gt;Production Overview&lt;/title&gt;
    &lt;style&gt;…inline CSS…&lt;/style&gt;
  &lt;/head&gt;
  &lt;body&gt;
    &lt;header&gt;…&lt;/header&gt;
    &lt;main class="synoptic"&gt;…&lt;/main&gt;
  &lt;/body&gt;
&lt;/html&gt;</code></pre>
        </div>

        <div>
          <div style="font-size:13px;color:var(--ink-muted);margin-bottom:4px;">Preview</div>
          <div style="border:1px solid var(--line);border-radius:8px;background:#f8fafc;
                      padding:10px;text-align:center;color:var(--ink-muted);">
            [здесь отображается PNG-превью рендера]
          </div>
        </div>

        <div style="font-size:12px;color:var(--ink-muted);">
            Статус: <span style="color:#15803d;">OK · /generate за 14.3 с</span>
        </div>
      </div>
    </div>
    """
    return html_wrap("fig-2-8", body, width, height)


def fig_2_9_generate_result(width=1600, height=840) -> str:
    body = """
    <div style="display:grid;grid-template-columns:1fr 1.6fr;gap:24px;padding-top:12px;">

      <div class="box" style="padding:0;overflow:hidden;">
        <div style="padding:10px 14px;background:#0f172a;color:#e2e8f0;font-weight:700;">Generated HTML</div>
        <pre style="margin:0;padding:14px;font-size:11.5px;line-height:1.45;background:#0b1120;color:#e2e8f0;
                    height:720px;overflow:hidden;"><code>&lt;!doctype html&gt;
&lt;html lang="ru"&gt;
&lt;head&gt;
  &lt;meta charset="utf-8"&gt;
  &lt;meta name="viewport" content="width=1280"&gt;
  &lt;title&gt;Production Line A — Overview&lt;/title&gt;
  &lt;style&gt;
    body{font-family:"Inter",sans-serif;background:#f1f5f9;margin:0;color:#0f172a}
    header{background:#0f172a;color:#e2e8f0;padding:14px 24px;display:flex;
           justify-content:space-between;align-items:center}
    .synoptic{display:grid;grid-template-columns:2fr 1fr;gap:16px;padding:16px 24px}
    .kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;padding:0 24px 16px}
    .kpi{background:#fff;border-left:4px solid #1e40af;padding:12px 14px;border-radius:8px}
    .alarms{background:#fff;border-radius:8px;padding:12px 14px}
    .alarms .row{display:flex;justify-content:space-between;padding:8px 0;
                 border-bottom:1px solid #e2e8f0}
    .badge-alarm{background:#fee2e2;color:#991b1b;font-weight:700;padding:2px 8px;border-radius:4px}
    .badge-warn {background:#ffedd5;color:#9a3412;font-weight:700;padding:2px 8px;border-radius:4px}
  &lt;/style&gt;
&lt;/head&gt;
&lt;body&gt;
  &lt;header&gt;
    &lt;div&gt;&lt;b&gt;Production Line A — Overview&lt;/b&gt;&lt;/div&gt;
    &lt;div&gt;2026-04-19 14:32:07 MSK&lt;/div&gt;
  &lt;/header&gt;
  &lt;section class="synoptic"&gt;
    &lt;div class="process"&gt;
      &lt;!-- танки, насосы, клапаны, сепаратор, датчики, трубопроводы --&gt;
    &lt;/div&gt;
    &lt;div class="alarms"&gt;
      &lt;div class="row"&gt;&lt;span&gt;14:31&lt;/span&gt;&lt;span&gt;TT-301&lt;/span&gt;
        &lt;span class="badge-alarm"&gt;ALARM&lt;/span&gt;&lt;/div&gt;
      &lt;div class="row"&gt;&lt;span&gt;14:22&lt;/span&gt;&lt;span&gt;FT-401&lt;/span&gt;
        &lt;span class="badge-warn"&gt;WARN&lt;/span&gt;&lt;/div&gt;
    &lt;/div&gt;
  &lt;/section&gt;
  &lt;section class="kpis"&gt;
    &lt;div class="kpi"&gt;&lt;b&gt;OEE&lt;/b&gt;&lt;div&gt;82.5&lt;/div&gt;&lt;/div&gt;
    &lt;div class="kpi"&gt;&lt;b&gt;Units/h&lt;/b&gt;&lt;div&gt;12480&lt;/div&gt;&lt;/div&gt;
    …
  &lt;/section&gt;
&lt;/body&gt;
&lt;/html&gt;</code></pre>
      </div>

      <div class="box" style="padding:14px;">
        <div style="border:1px solid var(--line);border-radius:8px;overflow:hidden;background:white;">

          <div style="background:#0f172a;color:#e2e8f0;padding:10px 14px;display:flex;justify-content:space-between;">
            <div><b>Production Line A — Overview</b><div style="font-size:11px;opacity:.7;">Shift B · Operator: A. Petrov</div></div>
            <div style="font-size:12px;background:#1e293b;padding:4px 10px;border-radius:6px;">2026-04-19 14:32:07 MSK</div>
          </div>

          <div style="padding:14px;">
            <div style="display:grid;grid-template-columns:2fr 1fr;gap:12px;align-items:start;">
              <div class="box" style="padding:12px;background:white;">
                <div style="font-weight:700;margin-bottom:6px;">Process flow — Line A</div>
                <svg width="100%" viewBox="0 0 600 160">
                  <line x1="40" y1="80" x2="560" y2="80" stroke="#94a3b8" stroke-width="6"/>
                  <rect x="20" y="50" width="40" height="60" fill="#15803d"/>
                  <polygon points="150,60 180,80 150,100 120,80" fill="#15803d" stroke="#0f172a"/>
                  <polygon points="260,60 290,80 260,100 230,80" fill="#c2410c" stroke="#0f172a"/>
                  <polygon points="370,60 400,80 370,100 340,80" fill="#b91c1c" stroke="#0f172a"/>
                  <ellipse cx="470" cy="80" rx="40" ry="28" fill="#15803d" stroke="#0f172a"/>
                  <rect x="540" y="50" width="40" height="60" fill="#15803d"/>
                </svg>
              </div>
              <div class="box" style="padding:12px;background:white;">
                <div style="font-weight:700;margin-bottom:6px;">Active alarms · 3 of 14</div>
                <div style="display:flex;justify-content:space-between;font-size:13px;padding:4px 0;border-bottom:1px solid #e2e8f0;">
                    <span>14:31 &nbsp; TT-301</span><span class="pill alarm">ALARM</span>
                </div>
                <div style="display:flex;justify-content:space-between;font-size:13px;padding:4px 0;border-bottom:1px solid #e2e8f0;">
                    <span>14:28 &nbsp; PT-102</span><span class="pill alarm">ALARM</span>
                </div>
                <div style="display:flex;justify-content:space-between;font-size:13px;padding:4px 0;">
                    <span>14:22 &nbsp; FT-401</span><span class="pill warn">WARN</span>
                </div>
              </div>
            </div>

            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:12px;">
              <div class="box" style="padding:10px;background:white;border-left:4px solid #1e40af;">
                <div style="font-size:12px;color:var(--ink-muted);">OEE</div>
                <div style="font-size:20px;font-weight:800;">82.5</div>
              </div>
              <div class="box" style="padding:10px;background:white;border-left:4px solid #1e40af;">
                <div style="font-size:12px;color:var(--ink-muted);">Units / h</div>
                <div style="font-size:20px;font-weight:800;">12480</div>
              </div>
              <div class="box" style="padding:10px;background:white;border-left:4px solid #c2410c;">
                <div style="font-size:12px;color:var(--ink-muted);">Reject</div>
                <div style="font-size:20px;font-weight:800;">0.6</div>
              </div>
              <div class="box" style="padding:10px;background:white;border-left:4px solid #1e40af;">
                <div style="font-size:12px;color:var(--ink-muted);">Energy</div>
                <div style="font-size:20px;font-weight:800;">742</div>
              </div>
            </div>

          </div>
        </div>
      </div>

    </div>
    """
    return html_wrap("fig-2-9", body, width, height)


def fig_2_10_refine_compare(width=1800, height=620) -> str:
    def screen(title_caption: str, alarms_style: str, kpi_style: str) -> str:
        return f"""
        <div class="box" style="padding:12px;">
            <div style="font-weight:700;margin-bottom:8px;text-align:center;color:var(--ink-muted);font-size:13px;">
                {title_caption}
            </div>
            <div style="border:1px solid var(--line);border-radius:8px;overflow:hidden;background:white;">
                <div style="background:#0f172a;color:#e2e8f0;padding:8px 10px;font-size:12px;">
                    Production Line A — Overview
                </div>
                <div style="padding:10px;">
                    <svg width="100%" viewBox="0 0 400 100" style="background:white;border:1px solid var(--line);border-radius:6px;">
                        <line x1="20" y1="50" x2="380" y2="50" stroke="#94a3b8" stroke-width="4"/>
                        <rect x="10" y="30" width="20" height="40" fill="#15803d"/>
                        <polygon points="100,35 120,50 100,65 80,50" fill="#15803d" stroke="#0f172a"/>
                        <polygon points="180,35 200,50 180,65 160,50" fill="#c2410c" stroke="#0f172a"/>
                        <polygon points="260,35 280,50 260,65 240,50" fill="#b91c1c" stroke="#0f172a"/>
                        <ellipse cx="330" cy="50" rx="22" ry="16" fill="#15803d" stroke="#0f172a"/>
                    </svg>
                    <div style="margin-top:10px;">{alarms_style}</div>
                    <div style="margin-top:10px;{kpi_style}"></div>
                </div>
            </div>
        </div>
        """

    col1 = screen(
        "а) эталон Figma",
        '<div style="display:flex;gap:6px;font-size:11px;"><span class="pill alarm">ALARM</span><span class="pill alarm">ALARM</span><span class="pill warn">WARN</span></div>',
        'display:grid;grid-template-columns:repeat(4,1fr);gap:6px;height:40px;background:#eff6ff;border-radius:4px;'
    )
    col2 = screen(
        "б) Refine №1",
        '<div style="display:flex;gap:6px;font-size:11px;"><span class="pill alarm">ALARM</span><span class="pill warn">WARN</span></div>',
        'display:grid;grid-template-columns:repeat(3,1fr);gap:6px;height:40px;background:#f1f5f9;border-radius:4px;'
    )
    col3 = screen(
        "в) Refine №2",
        '<div style="display:flex;gap:6px;font-size:11px;"><span class="pill alarm">ALARM</span><span class="pill alarm">ALARM</span><span class="pill warn">WARN</span></div>',
        'display:grid;grid-template-columns:repeat(4,1fr);gap:6px;height:40px;background:#eff6ff;border-radius:4px;'
    )
    body = f"""
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px;padding-top:24px;">
        {col1}{col2}{col3}
    </div>
    """
    return html_wrap("fig-2-10", body, width, height)


FIGURES = [
    ("fig-2-5-plugin-panel.png",    fig_2_8_plugin_panel,    1400, 820),
    ("fig-2-6-generate-result.png", fig_2_9_generate_result, 1600, 840),
    ("fig-2-7-refine-compare.png",  fig_2_10_refine_compare, 1800, 620),
    ("fig-2-8-layers.png",          fig_2_5_layers,          1500, 760),
]

MOCKUP_FIGURES = [
    ("fig-2-9-production.png", "05-production-overview.svg", 1440, 900),
    ("fig-2-10-alarms.png",    "02-alarm-event.svg",         1440, 900),
]


def render_html(page, html: str, width: int, height: int, out_path: Path) -> None:
    page.set_viewport_size({"width": width, "height": height})
    page.set_content(html, wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")
    page.evaluate("document.fonts && document.fonts.ready")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(out_path), clip={"x": 0, "y": 0, "width": width, "height": height})


def render_svg_file(page, svg_path: Path, width: int, height: int, out_path: Path) -> None:
    svg_text = svg_path.read_text(encoding="utf-8")
    html = (
        "<!doctype html><html><head><meta charset='utf-8'><style>"
        "html,body{margin:0;padding:0;background:#ffffff;}"
        f"body{{width:{width}px;height:{height}px;}}"
        f"svg{{display:block;width:{width}px;height:{height}px;}}"
        "</style></head><body>" + svg_text + "</body></html>"
    )
    render_html(page, html, width, height, out_path)


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(device_scale_factor=2)
        page = ctx.new_page()

        for filename, builder, w, h in FIGURES:
            html = builder()
            src_name = filename.replace(".png", ".html")
            (SRC_DIR / src_name).write_text(html, encoding="utf-8")
            render_html(page, html, w, h, FIG_DIR / filename)
            print(f"wrote {filename}  ({w}x{h})")

        for filename, svg_name, w, h in MOCKUP_FIGURES:
            svg_path = MOCKUPS_SVG / svg_name
            if not svg_path.exists():
                print(f"WARN: missing {svg_path}, skipping {filename}")
                continue
            render_svg_file(page, svg_path, w, h, FIG_DIR / filename)
            print(f"wrote {filename}  ({w}x{h})  ← {svg_name}")

        browser.close()


if __name__ == "__main__":
    main()
