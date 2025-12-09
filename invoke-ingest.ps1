$payload = '{"client_id":"lai_weekly","period_days":7}'
aws lambda invoke `
  --function-name vectora-inbox-ingest-normalize-dev `
  --cli-binary-format raw-in-base64-out `
  --payload $payload `
  --profile rag-lai-prod `
  --region eu-west-3 `
  out-ingest.json

if ($LASTEXITCODE -eq 0) {
    Write-Host "Lambda invoked successfully"
    Get-Content out-ingest.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
}
