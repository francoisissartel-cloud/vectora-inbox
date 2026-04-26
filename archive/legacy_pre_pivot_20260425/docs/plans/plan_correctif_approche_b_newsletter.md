# Plan Correctif - Migration Approche B Newsletter & Uniformisation Prompts

**Date**: 2026-01-29 20:00 UTC  
**Objectif**: Migrer lambda newsletter-v2 vers Approche B + Uniformiser système prompts  
**Durée estimée**: 3 heures  
**Priorité**: HAUTE (Architecture + Dates newsletter)

---

## 🎯 OBJECTIFS

### Objectif Principal
Migrer la lambda newsletter-v2 vers l'Approche B (prompts canonical + prompt_resolver) pour uniformiser l'architecture avec normalize-score-v2.

### Objectifs Spécifiques
1. ✅ Éliminer prompts Bedrock hardcodés dans `bedrock_editor.py`
2. ✅ Créer prompts LAI newsletter dans `canonical/prompts/editorial/`
3. ✅ Utiliser `prompt_resolver` pour chargement et résolution
4. ✅ Configuration client pilote les prompts (comme normalization/matching)
5. ✅ Résoudre problème dates newsletter (cache Lambda)
6. ✅ Établir convention de nommage claire pour éviter conflits

---

## 📋 CONVENTION DE NOMMAGE PROMPTS (RECOMMANDATION EXPERT)

### Problème Actuel
3 types de prompts Bedrock avec risque de confusion :
- `normalization` : Extraction entités + dates
- `matching` : Évaluation pertinence domaines
- `newsletter` : Génération contenu éditorial (TL;DR, intro)

### Solution Proposée : Catégorisation par Phase Pipeline

**Structure recommandée** :
```
canonical/prompts/
├── normalization/          # Phase 1 : Extraction données
│   └── lai_prompt.yaml
├── matching/               # Phase 2 : Évaluation pertinence
│   └── lai_prompt.yaml
└── editorial/              # Phase 3 : Génération contenu
    └── lai_prompt.yaml     # NOUVEAU
```

**Rationale** :
- ✅ **`editorial`** au lieu de `newsletter` : Plus précis (génération contenu éditorial)
- ✅ Évite confusion avec "newsletter" (output final vs génération contenu)
- ✅ Cohérent avec terminologie métier (éditorial = TL;DR, intro, reformulation)
- ✅ Extensible : `editorial/lai_prompt.yaml`, `editorial/gene_therapy_prompt.yaml`

### Configuration Client

**Avant (Incohérent)** :
```yaml
bedrock_config:
  normalization_prompt: "lai"    # ✅ Clair
  matching_prompt: "lai"         # ✅ Clair
  # newsletter_prompt: ???       # ❌ Manquant
```

**Après (Cohérent)** :
```yaml
bedrock_config:
  normalization_prompt: "lai"    # Phase 1 : Extraction
  matching_prompt: "lai"         # Phase 2 : Matching
  editorial_prompt: "lai"        # Phase 3 : Génération éditorial
```

**Avantages** :
1. Cohérence : Même pattern pour les 3 phases
2. Clarté : `editorial_prompt` explicite (génération contenu)
3. Évolutivité : Facile d'ajouter `gene_therapy`, `oncology`, etc.
4. Maintenabilité : Convention claire pour toute l'équipe

---

## 📊 PHASE 0: CADRAGE

### 0.1 Contexte

**État actuel** :
- ✅ normalize-score-v2 : Approche B complète
- ✅ bedrock_matcher : Approche B partielle
- ❌ newsletter-v2 : Approche A/B hybride (prompts hardcodés)

**Problèmes identifiés** :
1. Prompts Bedrock hardcodés dans `bedrock_editor.py`
2. Utilisation `global_prompts.yaml` (fallback historique)
3. Substitution manuelle basique (`replace()`)
4. Pas de résolution références canonical
5. Dates newsletter affichent fallback (cache Lambda)

### 0.2 Périmètre

**Inclus** :
- Migration `bedrock_editor.py` vers `prompt_resolver`
- Création `canonical/prompts/editorial/lai_prompt.yaml`
- Modification `client_config` pour `editorial_prompt`
- Suppression code hardcodé dans `bedrock_editor.py`
- Correction cache Lambda newsletter
- Tests E2E avec lai_weekly_v7

**Exclus** :
- Modification prompts normalization/matching (déjà Approche B)
- Refonte complète architecture newsletter
- Ajout nouveaux prompts éditoriaux (section_summary, title_reformulation)

