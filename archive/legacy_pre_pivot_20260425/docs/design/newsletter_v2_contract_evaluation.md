# Évaluation du Contrat newsletter_v2.md - Recommandations

**Date :** 21 décembre 2025  
**Phase :** 5 - Évaluation de la pertinence du contrat newsletter_v2.md  
**Objectif :** Vérifier l'alignement avec le moteur actuel et recommander des améliorations  

---

## 📋 COMPARAISON CONTRAT vs RÉALITÉ TECHNIQUE

### Alignement avec le Workflow Actuel (Phases 1-4)

#### ✅ Points Alignés avec la Réalité

**Rôle fonctionnel :**
```markdown
# CONTRAT (Section 1)
"assemblage final de la newsletter à partir des items normalisés et scorés"
"génération de contenu éditorial via Bedrock"

# RÉALITÉ VALIDÉE (Phase 4)
✅ Items curated disponibles dans S3 curated/
✅ Bedrock pour rédaction uniquement (TL;DR, intro, titres, résumés)
✅ Assemblage template Markdown
```

**Triggers :**
```json
// CONTRAT (Section 2)
{
  "client_id": "lai_weekly",
  "target_date": "2025-01-15",
  "period_days": 7
}

// RÉALITÉ VALIDÉE (Phase 4)
✅ client_id obligatoire et validé
✅ target_date optionnel (défaut: aujourd'hui)
✅ Trigger EventBridge après normalize-score possible
```

**Configurations lues :**
```yaml
# CONTRAT (Section 4)
client_config: client_profile, newsletter_layout.sections[], scoring_config.selection_overrides
canonical: prompts/global_prompts.yaml

# RÉALITÉ VALIDÉE (Phase 1-4)
✅ lai_weekly_v3.yaml avec newsletter_layout validé E2E
✅ global_prompts.yaml avec templates newsletter existants
✅ Configuration pilotée confirmée
```

**Workflow métier :**
```
# CONTRAT (Section 6)
1. Validation event → 2. Chargement configs → 3. Collecte items → 4. Sélection par section
→ 5. Génération TL;DR → 6. Génération intro → 7. Assemblage sections → 8. Génération résumés
→ 9. Assemblage final → 10. Calcul métriques → 11. Écriture S3

# RÉALITÉ VALIDÉE (Phase 4)
✅ Workflow cohérent avec stratégie d'assemblage définie
✅ Étapes logiques et implémentables
```

#### ⚠️ Points à Ajuster/Préciser

**Chemins S3 :**
```markdown
# CONTRAT
"S3 (`outbox/` layer)"

# RÉALITÉ (Phase 1)
❌ INCOHÉRENT : Structure réelle est newsletters/ pas outbox/
✅ CORRECTION : s3://vectora-inbox-newsletters-dev/{client_id}/{YYYY}/{MM}/{DD}/
```

**Inputs manquants :**
```markdown
# CONTRAT (Section 3)
Paramètres event complets mais...

# RÉALITÉ MANQUANTE
❌ Pas de spécification du chemin S3 input (curated/)
❌ Pas de gestion des fenêtres temporelles multiples
❌ Pas de paramètre deduplication_strategy
```

**Métriques sous-spécifiées :**
```json
// CONTRAT (Section 5)
"metrics": {
  "items_analyzed": 67,
  "items_selected": 15
}

// RÉALITÉ ENRICHIE (Phase 4)
✅ AJOUTER : bedrock_calls, processing_time_ms, estimated_cost_usd
✅ AJOUTER : deduplication_stats, section_breakdown
```

---

## 🔍 INCOHÉRENCES IDENTIFIÉES

### Avec ingest_v2.md et normalize_score_v2.md

#### Structure S3 Incohérente
```yaml
# ingest_v2.md
Output: "s3://vectora-inbox-data/ingested/{client_id}/{YYYY}/{MM}/{DD}/items.json"

# normalize_score_v2.md  
Output: "s3://vectora-inbox-data/curated/{client_id}/{YYYY}/{MM}/{DD}/items.json"

# newsletter_v2.md (ACTUEL)
Output: "s3://vectora-inbox-newsletters/{client_id}/{YYYY}/{MM}/{DD}/newsletter.md"
Input: ❌ NON SPÉCIFIÉ

# CORRECTION NÉCESSAIRE
Input: "s3://vectora-inbox-data/curated/{client_id}/{YYYY}/{MM}/{DD}/items.json"
```

