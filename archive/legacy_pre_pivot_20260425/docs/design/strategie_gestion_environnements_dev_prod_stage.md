# Stratégie de Gestion des Environnements Dev/Prod/Stage - Vectora Inbox

**Date**: 2026-01-30  
**Auteur**: Expert Cloud Architect  
**Objectif**: Évaluation diagnostique complète et recommandations pour gestion pérenne des environnements

---

## 📊 DIAGNOSTIC COMPLET

### 1. État Actuel de l'Infrastructure AWS

#### 1.1 Convention de Nommage Actuelle

**✅ CONSTAT: Convention `-dev` déjà en place et cohérente**

**Lambdas (3 fonctions V2):**
```
vectora-inbox-ingest-v2-dev
vectora-inbox-normalize-score-v2-dev
vectora-inbox-newsletter-v2-dev
```

**Buckets S3 (4 buckets):**
```
vectora-inbox-config-dev
vectora-inbox-data-dev
vectora-inbox-newsletters-dev
vectora-inbox-lambda-code-dev
```

**Lambda Layers (6 layers):**
```
vectora-inbox-common-deps-dev
vectora-inbox-vectora-core-dev (v42)
vectora-inbox-vectora-core-approche-b-dev (v10)
vectora-inbox-dependencies (sans suffixe)
vectora-inbox-yaml-fix-dev
vectora-inbox-yaml-minimal-dev
```

**Stacks CloudFormation (4 stacks):**
```
vectora-inbox-s0-core-dev
vectora-inbox-s0-iam-dev
vectora-inbox-s1-runtime-dev
vectora-inbox-s1-ingest-v2-dev
```

#### 1.2 Structure des Données S3

**Bucket data-dev:**
```
s3://vectora-inbox-data-dev/
├── clients/          # Configurations clients (legacy?)
├── curated/          # Items scorés et matchés (sortie normalize-score-v2)
├── deployments/      # Métadonnées de déploiement
├── ingested/         # Items bruts ingérés (sortie ingest-v2)
├── lambda-packages/  # Packages Lambda
├── normalized/       # Items normalisés (legacy?)
└── raw/              # Données brutes (debug)
```

**Bucket config-dev:**
```
s3://vectora-inbox-config-dev/
├── clients/          # Configurations clients actives
│   ├── lai_weekly_v4.yaml
│   ├── lai_weekly_v5.yaml
│   ├── lai_weekly_v6.yaml
│   └── lai_weekly_v7.yaml (POC actuel)
├── canonical/        # Scopes, prompts, sources métier
└── backups/          # Sauvegardes configurations
```

#### 1.3 Client de Référence Actuel

**POC en cours: lai_weekly_v7**
- Configuration: `s3://vectora-inbox-config-dev/clients/lai_weekly_v7.yaml`
- Données curated: `s3://vectora-inbox-data-dev/curated/lai_weekly_v7/2026/01/29/items.json`
- Statut: Moteur fonctionnel avec problèmes de bruit et prompts à optimiser

---

## 🎯 ÉVALUATION EXPERT

### 2. Points Forts de l'Architecture Actuelle

✅ **Convention de nommage cohérente**: Suffixe `-dev` appliqué systématiquement  
✅ **Architecture 3 Lambdas V2**: Séparation claire des responsabilités  
✅ **Infrastructure as Code**: CloudFormation pour toutes les ressources  
✅ **Versioning S3**: Activé sur tous les buckets (rollback possible)  
✅ **Séparation config/data**: Buckets distincts pour configuration et données  
✅ **Versioning client**: lai_weekly_v4 → v7 (itérations incrémentales)

### 3. Lacunes Identifiées

❌ **Pas d'environnement prod/stage**: Tout est en `-dev`  
❌ **Pas de stratégie de promotion**: Comment passer de dev → stage → prod?  
❌ **Versioning client non structuré**: v4, v5, v6, v7 sans distinction dev/prod  
❌ **Layers multiples**: 6 layers avec doublons (vectora-core vs vectora-core-approche-b)  
❌ **Pas de tagging environnement**: Difficile de filtrer ressources par env  
❌ **Documentation infrastructure**: Pas de guide de déploiement multi-env

### 4. Risques Identifiés