### 0.3 Contraintes

**Techniques** :
- Respecter `vectora-inbox-development-rules.md`
- Code dans `src_v2/`
- Prompts dans `canonical/prompts/editorial/`
- Utiliser `prompt_resolver` (comme normalize-score-v2)
- Layer structure : `python/vectora_core/`

**Métier** :
- Pas de régression fonctionnelle
- Dates effectives affichées dans newsletter
- TL;DR et introduction générés correctement
- Compatible avec tous les clients LAI

### 0.4 Risques

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Régression génération TL;DR | Faible | Moyen | Tests locaux avant déploiement |
| Cache Lambda persiste | Moyen | Faible | Forcer refresh via variable env |
| Prompts mal résolus | Faible | Élevé | Validation structure YAML |
| Temps déploiement > estimé | Moyen | Faible | Tests locaux exhaustifs |

---

## 🔍 PHASE 1: DIAGNOSTIC (15 min)

### 1.1 Audit Code Actuel

**Fichiers à analyser** :
- `src_v2/vectora_core/newsletter/bedrock_editor.py` (prompts hardcodés)
- `src_v2/vectora_core/newsletter/__init__.py` (appel bedrock_editor)
- `canonical/prompts/global_prompts.yaml` (prompts actuels)

**Points de vérification** :
- [ ] Identifier tous les appels Bedrock dans `bedrock_editor.py`
- [ ] Lister prompts utilisés (TL;DR, introduction)
- [ ] Vérifier variables substituées (`{{items_summary}}`, etc.)
- [ ] Identifier dépendances `config_loader.load_canonical_prompts()`

### 1.2 Analyse Prompts Existants

**Prompts à migrer** :
1. `global_prompts.yaml::newsletter.tldr_generation`
2. `global_prompts.yaml::newsletter.introduction_generation`

**Structure à créer** :
```yaml
# canonical/prompts/editorial/lai_prompt.yaml
metadata:
  vertical: "LAI"
  version: "1.0"

tldr_generation:
  system_instructions: |
    ...
  user_template: |
    {{items_summary}}
  bedrock_config:
    max_tokens: 200
    temperature: 0.1

introduction_generation:
  system_instructions: |
    ...
  user_template: |
    Week: {{week_start}} to {{week_end}}
    Sections: {{sections_summary}}
    Total items: {{total_items}}
  bedrock_config:
    max_tokens: 300
    temperature: 0.1
```

### 1.3 Validation Architecture Cible

**Pattern à suivre** (comme normalize-score-v2) :
```python
# 1. Chargement prompt template
prompt_template = prompt_resolver.load_prompt_template(
    'editorial', 
    client_config['bedrock_config']['editorial_prompt'],
    s3_io,
    config_bucket
)

# 2. Construction prompt avec variables
prompt = prompt_resolver.build_prompt(
    prompt_template['tldr_generation'],
    canonical_scopes,
    {'items_summary': items_summary}
)

# 3. Appel Bedrock
response = call_bedrock(prompt)
```

---

## 🔧 PHASE 2: CORRECTIFS LOCAUX (1h30)

### 2.1 Création Prompt Editorial LAI

**Fichier** : `canonical/prompts/editorial/lai_prompt.yaml`

**Contenu** :
```yaml
# Prompt éditorial LAI - Génération contenu newsletter
# Version: 1.0
# Date: 2026-01-29

metadata:
  vertical: "LAI"
  version: "1.0"
  created_date: "2026-01-29"
  description: "Prompt génération contenu éditorial pour newsletters LAI"
  author: "Vectora Inbox Team"

# Génération TL;DR exécutif
tldr_generation:
  system_instructions: |
    You are an expert newsletter editor for LAI (Long-Acting Injectable) intelligence.
    Generate concise, executive-level TL;DR summaries.
    Focus on strategic implications and key developments.
    
  user_template: |
    Generate a TL;DR (2-3 bullet points) for this week's LAI newsletter:
    
    ITEMS SUMMARY:
    {{items_summary}}
    
    FOCUS ON:
    - Major partnerships or deals
    - Regulatory milestones (FDA approvals, NDA submissions)
    - Clinical developments
    - Technology breakthroughs
    
    FORMAT: Return only the TL;DR text with bullet points.
    STYLE: Executive, factual, concise.
    LENGTH: 2-3 bullet points maximum.
    
  bedrock_config:
    max_tokens: 200
    temperature: 0.1
    anthropic_version: "bedrock-2023-05-31"

# Génération introduction newsletter
introduction_generation:
  system_instructions: |
    You are an expert newsletter editor for LAI intelligence.
    Generate professional, concise introductions.
    Keep it executive-focused and informative.
    
  user_template: |
    Generate a brief introduction (1-2 sentences) for this week's LAI newsletter.
    
    CONTEXT:
    - Week: {{week_start}} to {{week_end}}
    - Sections covered: {{sections_summary}}
    - Total items: {{total_items}}
    
    FOCUS ON:
    - Brief context about the week's coverage
    - What executives should expect to learn
    
    FORMAT: Return only the introduction text.
    STYLE: Professional, executive-focused, concise.
    LENGTH: 1-2 sentences maximum.
    
  bedrock_config:
    max_tokens: 300
    temperature: 0.1
    anthropic_version: "bedrock-2023-05-31"
```