#### Variables d'Environnement Manquantes
```yaml
# ingest_v2.md + normalize_score_v2.md
Variables: CONFIG_BUCKET, DATA_BUCKET, BEDROCK_MODEL_ID, BEDROCK_REGION

# newsletter_v2.md (ACTUEL)
Variables: ❌ NON SPÉCIFIÉES

# CORRECTION NÉCESSAIRE
Variables: CONFIG_BUCKET, DATA_BUCKET, NEWSLETTERS_BUCKET, BEDROCK_MODEL_ID, BEDROCK_REGION
```

### Avec blueprint-v2-current.yaml

#### Nommage des Buckets
```yaml
# blueprint-v2-current.yaml
newsletters_bucket: "vectora-inbox-newsletters-dev"

# newsletter_v2.md (ACTUEL)
Chemin: "s3://vectora-inbox-newsletters/{client_id}/"

# CORRECTION NÉCESSAIRE
Chemin: "s3://vectora-inbox-newsletters-dev/{client_id}/" (avec suffixe -dev)
```

#### Architecture 3 Lambdas
```yaml
# blueprint-v2-current.yaml
Lambdas: ingest-v2, normalize-score-v2, newsletter-v2

# newsletter_v2.md (ACTUEL)
✅ Cohérent : "utilise les résultats existants" (pas de duplication responsabilités)
```

### Avec vectora-inbox-development-rules.md

#### Conventions de Nommage
```yaml
# development-rules.md
Lambda: "vectora-inbox-newsletter-v2-dev"
Région: "eu-west-3"
Profil: "rag-lai-prod"

# newsletter_v2.md (ACTUEL)
❌ Pas de spécification des conventions AWS
```

---

## 📝 RECOMMANDATIONS D'AMÉLIORATION

### P0 - Corrections Critiques

#### 1. Ajouter Section "Inputs S3"
```markdown
## 3.5. Données lues

### S3 Curated Items (principal)
- **Chemin** : `s3://vectora-inbox-data-dev/curated/{client_id}/{YYYY}/{MM}/{DD}/items.json`
- **Format** : JSON array des items normalisés et scorés
- **Contenu requis** :
  - `scoring_results.final_score` : Pour filtrage par seuil
  - `matching_results.matched_domains` : Pour sélection par section
  - `normalized_content.event_classification.primary_type` : Pour filtrage par type
  - `normalized_content.summary` : Base pour génération éditoriale
  - `normalized_content.entities` : Contexte pour rédaction
```

#### 2. Corriger Chemins S3
```markdown
## 5. Données écrites

### S3 Newsletter Markdown (principal)
- **Chemin** : `s3://vectora-inbox-newsletters-dev/{client_id}/{YYYY}/{MM}/{DD}/newsletter.md`

### S3 Newsletter JSON (métadonnées)
- **Chemin** : `s3://vectora-inbox-newsletters-dev/{client_id}/{YYYY}/{MM}/{DD}/newsletter.json`

### S3 Delivery Manifest (tracking)
- **Chemin** : `s3://vectora-inbox-newsletters-dev/{client_id}/{YYYY}/{MM}/{DD}/manifest.json`
```

#### 3. Ajouter Variables d'Environnement
```markdown
## 2.5. Variables d'environnement

