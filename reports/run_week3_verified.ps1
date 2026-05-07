# 第三周导师三件事：生成 -> 按指令编辑 -> 多轮 Refine
# 仅当 GET /health 的 ui2code_n_active 为 true 时写入“正式结果”；否则只写 week003_FAILURE.txt
# 前置：Uvicorn 已用 USE_REAL_MODEL=1, UI2CODEN_MODEL_ID 指向权重；bf16 全卡设 UI2CODEN_QUANT=none（推荐 24G+ GPU）。
# 可选：$env:API_BASE = "http://127.0.0.1:8000" 指向远程或 SSH 转发后的服务。
# 若中途只跑完 generate+edit：用同目录 resume_week3_refine.ps1 续跑 Refine + 证据（见 WEEK3_INTERRUPTED_说明.txt）。

$ErrorActionPreference = "Stop"
$base = if ($env:API_BASE -and $env:API_BASE.Trim() -ne "") { $env:API_BASE.Trim() } else { "http://127.0.0.1:8000" }
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$outDir = Join-Path $root "reports"
$shotDir = Join-Path $outDir "screenshots"
if (-not (Test-Path $shotDir)) { New-Item -ItemType Directory -Path $shotDir -Force | Out-Null }
$refPng = Join-Path $root "mockups\png\01-equipment-status.png"
$RefineRounds = 3
$EditInstruction = "Increase the main page title font size and make it more prominent."
$RequestTimeoutSec = 7200

function Save-B64Png($B64, $Path) {
    if ([string]::IsNullOrEmpty($B64)) { return $false }
    [IO.File]::WriteAllBytes($Path, [Convert]::FromBase64String($B64))
    return $true
}

function Write-CodeResponseJson($Obj, $JsonPath) {
    if ($null -eq $Obj) { return }
    $j = $Obj | ConvertTo-Json -Depth 30 -Compress
    $u8 = New-Object System.Text.UTF8Encoding $false
    [IO.File]::WriteAllText($JsonPath, $j, $u8)
}
function Write-B64Text($B64, $TPath) {
    if ([string]::IsNullOrEmpty($B64)) { return }
    $u8 = New-Object System.Text.UTF8Encoding $false
    [IO.File]::WriteAllText($TPath, $B64, $u8)
}

function Assert-Ui2CodeN {
    $h = Invoke-RestMethod -Uri "$base/health" -TimeoutSec 30
    if (-not $h.ui2code_n_active) {
        throw "Real UI2Code^N is not active. model_kind=$($h.model_kind). Refuse to record week3 artifacts."
    }
}

$log = [System.Collections.ArrayList]@()
[void]$log.Add("=== Week3 verified run $(Get-Date -Format o) ===")
[void]$log.Add("Ref PNG: $refPng")
[void]$log.Add("POST /edit instruction (English): $EditInstruction")
[void]$log.Add("Refine rounds: $RefineRounds")
[void]$log.Add("")

# --- 1) Generate (截图->代码) ---
[void]$log.Add("[1] POST /generate ...")
$t0 = Get-Date
$b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($refPng))
$bodyG = @{
    image_base64 = $b64
    frame_name   = "Equipment Status Dashboard"
    width        = 1280
    height       = 720
} | ConvertTo-Json -Depth 5
$gen = Invoke-RestMethod -Uri "$base/generate" -Method Post -Body $bodyG `
    -ContentType "application/json; charset=utf-8" -TimeoutSec $RequestTimeoutSec
[void]$log.Add("    elapsed $([math]::Round(((Get-Date) - $t0).TotalSeconds,1))s")
Assert-Ui2CodeN
$code = $gen.code
$gen.code | Out-File (Join-Path $outDir "week003_01_generate.html") -Encoding utf8
Save-B64Png $gen.preview_base64 (Join-Path $shotDir "week003_01_generate_preview.png") | Out-Null
Write-CodeResponseJson $gen (Join-Path $outDir "week003_01_generate_response.json")
Write-B64Text $gen.preview_base64 (Join-Path $shotDir "week003_01_generate_preview.b64")
Copy-Item $refPng (Join-Path $shotDir "week003_00_reference.png") -Force
[void]$log.Add("    saved: week003_00_reference.png, week003_01_generate.html|.png|json|.b64")
[void]$log.Add("")

# --- 2) Edit (按指令改代码) — 对真实模型用英文指令，效果见 02 与 01 对比 ---
[void]$log.Add("[2] POST /edit ...")
$bodyE = @{
    current_code = $code
    instruction  = $EditInstruction
    width        = 1280
    height       = 720
} | ConvertTo-Json -Depth 8
$t1 = Get-Date
$ed = Invoke-RestMethod -Uri "$base/edit" -Method Post -Body $bodyE `
    -ContentType "application/json; charset=utf-8" -TimeoutSec $RequestTimeoutSec
