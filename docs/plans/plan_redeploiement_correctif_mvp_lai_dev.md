# Plan de redéploiement – Correctif sources MVP LAI (Environnement DEV)

## 1. Objectif

Ce document décrit le processus de **redéploiement** de la Lambda `vectora-inbox-ingest-normalize-dev` et des configurations associées après l'implémentation des correctifs sources pour le MVP LAI.

**Contexte** :

Les correctifs suivants ont été implémentés dans le code et les configurations :

- **Nouveau modèle de `source_catalog.yaml`** : ajout des champs `ingestion_mode` (rss/html/api/none), `enabled` (true/false), `homepage_url`, `rss_url`, `html_url` pour distinguer clairement les modes d'ingestion et l'activation des sources.

- **5 sources corporate LAI pilotes** avec ingestion HTML activée :
  - MedinCell (France)
  - Camurus (Suède)
  - DelSiTech (Finlande)
  - Nanexa (Suède)
  - Peptron (Corée du Sud)

- **3 sources presse sectorielle** avec flux RSS activés :
  - FierceBiotech
  - FiercePharma
  - Endpoints News

- **Code Python mis à jour** :
  - `src/vectora_core/config/resolver.py` : filtrage sur `enabled: true` et `ingestion_mode != "none"`
  - `src/vectora_core/ingestion/fetcher.py` : branchement selon `ingestion_mode` (rss → rss_url, html → html_url)
  - `src/vectora_core/ingestion/parser.py` : ajout d'un parser HTML générique avec BeautifulSoup

- **Configuration client mise à jour** :
  - `client-config-examples/lai_weekly.yaml` : utilisation des nouveaux bouquets `lai_press_mvp` (3 sources) et `lai_corporate_mvp` (5 sources)

- **Nouvelle dépendance** :
  - `requirements.txt` : ajout de `beautifulsoup4>=4.12.0` pour le parsing HTML

**Objectif du redéploiement** :

1. Re-packager la Lambda `vectora-inbox-ingest-normalize-dev` avec la nouvelle dépendance BeautifulSoup et le code mis à jour
2. Uploader le nouveau package ZIP dans le bucket de code Lambda
3. Mettre à jour le code de la fonction Lambda sur AWS
4. Re-uploader les fichiers de configuration mis à jour (`source_catalog.yaml` et `lai_weekly.yaml`) dans le bucket de configuration
5. Tester l'ingestion avec une invocation de la Lambda
6. Vérifier les résultats (logs CloudWatch, fichiers S3)

**Résultat attendu** :

Après ce redéploiement, la Lambda devrait produire `items_ingested > 0` lors de l'invocation, avec au moins 3-5 sources produisant des items (presse RSS + quelques sources corporate HTML).

---

## 2. Prérequis

Avant de commencer, assurez-vous que :

### AWS CLI installé et configuré

```powershell
# Vérifier la version d'AWS CLI
aws --version
```

**Résultat attendu** : `aws-cli/2.x.x` ou supérieur.

### Profil AWS configuré

Le profil `rag-lai-prod` doit être configuré avec les permissions nécessaires.

```powershell
# Lister les profils configurés
aws configure list-profiles
```

**Résultat attendu** : Le profil `rag-lai-prod` doit apparaître dans la liste.

### Connexion SSO valide

Si vous utilisez AWS SSO, assurez-vous que votre session est active :

```powershell
# Se connecter via SSO
aws sso login --profile rag-lai-prod --region eu-west-3

# Vérifier l'identité
aws sts get-caller-identity --profile rag-lai-prod --region eu-west-3
```

**Résultat attendu** :
```json
{
    "UserId": "...",
    "Account": "786469175371",
    "Arn": "arn:aws:sts::786469175371:assumed-role/AWSReservedSSO_RAGLai-Admin_..."
}
```

### Python et pip installés

Le packaging de la Lambda nécessite Python et pip :

```powershell
# Vérifier Python
python --version

# Vérifier pip
pip --version
```

**Résultat attendu** : Python 3.11 ou 3.12, pip installé.

### Se placer dans le répertoire du projet

```powershell
# Naviguer vers le répertoire du projet
cd "C:\Users\franc\OneDrive\Bureau\vectora-inbox"
```

