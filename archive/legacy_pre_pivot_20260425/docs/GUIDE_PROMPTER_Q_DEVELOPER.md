# Guide - Comment Prompter Amazon Q Developer

**Date**: 2026-01-30  
**Contexte**: Gouvernance en place, Q fait tout le code  
**Principe**: Vous décrivez ce que vous voulez, Q applique les règles automatiquement

---

## 🎯 Principe Fondamental

**Amazon Q Developer lit automatiquement `.q-context/vectora-inbox-development-rules.md`**

Vous n'avez PAS besoin de:
- ❌ Rappeler les règles de gouvernance
- ❌ Dire "utilise les scripts build"
- ❌ Préciser "respecte le workflow"
- ❌ Mentionner le fichier VERSION

**Q sait déjà tout ça !**

---

## 📝 Structure d'un Bon Prompt

### Template de Base

```
Je veux [ACTION] pour [OBJECTIF].

[Contexte optionnel si nécessaire]

Environnement cible: [dev/stage/local]
```

### Exemples Concrets

#### ✅ Prompt Simple et Efficace

```
Je veux ajouter une fonction pour extraire les dates des articles dans vectora_core.

Environnement: dev
```

**Ce que Q va faire automatiquement**:
1. Lire les règles de gouvernance
2. Modifier le code dans `src_v2/vectora_core/`
3. Incrémenter VERSION
4. Builder avec `scripts/build/build_all.py`
5. Déployer en dev avec `scripts/deploy/deploy_env.py --env dev`
6. Proposer des tests
7. Commiter

#### ✅ Prompt pour Correction Bug

```
Il y a un bug dans l'extraction des dates en normalize-score-v2.
Les dates au format "DD/MM/YYYY" ne sont pas reconnues.

Corrige ça et déploie en dev pour tester.
```

**Q va**:
1. Analyser le code
2. Corriger le bug
3. Incrémenter VERSION (PATCH)
4. Builder et déployer en dev
5. Proposer des tests

#### ✅ Prompt pour Modification Canonical

```
Ajoute 3 nouvelles entités dans tech_lai_ecosystem:
- "AI agents"
- "Multimodal AI"
- "AI safety"

Sync vers dev.
```

**Q va**:
1. Modifier `canonical/scopes/tech_lai_ecosystem.yaml`
2. Incrémenter CANONICAL_VERSION
3. Syncer vers S3 dev
4. Proposer des tests

---

## 🎯 Niveaux de Précision

### Niveau 1: Minimal (Recommandé)

**Vous dites juste ce que vous voulez**:

```
Ajoute une validation des emails dans config_loader.
```

Q devine automatiquement:
- Environnement: dev (par défaut)
- Workflow: complet (build → deploy → test)
- Versioning: PATCH (correction/amélioration)

### Niveau 2: Précis (Si besoin)

**Vous précisez l'environnement**:

```
Ajoute une validation des emails dans config_loader.

Environnement: dev
Tester avec: lai_weekly_v7
```

