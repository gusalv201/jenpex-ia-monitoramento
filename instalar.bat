@echo off
title Instalador de Dependencias - JENPEX Vision
color 0a

echo ====================================================================
echo        INSTALADOR DE DEPENDENCIAS - JENPEX VISION (IA)
echo ====================================================================
echo.
echo Instalando pacotes necessarios (Flask, OpenCV, Ultralytics YOLOv8)...
echo.

pip install -r requirements.txt

echo.
echo ====================================================================
echo   Instalacao concluida com sucesso!
echo   Voce ja pode clicar em 'iniciar.bat' para rodar o projeto.
echo ====================================================================
pause
