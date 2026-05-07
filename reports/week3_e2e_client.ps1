# （旧）快速串跑；若需「仅真模型通过才落盘 + 多轮 Refine 记录」请用 run_week3_verified.ps1
# Week 3 E2E: generate -> edit -> render -> refine (uses current mockups/png)
# Requires: uvicorn reachable ($env:API_BASE 或本机 8000) with USE_REAL_MODEL=1。
# 全精度：UI2CODEN_QUANT=none。Edit 指令见 $EditInstruction。
$ErrorActionPreference = "Stop"
# 发给 POST /edit 的英文指令（会写入 week003_EDIT_记录.txt）
$EditInstruction = "Increase the main page title font size and make it more prominent."
$base = if ($env:API_BASE -and $env:API_BASE.Trim() -ne "") { $env:API_BASE.Trim() } else { "http://127.0.0.1:8000" }
$outDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$shotDir = Join-Path $outDir "screenshots"
if (-not (Test-Path $shotDir)) { New-Item -ItemType Directory -Path $shotDir -Force | Out-Null }
$png = Join-Path (Split-Path -Parent $outDir) "mockups\png\01-equipment-status.png"
if (-not (Test-Path $png)) { throw "PNG not found: $png" }

function Save-B64Png {
    param([string]$B64, [string]$Path)
    if ([string]::IsNullOrEmpty($B64)) { return $false }
    [IO.File]::WriteAllBytes($Path, [Convert]::FromBase64String($B64))
    return $true
}

$log = @()
$log += "=== Week3 E2E run $(Get-Date -Format o) ==="
$log += "Input mockup: $png"
$log += ""

# --- 1) Screenshot -> code (导师要求 1) ---
$log += "[1] POST /generate (screenshot -> code) ..."
$b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($png))
$bodyGen = @{
    image_base64 = $b64
    frame_name   = "Equipment Status Dashboard"
    width        = 1280
    height       = 720
} | ConvertTo-Json -Depth 6
$t0 = Get-Date
$r1 = Invoke-RestMethod -Uri "$base/generate" -Method Post -Body $bodyGen `
    -ContentType "application/json; charset=utf-8" -TimeoutSec 7200
$log += "    done in $([math]::Round(((Get-Date) - $t0).TotalSeconds, 1)) s"
$r1.code | Out-File (Join-Path $outDir "week003_run_01_generate.html") -Encoding utf8
if (Save-B64Png $r1.preview_base64 (Join-Path $shotDir "week003_01_generate_preview.png")) {
    $log += "    saved week003_01_generate_preview.png"
} else {
    $log += "    preview_base64 was null (check service logs / Playwright)"
}
$log += ""

# --- 2) Edit by instruction (导师要求 2) ---
$log += "[2] POST /edit (instruction -> updated code) ..."
$log += "    instruction (exact): $EditInstruction"
$bodyEdit = @{
    current_code = $r1.code
    instruction  = $EditInstruction
    width        = 1280
    height       = 720
} | ConvertTo-Json -Depth 8
$t1 = Get-Date
$r2 = Invoke-RestMethod -Uri "$base/edit" -Method Post -Body $bodyEdit `
    -ContentType "application/json; charset=utf-8" -TimeoutSec 7200
$log += "    done in $([math]::Round(((Get-Date) - $t1).TotalSeconds, 1)) s"
$r2.code | Out-File (Join-Path $outDir "week003_run_02_after_edit.html") -Encoding utf8
if (Save-B64Png $r2.preview_base64 (Join-Path $shotDir "week003_02_after_edit_preview.png")) {
    $log += "    saved week003_02_after_edit_preview.png"
}
$log += ""

# --- 3) Render current HTML for refine pairing ---
$log += "[3] POST /render (current code -> PNG for refine) ..."
$bodyRender = @{
    html_code = $r1.code
    width     = 1280
    height    = 720
} | ConvertTo-Json -Depth 4
$rR = Invoke-RestMethod -Uri "$base/render" -Method Post -Body $bodyRender `
    -ContentType "application/json; charset=utf-8" -TimeoutSec 600
Save-B64Png $rR.image_base64 (Join-Path $shotDir "week003_03_render_of_generate_code.png") | Out-Null
$log += "    saved week003_03_render_of_generate_code.png"
$log += ""

# --- 4) Iterative refine (导师要求 3) ---
$log += "[4] POST /refine (reference + rendered + code -> closer to mockup) ..."
$bodyRef = @{
    reference_image_base64  = $b64
    current_code            = $r1.code
    rendered_image_base64   = $rR.image_base64
    width                   = 1280
    height                  = 720
} | ConvertTo-Json -Depth 6
$t2 = Get-Date
$r3 = Invoke-RestMethod -Uri "$base/refine" -Method Post -Body $bodyRef `
    -ContentType "application/json; charset=utf-8" -TimeoutSec 7200
$log += "    done in $([math]::Round(((Get-Date) - $t2).TotalSeconds, 1)) s"
$r3.code | Out-File (Join-Path $outDir "week003_run_04_after_refine.html") -Encoding utf8
if (Save-B64Png $r3.preview_base64 (Join-Path $shotDir "week003_04_after_refine_preview.png")) {
    $log += "    saved week003_04_after_refine_preview.png"
}
$log += "=== finished ==="

$logPath = Join-Path $outDir "week003_E2E_RUN_LOG.txt"
$log | Out-File $logPath -Encoding utf8
Write-Host ($log -join "`n")

# 记录 Edit 指令与预期画面变化（规则模型见 rule_based_model.edit 中对 title/large/increase 的分支）
$editNote = @"
=== Week3 · 按指令改代码（POST /edit）记录 ===
本次发送的 instruction（英文原文，与请求体一致）：
$EditInstruction

中文含义：要求把页面主标题字号加大、更醒目。

若当前后端为规则模型（rule_based_model）：
  当指令里同时包含 title 与 increase/large/bigger 等词时，会把 HTML 里形如
  `h1 { font-size: 22px` 的样式替换为 `h1 { font-size: 28px`（若生成结果里存在该片段）。
  预览图对比：week003_01_generate_preview.png（改前） vs week003_02_after_edit_preview.png（改后），
  若替换生效，顶部标题在渲染图中会略变大。

若后端为真实 UI2Code^N：由模型按自然语言改 HTML/CSS，变化不固定，但语义上应使标题更突出。
"@
$editNote | Out-File (Join-Path $outDir "week003_EDIT_记录.txt") -Encoding utf8
