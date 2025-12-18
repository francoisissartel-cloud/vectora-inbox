# Plan de Test : Workflow MVP lai_weekly_v3

**Date** : 16 janvier 2025  
**Objectif** : Test end-to-end du workflow ingest V2 → normalize_score V2 pour le client `lai_weekly_v3`  
**Environnement** : AWS eu-west-3, profil rag-lai-prod, compte 786469175371  

---

## Phase 0 – Préambule & rappel des objectifs

### Résumé du workflow à tester

- **Lambda ingest V2** : Ingestion brute, sources activées, écriture S3 `ingested/`
- **Lambda normalize_score V2** : Normalisation, matching, scoring, écriture S3 `curated/`
- **Déclenchement** : Event minimal `{}` → détection clients actifs (`active = true`)
- **Client MVP** : `lai_weekly_v3` avec config complète (2 domaines, scopes LAI, règles scoring)

### Objectifs du test

- ✅ **Fonctionnel** : Vérifier que le workflow fonctionne end-to-end sur `lai_weekly_v3`
- ✅ **Conformité** : Valider le respect des règles d'hygiène V4 (architecture, généricité, AWS)
- ✅ **Qualité** : Évaluer la pertinence de la normalisation, matching, scoring
- ✅ **Performance** : Mesurer coûts Bedrock, latence, scalabilité
- ✅ **Robustesse** : Tester gestion d'erreurs, retry, cas limites

### Contraintes et prérequis

- **Pas de refactoring** : Uniquement tester, mesurer, diagnostiquer
- **Environnement réel** : AWS avec vraies données, vrais appels Bedrock
- **Client actif** : `lai_weekly_v3.yaml` avec `active: true`
- **Stratégie dernier run** : normalize_score V2 traite uniquement le dernier run d'ingestion

---

## Phase 1 – Audit statique du code et des configs

### 1.1 Vérification conformité règles d'hygiène V4

**Architecture src_v2 :**
- [ ] Structure 3 Lambdas V2 respectée : `ingest/`, `normalize_score/`, `newsletter/`
- [ ] Handlers minimaux dans `/src_v2/lambdas/*/handler.py`
- [ ] Logique métier dans `vectora_core/` avec modules séparés
- [ ] Imports relatifs corrects : `from ..shared import`, `from . import`
- [ ] Aucune dépendance tierce dans `/src_v2/`

**Généricité du code :**
- [ ] Aucun `if client_id == 'lai_weekly'` hardcodé
- [ ] Configuration pilotée par `client_config + canonical`
- [ ] Variables d'environnement standardisées
- [ ] Fonctions d'orchestration génériques

**Environnement AWS :**
- [ ] Région principale : `eu-west-3`
- [ ] Profil CLI : `rag-lai-prod`
- [ ] Buckets conformes : `vectora-inbox-{type}-dev`
- [ ] Bedrock région : `us-east-1` (défaut observé)

### 1.2 Analyse du contrat ingest V2 → normalize_score V2

**Détection clients actifs :**
- [ ] Mécanisme de scan des `client_config/*.yaml` avec filtre `active: true`
- [ ] Identification automatique de `lai_weekly_v3` comme client actif
- [ ] Gestion cas où aucun client actif trouvé

**Chemins S3 d'entrée/sortie :**
- **Input ingest V2** : Sources externes (RSS, APIs, scraping)
- **Output ingest V2** : `s3://vectora-inbox-data-dev/ingested/{client_id}/{YYYY}/{MM}/{DD}/items.json`
- **Input normalize_score V2** : Dernier run d'ingestion (stratégie identification)
- **Output normalize_score V2** : `s3://vectora-inbox-data-dev/curated/{client_id}/{YYYY}/{MM}/{DD}/items.json`

**Stratégie "dernier run uniquement" :**
- [ ] Méthode d'identification du dernier run par client
- [ ] Gestion multiples runs même jour (timestamp S3)
- [ ] Validation existence fichier `items.json`
- [ ] Comportement si aucun run trouvé

### 1.3 Configuration lai_weekly_v3

**Client config analysé :**
- **Domaines de veille** : `tech_lai_ecosystem` (high priority), `regulatory_lai` (high priority)
- **Sources** : `lai_corporate_mvp` (5 sources), `lai_press_mvp` (3 sources)
- **Matching** : `trademark_privileges` activé, `require_entity_signals`
- **Scoring** : Bonus pure_player (5.0), trademark (4.0), partnership (8.0)
- **Seuils** : min_score 12, max_items_total 15

