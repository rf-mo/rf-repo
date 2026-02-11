$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

if (-not (Test-Path (Join-Path $repoRoot '.venv\\Scripts\\python.exe'))) {
  Write-Host 'No virtual environment found. Running setup first...'
  & (Join-Path $repoRoot 'setup.ps1')
}

npm run dev
