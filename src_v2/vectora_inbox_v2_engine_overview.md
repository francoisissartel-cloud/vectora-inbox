# Vectora Inbox V2 - Vue d'Ensemble du Moteur

**Date :** 18 décembre 2025  
**Version :** 2.0  
**Scope :** Documentation complète du moteur Vectora Inbox V2 stabilisé  
**Client de référence :** lai_weekly_v3  

---

## Vue d'Ensemble du Pipeline V2

### Architecture 3 Lambdas

Le moteur Vectora Inbox V2 implémente une architecture à **3 Lambdas séparées** avec responsabilités distinctes :

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   INGEST V2     │───▶│ NORMALIZE/SCORE │───▶│  NEWSLETTER V2  │
│                 │    │      V2         │    │                 │
│ Sources externes│    │ Bedrock + Rules │    │ Editorial + S3  │
│ ──────▶ S3 raw/ │    │ ──────▶ S3 cur/ │    │ ──────▶ S3 out/ │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**Flux de données :**
1. **Ingest V2** : Sources externes → S3 `ingested/{client_id}/{YYYY}/{MM}/{DD}/items.json`
2. **Normalize/Score V2** : S3 `ingested/` → Bedrock → S3 `curated/{client_id}/{YYYY}/{MM}/{DD}/items.json`
3. **Newsletter V2** : S3 `curated/` → Editorial → S3 `newsletters/{client_id}/{YYYY}/{MM}/{DD}/newsletter.md`

### Buckets S3 Utilisés

**Configuration et données canoniques :**
- **`vectora-inbox-config-dev`** : Configurations client + canonical (sources, scopes, prompts)

**Données de traitement :**
- **`vectora-inbox-data-dev`** : 
  - `ingested/` : Items bruts parsés par ingest V2
  - `curated/` : Items normalisés/scorés par normalize_score V2
  - `raw/` : Contenus bruts (debug optionnel)

**Sorties finales :**
- **`vectora-inbox-newsletters-dev`** : Newsletters finales générées

### Variables d'Environnement Importantes

**Communes à toutes les Lambdas :**
```bash
ENV=dev
PROJECT_NAME=vectora-inbox
CONFIG_BUCKET=vectora-inbox-config-dev
DATA_BUCKET=vectora-inbox-data-dev
LOG_LEVEL=INFO
```

**Spécifiques à normalize_score V2 :**
```bash
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_REGION=us-east-1
MAX_BEDROCK_WORKERS=1
```

**Spécifiques à newsletter V2 :**
```bash
NEWSLETTERS_BUCKET=vectora-inbox-newsletters-dev
BEDROCK_REGION_NEWSLETTER=us-east-1
```

---

## Flux de Données Réel pour lai_weekly_v3

### Ingestion (Lambda ingest-v2)

**Sources configurées (lai_weekly_v3.yaml) :**
```yaml
source_bouquets_enabled:
  - "lai_corporate_mvp"    # 5 sources corporate LAI
  - "lai_press_mvp"        # 3 sources presse sectorielle
```

**Résolution en sources individuelles :**
- **Corporate LAI (5 sources)** : MedinCell, Camurus, DelSiTech, Nanexa, Peptron
- **Presse sectorielle (3 sources)** : FierceBiotech, FiercePharma, Endpoints News

**Volume typique ingéré :**
- **15 items** pour une fenêtre de 30 jours (lai_weekly_v3)
- **Format de stockage :** `s3://vectora-inbox-data-dev/ingested/lai_weekly_v3/2025/12/17/items.json`

**Structure d'un item ingéré :**
```json
{
  "item_id": "press_corporate__medincell_20250115_001",
  "source_key": "press_corporate__medincell",
  "title": "MedinCell Announces Partnership with Teva for BEPO Technology",
  "content": "MedinCell (Euronext: MEDCL) today announced...",
  "url": "https://www.medincell.com/news/partnership-teva-bepo/",
  "published_at": "2025-01-15",
  "ingested_at": "2025-01-15T10:30:00Z",
  "language": "en",
  "content_hash": "sha256:abc123...",
  "metadata": {
    "author": "MedinCell Press Team",
    "word_count": 450
  }
}
```

### Normalisation/Scoring (Lambda normalize-score-v2)

