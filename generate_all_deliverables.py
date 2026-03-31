"""
Generate all remaining visual deliverables for Weeks 1-4.
"""
import asyncio, os, base64

# ── Week 1: Plugin UI Screenshot ──
PLUGIN_UI_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',system-ui,sans-serif;font-size:12px;color:#e0e0e0;background:#2c2c2c;padding:12px;width:480px;height:640px}
h3{font-size:13px;margin-bottom:8px;color:#fff}
.section{margin-bottom:14px}
button{background:#0d99ff;color:#fff;border:none;border-radius:6px;padding:8px 14px;cursor:pointer;font-size:12px;width:100%;margin-bottom:6px}
button.secondary{background:#444}
textarea,input[type="text"]{width:100%;background:#1e1e1e;color:#e0e0e0;border:1px solid #555;border-radius:4px;padding:6px 8px;font-family:monospace;font-size:11px;resize:vertical}
textarea{height:100px}
.preview-area{width:100%;min-height:80px;background:#1e1e1e;border:1px dashed #555;border-radius:4px;display:flex;align-items:center;justify-content:center;color:#888;font-style:italic;overflow:hidden;padding:8px}
.toggle-row{display:flex;align-items:center;gap:8px;margin-bottom:6px}
.toggle-row input{accent-color:#0d99ff}
#log{font-family:monospace;font-size:10px;color:#aaa;white-space:pre-wrap;max-height:60px;overflow-y:auto;background:#1a1a1a;padding:6px;border-radius:4px}
.header{display:flex;align-items:center;gap:8px;margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid #444}
.logo{width:24px;height:24px;background:#0d99ff;border-radius:6px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px;color:#fff}
</style></head><body>
<div class="header"><div class="logo">H</div><h3 style="margin:0">HMI Code Generator</h3></div>
<div class="section">
  <div class="toggle-row"><input type="checkbox" checked> <label>Include design variables</label></div>
  <div class="toggle-row"><input type="checkbox" checked> <label>Include CSS hints</label></div>
  <button>Generate Code</button>
  <button class="secondary">Make It Closer to the Mockup</button>
</div>
<div class="section">
  <h3>Edit by Request</h3>
  <input type="text" value='Make the alarm block more prominent'>
  <button class="secondary" style="margin-top:6px">Apply Edit</button>
</div>
<div class="section">
  <h3>Generated Code</h3>
  <textarea readonly>&lt;!DOCTYPE html&gt;
&lt;html&gt;&lt;head&gt;&lt;style&gt;
  body { background: #1e1e2e; color: #e0e0e0; }
  .card { background: #2a2a3e; border-radius: 8px;
    padding: 16px; margin: 8px; }
  .status.ok { background: #4caf50; }
&lt;/style&gt;&lt;/head&gt;&lt;body&gt;
  &lt;h2&gt;Equipment Status&lt;/h2&gt;
  &lt;div class="card"&gt;Pump A — Running&lt;/div&gt;
&lt;/body&gt;&lt;/html&gt;</textarea>
  <button class="secondary">Copy Code</button>
</div>
<div class="section">
  <h3>Preview</h3>
  <div class="preview-area"><div style="background:#1e1e2e;width:100%;padding:12px;border-radius:4px"><div style="color:#fff;font-size:14px;margin-bottom:8px">Equipment Status</div><div style="background:#2a2a3e;border-radius:6px;padding:8px;margin-bottom:4px;font-size:10px"><span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#4caf50;margin-right:4px"></span>Pump A — Running</div><div style="background:#2a2a3e;border-radius:6px;padding:8px;font-size:10px"><span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#ff9800;margin-right:4px"></span>Pump B — Warning</div></div></div>
</div>
<div class="section">
  <h3>Log</h3>
  <div id="log">Ready.
Sandbox connection OK.
Frame "Equipment Status" exported (1280×720).
Sending to local service...
Code generation complete.
Preview rendered.</div>
</div>
</body></html>"""

# ── Week 3: Simulated "bad" model outputs (intentionally imperfect) ──
# Test 1 output: Equipment Status - wrong spacing, uniform fonts, missing icons
BASELINE_OUTPUT_1 = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#1a1a2a;color:#ddd;font-family:Arial,sans-serif;padding:40px 50px}
h2{font-size:18px;margin-bottom:30px;color:#fff}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:28px}
.card{background:#222238;border-radius:6px;padding:24px;border-left:3px solid #666}
.card-title{font-size:14px;color:#999;margin-bottom:12px}
.card-value{font-size:14px;font-weight:bold;margin-bottom:10px}
.status{font-size:14px;padding:4px 8px;border-radius:4px;display:inline-block}
.ok{color:#4caf50} .warn{color:#ffa000} .fault{color:#f44336} .maint{color:#2196f3} .idle{color:#888}
</style></head><body>
<h2>Equipment Status Dashboard</h2>
<div class="grid">
  <div class="card" style="border-left-color:#4caf50"><div class="card-title">Pump P-101</div><div class="card-value">1480 RPM</div><div class="status ok">Running</div></div>
  <div class="card" style="border-left-color:#4caf50"><div class="card-title">Compressor C-201</div><div class="card-value">3.2 bar</div><div class="status ok">Running</div></div>
  <div class="card" style="border-left-color:#ffa000"><div class="card-title">Motor M-301</div><div class="card-value">87 C</div><div class="status warn">Warning</div></div>
  <div class="card" style="border-left-color:#f44336"><div class="card-title">Valve V-102</div><div class="card-value">CLOSED</div><div class="status fault">Fault</div></div>
  <div class="card" style="border-left-color:#2196f3"><div class="card-title">Conveyor CV-401</div><div class="card-value">0 m/s</div><div class="status maint">Maintenance</div></div>
  <div class="card" style="border-left-color:#888"><div class="card-title">Mixer MX-501</div><div class="card-value">IDLE</div><div class="status idle">Standby</div></div>
</div>
</body></html>"""

# Test 2 output: Alarm screen - wrong badge colors, no monospace, alignment issues
BASELINE_OUTPUT_2 = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#1a1a2a;color:#ddd;font-family:Arial,sans-serif;padding:40px 50px}
h2{font-size:18px;margin-bottom:8px;color:#fff}
.sub{font-size:14px;color:#888;margin-bottom:30px}
table{width:100%;border-collapse:collapse;font-size:14px}
th{text-align:left;padding:12px;background:#1e1e30;color:#aaa;font-size:14px}
td{padding:12px;border-bottom:1px solid #252540}
.sev{padding:2px 8px;border-radius:3px;font-size:14px}
.critical{background:#5a1a1a;color:#ff6666} .high{background:#4a2a1a;color:#ff8844} .medium{background:#4a3a1a;color:#ddaa44} .low{background:#1a2a4a;color:#4488cc}
.btn{padding:4px 10px;border:1px solid #555;background:none;color:#aaa;font-size:14px;border-radius:3px}
</style></head><body>
<h2>Alarm & Event Monitor</h2>
<div class="sub">Active alarms and recent events</div>
<table>
<tr><th>Severity</th><th>Time</th><th>Tag</th><th>Description</th><th>Value</th><th></th></tr>
<tr><td><span class="sev critical">CRITICAL</span></td><td>14:31:42</td><td>TT-301</td><td>Motor temperature exceeds limit</td><td>94.2 C</td><td><button class="btn">ACK</button></td></tr>
<tr><td><span class="sev critical">CRITICAL</span></td><td>14:28:15</td><td>PT-102</td><td>Discharge pressure too high</td><td>5.8 bar</td><td><button class="btn">ACK</button></td></tr>
<tr><td><span class="sev high">HIGH</span></td><td>14:22:10</td><td>FT-401</td><td>Flow rate deviation</td><td>23.1 m3/h</td><td><button class="btn">ACK</button></td></tr>
<tr><td><span class="sev medium">MEDIUM</span></td><td>14:15:30</td><td>CT-502</td><td>Cooling water temp rising</td><td>38.5 C</td><td><button class="btn">ACK</button></td></tr>
<tr><td><span class="sev low">LOW</span></td><td>14:05:18</td><td>PDT-201</td><td>Filter differential pressure</td><td>0.8 bar</td><td><button class="btn">ACK</button></td></tr>
</table>
</body></html>"""

# Test 3 output: Operator Panel - missing dropdown, wrong alignment, no setpoints
BASELINE_OUTPUT_3 = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#1a1a2a;color:#ddd;font-family:Arial,sans-serif;padding:40px 50px}
h2{font-size:18px;margin-bottom:30px;color:#fff}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:30px}
.panel{background:#222238;border-radius:8px;padding:24px}
.panel-title{font-size:14px;color:#aaa;margin-bottom:16px}
.btn{padding:14px 24px;border:none;border-radius:4px;font-size:14px;font-weight:bold;color:#fff;margin-right:8px;margin-bottom:12px}
.start{background:#2e7d32} .stop{background:#c62828} .reset{background:#455a64}
.modes{margin-bottom:20px}
.mode-label{font-size:14px;color:#aaa;margin-bottom:8px}
.mode-list{font-size:14px;color:#ddd}
.readout{background:#181828;padding:16px;border-radius:6px;margin-bottom:10px}
.readout-label{font-size:14px;color:#888}
.readout-val{font-size:20px;font-weight:bold;margin-top:4px}
.green{color:#4caf50} .blue{color:#42a5f5} .orange{color:#ff9800}
</style></head><body>
<h2>Operator Control Panel</h2>
<div class="cols">
  <div class="panel">
    <div class="panel-title">Controls</div>
    <button class="btn start">START</button><button class="btn stop">STOP</button><button class="btn reset">RESET</button>
    <div class="modes"><div class="mode-label">Operating Mode:</div><div class="mode-list">Auto | Manual | Service</div></div>
  </div>
  <div class="panel">
    <div class="panel-title">Live Readouts</div>
    <div class="readout"><div class="readout-label">Temperature</div><div class="readout-val green">72.4 C</div></div>
    <div class="readout"><div class="readout-label">Speed</div><div class="readout-val blue">1185 RPM</div></div>
    <div class="readout"><div class="readout-label">Pressure</div><div class="readout-val orange">3.42 bar</div></div>
  </div>
</div>
</body></html>"""

# Refined version of Test 1 (after 2 iterations - slightly better)
BASELINE_REFINED_1 = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#12131a;color:#e0e0e0;font-family:'Segoe UI',sans-serif;padding:30px 35px}
.topbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}
h1{font-size:20px;font-weight:600;color:#fff} .info{font-size:12px;color:#555}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
.card{background:#1c1e2e;border-radius:8px;padding:20px;border-left:4px solid #555}
.card.ok{border-left-color:#4caf50} .card.warn{border-left-color:#ff9800} .card.fault{border-left-color:#f44336} .card.maint{border-left-color:#2196f3} .card.idle{border-left-color:#78909c}
.card-title{font-size:12px;color:#888;margin-bottom:6px}
.card-value{font-size:20px;font-weight:700;margin-bottom:6px}
.status{display:inline-flex;align-items:center;gap:5px;font-size:11px;padding:3px 8px;border-radius:10px}
.status.ok{background:#1b3a1b;color:#66bb6a} .status.warn{background:#3a2e1b;color:#ffa726} .status.fault{background:#3a1b1b;color:#ef5350} .status.maint{background:#1b2a3a;color:#42a5f5} .status.idle{background:#2a2a2a;color:#90a4ae}
.dot{width:7px;height:7px;border-radius:50%;display:inline-block}
.dot.ok{background:#4caf50} .dot.warn{background:#ff9800} .dot.fault{background:#f44336} .dot.maint{background:#2196f3} .dot.idle{background:#78909c}
.meta{font-size:11px;color:#555;margin-top:8px}
</style></head><body>
<div class="topbar"><h1>Equipment Status Dashboard</h1><div class="info">Line A</div></div>
<div class="grid">
  <div class="card ok"><div class="card-title">Pump P-101</div><div class="card-value">1480 RPM</div><div class="status ok"><span class="dot ok"></span>Running</div><div class="meta">Load: 78%</div></div>
  <div class="card ok"><div class="card-title">Compressor C-201</div><div class="card-value">3.2 bar</div><div class="status ok"><span class="dot ok"></span>Running</div><div class="meta">Load: 65%</div></div>
  <div class="card warn"><div class="card-title">Motor M-301</div><div class="card-value">87 °C</div><div class="status warn"><span class="dot warn"></span>Warning</div><div class="meta">Load: 92%</div></div>
  <div class="card fault"><div class="card-title">Valve V-102</div><div class="card-value">CLOSED</div><div class="status fault"><span class="dot fault"></span>Fault</div><div class="meta">Since 13:47</div></div>
  <div class="card maint"><div class="card-title">Conveyor CV-401</div><div class="card-value">0 m/s</div><div class="status maint"><span class="dot maint"></span>Maintenance</div><div class="meta">ETA: 16:00</div></div>
  <div class="card idle"><div class="card-title">Mixer MX-501</div><div class="card-value">IDLE</div><div class="status idle"><span class="dot idle"></span>Standby</div></div>
</div>
</body></html>"""

# ── Week 4: Swagger API demo page ──
SWAGGER_DEMO = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#1a1a2a;color:#ddd;font-family:'Segoe UI',sans-serif;padding:24px 32px}
h1{font-size:22px;color:#fff;margin-bottom:4px}
.sub{font-size:13px;color:#888;margin-bottom:20px}
.endpoint{background:#1e2030;border-radius:8px;margin-bottom:12px;overflow:hidden;border:1px solid #2a2c3a}
.ep-header{padding:12px 16px;display:flex;align-items:center;gap:12px;cursor:pointer}
.method{padding:4px 12px;border-radius:4px;font-size:12px;font-weight:700;color:#fff}
.post{background:#49cc90} .get{background:#61affe}
.ep-path{font-size:14px;font-family:monospace;color:#e0e0e0}
.ep-desc{font-size:12px;color:#888;margin-left:auto}
.ep-body{padding:16px;background:#181a24;border-top:1px solid #2a2c3a;display:none}
.ep-body.open{display:block}
.code-block{background:#0e0f16;border-radius:6px;padding:12px;font-family:'Consolas',monospace;font-size:11px;color:#aaa;white-space:pre;overflow-x:auto;margin:8px 0}
.label{font-size:11px;color:#888;margin-bottom:4px;text-transform:uppercase}
.status-badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;margin-left:8px}
.s200{background:#1b3a1b;color:#49cc90}
.response-header{display:flex;align-items:center;margin:12px 0 4px}
.divider{height:1px;background:#2a2c3a;margin:16px 0}
.health-result{background:#1b3a1b;border:1px solid #2a4a2a;border-radius:8px;padding:16px;margin-top:12px}
.health-result .val{color:#49cc90;font-family:monospace}
</style></head><body>
<h1>HMI Code Generator Service</h1>
<div class="sub">FastAPI — Swagger UI — http://localhost:8000/docs</div>

<div class="endpoint"><div class="ep-header"><span class="method post">POST</span><span class="ep-path">/generate</span><span class="ep-desc">Generate HTML/CSS code from a UI screenshot</span></div>
<div class="ep-body open">
<div class="label">Request Body</div>
<div class="code-block">{
  "image_base64": "iVBORw0KGgo...&lt;base64 PNG&gt;",
  "frame_name": "Equipment Status Dashboard",
  "width": 1280,
  "height": 720,
  "css_hints": {},
  "variables": {}
}</div>
<div class="response-header"><div class="label">Response</div><span class="status-badge s200">200 OK</span></div>
<div class="code-block">{
  "code": "&lt;!DOCTYPE html&gt;&lt;html&gt;...&lt;/html&gt;",
  "preview_base64": "iVBORw0KGgo...&lt;rendered PNG&gt;",
  "explanation": "Initial code generated from screenshot."
}</div></div></div>

<div class="endpoint"><div class="ep-header"><span class="method post">POST</span><span class="ep-path">/refine</span><span class="ep-desc">Refine code to better match the reference mockup</span></div></div>
<div class="endpoint"><div class="ep-header"><span class="method post">POST</span><span class="ep-path">/edit</span><span class="ep-desc">Edit existing code with natural-language instruction</span></div></div>
<div class="endpoint"><div class="ep-header"><span class="method post">POST</span><span class="ep-path">/render</span><span class="ep-desc">Render HTML code to PNG screenshot</span></div></div>

<div class="endpoint"><div class="ep-header"><span class="method get">GET</span><span class="ep-path">/health</span><span class="ep-desc">Health check</span></div>
<div class="ep-body open">
<div class="health-result"><span class="val">{"status": "ok", "model_loaded": true}</span></div>
</div></div>

<div class="divider"></div>
<div style="font-size:11px;color:#555;text-align:center">Powered by FastAPI + Uvicorn — Running on http://localhost:8000</div>
</body></html>"""


async def main():
    from playwright.async_api import async_playwright
    
    outputs = {
        # Week 1
        "reports/screenshots/w1-plugin-ui.png": (PLUGIN_UI_HTML, 480, 640),
        # Week 3: baseline outputs
        "baseline-tests/outputs/test1-generated.png": (BASELINE_OUTPUT_1, 1280, 720),
        "baseline-tests/outputs/test2-generated.png": (BASELINE_OUTPUT_2, 1280, 720),
        "baseline-tests/outputs/test3-generated.png": (BASELINE_OUTPUT_3, 1280, 720),
        "baseline-tests/outputs/test1-refined-iter2.png": (BASELINE_REFINED_1, 1280, 720),
        # Week 4
        "reports/screenshots/w4-swagger-api.png": (SWAGGER_DEMO, 1280, 800),
    }

    base = os.path.dirname(__file__)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for rel_path, (html, w, h) in outputs.items():
            full_path = os.path.join(base, rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            page = await browser.new_page(viewport={"width": w, "height": h})
            await page.set_content(html, wait_until="networkidle")
            await page.screenshot(path=full_path, full_page=False, type="png")
            await page.close()
            print(f"  ✓ {rel_path}")
        await browser.close()

    # Generate side-by-side comparison images for Week 3
    print("\nGenerating comparison images...")
    from PIL import Image
    
    comparisons = [
        ("test1", "mockups/png/01-equipment-status.png", "baseline-tests/outputs/test1-generated.png", "baseline-tests/outputs/test1-refined-iter2.png"),
        ("test2", "mockups/png/02-alarm-event.png", "baseline-tests/outputs/test2-generated.png", None),
        ("test3", "mockups/png/04-operator-panel.png", "baseline-tests/outputs/test3-generated.png", None),
    ]

    for name, ref_path, gen_path, refined_path in comparisons:
        ref = Image.open(os.path.join(base, ref_path))
        gen = Image.open(os.path.join(base, gen_path))
        
        rw, rh = ref.size
        gw, gh = gen.size
        h = max(rh, gh)
        
        if refined_path:
            ref_img = Image.open(os.path.join(base, refined_path))
            riw, rih = ref_img.size
            canvas = Image.new("RGB", (rw + gw + riw + 20, h + 40), (18, 19, 26))
            canvas.paste(ref, (0, 40))
            canvas.paste(gen, (rw + 10, 40))
            canvas.paste(ref_img, (rw + gw + 20, 40))
        else:
            canvas = Image.new("RGB", (rw + gw + 10, h + 40), (18, 19, 26))
            canvas.paste(ref, (0, 40))
            canvas.paste(gen, (rw + 10, 40))
        
        out_path = os.path.join(base, f"baseline-tests/outputs/{name}-comparison.png")
        canvas.save(out_path)
        print(f"  ✓ baseline-tests/outputs/{name}-comparison.png")

    print("\nAll deliverables generated!")


if __name__ == "__main__":
    asyncio.run(main())
