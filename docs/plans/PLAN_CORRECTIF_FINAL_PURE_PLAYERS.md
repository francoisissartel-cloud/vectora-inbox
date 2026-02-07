# Plan Correctif FINAL - Pure Players LAI

**Date**: 2026-02-06  
**Problème**: Pure players filtrés par LAI keywords alors qu'ils ne devraient pas  
**Cause**: `company_id` non extrait depuis `source_key`  
**Solution**: Patch code minimaliste (3 lignes)  
**Version**: v1.7.0

---

## 🎯 Problème Identifié

### Symptômes v24 → v25
- Items ingérés: 31 → 27 (-13%)
- Taux relevant: 64% → 44% (-20 pp)
- Score moyen: 71.5 → 37.8 (-33.7 pts)

### Items Pure Players Exclus à Tort

| # | Titre | Source | Statut v25 | Raison |
|---|-------|--------|------------|--------|
| 1 | Teva NDA Olanzapine Extended-Release | MedinCell | ❌ EXCLU | Pas de LAI keywords dans titre/contenu court |
| 4 | Medincell Malaria Grant | MedinCell | ❌ EXCLU | Pas de LAI keywords dans titre/contenu court |

### Cause Racine

```python
# Code actuel (BUGUÉ)
company_id = source_meta.get('company_id', '')  # ← Retourne '' (vide)
is_lai_pure_player = company_id.lower() in _pure_players_cache  # ← Toujours False

if is_lai_pure_player:
    # Ingestion large sans LAI keywords
    ...
else:
    # ❌ TOUS les corporate passent ici
    return _filter_by_lai_keywords(items, source_key)  # ← Applique LAI keywords
```

**Problème**: `company_id` n'existe pas dans `source_catalog.yaml` → toujours vide → pure players non détectés → filtrage LAI keywords appliqué à tort.

---

## ✅ Solution Minimaliste

### Modification: `ingestion_profiles.py`

**Fichier**: `src_v2/vectora_core/ingest/ingestion_profiles.py`  
**Fonction**: `_apply_corporate_profile` (ligne ~120)  
**Lignes modifiées**: 3

```python
# AVANT (BUGUÉ)
company_id = source_meta.get('company_id', '')

# APRÈS (CORRIGÉ)
company_id = source_meta.get('company_id', '')
if not company_id and '__' in source_key:
    company_id = source_key.split('__')[1]  # Extraire depuis source_key

# Ajout log pour debug
logger.info(f"Source: {source_key}, Company ID: {company_id}, Pure player: {is_lai_pure_player}")
```

**Logique**: 
- `press_corporate__medincell` → `company_id = "medincell"`
- `press_corporate__camurus` → `company_id = "camurus"`
- `press_corporate__nanexa` → `company_id = "nanexa"`

**Résultat**: Pure players correctement détectés → pas de filtrage LAI keywords → ingestion large.

---

## 📋 Étapes d'Exécution

### Phase 1: Test AVANT Correction (Baseline v25) - 5 min

```bash
# 1. Sauvegarder les résultats v25 actuels comme baseline
mkdir -p .tmp/baseline_v25

aws s3 cp s3://vectora-inbox-data-dev/ingested/lai_weekly_v25/2026/02/06/items.json \
  .tmp/baseline_v25/ingested.json \
  --profile rag-lai-prod --region eu-west-3

aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v25/2026/02/06/items.json \
  .tmp/baseline_v25/curated.json \
  --profile rag-lai-prod --region eu-west-3

# 2. Extraire métriques baseline
echo "=== BASELINE v25 (AVANT correction) ==="
python -c "
import json
ingested = json.load(open('.tmp/baseline_v25/ingested.json'))
curated = json.load(open('.tmp/baseline_v25/curated.json'))
relevant = [i for i in curated if i.get('is_relevant')]
print(f'Items ingérés: {len(ingested)}')
print(f'Items curated: {len(curated)}')
print(f'Items relevant: {len(relevant)} ({len(relevant)/len(curated)*100:.1f}%)')
print(f'Score moyen: {sum(i.get(\"score\",0) for i in relevant)/len(relevant):.1f}')
"

# 3. Identifier items manquants de v24
echo "\n=== Items v24 manquants dans v25 ==="
echo "1. Teva NDA Olanzapine Extended-Release (MedinCell)"
echo "2. Medincell Malaria Grant"
```

### Phase 2: Build & Deploy Correction - 5 min

```bash
# 1. Build toutes les Lambdas avec correction
python scripts/build/build_all.py

# 2. Deploy dev
python scripts/deploy/deploy_env.py --env dev

# 3. Vérifier déploiement
aws lambda get-function \
  --function-name vectora-inbox-ingest-v2-dev \
  --profile rag-lai-prod \
  --region eu-west-3 \
  --query 'Configuration.[LastModified,CodeSize]' \
  --output table
```

