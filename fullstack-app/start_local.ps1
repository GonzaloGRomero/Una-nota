# Script PowerShell para iniciar entorno de desarrollo local
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Iniciando Entorno de Desarrollo Local" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "backend\main.py")) {
    Write-Host "ERROR: No se encontro backend\main.py" -ForegroundColor Red
    Write-Host "Asegurate de ejecutar este script desde la raiz del proyecto" -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}

if (-not (Test-Path "frontend\package.json")) {
    Write-Host "ERROR: No se encontro frontend\package.json" -ForegroundColor Red
    Write-Host "Asegurate de ejecutar este script desde la raiz del proyecto" -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}

Write-Host "[1/4] Verificando archivos .env..." -ForegroundColor Yellow
if (-not (Test-Path "backend\.env")) {
    Write-Host "  - Creando backend\.env desde .env.example..." -ForegroundColor Gray
    if (Test-Path "backend\.env.example") {
        Copy-Item "backend\.env.example" "backend\.env"
        Write-Host "  - Archivo creado. Editalo si necesitas agregar credenciales." -ForegroundColor Green
    } else {
        Write-Host "  - ADVERTENCIA: No se encontro backend\.env.example" -ForegroundColor Yellow
    }
} else {
    Write-Host "  - backend\.env existe" -ForegroundColor Green
}

if (-not (Test-Path "frontend\.env")) {
    Write-Host "  - Creando frontend\.env desde .env.example..." -ForegroundColor Gray
    if (Test-Path "frontend\.env.example") {
        Copy-Item "frontend\.env.example" "frontend\.env"
        Write-Host "  - Archivo creado." -ForegroundColor Green
    } else {
        Write-Host "  - ADVERTENCIA: No se encontro frontend\.env.example" -ForegroundColor Yellow
    }
} else {
    Write-Host "  - frontend\.env existe" -ForegroundColor Green
}

Write-Host ""
Write-Host "[2/4] Verificando entorno virtual del backend..." -ForegroundColor Yellow
if (-not (Test-Path "backend\venv")) {
    Write-Host "  - Creando entorno virtual..." -ForegroundColor Gray
    Set-Location backend
    python -m venv venv
    Set-Location ..
    Write-Host "  - Entorno virtual creado." -ForegroundColor Green
} else {
    Write-Host "  - Entorno virtual existe" -ForegroundColor Green
}

Write-Host ""
Write-Host "[3/4] Instalando dependencias del backend..." -ForegroundColor Yellow
Set-Location backend
if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
    Write-Host "  - Instalando paquetes Python..." -ForegroundColor Gray
    pip install -q -r requirements.txt
    Write-Host "  - Dependencias instaladas." -ForegroundColor Green
} else {
    Write-Host "  - ADVERTENCIA: No se pudo activar el entorno virtual" -ForegroundColor Yellow
}
Set-Location ..

Write-Host ""
Write-Host "[4/4] Verificando dependencias del frontend..." -ForegroundColor Yellow
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "  - Instalando paquetes npm (esto puede tardar)..." -ForegroundColor Gray
    Set-Location frontend
    npm install
    Set-Location ..
    Write-Host "  - Dependencias instaladas." -ForegroundColor Green
} else {
    Write-Host "  - node_modules existe" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Iniciando servidores..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend: http://localhost:8000" -ForegroundColor Green
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Green
Write-Host ""
Write-Host "Presiona Ctrl+C en cualquier terminal para detener los servidores" -ForegroundColor Yellow
Write-Host ""

# Iniciar backend en una nueva ventana
$backendPath = Join-Path $PSScriptRoot "backend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendPath'; if (Test-Path 'venv\Scripts\Activate.ps1') { . venv\Scripts\Activate.ps1; python main.py } else { python main.py }" -WindowStyle Normal

# Esperar un poco para que el backend inicie
Start-Sleep -Seconds 3

# Iniciar frontend en una nueva ventana
$frontendPath = Join-Path $PSScriptRoot "frontend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; npm start" -WindowStyle Normal

Write-Host ""
Write-Host "Servidores iniciados en ventanas separadas." -ForegroundColor Green
Write-Host "Cierra esta ventana cuando termines." -ForegroundColor Yellow
Read-Host "Presiona Enter para cerrar esta ventana"