🔴 **CRITIQUE**: Pas de sauvegarde du moteur fonctionnel actuel  
🔴 **CRITIQUE**: Modifications directes en dev peuvent casser le POC v7  
🟡 **MOYEN**: Confusion entre versions client (v7) et environnements (dev/prod)  
🟡 **MOYEN**: Pas de stratégie de rollback claire  
🟡 **MOYEN**: Coûts AWS non séparés par environnement

---

## 🏗️ STRATÉGIE RECOMMANDÉE

### 5. Principes Directeurs

**Minimaliste**: Ne créer que ce qui est strictement nécessaire  
**Progressif**: Commencer par sauvegarder dev, puis créer prod quand stable  
**Non-disruptif**: Ne pas toucher au moteur dev actuel (lai_weekly_v7)  
**Pérenne**: Conventions claires et documentées pour l'équipe

### 6. Convention de Nommage Recommandée

#### 6.1 Suffixes d'Environnement

```
-dev     : Développement et expérimentation
-stage   : Pré-production (validation avant prod)
-prod    : Production (clients réels)
```

#### 6.2 Ressources AWS

**Lambdas:**
```
vectora-inbox-{fonction}-v2-{env}

Exemples:
vectora-inbox-ingest-v2-dev
vectora-inbox-ingest-v2-stage
vectora-inbox-ingest-v2-prod
```

**Buckets S3:**
```
vectora-inbox-{type}-{env}

Exemples:
vectora-inbox-config-dev
vectora-inbox-config-stage
vectora-inbox-config-prod
```

**Lambda Layers:**
```
vectora-inbox-{nom}-{env}

Exemples:
vectora-inbox-vectora-core-dev
vectora-inbox-vectora-core-prod
vectora-inbox-common-deps-dev
vectora-inbox-common-deps-prod
```

**Stacks CloudFormation:**
```
vectora-inbox-{stack}-{env}

Exemples:
vectora-inbox-s0-core-dev
vectora-inbox-s0-core-prod
```

#### 6.3 Configurations Client

**Distinction version client vs environnement:**

```yaml
# Fichier: s3://vectora-inbox-config-{env}/clients/lai_weekly.yaml

client_profile:
  client_id: "lai_weekly"           # ID stable (pas de v7)
  version: "7.0.0"                  # Version de la config
  environment: "dev"                # Environnement de déploiement
```

**Rationale:**
- `client_id` stable: `lai_weekly` (pas `lai_weekly_v7`)
- `version` pour itérations: `7.0.0` → `7.1.0` → `8.0.0`
- `environment` pour déploiement: `dev` / `stage` / `prod`

**Avantages:**
- ✅ Même config client peut être promue dev → stage → prod
- ✅ Versioning sémantique clair (7.0.0 = version config)
- ✅ Pas de confusion entre version et environnement

---

## 📋 PLAN D'ACTION RECOMMANDÉ

### Phase 1: Sauvegarde et Stabilisation (IMMÉDIAT)

**Objectif**: Sauvegarder l'état actuel du moteur lai_weekly_v7 fonctionnel

#### 1.1 Snapshot Infrastructure Dev

```bash
# Créer dossier de sauvegarde
mkdir -p backup/snapshot_lai_v7_$(date +%Y%m%d)

# Sauvegarder configurations client
aws s3 cp s3://vectora-inbox-config-dev/clients/lai_weekly_v7.yaml \
  backup/snapshot_lai_v7_$(date +%Y%m%d)/

# Sauvegarder canonical (scopes, prompts, sources)
aws s3 sync s3://vectora-inbox-config-dev/canonical/ \
  backup/snapshot_lai_v7_$(date +%Y%m%d)/canonical/

# Sauvegarder dernières données curated
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v7/2026/01/29/items.json \
  backup/snapshot_lai_v7_$(date +%Y%m%d)/curated_items.json

# Sauvegarder versions Lambda actuelles
aws lambda get-function --function-name vectora-inbox-ingest-v2-dev \
  --query 'Configuration' > backup/snapshot_lai_v7_$(date +%Y%m%d)/lambda_ingest_config.json

aws lambda get-function --function-name vectora-inbox-normalize-score-v2-dev \
  --query 'Configuration' > backup/snapshot_lai_v7_$(date +%Y%m%d)/lambda_normalize_config.json

aws lambda get-function --function-name vectora-inbox-newsletter-v2-dev \
  --query 'Configuration' > backup/snapshot_lai_v7_$(date +%Y%m%d)/lambda_newsletter_config.json

# Sauvegarder versions layers
aws lambda list-layer-versions --layer-name vectora-inbox-vectora-core-dev \
  --query 'LayerVersions[0]' > backup/snapshot_lai_v7_$(date +%Y%m%d)/layer_vectora_core.json

aws lambda list-layer-versions --layer-name vectora-inbox-common-deps-dev \
  --query 'LayerVersions[0]' > backup/snapshot_lai_v7_$(date +%Y%m%d)/layer_common_deps.json
```

