#!/usr/bin/env pwsh
Set-Location "$PSScriptRoot\.."

# Install detect-secrets and pre-commit into the active Python environment
python -m pip install --upgrade pip
python -m pip install detect-secrets pre-commit -q

# Run detect-secrets across the repo and write baseline
detect-secrets scan --all-files > .secrets.baseline

# Stage baseline and commit if changed
git add .secrets.baseline
try {
    git commit -m "chore(security): add detect-secrets baseline"
} catch {
    Write-Host "No baseline changes to commit"
}

Write-Host "detect-secrets baseline created at .secrets.baseline"
