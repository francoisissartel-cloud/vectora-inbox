# Contracts – Contrats métier pour les composants Vectora Inbox

## Qu'est-ce que `contracts/` ?

Le répertoire `contracts/` contient les **contrats métier** des composants de Vectora Inbox (Lambdas, APIs, etc.). Un contrat métier décrit :

- **Le rôle et l'objectif** du composant
- **Les entrées** (événements, paramètres, configurations)
- **Les sorties** (fichiers S3, formats, structures de données)
- **Les étapes de traitement** (phases, logique métier)
- **Les cas d'erreur** et leur gestion
- **Les exemples concrets** (JSON, YAML, Markdown)

Ces contrats sont destinés à :
- **L'architecte / product owner** : pour valider la logique métier
- **Les développeurs** : pour implémenter les composants sans ambiguïté
- **Amazon Q Developer** : pour générer du code aligné avec les spécifications

## Structure du répertoire

```
contracts/
├── lambdas/                                    # Contrats des Lambdas AWS
│   ├── vectora-inbox-ingest-normalize.md      # Lambda Phase 1 (ingestion + normalisation)
│   └── vectora-inbox-engine.md                # Lambda Phases 2-4 (matching + scoring + newsletter)
└── README.md                                   # Ce fichier
```

## Contrats disponibles

### `vectora-inbox-ingest-normalize.md`

**Rôle :** Lambda responsable de la **Phase 1** du workflow (ingestion et normalisation).

**Contenu du contrat :**
- Ingestion des sources externes (RSS, APIs) sans IA
- Normalisation des items avec Amazon Bedrock (extraction d'entités, classification d'événements)
- Résolution des bouquets de sources (comment charger et combiner les sources)
- Chargement des scopes canonical pour guider la normalisation
- Écriture des items normalisés dans S3
- Exemples JSON d'entrée/sortie (succès, erreurs)

**Quand lire ce contrat :**
- Avant d'implémenter la Lambda d'ingestion
- Pour comprendre comment les sources sont résolues via les bouquets
- Pour comprendre comment Bedrock est utilisé pour la normalisation

### `vectora-inbox-engine.md`

**Rôle :** Lambda responsable des **Phases 2, 3 et 4** du workflow (matching, scoring, génération de newsletter).

