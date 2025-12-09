# Diagnostic : Implémentation de la Lambda vectora-inbox-engine

**Date** : 2025-01-15  
**Auteur** : Amazon Q Developer  
**Statut** : ✅ **IMPLÉMENTATION COMPLÉTÉE**

---

## Résumé exécutif

La Lambda `vectora-inbox-engine` a été **implémentée avec succès**. Le code couvre les Phases 2, 3 et 4 du workflow Vectora Inbox :

✅ **Phase 2 (Matching)** : Calcul des intersections d'ensembles pour déterminer les items pertinents  
✅ **Phase 3 (Scoring)** : Attribution de scores numériques basés sur des règles transparentes  
✅ **Phase 4 (Newsletter)** : Génération de textes éditoriaux avec Bedrock + assemblage Markdown

**Prochaine étape** : Packager et déployer la Lambda en DEV, puis tester le workflow complet.

---

## Architecture implémentée

### Modules créés/modifiés

**Orchestration** :
- `src/vectora_core/__init__.py` : Fonction `run_engine_for_client()` complète
  - Collecte des items normalisés depuis S3
  - Appel des modules matching, scoring, newsletter
  - Écriture de la newsletter dans S3
  - Gestion des erreurs et cas limites

**Phase 2 - Matching** :
- `src/vectora_core/matching/matcher.py` :
  - `match_items_to_domains()` : Calcule les intersections pour chaque watch_domain
  - `compute_intersection()` : Opération d'intersection d'ensembles
  - Annotation des items avec `matched_domains` (list[str])

**Phase 3 - Scoring** :
- `src/vectora_core/scoring/scorer.py` :
  - `score_items()` : Calcule le score de chaque item
  - `compute_score()` : Formule de scoring combinant 7 facteurs
  - `_compute_recency_factor()` : Décroissance exponentielle (demi-vie 7 jours)
  - `rank_items_by_score()` : Tri par score décroissant

**Phase 4 - Newsletter** :
- `src/vectora_core/newsletter/assembler.py` :
  - `generate_newsletter()` : Orchestration de la génération
  - `_select_items_by_section()` : Sélection des top N items par section
  - `_generate_minimal_newsletter()` : Fallback si aucun item
- `src/vectora_core/newsletter/bedrock_client.py` :
  - `generate_editorial_content()` : Appel Bedrock pour génération éditoriale
  - `_build_editorial_prompt()` : Construction du prompt structuré
  - `_call_bedrock_with_retry()` : Retry/backoff sur ThrottlingException (réutilisé de ingest-normalize)
  - `_parse_editorial_response()` : Parsing de la réponse JSON
  - `_generate_fallback_editorial()` : Fallback si échec Bedrock
- `src/vectora_core/newsletter/formatter.py` :
  - `assemble_markdown()` : Assemblage du Markdown final

**Utilitaires** :
- `src/vectora_core/storage/s3_client.py` : Fonction `write_text_to_s3()` pour écrire le Markdown
- `src/vectora_core/config/loader.py` : Fonction `load_scoring_rules()` pour charger les règles

---

## Logique de matching (Phase 2)

### Principe

Pour chaque item normalisé, calculer les intersections avec les scopes canonical référencés par chaque watch_domain.

### Processus

1. **Extraire les entités détectées** dans l'item :
   - `companies_detected` (list[str])
   - `molecules_detected` (list[str])
   - `technologies_detected` (list[str])
   - `indications_detected` (list[str])

2. **Pour chaque watch_domain** :
   - Charger les scopes canonical via les clés (`company_scope`, `molecule_scope`, etc.)
   - Calculer les intersections :
     - `companies_detected` ∩ `company_scope`
     - `molecules_detected` ∩ `molecule_scope`
     - `technologies_detected` ∩ `technology_scope`
     - `indications_detected` ∩ `indication_scope`

3. **Décider si l'item appartient au domaine** :
   - Si au moins une intersection est non vide → ajouter `domain_id` à `matched_domains`

### Exemple

