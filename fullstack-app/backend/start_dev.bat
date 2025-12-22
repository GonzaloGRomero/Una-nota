@echo off
echo Iniciando backend en modo desarrollo...
echo.

REM Activar entorno virtual si existe
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Verificar si existe .env
if not exist .env (
    echo ADVERTENCIA: No se encontro archivo .env
    echo Crea un archivo .env con las variables necesarias
    echo.
)

REM Iniciar servidor
python main.py
pause
