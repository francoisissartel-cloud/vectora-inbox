# Vectora Inbox - Plan de Migration Bedrock vers us-east-1

**Date** : 2025-12-12  
**Objectif** : Migrer l'usage d'Amazon Bedrock de eu-west-3 vers us-east-1 pour la normalisation et la génération de newsletter  
**Région infra** : eu-west-3 (Lambdas restent en place)  
**Région Bedrock cible** : us-east-1  

---

## Vue d'Ensemble

Ce plan structure la migration de l'usage Bedrock du projet Vectora Inbox de la région eu-west-3 vers us-east-1, sans impacter l'architecture existante (S3, Lambda, DynamoDB restent en eu-west-3).

### Motivation
- Normalisation sur us-east-1 pour Bedrock (région de référence AWS)
- Accès aux modèles les plus récents (Sonnet 3.5/4.5)
- Amélioration potentielle des performances et coûts

---

## Phase 0 – Discovery & Impact Analysis

### 0.1 Inventaire des Dépendances Bedrock

**Fichiers identifiés utilisant Bedrock :**
- `src/vectora_core/normalization/bedrock_client.py` : Client normalisation items
- `src/vectora_core/newsletter/bedrock_client.py` : Client génération newsletter
- Configuration actuelle : `region_name='eu-west-3'` hardcodée

**Lambdas impactées :**
- `vectora-inbox-ingest-normalize-dev` : Utilise normalisation Bedrock
- `vectora-inbox-engine-dev` : Utilise génération newsletter Bedrock

### 0.2 Modèle Actuel et Équivalent us-east-1

**Modèle actuel (eu-west-3) :**
- Identifiant : `anthropic.claude-3-5-sonnet-20240620-v1:0` (supposé)
- Usage : Normalisation + Newsletter

**Modèle cible (us-east-1) :**
- **Choix recommandé** : `anthropic.claude-3-5-sonnet-20241022-v2:0`
- **Justification** : Version la plus récente de Sonnet 3.5, disponible en us-east-1
- **Alternative** : `anthropic.claude-3-5-sonnet-20240620-v1:0` si disponible

### 0.3 Vérification Disponibilité Modèles us-east-1

**À valider en Phase 1 :**
- Lister les modèles Claude disponibles en us-east-1
- Confirmer la disponibilité du modèle cible
- Vérifier les quotas et limites

---

## Phase 1 – Refactor Repo (Région + Modèle)

### 1.1 Modifications Code Source

**Fichiers à modifier :**

1. **`src/vectora_core/normalization/bedrock_client.py`**
   - Ligne 25 : `region_name='eu-west-3'` → `region_name='us-east-1'`
   - Paramétrer via variable d'environnement `BEDROCK_REGION`

2. **`src/vectora_core/newsletter/bedrock_client.py`**
   - Ligne 25 : `region_name='eu-west-3'` → `region_name='us-east-1'`
   - Paramétrer via variable d'environnement `BEDROCK_REGION`

### 1.2 Configuration Modèle

**Stratégie :**
- Introduire variable d'environnement `BEDROCK_MODEL_ID`
- Valeur par défaut : `anthropic.claude-3-5-sonnet-20241022-v2:0`
- Permettre override pour tests/rollback

### 1.3 Refactoring Clients Bedrock

**Modifications proposées :**

```python
def get_bedrock_client():
    """
    Retourne un client boto3 Bedrock Runtime.
    """
    region = os.environ.get('BEDROCK_REGION', 'us-east-1')
    return boto3.client('bedrock-runtime', region_name=region)
```

**Variables d'environnement à ajouter :**
- `BEDROCK_REGION=us-east-1`
- `BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0`

---

## Phase 2 – Tests Locaux (Sans AWS Lambda)

### 2.1 Tests Normalisation

**Objectif :** Valider la normalisation avec le nouveau modèle/région

**Jeu de test :**
- 2-3 items représentatifs (Nanexa/Moderna, UZEDY®, MedinCell)
- Comparaison avant/après (eu-west-3 vs us-east-1)

**Métriques à mesurer :**
- Latence des appels Bedrock
- Qualité des résumés générés
- Détection des entités (companies, molecules, technologies)
- Taux d'erreur/throttling

