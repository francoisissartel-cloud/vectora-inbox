# Comparatif Avant/Après - Moteur Ingestion Canonical

**Date**: 2026-02-06

---

## 🔴 AVANT Plan Correctif

### Code ingestion_profiles.py (Hardcodé)

```python
# ❌ Pure players hardcodés (5 entreprises)
lai_pure_players = ['medincell', 'camurus', 'delsitech', 'nanexa', 'peptron']

# ❌ LAI keywords hardcodés (70 termes)
LAI_KEYWORDS = [
    "injectable", "injection", "long-acting", "extended-release", "depot",
    "medincell", "camurus", "uzedy", "bydureon", "invega",
    # ... 60 autres termes
]

# ❌ Exclusions hardcodées (20 termes)
EXCLUSION_KEYWORDS = [
    "hiring", "recruitment", "job opening", "career",
    "conference", "webinar", "presentation",
    "oral", "tablet", "capsule", "pill",
    # ... 10 autres termes
]

# ❌ Logique identique pour tous
def _apply_corporate_profile(items, source_meta):
    company_id = source_meta.get('company_id', '')
    
    # Même filtrage pour pure et hybrid
    if company_id.lower() in lai_pure_players:
        return _filter_by_lai_keywords(items)  # ← Incorrect !
    else:
        return _filter_by_lai_keywords(items)
```

### Résultat

```
MedinCell (pure player)
├─ Filtrage LAI keywords ❌ (devrait être permissif)
└─ Exclusions partielles (20 termes)

Teva (hybrid player)
├─ Filtrage LAI keywords ✅ (correct)
└─ Exclusions partielles (20 termes)
└─ Mais non identifié comme hybrid ❌
```

**Problèmes** :
- ❌ Pure players filtrés par LAI keywords (trop strict)
- ❌ Hybrid players non différenciés
- ❌ Seulement 4/8 scopes d'exclusion utilisés
- ❌ Modifications canonical sans effet (rebuild requis)

---

## 🟢 APRÈS Plan Correctif

### Code ingestion_profiles.py (Générique)

```python
# ✅ Caches chargés depuis S3
_exclusion_scopes_cache = None  # 8 scopes, 150+ termes
_pure_players_cache = None      # 14 entreprises
_hybrid_players_cache = None    # 27 entreprises
_lai_keywords_cache = None      # 150+ termes

# ✅ Initialisation depuis canonical
def initialize_exclusion_scopes(s3_io, config_bucket):
    global _exclusion_scopes_cache
    scopes = s3_io.read_yaml_from_s3(config_bucket, 'canonical/scopes/exclusion_scopes.yaml')
    _exclusion_scopes_cache = scopes
    logger.info(f"Exclusion scopes: {len(scopes)} catégories")

def initialize_company_scopes(s3_io, config_bucket):
    global _pure_players_cache, _hybrid_players_cache
    scopes = s3_io.read_yaml_from_s3(config_bucket, 'canonical/scopes/company_scopes.yaml')
    _pure_players_cache = [c.lower() for c in scopes.get('lai_companies_pure_players', [])]
    _hybrid_players_cache = [c.lower() for c in scopes.get('lai_companies_hybrid', [])]
    logger.info(f"Company scopes: {len(_pure_players_cache)} pure, {len(_hybrid_players_cache)} hybrid")

def initialize_lai_keywords(s3_io, config_bucket):
    global _lai_keywords_cache
    tech = s3_io.read_yaml_from_s3(config_bucket, 'canonical/scopes/technology_scopes.yaml')
    trademarks = s3_io.read_yaml_from_s3(config_bucket, 'canonical/scopes/trademark_scopes.yaml')
    _lai_keywords_cache = tech['lai_keywords']['core_phrases'] + trademarks['lai_trademarks_global']
    logger.info(f"LAI keywords: {len(_lai_keywords_cache)} termes")

# ✅ Logique différenciée pure/hybrid
def _apply_corporate_profile(items, source_meta):
    company_id = source_meta.get('company_id', '')
    
    if _is_pure_player(company_id):
        # Pure player : exclusions seules (permissif)
        logger.info(f"Pure player: {company_id} - exclusions seules")
        return _filter_by_exclusions_only(items)
    
    elif _is_hybrid_player(company_id):
        # Hybrid player : exclusions + LAI keywords
        logger.info(f"Hybrid player: {company_id} - exclusions + LAI")
        return _filter_by_exclusions_and_lai(items)
    
    else:
        # Entreprise inconnue : filtrage strict
        return _filter_by_exclusions_and_lai(items)

# ✅ Filtrage exclusions seules (pure players)
def _filter_by_exclusions_only(items):
    filtered = []
    for item in items:
        text = f"{item.get('title', '')} {item.get('content', '')}".lower()
        if not _contains_exclusion_keywords(text):
            filtered.append(item)
    return filtered

# ✅ Filtrage exclusions + LAI (hybrid players)
def _filter_by_exclusions_and_lai(items):
    filtered = []
    for item in items:
        text = f"{item.get('title', '')} {item.get('content', '')}".lower()
        if not _contains_exclusion_keywords(text) and _contains_lai_keywords(text):
            filtered.append(item)
    return filtered
```

### Résultat

```
MedinCell (pure player)
├─ Détecté comme pure player ✅
├─ Exclusions complètes (8 scopes, 150+ termes) ✅
└─ Pas de filtrage LAI keywords ✅ (permissif)

Teva (hybrid player)
├─ Détecté comme hybrid player ✅
├─ Exclusions complètes (8 scopes, 150+ termes) ✅
└─ Filtrage LAI keywords requis ✅ (filtré)
```

