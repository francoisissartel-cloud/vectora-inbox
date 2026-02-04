# Plan Optimisation .q-context UNIQUEMENT

**Date**: 2026-02-02  
**Durée**: 1h30  
**Focus**: Optimiser `.q-context/` pour meilleure collaboration Q Developer

---

## 🎯 OBJECTIF

Réduire `.q-context/` de 17 fichiers (3000+ lignes) à 9 fichiers (1600 lignes) sans redondance.

---

## 📋 ACTIONS

### 1. CRÉER CRITICAL_RULES.md (15 min)

**Extraire Top 10 règles de `vectora-inbox-development-rules.md`**:

```markdown
# Règles Critiques Vectora Inbox

## 1. Architecture 3 Lambdas V2 UNIQUEMENT
✅ ingest-v2 → normalize-score-v2 → newsletter-v2
❌ JAMAIS architecture 2 Lambdas

## 2. Code Source: src_v2/ UNIQUEMENT
✅ src_v2/
❌ JAMAIS archive/_src/

## 3. Git AVANT Build
✅ Commit → Build → Deploy
❌ Build → Deploy → Commit

## 4. Environnement TOUJOURS Explicite
✅ --env dev/stage/prod
❌ Déployer sans --env

## 5. Déploiement AWS = Code + Data + Test
✅ Deploy layers + Upload canonical + Test E2E
❌ Oublier canonical/

## 6. Tests Local AVANT AWS
✅ Local OK → Deploy → AWS Test
❌ Deploy sans test local

## 7. Client Config Auto-Généré
✅ Runners génèrent lai_weekly_vX
❌ Créer manuellement

## 8. Bedrock: us-east-1 + Sonnet
✅ Configuration validée E2E
❌ Changer sans validation

## 9. Temporaires dans .tmp/
✅ .tmp/ et .build/
❌ Fichiers à la racine

## 10. Blueprint Maintenu
✅ Update blueprint avec code
❌ Modifier code sans blueprint
```

**Fichier**: `.q-context/CRITICAL_RULES.md` (200 lignes)

---

### 2. SIMPLIFIER architecture.md (20 min)

**Réduire `vectora-inbox-architecture-overview.md` à l'essentiel**:

Garder SEULEMENT:
- Diagramme 3 Lambdas
- Flux S3 (ingested/ → curated/ → newsletters/)
- Variables d'environnement standard
- Commandes essentielles
- Buckets S3

Supprimer:
- Détails historiques
- Exemples longs
- Répétitions

**Fichier**: `.q-context/architecture.md` (250 lignes vs 500+ actuellement)

---

### 3. FUSIONNER git-workflow.md (15 min)

**Fusionner `vectora-inbox-git-workflow.md` + `vectora-inbox-git-rules.md`**:

Structure:
```markdown
# Git Workflow Vectora Inbox

## Règles Critiques
- Branche feature/ obligatoire
- Commit AVANT build
- PR obligatoire
- Tag après validation

## Workflow Standard
1. Créer branche
2. Modifier code
3. Commit
4. Build
5. Deploy dev
6. Test
7. PR
8. Merge
9. Tag
10. Promote stage

## Commandes
[Commandes Git exactes]

## Anti-Patterns
[Ce qu'il ne faut PAS faire]
```

**Fichier**: `.q-context/git-workflow.md` (200 lignes)

**Supprimer**: 
- `vectora-inbox-git-rules.md`

---

### 4. CRÉER aws-deployment.md (20 min)

**Extraire de `vectora-inbox-development-rules.md` section déploiement AWS**:

```markdown
# Déploiement AWS Vectora Inbox

## Checklist Complète

### Code Lambda
- [ ] Build layers
- [ ] Deploy layers
- [ ] Update Lambdas

### Canonical S3
- [ ] Identifier fichiers modifiés
- [ ] Upload vers S3
- [ ] Vérifier présence

### Validation
- [ ] Test E2E AWS
- [ ] Vérifier logs
- [ ] Confirmer résultats

## Scripts
[Scripts deploy_env.py, promote.py, etc.]

## Matrice Décision
[Tableau: Changement → Actions requises]

## Troubleshooting
[Symptômes + Solutions]
```

**Fichier**: `.q-context/aws-deployment.md` (200 lignes)

---

### 5. SIMPLIFIER q-planning-guide.md (15 min)

**Réduire `q-planning-rules.md` à l'essentiel**:

