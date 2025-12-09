# Vectora Inbox — LAI MVP Matching Refactor Results

**Date:** 2025-01-XX  
**Scope:** company_scopes.yaml refactor (pure players vs hybrid)  
**Status:** Completed

---

## 1. Résumé exécutif

Les company scopes LAI ont été restructurés pour séparer clairement les **pure players LAI** (entreprises 100% focalisées LAI) des **entreprises hybrid** (big pharma/mid pharma avec activité LAI diversifiée).

**Changements clés :**
- Création de 2 nouveaux scopes : `lai_companies_pure_players` (14 entreprises) et `lai_companies_hybrid` (27 entreprises)
- Conservation de `lai_companies_mvp_core` (5 entreprises pilotes) et `lai_companies_global` (160+ entreprises) pour compatibilité
- Documentation de l'usage prévu : pure players → 1 signal fort suffit ; hybrid → signaux multiples requis

---

## 2. Nouvelle structure des company scopes LAI

### 2.1 lai_companies_mvp_core (5 entreprises)

**Scope existant conservé — entreprises pilotes MVP**

| Entreprise | Statut | Commentaire |
|------------|--------|-------------|
| MedinCell | ✅ Conservé | Pure player LAI (France) |
| Camurus | ✅ Conservé | Pure player LAI (Suède) |
| DelSiTech | ✅ Conservé | Pure player LAI (Finlande) |
| Nanexa | ✅ Conservé | Pure player LAI (Suède) |
| Peptron | ✅ Conservé | Pure player LAI (Corée du Sud) |

**Usage :** Scope pilote pour le MVP initial. Toutes ces entreprises sont également dans `lai_companies_pure_players`.

---

### 2.2 lai_companies_pure_players (14 entreprises)

**Nouveau scope — entreprises 100% focalisées LAI**

| Entreprise | Pays/Région | Technologie principale | Source |
|------------|-------------|------------------------|--------|
| MedinCell | France | BEPO (in-situ forming depot) | mvp_core |
| Camurus | Suède | FluidCrystal (liquid crystal depot) | mvp_core |
| DelSiTech | Finlande | Silica-based depot | mvp_core |
| Nanexa | Suède | PharmaShell (microspheres) | mvp_core |
| Peptron | Corée du Sud | Microspheres | mvp_core |
| Bolder BioTechnology | USA | HLE (half-life extension) | lai_companies_global |
| Cristal Therapeutics | Pays-Bas | CriPec (polymeric micelles) | lai_companies_global |
| Durect | USA | SABER (in-situ forming depot) | lai_companies_global |
| Eupraxia Pharmaceuticals | Canada | DiffuSphere (microspheres) | lai_companies_global |
| Foresee Pharmaceuticals | Taiwan | Hydrogel depot | lai_companies_global |
| G2GBio | Corée du Sud | Microspheres | lai_companies_global |
| Hanmi Pharmaceutical | Corée du Sud | LAPSCOVERY (HLE platform) | lai_companies_global |
| LIDDS | Suède | NanoZolid (nanosuspension depot) | lai_companies_global |
| Taiwan Liposome | Taiwan | Liposomal depot | lai_companies_global |

**Principe métier :**
- Ces entreprises ont un business model centré exclusivement ou quasi-exclusivement sur les LAI
- Leur pipeline est majoritairement composé de produits LAI
- Leur communication corporate met en avant les LAI comme core business

**Usage prévu (phase suivante — code runtime) :**
- Pour ces entreprises, **1 signal fort LAI suffit** pour déclencher un match haute confiance
- Exemple : "MedinCell announces partnership" + mention de "injectable" → match LAI probable
- Logique : si l'entreprise est pure player LAI, tout ce qu'elle fait est probablement lié aux LAI

---

### 2.3 lai_companies_hybrid (27 entreprises)

**Nouveau scope — big pharma / mid pharma avec activité LAI**

