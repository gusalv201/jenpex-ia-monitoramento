@echo off
title Enviar Pull Request - JENPEX Grupo 2
color 0a

echo ====================================================================
echo   ENVIANDO ALTERACOES PARA O GITHUB (BRANCH: feature/grupo2-visao-panoramica)
echo ====================================================================
echo.

set GIT_CMD="C:\Users\202510521070010\bin\git\cmd\git.exe"
where git >nul 2>nul
if %ERRORLEVEL% EQU 0 set GIT_CMD=git

%GIT_CMD% push -u origin feature/grupo2-visao-panoramica

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ====================================================================
    echo [SUCESSO] Codigo enviado para o GitHub!
    echo Abrindo pagina para criacao do Pull Request no navegador...
    echo ====================================================================
    start "" "https://github.com/gusalv201/jenpex-ia-monitoramento/compare/main...feature/grupo2-visao-panoramica?expand=1"
) else (
    echo.
    echo ====================================================================
    echo [DICA] Caso nao tenha permissao de push direto no repositorio do professor:
    echo 1. Acesse https://github.com/gusalv201/jenpex-ia-monitoramento e clique em 'Fork'
    echo 2. Adicione seu fork: git remote set-url origin https://github.com/SEU_USUARIO/jenpex-ia-monitoramento.git
    echo 3. Execute novamente este arquivo para enviar e abrir o PR.
    echo ====================================================================
)

pause

