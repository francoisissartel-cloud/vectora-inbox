# Workflow de Développement Standard - Vectora Inbox

**Date**: 2026-01-30  
**Version**: 1.0  
**Principe**: Repo local = Source unique de vérité

---

## 🎯 Principe Fondamental

**Toute modification passe par le repo local et les scripts standardisés.**

```
Repo Local → Build → Deploy Dev → Test → Promote Stage → Test → Commit
```

---

## 📋 Scénarios Quotidiens

### Scénario 1: Nouvelle Fonctionnalité

**Contexte**: Ajouter une nouvelle fonctionnalité dans vectora_core

```powershell
# 1. Développer dans repo local
cd src_v2/vectora_core/normalization
# Modifier le code...

# 2. Incrémenter version
# Éditer VERSION: VECTORA_CORE_VERSION=1.2.4 (était 1.2.3)

# 3. Build artefacts
python scripts/build/build_all.py

# 4. Deploy vers dev
python scripts/deploy/deploy_env.py --env dev

# 5. Tester en dev
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7

# 6. Si OK, promouvoir vers stage
python scripts/deploy/promote.py --to stage --version 1.2.4

# 7. Tester en stage
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7 --env stage

# 8. Commit
git add .
git commit -m "feat: nouvelle fonctionnalité extraction dates"
git push
```

**Durée estimée**: 30-60 minutes

---

### Scénario 2: Correction Bug Urgent

**Contexte**: Bug critique en production, correction rapide nécessaire

```powershell
# 1. Corriger dans repo local
cd src_v2/vectora_core/shared
# Corriger le bug...

# 2. Incrémenter version PATCH
# Éditer VERSION: VECTORA_CORE_VERSION=1.2.4 (était 1.2.3)

# 3. Build + Deploy dev
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev

# 4. Test rapide dev
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7

# 5. Si OK, promouvoir immédiatement vers stage
python scripts/deploy/promote.py --to stage --version 1.2.4

# 6. Test stage
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7 --env stage

# 7. Commit
git add .
git commit -m "fix: correction bug extraction dates"
git push
```

**Durée estimée**: 15-30 minutes

---

### Scénario 3: Mise à Jour Canonical

**Contexte**: Modifier scopes, prompts ou sources

```powershell
# 1. Modifier dans repo local
cd canonical/scopes
# Modifier tech_lai_ecosystem.yaml...

# 2. Incrémenter version canonical
# Éditer VERSION: CANONICAL_VERSION=1.2 (était 1.1)

# 3. Sync vers dev (pas de build nécessaire)
aws s3 sync canonical/ s3://vectora-inbox-config-dev/canonical/ \
  --profile rag-lai-prod \
  --region eu-west-3

# 4. Tester en dev
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7

# 5. Si OK, sync vers stage
aws s3 sync canonical/ s3://vectora-inbox-config-stage/canonical/ \
  --profile rag-lai-prod \
  --region eu-west-3

# 6. Tester en stage
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7 --env stage

# 7. Commit
git add canonical/
git commit -m "feat: ajout entités tech_lai_ecosystem"
git push
```

**Durée estimée**: 10-20 minutes

---

### Scénario 4: Nouvelle Configuration Client

**Contexte**: Créer configuration pour nouveau client

```powershell
# 1. Créer config depuis template
cd client-config-examples
cp client_template_v2.yaml pharma_weekly_v1.yaml
# Éditer pharma_weekly_v1.yaml...

# 2. Valider config localement
python scripts/maintenance/validate_client_config.py \
  --config client-config-examples/pharma_weekly_v1.yaml

# 3. Upload vers dev
aws s3 cp client-config-examples/pharma_weekly_v1.yaml \
  s3://vectora-inbox-config-dev/clients/pharma_weekly_v1.yaml \
  --profile rag-lai-prod \
  --region eu-west-3

# 4. Tester en dev
python scripts/invoke/invoke_ingest_v2.py --client-id pharma_weekly_v1
python scripts/invoke/invoke_normalize_score_v2.py --client-id pharma_weekly_v1

# 5. Si OK, upload vers stage
aws s3 cp client-config-examples/pharma_weekly_v1.yaml \
  s3://vectora-inbox-config-stage/clients/pharma_weekly_v1.yaml \
  --profile rag-lai-prod \
  --region eu-west-3

# 6. Commit exemple (pas la config réelle)
git add client-config-examples/pharma_weekly_v1.yaml
git commit -m "feat: configuration client pharma_weekly_v1"
git push
```

**Durée estimée**: 20-40 minutes

---

### Scénario 5: Rebuild Layer Sans Modification Code

**Contexte**: Reconstruire layer pour nouvelle version dépendances