[void]$log.Add("    elapsed $([math]::Round(((Get-Date) - $t1).TotalSeconds,1))s")
Assert-Ui2CodeN
$code = $ed.code
$ed.code | Out-File (Join-Path $outDir "week003_02_after_edit.html") -Encoding utf8
Save-B64Png $ed.preview_base64 (Join-Path $shotDir "week003_02_after_edit_preview.png") | Out-Null
Write-CodeResponseJson $ed (Join-Path $outDir "week003_02_after_edit_response.json")
Write-B64Text $ed.preview_base64 (Join-Path $shotDir "week003_02_after_edit_preview.b64")
[void]$log.Add("    saved: week003_02_*.html|png|json|b64  (主标题/排版相对 01 以视觉对比为准)`n")

# --- 3) 多轮 Refine：每轮 先 /render 当前码 -> 再 /refine，并保存当轮预览 ---
$codeRef = $code
for ($i = 1; $i -le $RefineRounds; $i++) {
    [void]$log.Add("[3.$i] render + refine, iteration $i ...")
    $bodyR0 = @{
        html_code = $codeRef
        width     = 1280
        height    = 720
    } | ConvertTo-Json
    $rend = Invoke-RestMethod -Uri "$base/render" -Method Post -Body $bodyR0 `
        -ContentType "application/json; charset=utf-8" -TimeoutSec 600
    $renderName = "week003_refine_iter${i}_a_render_in.png"
    Save-B64Png $rend.image_base64 (Join-Path $shotDir $renderName) | Out-Null
    Write-CodeResponseJson $rend (Join-Path $outDir "week003_refine_iter${i}_render_api.json")
    Write-B64Text $rend.image_base64 (Join-Path $shotDir "week003_refine_iter${i}_a_render_in.b64")

    $bodyRf = @{
        reference_image_base64  = $b64
        current_code            = $codeRef
        rendered_image_base64   = $rend.image_base64
        width                   = 1280
        height                  = 720
    } | ConvertTo-Json -Depth 5
    $t2 = Get-Date
    $rf = Invoke-RestMethod -Uri "$base/refine" -Method Post -Body $bodyRf `
        -ContentType "application/json; charset=utf-8" -TimeoutSec $RequestTimeoutSec
    [void]$log.Add("    refine elapsed $([math]::Round(((Get-Date) - $t2).TotalSeconds,1))s")
    Assert-Ui2CodeN
    $codeRef = $rf.code
    $fn = "week003_refine_iter${i}_b_preview.png"
    Save-B64Png $rf.preview_base64 (Join-Path $shotDir $fn) | Out-Null
    Write-CodeResponseJson $rf (Join-Path $outDir "week003_refine_iter${i}_refine_response.json")
    Write-B64Text $rf.preview_base64 (Join-Path $shotDir "week003_refine_iter${i}_b_preview.b64")
    $codeRef | Out-File (Join-Path $outDir "week003_refine_iter${i}.html") -Encoding utf8
    [void]$log.Add("    saved: $renderName, a_render_in.b64, $fn, b_preview.b64, *refine_response.json, week003_refine_iter$($i).html`n")
}

# --- 4) 导师可验收：Swagger 与 /health 快照（需服务仍在本机 8000） ---
$py = Join-Path $root "local-service\.venv\Scripts\python.exe"
$cap = Join-Path $root "local-service\capture_week3_evidence.py"
if ((Test-Path $py) -and (Test-Path $cap)) {
    [void]$log.Add("[4] capture Swagger + health JSON ...")
    & $py $cap --base $base --out-dir $shotDir
    if ($LASTEXITCODE -ne 0) { [void]$log.Add("    (optional evidence capture failed — check if server still up)") }
}

$summary = @"
=== 指令与预期变化 (Edit) ===
英文 instruction: $EditInstruction
中文: 让页面主标题字号更大、更醒目。请在 week003_01 与 week003_02 预览间对比；真实模型会改 HTML/CSS 中标题相关样式/结构。

=== Refine ===
每轮将「Figma 导出的参考图 + 上一步编辑后的代码经 /render 的图 + 当前 HTML」交回模型，使画面接近参考稿。
已保存 $RefineRounds 轮: 每轮有 *_a_render_input_iter*.png（进 refine 前渲染）与 *_b_refine_iter*_preview.png（refine 后服务返回的预览）。

=== 与 mockup 差异说明 ===
若早先结果与 01-equipment-status.png 差很大，多半是当时走了 rule_based 模板而非 VLM。本次脚本在 health 中强制 ui2code_n_active 通过后才落盘。

VERIFY: 运行结束后请访问 GET $base/health 应显示 ui2code_n_active: true
"@
$summary | Out-File (Join-Path $outDir "week003_RECORD.txt") -Encoding utf8
$log | Out-File (Join-Path $outDir "week003_RUN_LOG.txt") -Encoding utf8
Write-Host ($log -join "`n")
Write-Host $summary
