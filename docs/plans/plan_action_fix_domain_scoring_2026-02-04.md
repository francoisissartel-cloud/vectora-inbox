# Plan d'Action - Correction Domain Scoring

**Date**: 2026-02-04  
**Objectif**: Corriger domain scoring + Synchroniser repo local ↔ S3 dev  
**Durée estimée**: 30 minutes  

---

## 🎯 OBJECTIF FINAL

À la fin de ce plan:
- ✅ Domain scoring fonctionne (>60% items relevant)
- ✅ Code `src_v2/` identique entre repo local et Lambda dev
- ✅ Config `canonical-config/` identique entre repo local et S3 dev
- ✅ Aucune divergence repo ↔ S3

---

## 📋 CORRECTIONS À APPLIQUER

### Correction #1: Prompt lai_domain_scoring.yaml
**Fichier**: `canonical-config/prompts/domain_scoring/lai_domain_scoring.yaml`  
**Action**: Supprimer lignes 59-60 (duplication)

### Correction #2: Code bedrock_domain_scorer.py
**Fichier**: `src_v2/vectora_core/normalization/bedrock_domain_scorer.py`  
**Action**: Ajouter `item_dosing_intervals` dans item_context

---

## 🔄 ÉTAPES DU PLAN

### ÉTAPE 1: Backup État Actuel (2 min)

```bash
# Créer snapshot S3 dev
mkdir -p .tmp/backup_s3_dev
aws s3 sync s3://vectora-inbox-config-dev/canonical/ .tmp/backup_s3_dev/canonical/ --profile rag-lai-prod

# Créer snapshot code local
mkdir -p .tmp/backup_code_local
xcopy /E /I src_v2 .tmp\backup_code_local\src_v2
xcopy /E /I canonical-config .tmp\backup_code_local\canonical-config

# Documenter versions Lambda actuelles
aws lambda get-function --function-name vectora-inbox-normalize-score-v2-dev \
  --profile rag-lai-prod --region eu-west-3 \
  --query 'Configuration.Layers[*].Arn' > .tmp/backup_lambda_versions.txt

echo "Backup créé: .tmp/backup_s3_dev/ et .tmp/backup_code_local/"
```

---

### ÉTAPE 2: Télécharger État Actuel S3 → Repo (5 min)

```bash
# Télécharger TOUT canonical depuis S3 dev vers repo local
aws s3 sync s3://vectora-inbox-config-dev/canonical/ canonical-config/ --profile rag-lai-prod --delete

# Vérifier ce qui a été téléchargé
echo "Fichiers synchronisés depuis S3:"
dir /S /B canonical-config

# Comparer avec backup pour voir les différences
echo "Différences détectées:"
# (manuel - vérifier visuellement)
```

**Résultat attendu**: `canonical-config/` local = S3 dev exactement

---

### ÉTAPE 3: Appliquer Correction #1 - Prompt (3 min)

```bash
# Éditer canonical-config/prompts/domain_scoring/lai_domain_scoring.yaml
# SUPPRIMER lignes 59-60:
#   LAI DOMAIN DEFINITION:
#   {{ref:lai_domain_definition}}
```

**Modification manuelle**:
```yaml
# AVANT (lignes 50-65):
user_template: |
  Evaluate this normalized item for LAI domain relevance and score it.

  NORMALIZED ITEM:
  Title: {{item_title}}
  Summary: {{item_summary}}
  Event Type: {{item_event_type}}
  Date: {{item_effective_date}}
  
  Entities Detected:
  - Companies: {{item_companies}}
  - Molecules: {{item_molecules}}
  - Technologies: {{item_technologies}}
  - Trademarks: {{item_trademarks}}
  - Indications: {{item_indications}}
  - Dosing Intervals: {{item_dosing_intervals}}

  LAI DOMAIN DEFINITION:
  {{ref:lai_domain_definition}}

  EVALUATION PROCESS:

# APRÈS (lignes 50-63):
user_template: |
  Evaluate this normalized item for LAI domain relevance and score it.

  NORMALIZED ITEM:
  Title: {{item_title}}
  Summary: {{item_summary}}
  Event Type: {{item_event_type}}
  Date: {{item_effective_date}}
  
  Entities Detected:
  - Companies: {{item_companies}}
  - Molecules: {{item_molecules}}
  - Technologies: {{item_technologies}}
  - Trademarks: {{item_trademarks}}
  - Indications: {{item_indications}}
  - Dosing Intervals: {{item_dosing_intervals}}

  EVALUATION PROCESS:
```

**Vérification**:
```bash
# Vérifier que {{ref:lai_domain_definition}} n'existe plus
findstr /C:"{{ref:lai_domain_definition}}" canonical-config\prompts\domain_scoring\lai_domain_scoring.yaml
# Attendu: aucun résultat
```

---

### ÉTAPE 4: Appliquer Correction #2 - Code (3 min)

**Fichier**: `src_v2/vectora_core/normalization/bedrock_domain_scorer.py`

