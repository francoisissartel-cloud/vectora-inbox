# Vectora Inbox LAI Weekly v2 - Analyse Qualitative Newsletter Run #2

**Date** : 2025-12-11  
**Newsletter analysée** : newsletter (2).md (Run #2)  
**Objectif** : Comprendre pourquoi la newsletter contient du bruit (HR, finance) au lieu de vrais signaux LAI

---

## Vue d'ensemble de la newsletter

**5 items dans la newsletter** :
1. MedinCell/Teva - Olanzapine NDA submission (LAI authentique)
2. DelSiTech - Process Engineer hiring (HR)
3. DelSiTech - Quality Director hiring (HR) 
4. DelSiTech - Leadership change (Corporate)
5. MedinCell - Financial results (Finance)

**Problème identifié** : 4/5 items sont du bruit (HR/finance/corporate), seul 1/5 est un vrai signal LAI.

---

## Analyse détaillée par item

### Item #1 : MedinCell/Teva Olanzapine NDA ✅ LAI-STRONG

**Titre** : "Medincell's Partner Teva Pharmaceuticals Announces the New Drug Application Submission to U.S. FDA for Olanzapine Extended-Release Injectable Suspension (TEV-'749 / mdc-TJK) for the Once-Monthly Treatment of Schizophrenia in Adults"

**Source** : press_corporate__medincell  
**URL** : https://www.medincell.com/wp-content/uploads/2025/12/MDC_Olanzapine-NDA-filing_09122025_EN_vf-2.pdf

**Analyse métier** :
- ✅ **LAI authentique** : Olanzapine extended-release injectable, once-monthly
- ✅ **Regulatory milestone** : NDA submission FDA
- ✅ **Pure player LAI** : MedinCell technology platform
- ✅ **Partnership Big Pharma** : Teva comme partenaire commercial

**Détection pipeline** :
- **Company** : MedinCell ✅ (pure player LAI)
- **Molecule** : olanzapine ✅ (LAI molecule)
- **Technology** : Probablement détecté (extended-release injectable)
- **Matching** : Réussi sur tech_lai_ecosystem
- **Scoring** : Score élevé (pure player + molecule + regulatory)

**Note métier** : **LAI-STRONG** - Signal parfait pour la newsletter LAI

---

### Item #2 : DelSiTech Process Engineer ❌ À EXCLURE

**Titre** : "DelSiTech is Hiring a Process Engineer"

**Source** : press_corporate__delsitech  
**URL** : https://www.delsitech.com/delsitech-is-hiring-a-process-engineer/

**Analyse métier** :
- ❌ **Pure HR** : Annonce de recrutement sans contenu technique
- ❌ **Aucun signal LAI** : Pas de mention technologie, molécule, partenariat
- ❌ **Bruit corporate** : Information RH sans valeur pour veille LAI

**Détection pipeline** :
- **Company** : DelSiTech ✅ (pure player LAI)
- **Molecule** : Aucune ❌
- **Technology** : Aucune ❌
- **Matching** : Probablement matché uniquement sur company (pure player)
- **Scoring** : Score artificiel via bonus pure_player (5.0)

**Problème identifié** : Les **exclusion_scopes** ne filtrent pas assez les annonces HR des pure players.

**Note métier** : **À EXCLURE** - Bruit RH sans valeur LAI

---

### Item #3 : DelSiTech Quality Director ❌ À EXCLURE

**Titre** : "DelSiTech Seeks an Experienced Quality Director"

**Source** : press_corporate__delsitech  
**URL** : https://www.delsitech.com/delsitech-seeks-an-experienced-quality-director/

**Analyse métier** :
- ❌ **Pure HR** : Annonce de recrutement sans contenu technique
- ❌ **Aucun signal LAI** : Pas de mention technologie, molécule, partenariat
- ❌ **Bruit corporate** : Information RH sans valeur pour veille LAI

**Détection pipeline** :
- **Company** : DelSiTech ✅ (pure player LAI)
- **Molecule** : Aucune ❌
- **Technology** : Aucune ❌
- **Matching** : Probablement matché uniquement sur company (pure player)
- **Scoring** : Score artificiel via bonus pure_player (5.0)

**Problème identifié** : Même problème que l'item #2 - exclusions HR insuffisantes.

**Note métier** : **À EXCLURE** - Bruit RH sans valeur LAI

---

### Item #4 : DelSiTech Leadership Change ❌ NON-LAI MAIS CORPORATE UTILE

**Titre** : "DelSiTech announces a leadership change. Carl-Åke Carlsson, CEO of DelSiTech, leaves the company and the Board nominates Martti Hedman as Interim CEO."

**Source** : press_corporate__delsitech  
**URL** : https://www.delsitech.com/delsitech-announces-a-leadership-change-carl-ake-carlsson-ceo-of-delsitech-leaves-the-company-and-the-board-nominates-martti-hedman-as-interim-ceo/

**Analyse métier** :
- ⚠️ **Corporate significatif** : Changement de CEO peut impacter stratégie
- ❌ **Pas de signal LAI direct** : Aucune mention technologie/pipeline
- ⚠️ **Valeur contextuelle** : Utile pour comprendre évolution pure player

**Détection pipeline** :
- **Company** : DelSiTech ✅ (pure player LAI)
- **Molecule** : Aucune ❌
- **Technology** : Aucune ❌
- **Matching** : Matché sur company uniquement
- **Scoring** : Score via bonus pure_player (5.0)

**Problème identifié** : Les **scoring rules** donnent trop de poids aux pure players même sans contenu LAI.

**Note métier** : **NON-LAI MAIS CORPORATE UTILE** - Peut être gardé en section "Corporate Updates" mais pas en top signals

---

### Item #5 : MedinCell Financial Results ❌ NON-LAI MAIS CORPORATE UTILE

**Titre** : "Medincell Publishes its Consolidated Half-Year Financial Results (April 1st , 2025 – September 30, 2025)"

**Source** : press_corporate__medincell  
**URL** : https://www.medincell.com/wp-content/uploads/2025/12/MDC_HY-Results-EN_09122025-1.pdf

**Analyse métier** :
- ❌ **Pure finance** : Résultats financiers sans contenu technique
- ❌ **Aucun signal LAI** : Pas de mention pipeline, partenariats, regulatory
- ⚠️ **Valeur contextuelle** : Performance financière pure player LAI

**Détection pipeline** :
- **Company** : MedinCell ✅ (pure player LAI)
- **Molecule** : Aucune ❌
- **Technology** : Aucune ❌
- **Matching** : Matché sur company uniquement
- **Scoring** : Score via bonus pure_player (5.0)

**Problème identifié** : Les **exclusion_scopes** ne filtrent pas assez les annonces financières des pure players.

**Note métier** : **NON-LAI MAIS CORPORATE UTILE** - Peut être gardé en section "Financial Updates" mais pas en top signals

---

## Analyse des causes du bruit

### 1. Exclusion_scopes insuffisants

**Problème** : Les scopes d'exclusion ne filtrent pas assez le bruit HR/finance des pure players.

**Termes manquants probables** :
- HR : "hiring", "seeks", "recruiting", "job opening", "career"
- Finance : "financial results", "earnings", "revenue", "consolidated results"

### 2. Scoring rules trop favorables aux pure players

**Problème** : Le bonus pure_player (5.0) est trop élevé et compense l'absence de signaux LAI.

**Logique actuelle** :
```yaml
pure_player_bonus: 5.0  # Trop élevé
```

**Impact** : Items DelSiTech/MedinCell sans contenu LAI arrivent dans le top 5.

### 3. Matching rules trop permissives

**Problème** : Les pure players matchent sur tech_lai_ecosystem même sans signaux LAI explicites.

**Hypothèse** : La règle `company_in_scope: lai_companies_global` suffit à matcher, même sans technology/molecule.

### 4. Profils d'ingestion non discriminants

**Problème** : Le profil `technology_complex` n'exclut pas assez le bruit corporate des pure players.

**Impact** : Tous les items corporate pure players sont ingérés, même HR/finance.

---

## Comparaison avec l'executive summary précédent

**Contradiction identifiée** : L'executive summary précédent mentionnait "0% faux positifs", mais l'analyse métier révèle 80% de bruit (4/5 items).

**Explication** : L'évaluation technique (matching sur companies LAI) ne correspond pas à l'évaluation métier (contenu réellement pertinent pour la veille LAI).

---

## Recommandations d'amélioration

### P0 - Corrections immédiates (config uniquement)

1. **Renforcer exclusion_scopes.yaml** :
   ```yaml
   hr_recruitment_terms:
     - "hiring"
     - "seeks"
     - "recruiting"
     - "job opening"
     - "career opportunities"
   
   financial_reporting_terms:
     - "financial results"
     - "earnings"
     - "consolidated results"
     - "interim report"
   ```

2. **Réduire bonus pure_player** :
   ```yaml
   pure_player_bonus: 2.0  # Au lieu de 5.0
   ```

3. **Ajuster seuils de matching** :
   - Exiger au moins 1 signal LAI (technology OU molecule) même pour pure players

### P1 - Améliorations structurelles

1. **Améliorer gating LLM** : Ajouter détection explicite "HR/Finance" dans le prompt Bedrock
2. **Enrichir technology_scopes** : Meilleure détection des termes LAI techniques
3. **Scoring contextuel** : Pénaliser items sans signaux LAI même pour pure players

---

## Conclusion

**Diagnostic principal** : La newsletter contient 80% de bruit car le pipeline privilégie les pure players LAI même sans contenu LAI authentique.

**Cause racine** : Configuration trop permissive (exclusions faibles + bonus pure_player élevé + matching non discriminant).

**Impact business** : Newsletter inutilisable pour veille LAI car noyée dans le bruit HR/finance.

**Solution prioritaire** : Renforcer exclusions HR/finance et réduire bonus pure_player avant le run #3.