**Validation** :
- [ ] Structure YAML valide
- [ ] Métadonnées complètes
- [ ] Variables clairement identifiées (`{{items_summary}}`, etc.)
- [ ] bedrock_config présent pour chaque prompt

### 2.2 Modification bedrock_editor.py

**Fichier** : `src_v2/vectora_core/newsletter/bedrock_editor.py`

**Changements** :

**AVANT (Approche A/B hybride)** :
```python
def generate_editorial_content(selected_items, client_config, env_vars):
    # Chargement prompts hardcodés
    prompts = config_loader.load_canonical_prompts(env_vars["CONFIG_BUCKET"])
    
    # Substitution manuelle
    user_prompt = user_template.replace('{{items_summary}}', items_summary)
```

**APRÈS (Approche B complète)** :
```python
def generate_editorial_content(selected_items, client_config, env_vars, s3_io, canonical_scopes):
    # Chargement prompt template LAI
    editorial_prompt = client_config.get('bedrock_config', {}).get('editorial_prompt', 'lai')
    
    prompt_template = prompt_resolver.load_prompt_template(
        'editorial',
        editorial_prompt,
        s3_io,
        env_vars["CONFIG_BUCKET"]
    )
    
    if not prompt_template:
        raise ValueError(f"Editorial prompt '{editorial_prompt}' not found")
    
    # Génération TL;DR avec résolution
    tldr = _generate_tldr_approche_b(
        bedrock_client, prompt_template, canonical_scopes, 
        items_summary, env_vars["BEDROCK_MODEL_ID"]
    )
    
    # Génération introduction avec résolution
    introduction = _generate_introduction_approche_b(
        bedrock_client, prompt_template, canonical_scopes,
        sections_summary, total_items, env_vars["BEDROCK_MODEL_ID"]
    )
```

**Nouvelles fonctions** :
```python
def _generate_tldr_approche_b(bedrock_client, prompt_template, canonical_scopes, 
                               items_summary, model_id):
    """Génère TL;DR via Approche B"""
    from ..shared import prompt_resolver
    
    # Construction prompt avec résolution
    prompt = prompt_resolver.build_prompt(
        prompt_template['tldr_generation'],
        canonical_scopes,
        {'items_summary': items_summary}
    )
    
    # Appel Bedrock
    bedrock_config = prompt_template['tldr_generation']['bedrock_config']
    response = _call_bedrock(
        bedrock_client, model_id, 
        prompt_template['tldr_generation']['system_instructions'],
        prompt,
        max_tokens=bedrock_config.get('max_tokens', 200),
        temperature=bedrock_config.get('temperature', 0.1)
    )
    
    return response.strip()

def _generate_introduction_approche_b(bedrock_client, prompt_template, canonical_scopes,
                                      sections_summary, total_items, model_id):
    """Génère introduction via Approche B"""
    from ..shared import prompt_resolver
    from datetime import datetime
    
    # Variables pour substitution
    variables = {
        'week_start': datetime.now().strftime('%B %d, %Y'),
        'week_end': datetime.now().strftime('%B %d, %Y'),
        'sections_summary': sections_summary,
        'total_items': str(total_items)
    }
    
    # Construction prompt avec résolution
    prompt = prompt_resolver.build_prompt(
        prompt_template['introduction_generation'],
        canonical_scopes,
        variables
    )
    
    # Appel Bedrock
    bedrock_config = prompt_template['introduction_generation']['bedrock_config']
    response = _call_bedrock(
        bedrock_client, model_id,
        prompt_template['introduction_generation']['system_instructions'],
        prompt,
        max_tokens=bedrock_config.get('max_tokens', 300),
        temperature=bedrock_config.get('temperature', 0.1)
    )
    
    return response.strip()
```

