# Diagnostic : Normalisation Open-World - Résultats

## Résumé des Modifications

**Date :** 2025-01-15  
**Objectif :** Implémentation de la normalisation "open-world" avec séparation molecule/trademark

### Fichiers Modifiés

#### 1. `src/vectora_core/normalization/bedrock_client.py`
- **Prompt Bedrock** : Instructions open-world explicites
- **Nouveau champ** : `trademarks_detected` ajouté au schéma JSON
- **Instructions clarifiées** : Séparation molecule vs trademark

#### 2. `src/vectora_core/normalization/normalizer.py`
- **Nouveau schéma** : Implémentation *_detected + *_in_scopes
- **Extraction trademarks** : Ajout dans `_extract_canonical_examples()`
- **Calcul intersections** : Appel à `compute_entities_in_scopes()`

#### 3. `src/vectora_core/normalization/entity_detector.py`
- **Support trademarks** : Détection par règles + fusion
- **Nouvelle fonction** : `compute_entities_in_scopes()` pour intersections canonical
- **Détection règles** : Ajout trademarks dans la recherche par mots-clés

#### 4. `canonical/vectora_inbox_newsletter_pipeline_overview.md`
- **Exemple corrigé** : Brixadi → trademarks_detected (au lieu de molecules_detected)
- **Schéma documenté** : Nouveau format avec *_detected + *_in_scopes

## Nouveau Schéma de Normalisation

### Structure Open-World

```json
{
  // Métadonnées de base
  "source_key": "press_corporate__camurus",
  "source_type": "press_corporate",
  "title": "...",
  "summary": "...",
  "url": "...",
  "date": "2025-01-15",
  
  // MONDE OUVERT : Toutes les entités détectées par Bedrock
  "companies_detected": ["Camurus", "Pfizer"],
  "molecules_detected": ["buprenorphine", "naloxone"],
  "trademarks_detected": ["Brixadi", "Suboxone"],
  "technologies_detected": ["long acting", "depot", "microspheres"],
  "indications_detected": ["opioid use disorder", "pain management"],
  
  // INTERSECTION CANONICAL : Entités présentes dans les scopes
  "companies_in_scopes": ["Camurus"],
  "molecules_in_scopes": ["buprenorphine"],
  "trademarks_in_scopes": ["Brixadi"],
  "technologies_in_scopes": ["long acting"],
  "indications_in_scopes": ["opioid use disorder"],
  
  "event_type": "clinical_update"
}
```

### Séparation Molecule vs Trademark

**Avant :**
```json
"molecules_detected": ["Brixadi", "buprenorphine"]  // ❌ Confusion
```

**Après :**
```json
"molecules_detected": ["buprenorphine"],           // ✅ Substance active
"trademarks_detected": ["Brixadi"]                 // ✅ Nom commercial
```

## Instructions Bedrock Mises à Jour

### Nouvelles Instructions Open-World

```
EXAMPLES OF ENTITIES (use as reference vocabulary, but detect ANY relevant entities):
- Companies: Camurus, Pfizer, ...
- Molecules (active substances): buprenorphine, aripiprazole, ...
- Trademarks (brand names): Brixadi, Abilify Maintena, ...
- Technologies: long-acting injectable, microspheres, ...

IMPORTANT INSTRUCTIONS:
- OPEN-WORLD DETECTION: Do not limit yourself to the examples provided
- The examples are vocabulary guides, not restrictive lists
- MOLECULE vs TRADEMARK: Clearly distinguish between active substances and commercial brand names
```

### Nouveau Format de Réponse

```json
{
  "summary": "...",
  "event_type": "...",
  "companies_detected": ["...", "..."],
  "molecules_detected": ["...", "..."],
  "trademarks_detected": ["...", "..."],      // ✅ NOUVEAU
  "technologies_detected": ["...", "..."],
  "indications_detected": ["...", "..."]
}
```

## Logique d'Intersection Canonical

### Fonction `compute_entities_in_scopes()`

Pour chaque type d'entité :
1. **Récupérer** toutes les entités détectées (*_detected)
2. **Agréger** tous les scopes canonical du même type
3. **Calculer** l'intersection (entités détectées ∩ scopes canonical)
4. **Retourner** la liste triée des entités dans les scopes

**Exemple :**
```python
# Entités détectées
companies_detected = ["Camurus", "Pfizer", "NewCorp"]

# Scopes canonical
lai_companies_global = ["Camurus", "Indivior", "Alkermes"]
lai_companies_pure_players = ["Camurus", "Indivior"]

# Intersection
companies_in_scopes = ["Camurus"]  # Seul Camurus est dans les scopes
```

## Impact sur le Code Existant

### Rétrocompatibilité

**Risque :** Code existant accédant aux anciens champs uniquement  
**Mitigation :** Les champs *_detected conservent la même structure (listes triées)

### Nouveaux Champs Disponibles

Le code peut maintenant utiliser :
- `item['companies_in_scopes']` : Entreprises connues dans les scopes
- `item['companies_detected']` : Toutes les entreprises détectées
- `item['trademarks_detected']` : Noms commerciaux séparés des molécules

## Risques Identifiés

### 1. Qualité de Séparation Molecule/Trademark
**Risque :** Bedrock peut mal classifier certaines entités  
**Mitigation :** Monitoring + ajustement prompt si nécessaire

### 2. Performance Bedrock
**Risque :** Prompt plus long avec instructions détaillées  
**Mitigation :** Tests de performance + optimisation si nécessaire

### 3. Parsing JSON Plus Complexe
**Risque :** Nouveau schéma avec plus de champs  
**Mitigation :** Validation robuste + fallbacks

## Prochaines Étapes

1. **Tests unitaires** : Validation du nouveau schéma
2. **Tests d'intégration** : Vérification bout-en-bout
3. **Monitoring** : Métriques qualité de normalisation
4. **Ajustements** : Fine-tuning selon retours

---

**Statut :** ✅ Implémenté  
**Tests :** En attente  
**Déploiement :** Non (phase locale uniquement)