# Plan d'implémentation : vectora-inbox-ingest-V2

## Introduction

Cette itération se limite à l'implémentation et au déploiement de `vectora-inbox-ingest-V2`. Les Lambdas `normalize-score` et `newsletter` V2 seront traitées plus tard, uniquement si cette première Lambda est un succès.

## Rôle de vectora-inbox-ingest-V2

La Lambda `vectora-inbox-ingest-V2` est responsable de l'**ingestion brute** des contenus depuis les sources externes (RSS, APIs, sites web) et de leur **stockage dans S3** pour traitement ultérieur. Elle ne fait **aucun appel à Bedrock** et se concentre uniquement sur la récupération et le parsing initial des contenus.

**Responsabilités :**
- Récupération des contenus bruts depuis les sources configurées
- Parsing initial des contenus en items structurés
- Stockage des données dans S3 layer `ingested/`
- Gestion des erreurs et retry automatique
- Respect des limites de débit par source

**Ce qu'elle NE fait PAS :**
- Normalisation des contenus (délégué à normalize-score V2)
- Appels à Bedrock (IA)
- Matching ou scoring des items

---

## Structure proposée pour /src_v2

```
/src_v2/
├── lambdas/
│   └── ingest/
│       ├── handler.py              # Point d'entrée Lambda
│       └── requirements.txt        # Dépendances spécifiques (si nécessaires)
└── vectora_core/
    ├── __init__.py
    ├── config_loader.py            # Chargement config client + canonical
    ├── s3_io.py                    # Opérations S3 (lecture/écriture)
    ├── source_fetcher.py           # Récupération contenus (RSS, HTTP, API)
    ├── content_parser.py           # Parsing contenus en items structurés
    ├── models.py                   # Modèles de données (Item, Source, etc.)
    └── utils.py                    # Utilitaires génériques
```

---

## Phase 0 – Analyse & Cadrage

### Objectifs
- Analyser l'existant V1 pour comprendre les patterns établis
- Valider l'alignement avec les règles d'hygiène V4
- Définir les spécifications techniques précises

### Actions détaillées
- Examiner le handler existant `/src/lambdas/ingest_normalize/handler.py`
- Analyser la structure de `vectora_core` V1 pour identifier les modules réutilisables
- Vérifier les variables d'environnement utilisées (CONFIG_BUCKET, DATA_BUCKET)
- Identifier les patterns de gestion d'erreur et de logging
- Valider les formats d'events d'entrée actuels
- Examiner les configurations canonical existantes (source_catalog.yaml)

### Fichiers concernés
- `/src/lambdas/ingest_normalize/handler.py` (lecture)
- `/src/vectora_core/` (analyse)
- `/canonical/sources/source_catalog.yaml` (lecture)
- `/client-config-examples/lai_weekly_v3.yaml` (lecture)

### Pilotage par config
- Validation que toute logique métier est pilotée par `client_config` et `canonical`
- Aucune règle business hardcodée dans le code Python
- Configuration des sources via `source_catalog.yaml`
- Paramètres d'ingestion via `ingestion_profiles.yaml`

### Respect src_lambda_hygiene_v4
- Aucune dépendance tierce copiée dans `/src_v2`
- Structure modulaire avec `vectora_core` séparé
- Handler minimal avec orchestration simple
- Taille du code source < 5MB

### Critères de "done"
- [ ] Analyse complète de l'existant V1 documentée
- [ ] Spécifications techniques V2 validées
- [ ] Structure `/src_v2` définie et approuvée
- [ ] Variables d'environnement identifiées

### Risques
- Incompatibilité avec les formats d'events existants
- Dépendances manquantes non identifiées

---

## Phase 1 – Design de la structure /src_v2

### Objectifs
- Créer la structure de dossiers `/src_v2` conforme aux règles V4
- Définir les interfaces entre modules
- Préparer l'utilisation future des Lambda Layers

### Actions détaillées
- Créer l'arborescence `/src_v2/lambdas/ingest/` et `/src_v2/vectora_core/`
- Définir les signatures des fonctions principales dans chaque module
- Créer les fichiers `__init__.py` minimaux
- Définir le contrat d'interface entre handler et vectora_core
- Préparer la structure pour les Lambda Layers (sans les implémenter)

