param(
  [Parameter(Mandatory=$true)]
  [ValidateSet("local","smoke","ci","detect")]
  [string]$Mode
)

$ErrorActionPreference = "Stop"

function Fail($msg) {
  Write-Host "[ERROR] $msg" -ForegroundColor Red
  exit 1
}

function Info($msg) {
  Write-Host "[INFO]  $msg" -ForegroundColor Cyan
}

function Ok($msg) {
  Write-Host "[OK]    $msg" -ForegroundColor Green
}

function RequireCmd($name, $hint) {
  if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
    Fail "Missing required tool: $name. $hint"
  }
}

function DetectProfile() {
  $backendMarkers = @(
    "services/api/pyproject.toml",
    "services/backend/pyproject.toml",
    "backend/pyproject.toml"
  )
  $frontendMarkers = @(
    "frontend/package.json",
    "web/package.json",
    "ui/package.json"
  )

  $hasBackend = $false
  foreach ($path in $backendMarkers) {
    if (Test-Path $path) {
      $hasBackend = $true
      break
    }
  }

  $hasFrontend = $false
  foreach ($path in $frontendMarkers) {
    if (Test-Path $path) {
      $hasFrontend = $true
      break
    }
  }

  $profile = "scaffold-only"
  if ($hasBackend -and $hasFrontend) {
    $profile = "backend+frontend"
  } elseif ($hasBackend) {
    $profile = "backend-present"
  } elseif ($hasFrontend) {
    $profile = "frontend-present"
  }

  return [PSCustomObject]@{
    Profile = $profile
    HasBackend = $hasBackend
    HasFrontend = $hasFrontend
  }
}

function InvokeMake($target) {
  Info "Running make $target"
  & make $target
  if ($LASTEXITCODE -ne 0) {
    Fail "make $target failed with exit code $LASTEXITCODE"
  }
}

function InvokeDockerComposeMake($target) {
  Info "Running docker compose wrapper for make $target"
  & docker compose -f docker-compose.dev.yml run --rm dev make $target
  if ($LASTEXITCODE -ne 0) {
    Fail "docker compose wrapper failed for make $target with exit code $LASTEXITCODE"
  }
}

# Hard stop: forbid fake/placeholder verification artifacts.
$forbidden = @(
  ".agentkit/scripts/verify_contract.py",
  "services/api/scripts/placeholder_checks.py",
  "frontend/scripts/placeholder-task.cjs"
)
foreach ($path in $forbidden) {
  if (Test-Path $path) {
    Fail "Forbidden placeholder verification artifact detected: $path. Remove it and restore real toolchain-based verification."
  }
}

$hasComposeFile = Test-Path "docker-compose.dev.yml"
$inDevContainer = $env:IN_DEV_CONTAINER -eq "1"
$useDockerWrapper = $hasComposeFile -and (-not $inDevContainer)

if ($useDockerWrapper) {
  RequireCmd docker "Install Docker Desktop and ensure 'docker' is on PATH."
  Info "Detected docker-compose.dev.yml on host. Container-first wrapper mode is active."
  Info "Running verification mode: $Mode"
  Info "Repo root: $(Get-Location)"

  switch ($Mode) {
    "detect" {
      InvokeDockerComposeMake "detect"
      Ok "detect completed"
      exit 0
    }
    "smoke" {
      InvokeDockerComposeMake "verify-smoke"
      Ok "verify-smoke passed"
      exit 0
    }
    "local" {
      InvokeDockerComposeMake "verify-local"
      Ok "verify-local passed"
      exit 0
    }
    "ci" {
      InvokeDockerComposeMake "verify-ci"
      Ok "verify-ci passed"
      exit 0
    }
  }
}

# Base tools are always required.
RequireCmd git "Install Git for Windows."
RequireCmd python "Install Python 3.13+ and ensure 'python' is on PATH."
RequireCmd make "Install GNU Make (e.g., via Chocolatey) OR run verify.sh from Git Bash. Recommended: install 'make' for Windows."

$profile = DetectProfile
Info "Detected verification profile: $($profile.Profile)"

Info "Running verification mode: $Mode"
Info "Repo root: $(Get-Location)"

if ($Mode -ne "detect") {
  # Profile-aware requirements:
  # - scaffold-only: no uv/node/pnpm required
  # - backend-present: uv required
  # - frontend-present: node + pnpm required
  if ($profile.HasBackend) {
    RequireCmd uv "Install uv and ensure it is on PATH."
  }
  if ($profile.HasFrontend) {
    RequireCmd node "Install Node.js 20+ and ensure it is on PATH."
    RequireCmd pnpm "Install pnpm and ensure it is on PATH."
  }
}

switch ($Mode) {
  "detect" {
    InvokeMake "detect"
    Ok "detect completed"
  }
  "smoke" {
    InvokeMake "verify-smoke"
    Ok "verify-smoke passed"
  }
  "local" {
    InvokeMake "verify-local"
    Ok "verify-local passed"
  }
  "ci" {
    InvokeMake "verify-ci"
    Ok "verify-ci passed"
  }
}
