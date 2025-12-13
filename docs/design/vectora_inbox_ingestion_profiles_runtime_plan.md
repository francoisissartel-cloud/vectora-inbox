# Plan Runtime : Implémentation des Profils d'Ingestion

## 1. Contexte et Objectifs

### 1.1 État Actuel
- Phase 1 terminée : Profils d'ingestion définis dans le canonical
- 7 profils créés : 3 opérationnels MVP + 4 préparatoires
- Sources MVP enrichies avec `ingestion_profile` dans `source_catalog.yaml`

### 1.2 Objectif Phase 2
Implémenter la logique de filtrage d'ingestion dans la Lambda `ingest-normalize` pour :
- Réduire le bruit avant normalisation Bedrock (économies 40-60%)
- Maintenir la compatibilité ascendante
- Préparer le terrain pour nouvelles sources (PubMed, etc.)

## 2. Architecture Runtime Cible

### 2.1 Pipeline d'Ingestion Modifié
```
[Source RSS/HTML] 
    ↓
[Scraping] → items_bruts
    ↓
[NOUVEAU: Filtrage Profils d'Ingestion] → items_filtrés
    ↓
[Normalisation Bedrock] → items_normalisés
    ↓
[Stockage S3]
```

### 2.2 Placement de la Logique
**Lambda `ingest-normalize`** :
- Chargement des profils d'ingestion depuis S3 canonical
- Application du filtrage après scraping, avant normalisation
- Métriques de filtrage par source/profil

**Lambda `engine`** :
- Aucune modification (matching post-normalisation inchangé)
- Contrats d'entrée/sortie préservés

### 2.3 Chargement des Configurations

#### Résolution des Profils
```python
# 1. Charger source_catalog.yaml depuis S3
# 2. Pour chaque source, résoudre ingestion_profile
# 3. Charger ingestion_profiles.yaml depuis S3
# 4. Charger les scopes référencés (technology, company, trademark, exclusion)
```

#### Cache et Performance
- Cache des profils en mémoire Lambda (réutilisation entre invocations)
- Invalidation sur changement de configuration
- Chargement lazy des scopes (seulement ceux utilisés)

## 3. Implémentation par Profil

### 3.1 `corporate_pure_player_broad`
**Stratégie** : `broad_ingestion` - Ingère tout sauf exclusions explicites

**Logique** :
```python
def apply_corporate_pure_player_broad(item_text, profile_config):
    # Vérifier exclusions (HR, ESG, financial generic)
    for exclusion_scope in profile_config['exclusion_scopes']:
        if detect_signals(item_text, exclusion_scope) > threshold:
            return False  # Filtrer
    return True  # Ingérer
```

**Scopes utilisés** :
- `exclusion_scopes.hr_content`
- `exclusion_scopes.esg_generic`
- `exclusion_scopes.financial_generic`

### 3.2 `press_technology_focused`
**Stratégie** : `multi_signal_ingestion` - Requiert entités + technologie

**Logique** :
```python
def apply_press_technology_focused(item_text, profile_config):
    entity_signals = detect_signals(item_text, ['lai_companies_global', 'lai_molecules_global'])
    tech_signals = detect_signals(item_text, ['lai_keywords.core_phrases', 'lai_keywords.technology_terms_high_precision'])
    trademark_signals = detect_signals(item_text, ['lai_trademarks_global'])
    
    # entity_signals AND (tech_signals OR trademark_signals)
    return entity_signals >= 1 and (tech_signals >= 1 or trademark_signals >= 1)
```

**Scopes utilisés** :
- `lai_companies_global`
- `lai_molecules_global`
- `lai_keywords.core_phrases`
- `lai_keywords.technology_terms_high_precision`
- `lai_trademarks_global`

### 3.3 `corporate_hybrid_technology_focused`
**Stratégie** : `signal_based_ingestion` - Signaux LAI forts requis

**Logique** :
```python
def apply_corporate_hybrid_technology_focused(item_text, profile_config):
    high_precision = detect_signals(item_text, ['lai_keywords.core_phrases', 'lai_keywords.technology_terms_high_precision'])
    supporting = detect_signals(item_text, ['lai_keywords.interval_patterns', 'lai_keywords.route_admin_terms'])
    trademark = detect_signals(item_text, ['lai_trademarks_global'])
    
    # high_precision OR (supporting AND trademark)
    return high_precision >= 1 or (supporting >= 1 and trademark >= 1)
```

### 3.4 `default_broad`
**Stratégie** : `no_filtering` - Comportement actuel

**Logique** :
```python
def apply_default_broad(item_text, profile_config):
    return True  # Ingérer tout (compatibilité ascendante)
```

## 4. Détection de Signaux

### 4.1 Algorithme Simple (Phase 2)
```python
def detect_signals(text, scope_keys):
    """Détection simple par matching de mots-clés"""
    text_lower = text.lower()
    total_matches = 0
    
    for scope_key in scope_keys:
        scope_data = get_scope_data(scope_key)  # Cache
        for keyword in scope_data:
            if keyword.lower() in text_lower:
                total_matches += 1
                
    return total_matches
```

### 4.2 Optimisations Futures
- Matching par regex pour expressions complexes
- Pondération par importance des mots-clés
- Détection de contexte (négation, etc.)

## 5. Intégration dans le Pipeline Existant

