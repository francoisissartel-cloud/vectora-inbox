# Plan de Test End-to-End : Vectora Inbox MVP lai_weekly_v3

**Date :** 17 décembre 2025  
**Objectif :** Test end-to-end complet du workflow Vectora Inbox jusqu'à normalize + matching + scoring  
**Client MVP :** lai_weekly_v3  
**Périmètre :** Lambdas V2 (ingest_v2 + normalize_score_v2) - PAS de newsletter  

---

## Phase 1 – Cadrage & Objectifs

### 1.1 Rôle global de Vectora Inbox

Vectora Inbox est un moteur d'intelligence sectorielle qui automatise la veille technologique :
- **Ingestion** : Collecte de contenus depuis sources externes (RSS, APIs, scraping)
- **Normalisation** : Extraction d'entités et classification via Bedrock
- **Matching** : Association aux domaines de veille client
- **Scoring** : Calcul de pertinence selon règles métier
- **Newsletter** : Génération de contenu éditorial (future Lambda 3)

### 1.2 Périmètre de ce test

**Workflow testé** : `ingest_v2` → `normalize_score_v2` → rapport détaillé  
**Client unique** : `lai_weekly_v3` (Long-Acting Injectables)  
**Exclusions** : Lambda newsletter (pas encore implémentée)  

### 1.3 Hypothèses environnement AWS

- **AWS Profile** : `rag-lai-prod`
- **Région principale** : `eu-west-3` (Paris)
- **Région Bedrock** : `us-east-1` (observé dans le code V2)
- **Compte AWS** : `786469175371`
- **Buckets S3** :
  - Config : `vectora-inbox-config-dev`
  - Data : `vectora-inbox-data-dev`
- **Lambdas** :
  - Ingest : `vectora-inbox-ingest-v2-dev` (handler ingest_v2)
  - Normalize : `vectora-inbox-normalize-score-v2-dev` (handler normalize_score_v2)

### 1.4 Critères de succès

**Fonctionnels** :
- ✅ Lambdas V2 trouvent automatiquement les clients actifs (lai_weekly_v3 avec `active: true`)
- ✅ Ingestion produit des items bruts cohérents dans S3 `ingested/`
- ✅ Normalisation + matching + scoring s'appliquent au dernier run d'ingest
- ✅ Métriques quantitatives + exemples qualitatifs d'items disponibles

**Techniques** :
- ✅ Respect strict de `src_lambda_hygiene_v4.md`
- ✅ Moteur générique piloté par `client_config` + `canonical`
- ✅ Pas de logique hardcodée spécifique au client
- ✅ Gestion d'erreurs robuste avec fallback

---

## Phase 2 – Stratégie de Test / Instrumentation

### 2.1 Méthode d'activation des Lambdas

**Test réel sur environnement AWS** (pas de simulation) :

**Activation ingest_v2** :
```bash
aws lambda invoke \
  --function-name vectora-inbox-ingest-normalize-dev \
  --payload '{"handler_type": "ingest_v2", "client_id": "lai_weekly_v3"}' \
  --profile rag-lai-prod \
  --region eu-west-3 \
  response_ingest.json
```

**Activation normalize_score_v2** :
```bash
aws lambda invoke \
  --function-name vectora-inbox-ingest-normalize-dev \
  --payload '{"handler_type": "normalize_score_v2", "client_id": "lai_weekly_v3"}' \
  --profile rag-lai-prod \
  --region eu-west-3 \
  response_normalize.json
```

**Justification payload minimal** : Les Lambdas V2 scannent automatiquement les `client_config` avec `active: true`, donc seul `client_id` est requis.

### 2.2 Métriques à mesurer

**Pour ingest_v2** :
- Nombre de clients actifs trouvés (attendu : 1 = lai_weekly_v3)
- Nombre de sources interrogées (attendu : 8 sources des bouquets `lai_corporate_mvp` + `lai_press_mvp`)
- Nombre d'items bruts récupérés par source
- Latence globale et par étape (chargement config, résolution sources, ingestion)
- Erreurs réseau/parsing par source

**Pour normalize_score_v2** :
- Nombre d'items pris en entrée (du dernier run d'ingest)
- Nombre d'appels Bedrock pour normalisation (1 par item)
- Nombre d'appels Bedrock pour matching (si implémenté, sinon matching déterministe)
- Distribution des scores de pertinence (min, max, moyenne, quartiles)
- Nombre d'items matchés par `watch_domain` (`tech_lai_ecosystem`, `regulatory_lai`)
- Temps d'exécution total et par sous-étape (normalisation, matching, scoring)
- Coût estimé en tokens Bedrock

