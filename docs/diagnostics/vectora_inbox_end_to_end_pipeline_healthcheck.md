# Vectora Inbox - Diagnostic End-to-End Pipeline Healthcheck

## Executive Summary

**État actuel** : Le pipeline Vectora Inbox présente une architecture solide et cohérente pour le MVP LAI, avec une séparation claire entre configuration client, canonical et moteur. La normalisation open-world et le système de matching/scoring sont bien conçus et extensibles.

**Forces principales** :
- Architecture modulaire et pilotable via YAML
- Normalisation open-world robuste avec Bedrock
- Système de matching sophistiqué avec profils technologiques
- Séparation claire client-config vs canonical
- Ingestion profiles pour optimiser les coûts Bedrock

**Risques identifiés** :
- Complexité du matching LAI pourrait créer des faux négatifs (Critique)
- Dépendance forte à Bedrock sans fallback (Important)
- Profils d'ingestion non encore implémentés en runtime (Important)

**Recommandation** : Architecture prête pour tests DEV avec monitoring renforcé sur le matching LAI.

---

## 1. Carte Complète du Pipeline Actuel

### 1.1 Vue d'Ensemble du Workflow

```
CLIENT CONFIG (lai_weekly.yaml)
    ↓
INGESTION (Phase 1A)
    → Source Resolution (bouquets → source_keys)
    → HTTP/RSS Fetching
    → Content Parsing
    → Profile Filtering (ingestion_profiles.yaml) [NOUVEAU]
    ↓
NORMALISATION (Phase 1B)
    → Bedrock Entity Detection + Classification
    → Open-World Schema (detected vs in_scopes)
    → S3 Storage (normalized/client_id/YYYY/MM/DD/)
    ↓
MATCHING (Phase 2)
    → Domain Matching Rules (domain_matching_rules.yaml)
    → Technology Profiles (technology_complex pour LAI)
    → Company Scope Modifiers (pure_player vs hybrid)
    ↓
SCORING (Phase 3)
    → Multi-Factor Scoring (event_type, domain_priority, recency, source_type)
    → Company Bonuses (pure_player +3, hybrid +1)
    → Signal Quality Assessment
    ↓
NEWSLETTER (Phase 4)
    → Item Selection par Section
    → Bedrock Editorial Generation
    → Markdown Assembly
    → S3 Storage (newsletters/client_id/YYYY/MM/DD/)
```

### 1.2 Ingestion - Résolution et Filtrage

**Comment un client_id est résolu :**

1. **Client Config** (`lai_weekly.yaml`) :
   - `source_bouquets_enabled: ["lai_press_mvp", "lai_corporate_mvp"]`
   - Référence des bouquets prédéfinis

2. **Source Catalog** (`canonical/sources/source_catalog.yaml`) :
   - Bouquet `lai_press_mvp` → 3 sources presse (FierceBiotech, FiercePharma, Endpoints)
   - Bouquet `lai_corporate_mvp` → 5 sources corporate (MedinCell, Camurus, DelSiTech, Nanexa, Peptron)
   - Chaque source a un `ingestion_profile` assigné

3. **Profils d'Ingestion** (`canonical/ingestion/ingestion_profiles.yaml`) :
   - `corporate_pure_player_broad` : Filtrage minimal pour pure players
   - `corporate_hybrid_technology_focused` : Filtrage strict pour hybrid (signaux technologiques requis)
   - `press_technology_focused` : Multi-signaux requis (entités + technologie)

**Application des profils d'ingestion :**
- **Pure Players** (MedinCell, Camurus, etc.) → `corporate_pure_player_broad`
  - Logique : Ingère tout sauf exclusions explicites (HR, ESG, finance)
  - Rationale : Taux de signal très élevé, peu de bruit
- **Hybrid/Big Pharma** → `corporate_hybrid_technology_focused`
  - Logique : Ingère seulement si signaux technologiques forts détectés
  - Rationale : Beaucoup de bruit, filtrage agressif nécessaire
- **Presse Sectorielle** → `press_technology_focused`
  - Logique : Entités LAI + (technologie OU trademarks)
  - Rationale : Presse très bruyante, signaux multiples requis

### 1.3 Normalisation Open-World

**Prompt Bedrock défini dans :**
- `vectora_core/normalization/normalizer.py`
- Construction dynamique avec exemples canonical
- Langue client + définitions event_type

**Fonctionnement open-world :**

```json
{
  // OPEN-WORLD: Tout ce que Bedrock détecte
  "companies_detected": ["Camurus", "AbbVie", "Unknown Biotech"],
  "molecules_detected": ["buprenorphine", "novel_compound_X"],
  "technologies_detected": ["long acting", "depot", "nanotechnology"],
  
  // CANONICAL INTERSECTION: Seulement ce qui existe dans nos scopes
  "companies_in_scopes": ["Camurus"],  // AbbVie pas dans lai_companies_global
  "molecules_in_scopes": ["buprenorphine"],  // novel_compound_X pas dans lai_molecules_global
  "technologies_in_scopes": ["long acting"]  // depot oui, nanotechnology non
}
```

