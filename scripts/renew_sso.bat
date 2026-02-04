@echo off
REM Script de renouvellement automatique SSO AWS
REM A executer avant chaque session de travail

echo ========================================
echo Renouvellement Session AWS SSO
echo ========================================
echo.

echo [1/2] Renouvellement du token SSO...
aws sso login --profile rag-lai-prod

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [2/2] Verification de l'identite...
    aws sts get-caller-identity --profile rag-lai-prod --region eu-west-3
    
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo ========================================
        echo [OK] Session AWS active
        echo ========================================
        echo.
        echo Vous pouvez maintenant utiliser AWS CLI
        echo La session expirera dans quelques heures
        echo.
    ) else (
        echo.
        echo [ERREUR] Verification echouee
        exit /b 1
    )
) else (
    echo.
    echo [ERREUR] Renouvellement echoue
    exit /b 1
)
