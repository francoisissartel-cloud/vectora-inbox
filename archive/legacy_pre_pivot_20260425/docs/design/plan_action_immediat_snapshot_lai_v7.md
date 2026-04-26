# Plan d'Action Immédiat - Sauvegarde lai_weekly_v7

**Date**: 2026-01-30  
**Priorité**: CRITIQUE  
**Durée estimée**: 30 minutes  
**Objectif**: Sauvegarder l'état actuel du moteur lai_weekly_v7 fonctionnel

---

## 🎯 OBJECTIF

Créer un point de sauvegarde complet de l'environnement dev actuel avec le POC lai_weekly_v7 fonctionnel, avant toute modification future.

**Pourquoi c'est critique:**
- ✅ Moteur fonctionne actuellement (avec problèmes de bruit mais fonctionnel)
- ⚠️ Modifications futures risquent de casser le moteur
- ⚠️ Pas de point de restauration actuellement
- ⚠️ Impossible de revenir en arrière si problème

---

## 📋 COMMANDES À EXÉCUTER

### Étape 1: Créer Dossier de Sauvegarde

```powershell
# Se placer à la racine du projet
cd "C:\Users\franc\OneDrive\Bureau\vectora-inbox"

# Créer dossier snapshot avec timestamp
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$snapshot_dir = "backup\snapshots\lai_v7_stable_$timestamp"
New-Item -ItemType Directory -Path $snapshot_dir -Force

# Créer sous-dossiers
New-Item -ItemType Directory -Path "$snapshot_dir\lambdas" -Force
New-Item -ItemType Directory -Path "$snapshot_dir\layers" -Force
New-Item -ItemType Directory -Path "$snapshot_dir\clients" -Force
New-Item -ItemType Directory -Path "$snapshot_dir\canonical" -Force
New-Item -ItemType Directory -Path "$snapshot_dir\stacks" -Force
New-Item -ItemType Directory -Path "$snapshot_dir\data" -Force

Write-Host "✅ Dossier snapshot créé: $snapshot_dir"
```

### Étape 2: Sauvegarder Configurations Lambda

```powershell
# Lambda ingest-v2-dev
aws lambda get-function `
  --function-name vectora-inbox-ingest-v2-dev `
  --profile rag-lai-prod `
  --region eu-west-3 `
  --query Configuration `
  > "$snapshot_dir\lambdas\ingest-v2-dev.json"

# Lambda normalize-score-v2-dev
aws lambda get-function `
  --function-name vectora-inbox-normalize-score-v2-dev `
  --profile rag-lai-prod `
  --region eu-west-3 `
  --query Configuration `
  > "$snapshot_dir\lambdas\normalize-score-v2-dev.json"

# Lambda newsletter-v2-dev
aws lambda get-function `
  --function-name vectora-inbox-newsletter-v2-dev `
  --profile rag-lai-prod `
  --region eu-west-3 `
  --query Configuration `
  > "$snapshot_dir\lambdas\newsletter-v2-dev.json"

Write-Host "✅ Configurations Lambda sauvegardées"
```

### Étape 3: Sauvegarder Versions Lambda Layers

```powershell
# Layer vectora-core-dev
aws lambda list-layer-versions `
  --layer-name vectora-inbox-vectora-core-dev `
  --profile rag-lai-prod `
  --region eu-west-3 `
  --max-items 1 `
  > "$snapshot_dir\layers\vectora-core-dev.json"

# Layer common-deps-dev
aws lambda list-layer-versions `
  --layer-name vectora-inbox-common-deps-dev `
  --profile rag-lai-prod `
  --region eu-west-3 `
  --max-items 1 `
  > "$snapshot_dir\layers\common-deps-dev.json"

# Layer vectora-core-approche-b-dev
aws lambda list-layer-versions `
  --layer-name vectora-inbox-vectora-core-approche-b-dev `
  --profile rag-lai-prod `
  --region eu-west-3 `
  --max-items 1 `
  > "$snapshot_dir\layers\vectora-core-approche-b-dev.json"

Write-Host "✅ Versions Lambda Layers sauvegardées"
```

### Étape 4: Sauvegarder Configuration Client lai_weekly_v7

```powershell
# Configuration client lai_weekly_v7
aws s3 cp `
  s3://vectora-inbox-config-dev/clients/lai_weekly_v7.yaml `
  "$snapshot_dir\clients\lai_weekly_v7.yaml" `
  --profile rag-lai-prod `
  --region eu-west-3

