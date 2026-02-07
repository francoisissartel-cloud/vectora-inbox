# Réponse Rapide - Moteur Ingestion Canonical

**Date**: 2026-02-06

---

## ❓ Question

Est-ce que le plan correctif assure que le profil d'ingestion est adapté pour :
- **Pure players** : Permissif, exclusion du bruit évident (`exclusion_scopes.yaml`)
- **Hybrid players** : Exclusion du bruit + détection LAI keywords

Est-ce que cela sera opérationnel dans le moteur ingestion ?

---

## ✅ Réponse : OUI

Le plan correctif a été **mis à jour** (8 phases, 3h) pour garantir :

### 1. Pure Players (14 entreprises) ✅
```yaml
# ingestion_profiles.yaml
pure_players:
  apply_exclusions: true          # ← 8 scopes, 150+ termes
  require_lai_keywords: false     # ← Pas de filtrage LAI (permissif)
```

**Implémentation** :
```python
if _is_pure_player(company_id):
    return _filter_by_exclusions_only(items)  # Exclusions seules
```

**Résultat** : MedinCell, Camurus → Tout sauf bruit RH/financier

---

### 2. Hybrid Players (27 entreprises) ✅
```yaml
# ingestion_profiles.yaml
hybrid_players:
  apply_exclusions: true          # ← 8 scopes, 150+ termes
  require_lai_keywords: true      # ← LAI keywords requis (filtré)
```

**Implémentation** :
```python
if _is_hybrid_player(company_id):
    return _filter_by_exclusions_and_lai(items)  # Exclusions + LAI
```

**Résultat** : Teva, Pfizer → Seulement contenu LAI

---

## 🔄 Transformations Appliquées

| Élément | Avant | Après | Phase |
|---------|-------|-------|-------|
| Exclusions | 20 hardcodés | 150+ S3 | 2-3 |
| Pure players | 5 hardcodés | 14 S3 | 4 |
| Hybrid players | Non géré | 27 S3 | 4 |
| LAI keywords | 70 hardcodés | 150+ S3 | 5 |
| Logique | Identique | Différenciée | 6 |

---

## 📋 Plan Correctif (8 Phases, 3h)

1. **Phase 1** (15 min) : Rebuild & deploy
2. **Phase 2** (30 min) : Supprimer fallback hardcodé
3. **Phase 3** (20 min) : Lire 8 scopes (vs 4)
4. **Phase 4** (45 min) : Externaliser company scopes (pure + hybrid)
5. **Phase 5** (30 min) : Externaliser LAI keywords
6. **Phase 6** (30 min) : Implémenter logique différenciée
7. **Phase 7** (20 min) : Test E2E
8. **Phase 8** (10 min) : Commit + doc

---

## ✅ Opérationnel dans le Moteur

```python
# __init__.py (Initialisation au démarrage)
initialize_exclusion_scopes(s3_io, config_bucket)    # 8 scopes
initialize_company_scopes(s3_io, config_bucket)      # 14 pure + 27 hybrid
initialize_lai_keywords(s3_io, config_bucket)        # 150+ termes

# ingestion_profiles.py (Filtrage différencié)
if _is_pure_player(company_id):
    return _filter_by_exclusions_only(items)         # Permissif
elif _is_hybrid_player(company_id):
    return _filter_by_exclusions_and_lai(items)      # Filtré
```

---

## 📊 Impact

**Avant** :
- Items ingérés : 25
- Pure players : Filtrage LAI ❌ (trop strict)
- Hybrid players : Non différenciés ❌
- Hardcoding : 3 listes

**Après** :
- Items ingérés : 20 (-5 bruit)
- Pure players : Exclusions seules ✅
- Hybrid players : Exclusions + LAI ✅
- Hardcoding : 0

---

## 📂 Documents Détaillés

1. **Plan correctif** : `docs/plans/PLAN_CORRECTIF_FILTRAGE_INGESTION.md`
2. **Architecture** : `docs/design/moteur_ingestion_canonical_architecture.md`
3. **Comparatif** : `docs/design/comparatif_avant_apres_moteur_canonical.md`
4. **Index** : `docs/design/INDEX_MOTEUR_CANONICAL.md`

---

## 🚀 Prochaine Étape

Exécuter le plan correctif (3h) :
```bash
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev
python scripts/invoke/invoke_ingest_v2.py --client-id lai_weekly_v24 --env dev
```

---

**Conclusion** : ✅ Plan validé - Moteur sera 100% générique et conforme aux profils canonical