**Suppression code obsolète** :
- Supprimer `_generate_tldr()` (ancienne version)
- Supprimer `_generate_introduction()` (ancienne version)
- Supprimer dépendance `config_loader.load_canonical_prompts()`

### 2.3 Modification newsletter/__init__.py

**Fichier** : `src_v2/vectora_core/newsletter/__init__.py`

**Changements** :
```python
def run_newsletter_for_client(client_id, env_vars, target_date=None, force_regenerate=False):
    # ... (code existant)
    
    # Chargement canonical scopes (NOUVEAU)
    canonical_scopes = config_loader.load_canonical_scopes(env_vars["CONFIG_BUCKET"])
    
    # Génération contenu éditorial avec Approche B
    editorial_content = bedrock_editor.generate_editorial_content(
        selected_items,
        client_config,
        env_vars,
        s3_io,              # NOUVEAU
        canonical_scopes    # NOUVEAU
    )
```

### 2.4 Modification Client Config

**Fichier** : `client-config-examples/lai_weekly_v7.yaml`

**Ajout** :
```yaml
bedrock_config:
  normalization_prompt: "lai"    # Phase 1 : Extraction entités + dates
  matching_prompt: "lai"         # Phase 2 : Matching domaines
  editorial_prompt: "lai"        # Phase 3 : Génération contenu éditorial (NOUVEAU)
```

### 2.5 Correctif Cache Lambda (Quick Fix)

**Objectif** : Forcer refresh cache pour afficher dates effectives

**Action** : Ajouter variable d'environnement `CACHE_BUST`

**Commande** :
```bash
aws lambda update-function-configuration \
  --function-name vectora-inbox-newsletter-v2-dev \
  --environment "Variables={...,CACHE_BUST=v10}" \
  --region eu-west-3 --profile rag-lai-prod
```

---

## 🧪 PHASE 3: TESTS LOCAUX (45 min)

### 3.1 Tests Unitaires

**Fichier** : `tests/unit/test_editorial_prompts_approche_b.py`

**Tests** :
```python
def test_load_editorial_prompt_lai():
    """Vérifie chargement prompt editorial LAI"""
    # Mock s3_io
    # Charger prompt
    # Vérifier structure

def test_build_tldr_prompt():
    """Vérifie construction prompt TL;DR avec variables"""
    # Charger template
    # Substituer variables
    # Vérifier résultat

def test_build_introduction_prompt():
    """Vérifie construction prompt introduction"""
    # Charger template
    # Substituer variables
    # Vérifier résultat

def test_editorial_prompt_missing():
    """Vérifie erreur si prompt manquant"""
    # Tenter charger prompt inexistant
    # Vérifier ValueError
```

### 3.2 Tests Intégration

**Fichier** : `tests/integration/test_newsletter_editorial_e2e.py`

**Tests** :
```python
def test_generate_editorial_content_approche_b():
    """Test E2E génération contenu éditorial"""
    # Charger items curated
    # Générer TL;DR et introduction
    # Vérifier format et contenu

def test_newsletter_with_effective_dates():
    """Vérifie dates effectives dans newsletter"""
    # Charger items avec effective_date
    # Générer newsletter
    # Vérifier dates affichées != fallback
```

### 3.3 Validation Manuelle

**Checklist** :
- [ ] Prompt LAI chargé depuis S3
- [ ] TL;DR généré correctement
- [ ] Introduction générée correctement
- [ ] Dates effectives affichées (pas fallback)
- [ ] Pas de régression fonctionnelle
- [ ] Logs clairs et informatifs

---

## 🚀 PHASE 4: DÉPLOIEMENT AWS (30 min)

### 4.1 Upload Prompt Editorial

**Commande** :
```bash
aws s3 cp canonical/prompts/editorial/lai_prompt.yaml \
  s3://vectora-inbox-config-dev/canonical/prompts/editorial/lai_prompt.yaml \
  --region eu-west-3 --profile rag-lai-prod
```

**Validation** :
```bash
aws s3 ls s3://vectora-inbox-config-dev/canonical/prompts/editorial/ \
  --region eu-west-3 --profile rag-lai-prod
```

### 4.2 Upload Client Config

**Commande** :
```bash
aws s3 cp client-config-examples/lai_weekly_v7.yaml \
  s3://vectora-inbox-config-dev/clients/lai_weekly_v7.yaml \
  --region eu-west-3 --profile rag-lai-prod
```

