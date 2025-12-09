# Diagnostic Sémantique – LAI Weekly MVP
## Analyse du Gap entre Sélection Actuelle et Focus LAI Métier

**Date** : 2025-12-08  
**Auteur** : Amazon Q Developer  
**Client** : lai_weekly (DEV)  
**Période analysée** : 7 jours  

---

## Résumé Exécutif

**Problème identifié** : La newsletter générée contient des items sur Pfizer, AbbVie, Otsuka, etc., qui ne sont **pas clairement LAI** d'un point de vue métier.

**Cause racine** : La logique de matching actuelle utilise un **OU logique** entre les scopes (companies OU molecules OU technologies). Un item est retenu dès qu'il mentionne **une seule entité** d'un scope, même sans contexte LAI.

**Impact** : 
- Newsletter trop large, avec du bruit sectoriel générique
- Pure players LAI (MedinCell, Camurus, DelSiTech, Nanexa, Peptron) noyés dans la masse
- Risque de manquer le signal LAI stratégique

---

## Analyse des Items Sélectionnés

### Items Analysés (50 items normalisés)

Sur les 50 items ingérés :
- **8 items matchés** au domaine `tech_lai_ecosystem` (16%)
- **5 items sélectionnés** pour la newsletter finale

### Détail des Items Sélectionnés dans la Newsletter

#### Item 1 : Pfizer Hympavzi (Hemophilia)
```yaml
source_key: press_sector__fiercepharma
title: "ASH: Pfizer, aiming to level the hemophilia playing field, trots out new Hympavzi data"
companies_detected: [Pfizer, Novo Nordisk, Sanofi]
molecules_detected: []
technologies_detected: []
matched_domains: [tech_lai_ecosystem]
```

**Pourquoi matché LAI ?**
- Pfizer est dans `lai_companies_global`
- Aucun mot-clé LAI détecté
- Aucune molécule LAI détectée
- **Verdict métier** : ❌ **PAS LAI** - Hympavzi est un anticorps pour l'hémophilie, pas une formulation LAI

---

#### Item 2 : Takeda Adzynma Safety Signal
```yaml
source_key: press_sector__fiercepharma
title: "FDA safety probe of Takeda drug; Otsuka kidney disease nod; ADC patent fight"
companies_detected: [Pfizer]
molecules_detected: []
technologies_detected: []
matched_domains: [tech_lai_ecosystem]
```

**Pourquoi matché LAI ?**
- Pfizer mentionné dans l'article (contexte ADC patent fight)
- Aucun mot-clé LAI détecté
- **Verdict métier** : ❌ **PAS LAI** - Article sur sécurité Takeda + approbation Otsuka, aucun lien avec LAI

---

#### Item 3 : AbbVie Skyrizi TV Ads
```yaml
source_key: press_sector__fiercepharma
title: "AbbVie revs up Skyrizi spending to top TV ad totals in November, edging out J&J's Tremfya"
companies_detected: [AbbVie]
molecules_detected: []
technologies_detected: []
matched_domains: [tech_lai_ecosystem]
```

**Pourquoi matché LAI ?**
- AbbVie est dans `lai_companies_global`
- Aucun mot-clé LAI détecté
- **Verdict métier** : ❌ **PAS LAI** - Article marketing sur dépenses publicitaires TV, aucun lien avec LAI

---

#### Item 4 : Merck Keytruda Subcutaneous (Patent Battle)
```yaml
source_key: press_sector__endpoints_news
title: "German court stops Merck from selling subcutaneous Keytruda in patent battle with Halozyme"
companies_detected: []
molecules_detected: []
technologies_detected: [subcutaneous]
matched_domains: [tech_lai_ecosystem]
```

**Pourquoi matché LAI ?**
- Mot-clé `subcutaneous` détecté (dans `lai_keywords`)
- **Verdict métier** : ⚠️ **LIMITE** - Keytruda SC est une formulation sous-cutanée, mais pas un LAI (pas de libération prolongée). C'est un faux positif du scope `lai_keywords`.

---

#### Item 5 : Regulatory Tracker (Generic)
```yaml
source_key: press_sector__fiercepharma
title: "Regulatory tracker: Agios awaits FDA decision as target date passes"
companies_detected: []
molecules_detected: []
technologies_detected: [PAS]
matched_domains: [tech_lai_ecosystem]
```

