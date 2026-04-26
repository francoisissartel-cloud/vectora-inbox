# Plan Correctif : vectora-inbox-ingest-V2 - Amélioration de l'Ingestion

## Introduction

Ce plan correctif vise à améliorer la Lambda `vectora-inbox-ingest-v2` pour passer de **12 items ingérés** à **35+ items pertinents** pour le client `lai_weekly_v3`, en s'appuyant sur l'analyse comparative V1 vs V2.

## Objectifs du Patch

### Objectifs Quantitatifs
- **Items ingérés** : 12 → 35+ items (+192%)
- **Précision** : Améliorer de ~50% à 70%
- **Rappel** : Récupérer 75% des items pertinents de V1
- **Performance** : Maintenir < 30s d'exécution

### Objectifs Qualitatifs
- Implémenter les profils d'ingestion canonical
- Assouplir le filtrage temporel trop strict
- Améliorer le parsing de dates
- Ajouter un mode d'ingestion configurable

## Problèmes Identifiés à Corriger

1. **Filtrage temporel trop strict** : Élimine 92% du contenu
2. **Profils d'ingestion non implémentés** : Pas de différenciation sources
3. **Parsing de dates défaillant** : Items pertinents perdus
4. **Pas de mode flexible** : Ingestion uniforme pour tous types de sources

---

## Phase 0 – Cadrage & Validation

### Objectifs
- Valider l'analyse V1 vs V2
- Définir les critères de succès précis
- Préparer l'environnement de développement

### Actions détaillées
- Analyser en détail les 104 items V1 vs 12 items V2
- Identifier les 25 items LAI les plus pertinents perdus
- Valider les profils canonical à implémenter
- Définir les métriques de validation

### Fichiers concernés
- `/docs/reports/v1_vs_v2_ingestion_analysis.md` (lecture)
- `/canonical/ingestion/ingestion_profiles.yaml` (analyse)
- Données S3 V1 et V2 (comparaison)

### Critères de "done"
- [ ] Liste des 25 items LAI prioritaires identifiée
- [ ] Profils d'ingestion à implémenter validés
- [ ] Métriques de succès définies
- [ ] Environnement de test préparé

### Risques
- Analyse incomplète des besoins réels
- Critères de succès trop ambitieux

---

## Phase 1 – Assouplissement du Filtrage Temporel

### Objectifs
- Modifier la logique de filtrage temporel pour récupérer plus d'items
- Améliorer la gestion des dates manquantes ou invalides
- Conserver la cohérence avec la fenêtre period_days

### Actions détaillées
- Modifier `utils.py::apply_temporal_filter()` pour mode "souple"
- Ajouter fallback sur date de récupération si date manquante
- Implémenter logique : `items >= cutoff_date OR date_missing OR date_recent_fetch`
- Ajouter paramètre `temporal_mode` dans l'event

### Fichiers concernés
- `/src_v2/vectora_core/utils.py` (modification)
- `/src_v2/vectora_core/__init__.py` (paramètre temporal_mode)
- `/src_v2/lambdas/ingest/handler.py` (event parsing)

### Respect src_lambda_hygiene_v4
- Modifications uniquement dans `/src_v2`
- Pas de nouvelles dépendances tierces
- Code minimal et efficace

### Critères de "done"
- [ ] Filtrage temporel assouplir implémenté
- [ ] Paramètre `temporal_mode` fonctionnel
- [ ] Tests unitaires sur `apply_temporal_filter()`
- [ ] Récupération estimée +20-30 items

### Risques
- Trop d'assouplissement = bruit excessif
- Logique de dates complexe

---

## Phase 2 – Implémentation des Profils d'Ingestion

### Objectifs
- Implémenter la logique des profils canonical dans le code V2
- Différencier le traitement entre sources corporate et presse
- Ajouter pré-filtrage par mots-clés LAI pour la presse

### Actions détaillées
- Créer `ingestion_profiles.py` dans `vectora_core`
- Implémenter `apply_ingestion_profile()` dans `content_parser.py`
- Ajouter logique corporate_pure_player_broad (ingestion large)
- Ajouter logique press_technology_focused (filtrage LAI)
- Intégrer dans le workflow principal

### Fichiers concernés
- `/src_v2/vectora_core/ingestion_profiles.py` (nouveau)
- `/src_v2/vectora_core/content_parser.py` (modification)
- `/src_v2/vectora_core/config_loader.py` (chargement profils)