### 2.2 Tests Newsletter

**Objectif :** Valider la génération newsletter avec le nouveau modèle

**Test :** Génération newsletter avec 5-10 items normalisés

**Métriques :**
- Qualité éditoriale
- Respect du format JSON
- Temps de génération

### 2.3 Documentation Résultats

**Fichier :** `docs/diagnostics/vectora_inbox_bedrock_region_migration_local_tests.md`

**Contenu :**
- Comparaison performances eu-west-3 vs us-east-1
- Différences qualitatives observées
- Recommandations pour le déploiement

---

## Phase 3 – Déploiement AWS DEV

### 3.1 Backup Configuration Actuelle

**Fichier de sauvegarde :** `docs/diagnostics/vectora_inbox_bedrock_migration_backup.md`

**Contenu :**
- Configuration actuelle (région + modèle)
- Procédure de rollback
- Variables d'environnement avant migration

### 3.2 Mise à Jour Variables d'Environnement

**Lambdas à mettre à jour :**

1. **vectora-inbox-ingest-normalize-dev**
   - `BEDROCK_REGION=us-east-1`
   - `BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0`

2. **vectora-inbox-engine-dev**
   - `BEDROCK_REGION=us-east-1`
   - `BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0`

### 3.3 Permissions IAM

**Vérification nécessaire :**
- Autorisation cross-région pour Bedrock us-east-1
- Mise à jour des policies si nécessaire

**Actions IAM potentielles :**
```json
{
  "Effect": "Allow",
  "Action": [
    "bedrock:InvokeModel"
  ],
  "Resource": [
    "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0"
  ]
}
```

### 3.4 Déploiement et Tests de Fumée

**Procédure :**
1. Déploiement des Lambdas avec nouvelles variables
2. Test d'invocation simple (1-2 items)
3. Vérification logs CloudWatch
4. Validation connectivité Bedrock us-east-1

---

## Phase 4 – Run de Validation End-to-End (lai_weekly_v3)

### 4.1 Configuration Run de Validation

**Paramètres :**
- Profil : lai_weekly_v3
- Période : 7 jours (volume modéré ~100 items)
- Mode : Données réelles (pas de simulation)

**Commande d'invocation :**
```powershell
# Méthode payload brut + base64 (validée)
aws lambda invoke --function-name vectora-inbox-ingest-normalize-dev --payload file://payload-lai-weekly-v3.json --cli-binary-format raw-in-base64-out out-ingest-migration-test.json --profile rag-lai-prod --region eu-west-3
```

### 4.2 Métriques de Validation

**Ingestion + Normalisation :**
- Nombre d'items ingérés
- Nombre d'items normalisés avec succès
- Taux d'erreurs Bedrock
- Temps total de normalisation
- Présence throttling

**Engine + Newsletter :**
- Temps d'exécution engine
- Qualité de la newsletter générée
- Présence des items "gold" attendus

**Items Gold à Vérifier :**
- Nanexa/Moderna PharmaShell®
- UZEDY® Extended-Release Injectable
- Signaux LAI authentiques vs bruit HR/finance

### 4.3 Invocation Manuelle Best Practice

**Méthode recommandée (PowerShell) :**
```powershell
# Template d'invocation fiable
$payload = Get-Content -Path "payload-lai-weekly-v3.json" -Raw
aws lambda invoke `
  --function-name vectora-inbox-ingest-normalize-dev `
  --payload $payload `
  --cli-binary-format raw-in-base64-out `
  out-migration-validation.json `
  --profile rag-lai-prod `
  --region eu-west-3

# Puis engine
aws lambda invoke `
  --function-name vectora-inbox-engine-dev `
  --payload file://engine-payload-v3.json `
  --cli-binary-format raw-in-base64-out `
  out-engine-migration-validation.json `
  --profile rag-lai-prod `
  --region eu-west-3
```

---

## Phase 5 – Comparaison Avant/Après & Recommandations

### 5.1 Diagnostic Complet

**Fichier :** `docs/diagnostics/vectora_inbox_bedrock_region_migration_results.md`

