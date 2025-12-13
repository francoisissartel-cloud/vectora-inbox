# Script de synchronisation pour lai_weekly_v3 client config
# Environnement : DEV
# Région : eu-west-3
# Profil : rag-lai-prod

param(
    [string]$Profile = "rag-lai-prod",
    [string]$Region = "eu-west-3",
    [string]$Env = "dev"
)

$ErrorActionPreference = "Stop"

Write-Host "=== Synchronisation LAI Weekly v3 Config - $Env ===" -ForegroundColor Green

# Variables
$ProjectName = "vectora-inbox"
$ConfigBucket = "$ProjectName-config-$Env"

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Profil AWS: $Profile"
Write-Host "  Région: $Region"
Write-Host "  Environnement: $Env"
Write-Host "  Config Bucket: $ConfigBucket"
Write-Host ""

# Étape 1 : Sync du client_config lai_weekly_v3.yaml vers S3
Write-Host "Étape 1 : Sync client_config lai_weekly_v3.yaml vers S3" -ForegroundColor Cyan

$ClientConfigLocal = "client-config-examples\lai_weekly_v3.yaml"
$ClientConfigS3Key = "clients/lai_weekly_v3.yaml"

if (Test-Path $ClientConfigLocal) {
    Write-Host "  Upload $ClientConfigLocal vers s3://$ConfigBucket/$ClientConfigS3Key"
    aws s3 cp $ClientConfigLocal "s3://$ConfigBucket/$ClientConfigS3Key" --profile $Profile --region $Region
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Client config lai_weekly_v3 uploadé avec succès" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Erreur lors de l'upload du client config" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  ❌ Fichier $ClientConfigLocal introuvable" -ForegroundColor Red
    exit 1
}

# Étape 2 : Vérification de l'accessibilité
Write-Host ""
Write-Host "Étape 2 : Vérification de l'accessibilité" -ForegroundColor Cyan

Write-Host "  Vérification de la présence du fichier en S3..."
aws s3 ls "s3://$ConfigBucket/$ClientConfigS3Key" --profile $Profile --region $Region

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ Fichier accessible en S3" -ForegroundColor Green
} else {
    Write-Host "  ❌ Fichier non accessible en S3" -ForegroundColor Red
    exit 1
}

# Étape 3 : Test de lecture du contenu
Write-Host ""
Write-Host "Étape 3 : Test de lecture du contenu" -ForegroundColor Cyan

Write-Host "  Téléchargement et vérification du contenu..."
aws s3 cp "s3://$ConfigBucket/$ClientConfigS3Key" "temp_lai_weekly_v3.yaml" --profile $Profile --region $Region

if ($LASTEXITCODE -eq 0 -and (Test-Path "temp_lai_weekly_v3.yaml")) {
    $Content = Get-Content "temp_lai_weekly_v3.yaml" -Raw
    
    # Vérifications clés
    $ClientIdFound = $Content -match 'client_id:\s*"lai_weekly_v3"'
    $PeriodDaysFound = $Content -match 'default_period_days:\s*30'
    $TrademarkScopeFound = $Content -match 'trademark_scope:\s*"lai_trademarks_global"'
    
    Write-Host "  Vérifications de contenu:" -ForegroundColor Yellow
    Write-Host "    client_id lai_weekly_v3: $(if($ClientIdFound){'✅'}else{'❌'})"
    Write-Host "    default_period_days 30: $(if($PeriodDaysFound){'✅'}else{'❌'})"
    Write-Host "    trademark_scope présent: $(if($TrademarkScopeFound){'✅'}else{'❌'})"
    
    # Nettoyage
    Remove-Item "temp_lai_weekly_v3.yaml" -Force
    
    if ($ClientIdFound -and $PeriodDaysFound -and $TrademarkScopeFound) {
        Write-Host "  ✅ Contenu validé avec succès" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Erreur dans le contenu du fichier" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  ❌ Erreur lors du téléchargement de vérification" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== Synchronisation Terminée ===" -ForegroundColor Green
Write-Host "lai_weekly_v3 est maintenant disponible pour les Lambdas en DEV" -ForegroundColor Yellow
Write-Host "Chemin S3: s3://$ConfigBucket/$ClientConfigS3Key" -ForegroundColor Yellow