---

## 3. Re-packager la Lambda ingest-normalize

La Lambda doit être re-packagée pour inclure la nouvelle dépendance BeautifulSoup et le code mis à jour.

### Définir les variables PowerShell

```powershell
# Variables d'environnement
$Profile = "rag-lai-prod"
$Region  = "eu-west-3"
$CodeBucket = "vectora-inbox-lambda-code-dev"
$BuildDir = "build\ingest-normalize"
```

### Nettoyer et créer le dossier de build

```powershell
# Supprimer le dossier de build existant (si présent)
Remove-Item -Recurse -Force $BuildDir -ErrorAction SilentlyContinue

# Créer un nouveau dossier de build
New-Item -ItemType Directory -Path $BuildDir | Out-Null
```

**Pourquoi cette étape** : On part d'un dossier propre pour éviter d'inclure d'anciens fichiers ou dépendances obsolètes.

### Installer les dépendances dans le dossier de build

```powershell
# Installer toutes les dépendances depuis requirements.txt dans le dossier de build
pip install -r requirements.txt -t $BuildDir --upgrade
```

**Résultat attendu** : Les dépendances (boto3, pyyaml, requests, feedparser, python-dateutil, beautifulsoup4) sont installées dans `build\ingest-normalize\`.

**Note importante** : Cette commande installe BeautifulSoup4 et toutes les autres dépendances nécessaires.

### Copier le code de la Lambda

```powershell
# Copier le handler de la Lambda
Copy-Item src\lambdas\ingest_normalize\handler.py $BuildDir\handler.py

# Copier le package vectora_core (logique métier)
Copy-Item -Recurse src\vectora_core $BuildDir\vectora_core
```

**Pourquoi cette étape** : Le code de la Lambda (handler + vectora_core) doit être à la racine du ZIP pour que AWS Lambda puisse l'exécuter.

### Créer le fichier ZIP

```powershell
# Créer le ZIP du package Lambda
Compress-Archive -Path "$BuildDir\*" -DestinationPath "build\ingest-normalize.zip" -Force
```

**Résultat attendu** : Un fichier `build\ingest-normalize.zip` est créé (environ 15-20 MB avec toutes les dépendances).

### Uploader le ZIP dans le bucket de code

```powershell
# Uploader le ZIP dans S3
aws s3 cp build\ingest-normalize.zip `
  s3://$CodeBucket/lambda/ingest-normalize/latest.zip `
  --profile $Profile --region $Region
```

**Résultat attendu** : Message `upload: build\ingest-normalize.zip to s3://vectora-inbox-lambda-code-dev/lambda/ingest-normalize/latest.zip`.

**Pourquoi cette étape** : AWS Lambda charge le code depuis S3. On doit donc uploader le nouveau package avant de mettre à jour la fonction.

---

## 4. Mettre à jour le code de la Lambda sur AWS

Une fois le nouveau package uploadé dans S3, on peut mettre à jour la fonction Lambda pour qu'elle utilise ce nouveau code.

```powershell
# Mettre à jour le code de la fonction Lambda
aws lambda update-function-code `
  --function-name vectora-inbox-ingest-normalize-dev `
  --s3-bucket $CodeBucket `
  --s3-key lambda/ingest-normalize/latest.zip `
  --profile $Profile --region $Region
```

**Résultat attendu** : Un JSON décrivant la fonction Lambda mise à jour, avec `LastModified` correspondant à l'heure actuelle.

**Pourquoi cette étape** : Cette commande indique à AWS Lambda de recharger le code depuis le nouveau ZIP dans S3. La fonction Lambda utilisera désormais le code mis à jour avec BeautifulSoup.

**Note** : La mise à jour du code peut prendre quelques secondes. AWS Lambda déploie le nouveau code de manière transparente.

---

## 5. Re-uploader les configurations (SourceCatalog + client lai_weekly)

Les fichiers de configuration ont été mis à jour et doivent être re-uploadés dans le bucket de configuration.

### Rappel de la structure du bucket de configuration

Le bucket `vectora-inbox-config-dev` contient :

