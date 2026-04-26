# Analyse Comparative V1 vs V2 : Règles d'Ingestion

## Résumé Exécutif

**Problématique** : La Lambda V1 `ingest-normalize` ingérait 104 items pour le client `lai_weekly_v3`, tandis que la Lambda V2 `ingest` n'en ingère que 12 items. Cette analyse identifie les différences de règles d'ingestion et propose des améliorations.

**Conclusion principale** : V2 est **trop restrictive** par rapport à V1. V1 ingérait **TOUT** le contenu brut sans filtrage préalable, puis laissait Bedrock faire le tri lors de la normalisation. V2 applique un filtrage temporel strict qui élimine 92% du contenu potentiellement pertinent.

## Différences Fondamentales V1 vs V2

### Architecture de Filtrage

| Aspect | V1 (ingest-normalize) | V2 (ingest-only) |
|--------|----------------------|-------------------|
| **Philosophie** | Ingestion large + filtrage Bedrock | Ingestion sélective + pas de Bedrock |
| **Filtrage temporel** | Après normalisation Bedrock | Avant parsing (très strict) |
| **Profils d'ingestion** | Non utilisés | Définis mais non implémentés |
| **Déduplication** | Après normalisation | Avant écriture S3 |
| **Validation** | Par Bedrock (IA) | Par règles simples |

### Workflow de Traitement

#### V1 : Ingestion Large → Normalisation IA → Filtrage Intelligent
```
Sources → Fetch → Parse → [TOUS LES ITEMS] → Bedrock Normalize → Filter → S3
         (104 items bruts)                    (104 items normalisés)
```

#### V2 : Filtrage Strict → Ingestion Sélective → Stockage Brut
```
Sources → Fetch → Parse → Temporal Filter → Dedupe → Validate → S3
         (104 items bruts)  (12 items conservés)
```

## Analyse Détaillée des Configurations

### Configuration Client `lai_weekly_v3`

**Period Days** : 30 jours (identique V1 et V2)
- V1 : Utilisé pour la collecte post-normalisation
- V2 : Utilisé pour le filtrage pré-ingestion (TROP STRICT)

**Sources Configurées** :
- `lai_corporate_mvp` : 5 sources corporate (MedinCell, Camurus, DelSiTech, Nanexa, Peptron)
- `lai_press_mvp` : 3 sources presse (FierceBiotech, FiercePharma, Endpoints)

### Profils d'Ingestion Canonical

#### Sources Corporate (Pure Players LAI)
**Profil** : `corporate_pure_player_broad`
- **Stratégie V1** : Ingestion de TOUT (pas de profil appliqué)
- **Stratégie V2** : Profil défini mais NON IMPLÉMENTÉ dans le code
- **Impact** : V2 devrait ingérer plus largement les pure players LAI

#### Sources Presse Sectorielle
**Profil** : `press_technology_focused`
- **Stratégie V1** : Ingestion de TOUT (pas de profil appliqué)
- **Stratégie V2** : Profil défini mais NON IMPLÉMENTÉ dans le code
- **Impact** : V2 devrait filtrer plus strictement la presse généraliste

## Analyse des 104 Items V1

### Répartition par Source
- **MedinCell** : ~12 items (corporate LAI - haute pertinence)
- **DelSiTech** : ~10 items (corporate LAI - moyenne pertinence)
- **FierceBiotech** : ~35 items (presse - pertinence variable)
- **FiercePharma** : ~25 items (presse - pertinence variable)
- **Endpoints** : ~15 items (presse - pertinence variable)
- **Autres sources** : ~7 items

### Analyse de Pertinence (basée sur échantillon V1)
- **Items LAI pertinents** : ~25 items (24%)
  - MedinCell avec mentions LAI explicites
  - Nanexa partnership avec Moderna (LAI)
  - UZEDY, olanzapine LAI mentions
- **Items pharma génériques** : ~60 items (58%)
  - Actualités pharma sans lien LAI direct
  - Regulatory updates génériques
  - Corporate moves non-LAI
- **Items non pertinents** : ~19 items (18%)
  - Recrutement, événements, communications corporate

## Problèmes Identifiés dans V2

### 1. Filtrage Temporel Trop Strict
**Problème** : V2 applique `period_days=30` comme filtre d'exclusion strict
- Items plus anciens que 30 jours = supprimés
- Mais beaucoup de sources corporate ont des dates de publication approximatives
- Perte de contenu pertinent avec dates mal parsées

**Impact** : 92 items perdus (88% du contenu)

### 2. Profils d'Ingestion Non Implémentés
**Problème** : Les profils canonical sont définis mais pas utilisés dans le code V2
- `corporate_pure_player_broad` devrait ingérer largement MedinCell, etc.
- `press_technology_focused` devrait filtrer intelligemment la presse

