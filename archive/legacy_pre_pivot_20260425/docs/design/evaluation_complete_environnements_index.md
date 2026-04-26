# Évaluation Complète - Gestion Environnements Vectora Inbox

**Date**: 2026-01-30  
**Expert**: Cloud Architect AWS  
**Demande**: Évaluation diagnostique et stratégie dev/prod/stage

---

## 📚 LIVRABLES CRÉÉS

### 1. Rapport Diagnostique Complet
**Fichier**: `docs/design/strategie_gestion_environnements_dev_prod_stage.md`

**Contenu**:
- ✅ Diagnostic complet infrastructure AWS actuelle
- ✅ Évaluation convention nommage (suffixe `-dev`)
- ✅ Identification ressources (Lambdas, buckets, layers, stacks)
- ✅ Points forts et lacunes architecture
- ✅ Risques identifiés
- ✅ Stratégie recommandée (progressive et sécurisée)
- ✅ Plan d'action en 4 phases
- ✅ Recommandations finales

**Taille**: ~15 pages

### 2. Modifications Règles de Développement
**Fichier**: `docs/design/modifications_regles_developpement_environnements.md`

**Contenu**:
- ✅ Nouvelles sections à ajouter (Gestion Environnements, Snapshots)
- ✅ Sections à modifier (Configuration AWS)
- ✅ Checklist Q Developer pour environnements
- ✅ Convention nommage multi-environnements
- ✅ Workflow promotion dev → stage → prod
- ✅ Variables d'environnement Lambda

**Taille**: ~12 pages

### 3. Script Snapshot Automatisé
**Fichier**: `scripts/maintenance/create_snapshot.py`

**Contenu**:
- ✅ Script Python complet pour création snapshots
- ✅ Sauvegarde Lambdas, layers, configs, canonical, données
- ✅ Métadonnées JSON automatiques
- ✅ README snapshot généré
- ✅ Usage: `python create_snapshot.py --env dev --name "lai_v7_stable"`

**Taille**: ~300 lignes

### 4. Plan d'Action Immédiat
**Fichier**: `docs/design/plan_action_immediat_snapshot_lai_v7.md`

**Contenu**:
- ✅ Commandes PowerShell prêtes à exécuter
- ✅ Sauvegarde complète lai_weekly_v7 actuel
- ✅ 10 étapes détaillées avec commandes AWS CLI
- ✅ Checklist validation post-snapshot
- ✅ Test restauration partielle
- ✅ Durée estimée: 30 minutes

**Taille**: ~10 pages

---

## 🎯 SYNTHÈSE EXÉCUTIVE

### État Actuel (Diagnostic)

**✅ POINTS FORTS:**
- Convention `-dev` cohérente sur toutes les ressources
- Architecture 3 Lambdas V2 claire et fonctionnelle
- Infrastructure as Code (CloudFormation)
- Versioning S3 activé (rollback possible)
- POC lai_weekly_v7 fonctionnel

**❌ LACUNES:**
- Pas d'environnement stage/prod (tout en dev)
- Pas de stratégie promotion code
- Versioning client non structuré (v4, v5, v6, v7)
- Pas de snapshots automatisés
- Confusion version client vs environnement

**🔴 RISQUES:**
- Pas de sauvegarde moteur fonctionnel actuel
- Modifications directes peuvent casser POC v7
- Pas de rollback rapide en cas de problème

### Stratégie Recommandée

**PRINCIPE: Progressive et Non-Disruptive**

```
Phase 1 (IMMÉDIAT)     : Snapshot lai_v7 stable
Phase 2 (Court terme)  : Refactoring config client
Phase 3 (Moyen terme)  : Création environnement stage
Phase 4 (Long terme)   : Création environnement prod
```

**CONVENTION NOMMAGE:**
```
Ressources AWS: {nom}-{env}
  - vectora-inbox-ingest-v2-dev
  - vectora-inbox-ingest-v2-stage
  - vectora-inbox-ingest-v2-prod

Config client: client_id stable + version sémantique
  - client_id: "lai_weekly" (stable)
  - version: "7.0.0" (sémantique)
  - Déploiement: s3://vectora-inbox-config-{env}/clients/lai_weekly.yaml
```

**WORKFLOW PROMOTION:**
```
dev → stage → prod
 ↓      ↓       ↓
Tests  Tests  Monitoring
```

---

## 📊 INFRASTRUCTURE ACTUELLE

### Ressources AWS Identifiées

**Lambdas (3 fonctions V2):**
```
vectora-inbox-ingest-v2-dev          (Python 3.12, modifié 2026-01-29)
vectora-inbox-normalize-score-v2-dev (Python 3.11, modifié 2026-01-30)
vectora-inbox-newsletter-v2-dev      (Python 3.11, modifié 2026-01-30)
```

**Buckets S3 (4 buckets):**
```
vectora-inbox-config-dev       (configurations, canonical)
vectora-inbox-data-dev         (ingested, curated, normalized)
vectora-inbox-newsletters-dev  (newsletters générées)
vectora-inbox-lambda-code-dev  (packages Lambda)
```

