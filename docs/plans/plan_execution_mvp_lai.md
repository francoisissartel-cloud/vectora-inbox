# Plan d'exécution MVP LAI – Phase 1 + Phase 2

## Objectif global
Passer de "AMBER" à "READY FOR INFRA + CODE" pour le MVP LAI en rendant la configuration cohérente et la documentation claire.

---

## PHASE 1 – Cohérence technique (bloquant)

### 1.1. Corriger `lai_weekly.yaml`
- Aligner toutes les références de scopes avec les clés existantes dans `canonical/scopes/*`
- Supprimer/commenter les scopes non-MVP (addiction, schizophrenia, etc.)
- Simplifier la config pour 1 client, 1 fréquence, bouquets activés
- Mettre à jour `CHANGELOG.md`

### 1.2. Créer le bouquet `lai_corporate_mvp`
- Ajouter un sous-bouquet dans `source_catalog.yaml` avec 5-10 sources LAI valides
- Référencer ce bouquet dans `lai_weekly.yaml`
- Mettre à jour `CHANGELOG.md`

### 1.3. Ajouter les seuils de sélection
- Créer section `selection_thresholds` dans `scoring_rules.yaml`
- Définir `min_score` et `min_items_per_section`
- Mettre à jour `CHANGELOG.md`

### 1.4. Clarifier la résolution des bouquets (contrat ingest-normalize)
- Ajouter explication détaillée de la résolution des bouquets
- Inclure exemple JSON/YAML
- Mettre à jour `CHANGELOG.md`

### 1.5. Clarifier le chargement des scopes (contrat engine)
- Expliquer comment charger les scopes canonical depuis la config client
- Ajouter exemple illustratif
- Mettre à jour `CHANGELOG.md`

---

## PHASE 2 – Confort développeur (fortement recommandé)

### 2.1. Exemples JSON pour les Lambdas
- Ajouter exemples input/output dans `vectora-inbox-ingest-normalize.md`
- Ajouter exemples input/output dans `vectora-inbox-engine.md`
- Mettre à jour `CHANGELOG.md`

### 2.2. Créer `canonical/README.md`
- Expliquer la structure de `canonical/`
- Documenter le pattern de nommage
- Donner exemples concrets d'ajout d'entités
- Mettre à jour `CHANGELOG.md`

### 2.3. Créer `canonical/scoring/scoring_examples.md`
- Fournir 2-3 exemples de calcul de score pas-à-pas
- Rendre le scoring intuitif pour un développeur
- Mettre à jour `CHANGELOG.md`

### 2.4. Créer `contracts/README.md`
- Expliquer le rôle des contrats
- Lister les contrats existants
- Guider l'utilisation
- Mettre à jour `CHANGELOG.md`

---

## Ordre d'exécution prévu

**Batch 1:** 1.1 (lai_weekly.yaml)
**Batch 2:** 1.2 (lai_corporate_mvp)
**Batch 3:** 1.3 (selection_thresholds)
**Batch 4:** 1.4 (contrat ingest-normalize)
**Batch 5:** 1.5 (contrat engine)
**Batch 6:** 2.1 (exemples JSON)
**Batch 7:** 2.2 (canonical/README.md)
**Batch 8:** 2.3 (scoring_examples.md)
**Batch 9:** 2.4 (contracts/README.md)

Chaque batch inclut la mise à jour du `CHANGELOG.md`.