### 5.1 Modification de `ingest-normalize`
**Fichier principal** : `src/lambdas/ingest_normalize/handler.py`

**Ajouts nécessaires** :
1. **Chargement des profils** au démarrage Lambda
2. **Résolution du profil** par source dans la boucle d'ingestion
3. **Application du filtrage** avant normalisation Bedrock
4. **Métriques** de filtrage

### 5.2 Structure du Code
```python
# Nouveau module : src/vectora_core/ingestion/profile_filter.py
class IngestionProfileFilter:
    def __init__(self, s3_client, bucket_name):
        self.profiles = {}  # Cache
        self.scopes = {}    # Cache
        
    def load_profiles(self):
        """Charge ingestion_profiles.yaml depuis S3"""
        
    def apply_filter(self, item, source_key):
        """Applique le profil d'ingestion à un item"""
        profile = self.get_profile_for_source(source_key)
        return self.execute_strategy(item, profile)
```

### 5.3 Intégration dans Handler
```python
# Dans handler.py
profile_filter = IngestionProfileFilter(s3_client, canonical_bucket)

for item in scraped_items:
    # NOUVEAU: Filtrage d'ingestion
    if not profile_filter.apply_filter(item, source_key):
        metrics['items_filtered'] += 1
        continue
        
    # Normalisation Bedrock (existant)
    normalized_item = normalize_with_bedrock(item)
    metrics['items_normalized'] += 1
```

## 6. Métriques et Monitoring

### 6.1 Métriques par Invocation
```python
metrics = {
    'items_scraped': 0,           # Items récupérés du scraping
    'items_filtered_ingestion': 0, # Items filtrés par profils d'ingestion
    'items_normalized': 0,        # Items normalisés par Bedrock
    'items_stored': 0,           # Items stockés en S3
    'filtering_by_profile': {},   # Détail par profil
    'filtering_by_source': {}     # Détail par source
}
```

### 6.2 Logs Structurés
```python
logger.info(f"[INGESTION_FILTER] source={source_key} profile={profile_name} "
           f"scraped={scraped_count} filtered={filtered_count} retained={retained_count}")
```

## 7. Plan d'Exécution par Phases

### Phase A : Implémentation Core
- [ ] Créer `src/vectora_core/ingestion/profile_filter.py`
- [ ] Implémenter le chargement des profils depuis S3
- [ ] Implémenter la détection de signaux simple
- [ ] Créer les stratégies de filtrage par profil

### Phase B : Intégration Pipeline
- [ ] Modifier `src/lambdas/ingest_normalize/handler.py`
- [ ] Ajouter le filtrage avant normalisation Bedrock
- [ ] Implémenter les métriques de filtrage
- [ ] Tester la compatibilité ascendante

### Phase C : Packaging et Déploiement DEV
- [ ] Packager la Lambda avec les nouvelles dépendances
- [ ] Déployer en environnement DEV uniquement
- [ ] Vérifier les logs et métriques

### Phase D : Test Complet LAI Weekly
- [ ] Lancer un test 7 jours sur `lai_weekly`
- [ ] Collecter les métriques avant/après
- [ ] Analyser l'impact sur la qualité et les coûts

### Phase E : Documentation et Diagnostic
- [ ] Créer le diagnostic de résultats
- [ ] Mettre à jour la documentation
- [ ] Recommandations pour la suite

## 8. Contraintes et Risques

### 8.1 Contraintes Techniques
- **Compatibilité ascendante** : Sources sans profil → `default_broad`
- **Performance** : Filtrage "cheap", pas de ML complexe
- **Contrats** : Aucun changement d'interface Lambda
- **Environnement** : DEV uniquement pour cette phase

### 8.2 Risques Identifiés
- **Sur-filtrage** : Perte de signaux pertinents
- **Performance** : Ralentissement du pipeline d'ingestion
- **Complexité** : Maintenance des profils et scopes
- **Faux négatifs** : Items pertinents filtrés par erreur

### 8.3 Stratégies de Mitigation
- Seuils conservateurs pour éviter le sur-filtrage
- Métriques détaillées pour monitoring
- Tests approfondis sur données réelles
- Possibilité de désactiver le filtrage par source

## 9. Critères de Succès

### 9.1 Métriques Cibles
- **Réduction volume** : 40-60% sur sources presse, 5% sur corporate
- **Performance** : Temps d'ingestion < +20% vs baseline
- **Qualité** : Pas de perte de signaux LAI évidents
- **Stabilité** : Aucune régression sur le pipeline existant

### 9.2 Validation
- [ ] Tous les profils MVP fonctionnent correctement
- [ ] Métriques de filtrage cohérentes avec les attentes
- [ ] Aucun impact sur la Lambda engine
- [ ] Documentation complète et à jour

## 10. Prochaines Étapes (Post-Phase 2)

### Phase 3 : Calibration Métier
- Ajustement des seuils selon les résultats
- Optimisation des profils selon feedback métier
- Extension à de nouvelles sources

### Phase 4 : Production
- Déploiement STAGE puis PROD
- Monitoring en continu
- Optimisations performance

---

**Statut** : Plan validé, prêt pour exécution  
**Prochaine étape** : Phase A - Implémentation Core  
**Timeline estimée** : 3-5 jours pour Phase 2 complète