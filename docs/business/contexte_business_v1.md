# Contexte Business — Vectora Inbox V1

**Date** : 2026-04-25
**Auteur** : Frank (fondateur Vectora)
**Statut** : Document de référence actif — à lire avant toute décision produit ou technique

> Ce document remplace `CONTEXTE_BUSINESS_VECTORA.md` (legacy Q Developer, archivé).
> Il décrit le projet tel qu'il est aujourd'hui : un datalake local-first alimenté par Claude (API Anthropic).

---

## 1. Qui est Frank

Frank est pharmacien de formation, avec une école de commerce en complément. Il a 11 ans d'expérience dans l'industrie pharmaceutique : analyste, business analyst, private equity, consulting, tech transfer. Il maîtrise en profondeur plusieurs marchés de niche biotech/pharma, notamment les Long-Acting Injectables (LAI).

**Ce qu'il sait faire mieux que quiconque :**
- Définir avec précision ce qui est pertinent dans un flux d'information pharma — la sémantique, les critères, les nuances
- Identifier ce qui est signal et ce qui est bruit dans un marché de niche
- Construire des ontologies et taxonomies métier (scopes, classifications, vocabulaire) que peu de gens peuvent formaliser
- Comprendre les enjeux des acteurs (pure players, big pharma, investisseurs, régulateurs)

**Ses contraintes réelles :**
- Il n'est pas développeur. Il peut lire du code, comprendre une architecture, valider un plan — mais il ne code pas.
- Il travaille seul. Pas de team. Pas de budget infrastructure. Le moteur doit tourner sur son PC Windows.
- Il pilote Claude comme architecte et développeur principal. La collaboration Frank ↔ Claude est le moteur de construction du projet.
- Le coût des appels LLM est une variable à piloter activement, pas à ignorer.

**Ce que ça implique pour le projet :**
L'avantage compétitif de Vectora n'est pas technologique — il est métier. La technologie (le datalake, le moteur d'ingestion, l'API Claude) est le levier qui industrialise une expertise qui existe déjà dans la tête de Frank. Le code doit refléter cette expertise, pas l'inverse.

---

## 2. Le Problème Marché

**Les marchés de niche biotech/pharma sont mal couverts par l'information existante.**

- Les grands outils de veille (Bloomberg, Evaluate Pharma, etc.) couvrent le pharma de façon générique et coûtent cher
- Les marchés de niche (LAI, siRNA, cell therapy, gene therapy) sont sous-couverts ou couverts par des généralistes qui manquent d'expertise
- Les décideurs perdent un temps considérable à agréger l'information depuis des dizaines de sources disparates
- Filtrer le signal du bruit dans ces niches demande une expertise métier rare — qui ne s'automatise pas avec des mots-clés simples

**Aucune newsletter 100% LAI n'existe sur le marché.** C'est une opportunité directe, identifiable, et adressable dès V1.

---

## 3. Ce qu'on Construit en V1 — Le Datalake

**Vectora Inbox V1 est un moteur d'alimentation d'un datalake de veille pharmaceutique.**

Ce n'est pas encore un produit vendu à des clients. C'est la fondation sur laquelle tous les produits seront construits.

Le moteur fait deux choses :
1. **Ingestion** : scraper des sources web (sites corporate, presse sectorielle, FDA, PubMed, ClinicalTrials.gov) et stocker les items bruts dans un dépôt `raw`
2. **Normalisation** : passer chaque item par Claude (API Anthropic) pour en extraire les entités structurées, qualifier la pertinence, et stocker le résultat dans un dépôt `curated`

Le datalake est l'artefact produit de V1. Il est **vivant** (alimenté régulièrement), **curé** (enrichi par LLM), et **structuré** (chaque item a un format normalisé, des tags écosystème, des entités extraites).

