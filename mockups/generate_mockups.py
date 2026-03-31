"""
Generate 8 industrial HMI mockup PNGs using Playwright.
Run: .venv/Scripts/python.exe mockups/generate_mockups.py
"""
import asyncio, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'local-service'))

MOCKUPS = {}

# ── 1. Equipment Status Dashboard (Simple) ──
MOCKUPS["01-equipment-status"] = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#12131a;color:#e0e0e0;font-family:'Segoe UI',system-ui,sans-serif;padding:28px 32px}
h1{font-size:20px;font-weight:600;margin-bottom:20px;color:#fff}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
.card{background:#1c1e2e;border-radius:10px;padding:20px;border-left:4px solid #555}
.card.ok{border-left-color:#4caf50} .card.warn{border-left-color:#ff9800} .card.fault{border-left-color:#f44336} .card.maint{border-left-color:#2196f3} .card.idle{border-left-color:#78909c}
.card-title{font-size:13px;color:#888;margin-bottom:8px}
.card-value{font-size:22px;font-weight:700;margin-bottom:6px}
.status{display:inline-flex;align-items:center;gap:6px;font-size:12px;padding:3px 10px;border-radius:12px}
.status.ok{background:#1b3a1b;color:#66bb6a} .status.warn{background:#3a2e1b;color:#ffa726} .status.fault{background:#3a1b1b;color:#ef5350} .status.maint{background:#1b2a3a;color:#42a5f5} .status.idle{background:#2a2a2a;color:#90a4ae}
.dot{width:8px;height:8px;border-radius:50%;display:inline-block}
.dot.ok{background:#4caf50} .dot.warn{background:#ff9800} .dot.fault{background:#f44336} .dot.maint{background:#2196f3} .dot.idle{background:#78909c}
.meta{font-size:11px;color:#666;margin-top:10px}
.topbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}
.topbar h1{margin:0} .topbar .info{font-size:12px;color:#555}
</style></head><body>
<div class="topbar"><h1>Equipment Status Dashboard</h1><div class="info">Line A &bull; Last update: 14:32:07</div></div>
<div class="grid">
  <div class="card ok"><div class="card-title">Pump P-101</div><div class="card-value">1480 RPM</div><div class="status ok"><span class="dot ok"></span>Running</div><div class="meta">Runtime: 2,341 h &bull; Load: 78%</div></div>
  <div class="card ok"><div class="card-title">Compressor C-201</div><div class="card-value">3.2 bar</div><div class="status ok"><span class="dot ok"></span>Running</div><div class="meta">Runtime: 1,102 h &bull; Load: 65%</div></div>
  <div class="card warn"><div class="card-title">Motor M-301</div><div class="card-value">87 °C</div><div class="status warn"><span class="dot warn"></span>Warning</div><div class="meta">Temp high &bull; Load: 92%</div></div>
  <div class="card fault"><div class="card-title">Valve V-102</div><div class="card-value">CLOSED</div><div class="status fault"><span class="dot fault"></span>Fault</div><div class="meta">Actuator error &bull; Since 13:47</div></div>
  <div class="card maint"><div class="card-title">Conveyor CV-401</div><div class="card-value">0 m/s</div><div class="status maint"><span class="dot maint"></span>Maintenance</div><div class="meta">Scheduled &bull; ETA: 16:00</div></div>
  <div class="card idle"><div class="card-title">Mixer MX-501</div><div class="card-value">IDLE</div><div class="status idle"><span class="dot idle"></span>Standby</div><div class="meta">Ready &bull; Last run: 11:20</div></div>
</div>
</body></html>"""

# ── 2. Alarm & Event Screen (Simple) ──
MOCKUPS["02-alarm-event"] = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#12131a;color:#e0e0e0;font-family:'Segoe UI',system-ui,sans-serif;padding:28px 32px}
h1{font-size:20px;font-weight:600;margin-bottom:6px;color:#fff}
.sub{font-size:12px;color:#666;margin-bottom:20px}
.tabs{display:flex;gap:4px;margin-bottom:16px}
.tab{padding:7px 18px;border-radius:6px;font-size:12px;cursor:pointer;background:#1c1e2e;color:#888}
.tab.active{background:#2a3a5c;color:#5b9cf6}
.badge{display:inline-block;min-width:18px;text-align:center;padding:0 6px;border-radius:10px;font-size:10px;margin-left:6px}
.badge.red{background:#3a1b1b;color:#ef5350} .badge.yel{background:#3a2e1b;color:#ffa726}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;padding:10px 12px;background:#181a24;color:#888;font-weight:500;border-bottom:1px solid #2a2c3a}
td{padding:10px 12px;border-bottom:1px solid #1e2030}
tr:hover{background:#1a1c2a}
.sev{padding:3px 10px;border-radius:4px;font-size:11px;font-weight:600;text-transform:uppercase}
.sev.critical{background:#3a1b1b;color:#ef5350} .sev.high{background:#3a2618;color:#ff7043} .sev.medium{background:#3a2e1b;color:#ffa726} .sev.low{background:#1b2a3a;color:#42a5f5}
.ts{font-family:'Consolas',monospace;color:#78909c;font-size:12px}
.btn{padding:4px 12px;border-radius:4px;border:1px solid #444;background:transparent;color:#aaa;font-size:11px;cursor:pointer}
.btn:hover{background:#2a2c3a}
.summary{display:flex;gap:16px;margin-bottom:16px}
.summary-item{background:#1c1e2e;padding:12px 20px;border-radius:8px;text-align:center;min-width:100px}
.summary-item .num{font-size:24px;font-weight:700} .summary-item .label{font-size:11px;color:#888;margin-top:2px}
.num.red{color:#ef5350} .num.orange{color:#ff7043} .num.yellow{color:#ffa726} .num.blue{color:#42a5f5}
</style></head><body>
<h1>Alarm & Event Monitor</h1>
<div class="sub">Active alarms and recent events &bull; Zone: Plant North</div>
<div class="summary">
  <div class="summary-item"><div class="num red">3</div><div class="label">Critical</div></div>
  <div class="summary-item"><div class="num orange">5</div><div class="label">High</div></div>
  <div class="summary-item"><div class="num yellow">12</div><div class="label">Medium</div></div>
  <div class="summary-item"><div class="num blue">8</div><div class="label">Low</div></div>
</div>
<div class="tabs"><div class="tab active">Active Alarms <span class="badge red">20</span></div><div class="tab">Acknowledged</div><div class="tab">History</div></div>
<table>
<tr><th>Severity</th><th>Timestamp</th><th>Tag</th><th>Description</th><th>Value</th><th>Action</th></tr>
<tr><td><span class="sev critical">Critical</span></td><td class="ts">14:31:42</td><td>TT-301</td><td>Motor temperature exceeds limit</td><td>94.2 °C</td><td><button class="btn">ACK</button></td></tr>
<tr><td><span class="sev critical">Critical</span></td><td class="ts">14:28:15</td><td>PT-102</td><td>Discharge pressure too high</td><td>5.8 bar</td><td><button class="btn">ACK</button></td></tr>
<tr><td><span class="sev critical">Critical</span></td><td class="ts">14:25:03</td><td>LS-201</td><td>Tank level critical high</td><td>98.1%</td><td><button class="btn">ACK</button></td></tr>
<tr><td><span class="sev high">High</span></td><td class="ts">14:22:10</td><td>FT-401</td><td>Flow rate deviation &gt; 15%</td><td>23.1 m³/h</td><td><button class="btn">ACK</button></td></tr>
<tr><td><span class="sev high">High</span></td><td class="ts">14:18:55</td><td>VB-103</td><td>Vibration level elevated</td><td>4.2 mm/s</td><td><button class="btn">ACK</button></td></tr>
<tr><td><span class="sev medium">Medium</span></td><td class="ts">14:15:30</td><td>CT-502</td><td>Cooling water temp rising</td><td>38.5 °C</td><td><button class="btn">ACK</button></td></tr>
<tr><td><span class="sev medium">Medium</span></td><td class="ts">14:10:22</td><td>LT-302</td><td>Buffer tank level low</td><td>22.3%</td><td><button class="btn">ACK</button></td></tr>
<tr><td><span class="sev low">Low</span></td><td class="ts">14:05:18</td><td>PDT-201</td><td>Filter differential pressure</td><td>0.8 bar</td><td><button class="btn">ACK</button></td></tr>
</table>
</body></html>"""

# ── 3. Real-Time Trend Monitor (Medium) ──
MOCKUPS["03-trend-monitor"] = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#12131a;color:#e0e0e0;font-family:'Segoe UI',system-ui,sans-serif;padding:28px 32px}
.topbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}
h1{font-size:20px;font-weight:600;color:#fff}
.time-sel{display:flex;gap:4px}
.time-btn{padding:5px 14px;border-radius:5px;font-size:11px;background:#1c1e2e;color:#888;border:none;cursor:pointer}
.time-btn.active{background:#2a3a5c;color:#5b9cf6}
.charts{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px}
.chart-box{background:#1c1e2e;border-radius:10px;padding:18px;position:relative;height:220px}
.chart-title{font-size:13px;color:#888;margin-bottom:4px}
.chart-val{font-size:28px;font-weight:700;margin-bottom:12px}
.chart-val .unit{font-size:14px;color:#666;font-weight:400}
.chart-area{position:absolute;bottom:16px;left:18px;right:18px;height:110px;border-bottom:1px solid #2a2c3a;border-left:1px solid #2a2c3a}
.line{position:absolute;bottom:0;left:0;right:0;height:100%}
svg{width:100%;height:100%}
.axis-label{position:absolute;font-size:9px;color:#555}
.ax-y1{left:-2px;top:0} .ax-y2{left:-2px;top:50%} .ax-y3{left:-2px;bottom:-2px}
.ax-x1{bottom:-14px;left:0} .ax-x2{bottom:-14px;left:50%} .ax-x3{bottom:-14px;right:0}
.live{display:flex;gap:20px;margin-bottom:16px}
.live-item{background:#1c1e2e;border-radius:10px;padding:14px 20px;flex:1;display:flex;justify-content:space-between;align-items:center}
.live-label{font-size:12px;color:#888} .live-val{font-size:20px;font-weight:700} .live-unit{font-size:12px;color:#666}
.green{color:#4caf50} .blue{color:#42a5f5} .orange{color:#ff9800} .purple{color:#ab47bc}
.legend{display:flex;gap:20px;justify-content:center;margin-top:12px}
.legend-item{display:flex;align-items:center;gap:6px;font-size:11px;color:#888}
.legend-dot{width:10px;height:10px;border-radius:50%}
</style></head><body>
<div class="topbar"><h1>Real-Time Trend Monitor</h1>
<div class="time-sel"><button class="time-btn">1H</button><button class="time-btn active">6H</button><button class="time-btn">24H</button><button class="time-btn">7D</button></div></div>
<div class="live">
  <div class="live-item"><div><div class="live-label">Temperature</div><div class="live-val green">72.4 <span class="live-unit">°C</span></div></div></div>
  <div class="live-item"><div><div class="live-label">Pressure</div><div class="live-val blue">3.21 <span class="live-unit">bar</span></div></div></div>
  <div class="live-item"><div><div class="live-label">Flow Rate</div><div class="live-val orange">18.7 <span class="live-unit">m³/h</span></div></div></div>
  <div class="live-item"><div><div class="live-label">pH Level</div><div class="live-val purple">7.02</div></div></div>
</div>
<div class="charts">
  <div class="chart-box"><div class="chart-title">Temperature (°C)</div><div class="chart-val green">72.4 <span class="unit">°C</span></div>
    <div class="chart-area"><span class="axis-label ax-y1">90</span><span class="axis-label ax-y2">70</span><span class="axis-label ax-y3">50</span><span class="axis-label ax-x1">08:00</span><span class="axis-label ax-x2">11:00</span><span class="axis-label ax-x3">14:00</span>
    <svg viewBox="0 0 400 100" preserveAspectRatio="none"><polyline fill="none" stroke="#4caf50" stroke-width="2" points="0,60 20,55 40,50 60,58 80,45 100,40 120,42 140,38 160,44 180,35 200,30 220,38 240,42 260,36 280,32 300,28 320,35 340,30 360,25 380,22 400,20"/><polyline fill="url(#g1)" stroke="none" points="0,60 20,55 40,50 60,58 80,45 100,40 120,42 140,38 160,44 180,35 200,30 220,38 240,42 260,36 280,32 300,28 320,35 340,30 360,25 380,22 400,20 400,100 0,100"/><defs><linearGradient id="g1" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#4caf50" stop-opacity="0.3"/><stop offset="100%" stop-color="#4caf50" stop-opacity="0"/></linearGradient></defs></svg></div></div>
  <div class="chart-box"><div class="chart-title">Pressure (bar)</div><div class="chart-val blue">3.21 <span class="unit">bar</span></div>
    <div class="chart-area"><span class="axis-label ax-y1">5.0</span><span class="axis-label ax-y2">3.0</span><span class="axis-label ax-y3">1.0</span><span class="axis-label ax-x1">08:00</span><span class="axis-label ax-x2">11:00</span><span class="axis-label ax-x3">14:00</span>
    <svg viewBox="0 0 400 100" preserveAspectRatio="none"><polyline fill="none" stroke="#42a5f5" stroke-width="2" points="0,50 30,48 60,52 90,46 120,50 150,44 180,48 210,42 240,46 270,40 300,44 330,38 360,42 400,36"/><polyline fill="url(#g2)" stroke="none" points="0,50 30,48 60,52 90,46 120,50 150,44 180,48 210,42 240,46 270,40 300,44 330,38 360,42 400,36 400,100 0,100"/><defs><linearGradient id="g2" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#42a5f5" stop-opacity="0.3"/><stop offset="100%" stop-color="#42a5f5" stop-opacity="0"/></linearGradient></defs></svg></div></div>
  <div class="chart-box"><div class="chart-title">Flow Rate (m³/h)</div><div class="chart-val orange">18.7 <span class="unit">m³/h</span></div>
    <div class="chart-area"><span class="axis-label ax-y1">30</span><span class="axis-label ax-y2">20</span><span class="axis-label ax-y3">10</span><span class="axis-label ax-x1">08:00</span><span class="axis-label ax-x2">11:00</span><span class="axis-label ax-x3">14:00</span>
    <svg viewBox="0 0 400 100" preserveAspectRatio="none"><polyline fill="none" stroke="#ff9800" stroke-width="2" points="0,40 25,38 50,42 75,35 100,38 125,32 150,36 175,30 200,34 225,28 250,32 275,26 300,30 325,25 350,28 375,22 400,20"/><polyline fill="url(#g3)" stroke="none" points="0,40 25,38 50,42 75,35 100,38 125,32 150,36 175,30 200,34 225,28 250,32 275,26 300,30 325,25 350,28 375,22 400,20 400,100 0,100"/><defs><linearGradient id="g3" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#ff9800" stop-opacity="0.3"/><stop offset="100%" stop-color="#ff9800" stop-opacity="0"/></linearGradient></defs></svg></div></div>
  <div class="chart-box"><div class="chart-title">pH Level</div><div class="chart-val purple">7.02</div>
    <div class="chart-area"><span class="axis-label ax-y1">9.0</span><span class="axis-label ax-y2">7.0</span><span class="axis-label ax-y3">5.0</span><span class="axis-label ax-x1">08:00</span><span class="axis-label ax-x2">11:00</span><span class="axis-label ax-x3">14:00</span>
    <svg viewBox="0 0 400 100" preserveAspectRatio="none"><polyline fill="none" stroke="#ab47bc" stroke-width="2" points="0,50 30,52 60,48 90,51 120,49 150,50 180,48 210,50 240,49 270,50 300,51 330,49 360,50 400,48"/><polyline fill="url(#g4)" stroke="none" points="0,50 30,52 60,48 90,51 120,49 150,50 180,48 210,50 240,49 270,50 300,51 330,49 360,50 400,48 400,100 0,100"/><defs><linearGradient id="g4" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#ab47bc" stop-opacity="0.3"/><stop offset="100%" stop-color="#ab47bc" stop-opacity="0"/></linearGradient></defs></svg></div></div>
</div>
</body></html>"""

# ── 4. Operator Control Panel (Medium) ──
MOCKUPS["04-operator-panel"] = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#12131a;color:#e0e0e0;font-family:'Segoe UI',system-ui,sans-serif;padding:28px 32px}
h1{font-size:20px;font-weight:600;color:#fff;margin-bottom:6px}
.sub{font-size:12px;color:#666;margin-bottom:20px}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:20px}
.panel{background:#1c1e2e;border-radius:10px;padding:20px}
.panel-title{font-size:14px;font-weight:600;margin-bottom:16px;color:#aaa;text-transform:uppercase;letter-spacing:1px;font-size:11px}
.ctrl-row{display:flex;gap:10px;margin-bottom:14px;align-items:center}
.btn-ctrl{padding:12px 28px;border-radius:6px;border:none;font-size:14px;font-weight:700;cursor:pointer;text-transform:uppercase;letter-spacing:1px}
.btn-start{background:#2e7d32;color:#fff} .btn-stop{background:#c62828;color:#fff} .btn-reset{background:#37474f;color:#ccc}
.mode-sel{display:flex;gap:4px;margin-bottom:14px}
.mode-btn{padding:8px 20px;border-radius:5px;font-size:12px;background:#252838;color:#888;border:1px solid #333;cursor:pointer}
.mode-btn.active{background:#1a3a5c;color:#5b9cf6;border-color:#3a6abf}
.input-group{margin-bottom:14px}
.input-label{font-size:11px;color:#888;margin-bottom:4px}
.input-row{display:flex;gap:8px;align-items:center}
.input-field{background:#0e0f16;border:1px solid #333;border-radius:5px;padding:8px 12px;color:#fff;font-family:'Consolas',monospace;font-size:16px;width:120px;text-align:right}
.input-unit{font-size:12px;color:#666}
.readout{background:#0e0f16;border-radius:8px;padding:14px;margin-bottom:12px;display:flex;justify-content:space-between;align-items:center}
.readout-label{font-size:12px;color:#888}
.readout-val{font-family:'Consolas',monospace;font-size:24px;font-weight:700}
.readout-unit{font-size:12px;color:#666}
.green{color:#4caf50} .blue{color:#42a5f5} .orange{color:#ff9800} .red{color:#ef5350}
.status-bar{background:#1c1e2e;border-radius:10px;padding:14px 20px;margin-top:20px;display:flex;justify-content:space-between;align-items:center}
.status-dot{width:10px;height:10px;border-radius:50%;background:#4caf50;display:inline-block;margin-right:8px}
.status-text{font-size:13px;color:#4caf50}
</style></head><body>
<h1>Operator Control Panel</h1>
<div class="sub">Mixing Unit MX-201 &bull; Manual Mode</div>
<div class="cols">
  <div class="panel">
    <div class="panel-title">Controls</div>
    <div class="ctrl-row"><button class="btn-ctrl btn-start">▶ START</button><button class="btn-ctrl btn-stop">■ STOP</button><button class="btn-ctrl btn-reset">↻ RESET</button></div>
    <div class="panel-title" style="margin-top:8px">Operating Mode</div>
    <div class="mode-sel"><div class="mode-btn">Auto</div><div class="mode-btn active">Manual</div><div class="mode-btn">Service</div></div>
    <div class="panel-title" style="margin-top:8px">Setpoints</div>
    <div class="input-group"><div class="input-label">Target Temperature</div><div class="input-row"><input class="input-field" value="75.0"><span class="input-unit">°C</span></div></div>
    <div class="input-group"><div class="input-label">Target Speed</div><div class="input-row"><input class="input-field" value="1200"><span class="input-unit">RPM</span></div></div>
    <div class="input-group"><div class="input-label">Target Pressure</div><div class="input-row"><input class="input-field" value="3.50"><span class="input-unit">bar</span></div></div>
  </div>
  <div class="panel">
    <div class="panel-title">Live Readouts</div>
    <div class="readout"><div><div class="readout-label">Temperature</div><div class="readout-val green">72.4 <span class="readout-unit">°C</span></div></div></div>
    <div class="readout"><div><div class="readout-label">Speed</div><div class="readout-val blue">1185 <span class="readout-unit">RPM</span></div></div></div>
    <div class="readout"><div><div class="readout-label">Pressure</div><div class="readout-val orange">3.42 <span class="readout-unit">bar</span></div></div></div>
    <div class="readout"><div><div class="readout-label">Torque</div><div class="readout-val">28.6 <span class="readout-unit">Nm</span></div></div></div>
    <div class="readout"><div><div class="readout-label">Batch Progress</div><div class="readout-val blue">67 <span class="readout-unit">%</span></div></div></div>
  </div>
</div>
<div class="status-bar"><div><span class="status-dot"></span><span class="status-text">System OK — Manual Mode Active</span></div><div style="font-size:12px;color:#666">Operator: ZHANG S. &bull; Shift: B</div></div>
</body></html>"""

# ── 5. Production Line Overview (Medium) ──
MOCKUPS["05-production-overview"] = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#12131a;color:#e0e0e0;font-family:'Segoe UI',system-ui,sans-serif;padding:28px 32px}
h1{font-size:20px;font-weight:600;color:#fff;margin-bottom:6px}
.sub{font-size:12px;color:#666;margin-bottom:20px}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:20px}
.kpi{background:#1c1e2e;border-radius:10px;padding:16px;text-align:center}
.kpi-val{font-size:28px;font-weight:700} .kpi-label{font-size:11px;color:#888;margin-top:4px}
.kpi-sub{font-size:10px;margin-top:2px}
.green{color:#4caf50} .blue{color:#42a5f5} .orange{color:#ff9800} .red{color:#ef5350}
.flow{background:#1c1e2e;border-radius:10px;padding:20px;margin-bottom:16px}
.flow-title{font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px;margin-bottom:16px}
.flow-line{display:flex;align-items:center;gap:0}
.station{background:#252838;border-radius:8px;padding:14px 16px;min-width:140px;text-align:center;position:relative}
.station-name{font-size:11px;color:#aaa;margin-bottom:4px}
.station-status{font-size:13px;font-weight:600}
.station.ok .station-status{color:#4caf50} .station.warn .station-status{color:#ff9800} .station.fault .station-status{color:#ef5350}
.arrow{color:#333;font-size:20px;padding:0 6px}
.bottom-row{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.panel{background:#1c1e2e;border-radius:10px;padding:18px}
.panel-title{font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px}
.bar-row{display:flex;align-items:center;gap:10px;margin-bottom:10px}
.bar-label{font-size:12px;color:#aaa;width:80px}
.bar-track{flex:1;height:8px;background:#252838;border-radius:4px;overflow:hidden}
.bar-fill{height:100%;border-radius:4px}
.bar-val{font-size:12px;font-family:'Consolas',monospace;width:45px;text-align:right}
.shift-row{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #1e2030;font-size:12px}
</style></head><body>
<h1>Production Line Overview</h1>
<div class="sub">Bottling Line BL-01 &bull; Shift B &bull; 14:32 UTC</div>
<div class="kpis">
  <div class="kpi"><div class="kpi-val green">87.3%</div><div class="kpi-label">OEE</div><div class="kpi-sub green">▲ 2.1% vs yesterday</div></div>
  <div class="kpi"><div class="kpi-val blue">12,847</div><div class="kpi-label">Units Produced</div><div class="kpi-sub blue">Target: 15,000</div></div>
  <div class="kpi"><div class="kpi-val orange">1,523</div><div class="kpi-label">Units / Hour</div><div class="kpi-sub orange">Rated: 1,800</div></div>
  <div class="kpi"><div class="kpi-val">2h 08m</div><div class="kpi-label">Time to Target</div><div class="kpi-sub" style="color:#666">ETA: 16:40</div></div>
</div>
<div class="flow">
  <div class="flow-title">Process Flow</div>
  <div class="flow-line">
    <div class="station ok"><div class="station-name">Filler</div><div class="station-status">● Running</div><div style="font-size:10px;color:#666;margin-top:4px">1,523/h</div></div>
    <div class="arrow">→</div>
    <div class="station ok"><div class="station-name">Capper</div><div class="station-status">● Running</div><div style="font-size:10px;color:#666;margin-top:4px">1,520/h</div></div>
    <div class="arrow">→</div>
    <div class="station warn"><div class="station-name">Labeler</div><div class="station-status">● Slow</div><div style="font-size:10px;color:#666;margin-top:4px">1,480/h</div></div>
    <div class="arrow">→</div>
    <div class="station ok"><div class="station-name">Inspector</div><div class="station-status">● Running</div><div style="font-size:10px;color:#666;margin-top:4px">Reject: 0.3%</div></div>
    <div class="arrow">→</div>
    <div class="station ok"><div class="station-name">Packer</div><div class="station-status">● Running</div><div style="font-size:10px;color:#666;margin-top:4px">254 cases</div></div>
  </div>
</div>
<div class="bottom-row">
  <div class="panel"><div class="panel-title">Performance Breakdown</div>
    <div class="bar-row"><span class="bar-label">Availability</span><div class="bar-track"><div class="bar-fill" style="width:94%;background:#4caf50"></div></div><span class="bar-val green">94.0%</span></div>
    <div class="bar-row"><span class="bar-label">Performance</span><div class="bar-track"><div class="bar-fill" style="width:92%;background:#42a5f5"></div></div><span class="bar-val blue">92.1%</span></div>
    <div class="bar-row"><span class="bar-label">Quality</span><div class="bar-track"><div class="bar-fill" style="width:99%;background:#ab47bc"></div></div><span class="bar-val purple" style="color:#ab47bc">99.7%</span></div>
  </div>
  <div class="panel"><div class="panel-title">Shift Summary</div>
    <div class="shift-row"><span style="color:#888">Shift Start</span><span>06:00</span></div>
    <div class="shift-row"><span style="color:#888">Downtime</span><span class="orange">18 min</span></div>
    <div class="shift-row"><span style="color:#888">Rejects</span><span>38 units (0.3%)</span></div>
    <div class="shift-row"><span style="color:#888">Changeovers</span><span>1 (12 min)</span></div>
    <div class="shift-row" style="border:none"><span style="color:#888">Operator</span><span>ZHANG S.</span></div>
  </div>
</div>
</body></html>"""

# ── 6. Tank Farm Synoptic (Medium-Hard) ──
MOCKUPS["06-tank-synoptic"] = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#12131a;color:#e0e0e0;font-family:'Segoe UI',system-ui,sans-serif;padding:28px 32px}
h1{font-size:20px;font-weight:600;color:#fff;margin-bottom:6px}
.sub{font-size:12px;color:#666;margin-bottom:24px}
.synoptic{display:flex;gap:24px;justify-content:center;margin-bottom:24px}
.tank-group{text-align:center}
.tank{width:120px;height:180px;border:2px solid #444;border-radius:8px 8px 12px 12px;position:relative;overflow:hidden;margin:0 auto 8px;background:#0e0f16}
.tank-fill{position:absolute;bottom:0;left:0;right:0;transition:height 0.3s}
.tank-fill.high{background:linear-gradient(to top,#1b5e20,#2e7d32)} .tank-fill.mid{background:linear-gradient(to top,#1565c0,#1e88e5)} .tank-fill.low{background:linear-gradient(to top,#bf360c,#e65100)}
.tank-pct{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:24px;font-weight:700;text-shadow:0 1px 4px rgba(0,0,0,0.8);z-index:1}
.tank-label{font-size:13px;font-weight:600;margin-bottom:2px}
.tank-cap{font-size:10px;color:#666}
.valve-row{display:flex;justify-content:center;gap:60px;margin-bottom:24px;align-items:center}
.valve{text-align:center}
.valve-icon{width:40px;height:40px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:18px;margin:0 auto 4px;border:2px solid}
.valve.open .valve-icon{border-color:#4caf50;color:#4caf50;background:#1b3a1b}
.valve.closed .valve-icon{border-color:#f44336;color:#f44336;background:#3a1b1b}
.valve-label{font-size:10px;color:#888}
.pipe{height:3px;background:#333;flex:1;margin:0 -8px;position:relative;top:-12px}
.pipe.active{background:#1e88e5}
.info-row{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}
.info-card{background:#1c1e2e;border-radius:8px;padding:14px;text-align:center}
.info-val{font-size:20px;font-weight:700;margin-bottom:2px}
.info-label{font-size:10px;color:#888}
.pump-row{display:flex;justify-content:center;gap:40px;margin-bottom:20px}
.pump{background:#1c1e2e;border-radius:8px;padding:10px 20px;text-align:center}
.pump-icon{font-size:20px;margin-bottom:4px}
.pump-label{font-size:11px;color:#888}
.pump-status{font-size:12px;font-weight:600}
.pump.on .pump-status{color:#4caf50} .pump.off .pump-status{color:#78909c}
</style></head><body>
<h1>Tank Farm Synoptic</h1>
<div class="sub">Storage Area SA-100 &bull; 4 Tanks &bull; Live View</div>
<div class="synoptic">
  <div class="tank-group"><div class="tank"><div class="tank-fill high" style="height:82%"></div><div class="tank-pct">82%</div></div><div class="tank-label">TK-101</div><div class="tank-cap">50,000 L &bull; Product A</div></div>
  <div class="tank-group"><div class="tank"><div class="tank-fill mid" style="height:55%"></div><div class="tank-pct">55%</div></div><div class="tank-label">TK-102</div><div class="tank-cap">50,000 L &bull; Product A</div></div>
  <div class="tank-group"><div class="tank"><div class="tank-fill low" style="height:18%"></div><div class="tank-pct">18%</div></div><div class="tank-label">TK-103</div><div class="tank-cap">30,000 L &bull; Product B</div></div>
  <div class="tank-group"><div class="tank"><div class="tank-fill mid" style="height:71%"></div><div class="tank-pct">71%</div></div><div class="tank-label">TK-104</div><div class="tank-cap">30,000 L &bull; Product B</div></div>
</div>
<div class="valve-row">
  <div class="valve open"><div class="valve-icon">⟐</div><div class="valve-label">V-101 OPEN</div></div>
  <div class="pipe active"></div>
  <div class="valve open"><div class="valve-icon">⟐</div><div class="valve-label">V-102 OPEN</div></div>
  <div class="pipe active"></div>
  <div class="valve closed"><div class="valve-icon">✕</div><div class="valve-label">V-103 CLOSED</div></div>
  <div class="pipe"></div>
  <div class="valve open"><div class="valve-icon">⟐</div><div class="valve-label">V-104 OPEN</div></div>
</div>
<div class="pump-row">
  <div class="pump on"><div class="pump-icon">⟳</div><div class="pump-label">Pump P-101</div><div class="pump-status">● Running</div></div>
  <div class="pump on"><div class="pump-icon">⟳</div><div class="pump-label">Pump P-102</div><div class="pump-status">● Running</div></div>
  <div class="pump off"><div class="pump-icon">○</div><div class="pump-label">Pump P-103</div><div class="pump-status">● Standby</div></div>
</div>
<div class="info-row">
  <div class="info-card"><div class="info-val green">41,000 L</div><div class="info-label">TK-101 Volume</div></div>
  <div class="info-card"><div class="info-val blue">27,500 L</div><div class="info-label">TK-102 Volume</div></div>
  <div class="info-card"><div class="info-val red">5,400 L</div><div class="info-label">TK-103 Volume</div></div>
  <div class="info-card"><div class="info-val blue">21,300 L</div><div class="info-label">TK-104 Volume</div></div>
</div>
</body></html>"""

# ── 7. Energy Monitoring Dashboard (Medium-Hard) ──
MOCKUPS["07-energy-dashboard"] = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#12131a;color:#e0e0e0;font-family:'Segoe UI',system-ui,sans-serif;padding:28px 32px}
h1{font-size:20px;font-weight:600;color:#fff;margin-bottom:6px}
.sub{font-size:12px;color:#666;margin-bottom:20px}
.kpi-row{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:20px}
.kpi{background:#1c1e2e;border-radius:10px;padding:16px}
.kpi-icon{font-size:20px;margin-bottom:6px}
.kpi-val{font-size:26px;font-weight:700} .kpi-label{font-size:11px;color:#888;margin-top:2px}
.kpi-delta{font-size:11px;margin-top:4px}
.green{color:#4caf50} .red{color:#ef5350} .blue{color:#42a5f5} .orange{color:#ff9800}
.charts{display:grid;grid-template-columns:2fr 1fr;gap:16px;margin-bottom:16px}
.chart-box{background:#1c1e2e;border-radius:10px;padding:18px}
.chart-title{font-size:12px;color:#888;margin-bottom:14px;text-transform:uppercase;letter-spacing:0.5px}
.bar-chart{display:flex;align-items:flex-end;gap:8px;height:160px;padding-top:10px}
.bar-col{display:flex;flex-direction:column;align-items:center;flex:1}
.bar{width:100%;border-radius:4px 4px 0 0;min-height:4px}
.bar-label{font-size:9px;color:#666;margin-top:6px}
.bar-val{font-size:9px;color:#aaa;margin-bottom:4px}
.donut-wrap{display:flex;flex-direction:column;align-items:center;gap:14px}
.donut{width:140px;height:140px;border-radius:50%;background:conic-gradient(#42a5f5 0% 35%,#4caf50 35% 60%,#ff9800 60% 80%,#78909c 80% 100%);position:relative;margin:0 auto}
.donut-center{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:90px;height:90px;border-radius:50%;background:#1c1e2e;display:flex;align-items:center;justify-content:center;flex-direction:column}
.donut-val{font-size:22px;font-weight:700} .donut-label{font-size:10px;color:#888}
.legend{display:flex;flex-direction:column;gap:8px;margin-top:8px}
.legend-item{display:flex;align-items:center;gap:8px;font-size:11px;color:#aaa}
.legend-dot{width:10px;height:10px;border-radius:3px}
.bottom-row{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.zone-row{display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid #1e2030;font-size:12px}
.zone-bar{width:80px;height:6px;background:#252838;border-radius:3px;overflow:hidden;display:inline-block;vertical-align:middle;margin-left:8px}
.zone-fill{height:100%;border-radius:3px}
</style></head><body>
<h1>Energy Monitoring Dashboard</h1>
<div class="sub">Plant-wide consumption &bull; Today: Mar 20, 2026</div>
<div class="kpi-row">
  <div class="kpi"><div class="kpi-icon">⚡</div><div class="kpi-val">2,847 <span style="font-size:14px;color:#666">kWh</span></div><div class="kpi-label">Today's Consumption</div><div class="kpi-delta red">▲ 5.2% vs avg</div></div>
  <div class="kpi"><div class="kpi-icon">💰</div><div class="kpi-val blue">¥4,128</div><div class="kpi-label">Today's Cost</div><div class="kpi-delta green">▼ 2.1% vs yesterday</div></div>
  <div class="kpi"><div class="kpi-icon">📊</div><div class="kpi-val green">0.42 <span style="font-size:14px;color:#666">kWh/unit</span></div><div class="kpi-label">Energy per Unit</div><div class="kpi-delta green">▼ 3.5%</div></div>
  <div class="kpi"><div class="kpi-icon">🏭</div><div class="kpi-val orange">312 <span style="font-size:14px;color:#666">kW</span></div><div class="kpi-label">Peak Demand</div><div class="kpi-delta">14:15 today</div></div>
</div>
<div class="charts">
  <div class="chart-box"><div class="chart-title">Hourly Consumption (kWh)</div>
    <div class="bar-chart">
      <div class="bar-col"><div class="bar-val">95</div><div class="bar" style="height:38%;background:#1e88e5"></div><div class="bar-label">6:00</div></div>
      <div class="bar-col"><div class="bar-val">142</div><div class="bar" style="height:57%;background:#1e88e5"></div><div class="bar-label">7:00</div></div>
      <div class="bar-col"><div class="bar-val">198</div><div class="bar" style="height:79%;background:#1e88e5"></div><div class="bar-label">8:00</div></div>
      <div class="bar-col"><div class="bar-val">234</div><div class="bar" style="height:94%;background:#ff9800"></div><div class="bar-label">9:00</div></div>
      <div class="bar-col"><div class="bar-val">248</div><div class="bar" style="height:99%;background:#f44336"></div><div class="bar-label">10:00</div></div>
      <div class="bar-col"><div class="bar-val">241</div><div class="bar" style="height:96%;background:#ff9800"></div><div class="bar-label">11:00</div></div>
      <div class="bar-col"><div class="bar-val">189</div><div class="bar" style="height:76%;background:#1e88e5"></div><div class="bar-label">12:00</div></div>
      <div class="bar-col"><div class="bar-val">225</div><div class="bar" style="height:90%;background:#ff9800"></div><div class="bar-label">13:00</div></div>
      <div class="bar-col"><div class="bar-val">250</div><div class="bar" style="height:100%;background:#f44336"></div><div class="bar-label">14:00</div></div>
    </div>
  </div>
  <div class="chart-box"><div class="chart-title">By Zone</div>
    <div class="donut-wrap"><div class="donut"><div class="donut-center"><div class="donut-val">2,847</div><div class="donut-label">kWh total</div></div></div>
    <div class="legend">
      <div class="legend-item"><div class="legend-dot" style="background:#42a5f5"></div>Production (35%)</div>
      <div class="legend-item"><div class="legend-dot" style="background:#4caf50"></div>HVAC (25%)</div>
      <div class="legend-item"><div class="legend-dot" style="background:#ff9800"></div>Utilities (20%)</div>
      <div class="legend-item"><div class="legend-dot" style="background:#78909c"></div>Other (20%)</div>
    </div></div>
  </div>
</div>
<div class="bottom-row">
  <div class="chart-box"><div class="chart-title">Zone Breakdown</div>
    <div class="zone-row"><span>Production Hall</span><span>997 kWh<div class="zone-bar"><div class="zone-fill" style="width:100%;background:#42a5f5"></div></div></span></div>
    <div class="zone-row"><span>HVAC System</span><span>712 kWh<div class="zone-bar"><div class="zone-fill" style="width:71%;background:#4caf50"></div></div></span></div>
    <div class="zone-row"><span>Utilities</span><span>569 kWh<div class="zone-bar"><div class="zone-fill" style="width:57%;background:#ff9800"></div></div></span></div>
    <div class="zone-row"><span>Warehouse</span><span>341 kWh<div class="zone-bar"><div class="zone-fill" style="width:34%;background:#78909c"></div></div></span></div>
    <div class="zone-row" style="border:none"><span>Office</span><span>228 kWh<div class="zone-bar"><div class="zone-fill" style="width:23%;background:#78909c"></div></div></span></div>
  </div>
  <div class="chart-box"><div class="chart-title">Weekly Comparison</div>
    <div class="zone-row"><span>Mon</span><span>2,640 kWh</span></div>
    <div class="zone-row"><span>Tue</span><span>2,780 kWh</span></div>
    <div class="zone-row"><span>Wed</span><span>2,710 kWh</span></div>
    <div class="zone-row"><span style="color:#fff;font-weight:600">Thu (today)</span><span style="color:#fff;font-weight:600">2,847 kWh</span></div>
    <div class="zone-row"><span style="color:#555">Fri (est.)</span><span style="color:#555">~2,800 kWh</span></div>
    <div class="zone-row" style="border:none"><span style="color:#888;font-weight:600">Week Total</span><span style="font-weight:600">~13,777 kWh</span></div>
  </div>
</div>
</body></html>"""

# ── 8. Batch Recipe Management (Hard) ──
MOCKUPS["08-batch-recipe"] = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#12131a;color:#e0e0e0;font-family:'Segoe UI',system-ui,sans-serif;padding:24px 28px;font-size:13px}
h1{font-size:20px;font-weight:600;color:#fff;margin-bottom:6px}
.sub{font-size:12px;color:#666;margin-bottom:18px}
.cols{display:grid;grid-template-columns:220px 1fr;gap:16px}
.steps-panel{background:#1c1e2e;border-radius:10px;padding:16px}
.panel-title{font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px}
.step{padding:10px 12px;border-radius:6px;margin-bottom:6px;border-left:3px solid transparent;cursor:pointer;font-size:12px}
.step.done{border-left-color:#4caf50;background:#151a15;color:#81c784}
.step.active{border-left-color:#42a5f5;background:#151520;color:#64b5f6;font-weight:600}
.step.pending{border-left-color:#333;color:#666}
.step-num{font-weight:700;margin-right:6px}
.step-time{font-size:10px;color:#555;margin-top:2px}
.right-area{display:flex;flex-direction:column;gap:16px}
.detail-panel{background:#1c1e2e;border-radius:10px;padding:18px}
.detail-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}
.badge{padding:4px 12px;border-radius:12px;font-size:11px;font-weight:600}
.badge.running{background:#1b2a3a;color:#42a5f5} .badge.done{background:#1b3a1b;color:#66bb6a}
table{width:100%;border-collapse:collapse}
th{text-align:left;padding:8px 10px;background:#181a24;color:#888;font-weight:500;font-size:11px}
td{padding:8px 10px;border-bottom:1px solid #1e2030;font-size:12px}
.val{font-family:'Consolas',monospace}
.ok{color:#4caf50} .warn{color:#ff9800}
.timeline{background:#1c1e2e;border-radius:10px;padding:16px}
.tl-bar{display:flex;height:28px;border-radius:4px;overflow:hidden;margin-bottom:8px}
.tl-seg{display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:600}
.tl-labels{display:flex;justify-content:space-between;font-size:10px;color:#666}
.ctrl-row{display:flex;gap:8px;margin-top:12px}
.btn{padding:8px 20px;border-radius:6px;border:none;font-size:12px;font-weight:600;cursor:pointer}
.btn-primary{background:#1565c0;color:#fff} .btn-sec{background:#37474f;color:#ccc} .btn-danger{background:#b71c1c;color:#fff}
.progress-info{display:flex;gap:24px;font-size:12px;color:#888;margin-top:8px}
.progress-info span{color:#e0e0e0;font-weight:600}
</style></head><body>
<h1>Batch Recipe Management</h1>
<div class="sub">Recipe: PHARMA-2026-A &bull; Batch #B-20260320-04 &bull; Product: Compound X-200</div>
<div class="cols">
  <div class="steps-panel"><div class="panel-title">Recipe Steps</div>
    <div class="step done"><span class="step-num">1.</span>Charge Raw Materials<div class="step-time">✓ 08:00–08:25 (25 min)</div></div>
    <div class="step done"><span class="step-num">2.</span>Pre-Heat to 60°C<div class="step-time">✓ 08:25–08:47 (22 min)</div></div>
    <div class="step done"><span class="step-num">3.</span>Add Catalyst<div class="step-time">✓ 08:47–08:55 (8 min)</div></div>
    <div class="step active"><span class="step-num">4.</span>Main Reaction @ 75°C<div class="step-time">▶ 08:55–now (5h 37m / 6h)</div></div>
    <div class="step pending"><span class="step-num">5.</span>Cool Down to 25°C</div>
    <div class="step pending"><span class="step-num">6.</span>Quality Sampling</div>
    <div class="step pending"><span class="step-num">7.</span>Transfer to Storage</div>
    <div class="step pending"><span class="step-num">8.</span>CIP Cleaning</div>
  </div>
  <div class="right-area">
    <div class="detail-panel">
      <div class="detail-header"><div><strong>Step 4: Main Reaction</strong><div style="font-size:11px;color:#888;margin-top:2px">Hold at 75°C with agitation for 6 hours</div></div><span class="badge running">● Running</span></div>
      <table>
        <tr><th>Parameter</th><th>Setpoint</th><th>Actual</th><th>Status</th></tr>
        <tr><td>Temperature</td><td class="val">75.0 °C</td><td class="val">74.8 °C</td><td class="ok">✓ OK</td></tr>
        <tr><td>Agitator Speed</td><td class="val">120 RPM</td><td class="val">119 RPM</td><td class="ok">✓ OK</td></tr>
        <tr><td>Pressure</td><td class="val">1.2 bar</td><td class="val">1.25 bar</td><td class="ok">✓ OK</td></tr>
        <tr><td>pH</td><td class="val">7.0 ± 0.2</td><td class="val">7.08</td><td class="ok">✓ OK</td></tr>
        <tr><td>Duration</td><td class="val">6h 00m</td><td class="val">5h 37m</td><td class="warn">⏳ 23 min left</td></tr>
      </table>
      <div class="ctrl-row"><button class="btn btn-sec">⏸ Pause</button><button class="btn btn-primary">⏭ Skip to Next</button><button class="btn btn-danger">⏹ Abort Batch</button></div>
    </div>
    <div class="timeline"><div class="panel-title">Batch Timeline</div>
      <div class="tl-bar">
        <div class="tl-seg" style="width:7%;background:#2e7d32;color:#a5d6a7">1</div>
        <div class="tl-seg" style="width:6%;background:#1b5e20;color:#81c784">2</div>
        <div class="tl-seg" style="width:3%;background:#33691e;color:#aed581">3</div>
        <div class="tl-seg" style="width:60%;background:#1565c0;color:#90caf9">4 — Main Reaction</div>
        <div class="tl-seg" style="width:24%;background:#252838;color:#555">5  6  7  8</div>
      </div>
      <div class="tl-labels"><span>08:00</span><span>10:00</span><span>12:00</span><span>14:00</span><span>16:00</span></div>
      <div class="progress-info"><div>Elapsed: <span>6h 32m</span></div><div>Remaining: <span>~1h 28m</span></div><div>ETA: <span>16:00</span></div></div>
    </div>
  </div>
</div>
</body></html>"""


async def main():
    from playwright.async_api import async_playwright
    out_dir = os.path.join(os.path.dirname(__file__), "png")
    os.makedirs(out_dir, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        for name, html in MOCKUPS.items():
            page = await browser.new_page(viewport={"width": 1280, "height": 720})
            await page.set_content(html, wait_until="networkidle")
            path = os.path.join(out_dir, f"{name}.png")
            await page.screenshot(path=path, full_page=False, type="png")
            await page.close()
            print(f"  ✓ {name}.png")

        await browser.close()
    print(f"\nDone — {len(MOCKUPS)} mockups saved to {out_dir}")


if __name__ == "__main__":
    asyncio.run(main())
