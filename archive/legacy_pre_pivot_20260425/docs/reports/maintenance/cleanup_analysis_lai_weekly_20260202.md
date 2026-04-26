# Analyse Nettoyage lai_weekly - 2026-02-02

## 📊 État Actuel

### Repo Local (client-config-examples/)

**Archive/** (8 fichiers obsolètes):
- lai_weekly_v3.yaml → v9.yaml
- lai_weekly_v5_test.yaml

**Racine** (3 fichiers legacy):
- lai_weekly.yaml
- client_config_template.yaml
- client_template_v2.yaml

**Production/**:
- lai_weekly_prod.yaml ✅ (à conserver)

**Templates/**:
- lai_weekly_template.yaml ✅ (à conserver)

**Test/** (vide actuellement):
- local/ (vide)
- aws/ (vide)

### AWS S3

**Dev (vectora-inbox-data-dev/curated/)**:
- lai_weekly_v3/ → v9/ (7 dossiers)
- Aucun client_config dans vectora-inbox-config-dev/client-configs/

**Stage (vectora-inbox-data-stage/curated/)**:
- lai_weekly_v7/ (1 dossier)
- Aucun client_config dans vectora-inbox-config-stage/client-configs/

**Prod**:
- Pas encore créé

### Scripts Invoke

**Test Events**:
- lai_weekly_v3.json
- lai_weekly_v7.json
- minimal_test.json

## 🎯 Stratégie de Nettoyage

### Principe: Garder Seulement le Nécessaire

**À CONSERVER**:
1. **Production**: lai_weekly_prod.yaml (config production future)
2. **Template**: lai_weekly_template.yaml (génération auto configs test)
3. **Dernière version validée**: lai_weekly_v9.yaml (référence dev)
4. **Stage actuel**: lai_weekly_v7 (données stage)

**À ARCHIVER/SUPPRIMER**:
1. Versions v3-v8 (sauf v7 stage et v9 dev)
2. Fichiers legacy racine
3. Test events obsolètes

## 📋 Plan de Nettoyage

### Phase 1: Repo Local

**Actions**:
1. Déplacer lai_weekly_v9.yaml de archive/ vers production/ (renommer lai_weekly_dev.yaml)
2. Supprimer archive/ complètement
3. Supprimer fichiers legacy racine (lai_weekly.yaml, client_config_template.yaml, client_template_v2.yaml)
4. Garder structure test/ pour futures générations auto

**Résultat**:
```
client-config-examples/
├── production/
│   ├── lai_weekly_prod.yaml (futur)
│   └── lai_weekly_dev.yaml (v9 actuel)
├── templates/
│   └── lai_weekly_template.yaml
├── test/
│   ├── local/ (auto-généré)
│   └── aws/ (auto-généré)
└── README.md
```

### Phase 2: AWS S3 Dev

**Données à conserver**:
- lai_weekly_v9/ (dernière version validée)

**Données à archiver**:
- lai_weekly_v3/ → v8/ (6 dossiers)

**Action**:
```bash
# Archiver anciennes versions
aws s3 sync s3://vectora-inbox-data-dev/curated/lai_weekly_v3/ \
  s3://vectora-inbox-backup-20260130/archive/dev/lai_weekly_v3/ --profile rag-lai-prod

# Répéter pour v4-v8

# Supprimer après vérification backup
aws s3 rm s3://vectora-inbox-data-dev/curated/lai_weekly_v3/ --recursive --profile rag-lai-prod
```

### Phase 3: AWS S3 Stage

**Données à conserver**:
- lai_weekly_v7/ (version stage actuelle)

**Action**: Rien (déjà propre)

### Phase 4: Scripts Invoke

**Test events à conserver**:
- minimal_test.json (générique)

**Test events à supprimer**:
- lai_weekly_v3.json
- lai_weekly_v7.json

**Raison**: Workflow E2E utilise maintenant --client-id dynamique, plus besoin d'events hardcodés

## 🔧 Script Automatisé

Créer `scripts/maintenance/cleanup_lai_weekly.py`:
- Mode dry-run par défaut
- Backup automatique avant suppression
- Logs détaillés
- Rollback possible

## 📊 Impact Estimé

### Espace Libéré

**Repo Local**: ~50 KB (fichiers yaml obsolètes)

**AWS S3 Dev**: À calculer
```bash
aws s3 ls s3://vectora-inbox-data-dev/curated/lai_weekly_v3/ --recursive --summarize --profile rag-lai-prod
```

### Coûts S3

Estimation: 6 dossiers × ~100 KB/dossier = ~600 KB
Coût mensuel actuel: ~$0.001/mois
Impact: Négligeable mais améliore clarté

## ✅ Checklist Exécution

- [ ] Phase 1: Nettoyage repo local
  - [ ] Backup archive/ localement
  - [ ] Déplacer v9 vers production/lai_weekly_dev.yaml
  - [ ] Supprimer archive/
  - [ ] Supprimer fichiers legacy racine
  - [ ] Commit changes

- [ ] Phase 2: Analyse taille S3 dev
  - [ ] Calculer taille v3-v8
  - [ ] Décider si archivage nécessaire

- [ ] Phase 3: Archivage S3 (si nécessaire)
  - [ ] Backup v3-v8 vers vectora-inbox-backup-20260130
  - [ ] Vérifier backups
  - [ ] Supprimer originaux

- [ ] Phase 4: Nettoyage scripts invoke
  - [ ] Supprimer test_events/lai_weekly_v3.json
  - [ ] Supprimer test_events/lai_weekly_v7.json
  - [ ] Commit changes

- [ ] Phase 5: Documentation
  - [ ] Mettre à jour README.md client-config-examples
  - [ ] Documenter nouvelle structure
  - [ ] Commit final

## 🎯 Résultat Attendu

**Structure Propre**:
- 1 config prod (futur)
- 1 config dev (v9 actuel)
- 1 template (génération auto)
- Test configs auto-générés (éphémères)

**AWS Propre**:
- Dev: Seulement v9 (dernière validée)
- Stage: Seulement v7 (version stage)
- Prod: Vide (pas encore déployé)

**Workflow Simplifié**:
- Nouveau test → Génère lai_weekly_test_XXX (local) ou lai_weekly_vX (AWS)
- Pas de réutilisation anciennes versions
- Nettoyage auto après validation

## 📝 Notes

**Règle Future**: 
- Garder max 2 versions dev (current + previous)
- Garder 1 version par env (stage, prod)
- Auto-cleanup après 30 jours si non utilisé

**Automation Possible**:
- Script cleanup hebdomadaire
- Alerte si >5 versions dev
- Auto-archive versions >30 jours