**Détection du dernier run :**
- Scan automatique de `s3://vectora-inbox-data-dev/ingested/lai_weekly_v3/`
- Sélection du run le plus récent avec `items.json` valide
- **Exemple :** `ingested/lai_weekly_v3/2025/12/17/` (15 items)

**Traitement Bedrock :**
- **Normalisation** : 15 appels Bedrock (1 par item)
- **Matching** : 15 appels Bedrock supplémentaires (évaluation domaines)
- **Modèle utilisé** : `anthropic.claude-3-sonnet-20240229-v1:0`
- **Région** : `us-east-1`
- **Temps total** : ~163 secondes (10.9s par item)

**Entités extraites (exemple réel) :**
- **Companies** : 15 détectées (MedinCell, Teva, Nanexa, Moderna, etc.)
- **Molecules** : 5 détectées (buprenorphine, naloxone, etc.)
- **Technologies** : 9 détectées (BEPO, PharmaShell®, long-acting injection, etc.)
- **Trademarks** : 7 détectées (UZEDY®, Suboxone®, etc.)

**Matching aux domaines :**
- **tech_lai_ecosystem** : 8-10 items matchés
- **regulatory_lai** : 3-5 items matchés
- **Overlap** : 2-3 items matchés aux 2 domaines

**Scoring et stockage :**
- **Distribution des scores** : 2.2 à 13.8 (moyenne 9.7)
- **Stockage final** : `s3://vectora-inbox-data-dev/curated/lai_weekly_v3/2025/12/17/items.json`

### Newsletter (Lambda newsletter-v2) - À Implémenter

**Lecture des items curés :**
- Source : `s3://vectora-inbox-data-dev/curated/lai_weekly_v3/2025/12/17/items.json`
- Tri par score décroissant
- Sélection selon `newsletter_layout` (lai_weekly_v3.yaml)

**Génération éditoriale :**
- **Sections configurées** : Top Signals, Partnerships, Regulatory, Clinical
- **Appels Bedrock** : Génération contenu éditorial
- **Format de sortie** : Markdown

**Stockage final :**
- Destination : `s3://vectora-inbox-newsletters-dev/lai_weekly_v3/2025/12/17/newsletter.md`

---

## Rôle de client_config + canonical

### Configuration Client (lai_weekly_v3.yaml)

**Contrôle de l'ingestion :**
```yaml
source_config:
  source_bouquets_enabled:
    - "lai_corporate_mvp"
    - "lai_press_mvp"
  
pipeline:
  default_period_days: 30  # Fenêtre temporelle étendue pour LAI
```

**Contrôle de la normalisation :**
```yaml
watch_domains:
  - id: "tech_lai_ecosystem"
    technology_scope: "lai_keywords"
    company_scope: "lai_companies_global"
    molecule_scope: "lai_molecules_global"
    trademark_scope: "lai_trademarks_global"
```

**Contrôle du matching :**
```yaml
matching_config:
  min_domain_score: 0.25              # Seuil global
  domain_type_thresholds:
    technology: 0.30
    regulatory: 0.20
  enable_fallback_mode: true          # Mode fallback pour pure players
  fallback_min_score: 0.15
```

**Contrôle du scoring :**
```yaml
scoring_config:
  client_specific_bonuses:
    pure_player_companies:
      scope: "lai_companies_mvp_core"
      bonus: 5.0                      # Bonus fort pour MedinCell, Camurus, etc.
    trademark_mentions:
      scope: "lai_trademarks_global"
      bonus: 4.0                      # Bonus pour UZEDY®, PharmaShell®, etc.
```

**Contrôle de la newsletter :**
```yaml
newsletter_layout:
  sections:
    - id: "top_signals"
      title: "Top Signals – LAI Ecosystem"
      max_items: 5
      sort_by: "score_desc"
    - id: "partnerships_deals"
      title: "Partnerships & Deals"
      max_items: 5
      filter_event_types: ["partnership", "corporate_move"]
```

### Fichiers Canonical Utilisés

**Sources et bouquets :**
- **`canonical/sources/source_catalog.yaml`** : 180+ sources avec bouquets prédéfinis
- **`canonical/ingestion/ingestion_profiles.yaml`** : Profils de récupération (timeout, retry)

