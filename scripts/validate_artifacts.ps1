param(
    [string]$StudyId,
    [string[]]$Artifact = @()
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$Python = Join-Path $RepoRoot "mcp-server\.venv\Scripts\python.exe"
$Validator = Join-Path $ScriptDir "validate_artifacts.py"

if (-not (Test-Path -LiteralPath $Python)) {
    Write-Error "Missing repo Python environment at $Python. Run: uv --directory mcp-server sync --all-extras --dev"
    exit 1
}

$ArgsList = @()
if ($StudyId) {
    $ArgsList += @("--study-id", $StudyId)
}
foreach ($Item in $Artifact) {
    $ArgsList += @("--artifact", $Item)
}

& $Python $Validator @ArgsList
exit $LASTEXITCODE
