# 续跑：在上次已跑完 Generate + Edit 的前提下，只补跑多轮 Refine + Swagger/health 证据。
# 起点：week003_02_after_edit.html + mockups\png\01-equipment-status.png
# 前置：Uvicorn 已用 USE_REAL_MODEL=1 与真模型；可选 $env:API_BASE 指定服务地址。

$ErrorActionPreference = "Stop"
$base = if ($env:API_BASE -and $env:API_BASE.Trim() -ne "") { $env:API_BASE.Trim() } else { "http://127.0.0.1:8000" }
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$outDir = Join-Path $root "reports"
$shotDir = Join-Path $outDir "screenshots"
$refPng = Join-Path $root "mockups\png\01-equipment-status.png"
$htmlAfterEdit = Join-Path $outDir "week003_02_after_edit.html"
$RefineRounds = 3
$RequestTimeoutSec = 7200

if (-not (Test-Path $htmlAfterEdit)) { throw "Missing $htmlAfterEdit — run run_week3_verified.ps1 first (at least through /edit)." }

function Save-B64Png($B64, $Path) {
    if ([string]::IsNullOrEmpty($B64)) { return $false }
    [IO.File]::WriteAllBytes($Path, [Convert]::FromBase64String($B64))
    return $true
}
function Assert-Ui2CodeN {
    $h = Invoke-RestMethod -Uri "$base/health" -TimeoutSec 30
    if (-not $h.ui2code_n_active) { throw "Real UI2Code^N is not active. model_kind=$($h.model_kind)." }
}

$b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($refPng))
$codeRef = Get-Content -Path $htmlAfterEdit -Raw -Encoding utf8
$log = [System.Collections.ArrayList]@()
[void]$log.Add("=== resume refine $(Get-Date -Format o) ===")

for ($i = 1; $i -le $RefineRounds; $i++) {
    [void]$log.Add("[refine $i] render + POST /refine ...")
    $bodyR0 = @{ html_code = $codeRef; width = 1280; height = 720 } | ConvertTo-Json
    $rend = Invoke-RestMethod -Uri "$base/render" -Method Post -Body $bodyR0 -ContentType "application/json; charset=utf-8" -TimeoutSec 600
    $renderName = "week003_refine_iter${i}_a_render_in.png"
    Save-B64Png $rend.image_base64 (Join-Path $shotDir $renderName) | Out-Null
    $bodyRf = @{
        reference_image_base64  = $b64
        current_code            = $codeRef
        rendered_image_base64   = $rend.image_base64
        width                   = 1280
        height                  = 720
    } | ConvertTo-Json -Depth 5
    $rf = Invoke-RestMethod -Uri "$base/refine" -Method Post -Body $bodyRf -ContentType "application/json; charset=utf-8" -TimeoutSec $RequestTimeoutSec
    Assert-Ui2CodeN
    $codeRef = $rf.code
    Save-B64Png $rf.preview_base64 (Join-Path $shotDir "week003_refine_iter${i}_b_preview.png") | Out-Null
    $codeRef | Out-File (Join-Path $outDir "week003_refine_iter${i}.html") -Encoding utf8
    [void]$log.Add("    ok iter $i")
}
$py = Join-Path $root "local-service\.venv\Scripts\python.exe"
$cap = Join-Path $root "local-service\capture_week3_evidence.py"
if ((Test-Path $py) -and (Test-Path $cap)) { & $py $cap --base $base --out-dir $shotDir }
$log | Out-File (Join-Path $outDir "week003_RESUME_LOG.txt") -Encoding utf8
Write-Host ($log -join "`n"); Write-Host "Done. See reports\screenshots\week003_swagger_api_docs.png and week003_health_snapshot.json if capture succeeded."
