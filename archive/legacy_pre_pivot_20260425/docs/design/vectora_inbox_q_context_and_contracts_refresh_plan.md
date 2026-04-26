# Vectora Inbox - Plan de Refresh du .q-context et des Contrats Métier

## Executive Summary

**Objectif** : Réaligner la documentation (.q-context) et les contrats métier avec l'état actuel du code après les évolutions majeures (normalisation open-world, ingestion profiles, matching refactor, scoring LAI).

**État actuel** : Documentation partiellement obsolète, contrats métier incomplets pour les nouvelles fonctionnalités.

**Livrable** : Documentation mise à jour reflétant fidèlement l'architecture et les fonctionnalités actuelles.

---

## 1. Analyse de l'État Actuel

### 1.1 Fichiers .q-context Existants

| Fichier | État | Problèmes Identifiés |
|---------|------|---------------------|
| `vectora-inbox-overview.md` | **Partiellement obsolète** | - Pas de mention des ingestion profiles<br>- Normalisation open-world non documentée<br>- Matching LAI complexe non expliqué |
| `vectora-inbox-q-rules.md` | **À vérifier** | - Règles AWS potentiellement obsolètes |
| `blueprint-draft-vectora-inbox.yaml` | **À vérifier** | - Infrastructure potentiellement obsolète |

### 1.2 Contrats Métier Existants

| Fichier | État | Problèmes Identifiés |
|---------|------|---------------------|
| `contracts/lambdas/vectora-inbox-ingest-normalize.md` | **Obsolète** | - Pas de mention des ingestion profiles<br>- Normalisation open-world non documentée<br>- Schéma JSON incomplet |
| `contracts/lambdas/vectora-inbox-engine.md` | **Obsolète** | - Matching rules complexes non documentées<br>- Technology profiles non expliqués<br>- Scoring LAI non détaillé |

### 1.3 Fonctionnalités Manquantes dans la Documentation

**Nouvelles fonctionnalités non documentées :**

1. **Ingestion Profiles** (`canonical/ingestion/ingestion_profiles.yaml`)
   - Profils de pré-filtrage par type de source
   - Logique corporate_pure_player_broad vs corporate_hybrid_technology_focused
   - Stratégies multi-signaux pour presse sectorielle

2. **Normalisation Open-World** 
   - Schéma `*_detected` vs `*_in_scopes`
   - Intersection canonical pour préserver cohérence
   - Séparation molecules vs trademarks

3. **Matching Refactor**
   - Technology profiles (technology_complex pour LAI)
   - Domain matching rules configurables
   - Company scope modifiers (pure_player vs hybrid)

4. **Scoring LAI**
   - Facteurs multi-dimensionnels
   - Company bonuses différenciés
   - Recency factor adaptatif

5. **Newsletter Engine**
   - Bedrock editorial generation
   - Section-based assembly
   - Markdown formatting avancé

---

## 2. Plan de Refresh - Phase par Phase

### 2.1 Phase A : Mise à Jour .q-context

#### A.1 Refresh `vectora-inbox-overview.md`

**Sections à mettre à jour :**

1. **Section 2.5 High-Level Data Flow**
   - Ajouter étape "Profile Filtering" entre ingestion et normalisation
   - Détailler normalisation open-world
   - Préciser rôle des technology profiles dans matching

2. **Section 3 End-to-End Workflow**
   - **Phase 1A** : Ajouter ingestion profiles
   - **Phase 1B** : Détailler normalisation open-world avec exemples JSON
   - **Phase 2** : Expliquer matching rules et technology profiles
   - **Phase 3** : Détailler scoring multi-facteurs LAI

3. **Nouvelle Section** : "Ingestion Profiles et Optimisation Coûts"
   - Philosophie du pré-filtrage
   - Profils par type de source
   - Métriques de rétention

4. **Nouvelle Section** : "Matching Avancé et Technology Profiles"
   - Logique technology_complex
   - Company scope modifiers
   - Combinaisons logiques configurables

#### A.2 Vérification `vectora-inbox-q-rules.md`

**Actions :**
- Vérifier cohérence avec infrastructure actuelle
- Mettre à jour si nécessaire
- Ajouter règles pour nouveaux composants

#### A.3 Vérification `blueprint-draft-vectora-inbox.yaml`

**Actions :**
- Vérifier cohérence avec déploiements actuels
- Mettre à jour variables d'environnement
- Ajouter nouvelles permissions si nécessaire

### 2.2 Phase B : Refresh Contrats Métier

#### B.1 Mise à Jour `vectora-inbox-ingest-normalize.md`

**Sections à ajouter/modifier :**

1. **Nouvelle Section** : "Phase 1A-bis : Profile Filtering"
   - Chargement des ingestion profiles
   - Application des filtres par source_key
   - Métriques de rétention

2. **Section "Phase 1B : Normalisation"** - Mise à jour complète :
   - Prompt Bedrock avec exemples canonical
   - Schéma open-world complet avec exemples
   - Intersection canonical vs detected
   - Séparation molecules/trademarks

3. **Exemples JSON** - Mise à jour complète :
   - Input avec profils d'ingestion
   - Output avec schéma open-world
   - Cas d'erreur avec profils

#### B.2 Mise à Jour `vectora-inbox-engine.md`

**Sections à ajouter/modifier :**

1. **Section "Phase 2 : Matching"** - Refactor complet :
   - Chargement des domain matching rules
   - Technology profiles et logique complexe
   - Company scope modifiers
   - Exemples de matching LAI

