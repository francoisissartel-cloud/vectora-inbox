# Diagnostic : Ajustement Scoring Recency - Résultats

## Résumé des Modifications

**Date :** 2025-01-15  
**Objectif :** Neutralisation du recency_factor pour les pipelines weekly (≤7 jours)

### Fichiers Modifiés

#### 1. `src/vectora_core/scoring/scorer.py`
- **Fonction `_compute_recency_factor()`** : Ajout paramètre `period_days`
- **Neutralisation weekly** : `recency_factor = 1.0` si `period_days <= 7`
- **Signatures mises à jour** : `score_items()` et `compute_score()` avec `period_days`

#### 2. `src/vectora_core/__init__.py`
- **Appel scorer** : Passage du paramètre `period_days` dans `run_engine_for_client()`

## Logique de Neutralisation

### Problème Identifié

**Pipeline weekly (7 jours) :**
- Tous les items ingérés sont récents (0-7 jours d'ancienneté)
- `recency_factor` varie de 1.0 à ~0.5 sur cette courte période
- Impact disproportionné vs facteurs métier (event_type, pure_player, etc.)

### Solution Implémentée

```python
def _compute_recency_factor(item_date: str, half_life_days: int, period_days: int = None) -> float:
    # Neutralisation pour les pipelines weekly (7 jours ou moins)
    if period_days and period_days <= 7:
        return 1.0  # Facteur neutre - récence non discriminante
    
    # Logique existante pour pipelines plus longs
    # ...
```

### Comportement par Type de Pipeline

| Pipeline Type | period_days | recency_factor | Impact |
|---------------|-------------|----------------|---------|
| **Weekly** | ≤ 7 | **1.0** (neutre) | ✅ Neutralisé |
| **Monthly** | 30 | 1.0 → 0.125 | ✅ Discriminant |
| **Quarterly** | 90 | 1.0 → 0.008 | ✅ Très discriminant |

## Nouveau Calcul de Score

### Formule Inchangée
```
base_score = event_weight × priority_weight × recency_factor × source_weight
final_score = (base_score × confidence_multiplier) + bonuses - penalties
```

### Impact sur Weekly (period_days = 7)

**Avant :**
```python
# Item récent (1 jour)
recency_factor = 0.9  # Léger avantage

# Item moins récent (7 jours)  
recency_factor = 0.5  # Pénalité significative

# Variation : 0.9 → 0.5 (facteur 1.8x)
```

**Après :**
```python
# Tous les items weekly
recency_factor = 1.0  # Neutre

# Variation : 1.0 → 1.0 (aucune)
```

### Drivers Principaux du Score Weekly

Avec `recency_factor = 1.0`, le score est maintenant dominé par :

1. **event_type_weight** (1-6) : Type d'événement
2. **domain_priority_weight** (1-3) : Priorité du domaine
3. **source_weight** (1-2) : Type de source
4. **pure_player_bonus** (+3) : Bonus entreprises pure-play
5. **signal_quality_score** (0-4) : Qualité des signaux matchés
6. **match_confidence_multiplier** (1.0-1.5) : Confiance du matching

## Exemples de Scoring

### Cas 1 : Item Pure Player Clinical Update

```python
# Paramètres
event_type = "clinical_update"          # weight = 5
domain_priority = "high"                # weight = 3  
source_type = "press_corporate"         # weight = 2
recency_factor = 1.0                    # ✅ NEUTRALISÉ
pure_player_bonus = 3
confidence_multiplier = 1.5

# Calcul
base_score = 5 × 3 × 1.0 × 2 = 30
final_score = (30 × 1.5) + 3 = 48
```

### Cas 2 : Item Hybrid Partnership

```python
# Paramètres  
event_type = "partnership"              # weight = 6
domain_priority = "medium"              # weight = 2
source_type = "sector"                  # weight = 1.5
recency_factor = 1.0                    # ✅ NEUTRALISÉ
hybrid_company_bonus = 1
confidence_multiplier = 1.2

# Calcul
base_score = 6 × 2 × 1.0 × 1.5 = 18
final_score = (18 × 1.2) + 1 = 22.6
```

## Impact Métier

### Avantages

1. **Cohérence weekly** : Récence non discriminante sur fenêtre courte
2. **Focus métier** : Score dominé par pertinence business
3. **Prévisibilité** : Comportement stable indépendant de l'heure d'exécution

### Tie-Breaking

En cas d'égalité de score, l'ordre peut être déterminé par :
- Ordre alphabétique des titres
- Date de publication (plus récent en premier)
- Source (corporate > sector > generic)

## Rétrocompatibilité

### Pipelines Existants

- **Monthly/Quarterly** : Comportement inchangé (recency_factor discriminant)
- **Weekly** : Nouveau comportement (recency_factor neutralisé)
- **API** : Paramètre `period_days` optionnel (défaut = comportement existant)

### Migration

Aucune migration nécessaire :
- Paramètre `period_days` optionnel
- Valeur par défaut = comportement existant
- Seuls les appels avec `period_days <= 7` sont affectés

## Tests Recommandés

### 1. Tests Unitaires
```python
def test_recency_factor_weekly_neutralized():
    # period_days = 7 → recency_factor = 1.0
    assert _compute_recency_factor("2025-01-10", 7, 7) == 1.0
    assert _compute_recency_factor("2025-01-15", 7, 7) == 1.0

def test_recency_factor_monthly_unchanged():
    # period_days = 30 → comportement existant
    factor = _compute_recency_factor("2025-01-01", 7, 30)
    assert 0.1 <= factor <= 1.0
```

### 2. Tests d'Intégration
- Scoring complet avec `period_days = 7`
- Vérification ordre des items par score
- Comparaison avant/après neutralisation

## Prochaines Étapes

1. **Tests locaux** : Validation du nouveau comportement
2. **Métriques** : Monitoring distribution des scores weekly
3. **Feedback utilisateurs** : Qualité du ranking des items
4. **Ajustements** : Fine-tuning autres facteurs si nécessaire

---

**Statut :** ✅ Implémenté  
**Tests :** En attente  
**Impact :** Weekly pipelines uniquement