# Plan de Refactor – Matching Générique Piloté par Config/Canonical

**Date** : 2025-12-08  
**Auteur** : Amazon Q Developer  
**Objectif** : Rendre le matching 100% générique et piloté par config/canonical, sans aucune logique métier LAI codée en dur

---

## Résumé Exécutif

**Problème actuel** : Le matcher est trop permissif. Il sélectionne des items dès qu'une company match (souvent big pharma) sans vérifier que le contenu parle vraiment de la technology définie dans le domaine. Résultat : 0% de précision LAI pour le domaine `tech_lai_ecosystem`.

**Solution** : Introduire un système de **règles de matching par type de domaine**, entièrement configurable via canonical, qui définit les contraintes logiques (AND/OR) entre les différentes dimensions (company, molecule, technology, indication).

**Principe clé** : Aucun `if domain.id == "tech_lai_ecosystem"` dans le code. Tout doit être piloté par des règles déclaratives dans canonical.

---

## 1. Contrat Métier : Règles de Matching par Type de Domaine

### 1.1 Concept : Matching Rules

Chaque **type de domaine** (`technology`, `indication`, `regulatory`, etc.) peut avoir des **règles de matching** qui définissent comment combiner les différentes dimensions pour décider si un item matche.

**Dimensions disponibles** :
- `company` : Entreprises détectées dans l'item
- `molecule` : Molécules détectées dans l'item
- `technology` : Mots-clés technologiques détectés dans l'item
- `indication` : Indications thérapeutiques détectées dans l'item

**Modes de matching** :
- `required` : La dimension DOIT matcher (au moins une entité)
- `optional` : La dimension PEUT matcher (bonus si elle matche, mais pas obligatoire)
- `forbidden` : La dimension NE DOIT PAS matcher (exclusion)

**Logique de combinaison** :
- `match_mode: "all_required"` : Toutes les dimensions marquées `required` doivent matcher (AND logique)
- `match_mode: "any_required"` : Au moins une dimension marquée `required` doit matcher (OR logique)
- `match_mode: "custom"` : Logique personnalisée définie par une expression (pour usage futur)

---

### 1.2 Exemple : Domaine Technology (LAI)

Pour un domaine de type `technology` comme `tech_lai_ecosystem`, on veut :
- **Obligatoirement** : Au moins un mot-clé technology (ex: `lai_keywords`)
- **ET obligatoirement** : Au moins une entité (company OU molecule)

**Règle de matching** :
```yaml
domain_type: technology
match_mode: all_required
dimensions:
  technology:
    requirement: required
    min_matches: 1
  entity:  # entity = company OR molecule
    requirement: required
    min_matches: 1
    sources: [company, molecule]
```

**Interprétation** :
- `technology.requirement: required` → L'item DOIT contenir au moins 1 mot-clé de `technology_scope`
- `entity.requirement: required` → L'item DOIT contenir au moins 1 company OU 1 molecule
- `match_mode: all_required` → Les deux conditions doivent être satisfaites (AND)

---

### 1.3 Exemple : Domaine Regulatory

Pour un domaine de type `regulatory`, on veut :
- **Au moins une entité** (company OU molecule OU technology)
- Pas de contrainte stricte sur la technology (car les news réglementaires peuvent ne pas mentionner explicitement les mots-clés LAI)

**Règle de matching** :
```yaml
domain_type: regulatory
match_mode: any_required
dimensions:
  company:
    requirement: optional
  molecule:
    requirement: optional
  technology:
    requirement: optional
```

**Interprétation** :
- `match_mode: any_required` → Au moins une dimension doit matcher
- Toutes les dimensions sont `optional` → Logique OR classique (company OU molecule OU technology)

---

### 1.4 Exemple : Domaine Indication

Pour un domaine de type `indication`, on veut :
- **Obligatoirement** : Au moins un mot-clé d'indication (ex: `addiction_keywords`)
- **ET obligatoirement** : Au moins une entité (company OU molecule)

