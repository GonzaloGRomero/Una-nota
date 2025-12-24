@echo off
echo ========================================
echo   Iniciando Entorno de Desarrollo Local
echo ========================================
echo.

REM Verificar que estamos en el directorio correcto
if not exist "backend\main.py" (
    echo ERROR: No se encontro backend\main.py
    echo Asegurate de ejecutar este script desde la raiz del proyecto
    pause
    exit /b 1
)

if not exist "frontend\package.json" (
    echo ERROR: No se encontro frontend\package.json
    echo Asegurate de ejecutar este script desde la raiz del proyecto
    pause
    exit /b 1
)

echo [1/4] Verificando archivos .env...
if not exist "backend\.env" (
    echo   - Creando backend\.env desde .env.example...
    if exist "backend\.env.example" (
        copy "backend\.env.example" "backend\.env" >nul
        echo   - Archivo creado. Editalo si necesitas agregar credenciales.
    ) else (
        echo   - ADVERTENCIA: No se encontro backend\.env.example
    )
) else (
    echo   - backend\.env existe
)

if not exist "frontend\.env" (
    echo   - Creando frontend\.env desde .env.example...
    if exist "frontend\.env.example" (
        copy "frontend\.env.example" "frontend\.env" >nul
        echo   - Archivo creado.
    ) else (
        echo   - ADVERTENCIA: No se encontro frontend\.env.example
    )
) else (
    echo   - frontend\.env existe
)

echo.
echo [2/4] Verificando entorno virtual del backend...
if not exist "backend\venv" (
    echo   - Creando entorno virtual...
    cd backend
    python -m venv venv
    cd ..
    echo   - Entorno virtual creado.
) else (
    echo   - Entorno virtual existe
)

echo.
echo [3/4] Instalando dependencias del backend...
cd backend
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo   - Instalando paquetes Python...
    pip install -q -r requirements.txt
    echo   - Dependencias instaladas.
) else (
    echo   - ADVERTENCIA: No se pudo activar el entorno virtual
)
cd ..

echo.
echo [4/4] Verificando dependencias del frontend...
if not exist "frontend\node_modules" (
    echo   - Instalando paquetes npm (esto puede tardar)...
    cd frontend
    call npm install
    cd ..
    echo   - Dependencias instaladas.
) else (
    echo   - node_modules existe
)

echo.
echo ========================================
echo   Iniciando servidores...
echo ========================================
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Presiona Ctrl+C en cualquier terminal para detener los servidores
echo.

REM Iniciar backend en una nueva ventana
start "Backend - Local" cmd /k "cd /d %~dp0backend && if exist venv\Scripts\activate.bat (call venv\Scripts\activate.bat && python main.py) else (python main.py)"

REM Esperar un poco para que el backend inicie
timeout /t 3 /nobreak >nul

REM Iniciar frontend en una nueva ventana
start "Frontend - Local" cmd /k "cd /d %~dp0frontend && npm start"

echo.
echo Servidores iniciados en ventanas separadas.
echo Cierra esta ventana cuando termines.
pause
