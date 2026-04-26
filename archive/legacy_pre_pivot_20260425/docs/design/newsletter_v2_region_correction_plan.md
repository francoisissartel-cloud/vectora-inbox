# Plan de Correction - Déploiement Newsletter V2 Conforme

**Date :** 21 décembre 2025  
**Objectif :** Corriger le déploiement newsletter-v2 selon les règles Vectora-Inbox  
**Problème :** Lambda déployée dans us-east-1 au lieu de eu-west-3 + nommage incorrect  
**Solution :** Redéploiement conforme dans eu-west-3 avec nom `-dev`  

---

## 🚨 Problèmes Identifiés

### Violations des Règles Vectora-Inbox

**1. Région Incorrecte :**
- ❌ **Actuel :** Lambda dans `us-east-1`
- ✅ **Requis :** Lambda dans `eu-west-3` (Paris)
- **Règle :** Toutes les ressources principales (S3, Lambda, CloudWatch) en eu-west-3

**2. Nommage Incorrect :**
- ❌ **Actuel :** `vectora-inbox-newsletter-v2`
- ✅ **Requis :** `vectora-inbox-newsletter-v2-dev`
- **Règle :** Suffixe `-dev` obligatoire pour environnement dev

**3. Incohérence Architecture :**
- ✅ **Autres Lambdas :** `eu-west-3` avec suffixe `-dev`
- ❌ **Newsletter :** `us-east-1` sans suffixe `-dev`

---

## 🎯 Objectif de Correction

### État Cible
**3 Lambdas V2 cohérentes dans eu-west-3 :**
```
eu-west-3 (Paris):
├── vectora-inbox-ingest-v2-dev          ✅ (existante)
├── vectora-inbox-normalize-score-v2-dev ✅ (existante)  
└── vectora-inbox-newsletter-v2-dev      ❌ (à créer)

us-east-1 (Virginie):
└── Bedrock uniquement                   ✅ (correct)
```

### Architecture Conforme
- **Lambdas :** eu-west-3 (région principale)
- **S3 Buckets :** eu-west-3 (région principale)
- **Bedrock :** us-east-1 (appels cross-region depuis eu-west-3)
- **Nommage :** Suffixe `-dev` sur toutes les ressources

---

## 📋 Plan de Correction

### Phase 1 : Nettoyage us-east-1 (5 min)

**Objectif :** Supprimer les ressources incorrectes

**Actions :**
1. Supprimer Lambda `vectora-inbox-newsletter-v2` (us-east-1)
2. Supprimer Layer `newsletter-v2-deps` (us-east-1)
3. Vérifier suppression complète

**Commandes :**
```bash
aws lambda delete-function \
  --function-name vectora-inbox-newsletter-v2 \
  --region us-east-1

aws lambda delete-layer-version \
  --layer-name newsletter-v2-deps \
  --version-number 2 \
  --region us-east-1
```

### Phase 2 : Création Layer eu-west-3 (10 min)

**Objectif :** Créer le layer dependencies dans la bonne région

**Actions :**
1. Créer layer `vectora-inbox-common-deps-dev` (nom conforme)
2. Déployer dans eu-west-3
3. Valider disponibilité

**Nom conforme :** `vectora-inbox-common-deps-dev`

### Phase 3 : Déploiement Lambda eu-west-3 (10 min)

**Objectif :** Déployer la Lambda dans la région correcte

**Actions :**
1. Créer Lambda `vectora-inbox-newsletter-v2-dev` (nom conforme)
2. Déployer dans eu-west-3
3. Attacher le layer eu-west-3
4. Configurer variables d'environnement

**Configuration :**
- **Nom :** `vectora-inbox-newsletter-v2-dev`
- **Région :** eu-west-3
- **Bedrock :** Cross-region vers us-east-1 (autorisé)

### Phase 4 : Validation Conformité (5 min)

**Objectif :** Valider la conformité totale

**Vérifications :**
1. 3 Lambdas V2 dans eu-west-3 avec suffixe `-dev`
2. Layer dans eu-west-3
3. Appels Bedrock cross-region fonctionnels
4. Test E2E réussi

---

## 🔧 Spécifications Techniques