### 2.3 Outils d'observation

**CloudWatch Logs** :
- `/aws/lambda/vectora-inbox-ingest-normalize-dev` : Logs des deux handlers
- Filtres par `handler_type` pour séparer ingest_v2 vs normalize_score_v2

**S3 Data Bucket** :
- `s3://vectora-inbox-data-dev/ingested/lai_weekly_v3/` : Items bruts ingérés
- `s3://vectora-inbox-data-dev/curated/lai_weekly_v3/` : Items normalisés et scorés

**Scripts de diagnostic** :
- `scripts/validate_s3_output.py` : Analyse des outputs S3
- Création de scripts d'analyse spécifiques si nécessaire (dans `/scripts`, pas `/src`)

---

## Phase 3 – Run Ingestion V2 (MVP lai_weekly_v3)

### 3.1 Pré-requis et validation

**Vérification client_config** :
```bash
aws s3 cp s3://vectora-inbox-config-dev/clients/lai_weekly_v3.yaml . \
  --profile rag-lai-prod --region eu-west-3
```
- ✅ Confirmer `active: true`
- ✅ Vérifier `source_bouquets_enabled: [lai_corporate_mvp, lai_press_mvp]`
- ✅ Valider `watch_domains` avec scopes LAI

**Vérification canonical** :
```bash
aws s3 ls s3://vectora-inbox-config-dev/canonical/sources/ \
  --profile rag-lai-prod --region eu-west-3
```
- ✅ Présence de `source_catalog.yaml`
- ✅ Bouquets `lai_corporate_mvp` et `lai_press_mvp` définis

### 3.2 Exécution du run d'ingestion

**Commande d'activation** :
```bash
aws lambda invoke \
  --function-name vectora-inbox-ingest-normalize-dev \
  --payload '{"handler_type": "ingest_v2", "client_id": "lai_weekly_v3"}' \
  --profile rag-lai-prod \
  --region eu-west-3 \
  response_ingest_e2e.json
```

**Observation temps réel** :
```bash
aws logs tail /aws/lambda/vectora-inbox-ingest-normalize-dev \
  --follow --filter-pattern "ingest_v2" \
  --profile rag-lai-prod --region eu-west-3
```

### 3.3 Métriques à collecter

**Métriques fonctionnelles** :
- Nombre de clients actifs scannés et traités
- Résolution des bouquets en sources individuelles
- Nombre d'items ingérés par source (attendu : 10-50 items total)
- Types de contenus obtenus (corporate news, press articles)

**Métriques techniques** :
- Temps d'exécution total (attendu : 2-5 minutes)
- Temps par étape : config loading, source resolution, ingestion
- Erreurs HTTP par source (timeouts, 404, parsing failures)
- Taille des outputs S3

**Validation des outputs** :
```bash
aws s3 ls s3://vectora-inbox-data-dev/ingested/lai_weekly_v3/ \
  --recursive --profile rag-lai-prod --region eu-west-3
```

**Structure attendue** :
```
ingested/lai_weekly_v3/2025/12/17/items.json
```

**Analyse qualitative** (3-5 items représentatifs) :
- Titre, URL, source, date de publication
- Qualité du parsing (contenu complet vs tronqué)
- Pertinence LAI apparente (mentions MedinCell, Camurus, technologies LAI)

---

## Phase 4 – Run Normalize/Match/Score V2

### 4.1 Pré-requis

**Vérification des scopes canonical** :
```bash
aws s3 cp s3://vectora-inbox-config-dev/canonical/scopes/company_scopes.yaml . \
  --profile rag-lai-prod --region eu-west-3
```
- ✅ Scope `lai_companies_global` avec 180+ entreprises LAI
- ✅ Scope `lai_companies_mvp_core` avec pure players (MedinCell, Camurus, etc.)

**Vérification des prompts Bedrock** :
```bash
aws s3 cp s3://vectora-inbox-config-dev/canonical/prompts/global_prompts.yaml . \
  --profile rag-lai-prod --region eu-west-3
```
- ✅ Prompt `normalization.lai_default` configuré
- ✅ Prompt `matching.matching_watch_domains_v2` (si matching Bedrock implémenté)

### 4.2 Exécution du run de normalisation

