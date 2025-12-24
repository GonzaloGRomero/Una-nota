@echo off
echo Iniciando backend en desarrollo...
echo.

REM Activar entorno virtual si existe
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Iniciar servidor
python main.py
