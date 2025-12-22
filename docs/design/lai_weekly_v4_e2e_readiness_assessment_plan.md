# Plan d'Évaluation E2E Complet - lai_weekly_v4 Workflow Assessment

**Date :** 21 décembre 2025  
**Version :** 3.0 (Option 1 - Test E2E Complet)  
**Objectif :** Évaluer le workflow Vectora Inbox V2 complet sur données réelles pour lai_weekly_v4  
**Workflow testé :** ingest-v2 → normalize-score-v2 → newsletter-v2  
**Contrainte :** AUCUNE modification de code, config, infra ou Lambdas autorisée  

---

## Périmètre du Test

### Lambdas Concernées
- **vectora-inbox-ingest-v2-dev** (handler: src_v2/lambdas/ingest/handler.py)
- **vectora-inbox-normalize-score-v2-dev** (handler: src_v2/lambdas/normalize_score/handler.py)
- **vectora-inbox-newsletter-v2-dev** (handler: src_v2/lambdas/newsletter/handler.py) ✅ **NOUVEAU**

### Environnement
- **Environnement :** dev
- **Région principale :** eu-west-3 (Paris)
- **Région Bedrock :** us-east-1 (Virginie du Nord)
- **Profil AWS :** rag-lai-prod
- **Compte AWS :** 786469175371

### Client Cible
- **Client ID :** lai_weekly_v4
- **Configuration :** client-config-examples/lai_weekly_v4.yaml

### Buckets Utilisés
- **Configuration :** vectora-inbox-config-dev
- **Données :** vectora-inbox-data-dev
- **Newsletters :** vectora-inbox-newsletters-dev (pour future Lambda newsletter)

---

## Objectifs Précis

### 1. Vérification Flux Technique Complet
Confirmer que le workflow complet fonctionne sur données réelles :
```
ingest_v2 → S3 ingested/lai_weekly_v4/YYYY/MM/DD/items.json 
         → normalize_score_v2 → S3 curated/lai_weekly_v4/YYYY/MM/DD/items.json
         → newsletter_v2 → S3 newsletters/lai_weekly_v4/YYYY/MM/DD/newsletter.md
```

### 2. Validation Mode Latest_Run_Only
Vérifier que le mode `newsletter_mode: "latest_run_only"` fonctionne correctement :
- Newsletter ne traite que le dernier dossier créé par normalize
- Pas de traitement sur période glissante (30 jours)
- Cohérence avec l'architecture "mode run"

### 3. Métriques et Performance Complètes
Mesurer :
- Volumes traités (items ingérés vs normalisés vs matchés vs sélectionnés newsletter)
- Matching rate par domaine de veille
- Distribution des scores et sélection newsletter
- Coûts Bedrock complets (normalisation + matching + newsletter)
- Temps d'exécution des 3 Lambdas
- Ratio bruit vs pertinence à chaque étape
- Qualité éditoriale de la newsletter générée

### 4. Document de Feedback Moteur ✅ **NOUVEAU**
Générer un document de synthèse structuré pour feedback à Q :
- Liste précise de chaque item avec décisions moteur
- Justifications des inclusions/exclusions/matchs/scores
- Format adapté pour validation humaine ("d'accord/pas d'accord")
- Recommandations d'amélioration ciblées (filtres, scores, prompts)

---

## Contraintes