**Ce que le datalake n'est pas en V1 :**
La newsletter, le rapport, le RAG, l'interface utilisateur — tout ça viendra après, comme consommateurs du datalake. En V1, on construit le moteur, pas les livrables finaux.

---

## 4. Le Premier Écosystème — Long-Acting Injectables (LAI)

### Pourquoi LAI en premier

- **200+ entreprises** développent des médicaments LAI dans le monde
- Marché en forte croissance (formulations à libération prolongée, compliance améliorée)
- Complexité technique élevée : microsphères, implants, liposomes, technologies propriétaires (Atrigel, Medisorb, etc.)
- **Frank a l'expertise** pour définir ce qui est LAI et ce qui ne l'est pas — ce n'est pas trivial
- **Aucune newsletter dédiée n'existe** — c'est une opportunité directe

### La Complexité de la Classification LAI

Savoir si une news est pertinente pour le marché LAI n'est pas une question de mots-clés. Exemples de cas difficiles :

- Une molécule peut avoir une forme LAI et une forme non-LAI → il faut vérifier le contexte
- Un partenariat signé par Pfizer peut concerner ses 50 autres domaines → il faut filtrer sémantiquement
- "Sustained-release formulation" peut ou non désigner une technologie LAI selon le contexte
- Un pure player LAI (Alkermes, Heron) génère un signal fort même pour des news génériques ; un big pharma génère du bruit par défaut

C'est précisément cette nuance que le moteur doit apprendre à gérer, grâce à l'ontologie définie par Frank dans `canonical/`.

### Les Entités à Tracker dans l'Écosystème LAI

| Entité | Exemples | Rôle |
|---|---|---|
| **Molecules** | Risperidone LAI, Paliperidone palmitate | Principes actifs en développement LAI |
| **Trademarks** | Risperdal Consta, Invega Sustenna | Produits commercialisés |
| **Companies** | Alkermes, Camurus, MedIncell, Pfizer | Acteurs du marché (pure players et big pharma) |
| **Technologies** | Atrigel, FluidCrystal, BEPO | Plateformes de formulation propriétaires |
| **Events** | Partenariats, approbations FDA/EMA, essais cliniques, publications | Signaux d'activité du marché |

---

## 5. Le Stack Produit — Du Datalake aux Livrables

Le datalake V1 est la fondation. Au-dessus, on construit une pile de produits et de services par ordre de complexité croissante.

```
DATALAKE CURATED (V1 — ce qu'on construit maintenant)
        │
        ├── Newsletter LAI générique (premier produit)
        │     → Hebdomadaire ou bimensuelle
        │     → Abonnement B2C : analystes, consultants, investisseurs, startups LAI
        │     → Top 5-10 signaux de la semaine, organisés par type d'event
        │
        ├── Newsletter sur-mesure (B2B)
        │     → Client définit ses watch scopes spécifiques (molécules, entreprises, technologies)
        │     → Configuration client_config.yaml personnalisée
        │     → Tarif premium : expertise + personnalisation
        │
        ├── Rapports d'expertise ponctuels
        │     → "State of the LAI market Q2 2026"
        │     → Livrable one-shot vendu à une pharma, un fonds, un cabinet de conseil
        │     → Frank apporte l'analyse, le datalake fournit les données structurées
        │
        └── RAG / Intelligence augmentée (vision long terme)
              → Corpus LAI structuré et interrogeable
              → Q&A contextuel : "Quels partenariats LAI signés en 2025 ?"
              → Analyse de tendances, veille concurrentielle augmentée
```

**Le principe central** : Frank vend son expertise métier. Le datalake la rend scalable, exhaustive, et reproductible. Sans le datalake, chaque livrable demande des dizaines d'heures de travail manuel. Avec le datalake, le travail de Frank se concentre sur l'analyse et la valeur ajoutée — pas sur l'agrégation.

---

## 6. Les Actifs Stratégiques

Le vrai actif de Vectora n'est pas le code. C'est ce qui s'accumule dans `canonical/` et dans le datalake au fil du temps.

