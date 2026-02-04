# Diagnostic 0% Matching - Tests AWS Dev v12

**Date**: 2026-02-03  
**Client**: lai_weekly_v12  
**Problème**: 0/29 items matched  
**Statut**: 🔍 CAUSE IDENTIFIÉE

---

## 🔍 ANALYSE DES LOGS

### Configuration Chargée ✅

```
✅ Client config: LAI Intelligence Weekly v12 (Test Domain Definition Fix)
✅ Scopes: 22 scopes + 1 domain
✅ Prompts: normalization, domain_scoring, editorial
✅ Domain definition: lai_domain_definition.yaml (8478 caractères)
✅ Canonical v2.2 chargé correctement
```

### Fichiers Canonical v2.2 Utilisés ✅

1. ✅ `generic_normalization.yaml` (3730 caractères)
2. ✅ `lai_domain_scoring.yaml` (4565 caractères)  
3. ✅ `lai_domain_definition.yaml` (8478 caractères)
4. ✅ `exclusion_scopes.yaml` (4445 caractères)

**Conclusion**: Canonical v2.2 est bien déployé et chargé par Lambda

---

## ⚠️ PROBLÈME IDENTIFIÉ

### Cause Probable: Chemin S3 Incorrect

**Observation**:
- Client ID: `lai_weekly_v12`
- Chemins S3 normalized existants:
  - `s3://vectora-inbox-data-dev/normalized/lai_weekly/`
  - `s3://vectora-inbox-data-dev/normalized/lai_weekly_v2/`
  - `s3://vectora-inbox-data-dev/normalized/lai_weekly_v3/`
- ❌ Pas de `lai_weekly_v12/`

**Hypothèse**:
Lambda cherche les données dans `normalized/lai_weekly_v12/` mais elles sont dans `normalized/lai_weekly/` ou `normalized/lai_weekly_v3/`

---

## 🔍 HYPOTHÈSES ALTERNATIVES

### Hypothèse 1: Pas de Données Input ⚠️

**Probabilité**: ÉLEVÉE

- Lambda a normalisé 29 items ✅
- Lambda a scoré 29 items ✅  
- Mais 0 items matched ❌

**Explication possible**:
- Les 29 items viennent d'un run précédent (v3 ou v7)
- Lambda v12 n'a pas trouvé de nouvelles données à ingérer
- Il a re-traité des anciennes données déjà normalisées

### Hypothèse 2: Tous les Scores < Seuil ⚠️

**Probabilité**: MOYENNE

- `min_domain_score: 0.25` dans lai_weekly_v12.yaml
- Canonical v2.2 avec règles strictes:
  - `financial_results` base_score = 0
  - `hybrid_company` boost = 0 (sans signaux)
  - Exclusions manufacturing

**Possible que**:
- Tous les 29 items ont score < 25
- Donc 0 matched

### Hypothèse 3: is_relevant = false pour Tous ⚠️

**Probabilité**: FAIBLE

- Domain scoring trop strict
- Tous les items rejetés par Bedrock
- Mais peu probable vu les tests locaux (67% matching)

---

## 📊 COMPARAISON TESTS

### Tests Local (Phase 5)

| Métrique | Valeur |
|----------|--------|
| Items testés | 3 |
| Items matched | 2 (67%) |
| Canonical | v2.2 local |
| Bedrock | Appels réels |

### Tests AWS Dev (Phase 7)

| Métrique | Valeur |
|----------|--------|
| Items input | 29 |
| Items normalized | 29 |
| Items matched | 0 (0%) |
| Canonical | v2.2 S3 |
| Bedrock | Appels réels |

**Écart**: -67% matching

---

## 🎯 ACTIONS RECOMMANDÉES

### Action 1: Vérifier Source des 29 Items (PRIORITAIRE)

```bash
# Vérifier d'où viennent les 29 items
aws s3 ls s3://vectora-inbox-data-dev/ingested/lai_weekly_v12/ \
  --profile rag-lai-prod --region eu-west-3 --recursive

# Vérifier les données normalisées
aws s3 ls s3://vectora-inbox-data-dev/normalized/lai_weekly/ \
  --profile rag-lai-prod --region eu-west-3 --recursive | tail -10
```

### Action 2: Analyser 1 Item Normalisé

```bash
# Télécharger 1 item normalisé pour voir son score
aws s3 cp s3://vectora-inbox-data-dev/normalized/lai_weekly/<latest_file> \
  ./item_sample.json --profile rag-lai-prod --region eu-west-3

# Analyser le contenu
cat item_sample.json | jq '.domain_scoring'
```

### Action 3: Relancer avec Nouveau Run

```bash
# Option A: Utiliser lai_weekly_v3 (données existantes)
python scripts/invoke/invoke_normalize_score_v2.py --event lai_weekly_v3

# Option B: Créer lai_weekly_v13 avec canonical_version: "2.2"
# Puis tester avec nouvelles données
```

### Action 4: Baisser Seuil Temporairement

```yaml
# Modifier lai_weekly_v12.yaml
matching_config:
  min_domain_score: 0.10  # Au lieu de 0.25
```

---

## 📝 CONCLUSION DIAGNOSTIC

**Cause la Plus Probable**: 
Les 29 items sont des données anciennes (v3 ou v7) déjà normalisées. Lambda v12 n'a pas trouvé de nouvelles données à ingérer, donc 0 matched.

**Preuve**:
- Pas de dossier `lai_weekly_v12/` dans S3
- 29 items normalisés + 29 items scorés = re-traitement
- 0 matched = pas de nouvelles données

**Solution Recommandée**:
1. Vérifier la source des 29 items
2. Relancer avec lai_weekly_v3 (données existantes)
3. Ou créer lai_weekly_v13 avec nouvelles données

---

**Diagnostic créé**: 2026-02-03  
**Prochaine action**: Vérifier source des 29 items
