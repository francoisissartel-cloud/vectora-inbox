# Règles Critiques Vectora Inbox

**Date**: 2026-02-02  
**Version**: 1.0  
**Objectif**: Top 10 règles NON-NÉGOCIABLES que Q Developer DOIT TOUJOURS respecter

---

## 🚨 TOP 10 RÈGLES CRITIQUES

### 1. Architecture 3 Lambdas V2 UNIQUEMENT

**✅ OBLIGATOIRE**:
```
ingest-v2 → normalize-score-v2 → newsletter-v2
```

**❌ INTERDIT**:
- Architecture 2 Lambdas (ingest-normalize, engine)
- Références au blueprint historique
- Proposer architecture legacy

**Raison**: Architecture V2 validée E2E, stabilisée, documentée.

---

### 2. Code Source: src_v2/ UNIQUEMENT

**✅ OBLIGATOIRE**:
- Tout code dans `src_v2/`
- Handlers dans `src_v2/lambdas/`
- Logique métier dans `src_v2/vectora_core/`

**❌ INTERDIT**:
- Utiliser `archive/_src/` (legacy archivé)
- Créer code hors de `src_v2/`
- Dupliquer vectora_core

**Raison**: `src_v2/` conforme règles hygiène V4, architecture modulaire validée.

---

### 3. Backup Local AVANT Modification

**✅ OBLIGATOIRE**:
```bash
# Creer backup horodate
python scripts/backup/create_local_backup.py --description "Avant modification X"

# Structure backup:
.backup/
├── 20260204_143022_avant_modification_X/
│   ├── src_v2/          # Copie complete code
│   ├── canonical/       # Copie complete config
│   ├── VERSION          # Version actuelle
│   └── BACKUP_INFO.txt  # Metadata backup
```

**❌ INTERDIT**:
- Modifier sans backup
- Ecraser backup existant
- Backup partiel (src_v2 OU canonical)

**Raison**: Backup local = rollback instantané. Copie complète garantit restauration exacte.

---

### 4. Environnement TOUJOURS Explicite

**✅ OBLIGATOIRE**:
```bash
python scripts/deploy/deploy_env.py --env dev
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7 --env dev
aws s3 sync canonical/ s3://vectora-inbox-config-dev/canonical/
```

**❌ INTERDIT**:
```bash
# ❌ Sans --env (risque déploiement mauvais environnement)
python scripts/deploy/deploy_env.py
aws s3 mb s3://vectora-inbox-config
```

**Raison**: Éviter déploiements accidentels vers mauvais environnement.

**Q Developer DOIT**: Refuser toute commande AWS sans environnement explicite.

---

### 5. Déploiement AWS = Code + Data + Test

**✅ CHECKLIST COMPLÈTE**:
- [ ] Build layers: `python scripts/build/build_all.py`
- [ ] Deploy layers: `python scripts/deploy/deploy_env.py --env dev`
- [ ] Upload canonical (si modifié): `aws s3 sync canonical/ s3://vectora-inbox-config-dev/canonical/`
- [ ] Upload client configs (si modifié)
- [ ] Test E2E AWS: `python scripts/invoke/invoke_e2e_workflow.py --client-id lai_weekly_vX --env dev`
- [ ] Vérifier logs Lambda
- [ ] Confirmer résultats

**❌ INTERDIT**:
- Déployer code sans déployer data (canonical)
- Assumer que fichiers canonical sont déjà sur S3
- Dire "déploiement complété" sans test E2E

**Raison**: Lambda charge canonical depuis S3. Si canonical manquant → FileNotFoundError.

**Phrase magique Q**: "Ai-je créé/modifié des fichiers dans canonical/? Sont-ils sur S3?"

---

### 6. Tests Local AVANT AWS

**✅ WORKFLOW OBLIGATOIRE**:
```bash
# 1. Test local
python tests/local/test_e2e_runner.py --new-context "Test X"
python tests/local/test_e2e_runner.py --run

# 2. SI LOCAL OK → Deploy AWS
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev

# 3. Test AWS
python tests/aws/test_e2e_runner.py --promote "Validation"
python tests/aws/test_e2e_runner.py --run
```