**Scopes métier :**
- **`canonical/scopes/company_scopes.yaml`** : 
  - `lai_companies_global` : 180+ entreprises LAI
  - `lai_companies_mvp_core` : 5 pure players (MedinCell, Camurus, DelSiTech, Nanexa, Peptron)
- **`canonical/scopes/molecule_scopes.yaml`** :
  - `lai_molecules_global` : 90+ molécules LAI actives
- **`canonical/scopes/technology_scopes.yaml`** :
  - `lai_keywords` : 80+ mots-clés technologiques LAI
- **`canonical/scopes/trademark_scopes.yaml`** :
  - `lai_trademarks_global` : 70+ marques commerciales LAI

**Règles métier :**
- **`canonical/scoring/scoring_rules.yaml`** : Poids par type d'événement, facteurs de recency
- **`canonical/matching/domain_matching_rules.yaml`** : Règles de matching par domaine

**Prompts Bedrock :**
- **`canonical/prompts/global_prompts.yaml`** : Templates pour normalisation et matching

### Exemples de Pilotage par Configuration

**Exemple 1 : Modifier les seuils de matching**
```yaml
# Dans lai_weekly_v3.yaml - Aucun changement de code requis
matching_config:
  min_domain_score: 0.20  # Baissé de 0.25 → 0.20 pour plus de rappel
```

**Exemple 2 : Ajouter un bonus pour une nouvelle technologie**
```yaml
# Dans lai_weekly_v3.yaml
scoring_config:
  client_specific_bonuses:
    new_technology:
      scope: "lai_delivery_systems"  # Référence canonical
      bonus: 3.0
```

**Exemple 3 : Modifier la structure de newsletter**
```yaml
# Dans lai_weekly_v3.yaml
newsletter_layout:
  sections:
    - id: "breakthrough_signals"     # Nouvelle section
      title: "Breakthrough Technologies"
      max_items: 3
      min_score: 15                  # Seuil élevé
```

---

## Appels Bedrock

### Vue d'Ensemble des Appels

**Modèle par défaut :** `anthropic.claude-3-sonnet-20240229-v1:0`  
**Région par défaut :** `us-east-1`  
**Configuration hybride supportée :** Variables `BEDROCK_REGION_NORMALIZATION` et `BEDROCK_REGION_NEWSLETTER`

### Appels dans Normalize/Score V2

**1. Normalisation des items (1 appel par item)**
- **Module :** `src_v2/vectora_core/normalization/normalizer.py`
- **Fonction :** `normalize_items_batch()`
- **Prompt :** `canonical/prompts/global_prompts.yaml::normalization.lai_default`
- **Objectif :** Extraction d'entités, classification d'événements, résumé
- **Configuration :**
  ```yaml
  max_tokens: 1000
  temperature: 0.0
  anthropic_version: "bedrock-2023-05-31"
  ```

**Exemple d'appel normalisation :**
```
INPUT: "MedinCell Announces Partnership with Teva for BEPO Technology..."

OUTPUT: {
  "summary": "MedinCell partners with Teva to develop long-acting injectable formulations using BEPO technology platform...",
  "event_type": "partnership",
  "companies_detected": ["MedinCell", "Teva Pharmaceutical"],
  "molecules_detected": ["buprenorphine", "naloxone"],
  "technologies_detected": ["BEPO", "long-acting injection", "subcutaneous delivery"],
  "trademarks_detected": ["Suboxone"],
  "lai_relevance_score": 9
}
```

**2. Matching aux domaines (1 appel par item)**
- **Module :** `src_v2/vectora_core/normalization/bedrock_matcher.py`
- **Fonction :** `match_watch_domains_with_bedrock()`
- **Prompt :** `canonical/prompts/global_prompts.yaml::matching.matching_watch_domains_v2`
- **Objectif :** Évaluation de la pertinence par domaine de veille
- **Configuration :**
  ```yaml
  max_tokens: 1500
  temperature: 0.1
  anthropic_version: "bedrock-2023-05-31"
  ```

