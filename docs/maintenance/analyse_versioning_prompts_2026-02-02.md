# Analyse Stratégies Versioning Prompts - 2026-02-02

## 🎯 Contexte

Vous allez itérer sur les prompts Bedrock via feedback E2E :
- Tests → Feedback → Amélioration prompts → Re-test
- Besoin de traçabilité des changements
- Question : Versioning dédié prompts OU versioning repo existant ?

## 📊 Analyse Comparative

### Option A : Versioning Intégré Repo (RECOMMANDÉ ✅)

**Principe** : Les prompts suivent le versioning global du repo

**Structure actuelle** :
```
canonical/prompts/
├── normalization/
│   └── generic_normalization.yaml  # metadata.version: "2.0"
├── domain_scoring/
│   └── lai_domain_scoring.yaml     # metadata.version: "2.0"
└── editorial/
    └── lai_editorial.yaml          # metadata.version: "1.0"
```

**Workflow** :
1. Feedback E2E → Modifier prompt
2. Incrémenter `metadata.version` dans le YAML (2.0 → 2.1)
3. Incrémenter `CANONICAL_VERSION` dans `VERSION` (2.0 → 2.1)
4. Commit avec message clair : "feat(prompts): amélioration extraction dates generic_normalization v2.1"
5. Build → Deploy dev → Test
6. Si OK → Promote stage

**Avantages** :
- ✅ Simple : un seul système de versioning
- ✅ Cohérence : prompts versionnés avec code qui les utilise
- ✅ Traçabilité Git : `git log canonical/prompts/` montre historique
- ✅ Rollback facile : `git checkout <commit>` restaure version antérieure
- ✅ Pas de duplication : un seul fichier par prompt
- ✅ Déjà en place : VERSION existe, gouvernance définie

**Inconvénients** :
- ⚠️ Comparaison versions : nécessite `git diff`
- ⚠️ Pas de versions parallèles actives

**Traçabilité** :
```bash
# Historique d'un prompt
git log --oneline canonical/prompts/normalization/generic_normalization.yaml

# Comparer 2 versions
git diff v2.0..v2.1 canonical/prompts/normalization/generic_normalization.yaml

# Restaurer version antérieure
git checkout v2.0 canonical/prompts/normalization/generic_normalization.yaml
```

---

### Option B : Versioning Dédié Prompts

**Principe** : Chaque version de prompt = fichier séparé

**Structure proposée** :
```
canonical/prompts/
├── normalization/
│   ├── generic_normalization_v2.0.yaml
│   ├── generic_normalization_v2.1.yaml
│   └── generic_normalization_v2.2.yaml  # Version active
├── domain_scoring/
│   ├── lai_domain_scoring_v2.0.yaml
│   └── lai_domain_scoring_v2.1.yaml     # Version active
└── editorial/
    └── lai_editorial_v1.0.yaml          # Version active
```

**Workflow** :
1. Feedback E2E → Copier prompt actuel
2. Créer nouveau fichier `_v2.2.yaml`
3. Modifier client_config : `normalization_prompt: "generic_normalization_v2.2"`
4. Build → Deploy → Test
5. Si OK → Marquer v2.2 comme active

**Avantages** :
- ✅ Comparaison facile : tous les fichiers visibles
- ✅ Versions parallèles : tester v2.1 et v2.2 simultanément
- ✅ Rollback immédiat : changer référence dans client_config

**Inconvénients** :
- ❌ Duplication : 3-5 versions × 3 prompts = 9-15 fichiers
- ❌ Complexité : quelle version est active ?
- ❌ Maintenance : supprimer anciennes versions manuellement
- ❌ Confusion : `config_loader.py` doit gérer versions multiples
- ❌ Incohérence : prompts v2.2 avec code v2.0 ?

---

### Option C : Versioning Hybride

**Principe** : Fichier actif + archive des versions

**Structure proposée** :
```
canonical/prompts/
├── normalization/
│   ├── generic_normalization.yaml       # Version active
│   └── archive/
│       ├── generic_normalization_v2.0.yaml
│       └── generic_normalization_v2.1.yaml
├── domain_scoring/
│   ├── lai_domain_scoring.yaml          # Version active
│   └── archive/
│       └── lai_domain_scoring_v2.0.yaml
└── editorial/
    └── lai_editorial.yaml               # Version active
```

