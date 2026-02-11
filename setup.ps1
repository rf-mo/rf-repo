$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

$venvPath = Join-Path $repoRoot '.venv'
$venvPython = Join-Path $venvPath 'Scripts\\python.exe'

if (-not (Test-Path $venvPython)) {
  Write-Host 'Creating Python virtual environment at .venv...'
  py -3.11 -m venv $venvPath
}

Write-Host 'Installing backend Python dependencies...'
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r (Join-Path $repoRoot 'backend\\requirements.txt')

Write-Host 'Installing root npm dependencies (concurrently)...'
npm install

Write-Host 'Installing frontend npm dependencies...'
npm --prefix frontend install

Write-Host 'Setup complete. Run `npm run dev` to start backend + frontend.'
