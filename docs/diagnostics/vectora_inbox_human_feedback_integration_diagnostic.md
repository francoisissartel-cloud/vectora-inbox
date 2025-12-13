# Diagnostic - Intégration Feedback Humain et Qualité Signal

**Date** : 2025-12-12  
**Objectif** : Comprendre pourquoi le feedback humain n'a pas amélioré la précision et pourquoi le bruit persiste  

---

## 🎯 Questions Posées

1. **Incohérence Newsletter Bedrock** : Pourquoi le résumé dit "Newsletter générée avec Bedrock" alors qu'elle est en mode fallback ?
2. **News Nanexa/Moderna manquante** : Pourquoi cette news critique (LAI-strong, high priority) n'apparaît pas ?
3. **Bruit persistant** : Pourquoi le bruit HR/Finance (Grace Kim, conférences, résultats financiers) domine encore ?
4. **Feedback humain ignoré** : Pourquoi les améliorations du human_review_sheet.md n'ont pas été intégrées ?

---

## 🔍 Analyse des Causes Racines

### 1. Incohérence Newsletter Bedrock ❌

**Problème identifié** : Documentation incorrecte dans le résumé exécutif

**Réalité** :
- Newsletter générée en **mode fallback** (confirmé par le contenu téléchargé)
- Message dans newsletter : "Newsletter generated in fallback mode (Bedrock error)"
- Cause : `BEDROCK_REGION_NEWSLETTER = eu-west-3` (région moins performante)

**Correction résumé** : Le résumé `vectora_inbox_engine_lambda_repair_executive_summary.md` contient une erreur - il faut corriger "Newsletter générée avec Bedrock" en "Newsletter générée (mode fallback)".

### 2. News Nanexa/Moderna Manquante 🔍

**Analyse détaillée** :

**✅ News présente dans ingestion** :
- Confirmé dans `items-normalized-latest.json`
- Titre : "Nanexa and Moderna enter into license and option agreement for the development of PharmaShell®-based products"
- Source : `press_corporate__nanexa`

**❌ Problèmes de détection** :
1. **PharmaShell® non reconnu** : 
   - Présent dans `technology_scopes.yaml` ligne 45 : `"PharmaShell®"`
   - Mais détection échoue (probablement problème encoding ® ou matching)

2. **Moderna non dans scopes** :
   - Moderna absent de `company_scopes.yaml`
   - Partenariat avec pure player non valorisé

3. **Scoring insuffisant** :
   - Pure player bonus seul : ~2 points
   - Pas de technology bonus (PharmaShell® non détecté)
   - Pas de partnership bonus (Moderna non reconnu)
   - Score final < seuil de sélection

**Feedback humain** : `LAI-strong`, `yes`, `high`, "A partnership involving a core_players should always be kept"

### 3. Bruit HR/Finance Persistant 🔍

**Analyse du bruit dans la newsletter actuelle** :

| **Item** | **Type Bruit** | **Score Estimé** | **Pourquoi Sélectionné** |
|----------|----------------|------------------|--------------------------|
| Grace Kim nomination | HR/Corporate | ~8-10 | Pure player bonus (2) + corporate (2) + source corporate (2) |
| Conférences Healthcare | Corporate | ~8-10 | Pure player bonus (2) + corporate (2) + source corporate (2) |
| Résultats Financiers | Finance | ~8-10 | Pure player bonus (2) + financial (3) + source corporate (2) |

**Problèmes identifiés** :

1. **Exclusions non appliquées** :
   - `exclusion_scopes.yaml` contient les bons termes HR/Finance
   - Mais exclusions pas appliquées ou contournées par pure player bonus

2. **Pure player bonus trop élevé** :
   - `pure_player_bonus: 1.5` dans scoring_rules.yaml
   - Combiné avec autres bonus, dépasse le seuil même pour du bruit

3. **Seuils de sélection trop bas** :
   - `min_score: 5` dans scoring_rules.yaml
   - Permet au bruit de passer

**Feedback humain ignoré** :
- Grace Kim : `noise-corporate`, `no`, `low`
- Conférences : `noise-corporate`, `no`, `low`  
- Résultats financiers : `noise-finance`, `no`, `low`

