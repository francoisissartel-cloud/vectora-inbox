# Script pour invoquer les Lambdas avec encodage correct
$ErrorActionPreference = "Stop"

# Créer le payload pour ingest-normalize
$ingestPayload = @{
    client_id = "lai_weekly"
    period_days = 7
}

# Convertir en JSON et sauvegarder avec encodage ASCII
$jsonPayload = $ingestPayload | ConvertTo-Json -Compress
[System.IO.File]::WriteAllText("$PWD\payload-ingest.json", $jsonPayload, [System.Text.Encoding]::ASCII)

Write-Host "=== Invocation de ingest-normalize ===" -ForegroundColor Cyan
aws lambda invoke `
  --function-name vectora-inbox-ingest-normalize-dev `
  --payload file://payload-ingest.json `
  --profile rag-lai-prod `
  --region eu-west-3 `
  out-ingest.json

if ($LASTEXITCODE -eq 0) {
    Write-Host "Ingest-normalize invoked successfully" -ForegroundColor Green
    $ingestResponse = Get-Content out-ingest.json | ConvertFrom-Json
    Write-Host ($ingestResponse | ConvertTo-Json -Depth 10)
    
    Write-Host "`n=== Waiting 10 seconds ===" -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    # Créer le payload pour engine
    $enginePayload = @{
        client_id = "lai_weekly"
        period_days = 7
    }
    
    $jsonPayload = $enginePayload | ConvertTo-Json -Compress
    [System.IO.File]::WriteAllText("$PWD\payload-engine.json", $jsonPayload, [System.Text.Encoding]::ASCII)
    
    Write-Host "`n=== Invocation de engine ===" -ForegroundColor Cyan
    aws lambda invoke `
      --function-name vectora-inbox-engine-dev `
      --payload file://payload-engine.json `
      --profile rag-lai-prod `
      --region eu-west-3 `
      out-engine.json
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Engine invoked successfully" -ForegroundColor Green
        $engineResponse = Get-Content out-engine.json | ConvertFrom-Json
        Write-Host ($engineResponse | ConvertTo-Json -Depth 10)
        
        # Extraire le chemin S3 de la newsletter
        if ($engineResponse.body.s3_output_path) {
            $s3Path = $engineResponse.body.s3_output_path
            Write-Host "`nNewsletter generated at: $s3Path" -ForegroundColor Green
            
            # Télécharger la newsletter
            $s3Path -match "s3://([^/]+)/(.+)" | Out-Null
            $bucket = $Matches[1]
            $key = $Matches[2]
            
            Write-Host "Downloading newsletter..." -ForegroundColor Yellow
            aws s3 cp s3://$bucket/$key newsletter-lai-weekly.md --profile rag-lai-prod --region eu-west-3
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Newsletter downloaded successfully" -ForegroundColor Green
            }
        }
    }
} else {
    Write-Host "Error invoking ingest-normalize" -ForegroundColor Red
}
