# Nouvelle Politique de Sélection Newsletter V2 - LAI Weekly V4

**Date :** 21 décembre 2025  
**Objectif :** Simplifier et sécuriser la logique de sélection pour vectora-inbox-newsletter-v2  
**Client de référence :** lai_weekly_v4  
**Statut :** Design documenté - Prêt pour validation  

---

## 🎯 VISION ET PRINCIPES DIRECTEURS

### Vision Métier
La sélection d'items pour la newsletter doit être **déterministe, transparente et config-driven**. Elle privilégie la **qualité sur la quantité** en se basant uniquement sur les items qui ont été **matchés et curated** par le pipeline amont.

### Principes Fondamentaux
1. **Matching = Filtre de Bruit** : Seuls les items avec `matched_domains` non vides entrent dans la sélection
2. **Score = Outil de Tri** : Le score sert à ordonner, pas à filtrer (sauf cas de volume excessif)
3. **Configuration Pilote** : Toute la logique est paramétrable via `lai_weekly_v4.yaml`
4. **Préservation des Signaux Critiques** : Certains types d'événements sont toujours conservés
5. **Transparence** : Chaque décision de sélection est traçable et explicable

---

## 📋 PHASE 1 : ANALYSE & SYNTHÈSE DE L'EXISTANT

### État Actuel du Pipeline (Décembre 2025)

**Architecture Validée :**
```
Sources LAI → ingest-v2 → S3 ingested/ → normalize-score-v2 → S3 curated/ → newsletter-v2
```

**Métriques lai_weekly_v4 :**
- **Items ingérés :** 15 items depuis 7 sources
- **Items matchés :** 8/15 (53.3%) avec `matched_domains` non vides
- **Items scorés :** 15/15 avec `final_score` calculé
- **Distribution scores :** 0-14.9 (items LAI forts : 12-14.9)

### Logique Actuelle Analysée

**Étapes de Sélection Existantes :**
1. **Filtrage global** : `final_score >= min_score` (12) + `matched_domains` non vides
2. **Déduplication** : Signature sémantique (companies + event_type + trademarks + date)
3. **Sélection par section** : Selon `newsletter_layout.sections` avec filtres domaines/événements
4. **Limite globale** : `max_items_total` (15) avec redistribution si dépassement

**Points Forts Identifiés :**
- ✅ Respect strict du matching (pas de fallback sur `lai_relevance_score`)
- ✅ Configuration pilotée via `newsletter_layout.sections`
- ✅ Déduplication sémantique sophistiquée
- ✅ Tri par score pour priorisation

**Points Faibles Identifiés :**
- ❌ Logique complexe avec "rollbacks" et "bidouilles"
- ❌ Paramètres dispersés dans plusieurs sections YAML
- ❌ Pas de protection des événements critiques
- ❌ Gestion rigide des volumes (tout ou rien)
- ❌ Manque de transparence dans les décisions

### Données Disponibles dans S3 curated/

**Structure des Items :**
```json
{
  "item_id": "unique_identifier",
  "normalized_content": {
    "summary": "Résumé Bedrock",
    "entities": {"companies": [], "technologies": [], "trademarks": []},
    "event_classification": {"primary_type": "partnership|regulatory|clinical_update"},
    "lai_relevance_score": 0-10
  },
  "matching_results": {
    "matched_domains": ["tech_lai_ecosystem"],
    "domain_relevance": {"tech_lai_ecosystem": {"score": 0.0-1.0}}
  },
  "scoring_results": {
    "final_score": 0.0-20.0,
    "base_score": 0.0-10.0,
    "bonuses": {},
    "penalties": {}
  }
}
```

**Qualité des Données :**
- ✅ Tous les champs requis présents
- ✅ Scores cohérents avec la pertinence LAI
- ✅ Entités LAI correctement extraites
- ⚠️ 47% d'items non matchés (bruit résiduel)

---

## 📋 PHASE 2 : DESIGN DÉTAILLÉ DE LA NOUVELLE LOGIQUE

### Inputs de Sélection - Données Disponibles