**Sections :**

#### 5.1.1 Comparaison Technique
- **Latence** : eu-west-3 vs us-east-1 (ms par appel)
- **Throughput** : Items/minute traités
- **Taux d'erreur** : Throttling, timeouts, autres erreurs
- **Stabilité** : Variabilité des performances

#### 5.1.2 Comparaison Business
- **Items normalisés** : Nombre total pour même période
- **Qualité détection** : Présence items gold, filtrage bruit
- **Newsletter** : Qualité éditoriale, structure, pertinence

#### 5.1.3 Comparaison Coût
- **Tokens consommés** : Input + output par run
- **Coût par token** : Différentiel tarifaire eu-west-3 vs us-east-1
- **Coût total estimé** : Par run lai_weekly_v3

### 5.2 Évaluation MVP

**Critères d'évaluation :**
- ✅ **MVP Prêt** : Performance égale/supérieure + items gold présents
- ⚠️ **MVP À Affiner** : Performance acceptable mais optimisations nécessaires
- ❌ **Rollback Requis** : Dégradation significative

### 5.3 Recommandations P1

**Si migration réussie :**
- Optimisations supplémentaires identifiées
- Monitoring à mettre en place
- Prochaines étapes (migration PROD)

**Si problèmes détectés :**
- Actions correctives prioritaires
- Alternatives à considérer
- Timeline de résolution

---

## Contraintes & Garde-Fous

### Environnements
- **DEV uniquement** : Aucune modification PROD
- **Profil AWS** : rag-lai-prod
- **Région infra** : eu-west-3 (inchangée)

### Rollback
- **Procédure documentée** : Retour configuration eu-west-3
- **Backup complet** : Variables d'environnement + configuration
- **Tests de rollback** : Validation retour état initial

### Sécurité
- **Permissions minimales** : Ajout IAM cross-région si nécessaire
- **Pas de credentials** : Utilisation profil AWS existant
- **Logs** : Monitoring CloudWatch pour détection anomalies

---

## Livrables Attendus

### Documentation
1. **Plan d'exécution** : Ce document
2. **Tests locaux** : `docs/diagnostics/vectora_inbox_bedrock_region_migration_local_tests.md`
3. **Backup config** : `docs/diagnostics/vectora_inbox_bedrock_migration_backup.md`
4. **Résultats finaux** : `docs/diagnostics/vectora_inbox_bedrock_region_migration_results.md`

### Code
1. **Clients Bedrock** : Refactoring avec variables d'environnement
2. **Configuration Lambda** : Variables BEDROCK_REGION + BEDROCK_MODEL_ID
3. **Scripts d'invocation** : PowerShell templates pour tests

### Validation
1. **Run complet lai_weekly_v3** : Avec nouveau Bedrock us-east-1
2. **Métriques comparatives** : Avant/après migration
3. **Recommandation finale** : Go/No-Go pour adoption

---

## Timeline Estimée

- **Phase 0** : 0.5 jour (Discovery)
- **Phase 1** : 1 jour (Refactoring code)
- **Phase 2** : 1 jour (Tests locaux)
- **Phase 3** : 0.5 jour (Déploiement AWS)
- **Phase 4** : 1 jour (Run validation E2E)
- **Phase 5** : 0.5 jour (Analyse & recommandations)

**Total** : 4.5 jours

---

## Critères de Succès

### Technique
- ✅ Appels Bedrock us-east-1 fonctionnels
- ✅ Pas de dégradation performance (latence < +20%)
- ✅ Taux d'erreur stable ou amélioré
- ✅ Pipeline E2E complet (ingestion → newsletter)

### Business
- ✅ Items gold présents (Nanexa/Moderna, UZEDY®)
- ✅ Filtrage bruit HR/finance maintenu
- ✅ Qualité newsletter équivalente/supérieure
- ✅ Coût par run stable ou réduit

### Opérationnel
- ✅ Procédure rollback validée
- ✅ Documentation complète
- ✅ Monitoring en place
- ✅ Équipe formée sur nouvelle configuration

---

**Plan créé le 2025-12-12. Prêt pour exécution phase par phase.**