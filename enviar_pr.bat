@echo off
title Enviar Pull Request - JENPEX Grupo 2
color 0a

echo ====================================================================
echo   ENVIANDO ALTERACOES DO GRUPO 2 PARA O REPOSITORIO (JENPEX)
echo   Branch: feature/grupo2-visao-panoramica
echo ====================================================================
echo.

set GIT_CMD="C:\Users\202510521070010\bin\git\cmd\git.exe"
where git >nul 2>nul
if %ERRORLEVEL% EQU 0 set GIT_CMD=git

echo [1/2] Enviando branch atualizada para o GitHub...
%GIT_CMD% push -u origin feature/grupo2-visao-panoramica

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ====================================================================
    echo [SUCESSO] Codigo enviado com sucesso!
    echo [2/2] Abrindo pagina para criar o Pull Request no navegador...
    echo ====================================================================
    start "" "https://github.com/gusalv201/jenpex-ia-monitoramento/compare/main...feature/grupo2-visao-panoramica?expand=1"
) else (
    echo.
    echo ====================================================================
    echo [AVISO DE PERMISSAO]
    echo Se voce nao tem acesso direto de gravacao no repositorio do professor:
    echo.
    echo 1. Va em: https://github.com/gusalv201/jenpex-ia-monitoramento e clique em 'Fork'
    echo 2. Execute no PowerShell ou CMD:
    echo    git remote set-url origin https://github.com/SEU_USUARIO/jenpex-ia-monitoramento.git
    echo 3. Execute novamente este arquivo (enviar_pr.bat)
    echo ====================================================================
)

echo.
pause
