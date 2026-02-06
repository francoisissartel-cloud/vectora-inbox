# Q Developer - Point d'Entree Vectora Inbox

**Version**: 2.0  
**Date**: 2026-02-04  
**Statut**: OBLIGATOIRE - Lire AVANT toute action

---

## AVANT TOUTE ACTION, LIRE DANS L'ORDRE:

### 1. CRITICAL_RULES.md (2 min) - OBLIGATOIRE
- 10 regles NON-NEGOCIABLES
- Checklist pre-action
- Architecture 3 Lambdas V2

### 2. GOLDEN_TEST_E2E.md (5 min) - REFERENCE
- Test de reference V17 (baseline)
- Metriques cibles
- Format rapport standard

### 3. Ce fichier (3 min) - WORKFLOW
- Workflow modifications
- Checklist validation
- Commandes essentielles

---

## WORKFLOW MODIFICATION (OBLIGATOIRE)

### Etape 1: Planification (AVANT code)

**Checklist**:
- [ ] Lire CRITICAL_RULES.md
- [ ] Identifier fichiers impactes:
  - [ ] Lambdas (src_v2/)
  - [ ] Prompts Bedrock (canonical/prompts/)
  - [ ] Canonical (canonical/domains/, canonical/scopes/)
- [ ] Creer MANIFEST.md listant tous les changements
- [ ] Valider plan avec utilisateur

**Template MANIFEST.md**:
```markdown
# Manifest - [Titre Modification]

## Fichiers Modifies
### Lambdas
- [ ] src_v2/xxx.py (description)

### Prompts
- [ ] canonical/prompts/xxx.yaml (description)

### Canonical
- [ ] canonical/domains/xxx.yaml (v1 -> v2)

### Config
- [ ] VERSION (1.X.Y -> 1.X.Z)

## Impact S3
- [ ] Upload: s3://vectora-inbox-data-dev/canonical/xxx

## Tests
- [ ] Test local
- [ ] Test AWS vs baseline V17

## Rollback
- Backup: .backup/YYYYMMDD_HHMMSS/
- Commandes: [restore]
```

---

### Etape 2: Backup Local (AVANT modification)

**Checklist**:
- [ ] Creer backup horodate
  ```bash
  python scripts/backup/create_local_backup.py --description "Avant [modification]"
  ```
- [ ] Verifier backup cree
  ```bash
  python scripts/backup/list_backups.py
  ```
- [ ] S3: Backup canonical si modifie
  ```bash
  aws s3 sync s3://vectora-inbox-data-dev/canonical/ .tmp/backup_canonical_$(date +%Y%m%d_%H%M%S)/ --profile rag-lai-prod
  ```
- [ ] Documenter backup dans MANIFEST.md

---

### Etape 3: Modification (Code)

**Checklist**:
- [ ] Modifier fichiers selon MANIFEST.md
- [ ] Incrementer VERSION si code Lambda modifie
- [ ] Comparer avec backup
  ```bash
  python scripts/backup/compare_with_backup.py --backup-id YYYYMMDD_HHMMSS
  ```

