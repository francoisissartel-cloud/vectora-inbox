# Diagnostic : Refactorisation Profils d'Ingestion Vectora Inbox

## Résumé Exécutif

✅ **Refactorisation terminée avec succès**

La couche de profils d'ingestion a été mise en place dans le canonical, permettant un filtrage intelligent des contenus avant normalisation Bedrock. Tous les objectifs de la Phase 1 ont été atteints sans impact sur le code runtime ni les stacks AWS.

## Modifications Réalisées

### 1. Nouveaux Fichiers Créés

#### `canonical/ingestion/ingestion_profiles.yaml`
- **Contenu** : 7 profils d'ingestion définis
- **Profils MVP** : 3 profils opérationnels pour LAI
- **Profils futurs** : 4 profils préparatoires (PubMed, indications)
- **Structure** : Générique et réutilisable pour autres verticales

#### `canonical/ingestion/README.md`
- **Contenu** : Documentation complète des profils
- **Sections** : Philosophie, structure, exemples d'usage
- **Guides** : Maintenance et ajout de nouveaux profils

#### `docs/design/vectora_inbox_ingestion_profiles_refactor_plan.md`
- **Contenu** : Plan détaillé de la refactorisation
- **Architecture** : Structure cible et types de profils
- **Phases** : Plan d'exécution par étapes

### 2. Fichiers Modifiés

#### `canonical/sources/source_catalog.yaml`
- **Ajout** : Champ `ingestion_profile` pour toutes les sources MVP
- **Assignments** :
  - Sources corporate LAI → `corporate_pure_player_broad`
  - Sources presse sectorielle → `press_technology_focused`
- **Compatibilité** : Maintenue pour sources sans profil

#### `canonical/scopes/exclusion_scopes.yaml`
- **Ajout** : 4 nouveaux scopes d'exclusion
  - `hr_content` : Contenu RH/recrutement
  - `esg_generic` : Contenu ESG généraliste
  - `financial_generic` : Contenu financier généraliste
  - `event_generic` : Contenu événementiel généraliste
- **Usage** : Support des profils `broad_ingestion`

## Architecture des Profils d'Ingestion

### Profils Opérationnels (MVP LAI)

#### 1. `corporate_pure_player_broad`
- **Cible** : MedinCell, Camurus, DelSiTech, Nanexa, Peptron
- **Stratégie** : `broad_ingestion` - ingère tout sauf exclusions
- **Rationale** : Taux de signal très élevé chez les pure players
- **Filtrage attendu** : ~5% (uniquement RH/ESG)

#### 2. `press_technology_focused`
- **Cible** : FierceBiotech, FiercePharma, Endpoints News
- **Stratégie** : `multi_signal_ingestion` - requiert entités + technologie
- **Rationale** : Presse sectorielle très bruyante
- **Filtrage attendu** : ~75% (garde uniquement articles LAI)

#### 3. `corporate_hybrid_technology_focused`
- **Cible** : Big pharma/hybrid (préparation future)
- **Stratégie** : `signal_based_ingestion` - requiert signaux LAI forts
- **Rationale** : Éviter le bruit des activités non-LAI
- **Filtrage attendu** : ~85% (garde uniquement news LAI)

### Profils Préparatoires

#### 4. `pubmed_technology_focused`
- **Cible** : Publications académiques PubMed
- **Stratégie** : `academic_signal_ingestion`
- **Seuil** : Élevé (0.8) pour éviter le bruit académique

#### 5. `pubmed_indication_focused`
- **Cible** : PubMed par indication thérapeutique
- **Stratégie** : `indication_signal_ingestion`
- **Combinaison** : Signaux indication + signaux LAI

#### 6. `default_broad`
- **Cible** : Compatibilité ascendante
- **Stratégie** : `no_filtering` - ingère tout
- **Usage** : Sources sans profil défini

## Mapping Sources → Profils

