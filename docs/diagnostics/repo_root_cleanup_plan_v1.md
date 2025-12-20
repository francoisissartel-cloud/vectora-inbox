# Plan de Nettoyage de la Racine - Vectora Inbox V1

**Date :** 18 décembre 2025  
**Objectif :** Ranger la racine sans suppression, en préservant l'intégrité du moteur V2  
**Règles :** Aucune suppression, déplacements uniquement, respect des contraintes V2

---

## Inventaire des Fichiers à la Racine

### 1. Lambda Packages (*.zip)

| Fichier | Taille Approx | Action Proposée | Justification |
|---------|---------------|-----------------|---------------|
| `bedrock-matching-patch-v2-20251217-095302.zip` | - | MOVE_TO_output/lambda_packages/ | Patch éphémère de déploiement |
| `bedrock-matching-patch-v2-20251217-095435.zip` | - | MOVE_TO_output/lambda_packages/ | Patch éphémère de déploiement |
| `bedrock-matching-patch-v2-20251217-140214.zip` | - | MOVE_TO_output/lambda_packages/ | Patch éphémère de déploiement |
| `bedrock-matching-patch-v2-20251217-140239.zip` | - | MOVE_TO_output/lambda_packages/ | Patch éphémère de déploiement |
| `ingest-v2-active-scan.zip` | - | MOVE_TO_output/lambda_packages/ | Package Lambda éphémère |
| `matching-v2-config-driven.zip` | - | MOVE_TO_output/lambda_packages/ | Package Lambda éphémère |
| `matching-v2-fix.zip` | - | MOVE_TO_output/lambda_packages/ | Package Lambda éphémère |
| `normalize-score-v2-20251216-154302.zip` | - | MOVE_TO_output/lambda_packages/ | Package Lambda éphémère |
| `normalize-score-v2-20251216-154404.zip` | - | MOVE_TO_output/lambda_packages/ | Package Lambda éphémère |
| `normalize-score-v2-20251216-184254.zip` | - | MOVE_TO_output/lambda_packages/ | Package Lambda éphémère |
| `normalize-score-v2-20251216-185953.zip` | - | MOVE_TO_output/lambda_packages/ | Package Lambda éphémère |
| `normalize-score-v2-20251217-112938.zip` | - | MOVE_TO_output/lambda_packages/ | Package Lambda éphémère |
| `normalize-score-v2-20251217-113340.zip` | - | MOVE_TO_output/lambda_packages/ | Package Lambda éphémère |
| `normalize-score-v2-real-data-fix-20251218-123110.zip` | - | MOVE_TO_output/lambda_packages/ | Package Lambda éphémère |
| `vectora-common-deps-complete.zip` | - | MOVE_TO_output/lambda_packages/ | Package de dépendances |
| `vectora-core-refactored-20251218-095151.zip` | - | MOVE_TO_output/lambda_packages/ | Package core éphémère |
| `vectora-core-refactored-20251218-095359.zip` | - | MOVE_TO_output/lambda_packages/ | Package core éphémère |
| `vectora-core-refactored-20251218-095501.zip` | - | MOVE_TO_output/lambda_packages/ | Package core éphémère |
| `vectora-core-refactored-20251218-095742.zip` | - | MOVE_TO_output/lambda_packages/ | Package core éphémère |
| `vectora-core-refactored-20251218-095932.zip` | - | MOVE_TO_output/lambda_packages/ | Package core éphémère |

**Total :** 20 fichiers ZIP éphémères

### 2. Diagnostics JSON

| Fichier | Action Proposée | Justification |
|---------|-----------------|---------------|
| `curated_items_analysis.json` | MOVE_TO_docs/diagnostics/raw/ | Analyse de données curées |
| `curated_items_e2e.json` | MOVE_TO_docs/diagnostics/raw/ | Test end-to-end |
| `curated_items_latest.json` | MOVE_TO_docs/diagnostics/raw/ | Dernière analyse |
| `current_lambda_state.json` | MOVE_TO_docs/diagnostics/raw/ | État Lambda pour debug |
| `ingested_items_e2e.json` | MOVE_TO_docs/diagnostics/raw/ | Test end-to-end ingestion |
| `lambda_env_update.json` | MOVE_TO_docs/diagnostics/raw/ | Mise à jour env Lambda |
| `latest_run_output.json` | MOVE_TO_docs/diagnostics/raw/ | Sortie dernière exécution |
| `normalize_lambda_diagnostic.json` | MOVE_TO_docs/diagnostics/raw/ | Diagnostic Lambda normalize |
| `vectora_core_deployment_info.json` | MOVE_TO_docs/diagnostics/raw/ | Info déploiement core |

**Total :** 9 fichiers JSON de diagnostic

### 3. Payloads de Test

| Fichier | Action Proposée | Justification |
|---------|-----------------|---------------|
| `ingest_payload.json` | MOVE_TO_tests/payloads/ | Payload test ingestion |
| `normalize_payload.json` | MOVE_TO_tests/payloads/ | Payload test normalisation |

**Total :** 2 fichiers payload

### 4. Snapshots de Données Réelles

