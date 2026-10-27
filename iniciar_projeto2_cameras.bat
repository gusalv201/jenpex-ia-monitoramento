@echo off
title PROJETO 2 - Sistema de Dupla Camera (JENPEX)
color 0b

echo ====================================================================
echo        PROJETO 2: SISTEMA DE DUPLA CAMERA (PANORAMICA + PORTA)
echo ====================================================================
echo.
echo Iniciando servidor e abrindo painel em http://localhost:5002...
echo.

start "" "http://localhost:5002"
python src\projeto2_dupla_camera\dual_camera_app.py

pause
