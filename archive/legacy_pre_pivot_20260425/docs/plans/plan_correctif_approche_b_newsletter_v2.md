# Plan Correctif v2 - Migration Approche B Newsletter + Convention Nommage

**Date**: 2026-01-29 21:00 UTC  
**Objectif**: Migrer newsletter-v2 vers Approche B + Convention nommage explicite  
**Durée estimée**: 3h30 (incluant renommage prompts)  
**Priorité**: HAUTE

---

## 🎯 OBJECTIFS

### Objectif Principal
Migrer newsletter-v2 vers Approche B + Établir convention nommage explicite pour éviter confusion.

### Objectifs Spécifiques
1. ✅ Éliminer prompts hardcodés dans `bedrock_editor.py`
2. ✅ Créer `canonical/prompts/editorial/lai_editorial.yaml`
3. ✅ Renommer prompts existants : `lai_normalization.yaml`, `lai_matching.yaml`
4. ✅ Modifier `prompt_resolver.py` pour nouveau pattern
5. ✅ Mettre à jour configs clients
6. ✅ Résoudre dates newsletter (cache Lambda)

---

## 📋 CONVENTION NOMMAGE (NOUVELLE)

### Pattern : `{vertical}_{phase}.yaml`

**Structure** :
```
canonical/prompts/
├── normalization/
│   └── lai_normalization.yaml     # ✅ Explicite
├── matching/
│   └── lai_matching.yaml          # ✅ Explicite
└── editorial/
    └── lai_editorial.yaml         # ✅ Explicite (NOUVEAU)
```

**Configuration client** :
```yaml
bedrock_config:
  normalization_prompt: "lai_normalization"
  matching_prompt: "lai_matching"
  editorial_prompt: "lai_editorial"
```

**Avantages** :
- ✅ Noms uniques et explicites
- ✅ Logs clairs : "Chargement lai_editorial.yaml"
- ✅ Pas de confusion possible
- ✅ Grep efficace : `grep -r "lai_editorial"`

---

## 📊 MODIFICATIONS REQUISES

### Repo Local (src_v2/)

**Fichiers à modifier** :
1. `src_v2/vectora_core/shared/prompt_resolver.py` (1 ligne)
2. `src_v2/vectora_core/newsletter/bedrock_editor.py` (migration Approche B)
3. `src_v2/vectora_core/newsletter/__init__.py` (ajout paramètres)

**Fichiers à renommer** :
1. `canonical/prompts/normalization/lai_prompt.yaml` → `lai_normalization.yaml`
2. `canonical/prompts/matching/lai_prompt.yaml` → `lai_matching.yaml`

**Fichiers à créer** :
1. `canonical/prompts/editorial/lai_editorial.yaml` (nouveau)

**Configs à modifier** :
1. `client-config-examples/lai_weekly_v3.yaml`
2. `client-config-examples/lai_weekly_v6.yaml`
3. `client-config-examples/lai_weekly_v7.yaml`

### AWS S3

**Prompts à uploader** :
1. `s3://.../canonical/prompts/normalization/lai_normalization.yaml`
2. `s3://.../canonical/prompts/matching/lai_matching.yaml`
3. `s3://.../canonical/prompts/editorial/lai_editorial.yaml`

**Configs à uploader** :
1. `s3://.../clients/lai_weekly_v3.yaml`
2. `s3://.../clients/lai_weekly_v6.yaml`
3. `s3://.../clients/lai_weekly_v7.yaml`

### AWS Lambda

**Layer à créer** : v11 (inclut prompt_resolver modifié)

**Lambdas à mettre à jour** :
1. `vectora-inbox-normalize-score-v2-dev` (layer v11)
2. `vectora-inbox-newsletter-v2-dev` (layer v11 + CACHE_BUST=v11)

---

## 🔧 PHASE 2: CORRECTIFS LOCAUX (1h45)

### 2.1 Renommage Prompts Existants