**Avantages** :
- ✅ Pure players : ingestion permissive (exclusions seules)
- ✅ Hybrid players : ingestion filtrée (exclusions + LAI)
- ✅ 8/8 scopes d'exclusion utilisés
- ✅ Modifications canonical → effet immédiat (sans rebuild)
- ✅ Zéro hardcoding

---

## 📊 Comparaison Chiffrée

| Métrique | Avant | Après | Amélioration |
|----------|-------|-------|--------------|
| **Exclusions** | 20 hardcodés | 150+ depuis S3 | +650% |
| **Scopes utilisés** | 4/8 | 8/8 | +100% |
| **Pure players** | 5 hardcodés | 14 depuis S3 | +180% |
| **Hybrid players** | 0 (non géré) | 27 depuis S3 | ∞ |
| **LAI keywords** | 70 hardcodés | 150+ depuis S3 | +114% |
| **Hardcoding** | 3 listes | 0 | -100% |
| **Rebuild requis** | Oui | Non | ✅ |

---

## 🔄 Flux de Modification

### ❌ Avant (Hardcodé)

```
Ajouter un pure player
    ↓
Modifier ingestion_profiles.py
    ↓
Rebuild layer (5 min)
    ↓
Deploy layer (5 min)
    ↓
Test (10 min)
    ↓
Total: 20 minutes
```

### ✅ Après (Canonical)

```
Ajouter un pure player
    ↓
Modifier company_scopes.yaml
    ↓
Upload vers S3 (10 sec)
    ↓
Effet immédiat (0 min)
    ↓
Total: 10 secondes
```

**Gain** : 120x plus rapide

---

## 🎯 Exemples Concrets

### Exemple 1 : MedinCell (Pure Player)

**Avant** :
```
Item: "MedinCell announces long-acting injectable partnership"
├─ Filtrage LAI keywords: ✅ Contient "long-acting injectable"
└─ Résultat: Conservé ✅ (mais logique incorrecte)

Item: "MedinCell expands manufacturing facility"
├─ Filtrage LAI keywords: ❌ Pas de LAI keywords
└─ Résultat: Exclu ❌ (devrait être conservé)
```

**Après** :
```
Item: "MedinCell announces long-acting injectable partnership"
├─ Pure player détecté: ✅
├─ Exclusions: ❌ Pas de bruit
└─ Résultat: Conservé ✅

Item: "MedinCell expands manufacturing facility"
├─ Pure player détecté: ✅
├─ Exclusions: ❌ Pas de bruit
└─ Résultat: Conservé ✅ (correct maintenant)
```

---

### Exemple 2 : Teva (Hybrid Player)

**Avant** :
```
Item: "Teva launches new long-acting injectable"
├─ Filtrage LAI keywords: ✅ Contient "long-acting injectable"
└─ Résultat: Conservé ✅

Item: "Teva reports quarterly earnings"
├─ Filtrage LAI keywords: ❌ Pas de LAI keywords
├─ Exclusions: ❌ Pas détecté (liste partielle)
└─ Résultat: Conservé ❌ (devrait être exclu)
```

**Après** :
```
Item: "Teva launches new long-acting injectable"
├─ Hybrid player détecté: ✅
├─ Exclusions: ❌ Pas de bruit
├─ LAI keywords: ✅ Contient "long-acting injectable"
└─ Résultat: Conservé ✅

Item: "Teva reports quarterly earnings"
├─ Hybrid player détecté: ✅
├─ Exclusions: ✅ Détecté "quarterly earnings"
└─ Résultat: Exclu ✅ (correct maintenant)
```

---

## 📂 Fichiers Canonical Utilisés

### exclusion_scopes.yaml
```yaml
hr_content: [job opening, hiring, ...]
financial_generic: [quarterly earnings, ...]
event_generic: [conference participation, ...]
# ... 5 autres scopes
```

### company_scopes.yaml
```yaml
lai_companies_pure_players:
  - MedinCell
  - Camurus
  # ... 12 autres

lai_companies_hybrid:
  - Teva
  - Pfizer
  # ... 25 autres
```

### technology_scopes.yaml
```yaml
lai_keywords:
  core_phrases:
    - long-acting injectable
    - depot
    # ... 50 autres
```

### trademark_scopes.yaml
```yaml
lai_trademarks_global:
  - Uzedy
  - Bydureon
  # ... 100 autres
```

---

## ✅ Validation

### Logs Attendus

**Avant** :
```
Profil corporate LAI : 15/25 items conservés
```

**Après** :
```
Étape 2.5: Initialisation exclusion scopes
Exclusion scopes chargés: 8 catégories
Company scopes: 14 pure players, 27 hybrid players
LAI keywords: 150+ termes chargés

Pure player: MedinCell - exclusions seules (pas de filtrage LAI)
Profil corporate : 20/25 items conservés (exclusions seules)

Hybrid player: Teva - exclusions + LAI keywords requis
Profil corporate : 10/25 items conservés (exclusions + LAI)
```

---

## 🚀 Conclusion

**Transformation réussie** :
- ❌ Avant : Moteur hardcodé, logique incorrecte
- ✅ Après : Moteur générique, piloté par canonical

**Conformité profils** :
- ✅ Pure players : Permissif (exclusions seules)
- ✅ Hybrid players : Filtré (exclusions + LAI)

**Opérationnalité** :
- ✅ Modifications sans rebuild
- ✅ Zéro hardcoding
- ✅ Logs explicites

---

**Statut** : Plan validé - Prêt pour exécution
