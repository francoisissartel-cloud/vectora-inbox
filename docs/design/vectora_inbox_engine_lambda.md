# Design Document – Lambda `vectora-inbox-engine`

**Date** : 2025-01-15  
**Auteur** : Amazon Q Developer  
**Statut** : DRAFT → IMPLEMENTATION  
**Version** : 1.0

---

## 1. Contexte et objectif

### 1.1 Rôle de la Lambda engine

La Lambda `vectora-inbox-engine` transforme les items normalisés (output de `vectora-inbox-ingest-normalize`) en une newsletter structurée, lisible et "premium" pour le client.

Elle implémente les **Phases 2, 3 et 4** du workflow Vectora Inbox :
- **Phase 2 (Matching)** : Détermine quels items correspondent aux domaines d'intérêt du client (watch_domains)
- **Phase 3 (Scoring)** : Attribue un score à chaque item pour prioriser les plus importants
- **Phase 4 (Newsletter)** : Génère la newsletter finale avec l'aide d'Amazon Bedrock

### 1.2 Prérequis

**Entrée** : Items normalisés dans `s3://vectora-inbox-data-dev/normalized/<client_id>/<YYYY>/<MM>/<DD>/items.json`

**Sortie** : Newsletter Markdown dans `s3://vectora-inbox-newsletters-dev/<client_id>/<YYYY>/<MM>/<DD>/newsletter.md`

**Configurations lues** :
- Configuration client : `s3://vectora-inbox-config-dev/clients/<client_id>.yaml`
- Scopes canonical : `s3://vectora-inbox-config-dev/canonical/scopes/*.yaml`
- Règles de scoring : `s3://vectora-inbox-config-dev/canonical/scoring/scoring_rules.yaml`

---

## 2. Contrat d'entrée

### 2.1 Payload d'invocation

```json
{
  "client_id": "lai_weekly",
  "period_days": 7,
  "target_date": "2025-01-15"
}
```

