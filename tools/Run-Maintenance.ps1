param([ValidateSet('check','update','rollback','publish')][string]$Mode = 'check', [switch]$Scheduled)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
$local = Join-Path $root '.local\maintenance'
New-Item -ItemType Directory -Path $local -Force | Out-Null
$stamp = Join-Path $local ('scheduled-' + $Mode + '-success-date.txt')
$date = Get-Date -Format 'yyyy-MM-dd'
if ($Scheduled) {
    if ((Get-Date).Hour -lt 12) { exit 0 }
    if ((Test-Path -LiteralPath $stamp) -and ((Get-Content -LiteralPath $stamp -Raw).Trim() -eq $date)) { exit 0 }
}
$runtimeFile = Join-Path $local 'runtime-paths.json'
if (Test-Path -LiteralPath $runtimeFile) {
    $runtime = Get-Content -LiteralPath $runtimeFile -Raw | ConvertFrom-Json
    $env:PATH = $runtime.git + ';' + $runtime.node + ';' + $env:PATH
}
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$OutputEncoding = [Console]::OutputEncoding
$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Missing .venv. See docs/MAINTENANCE.md.' }
$log = Join-Path $local ('run-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.log')
$attempts = if ($Scheduled) { 2 } else { 1 }
for ($attempt = 1; $attempt -le $attempts; $attempt++) {
    if ($Mode -eq 'publish') {
        & $python -X utf8 (Join-Path $PSScriptRoot 'auto_update.py') 2>&1 | Tee-Object -FilePath $log -Append
    } else {
        & $python -X utf8 (Join-Path $PSScriptRoot 'maintain.py') $Mode 2>&1 | Tee-Object -FilePath $log -Append
    }
    $result = $LASTEXITCODE
    if ($result -eq 0) { break }
    if ($attempt -lt $attempts) { Start-Sleep -Seconds 15 }
}
if ($Scheduled -and $result -eq 0) { [IO.File]::WriteAllText($stamp,$date) }
exit $result
