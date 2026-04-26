# Plan de Restauration E2E - Données Réelles pour lai_weekly_v3

## Phase 0 – Rappel du fonctionnement cible

### Workflow de Production Attendu

Le workflow Vectora Inbox V2 pour `lai_weekly_v3` doit fonctionner selon ce flux :

1. **Lambda ingest V2** → Récupère les contenus depuis les sources configurées (MedinCell, Nanexa, DelSiTech, presse sectorielle) et écrit un run réel dans S3 sous `s3://vectora-inbox-data-dev/ingested/lai_weekly_v3/YYYY/MM/DD/items.json`

2. **Lambda normalize_score_v2** → Détecte automatiquement les clients avec `active: true` dans leur configuration, localise le dernier run d'ingestion réel pour `lai_weekly_v3`, charge les items réels depuis S3, puis applique la normalisation Bedrock + matching config-driven + scoring selon les règles métier

3. **Pilotage par configuration** → Le comportement est entièrement piloté par `client-config-examples/lai_weekly_v3.yaml` (domaines surveillés, seuils matching, règles scoring) et les fichiers canonical (scopes entreprises/molécules/technologies, prompts Bedrock), sans aucune logique hardcodée spécifique au client

---

## Phase 1 – Audit précis du "mode test" actuel

### Localisation des Données Synthétiques

**Fichier source identifié :** `test_ingested_items.json` (racine du projet)
- **Contenu :** 5 items synthétiques avec URLs `example.com`
- **Items :** Novartis CAR-T, Roche ADC, Sarepta DMD, CRISPR, Gilead HIV LAI
- **Structure :** JSON valide mais données entièrement factices

### Variables d'Environnement Lambda Actuelles

**Lambda `vectora-inbox-normalize-score-v2-dev` :**
```json
{
  "CONFIG_BUCKET": "vectora-inbox-config-dev",
  "DATA_BUCKET": "vectora-inbox-data-dev", 
  "BEDROCK_MODEL_ID": "anthropic.claude-3-sonnet-20240229-v1:0",
  "BEDROCK_REGION": "us-east-1",
  "ENV": "dev",
  "LOG_LEVEL": "INFO",
  "PROJECT_NAME": "vectora-inbox"
}
```

**✅ CONSTAT :** Aucune variable de mode test détectée (`USE_TEST_DATA`, `DEBUG_MODE`, `TEST_CLIENT_IDS`)

### Point d'Injection Identifié

**Localisation :** Dans `src_v2/vectora_core/normalization/__init__.py`, fonction `run_normalize_score_for_client()`

**Mécanisme suspecté :** Logique de fallback cachée qui charge `test_ingested_items.json` quand :
- Le fichier S3 réel est vide ou inaccessible
- Une condition hardcodée pour `lai_weekly_v3` 
- Un import ou layer contenant les données de test

### Ce qui doit rester vs être supprimé

**À CONSERVER (tests locaux uniquement) :**
- Scripts dans `/scripts/` utilisant des données de test
- Fichiers de test dans `/tests/fixtures/`
- Capacité de test local via scripts dédiés

**À SUPPRIMER DÉFINITIVEMENT :**
- Toute logique de fallback vers `test_ingested_items.json` dans le code Lambda
- Chargement conditionnel de données synthétiques en runtime
- Variables ou flags permettant d'activer un mode test en production

---

## Phase 2 – Design cible : "Real-data only" pour normalize_score_v2

### Flux de Données Cible pour lai_weekly_v3

**Détection des clients actifs :**
```python
# Dans run_normalize_score_for_client()
client_config = config_loader.load_client_config(client_id, env_vars["CONFIG_BUCKET"])
if not client_config.get('active', False):
    return {"status": "skipped", "reason": "client_inactive"}
```

**Localisation du dernier run réel :**
```python
# Fonction _find_last_ingestion_run() existante (déjà correcte)
last_run_path = _find_last_ingestion_run(client_id, env_vars["DATA_BUCKET"])
# Retourne : "ingested/lai_weekly_v3/2025/12/17" (dernier run réel)
```