### Logique des Profils
```python
# Corporate Pure Players : Ingestion large (95% des items)
if source_type == "press_corporate" and company in lai_pure_players:
    return apply_broad_ingestion(items)

# Presse Sectorielle : Filtrage LAI (30% des items)
if source_type == "press_sector":
    return apply_lai_keyword_filter(items)
```

### Respect src_lambda_hygiene_v4
- Utilisation uniquement des libs Python standard
- Pas de dépendances ML/NLP complexes
- Filtrage par mots-clés simples

### Critères de "done"
- [ ] Profils d'ingestion implémentés
- [ ] Différenciation corporate vs presse fonctionnelle
- [ ] Filtrage LAI pour presse opérationnel
- [ ] Tests sur sources MedinCell et FierceBiotech

### Risques
- Logique de profils trop complexe
- Mots-clés LAI insuffisants

---

## Phase 3 – Amélioration du Parsing de Dates

### Objectifs
- Renforcer le parsing des dates depuis RSS et HTML
- Gérer les formats de dates variables
- Réduire les pertes d'items due aux dates mal parsées

### Actions détaillées
- Améliorer `content_parser.py::extract_date_from_content()`
- Ajouter support pour formats de dates multiples
- Implémenter fallback sur date de récupération
- Ajouter validation et logging des dates

### Fichiers concernés
- `/src_v2/vectora_core/content_parser.py` (modification)
- `/src_v2/vectora_core/utils.py` (fonctions dates)

### Formats de Dates à Supporter
- ISO 8601 : `2025-12-15`
- RSS : `Mon, 15 Dec 2025 10:30:00 GMT`
- Français : `15 décembre 2025`
- Relatif : `il y a 2 jours`

### Respect src_lambda_hygiene_v4
- Utilisation de `datetime` standard Python
- Pas de lib externe comme `dateutil`
- Parsing robuste mais simple

### Critères de "done"
- [ ] Parsing de dates amélioré
- [ ] Support formats multiples
- [ ] Fallback sur date de récupération
- [ ] Réduction des items perdus pour dates

### Risques
- Parsing de dates trop complexe
- Faux positifs sur dates relatives

---

## Phase 4 – Mode d'Ingestion Configurable

### Objectifs
- Ajouter paramètre `ingestion_mode` dans l'event
- Permettre modes "strict", "balanced", "broad"
- Donner flexibilité selon les besoins client

### Actions détaillées
- Modifier handler pour accepter `ingestion_mode`
- Implémenter logique de modes dans `__init__.py`
- Adapter les profils selon le mode choisi
- Documenter les modes disponibles

### Fichiers concernés
- `/src_v2/lambdas/ingest/handler.py` (event parsing)
- `/src_v2/vectora_core/__init__.py` (logique modes)
- `/src_v2/vectora_core/ingestion_profiles.py` (adaptation modes)

### Modes d'Ingestion
```python
# strict: Filtrage maximal (actuel V2)
# balanced: Profils canonical + filtrage temporel souple
# broad: Ingestion large comme V1
```

### Respect src_lambda_hygiene_v4
- Paramètre simple dans l'event
- Logique conditionnelle minimale
- Pas de complexité excessive

### Critères de "done"
- [ ] Paramètre `ingestion_mode` implémenté
- [ ] 3 modes fonctionnels
- [ ] Mode "balanced" par défaut
- [ ] Documentation des modes

### Risques
- Trop de modes = complexité
- Mode "broad" = trop de bruit

---

## Phase 5 – Tests Locaux & Validation

### Objectifs
- Tester les améliorations en local sur `lai_weekly_v3`
- Valider les métriques d'amélioration
- Comparer avec les données V1 de référence

### Actions détaillées
- Modifier `/scripts/test_ingest_v2_local.py` pour nouveaux paramètres
- Tester mode "balanced" sur toutes les sources
- Comparer résultats avec les 104 items V1
- Mesurer précision, rappel, F1-score

### Fichiers concernés
- `/scripts/test_ingest_v2_local.py` (modification)
- `/scripts/events/test_lai_weekly_balanced.json` (nouveau)

### Tests à Réaliser
1. **Test mode strict** : Vérifier compatibilité ascendante
2. **Test mode balanced** : Objectif 35+ items
3. **Test mode broad** : Comparaison avec V1
4. **Test sources individuelles** : MedinCell, FierceBiotech

### Critères de "done"
- [ ] Tests locaux réussis
- [ ] Mode balanced : 35+ items ingérés
- [ ] Précision estimée > 60%
- [ ] Pas de régression performance

