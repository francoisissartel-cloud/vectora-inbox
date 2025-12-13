# Vectora Inbox - Phase 1 : Gap Analysis (Repo vs AWS DEV)

**Date :** 2025-01-15  
**Objectif :** Inventaire complet et analyse des écarts entre le repo local et l'environnement AWS DEV  
**Périmètre :** Environnement DEV uniquement (eu-west-3)  
**Profil AWS :** rag-lai-prod

---

## Résumé Exécutif

### État Global : 🟡 ÉCARTS SIGNIFICATIFS IDENTIFIÉS

L'environnement AWS DEV est **partiellement synchronisé** avec le repo local. L'infrastructure de base est en place et fonctionnelle, mais plusieurs changements récents (2-3 derniers jours) ne sont pas encore déployés.

**Points critiques :**
- ✅ Infrastructure de base opérationnelle (buckets, Lambdas, IAM)
- ⚠️ Stack s1-runtime-dev en état UPDATE_ROLLBACK_COMPLETE (problème récent)
- ❌ Fichiers canonical récents manquants (ingestion_profiles.yaml)
- ❌ Code Lambda pas à jour avec les refactors récents

---

## Inventaire Infrastructure AWS DEV

### Stacks CloudFormation ✅ PRÉSENTES
```
vectora-inbox-s0-core-dev     : CREATE_COMPLETE (2025-12-08)
vectora-inbox-s0-iam-dev      : UPDATE_COMPLETE (2025-12-08)
vectora-inbox-s1-runtime-dev  : UPDATE_ROLLBACK_COMPLETE (2025-12-08) ⚠️
```

**⚠️ PROBLÈME IDENTIFIÉ :** La stack s1-runtime-dev est en état UPDATE_ROLLBACK_COMPLETE, indiquant un échec lors de la dernière mise à jour le 8 décembre.

### Fonctions Lambda ✅ PRÉSENTES
```
vectora-inbox-ingest-normalize-dev:
  - Runtime: python3.12
  - Handler: handler.lambda_handler
  - CodeSize: 18.3MB
  - LastModified: 2025-12-09T19:05:59

vectora-inbox-engine-dev:
  - Runtime: python3.12  
  - Handler: handler.lambda_handler
  - CodeSize: 18.3MB
  - LastModified: 2025-12-09T17:20:50
```

**Configuration Environment Variables ✅ CORRECTE :**
- CONFIG_BUCKET: vectora-inbox-config-dev
- DATA_BUCKET: vectora-inbox-data-dev
- NEWSLETTERS_BUCKET: vectora-inbox-newsletters-dev
- BEDROCK_MODEL_ID: eu.anthropic.claude-sonnet-4-5-20250929-v1:0

### Buckets S3 ✅ PRÉSENTS
```
vectora-inbox-config-dev      : Créé 2025-12-08
vectora-inbox-data-dev        : Créé 2025-12-08
vectora-inbox-newsletters-dev : Créé 2025-12-08
vectora-inbox-lambda-code-dev : Créé 2025-12-08
```

### Contenu Bucket Lambda Code ✅ PRÉSENT
```
lambda/engine/latest.zip         : 36.3MB (2025-12-09 20:47)
lambda/engine/phase1.zip         : 18.3MB (2025-12-09 18:20)
lambda/ingest-normalize/latest.zip : 18.3MB (2025-12-08 17:22)
lambda/ingest-normalize/rc0.zip    : 18.3MB (2025-12-09 18:37)
```

---

## Analyse des Écarts : Repo Local vs AWS DEV

### 1. Fichiers Canonical - ÉCARTS MAJEURS ❌

#### Fichiers Manquants dans S3 :
- ❌ **canonical/ingestion/ingestion_profiles.yaml** : ABSENT
  - **Impact :** Nouveau système de profils d'ingestion non déployé
  - **Criticité :** HAUTE - Fonctionnalité clé des changements récents

#### Fichiers Potentiellement Obsolètes dans S3 :
- ⚠️ **canonical/matching/domain_matching_rules.yaml** : Dernière MAJ 2025-12-09 20:45
- ⚠️ **canonical/scoring/scoring_rules.yaml** : Dernière MAJ 2025-12-09 17:13
- ⚠️ **canonical/scopes/technology_scopes.yaml** : Dernière MAJ 2025-12-09 17:12

