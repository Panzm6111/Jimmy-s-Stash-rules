param([ValidateSet('Start','Worker','Stop','Status','View','Report','Retry')][string]$Action='Status')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$python=Join-Path $root '.venv\Scripts\python.exe'
$program=Join-Path $PSScriptRoot 'stability.py'
$private=Join-Path $root '.local\stability'
[IO.Directory]::CreateDirectory($private) | Out-Null
if ($Action -in 'Start','Retry') {
    if ($Action -eq 'Retry') {
        $entry='retry'
    } else {
        $entry='resume'
    }
    $file=Join-Path $private 'supervisor.lock'
    try { $guard=[IO.File]::Open($file,'OpenOrCreate','ReadWrite','None'); $guard.Dispose() }
    catch { Write-Output 'Supervisor already running'; return }
    $env:JIMMY_STABILITY_ENTRY=$entry
    $p=Start-Process powershell.exe -WindowStyle Hidden -WorkingDirectory $root -PassThru -ArgumentList @(
        '-NoProfile','-ExecutionPolicy','Bypass','-File',('"' + $PSCommandPath + '"'),'Worker')
    Write-Output "Supervisor PID $($p.Id)"
} elseif ($Action -eq 'Worker') {
    $guard=[IO.File]::Open((Join-Path $private 'supervisor.lock'),'OpenOrCreate','ReadWrite','None')
    try {
        $entry=$env:JIMMY_STABILITY_ENTRY
        if ($entry -notin 'resume','retry') { $entry='run' }
        $backoff=5
        while ($true) {
            & $python -X utf8 $program $entry
            if ($LASTEXITCODE -eq 0 -or (Test-Path -LiteralPath (Join-Path $private 'stop'))) { break }
            Start-Sleep -Seconds $backoff
            $backoff=[Math]::Min(60,$backoff*2)
            $entry='run'
        }
    } finally { $guard.Dispose() }
} elseif ($Action -eq 'View') {
    try {
        $local=Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 -Uri 'http://127.0.0.1:18762/'
        if ($local.Content.Contains('id="trend"') -and $local.Content.Contains('id="capacity"')) {
            Write-Output 'http://127.0.0.1:18762/'
            return
        }
    } catch { }
    Start-Process $python -WindowStyle Hidden -WorkingDirectory $root -ArgumentList @('-X','utf8',('"' + $program + '"'),'view')
    Write-Output 'http://127.0.0.1:18762/'
} else {
    & $python -X utf8 $program $Action.ToLowerInvariant()
    $code=$LASTEXITCODE
    if ($Action -eq 'Stop' -and $code -eq 0) {
        $until=[DateTime]::UtcNow.AddSeconds(35)
        while ([DateTime]::UtcNow -lt $until) {
            try {
                $guard=[IO.File]::Open((Join-Path $private 'supervisor.lock'),'OpenOrCreate','ReadWrite','None')
                $guard.Dispose()
                Write-Output 'Collector supervisor stopped.'
                return
            } catch { Start-Sleep -Milliseconds 300 }
        }
        Write-Output 'Stop requested; waiting for outstanding work or supervisor backoff.'
    }
    exit $code
}
