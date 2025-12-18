# Contrat métier Lambda : vectora-inbox-newsletter V2

## 1. Rôle fonctionnel

La Lambda **vectora-inbox-newsletter** est responsable de l'**assemblage final de la newsletter** à partir des items normalisés et scorés, avec génération de contenu éditorial via Bedrock.

**Responsabilités principales :**
- Sélection des meilleurs items par section selon les règles de layout
- Génération de contenu éditorial via Bedrock (introduction, TL;DR, résumés de section)
- Assemblage de la newsletter finale au format Markdown
- Stockage de la newsletter dans S3 (`outbox/` layer)
- Génération de métriques de veille et statistiques

**Ce que cette Lambda NE fait PAS :**
- Ingestion ou normalisation des contenus
- Matching ou scoring des items (utilise les résultats existants)
- Envoi d'emails (délégué à un service externe)
- Conversion en HTML/PDF (traitement post-génération)

## 2. Triggers

### Trigger principal : EventBridge (après normalize-score)
```json
{
  "source": ["vectora.inbox"],
  "detail-type": ["Normalization Completed"],
  "detail": {
    "client_id": "lai_weekly",
    "processing_date": "2025-01-15",
    "items_scored": 67
  }
}
```

### Trigger manuel : Invocation directe
```json
{
  "client_id": "lai_weekly",
  "target_date": "2025-01-15",
  "period_days": 7
}
```

### Trigger Step Functions (orchestration finale)
- Dernière étape dans un workflow Step Functions
- Déclenchement automatique après succès de normalize-score

## 3. Shape de l'event d'entrée

### Event minimal
```json
{
  "client_id": "lai_weekly"
}
```

### Event complet
```json
{
  "client_id": "lai_weekly",
  "target_date": "2025-01-15",
  "period_days": 7,
  "from_date": "2025-01-08",
  "to_date": "2025-01-15",
  "force_regenerate": false,
  "bedrock_model_override": "anthropic.claude-3-sonnet-20240229-v1:0",
  "output_format": "markdown",
  "include_metrics": true
}
```