**Commandes** :
```bash
# Normalization
mv canonical/prompts/normalization/lai_prompt.yaml \
   canonical/prompts/normalization/lai_normalization.yaml

# Matching
mv canonical/prompts/matching/lai_prompt.yaml \
   canonical/prompts/matching/lai_matching.yaml
```

### 2.2 Modification prompt_resolver.py

**Fichier** : `src_v2/vectora_core/shared/prompt_resolver.py`

**Ligne 31 - AVANT** :
```python
prompt_key = f"canonical/prompts/{prompt_type}/{vertical}_prompt.yaml"
```

**Ligne 31 - APRÈS** :
```python
prompt_key = f"canonical/prompts/{prompt_type}/{vertical}.yaml"
```

### 2.3 Création Prompt Editorial

**Fichier** : `canonical/prompts/editorial/lai_editorial.yaml`

**Contenu** :
```yaml
metadata:
  vertical: "LAI"
  version: "1.0"
  created_date: "2026-01-29"
  description: "Prompt génération contenu éditorial LAI"

tldr_generation:
  system_instructions: |
    You are an expert newsletter editor for LAI intelligence.
    Generate concise, executive-level TL;DR summaries.
    
  user_template: |
    Generate a TL;DR (2-3 bullet points) for this week's LAI newsletter:
    
    {{items_summary}}
    
    FOCUS: Partnerships, regulatory milestones, clinical developments.
    FORMAT: Bullet points only.
    STYLE: Executive, factual, concise.
    
  bedrock_config:
    max_tokens: 200
    temperature: 0.1
    anthropic_version: "bedrock-2023-05-31"

introduction_generation:
  system_instructions: |
    You are an expert newsletter editor for LAI intelligence.
    Generate professional, concise introductions.
    
  user_template: |
    Generate a brief introduction (1-2 sentences) for this week's LAI newsletter.
    
    Week: {{week_start}} to {{week_end}}
    Sections: {{sections_summary}}
    Total items: {{total_items}}
    
    FORMAT: Introduction text only.
    STYLE: Professional, executive-focused.
    
  bedrock_config:
    max_tokens: 300
    temperature: 0.1
    anthropic_version: "bedrock-2023-05-31"
```

### 2.4 Migration bedrock_editor.py (Approche B)

**Fichier** : `src_v2/vectora_core/newsletter/bedrock_editor.py`

**Modifications clés** :
```python
from ..shared import prompt_resolver

def generate_editorial_content(selected_items, client_config, env_vars, s3_io, canonical_scopes):
    # Chargement prompt via Approche B
    editorial_prompt = client_config.get('bedrock_config', {}).get('editorial_prompt', 'lai_editorial')
    
    prompt_template = prompt_resolver.load_prompt_template(
        'editorial',
        editorial_prompt,
        s3_io,
        env_vars["CONFIG_BUCKET"]
    )
    
    # Génération TL;DR
    tldr = _generate_tldr_approche_b(
        bedrock_client, prompt_template, canonical_scopes,
        items_summary, env_vars["BEDROCK_MODEL_ID"]
    )
    
    # Génération introduction
    introduction = _generate_introduction_approche_b(
        bedrock_client, prompt_template, canonical_scopes,
        sections_summary, total_items, env_vars["BEDROCK_MODEL_ID"]
    )
```

### 2.5 Modification Configs Clients

**Fichiers** : `client-config-examples/lai_weekly_v*.yaml`

**AVANT** :
```yaml
bedrock_config:
  normalization_prompt: "lai"
  matching_prompt: "lai"
```

**APRÈS** :
```yaml
bedrock_config:
  normalization_prompt: "lai_normalization"
  matching_prompt: "lai_matching"
  editorial_prompt: "lai_editorial"
```

---

## 🚀 PHASE 4: DÉPLOIEMENT AWS (45 min)

### 4.1 Upload Prompts S3

