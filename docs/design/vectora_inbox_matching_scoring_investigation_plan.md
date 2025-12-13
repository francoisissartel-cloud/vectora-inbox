# Vectora Inbox - Plan d'Investigation Matching & Scoring

**Date** : 2025-12-12  
**Objectif** : Diagnostic approfondi des problèmes de matching (matched_domains vide) et scoring (pas de sélection cohérente)  
**Statut** : ✅ **INVESTIGATION TERMINÉE**

---

## Contexte

**Problème identifié** :
- Phase engine (matching + scoring) cassée
- `matched_domains` vide pour tous les items
- Pas de scores significatifs → newsletter vide/faible
- La partie newsletter fonctionne techniquement mais n'a pas de contenu pertinent à traiter

**Contraintes** :
- ✅ Diagnostic uniquement (pas de corrections dans cette passe)
- ✅ Création de scripts de debug et fichiers de diagnostic autorisée
- ❌ Pas de modification des règles métier, canonical, ou logique core matcher/scorer
- ❌ Pas de redéploiement Lambda avec logique modifiée

---

## Phase 0 – Lecture du Contexte

**Objectif** : Comprendre l'état attendu vs réel du système

### 0.1 Documents à relire
- [ ] `vectora_inbox_lai_weekly_v2_human_feedback_analysis_and_improvement_plan.md`
- [ ] `vectora_inbox_lai_weekly_v3_p0_executive_summary.md`
- [ ] `vectora_inbox_lai_weekly_v3_p0_validation_executive_summary.md`
- [ ] Derniers diagnostics E2E lai_weekly_v3 (ingestion/normalisation/newsletter)

### 0.2 Items gold de référence
- Nanexa/Moderna (PharmaShell®)
- UZEDY® / Teva / MedinCell (regulatory / extension)
- MedinCell malaria grant
- DelSiTech HR / MedinCell finance (bruit à exclure)

**Statut Phase 0** : ✅ **TERMINÉ**

### 0.3 Synthèse Phase 0
**Documents analysés** :
- ✅ Plan d'amélioration v2 → v3 : Corrections P0 identifiées (Bedrock tech detection, exclusions HR/finance, HTML extraction)
- ✅ Executive summary v3 P0 : Corrections implémentées mais validation bloquée par throttling Bedrock
- ✅ Validation executive summary : Blocage technique critique empêche validation complète
- ✅ Item traces v3 : Diagnostic détaillé des échecs de matching/scoring
- ✅ Human review sheet v2 : Items gold de référence et patterns de désaccord

**Constats clés** :
- Les corrections P0 sont **techniquement implémentées** mais **non validées** en conditions réelles
- **Problème principal identifié** : Bedrock ne détecte pas les technologies LAI malgré leur présence dans les scopes
- **Items gold perdus** : Nanexa/Moderna (normalisation), UZEDY (matching), MedinCell malaria (matching)
- **Bruit présent** : DelSiTech HR, MedinCell finance (exclusions non appliquées)
- **Cause racine suspectée** : Problème d'implémentation runtime, pas de configuration

---

## Phase 1 – Analyse Statique du Code et des Règles

**Objectif** : Cartographier précisément le pipeline matching/scoring

### 1.1 Identification des modules clés
- [ ] Localiser le code de matching (domain_matcher, matcher.py, etc.)
- [ ] Localiser le code de scoring (scorer.py ou équivalent)
- [ ] Comprendre le workflow entre les 2 lambdas :
  - `vectora-inbox-ingest-normalize-dev`
  - `vectora-inbox-engine-dev`

### 1.2 Analyse des fichiers de configuration
- [ ] `domain_matching_rules.yaml` - règles de matching
- [ ] `scoring_rules.yaml` - règles de scoring
- [ ] `client-config-examples/lai_weekly_v3.yaml` - config client
- [ ] Nouveaux champs : `lai_relevance`, `trademark_privileges`, etc.

### 1.3 Points d'élimination des items
Identifier tous les endroits où un item peut être filtré/éliminé :
- [ ] Items normalisés → Items matchés
- [ ] Items matchés → Items scorés
- [ ] Items scorés → Items sélectionnés pour newsletter

**Livrables Phase 1** :
- Cartographie complète du pipeline
- Liste des points de filtrage
- Identification des configurations utilisées

**Statut Phase 1** : ✅ **TERMINÉ**

### 1.4 Synthèse Phase 1
**Modules clés identifiés** :
- ✅ **Matching** : `src/vectora_core/matching/matcher.py` - Logique d'intersection d'ensembles avec support technology profiles
- ✅ **Scoring** : `src/vectora_core/scoring/scorer.py` - Calcul scores avec facteurs multiples (event_type, récence, pure_player_bonus)
- ✅ **Workflow** : `src/vectora_core/__init__.py` - Orchestration avec Phase 2.5 (exclusions) entre normalisation et matching
- ✅ **Exclusions** : `src/lambdas/engine/exclusion_filter.py` - Filtrage HR/finance avant matching