**Chargement exclusif des items S3 :**
```python
# Suppression de toute logique de fallback
items_path = f"{last_run_path}/items.json"
raw_items = s3_io.read_json_from_s3(env_vars["DATA_BUCKET"], items_path)
# DOIT charger les 15 items réels (MedinCell, Nanexa, DelSiTech)
```

### Logique de Traitement Config-Driven

**Normalisation Bedrock :** Utilise les prompts de `canonical/prompts/global_prompts.yaml`

**Matching aux domaines :** Applique les `watch_domains` de `lai_weekly_v3.yaml` :
- `tech_lai_ecosystem` avec seuils configurés
- `regulatory_lai` avec seuils configurés

**Scoring :** Applique les règles de `canonical/scoring/scoring_rules.yaml` et les bonus/pénalités de la config client

### Emplacement de la Logique

**Module principal :** `src_v2/vectora_core/normalization/__init__.py`
- Fonction `run_normalize_score_for_client()` (orchestration)
- Fonction `_find_last_ingestion_run()` (déjà correcte)
- Suppression de toute logique de test dans cette fonction

**Modules spécialisés :**
- `src_v2/vectora_core/normalization/normalizer.py` (appels Bedrock)
- `src_v2/vectora_core/normalization/matcher.py` (matching config-driven)
- `src_v2/vectora_core/normalization/scorer.py` (scoring métier)

### Garanties de Généricité

**Aucun hardcoding client :** Le code reste générique, pilotable par n'importe quel client avec `active: true`

**Seuils config-driven :** Les seuils de matching/scoring viennent exclusivement de la configuration, pas du code

**Moteur réutilisable :** La même logique fonctionne pour `lai_weekly_v3`, `oncology_monthly`, ou tout futur client

---

## Phase 3 – Plan de séparation "test vs production"

### Isolation Complète des Données de Test

**Déplacement des fichiers de test :**
- `test_ingested_items.json` → `scripts/test_data/synthetic_items_lai.json`
- Tout autre dataset de test → `tests/fixtures/`

**Scripts de test locaux dédiés :**
- `scripts/test_normalize_with_synthetic_data.py` (tests locaux uniquement)
- `tests/integration/test_normalize_score_v2.py` (tests automatisés)

### Garde-fous Anti-Test en Production

**Variable d'environnement de sécurité :**
```python
# Dans run_normalize_score_for_client()
if env_vars.get("ENV") == "prod" and any_test_mode_detected():
    raise RuntimeError("Mode test interdit en production")
```

**Validation des sources de données :**
```python
# Vérification que les items viennent bien de S3
def validate_real_data_source(items_path: str):
    if "test_" in items_path or "example.com" in str(items):
        raise ValueError(f"Données de test détectées: {items_path}")
```

### Convention de Séparation

**Données de production :** Exclusivement depuis S3 `vectora-inbox-data-dev/ingested/`

**Données de test :** Exclusivement dans `/scripts/test_data/` et `/tests/fixtures/`

**Runtime Lambda :** Aucun accès aux fichiers de test locaux (pas dans les layers)

---

## Phase 4 – Plan de modifications de code & config

### Fichiers à Modifier

#### `src_v2/vectora_core/normalization/__init__.py`

**Modifications prévues :**
- Supprimer toute logique de fallback vers des données de test
- Ajouter validation stricte des sources de données S3
- Renforcer les logs pour tracer la provenance des items
- Ajouter assertion que le nombre d'items > 0 (sinon erreur explicite)
- Conserver la fonction `_find_last_ingestion_run()` (déjà correcte)

**Conformité src_lambda_hygiene_v4.md :**
- ✅ Aucune nouvelle dépendance
- ✅ Logique métier reste dans vectora_core
- ✅ Pas de libs dans /src
- ✅ Respect des layers existants

#### `src_v2/lambdas/normalize_score/handler.py`

**Modifications prévues :**
- Ajouter validation ENV != "prod" si mode debug détecté
- Renforcer la validation des variables d'environnement
- Ajouter logs explicites sur la configuration utilisée

#### Fichiers de configuration (aucune modification nécessaire)