### Paramètres
- **`client_id`** (string, obligatoire) : Identifiant unique du client (ex: "lai_weekly")
- **`target_date`** (string, optionnel) : Date de référence pour la newsletter (défaut: aujourd'hui)
- **`period_days`** (int, optionnel) : Nombre de jours à analyser. Surcharge la config client
- **`from_date`** (string, optionnel) : Date de début au format ISO8601 (YYYY-MM-DD)
- **`to_date`** (string, optionnel) : Date de fin au format ISO8601 (YYYY-MM-DD)
- **`force_regenerate`** (bool, optionnel) : Force la régénération même si déjà fait (défaut: false)
- **`bedrock_model_override`** (string, optionnel) : Surcharge le modèle Bedrock configuré
- **`output_format`** (string, optionnel) : Format de sortie ("markdown", "json", "html")
- **`include_metrics`** (bool, optionnel) : Inclure les métriques de veille (défaut: true)

## 4. Configurations lues

### Fichiers client_config
- **Chemin S3** : `s3://vectora-inbox-config/clients/{client_id}.yaml`
- **Contenu utilisé** :
  - `client_profile` : Nom, langue, ton, voix, audience cible
  - `newsletter_layout.sections[]` : Structure des sections (titre, domaines sources, max_items, filtres)
  - `newsletter_delivery` : Format, options d'inclusion (TL;DR, intro, métriques)
  - `scoring_config.selection_overrides` : Seuils de sélection (min_score, max_items_total)
  - `pipeline.default_period_days` : Fenêtre temporelle par défaut

### Fichiers canonical
- **`canonical/prompts/global_prompts.yaml`** :
  - Templates Bedrock pour génération éditoriale (introduction, TL;DR, résumés de section)
  - Prompts par langue et ton (executive, technical, concise, detailed)
- **`canonical/scoring/scoring_rules.yaml`** :
  - Règles de tri et sélection finale
- **`canonical/events/event_type_definitions.yaml`** :
  - Définitions des types d'événements pour filtrage par section

## 5. Données écrites

### S3 Newsletter Markdown (principal)
- **Chemin** : `s3://vectora-inbox-newsletters/{client_id}/{YYYY}/{MM}/{DD}/newsletter.md`
- **Format** : Markdown structuré
- **Exemple** :
```markdown
# LAI Intelligence Weekly – January 15, 2025

*Executive intelligence on Long-Acting Injectable technologies and ecosystem*

## TL;DR – Key Takeaways

This week's LAI ecosystem shows strong partnership activity with MedinCell-Teva collaboration on BEPO technology, regulatory progress for Camurus' CAM2038, and clinical advances in psychiatric LAI formulations. Pure-play companies continue to drive innovation while big pharma partnerships accelerate market access.

**Key Metrics:** 67 signals analyzed • 15 items selected • 8 sources monitored

---

## Top Signals – LAI Ecosystem

### 🔥 MedinCell Announces Strategic Partnership with Teva for BEPO Technology Platform
**Source:** MedinCell Press Release • **Score:** 20.0 • **Date:** Jan 15, 2025

MedinCell (Euronext: MEDCL) today announced a strategic partnership with Teva Pharmaceutical to develop long-acting injectable formulations using the proprietary BEPO technology platform. The collaboration focuses on buprenorphine/naloxone combinations for opioid use disorder treatment...

[**Read more →**](https://www.medincell.com/news/partnership-teva-bepo/)

### 📊 Camurus Reports Positive Phase III Results for CAM2038 in Schizophrenia
**Source:** FierceBiotech • **Score:** 18.5 • **Date:** Jan 14, 2025

Swedish biotech Camurus announced positive topline results from its Phase III CLARITY study evaluating CAM2038, a long-acting injectable formulation of buprenorphine, in patients with treatment-resistant schizophrenia...

---

## Partnerships & Deals

### 🤝 Ipsen Expands Oncology LAI Portfolio Through Acquisition
**Source:** Endpoints News • **Score:** 17.2 • **Date:** Jan 13, 2025

French pharmaceutical company Ipsen has acquired exclusive rights to develop and commercialize a novel long-acting GnRH antagonist for prostate cancer treatment...

---

*Newsletter generated by Vectora Inbox – Powered by Amazon Bedrock*
```

### S3 Newsletter JSON (métadonnées)
- **Chemin** : `s3://vectora-inbox-newsletters/{client_id}/{YYYY}/{MM}/{DD}/newsletter.json`
- **Format** : JSON avec contenu éditorial et métadonnées
- **Exemple** :
```json
{
  "client_id": "lai_weekly",
  "target_date": "2025-01-15",
  "generation_date": "2025-01-15T12:30:00Z",
  "newsletter_title": "LAI Intelligence Weekly – January 15, 2025",
  
  "editorial_content": {
    "tldr": "This week's LAI ecosystem shows strong partnership activity...",
    "introduction": "Executive intelligence on Long-Acting Injectable technologies...",
    "section_summaries": {
      "top_signals": "Partnership activity dominates this week's signals...",
      "partnerships_deals": "Strategic collaborations continue to reshape..."
    }
  },
  
  "sections": [
    {
      "id": "top_signals",
      "title": "Top Signals – LAI Ecosystem",
      "items_count": 5,
      "items": [
        {
          "item_id": "press_corporate__medincell_20250115_001",
          "title": "MedinCell Announces Strategic Partnership with Teva...",
          "score": 20.0,
          "source_key": "press_corporate__medincell",
          "published_at": "2025-01-15",
          "url": "https://www.medincell.com/news/partnership-teva-bepo/"
        }
      ]
    }
  ],
  
  "metrics": {
    "period": {"from_date": "2025-01-08", "to_date": "2025-01-15"},
    "items_analyzed": 67,
    "items_selected": 15,
    "sources_monitored": 8,
    "average_score": 16.3,
    "source_breakdown": {
      "corporate": 9,
      "press": 6
    },
    "domain_breakdown": {
      "tech_lai_ecosystem": 12,
      "regulatory_lai": 3
    }
  },
  
  "generation_metadata": {
    "bedrock_model": "anthropic.claude-3-sonnet-20240229-v1:0",
    "processing_time_ms": 3450,
    "bedrock_calls": 4,
    "total_tokens": 12500,
    "version": "2.0.0"
  }
}
```

### S3 Delivery Manifest (tracking)
- **Chemin** : `s3://vectora-inbox-newsletters/{client_id}/{YYYY}/{MM}/{DD}/manifest.json`
- **Format** : Métadonnées de livraison
- **Contenu** : Statut de génération, chemins des fichiers, checksums

## 6. Workflow métier

1. **Validation de l'event** : Vérifier que `client_id` est fourni et valide
2. **Chargement des configurations** : Lire la config client et les prompts canonical depuis S3
3. **Collecte des items scorés** : Récupérer les items normalisés et scorés depuis S3 sur la fenêtre temporelle
4. **Sélection par section** : Pour chaque section du layout, sélectionner les meilleurs items selon les critères (domaines, types d'événements, scores)
5. **Génération du TL;DR** : Appeler Bedrock pour créer un résumé exécutif des signaux principaux
6. **Génération de l'introduction** : Appeler Bedrock pour créer une introduction contextuelle
7. **Assemblage des sections** : Formater chaque section avec ses items sélectionnés
8. **Génération des résumés de section** : Appeler Bedrock pour créer des résumés éditoriaux par section
9. **Assemblage final** : Construire la newsletter Markdown complète avec header, sections et footer
10. **Calcul des métriques** : Générer les statistiques de veille (sources, domaines, scores)
11. **Écriture S3** : Stocker la newsletter et les métadonnées dans le newsletters bucket
12. **Retour des statistiques** : Nombre d'items sélectionnés, sections générées, temps de traitement

## 7. Sources des spécifications

### Du blueprint (vision cible)
- **Bedrock pour contenu éditorial** : Introduction, TL;DR, résumés de section
- **Pas d'appel Bedrock pour** : Sélection des items (règles numériques), tri par score
- **Stockage newsletters** : Bucket dédié avec structure par date
- **Format Markdown first** : HTML/PDF en post-traitement

### Du code existant (observé dans /src)
- **Fonction orchestratrice** : `run_engine_for_client()` dans `vectora_core` (actuellement combine normalize + score + newsletter)
- **Module newsletter** : `vectora_core.newsletter.assembler` avec `generate_newsletter()`
- **Variables d'environnement** : `NEWSLETTERS_BUCKET`, `BEDROCK_MODEL_ID_NEWSLETTER`
- **Structure de sortie** : Newsletter Markdown + JSON éditorial
- **Gestion des sections** : `newsletter_layout.sections[]` avec filtres par `source_domains` et `filter_event_types`

### Des données canonical existantes
- **Prompts éditoriaux** : Templates Bedrock dans `canonical/prompts/global_prompts.yaml`
- **Types d'événements** : Définitions dans `canonical/events/event_type_definitions.yaml`
- **Config client LAI** : Structure de newsletter dans `lai_weekly_v3.yaml` avec 4 sections
- **Règles de scoring** : Seuils de sélection (`min_score: 12`, `max_items_total: 15`)
- **Profil client** : Langue, ton, voix dans `client_profile` pour personnalisation éditoriale

---

**Note** : Ce contrat finalise l'architecture 3 Lambdas en se concentrant uniquement sur l'assemblage éditorial et la génération de newsletter, sans redondance avec les étapes précédentes. La logique éditoriale complexe reste dans `vectora_core.newsletter` pour réutilisabilité.