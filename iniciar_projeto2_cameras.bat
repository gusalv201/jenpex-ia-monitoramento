@echo off
title PROJETO 2 - Monitor de Ocupacao Panoramica (JENPEX)
color 0b

echo ====================================================================
echo        PROJETO 2: SISTEMA DE MONITORAMENTO PANORAMICO COM IA
echo        IFMT - JENPEX 2026 (Visao Panoramica + Recorde de Pessoas)
echo ====================================================================
echo.
echo Iniciando servidor e abrindo painel em http://localhost:5002...
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

start "" "http://localhost:5002"
%PYTHON_CMD% src\projeto2_dupla_camera\dual_camera_app.py

pause