### Fichiers concernés
- `/src_v2/lambdas/ingest/handler.py` (squelette)
- `/src_v2/vectora_core/__init__.py`
- `/src_v2/vectora_core/config_loader.py` (squelette)
- `/src_v2/vectora_core/s3_io.py` (squelette)
- `/src_v2/vectora_core/source_fetcher.py` (squelette)
- `/src_v2/vectora_core/content_parser.py` (squelette)
- `/src_v2/vectora_core/models.py` (squelette)
- `/src_v2/vectora_core/utils.py` (squelette)

### Pilotage par config
- Interface `config_loader` pour charger client_config et canonical
- Aucune logique métier dans les squelettes
- Préparation pour la lecture des configurations S3

### Respect src_lambda_hygiene_v4
- Structure modulaire claire
- Séparation handler/core
- Aucune dépendance tierce dans `/src_v2`
- Préparation Lambda Layers

### Critères de "done"
- [ ] Structure `/src_v2` créée et conforme
- [ ] Squelettes de tous les modules créés
- [ ] Interfaces définies et documentées
- [ ] Aucune violation des règles V4

### Risques
- Structure inadaptée aux besoins réels
- Interfaces trop complexes ou trop simples

---

## Phase 2 – Implémentation du code de la Lambda

### Objectifs
- Implémenter la logique complète de la Lambda ingest V2
- Respecter le contrat métier défini dans `ingest_v2.md`
- Assurer la compatibilité avec les configurations existantes

### Actions détaillées
- Implémenter `handler.py` avec gestion des events et orchestration
- Développer `config_loader.py` pour charger client_config et canonical depuis S3
- Créer `s3_io.py` pour les opérations de lecture/écriture S3
- Implémenter `source_fetcher.py` pour récupérer contenus RSS/HTTP/API
- Développer `content_parser.py` pour parser les contenus en items structurés
- Créer `models.py` avec les classes Item, Source, Config
- Implémenter `utils.py` avec fonctions utilitaires (hashing, dates, etc.)
- Ajouter la gestion d'erreurs et logging appropriés
- Implémenter le retry automatique et rate limiting

### Fichiers concernés
- `/src_v2/lambdas/ingest/handler.py` (implémentation complète)
- `/src_v2/vectora_core/config_loader.py` (implémentation complète)
- `/src_v2/vectora_core/s3_io.py` (implémentation complète)
- `/src_v2/vectora_core/source_fetcher.py` (implémentation complète)
- `/src_v2/vectora_core/content_parser.py` (implémentation complète)
- `/src_v2/vectora_core/models.py` (implémentation complète)
- `/src_v2/vectora_core/utils.py` (implémentation complète)

### Pilotage par config
- Lecture des sources depuis `canonical/sources/source_catalog.yaml`
- Paramètres d'ingestion depuis `canonical/ingestion/ingestion_profiles.yaml`
- Configuration client depuis `client_config/{client_id}.yaml`
- Aucune logique métier hardcodée

### Respect src_lambda_hygiene_v4
- Utilisation uniquement des libs Python standard + boto3
- Aucune dépendance tierce copiée
- Code source total < 5MB
- Handler minimal avec logique dans vectora_core

### Critères de "done"
- [ ] Tous les modules implémentés et fonctionnels
- [ ] Gestion d'erreurs complète
- [ ] Logging approprié
- [ ] Respect du contrat `ingest_v2.md`
- [ ] Code testé unitairement (modules individuels)

### Risques
- Complexité sous-estimée du parsing de certaines sources
- Gestion des timeouts et rate limiting insuffisante
- Formats de données incompatibles avec V1

---

## Phase 3 – Tests locaux (sur le client lai_weekly_v3)

### Objectifs
- Valider le fonctionnement de la Lambda en local
- Tester avec la configuration réelle du client `lai_weekly_v3`
- Identifier et corriger les bugs avant déploiement

