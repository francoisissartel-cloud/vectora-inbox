# Script de déploiement pour la correction period_days client_config
# Environnement : DEV
# Région : eu-west-3
# Profil : rag-lai-prod

param(
    [string]$Profile = "rag-lai-prod",
    [string]$Region = "eu-west-3",
    [string]$Env = "dev"
)

$ErrorActionPreference = "Stop"

Write-Host "=== Déploiement Correction Period Days Client Config - $Env ===" -ForegroundColor Green

# Variables
$ProjectName = "vectora-inbox"
$ConfigBucket = "$ProjectName-config-$Env"
$DataBucket = "$ProjectName-data-$Env"

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Profil AWS: $Profile"
Write-Host "  Région: $Region"
Write-Host "  Environnement: $Env"
Write-Host "  Config Bucket: $ConfigBucket"
Write-Host ""

# Étape 1 : Sync du client_config lai_weekly_v2.yaml vers S3
Write-Host "Étape 1 : Sync client_config lai_weekly_v2.yaml vers S3" -ForegroundColor Cyan

$ClientConfigLocal = "client-config-examples\lai_weekly_v2.yaml"
$ClientConfigS3Key = "clients/lai_weekly_v2.yaml"

if (Test-Path $ClientConfigLocal) {
    Write-Host "  Upload $ClientConfigLocal vers s3://$ConfigBucket/$ClientConfigS3Key"
    aws s3 cp $ClientConfigLocal "s3://$ConfigBucket/$ClientConfigS3Key" --profile $Profile --region $Region
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Client config uploadé avec succès" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Erreur lors de l'upload du client config" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  ❌ Fichier $ClientConfigLocal introuvable" -ForegroundColor Red
    exit 1
}

# Étape 2 : Package et déploiement Lambda Engine
Write-Host ""
Write-Host "Étape 2 : Package et déploiement Lambda Engine" -ForegroundColor Cyan

# Créer le package
Write-Host "  Création du package engine..."
$PackageScript = "scripts\package-engine.ps1"
if (Test-Path $PackageScript) {
    & $PackageScript
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ❌ Erreur lors du packaging" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  ❌ Script de packaging introuvable : $PackageScript" -ForegroundColor Red
    exit 1
}

# Déployer la Lambda
$LambdaName = "$ProjectName-engine-$Env"
$ZipFile = "engine-v2-complete.zip"

if (Test-Path $ZipFile) {
    Write-Host "  Déploiement de $LambdaName..."
    aws lambda update-function-code --function-name $LambdaName --zip-file "fileb://$ZipFile" --profile $Profile --region $Region
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Lambda Engine déployée avec succès" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Erreur lors du déploiement de la Lambda Engine" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  ❌ Package $ZipFile introuvable" -ForegroundColor Red
    exit 1
}

# Étape 3 : Test de validation
Write-Host ""
Write-Host "Étape 3 : Test de validation" -ForegroundColor Cyan

$TestPayload = @{
    client_id = "lai_weekly_v2"
} | ConvertTo-Json -Compress

Write-Host "  Invocation de test avec payload : $TestPayload"

$TestResult = aws lambda invoke --function-name $LambdaName --payload $TestPayload --profile $Profile --region $Region response.json

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ Test d'invocation réussi" -ForegroundColor Green
    
    # Afficher les logs CloudWatch pour diagnostic
    Write-Host ""
    Write-Host "Étape 4 : Récupération des logs CloudWatch" -ForegroundColor Cyan
    
    $LogGroup = "/aws/lambda/$LambdaName"
    Write-Host "  Récupération des logs récents de $LogGroup..."
    
    # Attendre un peu pour que les logs soient disponibles
    Start-Sleep -Seconds 5
    
    $LogStreams = aws logs describe-log-streams --log-group-name $LogGroup --order-by LastEventTime --descending --max-items 1 --profile $Profile --region $Region | ConvertFrom-Json
    
    if ($LogStreams.logStreams.Count -gt 0) {
        $LatestStream = $LogStreams.logStreams[0].logStreamName
        Write-Host "  Stream le plus récent : $LatestStream"
        
        $LogEvents = aws logs get-log-events --log-group-name $LogGroup --log-stream-name $LatestStream --profile $Profile --region $Region | ConvertFrom-Json
        
        Write-Host ""
        Write-Host "=== LOGS DEBUG PERIOD_DAYS ===" -ForegroundColor Yellow
        foreach ($event in $LogEvents.events) {
            if ($event.message -like "*DEBUG*") {
                Write-Host $event.message -ForegroundColor White
            }
        }
        Write-Host "=== FIN LOGS DEBUG ===" -ForegroundColor Yellow
    }
    
} else {
    Write-Host "  ❌ Erreur lors du test d'invocation" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== Déploiement Terminé ===" -ForegroundColor Green
Write-Host "Vérifiez les logs DEBUG ci-dessus pour confirmer que :" -ForegroundColor Yellow
Write-Host "  1. Pipeline config contient default_period_days: 30" -ForegroundColor Yellow
Write-Host "  2. resolve_period_days() retourne 30" -ForegroundColor Yellow
Write-Host "  3. Fenêtre temporelle calculée utilise 30 jours" -ForegroundColor Yellow