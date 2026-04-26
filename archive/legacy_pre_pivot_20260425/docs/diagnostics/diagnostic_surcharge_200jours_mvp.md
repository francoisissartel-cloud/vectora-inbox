# Diagnostic Surcharge MVP - Période 200 jours

**Date :** 2026-04-23  
**Problème :** Sources échouent avec période 200 jours mais fonctionnent avec 100 jours  
**Contexte :** MVP avec seulement 9 sources - ne devrait pas être surchargé  

## Symptômes observés

### Run qui fonctionne (100 jours)
- **Run ID :** mvp_test_100days__20260423_142848_915b1a17
- **Durée :** 6.5 min
- **Sources :** 9/9 opérationnelles (100%)
- **Items extraits :** 181
- **Status :** success

### Run qui échoue (200 jours)
- **Run ID :** mvp_test_100days__20260423_170924_cadb32db  
- **Durée :** 13.0 min
- **Sources :** 2/9 opérationnelles (22%)
- **Items extraits :** 279 (mais 7 sources à 0 items)
- **Status :** partial

## Goulots d'étranglement identifiés

### 1. Timeout insuffisant
```yaml
# Configuration actuelle
fetch_timeout_seconds: 30

# Temps observés
- Sources échouées: 23-24s → timeout atteint
- Pfizer: 384.6s (6.4 min) pour 161 items
- Nanexa: 294.2s (4.9 min) pour 118 items
```

**Problème :** Le timeout de 30s est largement insuffisant pour les sources HTML complexes avec 200 jours de données.

### 2. Traitement séquentiel
```
Total parse time: 778s (13 min)
Traitement: séquentiel source par source
```

**Problème :** Pas de parallélisation des sources. Avec 9 sources traitées en parallèle, le temps total serait ~2-3 min au lieu de 13 min.

### 3. Fetch time anormal
```
Fetch time: 0.0s pour toutes les sources
```

**Problème :** Temps de téléchargement non comptabilisé ou problème de mesure réseau.

### 4. Échec de configuration
```
7 sources échouent avec "no_items_found"
Mais test individuel Medincell avec 200 jours → succès
```

**Problème :** Différence entre traitement individuel vs traitement en lot.

## Solutions appliquées

### 1. Augmentation des timeouts
```yaml
# Avant
fetch_timeout_seconds: 30

# Après  
fetch_timeout_seconds: 120
```

**Fichiers modifiés :**
- `canonical/ingestion/ingestion_profiles_v3.yaml`
- Profils : `html_generic`, `rss_with_fetch`

### 2. Solutions à implémenter

#### Parallélisation des sources
```python
# Traitement concurrent au lieu de séquentiel
max_concurrent_sources: 3-5
```

#### Optimisation mémoire
```python
# Limitation par source pour éviter surcharge
max_articles_per_source: 200  # au lieu de 400
```

#### Retry logic
```python
# Retry automatique pour sources qui timeout
retry_attempts: 2
retry_delay: 30s
```

## Tests de validation

### Test individuel réussi
- **Source :** Medincell seule avec 200 jours
- **Résultat :** ✅ 12 items extraits, 9 ingérés (81.8%)
- **Durée :** 47s
- **Conclusion :** Le problème n'est pas la période mais la charge simultanée

### Test à effectuer
1. Relancer MVP avec timeouts augmentés
2. Mesurer l'amélioration des taux de succès
3. Implémenter parallélisation si nécessaire

## Métriques cibles

### Performance acceptable
- **Durée totale :** < 8 min pour 9 sources
- **Taux de succès :** > 90% des sources opérationnelles
- **Timeout :** < 5% des sources en timeout

### Seuils d'alerte
- **Durée :** > 15 min → problème de performance
- **Échecs :** > 3 sources échouées → problème systémique
- **Parse time :** > 2 min par source → optimisation requise

## Recommandations

### Court terme
1. ✅ Augmenter timeouts à 120s
2. Tester le run MVP modifié
3. Monitorer les métriques de performance

### Moyen terme
1. Implémenter parallélisation des sources
2. Ajouter retry logic automatique
3. Optimiser la gestion mémoire

### Long terme
1. Mise en place de monitoring proactif
2. Auto-scaling basé sur la charge
3. Cache intelligent pour réduire les re-téléchargements

## Conclusion

Le problème n'est pas la période de 200 jours en soi, mais l'architecture séquentielle qui ne supporte pas la charge simultanée de 9 sources avec des volumes de données doublés. Les solutions de timeout et parallélisation devraient résoudre le problème pour le MVP.