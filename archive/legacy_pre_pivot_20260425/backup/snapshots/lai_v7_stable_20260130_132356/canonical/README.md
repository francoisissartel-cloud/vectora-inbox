# Canonical – Bibliothèque métier globale

## Qu'est-ce que `canonical/` ?

Le répertoire `canonical/` contient la **bibliothèque métier globale** de Vectora Inbox. C'est une base de connaissances partagée par :
- **Toutes les verticales** (LAI, thérapie génique, thérapie cellulaire, etc.)
- **Tous les clients** (chaque client référence les scopes qui l'intéressent)

Les fichiers dans `canonical/` définissent :
- Les **listes métier** (entreprises, molécules, technologies, indications, etc.)
- Les **sources d'information** (flux RSS, APIs, catalogues)
- Les **règles de scoring** (poids par type d'événement, facteurs de pertinence)

## Structure du répertoire

```
canonical/
├── scopes/                    # Listes métier (companies, molecules, keywords, etc.)
│   ├── company_scopes.yaml
│   ├── molecule_scopes.yaml
│   ├── trademark_scopes.yaml
│   ├── technology_scopes.yaml
│   ├── indication_scopes.yaml
│   └── exclusion_scopes.yaml
├── sources/                   # Catalogue global des sources et bouquets
│   └── source_catalog.yaml
├── scoring/                   # Règles de scoring et exemples
│   ├── scoring_rules.yaml
│   └── scoring_examples.md
└── imports/                   # Fichiers CSV d'amorçage (seeds)
    └── company_seed_lai.csv
```

## Sous-répertoires principaux

### `scopes/` – Listes métier

Contient les **listes d'entités métier** organisées par dimension :

- **`company_scopes.yaml`** : listes de sociétés groupées par secteur ou technologie
  - Exemple : `lai_companies_global`, `oncology_companies_us`, etc.

- **`molecule_scopes.yaml`** : listes de molécules groupées par aire thérapeutique
  - Exemple : `lai_molecules_global`, `oncology_molecules_approved`, etc.

- **`trademark_scopes.yaml`** : listes de marques commerciales
  - Exemple : `lai_trademarks_global`, `oncology_trademarks_us`, etc.

- **`technology_scopes.yaml`** : mots-clés et expressions pour identifier les technologies
  - Exemple : `lai_keywords`, `gene_therapy_keywords`, etc.

- **`indication_scopes.yaml`** : mots-clés pour identifier les indications thérapeutiques
  - Exemple : `addiction_keywords`, `schizophrenia_keywords`, etc.

- **`exclusion_scopes.yaml`** : mots-clés pour filtrer le bruit (job postings, webinars, etc.)
  - Exemple : `generic_exclusions`, `lai_exclusions`, etc.

### `sources/` – Catalogue des sources

Contient le **catalogue global des sources d'information** :

- **`source_catalog.yaml`** : définit toutes les sources disponibles (RSS, APIs) et les bouquets réutilisables
  - Section `sources:` : liste exhaustive des sources avec URLs, types, tags
  - Section `bouquets:` : groupes de sources prédéfinis (ex : `lai_corporate_mvp`, `press_biotech_premium`)

### `scoring/` – Règles de scoring

Contient les **règles de scoring** pour prioriser les items :

- **`scoring_rules.yaml`** : poids par type d'événement, priorité de domaine, facteurs additionnels
- **`scoring_examples.md`** : exemples de calcul de score pas-à-pas (pour comprendre la logique)

### `imports/` – Fichiers d'amorçage

Contient les **fichiers CSV d'amorçage** (seeds) utilisés pour initialiser les scopes :

- **`company_seed_lai.csv`** : liste initiale des sociétés LAI
- Autres fichiers CSV pour d'autres verticales ou dimensions

## Pattern de nommage des scopes

Les clés de scopes suivent le pattern : **`{verticale}_{dimension}_{segment}`**

### Exemples

- **`lai_companies_global`** : toutes les sociétés LAI (segment global)
- **`lai_molecules_addiction`** : molécules LAI pour l'addiction (segment spécifique)
- **`lai_trademarks_psychiatry`** : marques LAI pour la psychiatrie (segment spécifique)
- **`oncology_companies_us`** : sociétés oncologie aux États-Unis (segment géographique)

### Pourquoi ce pattern ?

- **Clarté** : on comprend immédiatement de quoi il s'agit
- **Évolutivité** : facile d'ajouter de nouvelles verticales ou segments
- **Réutilisabilité** : plusieurs clients peuvent référencer le même scope

## Comment les Lambdas utilisent les scopes

**Important :** Les Lambdas **ne lisent pas les commentaires YAML**. Elles ne lisent que les **clés** et les **valeurs**.

### Processus

1. **La config client référence des clés de scopes** :
   ```yaml
   watch_domains:
     - id: tech_lai_ecosystem
       company_scope: "lai_companies_global"
       molecule_scope: "lai_molecules_global"
   ```

2. **La Lambda charge les fichiers canonical** :
   ```python
   company_scopes = load_yaml("canonical/scopes/company_scopes.yaml")
   companies = company_scopes["lai_companies_global"]  # Charge la liste
   ```

3. **La Lambda utilise ces listes** pour le matching, le scoring, etc.

### Principe clé

- **Les Lambdas ne "connaissent" pas la verticale** : elles ne savent pas que `"lai_companies_global"` est "LAI"
- **Elles manipulent juste des listes** identifiées par leurs clés
- **La logique métier est dans le contenu des listes**, pas dans le code

## Comment ajouter une entité

### Exemple 1 : Ajouter une entreprise dans un scope LAI

1. **Ouvrir** `canonical/scopes/company_scopes.yaml`

2. **Trouver** la clé `lai_companies_global`

3. **Ajouter** le nom de l'entreprise dans la liste :
   ```yaml
   lai_companies_global:
     - Camurus
     - Alkermes
     - Indivior
     - NouvelleEntreprise  # ← Ajout ici
   ```

4. **Sauvegarder** le fichier

5. **Résultat** : la prochaine exécution des Lambdas prendra en compte cette nouvelle entreprise

### Exemple 2 : Ajouter un mot-clé technologique

1. **Ouvrir** `canonical/scopes/technology_scopes.yaml`

2. **Trouver** la clé `lai_keywords`

3. **Ajouter** le mot-clé dans la liste :
   ```yaml
   lai_keywords:
     - long-acting
     - depot injection
     - sustained release
     - nouveau-terme-technique  # ← Ajout ici
   ```

4. **Sauvegarder** le fichier

5. **Résultat** : les Lambdas détecteront ce nouveau mot-clé dans les textes

## Bonnes pratiques

### 1. Nommer les clés de manière cohérente

- Utiliser le pattern `{verticale}_{dimension}_{segment}`
- Utiliser des underscores (`_`), pas de tirets (`-`)
- Utiliser des noms en anglais pour les clés (même si les valeurs peuvent être multilingues)

### 2. Documenter les scopes avec des commentaires

- Ajouter des commentaires YAML pour expliquer le contenu d'un scope
- Les commentaires sont pour les humains, pas pour les Lambdas

### 3. Éviter les doublons

- Vérifier qu'une entité n'existe pas déjà avant de l'ajouter
- Utiliser des noms canoniques (ex : "Eli Lilly" plutôt que "Lilly" ou "Eli Lilly and Company")

### 4. Tester après modification

- Après avoir modifié un scope, tester l'ingestion et le matching
- Vérifier que les nouvelles entités sont bien détectées

## Questions fréquentes

### Quelle est la différence entre `canonical/` et `client-config-examples/` ?

- **`canonical/`** : bibliothèque globale partagée par tous les clients
- **`client-config-examples/`** : configurations spécifiques à chaque client (référencent les scopes canonical)

### Puis-je créer un scope spécifique à un client ?

- **Non** : les scopes dans `canonical/` sont partagés par tous les clients
- **Oui** : un client peut ajouter des entités spécifiques dans sa config via `add_companies`, `add_molecules`, etc.

### Comment savoir quels scopes existent ?

- Ouvrir les fichiers dans `canonical/scopes/`
- Lire les clés YAML (ex : `lai_companies_global`, `oncology_molecules_approved`, etc.)

### Que se passe-t-il si je référence une clé qui n'existe pas ?

- La Lambda lèvera une erreur au démarrage
- Le message d'erreur indiquera quelle clé est manquante

## Ressources complémentaires

- **Contrats des Lambdas** : voir `contracts/lambdas/` pour comprendre comment les Lambdas utilisent les scopes
- **Exemples de scoring** : voir `canonical/scoring/scoring_examples.md` pour des exemples concrets
- **Configuration client** : voir `client-config-examples/` pour des exemples de configs référençant les scopes

---

**Ce README est destiné aux développeurs, architectes et administrateurs de Vectora Inbox.**