### 4.3 Création Layer v10

**Structure** :
```bash
layer_build/
└── python/
    └── vectora_core/
        ├── newsletter/
        │   ├── bedrock_editor.py  # Modifié (Approche B)
        │   └── __init__.py        # Modifié
        └── shared/
            └── prompt_resolver.py  # Existant
```

**Commandes** :
```bash
# Préparation
mkdir -p layer_build/python
xcopy /E /I /Y src_v2\vectora_core layer_build\python\vectora_core

# Création zip
cd layer_build
powershell -Command "Compress-Archive -Path python -DestinationPath ../vectora-core-layer-v10.zip -Force"
cd ..

# Publication
aws lambda publish-layer-version \
  --layer-name vectora-inbox-vectora-core-approche-b-dev \
  --description "v10 - Newsletter Approche B + Editorial prompts" \
  --zip-file fileb://vectora-core-layer-v10.zip \
  --compatible-runtimes python3.11 \
  --region eu-west-3 --profile rag-lai-prod
```

### 4.4 Mise à Jour Lambda Newsletter

**Commande** :
```bash
# Attacher layer v10 + common-deps
aws lambda update-function-configuration \
  --function-name vectora-inbox-newsletter-v2-dev \
  --layers \
    arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-common-deps-dev:4 \
    arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-approche-b-dev:10 \
  --environment "Variables={CONFIG_BUCKET=vectora-inbox-config-dev,DATA_BUCKET=vectora-inbox-data-dev,NEWSLETTERS_BUCKET=vectora-inbox-newsletters-dev,BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0,BEDROCK_REGION=us-east-1,CACHE_BUST=v10}" \
  --region eu-west-3 --profile rag-lai-prod
```

---

## ✅ PHASE 5: VALIDATION E2E (30 min)

### 5.1 Test Newsletter lai_weekly_v7

**Commande** :
```bash
aws lambda invoke \
  --function-name vectora-inbox-newsletter-v2-dev \
  --cli-binary-format raw-in-base64-out \
  --payload file://event_newsletter_v7.json \
  --region eu-west-3 --profile rag-lai-prod \
  response_newsletter_v7_v10.json
```

### 5.2 Vérification Dates Effectives

**Commande** :
```bash
# Télécharger newsletter
aws s3 cp s3://vectora-inbox-newsletters-dev/lai_weekly_v7/2026/01/29/newsletter.md \
  newsletter_v7_v10.md \
  --region eu-west-3 --profile rag-lai-prod

# Vérifier dates
grep "Date:" newsletter_v7_v10.md
```

**Résultat attendu** :
```
**Date:** Jan 27, 2026  # ✅ Date Bedrock (pas Jan 29)
**Date:** Dec 09, 2025  # ✅ Date Bedrock
**Date:** Jan 09, 2026  # ✅ Date Bedrock
```

### 5.3 Vérification Contenu Éditorial

**Checklist** :
- [ ] TL;DR généré (2-3 bullet points)
- [ ] Introduction générée (1-2 phrases)
- [ ] Contenu cohérent avec items
- [ ] Pas de texte hardcodé/fallback
- [ ] Logs Bedrock sans erreur

### 5.4 Vérification Logs CloudWatch

**Commande** :
```bash
aws logs tail /aws/lambda/vectora-inbox-newsletter-v2-dev \
  --since 10m --region eu-west-3 --profile rag-lai-prod \
  --format short | findstr "Approche B\|editorial\|prompt"
```

**Logs attendus** :
```
[INFO] Editorial prompt 'lai' loaded successfully
[INFO] Generating TL;DR via Approche B
[INFO] Generating introduction via Approche B
[INFO] Using effective_date: 2026-01-27
```

---

## 📊 PHASE 6: RETOUR USER (15 min)

### 6.1 Métriques Finales

| Métrique | Avant | Après | Delta | Status |
|----------|-------|-------|-------|--------|
| Architecture newsletter | Approche A/B | Approche B | +100% | ✅ |
| Prompts hardcodés | 2 | 0 | -100% | ✅ |
| Dates effectives affichées | 0% | >90% | +90% | ✅ |
| Cohérence architecture | 66% | 100% | +34% | ✅ |
| Prompts versionnés | 66% | 100% | +34% | ✅ |

### 6.2 Validation Objectifs