Q sait:
- Déployer en dev
- Tester avec le client spécifié
- Ne pas promouvoir en stage (vous ne l'avez pas demandé)

### Niveau 3: Détaillé (Cas complexe)

**Vous donnez plus de contexte**:

```
Ajoute une validation des emails dans config_loader.

Contexte: Les configs clients ont parfois des emails invalides qui causent des erreurs.

Environnement: dev
Tester avec: lai_weekly_v7
Si OK: promouvoir en stage
```

Q va:
1. Implémenter la validation
2. Déployer en dev
3. Tester
4. Si tests OK, promouvoir en stage automatiquement

---

## 🌍 Spécifier l'Environnement

### Option 1: Implicite (Par Défaut = Dev)

```
Corrige le bug d'extraction de dates.
```

→ Q déploie en **dev** automatiquement

### Option 2: Explicite

```
Corrige le bug d'extraction de dates.

Environnement: stage
```

→ Q déploie en **stage** (après avoir testé en dev d'abord)

### Option 3: Workflow Complet

```
Corrige le bug d'extraction de dates.

Workflow: dev → stage
```

→ Q fait:
1. Deploy dev
2. Test dev
3. Promote stage
4. Test stage

---

## 🔧 Types de Tâches Courantes

### 1. Développement Nouvelle Fonctionnalité

**Prompt**:
```
Ajoute une fonction pour détecter les dates relatives ("hier", "la semaine dernière").

Environnement: dev
```

**Q fait**:
- Modifie code
- Incrémente VERSION (MINOR)
- Build + Deploy dev
- Propose tests

### 2. Correction Bug

**Prompt**:
```
Le matching Bedrock échoue quand il y a des caractères spéciaux.
Corrige ça.
```

**Q fait**:
- Analyse et corrige
- Incrémente VERSION (PATCH)
- Build + Deploy dev
- Propose tests

### 3. Modification Configuration

**Prompt**:
```
Ajoute un nouveau scope "regulatory_europe" dans canonical.

Sync vers dev et stage.
```

**Q fait**:
- Crée le fichier YAML
- Incrémente CANONICAL_VERSION
- Sync S3 dev
- Sync S3 stage

### 4. Nouveau Client

**Prompt**:
```
Crée une config pour un nouveau client "pharma_weekly_v1".

Basé sur lai_weekly_v3 mais avec:
- Seulement 3 items par section
- Focus sur regulatory

Environnement: dev
```

**Q fait**:
- Crée config depuis template
- Upload S3 dev
- Propose tests

### 5. Tests et Validation

**Prompt**:
```
Teste normalize-score-v2 en dev avec lai_weekly_v7.

Vérifie que l'extraction de dates fonctionne.
```

**Q fait**:
- Lance invoke script
- Analyse résultats
- Rapporte succès/échecs

---

## 🚀 Workflows Typiques

### Workflow 1: Développement Standard

**Votre prompt**:
```
Améliore la fonction de scoring pour donner plus de poids aux articles récents.

Environnement: dev
```

**Q exécute automatiquement**:
1. Modifie `src_v2/vectora_core/normalization/scorer.py`
2. Incrémente VERSION (MINOR: 1.2.3 → 1.3.0)
3. `python scripts/build/build_all.py`
4. `python scripts/deploy/deploy_env.py --env dev`
5. Propose: `python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7`
6. Demande: "Tests OK ? Je promeus en stage ?"

### Workflow 2: Hotfix Urgent

**Votre prompt**:
```
URGENT: Le layer stage a un bug, les dates ne sont pas extraites.

Corrige et déploie en stage immédiatement.
```

**Q exécute**:
1. Analyse le problème
2. Corrige dans repo local
3. Incrémente VERSION (PATCH: 1.2.3 → 1.2.4)
4. Build + Deploy dev (test rapide)
5. Promote stage
6. Test stage
7. Commit

### Workflow 3: Promotion Simple

**Votre prompt**:
```
La version 1.2.4 fonctionne bien en dev.

Promeus en stage.
```

**Q exécute**:
1. `python scripts/deploy/promote.py --to stage --version 1.2.4`
2. Propose tests stage
3. Demande confirmation pour commit

---

## ❌ Ce Qu'il NE FAUT PAS Faire

### ❌ Trop de Détails Techniques

**Mauvais prompt**:
```
Modifie src_v2/vectora_core/normalization/scorer.py ligne 45.
Puis édite VERSION et incrémente VECTORA_CORE_VERSION.
Puis lance python scripts/build/build_all.py.
Puis lance python scripts/deploy/deploy_env.py --env dev.
```

**Bon prompt**:
```
Améliore le scoring pour favoriser les articles récents.

Environnement: dev
```

→ Q sait déjà comment faire !

### ❌ Rappeler les Règles

**Mauvais prompt**:
```
Ajoute une fonction de validation.

N'oublie pas de:
- Respecter la gouvernance
- Utiliser les scripts build
- Incrémenter VERSION
- Déployer en dev d'abord
```

**Bon prompt**:
```
Ajoute une fonction de validation des emails.
```

→ Q applique les règles automatiquement !

### ❌ Commandes AWS Directes

**Mauvais prompt**:
```
Lance cette commande:
aws lambda update-function-code --function-name vectora-inbox-normalize-score-v2-dev
```

**Bon prompt**:
```
Déploie la nouvelle version en dev.
```

→ Q utilise les scripts de gouvernance !

---

## 💡 Astuces Pro

### 1. Laissez Q Proposer

**Vous**:
```
Je veux améliorer la performance du matching Bedrock.
```

**Q va proposer**:
```
Je peux:
1. Ajouter un cache pour les résultats Bedrock
2. Optimiser les prompts
3. Paralléliser les appels

Quelle approche préférez-vous ?
```

### 2. Demandez des Explications

**Vous**:
```
Explique-moi comment fonctionne l'extraction de dates actuellement.
```

**Q va**:
- Analyser le code
- Expliquer le flow
- Proposer des améliorations

### 3. Itérez Progressivement

**Étape 1**:
```
Ajoute une fonction pour extraire les dates.
```

**Étape 2** (après test):
```
Améliore la fonction pour gérer les dates relatives.
```

**Étape 3** (après test):
```
Promeus en stage.
```

---

## 📋 Checklist Prompt Efficace

Votre prompt doit contenir:

- [x] **Action claire**: "Ajoute", "Corrige", "Modifie", "Teste"
- [x] **Objectif**: Ce que vous voulez accomplir
- [ ] **Environnement** (optionnel): dev/stage/local (défaut: dev)
- [ ] **Contexte** (optionnel): Pourquoi, pour qui
- [ ] **Tests** (optionnel): Comment valider

**Exemple complet**:
```
Ajoute une fonction pour extraire les dates relatives ("hier", "la semaine dernière").

Contexte: Les articles LAI utilisent souvent des dates relatives.

Environnement: dev
Tester avec: lai_weekly_v7
```

---

## 🎯 Exemples Réels

### Exemple 1: Feature Simple

**Vous**:
```
Ajoute un log pour tracer les appels Bedrock.
```

**Q fait tout**:
- Modifie code
- Incrémente VERSION
- Build + Deploy dev
- Propose tests

### Exemple 2: Bug Fix

**Vous**:
```
Les articles avec des guillemets dans le titre causent des erreurs.
Corrige ça.
```

**Q fait tout**:
- Analyse et corrige
- Incrémente VERSION
- Build + Deploy dev
- Teste

### Exemple 3: Config Client

**Vous**:
```
Crée une config pour "biotech_daily_v1".

Similaire à lai_weekly_v7 mais quotidien.
```

**Q fait tout**:
- Crée config
- Upload S3 dev
- Propose tests

### Exemple 4: Promotion

**Vous**:
```
Tout fonctionne en dev.
Promeus en stage.
```

**Q fait tout**:
- Promote stage
- Teste stage
- Commit

---

## 🔄 Workflow Interactif avec Q

### Conversation Typique

**Vous**:
```
Je veux améliorer l'extraction de dates.
```

**Q**:
```
Je peux:
1. Ajouter support dates relatives
2. Améliorer parsing dates internationales
3. Ajouter validation dates futures

Quelle option ?
```

**Vous**:
```
Option 1 et 3.
```

**Q**:
```
OK, je vais:
1. Modifier src_v2/vectora_core/ingest/content_parser.py
2. Incrémenter VERSION (1.2.3 → 1.3.0)
3. Builder et déployer en dev
4. Tester avec lai_weekly_v7

Je commence ?
```

**Vous**:
```
Oui.
```

**Q exécute tout et rapporte**:
```
✅ Code modifié
✅ VERSION incrémentée (1.3.0)
✅ Build réussi
✅ Déployé en dev
✅ Tests passés

Voulez-vous promouvoir en stage ?
```

---

## 📚 Résumé

### Ce que Q fait AUTOMATIQUEMENT

✅ Lit les règles de gouvernance  
✅ Applique le workflow standard  
✅ Incrémente VERSION  
✅ Utilise les scripts build/deploy  
✅ Teste en dev avant stage  
✅ Commit avec message descriptif  

### Ce que VOUS faites

✅ Décrivez ce que vous voulez  
✅ Précisez l'environnement si besoin  
✅ Validez les propositions de Q  
✅ Confirmez les promotions  

### Formule Magique

```
[ACTION] + [OBJECTIF] + [Environnement optionnel]
```

**Exemples**:
- "Ajoute une validation des emails"
- "Corrige le bug d'extraction de dates"
- "Promeus la version 1.2.4 en stage"
- "Teste normalize-score-v2 avec lai_weekly_v7"

---

**Q Developer sait déjà comment travailler proprement.**  
**Vous n'avez qu'à dire ce que vous voulez !**

---

**Guide Prompter Q Developer - Version 1.0**  
**Date**: 2026-01-30  
**Statut**: Gouvernance en place