**Champs Utilisés dans matching_results :**
- `matched_domains` : Liste des domaines matchés (ex: ["tech_lai_ecosystem"])
- `domain_relevance` : Scores de pertinence par domaine (0.0-1.0)

**Champs Utilisés dans scoring_results :**
- `final_score` : Score final calculé (0.0-20.0)
- `base_score` : Score de base avant bonus/malus (0.0-10.0)
- `bonuses` : Détail des bonus appliqués
- `penalties` : Détail des pénalités appliquées

**Champs Utilisés dans normalized_content :**
- `lai_relevance_score` : Score de pertinence LAI Bedrock (0-10)
- `event_classification.primary_type` : Type d'événement (partnership, regulatory, clinical_update, etc.)
- `entities.companies` : Entreprises extraites
- `entities.trademarks` : Marques commerciales extraites
- `summary` : Résumé Bedrock de l'item

### Définition de l'Effective Score

**Principe :** L'effective_score combine intelligemment `final_score` et `lai_relevance_score` pour gérer les cas où l'un des deux est nul.

**Algorithme :**
```
effective_score = final_score si final_score > 0
                = lai_relevance_score * 2 si final_score == 0 et lai_relevance_score > 0
                = 0 si les deux sont nuls
```

**Justification :** 
- `final_score` est prioritaire car il intègre les bonus métier LAI
- `lai_relevance_score * 2` permet de normaliser sur l'échelle 0-20 en fallback
- Cette logique évite de perdre des items pertinents à cause d'erreurs de scoring

### Architecture de Sélection en 4 Étapes

**Principe Central :** Matching = filtre de bruit, Score = outil de tri, Configuration = pilote

```
Items Curated → Filtrage Matching → Déduplication → Distribution Sections → Trimming Intelligent
```

### Étape 1 : Filtrage par Matching (Obligatoire)

**Règle Stricte :** Seuls les items avec `matched_domains` non vides sont éligibles.

**Logique :**
- Filtrage binaire : `matched_domains` vide = rejet automatique
- Pas de fallback sur `lai_relevance_score`
- Respect total de la décision du pipeline amont

**Justification :** Le matching est notre **filtre de bruit primaire**. Un item non matché n'a pas sa place dans une newsletter de veille sectorielle.

### Étape 2 : Déduplication Globale

**Signature Sémantique :**
- `companies` + `event_type` + `trademarks` + `date_truncated`
- Même signature = items considérés comme doublons

**Sélection du Meilleur Doublon :**
1. **Priorité aux événements critiques** (selon `critical_event_types`)
2. **Sinon, meilleur effective_score**
3. **En cas d'égalité, item le plus récent**

**Gestion des Doublons Entre Sections :**
- Déduplication **avant** distribution en sections
- Un item ne peut apparaître que dans une seule section
- Évite les conflits et garantit l'unicité

### Étape 3 : Distribution en Sections

**Construction des Candidats par Section :**

Pour chaque section dans `newsletter_layout.sections` :

1. **Filtrage par domaine :** `item.matched_domains` ∩ `section.source_domains` ≠ ∅
2. **Filtrage par event_type :** Si `section.filter_event_types` défini, vérifier `item.event_classification.primary_type` ∈ `section.filter_event_types`
3. **Tri selon sort_by :**
   - `score_desc` : Tri par effective_score décroissant
   - `date_desc` : Tri par published_at décroissant
4. **Application max_items :** Prendre les N premiers selon `section.max_items`

**Gestion des Items Utilisés :**
- Traitement séquentiel des sections dans l'ordre de `newsletter_layout.sections`
- Un item sélectionné dans une section est marqué "utilisé"
- Les sections suivantes ne peuvent plus le sélectionner
- **Conséquence :** L'ordre des sections dans la config est important

### Étape 4 : Trimming Intelligent

**Déclenchement :** Si `total_items_selected > max_items_total`

**Politique de Trimming :**

1. **Identification des Événements Critiques :**
   - Selon `newsletter_selection.critical_event_types`
   - Ces items sont **toujours conservés**