### Lambda Configuration Conforme

```yaml
FunctionName: vectora-inbox-newsletter-v2-dev
Region: eu-west-3
Runtime: python3.11
Handler: handler.lambda_handler
Timeout: 900
MemorySize: 1024
Role: vectora-inbox-s0-iam-dev-EngineRole-x4yGG8dAutT9

Environment:
  CONFIG_BUCKET: vectora-inbox-config-dev
  DATA_BUCKET: vectora-inbox-data-dev
  NEWSLETTERS_BUCKET: vectora-inbox-newsletters-dev
  BEDROCK_MODEL_ID: anthropic.claude-3-sonnet-20240229-v1:0
  BEDROCK_REGION: us-east-1  # Cross-region autorisé pour Bedrock
```

### Layer Configuration Conforme

```yaml
LayerName: vectora-inbox-common-deps-dev
Region: eu-west-3
Description: Common dependencies for vectora-inbox Lambdas (PyYAML, requests)
CompatibleRuntimes: [python3.11]
```

---

## 🎯 Avantages de la Correction

### Conformité Architecture
- ✅ **3 Lambdas cohérentes** dans eu-west-3
- ✅ **Nommage uniforme** avec suffixe `-dev`
- ✅ **Région principale** respectée
- ✅ **Cross-region Bedrock** maintenu (us-east-1)

### Performance
- ✅ **Latence réduite** : Lambda et S3 dans même région
- ✅ **Coûts optimisés** : Pas de transfert inter-région S3
- ✅ **Monitoring unifié** : Toutes les Lambdas dans même région

### Maintenance
- ✅ **Cohérence opérationnelle** : Toutes les ressources au même endroit
- ✅ **Debugging facilité** : Logs centralisés eu-west-3
- ✅ **Évolutivité** : Architecture homogène

---

## ⚠️ Risques et Mitigations

### Risque : Cross-Region Bedrock
- **Problème :** Appels Bedrock depuis eu-west-3 vers us-east-1
- **Mitigation :** Configuration validée E2E sur autres Lambdas
- **Validation :** Test obligatoire après déploiement

### Risque : Interruption Service
- **Problème :** Suppression Lambda us-east-1 avant création eu-west-3
- **Mitigation :** Déploiement rapide, pas de dépendances externes
- **Impact :** Minimal (environnement dev)

---

## 📊 Critères de Succès

### Validation Technique
- ✅ Lambda `vectora-inbox-newsletter-v2-dev` dans eu-west-3
- ✅ Layer `vectora-inbox-common-deps-dev` dans eu-west-3
- ✅ Variables d'environnement configurées
- ✅ Appels Bedrock cross-region fonctionnels

### Validation Fonctionnelle
- ✅ Test E2E réussi avec payload lai_weekly_v4
- ✅ Newsletter générée avec données réelles
- ✅ Fichiers S3 créés dans newsletters-dev
- ✅ Bedrock TL;DR et introduction générés

### Validation Conformité
- ✅ 3 Lambdas V2 dans eu-west-3 avec nommage `-dev`
- ✅ Respect total des règles vectora-inbox-development-rules.md
- ✅ Architecture cohérente et maintenable

---

## 🚀 Timeline d'Exécution

**Total estimé :** 30 minutes

1. **Phase 1** (5 min) : Nettoyage us-east-1
2. **Phase 2** (10 min) : Layer eu-west-3
3. **Phase 3** (10 min) : Lambda eu-west-3
4. **Phase 4** (5 min) : Validation conformité

**Résultat :** Architecture 3 Lambdas V2 100% conforme dans eu-west-3

---

## ✅ Conclusion

Cette correction aligne parfaitement l'infrastructure avec les règles Vectora-Inbox :
- **Région principale** : eu-west-3 pour toutes les ressources
- **Nommage cohérent** : Suffixe `-dev` sur toutes les Lambdas
- **Architecture homogène** : 3 Lambdas V2 dans même région
- **Cross-region Bedrock** : Maintenu et validé

Le plan garantit une **architecture cohérente et conforme** aux standards établis.

---

*Plan de Correction - Déploiement Newsletter V2 Conforme*  
*Prêt pour exécution immédiate*