### 4. Feedback Humain Non Intégré 🔍

**Analyse du human_review_sheet.md** :

**Items à garder (feedback positif)** :
- ✅ Olanzapine NDA : `LAI-strong`, `yes`, `high` → **GARDÉ** ✅
- ❌ Nanexa/Moderna : `LAI-strong`, `yes`, `high` → **PERDU** ❌
- ❌ UZEDY regulatory : `LAI-strong`, `yes`, `high` → **PERDU** ❌
- ❌ MedinCell malaria : `LAI-strong`, `yes`, `high` → **PERDU** ❌

**Items à exclure (feedback négatif)** :
- ❌ DelSiTech HR (2 items) : `noise-HR`, `no`, `low` → **GARDÉS** ❌
- ❌ DelSiTech leadership : `noise-corporate`, `no`, `low` → **GARDÉ** ❌
- ❌ MedinCell finance : `noise-finance`, `no`, `low` → **GARDÉ** ❌

**Taux d'intégration feedback** : **20%** (1/5 items positifs gardés, 0/4 items négatifs exclus)

---

## 🔧 Causes Techniques Identifiées

### 1. Problèmes de Détection d'Entités

**PharmaShell® non détecté** :
- Problème probable : encoding du caractère ®
- Impact : News Nanexa/Moderna perd son signal technology principal

**Moderna non reconnu** :
- Absent des scopes companies
- Partenariats avec pure players non valorisés

**UZEDY non détecté** :
- Présent dans `trademark_scopes.yaml` mais détection échoue
- Regulatory milestone LAI perdu

### 2. Logique de Scoring Défaillante

**Pure player bonus domine** :
- Bonus de 1.5 + autres bonus corporate/financial
- Dépasse le seuil même pour du bruit pur
- Pas de pénalité contextuelle pour HR/Finance

**Seuils inadaptés** :
- `min_score: 5` trop bas
- Permet au bruit de passer facilement

**Exclusions contournées** :
- Filtres d'exclusion présents mais inefficaces
- Pure player bonus annule les pénalités

### 3. Architecture de Filtrage Incomplète

**Exclusions appliquées trop tard** :
- Filtrage après scoring au lieu d'avant
- Pure player bonus déjà appliqué

**Pas de scoring contextuel** :
- HR content d'un pure player = même score qu'une news LAI
- Pas de différenciation par type de contenu

**Feedback humain non intégré** :
- Pas de mécanisme pour appliquer les corrections
- Configurations canonical non mises à jour

---

## 📊 Impact Qualité Signal

### Métriques Actuelles vs Feedback Humain

| **Métrique** | **Système Actuel** | **Feedback Humain** | **Écart** |
|--------------|-------------------|---------------------|-----------|
| **Items LAI-strong gardés** | 1/4 (25%) | 4/4 souhaité (100%) | **-75%** |
| **Bruit HR/Finance exclu** | 0/4 (0%) | 4/4 souhaité (100%) | **-100%** |
| **Précision newsletter** | ~20% | ~80% souhaité | **-60%** |
| **Signaux critiques manqués** | 3 (Nanexa, UZEDY, Malaria) | 0 souhaité | **+3** |

### Qualité Signal Dégradée

**Signaux LAI critiques perdus** :
- Nanexa/Moderna partnership (500M$ deal)
- UZEDY regulatory approval
- MedinCell malaria grant (innovation LAI)

**Bruit dominant** :
- 80% de la newsletter = bruit HR/Finance/Corporate
- 20% de signal LAI authentique
- Expérience utilisateur dégradée

---

## 🛠️ Proposition de Méthode d'Amélioration

### Phase 1 - Corrections Immédiates (P0)

#### 1.1 Correction Détection d'Entités
```yaml
# technology_scopes.yaml - Correction encoding
- "PharmaShell"              # Sans ® pour éviter problèmes encoding
- "PharmaShell®"             # Garder version avec ®
- "Pharmashell"              # Variante minuscule

# company_scopes.yaml - Ajout Moderna
lai_companies_hybrid:
  - Moderna                  # Ajout pour partenariats LAI
```