2. **Tri des Items Réguliers :**
   - Items non critiques triés par effective_score décroissant
   - Sélection des meilleurs pour compléter jusqu'à `max_items_total`

3. **Redistribution dans les Sections :**
   - Maintenir la cohérence avec `newsletter_layout.sections`
   - Respecter `trimming_policy.min_items_per_section`
   - Éviter la dominance excessive d'une section (`max_section_dominance`)

**Règles Métier Proposées :**
- **Préservation critique :** regulatory_approval, nda_submission, pivotal_trial_result
- **Équilibrage :** Aucune section ne peut avoir >60% des items finaux
- **Minimum garanti :** Chaque section garde au moins 1 item si elle en avait

### Configuration newsletter_selection

**Emplacement :** `client-config-examples/lai_weekly_v4.yaml` au niveau racine

```yaml
newsletter_selection:
  # Paramètres de volume
  max_items_total: 20
  min_score_threshold: 0  # Score sert uniquement au tri
  
  # Événements critiques (toujours conservés)
  critical_event_types:
    - "regulatory_approval"
    - "nda_submission" 
    - "pivotal_trial_result"
    - "partnership"
    - "clinical_update"
  
  # Politique de trimming
  trimming_policy:
    preserve_critical_events: true
    min_items_per_section: 1
    max_section_dominance: 0.6
    prefer_recent_items: true
  
  # Déduplication
  deduplication:
    enabled: true
    similarity_threshold: 0.8
    prefer_critical_events: true
    prefer_higher_score: true
```

**Paramètres Config-Driven :**
- `max_items_total` : Limite globale d'items dans la newsletter
- `critical_event_types` : Types d'événements à préserver absolument
- `trimming_policy` : Règles de réduction intelligente
- `deduplication` : Paramètres de déduplication

### Métriques de Qualité Proposées

**Métriques de Sélection :**
- `matching_efficiency` : % d'items matchés effectivement utilisés
- `section_fill_rate` : % de remplissage moyen des sections
- `critical_events_preserved` : Nombre d'événements critiques conservés
- `deduplication_rate` : % d'items dédupliqués
- `trimming_applied` : Booléen indiquant si trimming nécessaire

**Métriques de Distribution :**
- `items_per_section` : Répartition des items par section
- `score_distribution` : Distribution des effective_scores sélectionnés
- `event_type_coverage` : Couverture des types d'événements
- `domain_coverage` : Couverture des domaines de veille

**Structure de Sortie Enrichie :**
```json
{
  "selection_metadata": {
    "total_items_processed": 15,
    "items_after_matching_filter": 8,
    "items_after_deduplication": 7,
    "items_selected": 6,
    "trimming_applied": false,
    "critical_events_preserved": 2,
    "matching_efficiency": 0.75,
    "section_fill_rates": {
      "top_signals": 1.0,
      "partnerships_deals": 0.6,
      "regulatory_updates": 0.8,
      "clinical_updates": 0.5
    },
    "score_distribution": {
      "min": 12.1,
      "max": 18.7,
      "avg": 15.2
    }
  },
  "sections": {
    "top_signals": {
      "title": "Top Signals – LAI Ecosystem",
      "items": [...],
      "metadata": {
        "items_count": 5,
        "avg_score": 16.8,
        "critical_events": 1
      }
    }
  }
}ing_applied": false,
    "critical_events_preserved": 2,
    "selection_policy_version": "2.0"
  },
  "sections": {
    "top_signals": {
      "items": [...],
      "selection_criteria": {
        "source_domains": ["tech_lai_ecosystem"],
        "sort_by": "score_desc",
        "max_items": 5
      }
    }
  }
}
```

---

## 📋 PHASE 3 : PLAN DE REFACTOR DU SELECTOR.PY

### Prérequis Techniques (P0 - Bloquant)

**1. Configuration Lambda newsletter-v2 (Identique à normalize-score-v2) :**

**Variables d'environnement :**
```bash
ENV=dev
CONFIG_BUCKET=vectora-inbox-config-dev
DATA_BUCKET=vectora-inbox-data-dev
NEWSLETTERS_BUCKET=vectora-inbox-newsletters-dev
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_REGION=us-east-1
LOG_LEVEL=INFO
```

