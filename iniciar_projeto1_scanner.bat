@echo off
title PROJETO 1 - Scanner Inteligente de Objetos (JENPEX)
color 0a

echo ====================================================================
echo        PROJETO 1: SCANNER DE OBJETOS EM QUADRADO IMAGINARIO
echo ====================================================================
echo.
echo Iniciando servidor e abrindo interface em http://localhost:5001...
echo.

start "" "http://localhost:5001"
python src\projeto1_scanner\scanner_app.py

pause
