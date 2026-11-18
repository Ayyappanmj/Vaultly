<#
.SYNOPSIS
    Vaultly development and operations management script for Windows PowerShell.
.PARAMETER Action
    Command to run: setup, dev, test, lint, migrate, seed, clean, help
#>
param(
    [Parameter(Position=0)]
    [ValidateSet("setup", "dev", "test", "lint", "migrate", "seed", "clean", "help")]
    [string]$Action = "help"
)

$ErrorActionPreference = "Stop"
$WorkspaceRoot = (Resolve-Path "$PSScriptRoot\..\..").Path
Set-Location $WorkspaceRoot

function Show-Help {
    Write-Host "Vaultly PowerShell Management CLI" -ForegroundColor Cyan
    Write-Host "Usage: .\infrastructure\scripts\vaultly.ps1 [command]"
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  setup    Initialize .env file, local directories, and verify prerequisites"
    Write-Host "  dev      Start the full stack with Docker Compose"
    Write-Host "  test     Run backend pytest and web checks"
    Write-Host "  lint     Run ruff (backend) and eslint (web)"
    Write-Host "  migrate  Apply database migrations with Alembic"
    Write-Host "  seed     Seed initial database data"
    Write-Host "  clean    Stop Docker containers, remove volumes and local cache files"
    Write-Host "  help     Show this help message"
}

function Invoke-Setup {
    Write-Host "==> Running Setup..." -ForegroundColor Green
    if (-not (Test-Path .env)) {
        Copy-Item .env.example .env
        Write-Host "Created .env from .env.example" -ForegroundColor Green
    } else {
        Write-Host ".env already exists." -ForegroundColor Yellow
    }

    if (-not (Test-Path uploads)) {
        New-Item -ItemType Directory -Path uploads -Force | Out-Null
        Write-Host "Created uploads/ directory." -ForegroundColor Green
    }

    # Verify tool availability
    Write-Host "Checking prerequisites:"
    $tools = @("docker", "python", "node", "flutter")
    foreach ($tool in $tools) {
        $found = Get-Command $tool -ErrorAction SilentlyContinue
        if ($found) {
            Write-Host "  [OK] $tool found at $($found.Source)" -ForegroundColor Green
        } else {
            Write-Host "  [MISSING] $tool is not installed or not in PATH" -ForegroundColor Yellow
        }
    }
}

function Invoke-Dev {
    Write-Host "==> Starting Vaultly stack..." -ForegroundColor Green
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error "Docker is not installed or not in PATH. Please install Docker Desktop with WSL2 to run the container stack."
    }
    docker compose up --build
}

function Invoke-Test {
    Write-Host "==> Running tests..." -ForegroundColor Green
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        Write-Host "Running Backend pytest..." -ForegroundColor Cyan
        & $pythonCmd.Source -m pytest -v backend/tests
    } else {
        Write-Host "Python not found in PATH." -ForegroundColor Red
    }

    if (Test-Path "web\node_modules") {
        Write-Host "Running Web build check..." -ForegroundColor Cyan
        cmd.exe /c "cd /d `"$WorkspaceRoot\web`" && npm run build"
    }

    if ((Get-Command flutter -ErrorAction SilentlyContinue) -and (Test-Path "mobile\pubspec.yaml")) {
        Write-Host "Running Mobile flutter test..." -ForegroundColor Cyan
        cmd.exe /c "cd /d `"$WorkspaceRoot\mobile`" && flutter test"
    }
}

function Invoke-Lint {
    Write-Host "==> Running linters..." -ForegroundColor Green
    $ruffCmd = Get-Command ruff -ErrorAction SilentlyContinue
    if ($ruffCmd) {
        Write-Host "Checking backend with ruff..." -ForegroundColor Cyan
        & $ruffCmd.Source check backend
        & $ruffCmd.Source format --check backend
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        python -m ruff check backend
        python -m ruff format --check backend
    } else {
        Write-Host "Ruff / Python not found." -ForegroundColor Yellow
    }

    if (Test-Path "web\node_modules") {
        Write-Host "Checking web with eslint..." -ForegroundColor Cyan
        cmd.exe /c "cd /d `"$WorkspaceRoot\web`" && npm run lint"
    }
}

function Invoke-Migrate {
    Write-Host "==> Applying database migrations..." -ForegroundColor Green
    $dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
    if ($dockerCmd) {
        docker compose exec backend alembic upgrade head
    } else {
        Write-Host "Applying migrations locally..." -ForegroundColor Cyan
        cmd.exe /c "cd /d `"$WorkspaceRoot\backend`" && alembic upgrade head"
    }
}

function Invoke-Seed {
    Write-Host "==> Seeding database..." -ForegroundColor Green
    $dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
    if ($dockerCmd) {
        docker compose exec backend python -m app.scripts.seed
    } else {
        cmd.exe /c "cd /d `"$WorkspaceRoot\backend`" && python -m app.scripts.seed"
    }
}

function Invoke-Clean {
    Write-Host "==> Cleaning environment..." -ForegroundColor Green
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        docker compose down -v --remove-orphans
    }
    @("backend\.pytest_cache", "backend\.ruff_cache", "web\.next") | ForEach-Object {
        if (Test-Path $_) {
            Remove-Item -Path $_ -Recurse -Force
            Write-Host "Removed $_" -ForegroundColor Yellow
        }
    }
}

switch ($Action) {
    "setup"   { Invoke-Setup }
    "dev"     { Invoke-Dev }
    "test"    { Invoke-Test }
    "lint"    { Invoke-Lint }
    "migrate" { Invoke-Migrate }
    "seed"    { Invoke-Seed }
    "clean"   { Invoke-Clean }
    Default   { Show-Help }
}