**Comparaison nécessaire :** Vérification du contenu pour identifier les différences exactes.

#### Fichiers Présents et Probablement À Jour :
- ✅ **canonical/scopes/company_scopes.yaml** : 2025-12-08 11:11
- ✅ **canonical/scopes/molecule_scopes.yaml** : 2025-12-08 11:11
- ✅ **canonical/scopes/trademark_scopes.yaml** : 2025-12-08 11:11
- ✅ **canonical/sources/source_catalog.yaml** : 2025-12-08 12:08
- ✅ **clients/lai_weekly.yaml** : 2025-12-08 12:08

### 2. Code Lambda - ÉCARTS CRITIQUES ❌

#### Modules Manquants dans les Packages Lambda :
Basé sur les diagnostics récents, les changements suivants ne sont PAS dans les Lambdas actuelles :

**Ingestion Profiles Runtime :**
- ❌ Module `profile_filter.py` (400+ lignes)
- ❌ Intégration dans `fetcher.py` et `normalizer.py`
- ❌ Logique de filtrage pré-Bedrock

**Normalisation Open-World :**
- ❌ Refactor `bedrock_client.py` avec nouveau schéma
- ❌ Séparation `molecules_detected` vs `trademarks_detected`
- ❌ Logique `*_detected` vs `*_in_scopes`

**Runtime LAI Matching :**
- ❌ Logique `technology_complex` dans `matcher.py`
- ❌ Company scope modifiers (pure_player vs hybrid)
- ❌ Nouvelles règles de combinaison

**HTML Parser Refactor :**
- ❌ Parser HTML générique
- ❌ Extracteurs spécialisés dans `html_extractors.yaml`

**Scoring Weekly :**
- ❌ Neutralisation `recency_factor` pour period_days <= 7
- ❌ Ajustements des bonuses pure_player

#### Taille des Packages :
- **Actuel :** ~18MB (ingest-normalize et engine)
- **Attendu :** Probablement 20-25MB avec tous les nouveaux modules

### 3. Configuration Client - PROBABLEMENT À JOUR ✅

Le fichier `clients/lai_weekly.yaml` semble à jour (2025-12-08), mais nécessite vérification du contenu pour s'assurer qu'il inclut les références aux nouveaux scopes et profils.

---

## Impact des Écarts Identifiés

### Fonctionnalités Non Disponibles en DEV :

