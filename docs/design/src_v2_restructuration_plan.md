# Plan de Restructuration src_v2 - Architecture 3 Lambdas V2

## Introduction

Ce plan restructure complètement `src_v2` pour accueillir proprement les 3 Lambdas V2 selon les contrats métier et les règles d'hygiène V4.

## Objectifs de la Restructuration

### Objectifs Techniques
- ✅ **Respecter les règles d'hygiène V4** : Séparation claire par Lambda
- ✅ **Permettre des déploiements séparés** : Packaging individuel par Lambda
- ✅ **Maintenir la clarté et maintenabilité** : Organisation logique des modules
- ✅ **Éviter le code spaghetti** : Responsabilités bien définies

### Objectifs Métier
- **Préparer normalize-score V2** : Modules Bedrock, matching, scoring
- **Préparer newsletter V2** : Modules assemblage éditorial, métriques
- **Maintenir ingest V2** : Modules existants réorganisés

## Structure Cible

### Architecture Finale
```
src_v2/
├── lambdas/
│   ├── ingest/
│   │   ├── handler.py
│   │   └── requirements.txt
│   ├── normalize_score/
│   │   ├── handler.py
│   │   └── requirements.txt
│   └── newsletter/
│       ├── handler.py
│       └── requirements.txt
├── vectora_core/
│   ├── shared/                    # Modules partagés entre Lambdas
│   │   ├── __init__.py
│   │   ├── config_loader.py
│   │   ├── s3_io.py
│   │   ├── models.py
│   │   └── utils.py
│   ├── ingest/                    # Modules spécifiques ingest V2
│   │   ├── __init__.py
│   │   ├── source_fetcher.py
│   │   ├── content_parser.py
│   │   └── ingestion_profiles.py
│   ├── normalization/             # Modules spécifiques normalize-score V2
│   │   ├── __init__.py
│   │   ├── normalizer.py
│   │   ├── matcher.py
│   │   ├── scorer.py
│   │   └── bedrock_client.py
│   └── newsletter/                # Modules spécifiques newsletter V2
│       ├── __init__.py
│       ├── assembler.py
│       ├── editorial.py
│       ├── layout.py
│       └── metrics.py
└── README.md
```

---

## Phase 1 – Préparation et Sauvegarde

### Objectifs
- Sauvegarder l'état actuel fonctionnel
- Analyser les dépendances entre modules
- Préparer l'environnement de migration

### Actions détaillées
- Créer backup complet de `src_v2` actuel
- Analyser les imports et dépendances dans `vectora_core`
- Identifier les modules partagés vs spécifiques
- Valider que les tests actuels passent
- Documenter l'état de référence

### Fichiers concernés
- `/src_v2/` (backup complet)
- Analyse des imports dans tous les `.py`

### Critères de "done"
- [ ] Backup créé dans `/backup/src_v2_before_restructure/`
- [ ] Matrice de dépendances documentée
- [ ] Tests actuels validés (ingest V2 fonctionne)
- [ ] État de référence documenté

### Risques
- Perte de code fonctionnel
- Dépendances cachées non identifiées

---

## Phase 2 – Création de la Nouvelle Structure

### Objectifs
- Créer l'arborescence cible complète
- Déplacer les modules existants aux bons emplacements
- Créer les squelettes des nouveaux modules

### Actions détaillées
- Créer la structure de dossiers cible
- Déplacer les modules partagés vers `vectora_core/shared/`
- Déplacer les modules ingest vers `vectora_core/ingest/`
- Créer les squelettes `vectora_core/normalization/` et `vectora_core/newsletter/`
- Créer les handlers squelettes pour normalize_score et newsletter
- Créer les `requirements.txt` individuels

### Fichiers concernés
#### Modules à déplacer vers `shared/`
- `config_loader.py` → `vectora_core/shared/config_loader.py`
- `s3_io.py` → `vectora_core/shared/s3_io.py`
- `models.py` → `vectora_core/shared/models.py`
- `utils.py` → `vectora_core/shared/utils.py`