### Phase 3: Test APRÈS Correction (v26) - 10 min

```bash
# 1. Créer config client v26
cp config/clients/lai_weekly_v25.yaml config/clients/lai_weekly_v26.yaml

# Upload config
aws s3 cp config/clients/lai_weekly_v26.yaml \
  s3://vectora-inbox-config-dev/clients/lai_weekly_v26.yaml \
  --profile rag-lai-prod --region eu-west-3

# 2. Run ingestion v26
echo "\n=== Lancement ingestion v26 (APRÈS correction) ==="
python scripts/invoke/invoke_ingest_v2.py --client-id lai_weekly_v26 --env dev

# Attendre ingestion
sleep 30

# 3. Normalize & Score
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --invocation-type Event \
  --cli-binary-format raw-in-base64-out \
  --payload '{"client_id":"lai_weekly_v26"}' \
  .tmp/normalize_v26.json \
  --profile rag-lai-prod --region eu-west-3

# Attendre normalisation
echo "Attente normalisation (2 min)..."
sleep 120

# 4. Download résultats v26
mkdir -p .tmp/results_v26

aws s3 cp s3://vectora-inbox-data-dev/ingested/lai_weekly_v26/2026/02/06/items.json \
  .tmp/results_v26/ingested.json \
  --profile rag-lai-prod --region eu-west-3

aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v26/2026/02/06/items.json \
  .tmp/results_v26/curated.json \
  --profile rag-lai-prod --region eu-west-3
```

### Phase 4: Vérification Logs Pure Players - 2 min

```bash
# Vérifier que pure players sont détectés
echo "\n=== Vérification détection pure players ==="

aws logs tail /aws/lambda/vectora-inbox-ingest-v2-dev \
  --since 10m \
  --filter-pattern "Pure player" \
  --profile rag-lai-prod --region eu-west-3 \
  > .tmp/logs_pure_players.txt

# Compter détections
echo "Pure players détectés:"
grep -c "Pure player: True" .tmp/logs_pure_players.txt || echo "0"

# Afficher détails
echo "\nDétails:"
grep "Source:.*Pure player:" .tmp/logs_pure_players.txt | head -10
```

### Phase 5: Comparaison AVANT/APRÈS - 5 min

```bash
# Script de comparaison détaillée
echo "\n=== COMPARAISON v25 (AVANT) vs v26 (APRÈS) ==="

python << 'EOF'
import json

# Charger données
v25_ingested = json.load(open('.tmp/baseline_v25/ingested.json'))
v25_curated = json.load(open('.tmp/baseline_v25/curated.json'))
v26_ingested = json.load(open('.tmp/results_v26/ingested.json'))
v26_curated = json.load(open('.tmp/results_v26/curated.json'))

# Métriques v25
v25_relevant = [i for i in v25_curated if i.get('is_relevant')]
v25_score_avg = sum(i.get('score',0) for i in v25_relevant)/len(v25_relevant) if v25_relevant else 0
v25_scores_80plus = sum(1 for i in v25_relevant if i.get('score',0) >= 80)

# Métriques v26
v26_relevant = [i for i in v26_curated if i.get('is_relevant')]
v26_score_avg = sum(i.get('score',0) for i in v26_relevant)/len(v26_relevant) if v26_relevant else 0
v26_scores_80plus = sum(1 for i in v26_relevant if i.get('score',0) >= 80)

# Afficher comparaison
print("\n" + "="*60)
print("MÉTRIQUES COMPARATIVES")
print("="*60)
print(f"{'Métrique':<30} {'v25 (AVANT)':<15} {'v26 (APRÈS)':<15} {'Δ':<10}")
print("-"*60)

# Items ingérés
delta_ing = v26_ingested.__len__() - v25_ingested.__len__()
print(f"{'Items ingérés':<30} {len(v25_ingested):<15} {len(v26_ingested):<15} {delta_ing:+d}")

# Taux relevant
v25_rate = len(v25_relevant)/len(v25_curated)*100 if v25_curated else 0
v26_rate = len(v26_relevant)/len(v26_curated)*100 if v26_curated else 0
delta_rate = v26_rate - v25_rate
print(f"{'Taux relevant':<30} {v25_rate:.1f}%{'':<10} {v26_rate:.1f}%{'':<10} {delta_rate:+.1f}pp")

# Score moyen
delta_score = v26_score_avg - v25_score_avg
print(f"{'Score moyen':<30} {v25_score_avg:.1f}{'':<12} {v26_score_avg:.1f}{'':<12} {delta_score:+.1f}")

# Scores 80+
v25_80plus_pct = v25_scores_80plus/len(v25_relevant)*100 if v25_relevant else 0
v26_80plus_pct = v26_scores_80plus/len(v26_relevant)*100 if v26_relevant else 0
delta_80plus = v26_80plus_pct - v25_80plus_pct
print(f"{'Scores 80+':<30} {v25_80plus_pct:.1f}%{'':<10} {v26_80plus_pct:.1f}%{'':<10} {delta_80plus:+.1f}pp")

print("="*60)

# Validation succès
print("\n" + "="*60)
print("VALIDATION CRITÈRES DE SUCCÈS")
print("="*60)

success_count = 0
total_checks = 4

if delta_ing >= 3:
    print("✅ Items ingérés: +{} (objectif: +3 minimum)".format(delta_ing))
    success_count += 1
else:
    print("❌ Items ingérés: +{} (objectif: +3 minimum)".format(delta_ing))

if delta_rate >= 15:
    print("✅ Taux relevant: +{:.1f}pp (objectif: +15pp minimum)".format(delta_rate))
    success_count += 1
else:
    print("❌ Taux relevant: +{:.1f}pp (objectif: +15pp minimum)".format(delta_rate))

if delta_score >= 25:
    print("✅ Score moyen: +{:.1f} (objectif: +25 minimum)".format(delta_score))
    success_count += 1
else:
    print("❌ Score moyen: +{:.1f} (objectif: +25 minimum)".format(delta_score))

if delta_80plus >= 15:
    print("✅ Scores 80+: +{:.1f}pp (objectif: +15pp minimum)".format(delta_80plus))
    success_count += 1
else:
    print("❌ Scores 80+: +{:.1f}pp (objectif: +15pp minimum)".format(delta_80plus))

print("\n" + "="*60)
if success_count == total_checks:
    print("🎉 SUCCÈS COMPLET: {}/{} critères validés".format(success_count, total_checks))
elif success_count >= 3:
    print("✅ SUCCÈS PARTIEL: {}/{} critères validés".format(success_count, total_checks))
else:
    print("❌ ÉCHEC: {}/{} critères validés".format(success_count, total_checks))
print("="*60)

EOF
```

