# Plan Correctif : Lambda Layers Vectora Inbox V2

**Date :** 17 décembre 2025  
**Objectif :** Corriger le problème PyYAML/requests dans normalize_score_v2  
**Conformité :** Strict respect src_lambda_hygiene_v4.md  
**Impact :** Zéro casse de l'existant  

---

## 🎯 Contexte et Objectif

### Problème Identifié
- Lambda `vectora-inbox-normalize-score-v2-dev` non fonctionnelle
- Erreur : "No module named 'yaml'" puis "No module named 'requests'"
- Root cause : Layer common-deps incomplet ou corrompu

### Solution Validée
Recréer le layer `vectora-inbox-common-deps-dev` avec toutes les dépendances Python nécessaires, en respectant les règles d'hygiène V4.

---

## 📋 Plan d'Exécution par Phases

### Phase 1 : Préparation et Diagnostic (15 min)

#### 1.1 Sauvegarde État Actuel
- Documenter configuration Lambda actuelle
- Sauvegarder ARNs des layers existants
- Créer point de restauration

#### 1.2 Analyse Dépendances Requises
- Identifier toutes les dépendances de vectora_core
- Valider versions compatibles Python 3.11
- Lister dépendances critiques : PyYAML, requests, feedparser, boto3

#### 1.3 Validation Environnement
- Vérifier accès AWS rag-lai-prod
- Confirmer permissions Lambda Layers
- Préparer environnement de build

### Phase 2 : Création Layer Common-Deps Corrigé (30 min)

#### 2.1 Environnement de Build Propre
```bash
# Création environnement isolé
mkdir -p /tmp/vectora_layer_fix
cd /tmp/vectora_layer_fix
mkdir python
```

#### 2.2 Installation Dépendances
```bash
# Installation avec contraintes hygiene_v4
pip install --target python/ --no-binary PyYAML \
  PyYAML==6.0.1 \
  requests==2.31.0 \
  feedparser==6.0.10 \
  beautifulsoup4==4.12.0
```

#### 2.3 Validation Layer
- Vérifier structure python/
- Tester imports critiques
- Valider taille < 50MB

#### 2.4 Package et Upload
```bash
# Création ZIP optimisé
zip -r vectora-inbox-common-deps-v2.zip python/

# Upload vers AWS
aws lambda publish-layer-version \
  --layer-name vectora-inbox-common-deps-dev \
  --zip-file fileb://vectora-inbox-common-deps-v2.zip \
  --compatible-runtimes python3.11 \
  --description "Common deps V2 - PyYAML + requests fix" \
  --profile rag-lai-prod --region eu-west-3
```

### Phase 3 : Mise à Jour Lambda Configuration (15 min)

#### 3.1 Récupération Nouvelle Version Layer
```bash
# Obtenir ARN du nouveau layer
NEW_LAYER_ARN=$(aws lambda list-layer-versions \
  --layer-name vectora-inbox-common-deps-dev \
  --query 'LayerVersions[0].LayerVersionArn' \
  --output text --profile rag-lai-prod --region eu-west-3)
```

#### 3.2 Mise à Jour Configuration Lambda
```bash
# Mise à jour avec nouveau layer
aws lambda update-function-configuration \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --layers arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev:1 \
           $NEW_LAYER_ARN \
  --profile rag-lai-prod --region eu-west-3
```

#### 3.3 Validation Configuration
- Vérifier layers attachés
- Confirmer versions correctes
- Attendre propagation (30s)

### Phase 4 : Tests de Validation (20 min)

#### 4.1 Test Import Minimal
```bash
# Test payload minimal
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --payload '{"client_id": "lai_weekly_v3", "test_mode": true}' \
  test_import_result.json \
  --profile rag-lai-prod --region eu-west-3
```

#### 4.2 Validation Réponse
- Vérifier absence d'erreur ImportModuleError
- Confirmer chargement vectora_core
- Analyser logs CloudWatch

#### 4.3 Test End-to-End Complet
```bash
# Test complet sur données réelles
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --payload '{"client_id": "lai_weekly_v3"}' \
  test_e2e_result.json \
  --profile rag-lai-prod --region eu-west-3
```

### Phase 5 : Validation Finale et Métriques (20 min)