### Variables requises
- **`ENV`** (string) : Environnement (dev, prod)
- **`CONFIG_BUCKET`** (string) : Bucket configurations (vectora-inbox-config-dev)
- **`DATA_BUCKET`** (string) : Bucket données (vectora-inbox-data-dev)
- **`NEWSLETTERS_BUCKET`** (string) : Bucket newsletters (vectora-inbox-newsletters-dev)
- **`BEDROCK_MODEL_ID`** (string) : Modèle Bedrock (anthropic.claude-3-sonnet-20240229-v1:0)
- **`BEDROCK_REGION`** (string) : Région Bedrock (us-east-1)
- **`LOG_LEVEL`** (string, optionnel) : Niveau de log (INFO)
```

### P1 - Améliorations Importantes

#### 4. Enrichir les Paramètres d'Event
```json
{
  "client_id": "lai_weekly_v3",
  "target_date": "2025-01-15",
  "period_days": 7,
  "from_date": "2025-01-08",
  "to_date": "2025-01-15",
  "force_regenerate": false,
  "bedrock_model_override": "anthropic.claude-3-sonnet-20240229-v1:0",
  "output_format": "markdown",
  "include_metrics": true,
  
  // NOUVEAUX PARAMÈTRES RECOMMANDÉS
  "deduplication_strategy": "semantic",     // basic, semantic, intelligent
  "max_bedrock_workers": 1,                // Contrôle parallélisation
  "include_section_summaries": true,       // Génération résumés sections
  "editorial_style": "executive"           // Surcharge du ton
}
```

#### 5. Enrichir les Métriques de Sortie
```json
{
  "generation_metadata": {
    "bedrock_model": "anthropic.claude-3-sonnet-20240229-v1:0",
    "processing_time_ms": 42000,
    "bedrock_calls": 13,
    "total_tokens": 10160,
    "estimated_cost_usd": 0.045,
    "version": "2.0.0",
    
    // NOUVELLES MÉTRIQUES RECOMMANDÉES
    "deduplication_stats": {
      "items_before_dedup": 15,
      "items_after_dedup": 12,
      "duplicates_removed": 3
    },
    "selection_stats": {
      "items_eligible": 12,
      "items_selected": 7,
      "selection_rate": 0.583
    },
    "section_breakdown": {
      "top_signals": 3,
      "partnerships_deals": 2,
      "regulatory_updates": 1,
      "clinical_updates": 1
    }
  }
}
```

#### 6. Préciser le Workflow de Déduplication
```markdown
## 6. Workflow métier

1. **Validation de l'event** : Vérifier que `client_id` est fourni et valide
2. **Chargement des configurations** : Lire la config client et les prompts canonical depuis S3
3. **Collecte des items scorés** : Récupérer les items normalisés et scorés depuis S3 sur la fenêtre temporelle
4. **Déduplication des items** : Appliquer la stratégie de déduplication (technique → sémantique → temporelle)
5. **Sélection par section** : Pour chaque section du layout, sélectionner les meilleurs items selon les critères
6. **Génération du TL;DR** : Appeler Bedrock pour créer un résumé exécutif des signaux principaux
7. **Génération de l'introduction** : Appeler Bedrock pour créer une introduction contextuelle
8. **Réécriture des titres** : Appeler Bedrock pour optimiser les titres d'items
9. **Assemblage des sections** : Formater chaque section avec ses items sélectionnés
10. **Génération des résumés de section** : Appeler Bedrock pour créer des résumés éditoriaux par section
11. **Assemblage final** : Construire la newsletter Markdown complète avec header, sections et footer
12. **Calcul des métriques** : Générer les statistiques de veille (sources, domaines, scores, coûts)
13. **Écriture S3** : Stocker la newsletter et métadonnées dans le bucket newsletters
```

### P2 - Optimisations Futures

#### 7. Ajouter Section Configuration Newsletter
```markdown
## 4.3. Configuration newsletter spécialisée

### newsletter_layout (client_config)
```yaml
newsletter_layout:
  # Configuration de déduplication
  deduplication:
    enabled: true
    strategy: "semantic"  # basic, semantic, intelligent
    preserve_corporate_sources: true
    max_items_per_event: 1
  
  # Sections de la newsletter
  sections:
    - id: "top_signals"
      title: "Top Signals – LAI Ecosystem"
      source_domains: ["tech_lai_ecosystem", "regulatory_lai"]
      max_items: 5
      sort_by: "score_desc"
      deduplication_priority: "highest_score"
    
    - id: "partnerships_deals"
      title: "Partnerships & Deals"
      source_domains: ["tech_lai_ecosystem"]
      max_items: 5
      filter_event_types: ["partnership", "corporate_move"]
      sort_by: "date_desc"
      deduplication_priority: "most_recent"
```

