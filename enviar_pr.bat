@echo off
title Enviar Pull Request - JENPEX Grupo 2
color 0a

echo ====================================================================
echo   ENVIANDO ALTERACOES DO GRUPO 2 PARA O REPOSITORIO (JENPEX)
echo   Autor: antonio-psrd-ifmt
echo   Branch: feature/grupo2-visao-panoramica
echo ====================================================================
echo.

set GIT_CMD="C:\Users\202510521070010\bin\git\cmd\git.exe"
where git >nul 2>nul
if %ERRORLEVEL% EQU 0 set GIT_CMD=git

echo [1/2] Enviando branch atualizada para o seu Fork no GitHub...
%GIT_CMD% push -u origin feature/grupo2-visao-panoramica

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ====================================================================
    echo [SUCESSO] Codigo enviado com sucesso para o seu Fork!
    echo [2/2] Abrindo pagina para criar o Pull Request para o professor...
    echo ====================================================================
    start "" "https://github.com/gusalv201/jenpex-ia-monitoramento/compare/main...antonio-psrd-ifmt:jenpex-ia-monitoramento:feature/grupo2-visao-panoramica?expand=1"
) else (
    echo.
    echo ====================================================================
    echo Se o Git pedir usuario e senha/token na janela:
    echo Usuario: antonio-psrd-ifmt
    echo Senha: Use seu Personal Access Token do GitHub
    echo ====================================================================
)

echo.
pause
