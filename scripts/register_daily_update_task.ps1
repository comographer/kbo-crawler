[CmdletBinding()]
param(
	[ValidateRange(2000, 2100)]
	[int]$Year = 2026,
	[string]$TaskName = "KBO Dashboard Daily Update"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$runnerPath = Join-Path $PSScriptRoot "run_daily_update.ps1"
$powerShellPath = Join-Path $PSHOME "powershell.exe"
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

if (-not (Test-Path -LiteralPath $runnerPath)) {
	throw "Daily update runner was not found at $runnerPath"
}

$actionArguments = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "{0}" -Year {1}' -f $runnerPath, $Year
$action = New-ScheduledTaskAction `
	-Execute $powerShellPath `
	-Argument $actionArguments `
	-WorkingDirectory $repoRoot
$trigger = New-ScheduledTaskTrigger `
	-Weekly `
	-WeeksInterval 1 `
	-DaysOfWeek Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday `
	-At 11:55PM
$settings = New-ScheduledTaskSettingsSet `
	-StartWhenAvailable `
	-WakeToRun `
	-AllowStartIfOnBatteries `
	-DontStopIfGoingOnBatteries `
	-ExecutionTimeLimit (New-TimeSpan -Hours 3) `
	-MultipleInstances IgnoreNew
$principal = New-ScheduledTaskPrincipal `
	-UserId $currentUser `
	-LogonType Interactive `
	-RunLevel Limited

Register-ScheduledTask `
	-TaskName $TaskName `
	-Action $action `
	-Trigger $trigger `
	-Settings $settings `
	-Principal $principal `
	-Description "Crawl, commit, and push KBO data Tuesday through Sunday at 23:55." `
	-Force | Out-Null

$task = Get-ScheduledTask -TaskName $TaskName
$taskInfo = Get-ScheduledTaskInfo -TaskName $TaskName
Write-Output "Registered task: $($task.TaskName)"
Write-Output "State: $($task.State)"
Write-Output "Next run: $($taskInfo.NextRunTime)"
Write-Output "User: $currentUser (runs only while logged on)"
