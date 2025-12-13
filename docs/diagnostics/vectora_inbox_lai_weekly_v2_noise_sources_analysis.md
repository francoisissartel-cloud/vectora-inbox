# Vectora Inbox LAI Weekly v2 - Analyse des Sources de Bruit

**Date** : 2025-12-11  
**Newsletter analysée** : Run #2 lai_weekly_v2  
**Objectif** : Cartographier les types de bruit et identifier les leviers d'amélioration

---

## Vue d'ensemble du bruit

**Newsletter actuelle** : 4/5 items sont du bruit (80%)
- 2x DelSiTech HR (recrutement)
- 1x DelSiTech Corporate (changement CEO)
- 1x MedinCell Finance (résultats financiers)
- 1x MedinCell LAI authentique ✅

**Problème** : Le pipeline privilégie les pure players même sans contenu LAI.

---

## Classification détaillée du bruit

### 1. HR / Recrutement (40% du bruit)

**Items identifiés** :
- "DelSiTech is Hiring a Process Engineer"
- "DelSiTech Seeks an Experienced Quality Director"

**Caractéristiques** :
- **Termes typiques** : "hiring", "seeks", "recruiting", "job opening"
- **Source** : Pure players LAI (DelSiTech)
- **Valeur LAI** : 0% (aucun signal technique)
- **Fréquence** : Élevée (pure players recrutent régulièrement)

**Analyse pipeline** :
- **Ingestion** : ✅ Passent les filtres (source corporate pure player)
- **Normalisation** : ✅ Company détectée (DelSiTech)
- **Matching** : ✅ Matché sur company seule (pure player bonus)
- **Scoring** : ✅ Score artificiel via pure_player_bonus (5.0)

**Défaillances identifiées** :
1. **exclusion_scopes.yaml** : Pas de filtrage HR
2. **ingestion_profiles** : technology_complex trop permissif pour pure players
3. **scoring_rules** : pure_player_bonus trop élevé (compense absence signaux LAI)

---

### 2. Finance / Résultats (20% du bruit)

**Items identifiés** :
- "Medincell Publishes its Consolidated Half-Year Financial Results"

**Caractéristiques** :
- **Termes typiques** : "financial results", "earnings", "consolidated results", "interim report"
- **Source** : Pure players LAI (MedinCell)
- **Valeur LAI** : 5% (contexte business pure player)
- **Fréquence** : Trimestrielle/semestrielle

**Analyse pipeline** :
- **Ingestion** : ✅ Passent les filtres (source corporate pure player)
- **Normalisation** : ✅ Company détectée (MedinCell)
- **Matching** : ✅ Matché sur company seule
- **Scoring** : ✅ Score artificiel via pure_player_bonus

**Défaillances identifiées** :
1. **exclusion_scopes.yaml** : Pas de filtrage finance
2. **scoring_rules** : Pas de malus pour contenu purement financier

---

### 3. Corporate Générique (20% du bruit)

**Items identifiés** :
- "DelSiTech announces a leadership change. Carl-Åke Carlsson, CEO of DelSiTech, leaves the company..."

**Caractéristiques** :
- **Termes typiques** : "leadership change", "CEO", "appointment", "board"
- **Source** : Pure players LAI
- **Valeur LAI** : 10% (impact potentiel sur stratégie)
- **Fréquence** : Occasionnelle mais significative

**Analyse pipeline** :
- **Ingestion** : ✅ Passent les filtres
- **Normalisation** : ✅ Company détectée
- **Matching** : ✅ Matché sur company
- **Scoring** : ✅ Score via pure_player_bonus

**Défaillances identifiées** :
1. **Scoring contextuel** : Pas de différenciation leadership vs HR
2. **Event_type detection** : "other" générique au lieu de "corporate"

---

### 4. ESG / Sustainability (0% observé mais potentiel)

**Items identifiés** : Aucun dans ce run, mais risque futur

**Caractéristiques potentielles** :
- **Termes typiques** : "sustainability", "ESG", "carbon neutral", "green"
- **Source** : Toutes companies
- **Valeur LAI** : 0-5%
- **Fréquence** : Croissante

**Défaillances anticipées** :
1. **exclusion_scopes.yaml** : Pas de filtrage ESG
2. **Scoring** : Risque de bonus company sans signaux LAI

---

## Analyse des défaillances par couche

### 1. Ingestion - Profils trop permissifs

**Profil technology_complex** :
```yaml
# Hypothèse de configuration actuelle
technology_complex:
  include_corporate: true
  include_pure_players: true  # Trop permissif
  exclude_hr: false          # Manquant
  exclude_finance: false     # Manquant
```

**Problème** : Pure players ingérés sans discrimination de contenu.

**Impact** : 100% des items corporate pure players passent, même HR/finance.

---

### 2. Normalisation - Détection insuffisante

**Bedrock LLM Gating** :
- ✅ **Companies** : Bien détectées
- ❌ **Content type** : HR/Finance non identifiés explicitement
- ❌ **Relevance scoring** : Pas de score de pertinence LAI

**Problème** : Le LLM ne catégorise pas le type de contenu (HR vs technique).

**Impact** : Tous les items pure players semblent équivalents post-normalisation.

---

### 3. Matching - Règles trop permissives

**Règles actuelles (hypothèse)** :
```yaml
tech_lai_ecosystem:
  company_in_scope: lai_companies_global  # Suffisant pour pure players
  technology_required: false              # Problème
  molecule_required: false                # Problème
  minimum_signals: 1                      # Trop faible
```

