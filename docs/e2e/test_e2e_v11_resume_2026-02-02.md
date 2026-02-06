# Résumé Actions - Test E2E lai_weekly_v11

## ✅ Actions Complétées

### 1. Création lai_weekly_v11.yaml
- **Fichier** : `client-config-examples/production/lai_weekly_v11.yaml`
- **Base** : Copie identique de lai_weekly_v10.yaml
- **Changements** :
  - `client_id: "lai_weekly_v11"`
  - `name: "LAI Intelligence Weekly v11 (Test Prompts Cleanup 2026-02-02)"`
  - `notification_email: "lai-weekly-v11@vectora.com"`
  - `template_version: "11.0.0"`
  - Notes: Test après cleanup prompts obsolètes

### 2. Build Réussi
- ✅ `vectora-core-1.4.1.zip` créé (0.25 MB)
- ✅ `common-deps-1.0.5.zip` créé (1.76 MB)
- ✅ Prompts nettoyés inclus dans layer

### 3. Prompts Actifs Validés
```
canonical/prompts/
├── normalization/generic_normalization.yaml
├── domain_scoring/lai_domain_scoring.yaml
└── editorial/lai_editorial.yaml
```

## ⚠️ Action Requise : AWS SSO

**Erreur deploy** : `Token has expired and refresh failed`

**Solution** :
```bash
# Rafraîchir token AWS SSO
aws sso login --profile rag-lai-prod

# Puis re-déployer
python scripts/deploy/deploy_env.py --env dev
```

## 🚀 Prochaines Étapes

### 1. Déployer sur dev
```bash
# Après aws sso login
python scripts/deploy/deploy_env.py --env dev
```

### 2. Uploader client config v11
```bash
# Upload vers S3
aws s3 cp client-config-examples/production/lai_weekly_v11.yaml ^
  s3://vectora-inbox-config-dev/clients/lai_weekly_v11.yaml ^
  --profile rag-lai-prod
```

### 3. Test E2E
```bash
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v11
```

### 4. Vérifications attendues

**Normalisation** :
- ✅ Utilise `generic_normalization.yaml`
- ✅ Extraction entités complète
- ✅ Extraction dates fonctionnelle

**Domain Scoring** :
- ✅ Utilise `lai_domain_scoring.yaml` (pas lai_matching)
- ✅ Détection signaux LAI
- ✅ Score 0-100 calculé
- ✅ Reasoning généré

**Résultats** :
- Items normalisés dans S3
- Items scorés avec domain_score
- Métriques détaillées

## 📊 Comparaison v10 vs v11

| Aspect | v10 | v11 |
|--------|-----|-----|
| **Objectif** | Test E2E AWS | Test après cleanup prompts |
| **Prompts** | Avec obsolètes | Prompts nettoyés |
| **Config** | matching_prompt (corrigé) | domain_scoring_prompt |
| **Données** | Fraîches v10 | Fraîches v11 |

## 📝 Notes

- v11 = Validation que cleanup prompts n'a pas cassé le pipeline
- Architecture v2.0 : 2 appels Bedrock validée
- Prompts obsolètes supprimés : lai_normalization, lai_matching, global_prompts
- Structure finale propre et maintenable

---

**Statut** : ⏸️ En attente refresh AWS SSO token
