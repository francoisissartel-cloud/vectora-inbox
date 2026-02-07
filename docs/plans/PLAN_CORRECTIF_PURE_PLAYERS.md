# Plan Correctif - Filtrage Pure Players LAI

**Date** : 2026-02-06  
**Problème** : Filtrage LAI keywords trop restrictif pour pure players  
**Solution** : Ajout flag `apply_lai_keywords_filter: false` dans `ingestion_profiles.yaml`  

---

## 🎯 Objectif

Désactiver le filtrage LAI keywords pour les sources corporate pure players en modifiant **uniquement le fichier canonical** `ingestion_profiles.yaml`.

---

## 📊 Diagnostic

### Problème Identifié
- **v24 → v25** : Dégradation significative
  - Items ingérés : 31 → 27 (-13%)
  - Taux relevant : 64% → 44% (-20 pp)
  - Score moyen : 71.5 → 37.8 (-33.7 pts)

### Cause Racine
Le filtrage LAI keywords (200+ keywords) s'applique à **toutes** les sources, y compris les pure players LAI qui sont 100% LAI par nature.

### Items Manquants v24 → v25
- Teva NDA Olanzapine Extended-Release (exclu)
- Medincell Malaria Grant (exclu)
- Novo Nordisk monthly GLP-1 (exclu - date 2023)

---

## 🔧 Solution Minimaliste

### Principe
Les pure players LAI (MedinCell, Camurus, Nanexa, DelSiTech, Peptron) sont **100% LAI par nature**.

**Donc** : Pas besoin de filtrage par LAI keywords, seulement exclusions du bruit évident.

### Modification Appliquée
**Fichier** : `canonical/ingestion/ingestion_profiles.yaml`

**Changement** : Ajout du flag `apply_lai_keywords_filter` dans les profils

```yaml
profiles:
  corporate_pure_player_broad:
    signal_requirements:
      mode: "exclude_only"
      apply_lai_keywords_filter: false  # ← PATCH v2.4: Désactive filtrage LAI keywords
      exclusion_scopes:
        - "exclusion_scopes.hr_content"
        - "exclusion_scopes.esg_generic"
        - "exclusion_scopes.financial_generic"
        # ...
  
  press_technology_focused:
    signal_requirements:
      mode: "require_multi_signals"
      apply_lai_keywords_filter: true   # ← PATCH v2.4: Active filtrage LAI keywords
      # ...
```

---

## 📋 Étapes d'Exécution

### 1. Upload Configuration sur S3 (DEV)

```bash
# Upload ingestion_profiles.yaml modifié
aws s3 cp canonical/ingestion/ingestion_profiles.yaml \
  s3://vectora-inbox-config-dev/canonical/ingestion/ingestion_profiles.yaml \
  --profile rag-lai-prod \
  --region eu-west-3

# Vérifier upload
aws s3 ls s3://vectora-inbox-config-dev/canonical/ingestion/ \
  --profile rag-lai-prod \
  --region eu-west-3
```

### 2. Redémarrer Lambda Ingest (Cold Start)

```bash
# Forcer cold start en mettant à jour variable d'environnement
aws lambda update-function-configuration \
  --function-name vectora-inbox-ingest-v2-dev \
  --environment Variables={CANONICAL_VERSION=2.4} \
  --profile rag-lai-prod \
  --region eu-west-3

# Attendre 30 secondes
sleep 30
```

### 3. Test E2E avec lai_weekly_v26

```bash
# Créer nouveau client test v26
cp config/clients/lai_weekly_v25.yaml config/clients/lai_weekly_v26.yaml

# Modifier version dans v26
# canonical_version: "2.4"

# Upload config v26
aws s3 cp config/clients/lai_weekly_v26.yaml \
  s3://vectora-inbox-config-dev/clients/lai_weekly_v26.yaml \
  --profile rag-lai-prod \
  --region eu-west-3

# Run E2E
python scripts/invoke/invoke_ingest_v2.py --client-id lai_weekly_v26 --env dev

# Attendre ingestion (30s)
sleep 30

# Normalize & Score
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --invocation-type Event \
  --cli-binary-format raw-in-base64-out \
  --payload '{"client_id":"lai_weekly_v26"}' \
  .tmp/normalize_v26.json \
  --profile rag-lai-prod \
  --region eu-west-3
```

### 4. Analyser Résultats