**2. Prompts Newsletter Manquants dans global_prompts.yaml :**

**À ajouter dans `canonical/prompts/global_prompts.yaml` :**
```yaml
newsletter:
  # Prompt existant (déjà présent)
  editorial_generation: # ... (existe déjà)
  
  # NOUVEAUX PROMPTS À AJOUTER
  tldr_generation:
    system_instructions: |
      You are a newsletter editor specialized in LAI (Long-Acting Injectable) technology intelligence.
      Generate a factual TL;DR of 2-3 sentences summarizing the week's key signals.
      Style: journalistic, descriptive, focus on "what happened this week".
      FORBIDDEN: strategic analysis, recommendations, opinions.
    
    user_template: |
      Here are this week's LAI signals:
      {{items_summary}}
      
      Generate a factual TL;DR of 2-3 sentences maximum.
    
    bedrock_config:
      max_tokens: 200
      temperature: 0.1
      anthropic_version: "bedrock-2023-05-31"

  introduction_generation:
    system_instructions: |
      You are a newsletter editor specialized in LAI intelligence.
      Generate a 3-4 sentence introduction presenting the week's activity.
      Style: professional, factual, focus on observed events.
      FORBIDDEN: predictions, strategic analysis, advice.
    
    user_template: |
      LAI Newsletter - Week of {{week_start}} to {{week_end}}
      Sections: {{sections_summary}}
      Signals processed: {{total_items}}
      
      Generate a factual introduction of 3-4 sentences.
    
    bedrock_config:
      max_tokens: 300
      temperature: 0.1
      anthropic_version: "bedrock-2023-05-31"
```

### Objectifs du Refactor

1. **Simplifier la logique** : Supprimer les "rollbacks" et "bidouilles"
2. **Centraliser la configuration** : Nouvelle section `newsletter_selection`
3. **Améliorer la traçabilité** : Métadonnées de sélection détaillées
4. **Sécuriser les signaux critiques** : Protection des événements importants

### Structure du Nouveau selector.py

```python
"""
Module selector - Sélection déterministe et intelligente des items
Version 2.0 - Politique de sélection simplifiée et sécurisée
"""

class NewsletterSelector:
    """Sélecteur d'items pour newsletter avec politique intelligente"""
    
    def __init__(self, client_config):
        self.client_config = client_config
        self.selection_config = client_config.get('newsletter_selection', {})
        self.newsletter_layout = client_config.get('newsletter_layout', {})
    
    def select_items(self, curated_items):
        """Point d'entrée principal pour la sélection"""
        
        # Étape 1: Filtrage par matching
        matched_items = self._filter_by_matching(curated_items)
        
        # Étape 2: Déduplication
        deduplicated_items = self._deduplicate_items(matched_items)
        
        # Étape 3: Distribution en sections
        sections_items = self._distribute_to_sections(deduplicated_items)
        
        # Étape 4: Trimming intelligent si nécessaire
        final_selection = self._apply_intelligent_trimming(sections_items)
        
        # Génération des métadonnées
        metadata = self._generate_selection_metadata(
            curated_items, matched_items, deduplicated_items, final_selection
        )
        
        return {
            'sections': final_selection,
            'metadata': metadata
        }
```

### Modules de Support

**1. CriticalEventDetector**
```python
class CriticalEventDetector:
    """Détecte les événements critiques à préserver"""
    
    def __init__(self, critical_event_types):
        self.critical_event_types = critical_event_types
    
    def is_critical(self, item):
        event_type = item['normalized_content']['event_classification']['primary_type']
        return event_type in self.critical_event_types
```

**2. DeduplicationEngine**
```python
class DeduplicationEngine:
    """Moteur de déduplication multi-niveaux"""
    
    def deduplicate(self, items):
        # Implémentation des 3 niveaux de déduplication
        pass
```

**3. SectionDistributor**
```python
class SectionDistributor:
    """Distribue les items dans les sections selon newsletter_layout"""
    
    def distribute(self, items, newsletter_layout):
        # Implémentation de la distribution
        pass
```

