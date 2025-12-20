# Plan d'Évaluation E2E - lai_weekly_v4 Readiness Assessment

**Date :** 19 décembre 2025  
**Version :** 2.0  
**Objectif :** Évaluer le workflow Vectora Inbox V2 existant sur données réelles pour lai_weekly_v4  
**Contrainte :** AUCUNE modification de code, config, infra ou Lambdas autorisée  

---

## Périmètre du Test

### Lambdas Concernées
- **vectora-inbox-ingest-v2-dev** (handler: src_v2/lambdas/ingest/handler.py)
- **vectora-inbox-normalize-score-v2-dev** (handler: src_v2/lambdas/normalize_score/handler.py)

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

### 1. Vérification Flux Technique
Confirmer que le workflow complet fonctionne sur données réelles :
```
ingest_v2 → S3 ingested/lai_weekly_v4/YYYY/MM/DD/items.json 
         → normalize_score_v2 → S3 curated/lai_weekly_v4/YYYY/MM/DD/items.json
```

### 2. Validation Préparation Newsletter
Vérifier que les items scorés/matchés dans curated/ sont structurés et prêts pour consommation par une future Lambda newsletter (champs, format, chemins S3).

### 3. Métriques et Performance
Mesurer :
- Volumes traités (items ingérés vs normalisés vs matchés)
- Matching rate par domaine de veille
- Distribution des scores
- Coûts Bedrock (nombre d'appels, estimation financière)
- Temps d'exécution des Lambdas
- Ratio bruit vs pertinence

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

## Structure du Plan - 7 Phases

### Phase 1 – Préparation & Sanity Check
**Durée estimée :** 30 minutes  
**Objectif :** Vérifier l'état de l'environnement sans rien modifier

### Phase 2 – Run Ingestion Réel  
**Durée estimée :** 45 minutes  
**Objectif :** Exécuter ingest_v2 pour lai_weekly_v4 et analyser les résultats

### Phase 3 – Run Normalize_Score Réel
**Durée estimée :** 60 minutes  
**Objectif :** Exécuter normalize_score_v2 et analyser la normalisation/scoring

### Phase 4 – Analyse S3 (Ingested + Curated)
**Durée estimée :** 45 minutes  
**Objectif :** Examiner la structure et le contenu des fichiers S3 générés

### Phase 5 – Analyse Détaillée des Items
**Durée estimée :** 90 minutes  
**Objectif :** Analyser item par item la qualité du matching et scoring

### Phase 6 – Métriques, Coûts, Performance
**Durée estimée :** 60 minutes  
**Objectif :** Calculer les métriques de performance et coûts

### Phase 7 – Synthèse & Recommandations Newsletter
**Durée estimée :** 45 minutes  
**Objectif :** Évaluer la readiness pour la 3ème Lambda newsletter

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
- [ ] **Fichier :** `docs/diagnostics/lai_weekly_v4_e2e_phase1_observations.md`
- [ ] Statut de chaque fichier de référence
- [ ] Confirmation de la configuration lai_weekly_v4
- [ ] Validation de la structure S3 attendue
- [ ] État des Lambdas V2 (dernière exécution, logs récents)

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
- [ ] **Fichier :** `docs/diagnostics/lai_weekly_v4_e2e_ingest_observation.md`
- [ ] Commande d'invocation utilisée
- [ ] Métriques d'exécution complètes
- [ ] Analyse préliminaire du contenu ingéré
- [ ] Chemin S3 exact pour la phase suivante

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
- [ ] **Fichier :** `docs/diagnostics/lai_weekly_v4_e2e_normalize_observation.md`
- [ ] Métriques d'exécution complètes
- [ ] Analyse des appels Bedrock
- [ ] Distribution détaillée des résultats
- [ ] Chemin S3 du fichier curated pour analyse

---

## Phase 4 – Analyse S3 (Ingested + Curated)

### Téléchargement des Fichiers

#### Fichiers Clés à Analyser
- [ ] **Input :** `s3://vectora-inbox-data-dev/ingested/lai_weekly_v4/<date>/items.json`
- [ ] **Output :** `s3://vectora-inbox-data-dev/curated/lai_weekly_v4/<date>/items.json`

#### Commandes de Téléchargement
```powershell
# Téléchargement fichier ingested
aws s3 cp s3://vectora-inbox-data-dev/ingested/lai_weekly_v4/<date>/items.json ./analysis/ingested_items.json --profile rag-lai-prod

# Téléchargement fichier curated  
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v4/<date>/items.json ./analysis/curated_items.json --profile rag-lai-prod
```

### Analyse Comparative

#### Structure des Données
- [ ] **Schéma ingested** : Vérifier les champs obligatoires (id, title, content, source, etc.)
- [ ] **Schéma curated** : Vérifier l'ajout des champs de normalisation et matching
- [ ] **Évolution des champs** : Documenter les transformations appliquées

#### Métriques de Transformation
- [ ] **Taux de conservation** : Items ingested → Items curated
- [ ] **Items filtrés** : Raisons d'exclusion (qualité, pertinence)
- [ ] **Enrichissement** : Nouveaux champs ajoutés par la normalisation

#### Validation Qualité
- [ ] **Cohérence des données** : Pas de corruption lors des transformations
- [ ] **Complétude** : Tous les champs requis sont présents
- [ ] **Format** : Conformité JSON et encodage UTF-8

### Livrables Phase 4
- [ ] **Fichier :** `docs/diagnostics/lai_weekly_v4_e2e_s3_analysis.md`
- [ ] Comparaison détaillée ingested vs curated
- [ ] Métriques de transformation
- [ ] Validation de la qualité des données
- [ ] Fichiers téléchargés dans `./analysis/` pour phases suivantes

---

## Phase 5 – Analyse Détaillée des Items

### Analyse Item par Item

#### Échantillonnage
- [ ] **Sélection représentative** : 5-10 items par domaine de veille
- [ ] **Cas limites** : Items avec scores très hauts/bas
- [ ] **Diversité des sources** : Couvrir différents types de contenu

#### Grille d'Évaluation par Item

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

### Livrables Phase 5
- [ ] **Fichier :** `docs/diagnostics/lai_weekly_v4_e2e_items_analysis.md`
- [ ] Grille d'évaluation complétée pour chaque item échantillon
- [ ] Métriques de qualité par domaine
- [ ] Identification des patterns de succès/échec
- [ ] Recommandations d'amélioration du matching

---

## Phase 6 – Métriques, Coûts, Performance

### Métriques de Performance

#### Temps d'Exécution
- [ ] **Ingest Lambda** : Durée totale et par étape
- [ ] **Normalize_Score Lambda** : Durée totale et par item
- [ ] **Goulots d'étranglement** : Identification des étapes lentes

#### Volumétrie
- [ ] **Items traités** : Nombre total par phase
- [ ] **Taux de succès** : % d'items complètement traités
- [ ] **Débit** : Items/minute pour chaque Lambda

### Analyse des Coûts

#### Coûts Bedrock
- [ ] **Appels de normalisation** : Nombre × coût unitaire
- [ ] **Appels de matching** : Nombre × coût unitaire par domaine
- [ ] **Tokens consommés** : Input + Output tokens
- [ ] **Estimation mensuelle** : Projection pour usage régulier

#### Coûts AWS
- [ ] **Lambda execution** : Durée × coût compute
- [ ] **S3 storage** : Taille des fichiers × coût stockage
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

#### Readiness Newsletter
- [ ] **Volume cible** : Nombre d'items pour newsletter hebdomadaire
- [ ] **Diversité** : Répartition équilibrée entre domaines
- [ ] **Qualité éditoriale** : Items prêts pour publication

### Livrables Phase 6
- [ ] **Fichier :** `docs/diagnostics/lai_weekly_v4_e2e_metrics_costs.md`
- [ ] Dashboard de métriques de performance
- [ ] Analyse détaillée des coûts avec projections
- [ ] Calcul du ROI et comparaison avec alternatives
- [ ] Métriques business pour validation produit

---

## Phase 7 – Synthèse & Recommandations Newsletter

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
**Durée totale :** 5h45 (réparties sur 1-2 jours)

| Phase | Durée | Dépendances |
|-------|-------|-------------|
| Phase 1 | 30min | - |
| Phase 2 | 45min | Phase 1 ✓ |
| Phase 3 | 60min | Phase 2 ✓ |
| Phase 4 | 45min | Phase 3 ✓ |
| Phase 5 | 90min | Phase 4 ✓ |
| Phase 6 | 60min | Phase 5 ✓ |
| Phase 7 | 45min | Phase 6 ✓ |

### Ressources Nécessaires
- [ ] **Accès AWS** : profil rag-lai-prod configuré
- [ ] **Permissions** : lecture S3, invocation Lambda, lecture CloudWatch
- [ ] **Outils** : AWS CLI, éditeur de texte, calculatrice coûts
- [ ] **Espace disque** : ~50MB pour téléchargement fichiers JSON

### Livrables Finaux
1. **Plan d'évaluation** : ce document
2. **7 rapports de phase** : observations détaillées par phase
3. **Rapport de synthèse** : readiness assessment final avec GO/NO-GO
4. **Fichiers d'analyse** : JSON téléchargés et scripts d'analyse

---

## Critères de Succès

### Objectifs Mesurables
- [ ] **Pipeline E2E validé** : ingest → normalize_score fonctionnel
- [ ] **Métriques collectées** : volumes, coûts, performance documentés
- [ ] **Qualité évaluée** : ratio signal/bruit quantifié
- [ ] **Readiness newsletter** : décision GO/NO-GO justifiée

### Livrables de Qualité
- [ ] **Documentation complète** : 8 fichiers markdown structurés
- [ ] **Données factuelles** : métriques précises et vérifiables
- [ ] **Analyse objective** : évaluation basée sur critères mesurables
- [ ] **Recommandations actionnables** : priorisées et spécifiques

### Impact Métier
- [ ] **Confiance technique** : validation de la stabilité du moteur V2
- [ ] **Visibilité coûts** : estimation précise des coûts opérationnels
- [ ] **Roadmap claire** : prochaines étapes pour newsletter Lambda définies
- [ ] **Risques maîtrisés** : identification proactive des points d'attention

---

*Plan d'évaluation E2E lai_weekly_v3 - Version 1.0*  
*Créé le : 18 décembre 2025*  
*Statut : Prêt pour exécution*