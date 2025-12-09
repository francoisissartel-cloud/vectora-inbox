# Script de test de la Lambda engine après le patch Markdown
# Ce script invoque la Lambda et vérifie que le Markdown est correct

$ErrorActionPreference = "Stop"

# Variables
$PROFILE = "rag-lai-prod"
$REGION = "eu-west-3"
$LAMBDA_NAME = "vectora-inbox-engine-dev"
$NEWSLETTERS_BUCKET = "vectora-inbox-newsletters-dev"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Lambda Engine - Patch Markdown" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Étape 1 : Créer le payload de test
Write-Host "[1/4] Création du payload de test..." -ForegroundColor Yellow
$PAYLOAD = @{
    client_id = "lai_weekly"
    period_days = 7
} | ConvertTo-Json

$PAYLOAD | Out-File -FilePath "test-event-engine-patch.json" -Encoding utf8

# Étape 2 : Invoquer la Lambda
Write-Host "[2/4] Invocation de la Lambda..." -ForegroundColor Yellow
aws lambda invoke `
    --function-name $LAMBDA_NAME `
    --payload file://test-event-engine-patch.json `
    --profile $PROFILE `
    --region $REGION `
    out-engine-patch.json | Out-Null

# Afficher la réponse
Write-Host ""
Write-Host "Réponse Lambda :" -ForegroundColor Green
$RESPONSE = Get-Content out-engine-patch.json | ConvertFrom-Json
$RESPONSE | ConvertTo-Json -Depth 10

# Vérifier le statut
if ($RESPONSE.statusCode -ne 200) {
    Write-Host ""
    Write-Host "ERREUR : La Lambda a retourné un statut $($RESPONSE.statusCode)" -ForegroundColor Red
    exit 1
}

# Extraire le chemin S3
$S3_PATH = $RESPONSE.body.s3_output_path
$S3_PATH_PARTS = $S3_PATH -replace "s3://", "" -split "/"
$BUCKET = $S3_PATH_PARTS[0]
$KEY = $S3_PATH_PARTS[1..($S3_PATH_PARTS.Length - 1)] -join "/"

Write-Host ""
Write-Host "[3/4] Téléchargement de la newsletter depuis S3..." -ForegroundColor Yellow
Write-Host "Chemin : $S3_PATH" -ForegroundColor White

# Télécharger le Markdown
aws s3 cp "s3://$BUCKET/$KEY" newsletter-patch.md `
    --profile $PROFILE `
    --region $REGION

# Télécharger le JSON éditorial (si présent)
$JSON_KEY = $KEY -replace "newsletter.md", "newsletter.json"
try {
    aws s3 cp "s3://$BUCKET/$JSON_KEY" newsletter-patch.json `
        --profile $PROFILE `
        --region $REGION 2>$null
    $JSON_EXISTS = $true
} catch {
    $JSON_EXISTS = $false
}

Write-Host ""
Write-Host "[4/4] Vérification du contenu..." -ForegroundColor Yellow

# Lire le contenu Markdown
$MD_CONTENT = Get-Content newsletter-patch.md -Raw

# Vérifier que ce n'est PAS du JSON brut
if ($MD_CONTENT -match '```json') {
    Write-Host ""
    Write-Host "❌ ÉCHEC : La newsletter contient encore du JSON brut !" -ForegroundColor Red
    Write-Host ""
    Write-Host "Contenu (premiers 500 caractères) :" -ForegroundColor Yellow
    Write-Host $MD_CONTENT.Substring(0, [Math]::Min(500, $MD_CONTENT.Length))
    exit 1
}

# Vérifier que c'est du Markdown valide
if ($MD_CONTENT -match '^# .+' -and $MD_CONTENT -match '## .+') {
    Write-Host ""
    Write-Host "✅ SUCCÈS : La newsletter est en Markdown lisible !" -ForegroundColor Green
    Write-Host ""
    Write-Host "Aperçu de la newsletter :" -ForegroundColor Cyan
    Write-Host "----------------------------------------" -ForegroundColor Gray
    Write-Host $MD_CONTENT.Substring(0, [Math]::Min(1000, $MD_CONTENT.Length))
    if ($MD_CONTENT.Length -gt 1000) {
        Write-Host "..." -ForegroundColor Gray
    }
    Write-Host "----------------------------------------" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Taille totale : $($MD_CONTENT.Length) caractères" -ForegroundColor White
    
    if ($JSON_EXISTS) {
        Write-Host ""
        Write-Host "✅ Fichier JSON éditorial également créé : newsletter-patch.json" -ForegroundColor Green
    }
} else {
    Write-Host ""
    Write-Host "⚠️ AVERTISSEMENT : Le format Markdown semble incomplet" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Contenu complet :" -ForegroundColor Yellow
    Write-Host $MD_CONTENT
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Test terminé" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Fichiers générés :" -ForegroundColor Cyan
Write-Host "  - newsletter-patch.md (Markdown)" -ForegroundColor White
if ($JSON_EXISTS) {
    Write-Host "  - newsletter-patch.json (JSON éditorial)" -ForegroundColor White
}
Write-Host "  - out-engine-patch.json (Réponse Lambda)" -ForegroundColor White
Write-Host "  - test-event-engine-patch.json (Payload de test)" -ForegroundColor White