# Copier aussi depuis local (backup)
Copy-Item `
  "client-config-examples\lai_weekly_v7.yaml" `
  "$snapshot_dir\clients\lai_weekly_v7_local.yaml"

Write-Host "✅ Configuration client lai_weekly_v7 sauvegardée"
```

### Étape 5: Sauvegarder Canonical (Scopes, Prompts, Sources)

```powershell
# Synchroniser tout le dossier canonical
aws s3 sync `
  s3://vectora-inbox-config-dev/canonical/ `
  "$snapshot_dir\canonical\" `
  --profile rag-lai-prod `
  --region eu-west-3

Write-Host "✅ Canonical sauvegardé (scopes, prompts, sources)"
```

### Étape 6: Sauvegarder Dernières Données Curated

```powershell
# Dernière exécution lai_weekly_v7
aws s3 cp `
  s3://vectora-inbox-data-dev/curated/lai_weekly_v7/2026/01/29/items.json `
  "$snapshot_dir\data\curated_items_20260129.json" `
  --profile rag-lai-prod `
  --region eu-west-3

Write-Host "✅ Dernières données curated sauvegardées"
```

### Étape 7: Sauvegarder Stacks CloudFormation

```powershell
# Stack S0-core-dev
aws cloudformation describe-stacks `
  --stack-name vectora-inbox-s0-core-dev `
  --profile rag-lai-prod `
  --region eu-west-3 `
  > "$snapshot_dir\stacks\s0-core-dev.json"

# Stack S0-iam-dev
aws cloudformation describe-stacks `
  --stack-name vectora-inbox-s0-iam-dev `
  --profile rag-lai-prod `
  --region eu-west-3 `
  > "$snapshot_dir\stacks\s0-iam-dev.json"

# Stack S1-runtime-dev
aws cloudformation describe-stacks `
  --stack-name vectora-inbox-s1-runtime-dev `
  --profile rag-lai-prod `
  --region eu-west-3 `
  > "$snapshot_dir\stacks\s1-runtime-dev.json"

Write-Host "✅ Stacks CloudFormation sauvegardées"
```

### Étape 8: Créer README Snapshot

```powershell
$readme_content = @"
# Snapshot Vectora Inbox: lai_v7_stable

**Date**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
**Environnement**: dev
**Client**: lai_weekly_v7
**Statut**: Moteur fonctionnel (avec problèmes de bruit à optimiser)

## Contexte

Ce snapshot capture l'état du moteur Vectora Inbox avec le POC lai_weekly_v7 fonctionnel.

**Workflow validé:**
```
ingest-v2 → normalize-score-v2 → newsletter-v2
```

**Dernière exécution réussie:**
- Date: 2026-01-29
- Items curated: ~62KB
- Configuration: lai_weekly_v7.yaml

**Problèmes connus:**
- Bruit dans les résultats (à optimiser)
- Prompts à améliorer
- Extraction dates à valider

## Contenu du Snapshot

### Lambdas (3 fonctions)
- vectora-inbox-ingest-v2-dev
- vectora-inbox-normalize-score-v2-dev
- vectora-inbox-newsletter-v2-dev

### Lambda Layers
- vectora-inbox-vectora-core-dev (v42)
- vectora-inbox-common-deps-dev (v4)
- vectora-inbox-vectora-core-approche-b-dev (v10)

### Configurations
- lai_weekly_v7.yaml (client)
- Canonical complet (scopes, prompts, sources)

### Données
- Derniers items curated (2026-01-29)

### Infrastructure
- Stacks CloudFormation (S0-core, S0-iam, S1-runtime)

## Restauration

Pour restaurer ce snapshot:

``````powershell
# Restaurer configuration client
aws s3 cp `
  "$snapshot_dir\clients\lai_weekly_v7.yaml" `
  s3://vectora-inbox-config-dev/clients/lai_weekly_v7.yaml `
  --profile rag-lai-prod `
  --region eu-west-3

# Restaurer canonical
aws s3 sync `
  "$snapshot_dir\canonical\" `
  s3://vectora-inbox-config-dev/canonical/ `
  --profile rag-lai-prod `
  --region eu-west-3

# Restaurer versions Lambda (voir ARNs dans lambdas/*.json)
``````

## Versions Exactes

Voir fichiers JSON dans chaque sous-dossier pour versions exactes:
- `lambdas/*.json`: Configurations Lambda complètes
- `layers/*.json`: ARNs et versions layers
- `stacks/*.json`: Paramètres et outputs stacks

## Notes

Ce snapshot est le point de référence pour le moteur lai_weekly_v7 fonctionnel.
Toute modification future doit pouvoir revenir à cet état en cas de problème.

---

**Créé par**: Plan d'action immédiat sauvegarde lai_v7
**Timestamp**: $timestamp
"@

$readme_content | Out-File -FilePath "$snapshot_dir\README.md" -Encoding UTF8

Write-Host "✅ README snapshot créé"
```

### Étape 9: Créer Métadonnées JSON

```powershell
$metadata = @{
    snapshot_name = "lai_v7_stable"
    timestamp = $timestamp
    created_at = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
    environment = "dev"
    client_id = "lai_weekly_v7"
    status = "functional_with_noise"
    components = @{
        lambdas = @(
            "vectora-inbox-ingest-v2-dev",
            "vectora-inbox-normalize-score-v2-dev",
            "vectora-inbox-newsletter-v2-dev"
        )
        layers = @(
            "vectora-inbox-vectora-core-dev",
            "vectora-inbox-common-deps-dev",
            "vectora-inbox-vectora-core-approche-b-dev"
        )
        buckets = @(
            "vectora-inbox-config-dev",
            "vectora-inbox-data-dev",
            "vectora-inbox-newsletters-dev"
        )
        stacks = @(
            "vectora-inbox-s0-core-dev",
            "vectora-inbox-s0-iam-dev",
            "vectora-inbox-s1-runtime-dev"
        )
    }
    known_issues = @(
        "Bruit dans résultats (à optimiser)",
        "Prompts à améliorer",
        "Extraction dates à valider"
    )
    last_successful_run = "2026-01-29"
}

$metadata | ConvertTo-Json -Depth 10 | Out-File -FilePath "$snapshot_dir\snapshot_metadata.json" -Encoding UTF8

Write-Host "✅ Métadonnées JSON créées"
```

### Étape 10: Résumé Final

```powershell
Write-Host ""
Write-Host "=" * 70
Write-Host "✅ SNAPSHOT CRÉÉ AVEC SUCCÈS"
Write-Host "=" * 70
Write-Host ""
Write-Host "Nom: lai_v7_stable_$timestamp"
Write-Host "Dossier: $snapshot_dir"
Write-Host ""
Write-Host "Contenu sauvegardé:"
Write-Host "  ✅ 3 configurations Lambda"
Write-Host "  ✅ 3 versions Lambda Layers"
Write-Host "  ✅ Configuration client lai_weekly_v7"
Write-Host "  ✅ Canonical complet (scopes, prompts, sources)"
Write-Host "  ✅ Dernières données curated"
Write-Host "  ✅ 3 stacks CloudFormation"
Write-Host "  ✅ README et métadonnées"
Write-Host ""
Write-Host "Taille totale:"
$size = (Get-ChildItem -Path $snapshot_dir -Recurse | Measure-Object -Property Length -Sum).Sum / 1KB
Write-Host "  $([math]::Round($size, 1)) KB"
Write-Host ""
Write-Host "=" * 70
Write-Host ""
Write-Host "🎯 PROCHAINES ÉTAPES:"
Write-Host ""
Write-Host "1. Vérifier contenu snapshot dans: $snapshot_dir"
Write-Host "2. Tester restauration partielle (config client)"
Write-Host "3. Documenter snapshot dans docs/snapshots/"
Write-Host "4. Continuer travail incrémental en toute sécurité"
Write-Host ""
Write-Host "💡 Pour restaurer ce snapshot:"
Write-Host "   Voir instructions dans $snapshot_dir\README.md"
Write-Host ""
```

---

## 🔍 VÉRIFICATION POST-SNAPSHOT

### Checklist de Validation

Après exécution des commandes, vérifier:

- [ ] Dossier `backup/snapshots/lai_v7_stable_YYYYMMDD_HHMMSS/` créé
- [ ] Sous-dossier `lambdas/` contient 3 fichiers JSON
- [ ] Sous-dossier `layers/` contient 3 fichiers JSON
- [ ] Sous-dossier `clients/` contient lai_weekly_v7.yaml
- [ ] Sous-dossier `canonical/` contient scopes/, prompts/, sources/
- [ ] Sous-dossier `data/` contient curated_items_20260129.json
- [ ] Sous-dossier `stacks/` contient 3 fichiers JSON
- [ ] Fichier `README.md` créé
- [ ] Fichier `snapshot_metadata.json` créé
- [ ] Taille totale > 50 KB (minimum attendu)

### Test de Restauration Partielle

Pour valider que le snapshot est utilisable:

```powershell
# Test: Restaurer configuration client dans un bucket temporaire
aws s3 cp `
  "$snapshot_dir\clients\lai_weekly_v7.yaml" `
  s3://vectora-inbox-config-dev/clients/lai_weekly_v7_test_restore.yaml `
  --profile rag-lai-prod `
  --region eu-west-3

# Vérifier que le fichier est identique
aws s3 cp `
  s3://vectora-inbox-config-dev/clients/lai_weekly_v7_test_restore.yaml `
  "test_restore.yaml" `
  --profile rag-lai-prod `
  --region eu-west-3

# Comparer
fc "$snapshot_dir\clients\lai_weekly_v7.yaml" "test_restore.yaml"

# Nettoyer
Remove-Item "test_restore.yaml"
aws s3 rm s3://vectora-inbox-config-dev/clients/lai_weekly_v7_test_restore.yaml `
  --profile rag-lai-prod `
  --region eu-west-3

Write-Host "✅ Test de restauration réussi"
```

---

## 📝 DOCUMENTATION SNAPSHOT

### Créer Fiche Snapshot

Créer `docs/snapshots/lai_v7_stable_YYYYMMDD.md`:

```markdown
# Snapshot lai_v7_stable - YYYYMMDD

## Résumé

Snapshot de l'environnement dev avec POC lai_weekly_v7 fonctionnel.

## État du Moteur

**Statut**: ✅ Fonctionnel (avec optimisations à faire)

**Workflow validé:**
- ingest-v2: Ingestion sources LAI
- normalize-score-v2: Normalisation + matching + scoring
- newsletter-v2: Génération newsletter

**Dernière exécution:**
- Date: 2026-01-29
- Items ingérés: ~15
- Items curated: ~10
- Newsletter générée: ✅

**Problèmes connus:**
- Bruit dans résultats (taux à mesurer)
- Prompts à optimiser (extraction dates, matching)
- Scoring à affiner (seuils)

## Versions Composants

**Lambdas:**
- ingest-v2-dev: Python 3.12, 512MB, 300s timeout
- normalize-score-v2-dev: Python 3.11, 512MB, 300s timeout
- newsletter-v2-dev: Python 3.11, 512MB, 300s timeout

**Layers:**
- vectora-core-dev: v42
- common-deps-dev: v4
- vectora-core-approche-b-dev: v10

**Configuration:**
- lai_weekly_v7.yaml (version 7.0.0)
- Canonical: scopes LAI, prompts éditoriaux, sources MVP

## Utilisation

**Quand restaurer ce snapshot:**
- Régression majeure après modification
- Perte de fonctionnalité critique
- Besoin de revenir à état stable connu

**Comment restaurer:**
Voir `backup/snapshots/lai_v7_stable_YYYYMMDD_HHMMSS/README.md`

## Prochaines Améliorations

À partir de ce snapshot stable:
1. Optimiser prompts matching
2. Réduire bruit dans résultats
3. Affiner scoring
4. Valider extraction dates
5. Créer environnement stage
```

---

## 🎯 APRÈS LE SNAPSHOT

### Vous Pouvez Maintenant

✅ **Travailler en toute sécurité** sur optimisations  
✅ **Expérimenter** nouvelles configurations  
✅ **Modifier prompts** sans risque  
✅ **Refactorer code** avec filet de sécurité  
✅ **Créer environnement stage** sans pression

### En Cas de Problème

```powershell
# Restauration rapide configuration client
aws s3 cp `
  "backup\snapshots\lai_v7_stable_YYYYMMDD_HHMMSS\clients\lai_weekly_v7.yaml" `
  s3://vectora-inbox-config-dev/clients/lai_weekly_v7.yaml `
  --profile rag-lai-prod `
  --region eu-west-3

# Restauration rapide canonical
aws s3 sync `
  "backup\snapshots\lai_v7_stable_YYYYMMDD_HHMMSS\canonical\" `
  s3://vectora-inbox-config-dev/canonical/ `
  --profile rag-lai-prod `
  --region eu-west-3
```

---

## ⏱️ TEMPS ESTIMÉ

**Total**: ~30 minutes

- Étape 1-2: 5 min (création dossiers + Lambda configs)
- Étape 3-4: 5 min (layers + config client)
- Étape 5-6: 10 min (canonical + données curated)
- Étape 7-9: 5 min (stacks + métadonnées)
- Étape 10: 5 min (vérification + documentation)

---

**EXÉCUTER MAINTENANT AVANT TOUTE AUTRE MODIFICATION**