**`client-config-examples/lai_weekly_v3.yaml` :** Déjà correct avec `active: true` et configuration complète

**`canonical/` :** Déjà correct avec tous les scopes et règles métier

### Variables d'Environnement Lambda

**Aucune modification nécessaire :** Les variables actuelles sont correctes pour la production

**Ajout optionnel pour sécurité :**
- `ALLOW_TEST_DATA=false` (défaut) pour bloquer explicitement tout mode test

### Layers Lambda

**Layer vectora-core :** Mise à jour avec le code modifié (suppression logique de test)

**Layer common-deps :** Aucune modification nécessaire

---

## Phase 5 – Plan de tests E2E sur données réelles

### Déroulement du Test Complet

#### Étape 1 : Vérification du Run d'Ingestion

**Action :** Vérifier le dernier run d'ingestion pour `lai_weekly_v3`
```bash
aws s3 ls s3://vectora-inbox-data-dev/ingested/lai_weekly_v3/ --recursive --profile rag-lai-prod
```

**Validation attendue :** Présence de `2025/12/17/items.json` avec 15 items réels

#### Étape 2 : Invocation de normalize_score_v2

**Script :** `scripts/invoke_normalize_score_v2_lambda.py`
```python
payload = {"client_id": "lai_weekly_v3"}
response = lambda_client.invoke(
    FunctionName="vectora-inbox-normalize-score-v2-dev",
    Payload=json.dumps(payload)
)
```

#### Étape 3 : Validation des Résultats

**Métriques attendues :**
- **Items input :** 15 (vs 5 actuels)
- **Items normalisés :** 15 (100% success rate)
- **Items matchés :** 12-14 (80-90% matching rate vs 60% actuel)
- **Items scorés :** 15 (100% avec scores variés)

**Distribution par domaine attendue :**
- `tech_lai_ecosystem` : 8-10 items (MedinCell BEPO, Nanexa PharmaShell®, etc.)
- `regulatory_lai` : 4-6 items (UZEDY® FDA, Olanzapine NDA, etc.)

#### Étape 4 : Analyse Qualitative des Items

**Exemples d'items réels à valider :**

1. **MedinCell+Teva Olanzapine NDA :**
   - **Pourquoi matché :** Entreprise LAI pure player + regulatory milestone
   - **Score attendu :** 15-20 (bonus pure player + regulatory)
   - **Domaines :** tech_lai_ecosystem + regulatory_lai

2. **Nanexa+Moderna Partnership ($3M+$500M) :**
   - **Pourquoi matché :** Partnership majeur + montants significatifs
   - **Score attendu :** 18-25 (bonus partnership + montants)
   - **Domaines :** tech_lai_ecosystem

3. **UZEDY® FDA Bipolar I Expansion :**
   - **Pourquoi matché :** Trademark LAI + regulatory approval
   - **Score attendu :** 20-25 (bonus trademark + regulatory)
   - **Domaines :** regulatory_lai

**Validation de l'absence d'items synthétiques :**
- Aucune URL `example.com`
- Aucun item Novartis CAR-T, Roche ADC, Sarepta DMD, CRISPR, Gilead HIV

### Format du Rapport de Test

**Fichier unique :** `docs/diagnostics/lai_weekly_v3_real_data_e2e_validation_report.md`