### Actions détaillées
- Créer un script de test local hors `/src_v2` : `/scripts/test_ingest_v2_local.py`
- Configurer les variables d'environnement locales (CONFIG_BUCKET, DATA_BUCKET)
- Préparer des events de test basés sur `lai_weekly_v3`
- Tester l'ingestion sur un sous-ensemble de sources (2-3 sources max)
- Valider la structure des données écrites dans S3
- Tester les cas d'erreur (source indisponible, timeout, etc.)
- Vérifier les logs et métriques
- Tester le mode `dry_run`

### Fichiers concernés
- `/scripts/test_ingest_v2_local.py` (nouveau)
- `/scripts/events/test_lai_weekly_minimal.json` (nouveau)
- `/scripts/events/test_lai_weekly_full.json` (nouveau)

### Pilotage par config
- Utilisation de la vraie config `lai_weekly_v3.yaml`
- Test avec les vraies sources du catalog canonical
- Validation que la config pilote bien le comportement

### Respect src_lambda_hygiene_v4
- Script de test hors `/src_v2`
- Pas de modification du code pour les tests
- Utilisation des vraies configs sans stub

### Critères de "done"
- [ ] Script de test local fonctionnel
- [ ] Tests réussis sur client `lai_weekly_v3`
- [ ] Données S3 générées conformes au format attendu
- [ ] Gestion d'erreurs validée
- [ ] Performance acceptable (< 5min pour ingestion complète)

### Risques
- Sources externes indisponibles pendant les tests
- Problèmes de permissions S3 en local
- Performance insuffisante

### Commandes de test (pseudo-code)
```bash
# Configuration environnement local
export AWS_PROFILE=rag-lai-prod
export AWS_REGION=eu-west-3
export CONFIG_BUCKET=vectora-inbox-config-dev
export DATA_BUCKET=vectora-inbox-data-dev

# Test minimal
python scripts/test_ingest_v2_local.py --event scripts/events/test_lai_weekly_minimal.json

# Test complet
python scripts/test_ingest_v2_local.py --event scripts/events/test_lai_weekly_full.json --dry-run
```

---

## Phase 4 – Packaging & déploiement AWS

### Objectifs
- Packager la Lambda pour déploiement AWS
- Créer/mettre à jour l'infrastructure CloudFormation
- Déployer la Lambda `vectora-inbox-ingest-v2` en environnement dev

### Actions détaillées
- Créer le package de déploiement (ZIP) avec `/src_v2/lambdas/ingest/` + `/src_v2/vectora_core/`
- Mettre à jour ou créer la stack CloudFormation pour la nouvelle Lambda
- Configurer les variables d'environnement AWS (CONFIG_BUCKET, DATA_BUCKET)
- Configurer les permissions IAM (S3 read/write, CloudWatch logs)
- Déployer la Lambda via CloudFormation
- Configurer les triggers EventBridge si nécessaire
- Vérifier le déploiement et les logs CloudWatch

### Fichiers concernés
- `/infra/s1-ingest-v2.yaml` (nouveau ou mise à jour)
- `/scripts/deploy_ingest_v2.sh` (nouveau)
- Package ZIP temporaire (généré)

### Pilotage par config
- Variables d'environnement pointant vers les bons buckets
- Aucune config hardcodée dans l'infra

### Respect src_lambda_hygiene_v4
- Package < 50MB (avec dépendances)
- Code source < 5MB
- Utilisation des conventions de nommage établies
- Région eu-west-3, profil rag-lai-prod

### Critères de "done"
- [ ] Package de déploiement créé et validé
- [ ] Stack CloudFormation déployée avec succès
- [ ] Lambda visible dans la console AWS
- [ ] Variables d'environnement correctement configurées
- [ ] Permissions IAM fonctionnelles
- [ ] Logs CloudWatch accessibles

### Risques
- Problèmes de permissions IAM
- Taille du package trop importante
- Erreurs de configuration CloudFormation