**Commande d'activation** :
```bash
aws lambda invoke \
  --function-name vectora-inbox-ingest-normalize-dev \
  --payload '{"handler_type": "normalize_score_v2", "client_id": "lai_weekly_v3"}' \
  --profile rag-lai-prod \
  --region eu-west-3 \
  response_normalize_e2e.json
```

**Observation temps réel** :
```bash
aws logs tail /aws/lambda/vectora-inbox-ingest-normalize-dev \
  --follow --filter-pattern "normalize_score_v2" \
  --profile rag-lai-prod --region eu-west-3
```

### 4.3 Métriques à collecter

**Pipeline interne observé** :
- Chargement des configs + canonical (temps et taille)
- Identification du dernier run d'ingest (path S3 résolu)
- Nombre d'items récupérés pour traitement

**Normalisation Bedrock** :
- Nombre d'items normalisés avec succès
- Temps moyen par appel Bedrock (attendu : 2-4 secondes)
- Entités extraites par catégorie :
  - Companies détectées (attendu : 10-15 avec MedinCell, Camurus, Teva, etc.)
  - Molecules détectées (attendu : 3-8 avec olanzapine, risperidone, etc.)
  - Technologies détectées (attendu : 5-12 avec "Long-Acting Injectable", "Extended-Release", etc.)
  - Trademarks détectées (attendu : 2-6 avec UZEDY®, Aristada, etc.)

**Matching par domaines** :
- Items matchés à `tech_lai_ecosystem` (attendu : 60-80% des items LAI)
- Items matchés à `regulatory_lai` (attendu : 20-40% des items)
- Items non matchés avec raisons (exclusions, seuils non atteints)
- Efficacité du matching flexible (variations de noms d'entreprises)

**Scoring de pertinence** :
- Distribution des scores finaux (histogramme 0-20)
- Items avec scores élevés (>15) : contenu et justification
- Items avec scores faibles (<5) : analyse du bruit
- Application des bonus LAI :
  - Pure player bonus (+5.0) : MedinCell, Camurus, etc.
  - Trademark bonus (+4.0) : UZEDY®, Aristada, etc.
  - Partnership bonus (+3.0) : annonces de partenariats

**Coûts et performance** :
- Tokens Bedrock consommés (input + output)
- Coût estimé du run complet (attendu : $0.03-0.10)
- Temps d'exécution total (attendu : 3-8 minutes selon nombre d'items)

### 4.4 Validation des outputs

**Structure S3 attendue** :
```bash
aws s3 ls s3://vectora-inbox-data-dev/curated/lai_weekly_v3/2025/12/17/ \
  --profile rag-lai-prod --region eu-west-3
```

**Analyse qualitative** (3-5 items représentatifs) :
- Item avec score maximal : contenu, entités, domaines matchés, score breakdown
- Item avec trademark LAI : traitement privilégié vérifié
- Item regulatory : matching au domaine `regulatory_lai`
- Item exclu : raisons d'exclusion (bruit, score trop faible)

---

## Phase 5 – Validation de la Conformité

### 5.1 Respect des règles d'hygiène V4