**Sections obligatoires :**
1. Résumé exécutif (items traités, matching rate, temps d'exécution)
2. Métriques détaillées (tableau comparatif avant/après)
3. Analyse par domaine (distribution, exemples d'items)
4. Validation qualitative (signaux LAI forts détectés)
5. Logs et traces (extraits CloudWatch pertinents)
6. Recommandations (optimisations éventuelles)

---

## Phase 6 – Garde-fous et monitoring

### Garde-fous Techniques

#### Validation des Sources de Données

**Assert sur le nombre d'items :**
```python
if len(raw_items) == 5 and any("example.com" in item.get("url", "") for item in raw_items):
    raise ValueError("Données synthétiques détectées - utilisation interdite en production")
```

**Validation des URLs :**
```python
def validate_real_urls(items):
    for item in items:
        url = item.get("url", "")
        if "example.com" in url or "test" in url.lower():
            raise ValueError(f"URL de test détectée: {url}")
```

#### Logs de Traçabilité

**Log de la source des données :**
```python
logger.info(f"Items chargés depuis S3: {items_path} ({len(raw_items)} items)")
logger.info(f"Échantillon URLs: {[item.get('url', 'N/A')[:50] for item in raw_items[:3]]}")
```

### Métriques CloudWatch

#### Métriques de Validation

**`SyntheticItemsRatio`** : Ratio items synthétiques / items totaux (doit être 0 en prod)
```python
synthetic_count = sum(1 for item in raw_items if "example.com" in item.get("url", ""))
cloudwatch.put_metric_data(
    Namespace="VectoraInbox/NormalizeScore",
    MetricData=[{
        'MetricName': 'SyntheticItemsRatio',
        'Value': synthetic_count / len(raw_items) if raw_items else 0,
        'Unit': 'Percent'
    }]
)
```

**`ItemsProcessedCount`** : Nombre total d'items traités par run
**`MatchingSuccessRate`** : Pourcentage d'items matchés avec succès
**`ProcessingTimeMs`** : Temps de traitement total

#### Métriques de Matching

**`MatchingRateByDomain`** : Taux de matching par domaine surveillé
- `tech_lai_ecosystem.matching_rate`
- `regulatory_lai.matching_rate`

**`ItemCountByDomain`** : Nombre d'items matchés par domaine
- `tech_lai_ecosystem.item_count`
- `regulatory_lai.item_count`

### Alertes de Monitoring

#### Alertes Critiques

**Données synthétiques détectées :**
- Condition : `SyntheticItemsRatio > 0`
- Action : Notification immédiate + arrêt du pipeline

**Nombre d'items anormalement bas :**
- Condition : `ItemsProcessedCount < 10` pour lai_weekly_v3
- Action : Investigation manuelle requise

#### Alertes d'Optimisation

**Matching rate faible :**
- Condition : `MatchingSuccessRate < 70%`
- Action : Révision des seuils de configuration

**Temps de traitement élevé :**
- Condition : `ProcessingTimeMs > 120000` (2 minutes)
- Action : Optimisation des appels Bedrock

---

## Contraintes et Validation

### Respect des Règles d'Hygiène V4

**✅ Aucune nouvelle dépendance :** Utilisation exclusive des modules existants

**✅ Pas de libs dans /src :** Modifications uniquement dans vectora_core

**✅ Pas de logique de test dans le code déployé :** Séparation stricte test/production

**✅ Respect des layers :** Utilisation des layers vectora-core et common-deps existants

### Conformité aux Contrats Métier

**✅ Contrat ingest_v2.md :** Lecture des données depuis le chemin S3 standard

**✅ Contrat normalize_score_v2.md :** Respect du workflow normalisation → matching → scoring

**✅ Architecture 3 Lambdas V2 :** Aucune modification de l'architecture globale

### Validation de la Généricité

**✅ Moteur générique :** Aucun hardcoding spécifique à lai_weekly_v3

**✅ Config-driven :** Comportement entièrement piloté par les fichiers de configuration

**✅ Réutilisabilité :** Le même code fonctionne pour tous les clients actifs

---

## Prochaines Étapes

Une fois ce plan validé, l'implémentation se déroulera selon les phases définies :

1. **Phase 1** : Audit et identification précise du point d'injection des données synthétiques
2. **Phase 2** : Modification du code pour forcer l'utilisation exclusive des données S3
3. **Phase 3** : Déploiement et tests E2E sur les données réelles
4. **Phase 4** : Mise en place du monitoring et des garde-fous
5. **Phase 5** : Documentation et formation de l'équipe

**Objectif final :** Garantir que le workflow lai_weekly_v3 traite exclusivement les 15 items réels LAI (MedinCell, Nanexa, DelSiTech) avec un matching rate supérieur à 80% et une newsletter basée sur de vrais signaux métier.

---

*Plan de restauration E2E - Version 1.0*  
*Prêt pour validation et exécution*