**Workflow** :
1. Feedback E2E → Copier version actuelle dans `archive/`
2. Modifier version active
3. Incrémenter `metadata.version` dans YAML
4. Commit
5. Build → Deploy → Test

**Avantages** :
- ✅ Fichier actif clair : pas de confusion
- ✅ Archive locale : comparaison rapide
- ✅ Compatible avec Option A

**Inconvénients** :
- ⚠️ Duplication partielle
- ⚠️ Git suffit déjà pour archivage

---

## 🎯 Recommandation : Option A (Versioning Intégré)

### Pourquoi ?

1. **Simplicité** : Votre système actuel est déjà bien conçu
2. **Cohérence** : Prompts = partie du canonical (CANONICAL_VERSION)
3. **Git suffit** : Historique, diff, rollback déjà disponibles
4. **Pas de duplication** : Un seul fichier source de vérité
5. **Gouvernance existante** : Workflow déjà défini

### Workflow Concret

```bash
# 1. Test E2E
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v10

# 2. Feedback : "Extraction dates insuffisante"

# 3. Modifier prompt
# Éditer: canonical/prompts/normalization/generic_normalization.yaml
# Changer metadata.version: "2.0" → "2.1"
# Améliorer instructions extraction dates

# 4. Incrémenter VERSION
# Éditer: VERSION
# CANONICAL_VERSION=2.0 → CANONICAL_VERSION=2.1

# 5. Commit AVANT build
git add canonical/prompts/normalization/generic_normalization.yaml VERSION
git commit -m "feat(prompts): amélioration extraction dates - generic_normalization v2.1"

# 6. Build & Deploy
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev

# 7. Re-test
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v10

# 8. Si OK → Promote
python scripts/deploy/promote.py --to stage --version 2.1
```

### Traçabilité Garantie

```bash
# Voir historique d'un prompt
git log --oneline --follow canonical/prompts/normalization/generic_normalization.yaml

# Comparer versions
git show v2.0:canonical/prompts/normalization/generic_normalization.yaml
git show v2.1:canonical/prompts/normalization/generic_normalization.yaml

# Restaurer version antérieure si régression
git checkout v2.0 canonical/prompts/normalization/generic_normalization.yaml
```

---

## 📋 Proposition Amélioration Metadata

**Enrichir metadata dans chaque prompt** :

```yaml
metadata:
  prompt_id: "generic_normalization"
  version: "2.1"
  created_date: "2026-01-31"
  last_modified: "2026-02-02"
  description: "Generic normalization for biotech/pharma news"
  
  # NOUVEAU : Changelog intégré
  changelog:
    - version: "2.1"
      date: "2026-02-02"
      author: "Q Developer"
      changes: "Amélioration extraction dates - ajout patterns français"
      test_results: "E2E lai_weekly_v10 - 95% dates extraites (vs 80% v2.0)"
      
    - version: "2.0"
      date: "2026-01-31"
      author: "Q Developer"
      changes: "Refonte architecture - vertical-agnostic"
      replaces: "lai_normalization.yaml v1.1"
```

**Avantages** :
- ✅ Historique dans le fichier lui-même
- ✅ Contexte des changements
- ✅ Résultats tests associés
- ✅ Pas de fichiers supplémentaires

---

## 🚀 Actions Recommandées

### Immédiat (Ne rien modifier sans accord)

1. **Valider Option A** : Versioning intégré repo
2. **Enrichir metadata** : Ajouter changelog dans prompts
3. **Documenter workflow** : Ajouter section prompts dans gouvernance

### Si vous validez

Je créerai :
1. Guide versioning prompts dans `.q-context/`
2. Template metadata enrichi
3. Mise à jour gouvernance

---

## ❓ Questions pour Décision

1. **Option A suffit-elle** pour votre workflow itératif ?
2. **Changelog intégré** dans metadata vous convient ?
3. **Fréquence itérations** : combien de versions par semaine ?
4. **Besoin versions parallèles** : tester 2 prompts simultanément ?

---

**Attendant votre validation avant toute modification**