**Workflow entre lambdas** :
1. **ingest-normalize** : Ingestion → Normalisation (Bedrock) → Écriture S3
2. **engine** : Lecture S3 → **Phase 2.5 Exclusions** → Phase 2 Matching → Phase 3 Scoring → Phase 4 Newsletter

**Configurations clés** :
- ✅ `domain_matching_rules.yaml` : Règles par type de domaine + technology_profiles (technology_complex)
- ✅ `scoring_rules.yaml` : Poids event_type, pure_player_bonus (1.5), seuils (min_score: 5)
- ✅ `lai_weekly_v3.yaml` : Config client avec watch_domains, trademark_privileges, scoring overrides
- ✅ `technology_scopes.yaml` : Scope lai_keywords avec profile technology_complex + catégories
- ✅ `exclusion_scopes.yaml` : Termes HR/finance pour filtrage

**Points d'élimination identifiés** :
1. **Normalisation** : Summary vide → Pas d'entités détectées
2. **Phase 2.5** : Exclusions HR/finance (exclusion_filter.py)
3. **Matching** : Pas de technology détectée → Pas de match domain tech_lai_ecosystem
4. **Scoring** : Score < min_score (5) → Pas de sélection newsletter

**Nouveaux champs identifiés** :
- `lai_relevance_score`, `anti_lai_detected`, `pure_player_context` : Champs Bedrock pour matching contextuel
- `domain_relevance` : Nouveau système d'évaluation Bedrock par domaine
- `matched_domains`, `matching_details` : Résultats du matching avec confidence
- `trademark_privileges` : Traitement privilégié des marques LAI

---

## Phase 2 – Analyse sur Données Réelles

**Objectif** : Tester la logique matching/scoring sur des données réelles en local

### 2.1 Préparation des données de test
- [ ] Récupérer les derniers fichiers d'items normalisés pour `lai_weekly_v3`
- [ ] Si v3 indisponible, utiliser `lai_weekly_v2`
- [ ] Identifier les items gold dans les données

### 2.2 Script de debug local
- [ ] Créer `scripts/debug_matching_scoring_lai_weekly_v3.py`
- [ ] Exécuter localement la logique matching + scoring (hors Lambda)
- [ ] Pour chaque item, produire :
  - `source_key`, `title`, `date`
  - `matched_domains` (liste)
  - `matching_signals` (si disponible)
  - `score_final` (ou score brut)

### 2.3 Focus sur items gold
Analyser spécifiquement :
- [ ] Nanexa/Moderna (PharmaShell®)
- [ ] UZEDY® / Teva / MedinCell (regulatory / extension)
- [ ] MedinCell malaria grant
- [ ] DelSiTech HR / MedinCell finance (bruit à exclure)

**Livrables Phase 2** :
- Script de debug fonctionnel
- Résultats détaillés pour chaque item gold
- Identification des items qui "tombent" et où

**Statut Phase 2** : ✅ **TERMINÉ**

### 2.4 Synthèse Phase 2
**Script de debug créé** : `scripts/debug_matching_scoring_lai_weekly_v3.py`

**Données analysées** : 104 items normalisés lai_weekly_v3_latest.json

**Résultats items gold** :
- ✅ **Nanexa/Moderna** : Trouvé, summary VIDE (0 chars), signaux LAI présents ("pharmashell"), technologies_detected = []
- ✅ **UZEDY Bipolar** : Trouvé, summary OK (200 chars), signaux LAI multiples, technologies_detected = []
- ✅ **UZEDY Growth** : Trouvé, summary OK (200 chars), signaux LAI multiples, technologies_detected = []
- ✅ **MedinCell Malaria** : Trouvé, summary OK (200 chars), pas de signaux LAI explicites, technologies_detected = []
- ❌ **MedinCell Olanzapine** : Non trouvé dans les données

**Statistiques critiques** :
- Total items : 104
- Items avec summary : 85 (81.7%)
- Items avec companies : 38 (36.5%)
- **Items avec technologies : 0 (0.0%)** ← PROBLÈME CRITIQUE
- Items avec matched_domains : 5 (4.8%)

**Test matching local** : 5/20 items matchés (malgré technologies_detected vides)

**Statut Phase 3** : ✅ **TERMINÉ**

### 3.3 Synthèse Phase 3
**Comparaison Plan vs Réalité** :

| **Élément du Plan** | **Implémenté** | **Utilisé** | **Problème** |
|-------------------|--------------|------------|---------------|
| Bonus/malus pure players | ✅ Oui | ✅ Oui | Fonctionne |
| Poids des trademarks | ✅ Oui | ❌ Non | **Trademarks non détectées** |
| Exclusions HR/finance | ✅ Oui | ✅ Oui | Fonctionne |
| Gating par lai_relevance | ✅ Oui | ❌ Non | **Champs Bedrock manquants** |
| Technology detection | ✅ Oui | ❌ Non | **Bedrock ne détecte rien** |
| Matching contextuel | ✅ Oui | ❌ Non | **Dépend des technologies** |