**`canonical/` — l'ontologie métier**

- `scopes/` : 200+ entreprises LAI, molécules, technologies, trademarks, indications — des années de travail de classification
- `ecosystems/` : définition précise de ce qu'est l'écosystème LAI, ses frontières, ses critères d'inclusion
- `sources/` : catalog des sources validées, candidats en attente de validation
- `imports/` : référentiels métier (glossaire, routes d'administration, familles technologiques)

Ces fichiers sont **rares et valorisables**. Ils reflètent une expertise pharma que peu de gens peuvent formaliser. Ils s'enrichissent à chaque cycle d'ingestion, à chaque feedback, à chaque nouvelle source validée.

**Le datalake curated**

Chaque item normalisé est une donnée structurée : entités extraites, score de pertinence, event type, tags écosystème. Après 6 mois de run, le datalake devient un corpus unique sur le marché LAI — impossible à répliquer rapidement par un concurrent.

**Principe** : investir dans la qualité des canonical scopes dès V1, c'est investir dans la valeur de tous les produits futurs.

---

## 7. Personas Cibles (Consommateurs des Livrables)

| Persona | Besoin | Produit adapté |
|---|---|---|
| Analyste pharma indépendant | Gagner du temps sur la veille hebdo | Newsletter générique LAI |
| Consultant pharma | Briefings clients rapides sur le marché LAI | Newsletter + rapports ponctuels |
| Investisseur (VC, PE) | Surveiller le pipeline et les partenariats | Newsletter générique ou sur-mesure |
| Startup LAI | Veille concurrentielle sur technos et acteurs | Newsletter sur-mesure |
| Business Development pharma | Identifier des cibles de licensing ou acquisition | Sur-mesure + rapports d'expertise |
| Tech transfer office | Suivre les publications et les brevets LAI | Newsletter + RAG (futur) |

---

## 8. Principes de Conception (Ce qui Guide Chaque Décision Technique)

Ces principes découlent directement du contexte business et des contraintes de Frank.

**Local-first** : tout tourne sur le PC de Frank. Pas d'infrastructure cloud en V1. Robustesse et simplicité avant performance.

**Configuration-driven** : aucune logique métier en dur dans le code. Tout ce qui peut changer (scopes, seuils, sources, prompts) est dans `canonical/` ou `config/`. Frank peut affiner l'ontologie sans toucher au code.

**Coût conscient** : chaque appel à l'API Claude est tracé et coûte de l'argent. Le moteur doit rapporter son coût à chaque run et respecter des plafonds configurables.

**Human-in-the-loop** : Claude génère, Frank valide. L'expertise métier de Frank est irremplaçable pour la validation finale de la pertinence. L'automatisation assiste, elle ne décide pas seule.

**Datalake = artefact produit** : on ne mélange jamais ingestion et consommation. La newsletter n'est pas dans le scope du moteur V1. Le moteur produit du curated ; d'autres outils consomment.

**Portabilité préservée** : les interfaces sont conçues pour permettre une migration future vers AWS/S3 si le volume le justifie. En V1, on n'y va pas, mais on ne ferme pas la porte.

---

## 9. Ce que V1 ne Fait Pas (Et Pourquoi C'est Intentionnel)

| Hors scope V1 | Raison |
|---|---|
| Générer une newsletter | Consommateur du datalake, pas le datalake lui-même |
| Interface utilisateur | Pas nécessaire pour valider le moteur |
| Multi-écosystème simultané | LAI d'abord, les autres niches après validation |
| Déploiement cloud / AWS | Surcoût inutile en phase de validation |
| Commercialisation | Moteur d'abord, produit ensuite |
| RAG / recherche sémantique | Vision long terme, pas V1 |

---

*Document vivant — mis à jour quand la vision ou le contexte évolue.*
*Ce document est lu par Claude au début de chaque session stratégique sur le projet.*