| Fichier | Action Proposée | Justification |
|---------|-----------------|---------------|
| `real_ingested_items_17dec.json` | MOVE_TO_tests/data_snapshots/ | Snapshot données réelles du 17 déc |
| `final_test.json` | MOVE_TO_tests/data_snapshots/ | Test final avec données réelles |

**Total :** 2 fichiers de données réelles

### 5. Configuration Racine

| Fichier | Action Proposée | Justification |
|---------|-----------------|---------------|
| `lai_weekly_v3.yaml` | MOVE_TO_backup/root_legacy/ | Doublon de client-config-examples/lai_weekly_v3.yaml |
| `global_prompts.yaml` | KEEP_IN_PLACE (temporaire) | À évaluer : canonical/prompts/ ou docs/design/ |

**Total :** 2 fichiers config

### 6. Documentation Métier

| Fichier | Action Proposée | Justification |
|---------|-----------------|---------------|
| `AWS_DEPLOYMENT_SUMMARY.md` | KEEP_IN_PLACE | Documentation de déploiement importante |
| `DEPLOY_INSTRUCTIONS.md` | KEEP_IN_PLACE | Instructions de déploiement critiques |

**Total :** 2 fichiers docs (gardés à la racine)

### 7. Scripts Python Isolés

| Fichier | Action Proposée | Justification |
|---------|-----------------|---------------|
| `analyze_results_simple.py` | MOVE_TO_scripts/analysis/ | Script d'analyse temporaire |

**Total :** 1 script

### 8. Fichiers Divers

| Fichier | Action Proposée | Justification |
|---------|-----------------|---------------|
| `required_dependencies.txt` | MOVE_TO_backup/root_legacy/ | Liste dépendances, probablement obsolète |
| `$null` | CANDIDATE_FOR_DELETION | Fichier système Windows vide |

**Total :** 2 fichiers divers

---

## Plan de Rangement - Phase 2

### Dossiers à Créer

```
output/lambda_packages/          # Pour tous les *.zip
docs/diagnostics/raw/           # Pour tous les *_e2e.json, *_analysis.json, etc.
tests/payloads/                 # Pour ingest_payload.json, normalize_payload.json
tests/data_snapshots/           # Pour real_ingested_items_17dec.json, final_test.json
backup/root_legacy/             # Pour lai_weekly_v3.yaml, required_dependencies.txt
scripts/analysis/               # Pour analyze_results_simple.py
```

### Actions Prioritaires (Cas Évidents)

**Déplacements immédiats :**
1. **20 fichiers *.zip** → `output/lambda_packages/`
2. **9 fichiers JSON de diagnostic** → `docs/diagnostics/raw/`
3. **2 payloads de test** → `tests/payloads/`
4. **2 snapshots de données** → `tests/data_snapshots/`
5. **1 script d'analyse** → `scripts/analysis/`

**Déplacements avec vérification :**
1. `lai_weekly_v3.yaml` → `backup/root_legacy/` (après vérification doublon)
2. `required_dependencies.txt` → `backup/root_legacy/`

### Fichiers Gardés à la Racine

- `AWS_DEPLOYMENT_SUMMARY.md` : Documentation critique
- `DEPLOY_INSTRUCTIONS.md` : Instructions de déploiement
- `.gitignore` : Configuration Git

### Fichiers à Évaluer Plus Tard

- `global_prompts.yaml` : Destination à déterminer (canonical/prompts/ vs docs/design/)

### Candidats à Suppression (NON SUPPRIMÉS)

- `$null` : Fichier système Windows vide

---

## Impact Estimé

### Libération d'Espace Racine

- **Fichiers déplacés :** 36 fichiers
- **Fichiers gardés :** 3 fichiers (.gitignore + 2 docs)
- **Réduction visuelle :** ~92% des fichiers isolés supprimés de la racine

### Compatibilité V2

✅ **Aucun impact sur :**
- `src_v2/` (code moteur V2)
- `canonical/` (configurations canoniques)
- `client-config-examples/` (configs client)
- Workflow `ingest_v2 + normalize_score_v2`

✅ **Amélioration :**
- Racine plus lisible
- Artefacts organisés par type
- Historique préservé dans backup/

---

## Validation Pré-Exécution

### Vérifications Obligatoires

1. **Doublon lai_weekly_v3.yaml :** Confirmer que `client-config-examples/lai_weekly_v3.yaml` existe
2. **Dossiers existants :** Vérifier que `output/`, `docs/diagnostics/`, `tests/` existent
3. **Permissions :** S'assurer des droits d'écriture sur tous les dossiers cibles

### Règles de Sécurité Respectées

- ❌ **Aucune suppression** (sauf candidat `$null` marqué mais non supprimé)
- ✅ **Déplacements uniquement**
- ✅ **Dossiers protégés** non touchés
- ✅ **Code V2** préservé
- ✅ **Configs canoniques** intactes

---

## Prochaine Étape

**Phase 2 :** Exécution du rangement selon ce plan, avec création du rapport d'exécution `repo_root_cleanup_execution_report_v1.md`.