### Commandes de déploiement (pseudo-code)
```bash
# Création du package
cd /src_v2/lambdas/ingest
zip -r ../../../vectora-inbox-ingest-v2.zip . -x "*.pyc" "__pycache__/*"
cd ../../../src_v2/vectora_core
zip -r ../../vectora-inbox-ingest-v2.zip . -x "*.pyc" "__pycache__/*"

# Upload du code
aws s3 cp vectora-inbox-ingest-v2.zip s3://vectora-inbox-lambda-code-dev/ --profile rag-lai-prod --region eu-west-3

# Déploiement de la stack
aws cloudformation deploy \
  --template-file infra/s1-ingest-v2.yaml \
  --stack-name vectora-inbox-s1-ingest-v2-dev \
  --capabilities CAPABILITY_IAM \
  --profile rag-lai-prod \
  --region eu-west-3

# Mise à jour du code Lambda
aws lambda update-function-code \
  --function-name vectora-inbox-ingest-v2-dev \
  --s3-bucket vectora-inbox-lambda-code-dev \
  --s3-key vectora-inbox-ingest-v2.zip \
  --profile rag-lai-prod \
  --region eu-west-3
```

---

## Phase 5 – Tests d'intégration finaux (sur le client lai_weekly_v3)

### Objectifs
- Valider le fonctionnement de la Lambda déployée en AWS
- Tester l'intégration complète avec S3 et les configurations
- Valider les performances et la fiabilité

