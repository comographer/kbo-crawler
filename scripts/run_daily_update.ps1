[CmdletBinding()]
param(
	[ValidateRange(2000, 2100)]
	[int]$Year = 2026,
	[switch]$DryRun
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$pythonPath = Join-Path $repoRoot ".venv\Scripts\python.exe"
$logRoot = Join-Path ([Environment]::GetFolderPath("LocalApplicationData")) "KBO Dashboard\logs"
$logPath = Join-Path $logRoot ("daily-update-{0:yyyy-MM}.log" -f (Get-Date))

New-Item -ItemType Directory -Path $logRoot -Force | Out-Null

function Write-UpdateLog {
	param([string]$Message)
	$line = "[{0:yyyy-MM-dd HH:mm:ss}] {1}" -f (Get-Date), $Message
	$line | Tee-Object -FilePath $logPath -Append
}

if (-not (Test-Path -LiteralPath $pythonPath)) {
	Write-UpdateLog "FAILED: Virtual environment Python was not found at $pythonPath"
	exit 1
}

$arguments = @("src/main.py", "--daily", "--year", $Year, "--push")
Write-UpdateLog "START: $pythonPath $($arguments -join ' ')"

if ($DryRun) {
	Write-UpdateLog "DRY RUN: Command was not executed."
	exit 0
}

Push-Location $repoRoot
try {
	& $pythonPath @arguments 2>&1 | Tee-Object -FilePath $logPath -Append
	$exitCode = $LASTEXITCODE
	if ($exitCode -ne 0) {
		throw "Crawler exited with code $exitCode."
	}
	Write-UpdateLog "SUCCESS: Daily update completed."
}
catch {
	Write-UpdateLog "FAILED: $($_.Exception.Message)"
	exit 1
}
finally {
	Pop-Location
}
