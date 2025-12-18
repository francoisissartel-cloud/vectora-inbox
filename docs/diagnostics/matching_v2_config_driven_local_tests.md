# Rapport de Tests Locaux : Matching V2 Configuration-Driven

**Date :** 2025-12-17 17:29:30
**Objectif :** Validation du matching configuration-driven sur données simulées lai_weekly_v3

---

## Résumé des Configurations Testées

| Configuration | Items Matchés | Taux | Tech | Regulatory | Fallback |
|---------------|---------------|------|------|------------|----------|
| Actuel (hardcodé 0.4) | 7/10 | 70.0% | 7 | 2 | 0 |
| Proposé LAI (0.25 global) | 7/10 | 70.0% | 7 | 3 | 0 |
| Proposé LAI avec seuils par type | 7/10 | 70.0% | 7 | 3 | 0 |
| Proposé LAI avec fallback | 10/10 | 100.0% | 10 | 3 | 3 |
| Strict (0.35) | 7/10 | 70.0% | 7 | 3 | 0 |
| Permissif (0.20) | 10/10 | 100.0% | 10 | 3 | 3 |

## Analyse Détaillée

### Actuel (hardcodé 0.4)

**Résultats :**
- Items matchés : 7/10 (70.0%)
- Domaine tech_lai_ecosystem : 7 items
- Domaine regulatory_lai : 2 items
- Mode fallback utilisé : 0 items

**Exemples d'items matchés :**

- Item 1: tech_lai_ecosystem, regulatory_lai
- Item 2: tech_lai_ecosystem, regulatory_lai
- Item 3: tech_lai_ecosystem

### Proposé LAI (0.25 global)

**Résultats :**
- Items matchés : 7/10 (70.0%)
- Domaine tech_lai_ecosystem : 7 items
- Domaine regulatory_lai : 3 items
- Mode fallback utilisé : 0 items

**Exemples d'items matchés :**

- Item 1: tech_lai_ecosystem, regulatory_lai
- Item 2: tech_lai_ecosystem, regulatory_lai
- Item 3: tech_lai_ecosystem

### Proposé LAI avec seuils par type

**Résultats :**
- Items matchés : 7/10 (70.0%)
- Domaine tech_lai_ecosystem : 7 items
- Domaine regulatory_lai : 3 items
- Mode fallback utilisé : 0 items

**Exemples d'items matchés :**

- Item 1: tech_lai_ecosystem, regulatory_lai
- Item 2: tech_lai_ecosystem, regulatory_lai
- Item 3: tech_lai_ecosystem

### Proposé LAI avec fallback

**Résultats :**
- Items matchés : 10/10 (100.0%)
- Domaine tech_lai_ecosystem : 10 items
- Domaine regulatory_lai : 3 items
- Mode fallback utilisé : 3 items

**Exemples d'items matchés :**

- Item 1: tech_lai_ecosystem, regulatory_lai
- Item 2: tech_lai_ecosystem, regulatory_lai
- Item 3: tech_lai_ecosystem

### Strict (0.35)

**Résultats :**
- Items matchés : 7/10 (70.0%)
- Domaine tech_lai_ecosystem : 7 items
- Domaine regulatory_lai : 3 items
- Mode fallback utilisé : 0 items

**Exemples d'items matchés :**

- Item 1: tech_lai_ecosystem, regulatory_lai
- Item 2: tech_lai_ecosystem, regulatory_lai
- Item 3: tech_lai_ecosystem

### Permissif (0.20)

**Résultats :**
- Items matchés : 10/10 (100.0%)
- Domaine tech_lai_ecosystem : 10 items
- Domaine regulatory_lai : 3 items
- Mode fallback utilisé : 3 items

**Exemples d'items matchés :**

- Item 1: tech_lai_ecosystem, regulatory_lai
- Item 2: tech_lai_ecosystem, regulatory_lai
- Item 3: tech_lai_ecosystem

## Recommandations

**Configuration recommandée pour lai_weekly_v3 :**

**Meilleure configuration :** Proposé LAI avec fallback
- Taux de matching optimal : 100.0%
- Distribution équilibrée tech/regulatory
- Pas de sur-matching (< 15 items)

**Prochaines étapes :**
1. Implémenter la configuration recommandée dans lai_weekly_v3.yaml
2. Déployer le code refactoré sur AWS
3. Tester en conditions réelles
4. Ajuster les seuils si nécessaire

---

**Rapport généré automatiquement le 2025-12-17T17:29:31.000037**