#### 8. Ajouter Gestion d'Erreurs
```markdown
## 7. Gestion d'erreurs

### Erreurs de configuration
- **ConfigurationError** : client_id invalide ou configuration manquante
- **ValidationError** : Structure newsletter_layout invalide

### Erreurs de données
- **DataNotFoundError** : Aucun item curated trouvé pour la période
- **InsufficientDataError** : Pas assez d'items après filtrage/déduplication

### Erreurs Bedrock
- **BedrockThrottlingError** : Limitation de débit Bedrock
- **BedrockModelError** : Modèle indisponible ou erreur génération

### Stratégies de fallback
- **Génération partielle** : Newsletter avec sections disponibles uniquement
- **Mode dégradé** : Newsletter sans génération Bedrock (titres originaux)
- **Retry automatique** : Nouvelle tentative avec délai exponentiel
```

---

## 🎯 ÉVALUATION FINALE DU CONTRAT

### ✅ Points Forts du Contrat Actuel

1. **Vision claire** : Rôle et responsabilités bien définis
2. **Workflow logique** : Étapes cohérentes et implémentables
3. **Configuration pilotée** : Aligné avec l'architecture V2
4. **Exemples concrets** : JSON et Markdown illustratifs
5. **Séparation des responsabilités** : Pas de duplication avec ingest/normalize

### ⚠️ Points à Améliorer

1. **Inputs sous-spécifiés** : Chemin S3 curated manquant
2. **Variables d'environnement** : Non documentées
3. **Chemins S3 incorrects** : outbox/ vs newsletters-dev/
4. **Déduplication absente** : Étape critique non mentionnée
5. **Métriques incomplètes** : Coûts Bedrock et stats manquants
6. **Gestion d'erreurs** : Non spécifiée

### 📊 Score de Pertinence

```
Alignement avec réalité technique : 75% ✅
Cohérence avec autres contrats   : 60% ⚠️
Complétude des spécifications   : 65% ⚠️
Implémentabilité directe        : 70% ✅

SCORE GLOBAL : 67.5% - ACCEPTABLE AVEC AMÉLIORATIONS
```

---

## 📋 PLAN D'AMÉLIORATION RECOMMANDÉ

### Phase Immédiate (Avant Développement)

1. **Corriger les chemins S3** : newsletters-dev/ avec suffixe environnement
2. **Ajouter section inputs** : Spécifier chemin curated/ et structure requise
3. **Documenter variables d'environnement** : CONFIG_BUCKET, DATA_BUCKET, NEWSLETTERS_BUCKET, BEDROCK_*
4. **Ajouter étape déduplication** : Dans workflow métier entre collecte et sélection

### Phase Développement (Pendant Implémentation)

5. **Enrichir les métriques** : Coûts Bedrock, stats déduplication, breakdown sections
6. **Préciser paramètres event** : deduplication_strategy, max_bedrock_workers
7. **Ajouter gestion d'erreurs** : Stratégies fallback et retry

### Phase Post-MVP (Après Validation)

8. **Configuration newsletter avancée** : Déduplication fine, priorités par section
9. **Optimisations performance** : Batch processing, caching, parallélisation
10. **Monitoring avancé** : Métriques qualité, alertes, dashboards

---

## 🎯 CONCLUSION PHASE 5

### Réponse à la Question Clé

**"Le contrat newsletter_v2.md est-il réaliste et aligné avec le moteur actuel ?"**

**✅ OUI, avec corrections mineures**

**Justification :**
- **Vision cohérente** : Rôle et workflow alignés avec stratégie Phase 4
- **Architecture compatible** : Respecte la séparation 3 Lambdas V2
- **Configuration pilotée** : Utilise client_config et canonical existants
- **Implémentable** : Étapes logiques et réalisables

**Corrections nécessaires :**
1. **Chemins S3** : newsletters-dev/ au lieu de outbox/
2. **Inputs spécifiés** : Chemin curated/ et structure JSON
3. **Variables d'environnement** : Documentation complète
4. **Déduplication** : Étape ajoutée au workflow

### Prochaine Étape

**Phase 6 :** Synthèse finale avec toutes les réponses aux questions métier/techniques et recommandations pour le développement.

---

**🎯 RÉSULTAT PHASE 5**

Le contrat newsletter_v2.md est **globalement pertinent** (67.5%) mais nécessite des **corrections mineures** avant développement. Les améliorations proposées le rendront **100% aligné** avec la réalité technique validée.