```powershell
# 1. Mettre à jour requirements si nécessaire
cd src_v2
# Éditer requirements.txt...

# 2. Incrémenter version common-deps
# Éditer VERSION: COMMON_DEPS_VERSION=1.0.6 (était 1.0.5)

# 3. Build layer
python scripts/build/build_layer_common_deps.py

# 4. Deploy vers dev
python scripts/deploy/deploy_layer.py \
  --layer-file .build/layers/common-deps-1.0.6.zip \
  --env dev \
  --layer-name vectora-inbox-common-deps

# 5. Tester en dev
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7

# 6. Si OK, promouvoir vers stage
python scripts/deploy/promote.py --to stage --version 1.0.6

# 7. Commit
git add VERSION src_v2/requirements.txt
git commit -m "chore: mise à jour dépendances common-deps"
git push
```

**Durée estimée**: 15-25 minutes

---

## 🚫 Anti-Patterns à Éviter

### ❌ Modification Directe AWS

**NE JAMAIS FAIRE**:
```bash
# ❌ Upload manuel layer
aws lambda publish-layer-version \
  --layer-name vectora-inbox-vectora-core-dev \
  --zip-file fileb://layer.zip

# ❌ Update code Lambda manuel
aws lambda update-function-code \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --zip-file fileb://code.zip

# ❌ Copie S3 manuelle
aws s3 cp .build/layers/vectora-core-1.2.3.zip \
  s3://vectora-inbox-lambda-code-dev/layers/
```

**TOUJOURS UTILISER**:
```bash
# ✅ Scripts standardisés
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev
python scripts/deploy/promote.py --to stage --version 1.2.3
```

---

### ❌ Oublier Versioning

**NE JAMAIS FAIRE**:
```bash
# ❌ Build sans incrémenter version
python scripts/build/build_all.py
# → Écrase version précédente, perte traçabilité
```

**TOUJOURS FAIRE**:
```bash
# ✅ Incrémenter version AVANT build
# 1. Éditer VERSION
# 2. Build
python scripts/build/build_all.py
```

---

### ❌ Tester Directement en Stage

**NE JAMAIS FAIRE**:
```bash
# ❌ Deploy direct vers stage sans test dev
python scripts/deploy/deploy_env.py --env stage
```

**TOUJOURS FAIRE**:
```bash
# ✅ Workflow complet
python scripts/deploy/deploy_env.py --env dev
# Tester en dev
python scripts/deploy/promote.py --to stage --version X.Y.Z
# Tester en stage
```

---

## 📊 Checklist Avant Commit

Avant chaque commit, vérifier:

- [ ] Version incrémentée dans `VERSION`
- [ ] Build réussi (`python scripts/build/build_all.py`)
- [ ] Tests dev passés
- [ ] Aucun fichier temporaire à la racine
- [ ] Tous les temporaires dans `.tmp/`
- [ ] Documentation mise à jour si nécessaire
- [ ] Message commit descriptif
- [ ] Test E2E documenté si modification majeure (utiliser template `docs/templates/TEMPLATE_TEST_E2E_STANDARD.md`)

---

## 📦 Guide Incrémentation VERSION

### Tableau de Décision

| Type Modification | Exemple | Incrémentation | Résultat |
|-------------------|---------|----------------|----------|
| Ajout fonction | extract_dates() | MINOR | 1.2.3 → 1.3.0 |
| Ajout paramètre | new_param=True | MINOR | 1.2.3 → 1.3.0 |
| Correction bug | fix typo | PATCH | 1.2.3 → 1.2.4 |
| Correction crash | fix null pointer | PATCH | 1.2.3 → 1.2.4 |
| Rename fonction | extract() → get() | MAJOR | 1.2.3 → 2.0.0 |
| Suppression fonction | remove old_func() | MAJOR | 1.2.3 → 2.0.0 |
| Mise à jour dépendance | PyYAML 6.0 → 6.1 | PATCH | 1.0.5 → 1.0.6 |
| Ajout dépendance | + requests | MINOR | 1.0.5 → 1.1.0 |

### Format Sémantique

```
MAJOR.MINOR.PATCH
  1  .  2  .  3

MAJOR : Breaking change (incompatible)
MINOR : Nouvelle fonctionnalité (compatible)
PATCH : Correction bug (compatible)
```

**Guide complet** : `docs/guides/comprendre_versioning.md`

---

## 🔄 Workflow Complet Résumé

```
┌─────────────────┐
│ 1. Modifier     │
│    Repo Local   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. Incrémenter  │
│    VERSION      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. Build        │
│    Artefacts    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. Deploy Dev   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 5. Test Dev     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 6. Promote      │
│    Stage        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 7. Test Stage   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 8. Commit Git   │
└─────────────────┘
```

---

## 📞 Support

**En cas de problème**:

1. Consulter logs: `.tmp/logs/`
2. Vérifier version: `cat VERSION`
3. Valider build: `ls .build/layers/`
4. Tester dry-run: `python scripts/deploy/deploy_env.py --env dev --dry-run`

**Documentation**:
- Règles développement: `.q-context/vectora-inbox-development-rules.md`
- Plan gouvernance: `docs/plans/plan_gouvernance_repo_et_environnements.md`
- Scripts annexes: `docs/plans/annexes_scripts_gouvernance.md`

---

**Workflow Standard - Version 1.0**  
**Date**: 2026-01-30  
**Statut**: Gouvernance en place