### Plan de Migration

**Étape 1 : Préparation (1 jour)**
- Ajouter section `newsletter_selection` à `lai_weekly_v4.yaml`
- Créer tests unitaires pour la nouvelle logique
- Documenter l'API du nouveau selector

**Étape 2 : Implémentation Core (2 jours)**
- Créer `NewsletterSelector` avec les 4 étapes
- Implémenter `CriticalEventDetector`
- Implémenter `DeduplicationEngine` amélioré

**Étape 3 : Intégration (1 jour)**
- Modifier `newsletter/__init__.py` pour utiliser le nouveau selector
- Adapter `assembler.py` pour les nouvelles métadonnées
- Tests d'intégration avec données réelles

**Étape 4 : Validation (1 jour)**
- Tests E2E sur `lai_weekly_v4`
- Comparaison avant/après
- Validation des métadonnées de sélection

---

## 📋 PHASE 4 : STRATÉGIE DE TESTS

### Tests Unitaires

**1. Test de Filtrage par Matching**
```python
def test_filter_by_matching():
    """Teste que seuls les items matchés passent le filtre"""
    items = [
        {"item_id": "1", "matching_results": {"matched_domains": ["tech_lai"]}},
        {"item_id": "2", "matching_results": {"matched_domains": []}},
        {"item_id": "3", "matching_results": {"matched_domains": ["tech_lai"]}}
    ]
    
    filtered = filter_by_matching(items)
    assert len(filtered) == 2
    assert all(item["matching_results"]["matched_domains"] for item in filtered)
```

**2. Test de Déduplication**
```python
def test_deduplication_semantic():
    """Teste la déduplication sémantique"""
    # Items identiques avec scores différents
    items = create_duplicate_items_with_scores([12.5, 14.2])
    
    deduplicated = deduplicate_items(items)
    assert len(deduplicated) == 1
    assert deduplicated[0]["scoring_results"]["final_score"] == 14.2
```

**3. Test de Protection des Événements Critiques**
```python
def test_critical_events_preservation():
    """Teste que les événements critiques sont toujours préservés"""
    items = create_mixed_items_with_critical_events()
    
    selected = apply_intelligent_trimming(items, max_items=3, critical_types=["regulatory_approval"])
    
    critical_items = [item for item in selected if is_critical_event(item)]
    assert len(critical_items) >= 1  # Au moins un événement critique préservé
```

### Tests d'Intégration

**1. Test Volume Faible (0-5 items)**
```python
def test_low_volume_scenario():
    """Teste le comportement avec peu d'items"""
    items = create_low_volume_items(3)
    
    result = selector.select_items(items)
    
    # Tous les items doivent être sélectionnés
    assert result['metadata']['items_selected'] == 3
    # Pas de trimming appliqué
    assert not result['metadata']['trimming_applied']
```

**2. Test Volume Élevé (>25 items)**
```python
def test_high_volume_scenario():
    """Teste le comportement avec beaucoup d'items"""
    items = create_high_volume_items(40)
    
    result = selector.select_items(items)
    
    # Trimming appliqué
    assert result['metadata']['trimming_applied']
    assert result['metadata']['items_selected'] <= 25
    # Événements critiques préservés
    assert result['metadata']['critical_events_preserved'] > 0
```

**3. Test avec Événements Critiques**
```python
def test_critical_events_scenario():
    """Teste la gestion des événements critiques"""
    items = create_items_with_critical_events()
    
    result = selector.select_items(items)
    
    # Vérifier que les événements critiques sont en tête
    top_items = get_top_items_by_score(result['sections'])
    critical_count = sum(1 for item in top_items if is_critical_event(item))
    assert critical_count > 0
```

### Tests E2E

**1. Test sur Données Réelles lai_weekly_v4**

**Données de test spécifiques :**
- **Fichier S3 :** `s3://vectora-inbox-data-dev/curated/lai_weekly_v4/2025/12/20/items.json`
- **Volume :** 15 items traités, 8 items matchés (53.3%)
- **Items LAI forts :** Nanexa-Moderna Partnership, UZEDY FDA Approval, Teva Olanzapine NDA
- **Distribution scores :** 0-14.9 (items pertinents : 12-14.9)