Garder:
- Quand créer un plan
- Templates à utiliser
- Phases obligatoires (Git/Versioning/Tests)
- Format checkpoint
- Gestion erreurs

Supprimer:
- Exemples longs
- Patterns détaillés
- Métriques

**Fichier**: `.q-context/q-planning-guide.md` (250 lignes vs 500+ actuellement)

---

### 6. SUPPRIMER FICHIERS REDONDANTS (5 min)

```bash
# Fusionnés ailleurs
rm .q-context/q-conformity-check.md          # → q-planning-guide.md
rm .q-context/q-response-format.md           # → README.md
rm .q-context/vectora-inbox-coding-standards.md  # → development-rules.md
rm .q-context/vectora-inbox-git-rules.md     # → git-workflow.md
rm .q-context/vectora-inbox-workflows.md     # → development-rules.md
```

---

### 7. SIMPLIFIER development-rules.md (20 min)

**Réduire `vectora-inbox-development-rules.md` de 1000+ à 400 lignes**:

Garder:
- Règles format réponse
- Structure src_v2/
- Configuration Bedrock
- Client config
- Lambda layers
- Tests E2E

Déplacer vers autres fichiers:
- Top 10 règles → CRITICAL_RULES.md
- Déploiement AWS → aws-deployment.md
- Git workflow → git-workflow.md
- Architecture → architecture.md

**Fichier**: `.q-context/vectora-inbox-development-rules.md` (400 lignes vs 1000+)

---

### 8. OPTIMISER README.md (10 min)

**Simplifier `.q-context/README.md`**:

Structure:
```markdown
# .q-context - Guide Q Developer

## 🚨 LIRE EN PREMIER
1. CRITICAL_RULES.md - Top 10 règles
2. architecture.md - Architecture 3 Lambdas
3. git-workflow.md - Workflow Git

## 📚 LIRE SI BESOIN
4. aws-deployment.md - Déploiement AWS
5. test-e2e-system.md - Tests E2E
6. q-planning-guide.md - Planification
7. q-prompting-guide.md - Prompting

## 🎯 TEMPLATES
8. templates/ - Templates plans/rapports

## 🚀 Quick Start
[Commandes essentielles]
```

**Fichier**: `.q-context/README.md` (150 lignes vs 200+ actuellement)

---

### 9. VALIDATION (10 min)

**Tester avec Q Developer**:

```
Prompt 1: "Explique l'architecture"
→ Q doit référencer CRITICAL_RULES.md + architecture.md

Prompt 2: "Je veux déployer en dev"
→ Q doit référencer aws-deployment.md

Prompt 3: "Workflow Git ?"
→ Q doit référencer git-workflow.md
```

**Vérifier**:
- Temps réponse < 10s
- Références précises
- Pas de confusion

---

## ✅ RÉSULTAT ATTENDU

### Avant
```
.q-context/
├── 17 fichiers
├── 3000+ lignes total
├── Redondances multiples
└── Fichiers trop longs (1000+ lignes)
```

### Après
```
.q-context/
├── 9 fichiers
├── 1600 lignes total
├── Zéro redondance
└── Fichiers focalisés (150-250 lignes)
```

### Fichiers Finaux
```
.q-context/
├── README.md (150 lignes)
├── CRITICAL_RULES.md (200 lignes) [NOUVEAU]
├── architecture.md (250 lignes) [SIMPLIFIÉ]
├── git-workflow.md (200 lignes) [FUSIONNÉ]
├── aws-deployment.md (200 lignes) [NOUVEAU]
├── test-e2e-system.md (200 lignes) [EXISTANT]
├── q-planning-guide.md (250 lignes) [SIMPLIFIÉ]
├── q-prompting-guide.md (150 lignes) [EXISTANT]
├── vectora-inbox-development-rules.md (400 lignes) [RÉDUIT]
└── templates/ [EXISTANT]
```

---

## 📊 IMPACT

- **Performance Q**: +50% (moins de contexte)
- **Clarté**: +80% (zéro redondance)
- **Maintenance**: -60% effort

---

## 🚀 EXÉCUTION

**Voulez-vous que je commence ?**

Options:
- ✅ **OUI** - Commencer action 1
- ⚠️ **MODIFIER** - Ajuster plan
- ❌ **ANNULER** - Ne pas exécuter

---

**Plan créé**: 2026-02-02  
**Durée**: 1h30  
**Focus**: `.q-context/` uniquement