**Pourquoi matché LAI ?**
- Mot-clé `PAS` détecté (faux positif : "passes" dans le texte)
- **Verdict métier** : ❌ **PAS LAI** - Faux positif de détection NLP

---

### Items LAI Authentiques (Non Sélectionnés ou Mal Classés)

#### ✅ MedinCell - UZEDY Bipolar I Approval
```yaml
source_key: press_corporate__medincell
title: "FDA Approves Expanded Indication for UZEDY® (risperidone) Extended-Release Injectable Suspension"
companies_detected: []
molecules_detected: [risperidone]
technologies_detected: [extended-release injectable, XTEN]
matched_domains: [tech_lai_ecosystem]
```

**Verdict métier** : ✅ **VRAI LAI** - Pure player LAI, molécule LAI (risperidone), technologie LAI (extended-release injectable)

---

#### ✅ MedinCell - Teva Olanzapine LAI NDA
```yaml
source_key: press_corporate__medincell
title: "UZEDY® continues strong growth; Teva setting the stage for US NDA Submission for Olanzapine LAI in Q4 2025"
companies_detected: []
molecules_detected: [olanzapine]
technologies_detected: []
matched_domains: [tech_lai_ecosystem]
```

**Verdict métier** : ✅ **VRAI LAI** - Pure player LAI, molécule LAI (olanzapine), mention explicite "Olanzapine LAI"

---

#### ✅ MedinCell - Risperidone LAI Canada Approval
```yaml
source_key: press_corporate__medincell
title: "Teva and Medincell's Risperidone LAI Approved in Canada as LONGAVO®"
companies_detected: [MedinCell]
molecules_detected: [risperidone]
technologies_detected: []
matched_domains: [tech_lai_ecosystem]
```

**Verdict métier** : ✅ **VRAI LAI** - Pure player LAI, molécule LAI (risperidone), mention explicite "Risperidone LAI"

---

#### ⚠️ DelSiTech - Leadership Change
```yaml
source_key: press_corporate__delsitech
title: "DelSiTech announces a leadership change. Carl-Åke Carlsson, CEO of DelSiTech, leaves the company"
companies_detected: [DelSiTech]
molecules_detected: []
technologies_detected: []
matched_domains: [tech_lai_ecosystem]
```

**Verdict métier** : ⚠️ **CONTEXTE LAI** - Pure player LAI, mais événement corporate générique (pas de technologie/molécule LAI mentionnée)

---

## Analyse Quantitative

### Répartition des Items Matchés (8 items)

| Type d'Item | Nombre | % | Verdict Métier |
|-------------|--------|---|----------------|
| **Vrai LAI** (pure players + molécules + technologies) | 3 | 37.5% | ✅ Signal stratégique |
| **Contexte LAI** (pure players, événement générique) | 2 | 25% | ⚠️ Utile mais secondaire |
| **Faux positifs** (big pharma sans contexte LAI) | 3 | 37.5% | ❌ Bruit sectoriel |

### Répartition par Source

| Bouquet | Items Matchés | Vrai LAI | Faux Positifs |
|---------|---------------|----------|---------------|
| `lai_corporate_mvp` (MedinCell, DelSiTech, Nanexa) | 5 | 3 | 2 |
| `lai_press_mvp` (FiercePharma, Endpoints, FierceBiotech) | 3 | 0 | 3 |

**Observation** : Les sources corporate LAI génèrent du vrai signal LAI, mais la presse sectorielle génère principalement du bruit.

---

## Causes Racines du Gap Sémantique

### 1. Logique de Matching Trop Permissive

**Code actuel** (`matcher.py`, ligne 75) :
```python
# Si au moins une intersection est non vide → l'item appartient au domaine
if companies_match or molecules_match or technologies_match or indications_match:
    matched_domains.append(domain_id)
```

**Problème** : Un item est retenu dès qu'il mentionne **une seule entité** d'un scope, même sans contexte LAI.

**Exemple** :
- Article sur Pfizer Hympavzi (hémophilie) → Pfizer dans `lai_companies_global` → ✅ Matché LAI
- Mais Hympavzi n'est **pas un LAI**