**Règle de matching** :
```yaml
domain_type: indication
match_mode: all_required
dimensions:
  indication:
    requirement: required
    min_matches: 1
  entity:
    requirement: required
    min_matches: 1
    sources: [company, molecule]
```

---

## 2. Implémentation : Nouveau Fichier Canonical

### 2.1 Fichier : `canonical/matching/domain_matching_rules.yaml`

Ce fichier définit les règles de matching pour chaque type de domaine.

```yaml
# Règles de matching par type de domaine.
# Ces règles définissent comment combiner les différentes dimensions (company, molecule, technology, indication)
# pour décider si un item matche un domaine.
#
# Principe : Le code ne contient AUCUNE logique métier spécifique (pas de "if LAI").
# Tout est piloté par ces règles déclaratives.

# Règle pour les domaines de type "technology"
# Exemple : tech_lai_ecosystem, tech_oncology_ecosystem, etc.
technology:
  match_mode: all_required
  description: "Pour un domaine technology, l'item doit contenir au moins un mot-clé technology ET au moins une entité (company ou molecule)"
  dimensions:
    technology:
      requirement: required
      min_matches: 1
      description: "Au moins un mot-clé du technology_scope doit être détecté"
    entity:
      requirement: required
      min_matches: 1
      sources: [company, molecule]
      description: "Au moins une company OU une molecule doit être détectée"

# Règle pour les domaines de type "indication"
# Exemple : indication_addiction, indication_schizophrenia, etc.
indication:
  match_mode: all_required
  description: "Pour un domaine indication, l'item doit contenir au moins un mot-clé indication ET au moins une entité (company ou molecule)"
  dimensions:
    indication:
      requirement: required
      min_matches: 1
      description: "Au moins un mot-clé du indication_scope doit être détecté"
    entity:
      requirement: required
      min_matches: 1
      sources: [company, molecule]
      description: "Au moins une company OU une molecule doit être détectée"

# Règle pour les domaines de type "regulatory"
# Exemple : regulatory_lai, regulatory_oncology, etc.
regulatory:
  match_mode: any_required
  description: "Pour un domaine regulatory, l'item doit contenir au moins une entité (company, molecule ou technology)"
  dimensions:
    company:
      requirement: optional
      description: "Company optionnelle"
    molecule:
      requirement: optional
      description: "Molecule optionnelle"
    technology:
      requirement: optional
      description: "Technology optionnelle"

# Règle par défaut (si le type de domaine n'est pas défini ci-dessus)
# Logique OR classique : au moins une dimension doit matcher
default:
  match_mode: any_required
  description: "Règle par défaut : au moins une dimension doit matcher (logique OR)"
  dimensions:
    company:
      requirement: optional
    molecule:
      requirement: optional
    technology:
      requirement: optional
    indication:
      requirement: optional
```

---

### 2.2 Chargement des Règles de Matching

Le module `config/resolver.py` doit charger ce fichier au même titre que les scopes.

**Ajout dans `config/resolver.py`** :
```python
def load_matching_rules(config_bucket: str) -> Dict[str, Any]:
    """
    Charge les règles de matching depuis canonical/matching/domain_matching_rules.yaml
    
    Returns:
        Dict avec les règles par type de domaine
    """
    s3 = boto3.client('s3')
    key = 'canonical/matching/domain_matching_rules.yaml'
    
    try:
        response = s3.get_object(Bucket=config_bucket, Key=key)
        rules = yaml.safe_load(response['Body'].read())
        logger.info(f"Règles de matching chargées : {list(rules.keys())}")
        return rules
    except Exception as e:
        logger.warning(f"Impossible de charger {key}, utilisation de la règle par défaut : {e}")
        # Règle par défaut : logique OR classique
        return {
            'default': {
                'match_mode': 'any_required',
                'dimensions': {
                    'company': {'requirement': 'optional'},
                    'molecule': {'requirement': 'optional'},
                    'technology': {'requirement': 'optional'},
                    'indication': {'requirement': 'optional'}
                }
            }
        }
```