**Scopes canonical utilisés :**
- `lai_companies_global` : 180+ entreprises LAI
- `lai_molecules_global` : 90+ molécules
- `lai_keywords` : 80+ mots-clés technologiques
- `lai_trademarks_global` : 70+ marques commerciales

**Résultat attendu Phase 1 :**
- Document d'audit avec écarts identifiés entre contrat métier et code réel
- Validation de la cohérence client_config ↔ canonical ↔ code
- Confirmation de la stratégie d'identification du dernier run

---

## Phase 2 – Plan de tests locaux (optionnel mais recommandé)

### 2.1 Simulation locale du workflow

**Fixtures de test :**
- [ ] Créer `tests/fixtures/lai_weekly_ingested_sample.json` avec 10-15 items représentatifs
- [ ] Couvrir cas typiques : partnerships MedinCell, updates cliniques, regulatory
- [ ] Inclure entités LAI : BEPO, Aristada, Camurus, buprenorphine, etc.
- [ ] Cas limites : items sans entités LAI, contenu très court/long

**Script de test local :**
- [ ] `scripts/test_normalize_score_v2_local.py`
- [ ] Mode mock Bedrock (`--mock-bedrock`) vs appels réels
- [ ] Chargement config depuis fichiers locaux (pas S3)
- [ ] Output local : `output/normalized_items_local.json`

**Tests unitaires par module :**
- [ ] `vectora_core/normalization/normalizer.py` : Extraction entités, classification
- [ ] `vectora_core/normalization/matcher.py` : Matching aux domaines de veille
- [ ] `vectora_core/normalization/scorer.py` : Calcul scores avec bonus/malus
- [ ] `vectora_core/normalization/bedrock_client.py` : Retry, timeout, gestion erreurs

### 2.2 Cas de test spécifiques

**Normalisation Bedrock :**
- [ ] Item avec entités LAI multiples → extraction correcte
- [ ] Item sans entité LAI → classification "non-relevant"
- [ ] Item avec trademark privilégié → boost détection
- [ ] Gestion timeout Bedrock (>30s)
- [ ] Gestion rate limiting (429)

**Matching domaines :**
- [ ] Item tech LAI → match `tech_lai_ecosystem`
- [ ] Item regulatory → match `regulatory_lai`
- [ ] Item sans signal LAI → aucun match
- [ ] Application `trademark_privileges` avec boost 2.5x

**Scoring LAI :**
- [ ] Pure player (MedinCell) → bonus 5.0
- [ ] Trademark (BEPO) → bonus 4.0
- [ ] Partnership → poids 8.0
- [ ] Score final > seuil 12 → sélection
- [ ] Score final < seuil 12 → rejet

---

## Phase 3 – Plan de tests AWS réels (profil rag-lai-prod)

### 3.1 Identification des fonctions Lambda réelles

**Commandes de découverte :**
```bash
# Lister les Lambdas Vectora Inbox
aws lambda list-functions --profile rag-lai-prod --region eu-west-3 \
  --query "Functions[?contains(FunctionName, 'vectora-inbox')].FunctionName"

# Vérifier les outputs CloudFormation
aws cloudformation describe-stacks --stack-name vectora-inbox-s1-runtime-dev \
  --profile rag-lai-prod --region eu-west-3 \
  --query "Stacks[0].Outputs"
```

**Fonctions attendues :**
- `vectora-inbox-ingest-normalize-dev` (existante, combine ingest+normalize)
- `vectora-inbox-engine-dev` (existante, matching+scoring+newsletter)
- **OU** nouvelles Lambdas V2 séparées si déployées

### 3.2 Stratégie d'invocation

**Test ingest V2 :**
```bash
# Event minimal pour déclencher scan clients actifs
aws lambda invoke \
  --function-name vectora-inbox-ingest-v2-dev \
  --payload '{}' \
  --profile rag-lai-prod --region eu-west-3 \
  response_ingest.json

# Event spécifique lai_weekly_v3
aws lambda invoke \
  --function-name vectora-inbox-ingest-v2-dev \
  --payload '{"client_id": "lai_weekly_v3"}' \
  --profile rag-lai-prod --region eu-west-3 \
  response_ingest_lai.json
```

**Vérification S3 post-ingestion :**
```bash
# Lister les runs d'ingestion lai_weekly_v3
aws s3 ls s3://vectora-inbox-data-dev/ingested/lai_weekly_v3/ \
  --recursive --profile rag-lai-prod --region eu-west-3

# Télécharger le dernier run pour inspection
aws s3 cp s3://vectora-inbox-data-dev/ingested/lai_weekly_v3/2025/01/16/items.json \
  ./ingested_items_sample.json --profile rag-lai-prod --region eu-west-3
```