**Lambda Layers (6 layers):**
```
vectora-inbox-vectora-core-dev (v42)
vectora-inbox-common-deps-dev (v4)
vectora-inbox-vectora-core-approche-b-dev (v10)
vectora-inbox-dependencies (legacy)
vectora-inbox-yaml-fix-dev
vectora-inbox-yaml-minimal-dev
```

**Stacks CloudFormation (4 stacks):**
```
vectora-inbox-s0-core-dev       (buckets S3)
vectora-inbox-s0-iam-dev        (rôles IAM)
vectora-inbox-s1-runtime-dev    (Lambdas engine/ingest-normalize)
vectora-inbox-s1-ingest-v2-dev  (Lambda ingest-v2)
```

**Configurations Client:**
```
lai_weekly_v4.yaml (2025-12-22)
lai_weekly_v5.yaml (2026-01-27)
lai_weekly_v6.yaml (2026-01-30)
lai_weekly_v7.yaml (2026-01-30) ← POC actuel
```

### Structure Données S3

**Bucket data-dev:**
```
curated/lai_weekly_v7/2026/01/29/items.json  (62KB, dernière exécution)
ingested/lai_weekly_v7/...
normalized/... (legacy?)
raw/... (debug)
```

---

## 🚀 PLAN D'ACTION RECOMMANDÉ

### Phase 1: IMMÉDIAT (Aujourd'hui)

**Objectif**: Sauvegarder état actuel lai_weekly_v7

**Actions**:
1. ✅ Exécuter `plan_action_immediat_snapshot_lai_v7.md`
2. ✅ Créer snapshot complet (30 min)
3. ✅ Valider snapshot restaurable
4. ✅ Documenter dans `docs/snapshots/`

**Résultat**: Point de restauration sécurisé

### Phase 2: Court Terme (1-2 Semaines)

**Objectif**: Refactoring configuration client

**Actions**:
1. Créer `lai_weekly.yaml` (sans v7)
2. Ajouter `version: "7.0.0"` dans metadata
3. Tester avec moteur actuel
4. Mettre à jour règles développement

**Résultat**: Distinction version vs environnement

### Phase 3: Moyen Terme (2-4 Semaines)

**Objectif**: Créer environnement stage

**Actions**:
1. Déployer stacks CloudFormation stage
2. Créer layers stage
3. Copier code validé dev → stage
4. Tests E2E sur stage

**Résultat**: Environnement validation pré-prod

### Phase 4: Long Terme (1-3 Mois)

**Objectif**: Créer environnement prod

**Actions**:
1. Valider stabilité stage (2 semaines min)
2. Déployer infrastructure prod
3. Migrer premier client réel
4. Monitoring prod opérationnel

**Résultat**: Production clients réels

---

## 📋 CHECKLIST VALIDATION

### Avant de Commencer

- [ ] Lire rapport complet `strategie_gestion_environnements_dev_prod_stage.md`
- [ ] Comprendre risques actuels
- [ ] Valider stratégie avec équipe
- [ ] Préparer 30 min pour snapshot

### Phase 1 (Snapshot)

- [ ] Exécuter commandes PowerShell plan immédiat
- [ ] Vérifier dossier `backup/snapshots/lai_v7_stable_*/` créé
- [ ] Valider contenu snapshot (lambdas, layers, configs, canonical, data)
- [ ] Tester restauration partielle (config client)
- [ ] Documenter snapshot dans `docs/snapshots/`

### Phase 2 (Refactoring Config)

- [ ] Créer `lai_weekly.yaml` (sans v7)
- [ ] Tester avec moteur dev
- [ ] Pas de régression fonctionnelle
- [ ] Mettre à jour règles développement

### Phase 3 (Stage)

- [ ] Infrastructure stage déployée
- [ ] Code promu dev → stage
- [ ] Tests E2E passés sur stage
- [ ] Workflow promotion validé

### Phase 4 (Prod)

- [ ] Stage stable 2 semaines minimum
- [ ] Infrastructure prod déployée
- [ ] Premier client migré
- [ ] Monitoring prod opérationnel

---

## 🔧 MODIFICATIONS RÈGLES DÉVELOPPEMENT

### Sections à Ajouter

**1. Gestion des Environnements**
- Définition dev/stage/prod
- Convention nommage `-{env}`
- Workflow promotion
- Variables d'environnement Lambda

**2. Snapshots et Rollback**
- Quand créer snapshot
- Commandes création/restauration
- Politique rétention
- Snapshots automatiques

**3. Checklist Q Developer**
- Vérifications environnement
- Questions à poser utilisateur
- Réponses adaptées par env

### Sections à Modifier

**Configuration AWS** → **Configuration AWS par Environnement**
- Détailler ressources par env
- Commandes déploiement par env

**Règles Configuration Client**
- Distinction `client_id` vs `version`
- Déploiement multi-env