---

## 3. Adaptation du Matcher

### 3.1 Nouvelle Signature de `match_items_to_domains`

```python
def match_items_to_domains(
    normalized_items: List[Dict[str, Any]],
    watch_domains: List[Dict[str, Any]],
    canonical_scopes: Dict[str, Any],
    matching_rules: Dict[str, Any]  # ← NOUVEAU
) -> List[Dict[str, Any]]:
```

---

### 3.2 Logique de Matching Générique

```python
def match_items_to_domains(
    normalized_items: List[Dict[str, Any]],
    watch_domains: List[Dict[str, Any]],
    canonical_scopes: Dict[str, Any],
    matching_rules: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Détermine quels items correspondent à quels watch_domains.
    Utilise les règles de matching définies dans canonical/matching/domain_matching_rules.yaml
    """
    import logging
    logger = logging.getLogger(__name__)
    
    for item in normalized_items:
        matched_domains = []
        
        # Extraire les entités détectées dans l'item
        item_companies = set(item.get('companies_detected', []))
        item_molecules = set(item.get('molecules_detected', []))
        item_technologies = set(item.get('technologies_detected', []))
        item_indications = set(item.get('indications_detected', []))
        
        # Pour chaque watch_domain
        for domain in watch_domains:
            domain_id = domain.get('id')
            domain_type = domain.get('type', 'default')
            
            # Charger les scopes référencés par ce domaine
            company_scope_key = domain.get('company_scope')
            molecule_scope_key = domain.get('molecule_scope')
            technology_scope_key = domain.get('technology_scope')
            indication_scope_key = domain.get('indication_scope')
            
            # Construire les ensembles de référence depuis les scopes canonical
            scope_companies = set()
            if company_scope_key:
                scope_companies = set(canonical_scopes.get('companies', {}).get(company_scope_key, []))
            
            scope_molecules = set()
            if molecule_scope_key:
                scope_molecules = set(canonical_scopes.get('molecules', {}).get(molecule_scope_key, []))
            
            scope_technologies = set()
            if technology_scope_key:
                scope_technologies = set(canonical_scopes.get('technologies', {}).get(technology_scope_key, []))
            
            scope_indications = set()
            if indication_scope_key:
                scope_indications = set(canonical_scopes.get('indications', {}).get(indication_scope_key, []))
            
            # Calculer les intersections
            companies_match = compute_intersection(item_companies, scope_companies)
            molecules_match = compute_intersection(item_molecules, scope_molecules)
            technologies_match = compute_intersection(item_technologies, scope_technologies)
            indications_match = compute_intersection(item_indications, scope_indications)
            
            # Appliquer les règles de matching pour ce type de domaine
            rule = matching_rules.get(domain_type, matching_rules.get('default'))
            
            if _evaluate_matching_rule(
                rule=rule,
                companies_match=companies_match,
                molecules_match=molecules_match,
                technologies_match=technologies_match,
                indications_match=indications_match
            ):
                matched_domains.append(domain_id)
                logger.debug(f"Item '{item.get('title', '')[:50]}...' matché au domaine {domain_id} (type: {domain_type})")
        
        # Annoter l'item avec les domaines matchés
        item['matched_domains'] = matched_domains
    
    return normalized_items


def _evaluate_matching_rule(
    rule: Dict[str, Any],
    companies_match: Set[str],
    molecules_match: Set[str],
    technologies_match: Set[str],
    indications_match: Set[str]
) -> bool:
    """
    Évalue si un item satisfait une règle de matching.
    
    Args:
        rule: Règle de matching (depuis domain_matching_rules.yaml)
        companies_match: Companies matchées
        molecules_match: Molecules matchées
        technologies_match: Technologies matchées
        indications_match: Indications matchées
    
    Returns:
        True si l'item satisfait la règle, False sinon
    """
    match_mode = rule.get('match_mode', 'any_required')
    dimensions = rule.get('dimensions', {})
    
    # Construire un dict des matches par dimension
    matches = {
        'company': companies_match,
        'molecule': molecules_match,
        'technology': technologies_match,
        'indication': indications_match
    }
    
    # Évaluer chaque dimension
    dimension_results = {}
    
    for dim_name, dim_config in dimensions.items():
        requirement = dim_config.get('requirement', 'optional')
        min_matches = dim_config.get('min_matches', 1)
        
        # Cas spécial : dimension "entity" = company OR molecule
        if dim_name == 'entity':
            sources = dim_config.get('sources', ['company', 'molecule'])
            entity_matches = set()
            for source in sources:
                entity_matches.update(matches.get(source, set()))
            
            has_match = len(entity_matches) >= min_matches
        else:
            # Dimension simple
            has_match = len(matches.get(dim_name, set())) >= min_matches
        
        dimension_results[dim_name] = {
            'has_match': has_match,
            'requirement': requirement
        }
    
    # Appliquer la logique de combinaison
    if match_mode == 'all_required':
        # Toutes les dimensions "required" doivent matcher
        for dim_name, result in dimension_results.items():
            if result['requirement'] == 'required' and not result['has_match']:
                return False
        return True
    
    elif match_mode == 'any_required':
        # Au moins une dimension doit matcher
        for dim_name, result in dimension_results.items():
            if result['has_match']:
                return True
        return False
    
    else:
        # Mode inconnu, fallback sur any_required
        for dim_name, result in dimension_results.items():
            if result['has_match']:
                return True
        return False
```