#### 5.1 Analyse Outputs S3
```bash
# Vérifier création fichiers curated
aws s3 ls s3://vectora-inbox-data-dev/curated/lai_weekly_v3/ \
  --recursive --profile rag-lai-prod --region eu-west-3
```

#### 5.2 Validation Métriques
- Items normalisés : attendu 15/15
- Items matchés : attendu 8-12/15
- Temps d'exécution : attendu 3-8 min
- Coût Bedrock : attendu ~$0.036

#### 5.3 Rapport de Validation
- Documenter métriques obtenues
- Comparer aux projections
- Identifier optimisations possibles

---

## 🔒 Contraintes de Sécurité

### Respect src_lambda_hygiene_v4.md
- ✅ Aucune modification de /src
- ✅ Utilisation exclusive Lambda Layers
- ✅ Pas de dépendances tierces dans code
- ✅ Préservation architecture 3 Lambdas V2

### Zéro Impact Existant
- ✅ Pas de modification code Lambda
- ✅ Pas de changement configuration client
- ✅ Pas de modification canonical
- ✅ Rollback possible instantané

### Validation Continue
- Test après chaque phase
- Logs CloudWatch surveillés
- Métriques de performance trackées
- Point d'arrêt si régression

---

## 📊 Critères de Succès

### Phase 2 - Layer Creation
- ✅ Layer créé < 50MB
- ✅ PyYAML importable
- ✅ Requests importable
- ✅ Upload AWS réussi

### Phase 4 - Tests
- ✅ Pas d'ImportModuleError
- ✅ Lambda s'exécute sans erreur
- ✅ Temps d'exécution < 15 min
- ✅ Logs propres

### Phase 5 - Validation E2E
- ✅ Items normalisés > 0
- ✅ Items matchés > 0
- ✅ Fichiers S3 curated créés
- ✅ Métriques cohérentes

---

## 🚨 Plan de Rollback

### Si Échec Phase 2-3
```bash
# Restaurer layer précédent
aws lambda update-function-configuration \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --layers arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev:1 \
           arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-common-deps-dev:1 \
  --profile rag-lai-prod --region eu-west-3
```

### Si Échec Phase 4-5
- Analyser logs d'erreur
- Identifier dépendance manquante
- Itérer sur Phase 2 avec dépendance supplémentaire
- Pas de rollback nécessaire (pas de casse)

---

## ⏱️ Timeline d'Exécution

| Phase | Durée | Dépendances | Validation |
|-------|-------|-------------|------------|
| Phase 1 | 15 min | - | État documenté |
| Phase 2 | 30 min | Phase 1 | Layer uploadé |
| Phase 3 | 15 min | Phase 2 | Config mise à jour |
| Phase 4 | 20 min | Phase 3 | Tests passent |
| Phase 5 | 20 min | Phase 4 | E2E validé |
| **Total** | **100 min** | - | **Pipeline fonctionnel** |

---

## 📋 Checklist d'Exécution

### Pré-requis
- [ ] Accès AWS rag-lai-prod configuré
- [ ] Permissions Lambda Layers validées
- [ ] Environnement de build disponible
- [ ] Scripts de test préparés

### Phase 1
- [ ] Configuration Lambda documentée
- [ ] ARNs layers sauvegardés
- [ ] Dépendances listées
- [ ] Environnement validé

### Phase 2
- [ ] Environnement build créé
- [ ] Dépendances installées
- [ ] Layer validé localement
- [ ] Upload AWS réussi

### Phase 3
- [ ] Nouveau layer ARN récupéré
- [ ] Configuration Lambda mise à jour
- [ ] Layers attachés vérifiés
- [ ] Propagation attendue

### Phase 4
- [ ] Test import réussi
- [ ] Logs CloudWatch propres
- [ ] Test E2E lancé
- [ ] Réponse Lambda validée

### Phase 5
- [ ] Outputs S3 vérifiés
- [ ] Métriques collectées
- [ ] Performance validée
- [ ] Rapport complété

---

**Plan prêt pour exécution immédiate**  
**Durée estimée : 100 minutes**  
**Risque : Minimal (rollback possible)**  
**Impact : Zéro sur existant**