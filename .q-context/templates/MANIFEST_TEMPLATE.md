# Manifest Changements - [TITRE MODIFICATION]

**Date**: YYYY-MM-DD  
**Branche**: feature/xxx  
**Objectif**: [Description courte de la modification]  
**Version**: X.Y.Z

---

## Fichiers Modifies

### Lambdas (src_v2/)
- [ ] Aucun

**OU**

- [ ] src_v2/vectora_core/normalization/bedrock_client.py
  - Lignes: XXX-YYY
  - Changement: [Description]
  - Impact: [Impact attendu]

- [ ] src_v2/lambdas/normalize_score_v2/handler.py
  - Lignes: XXX-YYY
  - Changement: [Description]
  - Impact: [Impact attendu]

### Prompts Bedrock (canonical/prompts/)
- [ ] Aucun

**OU**

- [ ] canonical/prompts/domain_scoring/lai_domain_scoring.yaml
  - Version: vX.Y -> vX.Z
  - Changement: [Description]
  - Impact: [Impact attendu]

### Canonical (canonical/)
- [ ] Aucun

**OU**

- [ ] canonical/domains/lai_domain_definition.yaml
  - Version: vX.Y -> vX.Z
  - Changement: [Description]
  - Impact: [Impact attendu]

- [ ] canonical/scopes/company_scopes.yaml
  - Changement: [Description]
  - Impact: [Impact attendu]

### Configuration
- [ ] VERSION
  - Avant: X.Y.Z
  - Apres: X.Y.Z+1
  - Raison: [Breaking/Feature/Fix]

---

## Impact S3

### Fichiers a uploader
- [ ] s3://vectora-inbox-data-dev/canonical/domains/lai_domain_definition.yaml
- [ ] s3://vectora-inbox-data-dev/canonical/prompts/domain_scoring/lai_domain_scoring.yaml

### Backup requis AVANT upload
```bash
# Backup canonical
aws s3 sync s3://vectora-inbox-data-dev/canonical/ .tmp/backup_canonical_$(date +%Y%m%d_%H%M%S)/ --profile rag-lai-prod

# Sauvegarder timestamp backup
echo "Backup: .tmp/backup_canonical_YYYYMMDD_HHMMSS" >> MANIFEST.md
```

---

## Tests Requis

### Test Local
- [ ] Validation structure fichiers
- [ ] Test unitaire si applicable
- [ ] Verification syntaxe YAML

### Test AWS Dev
- [ ] Client ID: lai_weekly_vX
- [ ] Ingest: [Statut]
- [ ] Normalize: [Statut]
- [ ] Comparaison vs V17 baseline

### Metriques Attendues
- Items ingeres: [Cible: 25-40]
- Companies: [Cible: >=70%]
- Items relevant: [Cible: >=60%]
- Score moyen: [Cible: 65-85]
- Faux negatifs: [Cible: <=1]

---

## Rollback Plan

### Si echec test AWS

**Etape 1: Restaurer S3**
```bash
# Restaurer canonical depuis backup
aws s3 sync .tmp/backup_canonical_YYYYMMDD_HHMMSS/ s3://vectora-inbox-data-dev/canonical/ --profile rag-lai-prod
```

**Etape 2: Rollback code**
```bash
# Revenir commit precedent
git reset --hard HEAD~1

# OU revenir version specifique
git checkout <commit-sha>
```

**Etape 3: Rebuild & Redeploy**
```bash
# Rebuild version precedente
python scripts/build/build_all.py

# Redeploy
python scripts/deploy/deploy_env.py --env dev
```

**Etape 4: Verifier**
```bash
# Test rapide
python scripts/invoke/invoke_normalize_score_v2.py --event lai_weekly_v17
```

---

## Checklist Pre-Commit

- [ ] Tous fichiers modifies listes ci-dessus
- [ ] VERSION incrementee si code Lambda modifie
- [ ] Backup S3 cree si canonical modifie
- [ ] Tests locaux passes
- [ ] MANIFEST.md complete

---

## Checklist Pre-Merge

- [ ] Test AWS dev reussi
- [ ] Metriques >= baseline V17
- [ ] Rapport E2E cree (format GOLDEN_TEST_E2E.md)
- [ ] Faux negatifs analyses
- [ ] Rollback plan teste (si critique)

---

## Notes

[Ajouter notes specifiques, observations, decisions prises]

---

**Manifest cree**: YYYY-MM-DD  
**Auteur**: [Nom]  
**Statut**: [DRAFT / EN_COURS / COMPLETE]