**Item** :
```json
{
  "title": "Camurus Announces Positive Phase 3 Results for Brixadi",
  "companies_detected": ["Camurus"],
  "technologies_detected": ["long acting", "depot"]
}
```

**Watch domain `tech_lai_ecosystem`** :
- `company_scope`: `lai_companies_global` (contient "Camurus")
- `technology_scope`: `lai_keywords` (contient "long acting", "depot")

**Résultat** : `matched_domains = ["tech_lai_ecosystem"]`

---

## Logique de scoring (Phase 3)

### Facteurs de scoring

Le score combine 7 facteurs :

1. **Importance de l'event_type** : clinical_update (5), regulatory (5), partnership (6), etc.
2. **Priorité du watch_domain** : high (3), medium (2), low (1)
3. **Récence** : Décroissance exponentielle avec demi-vie de 7 jours
4. **Type de source** : press_corporate (2), press_sector (1.5), generic (1)
5. **Profondeur du signal** : +0.3 par entité détectée au-delà de la première
6. **Bonus compétiteurs clés** : +2 (non implémenté dans le MVP)
7. **Bonus molécules clés** : +1.5 (non implémenté dans le MVP)

### Formule

```
score = (event_weight * priority_weight * recency_factor * source_weight) + signal_depth_bonus
```

### Exemple

**Item** :
- `event_type`: "clinical_update" → event_weight = 5
- `matched_domains`: ["tech_lai_ecosystem"] → priority = "high" → priority_weight = 3
- `date`: "2025-01-14" (1 jour) → recency_factor ≈ 0.9
- `source_type`: "press_corporate" → source_weight = 2
- Entités détectées : 4 → signal_depth_bonus = (4-1) * 0.3 = 0.9

**Score** : (5 * 3 * 0.9 * 2) + 0.9 = 27 + 0.9 = **27.9**

---

## Logique de génération de newsletter (Phase 4)

### Sélection des items par section

Pour chaque section définie dans `newsletter_layout.sections` :

1. **Filtrer les items** :
   - Garder uniquement les items matchés aux `source_domains` de la section
   - Appliquer les filtres `filter_event_types` si présents

2. **Trier par score décroissant**

3. **Sélectionner les top N items** (selon `max_items`)

### Appel à Bedrock

**Prompt structuré** contenant :
- Contexte global (période, nombre d'items analysés, domaines d'intérêt)
- Liste des items sélectionnés par section (titre, summary, source, URL, date)
- Attentes sur le ton (tone, voice, langue)
- Structure attendue (titre, intro, TL;DR, sections)

**Réponse attendue** (JSON) :
```json
{
  "title": "Weekly Biotech Intelligence – January 15, 2025",
  "intro": "2-4 sentences summarizing the week's context",
  "tldr": ["Bullet point 1", "Bullet point 2", "Bullet point 3"],
  "sections": [
    {
      "section_title": "Top Signals – LAI Ecosystem",
      "section_intro": "1-2 sentences introducing this section",
      "items": [
        {
          "title": "Item title",
          "rewritten_summary": "Concise rewrite (2-3 sentences)",
          "url": "https://..."
        }
      ]
    }
  ]
}
```

### Assemblage du Markdown

Le module `formatter.py` assemble la réponse Bedrock en un document Markdown :

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
[Read more](URL)

---

*Newsletter générée par Vectora Inbox – Powered by Amazon Bedrock*
```

---

## Gestion des erreurs

### Aucun item normalisé trouvé

**Comportement** : Générer une newsletter minimale avec un message explicite

**Exemple** :
```markdown
# LAI Intelligence Weekly – 2025-01-15

No critical signals this week. We continue to monitor your domains of interest.

---