```python
def test_e2e_lai_weekly_v4():
    """Test E2E avec les vraies données lai_weekly_v4 du 20/12/2025"""
    # Charger les données curated réelles
    curated_items = load_s3_data(
        "vectora-inbox-data-dev", 
        "curated/lai_weekly_v4/2025/12/20/items.json"
    )
    
    # Appliquer la nouvelle sélection
    result = selector.select_items(curated_items)
    
    # Validations métier
    assert result['metadata']['items_selected'] >= 4  # Minimum viable
    assert result['metadata']['items_selected'] <= 25  # Maximum configuré
    
    # Vérifier la distribution en sections
    sections = result['sections']
    assert len(sections) >= 2  # Au moins 2 sections non vides
    
    # Vérifier la cohérence des scores
    all_items = get_all_items_from_sections(sections)
    scores = [item['scoring_results']['final_score'] for item in all_items]
    assert all(score > 0 for score in scores)  # Pas de score à 0
    
    # Vérifier items LAI forts sélectionnés
    high_score_items = [item for item in all_items if item['scoring_results']['final_score'] >= 12]
    assert len(high_score_items) >= 3  # Au moins 3 items LAI forts
```

### Métriques de Validation

**Métriques Techniques :**
- **Taux de sélection** : 40-60% des items matchés sélectionnés
- **Distribution sections** : Aucune section >60% des items
- **Préservation critique** : 100% des événements critiques conservés
- **Performance** : <2 secondes pour 50 items

**Métriques Qualité :**
- **Cohérence scores** : Corrélation >0.8 entre ordre de sélection et final_score
- **Pertinence LAI** : >80% des items sélectionnés avec lai_relevance_score ≥ 6
- **Déduplication** : 0 doublons dans la sélection finale
- **Traçabilité** : 100% des décisions documentées dans metadata

---

## 📋 PHASE 5 : PLAN DE DÉPLOIEMENT & MONITORING

### Stratégie de Déploiement

**Approche Blue-Green avec lai_weekly_v4 :**
1. **Déploiement parallèle** : Nouvelle logique en mode "shadow" 
2. **Comparaison A/B** : Ancienne vs nouvelle sélection sur 1 semaine
3. **Validation métier** : Review manuelle des newsletters générées
4. **Bascule progressive** : Migration client par client

**Commandes AWS CLI (Basées sur vectora-inbox-development-rules.md) :**

```bash
# 1. Déploiement infrastructure Lambda newsletter
aws cloudformation deploy \
  --template-file infra/s1-runtime.yaml \
  --stack-name vectora-inbox-s1-runtime-dev \
  --region eu-west-3 \
  --profile rag-lai-prod

# 2. Test Lambda newsletter avec lai_weekly_v4
aws lambda invoke \
  --function-name vectora-inbox-newsletter-v2-dev \
  --payload '{"client_id": "lai_weekly_v4"}' \
  --region eu-west-3 \
  --profile rag-lai-prod \
  response_newsletter.json

# 3. Vérification résultat
cat response_newsletter.json | jq '.statusCode, .body.status, .body.items_selected'

# 4. Téléchargement newsletter générée
aws s3 ls s3://vectora-inbox-newsletters-dev/lai_weekly_v4/ \
  --recursive --profile rag-lai-prod

aws s3 cp s3://vectora-inbox-newsletters-dev/lai_weekly_v4/2025/12/21/newsletter.md \
  newsletter_test.md --profile rag-lai-prod
```

**Rollback Plan :**
- Configuration `newsletter_selection.enabled: false` pour revenir à l'ancienne logique
- Sauvegarde des configurations précédentes
- Monitoring des métriques de qualité en temps réel

### Métriques de Monitoring