#### Modules à déplacer vers `ingest/`
- `source_fetcher.py` → `vectora_core/ingest/source_fetcher.py`
- `content_parser.py` → `vectora_core/ingest/content_parser.py`
- `ingestion_profiles.py` → `vectora_core/ingest/ingestion_profiles.py`
- `__init__.py` (fonction ingest) → `vectora_core/ingest/__init__.py`

#### Nouveaux fichiers à créer
- `lambdas/normalize_score/handler.py` (squelette)
- `lambdas/newsletter/handler.py` (squelette)
- `vectora_core/normalization/` (modules squelettes)
- `vectora_core/newsletter/` (modules squelettes)

### Critères de "done"
- [ ] Structure de dossiers complète créée
- [ ] Tous les modules existants déplacés
- [ ] Squelettes des nouveaux modules créés
- [ ] Handlers squelettes fonctionnels
- [ ] Requirements.txt individuels créés

### Risques
- Erreurs de déplacement de fichiers
- Structure incomplète

---

## Phase 3 – Mise à Jour des Imports et Intégration

### Objectifs
- Corriger tous les imports selon la nouvelle structure
- Intégrer les modules dans leurs nouveaux emplacements
- Valider que la Lambda ingest fonctionne toujours

### Actions détaillées
- Mettre à jour tous les imports dans les modules déplacés
- Corriger les imports dans `lambdas/ingest/handler.py`
- Créer les `__init__.py` appropriés dans chaque dossier
- Implémenter les fonctions d'orchestration dans les nouveaux modules
- Tester le packaging de la Lambda ingest
- Valider le déploiement ingest avec nouvelle structure

### Fichiers concernés
#### Imports à corriger
- `lambdas/ingest/handler.py` : `from vectora_core.ingest import run_ingest_for_client`
- `vectora_core/ingest/__init__.py` : Imports depuis `shared/` et modules locaux
- Tous les modules : Ajuster imports relatifs

#### Nouveaux `__init__.py`
- `vectora_core/shared/__init__.py`
- `vectora_core/ingest/__init__.py` (avec fonction principale)
- `vectora_core/normalization/__init__.py` (squelette)
- `vectora_core/newsletter/__init__.py` (squelette)

### Critères de "done"
- [ ] Tous les imports corrigés et fonctionnels
- [ ] Lambda ingest package correctement
- [ ] Lambda ingest se déploie sans erreur
- [ ] Tests d'intégration ingest passent
- [ ] Aucune régression fonctionnelle

### Risques
- Imports cassés
- Régression fonctionnelle Lambda ingest
- Problèmes de packaging

---

## Phase 4 – Validation, Documentation et Finalisation

### Objectifs
- Valider la conformité aux règles d'hygiène V4
- Documenter la nouvelle organisation
- Préparer les scripts de déploiement
- Finaliser la migration

### Actions détaillées
- Valider conformité règles d'hygiène V4
- Créer documentation de la nouvelle structure
- Adapter les scripts de build/deploy existants
- Créer scripts de build/deploy pour futures Lambdas
- Tester packaging des 3 Lambdas (même si 2 sont squelettes)
- Nettoyer les fichiers temporaires
- Valider que tout fonctionne end-to-end

### Fichiers concernés
#### Documentation
- `src_v2/README.md` (nouvelle organisation)
- `docs/design/src_v2_architecture.md` (architecture détaillée)

#### Scripts
- `scripts/package_ingest_v2.py` (adaptation)
- `scripts/package_normalize_score_v2.py` (nouveau)
- `scripts/package_newsletter_v2.py` (nouveau)
- `scripts/deploy_normalize_score_v2.py` (nouveau)
- `scripts/deploy_newsletter_v2.py` (nouveau)

#### Validation
- Script de validation conformité V4
- Tests d'intégration complets

### Critères de "done"
- [ ] Conformité V4 validée
- [ ] Documentation complète et à jour
- [ ] Scripts de build/deploy fonctionnels pour les 3 Lambdas
- [ ] Tests end-to-end passent
- [ ] Migration finalisée et validée

