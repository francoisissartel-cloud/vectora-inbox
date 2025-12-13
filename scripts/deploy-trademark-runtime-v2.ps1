# ============================================================================
# SCRIPT DE DEPLOIEMENT - TRADEMARK RUNTIME V2
# ============================================================================

param(
    [string]$Environment = "dev",
    [string]$Profile = "rag-lai-prod",
    [string]$Region = "eu-west-3",
    [switch]$SkipLambdas = $false,
    [switch]$SkipConfigs = $false
)

$ErrorActionPreference = "Stop"

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "DEPLOIEMENT TRADEMARK RUNTIME V2 - VECTORA INBOX" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Yellow
Write-Host "Profile AWS: $Profile" -ForegroundColor Yellow
Write-Host "Region: $Region" -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Cyan

# Variables d'environnement
$PROJECT_ROOT = Split-Path -Parent $PSScriptRoot
$CONFIG_BUCKET = "vectora-inbox-config-$Environment"
$DATA_BUCKET = "vectora-inbox-data-$Environment"

Write-Host "`n[INFO] Verification des buckets S3..." -ForegroundColor Green

# Verifier l'existence des buckets
try {
    aws s3 ls "s3://$CONFIG_BUCKET" --profile $Profile --region $Region | Out-Null
    Write-Host "[OK] Bucket config trouve: $CONFIG_BUCKET" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Bucket config introuvable: $CONFIG_BUCKET" -ForegroundColor Red
    Write-Host "[INFO] Commande utilisee: aws s3 ls s3://$CONFIG_BUCKET --profile $Profile --region $Region" -ForegroundColor Yellow
    exit 1
}

# ============================================================================
# ETAPE 1: SYNCHRONISATION DES CONFIGURATIONS CANONICAL
# ============================================================================

if (-not $SkipConfigs) {
    Write-Host "`n[ETAPE 1] Synchronisation des configurations canonical..." -ForegroundColor Cyan
    
    # Synchroniser le dossier canonical complet
    Write-Host "[INFO] Upload canonical/ vers S3..." -ForegroundColor Yellow
    aws s3 sync "$PROJECT_ROOT\canonical" "s3://$CONFIG_BUCKET/canonical" --profile $Profile --region $Region --delete
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Configurations canonical synchronisees" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Echec synchronisation canonical" -ForegroundColor Red
        Write-Host "[INFO] Commande utilisee: aws s3 sync canonical s3://$CONFIG_BUCKET/canonical --profile $Profile --region $Region --delete" -ForegroundColor Yellow
        exit 1
    }
    
    # Upload specifique du client lai_weekly_v2.yaml
    Write-Host "[INFO] Upload lai_weekly_v2.yaml..." -ForegroundColor Yellow
    aws s3 cp "$PROJECT_ROOT\client-config-examples\lai_weekly_v2.yaml" "s3://$CONFIG_BUCKET/clients/lai_weekly_v2.yaml" --profile $Profile --region $Region
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Client lai_weekly_v2 uploade" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Echec upload lai_weekly_v2.yaml" -ForegroundColor Red
        Write-Host "[INFO] Commande utilisee: aws s3 cp lai_weekly_v2.yaml s3://$CONFIG_BUCKET/clients/lai_weekly_v2.yaml --profile $Profile --region $Region" -ForegroundColor Yellow
        exit 1
    }
    
    # Verification des fichiers cles
    Write-Host "[INFO] Verification des fichiers cles..." -ForegroundColor Yellow
    $key_files = @(
        "canonical/scopes/trademark_scopes.yaml",
        "canonical/scopes/technology_scopes.yaml", 
        "canonical/scopes/company_scopes.yaml",
        "canonical/matching/domain_matching_rules.yaml",
        "canonical/scoring/scoring_rules.yaml",
        "clients/lai_weekly_v2.yaml"
    )
    
    foreach ($file in $key_files) {
        try {
            aws s3 ls "s3://$CONFIG_BUCKET/$file" --profile $Profile --region $Region | Out-Null
            Write-Host "[OK] Fichier present: $file" -ForegroundColor Green
        } catch {
            Write-Host "[WARNING] Fichier manquant: $file" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "`n[SKIP] Synchronisation configurations (--SkipConfigs)" -ForegroundColor Yellow
}

# ============================================================================
# ETAPE 2: RE-PACKAGING DES LAMBDAS
# ============================================================================

if (-not $SkipLambdas) {
    Write-Host "`n[ETAPE 2] Re-packaging des Lambdas avec modifications v2..." -ForegroundColor Cyan
    
    # Package ingest-normalize
    Write-Host "[INFO] Package ingest-normalize..." -ForegroundColor Yellow
    if (Test-Path "$PROJECT_ROOT\scripts\package-ingest-normalize.ps1") {
        & "$PROJECT_ROOT\scripts\package-ingest-normalize.ps1"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] ingest-normalize package" -ForegroundColor Green
        } else {
            Write-Host "[ERROR] Echec package ingest-normalize" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "[WARNING] Script package-ingest-normalize.ps1 introuvable" -ForegroundColor Yellow
    }
    
    # Package engine
    Write-Host "[INFO] Package engine..." -ForegroundColor Yellow
    if (Test-Path "$PROJECT_ROOT\scripts\package-engine.ps1") {
        & "$PROJECT_ROOT\scripts\package-engine.ps1"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] engine package" -ForegroundColor Green
        } else {
            Write-Host "[ERROR] Echec package engine" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "[WARNING] Script package-engine.ps1 introuvable" -ForegroundColor Yellow
    }
    
    # ============================================================================
    # ETAPE 3: DEPLOIEMENT DES LAMBDAS
    # ============================================================================
    
    Write-Host "`n[ETAPE 3] Deploiement des Lambdas..." -ForegroundColor Cyan
    
    # Deployer ingest-normalize
    Write-Host "[INFO] Deploiement ingest-normalize..." -ForegroundColor Yellow
    $ingest_zip = "$PROJECT_ROOT\ingest-normalize-rc0.zip"
    if (Test-Path $ingest_zip) {
        aws lambda update-function-code --function-name "vectora-inbox-ingest-normalize-$Environment" --zip-file "fileb://$ingest_zip" --profile $Profile --region $Region
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] ingest-normalize deploye" -ForegroundColor Green
        } else {
            Write-Host "[ERROR] Echec deploiement ingest-normalize" -ForegroundColor Red
            Write-Host "[INFO] Commande utilisee: aws lambda update-function-code --function-name vectora-inbox-ingest-normalize-$Environment --zip-file fileb://$ingest_zip --profile $Profile --region $Region" -ForegroundColor Yellow
            exit 1
        }
    } else {
        Write-Host "[WARNING] Fichier ZIP ingest-normalize introuvable: $ingest_zip" -ForegroundColor Yellow
    }
    
    # Deployer engine
    Write-Host "[INFO] Deploiement engine..." -ForegroundColor Yellow
    $engine_zip = "$PROJECT_ROOT\engine-complete.zip"
    if (Test-Path $engine_zip) {
        aws lambda update-function-code --function-name "vectora-inbox-engine-$Environment" --zip-file "fileb://$engine_zip" --profile $Profile --region $Region
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] engine deploye" -ForegroundColor Green
        } else {
            Write-Host "[ERROR] Echec deploiement engine" -ForegroundColor Red
            Write-Host "[INFO] Commande utilisee: aws lambda update-function-code --function-name vectora-inbox-engine-$Environment --zip-file fileb://$engine_zip --profile $Profile --region $Region" -ForegroundColor Yellow
            exit 1
        }
    } else {
        Write-Host "[WARNING] Fichier ZIP engine introuvable: $engine_zip" -ForegroundColor Yellow
    }
} else {
    Write-Host "`n[SKIP] Re-packaging et deploiement Lambdas (--SkipLambdas)" -ForegroundColor Yellow
}