---

### 3.3 Enrichissement de la Structure de Sortie

Pour faciliter les diagnostics, on enrichit l'item avec des détails sur les matches :

```python
# Dans match_items_to_domains, après avoir calculé les intersections :
item['matching_details'] = {
    'companies_matched': list(companies_match),
    'molecules_matched': list(molecules_match),
    'technologies_matched': list(technologies_match),
    'indications_matched': list(indications_match),
    'domain_type': domain_type,
    'rule_applied': rule.get('description', 'N/A')
}
```

---

## 4. Adaptation du Scorer

### 4.1 Bonus Pure Players : Générique via Scopes

Au lieu de coder en dur la liste des pure players LAI dans `scoring_rules.yaml`, on utilise un **scope canonical**.

**Nouveau scope dans `canonical/scopes/company_scopes.yaml`** :
```yaml
# Pure players LAI pour le MVP (focus strict sur les 5 entreprises pilotes).
lai_companies_mvp_core:
  - MedinCell
  - Camurus
  - DelSiTech
  - Nanexa
  - Peptron
```

**Modification de `canonical/scoring/scoring_rules.yaml`** :
```yaml
other_factors:
  # Bonus pour les pure players (défini par un scope canonical)
  pure_player_bonus: 3
  pure_player_scope: "lai_companies_mvp_core"  # ← Référence à un scope
```

**Adaptation de `scorer.py`** :
```python
def compute_score(
    item: Dict[str, Any],
    scoring_rules: Dict[str, Any],
    domain_priority: str,
    canonical_scopes: Dict[str, Any]  # ← NOUVEAU
) -> float:
    # ... (scoring actuel)
    
    # Facteur 6 : Bonus pure player (générique via scope)
    pure_player_scope_key = scoring_rules.get('other_factors', {}).get('pure_player_scope')
    pure_player_bonus_value = scoring_rules.get('other_factors', {}).get('pure_player_bonus', 0)
    
    pure_player_bonus = 0
    if pure_player_scope_key:
        pure_players = set(canonical_scopes.get('companies', {}).get(pure_player_scope_key, []))
        item_companies = set(item.get('companies_detected', []))
        
        if item_companies & pure_players:  # Intersection non vide
            pure_player_bonus = pure_player_bonus_value
    
    # Formule de scoring
    base_score = event_weight * priority_weight * recency_factor * source_weight
    final_score = base_score + signal_depth_bonus + pure_player_bonus
    
    return round(final_score, 2)
```