| Entreprise | Type | Exemples produits LAI | Commentaire |
|------------|------|----------------------|-------------|
| AbbVie | Big Pharma | Skyrizi (risankizumab SC q12w) | Portfolio diversifié (oral, IV, LAI) |
| Alkermes | Mid Pharma | Aristada (aripiprazole LAI), Vivitrol | Spécialiste CNS avec LAI |
| Amgen | Big Pharma | Prolia (denosumab SC q6m), Repatha | Portfolio diversifié |
| Ascendis Pharma | Mid Pharma | TransCon platform (HLE) | Technologie HLE pour LAI |
| Astellas Pharma | Big Pharma | — | Portfolio diversifié |
| AstraZeneca | Big Pharma | — | Portfolio diversifié |
| Bayer | Big Pharma | — | Portfolio diversifié |
| Eli Lilly | Big Pharma | Trulicity (dulaglutide SC q1w) | Portfolio diversifié |
| Ferring | Mid Pharma | — | Spécialiste reproductive health |
| Gilead Sciences | Big Pharma | Cabenuva (cabotegravir + rilpivirine LAI) | Portfolio diversifié (oral, IV, LAI) |
| GlaxoSmithKline | Big Pharma | Cabenuva (co-dev avec Janssen) | Portfolio diversifié |
| Ipsen | Mid Pharma | Somatuline (lanreotide LAI) | Spécialiste oncology/endocrinology |
| Janssen | Big Pharma | Invega Sustenna (paliperidone LAI) | Portfolio diversifié |
| Janssen Pharmaceuticals | Big Pharma | Idem Janssen | Idem |
| Johnson & Johnson | Big Pharma | Via Janssen | Portfolio diversifié |
| Jazz Pharmaceuticals | Mid Pharma | — | Portfolio diversifié |
| Lundbeck | Mid Pharma | — | Spécialiste CNS |
| Luye Pharma | Mid Pharma | — | Spécialiste LAI (Chine) |
| Merck & Co | Big Pharma | — | Portfolio diversifié |
| Novartis | Big Pharma | — | Portfolio diversifié |
| Novo Nordisk | Big Pharma | Ozempic (semaglutide SC q1w) | Spécialiste diabetes/obesity |
| Otsuka | Mid Pharma | Abilify Maintena (aripiprazole LAI) | Portfolio diversifié |
| Pfizer | Big Pharma | — | Portfolio diversifié |
| Sanofi | Big Pharma | — | Portfolio diversifié |
| Takeda Pharmaceutical | Big Pharma | — | Portfolio diversifié |
| Teva Pharmaceutical | Big Pharma | — | Portfolio diversifié |
| ViiV Healthcare | Mid Pharma | Cabenuva (cabotegravir + rilpivirine LAI) | Spécialiste HIV |

**Principe métier :**
- Ces entreprises ont un portfolio diversifié incluant des LAI mais ne sont pas focalisées exclusivement sur les LAI
- Leur pipeline contient des produits oraux, IV, topiques, etc. en plus des LAI
- Leur communication corporate ne met pas les LAI en avant comme core business

**Usage prévu (phase suivante — code runtime) :**
- Pour ces entreprises, **signaux multiples requis** pour déclencher un match LAI
- Exemple : "Pfizer announces partnership" + mention de "injectable" → pas de match LAI (trop générique)
- Exemple : "Pfizer announces partnership" + mention de "long-acting injectable" + "depot injection" → match LAI probable
- Logique : éviter les faux positifs sur des activités non-LAI de ces big pharma

**⚠️ Impact attendu :**
- Réduction drastique des faux positifs sur AbbVie, Pfizer, Novo Nordisk, etc.
- Ces entreprises étaient responsables de la majorité des faux positifs LAI (précision à 0%)

---

### 2.4 lai_companies_global (160+ entreprises)

**Scope existant conservé — toutes les entreprises avec activité LAI**

**Relation avec les nouveaux scopes :**
- `lai_companies_pure_players` ⊂ `lai_companies_global`
- `lai_companies_hybrid` ⊂ `lai_companies_global`
- `lai_companies_global` = `lai_companies_pure_players` ∪ `lai_companies_hybrid` ∪ autres entreprises LAI

**Usage :** Scope exhaustif pour référence. Contient toutes les entreprises ayant une activité LAI documentée, quelle que soit leur taille ou leur focus.

**Note :** Ce scope n'est pas modifié dans cette phase pour préserver la compatibilité avec les analyses existantes.

---

## 3. Principes de classification

### 3.1 Critères pour pure_players

Une entreprise est classée **pure player LAI** si elle remplit **au moins 2 des 3 critères** suivants :

1. **Business model :** >80% du pipeline/portfolio est LAI
2. **Communication corporate :** Les LAI sont mis en avant comme core business dans la communication officielle
3. **Technologie propriétaire :** L'entreprise possède une plateforme technologique LAI propriétaire (ex : BEPO, FluidCrystal, SABER, etc.)

**Exemples :**
- ✅ MedinCell : 100% LAI, BEPO propriétaire, communication 100% LAI
- ✅ Camurus : 100% LAI, FluidCrystal propriétaire, communication 100% LAI
- ✅ Durect : >90% LAI, SABER propriétaire, communication LAI-centric

---

### 3.2 Critères pour hybrid

Une entreprise est classée **hybrid** si elle remplit **au moins 1 des 3 critères** suivants :

1. **Portfolio diversifié :** <50% du pipeline/portfolio est LAI
2. **Big pharma / mid pharma :** Entreprise de taille significative avec activités multiples (oral, IV, topique, etc.)
3. **Pas de technologie LAI propriétaire :** L'entreprise utilise des technologies LAI sous licence ou en partenariat

