# Contexte Business Vectora Inbox

**Date**: 2026-01-31  
**Auteur**: Fondateur Vectora  
**Statut**: Document de référence pour Q Developer

---

## 🎯 Vision et Raison d'Être

### Le Problème

**Marchés de niche biotech/pharma = Expertise rare + Information dispersée**

- Les grands groupes de veille couvrent le pharma de manière générique
- Les secteurs de niche (LAI, siRNA, cell therapy, gene therapy) sont mal couverts
- Aucune newsletter spécialisée 100% LAI n'existe sur le marché
- Les décideurs perdent du temps à agréger l'information de multiples sources
- L'expertise métier nécessaire pour filtrer le signal du bruit est rare

### La Solution Vectora

**Moteur générique de newsletters ultra-spécialisées sur des marchés de niche biotech/pharma**

- Automatisation du scraping multi-sources (corporate, médias, PubMed, FDA, ClinicalTrials.gov)
- Filtrage intelligent basé sur expertise métier (pas juste keywords)
- Scoring contextuel adapté au type d'acteur (pure player vs. big pharma)
- Génération semi-automatique de newsletters prêtes à envoyer
- Human-in-the-loop pour validation finale

### Avantage Compétitif

**Expertise métier rare + Capacité technique (Q Developer) = Newsletters de niche impossibles à répliquer**

- 11 ans d'expérience pharma (analyste, business analyst, private equity, consulting, tech transfer)
- Profil pharmacien + école de commerce
- Capacité à définir ontologies, sémantiques, critères métier précis
- Maîtrise des secteurs de niche que peu de gens comprennent
- Agilité pour créer des newsletters sur-mesure rapidement

---

## 🏥 Expertise Métier: Long-Acting Injectables (LAI)

### Pourquoi LAI comme Premier Marché?

**Marché de niche suffisamment grand + Expertise rare + Aucune newsletter dédiée**

- **200+ entreprises** développent des médicaments LAI
- Marché en forte croissance (formulations à libération prolongée)
- Complexité technique élevée (microsphères, implants, technologies de formulation)
- Expertise métier nécessaire pour comprendre les enjeux
- **Aucune newsletter 100% LAI n'existe** → Opportunité unique

### Difficulté Métier: Définir et Classifier les LAI

**Pas trivial de savoir ce qui est LAI ou pas**

- Définition précise nécessaire (durée d'action, voie d'administration, technologie)
- Classification par type de formulation (microsphères, liposomes, implants, etc.)
- Distinction LAI vs. depot vs. sustained-release
- Connaissance des technologies propriétaires (Atrigel, Medisorb, etc.)
- Compréhension des KPIs pertinents (durée d'action, fréquence d'injection, compliance)

### Ontologie LAI (Exemples de Complexité)

**Entités à tracker**:
- **Molecules**: Principes actifs en développement LAI
- **Trademarks**: Noms commerciaux des produits LAI
- **Companies**: 200+ acteurs (pure players + big pharma)
- **Technologies**: Plateformes de formulation propriétaires
- **Events**: Partenariats, essais cliniques, approbations, publications

**Difficulté**: Une même molécule peut avoir une forme LAI et non-LAI → Filtrage sémantique crucial

---

## 👥 Personas et Cas d'Usage

### Qui Lit les Newsletters?

**Décideurs dans biotech, startups, fonds d'investissement, tech transfer**

Départements cibles:
- **R&D**: Surveiller pipeline concurrents, innovations technologiques
- **Business Development**: Identifier opportunités de partenariats
- **Marketing**: Anticiper lancements produits, positionnement concurrentiel
- **Regulatory Affairs**: Suivre approbations FDA/EMA, changements réglementaires
- **Medical Affairs**: Veille scientifique, publications cliniques
- **Executives**: Vision stratégique, décisions d'investissement

### Cas d'Usage 1: Newsletter Générique LAI (B2C)

**Abonnement hebdomadaire/mensuel à une newsletter LAI**