### Interdictions Absolues
- ❌ Modification de src_v2/ (code)
- ❌ Modification de client-config-examples/lai_weekly_v4.yaml
- ❌ Modification de canonical/* (prompts, scopes)
- ❌ Modification de la configuration des Lambdas ou layers
- ❌ Modification de l'infrastructure AWS

### Actions Autorisées
- ✅ Lancement d'invocations Lambda (scripts ou CLI)
- ✅ Lecture des logs CloudWatch
- ✅ Téléchargement et analyse des fichiers S3
- ✅ Création de nouveaux fichiers dans docs/ / output/ / tests/ / scripts/ pour analyser
- ✅ Mesure des métriques et coûts

---

## Structure du Plan - 8 Phases

### Phase 1 – Préparation & Sanity Check
**Durée estimée :** 30 minutes  
**Objectif :** Vérifier l'état de l'environnement sans rien modifier

### Phase 2 – Run Ingestion Réel  
**Durée estimée :** 45 minutes  
**Objectif :** Exécuter ingest_v2 pour lai_weekly_v4 et analyser les résultats

### Phase 3 – Run Normalize_Score Réel
**Durée estimée :** 60 minutes  
**Objectif :** Exécuter normalize_score_v2 et analyser la normalisation/scoring

### Phase 4 – Run Newsletter Réel ✅ **NOUVEAU**
**Durée estimée :** 45 minutes  
**Objectif :** Exécuter newsletter_v2 et analyser la génération de newsletter

### Phase 5 – Analyse S3 (Ingested + Curated + Newsletter)
**Durée estimée :** 60 minutes  
**Objectif :** Examiner la structure et le contenu des fichiers S3 générés

### Phase 6 – Analyse Détaillée des Items
**Durée estimée :** 90 minutes  
**Objectif :** Analyser item par item la qualité du matching et scoring

### Phase 7 – Métriques, Coûts, Performance
**Durée estimée :** 60 minutes  
**Objectif :** Calculer les métriques de performance et coûts complets

### Phase 8 – Document de Feedback Moteur ✅ **NOUVEAU**
**Durée estimée :** 75 minutes  
**Objectif :** Générer le document de synthèse pour feedback à Q

---

## Phase 1 – Préparation & Sanity Check

### Fichiers de Référence à Vérifier (Lecture Seule)

#### Code Source V2
- [ ] `src_v2/lambdas/ingest/handler.py`
- [ ] `src_v2/lambdas/normalize_score/handler.py`
- [ ] `src_v2/vectora_core/ingest/__init__.py`
- [ ] `src_v2/vectora_core/normalization/__init__.py`
- [ ] `src_v2/vectora_core/shared/config_loader.py`
- [ ] `src_v2/vectora_core/shared/s3_io.py`

#### Configuration Client
- [ ] `client-config-examples/lai_weekly_v4.yaml`
- [ ] Vérifier `active: true` (ou équivalent)
- [ ] Vérifier `watch_domains` configurés
- [ ] Vérifier `newsletter_layout` présent

#### Configuration Canonical
- [ ] `canonical/prompts/global_prompts.yaml`
- [ ] `canonical/scopes/tech_lai_ecosystem.yaml`
- [ ] `canonical/scopes/regulatory_lai.yaml`
- [ ] `canonical/scopes/partnerships_lai.yaml`
- [ ] `canonical/sources/source_catalog.yaml`

### Vérifications Environnement

#### Structure S3 Attendue
Confirmer que la structure S3 cible est conforme :
```
s3://vectora-inbox-data-dev/
├── ingested/lai_weekly_v4/<YYYY>/<MM>/<DD>/items.json
├── curated/lai_weekly_v4/<YYYY>/<MM>/<DD>/items.json
└── raw/ (optionnel, debug)
```

#### Configuration Lambdas V2
Vérifier que les Lambdas sont configurées pour :
- Scanner les clients actifs si event est vide/minimal
- Utiliser les variables d'environnement standard :
  - ENV=dev
  - CONFIG_BUCKET=vectora-inbox-config-dev
  - DATA_BUCKET=vectora-inbox-data-dev
  - BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
  - BEDROCK_REGION=us-east-1

### Livrables Phase 1
- [ ] Consolidation dans le document final unique

---

## Phase 2 – Run Ingestion V2 Réel

### Préparation Invocation

#### Script d'Invocation
Si disponible, utiliser : `scripts/invoke_ingest_v2_lambda.py`  
Sinon, documenter la commande CLI exacte :

```powershell
# Configuration environnement
$env:AWS_PROFILE = "rag-lai-prod"
$env:AWS_DEFAULT_REGION = "eu-west-3"

# Invocation Lambda
aws lambda invoke `
  --function-name vectora-inbox-ingest-v2-dev `
  --payload '{"client_id": "lai_weekly_v4"}' `
  --cli-binary-format raw-in-base64-out `
  response.json
```

### Exécution et Collecte

#### Métriques à Capturer
- [ ] **Timestamp début/fin** d'exécution
- [ ] **Durée totale** d'exécution
- [ ] **Nombre d'items ingérés** (total)
- [ ] **Sources utilisées** (domaines, RSS, APIs)
- [ ] **Chemin S3 exact** du fichier généré
- [ ] **Taille du fichier** items.json généré
- [ ] **Logs CloudWatch** (erreurs, warnings, infos)

#### Analyse Immédiate
- [ ] Télécharger le fichier `ingested/lai_weekly_v4/<date>/items.json`
- [ ] Vérifier la structure JSON (conformité au schéma attendu)
- [ ] Compter les items par source
- [ ] Identifier les domaines les plus représentés

### Livrables Phase 2
- [ ] Consolidation dans le document final unique

---

## Phase 3 – Run Normalize_Score V2 Réel

### Préparation Invocation

#### Commande CLI
```powershell
# Configuration environnement
$env:AWS_PROFILE = "rag-lai-prod"
$env:AWS_DEFAULT_REGION = "eu-west-3"

# Invocation Lambda normalize_score
aws lambda invoke `
  --function-name vectora-inbox-normalize-score-v2-dev `
  --payload '{"client_id": "lai_weekly_v4"}' `
  --cli-binary-format raw-in-base64-out `
  response_normalize.json
```

### Exécution et Collecte

#### Métriques à Capturer
- [ ] **Timestamp début/fin** d'exécution
- [ ] **Durée totale** d'exécution (attendu : ~2-3 minutes pour 15-20 items)
- [ ] **Nombre d'items traités** (input depuis ingested/)
- [ ] **Nombre d'items normalisés** (output vers curated/)
- [ ] **Nombre d'items matchés** par domaine de veille
- [ ] **Nombre d'appels Bedrock** (normalisation + matching)
- [ ] **Chemin S3 exact** du fichier curated généré

#### Analyse Bedrock
- [ ] **Appels de normalisation** : nombre et succès
- [ ] **Appels de matching** : nombre par domaine
- [ ] **Temps de réponse Bedrock** moyen
- [ ] **Erreurs Bedrock** éventuelles (rate limiting, timeouts)

#### Distribution des Résultats
- [ ] **Items par domaine** :
  - tech_lai_ecosystem : X items
  - Autres domaines : W items
- [ ] **Distribution des scores** :
  - Score moyen par domaine
  - Score min/max global
  - Items avec score > 0.5 (haute confiance)

### Livrables Phase 3
- [ ] Consolidation dans le document final unique

---

## Phase 4 – Run Newsletter V2 Réel ✅ **NOUVEAU**

### Préparation Invocation

#### Commande CLI
```powershell
# Configuration environnement
$env:AWS_PROFILE = "rag-lai-prod"
$env:AWS_DEFAULT_REGION = "eu-west-3"

# Invocation Lambda newsletter
aws lambda invoke `
  --function-name vectora-inbox-newsletter-v2-dev `
  --payload '{"client_id": "lai_weekly_v4", "target_date": "2025-12-21", "force_regenerate": false}' `
  --cli-binary-format raw-in-base64-out `
  response_newsletter.json
```

### Exécution et Collecte

#### Métriques à Capturer
- [ ] **Timestamp début/fin** d'exécution
- [ ] **Durée totale** d'exécution (attendu : ~2-3 minutes)
- [ ] **Nombre d'items traités** (input depuis curated/)
- [ ] **Nombre d'items sélectionnés** pour newsletter
- [ ] **Mode de lecture** : vérifier latest_run_only vs period_based
- [ ] **Nombre d'appels Bedrock** (TL;DR + introduction)
- [ ] **Chemins S3 exacts** des fichiers newsletter générés

#### Analyse Bedrock Newsletter
- [ ] **Appels TL;DR** : nombre et succès
- [ ] **Appels introduction** : nombre et succès
- [ ] **Temps de réponse Bedrock** moyen
- [ ] **Erreurs Bedrock** éventuelles

#### Distribution Newsletter
- [ ] **Items par section** :
  - top_signals : X items
  - partnerships_deals : Y items
  - regulatory_updates : Z items
  - clinical_updates : W items
- [ ] **Métadonnees sélection** :
  - Trimming appliqué : oui/non
  - Événements critiques préservés : X
  - Efficacité matching : X%

### Livrables Phase 4
- [ ] Consolidation dans le document final unique

---

## Phase 5 – Analyse S3 (Ingested + Curated + Newsletter)

### Téléchargement des Fichiers

#### Fichiers Clés à Analyser
- [ ] **Input :** `s3://vectora-inbox-data-dev/ingested/lai_weekly_v4/<date>/items.json`
- [ ] **Intermediate :** `s3://vectora-inbox-data-dev/curated/lai_weekly_v4/<date>/items.json`
- [ ] **Output :** `s3://vectora-inbox-newsletters-dev/lai_weekly_v4/<date>/newsletter.md`
- [ ] **Output :** `s3://vectora-inbox-newsletters-dev/lai_weekly_v4/<date>/newsletter.json`
- [ ] **Output :** `s3://vectora-inbox-newsletters-dev/lai_weekly_v4/<date>/manifest.json`

#### Commandes de Téléchargement
```powershell
# Téléchargement fichier ingested
aws s3 cp s3://vectora-inbox-data-dev/ingested/lai_weekly_v4/<date>/items.json ./analysis/ingested_items.json --profile rag-lai-prod

# Téléchargement fichier curated  
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v4/<date>/items.json ./analysis/curated_items.json --profile rag-lai-prod

# Téléchargement fichiers newsletter
aws s3 cp s3://vectora-inbox-newsletters-dev/lai_weekly_v4/<date>/newsletter.md ./analysis/newsletter.md --profile rag-lai-prod
aws s3 cp s3://vectora-inbox-newsletters-dev/lai_weekly_v4/<date>/newsletter.json ./analysis/newsletter.json --profile rag-lai-prod
aws s3 cp s3://vectora-inbox-newsletters-dev/lai_weekly_v4/<date>/manifest.json ./analysis/manifest.json --profile rag-lai-prod
```

### Analyse Comparative Complète

#### Structure des Données
- [ ] **Schéma ingested** : Vérifier les champs obligatoires (id, title, content, source, etc.)
- [ ] **Schéma curated** : Vérifier l'ajout des champs de normalisation et matching
- [ ] **Schéma newsletter** : Vérifier la structure finale (sections, items sélectionnés, métadonnees)
- [ ] **Évolution des champs** : Documenter les transformations appliquées à chaque étape

#### Métriques de Transformation Complètes
- [ ] **Taux de conservation ingest → curated** : Items ingested → Items curated
- [ ] **Taux de sélection curated → newsletter** : Items curated → Items newsletter
- [ ] **Taux global ingest → newsletter** : Items ingested → Items newsletter
- [ ] **Items filtrés** : Raisons d'exclusion à chaque étape
- [ ] **Enrichissement** : Nouveaux champs ajoutés par chaque Lambda

#### Validation Qualité Newsletter
- [ ] **Cohérence éditoriale** : Newsletter lisible et structurée
- [ ] **Complétude sections** : Toutes les sections remplies selon config
- [ ] **Qualité TL;DR** : Résumé global pertinent
- [ ] **Qualité introduction** : Introduction engageante et informative

### Livrables Phase 5
- [ ] Consolidation dans le document final unique

---

## Phase 6 – Analyse Détaillée des Items

### Analyse Item par Item

#### Échantillonnage
- [ ] **Sélection représentative** : 5-10 items par domaine de veille
- [ ] **Cas limites** : Items avec scores très hauts/bas
- [ ] **Diversité des sources** : Couvrir différents types de contenu

#### Analyse par Item avec Statut Newsletter

##### Qualité de la Normalisation
- [ ] **Title normalisé** : Pertinence et clarté
- [ ] **Summary généré** : Fidélité au contenu original
- [ ] **Keywords extraits** : Représentativité du sujet
- [ ] **Metadata enrichis** : Complétude et exactitude

##### Qualité du Matching
- [ ] **Domaine assigné** : Cohérence avec le contenu
- [ ] **Score de pertinence** : Justification du niveau
- [ ] **Faux positifs** : Items mal catégorisés
- [ ] **Faux négatifs** : Items manqués dans leur domaine

##### Statut Newsletter ✅ **NOUVEAU**
- [ ] **Sélectionné newsletter** : Oui/Non avec justification
- [ ] **Section assignée** : top_signals, partnerships_deals, etc.
- [ ] **Rang dans section** : Position selon tri (score/date)
- [ ] **Raison exclusion** : Si non sélectionné (score trop bas, trimming, etc.)

#### Analyse par Domaine de Veille

##### tech_lai_ecosystem
- [ ] **Couverture** : IA, ML, LLM, outils tech
- [ ] **Précision** : Éviter les sujets génériques tech
- [ ] **Actualité** : Nouveautés et innovations

##### regulatory_lai
- [ ] **Couverture** : Réglementations, compliance, éthique
- [ ] **Géographie** : EU AI Act, réglementations nationales
- [ ] **Secteurs** : Finance, santé, transport

##### partnerships_lai
- [ ] **Couverture** : Alliances, acquisitions, collaborations
- [ ] **Acteurs** : Entreprises, institutions, startups
- [ ] **Impact** : Stratégique vs opérationnel

### Métriques de Qualité

#### Scoring Distribution
- [ ] **Par domaine** : Score moyen, médian, écart-type
- [ ] **Seuils critiques** : Items > 0.7 (très pertinents), < 0.3 (bruit)
- [ ] **Cohérence** : Scores similaires pour contenus similaires

#### Matching Accuracy
- [ ] **Précision** : % d'items correctement catégorisés
- [ ] **Rappel** : % d'items pertinents effectivement trouvés
- [ ] **F1-Score** : Métrique combinée de performance

### Livrables Phase 6
- [ ] Consolidation dans le document final unique

---

## Phase 7 – Métriques, Coûts, Performance

### Métriques de Performance

#### Temps d'Exécution Complet
- [ ] **Ingest Lambda** : Durée totale et par étape
- [ ] **Normalize_Score Lambda** : Durée totale et par item
- [ ] **Newsletter Lambda** : Durée totale et par étape
- [ ] **Workflow complet** : Temps total ingest → newsletter
- [ ] **Goulots d'étranglement** : Identification des étapes lentes

#### Volumétrie Complète
- [ ] **Items traités** : Nombre total par phase
- [ ] **Taux de succès** : % d'items complètement traités
- [ ] **Débit** : Items/minute pour chaque Lambda
- [ ] **Efficacité globale** : Items ingested → Items newsletter

### Analyse des Coûts

#### Coûts Bedrock Complets
- [ ] **Appels de normalisation** : Nombre × coût unitaire
- [ ] **Appels de matching** : Nombre × coût unitaire par domaine
- [ ] **Appels newsletter** : TL;DR + introduction × coût unitaire
- [ ] **Tokens consommés** : Input + Output tokens par type d'appel
- [ ] **Estimation mensuelle** : Projection pour usage régulier (4 runs/mois)

#### Coûts AWS Complets
- [ ] **Lambda execution** : Durée × coût compute (3 Lambdas)
- [ ] **S3 storage** : Taille des fichiers × coût stockage (3 buckets)
- [ ] **S3 requests** : GET/PUT × coût requêtes
- [ ] **CloudWatch logs** : Volume × coût logging

#### Calcul ROI
- [ ] **Coût par item traité** : Coût total / nombre d'items
- [ ] **Coût par item pertinent** : Coût total / items avec score > 0.5
- [ ] **Comparaison manuelle** : Estimation du coût équivalent en traitement humain

### Métriques Business

#### Qualité du Signal
- [ ] **Signal/Bruit ratio** : Items pertinents vs total
- [ ] **Couverture domaines** : % de sujets importants capturés
- [ ] **Fraîcheur** : Délai entre publication et traitement

#### Readiness Production
- [ ] **Volume cible** : Nombre d'items pour newsletter hebdomadaire
- [ ] **Diversité** : Répartition équilibrée entre domaines
- [ ] **Qualité éditoriale** : Newsletter prête pour publication
- [ ] **Stabilité workflow** : Reproductibilité et fiabilité

### Livrables Phase 7
- [ ] Consolidation dans le document final unique

---

## Phase 8 – Document de Feedback Moteur ✅ **NOUVEAU**

### Objectif
Générer un document de synthèse structuré permettant à l'utilisateur de donner un feedback précis à Q sur les décisions du moteur Vectora-Inbox, dans le but d'améliorer les filtres, scores, exclusions et prompts.

### Structure du Document de Feedback

#### Section 1 : Vue d'Ensemble du Run
```markdown
# Feedback Moteur Vectora-Inbox - Run lai_weekly_v4 du [DATE]

## Métriques Globales
- **Items ingérés** : X items
- **Items normalisés** : Y items (Z% de conservation)
- **Items matchés** : W items (V% de matching)
- **Items sélectionnés newsletter** : U items (T% de sélection)
- **Coût total** : $X.XX
- **Temps total** : X minutes

## Évaluation Globale
✅ **D'ACCORD** / ❌ **PAS D'ACCORD** avec la performance globale du moteur

**Justification :**
[Espace pour commentaire utilisateur]
```

#### Section 2 : Analyse Détaillée par Item
Pour chaque item traité, générer :

```markdown
### Item #X : [TITRE]

**Source :** [URL/Domaine]  
**Date :** [Date publication]  

#### Décisions Moteur
- **Normalisé** : ✅ Oui / ❌ Non
- **Domaine matché** : [tech_lai_ecosystem/regulatory_lai/partnerships_lai/AUCUN]
- **Score final** : X.X/20
- **Sélectionné newsletter** : ✅ Oui / ❌ Non
- **Section newsletter** : [top_signals/partnerships_deals/regulatory_updates/clinical_updates/AUCUNE]

#### Justifications Moteur
- **Matching** : [Raison du match/non-match]
- **Scoring** : [Facteurs de score : entités détectées, bonus, etc.]
- **Sélection** : [Raison inclusion/exclusion newsletter]

#### Évaluation Humaine
✅ **D'ACCORD** / ❌ **PAS D'ACCORD** avec les décisions du moteur

**Détail des désaccords :**
- [ ] Normalisation incorrecte
- [ ] Matching incorrect (mauvais domaine)
- [ ] Score trop élevé/trop bas
- [ ] Sélection newsletter incorrecte
- [ ] Autre : [préciser]

**Commentaire :**
[Espace pour commentaire détaillé]

---
```

#### Section 3 : Recommandations d'Amélioration
```markdown
## Recommandations d'Amélioration

### Filtres et Seuils
- [ ] Ajuster min_domain_score (actuel : X.X)
- [ ] Modifier seuils par domaine
- [ ] Améliorer filtrage sources

### Prompts Bedrock
- [ ] Améliorer prompt normalisation
- [ ] Affiner prompt matching [domaine]
- [ ] Optimiser prompt newsletter

### Scopes et Entités
- [ ] Enrichir scope [nom_scope]
- [ ] Ajouter entités manquantes
- [ ] Supprimer entités parasites

### Configuration Scoring
- [ ] Ajuster bonus par type d'événement
- [ ] Modifier pondération domaines
- [ ] Revoir critères événements critiques

**Commentaires généraux :**
[Espace pour recommandations générales]
```

### Génération Automatique

#### Script de Génération Complet
Créer un script Python qui :
- [ ] Lit les fichiers ingested.json, curated.json, newsletter.json
- [ ] Extrait les décisions moteur pour chaque item
- [ ] Consolide toutes les métriques des 8 phases
- [ ] Génère le document markdown unique structuré
- [ ] Inclut les justifications des scores et matchs
- [ ] Prépare les cases à cocher pour feedback humain
- [ ] Intègre l'analyse complète du workflow E2E

#### Informations à Extraire
Pour chaque item :
- [ ] **Identité** : titre, URL, source, date
- [ ] **Normalisation** : entités détectées, keywords, classification
- [ ] **Matching** : domaines matchés, scores par domaine, raisons
- [ ] **Scoring** : score final, facteurs contributeurs, bonus appliqués
- [ ] **Sélection** : statut newsletter, section, rang, raison exclusion

### Livrables Phase 8
- [ ] **Script :** `scripts/generate_feedback_document.py`
- [ ] **Document final unique :** `docs/diagnostics/lai_weekly_v4_e2e_feedback_moteur_complet.md`

### Évaluation Readiness Newsletter

#### Critères de Validation
- [ ] **Volume suffisant** : 15-25 items pertinents par semaine
- [ ] **Qualité éditoriale** : Items prêts pour curation humaine minimale
- [ ] **Diversité thématique** : Couverture équilibrée des 3 domaines
- [ ] **Fiabilité technique** : Workflow stable et reproductible

#### Structure Données pour Newsletter
- [ ] **Champs requis** : Tous présents et bien formatés
- [ ] **Métadonnées** : Suffisantes pour génération automatique
- [ ] **Scoring** : Utilisable pour priorisation éditoriale
- [ ] **Grouping** : Possibilité de regroupement par thème/domaine

### Recommandations Techniques

#### Optimisations Immédiates
- [ ] **Performance** : Goulots identifiés et solutions proposées
- [ ] **Coûts** : Optimisations possibles sans impact qualité
- [ ] **Monitoring** : Métriques à surveiller en production

#### Améliorations Futures
- [ ] **Matching accuracy** : Pistes d'amélioration des prompts
- [ ] **Sources** : Nouvelles sources à intégrer
- [ ] **Automation** : Étapes automatisables supplémentaires

### Plan de Déploiement Newsletter

#### Prérequis Techniques
- [ ] **Lambda newsletter** : Spécifications fonctionnelles
- [ ] **Template generation** : Format de sortie (HTML, Markdown)
- [ ] **Distribution** : Mécanisme d'envoi (SES, API externe)

#### Timeline Recommandée
- [ ] **Semaine 1** : Développement Lambda newsletter
- [ ] **Semaine 2** : Tests E2E complets avec génération
- [ ] **Semaine 3** : Validation éditoriale et ajustements
- [ ] **Semaine 4** : Déploiement production et première newsletter

### Livrables Phase 7
- [ ] **Fichier :** `docs/diagnostics/lai_weekly_v4_e2e_final_assessment.md`
- [ ] Validation complète de la readiness newsletter
- [ ] Recommandations techniques prioritaires
- [ ] Plan de déploiement détaillé
- [ ] Métriques de succès pour le suivi production

---

## Checklist Finale

### Validation Technique
- [ ] Workflow complet ingest → normalize_score fonctionnel
- [ ] Données structurées correctement dans S3
- [ ] Performance acceptable (< 5 min total)
- [ ] Coûts maîtrisés (< 2€ par exécution)

### Validation Business
- [ ] Volume suffisant d'items pertinents
- [ ] Qualité de matching satisfaisante (> 70% précision)
- [ ] Couverture des 3 domaines de veille
- [ ] Prêt pour curation éditoriale légère

### Validation Opérationnelle
- [ ] Logs et monitoring en place
- [ ] Gestion d'erreurs robuste
- [ ] Documentation complète
- [ ] Plan de déploiement newsletter validé

---

**Durée totale estimée :** 5h45 minutes  
**Livrables :** 7 fichiers de diagnostic + 1 synthèse finale  
**Décision finale :** GO/NO-GO pour développement Lambda newslettere rag-lai-prod_v3/<date>/items.json ./analysis/curated_items.json --profile rag-lai-prod
```

### Analyse Comparative

#### Structure et Schéma
- [ ] **Champs ingested** : titre, url, content, source, timestamp, etc.
- [ ] **Champs curated** : + normalized_content, matched_domains, scores, etc.
- [ ] **Conformité schéma** : validation des champs obligatoires
- [ ] **Évolution des données** : transformation ingested → curated

#### Métriques de Transformation
- [ ] **Taux de conservation** : items ingested vs curated
- [ ] **Taux de matching** : items matchés vs total
- [ ] **Qualité normalisation** : cohérence des champs normalisés
- [ ] **Distribution géographique** : sources par pays/région

### Livrables Phase 4
- [ ] **Fichier :** `docs/diagnostics/lai_weekly_v3_e2e_s3_analysis.md`
- [ ] Comparaison détaillée ingested vs curated
- [ ] Métriques de transformation
- [ ] Validation de la conformité schéma
- [ ] Fichiers JSON téléchargés dans `./analysis/`

---

## Phase 5 – Analyse Détaillée des Items (Micro-niveau)

### Sélection d'Items Représentatifs

#### Critères de Sélection
- [ ] **2-3 items** avec score élevé (> 0.7) par domaine principal
- [ ] **2-3 items** avec score moyen (0.3-0.7)
- [ ] **2-3 items** avec score faible (< 0.3) ou rejetés
- [ ] **1-2 items** borderline ou ambigus

#### Analyse Item par Item
Pour chaque item sélectionné, documenter :

**Identification :**
- [ ] Titre original
- [ ] URL source
- [ ] Domaine/source d'origine
- [ ] Timestamp d'ingestion

**Contenu Normalisé :**
- [ ] Entreprises détectées (ex: MedinCell, Nanexa)
- [ ] Molécules/produits détectés (ex: UZEDY®, palipéridone)
- [ ] Technologies détectées (ex: LAI, depot injection)
- [ ] Événements détectés (ex: approbation FDA, partenariat)

**Matching et Scoring :**
- [ ] Domaines de veille matchés (tech_lai_ecosystem, regulatory_lai, etc.)
- [ ] Score par domaine + justification
- [ ] Score global de l'item
- [ ] Raison de l'acceptation/rejet selon les prompts et scopes

**Évaluation Qualitative :**
- [ ] **Pertinence métier** : l'item est-il réellement pertinent pour LAI weekly ?
- [ ] **Précision matching** : les domaines matchés sont-ils corrects ?
- [ ] **Cohérence scoring** : le score reflète-t-il la pertinence ?
- [ ] **Faux positifs/négatifs** : erreurs de classification détectées ?

### Patterns et Tendances

#### Analyse Transversale
- [ ] **Mots-clés récurrents** dans les items bien scorés
- [ ] **Sources privilégiées** (domaines avec meilleur matching)
- [ ] **Seuils optimaux** : les seuils config actuels sont-ils adaptés ?
- [ ] **Bruit identifié** : types d'items non pertinents qui passent

### Livrables Phase 5
- [ ] **Fichier :** `docs/diagnostics/lai_weekly_v3_e2e_items_breakdown_v2.md`
- [ ] Analyse détaillée de 8-10 items représentatifs
- [ ] Évaluation qualitative de la pertinence
- [ ] Identification des patterns et tendances
- [ ] Recommandations d'ajustement des seuils

---

## Phase 6 – Métriques, Coûts, Performance

### Calcul des Métriques

#### Volumes et Taux
- [ ] **Items ingérés** : nombre total
- [ ] **Items normalisés** : nombre traité par normalize_score
- [ ] **Items matchés** : nombre avec au moins un domaine
- [ ] **Taux de conservation** : normalisés/ingérés (%)
- [ ] **Taux de matching** : matchés/normalisés (%)
- [ ] **Distribution par domaine** :
  - tech_lai_ecosystem : X items (Y%)
  - regulatory_lai : X items (Y%)
  - partnerships_lai : X items (Y%)

#### Performance Technique
- [ ] **Temps d'exécution ingest** : X minutes
- [ ] **Temps d'exécution normalize_score** : Y minutes
- [ ] **Temps total pipeline** : X + Y minutes
- [ ] **Throughput** : items/minute
- [ ] **Mémoire utilisée** : pics par Lambda

### Calcul des Coûts Bedrock

#### Appels et Tokens
- [ ] **Nombre d'appels normalisation** : X appels
- [ ] **Nombre d'appels matching** : Y appels (par domaine)
- [ ] **Total appels Bedrock** : X + Y appels
- [ ] **Tokens estimés** par appel (input + output)
- [ ] **Total tokens** consommés

#### Estimation Financière
Basé sur les prix Bedrock Claude-3-Sonnet (us-east-1) :
- [ ] **Coût par token input** : $0.003 / 1K tokens
- [ ] **Coût par token output** : $0.015 / 1K tokens
- [ ] **Coût total par run** : $X.XX
- [ ] **Coût mensuel estimé** (4 runs/mois) : $Y.YY
- [ ] **Coût annuel estimé** : $Z.ZZ

### Analyse Qualité vs Bruit

#### Évaluation de la Pertinence
- [ ] **Items hautement pertinents** (score > 0.7) : X items
- [ ] **Items moyennement pertinents** (0.3-0.7) : Y items  
- [ ] **Items faiblement pertinents** (< 0.3) : Z items
- [ ] **Faux positifs identifiés** : items non pertinents mais bien scorés
- [ ] **Faux négatifs identifiés** : items pertinents mais mal scorés

#### Recommandations Seuils
- [ ] **Seuils actuels** dans lai_weekly_v3.yaml
- [ ] **Seuils optimaux suggérés** basés sur l'analyse
- [ ] **Impact estimé** des ajustements de seuils
- [ ] **Trade-offs** : précision vs rappel

### Livrables Phase 6
- [ ] **Fichier :** `docs/diagnostics/lai_weekly_v3_e2e_metrics_and_costs_v2.md`
- [ ] Métriques complètes de volume et performance
- [ ] Calcul détaillé des coûts Bedrock
- [ ] Analyse qualité vs bruit
- [ ] Recommandations d'optimisation des seuils

---

## Phase 7 – Synthèse & Recommandations Newsletter

### Évaluation Readiness Newsletter

#### Flux Technique
**Question :** Les sorties de normalize_score_v2 sont-elles prêtes pour la Lambda newsletter ?

**Critères d'évaluation :**
- [ ] **Structure JSON** : champs obligatoires présents et bien formés
- [ ] **Champs essentiels** pour newsletter :
  - titre, url, content normalisé ✓/✗
  - domaines matchés avec scores ✓/✗
  - timestamp, source, metadata ✓/✗
- [ ] **Qualité des données** : contenu exploitable pour génération newsletter
- [ ] **Chemins S3** : structure curated/ compatible avec lecture par newsletter Lambda
- [ ] **Format de sortie** : JSON parsable et structuré

#### Flux Métier
**Question :** Les signaux détectés sont-ils cohérents avec le scope lai_weekly_v3 ?

**Critères d'évaluation :**
- [ ] **Entités LAI** correctement détectées :
  - MedinCell, Nanexa, Janssen, etc. ✓/✗
  - UZEDY®, Invega Sustenna, etc. ✓/✗
- [ ] **Domaines de veille** pertinents :
  - tech_lai_ecosystem : innovations, R&D ✓/✗
  - regulatory_lai : approbations, guidelines ✓/✗
  - partnerships_lai : collaborations, M&A ✓/✗
- [ ] **Niveau de bruit** acceptable pour newsletter professionnelle
- [ ] **Couverture** : pas de gaps majeurs dans la veille

### Identification des Risques

#### Risques Techniques
- [ ] **Dépendance S3** : que se passe-t-il si curated/ est vide ?
- [ ] **Format évolutif** : compatibilité si schéma curated change ?
- [ ] **Performance** : temps de lecture curated/ acceptable ?
- [ ] **Concurrence** : gestion si newsletter et normalize_score simultanés ?

#### Risques Métier
- [ ] **Qualité variable** : items de qualité hétérogène dans curated/
- [ ] **Seuils inadaptés** : trop/pas assez d'items pour newsletter
- [ ] **Biais sources** : sur-représentation de certains domaines
- [ ] **Fraîcheur** : délai entre événement et newsletter acceptable ?

### Recommandations d'Amélioration

#### Ajustements Configuration (à traiter plus tard)
- [ ] **Prompts** : améliorations suggérées pour réduire le bruit
- [ ] **Seuils** : ajustements min_domain_score par domaine
- [ ] **Sources** : ajout/suppression de sources dans source_catalog
- [ ] **Scopes** : enrichissement des entités dans canonical/scopes/

#### Préparation Newsletter Lambda
- [ ] **Contrat d'interface** : définir le format d'entrée newsletter
- [ ] **Configuration newsletter** : valider newsletter_layout dans client config
- [ ] **Templates** : préparer les templates de génération
- [ ] **Tests** : définir les critères de validation newsletter

### Conclusion et Go/No-Go

#### Critères de Décision
**✅ GO - Prêt pour newsletter Lambda :**
- Structure curated/ exploitable
- Qualité des données acceptable (< 20% bruit)
- Performance technique satisfaisante
- Risques identifiés et maîtrisables

**❌ NO-GO - Pas encore prêt :**
- Structure curated/ incomplète ou incohérente
- Trop de bruit (> 30% items non pertinents)
- Performance technique insuffisante
- Risques bloquants non résolus

#### Priorisation des Actions
**P0 - Bloquant :** actions obligatoires avant newsletter Lambda  
**P1 - Important :** améliorations recommandées à court terme  
**P2 - Optimisation :** améliorations à moyen terme  

### Livrables Phase 7
- [ ] **Fichier :** `docs/diagnostics/lai_weekly_v3_e2e_readiness_assessment_report.md`
- [ ] Évaluation complète flux technique et métier
- [ ] Identification et analyse des risques
- [ ] Recommandations priorisées d'amélioration
- [ ] **Décision finale GO/NO-GO** avec justification détaillée

---

## Planning et Ressources

### Timeline Estimée
**Durée totale :** 7h15 (réparties sur 1-2 jours)

| Phase | Durée | Dépendances |
|-------|-------|-------------|
| Phase 1 | 30min | - |
| Phase 2 | 45min | Phase 1 ✓ |
| Phase 3 | 60min | Phase 2 ✓ |
| Phase 4 | 45min | Phase 3 ✓ |
| Phase 5 | 60min | Phase 4 ✓ |
| Phase 6 | 90min | Phase 5 ✓ |
| Phase 7 | 60min | Phase 6 ✓ |
| Phase 8 | 75min | Phase 7 ✓ |

### Ressources Nécessaires
- [ ] **Accès AWS** : profil rag-lai-prod configuré
- [ ] **Permissions** : lecture S3, invocation Lambda, lecture CloudWatch
- [ ] **Outils** : AWS CLI, éditeur de texte, calculatrice coûts
- [ ] **Espace disque** : ~50MB pour téléchargement fichiers JSON

### Livrables Finaux
1. **Plan d'évaluation** : ce document
2. **Document final unique** : synthèse complète avec feedback moteur
3. **Script de génération feedback** : outil réutilisable

---

## Critères de Succès

### Objectifs Mesurables
- [ ] **Pipeline E2E validé** : ingest → normalize_score → newsletter fonctionnel
- [ ] **Métriques collectées** : volumes, coûts, performance documentés
- [ ] **Qualité évaluée** : ratio signal/bruit quantifié à chaque étape
- [ ] **Document feedback généré** : prêt pour validation humaine et amélioration moteur

### Livrables de Qualité
- [ ] **Document unique complet** : synthèse structurée de toutes les phases
- [ ] **Données factuelles** : métriques précises et vérifiables
- [ ] **Analyse objective** : évaluation basée sur critères mesurables
- [ ] **Feedback actionnable** : document structuré pour amélioration moteur

### Impact Métier
- [ ] **Confiance technique** : validation de la stabilité du workflow complet V2
- [ ] **Visibilité coûts** : estimation précise des coûts opérationnels
- [ ] **Amélioration continue** : mécanisme de feedback pour optimisation moteur
- [ ] **Readiness production** : validation complète pour déploiement

---

*Plan d'Évaluation E2E Complet lai_weekly_v4 - Version 3.0*  
*Créé le : 21 décembre 2025*  
*Statut : Prêt pour exécution - Test workflow complet avec document de feedback moteur*