**Test normalize_score V2 :**
```bash
# Event minimal (détection automatique dernier run)
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --payload '{"client_id": "lai_weekly_v3"}' \
  --profile rag-lai-prod --region eu-west-3 \
  response_normalize.json

# Event avec paramètres spécifiques
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --payload '{"client_id": "lai_weekly_v3", "scoring_mode": "balanced", "force_reprocess": true}' \
  --profile rag-lai-prod --region eu-west-3 \
  response_normalize_full.json
```

### 3.3 Collecte des logs et traces

**CloudWatch Logs :**
```bash
# Logs ingest V2
aws logs filter-log-events \
  --log-group-name "/aws/lambda/vectora-inbox-ingest-v2-dev" \
  --start-time $(date -d "1 hour ago" +%s)000 \
  --profile rag-lai-prod --region eu-west-3

# Logs normalize_score V2
aws logs filter-log-events \
  --log-group-name "/aws/lambda/vectora-inbox-normalize-score-v2-dev" \
  --start-time $(date -d "1 hour ago" +%s)000 \
  --profile rag-lai-prod --region eu-west-3
```

**Inspection S3 résultats :**
```bash
# Télécharger les items normalisés
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v3/2025/01/16/items.json \
  ./curated_items_sample.json --profile rag-lai-prod --region eu-west-3

# Comparer volumes ingested vs curated
aws s3api head-object --bucket vectora-inbox-data-dev \
  --key ingested/lai_weekly_v3/2025/01/16/items.json \
  --profile rag-lai-prod --region eu-west-3 --query "ContentLength"

aws s3api head-object --bucket vectora-inbox-data-dev \
  --key curated/lai_weekly_v3/2025/01/16/items.json \
  --profile rag-lai-prod --region eu-west-3 --query "ContentLength"
```

---

## Phase 4 – Métriques techniques & métier à collecter

### 4.1 Métriques d'ingestion

**Sources et volumes :**
- `sources_activated_count` : Nombre de sources activées pour lai_weekly_v3
- `sources_success_count` : Nombre de sources récupérées avec succès
- `sources_failed_count` : Nombre de sources en échec (avec raisons)
- `items_raw_total` : Nombre total d'items récupérés
- `items_ingested_total` : Nombre d'items après filtrage et déduplication

**Répartition par source :**
- Items par source corporate (MedinCell, Camurus, DelSiTech, Nanexa, Peptron)
- Items par source presse (FierceBiotech, FiercePharma, Endpoints)
- Taux de succès par type de source (RSS vs scraping)

### 4.2 Métriques de normalisation/matching/scoring

**Volumes de traitement :**
- `items_input_count` : Items en entrée (depuis dernier run ingestion)
- `items_normalized_success` : Items normalisés avec succès par Bedrock
- `items_normalized_failed` : Items en échec de normalisation
- `items_matched_count` : Items matchés à au moins un domaine de veille
- `items_scored_count` : Items avec score final calculé
- `items_selected_count` : Items avec score ≥ seuil (12 pour lai_weekly_v3)

**Distribution des scores :**
- `score_min`, `score_max`, `score_avg`, `score_median`
- Histogramme par tranches : [0-5], [5-10], [10-15], [15-20], [20+]
- `high_score_items` : Items avec score > 20 (très pertinents)

**Matching par domaine :**
- Items matchés `tech_lai_ecosystem` vs `regulatory_lai`
- Taux de matching par type d'entité (company, molecule, technology, trademark)
- Efficacité `trademark_privileges` (boost 2.5x appliqué)

### 4.3 Métriques Bedrock

**Appels et performance :**
- `bedrock_calls_total` : Nombre total d'appels Bedrock
- `bedrock_calls_success` : Appels réussis (200 OK)
- `bedrock_calls_retry` : Appels avec retry (throttling, timeout)
- `bedrock_calls_failed` : Échecs définitifs après retry
- `bedrock_latency_avg` : Latence moyenne par appel (ms)
- `bedrock_latency_p95` : 95e percentile de latence

**Coûts estimés :**
- `bedrock_tokens_input_total` : Tokens en entrée (prompts + contexte)
- `bedrock_tokens_output_total` : Tokens en sortie (réponses JSON)
- `bedrock_cost_estimate_usd` : Estimation coût total du run ($)
- Coût par item normalisé ($/item)

**Méthode de collecte :**
- Logs structurés JSON dans CloudWatch
- Parsing des réponses Lambda pour extraction métriques
- Scripts d'analyse post-run : `scripts/analyze_run_metrics.py`