```python
# AVANT (lignes ~35-45):
        item_context = {
            'item_title': normalized_item.get('title', ''),
            'item_summary': normalized_content.get('summary', ''),
            'item_event_type': normalized_content.get('event_classification', {}).get('primary_type', 'other'),
            'item_effective_date': normalized_item.get('effective_date', ''),
            'item_companies': ', '.join(entities.get('companies', [])),
            'item_molecules': ', '.join(entities.get('molecules', [])),
            'item_technologies': ', '.join(entities.get('technologies', [])),
            'item_trademarks': ', '.join(entities.get('trademarks', [])),
            'item_indications': ', '.join(entities.get('indications', []))
        }

# APRÈS (lignes ~35-46):
        item_context = {
            'item_title': normalized_item.get('title', ''),
            'item_summary': normalized_content.get('summary', ''),
            'item_event_type': normalized_content.get('event_classification', {}).get('primary_type', 'other'),
            'item_effective_date': normalized_item.get('effective_date', ''),
            'item_companies': ', '.join(entities.get('companies', [])),
            'item_molecules': ', '.join(entities.get('molecules', [])),
            'item_technologies': ', '.join(entities.get('technologies', [])),
            'item_trademarks': ', '.join(entities.get('trademarks', [])),
            'item_indications': ', '.join(entities.get('indications', [])),
            'item_dosing_intervals': ', '.join(entities.get('dosing_intervals', []))
        }
```

**Vérification**:
```bash
# Vérifier que item_dosing_intervals est présent
findstr /C:"item_dosing_intervals" src_v2\vectora_core\normalization\bedrock_domain_scorer.py
# Attendu: 1 ligne trouvée
```

---

### ÉTAPE 5: Upload Repo → S3 (3 min)

```bash
# Upload canonical-config corrigé vers S3 dev
aws s3 sync canonical-config/ s3://vectora-inbox-config-dev/canonical/ --profile rag-lai-prod --delete

# Vérifier upload
aws s3 ls s3://vectora-inbox-config-dev/canonical/prompts/domain_scoring/ --profile rag-lai-prod
# Attendu: lai_domain_scoring.yaml avec nouvelle date

# Télécharger pour vérifier
aws s3 cp s3://vectora-inbox-config-dev/canonical/prompts/domain_scoring/lai_domain_scoring.yaml .tmp/verify_upload.yaml --profile rag-lai-prod

# Comparer
fc canonical-config\prompts\domain_scoring\lai_domain_scoring.yaml .tmp\verify_upload.yaml
# Attendu: fichiers identiques
```

---

### ÉTAPE 6: Build + Deploy Code (5 min)

```bash
# Build avec code corrigé
python scripts/build/build_all.py

# Deploy vers dev
python scripts/deploy/deploy_env.py --env dev

# Vérifier nouvelle version déployée
aws lambda get-function --function-name vectora-inbox-normalize-score-v2-dev \
  --profile rag-lai-prod --region eu-west-3 \
  --query 'Configuration.Layers[*].Arn'
# Attendu: version layer incrémentée (ex: :61 au lieu de :60)
```

---

### ÉTAPE 7: Test Validation (5 min)

```bash
# Créer nouveau client test
copy client-config-examples\production\lai_weekly_v17.yaml client-config-examples\production\lai_weekly_v22.yaml

# Upload
aws s3 cp client-config-examples\production\lai_weekly_v22.yaml s3://vectora-inbox-config-dev/clients/lai_weekly_v22.yaml --profile rag-lai-prod --region eu-west-3

# Lancer workflow
aws lambda invoke --function-name vectora-inbox-ingest-v2-dev --cli-binary-format raw-in-base64-out --payload "{\"client_id\":\"lai_weekly_v22\"}" .tmp\v22_ingest.json --profile rag-lai-prod --region eu-west-3

aws lambda invoke --function-name vectora-inbox-normalize-score-v2-dev --invocation-type Event --cli-binary-format raw-in-base64-out --payload "{\"client_id\":\"lai_weekly_v22\"}" .tmp\v22_normalize.json --profile rag-lai-prod --region eu-west-3

# Attendre 5-10 min puis analyser
# (script d'attente fourni ci-dessous)
```

---

### ÉTAPE 8: Vérification Synchronisation (2 min)

```bash
# Vérifier que repo local = S3 dev
aws s3 sync s3://vectora-inbox-config-dev/canonical/ .tmp/verify_s3/ --profile rag-lai-prod --delete

# Comparer
xcopy /E /I canonical-config .tmp\verify_local
fc /B .tmp\verify_local .tmp\verify_s3
# Attendu: fichiers identiques

# Vérifier code déployé = code local
# (version layer doit correspondre au dernier build)
```

---

### ÉTAPE 9: Analyse Résultats (2 min)