**1. Métriques de Sélection**
```yaml
selection_metrics:
  - name: "items_selected_rate"
    description: "Pourcentage d'items matchés sélectionnés"
    target: "40-60%"
    alert_threshold: "<20% ou >80%"
  
  - name: "critical_events_preserved_rate" 
    description: "Pourcentage d'événements critiques préservés"
    target: "100%"
    alert_threshold: "<95%"
  
  - name: "deduplication_effectiveness"
    description: "Pourcentage de doublons détectés et supprimés"
    target: ">90%"
    alert_threshold: "<80%"
```

**2. Métriques de Qualité**
```yaml
quality_metrics:
  - name: "newsletter_engagement_rate"
    description: "Taux d'engagement sur les newsletters"
    target: ">25%"
    alert_threshold: "<15%"
  
  - name: "user_feedback_score"
    description: "Score de satisfaction utilisateur (1-5)"
    target: ">4.0"
    alert_threshold: "<3.5"
  
  - name: "false_positive_rate"
    description: "Pourcentage d'items non pertinents sélectionnés"
    target: "<20%"
    alert_threshold: ">30%"
```

**3. Métriques Techniques**
```yaml
technical_metrics:
  - name: "selection_processing_time"
    description: "Temps de traitement de la sélection"
    target: "<2 secondes"
    alert_threshold: ">5 secondes"
  
  - name: "configuration_compliance_rate"
    description: "Respect des paramètres de configuration"
    target: "100%"
    alert_threshold: "<98%"
```

### Dashboard de Monitoring

**Vue Exécutive :**
- Nombre d'items sélectionnés par newsletter
- Taux de satisfaction utilisateur
- Évolution de la qualité semaine par semaine

**Vue Technique :**
- Distribution des scores des items sélectionnés
- Efficacité de la déduplication
- Performance de la sélection par section

**Vue Métier :**
- Types d'événements les plus sélectionnés
- Entités LAI les plus représentées
- Évolution des signaux critiques

### Alertes Automatiques

**Alertes Critiques (P0) :**
- Aucun item sélectionné pour une newsletter
- Événement critique non préservé lors du trimming
- Temps de traitement >10 secondes

**Alertes Importantes (P1) :**
- Taux de sélection <20% ou >80%
- Score de satisfaction <3.5
- Déduplication <80% d'efficacité

**Alertes Informatives (P2) :**
- Nouvelle distribution inhabituelle par section
- Évolution significative des scores moyens
- Changement dans les types d'événements dominants

---

## 🎯 CONCLUSION ET RECOMMANDATIONS

### Bénéfices Attendus de la Nouvelle Politique

**1. Simplicité et Maintenabilité**
- Logique claire en 4 étapes séquentielles
- Configuration centralisée dans `newsletter_selection`
- Suppression des "rollbacks" et "bidouilles"

**2. Qualité et Pertinence**
- Protection garantie des événements critiques
- Déduplication intelligente multi-niveaux
- Trimming respectueux de la diversité des signaux

**3. Transparence et Traçabilité**
- Métadonnées détaillées de chaque décision
- Monitoring en temps réel de la qualité
- Possibilité d'audit et d'amélioration continue

**4. Flexibilité et Évolutivité**
- Configuration pilotée sans modification de code
- Adaptation facile à de nouveaux clients
- Extension possible à d'autres types de signaux

### Recommandations de Mise en Œuvre

**Priorité P0 (Bloquant) :**
1. **Ajouter configuration newsletter_selection** dans `lai_weekly_v4.yaml` (emplacement : racine, même niveau que newsletter_layout)
2. **Ajouter prompts newsletter manquants** dans `canonical/prompts/global_prompts.yaml` (tldr_generation, introduction_generation)
3. **Configurer variables d'environnement Lambda newsletter** (identiques à normalize-score-v2 + NEWSLETTERS_BUCKET)
4. **Implémenter et tester la logique de protection des événements critiques**
5. **Créer les tests E2E sur données réelles** (`s3://vectora-inbox-data-dev/curated/lai_weekly_v4/2025/12/20/items.json`)

**Priorité P1 (Important) :**
1. Mettre en place le monitoring et les alertes
2. Documenter la nouvelle API pour les équipes
3. Préparer le plan de migration et de rollback

