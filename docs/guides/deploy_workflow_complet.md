# Workflow de Déploiement Complet

**Date**: 2026-02-02  
**Version**: 2.0  
**Statut**: Automatisation complète

---

## 🎯 Commande Unique

```bash
python scripts/deploy/deploy_env.py --env dev
```

Une seule commande pour un déploiement complet.

---

## 📋 Ce que fait cette commande

### Étape 1: Publication vectora-core layer
- Lit version depuis `VERSION` (VECTORA_CORE_VERSION)
- Upload ZIP vers S3: `s3://vectora-inbox-lambda-code-dev/layers/`
- Publie layer: `vectora-inbox-vectora-core-dev`
- Retourne ARN du layer

### Étape 2: Publication common-deps layer
- Lit version depuis `VERSION` (COMMON_DEPS_VERSION)
- Upload ZIP vers S3: `s3://vectora-inbox-lambda-code-dev/layers/`
- Publie layer: `vectora-inbox-common-deps-dev`
- Retourne ARN du layer

### Étape 3: Récupération ARNs
- Récupère dernière version de chaque layer publié
- Construit liste des ARNs: `[vectora-core-arn, common-deps-arn]`

### Étape 4: Mise à jour Lambdas (NOUVEAU depuis 2026-02-02)
- Met à jour `vectora-inbox-ingest-v2-dev` avec nouveaux layers
- Met à jour `vectora-inbox-normalize-score-v2-dev` avec nouveaux layers
- Met à jour `vectora-inbox-newsletter-v2-dev` avec nouveaux layers

---

## 🔧 Gestion des Erreurs

### Erreur publication layer
**Comportement**: Arrêt immédiat  
**Raison**: Layers sont critiques pour les Lambdas

### Lambda manquante
**Comportement**: Warning + Continue  
**Raison**: Lambda peut ne pas encore exister (première fois)  
**Log**: `[SKIP] Lambda not found`

### Erreur mise à jour Lambda
**Comportement**: Arrêt immédiat  
**Raison**: Problème de configuration ou permissions

---

## 🧪 Dry-Run

```bash
python scripts/deploy/deploy_env.py --env dev --dry-run
```

**Simule le déploiement sans modifications AWS**:
- Vérifie que les fichiers ZIP existent
- Affiche les commandes qui seraient exécutées
- N'upload rien vers S3
- Ne publie aucun layer
- Ne met à jour aucune Lambda

**Utilisation**: Valider avant déploiement réel

---

## 📊 Logs de Sortie

### Sortie normale

```
[DEPLOY] Deploying to dev environment

[INFO] Versions:
   vectora-core: 1.3.0
   common-deps: 1.0.5

============================================================
Deploying vectora-core layer...
============================================================
[DEPLOY] Uploading to s3://vectora-inbox-lambda-code-dev/layers/vectora-core-1.3.0.zip
[DEPLOY] Publishing layer vectora-inbox-vectora-core-dev

[SUCCESS] Layer deployed successfully!
   ARN: arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev:49
   Version: 49

============================================================
Deploying common-deps layer...
============================================================
[DEPLOY] Uploading to s3://vectora-inbox-lambda-code-dev/layers/common-deps-1.0.5.zip
[DEPLOY] Publishing layer vectora-inbox-common-deps-dev

[SUCCESS] Layer deployed successfully!
   ARN: arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-common-deps-dev:11
   Version: 11

============================================================
Updating Lambda layers...
============================================================
   Layer ARNs:
      vectora-core: arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev:49
      common-deps: arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-common-deps-dev:11
   Updating vectora-inbox-ingest-v2-dev...
      [OK] Layers updated
   Updating vectora-inbox-normalize-score-v2-dev...
      [OK] Layers updated
   Updating vectora-inbox-newsletter-v2-dev...
      [OK] Layers updated

============================================================
[SUCCESS] Deployment to dev completed successfully!
============================================================
```

---

## 🔄 Workflow Complet

```
1. Modifier code dans src_v2/
2. Incrémenter VERSION
3. Build: python scripts/build/build_all.py
4. Deploy: python scripts/deploy/deploy_env.py --env dev  ← AUTOMATIQUE
5. Test: python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7
```

**Avant février 2026**:
```
4. Deploy layers: python scripts/deploy/deploy_env.py --env dev
5. Mise à jour manuelle: aws lambda update-function-configuration ...  ← MANUEL
6. Test: python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7
```

**Gain**: Suppression étape manuelle + Prévention erreurs

---

## 🚨 Troubleshooting

### Erreur: "Layer file not found"
**Cause**: Build pas exécuté  
**Solution**: `python scripts/build/build_all.py`

### Erreur: "Could not get layer version"
**Cause**: Layer jamais publié  
**Solution**: Vérifier que layer existe sur AWS ou ignorer warning

### Warning: "Lambda not found"
**Cause**: Lambda pas encore créée  
**Solution**: Normal pour première fois, créer Lambda d'abord

### Erreur: "Access Denied"
**Cause**: Permissions IAM insuffisantes  
**Solution**: Vérifier profil AWS `rag-lai-prod`

---

## 📚 Références

**Scripts**:
- `scripts/deploy/deploy_env.py` - Script principal
- `scripts/deploy/deploy_layer.py` - Publication layer
- `scripts/build/build_all.py` - Build artefacts

**Documentation**:
- `.q-context/vectora-inbox-workflows.md` - Workflows complets
- `.q-context/vectora-inbox-governance.md` - Règles gouvernance
- `docs/reports/development/diagnostic_deploy_script_20260202.md` - Diagnostic Phase 6ter

---

## 📝 Historique

**Avant 2026-02-02**:
- `deploy_env.py` publiait uniquement les layers
- Nécessitait commande manuelle `aws lambda update-function-configuration`
- Risque d'oubli de mise à jour des Lambdas

**Depuis 2026-02-02** (Phase 6ter):
- `deploy_env.py` publie layers ET met à jour Lambdas automatiquement
- 1 commande = déploiement complet
- Impossible d'oublier la mise à jour des Lambdas
- Gestion erreurs robuste

---

**Guide créé le**: 2026-02-02  
**Version**: 2.0 (automatisation complète)  
**Statut**: ✅ Opérationnel