- `canonical/sources/source_catalog.yaml` : catalogue global des sources avec les nouveaux champs `ingestion_mode`, `enabled`, etc.
- `clients/lai_weekly.yaml` : configuration client utilisant les nouveaux bouquets `lai_press_mvp` et `lai_corporate_mvp`

### Uploader le nouveau source_catalog.yaml

```powershell
# Uploader le catalogue de sources mis à jour
aws s3 cp canonical\sources\source_catalog.yaml `
  s3://vectora-inbox-config-dev/canonical/sources/source_catalog.yaml `
  --profile $Profile --region $Region
```

**Résultat attendu** : Message `upload: canonical\sources\source_catalog.yaml to s3://vectora-inbox-config-dev/canonical/sources/source_catalog.yaml`.

**Pourquoi cette étape** : Le nouveau catalogue contient les 8 sources MVP avec les champs `ingestion_mode`, `enabled`, `rss_url`, `html_url` nécessaires au fonctionnement du pipeline.

### Uploader la configuration client lai_weekly.yaml

```powershell
# Uploader la configuration client mise à jour
aws s3 cp client-config-examples\lai_weekly.yaml `
  s3://vectora-inbox-config-dev/clients/lai_weekly.yaml `
  --profile $Profile --region $Region
```

**Résultat attendu** : Message `upload: client-config-examples\lai_weekly.yaml to s3://vectora-inbox-config-dev/clients/lai_weekly.yaml`.

**Pourquoi cette étape** : La configuration client mise à jour utilise les nouveaux bouquets `lai_press_mvp` et `lai_corporate_mvp` qui correspondent aux 8 sources activées dans le catalogue.

### Vérifier les uploads

```powershell
# Lister les fichiers dans le bucket de configuration
aws s3 ls s3://vectora-inbox-config-dev/canonical/sources/ --profile $Profile --region $Region
aws s3 ls s3://vectora-inbox-config-dev/clients/ --profile $Profile --region $Region
```

**Résultat attendu** : Vous devez voir `source_catalog.yaml` et `lai_weekly.yaml` avec des dates de modification récentes.

---

## 6. Invocation de test de la Lambda

Maintenant que le code et les configurations sont à jour, on peut tester l'ingestion en invoquant la Lambda.

### Créer le payload JSON

Le payload définit les paramètres d'invocation de la Lambda :

```powershell
# Définir le payload JSON
$Payload = '{"client_id":"lai_weekly","period_days":7}'
```

**Explication du payload** :
- `client_id` : identifiant du client (doit correspondre au fichier `clients/lai_weekly.yaml`)
- `period_days` : nombre de jours à remonter dans le passé pour l'ingestion (7 jours = 1 semaine)

### Invoquer la Lambda

```powershell
# Invoquer la Lambda et enregistrer la réponse
aws lambda invoke `
  --function-name vectora-inbox-ingest-normalize-dev `
  --payload $Payload `
  --cli-binary-format raw-in-base64-out `
  out_ingest_lai_weekly_after_correctif.json `
  --profile $Profile --region $Region
```

**Résultat attendu** : Message `StatusCode: 200` et création du fichier `out_ingest_lai_weekly_after_correctif.json`.

**Pourquoi cette étape** : Cette commande déclenche l'exécution de la Lambda avec le nouveau code et les nouvelles configurations. La réponse est enregistrée dans un fichier JSON pour analyse.

### Consulter la réponse

```powershell
# Afficher le contenu de la réponse
Get-Content out_ingest_lai_weekly_after_correctif.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

**Réponse attendue en cas de succès** :

```json
{
  "statusCode": 200,
  "body": {
    "client_id": "lai_weekly",
    "execution_date": "2025-01-15T14:30:00Z",
    "sources_processed": 8,
    "items_ingested": 45,
    "items_normalized": 45,
    "s3_output_path": "s3://vectora-inbox-data-dev/normalized/lai_weekly/2025/01/15/items.json",
    "execution_time_seconds": 87.3
  }
}
```

**Critères de succès** :
- `statusCode: 200` : pas d'erreur critique
- `items_ingested > 0` : au moins quelques items ont été récupérés
- `sources_processed >= 3` : au moins quelques sources ont fonctionné

