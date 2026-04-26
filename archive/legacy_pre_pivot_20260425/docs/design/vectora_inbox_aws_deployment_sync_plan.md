# Vectora Inbox - Plan de Synchronisation AWS DEV

**Date:** 2025-01-15  
**Objectif:** Synchroniser le repo local vectora-inbox avec l'environnement AWS DEV  
**Environnement cible:** DEV uniquement (eu-west-3)  
**Profil AWS:** rag-lai-prod (selon configuration existante)

## État Actuel - Synthèse Rapide

### Ce qui tourne déjà en DEV
- **Stacks CloudFormation:** vectora-inbox-s1-runtime-dev
- **Lambdas:** ingest-normalize, engine
- **Buckets S3:**
  - Config bucket: stockage canonical/, clients/
  - Data bucket: données normalisées par client/date
  - Newsletters bucket: newsletters générées
  - Lambda code bucket: packages des fonctions Lambda
- **Workflow opérationnel:** Ingestion → Normalisation → Engine → Newsletter

### Changements récents côté repo (2-3 derniers jours)
1. **ingestion_profiles & ingestion_profiles.yaml**
   - Nouveau système de filtrage pré-normalisation
   - Profils: corporate_pure_player_broad, corporate_hybrid_technology_focused, press_technology_focused

2. **Refactor matching LAI + domain_matching_rules**
   - Logique de matching complexe pour domaines technologiques
   - Nouvelles règles dans canonical/matching/domain_matching_rules.yaml

3. **Refactor runtime LAI (matcher/scorer, open-world normalisation)**
   - Normalisation open-world avec intersection canonique
   - Amélioration du scoring avec bonuses pure_player

4. **Refactor parser HTML corporate (parser générique + html_extractors)**
   - Parser HTML générique avec extracteurs spécialisés
   - Support amélioré pour sources corporate

5. **Scripts de packaging / déploiement Lambda**
   - Nouveaux scripts de build et déploiement
   - Gestion des dépendances améliorée

## Architecture Cible

### Buckets/Configs à aligner
- **Config bucket DEV:**
  - canonical/ (scopes, matching rules, scoring rules, ingestion profiles)
  - clients/ (configurations client mises à jour)
- **Code bucket DEV:**
  - Packages Lambda avec nouveaux modules
- **Data/Newsletter buckets:** Pas de changement structurel

### Lambdas à mettre à jour
- **ingest-normalize:** Nouveaux modules ingestion_profiles, html_parser refactor
- **engine:** Runtime LAI amélioré, matching/scoring refactorisé
- **Autres:** À déterminer selon l'inventaire

## Phases d'Exécution

### Phase 1 – Inventory & Gap Analysis
**Objectif:** Inventaire complet et analyse des écarts repo vs AWS DEV

**Actions:**
- Inventaire stacks CloudFormation DEV (vectora-inbox-*)
- Inventaire Lambdas (nom, runtime, handler, taille package)
- Inventaire buckets S3 et leur contenu
- Comparaison canonical/ local vs S3
- Comparaison clients/ local vs S3
- Analyse des modules code manquants côté AWS

**Fichiers concernés:**
- Tous les fichiers canonical/
- Tous les fichiers clients/
- Scripts d'infrastructure (infra/, scripts/)
- Modules Python (vectora_core/)

**Commandes AWS/CLI envisagées:**
```bash
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE
aws lambda list-functions --region eu-west-3
aws s3 ls s3://vectora-inbox-config-dev/ --recursive
aws s3 ls s3://vectora-inbox-lambda-code-dev/ --recursive
```

**Definition of Done:**
- Inventaire complet de l'état AWS DEV
- Diagnostic détaillé des écarts identifiés
- Recommandations de séquence de déploiement
- Évaluation des risques par composant

### Phase 2 – Mise à jour Canonical/Config en DEV
**Objectif:** Synchroniser les fichiers de configuration sans impact sur le runtime

**Actions:**
- Backup des configs actuelles S3
- Upload canonical/ mis à jour (scopes, matching rules, scoring rules)
- Upload ingestion_profiles.yaml
- Upload clients/ mis à jour
- Vérification de l'intégrité des uploads