---

## 5. Impacts sur les Diagnostics

### 5.1 Logs de Matching

Les logs doivent expliquer **pourquoi** un item a matché ou non :

```python
logger.debug(
    f"Item '{item.get('title', '')[:50]}...' : "
    f"domain={domain_id}, type={domain_type}, "
    f"companies={len(companies_match)}, molecules={len(molecules_match)}, "
    f"technologies={len(technologies_match)}, indications={len(indications_match)}, "
    f"rule={rule.get('description', 'N/A')}, matched={matched}"
)
```

---

### 5.2 Fichier de Diagnostic

Le diagnostic doit inclure :
- Liste des items sélectionnés avec leurs `matching_details`
- Proportion de pure players vs big pharma
- Justification des matches (quels scopes ont matché, quels mots-clés)

**Template de diagnostic** :
```markdown
## Items Sélectionnés

| # | Titre | Companies | Molecules | Technologies | Pure Player ? | Score |
|---|-------|-----------|-----------|--------------|---------------|-------|
| 1 | MedinCell UZEDY Approval | MedinCell | risperidone | extended-release injectable | ✅ | 25.3 |
| 2 | Pfizer Hympavzi Data | Pfizer | - | - | ❌ | 12.1 |

## Analyse des Matches

### Item 1 : MedinCell UZEDY Approval
- **Domain type** : technology
- **Rule applied** : "Pour un domaine technology, l'item doit contenir au moins un mot-clé technology ET au moins une entité"
- **Companies matched** : MedinCell (pure player ✅)
- **Molecules matched** : risperidone
- **Technologies matched** : extended-release injectable
- **Verdict** : ✅ MATCH (technology + entity)

### Item 2 : Pfizer Hympavzi Data
- **Domain type** : technology
- **Rule applied** : "Pour un domaine technology, l'item doit contenir au moins un mot-clé technology ET au moins une entité"
- **Companies matched** : Pfizer
- **Molecules matched** : -
- **Technologies matched** : -
- **Verdict** : ❌ NO MATCH (entity présente mais technology absente)
```

---

## 6. Définition de Done pour le MVP LAI

### 6.1 Critères de Succès

Pour valider le refactor, la newsletter `lai_weekly` doit respecter :

| Critère | Objectif | Mesure |
|---------|----------|--------|
| **Précision LAI** | ≥ 80% des items sélectionnés sont clairement LAI | Lecture humaine |
| **Représentation pure players** | ≥ 50% des items concernent des pure players LAI | Comptage automatique via `lai_companies_mvp_core` |
| **Zéro faux positif big pharma** | Aucun item big pharma sans contexte LAI | Lecture humaine |
| **Couverture pure players** | 100% des news LAI de pure players capturées | Vérification manuelle |

---

### 6.2 Tests de Non-Régression

Pour s'assurer que le refactor ne casse rien :

1. **Test avec `lai_weekly`** : Vérifier que les items LAI authentiques (MedinCell UZEDY, etc.) sont toujours sélectionnés
2. **Test avec un domaine `regulatory`** : Vérifier que la logique OR classique fonctionne toujours
3. **Test avec un domaine `indication`** (futur) : Vérifier que la règle `indication` fonctionne

---

## 7. Plan d'Implémentation

### Phase 1 : Création du Fichier de Règles

1. Créer `canonical/matching/domain_matching_rules.yaml` avec les règles pour `technology`, `indication`, `regulatory`, `default`
2. Uploader le fichier dans S3 (`s3://vectora-inbox-config-dev/canonical/matching/domain_matching_rules.yaml`)

---

### Phase 2 : Adaptation du Code

1. **`config/resolver.py`** : Ajouter `load_matching_rules()`
2. **`matching/matcher.py`** : 
   - Ajouter le paramètre `matching_rules` à `match_items_to_domains()`
   - Implémenter `_evaluate_matching_rule()`
   - Enrichir la structure de sortie avec `matching_details`