### Risques
- Tests locaux non représentatifs
- Métriques difficiles à mesurer sans Bedrock

---

## Phase 6 – Déploiement AWS

### Objectifs
- Déployer les améliorations sur AWS
- Maintenir la compatibilité avec l'infrastructure existante
- Tester en environnement réel

### Actions détaillées
- Packager le code V2 amélioré
- Déployer via CloudFormation existant
- Mettre à jour la Lambda Layer si nécessaire
- Vérifier les variables d'environnement

### Fichiers concernés
- `/scripts/package_ingest_v2.py` (utilisation)
- `/scripts/deploy_ingest_v2.py` (utilisation)
- `/infra/s1-ingest-v2.yaml` (vérification)

### Respect src_lambda_hygiene_v4
- Utilisation des scripts de déploiement existants
- Pas de modification d'infrastructure
- Compatibilité avec Lambda Layer v3

### Critères de "done"
- [ ] Code packagé et déployé
- [ ] Lambda mise à jour sans erreur
- [ ] Variables d'environnement correctes
- [ ] Logs CloudWatch accessibles

### Risques
- Problèmes de déploiement
- Incompatibilité avec Layer existant

---

## Phase 7 – Tests AWS & Validation Finale

### Objectifs
- Tester la Lambda améliorée sur AWS
- Valider les métriques sur `lai_weekly_v3`
- Comparer avec les performances V1

### Actions détaillées
- Exécuter tests avec mode "balanced"
- Analyser les items ingérés vs V1
- Mesurer les performances (temps, mémoire)
- Valider la qualité des données S3

### Fichiers concernés
- `/scripts/test_ingest_v2_aws.py` (modification)
- Données S3 générées (analyse)

### Tests AWS
1. **Test minimal** : 2 sources, mode balanced
2. **Test complet** : Toutes sources, mode balanced
3. **Test performance** : Mesure temps d'exécution
4. **Test qualité** : Analyse des items ingérés

### Critères de "done"
- [ ] Tests AWS réussis
- [ ] 35+ items ingérés pour lai_weekly_v3
- [ ] Performance < 30s
- [ ] Qualité des données validée

### Risques
- Performance dégradée
- Qualité insuffisante

---

## Phase 8 – Rapport Final & Métriques

### Objectifs
- Documenter les améliorations apportées
- Mesurer l'impact quantitatif et qualitatif
- Fournir recommandations pour la suite

### Actions détaillées
- Analyser les métriques avant/après patch
- Comparer avec les objectifs initiaux
- Documenter les leçons apprises
- Proposer améliorations futures

### Fichiers concernés
- `/docs/reports/ingest_v2_patch_results.md` (nouveau)
- Métriques CloudWatch (analyse)
- Données S3 (comparaison)

### Métriques à Mesurer
- **Quantité** : Items ingérés (12 → 35+)
- **Qualité** : Précision estimée (50% → 70%)
- **Performance** : Temps d'exécution
- **Fiabilité** : Taux de succès sources

### Critères de "done"
- [ ] Rapport final rédigé
- [ ] Métriques documentées
- [ ] Recommandations futures
- [ ] Validation des objectifs

---

## Configuration des Tests

### Events de Test
```json
{
  "client_id": "lai_weekly_v3",
  "ingestion_mode": "balanced",
  "temporal_mode": "flexible",
  "period_days": 30,
  "dry_run": false
}
```

### Métriques de Succès
- **Items ingérés** : ≥ 35 items
- **Temps d'exécution** : ≤ 30 secondes
- **Taux de succès sources** : ≥ 80%
- **Précision estimée** : ≥ 60%

### Environnement
- **AWS Profile** : rag-lai-prod
- **Région** : eu-west-3
- **Lambda** : vectora-inbox-ingest-v2-dev
- **Client test** : lai_weekly_v3

---

## Résumé des Phases

1. **Phase 0** : Cadrage & validation (1h)
2. **Phase 1** : Filtrage temporel souple (2h)
3. **Phase 2** : Profils d'ingestion (3h)
4. **Phase 3** : Parsing de dates (2h)
5. **Phase 4** : Modes configurables (1h)
6. **Phase 5** : Tests locaux (2h)
7. **Phase 6** : Déploiement AWS (1h)
8. **Phase 7** : Tests AWS (1h)
9. **Phase 8** : Rapport final (1h)

**Durée totale estimée** : 14 heures

**Objectif final** : Lambda V2 ingérant 35+ items pertinents avec 70% de précision pour `lai_weekly_v3`.