**Contenu du contrat :**
- Matching des items avec les domaines d'intérêt du client (watch_domains)
- Chargement des scopes canonical pour le matching (comment charger les listes via les clés)
- Scoring des items (règles déterministes, pas d'IA)
- Génération de la newsletter avec Amazon Bedrock (réécriture éditoriale)
- Écriture de la newsletter en Markdown dans S3
- Exemples JSON d'entrée/sortie (succès, erreurs)

**Quand lire ce contrat :**
- Avant d'implémenter la Lambda moteur
- Pour comprendre comment les scopes canonical sont chargés et utilisés
- Pour comprendre la logique de scoring
- Pour comprendre comment Bedrock est utilisé pour la génération éditoriale

## Comment utiliser ces contrats

### 1. Lire d'abord l'overview dans `.q-context/`

Avant de plonger dans les contrats détaillés, commencez par lire :
- `.q-context/overview.md` : vue d'ensemble de l'architecture Vectora Inbox
- `.q-context/workflow.md` : description des 4 phases du workflow

Ces documents donnent le contexte global nécessaire pour comprendre les contrats.

### 2. Lire le contrat du composant à implémenter

Une fois le contexte compris, lisez le contrat du composant que vous allez implémenter :
- **Pour l'ingestion** : `contracts/lambdas/vectora-inbox-ingest-normalize.md`
- **Pour le moteur** : `contracts/lambdas/vectora-inbox-engine.md`

### 3. Utiliser les exemples JSON pour les tests

Chaque contrat contient des exemples JSON d'entrée/sortie. Utilisez-les pour :
- **Tester manuellement** : invoquer la Lambda avec un événement d'exemple
- **Écrire des tests unitaires** : valider que la Lambda répond correctement
- **Déboguer** : comparer la sortie réelle avec la sortie attendue

### 4. Respecter les contrats lors de l'implémentation

Les contrats définissent :
- **Les champs obligatoires** : ne pas les omettre
- **Les formats de données** : respecter les types (string, integer, liste, etc.)
- **Les chemins S3** : respecter la structure des répertoires
- **Les cas d'erreur** : gérer les erreurs comme spécifié

**Important :** Si vous devez dévier du contrat, **mettez à jour le contrat** pour refléter la réalité.

## Principes des contrats métier

### 1. Contrats = source de vérité

Les contrats sont la **source de vérité** pour la logique métier. Si le code et le contrat divergent, c'est le contrat qui a raison (ou il faut le mettre à jour).

### 2. Contrats = documentation vivante

Les contrats ne sont pas figés. Ils évoluent avec le produit. Si une fonctionnalité change, le contrat doit être mis à jour.

### 3. Contrats = langage commun

Les contrats utilisent un langage métier (pas de jargon technique inutile). Ils sont compréhensibles par :
- Un product owner (pour valider la logique)
- Un développeur (pour implémenter)
- Une IA (pour générer du code)

### 4. Contrats = exemples concrets

Les contrats contiennent des exemples concrets (JSON, YAML, Markdown) pour éviter les ambiguïtés. Un exemple vaut mieux qu'une longue explication.

## Différence entre `contracts/` et `canonical/`

| Aspect | `contracts/` | `canonical/` |
|--------|--------------|--------------|
| **Contenu** | Spécifications des composants (Lambdas, APIs) | Données métier (listes, règles, sources) |
| **Format** | Markdown (documentation) | YAML, CSV (données structurées) |
| **Audience** | Développeurs, architectes | Lambdas, administrateurs |
| **Évolution** | Change quand la logique change | Change quand les données métier changent |
| **Exemple** | "La Lambda doit charger les scopes via les clés" | "lai_companies_global: [Camurus, Alkermes, ...]" |

**En résumé :**
- **`contracts/`** : "Comment ça marche ?"
- **`canonical/`** : "Quelles sont les données ?"

## Différence entre `contracts/` et `.q-context/`

| Aspect | `contracts/` | `.q-context/` |
|--------|--------------|---------------|
| **Niveau de détail** | Détaillé (spécifications complètes) | Synthétique (vue d'ensemble) |
| **Audience** | Développeurs implémentant un composant | Architectes, product owners, nouveaux arrivants |
| **Objectif** | Implémenter sans ambiguïté | Comprendre le contexte global |
| **Exemple** | "La Lambda doit résoudre les bouquets en 4 étapes..." | "Vectora Inbox est un moteur de veille..." |

**En résumé :**
- **`.q-context/`** : "Qu'est-ce que Vectora Inbox ?"
- **`contracts/`** : "Comment implémenter la Lambda X ?"

## Bonnes pratiques

### 1. Lire les contrats avant de coder

Ne commencez pas à coder sans avoir lu le contrat. Vous risquez de partir dans la mauvaise direction.

### 2. Mettre à jour les contrats si nécessaire

Si vous découvrez une ambiguïté ou une erreur dans un contrat, **corrigez-le immédiatement**. Ne laissez pas le contrat diverger de la réalité.

### 3. Ajouter des exemples si besoin

Si un cas d'usage n'est pas couvert par les exemples existants, **ajoutez un exemple**. Les exemples sont la meilleure documentation.

### 4. Utiliser les contrats pour les revues de code

Lors des revues de code, vérifiez que le code respecte le contrat. Si le code fait quelque chose de différent, soit le code est faux, soit le contrat doit être mis à jour.

## Questions fréquentes

### Qui maintient les contrats ?

- **L'architecte / product owner** : définit la logique métier initiale
- **Les développeurs** : mettent à jour les contrats quand ils découvrent des ambiguïtés ou des erreurs
- **Tout le monde** : peut proposer des améliorations

### Que faire si le contrat est incomplet ?

- **Poser des questions** : demander des clarifications à l'architecte ou au product owner
- **Compléter le contrat** : ajouter les informations manquantes et les faire valider
- **Ne pas deviner** : ne pas implémenter quelque chose qui n'est pas spécifié

### Que faire si le code ne respecte pas le contrat ?

- **Corriger le code** : le contrat est la source de vérité
- **Ou mettre à jour le contrat** : si le code fait quelque chose de mieux, mettre à jour le contrat pour refléter la nouvelle logique

### Les contrats sont-ils figés ?

Non. Les contrats évoluent avec le produit. Ils sont une **documentation vivante**, pas un document figé.

## Ressources complémentaires

- **Vue d'ensemble** : `.q-context/overview.md` pour comprendre l'architecture globale
- **Workflow** : `.q-context/workflow.md` pour comprendre les 4 phases
- **Données métier** : `canonical/README.md` pour comprendre les scopes et les sources
- **Exemples de scoring** : `canonical/scoring/scoring_examples.md` pour comprendre la logique de scoring

---

**Ce README est destiné aux développeurs, architectes et product owners de Vectora Inbox.**