**Commandes** :
```bash
# Normalization (renommé)
aws s3 cp canonical/prompts/normalization/lai_normalization.yaml \
  s3://vectora-inbox-config-dev/canonical/prompts/normalization/lai_normalization.yaml \
  --region eu-west-3 --profile rag-lai-prod

# Matching (renommé)
aws s3 cp canonical/prompts/matching/lai_matching.yaml \
  s3://vectora-inbox-config-dev/canonical/prompts/matching/lai_matching.yaml \
  --region eu-west-3 --profile rag-lai-prod

# Editorial (nouveau)
aws s3 cp canonical/prompts/editorial/lai_editorial.yaml \
  s3://vectora-inbox-config-dev/canonical/prompts/editorial/lai_editorial.yaml \
  --region eu-west-3 --profile rag-lai-prod
```

### 4.2 Upload Configs Clients

**Commandes** :
```bash
aws s3 cp client-config-examples/lai_weekly_v7.yaml \
  s3://vectora-inbox-config-dev/clients/lai_weekly_v7.yaml \
  --region eu-west-3 --profile rag-lai-prod
```

### 4.3 Création Layer v11

**Inclut** :
- `prompt_resolver.py` modifié (ligne 31)
- `bedrock_editor.py` migré Approche B
- `newsletter/__init__.py` modifié

**Commandes** :
```bash
# Préparation
if exist layer_build rmdir /s /q layer_build
mkdir layer_build\python
xcopy /E /I /Y src_v2\vectora_core layer_build\python\vectora_core

# Création zip
cd layer_build
powershell -Command "Compress-Archive -Path python -DestinationPath ../vectora-core-layer-v11.zip -Force"
cd ..

# Publication
aws lambda publish-layer-version \
  --layer-name vectora-inbox-vectora-core-approche-b-dev \
  --description "v11 - Newsletter Approche B + Convention nommage explicite" \
  --zip-file fileb://vectora-core-layer-v11.zip \
  --compatible-runtimes python3.11 \
  --region eu-west-3 --profile rag-lai-prod
```

### 4.4 Mise à Jour Lambdas

**normalize-score-v2** :
```bash
aws lambda update-function-configuration \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --layers \
    arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-common-deps-dev:4 \
    arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-approche-b-dev:11 \
  --region eu-west-3 --profile rag-lai-prod
```

**newsletter-v2** :
```bash
aws lambda update-function-configuration \
  --function-name vectora-inbox-newsletter-v2-dev \
  --layers \
    arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-common-deps-dev:4 \
    arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-approche-b-dev:11 \
  --environment "Variables={CONFIG_BUCKET=vectora-inbox-config-dev,DATA_BUCKET=vectora-inbox-data-dev,NEWSLETTERS_BUCKET=vectora-inbox-newsletters-dev,BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0,BEDROCK_REGION=us-east-1,CACHE_BUST=v11}" \
  --region eu-west-3 --profile rag-lai-prod
```

---

## ✅ PHASE 5: VALIDATION E2E (30 min)

### 5.1 Test Normalize-Score

**Commande** :
```bash
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --payload file://event_normalize_v7.json \
  --region eu-west-3 --profile rag-lai-prod \
  response_normalize_v7_v11.json
```

**Vérification logs** :
```bash
aws logs tail /aws/lambda/vectora-inbox-normalize-score-v2-dev \
  --since 5m --region eu-west-3 --profile rag-lai-prod \
  | findstr "lai_normalization\|lai_matching"
```

**Logs attendus** :
```
[INFO] Prompt template chargé: canonical/prompts/normalization/lai_normalization.yaml
[INFO] Prompt template chargé: canonical/prompts/matching/lai_matching.yaml
```

### 5.2 Test Newsletter

**Commande** :
```bash
aws lambda invoke \
  --function-name vectora-inbox-newsletter-v2-dev \
  --payload file://event_newsletter_v7.json \
  --region eu-west-3 --profile rag-lai-prod \
  response_newsletter_v7_v11.json
```