**Exemples :**
- ✅ AbbVie : <10% LAI, big pharma, portfolio diversifié (Humira oral, Skyrizi LAI, etc.)
- ✅ Pfizer : <5% LAI, big pharma, portfolio diversifié
- ✅ Novo Nordisk : ~20% LAI (Ozempic, Wegovy), big pharma, portfolio diversifié (insulines, GLP-1, etc.)

---

### 3.3 Cas limites

| Entreprise | Classification | Justification |
|------------|----------------|---------------|
| Alkermes | Hybrid | Spécialiste CNS avec LAI (Aristada, Vivitrol) mais aussi oral (Lybalvi, etc.) → <60% LAI |
| Luye Pharma | Hybrid | Spécialiste LAI en Chine mais portfolio diversifié → ~70% LAI, classé hybrid par prudence |
| Hanmi Pharmaceutical | Pure player | LAPSCOVERY platform propriétaire, >80% pipeline LAI, communication LAI-centric |
| Ascendis Pharma | Hybrid | TransCon platform (HLE) mais aussi produits non-LAI → ~60% LAI, classé hybrid |

**Principe :** En cas de doute, classer en **hybrid** pour éviter les faux positifs (précision avant rappel).

---

## 4. Usage prévu dans le moteur de matching

### 4.1 Logique de scoring différenciée

**Pour lai_companies_pure_players :**
```
IF company IN lai_companies_pure_players:
    IF 1+ core_phrase OR 1+ technology_terms_high_precision:
        → match LAI haute confiance (score ≥ 0.8)
    ELIF 1+ technology_use + 1+ route_admin_terms:
        → match LAI confiance moyenne (score ≥ 0.6)
    ELSE:
        → pas de match LAI
```

**Pour lai_companies_hybrid :**
```
IF company IN lai_companies_hybrid:
    IF 2+ core_phrase OR (1+ core_phrase + 1+ technology_terms_high_precision):
        → match LAI haute confiance (score ≥ 0.8)
    ELIF 1+ technology_terms_high_precision + 1+ route_admin_terms + 1+ interval_patterns:
        → match LAI confiance moyenne (score ≥ 0.6)
    ELSE:
        → pas de match LAI
```

**Principe :** Les pure players nécessitent moins de signaux pour déclencher un match (1 signal fort suffit), tandis que les hybrid nécessitent une combinaison de signaux multiples (éviter faux positifs).

---

### 4.2 Exemples concrets

#### Exemple 1 : MedinCell (pure player)

**Texte :** "MedinCell announces new partnership for injectable formulation development"

**Signaux détectés :**
- company : MedinCell → lai_companies_pure_players ✅
- technology_use : "injectable" ✅
- route_admin_terms : (implicite via "injectable")

**Résultat attendu :** Match LAI confiance moyenne (score ≥ 0.6)

**Justification :** MedinCell est pure player LAI, donc 1 signal d'usage (injectable) suffit pour déclencher un match.

---

#### Exemple 2 : Pfizer (hybrid)

**Texte :** "Pfizer announces new partnership for injectable formulation development"

**Signaux détectés :**
- company : Pfizer → lai_companies_hybrid ✅
- technology_use : "injectable" ✅
- route_admin_terms : (implicite via "injectable")

**Résultat attendu :** Pas de match LAI

**Justification :** Pfizer est hybrid, donc 1 signal d'usage seul ne suffit pas. Il faut des signaux multiples (core_phrase + technology_terms_high_precision, ou combinaison de 3+ signaux).

---

#### Exemple 3 : Pfizer (hybrid) avec signaux multiples

**Texte :** "Pfizer announces new long-acting injectable formulation using PLGA microspheres for once-monthly administration"

**Signaux détectés :**
- company : Pfizer → lai_companies_hybrid ✅
- core_phrases : "long-acting injectable" ✅
- technology_terms_high_precision : "PLGA microspheres" ✅
- interval_patterns : "once-monthly" ✅

**Résultat attendu :** Match LAI haute confiance (score ≥ 0.8)

**Justification :** Pfizer est hybrid, mais présence de 1 core_phrase + 1 technology_terms_high_precision + 1 interval_pattern → combinaison suffisante pour match haute confiance.

---

## 5. Impact attendu sur la précision LAI

### Avant refactor (company scopes non différenciés)

**Problème :**
- Toutes les entreprises de `lai_companies_global` traitées de la même manière
- 1 signal générique (ex : "subcutaneous", "PEG") déclenchait un match LAI pour AbbVie, Pfizer, Novo Nordisk, etc.
- Faux positifs massifs → précision LAI à 0%

**Exemple de faux positif :**
- "AbbVie announces PEGylated antibody for subcutaneous injection" → match LAI ❌
- Raison : AbbVie dans lai_companies_global + "PEGylated" + "subcutaneous" → match LAI
- Problème : Ce n'est pas un LAI (PEGylated antibody standard, pas de durée prolongée)