---

## Phase 5 – Audit qualité détaillé des résultats

### 5.1 Échantillonnage représentatif

**Sélection d'items pour audit manuel :**
- **10 items score élevé** (>15) : Vérifier pertinence justifiée
- **10 items score moyen** (8-15) : Vérifier cohérence scoring
- **5 items score faible** (<8) : Vérifier rejet justifié
- **5 items par source principale** : MedinCell, Camurus, FierceBiotech
- **5 items par type d'événement** : partnership, clinical, regulatory

**Critères d'évaluation par item :**

### 5.2 Grille d'audit qualité

**1. Cohérence entités extraites :**
- [ ] **Companies** : Entités présentes dans le texte source ?
- [ ] **Molecules** : Molécules LAI correctement identifiées ?
- [ ] **Technologies** : Mots-clés LAI pertinents détectés ?
- [ ] **Trademarks** : Marques commerciales LAI reconnues ?
- **Score** : 0-5 (5 = parfaite cohérence, 0 = entités fantômes)

**2. Pertinence classification événement :**
- [ ] **Event type** : Partnership/clinical/regulatory correct ?
- [ ] **Confidence** : Niveau de confiance justifié ?
- [ ] **Secondary types** : Classifications secondaires pertinentes ?
- **Score** : 0-5 (5 = classification parfaite, 0 = hors-sujet)

**3. Logique matching domaines :**
- [ ] **tech_lai_ecosystem** : Matching justifié par entités tech ?
- [ ] **regulatory_lai** : Matching justifié par contenu regulatory ?
- [ ] **Domain relevance score** : Score de pertinence cohérent ?
- **Score** : 0-5 (5 = matching logique, 0 = matching aberrant)

**4. Cohérence scoring final :**
- [ ] **Base score** : Reflète la pertinence perçue ?
- [ ] **Bonus application** : Pure player/trademark/partnership justifiés ?
- [ ] **Final score** : Résultat final cohérent avec l'intérêt LAI ?
- **Score** : 0-5 (5 = scoring parfait, 0 = scoring incohérent)

**5. Filtrage du bruit :**
- [ ] **Signal vs bruit** : Item pertinent pour veille LAI ?
- [ ] **Exclusions** : Items non-LAI correctement filtrés ?
- [ ] **False positives** : Taux d'items non-pertinents avec score élevé ?
- **Score** : 0-5 (5 = signal pur, 0 = bruit majoritaire)

### 5.3 Métriques qualité agrégées

**Taux de qualité globaux :**
- `coherence_entities_rate` : % items avec entités cohérentes (score ≥4)
- `classification_accuracy_rate` : % items avec classification correcte (score ≥4)
- `matching_logic_rate` : % items avec matching logique (score ≥4)
- `scoring_coherence_rate` : % items avec scoring cohérent (score ≥4)
- `signal_purity_rate` : % items pertinents pour LAI (score ≥4)

**Seuils d'acceptabilité :**
- **Excellent** : >90% sur tous les critères
- **Bon** : 80-90% sur tous les critères
- **Acceptable** : 70-80% sur tous les critères
- **Problématique** : <70% sur un critère majeur

---

## Phase 6 – Scalabilité, robustesse et conformité hygiène

### 6.1 Tests de scalabilité

**Simulation montée en charge :**
- [ ] **x2 sources** : Doubler le nombre de sources lai_weekly_v3 → impact performance ?
- [ ] **x5 items** : Simuler 5x plus d'items ingérés → timeout Lambda ?
- [ ] **x10 clients** : Simuler 10 clients actifs simultanés → throttling Bedrock ?

**Métriques de scalabilité :**
- Temps d'exécution vs nombre d'items (linéaire ?)
- Coût Bedrock vs volume (proportionnel ?)
- Taux d'erreur vs charge (stable <5% ?)

### 6.2 Tests de robustesse

**Gestion d'erreurs réseau :**
- [ ] **Timeout Bedrock** : Comportement si appel >30s ?
- [ ] **Rate limiting** : Retry automatique si 429 ?
- [ ] **Bedrock indisponible** : Fallback gracieux ?
- [ ] **S3 inaccessible** : Gestion erreurs lecture/écriture ?

**Cas limites données :**
- [ ] **Aucun item ingéré** : Comportement si dernier run vide ?
- [ ] **Items corrompus** : Gestion JSON malformé ?
- [ ] **Config manquante** : Comportement si client_config absent ?
- [ ] **Scopes vides** : Gestion canonical incomplet ?