**IMPORTANT**: Backup local AVANT modification (regle critique #3)

---

### Etape 4: Build & Deploy (AWS)

**Checklist**:
- [ ] Build layers
  ```bash
  python scripts/build/build_all.py
  ```
- [ ] Deploy dev
  ```bash
  python scripts/deploy/deploy_env.py --env dev
  ```
- [ ] Upload canonical si modifie
  ```bash
  aws s3 sync canonical/ s3://vectora-inbox-data-dev/canonical/ --profile rag-lai-prod --region eu-west-3
  ```

---

### Etape 5: Test E2E (Validation)

**Checklist**:
- [ ] Choisir nouveau client_id (ex: lai_weekly_v18)
- [ ] Creer/upload config client
- [ ] Executer test E2E complet
  ```bash
  # Ingest
  aws lambda invoke --function-name vectora-inbox-ingest-v2-dev --payload '{"client_id":"lai_weekly_v18"}' .tmp/ingest_response.json --profile rag-lai-prod --region eu-west-3
  
  # Normalize (asynchrone - attendre 5-10 min)
  aws lambda invoke --function-name vectora-inbox-normalize-score-v2-dev --invocation-type Event --payload '{"client_id":"lai_weekly_v18"}' .tmp/normalize_response.json --profile rag-lai-prod --region eu-west-3
  
  # Telecharger resultats
  aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v18/YYYY/MM/DD/items.json .tmp/v18_curated.json --profile rag-lai-prod
  ```
- [ ] Analyser resultats
- [ ] Comparer vs baseline V17 (voir GOLDEN_TEST_E2E.md)

---

### Etape 6: Rapport (Documentation)

**Checklist**:
- [ ] Creer rapport selon format GOLDEN_TEST_E2E.md
- [ ] Fichier: `docs/reports/e2e/test_e2e_v18_rapport_YYYY-MM-DD.md`
- [ ] Inclure:
  - [ ] Resume executif (verdict)
  - [ ] Metriques comparatives (V17 vs V18)
  - [ ] Distribution sources/scores
  - [ ] Top 5 items relevant
  - [ ] Analyse faux negatifs
  - [ ] Recommandations
  - [ ] Annexes (fichiers, commandes, versions)

**Metriques obligatoires** (comparer vs V17):
```
Items ingeres:       X (V17: 31)
Companies:           X% (V17: 74%)
Items relevant:      X% (V17: 64%)
Score moyen:         X (V17: 71.5)
Faux negatifs:       X (V17: 0)
Domain scoring:      X% (V17: 100%)
```

**Verdict**:
- ✅ SUCCES: Toutes metriques >= seuils V17
- ⚠️ ATTENTION: 1-2 metriques < seuils
- ❌ ECHEC: 3+ metriques < seuils

---

### Etape 7: Decision (Merge ou Rollback)

**Si SUCCES**:
- [ ] Valider modifications finales
- [ ] Archiver backup
  ```bash
  python scripts/backup/archive_backup.py --backup-id YYYYMMDD_HHMMSS --success
  ```

**Si ECHEC**:
- [ ] Analyser causes
- [ ] Rollback local
  ```bash
  python scripts/backup/restore_backup.py --backup-id YYYYMMDD_HHMMSS
  ```
- [ ] Rollback S3 si necessaire
  ```bash
  aws s3 sync .tmp/backup_canonical_YYYYMMDD_HHMMSS/ s3://vectora-inbox-data-dev/canonical/ --profile rag-lai-prod
  ```
- [ ] Corriger et recommencer Etape 3

---

## COMMANDES ESSENTIELLES

### Backup & Restore Local
```bash
# Creer backup local
python scripts/backup/create_local_backup.py --description "Avant optimisation X"

# Lister backups
python scripts/backup/list_backups.py

# Comparer avec backup
python scripts/backup/compare_with_backup.py --backup-id 20260204_143022

# Restaurer backup
python scripts/backup/restore_backup.py --backup-id 20260204_143022
```

### Build & Deploy
```bash
# Build
python scripts/build/build_all.py

# Deploy dev
python scripts/deploy/deploy_env.py --env dev

# Upload canonical
aws s3 sync canonical/ s3://vectora-inbox-data-dev/canonical/ --profile rag-lai-prod --region eu-west-3
```

### Test E2E
```bash
# Ingest
aws lambda invoke --function-name vectora-inbox-ingest-v2-dev --payload '{"client_id":"lai_weekly_vX"}' .tmp/ingest_response.json --profile rag-lai-prod --region eu-west-3

# Normalize (asynchrone)
aws lambda invoke --function-name vectora-inbox-normalize-score-v2-dev --invocation-type Event --payload '{"client_id":"lai_weekly_vX"}' .tmp/normalize_response.json --profile rag-lai-prod --region eu-west-3

# Attendre 5-10 min puis telecharger
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_vX/YYYY/MM/DD/items.json .tmp/vX_curated.json --profile rag-lai-prod
```

### Snapshot & Diff
```bash
# Creer backup local AVANT modification
python scripts/backup/create_local_backup.py --description "Avant optimisation X"

# Lister backups disponibles
python scripts/backup/list_backups.py

# Comparer avec backup
python scripts/backup/compare_with_backup.py --backup-id 20260204_143022

# Diff detaille
python scripts/backup/compare_with_backup.py --backup-id 20260204_143022 --detailed
```

### Backup & Restore S3
```bash
# Backup canonical
aws s3 sync s3://vectora-inbox-data-dev/canonical/ .tmp/backup_canonical_$(date +%Y%m%d_%H%M%S)/ --profile rag-lai-prod

# Restore canonical
aws s3 sync .tmp/backup_canonical_YYYYMMDD_HHMMSS/ s3://vectora-inbox-data-dev/canonical/ --profile rag-lai-prod
```

### Analyse Resultats
```bash
# Compter items
python -c "import json; items=json.load(open('.tmp/vX_curated.json', encoding='utf-8')); print(f'Items: {len(items)}')"

# Metriques
python -c "import json; items=json.load(open('.tmp/vX_curated.json', encoding='utf-8')); with_ds=sum(1 for i in items if i.get('has_domain_scoring')); relevant=sum(1 for i in items if i.get('domain_scoring',{}).get('is_relevant')); companies=sum(1 for i in items if i.get('normalized_content',{}).get('entities',{}).get('companies')); scores=[i.get('domain_scoring',{}).get('score',0) for i in items if i.get('has_domain_scoring')]; print(f'Domain scoring: {with_ds}/{len(items)} ({with_ds/len(items)*100:.0f}%)'); print(f'Companies: {companies}/{len(items)} ({companies/len(items)*100:.0f}%)'); print(f'Relevant: {relevant}/{with_ds} ({relevant/with_ds*100:.0f}%)'); print(f'Score moyen: {sum(scores)/len(scores):.1f}')"
```

---

## REGLES CRITIQUES (RAPPEL)

1. ✅ Architecture 3 Lambdas V2 UNIQUEMENT
2. ✅ Code dans src_v2/ UNIQUEMENT
3. ✅ Git AVANT build
4. ✅ Environnement TOUJOURS explicite (--env dev)
5. ✅ Deploiement = Code + Data + Test
6. ✅ Tests local AVANT AWS
7. ✅ Client config auto-genere
8. ✅ Bedrock: us-east-1 + Sonnet
9. ✅ Temporaires dans .tmp/
10. ✅ Blueprint a jour

**Si UNE SEULE regle non respectee → STOP et corriger**

---

## QUESTIONS FREQUENTES

### Q: Dois-je suivre ce workflow pour TOUTE modification?
**R**: OUI. Meme pour petites modifications. Le workflow garantit stabilite.

### Q: Puis-je sauter l'etape backup?
**R**: NON. Backup obligatoire si canonical modifie. Rollback impossible sinon.

### Q: Puis-je deployer directement en stage?
**R**: NON. Toujours dev → test → stage. Regle critique #6.

### Q: Comment savoir si mes metriques sont bonnes?
**R**: Comparer vs baseline V17 dans GOLDEN_TEST_E2E.md. Seuils definis.

### Q: Que faire si test E2E echoue?
**R**: Analyser causes, rollback si necessaire, corriger, recommencer. Ne JAMAIS merge un echec.

---

## FICHIERS Q CONTEXT

**Fichiers essentiels** (3 fichiers):
1. `00-START-HERE.md` (ce fichier) - Point d'entree
2. `CRITICAL_RULES.md` - 10 regles non-negociables
3. `GOLDEN_TEST_E2E.md` - Test de reference V17

**Fichiers archives** (11 fichiers dans `archive/`):
- Consulter si besoin de details specifiques
- Mais 3 fichiers essentiels suffisent pour 95% des cas

---

**Point d'entree cree**: 2026-02-04  
**Version**: 2.0  
**Statut**: OPERATIONNEL - Workflow obligatoire