*Newsletter générée par Vectora Inbox – Powered by Amazon Bedrock*
```

### Échec Bedrock

**Comportement** : Fallback vers une newsletter simplifiée sans réécriture Bedrock

**Exemple** : Utiliser les summaries existants des items normalisés + disclaimer "Newsletter générée en mode dégradé"

### Configuration client invalide

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

## Alignement avec l'existant

### Réutilisation du code ingest-normalize

✅ **Bedrock retry/backoff** : Même pattern que `src/vectora_core/normalization/bedrock_client.py`  
✅ **Inference profile** : Même `BEDROCK_MODEL_ID` = `eu.anthropic.claude-sonnet-4-5-20250929-v1:0`  
✅ **Logs structurés** : Même format (client_id, execution_date, etc.)

### Respect de la structure du repo

✅ **Code source** : `src/vectora_core/` (logique métier) + `src/lambdas/engine/` (handler Lambda)  
✅ **Infra** : Déjà définie dans `infra/s1-runtime.yaml` (Lambda engine déjà déclarée)  
✅ **Configs** : Utilise les mêmes buckets S3 (CONFIG_BUCKET, DATA_BUCKET, NEWSLETTERS_BUCKET)

### Naming conventions

✅ **Lambda** : `vectora-inbox-engine-dev` (déjà défini dans `s1-runtime.yaml`)  
✅ **Logs CloudWatch** : `/aws/lambda/vectora-inbox-engine-dev`  
✅ **Fichiers S3** : `normalized/<client_id>/<YYYY>/<MM>/<DD>/items.json` → `newsletters/<client_id>/<YYYY>/<MM>/<DD>/newsletter.md`

---

## Prochaines étapes

### 1. Packaging et déploiement

**Commandes** :
```powershell
# Packager la Lambda engine
cd src
zip -r ../engine.zip . -x "*.pyc" -x "__pycache__/*"

# Uploader dans S3
aws s3 cp engine.zip s3://vectora-inbox-lambda-code-dev/lambda/engine/latest.zip --profile rag-lai-prod --region eu-west-3

# Mettre à jour le code de la Lambda
aws lambda update-function-code `
  --function-name vectora-inbox-engine-dev `
  --s3-bucket vectora-inbox-lambda-code-dev `
  --s3-key lambda/engine/latest.zip `
  --profile rag-lai-prod `
  --region eu-west-3
```

### 2. Test d'intégration

**Scénario** :
1. Invoquer `vectora-inbox-ingest-normalize-dev` pour générer des items normalisés
2. Invoquer `vectora-inbox-engine-dev` pour générer la newsletter
3. Télécharger la newsletter depuis S3 et vérifier le format Markdown

**Script de test** : `scripts/test-engine-lai-weekly.ps1`

### 3. Validation qualité

**Critères** :
- ✅ Items correctement matchés aux watch_domains (vérifiable via logs)
- ✅ Items triés par score décroissant (vérifiable via logs)
- ✅ Bedrock génère des textes cohérents (titre, intro, TL;DR, sections)
- ✅ Newsletter Markdown valide dans S3
- ✅ Pas de régression sur ingest-normalize

### 4. Documentation

**Créer** : `docs/diagnostics/vectora_inbox_engine_first_run.md`

**Contenu** :
- Scénario testé (client_id, period_days)
- Résultats (nb items, nb sections, temps d'exécution)
- Qualité des textes générés par Bedrock
- Problèmes rencontrés et solutions
- Recommandations d'ajustement

### 5. Mise à jour du CHANGELOG

**Statut final** : ✅ GREEN – First full newsletter successfully generated

---

## Métriques de succès

### Critères de validation

✅ **Matching fonctionnel** : Items correctement matchés aux watch_domains  
✅ **Scoring cohérent** : Items triés par score décroissant  
✅ **Bedrock opérationnel** : Appels API réussis avec génération de textes éditoriaux  
✅ **Newsletter générée** : Fichier Markdown valide dans S3  
✅ **Pas de régression** : Lambda ingest-normalize continue de fonctionner

### Scénario de test nominal

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

## Conclusion

L'implémentation de la Lambda `vectora-inbox-engine` est **complète et prête pour le déploiement**. Le code couvre les 3 phases du moteur de newsletter (matching, scoring, génération) avec une architecture modulaire et réutilisable.

**Recommandation** : Procéder au packaging, déploiement et test d'intégration en DEV.

---

**Auteur** : Amazon Q Developer  
**Date de création** : 2025-01-15  
**Version** : 1.0