---

## 💡 RECOMMANDATIONS EXPERT

### 1. Priorité Absolue: Snapshot

**EXÉCUTER MAINTENANT** le plan d'action immédiat avant toute autre modification.

Sans snapshot:
- ❌ Risque de perdre moteur fonctionnel
- ❌ Impossible de revenir en arrière
- ❌ Stress lors de modifications

Avec snapshot:
- ✅ Sécurité totale
- ✅ Rollback en 5 minutes
- ✅ Confiance pour expérimenter

### 2. Approche Progressive

**NE PAS** créer stage et prod immédiatement.

**Ordre recommandé:**
1. Snapshot (aujourd'hui)
2. Refactoring config (1-2 semaines)
3. Stage (2-4 semaines)
4. Prod (1-3 mois)

**Rationale:**
- Moteur pas encore optimal (bruit, prompts)
- Besoin d'itérations en dev
- Stage prématuré = gaspillage ressources
- Prod prématuré = risque clients

### 3. Convention Nommage

**Adopter immédiatement:**
- Suffixe `-{env}` pour toutes nouvelles ressources
- `client_id` stable sans version
- `version` sémantique séparée

**Migrer progressivement:**
- Configurations client existantes (v4, v5, v6, v7)
- Layers avec doublons (vectora-core vs vectora-core-approche-b)

### 4. Documentation

**Mettre à jour:**
- `.q-context/vectora-inbox-development-rules.md`
- Ajouter sections environnements
- Intégrer snapshots dans workflow

**Créer:**
- `docs/snapshots/` (historique snapshots)
- `docs/runbooks/` (procédures promotion)
- `docs/architecture/multi-env.md`

### 5. Scripts Automatisation

**Créer:**
- `scripts/maintenance/create_snapshot.py` ✅ (déjà créé)
- `scripts/maintenance/rollback_snapshot.py`
- `scripts/deploy/promote_dev_to_stage.sh`
- `scripts/deploy/promote_stage_to_prod.sh`

**Intégrer:**
- Snapshot automatique avant déploiement
- Validation pré-promotion
- Rollback automatique si échec

---

## 🎯 PROCHAINE ÉTAPE IMMÉDIATE

### EXÉCUTER MAINTENANT

```powershell
# 1. Ouvrir PowerShell en tant qu'administrateur
# 2. Se placer dans le projet
cd "C:\Users\franc\OneDrive\Bureau\vectora-inbox"

# 3. Ouvrir le plan d'action immédiat
code docs\design\plan_action_immediat_snapshot_lai_v7.md

# 4. Exécuter les commandes étape par étape
# 5. Vérifier le snapshot créé
# 6. Documenter dans docs/snapshots/

# Durée: 30 minutes
# Résultat: Sécurité totale pour la suite
```

### Après le Snapshot

1. **Lire rapport complet** `strategie_gestion_environnements_dev_prod_stage.md`
2. **Planifier Phase 2** (refactoring config client)
3. **Mettre à jour règles** développement
4. **Continuer optimisations** moteur en toute sécurité

---

## 📞 SUPPORT

### Questions Fréquentes

**Q: Dois-je créer stage/prod maintenant?**
R: Non, commencer par snapshot puis refactoring config. Stage/prod quand moteur stable.

**Q: Puis-je continuer à travailler sur lai_weekly_v7?**
R: Oui, après snapshot vous pouvez modifier en toute sécurité.

**Q: Comment restaurer si problème?**
R: Voir `backup/snapshots/lai_v7_stable_*/README.md` pour commandes restauration.

**Q: Faut-il modifier les règles de développement maintenant?**
R: Après snapshot et validation. Voir `modifications_regles_developpement_environnements.md`.

**Q: Combien coûte un environnement stage/prod?**
R: ~même coût que dev (Lambdas, S3, Bedrock). Optimiser après stabilisation.

---

## ✅ CONCLUSION

### Votre Infrastructure Est Solide

- ✅ Convention nommage cohérente
- ✅ Architecture 3 Lambdas V2 claire
- ✅ Infrastructure as Code
- ✅ POC lai_weekly_v7 fonctionnel

### Il Manque Juste

- ⏳ Snapshot état actuel (30 min)
- ⏳ Distinction version vs environnement
- ⏳ Environnements stage/prod (plus tard)
- ⏳ Workflow promotion automatisé

### Stratégie Recommandée

**Simple, Progressive, Sécurisée**

1. Snapshot aujourd'hui (30 min)
2. Refactoring config (1-2 semaines)
3. Stage quand stable (2-4 semaines)
4. Prod quand validé (1-3 mois)

### Prochaine Action

**CRÉER SNAPSHOT LAI_V7 MAINTENANT**

Voir: `docs/design/plan_action_immediat_snapshot_lai_v7.md`

---

**FIN DE L'ÉVALUATION**

*Tous les documents sont dans `docs/design/`*  
*Script snapshot dans `scripts/maintenance/`*  
*Prêt pour exécution immédiate*