### Phase 6: Vérification Items Spécifiques - 3 min

```bash
# Vérifier présence des items manquants de v24
echo "\n=== Vérification items v24 manquants ==="

python << 'EOF'
import json

v26_ingested = json.load(open('.tmp/results_v26/ingested.json'))
v26_curated = json.load(open('.tmp/results_v26/curated.json'))

# Items à chercher (patterns)
target_items = [
    {"pattern": "olanzapine", "source": "medincell", "desc": "Teva NDA Olanzapine"},
    {"pattern": "malaria", "source": "medincell", "desc": "Medincell Malaria Grant"},
]

print("\nRecherche items v24 manquants dans v26:")
print("-" * 60)

for target in target_items:
    found_ingested = False
    found_curated = False
    
    # Chercher dans ingested
    for item in v26_ingested:
        title = item.get('title', '').lower()
        source = item.get('source_key', '').lower()
        if target['pattern'] in title and target['source'] in source:
            found_ingested = True
            print(f"✅ {target['desc']}")
            print(f"   Ingéré: OUI")
            
            # Chercher dans curated
            item_id = item.get('item_id')
            for curated_item in v26_curated:
                if curated_item.get('item_id') == item_id:
                    found_curated = True
                    score = curated_item.get('score', 0)
                    is_relevant = curated_item.get('is_relevant', False)
                    print(f"   Curated: OUI (score: {score}, relevant: {is_relevant})")
                    break
            
            if not found_curated:
                print(f"   Curated: NON")
            break
    
    if not found_ingested:
        print(f"❌ {target['desc']}")
        print(f"   Ingéré: NON")
        print(f"   Curated: NON")
    
    print()

EOF
```

---

## ✅ Critères de Succès

### Métriques Attendues v26 vs v25

| Métrique | v25 | v26 Attendu | Amélioration | Statut |
|----------|-----|-------------|--------------|--------|
| Items ingérés | 27 | 30-32 | +10-18% | 🎯 |
| Taux relevant | 44% | 60-70% | +16-26 pp | 🎯 |
| Score moyen | 37.8 | 65-75 | +27-37 pts | 🎯 |
| Scores 80+ | 15% | 35-45% | +20-30 pp | 🎯 |

### Validation Qualitative

- ✅ Items #1 et #4 de v24 présents dans v26
- ✅ Logs montrent "Pure player LAI détecté" pour MedinCell, Camurus, Nanexa, DelSiTech
- ✅ Pas de régression sur items déjà ingérés en v25
- ✅ Sources pure players ont taux rétention >80%

### Validation Logs

```bash
# Vérifier que pure players sont détectés
grep "Pure player: True" .tmp/logs_v26.txt | wc -l
# Attendu: 4-5 (medincell, camurus, nanexa, delsitech, peptron)

# Vérifier qu'aucun pure player n'a filtrage LAI keywords
grep "press_corporate__medincell" .tmp/logs_v26.txt | grep "filtrage par mots-clés LAI"
# Attendu: aucun résultat
```

