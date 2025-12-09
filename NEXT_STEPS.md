# Prochaines Étapes – Vectora Inbox

**Date** : 2025-01-15  
**Statut** : 🟡 **PRÊT POUR EXÉCUTION MANUELLE**

---

## 🎯 Objectif Immédiat

Déployer et tester la Lambda engine en DEV pour générer la première newsletter complète.

---

## ✅ Ce qui est prêt

- ✅ **Code** : Lambda engine implémentée (matching, scoring, newsletter)
- ✅ **Infrastructure** : Templates CloudFormation mis à jour
- ✅ **Scripts** : Tous les scripts de déploiement et tests créés
- ✅ **Documentation** : Plan détaillé, guides, templates de diagnostic

---

## 🚀 Actions à Exécuter (3 étapes)

### Étape 1 : Déploiement (5 minutes)

```powershell
# 1. Redéployer le rôle IAM Engine avec les nouvelles permissions
aws cloudformation deploy `
  --template-file infra/s0-iam.yaml `
  --stack-name vectora-inbox-s0-iam-dev `
  --parameter-overrides `
    Env=dev `
    ProjectName=vectora-inbox `
    ConfigBucketName=vectora-inbox-config-dev `
    DataBucketName=vectora-inbox-data-dev `
    NewslettersBucketName=vectora-inbox-newsletters-dev `
    PubmedApiKeyParamPath=/rag-lai/dev/pubmed/api-key `
  --capabilities CAPABILITY_IAM `
  --profile rag-lai-prod `
  --region eu-west-3

# 2. Packager et uploader le code engine
.\scripts\package-engine.ps1

# 3. Déployer la stack runtime
.\scripts\deploy-runtime-dev.ps1

# 4. Vérifier le déploiement
.\scripts\verify-engine-deployment.ps1
```

**Résultat attendu** : Lambda engine déployée avec les bonnes permissions et configuration.

---

### Étape 2 : Test End-to-End (2 minutes)

```powershell
# Exécuter le test complet
.\scripts\test-engine-lai-weekly.ps1
```

**Résultat attendu** :
- Items normalisés générés par ingest-normalize
- Newsletter générée par engine
- Fichier `newsletter-lai-weekly.md` téléchargé

---

### Étape 3 : Documentation (10 minutes)

1. **Compléter le diagnostic** : `docs/diagnostics/vectora_inbox_engine_first_run.md`
   - Remplir les sections avec les résultats du test
   - Évaluer la qualité de la newsletter
   - Documenter les problèmes rencontrés

2. **Mettre à jour le CHANGELOG** : `CHANGELOG.md`
   - Changer le statut de 🟡 AMBER à ✅ GREEN
   - Ajouter les statistiques du test

3. **Consulter les logs** :
   ```powershell
   aws logs tail /aws/lambda/vectora-inbox-engine-dev --since 10m --format detailed --profile rag-lai-prod --region eu-west-3
   ```

---

## 📚 Ressources

### Documents Essentiels

- **Guide d'exécution détaillé** : `docs/guides/guide_execution_deploiement_engine.md`
- **Plan de déploiement** : `docs/design/vectora_inbox_engine_deploy_and_test_plan.md`
- **Statut du projet** : `docs/STATUS.md`
- **Documentation des scripts** : `scripts/README.md`

### Commandes Utiles

```powershell
# Consulter les logs engine
aws logs tail /aws/lambda/vectora-inbox-engine-dev --since 10m --format detailed --profile rag-lai-prod --region eu-west-3

# Consulter les logs ingest-normalize
aws logs tail /aws/lambda/vectora-inbox-ingest-normalize-dev --since 10m --format detailed --profile rag-lai-prod --region eu-west-3

# Lister les newsletters générées
aws s3 ls s3://vectora-inbox-newsletters-dev/lai_weekly/ --recursive --profile rag-lai-prod --region eu-west-3

# Télécharger une newsletter
aws s3 cp s3://vectora-inbox-newsletters-dev/lai_weekly/2025/01/15/newsletter.md newsletter.md --profile rag-lai-prod --region eu-west-3
```

