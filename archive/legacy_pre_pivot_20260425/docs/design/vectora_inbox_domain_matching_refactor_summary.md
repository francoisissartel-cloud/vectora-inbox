# Résumé – Refactor Matching Générique Piloté par Config/Canonical

**Date** : 2025-12-08  
**Auteur** : Amazon Q Developer  
**Statut** : 🟡 AMBER - Implémentation complétée, tests en attente

---

## Objectif

Rendre le matching 100% générique et piloté par config/canonical, sans aucune logique métier LAI codée en dur, pour résoudre le problème de 0% de précision LAI dans la newsletter `lai_weekly`.

---

## Problème Initial

**Symptôme** : Newsletter `lai_weekly` contient 0% d'items LAI authentiques (5/5 items sont des faux positifs big pharma).

**Cause racine** : Le matcher est trop permissif. Il sélectionne des items dès qu'une company match (ex: Pfizer, AbbVie) sans vérifier que le contenu parle vraiment de la technology LAI.

**Exemple de faux positif** :
- Item : "AbbVie revs up Skyrizi spending to top TV ad totals"
- Company matchée : AbbVie (présente dans `lai_companies_global`)
- Technology LAI mentionnée : **AUCUNE**
- Résultat : Item sélectionné ❌ (faux positif)

---

## Solution Implémentée

### Principe Clé

**Aucun `if domain.id == "tech_lai_ecosystem"` dans le code.**

Tout est piloté par des **règles de matching déclaratives** dans `canonical/matching/domain_matching_rules.yaml`.

---

### Architecture de la Solution

```
canonical/matching/domain_matching_rules.yaml
    ↓
config/resolver.py → load_matching_rules()
    ↓
matching/matcher.py → _evaluate_matching_rule()
    ↓
Décision : MATCH ou NO MATCH
```

---

### Fichier de Règles : `canonical/matching/domain_matching_rules.yaml`

**Règle pour domaine `technology`** (ex: `tech_lai_ecosystem`) :

```yaml
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
```

**Interprétation** :
- `match_mode: all_required` → Les deux dimensions doivent être satisfaites (AND logique)
- `technology.requirement: required` → Au moins 1 mot-clé de `lai_keywords` doit être détecté
- `entity.requirement: required` → Au moins 1 company OU 1 molecule doit être détectée

**Résultat attendu** :
- ✅ Item avec `MedinCell` + `extended-release injectable` → MATCH
- ❌ Item avec `Pfizer` seul (sans mot-clé technology) → NO MATCH
- ❌ Item avec `long-acting` seul (sans company/molecule) → NO MATCH

---

### Règles pour Autres Types de Domaines

**Domaine `regulatory`** : Logique OR classique (au moins une entité)

```yaml
regulatory:
  match_mode: any_required
  dimensions:
    company:
      requirement: optional
    molecule:
      requirement: optional
    technology:
      requirement: optional
```

**Domaine `indication`** : Technology + Entity (même logique que `technology`)

