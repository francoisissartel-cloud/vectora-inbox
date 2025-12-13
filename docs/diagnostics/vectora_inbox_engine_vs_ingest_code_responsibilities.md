# Audit Métier - Responsabilités Code Engine vs Ingest-Normalize

**Date** : 2025-12-12  
**Objectif** : Analyser les responsabilités métier prévues dans le code des deux Lambdas  

---

## 1. Lambda Ingest-Normalize - Responsabilités Métier

### 1.1 Handler (`src/lambdas/ingest_normalize/handler.py`)

**Responsabilités Handler** :
- ✅ Point d'entrée AWS Lambda uniquement
- ✅ Parsing événement (client_id, sources, period_days, dates)
- ✅ Lecture variables d'environnement (CONFIG_BUCKET, DATA_BUCKET, BEDROCK_MODEL_ID)
- ✅ Délégation complète à `run_ingest_normalize_for_client()`
- ✅ Formatage réponse (statusCode, body JSON)
- ✅ Gestion erreurs globales

**Aucune logique métier dans le handler** ✅

### 1.2 Fonction Métier (`vectora_core.run_ingest_normalize_for_client()`)

**Responsabilités Métier Prévues** :
1. **Phase 1A - Ingestion** :
   - Chargement configuration client + canonical depuis S3
   - Résolution bouquets sources (développement source_key)
   - Récupération contenu brut (HTTP/RSS) via `fetcher.fetch_source()`
   - Parsing contenu en items structurés via `parser.parse_source_content()`

2. **Phase 1B - Normalisation** :
   - Application filtre temporel (period_days)
   - Normalisation items avec Bedrock via `normalizer.normalize_items_batch()`
   - Détection entités + classification + résumé
   - Écriture items normalisés dans S3 (DATA_BUCKET)

**Workflow Prévu** :
```
Sources → Ingestion → Parsing → Filtre Temporel → Normalisation Bedrock → S3
```

**Variables d'Environnement Utilisées** :
- `CONFIG_BUCKET` : Configuration client + canonical
- `DATA_BUCKET` : Écriture items normalisés
- `BEDROCK_MODEL_ID` : Modèle pour normalisation
- `PUBMED_API_KEY_PARAM` : API PubMed (optionnel)

---

## 2. Lambda Engine - Responsabilités Métier

### 2.1 Handler (`src/lambdas/engine/handler.py`)

**Responsabilités Handler** :
- ✅ Point d'entrée AWS Lambda uniquement
- ✅ Parsing événement (client_id, period_days, dates, target_date)
- ✅ Lecture variables d'environnement (CONFIG_BUCKET, DATA_BUCKET, NEWSLETTERS_BUCKET, BEDROCK_MODEL_ID)
- ✅ Support configuration hybride Bedrock (P1) :
  - `BEDROCK_REGION_NEWSLETTER` / `BEDROCK_MODEL_ID_NEWSLETTER`
  - `BEDROCK_REGION_NORMALIZATION` / `BEDROCK_MODEL_ID_NORMALIZATION`
- ✅ Paramètres cache newsletter (`force_regenerate`)
- ✅ Délégation complète à `run_engine_for_client()`

**Aucune logique métier dans le handler** ✅

### 2.2 Fonction Métier (`vectora_core.run_engine_for_client()`)

**Responsabilités Métier Prévues** :
1. **Phase 2 - Matching** :
   - Chargement configuration client + canonical + scoring_rules + matching_rules
   - Collecte items normalisés depuis S3 (fenêtre temporelle)
   - Application filtres d'exclusion (HR/Finance) via `exclusion_filter`
   - Matching items aux watch_domains via `matcher.match_items_to_domains()`

2. **Phase 3 - Scoring** :
   - Scoring items matchés via `scorer.score_items()`
   - Support système `domain_relevance` (nouveau) vs matching traditionnel
   - Tri et sélection items top

3. **Phase 4 - Newsletter** :
   - Génération newsletter avec Bedrock via `assembler.generate_newsletter()`
   - Écriture newsletter dans S3 (NEWSLETTERS_BUCKET)
   - Support contenu éditorial JSON

**Workflow Prévu** :
```
S3 Items → Collecte → Exclusions → Matching → Scoring → Newsletter Bedrock → S3
```

**Variables d'Environnement Utilisées** :
- `CONFIG_BUCKET` : Configuration client + canonical + règles
- `DATA_BUCKET` : Lecture items normalisés
- `NEWSLETTERS_BUCKET` : Écriture newsletter finale
- `BEDROCK_MODEL_ID` : Modèle pour génération newsletter
- Configuration hybride P1 (newsletter vs normalisation)

---

## 3. Analyse des Responsabilités

### 3.1 Séparation des Responsabilités ✅

| **Aspect** | **Ingest-Normalize** | **Engine** |
|------------|---------------------|------------|
| **Phase** | 1A (Ingestion) + 1B (Normalisation) | 2 (Matching) + 3 (Scoring) + 4 (Newsletter) |
| **Input** | Sources externes (RSS, APIs) | Items normalisés S3 |
| **Output** | Items normalisés → S3 | Newsletter → S3 |
| **Bedrock Usage** | Normalisation (entités, classification) | Génération newsletter |
| **S3 Read** | Configuration uniquement | Configuration + Items normalisés |
| **S3 Write** | Items normalisés (DATA_BUCKET) | Newsletter (NEWSLETTERS_BUCKET) |