3. **`scoring/scorer.py`** :
   - Ajouter le paramètre `canonical_scopes` à `compute_score()`
   - Remplacer la liste hardcodée de pure players par une référence à un scope
4. **`src/vectora_core/__init__.py`** (orchestration) :
   - Charger les matching rules via `load_matching_rules()`
   - Passer les matching rules au matcher
   - Passer les canonical scopes au scorer

---

### Phase 3 : Tests & Diagnostics

1. Re-packager et redéployer la Lambda engine en DEV
2. Re-lancer un run complet pour `lai_weekly` sur 7 jours
3. Créer le diagnostic `docs/diagnostics/vectora_inbox_lai_mvp_matching_refactor_results.md`
4. Vérifier les critères de Done (précision LAI, pure players, faux positifs)

---

### Phase 4 : Documentation

1. Mettre à jour `CHANGELOG.md` avec le statut final (GREEN ou AMBER)
2. Mettre à jour `docs/diagnostics/lai_weekly_mvp_recentrage_summary.md` avec la nouvelle décision (Accepté / À affiner)
3. Créer un README dans `canonical/matching/` pour expliquer le système de règles

---

## 8. Extensibilité : Autres Verticaux

### 8.1 Exemple : Oncologie

Pour ajouter un vertical oncologie, il suffit de :

1. **Créer les scopes** dans `canonical/scopes/` :
   - `oncology_companies_global`
   - `oncology_molecules_global`
   - `oncology_keywords`

2. **Créer une config client** `oncology_weekly.yaml` :
```yaml
watch_domains:
  - id: "tech_oncology_ecosystem"
    type: "technology"
    technology_scope: "oncology_keywords"
    company_scope: "oncology_companies_global"
    molecule_scope: "oncology_molecules_global"
    priority: "high"
```

3. **Aucune modification du code** : Les règles de matching pour `type: technology` s'appliquent automatiquement.

---

### 8.2 Exemple : Diabète avec Logique Spécifique

Si le vertical diabète nécessite une logique différente (ex: technology OU indication, sans contrainte AND), on ajoute une nouvelle règle :

```yaml
# Dans canonical/matching/domain_matching_rules.yaml
diabetes_technology:
  match_mode: any_required
  description: "Pour un domaine diabetes_technology, l'item doit contenir technology OU indication"
  dimensions:
    technology:
      requirement: optional
    indication:
      requirement: optional
    entity:
      requirement: required
      min_matches: 1
      sources: [company, molecule]
```

Et dans la config client :
```yaml
watch_domains:
  - id: "tech_diabetes_ecosystem"
    type: "diabetes_technology"  # ← Type personnalisé
    technology_scope: "diabetes_keywords"
    indication_scope: "diabetes_indications"
    company_scope: "diabetes_companies_global"
    priority: "high"
```

---

## 9. Risques & Mitigations

| Risque | Impact | Mitigation |
|--------|--------|------------|
| **Règles trop strictes** | Perte de rappel (items LAI manqués) | Ajuster `min_matches` ou ajouter des dimensions `optional` |
| **Règles trop permissives** | Faux positifs (items non-LAI sélectionnés) | Renforcer les contraintes `required` |
| **Complexité accrue** | Difficulté de maintenance | Documentation claire + exemples + tests |
| **Performance** | Temps d'exécution accru | Optimiser les intersections d'ensembles (déjà O(n)) |

---

## 10. Prochaines Étapes

1. ✅ **Plan de refactor** : Complété (ce document)
2. ⏳ **Implémentation** : Créer le fichier de règles + adapter le code
3. ⏳ **Tests** : Re-lancer un run LAI et valider les critères de Done
4. ⏳ **Documentation** : Créer le diagnostic de résultats + mettre à jour CHANGELOG

---

**Auteur** : Amazon Q Developer  
**Date** : 2025-12-08  
**Version** : 1.0
