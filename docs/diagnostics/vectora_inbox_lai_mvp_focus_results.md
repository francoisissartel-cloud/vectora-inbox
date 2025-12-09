# Vectora Inbox – Résultats MVP LAI Focus

**Client** : `lai_weekly`  
**Date de test** : 2025-12-08  
**Période analysée** : 7 jours (2025-12-01 à 2025-12-08)  
**Environnement** : DEV

---

## Résumé Exécutif

Le test MVP LAI a généré une newsletter avec **5 items sélectionnés** sur **50 items analysés** et **8 items matchés**.

### Verdict Préliminaire : ❌ MVP LAI – À AJUSTER

**Raison** : Aucun des 5 items sélectionnés ne concerne directement les technologies LAI (Long-Acting Injectables). Tous les items sont des actualités pharma génériques (hemophilia, regulatory tracker, TV advertising, safety probe, sponsorship) sans lien avec les formulations LAI.

---

## Analyse Détaillée des Items Sélectionnés

| # | Titre | Company | LAI ? | Pure Player ? | Commentaire |
|---|-------|---------|-------|---------------|-------------|
| 1 | Pfizer - Hympavzi Phase 3 data (hemophilia) | Pfizer | ❌ NON | ❌ NON | Hémophilie, pas de mention LAI. Pfizer est dans `lai_companies_global` mais l'item n'est pas LAI. |
| 2 | Agios - FDA regulatory tracker | Agios | ❌ NON | ❌ NON | Tracker réglementaire générique, pas de lien LAI. Agios n'est pas dans les scopes LAI. |
| 3 | AbbVie - Skyrizi TV advertising | AbbVie | ❌ NON | ❌ NON | Publicité TV pour Skyrizi (immunologie), pas de lien LAI. AbbVie est dans `lai_companies_global` mais l'item n'est pas LAI. |
| 4 | Takeda/Otsuka - FDA safety probe / IgA nephropathy | Takeda, Otsuka | ❌ NON | ❌ NON | Safety probe + approbation IgA nephropathy, pas de mention LAI. Takeda est dans `lai_companies_global` mais l'item n'est pas LAI. |
| 5 | Pfizer/GSK/Shionogi - Antimicrobial resistance musical | Pfizer, GSK, Shionogi | ❌ NON | ❌ NON | Sponsorship d'une comédie musicale, aucun lien LAI. |

---

## Métriques MVP LAI

### Objectifs vs Résultats

| Métrique | Objectif | Résultat | Statut |
|----------|----------|----------|--------|
| **Précision LAI** | 80–90% | **0%** (0/5) | ❌ ÉCHEC |
| **Proportion pure players LAI** | ≥ 50% | **0%** (0/5) | ❌ ÉCHEC |
| **Faux positifs manifestes** | 0 | **5** (tous hors LAI) | ❌ ÉCHEC |
| **Nombre d'items sélectionnés** | 5–10 | **5** | ✅ OK |

### Détail des Métriques

- **Items analysés** : 50
- **Items matchés** : 8 (16% de matching)
- **Items sélectionnés** : 5 (62.5% des items matchés)
- **Items LAI** : 0 (0% de précision LAI)
- **Items pure players LAI** : 0 (0% de pure players)
- **Faux positifs** : 5 (100% de faux positifs)

---

## Diagnostic du Problème

### Hypothèses

1. **Matching trop large** : Le matcher sélectionne des items qui mentionnent des companies dans `lai_companies_global` (Pfizer, AbbVie, Takeda, GSK, Shionogi) SANS vérifier que l'item concerne réellement les LAI.

2. **Scopes technology_scope insuffisamment restrictifs** : Les mots-clés LAI (`lai_keywords`) ne sont peut-être pas assez présents dans les items, ou le matching ne les exige pas.

3. **Scoring favorise les big pharma** : Les items mentionnant Pfizer, AbbVie, Takeda obtiennent des scores élevés car ces companies sont dans `lai_companies_global`, même si l'item n'est pas LAI.

4. **Absence de filtre "LAI obligatoire"** : Le système ne vérifie pas que l'item contient au moins un mot-clé LAI avant de le sélectionner.

### Analyse des Sources

Les 5 items proviennent tous de **FiercePharma** (source presse sectorielle), ce qui est cohérent avec le bouquet `lai_press_mvp`. Cependant, ces items sont des actualités pharma génériques, pas des actualités LAI.

**Observation** : Les sources corporate LAI (MedinCell, Camurus, DelSiTech, Nanexa, Peptron) n'ont généré aucun item sélectionné. Cela suggère soit :
- Pas de contenu récent sur ces sites (période de 7 jours)
- Contenu non ingesté correctement
- Contenu ingesté mais non matché

---

## Propositions d'Ajustement Rapide

### Ajustement 1 : Rendre le matching LAI obligatoire

**Action** : Modifier `matcher.py` pour exiger qu'un item matche **à la fois** :
- Une company dans `lai_companies_global` OU `lai_companies_mvp_core`
- **ET** au moins un mot-clé dans `lai_keywords`

**Impact attendu** : Éliminer les faux positifs (items mentionnant des big pharma sans lien LAI).

**Effort** : Faible (modification du matcher, 1h)

---

### Ajustement 2 : Augmenter le bonus pure players LAI

**Action** : Passer le `pure_player_lai_bonus` de 3 à **10** dans `scoring_rules.yaml`.

**Impact attendu** : Favoriser massivement les items des pure players LAI (MedinCell, Camurus, etc.) par rapport aux big pharma.

**Effort** : Très faible (modification d'un paramètre, 5 min)

---

### Ajustement 3 : Vérifier l'ingestion des sources corporate LAI

**Action** : Vérifier dans S3 (`vectora-inbox-data-dev`) si les sources corporate LAI (MedinCell, Camurus, etc.) ont bien été ingérées sur la période 2025-12-01 à 2025-12-08.

**Impact attendu** : Identifier si le problème vient de l'ingestion (pas de contenu) ou du matching (contenu présent mais non matché).

**Effort** : Faible (inspection S3, 15 min)

---

## Recommandation Prioritaire

**Ajustement 1 (matching LAI obligatoire)** est la priorité absolue. Sans cela, le système continuera à sélectionner des items pharma génériques mentionnant des big pharma, même si ces items n'ont aucun lien avec les LAI.

**Ordre d'exécution recommandé** :
1. Ajustement 3 (vérifier ingestion sources corporate LAI) – pour comprendre si le problème est en amont
2. Ajustement 1 (matching LAI obligatoire) – pour corriger le cœur du problème
3. Ajustement 2 (bonus pure players) – pour affiner le scoring

---

## Conclusion Phase 4.3

Le MVP LAI en l'état actuel **ne répond pas aux critères de succès**. Les items sélectionnés sont des actualités pharma génériques sans lien avec les LAI. Le système matche correctement les companies (Pfizer, AbbVie, Takeda) mais ne vérifie pas que l'item concerne les technologies LAI.

**Décision** : MVP LAI – DEV : **À AJUSTER** (ajustements rapides nécessaires avant acceptation).

---

**Prochaine étape** : Implémenter les ajustements proposés et relancer un test Phase 4.2 bis.
