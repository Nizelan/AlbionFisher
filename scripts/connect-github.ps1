# Connect D:\Projects\AlbionFisher to GitHub
# Usage: .\scripts\connect-github.ps1 [-RemoteUrl <url>] [-Branch main]

param(
    [string]$RemoteUrl = "https://github.com/Nizelan/AlbionFisher.git",
    [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

function Find-Git {
    $candidates = @(
        "git",
        "${env:ProgramFiles}\Git\cmd\git.exe",
        "${env:ProgramFiles(x86)}\Git\cmd\git.exe",
        "$env:LOCALAPPDATA\Programs\Git\cmd\git.exe"
    )
    foreach ($c in $candidates) {
        if ($c -eq "git") {
            $cmd = Get-Command git -ErrorAction SilentlyContinue
            if ($cmd) { return $cmd.Source }
        } elseif (Test-Path $c) {
            return $c
        }
    }
    return $null
}

$git = Find-Git
if (-not $git) {
    Write-Host "Git not found. Install from https://git-scm.com/download/win then re-run this script." -ForegroundColor Red
    exit 1
}

Write-Host "Using git: $git" -ForegroundColor Cyan

if (-not (Test-Path ".git")) {
    & $git init
    Write-Host "Initialized git repository." -ForegroundColor Green
} else {
    Write-Host "Git repository already exists." -ForegroundColor Yellow
}

$remotes = & $git remote 2>$null
if ($remotes -contains "origin") {
    $current = & $git remote get-url origin
    if ($current -ne $RemoteUrl) {
        Write-Host "Updating origin: $current -> $RemoteUrl"
        & $git remote set-url origin $RemoteUrl
    } else {
        Write-Host "Remote origin already set: $RemoteUrl" -ForegroundColor Green
    }
} else {
    & $git remote add origin $RemoteUrl
    Write-Host "Added remote origin: $RemoteUrl" -ForegroundColor Green
}

& $git add -A
$status = & $git status --porcelain
if ($status) {
    & $git commit -m "chore: loop engineering scaffold for AlbionFisher"
    Write-Host "Created initial commit." -ForegroundColor Green
} else {
    Write-Host "Nothing to commit (working tree clean)." -ForegroundColor Yellow
}

$currentBranch = & $git branch --show-current 2>$null
if ($currentBranch -ne $Branch) {
    & $git branch -M $Branch
}

Write-Host ""
Write-Host "Ready to push. Run:" -ForegroundColor Cyan
Write-Host "  & `"$git`" push -u origin $Branch" -ForegroundColor White
Write-Host ""
Write-Host "If push fails, authenticate with GitHub (HTTPS token or SSH key)." -ForegroundColor Yellow