- Client type: Analyste pharma, consultant, investisseur, startup LAI
- Contenu: Top 5-10 signaux importants de la semaine
- Sections: Partenariats, essais cliniques, approbations, innovations tech, publications
- Valeur: Gain de temps (10h → 2h/semaine), exhaustivité (180+ sources), pertinence (scoring métier)

### Cas d'Usage 2: Newsletter Sur-Mesure (B2B)

**Client demande une newsletter personnalisée avec watch_domains spécifiques**

- Client type: Entreprise biotech, fonds d'investissement, big pharma
- Contenu: Veille ultra-ciblée sur compétiteurs, technologies, molécules spécifiques
- Configuration: watch_domains définis par le client, seuils ajustés, sources prioritaires
- Valeur: Intelligence concurrentielle actionnable, réactivité (détection J+1)

---

## 🎯 Modèle Business

### Offres

**1. Newsletter Générique LAI (POC actuel)**
- Abonnement mensuel/annuel
- Contenu standardisé mais haute valeur ajoutée
- Scalable (1 newsletter → N abonnés)

**2. Newsletter Sur-Mesure**
- Configuration client spécifique
- Tarif premium (expertise + personnalisation)
- Récurrent (hebdomadaire/mensuel)

**3. Extension à d'Autres Niches**
- siRNA, cell therapy, gene therapy, etc.
- Réutilisation du moteur Vectora Inbox
- Nouvelles ontologies canonical à définir

### KPIs Business (Pas Techniques)

- **Taux de lecture**: % d'abonnés qui ouvrent la newsletter
- **Engagement**: Clics sur items, feedback qualité
- **Rétention**: Taux de renouvellement abonnements
- **Acquisition**: Nouveaux abonnés/mois
- **Satisfaction**: Feedback qualitatif sur pertinence des items

---

## 🔬 Défis Métier et Techniques

### Défi 1: Filtrage Contextuel (Pure Player vs. Big Pharma)

**Problème**: Mêmes critères → Résultats différents selon type d'acteur

**Exemple concret**:
- **Pure player LAI** (ex: Alkermes, Heron Therapeutics):
  - 100% focus LAI
  - Toute news partenariat/essai clinique/approbation = Probablement pertinente
  - Scoring: Bonus +5.0 car signal fort
  
- **Big Pharma** (ex: Pfizer, Novartis):
  - <1% activité LAI (99% autres domaines)
  - Même critère "partenariat" = 99.99% bruit (non-LAI)
  - Scoring: Besoin de filtres sémantiques stricts pour éviter faux positifs

**Solution actuelle**:
- Bonus pure_player_companies: +5.0 dans scoring_config
- Filtrage sémantique Bedrock pour big pharma (vérifier mention LAI explicite)
- Seuils de matching ajustés par type d'acteur

**À améliorer**:
- Règles contextuelles plus sophistiquées
- Apprentissage des patterns par type d'acteur
- Feedback loop pour affiner les critères

### Défi 2: Définir les Bons Critères de Scoring

**Problème**: Quels critères métier sont vraiment prédictifs de pertinence?

**Critères actuels** (à valider/optimiser):
- **Trademark mention**: +4.0 (signal lancement produit imminent)
- **Pure player**: +5.0 (focus LAI garanti)
- **Event type**: Partenariat (+3.0), Approbation (+5.0), Publication (+2.0)
- **Recency**: Items récents privilégiés
- **Source authority**: FDA > média généraliste

**Questions ouvertes**:
- Ces bonus sont-ils bien calibrés?
- Manque-t-il des critères importants?
- Comment pondérer les critères entre eux?
- Comment apprendre des feedbacks semaine après semaine?

### Défi 3: Matching Sémantique aux Watch Domains

**Problème**: Déterminer si un item appartient à un watch_domain

**Exemple watch_domain LAI**:
- Domain: "tech_lai_ecosystem"
- Scope: Technologies LAI, formulations, plateformes propriétaires
- Seuil: min_domain_score = 0.25