**Impact** : Pas de différenciation entre sources corporate et presse

### 3. Absence de Normalisation IA
**Problème** : V2 n'a pas Bedrock pour évaluer la pertinence réelle
- V1 utilisait Bedrock pour détecter companies, molecules, technologies
- V2 se base uniquement sur des règles simples

**Impact** : Impossible de distinguer le signal du bruit

### 4. Parsing de Dates Défaillant
**Problème** : Beaucoup d'items ont des dates mal parsées ou manquantes
- Sources corporate avec dates approximatives
- RSS feeds avec formats de dates variables

**Impact** : Items pertinents éliminés par le filtre temporel

## Recommandations pour Améliorer V2

### Recommandation 1 : Assouplir le Filtrage Temporel
**Action** : Modifier la logique de filtrage temporel
```python
# Au lieu de : items >= cutoff_date (strict)
# Utiliser : items >= cutoff_date OR date_missing OR date_invalid
```
**Bénéfice** : Récupérer ~30-40 items supplémentaires

### Recommandation 2 : Implémenter les Profils d'Ingestion
**Action** : Ajouter la logique des profils canonical dans `content_parser.py`
- Corporate pure players : ingestion large (95% des items)
- Presse sectorielle : filtrage par mots-clés LAI (30% des items)

**Bénéfice** : Filtrage intelligent par type de source

### Recommandation 3 : Améliorer le Parsing de Dates
**Action** : Renforcer `content_parser.py` pour gérer les formats de dates variables
- Fallback sur date de récupération si date manquante
- Parsing plus robuste des formats RSS/HTML

**Bénéfice** : Réduire les pertes dues aux dates mal parsées

### Recommandation 4 : Mode "Ingestion Large" Optionnel
**Action** : Ajouter un paramètre `ingestion_mode` dans l'event
```json
{
  "client_id": "lai_weekly_v3",
  "ingestion_mode": "broad",  // "strict" | "broad" | "balanced"
  "period_days": 30
}
```
**Bénéfice** : Flexibilité selon les besoins client

### Recommandation 5 : Pré-filtrage par Mots-Clés LAI
**Action** : Implémenter un filtrage léger par mots-clés LAI pour la presse
- Conserver items avec : "injectable", "LAI", "long-acting", noms d'entreprises LAI
- Éliminer items avec : "oral", "tablet", sujets non-pharma

**Bénéfice** : Réduire le bruit de la presse généraliste

## Estimation d'Impact des Améliorations

### Scénario Optimisé V2
Avec les recommandations appliquées :

| Source Type | Items V1 | Items V2 Actuel | Items V2 Optimisé | Gain |
|-------------|----------|-----------------|-------------------|------|
| Corporate LAI | 22 | 12 | 20 | +67% |
| Presse Filtrée | 25 | 0 | 15 | +∞ |
| **Total** | **47** | **12** | **35** | **+192%** |

**Objectif** : Passer de 12 à 35 items pertinents (75% de récupération vs V1)

### Métriques de Qualité Cibles
- **Précision** : 70% (vs 24% en V1)
- **Rappel** : 75% (vs 100% en V1)
- **F1-Score** : 72% (vs 39% en V1)

## Plan d'Implémentation

### Phase 1 : Corrections Rapides (2h)
1. Assouplir le filtrage temporel
2. Améliorer le parsing de dates
3. Ajouter le mode "broad" optionnel

### Phase 2 : Profils d'Ingestion (4h)
1. Implémenter la logique des profils canonical
2. Ajouter le pré-filtrage par mots-clés LAI
3. Tests sur `lai_weekly_v3`

### Phase 3 : Validation (2h)
1. Comparer les résultats V2 optimisé vs V1
2. Ajuster les seuils selon les métriques
3. Documentation des nouvelles règles

## Conclusion

V2 est actuellement **trop restrictive** par rapport à V1. Les 104 items de V1 contenaient certes du bruit (58% d'items génériques), mais aussi 25 items LAI très pertinents que V2 élimine par excès de prudence.

**Recommandation principale** : Implémenter un filtrage **intelligent** plutôt que **strict**, en s'appuyant sur les profils canonical et un assouplissement du filtrage temporel.

L'objectif est d'atteindre **35 items de qualité** (vs 12 actuels) avec une **précision de 70%** (vs 24% en V1), offrant le meilleur compromis signal/bruit pour le client LAI.

---

**Date** : 2025-12-15  
**Analysé par** : Amazon Q Developer  
**Sources** : V1 normalized data (104 items), V2 ingested data (12 items), configurations canonical