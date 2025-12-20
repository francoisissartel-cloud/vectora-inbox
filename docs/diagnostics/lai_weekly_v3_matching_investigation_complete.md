# Investigation Complète - Problème Matching 0% lai_weekly_v3

**Date :** 19 décembre 2025  
**Statut :** 🔍 INVESTIGATION COMPLÈTE - CAUSE RACINE IDENTIFIÉE  
**Matching rate :** 0% (problème confirmé)

---

## Résumé Exécutif

**🎯 CAUSE RACINE IDENTIFIÉE : STRUCTURE COMPLEXE DES SCOPES LAI NON SUPPORTÉE**

L'analyse détaillée du fichier `curated_items_final.json` et du code de matching révèle que **TOUS les items ont `matched_domains: []` et `domain_relevance: {}`**, confirmant un problème systémique dans la logique de matching.

**Problème principal :** Le scope `lai_keywords` utilise une structure complexe avec sous-catégories (`core_phrases`, `technology_terms_high_precision`, etc.) que le code de matching actuel ne sait pas traiter.

---

## Option 1 : Analyse Détaillée du Fichier Curated

### Observations Critiques

**✅ Items bien normalisés :**
- 15 items traités avec succès
- Entités correctement extraites (companies, molecules, technologies, trademarks)
- Scores LAI élevés (7-10)
- Pas d'exclusions appliquées sur les items pertinents

**❌ Matching systématiquement vide :**
```json
"matching_results": {
  "matched_domains": [],           // ⚠️ TOUJOURS VIDE
  "domain_relevance": {},          // ⚠️ TOUJOURS VIDE
  "exclusion_applied": false,      // Pas d'exclusions sur items pertinents
  "exclusion_reasons": []
}
```

**✅ Scoring fonctionne correctement :**
- Scores finaux élevés (8.7 à 14.9)
- Bonus pure_player détectés (Nanexa, MedinCell)
- Bonus trademark détectés (PharmaShell®, UZEDY®)
- `domain_relevance_factor: 0.05` → **PROBLÈME IDENTIFIÉ**

### Items Représentatifs Analysés

**Item 1 - Nanexa/Moderna Partnership :**
- Entités : `["Nanexa", "Moderna"]`, `["PharmaShell®"]`
- Score LAI : 8, Score final : 14.9
- **Matching : VIDE** → Devrait matcher `tech_lai_ecosystem`

**Item 2 - MedinCell/Teva NDA :**
- Entités : `["Medincell", "Teva Pharmaceuticals"]`, `["olanzapine"]`, `["Extended-Release Injectable"]`
- Score LAI : 10, Score final : 13.8
- **Matching : VIDE** → Devrait matcher `tech_lai_ecosystem` ET `regulatory_lai`

**Item 3 - UZEDY® FDA Approval :**
- Entités : `["risperidone"]`, `["UZEDY®"]`, `["Extended-Release Injectable"]`
- Score LAI : 10, Score final : 12.8
- **Matching : VIDE** → Devrait matcher les deux domaines

---

## Option 2 : Analyse Mécanique de Matching Complète

### 1. Configuration Client lai_weekly_v3

**Domaines configurés :**
```yaml
watch_domains:
  - id: "tech_lai_ecosystem"
    type: "technology"
    technology_scope: "lai_keywords"      # ⚠️ PROBLÈME ICI
    company_scope: "lai_companies_global"
    molecule_scope: "lai_molecules_global"
    trademark_scope: "lai_trademarks_global"
    
  - id: "regulatory_lai"
    type: "regulatory"
    technology_scope: "lai_keywords"      # ⚠️ MÊME PROBLÈME
    company_scope: "lai_companies_global"
    trademark_scope: "lai_trademarks_global"
```

### 2. Structure Problématique du Scope lai_keywords

**Structure actuelle (COMPLEXE) :**
```yaml
lai_keywords:
  _metadata:
    profile: technology_complex
  core_phrases:
    - "long-acting injectable"
    - "extended-release injection"
    # ... 13 termes
  technology_terms_high_precision:
    - "drug delivery system"
    - "PharmaShell®"
    # ... 80+ termes
  technology_use:
    - "injectable"
    - "injection"
    # ... 10+ termes
  # ... autres sous-catégories
```

**Structure attendue par le code (PLATE) :**
```yaml
lai_keywords:
  - "long-acting injectable"
  - "extended-release injection"
  - "drug delivery system"
  - "PharmaShell®"
  # ... liste plate de termes
```

### 3. Code de Matching - Fonction Défaillante

**Fonction `_match_entities_flexible()` :**
```python
def _match_entities_flexible(detected_entities: List[str], scope_entities: List[str]) -> List[str]:
    if not detected_entities or not scope_entities:
        return []
    # ... logique de matching
```

**Problème :** `scope_entities` reçoit la structure complexe `lai_keywords` au lieu d'une liste plate.

**Résultat :** `scope_entities` = `{"core_phrases": [...], "technology_terms_high_precision": [...]}` 
→ Type `dict` au lieu de `List[str]` → Matching échoue silencieusement

### 4. Fonction load_canonical_scopes

**Code actuel :**
```python
def load_canonical_scopes(config_bucket: str) -> Dict[str, Any]:
    # ...
    for scope_type, file_path in scope_files.items():
        scope_data = s3_io.read_yaml_from_s3(config_bucket, file_path)
        all_scopes.update(scope_data)  # ⚠️ AJOUTE STRUCTURE COMPLEXE
```