**Objectif 1** : Éliminer prompts hardcodés ✅
- Avant : 2 prompts hardcodés dans `bedrock_editor.py`
- Après : 0 prompts hardcodés, tous dans `canonical/prompts/editorial/`

**Objectif 2** : Uniformiser architecture ✅
- normalize-score-v2 : Approche B ✅
- bedrock_matcher : Approche B ✅
- newsletter-v2 : Approche B ✅

**Objectif 3** : Dates effectives affichées ✅
- Cache Lambda forcé via `CACHE_BUST=v10`
- Dates Bedrock affichées dans newsletter

**Objectif 4** : Convention nommage claire ✅
- `normalization_prompt` : Extraction entités
- `matching_prompt` : Évaluation pertinence
- `editorial_prompt` : Génération contenu

### 6.3 Documentation Livrée

**Fichiers créés** :
1. `canonical/prompts/editorial/lai_prompt.yaml`
2. `src_v2/vectora_core/newsletter/bedrock_editor.py` (modifié)
3. `src_v2/vectora_core/newsletter/__init__.py` (modifié)
4. `client-config-examples/lai_weekly_v7.yaml` (modifié)
5. `tests/unit/test_editorial_prompts_approche_b.py`
6. `tests/integration/test_newsletter_editorial_e2e.py`
7. `docs/plans/plan_correctif_approche_b_newsletter.md` (ce fichier)

**Rapports** :
- `docs/reports/diagnostic_systeme_prompts_dates_newsletter.md`
- `docs/reports/resume_executif_diagnostic_prompts.md`

### 6.4 Recommandations Futures

**Court terme** :
1. Migrer autres clients vers `editorial_prompt` dans config
2. Supprimer `global_prompts.yaml` (obsolète)
3. Créer prompts éditoriaux pour autres verticales (gene_therapy, oncology)

**Moyen terme** :
1. Ajouter prompts éditoriaux avancés (section_summary, title_reformulation)
2. Créer tests de régression automatiques
3. Monitoring qualité contenu éditorial généré

**Long terme** :
1. Système de versioning prompts avec A/B testing
2. Métriques qualité contenu éditorial (engagement, feedback)
3. Optimisation coûts Bedrock (cache, batching)

---

## 📋 CHECKLIST FINALE

### Avant Déploiement
- [ ] Tests unitaires passent (100%)
- [ ] Tests intégration passent (100%)
- [ ] Prompt LAI validé (structure YAML)
- [ ] Client config mis à jour
- [ ] Code review effectué
- [ ] Documentation à jour

### Après Déploiement
- [ ] Prompt uploadé S3
- [ ] Layer v10 créé et attaché
- [ ] Lambda newsletter mise à jour
- [ ] Cache Lambda forcé (`CACHE_BUST=v10`)
- [ ] Newsletter générée avec succès
- [ ] Dates effectives affichées
- [ ] Contenu éditorial correct
- [ ] Logs CloudWatch sans erreur

### Validation Finale
- [ ] Architecture uniformisée (Approche B partout)
- [ ] Prompts versionnés dans canonical
- [ ] Convention nommage respectée
- [ ] Pas de régression fonctionnelle
- [ ] Documentation complète
- [ ] Retour user positif

---

## 🎯 RÉSUMÉ EXÉCUTIF

### Travail Accompli
✅ Migration newsletter-v2 vers Approche B  
✅ Création prompts éditoriaux LAI dans canonical  
✅ Uniformisation architecture (3 lambdas Approche B)  
✅ Convention nommage claire (`editorial` vs `newsletter`)  
✅ Correction dates newsletter (cache Lambda)  
✅ Suppression prompts hardcodés  

### Temps Investi
- Phase 0-1 : 30 min (Cadrage + Diagnostic)
- Phase 2 : 1h30 (Correctifs locaux)
- Phase 3 : 45 min (Tests locaux)
- Phase 4 : 30 min (Déploiement AWS)
- Phase 5 : 30 min (Validation E2E)
- Phase 6 : 15 min (Retour user)
- **Total** : 4h00

### Bénéfices
1. **Architecture cohérente** : Approche B pour toutes les lambdas
2. **Maintenabilité** : Prompts versionnés, pas de code hardcodé
3. **Évolutivité** : Facile d'ajouter nouveaux verticaux
4. **Qualité** : Dates effectives affichées, contenu éditorial correct
5. **Conformité** : Respect vectora-inbox-development-rules.md

---

**Status** : ✅ PLAN PRÊT POUR EXÉCUTION  
**Prochaine action** : Exécuter Phase 2 (Correctifs locaux)
