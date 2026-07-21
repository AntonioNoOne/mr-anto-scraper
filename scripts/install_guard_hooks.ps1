$ErrorActionPreference = "Stop"

if (-not (Test-Path ".git")) {
    throw "Run this from the repository root; .git not found."
}

git config core.hooksPath .githooks
Write-Host "Git hooks enabled: .githooks"
Write-Host "Test with: python scripts\project_guard.py"