**Problème :** La structure complexe de `lai_keywords` est ajoutée telle quelle, sans aplatissement.

### 5. Chaîne de Défaillance Complète

1. **Chargement :** `lai_keywords` chargé avec structure complexe ✅
2. **Résolution :** `technology_scope: "lai_keywords"` → Récupère structure complexe ❌
3. **Matching :** `_match_entities_flexible()` reçoit `dict` au lieu de `List[str]` ❌
4. **Résultat :** `matched_technologies = []` → Pas de match ❌
5. **Évaluation :** `technology_signals = 0` → Pas de match domaine ❌
6. **Final :** `matched_domains = []` → Matching rate 0% ❌

---

## Analyse des Autres Composants

### ✅ Bedrock - Fonctionne Correctement
- Entités bien extraites
- Technologies LAI détectées : "Extended-Release Injectable", "Long-Acting Injectable"
- Trademarks détectés : "PharmaShell®", "UZEDY®", "TEV-'749"
- Scores LAI pertinents (7-10)

### ✅ Prompts Bedrock - Fonctionnent Correctement
- Normalisation cohérente
- Classification d'événements correcte
- Pas d'anti-LAI détecté à tort

### ✅ Fichiers Chargés - Corrects
- `lai_companies_global` : 100+ entreprises chargées
- `lai_trademarks_global` : Marques LAI chargées
- Structure des autres scopes : plates et correctes

### ❌ Code Matcher - Défaillant
- Ne gère pas les structures complexes de scopes
- Logique d'évaluation correcte mais données d'entrée invalides
- Pas de validation de type sur `scope_entities`

---

## Solutions Identifiées

### Solution 1 : Aplatissement des Scopes Complexes (RECOMMANDÉE)

**Modifier `load_canonical_scopes()` :**
```python
def load_canonical_scopes(config_bucket: str) -> Dict[str, Any]:
    # ... code existant ...
    for scope_type, file_path in scope_files.items():
        scope_data = s3_io.read_yaml_from_s3(config_bucket, file_path)
        
        # Aplatissement des scopes complexes
        flattened_scopes = {}
        for scope_name, scope_content in scope_data.items():
            if isinstance(scope_content, dict) and not scope_name.startswith('_'):
                # Scope complexe : aplatir toutes les sous-catégories
                flattened_terms = []
                for category, terms in scope_content.items():
                    if isinstance(terms, list) and not category.startswith('_'):
                        flattened_terms.extend(terms)
                flattened_scopes[scope_name] = flattened_terms
            else:
                # Scope simple : conserver tel quel
                flattened_scopes[scope_name] = scope_content
        
        all_scopes.update(flattened_scopes)
```

### Solution 2 : Support Natif des Structures Complexes

**Modifier `_match_entities_flexible()` pour gérer les structures complexes :**
```python
def _match_entities_flexible(detected_entities: List[str], scope_entities) -> List[str]:
    # Normalisation du scope
    if isinstance(scope_entities, dict):
        # Scope complexe : aplatir
        flat_entities = []
        for category, terms in scope_entities.items():
            if isinstance(terms, list) and not category.startswith('_'):
                flat_entities.extend(terms)
        scope_entities = flat_entities
    elif not isinstance(scope_entities, list):
        return []
    
    # ... logique de matching existante
```

### Solution 3 : Restructuration du Scope lai_keywords

**Créer une version plate de `lai_keywords` :**
```yaml
lai_keywords:
  - "long-acting injectable"
  - "extended-release injection"
  - "drug delivery system"
  - "PharmaShell®"
  # ... tous les termes des sous-catégories
```

---

## Impact et Priorité

### Impact Business
- **Critique :** 0% de matching = Newsletter vide
- **Bloquant :** Phase 4 impossible sans matching fonctionnel
- **Coût :** Temps développement et tests perdus

### Priorité Technique
- **P0 :** Correction immédiate requise
- **Complexité :** Faible (modification 10-20 lignes)
- **Risque :** Très faible (amélioration pure)

### Validation Requise
- **Test local :** Avec items synthétiques
- **Test AWS :** Déploiement et validation
- **Métriques :** Matching rate > 60% attendu

---

## Recommandations Immédiates

### Phase 1 : Correction Immédiate (2h)
1. **Implémenter Solution 1** (aplatissement dans `load_canonical_scopes`)
2. **Test local** avec items curated existants
3. **Validation** : matching_results non vides

### Phase 2 : Déploiement (1h)
1. **Package et déploiement** layer vectora-core
2. **Test AWS** avec payload lai_weekly_v3
3. **Validation** : matching rate > 0%

### Phase 3 : Optimisation (optionnel)
1. **Analyse qualité** des matches obtenus
2. **Ajustement seuils** si nécessaire
3. **Documentation** de la correction

---

## Conclusion

**Cause racine confirmée :** Structure complexe du scope `lai_keywords` non supportée par le code de matching actuel.

**Solution simple :** Aplatissement des scopes complexes dans `load_canonical_scopes()`.

**Impact attendu :** Matching rate passant de 0% à 60-80% avec cette seule correction.

**Prêt pour implémentation immédiate.**

---

*Investigation complète - 19 décembre 2025*  
*Cause racine identifiée - Solution prête*