### Actions détaillées
- Invoquer la Lambda via AWS CLI avec des events de test
- Tester l'ingestion complète du client `lai_weekly_v3`
- Vérifier les données écrites dans S3 `vectora-inbox-data-dev`
- Analyser les logs CloudWatch pour détecter les erreurs
- Mesurer les performances (durée d'exécution, mémoire utilisée)
- Tester les cas d'erreur (sources indisponibles, timeouts)
- Valider le retry automatique
- Tester l'invocation via EventBridge (si configuré)

### Fichiers concernés
- `/scripts/test_ingest_v2_aws.py` (nouveau)
- Events de test JSON (réutilisés de Phase 3)
- Logs CloudWatch (lecture)

### Pilotage par config
- Utilisation des vraies configurations en environnement dev
- Test avec toutes les sources configurées pour `lai_weekly_v3`

### Respect src_lambda_hygiene_v4
- Tests via outils AWS standard
- Pas de modification du code déployé
- Utilisation du profil rag-lai-prod

### Critères de "done"
- [ ] Lambda invocable avec succès via AWS CLI
- [ ] Ingestion complète `lai_weekly_v3` réussie
- [ ] Données S3 conformes et complètes
- [ ] Logs CloudWatch propres (pas d'erreurs critiques)
- [ ] Performance acceptable (< 15min timeout Lambda)
- [ ] Gestion d'erreurs fonctionnelle

### Risques
- Timeout Lambda (15min max)
- Problèmes de réseau AWS vers sources externes
- Quotas AWS dépassés

### Commandes de test (pseudo-code)
```bash
# Test invocation directe
aws lambda invoke \
  --function-name vectora-inbox-ingest-v2-dev \
  --payload file://scripts/events/test_lai_weekly_full.json \
  --response.json \
  --profile rag-lai-prod \
  --region eu-west-3

# Vérification des données S3
aws s3 ls s3://vectora-inbox-data-dev/ingested/lai_weekly/ --recursive --profile rag-lai-prod --region eu-west-3

# Consultation des logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/vectora-inbox-ingest-v2" --profile rag-lai-prod --region eu-west-3
```

---

## Phase 6 – Retours avec statut, état, mesures métriques, qualité d'utilisation

### Objectifs
- Évaluer la qualité et l'efficacité de la Lambda déployée
- Mesurer sa capacité à ingérer sur le MVP et réduire le bruit
- Analyser sa sélectivité et précision
- Documenter les métriques de performance et qualité

### Actions détaillées
- Collecter les métriques CloudWatch (durée, mémoire, erreurs, invocations)
- Analyser la qualité des données ingérées (complétude, précision, déduplication)
- Mesurer le taux de succès par source (sources disponibles vs indisponibles)
- Évaluer la capacité de filtrage temporel et de déduplication
- Analyser les logs pour identifier les patterns d'erreur
- Mesurer l'impact sur les coûts AWS (Lambda, S3, CloudWatch)
- Documenter les recommandations d'amélioration
- Préparer un rapport de qualité pour validation

### Fichiers concernés
- `/docs/reports/ingest_v2_quality_report.md` (nouveau)
- `/scripts/analyze_ingest_v2_metrics.py` (nouveau)
- Métriques CloudWatch (lecture)
- Données S3 ingérées (analyse)

### Métriques à collecter
- **Performance** : Durée moyenne d'exécution, pic mémoire, taux d'erreur
- **Qualité des données** : Nombre d'items ingérés, taux de déduplication, sources en échec
- **Sélectivité** : Précision du filtrage temporel, pertinence des items récupérés
- **Fiabilité** : Taux de succès des retry, gestion des timeouts
- **Coûts** : Coût par invocation, coût de stockage S3 généré

### Pilotage par config
- Analyse de l'efficacité du pilotage par configuration
- Identification des paramètres de config les plus impactants

### Respect src_lambda_hygiene_v4
- Analyse de la conformité aux règles d'hygiène
- Validation de la maintenabilité du code

### Critères de "done"
- [ ] Métriques de performance collectées et analysées
- [ ] Rapport de qualité des données rédigé
- [ ] Recommandations d'amélioration documentées
- [ ] Validation de la capacité à réduire le bruit
- [ ] Évaluation de la sélectivité et précision
- [ ] Analyse des coûts AWS générés

### Risques
- Métriques insuffisantes pour évaluation complète
- Qualité des données difficile à mesurer objectivement
- Coûts AWS plus élevés que prévu

---

## Configuration S3 et Events

### Buckets S3 utilisés (environnement dev)
- **Config** : `vectora-inbox-config-dev`
  - `clients/lai_weekly_v3.yaml` : Configuration client
  - `canonical/sources/source_catalog.yaml` : Catalogue des sources
  - `canonical/ingestion/ingestion_profiles.yaml` : Profils d'ingestion
- **Data** : `vectora-inbox-data-dev`
  - `ingested/{client_id}/{YYYY}/{MM}/{DD}/items.json` : Items parsés (sortie principale)
  - `raw/{client_id}/{source_key}/{YYYY}/{MM}/{DD}/raw.json` : Contenus bruts (debug, optionnel)

### Structure des events d'entrée
```json
{
  "client_id": "lai_weekly_v3",
  "sources": ["press_corporate__medincell", "press_sector__fiercebiotech"],
  "period_days": 7,
  "dry_run": false
}
```

### Naming de la Lambda AWS
- **Nom de fonction** : `vectora-inbox-ingest-v2-dev`
- **Groupe de logs** : `/aws/lambda/vectora-inbox-ingest-v2-dev`
- **Rôle IAM** : `vectora-inbox-ingest-v2-role-dev`

---

## Utilisation future des Lambda Layers

### Préparation (sans implémentation immédiate)
- Structure `vectora_core` conçue pour être extraite en Layer
- Séparation claire entre handler (spécifique) et core (générique)
- Taille du core estimée < 10MB pour compatibilité Layer

### Avantages futurs
- Réutilisation de `vectora_core` par les Lambdas normalize-score et newsletter V2
- Réduction de la taille des packages de déploiement
- Mise à jour centralisée des fonctions communes

### Structure Layer future
```
/lambda-layers/
└── vectora-core-v2/
    └── python/
        └── vectora_core/
            ├── __init__.py
            ├── config_loader.py
            ├── s3_io.py
            ├── models.py
            └── utils.py
```

---

## Résumé des phases

- **Phase 0** : Analyse & cadrage
- **Phase 1** : Design de la structure /src_v2
- **Phase 2** : Implémentation du code de la Lambda
- **Phase 3** : Tests locaux (sur le client lai_weekly_v3)
- **Phase 4** : Packaging & déploiement AWS
- **Phase 5** : Tests d'intégration finaux (sur le client lai_weekly_v3)
- **Phase 6** : Retours avec statut, état, mesures métriques, qualité d'utilisation

Chaque phase doit être validée avant de passer à la suivante.