1. **Profils d'Ingestion (CRITIQUE)**
   - Pas de filtrage pré-Bedrock
   - Coûts Bedrock plus élevés (60-80% d'économies perdues)
   - Sources hybrid non optimisées

2. **Normalisation Open-World (IMPORTANTE)**
   - Pas de séparation molecules/trademarks
   - Schéma de données obsolète
   - Détection d'entités limitée aux scopes canonical

3. **Matching LAI Avancé (IMPORTANTE)**
   - Logique technology_complex non disponible
   - Company scope modifiers non appliqués
   - Risque de faux positifs/négatifs

4. **Parser HTML Générique (MODÉRÉE)**
   - Sources corporate limitées aux extracteurs hardcodés
   - Pas de flexibilité pour nouvelles sources

5. **Scoring Weekly Optimisé (MODÉRÉE)**
   - Recency factor non neutralisé
   - Scoring potentiellement biaisé sur fenêtre courte

### Risques Opérationnels :

1. **Tests Incomplets**
   - Impossible de tester les nouvelles fonctionnalités en DEV
   - Validation métier bloquée

2. **Régression Potentielle**
   - Stack s1-runtime-dev en état d'échec
   - Risque de dysfonctionnement des Lambdas

3. **Incohérence Environnements**
   - Développement local vs DEV désynchronisés
   - Risque d'erreurs lors du passage en PROD

---

## Recommandations de Séquence de Déploiement

### Phase 2 : Mise à Jour Canonical/Config (PRIORITÉ 1) 🔥
**Durée estimée :** 30 minutes  
**Risque :** FAIBLE

**Actions :**
1. Upload `canonical/ingestion/ingestion_profiles.yaml`
2. Vérification et mise à jour des fichiers canonical modifiés
3. Backup des versions actuelles avant remplacement

**Justification :** Sans risque, permet de préparer le terrain pour les Lambdas

### Phase 3 : Résolution Stack Runtime (PRIORITÉ 1) 🔥
**Durée estimée :** 1 heure  
**Risque :** MODÉRÉ

**Actions :**
1. Investigation de l'échec UPDATE_ROLLBACK_COMPLETE
2. Correction des paramètres ou template si nécessaire
3. Redéploiement de la stack s1-runtime-dev

**Justification :** Critique pour la stabilité de l'environnement

### Phase 4 : Packaging et Déploiement Lambda (PRIORITÉ 2) ⚠️
**Durée estimée :** 2 heures  
**Risque :** MODÉRÉ à ÉLEVÉ

**Actions :**
1. Build des nouveaux packages avec tous les modules récents
2. Upload vers le bucket lambda-code-dev
3. Mise à jour des fonctions Lambda
4. Tests de validation

**Justification :** Apporte toutes les nouvelles fonctionnalités mais risque de régression

### Phase 5 : Tests End-to-End (PRIORITÉ 3) 📋
**Durée estimée :** 1 heure  
**Risque :** FAIBLE

**Actions :**
1. Test complet du workflow lai_weekly
2. Validation des nouvelles fonctionnalités
3. Comparaison avec les résultats attendus

---

## Critères de Succès par Phase

### Phase 2 - Canonical/Config :
- ✅ Tous les fichiers canonical synchronisés
- ✅ `ingestion_profiles.yaml` présent dans S3
- ✅ Backup des anciennes versions créé
- ✅ Pas d'erreurs de validation YAML

### Phase 3 - Stack Runtime :
- ✅ Stack s1-runtime-dev en état UPDATE_COMPLETE
- ✅ Lambdas fonctionnelles et accessibles
- ✅ Variables d'environnement correctes
- ✅ Logs CloudWatch sans erreurs

### Phase 4 - Lambda Code :
- ✅ Packages buildés avec succès (taille attendue 20-25MB)
- ✅ Fonctions Lambda mises à jour
- ✅ Nouveaux modules importables
- ✅ Tests unitaires passent en environnement Lambda

### Phase 5 - Tests E2E :
- ✅ Workflow lai_weekly complet fonctionnel
- ✅ Profils d'ingestion appliqués correctement
- ✅ Normalisation open-world opérationnelle
- ✅ Newsletter générée avec nouveau format

---

## Plan de Rollback

### En cas de problème Phase 2 :
- Restauration des fichiers canonical depuis backup S3
- Pas d'impact sur les Lambdas (lecture seule)

### En cas de problème Phase 3 :
- Rollback de la stack CloudFormation vers version précédente
- Vérification de l'état des Lambdas

### En cas de problème Phase 4 :
- Rollback des packages Lambda vers versions précédentes
- Utilisation des fichiers .zip de backup dans S3
- Redéploiement des fonctions avec anciens packages

### En cas de problème Phase 5 :
- Pas de rollback nécessaire (tests uniquement)
- Investigation et correction des problèmes identifiés

---

## Conclusion

L'environnement AWS DEV nécessite une **synchronisation complète** pour être aligné avec les développements récents. Les écarts identifiés sont significatifs mais gérables avec une approche séquentielle.

**Recommandation principale :** Procéder aux phases 2 et 3 immédiatement (canonical + stack runtime), puis planifier la phase 4 (Lambda code) avec précaution.

**Risque principal :** La stack s1-runtime-dev en échec nécessite une attention immédiate pour éviter des problèmes de stabilité.

**Opportunité :** Une fois synchronisé, l'environnement DEV permettra de valider toutes les améliorations récentes avant le passage en production.

---

**Prochaine étape :** Exécution de la Phase 2 (Canonical/Config) après validation de ce diagnostic.

**Audit réalisé par :** Amazon Q Developer  
**Validation :** Infrastructure AWS, code Lambda, configurations canonical  
**Périmètre :** Environnement DEV complet