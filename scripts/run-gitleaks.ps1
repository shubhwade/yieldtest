param(
    [string]$OutputFile = "security/gitleaks-report.json"
)

Set-Location "$PSScriptRoot\.."

if (-not (Test-Path "security")) { New-Item -ItemType Directory -Path "security" | Out-Null }

Write-Host "Running gitleaks via Docker (requires Docker installed and running)"

if (Get-Command docker -ErrorAction SilentlyContinue) {
    docker run --rm -v "${PWD}:/repo" -w /repo zricethezav/gitleaks:latest detect --source /repo --report-path /repo/$OutputFile --report-format json
    Write-Host "Gitleaks report saved to $OutputFile"
} else {
    Write-Host "Docker is not available. To run gitleaks locally, install gitleaks or Docker."
    Write-Host "Install gitleaks: https://github.com/gitleaks/gitleaks#installation"
}