**❌ INTERDIT**:
- Deploy AWS sans test local
- Bypasser système de contextes
- Tester directement en stage

**Raison**: Protections automatiques. Impossible de promouvoir vers AWS sans succès local.

---

### 7. Client Config Auto-Généré

**✅ OBLIGATOIRE**:
```bash
# Runners génèrent automatiquement
python tests/local/test_e2e_runner.py --new-context "Test"  # → lai_weekly_test_XXX
python tests/aws/test_e2e_runner.py --promote "Validation"  # → lai_weekly_vX
```

**❌ INTERDIT**:
- Créer `lai_weekly_vX.yaml` manuellement
- Réutiliser client_id d'un test précédent
- Bypasser génération automatique

**Raison**: 1 contexte = 1 client_config = 1 dossier S3 isolé. Garantit isolation tests.

---

### 8. Bedrock: us-east-1 + Sonnet

**✅ CONFIGURATION VALIDÉE E2E**:
```bash
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_REGION=us-east-1
```

**❌ INTERDIT**:
- Changer modèle Bedrock sans validation E2E
- Utiliser autre région que us-east-1
- Proposer modèles non testés

**Raison**: Configuration validée avec lai_weekly_v3 (15 items, 30 appels, 100% succès).

---

### 9. Temporaires dans .tmp/

**✅ OBLIGATOIRE**:
```
.tmp/
├── events/          # Events de test
├── responses/       # Réponses Lambda
├── items/           # Items temporaires
└── logs/            # Logs debug

.build/
├── layers/          # ZIPs layers
└── packages/        # Packages Lambda
```

**❌ INTERDIT À LA RACINE**:
- `event_*.json`
- `response_*.json`
- `items_*.json`
- `logs_*.txt`
- `*.zip`
- Scripts one-shot

**Raison**: Racine propre = repo maintenable. Temporaires dans `.tmp/` (gitignored).

---

### 10. Blueprint Maintenu à Jour

**✅ OBLIGATOIRE**:

Quand Q modifie:
- Architecture (Lambda, S3, IAM)
- Configuration Bedrock (modèle, région)
- Variables d'environnement critiques
- Client de référence

**Q DOIT**:
1. Modifier le code
2. Proposer: "Je vais aussi mettre à jour le blueprint"
3. Mettre à jour `docs/architecture/blueprint-v2-ACTUAL-2026.yaml`
4. Ajouter entrée dans `metadata.changes`
5. Commit ENSEMBLE (code + blueprint)

**❌ INTERDIT**:
- Modifier code sans mettre à jour blueprint
- Commit code et blueprint séparément
- Oublier date `last_updated`

**Raison**: Blueprint = documentation vivante. Doit refléter état réel du système.

**Guide**: `docs/architecture/BLUEPRINT_MAINTENANCE.md`

---

## 📋 CHECKLIST Q DEVELOPER

**Avant toute action, Q DOIT vérifier**:

- [ ] Architecture 3 Lambdas V2 ?
- [ ] Code dans src_v2/ ?
- [ ] Git avant build ?
- [ ] Environnement explicite ?
- [ ] Déploiement complet (code + data + test) ?
- [ ] Tests local avant AWS ?
- [ ] Client config auto-généré ?
- [ ] Bedrock us-east-1 + Sonnet ?
- [ ] Temporaires dans .tmp/ ?
- [ ] Blueprint à jour ?

**Si UNE SEULE réponse = NON → STOP et corriger**

---

## 🎯 UTILISATION PAR Q DEVELOPER

**Q DOIT**:
- Lire ce fichier EN PREMIER avant toute action
- Vérifier conformité à CHAQUE étape
- Refuser actions non conformes
- Proposer alternatives conformes

**Q NE DOIT JAMAIS**:
- Ignorer ces règles
- Proposer contournements
- Assumer exceptions

**En cas de doute**: Demander clarification utilisateur.

---

**Règles créées le**: 2026-02-02  
**Version**: 1.0  
**Statut**: Opérationnel - Règles NON-NÉGOCIABLES