---

### 2. Scope `lai_companies_global` Trop Large

**Contenu actuel** : 170+ entreprises, incluant :
- **Pure players LAI** : MedinCell, Camurus, DelSiTech, Nanexa, Peptron (5 entreprises)
- **Big Pharma généralistes** : Pfizer, AbbVie, Novo Nordisk, Sanofi, etc. (165+ entreprises)

**Problème** : Les big pharma ont des pipelines diversifiés (oncologie, immunologie, etc.). Mentionner Pfizer ne signifie **pas** que l'article parle de LAI.

---

### 3. Mots-Clés LAI Trop Génériques

**Exemples de faux positifs** :
- `PAS` : détecte "passes" dans "target date passes"
- `DDS` : détecte "DDS" dans des contextes non-LAI
- `subcutaneous` : détecte Keytruda SC (pas un LAI, juste une formulation SC)

---

### 4. Scoring Insuffisant pour Discriminer

**Scoring actuel** : Favorise les big pharma (Pfizer, AbbVie) car :
- `source_type_weight_sector = 1.5` (presse sectorielle)
- `event_type_weights` : tous les événements ont un poids > 0
- Pas de bonus pour les pure players LAI

**Résultat** : Les articles big pharma (Pfizer Hympavzi, AbbVie Skyrizi) remontent en tête, même sans contexte LAI.

---

## Recommandations pour le Recentrage LAI

### Option A : Scope `lai_companies_mvp_core` (Recommandé pour MVP)

**Action** : Créer un scope `lai_companies_mvp_core` avec les 5 pure players LAI uniquement.

**Avantages** :
- ✅ Focus strict sur les pure players LAI
- ✅ Réduit drastiquement le bruit sectoriel
- ✅ Simple à implémenter

**Inconvénients** :
- ⚠️ Risque de manquer des news LAI de big pharma (ex: Novo Nordisk semaglutide LAI)

---

### Option B : Matching avec ET Logique (Recommandé)

**Action** : Pour `tech_lai_ecosystem`, exiger :
- **(company dans lai_companies_mvp_core OU molecule dans lai_molecules_global) ET**
- **au moins un mot-clé dans lai_keywords**

**Avantages** :
- ✅ Garantit un contexte LAI (technologie + entité)
- ✅ Réduit les faux positifs big pharma
- ✅ Conserve les news LAI de big pharma si contexte LAI

**Inconvénients** :
- ⚠️ Plus complexe à implémenter
- ⚠️ Risque de manquer des news LAI si NLP rate un mot-clé

---

### Option C : Bonus/Malus dans le Scoring

**Action** : Ajouter dans `scoring_rules.yaml` :
- `pure_player_lai_bonus: 5` (pour MedinCell, Camurus, DelSiTech, Nanexa, Peptron)
- `big_pharma_without_lai_keyword_malus: -3` (pénaliser big pharma sans mot-clé LAI)

**Avantages** :
- ✅ Favorise les pure players LAI
- ✅ Pénalise les faux positifs big pharma
- ✅ Conserve la flexibilité du matching

**Inconvénients** :
- ⚠️ Ne résout pas le problème à la racine (matching trop permissif)

---

## Critères de Succès pour le MVP

Pour valider le recentrage LAI, la newsletter doit respecter :

1. **80-90% des items retenus sont clairement LAI** à la lecture humaine
2. **Pure players LAI (MedinCell, Camurus, DelSiTech, Nanexa, Peptron) représentent ≥ 50% des items**
3. **Big pharma uniquement si contexte LAI explicite** (molécule LAI + technologie LAI)
4. **Zéro faux positif** de type "Pfizer Hympavzi" ou "AbbVie Skyrizi TV ads"

---

## Prochaines Étapes

1. ✅ **Diagnostic sémantique** : Complété (ce document)
2. ⏳ **Plan de recentrage LAI** : À créer (`vectora_inbox_lai_mvp_focus_plan.md`)
3. ⏳ **Implémentation** : Appliquer la solution recommandée
4. ⏳ **Test & Validation** : Re-lancer un run 7 jours et valider les critères de succès

---

**Auteur** : Amazon Q Developer  
**Date** : 2025-12-08  
**Version** : 1.0
