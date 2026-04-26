# Plan de Refactor : Normalisation Open-World et Ajustement Scoring

## Résumé Exécutif

Ce plan détaille la refactorisation de la normalisation Vectora Inbox pour implémenter :

1. **Normalisation "open-world"** : Bedrock peut détecter des entités non présentes dans les scopes canonical
2. **Schéma de sortie corrigé** : Séparation claire molecule vs trademark 
3. **Ajustement recency_factor** : Neutralisation pour le cas weekly (7 jours)

**Points clés :**
- Les scopes canonical deviennent des guides, pas des prisons
- Nouveau schéma : `*_detected` (monde ouvert) + `*_in_scopes` (intersection canonical)
- Recency_factor neutralisé pour period_days=7 (weekly)
- Pas de déploiement AWS dans cette phase

## Analyse de l'Existant

### Architecture Actuelle de Normalisation

**Fichiers clés identifiés :**
- `src/vectora_core/normalization/normalizer.py` : Orchestration principale
- `src/vectora_core/normalization/bedrock_client.py` : Appels Bedrock + prompt construction
- `src/vectora_core/normalization/entity_detector.py` : Fusion règles + Bedrock
- `canonical/scopes/trademark_scopes.yaml` : Scopes trademarks existants

**Prompt Bedrock actuel :**
```python
# Dans _build_normalization_prompt()
- Companies: {', '.join(companies_ex)}
- Molecules/Drugs: {', '.join(molecules_ex)}
- Technologies: {', '.join(technologies_ex)}

# Instructions actuelles :
"Extract ALL pharmaceutical/biotech company names mentioned in the text (including those in examples and ANY others)"
```

**Schéma de sortie actuel :**
```json
{
  "companies_detected": ["Camurus"],
  "molecules_detected": ["Brixadi", "buprenorphine"],  // ❌ PROBLÈME : Brixadi = trademark
  "technologies_detected": ["long acting", "depot"],
  "indications_detected": ["opioid use disorder"],
  "event_type": "clinical_update"
}
```

**Problèmes identifiés :**
1. **Confusion molecule/trademark** : "Brixadi" (trademark) classé comme molecule
2. **Pas de champ trademarks_detected** dans le schéma
3. **Pas de distinction *_detected vs *_in_scopes**
4. **Filtrage potentiel** : besoin de vérifier si les entités hors-scopes sont conservées

### Architecture Actuelle de Scoring

**Fichier clé :** `src/vectora_core/scoring/scorer.py`

**Calcul recency_factor actuel :**
```python
def _compute_recency_factor(item_date: str, half_life_days: int) -> float:
    # Décroissance exponentielle : factor = 2^(-age_days / half_life_days)
    recency_factor = math.pow(2, -age_days / half_life_days)
    return max(0.1, min(1.0, recency_factor))
```

**Problème identifié :**
- Pour period_days=7 (weekly), tous les items sont récents (0-7 jours)
- Variation recency_factor : 1.0 → 0.5 sur 7 jours
- Impact trop fort pour une fenêtre si courte

## Schéma Cible "Open-World"

### Nouveau Schéma de Sortie Normalisé

```json
{
  "source_key": "press_corporate__camurus",
  "source_type": "press_corporate", 
  "title": "Camurus Announces Positive Phase 3 Results for Brixadi",
  "summary": "Camurus reported positive results...",
  "url": "https://example.com/article",
  "date": "2025-01-15",
  
  // MONDE OUVERT : Toutes les entités détectées par Bedrock
  "companies_detected": ["Camurus", "Pfizer"],
  "molecules_detected": ["buprenorphine", "naloxone"],
  "trademarks_detected": ["Brixadi", "Suboxone"],  // ✅ NOUVEAU
  "technologies_detected": ["long acting", "depot", "microspheres"],
  "indications_detected": ["opioid use disorder", "pain management"],
  
  // INTERSECTION CANONICAL : Entités présentes dans les scopes
  "companies_in_scopes": ["Camurus"],
  "molecules_in_scopes": ["buprenorphine"],
  "trademarks_in_scopes": ["Brixadi"],
  "technologies_in_scopes": ["long acting"],
  "indications_in_scopes": ["opioid use disorder"],
  
  "event_type": "clinical_update"
}
```

### Séparation Molecule vs Trademark

**Définitions claires :**
- **molecules_detected** : Substances actives, principes actifs, noms génériques (ex: "buprenorphine", "naloxone")
- **trademarks_detected** : Noms commerciaux, marques, spécialités (ex: "Brixadi", "Suboxone", "Abilify")

**Instructions Bedrock mises à jour :**
```
6. Extract ALL drug molecule names (generic names, active substances, e.g., "buprenorphine", "aripiprazole")
7. Extract ALL pharmaceutical trademarks/brand names (commercial names, e.g., "Brixadi", "Abilify Maintena")
```