**Séparation molecules vs trademarks :**
- `molecules_detected` : Substances actives (buprenorphine, olanzapine)
- `trademarks_detected` : Noms commerciaux (Brixadi, Zyprexa)
- Scopes séparés : `molecule_scopes.yaml` vs `trademark_scopes.yaml`

### 1.4 Matching - Logique LAI Complexe

**Watch_domains du client :**
```yaml
watch_domains:
  - id: "tech_lai_ecosystem"
    type: "technology"
    technology_scope: "lai_keywords"
    company_scope: "lai_companies_global"
    molecule_scope: "lai_molecules_global"
    priority: "high"
```

**Domain Matching Rules** (`domain_matching_rules.yaml`) :

1. **Technology Profile "technology_complex"** (pour LAI) :
   - **High Precision Signals** : `core_phrases`, `technology_terms_high_precision`
   - **Supporting Signals** : `route_admin_terms`, `interval_patterns`
   - **Company Scope Modifiers** :
     - Pure players : High precision signals suffisent
     - Hybrid : High precision + supporting requis

2. **Logique de combinaison** :
   ```
   MATCH if:
     (high_precision_signal AND entity) OR
     (supporting_signal AND supporting_signal AND entity) OR
     (high_precision_signal AND pure_player_company)
   
   REJECT if:
     negative_term detected
   ```

**Activation logique LAI :**
- Référence `technology_scope: "lai_keywords"` dans client config
- `lai_keywords` a `profile: "technology_complex"` dans `technology_scopes.yaml`
- Déclenche la logique complexe avec company scope modifiers

### 1.5 Scoring - Facteurs Multiples

**Facteurs dans le score :**

1. **Event Type Weight** (`scoring_rules.yaml`) :
   - `clinical_update: 3.0`
   - `partnership: 2.5`
   - `regulatory: 2.0`

2. **Domain Priority Weight** :
   - `high: 2.0`, `medium: 1.5`, `low: 1.0`

3. **Source Type Weight** :
   - `press_corporate: 1.5`
   - `press_sector: 1.2`

4. **Company Bonuses** :
   - Pure player : +3 points
   - Hybrid : +1 point

5. **Recency Factor** :
   - Weekly : Décroissance sur 7 jours
   - Monthly : Décroissance sur 30 jours

**Formule de scoring :**
```
score = (event_type_weight × domain_priority_weight × recency_factor × source_type_weight) 
        + company_bonus + signal_quality_score + match_confidence_multiplier
        - negative_term_penalty
```

### 1.6 Newsletter Engine - Assemblage et Éditorial

**Sélection des items :**
1. Groupement par sections (`newsletter_layout` dans client config)
2. Filtrage par `filter_event_types` si spécifié
3. Tri par score décroissant
4. Sélection top N par section (`max_items`)

**Bedrock éditorial :**
- **Input** : Items sélectionnés + contexte client + période
- **Output** : Titre newsletter, introduction, TL;DR, intros de section, reformulations d'items
- **Respect** : Langue, ton, voix du client

**Format final :**
- **Markdown** : Structure lisible avec liens
- **JSON** : Métadonnées éditoriales pour debug
- **S3** : `newsletters/client_id/YYYY/MM/DD/newsletter.md`

---

## 2. Customisation par Client

### 2.1 Ce qu'un Client Peut Contrôler (Client Config)

**Sources et Ingestion :**
- `source_bouquets_enabled` : Quels bouquets de sources utiliser
- `sources_extra_enabled` : Sources additionnelles spécifiques

**Surveillance :**
- `watch_domains` : Domaines à surveiller avec références aux scopes canonical
- Priorités par domaine (`high`, `medium`, `low`)

**Newsletter :**
- `newsletter_layout.sections` : Structure et nombre d'items par section
- `filter_event_types` : Types d'événements par section
- `client_profile` : Langue, ton, voix pour Bedrock

**Exemple de customisation :**
```yaml
# Client A : Focus LAI addiction
watch_domains:
  - id: "lai_addiction"
    indication_scope: "addiction_keywords"
    company_scope: "lai_companies_global"

# Client B : Focus LAI toutes indications
watch_domains:
  - id: "tech_lai_ecosystem"
    technology_scope: "lai_keywords"
    company_scope: "lai_companies_global"
```

### 2.2 Ce qui est Piloté par Canonical

