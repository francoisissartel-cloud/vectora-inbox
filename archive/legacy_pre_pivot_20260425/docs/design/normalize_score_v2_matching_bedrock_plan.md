# Plan d'implémentation : Deuxième appel Bedrock pour matching par domaines dans normalize_score_v2

## Phase 0 – Cadrage & objectifs

### Rôle de normalize_score_v2 dans le workflow Vectora Inbox

La Lambda `vectora-inbox-normalize-score-v2` est responsable de la **normalisation intelligente** des items bruts ingérés et de leur **scoring de pertinence** pour préparer la génération de newsletter. Elle se situe entre l'ingestion brute (ingest_v2) et la génération de newsletter, transformant les contenus bruts en items structurés, matchés et scorés.

### Problème actuel identifié

D'après le diagnostic `normalize_score_v2_matching_investigation_report.md`, le matching aux domaines présente un **taux de succès de 0%** sur le MVP lai_weekly_v3 :
- 15 items normalisés avec succès par Bedrock (extraction d'entités fonctionnelle)
- **0 item matché** aux domaines `tech_lai_ecosystem` et `regulatory_lai` 
- Cause principale : logique de matching déterministe trop stricte (intersections d'ensembles) qui ne capture pas les nuances sémantiques
- Entités extraites correctement par Bedrock mais échec du matching par règles (ex: "Teva Pharmaceuticals" vs "Teva Pharmaceutical")

### Objectif de ce plan

Ajouter un **deuxième appel Bedrock dédié au matching par domaines** qui :
- Utilise l'intelligence linguistique de Bedrock pour évaluer la pertinence sémantique d'un item normalisé par rapport aux watch_domains configurés
- Complète (sans remplacer) le matching déterministe existant
- Reste piloté par `client_config` + `canonical` (pas de logique hardcodée)
- Respecte strictement les règles d'hygiène `src_lambda_hygiene_v4.md`

### Critères de succès

**Quantitatifs :**
- **≥ 60%** d'items correctement matchés à au moins 1 watch_domain sur le MVP lai_weekly_v3
- **≥ 80%** de précision (items matchés effectivement pertinents selon review humaine)
- **≤ 2 secondes** de temps d'exécution supplémentaire par item pour l'appel Bedrock matching

**Qualitatifs :**
- Qualité perçue du matching supérieure au matching déterministe actuel
- Simplicité & conformité totale aux règles `hygiene_v4` (pas d'usine à gaz)
- Généricité : fonctionne pour tout client avec watch_domains configurés

---

## Phase 1 – Analyse de l'existant (workflow réel)

### Chaîne actuelle pour le MVP lai_weekly_v3

**Output de ingest_v2 (dernier run observé) :**
- **15 items** ingérés depuis 8 sources LAI (MedinCell, Nanexa, DelSiTech)
- Sources actives : `lai_corporate_mvp` + `lai_press_mvp`
- Période : 30 jours (config lai_weekly_v3)
- Format JSON : `[{"item_id": "...", "title": "...", "content": "...", "url": "...", "published_at": "...", ...}]`

**Ce que fait EXACTEMENT normalize_score_v2 aujourd'hui :**

*Inputs :*
- Items ingérés depuis S3 `ingested/{client_id}/{YYYY}/{MM}/{DD}/items.json`
- Config client `lai_weekly_v3.yaml` (watch_domains, scoring_config, matching_config)
- Scopes canonical (companies, molecules, technologies, trademarks)
- Prompts Bedrock depuis `canonical/prompts/global_prompts.yaml`

*Appel Bedrock actuel (normalisation) :*
- **1 seul appel** par item via `vectora_core/normalization/bedrock_client.py`
- Modèle : `anthropic.claude-3-sonnet-20240229-v1:0` (région `us-east-1`)
- Prompt : `normalization.lai_default` depuis `global_prompts.yaml`
- Output : entités extraites (companies, molecules, technologies, trademarks), résumé, classification d'événement

*Output actuel :*
- Items normalisés avec champs : `normalized_content`, `matching_results` (vide), `scoring_results`
- Stockage S3 : `curated/{client_id}/{YYYY}/{MM}/{DD}/items.json`

### Identification du point d'insertion du matching

**Où le matching devrait se produire dans le pipeline :**
1. ✅ Normalisation Bedrock (existant) → extraction d'entités
2. **🎯 NOUVEAU : Matching Bedrock** → évaluation pertinence par domaine
3. ✅ Scoring déterministe (existant) → calcul scores finaux

**Champs de l'item normalisé utilisés comme input du matching :**
- `title` : titre de l'article
- `normalized_content.summary` : résumé généré par Bedrock
- `normalized_content.entities` : entités extraites (companies, molecules, technologies, trademarks)
- `normalized_content.event_classification` : type d'événement classifié

### Limitations actuelles expliquant le matching = 0%

**Logique trop déterministe :**
- Matching par intersections d'ensembles strictes dans `vectora_core/matching/matcher.py`
- Échec sur variations mineures : "Teva Pharmaceuticals" ≠ "Teva Pharmaceutical"
- Pas de compréhension sémantique du contexte

**Prompts inadaptés :**
- Aucun prompt Bedrock dédié au matching dans `global_prompts.yaml`
- Le prompt de normalisation ne génère pas d'évaluation de pertinence par domaine

**Mauvaise exploitation des scopes canonical :**
- Les scopes sont correctement chargés mais la logique de matching ne capture pas les nuances
- Pas de prise en compte du contexte métier (pure players vs hybrid companies)

---

## Phase 2 – Design fonctionnel du matching via Bedrock

### Rôle fonctionnel du nouvel appel Bedrock

**Input du matching Bedrock :**
- Item normalisé complet (titre, résumé, entités extraites, type d'événement)
- Description structurée des watch_domains activés pour le client
- Scopes canonical dérivés et contextualisés par domaine

**Output du matching Bedrock :**
```json
{
  "domain_evaluations": [
    {
      "domain_id": "tech_lai_ecosystem",
      "is_relevant": true,
      "relevance_score": 0.85,
      "confidence": "high",
      "reasoning": "Article discusses MedinCell's BEPO technology partnership with Teva for long-acting injectable development",
      "matched_entities": {
        "companies": ["MedinCell", "Teva"],
        "technologies": ["BEPO", "long-acting injectable"],
        "trademarks": ["Suboxone"]
      }
    },
    {
      "domain_id": "regulatory_lai",
      "is_relevant": false,
      "relevance_score": 0.25,
      "confidence": "medium",
      "reasoning": "No regulatory events mentioned, focus is on technology partnership"
    }
  ]
}
```

### Utilisation des scopes canonical

**Pour chaque watch_domain, dérivation du contexte :**
- `technology_scope: "lai_keywords"` → Liste des 80+ mots-clés LAI depuis `canonical/scopes/technology_scopes.yaml`
- `company_scope: "lai_companies_global"` → Liste des 180+ entreprises LAI depuis `canonical/scopes/company_scopes.yaml`
- `molecule_scope: "lai_molecules_global"` → Liste des 90+ molécules LAI
- `trademark_scope: "lai_trademarks_global"` → Liste des 70+ marques LAI

**Stratégie de contextualisation :**
- La Lambda prépare le contexte structuré par domaine avant l'appel Bedrock
- Bedrock reçoit les listes d'entités pertinentes, pas les références aux scopes
- Exemple : "Pour le domaine tech_lai_ecosystem, les entreprises d'intérêt sont : MedinCell, Camurus, Teva Pharmaceutical, ..."

### Stratégie de tolérance au bruit

**Seuils de score configurables :**
- Seuil minimum par défaut : `0.4` (40% de confiance)
- Seuils ajustables par type de domaine dans `client_config`
- Seuils différenciés par niveau de confiance : `high` (≥0.7), `medium` (0.4-0.7), `low` (<0.4)

**Gestion des cas ambigus :**
- Item matchant plusieurs domaines : accepté (cas normal)
- Item ne matchant aucun domaine : conservé avec `matched_domains: []`
- Conflits entre matching déterministe et Bedrock : priorité à Bedrock si score ≥ 0.6

---

## Phase 3 – Design technique (architecture simple conforme à hygiene_v4)

### Intégration dans normalize_score_v2

**Fonction pure dans vectora_core :**
```python
# Nouveau fichier : src/vectora_core/matching/bedrock_matcher.py
def match_watch_domains_with_bedrock(
    normalized_item: Dict[str, Any],
    watch_domains: List[Dict[str, Any]],
    canonical_scopes: Dict[str, Any],
    bedrock_model_id: str,
    bedrock_region: str = "us-east-1"
) -> Dict[str, Any]:
    """
    Évalue la pertinence d'un item normalisé par rapport aux watch_domains via Bedrock.
    
    Returns:
        {
            "matched_domains": ["tech_lai_ecosystem"],
            "domain_relevance": {
                "tech_lai_ecosystem": {"score": 0.85, "confidence": "high", ...}
            }
        }
    """
```

**Étapes dans le pipeline de la Lambda :**
1. ✅ Charger configs + canonical (existant)
2. ✅ Normaliser via Bedrock (appel existant)
3. **🎯 NOUVEAU : Préparer le contexte watch_domains et scopes**
4. **🎯 NOUVEAU : Appel Bedrock 2 pour matching**
5. **🎯 NOUVEAU : Injection du résultat de matching dans la structure de l'item**
6. ✅ Scoring déterministe (existant, utilise les résultats de matching)

### Nouveau prompt dans global_prompts.yaml

**Nom du prompt :** `matching_watch_domains_v2`

**Variables attendues :**
- `{{item_title}}` : Titre de l'article
- `{{item_summary}}` : Résumé généré par la normalisation
- `{{item_entities}}` : Entités extraites (JSON)
- `{{item_event_type}}` : Type d'événement classifié
- `{{domains_context}}` : Contexte structuré des domaines avec scopes

**Type de sortie :** JSON strict avec schéma défini pour parsing robuste

**Exemple de structure :**
```yaml
matching:
  matching_watch_domains_v2:
    system_instructions: |
      You are a domain relevance expert for biotech/pharma intelligence.
      Evaluate how relevant a normalized news item is to specific watch domains.
      Focus on semantic understanding beyond keyword matching.
      
    user_template: |
      Evaluate the relevance of this normalized item to the configured watch domains:

      ITEM TO EVALUATE:
      Title: {{item_title}}
      Summary: {{item_summary}}
      Entities: {{item_entities}}
      Event Type: {{item_event_type}}

      WATCH DOMAINS TO EVALUATE:
      {{domains_context}}

      For each domain, evaluate:
      1. Is this item relevant to the domain's focus area?
      2. What is the relevance score (0.0 to 1.0)?
      3. What is your confidence level (high/medium/low)?
      4. Which entities contributed to the match?
      5. Brief reasoning for the evaluation

      RESPONSE FORMAT (JSON only):
      {
        "domain_evaluations": [
          {
            "domain_id": "...",
            "is_relevant": true/false,
            "relevance_score": 0.0-1.0,
            "confidence": "high/medium/low",
            "reasoning": "...",
            "matched_entities": {...}
          }
        ]
      }

    bedrock_config:
      max_tokens: 1500
      temperature: 0.1
      anthropic_version: "bedrock-2023-05-31"
```

### Respect des règles src_lambda_hygiene_v4

**Lambdas génériques, pilotées par client_config + canonical :**
- ✅ Aucune logique métier hardcodée spécifique à LAI
- ✅ Domaines et scopes définis dans `client_config` et `canonical`
- ✅ Prompt Bedrock externalisé dans `global_prompts.yaml`

**Pas de pollution de /src :**
- ✅ Nouveau code uniquement dans `vectora_core/matching/bedrock_matcher.py`
- ✅ Pas de dépendances tierces supplémentaires
- ✅ Réutilisation du client Bedrock existant

**Pas de layers ou usine à gaz :**
- ✅ Fonction pure simple dans vectora_core
- ✅ Intégration minimale dans le pipeline existant
- ✅ Pas de nouvelle Lambda ou service

---

## Phase 4 – Plan d'implémentation future (à exécuter uniquement si GO)

### Étape 4.1 – Préparation

**Ajouter le nouveau prompt de matching :**
- Fichier cible : `canonical/prompts/global_prompts.yaml`
- Section : `matching.matching_watch_domains_v2`
- Variables : `item_title`, `item_summary`, `item_entities`, `item_event_type`, `domains_context`

**Ajouter les fonctions dans vectora_core :**
- Fichier cible : `src/vectora_core/matching/bedrock_matcher.py`
- Signatures principales :
  ```python
  def match_watch_domains_with_bedrock(...) -> Dict[str, Any]
  def _build_domains_context(...) -> str
  def _parse_bedrock_matching_response(...) -> Dict[str, Any]
  ```

### Étape 4.2 – Modification contrôlée de normalize_score_v2

**Point exact d'insertion dans le pipeline :**
- Fichier : `src/vectora_core/normalization/__init__.py`
- Fonction : `run_normalize_score_for_client()`
- Position : Après normalisation Bedrock, avant scoring déterministe

**Gestion des erreurs Bedrock :**
- Timeout : fallback sur matching déterministe seul
- JSON mal formé : log d'erreur + fallback
- Quota dépassé : retry avec backoff exponentiel

**Respect strict des règles hygiene_v4 :**
- Taille code : fonction < 100 lignes
- Dépendances : réutilisation du client Bedrock existant
- Logs : utilisation du logger vectora_core standard

### Étape 4.3 – Tests locaux

**Dry-run sur sous-ensemble d'items MVP :**
- Dataset : 5 items représentatifs du dernier run lai_weekly_v3
- Items test : MedinCell partnership, Teva regulatory, Nanexa technology

**Logs côté développeur :**
- Input Bedrock : contexte domaines + item normalisé
- Output Bedrock : réponse JSON brute
- Résultat parsing : scores de matching par domaine
- Comparaison : matching déterministe vs Bedrock

**Métriques locales :**
- % d'items matchés par domaine (cible : ≥60%)
- Distribution des scores de confiance
- Temps d'exécution par appel Bedrock (cible : ≤2s)

### Étape 4.4 – Déploiement AWS (profil rag-lai-prod, région Paris)

**Stratégie de déploiement minimal impact :**
- Mise à jour de la Lambda `vectora-inbox-normalize-score-dev` uniquement
- Pas de modification d'infrastructure (buckets, rôles IAM inchangés)
- Déploiement via script existant `scripts/package_normalize_score_v2_deploy.py`

**Validation CloudWatch :**
- Logs Bedrock : appels réussis/échoués, temps de réponse
- Items traités : nombre d'items matchés avant/après
- Erreurs éventuelles : timeouts, parsing JSON, quotas

### Étape 4.5 – Audit qualité & coût

**Mesures Bedrock :**
- Tokens par run : estimation 500-800 tokens par item (input + output)
- Coût estimé par mois : ~15 items × 4 runs × 800 tokens × $0.003/1K = $0.14/mois
- Comparaison avec coût normalisation existant

**Analyse qualitative :**
- Review manuelle de 10 items matchés : pertinence réelle vs score Bedrock
- Faux positifs : items matchés mais non pertinents
- Faux négatifs : items pertinents mais non matchés

**Recommandations d'ajustement :**
- Ajustement des seuils de score par domaine
- Amélioration du prompt si patterns d'erreur identifiés
- Optimisation des scopes canonical si gaps détectés

---

## Phase 5 – Synthèse & recommandations

### Vision de la solution

**Simple et générique :**
- ✅ Ajoute une seule fonction pure dans vectora_core
- ✅ Réutilise l'infrastructure Bedrock existante
- ✅ Pilotée par configuration (client_config + canonical)
- ✅ Pas d'impact sur les autres Lambdas

**Scalable :**
- ✅ Fonctionne pour tout client avec watch_domains configurés
- ✅ Pas de logique spécifique à LAI hardcodée
- ✅ Extensible à d'autres verticales (oncology, CNS, etc.)

### Risques potentiels

**Coûts :**
- 🟡 **FAIBLE** : ~$0.14/mois pour MVP lai_weekly_v3
- 🟡 **MOYEN** : Scaling à 10 clients → ~$1.40/mois
- ✅ **MITIGATION** : Seuils configurables pour limiter les appels

**Bruit (faux positifs) :**
- 🟡 **MOYEN** : Bedrock peut sur-matcher des items marginaux
- ✅ **MITIGATION** : Seuils de confiance ajustables par domaine
- ✅ **MITIGATION** : Combinaison avec matching déterministe

**Complexité :**
- 🟢 **FAIBLE** : Design simple respectant hygiene_v4
- 🟢 **FAIBLE** : Pas de nouvelle infrastructure
- 🟢 **FAIBLE** : Fallback sur matching existant en cas d'erreur

### Recommandations finales

**GO / NO GO : 🟢 GO RECOMMANDÉ**

**Justification :**
1. **Problème critique** : 0% de matching actuel rend le système inutilisable
2. **Solution proportionnée** : Ajout minimal, pas d'usine à gaz
3. **Coût négligeable** : <$2/mois même avec scaling
4. **Risque maîtrisé** : Fallback sur logique existante
5. **Conformité totale** : Respect strict des règles hygiene_v4

**Priorités d'implémentation :**
1. **Phase 1** : Commencer sur le domaine `tech_lai_ecosystem` uniquement
2. **Phase 2** : Étendre à `regulatory_lai` après validation
3. **Phase 3** : Généraliser à tous les domaines configurés

**Critères de validation avant généralisation :**
- ≥ 60% d'items matchés sur tech_lai_ecosystem
- ≥ 80% de précision selon review humaine
- Temps d'exécution ≤ 2s par item
- Coût Bedrock ≤ $0.20/mois pour MVP

---

**Conclusion :** Cette solution apporte une amélioration significative du matching avec un impact minimal sur l'architecture existante, tout en respectant parfaitement les principes de simplicité et de généricité de Vectora Inbox.