**Vérification logs** :
```bash
aws logs tail /aws/lambda/vectora-inbox-newsletter-v2-dev \
  --since 5m --region eu-west-3 --profile rag-lai-prod \
  | findstr "lai_editorial\|effective_date"
```

**Logs attendus** :
```
[INFO] Prompt template chargé: canonical/prompts/editorial/lai_editorial.yaml
[INFO] Using effective_date: 2026-01-27
```

### 5.3 Vérification Dates Newsletter

**Commande** :
```bash
aws s3 cp s3://vectora-inbox-newsletters-dev/lai_weekly_v7/2026/01/29/newsletter.md - \
  --region eu-west-3 --profile rag-lai-prod \
  | grep "Date:"
```

**Résultat attendu** :
```
**Date:** Jan 27, 2026  # ✅ Date Bedrock
**Date:** Dec 09, 2025  # ✅ Date Bedrock
**Date:** Jan 09, 2026  # ✅ Date Bedrock
```

---

## 📊 RÉCAPITULATIF MODIFICATIONS

### Fichiers Modifiés (Repo)

| Fichier | Type | Modification |
|---------|------|--------------|
| `prompt_resolver.py` | Code | Ligne 31 : Pattern nommage |
| `bedrock_editor.py` | Code | Migration Approche B |
| `newsletter/__init__.py` | Code | Ajout paramètres |
| `lai_weekly_v*.yaml` | Config | Ajout `editorial_prompt` |

### Fichiers Renommés (Repo)

| Avant | Après |
|-------|-------|
| `normalization/lai_prompt.yaml` | `normalization/lai_normalization.yaml` |
| `matching/lai_prompt.yaml` | `matching/lai_matching.yaml` |

### Fichiers Créés (Repo)

| Fichier | Description |
|---------|-------------|
| `editorial/lai_editorial.yaml` | Prompt génération contenu |

### Ressources AWS

| Ressource | Action | Détails |
|-----------|--------|---------|
| S3 Prompts | Upload | 3 fichiers (normalization, matching, editorial) |
| S3 Configs | Upload | 3 configs clients |
| Layer | Créer | v11 avec prompt_resolver modifié |
| Lambda normalize | Update | Layer v11 |
| Lambda newsletter | Update | Layer v11 + CACHE_BUST=v11 |

---

## 🎯 CHECKLIST FINALE

### Repo Local
- [ ] Prompts renommés (normalization, matching)
- [ ] Prompt editorial créé
- [ ] prompt_resolver.py modifié (ligne 31)
- [ ] bedrock_editor.py migré Approche B
- [ ] Configs clients mis à jour
- [ ] Tests locaux passent

### AWS S3
- [ ] lai_normalization.yaml uploadé
- [ ] lai_matching.yaml uploadé
- [ ] lai_editorial.yaml uploadé
- [ ] Configs clients uploadés

### AWS Lambda
- [ ] Layer v11 créé
- [ ] normalize-score-v2 mis à jour
- [ ] newsletter-v2 mis à jour
- [ ] CACHE_BUST=v11 appliqué

### Validation
- [ ] Logs normalize : "lai_normalization.yaml"
- [ ] Logs newsletter : "lai_editorial.yaml"
- [ ] Dates newsletter : Bedrock (pas fallback)
- [ ] TL;DR généré correctement
- [ ] Introduction générée correctement

---

## 📈 MÉTRIQUES SUCCÈS

| Métrique | Avant | Après | Status |
|----------|-------|-------|--------|
| Noms prompts uniques | Non | Oui | ✅ |
| Logs clairs | Non | Oui | ✅ |
| Architecture cohérente | 66% | 100% | ✅ |
| Dates effectives | 0% | >90% | ✅ |
| Prompts hardcodés | 2 | 0 | ✅ |

---

**Status** : ✅ PLAN V2 PRÊT  
**Durée** : 3h30  
**Prochaine action** : Exécuter Phase 2 (Correctifs locaux)