### Risques
- Documentation incomplète
- Scripts de déploiement non fonctionnels

---

## Mapping des Modules

### Modules Partagés (vectora_core/shared/)
| Module Actuel | Nouveau Emplacement | Utilisé par |
|---------------|-------------------|-------------|
| `config_loader.py` | `shared/config_loader.py` | Toutes les Lambdas |
| `s3_io.py` | `shared/s3_io.py` | Toutes les Lambdas |
| `models.py` | `shared/models.py` | Toutes les Lambdas |
| `utils.py` | `shared/utils.py` | Toutes les Lambdas |

### Modules Ingest (vectora_core/ingest/)
| Module Actuel | Nouveau Emplacement | Responsabilité |
|---------------|-------------------|----------------|
| `source_fetcher.py` | `ingest/source_fetcher.py` | Récupération contenus |
| `content_parser.py` | `ingest/content_parser.py` | Parsing RSS/HTML |
| `ingestion_profiles.py` | `ingest/ingestion_profiles.py` | Profils canonical |
| `__init__.py` (fonction ingest) | `ingest/__init__.py` | Orchestration ingest |

### Nouveaux Modules Normalize-Score (vectora_core/normalization/)
| Module | Responsabilité | Basé sur Contrat |
|--------|----------------|------------------|
| `normalizer.py` | Appels Bedrock normalisation | normalize_score_v2.md |
| `matcher.py` | Matching aux domaines | normalize_score_v2.md |
| `scorer.py` | Calcul scores pertinence | normalize_score_v2.md |
| `bedrock_client.py` | Client Bedrock spécialisé | normalize_score_v2.md |

### Nouveaux Modules Newsletter (vectora_core/newsletter/)
| Module | Responsabilité | Basé sur Contrat |
|--------|----------------|------------------|
| `assembler.py` | Assemblage newsletter | newsletter_v2.md |
| `editorial.py` | Génération contenu Bedrock | newsletter_v2.md |
| `layout.py` | Gestion sections format | newsletter_v2.md |
| `metrics.py` | Calcul statistiques veille | newsletter_v2.md |

## Impact sur les Déploiements

### Avant Restructuration
- **1 Lambda** : `vectora-inbox-ingest-v2`
- **1 Package** : `vectora-inbox-ingest-v2.zip`
- **1 Script** : `deploy_ingest_v2.py`

### Après Restructuration
- **3 Lambdas** : 
  - `vectora-inbox-ingest-v2`
  - `vectora-inbox-normalize-score-v2`
  - `vectora-inbox-newsletter-v2`
- **3 Packages** :
  - `vectora-inbox-ingest-v2.zip`
  - `vectora-inbox-normalize-score-v2.zip`
  - `vectora-inbox-newsletter-v2.zip`
- **3 Scripts** :
  - `deploy_ingest_v2.py`
  - `deploy_normalize_score_v2.py`
  - `deploy_newsletter_v2.py`
- **1 Lambda Layer** : `vectora-core-v2` (partagé)

## Validation de Conformité V4

### Règles Respectées
- ✅ **Handlers séparés** : Un par Lambda dans `lambdas/`
- ✅ **Logique métier séparée** : Modules spécialisés par Lambda
- ✅ **Code partagé identifié** : Dans `vectora_core/shared/`
- ✅ **Pas de dépendances tierces** : Dans `src_v2/`
- ✅ **Taille handlers** : < 5MB chacun
- ✅ **Lambda Layers** : `vectora_core` complet

### Bénéfices Attendus
- **Clarté** : Chaque fichier appartient à une Lambda précise
- **Maintenabilité** : Évolution isolée par Lambda
- **Déploiement** : Scripts et packages séparés
- **Évolutivité** : Ajout facile de nouvelles Lambdas

## Conclusion

Cette restructuration transforme `src_v2` d'une organisation monolithique en une architecture modulaire claire, respectant les règles V4 et préparant l'implémentation des Lambdas normalize-score et newsletter V2.

---

**Durée estimée** : 4 heures  
**Priorité** : CRITIQUE  
**Prérequis** : Backup complet de l'existant