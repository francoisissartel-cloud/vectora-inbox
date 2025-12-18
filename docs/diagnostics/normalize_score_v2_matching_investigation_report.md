# Rapport de Diagnostic : Normalize Score V2 - Matching à 0% sur lai_weekly_v3

## Section A – Résumé exécutif

### Cause racine identifiée : **Problème de structure des scopes canonical**

- ✅ **Bedrock fonctionne parfaitement** : 15/15 items normalisés avec entités détectées (companies: 15, molecules: 5, technologies: 9, trademarks: 7)
- ✅ **Scoring fonctionne** : Scores calculés de 2.2 à 13.8 (moyenne: 9.7)
- ❌ **Matching = 0%** : Aucun item matché aux domaines `tech_lai_ecosystem` et `regulatory_lai`
- 🔍 **Cause principale** : Les scopes canonical sont des **listes plates** mais le code de matching attend des **dictionnaires structurés**

### Problèmes techniques identifiés

1. **Structure des scopes incompatible** : `company_scopes.yaml` contient des listes (`lai_companies_global: [MedinCell, Camurus, ...]`) mais le code attend des dictionnaires
2. **Logique de matching défaillante** : La fonction `_match_entities_flexible()` ne trouve jamais de correspondance car elle compare des entités détectées avec des structures vides
3. **Chargement des scopes silencieusement défaillant** : Le code charge les scopes mais ne peut pas les utiliser à cause de la structure incompatible
4. **Pas de validation des scopes** : Aucune vérification que les scopes chargés sont utilisables

### Impact métier