**Difficulté**:
- Item mentionne "sustained-release formulation" → LAI ou pas?
- Item mentionne "Pfizer partnership" → LAI ou autre domaine?
- Item mentionne "microsphere technology" → LAI probable, mais contexte?

**Solution actuelle**:
- Bedrock matching avec prompt lai_matching.yaml
- Références aux canonical scopes (lai_keywords, lai_technologies)
- Score de 0 à 1, seuil configurable par client

**À améliorer**:
- Affiner les prompts Bedrock avec exemples positifs/négatifs
- Enrichir canonical scopes avec feedback terrain
- Tester différents seuils de matching

### Défi 4: Complexité des Canonical Scopes

**Problème**: Fichiers canonical deviennent complexes à maintenir

**Fichiers actuels**:
- `canonical/scopes/company_scopes.yaml`: 200+ entreprises LAI
- `canonical/scopes/molecule_scopes.yaml`: Molécules LAI actives
- `canonical/scopes/technology_scopes.yaml`: Mots-clés technologiques
- `canonical/scopes/trademark_scopes.yaml`: Marques commerciales

**Difficulté**:
- Maintenir à jour (nouvelles entreprises, fusions, acquisitions)
- Éviter redondances et incohérences
- Gérer synonymes et variantes (ex: "long-acting injectable" vs. "LAI" vs. "depot injection")

**À améliorer**:
- Simplifier la structure des scopes
- Automatiser la mise à jour (scraping listes entreprises)
- Valider cohérence entre scopes

---

## 🔄 Workflow Opérationnel Cible

### Génération Newsletter Hebdomadaire (Steady State)

**Lundi matin** (automatisé):
1. Ingest V2: Scraping sources (corporate, médias, PubMed, FDA, ClinicalTrials.gov)
2. Normalize-Score V2: Extraction entités, matching, scoring
3. Newsletter V2: Génération éditoriale, structuration par sections

**Lundi après-midi** (human-in-the-loop):
4. Revue manuelle: Validation pertinence items, ajustements éditoriaux
5. Feedback à Q: "Cet item est du bruit", "Cet item devrait être mieux noté"
6. Envoi newsletter aux abonnés

**Amélioration continue**:
- Q ajuste scoring, canonical, keywords basé sur feedback
- Semaine après semaine, qualité s'améliore
- Moins d'intervention manuelle nécessaire

### Onboarding Nouveau Client Sur-Mesure

**Jour 1-2**: Cadrage besoins client
- Définir watch_domains spécifiques
- Identifier sources prioritaires
- Définir seuils de pertinence

**Jour 3-5**: Configuration client_config.yaml
- Créer fichier client depuis template
- Paramétrer scoring_config, matching_config, newsletter_layout
- Enrichir canonical scopes si nécessaire

**Jour 6-7**: Tests et ajustements
- Générer newsletter test sur période passée
- Feedback client sur pertinence
- Ajuster paramètres

**Semaine 2+**: Production
- Génération automatique hebdomadaire
- Feedback loop pour amélioration continue

---

## 🎓 Apprentissage et Amélioration Continue

### Feedback Loop avec Q Developer

**Objectif**: Améliorer scoring, matching, sélection semaine après semaine

**Processus**:
1. **Génération newsletter**: Vectora produit newsletter automatiquement
2. **Revue humaine**: Identification items bruit vs. signal
3. **Feedback structuré à Q**:
   - "Item X est du bruit car [raison]"
   - "Item Y devrait être mieux noté car [raison]"
   - "Source Z produit trop de bruit, ajuster filtres"
4. **Q ajuste**:
   - Modifier scoring_config (bonus, malus)
   - Enrichir canonical scopes (keywords, negative_terms)
   - Affiner prompts Bedrock (exemples positifs/négatifs)
5. **Test**: Régénérer newsletter sur même période, valider amélioration
6. **Deploy**: Promouvoir changements vers prod

### Questions Ouvertes pour Expert Scoring/Matching