2. **Section "Phase 3 : Scoring"** - Détail complet :
   - Facteurs de scoring multi-dimensionnels
   - Company bonuses différenciés
   - Recency factor par fréquence client
   - Formule de calcul explicite

3. **Section "Phase 4 : Newsletter"** - Mise à jour :
   - Bedrock editorial generation
   - Assembly par sections
   - Markdown formatting

4. **Exemples JSON** - Mise à jour complète :
   - Input avec items normalisés open-world
   - Intermediate avec matching results
   - Output avec newsletter complète

### 2.3 Phase C : Nouveaux Documents

#### C.1 Création `contracts/data/normalized_item_schema.md`

**Contenu :**
- Schéma JSON complet des items normalisés
- Explication open-world vs canonical
- Exemples par type de source
- Validation et contraintes

#### C.2 Création `contracts/config/ingestion_profiles_specification.md`

**Contenu :**
- Spécification complète des profils d'ingestion
- Stratégies de filtrage
- Configuration des signaux requis
- Exemples par type de source

#### C.3 Création `contracts/config/matching_rules_specification.md`

**Contenu :**
- Spécification des domain matching rules
- Technology profiles détaillés
- Company scope modifiers
- Logiques de combinaison

---

## 3. Critères de "Done"

### 3.1 Pour .q-context

**Un humain peut :**
- Comprendre l'architecture complète en lisant `vectora-inbox-overview.md`
- Identifier les phases du pipeline et leurs responsabilités
- Comprendre les paramètres disponibles pour un nouveau client
- Localiser les fichiers de configuration pertinents

**Q Developer peut :**
- Générer du code cohérent avec l'architecture documentée
- Comprendre les contrats entre composants
- Identifier les points d'extension pour nouvelles fonctionnalités

### 3.2 Pour Contrats Métier

**Un développeur peut :**
- Implémenter une Lambda sans ambiguïté
- Comprendre les formats d'entrée/sortie exacts
- Gérer les cas d'erreur spécifiés
- Tester avec les exemples fournis

**Un architecte peut :**
- Valider la logique métier implémentée
- Identifier les impacts de changements de configuration
- Comprendre les dépendances entre composants

### 3.3 Cohérence Globale

**Vocabulaire aligné :**
- Noms des scopes cohérents entre docs et code
- Terminologie technique unifiée
- Références croisées correctes

**Exemples fonctionnels :**
- JSON d'exemple exécutables
- Configurations d'exemple valides
- Cas d'usage réalistes

---

## 4. Exécution du Plan

### 4.1 Ordre d'Exécution

1. **Phase A.1** : Refresh `vectora-inbox-overview.md` (priorité haute)
2. **Phase B.1** : Refresh `vectora-inbox-ingest-normalize.md` (priorité haute)
3. **Phase B.2** : Refresh `vectora-inbox-engine.md` (priorité haute)
4. **Phase A.2-A.3** : Vérification autres fichiers .q-context (priorité moyenne)
5. **Phase C** : Nouveaux documents spécialisés (priorité basse)

### 4.2 Validation

**Après chaque phase :**
- Relecture croisée entre documents
- Vérification cohérence avec code actuel
- Test des exemples JSON fournis

**Validation finale :**
- Relecture complète de la documentation
- Vérification des références croisées
- Test de compréhension avec persona "nouveau développeur"

---

## 5. Ressources et Références

### 5.1 Code Source à Analyser

**Modules principaux :**
- `src/vectora_core/__init__.py` : Orchestration générale
- `src/vectora_core/ingestion/profile_filter.py` : Profils d'ingestion
- `src/vectora_core/normalization/normalizer.py` : Normalisation open-world
- `src/vectora_core/matching/matcher.py` : Matching avec technology profiles
- `src/vectora_core/scoring/scorer.py` : Scoring multi-facteurs
- `src/vectora_core/newsletter/assembler.py` : Assembly newsletter

### 5.2 Configurations à Documenter

**Canonical :**
- `canonical/ingestion/ingestion_profiles.yaml`
- `canonical/matching/domain_matching_rules.yaml`
- `canonical/scoring/scoring_rules.yaml`
- `canonical/scopes/*.yaml`

**Client Config :**
- `client-config-examples/lai_weekly.yaml`

### 5.3 Documents de Référence

**Diagnostics récents :**
- `docs/diagnostics/vectora_inbox_*_results.md`
- `docs/design/vectora_inbox_*_plan.md`

**Documentation existante :**
- `canonical/README.md`
- `canonical/*/README.md`

---

## 6. Livrables Attendus

### 6.1 Fichiers Mis à Jour

- `.q-context/vectora-inbox-overview.md` (refresh complet)
- `contracts/lambdas/vectora-inbox-ingest-normalize.md` (refresh complet)
- `contracts/lambdas/vectora-inbox-engine.md` (refresh complet)

### 6.2 Nouveaux Fichiers (Optionnels)

- `contracts/data/normalized_item_schema.md`
- `contracts/config/ingestion_profiles_specification.md`
- `contracts/config/matching_rules_specification.md`

### 6.3 Validation

- Cohérence terminologique vérifiée
- Exemples JSON testés
- Documentation alignée avec code actuel

---

**Ce plan sera exécuté phase par phase, avec validation continue pour assurer la cohérence et la qualité de la documentation mise à jour.**