**Définitions d'Entités :**
- `company_scopes.yaml` : Listes d'entreprises par segment
- `molecule_scopes.yaml` : Substances actives par domaine
- `technology_scopes.yaml` : Mots-clés technologiques avec profils
- `trademark_scopes.yaml` : Noms commerciaux

**Logiques Métier :**
- `domain_matching_rules.yaml` : Comment combiner les signaux
- `scoring_rules.yaml` : Poids et facteurs de scoring
- `ingestion_profiles.yaml` : Stratégies de pré-filtrage

**Sources et Bouquets :**
- `source_catalog.yaml` : Définition des sources et bouquets
- Assignation des profils d'ingestion par source

### 2.3 Frontière Générique vs LAI

**Générique (Réutilisable) :**
- Architecture du pipeline (ingestion → normalisation → matching → scoring → newsletter)
- Système de scopes et références
- Logique de matching par type de domaine
- Framework de scoring multi-facteurs
- Profils d'ingestion configurables

**Spécifique LAI :**
- Contenu des scopes (`lai_companies_global`, `lai_keywords`, etc.)
- Profil `technology_complex` avec logique company scope modifiers
- Bouquets `lai_press_mvp` et `lai_corporate_mvp`
- Poids de scoring spécifiques aux événements LAI

**Extensibilité :**
- **Nouvelle verticale** : Créer nouveaux scopes + profil technology + bouquets
- **Nouveau client** : Référencer scopes existants + customiser newsletter_layout
- **Nouvelle source** : Ajouter dans source_catalog + assigner profil d'ingestion

---

## 3. Forces et Faiblesses

### 3.1 Forces Identifiées

**Architecture Modulaire :**
- Séparation claire des responsabilités (config/canonical/runtime)
- Pilotage déclaratif via YAML
- Extensibilité sans modification de code

**Normalisation Robuste :**
- Open-world schema évite la perte d'information
- Intersection canonical préserve la cohérence
- Bedrock avec exemples canonical améliore la précision

**Matching Sophistiqué :**
- Technology profiles pour logiques complexes
- Company scope modifiers (pure_player vs hybrid)
- Combinaisons logiques configurables

**Scoring Transparent :**
- Facteurs explicites et auditables
- Bonuses/pénalités configurables
- Recency factor adaptatif

### 3.2 Faiblesses et Risques

#### 3.2.1 Complexité du Matching LAI (CRITIQUE)

**Problème :**
- Logique `technology_complex` très sophistiquée mais potentiellement fragile
- Risque de faux négatifs si signaux LAI subtils
- Dépendance aux catégories de mots-clés (`core_phrases`, `technology_terms_high_precision`)

**Impact :**
- Items LAI pertinents pourraient être rejetés
- Difficile à débugger pour les utilisateurs métier

**Recommandation :**
- Implémenter logging détaillé du matching avec scores intermédiaires
- Créer dashboard de monitoring des taux de matching
- Prévoir mode "debug" pour analyser les rejets

**Fichiers concernés :**
- `canonical/matching/domain_matching_rules.yaml`
- `vectora_core/matching/matcher.py`

#### 3.2.2 Dépendance Bedrock Sans Fallback (IMPORTANT)

**Problème :**
- Normalisation et newsletter 100% dépendantes de Bedrock
- Pas de fallback en cas d'indisponibilité ou de rate limiting
- Coûts potentiellement élevés avec montée en charge

**Impact :**
- Pipeline bloqué si Bedrock indisponible
- Coûts imprévisibles avec multi-clients

**Recommandation :**
- Implémenter retry avec backoff exponentiel
- Créer fallback rule-based pour normalisation basique
- Monitoring des coûts Bedrock par client

**Fichiers concernés :**
- `vectora_core/normalization/bedrock_client.py`
- `vectora_core/newsletter/bedrock_client.py`

#### 3.2.3 Profils d'Ingestion Non Implémentés (IMPORTANT)

**Problème :**
- Profils d'ingestion définis dans YAML mais pas encore en runtime
- Filtrage pré-normalisation manquant
- Risque de normaliser beaucoup de bruit

**Impact :**
- Coûts Bedrock plus élevés que nécessaire
- Qualité du signal dégradée

**Recommandation :**
- Implémenter `IngestionProfileFilter` en priorité
- Tester sur sources hybrid (AbbVie, Pfizer) pour valider l'efficacité
- Métriques de rétention par profil

**Fichiers concernés :**
- `vectora_core/ingestion/profile_filter.py` (à implémenter)
- `canonical/ingestion/ingestion_profiles.yaml`

#### 3.2.4 Scopes LAI Potentiellement Trop Larges (MINEUR)

**Problème :**
- `lai_companies_global` contient 150+ entreprises
- Risque de faux positifs sur entreprises périphériques
- `lai_keywords` pourrait capturer du bruit

**Impact :**
- Précision dégradée, bruit dans les newsletters
- Difficulté à maintenir la qualité avec la croissance