#### 1.2 Tag Ressources Dev

```bash
# Tagger toutes les ressources dev pour identification
aws lambda tag-resource \
  --resource arn:aws:lambda:eu-west-3:786469175371:function:vectora-inbox-ingest-v2-dev \
  --tags Environment=dev,Snapshot=lai_v7_20260130,Status=stable

# Répéter pour toutes les Lambdas et layers
```

#### 1.3 Documentation État Actuel

Créer `docs/snapshots/lai_v7_snapshot_20260130.md` avec:
- Versions exactes de toutes les ressources
- ARNs des layers utilisés
- Configuration client lai_weekly_v7.yaml
- Résultats dernière exécution réussie
- Problèmes connus (bruit, prompts)

### Phase 2: Refactoring Configuration Client (COURT TERME)

**Objectif**: Séparer version client et environnement

#### 2.1 Nouvelle Structure Configuration

```yaml
# Fichier: client-config-examples/lai_weekly.yaml (template)

client_profile:
  name: "LAI Intelligence Weekly"
  client_id: "lai_weekly"              # ID stable
  version: "7.0.0"                     # Version config (sémantique)
  active: true
  language: "en"
  frequency: "weekly"

metadata:
  config_version: "7.0.0"
  created_date: "2026-01-30"
  last_modified: "2026-01-30"
  changelog:
    - version: "7.0.0"
      date: "2026-01-30"
      changes: "Extraction dates Bedrock, prompts éditoriaux"
    - version: "6.0.0"
      date: "2026-01-27"
      changes: "Fresh run test, domaine unique"
```

#### 2.2 Déploiement par Environnement

```bash
# Dev: Expérimentation et tests
aws s3 cp client-config-examples/lai_weekly.yaml \
  s3://vectora-inbox-config-dev/clients/lai_weekly.yaml

# Stage: Validation pré-prod (quand créé)
aws s3 cp client-config-examples/lai_weekly.yaml \
  s3://vectora-inbox-config-stage/clients/lai_weekly.yaml

# Prod: Client réel (quand stable)
aws s3 cp client-config-examples/lai_weekly.yaml \
  s3://vectora-inbox-config-prod/clients/lai_weekly.yaml
```

### Phase 3: Création Environnement Stage (MOYEN TERME)

**Objectif**: Environnement de validation avant production

#### 3.1 Déploiement Infrastructure Stage

```bash
# Stack S0-core-stage
aws cloudformation deploy \
  --template-file infra/s0-core.yaml \
  --stack-name vectora-inbox-s0-core-stage \
  --parameter-overrides Env=stage ProjectName=vectora-inbox \
  --region eu-west-3 \
  --profile rag-lai-prod

# Stack S0-iam-stage
aws cloudformation deploy \
  --template-file infra/s0-iam.yaml \
  --stack-name vectora-inbox-s0-iam-stage \
  --parameter-overrides Env=stage \
    ConfigBucketName=vectora-inbox-config-stage \
    DataBucketName=vectora-inbox-data-stage \
    NewslettersBucketName=vectora-inbox-newsletters-stage \
  --capabilities CAPABILITY_IAM \
  --region eu-west-3 \
  --profile rag-lai-prod

# Stack S1-runtime-stage
aws cloudformation deploy \
  --template-file infra/s1-runtime.yaml \
  --stack-name vectora-inbox-s1-runtime-stage \
  --parameter-overrides Env=stage \
    ConfigBucketName=vectora-inbox-config-stage \
    DataBucketName=vectora-inbox-data-stage \
    NewslettersBucketName=vectora-inbox-newsletters-stage \
    IngestNormalizeRoleArn=<ARN_from_s0-iam-stage> \
    EngineRoleArn=<ARN_from_s0-iam-stage> \
  --region eu-west-3 \
  --profile rag-lai-prod
```

#### 3.2 Promotion Code Dev → Stage

