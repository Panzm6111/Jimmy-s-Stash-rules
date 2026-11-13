param(
    [ValidateRange(3,5)][int]$Days = 5,
    [string]$Session
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$pythonWindowless = Join-Path $projectRoot '.venv\Scripts\pythonw.exe'
$recorder = Join-Path $PSScriptRoot 'clash_monitor.py'
if (!(Test-Path -LiteralPath $pythonWindowless)) { throw 'Expected existing venv pythonw.exe' }
if (!$Session) {
    $Session = (& $python -X utf8 $recorder create --days $Days | Select-Object -Last 1).Trim()
    if ($LASTEXITCODE -ne 0) { throw 'Session creation failed' }
}
$sessionPath = (Resolve-Path -LiteralPath $Session).Path
$settingsJson = Get-Content -LiteralPath $sessionPath -Raw -Encoding UTF8 | ConvertFrom-Json
$sessionRoot = [IO.Path]::GetFullPath((Join-Path $projectRoot '.local\clash-monitor')) + [IO.Path]::DirectorySeparatorChar
if (!$sessionPath.StartsWith($sessionRoot,[StringComparison]::OrdinalIgnoreCase)) { throw 'Session must stay in this project local monitor folder' }
$deadline = [DateTimeOffset]::FromUnixTimeSeconds([long][Math]::Floor($settingsJson.end)).LocalDateTime
if ($deadline -le (Get-Date)) { throw 'Monitoring deadline already passed' }
$taskName = 'Jimmy-Clash-Usage-Monitor-' + (Split-Path -Leaf (Split-Path -Parent $sessionPath))
$arguments = '-X utf8 "' + $recorder + '" run --session "' + $sessionPath + '"'
$action = New-ScheduledTaskAction -Execute $pythonWindowless -Argument $arguments -WorkingDirectory $projectRoot
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddSeconds(10) -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration ($deadline - (Get-Date))
$trigger.EndBoundary = $deadline.ToString('yyyy-MM-ddTHH:mm:ss')
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Days 6) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
$principal = New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
$definition = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description 'Temporary passive Clash Verge usage monitor; no node probing or core configuration writes; bounded by session deadline.'
Register-ScheduledTask -TaskName $taskName -InputObject $definition | Out-Null
Start-ScheduledTask -TaskName $taskName
$receipt = [ordered]@{ task=$taskName; session=$sessionPath; deadline=$deadline.ToString('o'); executable=$pythonWindowless; auto_resume='Every 5 minutes while logged on; no wake timer'; rules_changed=$false }
$receipt | ConvertTo-Json | Set-Content -LiteralPath (Join-Path (Split-Path -Parent $sessionPath) 'installation.json') -Encoding UTF8
$receipt | ConvertTo-Json
