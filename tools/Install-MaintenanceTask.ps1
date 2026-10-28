param([string]$TaskName = 'Jimmy-Stash-Rules-Noon-Check')
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$local = Join-Path $root '.local\maintenance'
New-Item -ItemType Directory -Path $local -Force | Out-Null
$runtime = @{git=(Split-Path -Parent (Get-Command git -ErrorAction Stop).Source);node=(Split-Path -Parent (Get-Command node -ErrorAction Stop).Source)}
$runtime | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $local 'runtime-paths.json') -Encoding UTF8
$runner = Join-Path $PSScriptRoot 'Run-Maintenance.ps1'
$executable = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$action = New-ScheduledTaskAction -Execute $executable -Argument ('-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "' + $runner + '" -Mode publish -Scheduled') -WorkingDirectory $root
$daily = New-ScheduledTaskTrigger -Daily -At '12:00'
$user = [Security.Principal.WindowsIdentity]::GetCurrent().Name
$logon = New-ScheduledTaskTrigger -AtLogOn -User $user
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 1)
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing -and ($existing.Actions.Arguments -notlike ('*' + $runner + '*'))) { throw 'An unrelated task already uses that name; no changes applied.' }
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger @($daily,$logon) -Principal $principal -Settings $settings -Description 'Daily noon public-rule update; validate and publish relevant changes only; no private data.' -Force | Out-Null
$info = Get-ScheduledTaskInfo -TaskName $TaskName
[pscustomobject]@{Task=$TaskName;NextRun=$info.NextRunTime;TimeZone=(Get-TimeZone).Id;Runner=$runner} | Format-List