**Paramètres** :
- `client_id` (obligatoire) : Identifiant du client
- `period_days` (optionnel) : Nombre de jours à analyser (défaut : 7)
- `from_date` / `to_date` (optionnel) : Fenêtre temporelle explicite
- `target_date` (optionnel) : Date de référence pour la newsletter (défaut : aujourd'hui)

### 2.2 Collecte des items normalisés

La Lambda liste les fichiers `items.json` dans la fenêtre temporelle :
```
s3://vectora-inbox-data-dev/normalized/<client_id>/<YYYY>/<MM>/<DD>/items.json
```

Exemple : pour `period_days=7` et `target_date=2025-01-15`, elle charge les items du 2025-01-08 au 2025-01-15.

---

## 3. Phase 2 – Matching (SANS Bedrock)

### 3.1 Objectif

Déterminer pour chaque item normalisé à quels `watch_domains` il appartient.

### 3.2 Processus

Pour chaque item normalisé :

1. **Charger les champs détectés** :
   - `companies_detected` (list[str])
   - `molecules_detected` (list[str])
   - `technologies_detected` (list[str])
   - `indications_detected` (list[str])

2. **Pour chaque watch_domain** défini dans la config client :
   - Charger les scopes canonical référencés (via les clés `company_scope`, `molecule_scope`, etc.)
   - Calculer les intersections :
     - `companies_detected` ∩ `company_scope`
     - `molecules_detected` ∩ `molecule_scope`
     - `technologies_detected` ∩ `technology_scope`
     - `indications_detected` ∩ `indication_scope`

3. **Décider si l'item appartient au domaine** :
   - Si au moins une intersection est non vide → l'item appartient au domaine
   - Un item peut appartenir à plusieurs domaines

4. **Annoter l'item** :
   - Ajouter un champ `matched_domains` (list[str]) contenant les IDs des domaines matchés

### 3.3 Exemple

**Item normalisé** :
```json
{
  "title": "Camurus Announces Positive Phase 3 Results for Brixadi",
  "companies_detected": ["Camurus"],
  "molecules_detected": ["Brixadi", "buprenorphine"],
  "technologies_detected": ["long acting", "depot"],
  "indications_detected": ["opioid use disorder"],
  "event_type": "clinical_update"
}
```

**Watch domain `tech_lai_ecosystem`** :
- `technology_scope`: `lai_keywords` (contient "long acting", "depot")
- `company_scope`: `lai_companies_global` (contient "Camurus")

**Résultat** : L'item est matché au domaine `tech_lai_ecosystem` car :
- `{"Camurus"}` ∩ `{"Camurus", "Alkermes", ...}` = `{"Camurus"}` (non vide)
- `{"long acting", "depot"}` ∩ `{"long acting", "depot", ...}` = `{"long acting", "depot"}` (non vide)

---

## 4. Phase 3 – Scoring (SANS Bedrock)

### 4.1 Objectif

Attribuer un score numérique à chaque item pour prioriser les plus importants.

### 4.2 Facteurs de scoring

Le score combine plusieurs facteurs (basés sur `canonical/scoring/scoring_rules.yaml`) :

1. **Importance de l'event_type** :
   - `clinical_update`: 5
   - `regulatory`: 5
   - `partnership`: 6
   - `corporate_move`: 2
   - `financial_results`: 3
   - `scientific_publication`: 3
   - `other`: 1

2. **Priorité du watch_domain** :
   - `high`: 3
   - `medium`: 2
   - `low`: 1

3. **Récence** : Décroissance exponentielle avec demi-vie de 7 jours

4. **Bonus compétiteurs clés** : +2 si l'item mentionne un compétiteur prioritaire

5. **Bonus molécules clés** : +1.5 si l'item mentionne une molécule prioritaire

6. **Type de source** :
   - `press_corporate`: 2
   - `press_sector`: 1.5
   - `generic`: 1

7. **Profondeur du signal** : +0.3 par entité pertinente détectée

### 4.3 Formule de scoring (simplifiée)

```
score = (event_type_weight * domain_priority_weight * recency_factor) 
        + competitor_bonus 
        + molecule_bonus 
        + (source_type_weight * signal_depth_bonus)
```

### 4.4 Seuils de sélection

- **Score minimum** : 10 (items en dessous sont exclus)
- **Items minimum par section** : 1 (garantit qu'une section n'est jamais vide)

---

## 5. Phase 4 – Génération de la newsletter (AVEC Bedrock)

### 5.1 Objectif

Transformer les items scorés en une newsletter structurée, lisible et "premium".

### 5.2 Sélection des items par section

Pour chaque section définie dans `newsletter_layout.sections` :

1. **Filtrer les items** :
   - Garder uniquement les items matchés aux `source_domains` de la section
   - Appliquer les filtres `filter_event_types` si présents

2. **Trier par score décroissant**

3. **Sélectionner les top N items** (selon `max_items`)

### 5.3 Contrat avec Bedrock

#### Ce que la Lambda envoie à Bedrock

Un prompt structuré contenant :

- **Liste des items sélectionnés par section** (titre, summary, score, source, URL, date, entités)
- **Contexte global** : période couverte, nombre total d'items analysés, domaines d'intérêt
- **Attentes sur le ton** : tone, voice, langue (depuis `client_profile`)
- **Structure attendue** : titre, intro, TL;DR, sections

#### Ce que la Lambda attend en retour

Une réponse structurée (JSON) contenant :

1. **Titre de la newsletter** : "Weekly Biotech Intelligence – January 15, 2025"
2. **Paragraphe d'introduction** : 2-4 phrases résumant le contexte de la semaine
3. **TL;DR** : 3-5 bullet points résumant les signaux les plus importants
4. **Pour chaque section** :
   - Texte d'introduction de la section (1-2 phrases)
   - Formulations synthétiques pour chaque item (réécriture du summary)

#### Contraintes pour Bedrock

- **Ne pas halluciner** : Se limiter aux informations présentes dans les items
- **Ne pas inventer de faits** : Pas de chiffres, dates ou noms inventés
- **Respecter la langue** : Tout le contenu doit être dans la langue du client
- **Garder les noms exacts** : Noms de sociétés, molécules, technologies conservés tels quels
- **Ton cohérent** : Respecter le tone et voice définis dans `client_profile`

### 5.4 Assemblage du Markdown

La Lambda assemble la sortie de Bedrock en un document Markdown :

```markdown
# [Titre de la newsletter]

[Paragraphe d'introduction]

## TL;DR

- [Bullet point 1]
- [Bullet point 2]
- [Bullet point 3]

---

## [Titre de la section 1]

[Texte d'introduction de la section]

**[Titre de l'item 1]**  
[Formulation synthétique]  
[Lire l'article](URL)

**[Titre de l'item 2]**  
[Formulation synthétique]  
[Lire l'article](URL)

---

## [Titre de la section 2]

...

---

*Newsletter générée par Vectora Inbox – Powered by Amazon Bedrock*
```

---

## 6. Format de sortie

### 6.1 Fichier newsletter (obligatoire)

**Emplacement** : `s3://vectora-inbox-newsletters-dev/<client_id>/<YYYY>/<MM>/<DD>/newsletter.md`

**Format** : Markdown

**Exemple** : `s3://vectora-inbox-newsletters-dev/lai_weekly/2025/01/15/newsletter.md`

### 6.2 Réponse Lambda

```json
{
  "statusCode": 200,
  "body": {
    "client_id": "lai_weekly",
    "execution_date": "2025-01-15T11:45:00Z",
    "target_date": "2025-01-15",
    "period": {
      "from_date": "2025-01-08",
      "to_date": "2025-01-15"
    },
    "items_analyzed": 138,
    "items_matched": 87,
    "items_selected": 13,
    "sections_generated": 2,
    "s3_output_path": "s3://vectora-inbox-newsletters-dev/lai_weekly/2025/01/15/newsletter.md",
    "execution_time_seconds": 28.7,
    "message": "Newsletter générée avec succès."
  }
}
```

---

## 7. Gestion des erreurs

### 7.1 Aucun item normalisé trouvé

**Comportement** : Générer une newsletter minimale avec un message explicite

**Exemple** :
```markdown
# Weekly Biotech Intelligence – January 15, 2025

No critical signals this week. We continue to monitor your domains of interest.

---

*Newsletter générée par Vectora Inbox – Powered by Amazon Bedrock*
```

### 7.2 Échec Bedrock

**Comportement** : Fallback vers une newsletter simplifiée sans réécriture Bedrock

**Exemple** : Utiliser les summaries existants des items normalisés + disclaimer "Newsletter générée en mode dégradé"

### 7.3 Configuration client invalide

**Comportement** : Lever une erreur explicite et arrêter le traitement

**Réponse** :
```json
{
  "statusCode": 400,
  "body": {
    "error": "ConfigurationError",
    "message": "Configuration client invalide : champ 'newsletter_layout' manquant"
  }
}
```

---

## 8. Plan d'implémentation par phases

### Phase A – Wiring S3 + lecture des items normalisés

**Objectif** : Mettre en place la structure de base de la Lambda

**Tâches** :
1. Créer le handler Lambda dans `src/lambdas/engine/handler.py` (déjà existant)
2. Implémenter `run_engine_for_client()` dans `src/vectora_core/__init__.py`
3. Implémenter la collecte des items normalisés depuis S3 (liste des fichiers dans la fenêtre temporelle)
4. Logs structurés : client_id, period, nb_items, etc.

**Validation** : Invoquer la Lambda et vérifier qu'elle charge correctement les items normalisés

---

### Phase B – Logique d'agrégation / sélection / scoring (sans Bedrock)

**Objectif** : Implémenter le matching et le scoring

**Tâches** :
1. Implémenter `match_items_to_domains()` dans `src/vectora_core/matching/matcher.py`
2. Implémenter `score_items()` dans `src/vectora_core/scoring/scorer.py`
3. Implémenter la sélection des top N items par section
4. Retourner un objet en mémoire représentant la "newsletter brute"

**Validation** : Vérifier que les items sont correctement matchés et scorés (logs + tests unitaires)

---

### Phase C – Intégration Bedrock / Sonnet 4.5

**Objectif** : Générer les textes éditoriaux avec Bedrock

**Tâches** :
1. Créer `src/vectora_core/newsletter/bedrock_client.py` (déjà existant)
2. Implémenter `generate_newsletter_with_bedrock()` : construction du prompt + appel Bedrock
3. Réutiliser le même mécanisme de retry/backoff que `ingest-normalize` (ThrottlingException)
4. Parser la réponse Bedrock (JSON structuré)

**Validation** : Vérifier que Bedrock génère des textes cohérents (titre, intro, TL;DR, sections)

---

### Phase D – Sortie S3 & diagnostics

**Objectif** : Écrire la newsletter finale dans S3

**Tâches** :
1. Implémenter `assemble_markdown()` dans `src/vectora_core/newsletter/formatter.py`
2. Écrire la newsletter dans `s3://vectora-inbox-newsletters-dev/<client_id>/<YYYY>/<MM>/<DD>/newsletter.md`
3. Ajouter des logs utiles : nb d'items entrants, nb d'items retenus par section, temps total, nb d'appels Bedrock

**Validation** : Télécharger la newsletter depuis S3 et vérifier le format Markdown

---

### Phase E – Tests & docs

**Objectif** : Valider le workflow complet et documenter

**Tâches** :
1. Créer un script de test dans `scripts/test-engine-lai-weekly.ps1`
2. Créer un fichier de diagnostic dans `docs/diagnostics/vectora_inbox_engine_first_run.md`
3. Mettre à jour `CHANGELOG.md`

**Validation** : Run complet `ingest-normalize` → `engine` → newsletter générée

---

## 9. Alignement avec l'existant

### 9.1 Réutilisation du code ingest-normalize

**Bedrock retry/backoff** : Réutiliser exactement le même pattern que `src/vectora_core/normalization/bedrock_client.py`

**Inference profile** : Utiliser le même `BEDROCK_MODEL_ID` = `eu.anthropic.claude-sonnet-4-5-20250929-v1:0`

**Logs structurés** : Même format que `ingest-normalize` (client_id, execution_date, etc.)

### 9.2 Respect de la structure du repo

**Code source** : `src/vectora_core/` (logique métier) + `src/lambdas/engine/` (handler Lambda)

**Infra** : Déjà définie dans `infra/s1-runtime.yaml` (Lambda engine déjà déclarée)

**Configs** : Utiliser les mêmes buckets S3 (CONFIG_BUCKET, DATA_BUCKET, NEWSLETTERS_BUCKET)

### 9.3 Naming conventions

**Lambda** : `vectora-inbox-engine-dev` (déjà défini dans `s1-runtime.yaml`)

**Logs CloudWatch** : `/aws/lambda/vectora-inbox-engine-dev`

**Fichiers S3** : `normalized/<client_id>/<YYYY>/<MM>/<DD>/items.json` → `newsletters/<client_id>/<YYYY>/<MM>/<DD>/newsletter.md`

---

## 10. Métriques de succès

### 10.1 Critères de validation

✅ **Matching fonctionnel** : Items correctement matchés aux watch_domains (vérifiable via logs)

✅ **Scoring cohérent** : Items triés par score décroissant (vérifiable via logs)

✅ **Bedrock opérationnel** : Appels API réussis avec génération de textes éditoriaux

✅ **Newsletter générée** : Fichier Markdown valide dans S3

✅ **Pas de régression** : Lambda ingest-normalize continue de fonctionner

### 10.2 Scénario de test nominal

**Input** :
```json
{
  "client_id": "lai_weekly",
  "period_days": 7
}
```

**Output attendu** :
- Newsletter Markdown dans `s3://vectora-inbox-newsletters-dev/lai_weekly/2025/01/15/newsletter.md`
- Réponse Lambda avec `statusCode: 200` et statistiques d'exécution
- Logs CloudWatch détaillés (nb items, nb appels Bedrock, temps d'exécution)

---

## 11. Prochaines étapes après implémentation

1. **Déploiement DEV** : Packager et déployer la Lambda engine
2. **Test d'intégration** : Run complet `ingest-normalize` → `engine`
3. **Validation qualité** : Vérifier la qualité des textes générés par Bedrock
4. **Ajustement des prompts** : Itérer sur les prompts Bedrock si nécessaire
5. **Documentation** : Créer le diagnostic `vectora_inbox_engine_first_run.md`
6. **CHANGELOG** : Mettre à jour avec le statut GREEN

---

**Fin du document de design.**

Ce plan sera maintenant exécuté phase par phase pour implémenter la Lambda engine.
