# Règles de Matching – Vectora Inbox

Ce répertoire contient les règles de matching qui définissent comment les items sont associés aux domaines de veille (watch_domains) d'un client.

---

## Principe

Le matching est **100% générique** et **piloté par configuration**. Aucune logique métier spécifique (LAI, oncologie, etc.) n'est codée en dur dans le code Python.

Les règles de matching définissent, pour chaque **type de domaine**, comment combiner les différentes **dimensions** (company, molecule, technology, indication) pour décider si un item matche.

---

## Fichier : `domain_matching_rules.yaml`

Ce fichier contient les règles de matching par type de domaine.

### Structure

```yaml
<domain_type>:
  match_mode: <all_required|any_required>
  description: "Description de la règle"
  dimensions:
    <dimension_name>:
      requirement: <required|optional>
      min_matches: <nombre>
      sources: [<dimension1>, <dimension2>]  # Pour les dimensions composites
      description: "Description de la dimension"
```

### Champs

- **`match_mode`** : Mode de combinaison des dimensions
  - `all_required` : Toutes les dimensions marquées `required` doivent matcher (AND logique)
  - `any_required` : Au moins une dimension doit matcher (OR logique)

- **`dimensions`** : Dictionnaire des dimensions à évaluer
  - `company` : Entreprises détectées dans l'item
  - `molecule` : Molécules détectées dans l'item
  - `technology` : Mots-clés technologiques détectés dans l'item
  - `indication` : Indications thérapeutiques détectées dans l'item
  - `entity` : Dimension composite (company OU molecule)

- **`requirement`** : Niveau d'exigence pour la dimension
  - `required` : La dimension DOIT matcher (au moins `min_matches` entités)
  - `optional` : La dimension PEUT matcher (bonus si elle matche, mais pas obligatoire)

- **`min_matches`** : Nombre minimum d'entités à matcher pour satisfaire la dimension (défaut : 1)

- **`sources`** : Pour les dimensions composites (ex: `entity`), liste des dimensions sources à combiner

---

## Exemples de Règles

### Domaine de Type `technology`

Pour un domaine de type `technology` (ex: `tech_lai_ecosystem`), on veut :
- **Obligatoirement** : Au moins un mot-clé technology
- **ET obligatoirement** : Au moins une entité (company OU molecule)

```yaml
technology:
  match_mode: all_required
  dimensions:
    technology:
      requirement: required
      min_matches: 1
    entity:
      requirement: required
      min_matches: 1
      sources: [company, molecule]
```

**Résultat** :
- ✅ Item avec `MedinCell` + `extended-release injectable` → MATCH
- ❌ Item avec `Pfizer` seul (sans mot-clé technology) → NO MATCH
- ❌ Item avec `long-acting` seul (sans company/molecule) → NO MATCH

---

### Domaine de Type `regulatory`

Pour un domaine de type `regulatory`, on veut :
- **Au moins une entité** (company OU molecule OU technology)
- Pas de contrainte stricte sur la technology (car les news réglementaires peuvent ne pas mentionner explicitement les mots-clés)

```yaml
regulatory:
  match_mode: any_required
  dimensions:
    company:
      requirement: optional
    molecule:
      requirement: optional
    technology:
      requirement: optional
```

**Résultat** :
- ✅ Item avec `Pfizer` seul → MATCH
- ✅ Item avec `risperidone` seul → MATCH
- ✅ Item avec `long-acting` seul → MATCH
- ❌ Item sans aucune entité → NO MATCH

---

### Domaine de Type `indication`

Pour un domaine de type `indication` (ex: `indication_addiction`), on veut :
- **Obligatoirement** : Au moins un mot-clé d'indication
- **ET obligatoirement** : Au moins une entité (company OU molecule)

```yaml
indication:
  match_mode: all_required
  dimensions:
    indication:
      requirement: required
      min_matches: 1
    entity:
      requirement: required
      min_matches: 1
      sources: [company, molecule]
```

---

## Comment Ajouter un Nouveau Type de Domaine

### Exemple : Domaine `diabetes_technology`

Si vous voulez créer un nouveau type de domaine avec une logique spécifique (ex: technology OU indication, sans contrainte AND), ajoutez une nouvelle règle :

```yaml
diabetes_technology:
  match_mode: any_required
  description: "Pour un domaine diabetes_technology, l'item doit contenir technology OU indication"
  dimensions:
    technology:
      requirement: optional
    indication:
      requirement: optional
    entity:
      requirement: required
      min_matches: 1
      sources: [company, molecule]
```

Puis, dans la config client :

```yaml
watch_domains:
  - id: "tech_diabetes_ecosystem"
    type: "diabetes_technology"  # ← Type personnalisé
    technology_scope: "diabetes_keywords"
    indication_scope: "diabetes_indications"
    company_scope: "diabetes_companies_global"
    priority: "high"
```

**Aucune modification du code Python n'est nécessaire** : le matcher appliquera automatiquement la règle `diabetes_technology`.

---

## Règle par Défaut

Si un type de domaine n'est pas défini dans `domain_matching_rules.yaml`, le matcher utilise la règle `default` :

```yaml
default:
  match_mode: any_required
  description: "Règle par défaut : au moins une dimension doit matcher (logique OR)"
  dimensions:
    company:
      requirement: optional
    molecule:
      requirement: optional
    technology:
      requirement: optional
    indication:
      requirement: optional
```

Cette règle correspond à la logique OR classique : un item matche dès qu'il contient au moins une entité (company OU molecule OU technology OU indication).

---

## Extensibilité Multi-Verticales

Le système de règles de matching est conçu pour être **100% réutilisable** pour d'autres verticaux (oncologie, diabète, etc.).

Pour ajouter un nouveau vertical :

1. **Créer les scopes** dans `canonical/scopes/` :
   - `oncology_companies_global`
   - `oncology_molecules_global`
   - `oncology_keywords`

2. **Créer une config client** `oncology_weekly.yaml` :
```yaml
watch_domains:
  - id: "tech_oncology_ecosystem"
    type: "technology"  # ← Réutilise la règle existante
    technology_scope: "oncology_keywords"
    company_scope: "oncology_companies_global"
    molecule_scope: "oncology_molecules_global"
    priority: "high"
```

3. **Aucune modification du code** : Les règles de matching pour `type: technology` s'appliquent automatiquement.

---

## Diagnostic et Logs

Le matcher génère des logs détaillés pour expliquer pourquoi un item a matché ou non :

```
Item 'MedinCell UZEDY Approval...' matché au domaine tech_lai_ecosystem 
(type: technology, companies: 1, molecules: 1, technologies: 2, indications: 0)
```

Pour un diagnostic complet, consultez les fichiers de résultats dans `docs/diagnostics/`.

---

## Ressources Complémentaires

- **Plan de refactor** : `docs/design/vectora_inbox_domain_matching_refactor_plan.md`
- **Scopes canonical** : `canonical/scopes/`
- **Config client** : `client-config-examples/`
- **Code du matcher** : `src/vectora_core/matching/matcher.py`

---

**Auteur** : Amazon Q Developer  
**Date** : 2025-12-08  
**Version** : 1.0