```bash
# Copier layers validés en dev vers stage
aws lambda publish-layer-version \
  --layer-name vectora-inbox-vectora-core-stage \
  --content S3Bucket=vectora-inbox-lambda-code-dev,S3Key=layers/vectora-core-v42.zip \
  --compatible-runtimes python3.11 python3.12

# Copier configurations canonical
aws s3 sync s3://vectora-inbox-config-dev/canonical/ \
  s3://vectora-inbox-config-stage/canonical/

# Copier configuration client validée
aws s3 cp s3://vectora-inbox-config-dev/clients/lai_weekly.yaml \
  s3://vectora-inbox-config-stage/clients/lai_weekly.yaml
```

### Phase 4: Création Environnement Prod (LONG TERME)

**Objectif**: Environnement production pour clients réels

**Critères de passage stage → prod:**
- ✅ Moteur stable sur stage pendant 2 semaines minimum
- ✅ Taux de bruit < 10%
- ✅ Prompts validés et optimisés
- ✅ Coûts Bedrock maîtrisés
- ✅ Tests E2E passés sur stage
- ✅ Documentation complète

**Déploiement identique à stage avec `Env=prod`**

---

## 🔧 AMÉLIORATIONS RÈGLES DE DÉVELOPPEMENT

### 7. Modifications Recommandées pour vectora-inbox-development-rules.md

#### 7.1 Nouvelle Section: Gestion des Environnements

```markdown
## 🌍 GESTION DES ENVIRONNEMENTS

### Environnements Disponibles

**dev**: Développement et expérimentation
- Modifications fréquentes autorisées
- Tests de nouvelles fonctionnalités
- Coûts AWS non critiques
- Données de test et POC

**stage**: Pré-production et validation
- Code stable uniquement
- Validation avant production
- Tests E2E complets
- Données réalistes

**prod**: Production clients réels
- Code validé en stage uniquement
- Aucune modification directe
- Monitoring actif
- SLA et disponibilité critiques

### Convention de Nommage par Environnement

**Ressources AWS:**
```
{resource-name}-{env}

Exemples:
vectora-inbox-ingest-v2-dev
vectora-inbox-config-stage
vectora-inbox-vectora-core-prod
```

**Configurations Client:**
```yaml
client_profile:
  client_id: "lai_weekly"      # ID stable
  version: "7.0.0"             # Version config
  
# Déploiement:
# dev:   s3://vectora-inbox-config-dev/clients/lai_weekly.yaml
# stage: s3://vectora-inbox-config-stage/clients/lai_weekly.yaml
# prod:  s3://vectora-inbox-config-prod/clients/lai_weekly.yaml
```

### Workflow de Promotion

```
dev → stage → prod

1. Développement en dev
2. Tests locaux + validation dev
3. Promotion vers stage (manuel)
4. Tests E2E stage
5. Promotion vers prod (manuel + approbation)
```

### Variables d'Environnement Lambda

Toutes les Lambdas doivent lire `ENV` pour adapter leur comportement:

```python
env = os.environ.get("ENV", "dev")
config_bucket = f"vectora-inbox-config-{env}"
data_bucket = f"vectora-inbox-data-{env}"
```
```

#### 7.2 Nouvelle Section: Snapshots et Rollback

```markdown
## 📸 SNAPSHOTS ET ROLLBACK

### Avant Modifications Majeures

**Créer snapshot complet:**
```bash
python scripts/maintenance/create_snapshot.py --env dev --name "pre_migration_v8"
```

**Contenu snapshot:**
- Configurations client S3
- Canonical (scopes, prompts, sources)
- Versions Lambda (ARNs)
- Versions layers (ARNs)
- Dernières données curated
- Métadonnées infrastructure

### Rollback en Cas de Problème

```bash
python scripts/maintenance/rollback_snapshot.py --snapshot "pre_migration_v8"
```

### Snapshots Automatiques

- Avant chaque déploiement Lambda
- Avant modification canonical
- Avant promotion stage → prod
```

---

## 📊 TABLEAU RÉCAPITULATIF

### 8. Comparaison État Actuel vs Recommandé

| Aspect | État Actuel | Recommandé | Priorité |
|--------|-------------|------------|----------|
| **Environnements** | dev uniquement | dev + stage + prod | HAUTE |
| **Nommage ressources** | `-dev` cohérent | `-{env}` cohérent | MOYENNE |
| **Config client** | `lai_weekly_v7` | `lai_weekly` v7.0.0 | HAUTE |
| **Snapshots** | Manuels ad-hoc | Automatisés | HAUTE |
| **Promotion code** | Manuelle | Scriptée | MOYENNE |
| **Rollback** | Difficile | Automatisé | HAUTE |
| **Tagging AWS** | Minimal | Complet | BASSE |
| **Documentation** | Partielle | Complète | MOYENNE |