---

## 🎯 Critères de Succès

### Déploiement

- ✅ Lambda engine existe et est configurée
- ✅ Variables d'environnement présentes (CONFIG_BUCKET, DATA_BUCKET, NEWSLETTERS_BUCKET, BEDROCK_MODEL_ID)
- ✅ Concurrence limitée à 1 en DEV
- ✅ Permissions IAM correctes (lecture config + data, écriture newsletters, Bedrock)

### Tests

- ✅ ingest-normalize génère des items normalisés (statusCode: 200, items_normalized > 0)
- ✅ engine génère une newsletter (statusCode: 200, items_selected > 0)
- ✅ Newsletter Markdown téléchargeable depuis S3
- ✅ Pas d'erreurs critiques dans les logs

### Qualité

- ✅ Newsletter cohérente (titre, intro, TL;DR, sections, items)
- ✅ Pas d'hallucinations détectées
- ✅ Noms de sociétés/molécules préservés
- ✅ Ton et voice respectés

---

## 🔄 Après le Premier Run

### Si le test est réussi (✅ GREEN)

1. **Itérer sur les configurations** :
   - Ajuster les prompts Bedrock si nécessaire
   - Ajuster les poids de scoring si nécessaire
   - Enrichir les scopes canonical si nécessaire

2. **Préparer le déploiement STAGE** :
   - Dupliquer les stacks pour STAGE
   - Ajuster la concurrence Lambda (2-3 pour STAGE)
   - Tester avec plusieurs clients

3. **Mettre en place le monitoring** :
   - Créer un dashboard CloudWatch
   - Configurer des alertes SNS
   - Surveiller les quotas Bedrock

### Si le test rencontre des problèmes (⚠️ AMBER / ❌ RED)

1. **Diagnostiquer** :
   - Consulter les logs CloudWatch en détail
   - Identifier la cause racine (code, config, infra, Bedrock)
   - Documenter le problème dans le diagnostic

2. **Corriger** :
   - Appliquer les corrections nécessaires
   - Redéployer si nécessaire
   - Re-tester

3. **Documenter** :
   - Mettre à jour le diagnostic avec la solution
   - Mettre à jour le CHANGELOG

---

## 📞 Support

### En cas de problème

1. **Consulter les diagnostics** : `docs/diagnostics/`
2. **Consulter le guide de dépannage** : `docs/guides/guide_execution_deploiement_engine.md` (section Dépannage)
3. **Consulter les logs CloudWatch** : Commandes ci-dessus

### Ressources complémentaires

- **Architecture** : `docs/design/vectora_inbox_engine_lambda.md`
- **Contrats Lambda** : `contracts/lambdas/`
- **Code source** : `src/vectora_core/`

---

## 📊 Résumé Visuel

```
┌─────────────────────────────────────────────────────────────┐
│                    ÉTAT ACTUEL DU PROJET                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ✅ Lambda ingest-normalize    →  OPÉRATIONNELLE           │
│  🟡 Lambda engine              →  PRÊTE POUR DÉPLOIEMENT   │
│  ✅ Infrastructure             →  TEMPLATES MIS À JOUR     │
│  ✅ Scripts                    →  CRÉÉS ET DOCUMENTÉS      │
│  ✅ Documentation              →  COMPLÈTE                 │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                    PROCHAINES ACTIONS                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1️⃣  Déployer (5 min)         →  3 commandes PowerShell   │
│  2️⃣  Tester (2 min)           →  1 commande PowerShell    │
│  3️⃣  Documenter (10 min)      →  Compléter le diagnostic  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

**Auteur** : Amazon Q Developer  
**Date de création** : 2025-01-15  
**Version** : 1.0