---

### Après refactor (pure players vs hybrid)

**Amélioration :**
- Séparation claire pure players (14) vs hybrid (27)
- Logique de scoring différenciée : pure players → 1 signal suffit ; hybrid → signaux multiples requis
- Termes génériques isolés dans `generic_terms` (ne matchent plus seuls)

**Exemple de faux positif éliminé :**
- "AbbVie announces PEGylated antibody for subcutaneous injection" → pas de match LAI ✅
- Raison : AbbVie dans lai_companies_hybrid + "PEGylated" (generic_term) + "subcutaneous" (route_admin_term) → pas assez de signaux forts
- Résultat : Faux positif éliminé

**Exemple de vrai positif conservé :**
- "AbbVie announces long-acting injectable formulation using PLGA microspheres for once-monthly administration" → match LAI ✅
- Raison : AbbVie dans lai_companies_hybrid + "long-acting injectable" (core_phrase) + "PLGA microspheres" (technology_terms_high_precision) + "once-monthly" (interval_pattern) → signaux multiples suffisants
- Résultat : Vrai positif conservé

---

### Métriques attendues

| Métrique | Avant refactor | Après refactor (attendu) |
|----------|----------------|--------------------------|
| Précision LAI | 0% | >50% |
| Faux positifs big pharma | ~80% des matches | <10% des matches |
| Vrais positifs pure players | ~100% | ~100% (conservé) |
| Vrais positifs hybrid | ~20% | ~80% (amélioration) |

**Note :** Ces métriques sont des estimations. La validation réelle nécessite l'adaptation du code runtime et des tests sur le corpus existant.

---

## 6. Points restant ambigus (pour phase suivante)

### 6.1 Entreprises à reclassifier potentiellement

| Entreprise | Classification actuelle | Ambiguïté | Action recommandée |
|------------|------------------------|-----------|-------------------|
| Alkermes | Hybrid | Spécialiste CNS avec LAI significatif (~60% pipeline) | Monitorer, potentiellement reclasser en pure player si >80% LAI |
| Luye Pharma | Hybrid | Spécialiste LAI en Chine (~70% pipeline) | Idem |
| Ascendis Pharma | Hybrid | TransCon platform HLE (~60% pipeline) | Idem |

### 6.2 Entreprises manquantes potentielles

**À considérer pour ajout futur (si détectées dans corpus) :**
- Autres pure players LAI émergents (ex : startups biotech LAI)
- CDMO spécialisés LAI (ex : Recipharm, Catalent avec activité LAI significative)

### 6.3 Seuils de scoring

**Question ouverte pour phase suivante (code runtime) :**
- Quel score minimum pour match haute confiance ? (proposition : ≥ 0.8)
- Quel score minimum pour match confiance moyenne ? (proposition : ≥ 0.6)
- Comment gérer les cas limites (score entre 0.5 et 0.6) ?

**Recommandation :** Implémenter des seuils configurables dans `domain_matching_rules.yaml` et tester sur le corpus existant pour calibrer.

---

## 7. Prochaines étapes (hors scope de cette phase)

### Phase suivante : Adaptation du code runtime

**Fichiers à modifier :**
1. `domain_matching_rules.yaml` :
   - Définir les règles de scoring différenciées pour pure_players vs hybrid
   - Configurer les seuils de confiance (haute, moyenne, basse)

2. `matcher.py` :
   - Implémenter la logique de scoring différenciée par type d'entreprise
   - Gérer les combinaisons de signaux selon le type d'entreprise

3. `scorer.py` :
   - Adapter le scoring pour prendre en compte le type d'entreprise (pure_player vs hybrid)
   - Implémenter les seuils de confiance configurables

**Tests à effectuer :**
- Mesurer la nouvelle précision LAI sur le corpus existant
- Valider que les faux positifs big pharma (AbbVie, Pfizer, etc.) sont éliminés
- Vérifier que les vrais positifs pure players (MedinCell, Camurus, etc.) sont conservés
- Vérifier que les vrais positifs hybrid (avec signaux multiples) sont conservés

---

## 8. Conclusion

Le refactor des company scopes LAI est terminé. La nouvelle structure avec séparation pure_players / hybrid permet :
- ✅ Une classification claire des entreprises par niveau de focus LAI
- ✅ Une base solide pour implémenter une logique de scoring différenciée
- ✅ Une réduction attendue des faux positifs big pharma (précision LAI de 0% vers >50%)

**Impact attendu :** Amélioration drastique de la précision LAI en éliminant les faux positifs sur les big pharma tout en conservant les vrais positifs sur les pure players et les hybrid avec signaux multiples.

---

**Fin du diagnostic Phase 2.**