**Si `items_ingested == 0`** :
- Consulter les logs CloudWatch (voir section suivante)
- Vérifier que les URLs RSS/HTML sont correctes
- Vérifier que les parsers fonctionnent

**Si `statusCode: 500`** :
- Erreur critique dans le code
- Consulter les logs CloudWatch pour identifier l'erreur
- Vérifier la configuration (clés de scopes manquantes, etc.)

---

## 7. Vérifier les logs CloudWatch

Les logs CloudWatch contiennent des informations détaillées sur l'exécution de la Lambda.

### Afficher les logs récents

```powershell
# Afficher les logs des 10 dernières minutes
aws logs tail "/aws/lambda/vectora-inbox-ingest-normalize-dev" `
  --since 10m --format detailed `
  --profile $Profile --region $Region
```

**Résultat attendu** : Logs détaillés de l'exécution de la Lambda.

### Logs attendus en cas de succès

```
INFO: Démarrage de l'ingestion + normalisation pour le client : lai_weekly
INFO: Chargement des configurations depuis S3
INFO: Résolution des sources à traiter
INFO: Bouquets activés : ['lai_press_mvp', 'lai_corporate_mvp']
INFO: Bouquet 'lai_press_mvp' résolu : 3 sources
INFO: Bouquet 'lai_corporate_mvp' résolu : 5 sources
INFO: Total de sources uniques après résolution : 8
INFO: Filtrage sur enabled=true : 8 sources activées, 0 sources ignorées
INFO: Nombre de sources à traiter : 8
INFO: Phase 1A : Ingestion des sources
INFO: Récupération de press_sector__fiercebiotech (mode: rss) depuis https://www.fiercebiotech.com/rss/xml
INFO: Source press_sector__fiercebiotech : 15234 caractères récupérés
INFO: Parsing du contenu de press_sector__fiercebiotech (mode: rss)
INFO: Source press_sector__fiercebiotech : 12 items parsés
INFO: Récupération de press_corporate__camurus (mode: html) depuis https://www.camurus.com/media/press-releases/
INFO: Source press_corporate__camurus : 8765 caractères récupérés
INFO: Parsing du contenu de press_corporate__camurus (mode: html)
INFO: Source press_corporate__camurus : 5 items parsés
...
INFO: Total items bruts récupérés : 45
INFO: Phase 1B : Normalisation des items avec Bedrock
INFO: Total items normalisés : 45
INFO: Écriture des items normalisés dans s3://vectora-inbox-data-dev/normalized/lai_weekly/2025/01/15/items.json
INFO: Ingestion + normalisation terminée
```

### Points à surveiller dans les logs

**Erreurs réseau** :
- `WARNING: Source XXX : HTTP 404` → URL invalide
- `ERROR: Source XXX : timeout après 30s` → source lente ou inaccessible

**Erreurs de parsing** :
- `WARNING: Source XXX : parsing HTML n'a produit aucun item (structure non reconnue)` → structure HTML non supportée par le parser générique
- `ERROR: Erreur lors du parsing RSS de XXX` → flux RSS mal formé

**Sources désactivées** :
- `WARNING: Source 'XXX' est désactivée (enabled=false), ignorée` → source présente dans le catalogue mais désactivée
- `WARNING: Source 'XXX' : ingestion_mode='none', skip` → source sans mode d'ingestion défini

### Suivre les logs en temps réel (optionnel)

Si vous voulez voir les logs en temps réel pendant l'exécution :

```powershell
# Suivre les logs en temps réel
aws logs tail "/aws/lambda/vectora-inbox-ingest-normalize-dev" `
  --follow `
  --profile $Profile --region $Region
```

**Note** : Utilisez `Ctrl+C` pour arrêter le suivi.

---

## 8. Vérifier les fichiers dans DATA_BUCKET

Les items normalisés sont écrits dans le bucket `vectora-inbox-data-dev`. On peut vérifier leur présence et leur contenu.

### Lister les fichiers normalisés

```powershell
# Lister les fichiers dans le bucket de données
aws s3 ls s3://vectora-inbox-data-dev/normalized/lai_weekly/ `
  --recursive --profile $Profile --region $Region