**Exemple d'appel matching :**
```
INPUT: Item normalisé + watch_domains (tech_lai_ecosystem, regulatory_lai)

OUTPUT: {
  "domain_evaluations": [
    {
      "domain_id": "tech_lai_ecosystem",
      "is_relevant": true,
      "relevance_score": 0.85,
      "confidence": "high",
      "reasoning": "Strong LAI technology signals with BEPO platform and partnership context",
      "matched_entities": {
        "companies": ["MedinCell"],
        "technologies": ["BEPO", "long-acting injection"],
        "trademarks": ["Suboxone"]
      }
    }
  ]
}
```

### Appels dans Newsletter V2 (À Implémenter)

**3. Génération éditoriale (1 appel par section)**
- **Module :** `src_v2/vectora_core/newsletter/editorial.py` (à implémenter)
- **Prompt :** `canonical/prompts/global_prompts.yaml::newsletter.editorial_generation`
- **Objectif :** Génération de contenu éditorial pour chaque section
- **Configuration :**
  ```yaml
  max_tokens: 4000
  temperature: 0.2
  anthropic_version: "bedrock-2023-05-31"
  ```

### Orchestration des Appels

**Contrôle de la parallélisation :**
```python
# Dans normalize_score V2
max_workers = int(env_vars.get("MAX_BEDROCK_WORKERS", "1"))  # 1 par défaut (évite throttling)

# Appels séquentiels pour éviter les limites de débit
normalized_items = normalizer.normalize_items_batch(
    raw_items, 
    canonical_scopes, 
    canonical_prompts,
    bedrock_model,
    bedrock_region,
    max_workers=max_workers
)
```

**Gestion des erreurs et retry :**
- Retry automatique sur erreurs temporaires (throttling, timeout)
- Fallback sur erreurs persistantes (item marqué comme non-normalisé)
- Logs détaillés pour debugging

### Coûts et Performance

**Métriques observées (lai_weekly_v3) :**
- **30 appels Bedrock** pour 15 items (normalisation + matching)
- **Temps total** : 163 secondes (5.4s par appel en moyenne)
- **Tokens consommés** : ~1000 tokens par appel (estimation)
- **Coût estimé** : ~$0.15 par run (15 items)

---

## Surface de Réglage (Tuning) pour l'Utilisateur

### Paramètres Métier Ajustables

**1. Seuils de Matching (sans redéploiement)**
```yaml
# Dans lai_weekly_v3.yaml
matching_config:
  min_domain_score: 0.25              # Seuil global
  domain_type_thresholds:
    technology: 0.30                  # Plus strict pour tech
    regulatory: 0.20                  # Plus permissif pour regulatory
  enable_fallback_mode: true          # Mode fallback pour pure players
  fallback_min_score: 0.15            # Seuil très bas pour récupérer les cas limites
```

**2. Bonus de Scoring (sans redéploiement)**
```yaml
# Dans lai_weekly_v3.yaml
scoring_config:
  client_specific_bonuses:
    pure_player_companies:
      bonus: 5.0                      # Augmenter pour privilégier les pure players
    trademark_mentions:
      bonus: 4.0                      # Augmenter pour privilégier les marques
    key_molecules:
      bonus: 2.5                      # Ajuster selon l'importance des molécules
```

**3. Structure de Newsletter (sans redéploiement)**
```yaml
# Dans lai_weekly_v3.yaml
newsletter_layout:
  sections:
    - id: "top_signals"
      max_items: 5                    # Augmenter/diminuer le nombre d'items
      min_score: 12                   # Ajuster le seuil de qualité
    - id: "partnerships_deals"
      max_items: 5
      filter_event_types:             # Ajouter/retirer des types d'événements
        - "partnership"
        - "corporate_move"
        - "licensing_deal"            # Nouveau type
```

**4. Fenêtre Temporelle (sans redéploiement)**
```yaml
# Dans lai_weekly_v3.yaml
pipeline:
  default_period_days: 30             # Ajuster selon la fréquence souhaitée
```

### Scopes Canonical Ajustables

**1. Entreprises surveillées**
```yaml
# Dans canonical/scopes/company_scopes.yaml
lai_companies_custom:
  - "MedinCell"
  - "Camurus"
  - "Nouvelle Entreprise LAI"         # Ajouter de nouvelles entreprises
```

**2. Technologies surveillées**
```yaml
# Dans canonical/scopes/technology_scopes.yaml
lai_keywords_extended:
  - "long-acting injection"
  - "depot injection"
  - "nouvelle technologie LAI"        # Ajouter de nouveaux mots-clés
```

