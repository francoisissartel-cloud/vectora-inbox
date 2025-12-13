# Diagnostic Corporate HTML : Peptron & Camurus

**Date :** 2024-12-19  
**Objectif :** Vérifier et corriger l'ingestion HTML pour Peptron & Camurus en DEV  

## A1 - Diagnostic repo ↔ AWS

### A1.1 - Vérification fichiers repo ✅

**Fichiers clés présents et analysés :**

1. **`src/vectora_core/ingestion/parser.py`** ✅
   - Parser HTML générique implémenté avec `_parse_html_page()`
   - Support ingestion_mode='html' dans `parse_source_content()`
   - Fallback BeautifulSoup avec patterns courants (article, div news/post/item)

2. **`src/vectora_core/ingestion/html_extractor.py`** ✅
   - Classe `ConfigurableHTMLExtractor` implémentée
   - Chargement config depuis `canonical/sources/html_extractors.yaml`
   - Fallback automatique sur parser générique si pas de config spécifique

3. **`canonical/sources/source_catalog.yaml`** ✅
   - Camurus : `html_url: "https://www.camurus.com/media/press-releases/"`, `ingestion_mode: "html"`
   - Peptron : `html_url: "https://www.peptron.co.kr/eng/pr/news.php"`, `ingestion_mode: "html"`
   - Bouquet `lai_corporate_mvp` contient bien les 5 sources corporate

4. **`canonical/sources/html_extractors.yaml`** ✅
   - **Camurus** : extracteur spécifique avec sélecteurs pour press releases
   - **Peptron** : extracteur spécifique avec `ssl_verify: false` pour certificat SSL invalide
   - Configuration globale avec fallback_selectors

### A1.2 - Vérification AWS DEV ✅

**Vérification Lambda vectora-inbox-ingest-normalize-dev :**
- ✅ Lambda existe : `vectora-inbox-ingest-normalize-dev`
- ✅ Runtime : Python 3.12
- ✅ Timeout : 600s, Memory : 512MB
- ✅ Variables d'environnement :
  - `CONFIG_BUCKET`: `vectora-inbox-config-dev`
  - `DATA_BUCKET`: `vectora-inbox-data-dev`
  - `ENV`: `dev`
  - `BEDROCK_MODEL_ID`: `eu.anthropic.claude-sonnet-4-5-20250929-v1:0`
- ⚠️ **ReservedConcurrentExecutions** : NON CONFIGURÉ (limite compte : 10 total)

**Vérification bucket config S3 :**
- ✅ Bucket `vectora-inbox-config-dev` accessible
- ✅ Fichiers canonical présents :
  - `canonical/sources/source_catalog.yaml` (4.8KB, 2025-12-10)
  - `canonical/sources/html_extractors.yaml` (2.6KB, 2025-12-10)
- ✅ **Synchronisation parfaite** : fichiers repo ↔ S3 identiques (fc confirme)

**Analyse logs récents (2025-12-11 09:47-09:50) :**
- ✅ Exécution lai_weekly_v2 réussie : **104 items normalisés**
- ⚠️ **PROBLÈME THROTTLING MAJEUR** :
  - Nombreuses `ThrottlingException` Bedrock
  - Plusieurs échecs après 4 tentatives
  - Durée excessive : **485 secondes** (8+ minutes)
  - **CAUSE IDENTIFIÉE** : `MAX_BEDROCK_WORKERS = 4` dans `normalizer.py`

### A1.3 - Diagnostic final A1 ✅

**Résumé diagnostic repo ↔ AWS :**
- ✅ **Parser HTML générique** : implémenté dans `parser.py`
- ✅ **Extracteurs spécifiques** : Camurus et Peptron configurés dans `html_extractors.yaml`
- ✅ **Synchronisation S3** : fichiers canonical à jour en DEV
- ✅ **Lambda packaging** : dernière version déployée (2025-12-10)
- ⚠️ **Throttling Bedrock** : parallélisation excessive (4 workers → quota DEV saturé)

## A2 - Corrections de sync & config

### A2.1 - Correction throttling Bedrock ✅

**Problème identifié :**
- `MAX_BEDROCK_WORKERS = 4` dans `src/vectora_core/normalization/normalizer.py`
- Quota Bedrock DEV limité → ThrottlingException en cascade
- Durée d'exécution excessive (8+ minutes pour 104 items)

**Correction appliquée :**
- ✅ Modification `src/vectora_core/normalization/normalizer.py` :
  ```python
  # Avant
  MAX_BEDROCK_WORKERS = 4
  
  # Après
  import os
  MAX_BEDROCK_WORKERS = 1 if os.environ.get('ENV') == 'dev' else 4
  ```
- ✅ **Impact** : DEV utilise 1 worker, PROD garde 4 workers
- ✅ **Bénéfice attendu** : réduction drastique des ThrottlingException en DEV

### A2.2 - Vérification configurations spécifiques ✅

**Peptron SSL :**
- ✅ Configuration `ssl_verify: false` présente dans `html_extractors.yaml`
- ✅ Certificat SSL invalide de peptron.co.kr géré correctement

**Camurus extracteur :**
- ✅ Sélecteurs spécifiques configurés pour structure press releases
- ✅ Base URL et format de date définis

### A2.3 - Redéploiement requis ⚠️

**Action nécessaire :**
- ⚠️ **Redéploiement Lambda** requis pour appliquer la correction MAX_BEDROCK_WORKERS
- ⚠️ Utiliser le processus de déploiement existant (CDK/CloudFormation)

**Status A2 :** Corrections code terminées, redéploiement en attente