```

**Résultat attendu** : Vous devez voir au moins un fichier comme :
```
2025-01-15 14:30:00    125678 normalized/lai_weekly/2025/01/15/items.json
```

**Pourquoi cette étape** : Cette vérification confirme que la Lambda a bien écrit les items normalisés dans S3.

### Télécharger et inspecter les items normalisés

```powershell
# Télécharger le fichier d'items normalisés
aws s3 cp s3://vectora-inbox-data-dev/normalized/lai_weekly/2025/01/15/items.json `
  items_normalized_after_correctif.json `
  --profile $Profile --region $Region

# Afficher les 3 premiers items
Get-Content items_normalized_after_correctif.json | ConvertFrom-Json | Select-Object -First 3 | ConvertTo-Json -Depth 10
```

**Structure attendue d'un item normalisé** :

```json
{
  "source_key": "press_corporate__camurus",
  "source_type": "press_corporate",
  "title": "Camurus Announces Positive Phase 3 Results for Brixadi",
  "summary": "Camurus a annoncé des résultats positifs pour son essai de Phase 3...",
  "url": "https://www.camurus.com/news/2025/01/phase-3-results",
  "date": "2025-01-10",
  "companies_detected": ["Camurus"],
  "molecules_detected": ["Brixadi", "buprenorphine"],
  "technologies_detected": ["long acting", "depot"],
  "indications_detected": ["opioid use disorder"],
  "event_type": "clinical_update"
}
```