---

## 🔄 Rollback (si nécessaire)

### Option A: Depuis Sauvegarde Locale (Recommandé)

```bash
# 1. Supprimer src_v2 actuel
rmdir /S /Q "c:\Users\franc\OneDrive\Bureau\vectora-inbox\src_v2"

# 2. Restaurer depuis sauvegarde v1.6.0
xcopy "c:\Users\franc\OneDrive\Bureau\vectora-inbox\src_v2_backup_v1.6.0_before_pure_players_fix" ^
      "c:\Users\franc\OneDrive\Bureau\vectora-inbox\src_v2" /E /I /H /Y

# 3. Rebuild & redeploy
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev

# 4. Vérifier rollback
aws lambda get-function \
  --function-name vectora-inbox-ingest-v2-dev \
  --profile rag-lai-prod \
  --region eu-west-3 \
  --query 'Configuration.LastModified'
```

### Option B: Depuis Git

```bash
# Restaurer version précédente
git checkout HEAD~1 src_v2/vectora_core/ingest/ingestion_profiles.py

# Rebuild & redeploy
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev
```

### Sauvegarde Créée

✅ **Sauvegarde complète créée**: `src_v2_backup_v1.6.0_before_pure_players_fix/`
- **66 fichiers** sauvegardés
- **Version**: v1.6.0 (avant correction)
- **Date**: 2026-02-06
- **Documentation**: Voir `README_BACKUP.md` dans le dossier de sauvegarde

---

## 📝 Prochaines Étapes

### Si Succès ✅

1. **Promouvoir vers STAGE**
```bash
python scripts/deploy/promote.py --to stage --version 1.7.0
```

2. **Générer rapport E2E v26 complet**
```bash
python scripts/analysis/generate_e2e_report.py \
  --client-id lai_weekly_v26 \
  --env dev \
  --output docs/e2e/test_e2e_lai_weekly_v26_rapport_2026-02-06.md
```

3. **Documenter dans CHANGELOG**
```markdown
## [1.7.0] - 2026-02-06
### Fixed
- Pure players LAI correctement détectés (extraction company_id depuis source_key)
- Filtrage LAI keywords désactivé pour pure players (ingestion large)
- Items pertinents MedinCell/Camurus non exclus à tort
```

4. **Amélioration future** (optionnel)
- Ajouter `company_id` explicite dans `source_catalog.yaml`
- Créer test unitaire pour vérifier détection pure players

### Si Échec Partiel ⚠️

1. **Analyser logs** pour voir quels items sont encore exclus
2. **Vérifier** si exclusions sont trop larges (114 keywords)
3. **Tester** avec exclusions réduites
4. **Ajuster** si nécessaire

---

## 📁 Fichiers Modifiés

### Code ⭐
- `src_v2/vectora_core/ingest/ingestion_profiles.py` (4 lignes modifiées)
  - Ligne ~122: Extraction `company_id` depuis `source_key`
  - Ligne ~129: Ajout log debug

### Canonical
- ❌ Aucune modification canonical

### Documentation
- `docs/plans/PLAN_CORRECTIF_FINAL_PURE_PLAYERS.md` (ce fichier)

---

## 🔍 Détails Techniques

### Avant (v1.6.0)
```python
def _apply_corporate_profile(items, source_meta):
    company_id = source_meta.get('company_id', '')  # ← Toujours ''
    is_lai_pure_player = company_id.lower() in _pure_players_cache  # ← Toujours False
    
    if is_lai_pure_player:  # ← Jamais exécuté
        # Ingestion large
        ...
    else:  # ← Toujours exécuté
        return _filter_by_lai_keywords(items, source_key)  # ← Applique LAI keywords à TOUS
```

### Après (v1.7.0)
```python
def _apply_corporate_profile(items, source_meta):
    company_id = source_meta.get('company_id', '')
    if not company_id and '__' in source_key:
        company_id = source_key.split('__')[1]  # ← Extraction depuis source_key
    
    is_lai_pure_player = company_id.lower() in _pure_players_cache  # ← Maintenant True pour pure players
    logger.info(f"Source: {source_key}, Company ID: {company_id}, Pure player: {is_lai_pure_player}")
    
    if is_lai_pure_player:  # ← Exécuté pour MedinCell, Camurus, etc.
        # Ingestion large sans LAI keywords ✅
        ...
    else:
        return _filter_by_lai_keywords(items, source_key)
```

---

**Statut**: ✅ Prêt pour build & deploy  
**Risque**: 🟢 Faible (patch minimaliste, logique claire)  
**Temps estimé**: 20 minutes (build + deploy + test)  
**Impact**: 🎯 Résout le problème v24→v25 pour pure players  
**Version**: v1.7.0