```python
# Script: .tmp/analyze_v22.py
import json

items = json.load(open('.tmp/v22_curated.json', encoding='utf-8'))
total = len(items)
relevant = sum(1 for i in items if i.get('domain_scoring',{}).get('is_relevant'))
scores = [i.get('domain_scoring',{}).get('score',0) for i in items if i.get('domain_scoring',{}).get('is_relevant')]
avg = sum(scores)/len(scores) if scores else 0

print(f"RESULTATS V22:")
print(f"  Total: {total}")
print(f"  Relevant: {relevant} ({relevant/total*100:.0f}%)")
print(f"  Score moyen: {avg:.1f}")
print(f"  Verdict: {'OK' if relevant >= total*0.6 else 'FAIL'}")

# Examiner 1 item relevant
relevant_items = [i for i in items if i.get('domain_scoring',{}).get('is_relevant')]
if relevant_items:
    item = relevant_items[0]
    print(f"\nEXEMPLE ITEM RELEVANT:")
    print(f"  Title: {item.get('title','')[:60]}")
    print(f"  Score: {item.get('domain_scoring',{}).get('score')}")
    print(f"  Reasoning: {item.get('domain_scoring',{}).get('reasoning','')[:100]}")
```

**Critères de succès**:
- ✅ Relevant ≥ 60%
- ✅ Score moyen 65-85
- ✅ Reasoning contient des signaux LAI (pas "Bedrock failed")

---

## 📊 CHECKLIST FINALE

### Synchronisation Repo ↔ S3
- [ ] `canonical-config/` local = S3 dev (vérification fc)
- [ ] Aucun fichier orphelin sur S3
- [ ] Aucun fichier orphelin en local
- [ ] Dates de modification cohérentes

### Code Déployé
- [ ] Layer version incrémentée
- [ ] Code `src_v2/` = code dans layer
- [ ] Pas de modifications non déployées

### Fonctionnel
- [ ] Domain scoring fonctionne (>60% relevant)
- [ ] Pas d'erreur dans logs CloudWatch
- [ ] Temps exec < 10 min
- [ ] Reasoning contient signaux LAI

---

## 🔧 SCRIPTS UTILITAIRES

### Script Attente V22
```python
# .tmp/wait_v22.py
import subprocess, time, sys
for i in range(20):
    time.sleep(30)
    print(f"{i+1}/20", flush=True)
    r = subprocess.run(['aws','s3','ls','s3://vectora-inbox-data-dev/curated/lai_weekly_v22/','--recursive','--profile','rag-lai-prod'], capture_output=True, text=True)
    if r.returncode == 0 and r.stdout.strip():
        print("OK")
        subprocess.run(['aws','s3','cp','s3://vectora-inbox-data-dev/curated/lai_weekly_v22/2026/02/04/items.json','.tmp/v22_curated.json','--profile','rag-lai-prod'])
        sys.exit(0)
print("TIMEOUT")
sys.exit(1)
```

### Script Vérification Sync
```bash
# .tmp/verify_sync.bat
@echo off
echo Verification synchronisation repo local - S3 dev

echo.
echo 1. Telechargement S3 vers .tmp/verify_s3/
aws s3 sync s3://vectora-inbox-config-dev/canonical/ .tmp/verify_s3/ --profile rag-lai-prod --delete --quiet

echo.
echo 2. Copie local vers .tmp/verify_local/
xcopy /E /I /Q canonical-config .tmp\verify_local > nul

echo.
echo 3. Comparaison fichiers
fc /B .tmp\verify_local .tmp\verify_s3 > .tmp\sync_diff.txt 2>&1

if %ERRORLEVEL% EQU 0 (
    echo [OK] Repo local = S3 dev
) else (
    echo [ERREUR] Differences detectees:
    type .tmp\sync_diff.txt
)
```

---

## 🚨 ROLLBACK (si échec)

```bash
# Restaurer S3 depuis backup
aws s3 sync .tmp/backup_s3_dev/canonical/ s3://vectora-inbox-config-dev/canonical/ --profile rag-lai-prod --delete

# Restaurer code local depuis backup
xcopy /E /I /Y .tmp\backup_code_local\src_v2 src_v2
xcopy /E /I /Y .tmp\backup_code_local\canonical-config canonical-config

# Redeploy version précédente
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev
```

---

## 📝 DOCUMENTATION POST-CORRECTION

### Fichiers à mettre à jour
1. `docs/reports/diagnostic_domain_scoring_2026-02-04.md` - Ajouter section "Corrections appliquées"
2. `docs/architecture/blueprint-v2-ACTUAL-2026.yaml` - Mettre à jour si nécessaire
3. `.q-context/CHANGELOG.md` - Documenter les changements

### Commit Git
```bash
git add src_v2/vectora_core/normalization/bedrock_domain_scorer.py
git add canonical-config/prompts/domain_scoring/lai_domain_scoring.yaml
git commit -m "fix: domain scoring - remove prompt duplication + add dosing_intervals

- Remove {{ref:lai_domain_definition}} duplication in lai_domain_scoring.yaml
- Add item_dosing_intervals to bedrock_domain_scorer.py context
- Fixes 100% items rejected issue (V18-V21)
- Tested with V22: >60% relevant, score 65-75"
```

---

**Temps total estimé**: 30 minutes  
**Risque**: FAIBLE (corrections minimales + backup complet)  
**Impact**: CRITIQUE (débloquer domain scoring)