**Pourquoi cette étape** : Cette inspection permet de vérifier la qualité des items normalisés (entités détectées, classification d'événements, résumés).

---

## 9. Interprétation des résultats

### Scénario 1 : Succès complet ✅

**Indicateurs** :
- `statusCode: 200`
- `items_ingested > 0` (par exemple 45 items)
- `sources_processed >= 3` (par exemple 8 sources)
- Fichiers présents dans S3
- Logs sans erreurs critiques

**Conclusion** : Le pipeline fonctionne correctement. Les correctifs ont été déployés avec succès.

**Prochaines étapes** :
- Tester la Lambda engine pour générer la première newsletter
- Valider la qualité des résumés et du matching
- Élargir progressivement le nombre de sources activées

### Scénario 2 : Succès partiel ⚠️

**Indicateurs** :
- `statusCode: 200`
- `items_ingested > 0` mais inférieur à l'attendu
- Certaines sources produisent 0 items
- Logs avec warnings sur parsing HTML

**Conclusion** : Le pipeline fonctionne mais certaines sources ne produisent pas d'items (structure HTML non reconnue, URLs invalides).

**Actions** :
- Identifier les sources en échec dans les logs
- Vérifier manuellement les URLs dans un navigateur
- Ajuster les URLs ou désactiver temporairement les sources problématiques
- Accepter un taux de succès partiel (50-70% des sources HTML)

### Scénario 3 : Aucun item ingéré ❌

**Indicateurs** :
- `statusCode: 200`
- `items_ingested == 0`
- Toutes les sources produisent 0 items

**Conclusion** : Aucune source n'a produit d'items. Problème de configuration ou d'URLs.

**Actions** :
- Consulter les logs CloudWatch pour identifier les erreurs
- Vérifier que les URLs RSS/HTML sont correctes
- Vérifier que les sources sont bien activées (`enabled: true`)
- Tester manuellement les URLs dans un navigateur

### Scénario 4 : Erreur critique ❌

**Indicateurs** :
- `statusCode: 500`
- Message d'erreur dans la réponse

**Conclusion** : Le pipeline a planté. Erreur de code ou de configuration.

**Actions** :
- Consulter les logs CloudWatch pour identifier l'erreur exacte
- Vérifier la configuration (clés de scopes manquantes, etc.)
- Corriger le code ou la configuration
- Re-déployer et re-tester

---

## 10. Limitations connues et points de vigilance

### Parser HTML générique

Le parser HTML est simple et peut ne pas fonctionner sur toutes les structures :
- Cherche des patterns courants (`<article>`, divs avec 'news'/'post')
- Ne gère pas les URLs relatives (nécessite URLs absolues)
- Ne gère pas les sites avec JavaScript dynamique
- Taux de succès attendu : 50-70%

**Solution future** : Ajouter des parsers spécifiques par source si nécessaire.

### URLs à valider manuellement

Certaines sources peuvent avoir des URLs invalides ou des structures HTML complexes. Il est recommandé de :
- Tester manuellement les URLs dans un navigateur
- Vérifier que les flux RSS sont bien accessibles
- Documenter les sources difficiles à parser

### BeautifulSoup requis

Le parser HTML nécessite BeautifulSoup4. Si la dépendance n'est pas installée dans le package Lambda, le parsing HTML échouera.

**Vérification** : S'assurer que `beautifulsoup4>=4.12.0` est dans `requirements.txt` et installé dans le package Lambda.

### Coûts Bedrock

La normalisation utilise Bedrock pour chaque item. Avec 45 items, cela représente environ 45 appels à Bedrock.

**Estimation de coût** : Environ 0.01-0.05 USD par exécution (selon le modèle et la taille des prompts).

**Optimisation future** : Batching des appels Bedrock, cache des résultats.

---

## 11. Résumé des commandes essentielles

### Variables PowerShell

```powershell
$Profile = "rag-lai-prod"
$Region  = "eu-west-3"
$CodeBucket = "vectora-inbox-lambda-code-dev"
$BuildDir = "build\ingest-normalize"
```

### Re-packaging et déploiement complet

```powershell
# 1. Nettoyer et créer le dossier de build
Remove-Item -Recurse -Force $BuildDir -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $BuildDir | Out-Null

# 2. Installer les dépendances
pip install -r requirements.txt -t $BuildDir --upgrade

# 3. Copier le code
Copy-Item src\lambdas\ingest_normalize\handler.py $BuildDir\handler.py
Copy-Item -Recurse src\vectora_core $BuildDir\vectora_core

# 4. Créer le ZIP
Compress-Archive -Path "$BuildDir\*" -DestinationPath "build\ingest-normalize.zip" -Force

# 5. Uploader dans S3
aws s3 cp build\ingest-normalize.zip s3://$CodeBucket/lambda/ingest-normalize/latest.zip --profile $Profile --region $Region

# 6. Mettre à jour la Lambda
aws lambda update-function-code --function-name vectora-inbox-ingest-normalize-dev --s3-bucket $CodeBucket --s3-key lambda/ingest-normalize/latest.zip --profile $Profile --region $Region

# 7. Uploader les configurations
aws s3 cp canonical\sources\source_catalog.yaml s3://vectora-inbox-config-dev/canonical/sources/source_catalog.yaml --profile $Profile --region $Region
aws s3 cp client-config-examples\lai_weekly.yaml s3://vectora-inbox-config-dev/clients/lai_weekly.yaml --profile $Profile --region $Region

# 8. Invoquer la Lambda
$Payload = '{"client_id":"lai_weekly","period_days":7}'
aws lambda invoke --function-name vectora-inbox-ingest-normalize-dev --payload $Payload --cli-binary-format raw-in-base64-out out_ingest_lai_weekly_after_correctif.json --profile $Profile --region $Region

# 9. Consulter la réponse
Get-Content out_ingest_lai_weekly_after_correctif.json | ConvertFrom-Json | ConvertTo-Json -Depth 10

# 10. Consulter les logs
aws logs tail "/aws/lambda/vectora-inbox-ingest-normalize-dev" --since 10m --format detailed --profile $Profile --region $Region

# 11. Vérifier les fichiers S3
aws s3 ls s3://vectora-inbox-data-dev/normalized/lai_weekly/ --recursive --profile $Profile --region $Region
```

---

## 12. Prochaines étapes après succès

Une fois le redéploiement réussi et l'ingestion validée :

1. **Tester la Lambda engine** : Invoquer `vectora-inbox-engine-dev` pour générer la première newsletter
2. **Valider la qualité** : Vérifier les résumés, le matching, les scores
3. **Itérer sur les configurations** : Ajuster les scopes, les sources, les règles de scoring
4. **Élargir les sources** : Activer progressivement plus de sources corporate LAI
5. **Monitorer les coûts** : Suivre les coûts Bedrock et optimiser si nécessaire

---

**Document créé le** : 2025-01-15  
**Dernière mise à jour** : 2025-01-15  
**Version** : 1.0
