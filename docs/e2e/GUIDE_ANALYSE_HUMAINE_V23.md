# Guide d'Analyse Humaine - Golden Test V23

**Objectif**: Valider les décisions du système avec un œil humain expert

---

## 📁 FICHIERS DISPONIBLES

### Rapports d'analyse
1. **`test_e2e_v23_rapport_detaille_item_par_item_2026-02-04.md`** (47.6 KB)
   - Vue d'ensemble des 32 items
   - Résumé de chaque item (relevant + non-relevant)
   - Statistiques par catégorie

2. **`test_e2e_v23_rapport_enrichi_avec_json_2026-02-04.md`** ⭐ **RECOMMANDÉ**
   - Analyse détaillée des 5 premiers items relevant
   - Sorties JSON complètes (normalisation + domain scoring)
   - Questions guidées pour analyse humaine
   - 3 exemples d'items non-relevant

### Données brutes
3. **`tests/data_snapshots/golden_test_v23_2026-02-04.json`**
   - Données complètes des 32 items
   - Format JSON exploitable

---

## 🎯 COMMENT ANALYSER

### Étape 1: Lire le rapport enrichi

Ouvrir `test_e2e_v23_rapport_enrichi_avec_json_2026-02-04.md`

Pour chaque item, tu verras :
- Le titre et le contenu brut
- La sortie JSON complète de normalisation
- La sortie JSON complète de domain scoring
- Des questions guidées

### Étape 2: Valider la normalisation (1er appel Bedrock)

**Questions à se poser** :

1. **Summary** : Est-ce que le résumé capture l'essentiel ?
   - ✅ Bon : "Teva submitted NDA for olanzapine LAI"
   - ❌ Mauvais : "Company announced something"

2. **Entités** : Les entités détectées sont-elles correctes ?
   - `companies` : Toutes les entreprises mentionnées ?
   - `technologies` : Technologies LAI identifiées ?
   - `molecules` : Molécules actives extraites ?
   - `trademarks` : Noms de marque détectés ?
   - `indications` : Pathologies mentionnées ?
   - `dosing_intervals` : Fréquence d'administration ?

3. **Event type** : La classification est-elle appropriée ?
   - `regulatory` : Approbation FDA, NDA, etc.
   - `clinical_update` : Résultats essais cliniques
   - `partnership` : Accords, collaborations
   - `corporate_move` : Acquisitions, nominations
   - `financial_results` : Résultats financiers

### Étape 3: Valider le domain scoring (2ème appel Bedrock)

**Questions à se poser** :

1. **Signaux détectés** : Sont-ils pertinents pour LAI ?
   - **Strong** : Pure players (MedinCell, Camurus), technologies core LAI, trademarks
   - **Medium** : Hybrid companies (Teva, Pfizer), dosing intervals (monthly, quarterly)
   - **Weak** : Molécules, indications
   - **Exclusions** : Oral tablets, patches, etc.

2. **Score** : Reflète-t-il l'importance LAI ?
   - 80-100 : Très pertinent (pure player + technologie LAI + trademark)
   - 60-79 : Pertinent (signaux moyens, hybrid company)
   - 40-59 : Faiblement pertinent (signaux faibles)
   - 0-39 : Non pertinent

3. **Reasoning** : Est-il convaincant ?
   - Mentionne-t-il les bons signaux ?
   - Justifie-t-il le score ?
   - Est-il cohérent avec les entités détectées ?

### Étape 4: Décision finale

Pour chaque item, décider :
- [ ] ✅ D'accord avec le système
- [ ] ❌ Faux positif (devrait être non-relevant)
- [ ] ❌ Faux négatif (devrait être relevant)
- [ ] ⚠️ Score inadapté (trop haut/bas)

---

## 🔍 CAS D'USAGE TYPIQUES

### Cas 1: Item clairement relevant
**Exemple** : "Teva submits NDA for once-monthly olanzapine LAI"
- ✅ Pure player ou hybrid company
- ✅ Technologie LAI explicite
- ✅ Dosing interval LAI (monthly, quarterly)
- ✅ Event type important (regulatory, clinical)
- **Attendu** : Score 80-90, relevant

### Cas 2: Item borderline
**Exemple** : "MedinCell awarded grant for malaria research"
- ✅ Pure player (MedinCell)
- ❌ Pas de technologie LAI mentionnée
- ❌ Pas de produit spécifique
- ⚠️ Indication pertinente (malaria)
- **Attendu** : Score 60-70, relevant mais faible

### Cas 3: Item non-relevant
**Exemple** : "MedinCell publishes financial results"
- ✅ Pure player (MedinCell)
- ❌ Pas de technologie LAI
- ❌ Pas de produit
- ❌ Event type générique (financial_results)
- **Attendu** : Score 0, non-relevant

### Cas 4: Faux positif potentiel
**Exemple** : "Abbott FDA warning for FreeStyle Libre CGM"
- ⚠️ Company détectée (Abbott)
- ⚠️ Trademark détecté (FreeStyle Libre)
- ❌ Pas de technologie LAI (CGM = continuous glucose monitor)
- ❌ Pas d'injection
- **Question** : Est-ce vraiment LAI ? Ou erreur du système ?

---

## 📊 MÉTRIQUES À CALCULER

Après analyse des 5 items détaillés :

1. **Taux d'accord** : X/5 items où tu es d'accord avec le système

2. **Faux positifs** : Items marqués relevant mais qui ne devraient pas l'être

3. **Problèmes de normalisation** : Items où les entités sont mal extraites

4. **Problèmes de scoring** : Items où le score ne reflète pas la pertinence

---

## 💡 RECOMMANDATIONS

### Si taux d'accord > 80%
✅ Le système fonctionne bien, golden test validé

### Si taux d'accord 60-80%
⚠️ Ajustements mineurs nécessaires :
- Affiner les seuils de scoring
- Enrichir les scopes (technologies, companies)
- Améliorer les prompts

### Si taux d'accord < 60%
❌ Problèmes majeurs :
- Revoir la logique de domain scoring
- Vérifier les prompts Bedrock
- Analyser les signaux détectés

---

## 📝 TEMPLATE D'ANALYSE

Pour chaque item analysé :

```markdown
### Item X - [Titre]

**Normalisation** : ✅ OK / ❌ Problème
- Problèmes identifiés : ...

**Domain Scoring** : ✅ OK / ❌ Problème
- Signaux manquants : ...
- Signaux erronés : ...
- Score attendu : ...

**Décision** : ✅ D'accord / ❌ Faux positif / ❌ Faux négatif

**Notes** : ...
```

---

## 🎯 PROCHAINES ÉTAPES

1. Analyser les 5 items détaillés du rapport enrichi
2. Noter tes observations dans le template
3. Calculer le taux d'accord
4. Identifier les patterns de problèmes
5. Proposer des améliorations si nécessaire

**Bon courage pour l'analyse ! 🚀**