### Sources Corporate LAI (Bouquet `lai_corporate_mvp`)
```
press_corporate__medincell   → corporate_pure_player_broad
press_corporate__camurus     → corporate_pure_player_broad
press_corporate__delsitech   → corporate_pure_player_broad
press_corporate__nanexa      → corporate_pure_player_broad
press_corporate__peptron     → corporate_pure_player_broad
```

### Sources Presse Sectorielle (Bouquet `lai_press_mvp`)
```
press_sector__fiercebiotech  → press_technology_focused
press_sector__fiercepharma   → press_technology_focused
press_sector__endpoints_news → press_technology_focused
```

## Validation de l'Architecture

### ✅ Critères de Réussite Atteints

1. **Généricité** : Structure réutilisable pour autres verticales
2. **Configuration** : 100% piloté par canonical, aucun code en dur
3. **Compatibilité** : Aucun impact sur clients existants
4. **Extensibilité** : Profils futurs préparés (PubMed, indications)
5. **Documentation** : Complète et détaillée

### ✅ Scopes Référencés Validés

Tous les scopes référencés dans les profils existent :
- `lai_companies_pure_players` ✓
- `lai_companies_mvp_core` ✓
- `lai_companies_hybrid` ✓
- `lai_companies_global` ✓
- `lai_keywords.core_phrases` ✓
- `lai_keywords.technology_terms_high_precision` ✓
- `lai_trademarks_global` ✓
- `lai_molecules_global` ✓
- `exclusion_scopes.*` ✓ (nouveaux scopes créés)

### ✅ Cohérence avec Matching Existant

Les profils d'ingestion complètent les règles de matching sans les dupliquer :
- **Ingestion** : Garde-fou contre le bruit évident
- **Matching** : Sélection fine post-normalisation
- **Aucun conflit** : Logiques complémentaires

## Impact Attendu (Phase 2 - Runtime)

### Économies Bedrock Estimées

#### Sources Corporate Pure Players
- **Filtrage** : ~5% (95% ingéré)
- **Économie** : Faible mais qualité préservée

#### Sources Presse Sectorielle
- **Filtrage** : ~75% (25% ingéré)
- **Économie** : Élevée, réduction significative du bruit

#### Sources Hybrid (futures)
- **Filtrage** : ~85% (15% ingéré)
- **Économie** : Très élevée, focus sur signaux LAI

### Métriques à Surveiller (Phase 2)
- Taux de filtrage par source
- Faux positifs/négatifs du filtrage
- Temps de traitement d'ingestion
- Coûts Bedrock avant/après
- Qualité des items normalisés

## Prochaines Étapes

### Phase 2 : Implémentation Runtime
1. **Adaptation Lambdas** : Intégrer la logique de profils
2. **Détection de signaux** : Implémenter les algorithmes de matching
3. **Métriques** : Ajouter le monitoring des profils
4. **Tests** : Validation avec données réelles

### Phase 3 : Extension
1. **Nouvelles sources** : Big pharma avec profils hybrid
2. **Nouvelles verticales** : Indications, autres technologies
3. **Sources académiques** : PubMed, ClinicalTrials
4. **Optimisation** : Ajustement des seuils selon métriques

## Risques Identifiés et Mitigation

### Risque : Sur-filtrage
- **Impact** : Perte de signaux pertinents
- **Mitigation** : Seuils conservateurs, monitoring strict

### Risque : Complexité de maintenance
- **Impact** : Difficulté à maintenir les profils
- **Mitigation** : Documentation complète, tests automatisés

### Risque : Performance
- **Impact** : Ralentissement de l'ingestion
- **Mitigation** : Algorithmes optimisés, cache des signaux

## Conclusion

La refactorisation des profils d'ingestion est un succès complet. L'architecture mise en place est :

- **Opérationnelle** : Prête pour implémentation runtime
- **Évolutive** : Extensible à d'autres verticales
- **Documentée** : Maintenance facilitée
- **Validée** : Tous les scopes et références vérifiés

La Phase 1 (canonical only) est terminée. La Phase 2 (runtime) peut commencer.

---

**Date** : 2024-12-19  
**Statut** : ✅ Terminé  
**Prochaine phase** : Implémentation runtime dans les Lambdas