## Stratégie Recency_Factor

### Problème Actuel
- Pipeline weekly : ingestion sur 7 jours seulement
- Tous les items sont "récents" (0-7 jours d'ancienneté)
- recency_factor varie de 1.0 à ~0.5 sur cette courte période
- Impact disproportionné vs autres facteurs métier

### Solution Proposée : Neutralisation Weekly

**Option retenue :** Neutralisation complète pour period_days ≤ 7

```python
def _compute_recency_factor(item_date: str, half_life_days: int, period_days: int = None) -> float:
    # Pour les pipelines weekly (≤7 jours), neutraliser la récence
    if period_days and period_days <= 7:
        return 1.0  # Facteur neutre
    
    # Logique existante pour les pipelines plus longs
    # ...
```

**Justification :**
- Score dominé par : event_type, pertinence métier, pure_player vs hybrid, source_type
- Récence devient un tie-breaker très léger ou neutralisé
- Cohérent avec l'objectif métier du weekly

## Phases d'Exécution

### Phase A : Refactor Prompt Bedrock + Structure Output

**Objectifs :**
- Modifier le prompt Bedrock pour instructions "open-world"
- Ajouter séparation molecule vs trademark
- Implémenter nouveau schéma avec *_detected + *_in_scopes

**Fichiers concernés :**
- `src/vectora_core/normalization/bedrock_client.py` : Prompt + parsing
- `src/vectora_core/normalization/normalizer.py` : Structure output
- `src/vectora_core/normalization/entity_detector.py` : Calcul intersections

**Critères de succès :**
- Prompt Bedrock contient instructions open-world explicites
- Schéma JSON retourné contient 10 champs (*_detected + *_in_scopes)
- Séparation molecule/trademark fonctionnelle
- Tests unitaires passent

### Phase B : Adaptation Scoring (Recency)

**Objectifs :**
- Modifier `_compute_recency_factor()` pour neutralisation weekly
- Ajouter paramètre period_days au scorer
- Documenter l'impact sur le scoring

**Fichiers concernés :**
- `src/vectora_core/scoring/scorer.py` : Fonction recency
- `src/vectora_core/__init__.py` : Passage paramètre period_days

**Critères de succès :**
- recency_factor = 1.0 pour period_days ≤ 7
- Logique existante préservée pour autres cas
- Score weekly dominé par event_type + métier

### Phase C : Mise à Jour Documentation

**Objectifs :**
- Corriger l'exemple Brixadi dans la doc pipeline
- Documenter le nouveau schéma open-world
- Expliquer l'ajustement recency pour weekly

**Fichiers concernés :**
- `canonical/vectora_inbox_newsletter_pipeline_overview.md`
- `client-config-examples/README.md`

**Critères de succès :**
- Exemple Brixadi corrigé (trademark, pas molecule)
- Schéma documenté avec *_detected + *_in_scopes
- Impact recency expliqué

### Phase D : Tests Locaux

**Objectifs :**
- Tests unitaires pour normalisation open-world
- Tests scoring avec recency neutralisé
- Test bout-en-bout simulation (sans AWS)

**Fichiers concernés :**
- `tests/unit/test_normalization_open_world.py` (nouveau)
- `tests/unit/test_scoring_recency.py` (nouveau)
- Script simulation locale

**Critères de succès :**
- Entités hors-scopes conservées dans *_detected
- Intersections correctes dans *_in_scopes
- Scoring weekly avec recency=1.0
- Pas de régression fonctionnelle

## Risques et Points d'Attention

### Risques Techniques
1. **Compatibilité descendante** : Code existant accédant aux anciens champs
2. **Performance Bedrock** : Prompt plus long avec instructions détaillées
3. **Parsing JSON** : Nouveau schéma plus complexe à parser

### Risques Métier
1. **Bruit** : Plus d'entités détectées = potentiel bruit dans le matching
2. **Scoring** : Neutralisation recency peut changer l'ordre des items
3. **Cohérence** : Séparation molecule/trademark dépend de la qualité Bedrock

### Mitigations
- Tests exhaustifs avant déploiement
- Monitoring des taux de parsing JSON
- Validation manuelle sur échantillon d'items
- Rollback plan si dégradation qualité

## Prochaines Étapes Post-Refactor

1. **Tests DEV** : Déploiement sur environnement DEV
2. **Validation lai_weekly** : Test sur pipeline réel
3. **Monitoring** : Métriques qualité normalisation
4. **Ajustements** : Fine-tuning selon retours utilisateurs

---

**Statut :** Plan validé, prêt pour exécution
**Durée estimée :** 2-3 jours (développement + tests locaux)
**Prérequis :** Aucun déploiement AWS dans cette phase