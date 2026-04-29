@echo off
title NeveStudio
cd /d "%~dp0"

REM Caminho do Python configurado no projeto
set "PYTHON_EXE=C:\Users\lopesm21\Downloads\Outros\Python\Python311\python.exe"

REM Fallback: se o caminho acima nao existir, tenta o python do PATH
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"

"%PYTHON_EXE%" "%~dp0app.py"

if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao executar o NeveStudio.
    pause
)
