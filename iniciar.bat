@echo off
title JENPEX Vision - Monitor Panoramico de Ocupacao (IFMT)
color 0b

echo ====================================================================
echo        PROJETO 2 (GRUPO 2): MONITOR DE OCUPACAO PANORAMICA
echo        IFMT - JENPEX 2026 (Visao Panoramica + Recorde de Pessoas)
echo ====================================================================
echo.
echo [1/2] Abrindo painel no navegador em http://localhost:5002...
start "" "http://localhost:5002"
echo.
echo [2/2] Iniciando o servidor de visao computacional...
echo.

set PYTHON_CMD=python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    if exist "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" (
        set PYTHON_CMD="%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe"
    ) else (
        set PYTHON_CMD=py
    )
)

%PYTHON_CMD% src\projeto2_dupla_camera\dual_camera_app.py

pause
