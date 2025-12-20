# Diagnostic des Dossiers layer_* - Vectora Inbox

**Date :** 18 décembre 2025  
**Objectif :** Analyser le rôle et les options de nettoyage des dossiers layer_*  
**Statut :** Diagnostic uniquement, aucune modification

---

## Vue d'Ensemble des Dossiers layer_*

### Dossiers Identifiés

1. **layer_build/** - Construction de layers complètes
2. **layer_inspection/** - Inspection/extraction de layers
3. **layer_minimal/** - Layer minimale (YAML uniquement)
4. **layer_rebuild/** - Reconstruction de layers avec dépendances complètes

---

## Analyse Détaillée par Dossier

### 1. layer_build/ - Layer de Construction Principale

**Contenu :**
- `python/` : Dépendances complètes (beautifulsoup4, certifi, charset_normalizer, feedparser, idna, pyyaml, requests, soupsieve, urllib3, yaml, sgmllib)
- `test_imports.py` : Script de test des imports
- `vectora-inbox-common-deps-v2.zip` : Package layer finalisé

**Rôle identifié :**
- **Construction de la layer vectora-inbox-common-deps-v2**
- Contient toutes les dépendances communes aux Lambdas V2
- Layer de référence pour le déploiement

**Utilité pour V2 :**
- ✅ **CRITIQUE** : Layer utilisée par les Lambdas ingest-v2, normalize-score-v2
- ✅ **ACTIVE** : Package `vectora-inbox-common-deps-v2.zip` déployé en production
- ✅ **MAINTENUE** : Dépendances à jour (certifi-2025.11.12, charset_normalizer-3.4.4)

**Recommandation :** **CONSERVER** - Dossier essentiel au pipeline V2

### 2. layer_inspection/ - Inspection de Layers

**Contenu :**
- `yaml-minimal-extracted/python/` : Extraction de la layer YAML minimale
- `yaml-minimal-layer.zip` : Package layer YAML minimal

**Rôle identifié :**
- **Inspection et extraction de layers existantes**
- Permet d'analyser le contenu des layers déployées
- Utile pour debugging et validation

**Utilité pour V2 :**
- ⚠️ **UTILITAIRE** : Pas directement utilisé par le pipeline V2
- ✅ **DEBUG** : Utile pour diagnostiquer les problèmes de layers
- ⚠️ **EXPÉRIMENTAL** : Semble être un outil de développement

**Recommandation :** **CONSERVER** - Utile pour maintenance et debug

### 3. layer_minimal/ - Layer YAML Minimale

**Contenu :**
- `python/` : Uniquement PyYAML (pyyaml-6.0.1, yaml/, _yaml/)
- `yaml-minimal.zip` : Package layer YAML seule

**Rôle identifié :**
- **Layer minimale contenant uniquement PyYAML**
- Alternative légère à la layer complète
- Potentiellement pour des Lambdas nécessitant seulement YAML

**Utilité pour V2 :**
- ❌ **NON UTILISÉE** : Les Lambdas V2 utilisent la layer complète
- ⚠️ **EXPÉRIMENTALE** : Possiblement pour optimisation future
- ❌ **OBSOLÈTE** : Pas référencée dans les déploiements actuels

**Recommandation :** **CANDIDATE_FOR_DELETION** - Non utilisée par V2

### 4. layer_rebuild/ - Reconstruction Complète

**Contenu :**
- `python/` : Dépendances très complètes (boto3, botocore, dateutil, feedparser, jmespath, s3transfer, etc.)
- Plus de dépendances que layer_build/ (inclut boto3/botocore)

**Rôle identifié :**
- **Reconstruction de layer avec dépendances AWS complètes**
- Inclut boto3/botocore en plus des dépendances communes
- Potentiellement pour une layer "tout-en-un"

**Utilité pour V2 :**
- ❌ **NON UTILISÉE** : V2 utilise boto3 via runtime Lambda, pas via layer
- ⚠️ **EXPÉRIMENTALE** : Test d'une approche différente
- ❌ **REDONDANTE** : Duplique layer_build/ avec ajouts non nécessaires

**Recommandation :** **CANDIDATE_FOR_DELETION** - Approche abandonnée

---

## Analyse Comparative des Layers

### Dépendances par Layer

| Dépendance | layer_build | layer_minimal | layer_rebuild | Nécessaire V2 |
|------------|-------------|---------------|---------------|---------------|
| **PyYAML** | ✅ | ✅ | ✅ | ✅ Critique |
| **requests** | ✅ | ❌ | ✅ | ✅ HTTP calls |
| **feedparser** | ✅ | ❌ | ✅ | ✅ RSS parsing |
| **beautifulsoup4** | ✅ | ❌ | ❌ | ✅ HTML parsing |
| **boto3/botocore** | ❌ | ❌ | ✅ | ❌ Runtime fourni |
| **certifi/urllib3** | ✅ | ❌ | ✅ | ✅ HTTPS |
| **charset_normalizer** | ✅ | ❌ | ✅ | ✅ Encoding |

### Tailles Estimées

- **layer_build/** : ~15-20 MB (dépendances optimales)
- **layer_minimal/** : ~2-3 MB (YAML uniquement)
- **layer_rebuild/** : ~25-30 MB (avec boto3)
- **layer_inspection/** : ~2-3 MB (extraction)

---

## Recommandations de Nettoyage

### Option 1 : Nettoyage Conservateur (Recommandée)

**CONSERVER :**
- ✅ `layer_build/` - Layer de production V2
- ✅ `layer_inspection/` - Utilitaire de debug

**MARQUER POUR SUPPRESSION FUTURE :**
- ⚠️ `layer_minimal/` - Non utilisée, mais petite
- ⚠️ `layer_rebuild/` - Expérimentale, mais peut contenir historique

**Actions :**
- Documenter le rôle de chaque dossier
- Créer un README dans chaque dossier
- Pas de suppression immédiate

### Option 2 : Nettoyage Agressif

**CONSERVER :**
- ✅ `layer_build/` - Layer de production V2

**SUPPRIMER :**
- ❌ `layer_minimal/` - Non utilisée par V2
- ❌ `layer_rebuild/` - Approche abandonnée
- ❌ `layer_inspection/` - Utilitaire non critique

**REGROUPER :**
- Créer `layer_build/archive/` pour historique

### Option 3 : Regroupement Structuré

**STRUCTURE PROPOSÉE :**
```
layer_management/
├── active/
│   └── layer_build/          # Layer de production
├── experimental/
│   ├── layer_minimal/        # Tests layer minimale
│   └── layer_rebuild/        # Tests layer complète
└── tools/
    └── layer_inspection/     # Outils d'inspection
```

---

## Impact sur le Pipeline V2

### Dépendances Critiques

**layer_build/ est ESSENTIELLE :**
- ✅ Utilisée par `vectora-inbox-ingest-v2`
- ✅ Utilisée par `vectora-inbox-normalize-score-v2`
- ✅ Contient les dépendances requises (PyYAML, requests, feedparser, beautifulsoup4)

**Autres layers sont OPTIONNELLES :**
- ❌ Pas référencées dans les déploiements CloudFormation
- ❌ Pas utilisées par le code src_v2/
- ❌ Pas mentionnées dans la documentation V2

### Risques de Suppression

**AUCUN RISQUE :**
- `layer_minimal/` et `layer_rebuild/` peuvent être supprimées sans impact
- `layer_inspection/` est un utilitaire indépendant

**RISQUE CRITIQUE :**
- Supprimer `layer_build/` casserait le déploiement V2

---

## Recommandation Finale

### Approche Recommandée : **Option 1 - Conservateur**

**Justification :**
1. **Sécurité** : Préserve l'historique et les expérimentations
2. **Debug** : Garde les outils d'inspection disponibles
3. **Évolutivité** : Permet de revenir aux expérimentations si nécessaire

**Actions Immédiates :**
1. **Documenter** chaque dossier avec un README
2. **Marquer** layer_minimal/ et layer_rebuild/ comme expérimentales
3. **Valider** que layer_build/ est bien la layer de référence

**Actions Futures (Phase 4) :**
1. Après 1 mois sans utilisation, supprimer layer_minimal/ et layer_rebuild/
2. Archiver layer_inspection/ si non utilisée
3. Optimiser layer_build/ si nécessaire

---

## Métriques de Nettoyage

### Gain d'Espace Potentiel

**Si suppression aggressive :**
- `layer_minimal/` : ~3 MB
- `layer_rebuild/` : ~30 MB
- `layer_inspection/` : ~3 MB
- **Total libéré :** ~36 MB

**Impact visuel :**
- Réduction de 3 dossiers sur 4 (75%)
- Simplification de la structure

### Risque/Bénéfice

**Bénéfice :** Faible (36 MB, simplification visuelle)  
**Risque :** Moyen (perte d'historique, outils de debug)  
**Recommandation :** Conserver pour l'instant, réévaluer plus tard