**Fichiers concernés:**
- canonical/scopes/*.yaml
- canonical/matching/domain_matching_rules.yaml
- canonical/scoring/scoring_rules.yaml
- canonical/ingestion_profiles.yaml
- clients/*.yaml

**Commandes AWS/CLI envisagées:**
```bash
aws s3 sync canonical/ s3://vectora-inbox-config-dev/canonical/ --dryrun
aws s3 sync clients/ s3://vectora-inbox-config-dev/clients/ --dryrun
aws s3 cp canonical/ingestion_profiles.yaml s3://vectora-inbox-config-dev/canonical/
```

**Definition of Done:**
- Tous les fichiers canonical/ synchronisés
- Tous les fichiers clients/ synchronisés
- Backup des anciennes versions créé
- Vérification de l'intégrité des fichiers uploadés

### Phase 3 – Packaging & Mise à jour des Lambdas
**Objectif:** Déployer le code Lambda refactorisé

**Actions:**
- Build des packages Lambda avec nouveaux modules
- Upload vers le bucket de code Lambda
- Mise à jour des fonctions Lambda (ou stacks selon architecture)
- Vérification des handlers et configurations

**Fichiers concernés:**
- vectora_core/ (tous les modules)
- scripts/packaging/
- requirements.txt
- lambda handlers

**Commandes AWS/CLI envisagées:**
```bash
# Build packages
python scripts/build_lambda_packages.py

# Upload packages
aws s3 cp dist/ingest-normalize.zip s3://vectora-inbox-lambda-code-dev/
aws s3 cp dist/engine.zip s3://vectora-inbox-lambda-code-dev/

# Update functions
aws lambda update-function-code --function-name vectora-inbox-ingest-normalize-dev --s3-bucket vectora-inbox-lambda-code-dev --s3-key ingest-normalize.zip
aws lambda update-function-code --function-name vectora-inbox-engine-dev --s3-bucket vectora-inbox-lambda-code-dev --s3-key engine.zip
```

**Definition of Done:**
- Packages Lambda buildés avec succès
- Fonctions Lambda mises à jour
- Handlers et configurations vérifiés
- Tests de base (invoke test) réussis

### Phase 4 – Tests End-to-End en DEV
**Objectif:** Validation du workflow complet après déploiement

**Actions:**
- Test d'ingestion avec profils mis à jour
- Test de normalisation avec nouveau runtime
- Test d'engine avec matching/scoring refactorisé
- Test de génération newsletter
- Analyse des logs CloudWatch

**Fichiers concernés:**
- Logs CloudWatch des Lambdas
- Données de test dans buckets S3
- Newsletters générées

**Commandes AWS/CLI envisagées:**
```bash
# Trigger test ingestion
aws lambda invoke --function-name vectora-inbox-ingest-normalize-dev --payload '{"test": true}' response.json

# Check logs
aws logs filter-log-events --log-group-name /aws/lambda/vectora-inbox-ingest-normalize-dev --start-time $(date -d '1 hour ago' +%s)000

# Verify S3 outputs
aws s3 ls s3://vectora-inbox-data-dev/normalized/lai_weekly/$(date +%Y/%m/%d)/
aws s3 ls s3://vectora-inbox-newsletters-dev/lai_weekly/$(date +%Y/%m/%d)/
```

**Definition of Done:**
- Workflow end-to-end fonctionnel
- Pas d'erreurs critiques dans les logs
- Données normalisées générées correctement
- Newsletter générée avec nouveau format
- Performance acceptable (temps d'exécution)

### Phase 5 – Synthèse & Check de Santé Final
**Objectif:** Documentation de l'état final et validation complète

**Actions:**
- Synthèse des déploiements effectués
- Check de santé complet de l'environnement DEV
- Documentation des changements pour référence future
- Recommandations pour monitoring continu

**Fichiers concernés:**
- docs/diagnostics/ (nouveaux diagnostics)
- docs/design/ (mise à jour documentation)

**Definition of Done:**
- Résumé exécutif de l'état post-déploiement
- Tous les composants validés fonctionnels
- Documentation à jour
- Plan de monitoring défini

## Gestion des Risques

### Risques identifiés
1. **Incompatibilité des nouvelles configs** avec les Lambdas actuelles
2. **Régression du workflow** pendant la mise à jour des Lambdas
3. **Perte de données** lors des uploads S3
4. **Timeout des Lambdas** avec les nouveaux modules

### Stratégies de mitigation
1. **Déploiement séquentiel:** Config d'abord, puis code
2. **Backups systématiques** avant chaque modification
3. **Tests de validation** après chaque phase
4. **Rollback plan** documenté pour chaque composant

## Executive Summary

**Stratégie globale:** Déploiement séquentiel et contrôlé en 5 phases, du moins risqué (config) au plus critique (code Lambda).

**Approche de sécurité:** Backup systématique, tests de validation, possibilité de rollback à chaque étape.

**Durée estimée:** 2-3 heures pour l'ensemble des phases, avec validation approfondie.

**Points d'attention critiques:**
- Compatibilité des nouveaux ingestion_profiles avec le workflow existant
- Impact du refactor runtime LAI sur les performances
- Validation du nouveau système de matching complexe

**Critères de succès:**
- Workflow end-to-end fonctionnel avec toutes les améliorations
- Pas de régression de performance
- Logs propres sans erreurs critiques
- Newsletter générée avec le nouveau format et contenu amélioré

**Plan de rollback:** Chaque phase dispose de sa procédure de rollback documentée, permettant un retour à l'état antérieur en cas de problème.