**3. Molécules surveillées**
```yaml
# Dans canonical/scopes/molecule_scopes.yaml
lai_molecules_priority:
  - "buprenorphine"
  - "naloxone"
  - "nouvelle molécule"               # Ajouter de nouvelles molécules
```

### Exemple Concret : Ajuster les Signaux Regulatory

**Problème :** "Je veux plus de signaux regulatory dans ma newsletter"

**Solution 1 : Baisser le seuil regulatory**
```yaml
# Dans lai_weekly_v3.yaml
matching_config:
  domain_type_thresholds:
    regulatory: 0.15                  # Baissé de 0.20 → 0.15
```

**Solution 2 : Augmenter le bonus regulatory**
```yaml
# Dans lai_weekly_v3.yaml
scoring_config:
  event_type_weight_overrides:
    regulatory: 8                     # Augmenté de 7 → 8
```

**Solution 3 : Ajouter une section dédiée**
```yaml
# Dans lai_weekly_v3.yaml
newsletter_layout:
  sections:
    - id: "regulatory_focus"
      title: "Regulatory Focus"
      source_domains: ["regulatory_lai"]
      max_items: 8                    # Plus d'items regulatory
      min_score: 8                    # Seuil plus bas
```

**Solution 4 : Étendre les mots-clés regulatory**
```yaml
# Dans canonical/scopes/technology_scopes.yaml
lai_regulatory_keywords:
  - "FDA approval"
  - "EMA approval"
  - "regulatory submission"
  - "label update"                    # Nouveau mot-clé
  - "post-market surveillance"        # Nouveau mot-clé
```

### Où Modifier Chaque Type de Paramètre

| Type de Réglage | Fichier | Redéploiement Requis |
|------------------|---------|---------------------|
| **Seuils matching** | `lai_weekly_v3.yaml` | ❌ Non |
| **Bonus scoring** | `lai_weekly_v3.yaml` | ❌ Non |
| **Structure newsletter** | `lai_weekly_v3.yaml` | ❌ Non |
| **Sources ingestion** | `lai_weekly_v3.yaml` | ❌ Non |
| **Entreprises surveillées** | `canonical/scopes/company_scopes.yaml` | ❌ Non |
| **Technologies surveillées** | `canonical/scopes/technology_scopes.yaml` | ❌ Non |
| **Prompts Bedrock** | `canonical/prompts/global_prompts.yaml` | ❌ Non |
| **Modèle Bedrock** | Variables d'environnement Lambda | ✅ Oui |
| **Région Bedrock** | Variables d'environnement Lambda | ✅ Oui |

---

## Conclusion

### Points Forts du Moteur V2

**1. Architecture Modulaire**
- 3 Lambdas séparées avec responsabilités claires
- vectora_core réutilisable via layers
- Déploiements indépendants possibles

**2. Configuration-Driven**
- Comportement entièrement piloté par YAML
- Aucune logique métier hardcodée
- Réglages sans redéploiement de code

**3. Intégration Bedrock Optimisée**
- Prompts canonicalisés et versionnés
- Gestion des erreurs et retry robuste
- Contrôle de la parallélisation

**4. Observabilité Complète**
- Logs détaillés à chaque étape
- Métriques de performance et qualité
- Traçabilité des décisions de matching/scoring

### Prêt pour Production

**Validation E2E réussie :**
- ✅ 15 items LAI réels traités avec succès
- ✅ Entités extraites correctement (36 entités détectées)
- ✅ Matching aux domaines fonctionnel
- ✅ Scoring métier appliqué
- ✅ Configuration lai_weekly_v3 respectée

**Prochaine étape :**
- Implémentation de la Lambda newsletter V2
- Génération de la première newsletter basée sur les 15 items curés
- Validation du pipeline complet end-to-end

Le moteur Vectora Inbox V2 est **stabilisé, documenté et prêt** pour servir de base à la génération de newsletters intelligentes pilotées par configuration.

---

*Documentation moteur Vectora Inbox V2 - Version 2.0*  
*Date : 18 décembre 2025*  
*Statut : ✅ STABILISÉ ET DOCUMENTÉ*