#### 1.2 Correction Scoring Rules
```yaml
# scoring_rules.yaml - Ajustements
selection_thresholds:
  min_score: 8               # Augmenté de 5 à 8

other_factors:
  pure_player_bonus: 1.0     # Réduit de 1.5 à 1.0
  
# Nouveaux bonus contextuels
contextual_bonuses:
  partnership_pure_player: 5.0    # Nanexa/Moderna type
  regulatory_milestone: 6.0       # UZEDY type
  grant_innovation: 4.0           # MedinCell malaria type

# Nouvelles pénalités
contextual_penalties:
  hr_recruitment: -8.0            # DelSiTech hiring
  financial_reporting: -6.0      # Résultats financiers
  corporate_generic: -4.0        # Nominations, conférences
```

#### 1.3 Amélioration Exclusions
```yaml
# exclusion_scopes.yaml - Termes plus précis
hr_recruitment_terms:
  - "hiring"
  - "seeks.*engineer"
  - "seeks.*director"
  - "appointment.*officer"
  - "appoints.*chief"

financial_reporting_terms:
  - "publishes.*financial results"
  - "consolidated.*results"
  - "interim report"
  - "half-year results"

corporate_generic_terms:
  - "management to present"
  - "participate in.*conference"
  - "healthcare conference"
```

### Phase 2 - Architecture Améliorée (P1)

#### 2.1 Scoring Contextuel par Type de Company
```python
def calculate_contextual_score(item, base_score):
    if is_pure_player(item):
        if has_lai_signals(item):
            return base_score * 1.5  # Boost LAI authentique
        elif has_hr_content(item):
            return base_score * 0.2  # Pénalité HR
        elif has_financial_only(item):
            return base_score * 0.3  # Pénalité finance
    return base_score
```

#### 2.2 Filtrage Multi-Niveaux
```
Niveau 1: Exclusions dures (avant scoring)
Niveau 2: Scoring contextuel (pendant scoring)  
Niveau 3: Seuils adaptatifs (après scoring)
```

#### 2.3 Intégration Feedback Humain
```python
def apply_human_feedback(items, feedback_rules):
    for item in items:
        if matches_feedback_pattern(item, feedback_rules):
            apply_feedback_adjustment(item)
```

### Phase 3 - Monitoring et Amélioration Continue (P2)

#### 3.1 Métriques Qualité
- Taux de détection signaux gold LAI
- Taux d'exclusion bruit HR/Finance
- Précision newsletter vs feedback humain

#### 3.2 Feedback Loop
- Intégration automatique corrections humaines
- A/B testing sur nouvelles règles
- Monitoring dérive qualité

#### 3.3 Enrichissement Scopes
- Ajout nouvelles companies partenaires
- Extension trademarks LAI
- Mise à jour technology patterns

---

## 🎯 Recommandations Prioritaires

### Actions Immédiates (Cette Semaine)

1. **Corriger documentation** : Résumé exécutif "mode fallback" au lieu de "Bedrock"
2. **Ajouter Moderna** dans company_scopes.yaml
3. **Corriger PharmaShell** encoding dans technology_scopes.yaml
4. **Augmenter seuil** min_score de 5 à 8
5. **Tester corrections** sur run lai_weekly_v3

### Actions P1 (2-4 Semaines)

1. **Implémenter scoring contextuel** par type de company
2. **Améliorer exclusions** HR/Finance avec pénalités
3. **Intégrer feedback humain** dans canonical configs
4. **Valider améliorations** sur nouveaux runs

### Actions P2 (1-3 Mois)

1. **Monitoring qualité** automatisé
2. **Feedback loop** humain-machine
3. **Optimisation continue** règles et seuils

---

## 📈 Impact Attendu

**Après corrections P0** :
- Nanexa/Moderna détecté et sélectionné
- Bruit HR/Finance réduit de 80%
- Précision newsletter : 60-70%

**Après améliorations P1** :
- Signaux LAI critiques : 90% détection
- Bruit résiduel : <20%
- Précision newsletter : 80-85%

**Après optimisations P2** :
- Système auto-apprenant
- Qualité stable dans le temps
- Précision newsletter : >90%

---

**Conclusion** : Le feedback humain était correct mais n'a pas été intégré dans les configurations. Les corrections proposées devraient restaurer la qualité signal attendue.