param(
    [string[]]$SecretsToReplace = @(),
    [string]$BackupDir = "$env:USERPROFILE\\.git-filter-backup"
)

Set-Location "$PSScriptRoot\.."

if ($SecretsToReplace.Length -eq 0) {
    Write-Host "No secrets provided. Example usage:`n./prepare-git-filter-repo.ps1 -SecretsToReplace 'GEMINI_API_KEY' 'FRED_API_KEY'"
    exit 1
}

if (-not (Test-Path $BackupDir)) { New-Item -ItemType Directory -Path $BackupDir | Out-Null }

Write-Host "Preparing git-filter-repo command. This WILL rewrite history if executed."
Write-Host "Review the generated command before running it."

$replacements = @()
foreach ($s in $SecretsToReplace) {
    $escaped = [Regex]::Escape($s)
    $replacements += "--replace-text <(printf '%s\n' '$s')"
}

Write-Host "Example (manual) steps to run git-filter-repo safely:" 
Write-Host "1) Backup mirror: git clone --mirror <repo> repo-mirror.git"
Write-Host "2) cd repo-mirror.git"
Write-Host "3) Run git-filter-repo, e.g.:"
Write-Host "   git filter-repo --replace-text replacements.txt"
Write-Host "See https://github.com/newren/git-filter-repo for details."

# Create a simple replacements file
$replFile = Join-Path $PWD "security" "replacements.txt"
if (-not (Test-Path (Join-Path $PWD "security"))) { New-Item -ItemType Directory -Path (Join-Path $PWD "security") | Out-Null }

Remove-Item -Force $replFile -ErrorAction SilentlyContinue
foreach ($s in $SecretsToReplace) {
    Add-Content -Path $replFile -Value "$s==>[REDACTED]"
}

Write-Host "Wrote replacements file to $replFile"
Write-Host "When ready, run the filter-repo steps in a mirror clone to purge secrets from history."