# ============================================================================
# ETAPE 4: VALIDATION DU DEPLOIEMENT
# ============================================================================

Write-Host "`n[ETAPE 4] Validation du deploiement..." -ForegroundColor Cyan

# Test de configuration lai_weekly_v2
Write-Host "[INFO] Test chargement lai_weekly_v2..." -ForegroundColor Yellow
try {
    $config_content = aws s3 cp "s3://$CONFIG_BUCKET/clients/lai_weekly_v2.yaml" - --profile $Profile --region $Region
    if ($config_content -match "template_version.*2\.0\.0") {
        Write-Host "[OK] Config v2 detectee dans lai_weekly_v2.yaml" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] Config v2 non detectee" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[ERROR] Impossible de lire lai_weekly_v2.yaml" -ForegroundColor Red
}

# Test des fonctions Lambda
Write-Host "[INFO] Test des fonctions Lambda..." -ForegroundColor Yellow

# Test ingest-normalize
try {
    $ingest_info = aws lambda get-function --function-name "vectora-inbox-ingest-normalize-$Environment" --profile $Profile --region $Region | ConvertFrom-Json
    $last_modified = $ingest_info.Configuration.LastModified
    Write-Host "[OK] ingest-normalize actif (derniere modif: $last_modified)" -ForegroundColor Green
} catch {
    Write-Host "[WARNING] Fonction ingest-normalize inaccessible" -ForegroundColor Yellow
}

# Test engine
try {
    $engine_info = aws lambda get-function --function-name "vectora-inbox-engine-$Environment" --profile $Profile --region $Region | ConvertFrom-Json
    $last_modified = $engine_info.Configuration.LastModified
    Write-Host "[OK] engine actif (derniere modif: $last_modified)" -ForegroundColor Green
} catch {
    Write-Host "[WARNING] Fonction engine inaccessible" -ForegroundColor Yellow
}

Write-Host "`n============================================================================" -ForegroundColor Cyan
Write-Host "DEPLOIEMENT TERMINE" -ForegroundColor Green
Write-Host "Profile: $Profile | Region: $Region | Environment: $Environment" -ForegroundColor Yellow
Write-Host "Config Bucket: $CONFIG_BUCKET" -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Cyan