---

## 🎯 RECOMMANDATIONS FINALES

### 9. Actions Immédiates (Cette Semaine)

1. **Créer snapshot lai_v7** (Phase 1.1)
   - Sauvegarder toutes les ressources actuelles
   - Documenter état fonctionnel
   - Créer point de restauration

2. **Refactorer config client** (Phase 2.1)
   - Créer `lai_weekly.yaml` (sans v7)
   - Ajouter champ `version: "7.0.0"`
   - Tester avec moteur actuel

3. **Mettre à jour règles développement**
   - Ajouter section environnements
   - Documenter convention nommage
   - Expliquer workflow promotion

### 10. Actions Court Terme (2-4 Semaines)

4. **Créer environnement stage**
   - Déployer stacks CloudFormation stage
   - Copier code validé dev → stage
   - Tester E2E sur stage

5. **Créer scripts promotion**
   - `scripts/deploy/promote_dev_to_stage.sh`
   - `scripts/deploy/promote_stage_to_prod.sh`
   - Validation automatique avant promotion

6. **Implémenter snapshots automatiques**
   - `scripts/maintenance/create_snapshot.py`
   - `scripts/maintenance/rollback_snapshot.py`
   - Intégrer dans workflow déploiement

### 11. Actions Long Terme (1-3 Mois)

7. **Créer environnement prod**
   - Quand moteur stable en stage
   - Déployer infrastructure prod
   - Migrer premier client réel

8. **Monitoring multi-environnement**
   - Dashboards CloudWatch par env
   - Alertes différenciées dev/stage/prod
   - Métriques coûts par environnement

9. **CI/CD Pipeline**
   - Tests automatisés avant promotion
   - Déploiement automatisé stage
   - Approbation manuelle prod

---

## ✅ CHECKLIST DE VALIDATION

### Avant de Commencer

- [ ] Snapshot complet lai_v7 créé
- [ ] Documentation état actuel complète
- [ ] Équipe alignée sur stratégie
- [ ] Budget AWS validé pour stage/prod

### Après Phase 1 (Sauvegarde)

- [ ] Backup lai_v7 testé et restaurable
- [ ] Point de rollback fonctionnel
- [ ] Documentation snapshot à jour

### Après Phase 2 (Refactoring Config)

- [ ] Config `lai_weekly.yaml` testée en dev
- [ ] Moteur fonctionne avec nouvelle config
- [ ] Pas de régression fonctionnelle

### Après Phase 3 (Stage)

- [ ] Infrastructure stage déployée
- [ ] Tests E2E passés sur stage
- [ ] Workflow promotion dev→stage validé

### Après Phase 4 (Prod)

- [ ] Infrastructure prod déployée
- [ ] Premier client migré avec succès
- [ ] Monitoring prod opérationnel

---

## 📝 CONCLUSION

### État Actuel: SOLIDE MAIS INCOMPLET

Votre infrastructure actuelle est **bien structurée** avec:
- Convention `-dev` cohérente
- Architecture 3 Lambdas V2 claire
- Infrastructure as Code (CloudFormation)
- Versioning S3 activé

Mais il manque:
- Environnements stage et prod
- Stratégie de promotion claire
- Snapshots automatisés
- Distinction version client vs environnement

### Stratégie Recommandée: PROGRESSIVE ET SÉCURISÉE

1. **Sauvegarder d'abord** (lai_v7 snapshot)
2. **Refactorer config client** (version vs environnement)
3. **Créer stage** (validation pré-prod)
4. **Créer prod** (quand stable)

### Principe Directeur: NE PAS CASSER LE MOTEUR ACTUEL

Toutes les modifications doivent:
- ✅ Préserver le moteur lai_v7 fonctionnel
- ✅ Permettre rollback immédiat
- ✅ Être testées en isolation
- ✅ Être documentées

### Prochaine Étape Immédiate

**Créer le snapshot lai_v7 MAINTENANT** avant toute autre modification.

```bash
# Commande à exécuter:
mkdir -p backup/snapshot_lai_v7_20260130
# Puis suivre Phase 1.1 du plan d'action
```

---

**FIN DU RAPPORT**