**Besoin de conseils d'expert pour**:
- Comment bien calibrer les bonus de scoring?
- Quels critères métier sont les plus prédictifs?
- Comment gérer les règles contextuelles (pure player vs. big pharma)?
- Comment structurer les canonical scopes pour éviter complexité?
- Comment mesurer la qualité du matching (métriques)?
- Comment apprendre des feedbacks de manière systématique?

---

## 🚀 Roadmap Produit

### Phase 1: POC LAI (Actuel)

**Objectif**: Valider moteur sur newsletter générique LAI

- ✅ Architecture 3 Lambdas opérationnelle
- ✅ Client lai_weekly_v7 configuré
- ✅ Canonical scopes LAI définis
- ✅ Scoring et matching basiques fonctionnels
- 🚧 Newsletter V2 (génération éditoriale) en cours
- 🚧 Amélioration scoring/matching via feedback loop

**Critère de succès**: Newsletter LAI hebdomadaire de qualité, prête à commercialiser

### Phase 2: Commercialisation LAI (Q2 2026)

**Objectif**: Premiers clients payants newsletter LAI

- Offre abonnement mensuel/annuel
- Landing page + marketing
- 10-50 premiers abonnés
- Feedback clients pour amélioration

### Phase 3: Extension Sources (Q3 2026)

**Objectif**: Enrichir sources d'ingestion

- PubMed API (publications scientifiques)
- ClinicalTrials.gov API (essais cliniques)
- FDA Daily (approbations réglementaires)
- Scraping corporate avancé (communiqués de presse)
- Médias spécialisés biotech (FierceBiotech, etc.)

### Phase 4: Nouvelles Niches (Q4 2026)

**Objectif**: Répliquer succès LAI sur autres niches

- siRNA (small interfering RNA)
- Cell therapy (thérapies cellulaires)
- Gene therapy (thérapies géniques)
- Réutilisation moteur Vectora Inbox
- Nouvelles ontologies canonical

### Phase 5: Newsletters Sur-Mesure (2027)

**Objectif**: Offre B2B premium

- Configuration client spécifique
- Watch_domains personnalisés
- Tarif premium
- Support dédié

### Phase 6: RAG LAI (Vision Long Terme)

**Objectif**: Capitaliser sur Vectora Inbox pour créer un RAG spécialisé LAI

**Rationale**: Si Vectora Inbox est un succès commercial, le moteur devient la première brique d'un système RAG plus large

**Assets réutilisables**:
- **Ingestion multi-sources**: Pipeline validé (corporate, médias, PubMed, FDA, ClinicalTrials.gov)
- **Normalisation structurée**: Entités extraites (companies, molecules, technologies, trademarks, events)
- **Taxonomie LAI**: Ontologie précise et validée terrain
- **Canonical scopes**: Définitions, classifications, vocabulaire métier
- **Données curées**: Historique d'items normalisés et enrichis

**Valeur ajoutée RAG**:
- Recherche sémantique sur corpus LAI structuré
- Q&A contextuel pour décideurs ("Quels partenariats LAI en 2025?")
- Analyse de tendances ("Évolution technologies microsphères")
- Intelligence concurrentielle augmentée

**Principe**: Taxonomie, ontologie, définitions des scopes sont des actifs précieux à long terme

**Statut**: Vision exploratoire, très long terme, incertain

---

## 📊 Métriques de Succès

### Métriques Techniques (Actuelles)

- Temps d'exécution pipeline
- Taux de succès Bedrock
- Coût par newsletter
- Nombre d'items traités

### Métriques Business (Cibles)

**Qualité**:
- % items pertinents dans newsletter (objectif: >80%)
- Taux de faux positifs (objectif: <20%)
- Satisfaction client (NPS)

**Engagement**:
- Taux d'ouverture newsletter (objectif: >40%)
- Taux de clic sur items (objectif: >15%)
- Feedback qualitatif positif

**Croissance**:
- Nombre d'abonnés newsletter LAI
- Taux de renouvellement (objectif: >80%)
- Nouveaux clients sur-mesure/trimestre

---

## 🎯 Principes de Conception Vectora

