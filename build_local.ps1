# scripts/build_local.ps1
Write-Host "Starting Local Build..." -ForegroundColor Cyan

# 1. Install Python Dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { Write-Error "Pip install failed"; exit 1 }
pip install pyinstaller
if ($LASTEXITCODE -ne 0) { Write-Error "PyInstaller install failed"; exit 1 }

# 2. Build Backend
Write-Host "Building Backend (PyInstaller)..." -ForegroundColor Yellow
pyinstaller --name ragkit-backend --onefile --clean ragkit/desktop/main.py
if ($LASTEXITCODE -ne 0) { Write-Error "Backend build failed"; exit 1 }

# 3. Move Binary
Write-Host "Moving Binary..." -ForegroundColor Yellow
$binDir = "desktop/src-tauri/binaries"
if (-not (Test-Path $binDir)) { New-Item -ItemType Directory -Path $binDir | Out-Null }
Copy-Item "dist/ragkit-backend.exe" "$binDir/ragkit-backend-x86_64-pc-windows-msvc.exe" -Force

# 4. Install Frontend Dependencies
Write-Host "Installing Frontend dependencies..." -ForegroundColor Yellow
cd desktop
npm install
if ($LASTEXITCODE -ne 0) { Write-Error "NPM install failed"; cd ..; exit 1 }

# 5. Build Tauri App
Write-Host "Building Tauri App..." -ForegroundColor Yellow
npm run tauri build
if ($LASTEXITCODE -ne 0) { Write-Error "Tauri build failed"; cd ..; exit 1 }

cd ..
Write-Host "Build Complete! Check desktop/src-tauri/target/release/bundle/nsis/" -ForegroundColor Green