```bash
# Download items ingérés
aws s3 cp s3://vectora-inbox-data-dev/ingested/lai_weekly_v26/2026/02/06/items.json \
  .tmp/v26_ingested.json \
  --profile rag-lai-prod \
  --region eu-west-3

# Download items curated
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v26/2026/02/06/items.json \
  .tmp/v26_curated.json \
  --profile rag-lai-prod \
  --region eu-west-3

# Comparer métriques
python scripts/analysis/compare_runs.py --v1 v25 --v2 v26
```

---

## ✅ Critères de Succès

### Métriques Attendues v26 vs v25

| Métrique | v25 | v26 Attendu | Amélioration |
|----------|-----|-------------|--------------|
| Items ingérés | 27 | 30-32 | +10-18% |
| Taux relevant | 44% | 55-65% | +11-21 pp |
| Score moyen | 37.8 | 60-70 | +22-32 pts |
| Scores 80+ | 15% | 30-40% | +15-25 pp |

### Validation Qualitative
- ✅ Items v24 pertinents présents dans v26
- ✅ Pas de régression sur items déjà ingérés
- ✅ Logs montrent "apply_lai_keywords_filter: false" pour pure players

---

## 🔄 Rollback (si nécessaire)

```bash
# Restaurer version précédente depuis Git
git checkout HEAD~1 canonical/ingestion/ingestion_profiles.yaml

# Upload version précédente
aws s3 cp canonical/ingestion/ingestion_profiles.yaml \
  s3://vectora-inbox-config-dev/canonical/ingestion/ingestion_profiles.yaml \
  --profile rag-lai-prod \
  --region eu-west-3

# Forcer cold start
aws lambda update-function-configuration \
  --function-name vectora-inbox-ingest-v2-dev \
  --environment Variables={CANONICAL_VERSION=2.3} \
  --profile rag-lai-prod \
  --region eu-west-3
```

---

## ⚠️ Note Importante: Code Lambda

### Vérification Effectuée

Le code Lambda actuel dans `ingestion_profiles.py` **ne lit PAS encore** le flag `apply_lai_keywords_filter`.

**Impact** : Le patch canonical seul ne suffit pas, il faut aussi modifier le code.

### Options

#### Option A: Patch Code Minimal (Recommandé)
Modifier `ingestion_profiles.py` pour lire le flag:

```python
def _apply_corporate_profile(items, source_meta):
    # Charger profil depuis ingestion_profiles.yaml
    profile = load_profile_for_source(source_meta)
    apply_lai_filter = profile.get('signal_requirements', {}).get('apply_lai_keywords_filter', True)
    
    if is_lai_pure_player and not apply_lai_filter:
        # Ingestion large sans LAI keywords
        return _filter_by_exclusions_only(items)
    else:
        # Filtrage LAI keywords
        return _filter_by_lai_keywords(items, source_key)
```

#### Option B: Patch Canonical Alternatif (Sans Code)
Créer une liste d'exclusion dans `lai_keywords.yaml` pour désactiver le filtrage:

```yaml
# Dans lai_keywords.yaml
lai_keywords_exemptions:
  # Sources exemptées du filtrage LAI keywords (pure players)
  - press_corporate__medincell
  - press_corporate__camurus
  - press_corporate__nanexa
  - press_corporate__delsitech
  - press_corporate__peptron
```

Puis modifier le code pour vérifier cette liste.

---

## 📝 Prochaines Étapes

### Si Succès
1. Promouvoir vers STAGE
2. Générer rapport E2E v26 complet (format gold standard)
3. Documenter dans CHANGELOG

### Si Échec
1. Analyser logs Lambda
2. Vérifier chargement ingestion_profiles.yaml
3. Ajuster configuration si nécessaire

---

## 📁 Fichiers Modifiés

### Modifiés
- `canonical/ingestion/ingestion_profiles.yaml` ⭐ (ajout flags `apply_lai_keywords_filter`)
- `canonical/ingestion/README.md` (documentation)
- `docs/plans/PLAN_CORRECTIF_PURE_PLAYERS.md` (ce fichier)

### Code
- ⚠️ **Modification code nécessaire** pour lire le flag `apply_lai_keywords_filter`
- Alternative: Patch canonical avec liste d'exemptions

---

**Statut** : ⚠️ **Nécessite modification code OU patch canonical alternatif**  
**Risque** : 🟡 Moyen (changement configuration + code)  
**Temps estimé** : 30 minutes (avec code) / 20 minutes (patch alternatif)  