**Conclusion** : Séparation claire et logique ✅

### 3.2 Chevauchements Identifiés ⚠️

**1. Configuration Loading** :
- **Ingest-Normalize** : Charge client_config + canonical_scopes + source_catalog
- **Engine** : Charge client_config + canonical_scopes + scoring_rules + matching_rules
- **Impact** : Duplication acceptable (configurations différentes)

**2. Period Days Resolution** :
- **Ingest-Normalize** : Résout period_days pour filtre temporel ingestion
- **Engine** : Résout period_days pour fenêtre collecte items
- **Impact** : Logique identique mais usage différent ✅

**3. Bedrock Usage** :
- **Ingest-Normalize** : Normalisation items (us-east-1)
- **Engine** : Génération newsletter (eu-west-3 en mode hybride)
- **Impact** : Usages différents, pas de conflit ✅

### 3.3 Dépendances Identifiées

**Engine dépend d'Ingest-Normalize** :
- Engine lit les items normalisés produits par Ingest-Normalize
- Pas d'exécution Engine possible sans Ingest-Normalize préalable
- **Workflow** : Ingest-Normalize → Engine (séquentiel)

---

## 4. TODO et Commentaires Contradictoires

### 4.1 Dans Ingest-Normalize

**Commentaires Positifs** :
- ✅ Documentation claire des phases 1A/1B
- ✅ Séparation handler/logique métier respectée
- ✅ Variables d'environnement bien documentées

**TODO Identifiés** :
- Aucun TODO contradictoire majeur identifié

### 4.2 Dans Engine

**Commentaires Positifs** :
- ✅ Documentation claire des phases 2/3/4
- ✅ Support configuration hybride Bedrock (P1)
- ✅ Gestion cas edge (aucun item trouvé)

**TODO Identifiés** :
- Configuration hybride marquée "P1" (implémentée mais en cours d'optimisation)
- Support cache newsletter (`force_regenerate`) implémenté

### 4.3 Évolutions Récentes Identifiées

**1. Configuration Hybride Bedrock** :
- Engine handler supporte régions/modèles séparés pour newsletter vs normalisation
- Permet d'utiliser us-east-1 pour normalisation, eu-west-3 pour newsletter
- **Statut** : Implémenté, en cours de validation

**2. Système Domain Relevance** :
- Engine supporte nouveau système `domain_relevance` vs matching traditionnel
- Détection automatique du système à utiliser
- **Statut** : Implémenté, opérationnel

**3. Filtres d'Exclusion** :
- Engine applique filtres HR/Finance avant matching
- Module `exclusion_filter` dédié
- **Statut** : Implémenté, opérationnel

---

## 5. Synthèse des Responsabilités

### 5.1 Ingest-Normalize - Responsabilités Finales

**Ce que fait cette Lambda** :
1. ✅ Scraping sources externes (RSS, APIs, HTML)
2. ✅ Parsing contenu brut en items structurés
3. ✅ Application filtre temporel (period_days)
4. ✅ Normalisation Bedrock (entités, classification, résumé)
5. ✅ Écriture items normalisés dans S3

**Ce qu'elle ne fait PAS** :
- ❌ Matching aux domaines client
- ❌ Scoring des items
- ❌ Génération newsletter
- ❌ Lecture items normalisés existants

### 5.2 Engine - Responsabilités Finales

**Ce que fait cette Lambda** :
1. ✅ Collecte items normalisés depuis S3
2. ✅ Application filtres d'exclusion (HR/Finance)
3. ✅ Matching items aux watch_domains client
4. ✅ Scoring et sélection items pertinents
5. ✅ Génération newsletter avec Bedrock
6. ✅ Écriture newsletter finale dans S3

**Ce qu'elle ne fait PAS** :
- ❌ Scraping sources externes
- ❌ Normalisation items bruts
- ❌ Écriture items normalisés

---

## 6. Conclusion

### 6.1 Architecture Saine ✅

**Points Forts** :
- Séparation claire des responsabilités métier
- Handlers minimalistes (délégation complète à vectora_core)
- Workflow séquentiel logique (Ingest → Engine)
- Pas de chevauchements problématiques
- Évolutions récentes bien intégrées

### 6.2 Pas de Problèmes Architecturaux Majeurs

**Aucun conflit identifié** :
- Pas de logique métier dupliquée
- Pas de responsabilités contradictoires
- Pas de TODO bloquants

### 6.3 Évolutions Récentes Cohérentes

**Améliorations Identifiées** :
- Configuration hybride Bedrock (résolution fallback newsletter)
- Système domain_relevance (amélioration matching)
- Filtres d'exclusion (amélioration qualité signal)

**Recommandation** : L'architecture code est saine. Les problèmes de fallback newsletter ne viennent pas de la répartition des responsabilités mais probablement de la configuration AWS ou des permissions.