**Architecture** :
- ✅ Code dans `src_v2/` (pas l'ancien `/src/`)
- ✅ Handlers minimaux délégant à `vectora_core`
- ✅ Séparation claire ingest vs normalize_score
- ✅ Aucune duplication de code métier

**Dépendances** :
- ✅ Aucune lib tierce dans `/src/`
- ✅ Utilisation des Lambda Layers
- ✅ Pas de stubs `_yaml` ou contournements

**Configuration** :
- ✅ Logique métier pilotée par `client_config` + `canonical`
- ✅ Pas de hardcoding spécifique à lai_weekly_v3
- ✅ Généricité du moteur préservée

### 5.2 Validation environnement AWS

**Ressources utilisées** :
- ✅ Région `eu-west-3` pour ressources principales
- ✅ Région `us-east-1` pour Bedrock (configuration observée)
- ✅ Profil `rag-lai-prod` utilisé
- ✅ Conventions de nommage respectées

**Modèles Bedrock** :
- ✅ Modèle par défaut : `anthropic.claude-3-sonnet-20240229-v1:0`
- ✅ Configuration hybride supportée si nécessaire
- ✅ Gestion des erreurs Bedrock avec retry

---

## Phase 6 – Critères d'Arrêt et Validation

### 6.1 Critères de succès technique

**Ingestion** :
- ✅ Au moins 10 items ingérés depuis sources LAI
- ✅ Aucune erreur critique (500, timeout Lambda)
- ✅ Temps d'exécution < 10 minutes

**Normalisation** :
- ✅ Taux de normalisation > 90% (items traités avec succès)
- ✅ Entités LAI détectées (companies, molecules, technologies, trademarks)
- ✅ Temps d'exécution < 15 minutes

**Matching** :
- ✅ Taux de matching > 50% (items matchés aux domaines LAI)
- ✅ Les deux domaines `tech_lai_ecosystem` et `regulatory_lai` alimentés
- ✅ Traitement privilégié des trademarks fonctionnel

**Scoring** :
- ✅ Distribution cohérente des scores (pas tous à 0 ou 20)
- ✅ Items LAI pertinents avec scores élevés (>12)
- ✅ Bonus LAI appliqués correctement

### 6.2 Critères de succès métier

**Qualité du signal** :
- ✅ Items haute valeur identifiés (partnerships, regulatory, clinical)
- ✅ Pure players LAI (MedinCell, Camurus) bien scorés
- ✅ Trademarks LAI (UZEDY®, Aristada) détectés et privilégiés
- ✅ Bruit filtré (items non-LAI exclus)

**Préparation newsletter** :
- ✅ Suffisamment d'items scorés pour alimenter 4 sections newsletter
- ✅ Répartition équilibrée entre domaines tech vs regulatory
- ✅ Items récents privilégiés (facteur de recency appliqué)

### 6.3 Seuils d'alerte

**Seuils critiques** (échec du test) :
- ❌ 0 items ingérés ou normalisés
- ❌ Erreurs Bedrock > 20%
- ❌ Taux de matching = 0%
- ❌ Tous les scores identiques (logique de scoring cassée)

**Seuils d'optimisation** (succès partiel) :
- ⚠️ Taux de matching < 30%
- ⚠️ Coût Bedrock > $0.20 par run
- ⚠️ Temps d'exécution > 20 minutes total
- ⚠️ Moins de 5 items avec score > 10

---

## Phase 7 – Livrables Attendus

### 7.1 Rapport technique détaillé

**Fichier** : `docs/diagnostics/vectora_inbox_mvp_lai_weekly_v3_e2e_test_report.md`

**Structure obligatoire** :
1. **Résumé exécutif** (10-15 lignes)
2. **Métriques d'ingestion** (sources, items, erreurs)
3. **Métriques de normalisation** (Bedrock, entités, temps)
4. **Métriques de matching** (domaines, taux, exemples)
5. **Métriques de scoring** (distribution, bonus, seuils)
6. **Analyse coûts/performance** (Bedrock, Lambda, scalabilité)
7. **Évaluation client_config + canonical** (qualité, complétude)
8. **Conformité hygiene_v4** (violations, déviations)
9. **Recommandations concrètes** (priorités, actions)

### 7.2 Données de validation

**Exemples d'items** (5-8 items représentatifs) :
- Items parfaitement matchés et scorés
- Items avec trademarks LAI privilégiés
- Items regulatory bien classifiés
- Items exclus avec justification

**Métriques quantitatives** :
- Tableaux de distribution (scores, domaines, sources)
- Temps d'exécution par phase
- Coûts Bedrock détaillés
- Taux d'erreur par composant

### 7.3 Recommandations d'amélioration

**Priorité 1** (critiques pour newsletter) :
- Corrections de matching si taux < 50%
- Optimisations de prompts si entités manquées
- Ajustements de scoring si distribution incohérente

**Priorité 2** (optimisations) :
- Réduction des coûts Bedrock
- Amélioration des temps d'exécution
- Enrichissement des scopes canonical

**Priorité 3** (évolutions futures) :
- Nouvelles sources LAI
- Domaines de veille supplémentaires
- Métriques de qualité avancées

---

## Validation Finale

### Checklist pré-exécution

- [ ] Client `lai_weekly_v3` avec `active: true` déployé sur S3
- [ ] Scopes canonical LAI complets et à jour
- [ ] Prompts Bedrock canonicalisés configurés
- [ ] Lambdas V2 déployées et fonctionnelles
- [ ] Accès AWS avec profil `rag-lai-prod` configuré
- [ ] Scripts de validation dans `/scripts` prêts

### Checklist post-exécution

- [ ] Rapport technique complet rédigé
- [ ] Métriques quantitatives collectées et analysées
- [ ] Exemples qualitatifs documentés
- [ ] Recommandations concrètes formulées
- [ ] Conformité hygiene_v4 validée
- [ ] Prêt pour implémentation Lambda newsletter

---

**Plan validé pour exécution immédiate sur environnement AWS rag-lai-prod**