### 1. Configuration > Code

**Tout paramètre métier doit être configurable sans redéploiement**

- Seuils de scoring dans client_config.yaml
- Canonical scopes dans S3 (pas hardcodés)
- Prompts Bedrock externalisés
- Sources d'ingestion dans source_catalog.yaml

### 2. Expertise Métier Embarquée

**Le code doit refléter l'expertise pharma, pas juste de la tech**

- Ontologies LAI précises
- Règles de scoring basées sur connaissance métier
- Filtres contextuels (pure player vs. big pharma)
- Vocabulaire métier dans les logs et outputs

### 3. Human-in-the-Loop

**L'IA assiste, l'humain décide**

- Newsletter générée automatiquement
- Revue humaine obligatoire avant envoi
- Feedback humain pour amélioration continue
- Expertise métier irremplaçable pour validation finale

### 4. Amélioration Continue

**Chaque newsletter est une opportunité d'apprendre**

- Feedback structuré après chaque génération
- Ajustements incrémentaux scoring/matching
- Enrichissement canonical scopes
- Mesure de la progression qualité

### 5. Généricité et Réutilisabilité

**Moteur conçu pour s'étendre à d'autres niches**

- Architecture agnostique du vertical (LAI, siRNA, etc.)
- Canonical scopes modulaires par vertical
- Client_config.yaml flexible
- Ajout de nouvelles sources facilité

### 6. Actifs Stratégiques Long Terme

**Taxonomie, ontologie, scopes = Fondations pour évolutions futures**

- Canonical scopes sont des actifs précieux (pas juste config)
- Ontologie LAI validée terrain = Rare et valorisable
- Données normalisées structurées = Base pour RAG futur
- Pipeline ingestion multi-sources = Réutilisable pour autres cas d'usage
- Qualité des définitions métier = Différenciation durable

**Vision**: Si Vectora Inbox réussit, ces actifs permettront de construire un RAG spécialisé LAI (recherche sémantique, Q&A, analyse tendances)

---

## 💡 Pour Q Developer

### Ce que Q Doit Comprendre

**Vectora Inbox n'est pas un outil de veille générique**

- C'est un moteur de newsletters ultra-spécialisées sur des niches biotech/pharma
- L'expertise métier est l'avantage compétitif, pas la tech
- Le scoring/matching doit refléter la connaissance métier, pas juste des keywords
- Les règles doivent être contextuelles (pure player ≠ big pharma)
- L'amélioration continue via feedback est au cœur du produit

### Quand Q Propose des Améliorations

**Toujours se demander**:
- Est-ce que ça améliore la pertinence métier des items sélectionnés?
- Est-ce que ça réduit le bruit (faux positifs)?
- Est-ce que ça facilite la configuration par un expert métier?
- Est-ce que ça permet d'apprendre des feedbacks?
- Est-ce que ça s'étend facilement à d'autres niches?

### Priorités de Développement

**1. Qualité > Quantité**
- Mieux vaut 5 items ultra-pertinents que 20 items moyens
- Scoring strict pour éviter le bruit

**2. Configurabilité > Performance**
- Mieux vaut 10s de plus d'exécution que paramètres hardcodés
- Faciliter l'ajustement par expert métier

**3. Feedback Loop > Automatisation Totale**
- Human-in-the-loop est une feature, pas un bug
- Apprendre des feedbacks est prioritaire

**4. Simplicité > Sophistication**
- Canonical scopes doivent rester maintenables
- Règles de scoring doivent être compréhensibles
- Éviter la sur-ingénierie

**5. Qualité des Définitions Métier**
- Taxonomie et ontologie sont des actifs stratégiques long terme
- Investir dans la précision des canonical scopes
- Documenter les définitions et classifications
- Penser réutilisabilité future (RAG, autres produits)

---

**Document vivant - À enrichir au fur et à mesure**

*Ce document capture l'expertise métier et la vision produit de Vectora Inbox. Il doit être lu par Q Developer avant toute proposition d'amélioration ou développement de feature.*
