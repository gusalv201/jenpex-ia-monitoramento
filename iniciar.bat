@echo off
title JENPEX Vision - Monitor de Ocupacao em Tempo Real
color 0b

echo ====================================================================
echo             JENPEX VISION - MONITOR DE OCUPACAO COM IA
echo ====================================================================
echo.
echo [1/2] Iniciando o servidor de visao computacional e dashboard...
echo.

start "" "http://localhost:5000"
python src\app.py

pause