### 6.3 Conformité règles d'hygiène V4

**Architecture et code :**
- [ ] **Séparation responsabilités** : Handlers vs vectora_core respectée ?
- [ ] **Généricité** : Aucun hardcoding client spécifique ?
- [ ] **Imports relatifs** : Structure src_v2 respectée ?
- [ ] **Taille packages** : Handlers <5MB, layers <50MB ?

**Environnement AWS :**
- [ ] **Région cohérente** : Toutes ressources en eu-west-3 ?
- [ ] **Conventions nommage** : Buckets/Lambdas conformes ?
- [ ] **Profil CLI** : Utilisation exclusive rag-lai-prod ?
- [ ] **Bedrock région** : us-east-1 par défaut respecté ?

**Configuration et canonical :**
- [ ] **Pilotage config** : Logique métier dans YAML, pas code ?
- [ ] **Scopes centralisés** : Canonical utilisé, pas duplication ?
- [ ] **Variables env** : Standardisation respectée ?

---

## Phase 7 – Synthèse & recommandations

### 7.1 Critères de verdict global

**✅ PROPRE / FONCTIONNEL / PUISSANT si :**
- Workflow end-to-end fonctionne sans intervention manuelle
- Conformité règles d'hygiène V4 > 95%
- Qualité résultats > 80% sur tous critères
- Performance acceptable (<5min, <$1 par run)
- Robustesse démontrée (gestion erreurs, retry)

**⚠️ FONCTIONNEL AVEC RÉSERVES si :**
- Workflow fonctionne mais nécessite ajustements mineurs
- Conformité règles d'hygiène V4 > 85%
- Qualité résultats > 70% sur critères majeurs
- Performance acceptable avec optimisations possibles

**❌ PROBLÉMATIQUE si :**
- Échecs fonctionnels bloquants
- Violations règles d'hygiène V4 critiques
- Qualité résultats <70% sur critères majeurs
- Performance inacceptable (timeout, coût excessif)

### 7.2 Structure du rapport de synthèse

**Points forts identifiés :**
- Architecture respectée et maintenable
- Généricité et pilotage par configuration
- Performance et coûts maîtrisés
- Qualité des résultats LAI

**Faiblesses détectées :**
- Problèmes de qualité (bruit, faux positifs)
- Problèmes de performance (latence, coût)
- Problèmes d'architecture (couplage, complexité)
- Problèmes de robustesse (gestion erreurs)

**Recommandations de tuning :**

*Sur la configuration :*
- Ajustements scopes LAI (ajout/suppression entités)
- Modification seuils scoring (min_score, bonus)
- Optimisation règles matching (trademark_privileges)
- Révision structure sections newsletter

*Sur le prompting Bedrock :*
- Amélioration prompts normalisation (précision entités)
- Optimisation longueur prompts (coût tokens)
- Ajustement exemples canoniques (qualité extraction)

*Sur le code (sans modification immédiate) :*
- Optimisations performance (parallélisation, cache)
- Amélioration gestion erreurs (retry, fallback)
- Enrichissement logging (métriques, debug)
- Refactoring modules si complexité excessive

### 7.3 Avis global industrialisation

**Question clé :** Cette approche est-elle saine pour industrialiser Vectora Inbox ?

**Évaluation sur :**
- **Maintenabilité** : Code simple, architecture claire ?
- **Évolutivité** : Ajout nouveaux clients facile ?
- **Fiabilité** : Robustesse en production ?
- **Coût** : Modèle économique viable ?
- **Qualité** : Résultats exploitables par analystes ?

**Recommandation finale :**
- ✅ **INDUSTRIALISER** : Approche validée, déploiement recommandé
- ⚠️ **INDUSTRIALISER AVEC AJUSTEMENTS** : Corrections mineures nécessaires
- ❌ **REVOIR APPROCHE** : Problèmes fondamentaux à résoudre

---

## Résumé exécutif du plan

Ce plan de test couvre exhaustivement le workflow MVP lai_weekly_v3 avec une approche progressive :

1. **Audit statique** pour valider la conformité architecturale
2. **Tests locaux** pour valider la logique métier
3. **Tests AWS réels** pour valider l'intégration end-to-end
4. **Métriques détaillées** pour évaluer performance et coûts
5. **Audit qualité** pour valider la pertinence des résultats
6. **Tests robustesse** pour valider la fiabilité
7. **Synthèse** pour recommandations d'amélioration

**Prochaine étape :** Exécution de ce plan et production du rapport de diagnostic dans `docs/diagnostics/workflow_mvp_lai_weekly_v3_diagnostic.md`.