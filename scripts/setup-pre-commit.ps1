Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

python -m pip install --upgrade pip
python -m pip install pre-commit
pre-commit install --install-hooks

Write-Host ""
Write-Host "Pre-commit installed. Gitleaks will run automatically before each commit."