```yaml
indication:
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

## Modifications du Code

### 1. `config/resolver.py`

**Ajout** : Fonction `load_matching_rules()` pour charger les règles depuis S3.

```python
def load_matching_rules(config_bucket: str) -> Dict[str, Any]:
    """
    Charge les règles de matching depuis canonical/matching/domain_matching_rules.yaml
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
        return { 'default': { ... } }
```

---

### 2. `matching/matcher.py`

**Modification** : Remplacement de la logique codée en dur par l'évaluation des règles.

**Avant** :
```python
if domain_type == 'technology':
    has_entity = bool(companies_match or molecules_match)
    has_technology = bool(technologies_match)
    
    if has_entity and has_technology:
        matched_domains.append(domain_id)
else:
    if companies_match or molecules_match or technologies_match or indications_match:
        matched_domains.append(domain_id)
```

**Après** :
```python
domain_type = domain.get('type', 'default')
rule = matching_rules.get(domain_type, matching_rules.get('default'))

if _evaluate_matching_rule(
    rule=rule,
    companies_match=companies_match,
    molecules_match=molecules_match,
    technologies_match=technologies_match,
    indications_match=indications_match
):
    matched_domains.append(domain_id)
```

**Ajout** : Fonction `_evaluate_matching_rule()` pour évaluer les règles de manière générique.

---

### 3. `scoring/scorer.py`

**Modification** : Remplacement de la liste hardcodée de pure players par une référence à un scope.

**Avant** :
```python
pure_players = other_factors.get('pure_players_lai', [])
item_companies = item.get('companies_detected', [])

if any(company in pure_players for company in item_companies):
    pure_player_bonus = other_factors.get('pure_player_lai_bonus', 0)
```

**Après** :
```python
pure_player_scope_key = other_factors.get('pure_player_scope')
pure_player_bonus_value = other_factors.get('pure_player_bonus', 0)

if pure_player_scope_key:
    pure_players = set(canonical_scopes.get('companies', {}).get(pure_player_scope_key, []))
    item_companies = set(item.get('companies_detected', []))
    
    if item_companies & pure_players:  # Intersection non vide
        pure_player_bonus = pure_player_bonus_value
```

---

### 4. `canonical/scoring/scoring_rules.yaml`

**Modification** : Remplacement de la liste hardcodée par une référence à un scope.

**Avant** :
```yaml
pure_player_lai_bonus: 3
pure_players_lai:
  - MedinCell
  - Camurus
  - DelSiTech
  - Nanexa
  - Peptron
```

**Après** :
```yaml
pure_player_bonus: 3
pure_player_scope: "lai_companies_mvp_core"  # Référence à un scope
```

---

### 5. `src/vectora_core/__init__.py`

**Modification** : Chargement et passage des matching rules au matcher.

```python
# Charger les matching rules
matching_rules = resolver.load_matching_rules(config_bucket)

# Passer au matcher
matched_items = matcher.match_items_to_domains(all_items, watch_domains, canonical_scopes, matching_rules)

# Passer les canonical_scopes au scorer
scored_items = scorer.score_items(matched_items, scoring_rules, watch_domains, canonical_scopes)
```

---

## Extensibilité Multi-Verticales

Le système est **100% réutilisable** pour d'autres verticaux (oncologie, diabète, etc.) sans modification du code.

### Exemple : Ajouter un Vertical Oncologie

1. **Créer les scopes** dans `canonical/scopes/` :
   - `oncology_companies_global`
   - `oncology_molecules_global`
   - `oncology_keywords`

2. **Créer une config client** `oncology_weekly.yaml` :
```yaml
watch_domains:
  - id: "tech_oncology_ecosystem"
    type: "technology"  # ← Réutilise la règle existante
    technology_scope: "oncology_keywords"
    company_scope: "oncology_companies_global"
    molecule_scope: "oncology_molecules_global"
    priority: "high"
```

3. **Aucune modification du code** : Les règles de matching pour `type: technology` s'appliquent automatiquement.

---

## Critères de Succès (Definition of Done)

Pour valider le refactor, la newsletter `lai_weekly` doit respecter :

| Critère | Objectif | Mesure |
|---------|----------|--------|
| **Précision LAI** | ≥ 80% des items sélectionnés sont clairement LAI | Lecture humaine |
| **Représentation pure players** | ≥ 50% des items concernent des pure players LAI | Comptage automatique via `lai_companies_mvp_core` |
| **Zéro faux positif big pharma** | Aucun item big pharma sans contexte LAI | Lecture humaine |
| **Couverture pure players** | 100% des news LAI de pure players capturées | Vérification manuelle |

---

## Fichiers Créés/Modifiés

### Fichiers Créés

1. `canonical/matching/domain_matching_rules.yaml` - Règles de matching par type de domaine
2. `canonical/matching/README.md` - Documentation du système de règles
3. `scripts/redeploy-engine-matching-refactor.ps1` - Script de redéploiement
4. `scripts/test-engine-matching-refactor.ps1` - Script de test
5. `docs/diagnostics/vectora_inbox_lai_mvp_matching_refactor_results.md` - Template de diagnostic
6. `docs/design/vectora_inbox_domain_matching_refactor_plan.md` - Plan détaillé
7. `docs/design/vectora_inbox_domain_matching_refactor_summary.md` - Ce document

### Fichiers Modifiés

1. `src/vectora_core/config/resolver.py` - Ajout de `load_matching_rules()`
2. `src/vectora_core/matching/matcher.py` - Logique générique avec `_evaluate_matching_rule()`
3. `src/vectora_core/scoring/scorer.py` - Bonus pure players via scope
4. `src/vectora_core/__init__.py` - Orchestration avec matching rules
5. `canonical/scoring/scoring_rules.yaml` - Référence à un scope au lieu d'une liste
6. `CHANGELOG.md` - Entrée pour le refactor
7. `docs/diagnostics/lai_weekly_mvp_recentrage_summary.md` - Mise à jour du statut

---

## Prochaines Étapes

### Phase 3 : Tests & Diagnostics

1. **Redéployer la Lambda engine** :
   ```powershell
   .\scripts\redeploy-engine-matching-refactor.ps1
   ```

2. **Lancer un test complet** :
   ```powershell
   .\scripts\test-engine-matching-refactor.ps1
   ```

3. **Analyser les résultats** :
   - Consulter les logs CloudWatch
   - Vérifier la newsletter générée dans S3
   - Compléter le diagnostic dans `docs/diagnostics/vectora_inbox_lai_mvp_matching_refactor_results.md`

4. **Évaluer les critères de Done** :
   - Précision LAI ≥ 80% ?
   - Pure players ≥ 50% ?
   - Zéro faux positifs ?

5. **Mettre à jour le statut** :
   - Si tous les critères sont atteints : 🟢 GREEN
   - Si certains critères non atteints : 🟡 AMBER (ajustements nécessaires)
   - Si échec critique : 🔴 RED (revoir la stratégie)

---

## Documentation Complémentaire

- **Plan détaillé** : `docs/design/vectora_inbox_domain_matching_refactor_plan.md`
- **README matching** : `canonical/matching/README.md`
- **Diagnostic LAI** : `docs/diagnostics/lai_weekly_mvp_semantic_gap_analysis.md`
- **Plan de recentrage LAI** : `docs/design/vectora_inbox_lai_mvp_focus_plan.md`

---

**Auteur** : Amazon Q Developer  
**Date** : 2025-12-08  
**Version** : 1.0