**Causes racines identifiées** :
1. **Bedrock ne détecte aucune technology** malgré signaux présents ("extended-release injectable", "UZEDY", "PharmaShell")
2. **Champs lai_relevance, anti_lai_detected, pure_player_context = null** (pas implémentés dans normalisation)
3. **Trademarks non détectées** (UZEDY®, PharmaShell® présents mais trademarks_detected = [])
4. **Summary vide pour Nanexa/Moderna** (problème extraction HTML)

**Statut Phase 4** : ✅ **TERMINÉ**

### 4.4 Synthèse Phase 4
**Rapport de diagnostic créé** : `docs/diagnostics/vectora_inbox_matching_scoring_investigation_results.md`

**Analyse par type d'item** :

| **Item Gold** | **Normalisé** | **Matché** | **Sélectionné** | **Cause d'échec** |
|---------------|---------------|------------|-------------------|-------------------|
| Nanexa/Moderna | ❌ Non (summary vide) | ❌ Non | ❌ Non | **Extraction HTML + Bedrock** |
| UZEDY Bipolar | ✅ Oui | ❌ Non | ❌ Non | **Bedrock ne détecte pas technologies** |
| UZEDY Growth | ✅ Oui | ❌ Non | ❌ Non | **Bedrock ne détecte pas technologies** |
| MedinCell Malaria | ✅ Oui | ❌ Non | ❌ Non | **Matching contextuel non actif** |

**Hypothèses P0 confirmées** :
1. 🔴 **Bedrock ne détecte aucune technology** (0/104 items) malgré signaux présents
2. 🔴 **Champs lai_relevance, anti_lai_detected, pure_player_context = null** (non implémentés)
3. 🟡 **Extraction HTML partielle** (Nanexa summary vide)

**Points de correction identifiés** :
- `src/vectora_core/normalization/bedrock_client.py` : Fix prompt technology section
- `src/vectora_core/normalization/normalizer.py` : Implémenter champs LAI manquants
- `src/vectora_core/ingestion/html_extractor_robust.py` : Améliorer fallback Nanexa
- `src/vectora_core/matching/matcher.py` : Activer matching contextuel

---

## Phase 3 – Comparaison "Plan vs Réalité" Côté Code

**Objectif** : Comparer l'implémentation réelle avec le plan d'amélioration

### 3.1 Éléments du plan à vérifier
- [ ] Bonus/malus pure players - implémenté ?
- [ ] Poids des trademarks - utilisé ?
- [ ] Exclusions HR/finance - fonctionnelles ?
- [ ] Gating par `lai_relevance` - actif ?

### 3.2 Analyse des écarts
Identifier :
- [ ] Ce qui est implémenté mais non utilisé
- [ ] Ce qui est utilisé mais trop strict (seuils > scores observés)
- [ ] Ce qui a été cassé/oublié lors des refactors récents

### 3.3 Analyse des seuils et paramètres
- [ ] Seuils de matching trop élevés ?
- [ ] Seuils de scoring trop restrictifs ?
- [ ] Paramètres de configuration incorrects ?

**Livrables Phase 3** :
- Tableau comparatif Plan vs Implémentation
- Liste des écarts critiques
- Hypothèses sur les causes racines

**Statut Phase 3** : ⏳ En attente Phase 2

---

## Phase 4 – Rapport de Diagnostic Détaillé

**Objectif** : Produire un diagnostic clair et actionnable

### 4.1 Analyse par type d'item
Pour chaque item clé (gold vs bruit) :
- [ ] Est-il bien normalisé ? (oui/non, pourquoi)
- [ ] Est-il bien matché ? (oui/non, pourquoi)
- [ ] Est-il bien scoré et sélectionné ? (oui/non, pourquoi)

### 4.2 Hypothèses P0
Identifier les 2-3 hypothèses les plus probables :
- [ ] Pourquoi `matched_domains` est vide
- [ ] Pourquoi les scores sont à zéro/en-dessous des seuils

### 4.3 Points de correction
Lister les points précis du code à corriger (sans les modifier) :
- [ ] Modules à patcher
- [ ] Configurations à ajuster
- [ ] Seuils à revoir

**Livrables Phase 4** :
- `docs/diagnostics/vectora_inbox_matching_scoring_investigation_results.md`
- Résumé exécutif avec causes racines
- Plan P0 "runtime fix" pour la suite

**Statut Phase 4** : ⏳ En attente Phase 3

---

## Suivi d'Exécution

| Phase | Statut | Date Début | Date Fin | Commentaires |
|-------|--------|------------|----------|--------------|
| Phase 0 | ⏳ Planifié | - | - | Lecture contexte |
| Phase 1 | ⏳ En attente | - | - | Analyse statique |
| Phase 2 | ⏳ En attente | - | - | Tests locaux |
| Phase 3 | ⏳ En attente | - | - | Plan vs Réalité |
| Phase 4 | ⏳ En attente | - | - | Rapport final |

---

**Prochaine étape** : Démarrage Phase 0 - Lecture du contexte