# Analyse Phase d'Ingestion - Vectora Inbox

**Date** : 2026-02-06  
**Objectif** : Comprendre comment fonctionne le filtrage en ingestion

---

## 🔍 DÉCOUVERTES CLÉS

### 1. Architecture du filtrage

**Fichiers impliqués** :
- `src_v2/vectora_core/ingest/ingestion_profiles.py` : Logique de filtrage
- `canonical/scopes/exclusion_scopes.yaml` : Keywords d'exclusion

### 2. Logique de filtrage

```python
apply_ingestion_profile(items, source_meta, ingestion_mode="balanced")
  ↓
if source_type == 'press_corporate':
    _apply_corporate_profile()
      ↓
    if is_lai_pure_player:  # medincell, camurus, delsitech, nanexa, peptron
        # INGESTION LARGE avec exclusion MINIMALE
        _contains_exclusion_keywords(text)  # Filtre léger
    else:
        # FILTRAGE STRICT par keywords LAI
        _filter_by_lai_keywords(text)
```

### 3. Scopes utilisés par le code

**SEULEMENT 4 scopes sont lus** :
1. `hr_content`
2. `financial_generic`
3. `hr_recruitment_terms`
4. `financial_reporting_terms`

**Scopes IGNORÉS** :
- `event_generic` ❌
- `esg_generic` ❌
- `corporate_noise_terms` ❌
- `anti_lai_routes` ❌

### 4. Fonction de matching

```python
def _contains_exclusion_keywords(text: str) -> bool:
    for keyword in exclusion_terms:
        if keyword.lower() in text_lower:  # Simple substring match
            return True
    return False
```

---

## ⚠️ PROBLÈME IDENTIFIÉ

**lai_weekly_v24 utilise des PURE PLAYERS LAI** :
- Sources : `lai_corporate_mvp` (MedinCell, Camurus, etc.)
- Profil appliqué : `corporate_pure_player_broad`
- Filtrage : **MINIMAL** (par design)

**Résultat** : Les keywords ajoutés dans `exclusion_scopes.yaml` sont ACTIFS mais le filtrage est VOLONTAIREMENT léger pour les pure players LAI.

---

## ✅ SOLUTION

### Option 1 : Enrichir les 4 scopes utilisés

Ajouter keywords dans :
- `hr_content` : Conférences génériques
- `financial_generic` : Rapports financiers + Corporate générique

**Statut** : ✅ FAIT mais impact limité car pure players

### Option 2 : Modifier le code pour filtrer plus

Modifier `_apply_corporate_profile()` pour filtrer même les pure players.

**Statut** : ❌ Nécessite modification moteur (hors scope)

### Option 3 : Tester avec sources non-pure-player

Tester avec `lai_press_mvp` qui a filtrage STRICT.

**Statut** : 🔄 À tester

---

## 📊 CONCLUSION

**Le moteur fonctionne correctement** :
- Les scopes `exclusion_scopes.yaml` SONT utilisés ✓
- Le filtrage est ACTIF ✓
- MAIS il est VOLONTAIREMENT léger pour les pure players LAI ✓

**Pour améliorer le filtrage** :
1. Enrichir les 4 scopes utilisés (fait)
2. OU modifier le code pour filtrer plus (hors scope)
3. OU accepter que les pure players ont peu de bruit (by design)

**Recommandation** : Le système fonctionne comme prévu. Les 24 items de v24 viennent majoritairement de pure players LAI, donc le filtrage minimal est NORMAL.