**Problème** : Company seule suffit pour matcher les pure players.

**Impact** : DelSiTech HR matche aussi facilement que MedinCell NDA.

---

### 4. Scoring - Bonus déséquilibrés

**Poids actuels (hypothèse)** :
```yaml
pure_player_bonus: 5.0      # Trop élevé
technology_bonus: 2.0       # Trop faible relativement
molecule_bonus: 3.0         # Trop faible relativement
partnership_bonus: 1.5     # Trop faible
```

**Problème** : pure_player_bonus compense l'absence totale de signaux LAI.

**Impact** : DelSiTech HR (company seule) score plus haut que news sectorielles avec signaux LAI partiels.

---

## Cartographie des leviers d'amélioration

### Niveau 1 : Configuration seule (P0)

**exclusion_scopes.yaml** :
```yaml
hr_recruitment_exclusions:
  - "hiring"
  - "seeks"
  - "recruiting"
  - "job opening"
  - "career"
  - "position available"

financial_reporting_exclusions:
  - "financial results"
  - "earnings"
  - "consolidated results"
  - "interim report"
  - "quarterly results"
  - "revenue"

corporate_generic_exclusions:
  - "leadership change"
  - "CEO departure"
  - "board appointment"
  - "organizational restructuring"
```

**scoring_rules.yaml** :
```yaml
pure_player_bonus: 2.0      # Réduit de 5.0 à 2.0
technology_bonus: 3.0       # Augmenté
molecule_bonus: 4.0         # Augmenté
partnership_bonus: 3.0     # Augmenté
content_type_malus:
  hr: -2.0                  # Nouveau
  finance: -1.0             # Nouveau
  corporate: -0.5           # Nouveau
```

**Bénéfice attendu** : Réduction 60-80% du bruit HR/finance.

---

### Niveau 2 : Prompts LLM (P1)

**Amélioration Bedrock normalization** :
```
Classify content type:
- technical: R&D, clinical, regulatory, partnerships
- hr: recruitment, hiring, personnel
- finance: earnings, results, revenue
- corporate: leadership, governance, awards

Score LAI relevance (0-10):
- 8-10: Direct LAI technology/molecules
- 5-7: LAI companies with technical content
- 2-4: LAI companies with corporate content
- 0-1: Pure HR/finance/generic
```

**Bénéfice attendu** : Détection explicite du type de contenu + score de pertinence.

---

### Niveau 3 : Code / Matching (P1)

**Matching rules enhancement** :
```python
def enhanced_matching(item):
    if item.company_in_scope:
        if item.is_pure_player:
            # Pure players need at least 1 LAI signal
            return (item.technology_detected or 
                   item.molecule_detected or 
                   item.trademark_detected or
                   item.lai_relevance_score >= 6)
        else:
            # Hybrid companies more flexible
            return item.lai_relevance_score >= 4
    return False
```

**Bénéfice attendu** : Matching discriminant basé sur contenu réel.

---

### Niveau 4 : Enrichissement automatique (P2)

**Auto-enhancement des scopes** :
- Détection automatique nouveaux termes LAI
- Learning des patterns HR/finance
- Adaptation dynamique aux pure players

**Bénéfice attendu** : Réduction continue du bruit sans maintenance manuelle.

---

## Priorisation des corrections

### P0 - Impact immédiat (config seule)
1. **exclusion_scopes.yaml** : Filtrer HR/finance
2. **scoring_rules.yaml** : Réduire pure_player_bonus
3. **Test run #3** : Validation immédiate

**Effort** : 1 heure  
**Impact** : -60% bruit  
**Risque** : Faible

### P1 - Impact structurel (prompts + code)
1. **Bedrock prompt** : Content type + relevance scoring
2. **Matching rules** : Exiger signaux LAI pour pure players
3. **Test run #4** : Validation complète

**Effort** : 1 jour  
**Impact** : -80% bruit  
**Risque** : Moyen

### P2 - Impact évolutif (ML/auto)
1. **Auto-learning** : Patterns bruit/signal
2. **Dynamic scopes** : Adaptation continue
3. **Monitoring** : Alertes qualité

**Effort** : 1 semaine  
**Impact** : -90% bruit  
**Risque** : Élevé

---

## Métriques de succès

### Objectifs quantitatifs
- **Bruit HR** : 0% (actuellement 40%)
- **Bruit Finance** : <10% (actuellement 20%)
- **Bruit Corporate** : <20% (actuellement 20%)
- **Signaux LAI authentiques** : >60% (actuellement 20%)

### Objectifs qualitatifs
- Newsletter utilisable pour veille LAI
- Signaux majeurs (Nanexa/Moderna) présents
- Équilibre pure players vs hybrid companies
- Cohérence temporelle (pas de régression)

---

## Conclusion

**Diagnostic principal** : Le bruit provient d'un **déséquilibre scoring** favorisant les pure players sans discrimination de contenu.

**Cause racine** : Configuration trop permissive (exclusions faibles + bonus pure_player élevé + matching non discriminant).

**Solution prioritaire** : Corrections P0 (config) pour impact immédiat, puis P1 (prompts) pour robustesse.

**Validation** : Run #3 avec corrections P0 devrait produire newsletter avec <30% bruit et signaux LAI majeurs présents.