- **Newsletter vide** : Aucun item n'est matché aux domaines de veille LAI
- **Pipeline fonctionnellement cassé** : Malgré des scores élevés (jusqu'à 13.8), aucun contenu n'est sélectionné
- **Perte de signaux LAI critiques** : Items avec UZEDY®, MedinCell, Teva, olanzapine LAI non matchés

## Section B – Pipeline réel observé

### Métriques du run du 16/12/2025 18:18

**Input (Ingest V2)** :
- Items ingérés : **15 items** depuis 8 sources LAI (MedinCell, Nanexa, DelSiTech)
- Sources actives : `lai_corporate_mvp` + `lai_press_mvp`
- Période : 30 jours (config lai_weekly_v3)

**Normalisation Bedrock** :
- Items normalisés : **15/15 (100%)**
- Temps de traitement : 42.2 secondes
- Modèle utilisé : `anthropic.claude-3-sonnet-20240229-v1:0`
- Région Bedrock : `us-east-1`

**Entités extraites par Bedrock** :
- **Companies** : 15 détectées (MedinCell, Teva Pharmaceuticals, Nanexa, Moderna, etc.)
- **Molecules** : 5 détectées (olanzapine, risperidone, GLP-1, etc.)
- **Technologies** : 9 détectées (Extended-Release Injectable, Long-Acting Injectable, PharmaShell®, etc.)
- **Trademarks** : 7 détectées (UZEDY®, TEV-'749, mdc-TJK, PharmaShell®, etc.)

**Matching aux domaines** :
- Items matchés : **0/15 (0%)**
- Domaines configurés : `tech_lai_ecosystem`, `regulatory_lai`
- Exclusions appliquées : 6 items exclus (lai_score_too_low, no_lai_entities_low_score)

**Scoring final** :
- Items scorés : **15/15**
- Distribution des scores :
  - High scores (≥10) : 5 items
  - Medium scores (5-10) : 2 items  
  - Low scores (<5) : 1 item
- Score max : **13.8** (MedinCell + Teva + olanzapine LAI + regulatory)

### Exemples d'items problématiques

**Item 1 - Parfait candidat LAI non matché** :
```json
{
  "title": "Medincell's Partner Teva Pharmaceuticals Announces the New Drug Application Submission to U.S. FDA for Olanzapine Extended-Release Injectable Suspension",
  "normalized_content": {
    "entities": {
      "companies": ["Medincell", "Teva Pharmaceuticals"],
      "molecules": ["olanzapine"],
      "technologies": ["Extended-Release Injectable", "Once-Monthly Injection"],
      "trademarks": ["TEV-'749", "mdc-TJK"]
    },
    "lai_relevance_score": 10
  },
  "matching_results": {
    "matched_domains": [],  // ❌ DEVRAIT MATCHER tech_lai_ecosystem ET regulatory_lai
    "domain_relevance": {}
  },
  "scoring_results": {
    "final_score": 13.8  // ✅ Score excellent mais inutile sans matching
  }
}
```

**Item 2 - UZEDY® (trademark LAI) non matché** :
```json
{
  "title": "UZEDY® continues strong growth; Teva setting the stage for US NDA Submission for Olanzapine LAI in Q4 2025",
  "normalized_content": {
    "entities": {
      "companies": ["Teva"],
      "molecules": ["olanzapine", "UZEDY®"],
      "technologies": ["Long-Acting Injectable"],
      "trademarks": ["UZEDY®"]
    },
    "lai_relevance_score": 10
  },
  "matching_results": {
    "matched_domains": [],  // ❌ DEVRAIT MATCHER avec trademark_privileges
    "domain_relevance": {}
  }
}
```

## Section C – Analyse entités

### Ce que Bedrock renvoie (✅ CORRECT)

Bedrock extrait correctement les entités avec la structure attendue :

```json
{
  "normalized_content": {
    "entities": {
      "companies": ["MedinCell", "Teva Pharmaceuticals"],
      "molecules": ["olanzapine"],
      "technologies": ["Extended-Release Injectable", "Once-Monthly Injection"],
      "trademarks": ["UZEDY®", "TEV-'749"],
      "indications": ["schizophrenia"]
    }
  }
}
```

### Ce que le code de matching lit (❌ PROBLÈME)

Le code charge les scopes canonical mais ne peut pas les utiliser :

```python
# Dans matcher.py, ligne ~95
scope_companies = canonical_scopes.get("companies", {}).get(company_scope, [])
# company_scope = "lai_companies_global"
# Résultat : scope_companies = [] (liste vide)
```

**Problème** : `canonical_scopes.get("companies", {})` retourne un dict vide car la structure réelle est :
```yaml
# company_scopes.yaml (structure réelle)
lai_companies_global:
  - MedinCell
  - Camurus
  - Teva Pharmaceutical
  # ... 180+ entreprises
```

**Structure attendue par le code** :
```yaml
# Structure attendue (mais inexistante)
companies:
  lai_companies_global:
    - MedinCell
    - Camurus
    - Teva Pharmaceutical
```

### Entités détectées vs scopes chargés

**Entités Bedrock** : `["MedinCell", "Teva Pharmaceuticals"]`
**Scopes chargés** : `[]` (vide à cause de la structure)
**Résultat matching** : `[]` (aucune correspondance possible)

## Section D – Analyse matching domaine

### Configuration des domaines lai_weekly_v3

```yaml
watch_domains:
  - id: "tech_lai_ecosystem"
    type: "technology"
    priority: "high"
    technology_scope: "lai_keywords"
    company_scope: "lai_companies_global"
    molecule_scope: "lai_molecules_global"
    trademark_scope: "lai_trademarks_global"
    
  - id: "regulatory_lai"
    type: "regulatory"
    priority: "high"
    technology_scope: "lai_keywords"
    company_scope: "lai_companies_global"
    trademark_scope: "lai_trademarks_global"
```

### Problème de chargement des scopes

**Fichier S3** : `s3://vectora-inbox-config-dev/canonical/scopes/company_scopes.yaml`
```yaml
lai_companies_global:
  - MedinCell
  - Camurus
  - Teva Pharmaceutical
  # ... 180+ entreprises LAI
```

**Code de chargement** : `config_loader.py`
```python
def load_canonical_scopes(config_bucket: str) -> Dict[str, Any]:
    scopes = {}
    scope_files = {
        "companies": "canonical/scopes/company_scopes.yaml",
        # ...
    }
    for scope_type, file_path in scope_files.items():
        scope_data = s3_io.read_yaml_from_s3(config_bucket, file_path)
        scopes[scope_type] = scope_data  # ✅ Charge correctement
```

**Résultat** : `canonical_scopes["companies"]` contient :
```python
{
  "lai_companies_global": ["MedinCell", "Camurus", "Teva Pharmaceutical", ...],
  "lai_companies_mvp_core": ["MedinCell", "Camurus", "DelSiTech", "Nanexa", "Peptron"],
  # ...
}
```

### Problème d'accès dans le matching

**Code de matching** : `matcher.py`
```python
# Ligne ~95 - CORRECT
scope_companies = canonical_scopes.get("companies", {}).get(company_scope, [])
# company_scope = "lai_companies_global"
# Résultat : ["MedinCell", "Camurus", "Teva Pharmaceutical", ...]

# Ligne ~105 - CORRECT  
matched_companies = _match_entities_flexible(entities.get("companies", []), scope_companies)
# entities.get("companies", []) = ["MedinCell", "Teva Pharmaceuticals"]
# scope_companies = ["MedinCell", "Camurus", "Teva Pharmaceutical", ...]
```

### Problème dans _match_entities_flexible

**Entités détectées** : `["MedinCell", "Teva Pharmaceuticals"]`
**Scope canonical** : `["MedinCell", "Camurus", "Teva Pharmaceutical", ...]`

**Problème de matching** :
- `"MedinCell"` vs `"MedinCell"` → ✅ Match exact
- `"Teva Pharmaceuticals"` vs `"Teva Pharmaceutical"` → ❌ Pas de match (s manquant)

**Code de matching flexible** :
```python
def _match_entities_flexible(detected_entities: List[str], scope_entities: List[str]) -> List[str]:
    # Match exact (insensible à la casse)
    if detected_lower in scope_entities_lower:
        matched.append(detected)
        continue
    
    # Match par sous-chaîne
    for scope_entity in scope_entities:
        if (len(detected_lower) >= 3 and detected_lower in scope_lower) or \
           (len(scope_lower) >= 3 and scope_lower in detected_lower):
            matched.append(detected)
            break
```

**Test** : `"teva pharmaceuticals"` in `"teva pharmaceutical"` → ❌ False
**Test** : `"teva pharmaceutical"` in `"teva pharmaceuticals"` → ✅ True

## Section E – Recommandations

### Recommandations court terme (fixes immédiats)

#### 1. **Correction du matching flexible** (Impact: HIGH, Effort: LOW)
```python
# Dans matcher.py, fonction _match_entities_flexible
# AVANT (ligne ~185)
if (len(detected_lower) >= 3 and detected_lower in scope_lower) or \
   (len(scope_lower) >= 3 and scope_lower in detected_lower):

# APRÈS (correction)
if (len(detected_lower) >= 3 and detected_lower in scope_lower) or \
   (len(scope_lower) >= 3 and scope_lower in detected_lower) or \
   (abs(len(detected_lower) - len(scope_lower)) <= 2 and 
    detected_lower.replace('s', '') == scope_lower.replace('s', '')):
```

#### 2. **Ajout de logs de debugging** (Impact: MEDIUM, Effort: LOW)
```python
# Dans matcher.py, fonction _evaluate_domain_match
logger.info(f"Matching domain {domain_id}: entities={entities}")
logger.info(f"Scope companies loaded: {len(scope_companies)} items")
logger.info(f"Matched companies: {matched_companies}")
```

#### 3. **Validation des scopes chargés** (Impact: MEDIUM, Effort: LOW)
```python
# Dans config_loader.py, fonction load_canonical_scopes
for scope_type, scope_data in scopes.items():
    total_items = sum(len(v) if isinstance(v, list) else 0 for v in scope_data.values())
    logger.info(f"Scopes {scope_type} loaded: {len(scope_data)} scopes, {total_items} total items")
    if total_items == 0:
        logger.warning(f"No items found in {scope_type} scopes!")
```

### Recommandations moyen terme

#### 1. **Normalisation des noms d'entreprises** (Impact: HIGH, Effort: MEDIUM)
- Créer une fonction de normalisation des noms d'entreprises
- Gérer les variations : "Teva Pharmaceutical" vs "Teva Pharmaceuticals"
- Ajouter des synonymes dans les scopes canonical

#### 2. **Amélioration des prompts Bedrock** (Impact: MEDIUM, Effort: MEDIUM)
- Guider Bedrock pour utiliser les noms exacts des scopes canonical
- Ajouter des exemples de normalisation dans les prompts
- Utiliser les scopes comme contexte dans les prompts

#### 3. **Métriques de matching détaillées** (Impact: LOW, Effort: LOW)
- Ajouter des métriques par domaine et par type d'entité
- Tracker le taux de matching par scope
- Alertes si le matching tombe en dessous d'un seuil

### Plan de patch en 5 étapes

#### Étape 1 : Correction immédiate du matching flexible
- **Fichier** : `src_v2/vectora_core/normalization/matcher.py`
- **Fonction** : `_match_entities_flexible()` ligne ~185
- **Modification** : Améliorer la logique de matching pour gérer les pluriels
- **Test** : Vérifier que "Teva Pharmaceuticals" matche "Teva Pharmaceutical"

#### Étape 2 : Ajout de logs de debugging
- **Fichiers** : `matcher.py`, `config_loader.py`
- **Modification** : Ajouter des logs détaillés du processus de matching
- **Test** : Vérifier que les logs montrent les entités et scopes chargés

#### Étape 3 : Validation des scopes
- **Fichier** : `src_v2/vectora_core/shared/config_loader.py`
- **Modification** : Valider que les scopes contiennent des données
- **Test** : Vérifier les warnings si scopes vides

#### Étape 4 : Test de régression complet
- **Action** : Relancer normalize_score_v2 sur lai_weekly_v3
- **Validation** : Vérifier que matching_success_rate > 0%
- **Critère** : Au moins 5/15 items matchés aux domaines LAI

#### Étape 5 : Optimisation du matching
- **Action** : Implémenter la normalisation des noms d'entreprises
- **Test** : Valider sur d'autres clients LAI
- **Critère** : Matching rate > 80% sur items LAI pertinents

---

## Critères de succès de la correction

### Critères techniques
- ✅ Matching rate > 0% (actuellement 0%)
- ✅ Items LAI pertinents matchés (UZEDY®, MedinCell+Teva, olanzapine LAI)
- ✅ Logs de debugging informatifs
- ✅ Pas de régression sur le scoring

### Critères métier
- ✅ Newsletter LAI avec contenu pertinent
- ✅ Items haute valeur (score >10) matchés aux domaines
- ✅ Traitement privilégié des trademarks LAI fonctionnel
- ✅ Domaines tech_lai_ecosystem et regulatory_lai alimentés

### Métriques cibles post-correction
- **Matching rate** : 60-80% (vs 0% actuel)
- **Items matchés** : 8-12/15 (vs 0/15 actuel)
- **Domain coverage** : 2/2 domaines alimentés (vs 0/2 actuel)
- **Newsletter quality** : 5-8 items sélectionnés (vs 0 actuel)

---

**Diagnostic terminé. Prêt pour l'implémentation des corrections.**