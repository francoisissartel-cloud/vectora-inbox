@echo off
REM Upload tous les fichiers canonical manquants sur S3

echo ========================================
echo UPLOAD FICHIERS CANONICAL VERS S3
echo ========================================
echo.
echo Bucket: vectora-inbox-data-dev
echo Fichiers: 18 manquants
echo.

set PROFILE=rag-lai-prod
set BUCKET=vectora-inbox-data-dev

echo [1/18] company_scopes.yaml...
aws s3 cp canonical/scopes/company_scopes.yaml s3://%BUCKET%/canonical/scopes/company_scopes.yaml --profile %PROFILE%

echo [2/18] domain_definitions.yaml...
aws s3 cp canonical/scopes/domain_definitions.yaml s3://%BUCKET%/canonical/scopes/domain_definitions.yaml --profile %PROFILE%

echo [3/18] domain_matching_rules.yaml...
aws s3 cp canonical/matching/domain_matching_rules.yaml s3://%BUCKET%/canonical/matching/domain_matching_rules.yaml --profile %PROFILE%

echo [4/18] event_type_definitions.yaml...
aws s3 cp canonical/events/event_type_definitions.yaml s3://%BUCKET%/canonical/events/event_type_definitions.yaml --profile %PROFILE%

echo [5/18] event_type_patterns.yaml...
aws s3 cp canonical/events/event_type_patterns.yaml s3://%BUCKET%/canonical/events/event_type_patterns.yaml --profile %PROFILE%

echo [6/18] exclusion_scopes.yaml...
aws s3 cp canonical/scopes/exclusion_scopes.yaml s3://%BUCKET%/canonical/scopes/exclusion_scopes.yaml --profile %PROFILE%

echo [7/18] generic_normalization.yaml...
aws s3 cp canonical/prompts/normalization/generic_normalization.yaml s3://%BUCKET%/canonical/prompts/normalization/generic_normalization.yaml --profile %PROFILE%

echo [8/18] html_extractors.yaml...
aws s3 cp canonical/sources/html_extractors.yaml s3://%BUCKET%/canonical/sources/html_extractors.yaml --profile %PROFILE%

echo [9/18] indication_scopes.yaml...
aws s3 cp canonical/scopes/indication_scopes.yaml s3://%BUCKET%/canonical/scopes/indication_scopes.yaml --profile %PROFILE%

echo [10/18] ingestion_profiles.yaml...
aws s3 cp canonical/ingestion/ingestion_profiles.yaml s3://%BUCKET%/canonical/ingestion/ingestion_profiles.yaml --profile %PROFILE%

echo [11/18] lai_editorial.yaml...
aws s3 cp canonical/prompts/editorial/lai_editorial.yaml s3://%BUCKET%/canonical/prompts/editorial/lai_editorial.yaml --profile %PROFILE%

echo [12/18] molecule_scopes.yaml...
aws s3 cp canonical/scopes/molecule_scopes.yaml s3://%BUCKET%/canonical/scopes/molecule_scopes.yaml --profile %PROFILE%

echo [13/18] scoring_rules.yaml...
aws s3 cp canonical/scoring/scoring_rules.yaml s3://%BUCKET%/canonical/scoring/scoring_rules.yaml --profile %PROFILE%

echo [14/18] source_catalog.yaml...
aws s3 cp canonical/sources/source_catalog.yaml s3://%BUCKET%/canonical/sources/source_catalog.yaml --profile %PROFILE%

echo [15/18] source_catalog_backup.yaml...
aws s3 cp canonical/sources/source_catalog_backup.yaml s3://%BUCKET%/canonical/sources/source_catalog_backup.yaml --profile %PROFILE%

echo [16/18] technology_scopes.yaml...
aws s3 cp canonical/scopes/technology_scopes.yaml s3://%BUCKET%/canonical/scopes/technology_scopes.yaml --profile %PROFILE%

echo [17/18] trademark_scopes.yaml...
aws s3 cp canonical/scopes/trademark_scopes.yaml s3://%BUCKET%/canonical/scopes/trademark_scopes.yaml --profile %PROFILE%

echo [18/18] vectora-inbox-lai-core-scopes.yaml...
aws s3 cp canonical/imports/vectora-inbox-lai-core-scopes.yaml s3://%BUCKET%/canonical/imports/vectora-inbox-lai-core-scopes.yaml --profile %PROFILE%

echo.
echo ========================================
echo [OK] Upload termine
echo ========================================
echo.
echo Verification...
aws s3 ls s3://%BUCKET%/canonical/ --recursive --profile %PROFILE%