**Priorité P2 (Amélioration) :**
1. Optimiser les performances pour de gros volumes
2. Étendre à d'autres clients (lai_weekly_v3, etc.)
3. Analyser les patterns d'usage pour améliorer la sélection

### Critères de Succès

**Technique :**
- ✅ 0 erreur dans la sélection sur 1 mois
- ✅ Temps de traitement <2 secondes pour 50 items
- ✅ 100% des événements critiques préservés

**Métier :**
- ✅ Taux de satisfaction utilisateur >4.0/5
- ✅ Taux d'engagement newsletter >25%
- ✅ <20% de signalements de contenu non pertinent

**Opérationnel :**
- ✅ Déploiement sans interruption de service
- ✅ Monitoring opérationnel dès J+1
- ✅ Documentation à jour et accessible

---

**Cette nouvelle politique de sélection transforme la newsletter V2 en un outil de veille intelligent, transparent et fiable, respectant strictement les règles de développement Vectora Inbox tout en maximisant la valeur métier pour les utilisateurs.**

---

*Nouvelle Politique de Sélection Newsletter V2 - Version 1.0*  
*Prête pour validation et implémentation*

### Vérification de Conformité

**Respect des Règles vectora-inbox-development-rules.md :**
- ✅ **Architecture V2 préservée** : Aucun impact sur ingest-v2 et normalize-score-v2
- ✅ **Configuration pilotée** : Toute la logique paramétrable via lai_weekly_v4.yaml
- ✅ **Pas de hardcoding** : Aucune logique métier figée dans le code
- ✅ **Modules vectora_core** : Logique dans vectora_core/newsletter/selector.py
- ✅ **Bedrock préservé** : Pas d'impact sur les appels Bedrock existants

**Non-Impact sur les Lambdas Amont :**
- ✅ **ingest-v2** : Aucune modification des données ingested/
- ✅ **normalize-score-v2** : Aucune modification des données curated/
- ✅ **Contrats préservés** : Structure des items curated/ inchangée
- ✅ **Rétrocompatibilité** : Ancienne config continue de fonctionner

**Cohérence avec les Données lai_weekly_v4 :**
- ✅ **Domaine unique** : tech_lai_ecosystem (focus tech confirmé)
- ✅ **Scores disponibles** : final_score et lai_relevance_score présents
- ✅ **Event types** : partnership, regulatory, clinical_update identifiés
- ✅ **Volume réaliste** : max_items_total: 20 adapté aux 8 items matchés typiques

---

## ✅ STATUT PHASE 3 : IMPLÉMENTATION TERMINÉE

**Implémentation Réalisée :**
- ✅ **Configuration newsletter_selection** ajoutée dans `lai_weekly_v4.yaml`
- ✅ **Refactor complet de selector.py** avec nouvelle logique en 4 étapes
- ✅ **Classe NewsletterSelector** implémentée avec métadonnées
- ✅ **Mise à jour newsletter/__init__.py** pour utiliser les nouvelles métadonnées
- ✅ **Tests unitaires complets** créés et validés (6 tests passent)

**Fonctionnalités Implémentées :**
- ✅ **Filtrage strict par matching** : Seuls les items avec matched_domains non vides
- ✅ **Effective_score intelligent** : Fallback lai_relevance_score * 2 si final_score = 0
- ✅ **Déduplication avec priorité critique** : Événements critiques prioritaires
- ✅ **Distribution séquentielle en sections** : Ordre des sections important
- ✅ **Trimming intelligent** : Préservation absolue des événements critiques
- ✅ **Métadonnées détaillées** : Traçabilité complète des décisions

**Tests Validés :**
- ✅ **test_filter_by_matching** : Filtrage par matching fonctionne
- ✅ **test_effective_score_calculation** : Calcul effective_score correct
- ✅ **test_critical_event_detection** : Détection événements critiques
- ✅ **test_deduplication_with_critical_priority** : Priorité aux critiques
- ✅ **test_section_distribution** : Distribution en sections correcte
- ✅ **test_full_selection_workflow** : Workflow complet fonctionnel

**Prêt pour Tests E2E avec lai_weekly_v4.**