**Recommandation :**
- Segmenter `lai_companies_global` par tiers (core, extended, peripheral)
- Analyser les faux positifs sur 1 mois de données
- Affiner les mots-clés `generic_terms` et `negative_terms`

**Fichiers concernés :**
- `canonical/scopes/company_scopes.yaml`
- `canonical/scopes/technology_scopes.yaml`

---

## 4. Pertinence et Extensibilité

### 4.1 Pertinence pour MVP LAI

**Très Solide :**
- Architecture adaptée au besoin LAI (surveillance technologique + entités)
- Logique company scope modifiers pertinente (pure_player vs hybrid)
- Sources corporate + presse sectorielle cohérentes avec l'écosystème LAI

**Cohérent :**
- Séparation claire entre ingestion (coût) et matching (précision)
- Scoring multi-facteurs adapté aux priorités business
- Newsletter structure flexible pour différents publics

### 4.2 Puissance/Extensibilité

**Multi-Clients :**
- Framework de scopes permet de créer facilement de nouveaux clients
- Client config découple la surveillance des définitions canonical
- Système de bouquets réutilisable

**Multi-Verticales :**
- Technology profiles extensibles (technology_simple, technology_complex)
- Domain types configurables (technology, indication, regulatory)
- Profils d'ingestion adaptables par secteur

**Limites Identifiées :**
- Bedrock prompt construction pourrait devenir complexe avec beaucoup de scopes
- Scoring rules globales pourraient nécessiter segmentation par verticale
- Source catalog pourrait devenir difficile à maintenir avec croissance

### 4.3 Pilotabilité

**Excellent :**
- Nouveau client = 1 fichier YAML + références aux scopes existants
- Modification des règles sans redéploiement (config S3)
- Métriques et logs structurés pour monitoring

**À Améliorer :**
- Interface de validation des configurations
- Dashboard de monitoring des performances par client
- Outils de debug pour les règles de matching

### 4.4 Précision - Risques de Faux Positifs/Négatifs

**Faux Positifs (Risque Modéré) :**
- Entreprises hybrid avec mentions LAI périphériques
- Mots-clés technologiques dans contextes non-LAI
- Sources presse avec signaux faibles mais multiples

**Faux Négatifs (Risque Élevé) :**
- Items LAI avec terminologie non-standard
- Signaux LAI subtils dans textes longs
- Nouvelles entreprises/molécules non encore dans scopes

**Zones de Risque Principales :**
1. **Matching Technology Complex** : Logique sophistiquée mais fragile
2. **Ingestion Profiles** : Filtrage agressif pourrait éliminer du signal
3. **Scopes Maintenance** : Entités manquantes créent des angles morts

---

## 5. Recommandations par Priorité

### 5.1 Critique (Corriger Maintenant)

1. **Implémenter Monitoring du Matching LAI**
   - Logging détaillé des décisions de matching
   - Métriques de taux de matching par domaine
   - Dashboard de suivi des rejets

2. **Valider la Logique Technology Complex**
   - Tests sur dataset réel avec validation manuelle
   - Ajustement des seuils si nécessaire
   - Documentation des cas limites

### 5.2 Important (Corriger Avant Déploiement DEV)

1. **Implémenter Profils d'Ingestion Runtime**
   - `IngestionProfileFilter` fonctionnel
   - Tests sur sources hybrid
   - Métriques de rétention

2. **Bedrock Resilience**
   - Retry avec backoff exponentiel
   - Monitoring des coûts
   - Fallback basique pour normalisation

3. **Refresh Documentation Technique**
   - Mise à jour .q-context
   - Contrats métier alignés
   - Guide de troubleshooting

### 5.3 Mineur (Documenter/Planifier)

1. **Optimisation des Scopes LAI**
   - Analyse des faux positifs/négatifs
   - Segmentation company_scopes
   - Affinage technology_scopes

2. **Interface de Configuration**
   - Validation YAML automatique
   - Preview des changements
   - Rollback des configurations

---

## 6. Conclusion

L'architecture Vectora Inbox est **solide et prête pour les tests DEV** avec les réserves suivantes :

**Points Forts :**
- Design modulaire et extensible
- Logique métier bien externalisée
- Normalisation open-world robuste
- Scoring transparent et configurable

**Risques à Surveiller :**
- Complexité du matching LAI (monitoring essentiel)
- Dépendance Bedrock (resilience à implémenter)
- Profils d'ingestion (runtime à finaliser)

**Prêt pour :** Tests DEV avec monitoring renforcé
**Pas prêt pour :** Production sans validation du matching LAI sur données réelles

La phase de tests DEV devra se concentrer sur la validation de la précision du matching et l'implémentation des profils d'ingestion pour optimiser les coûts Bedrock.