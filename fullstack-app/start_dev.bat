@echo off
echo ========================================
echo   Iniciando Entorno de Desarrollo
echo ========================================
echo.

REM Verificar que estamos en el directorio correcto
if not exist "backend\main.py" (
    echo ERROR: No se encontro backend\main.py
    echo Ejecuta este script desde la raiz del proyecto
    pause
    exit /b 1
)

REM Iniciar backend en una nueva ventana
start "Backend - Desarrollo" cmd /k "cd /d %~dp0backend && if exist venv\Scripts\activate.bat (call venv\Scripts\activate.bat && python main.py) else (python main.py)"

REM Esperar un poco para que el backend inicie
timeout /t 3 /nobreak >nul

REM Iniciar frontend en una nueva ventana
start "Frontend - Desarrollo" cmd /k "cd /d %~dp0frontend && npm start"

echo.
echo Servidores iniciados en ventanas separadas.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Cierra esta ventana cuando termines.
pause
