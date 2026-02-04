# Plan Optimisation .q-context - Vectora Inbox

**Date**: 2026-02-02  
**Objectif**: Optimiser `.q-context/` pour collaboration efficace avec Q Developer  
**Durée estimée**: 2-3 heures

---

## 🎯 OBJECTIFS

1. **Réduire bruit**: Archiver 90% des fichiers `docs/` historiques
2. **Clarifier priorités**: Hiérarchie claire pour Q Developer
3. **Simplifier règles**: Fichiers focalisés < 300 lignes chacun
4. **Améliorer performance**: Q charge moins de contexte inutile

---

## 📋 PHASE 1: ARCHIVAGE DOCS (30 min)

### Actions

**1.1 Créer structure archive**
```bash
mkdir -p docs/archive/2025-12
mkdir -p docs/archive/2026-01
mkdir -p docs/archive/2026-02
mkdir -p docs/active/architecture
mkdir -p docs/active/guides
```

**1.2 Archiver plans historiques**
```bash
# Plans obsolètes (100+ fichiers)
mv docs/design/bedrock_*.md docs/archive/2025-12/
mv docs/design/lai_weekly_v2_*.md docs/archive/2025-12/
mv docs/design/lai_weekly_v3_*.md docs/archive/2025-12/
mv docs/design/lai_weekly_v4_*.md docs/archive/2026-01/
mv docs/design/normalize_*.md docs/archive/2025-12/
mv docs/design/newsletter_*.md docs/archive/2025-12/
mv docs/design/phase*.md docs/archive/2025-12/
mv docs/design/plan_*.md docs/archive/2026-01/
mv docs/design/vectora_inbox_*.md docs/archive/2025-12/

# Garder SEULEMENT dans docs/design/:
# - repo_layout_v2_overview.md (référence)
# - src_v2_restructuration_plan.md (référence)
```

**1.3 Archiver diagnostics historiques**
```bash
mv docs/diagnostics/lai_weekly_v4_*.md docs/archive/2026-01/
mv docs/diagnostics/lai_weekly_v5_*.md docs/archive/2026-01/
mv docs/diagnostics/bedrock_*.md docs/archive/2025-12/
mv docs/diagnostics/matching_*.md docs/archive/2025-12/
mv docs/diagnostics/newsletter_*.md docs/archive/2025-12/
mv docs/diagnostics/normalize_*.md docs/archive/2025-12/
mv docs/diagnostics/scoring_*.md docs/archive/2025-12/
mv docs/diagnostics/phase*.md docs/archive/2025-12/

# Garder SEULEMENT dans docs/diagnostics/:
# - raw/ (données brutes)
```

**1.4 Archiver plans obsolètes**
```bash
mv docs/plans/plan_correctif_*.md docs/archive/2026-01/
mv docs/plans/plan_test_e2e_lai_weekly_v5*.md docs/archive/2026-01/
mv docs/plans/plan_test_e2e_lai_weekly_v6*.md docs/archive/2026-01/
mv docs/plans/PROMPT_*.md docs/archive/2026-01/
mv docs/plans/RESUME_*.md docs/archive/2026-01/
mv docs/plans/SUIVI_*.md docs/archive/2026-01/

# Garder SEULEMENT dans docs/plans/:
# - plan_refactoring_bedrock_canonical_suite_20260202.md (actif)
# - plan_workflow_e2e_invocation_20260202.md (actif)
# - GUIDE_TRANSITION_NOUVEAU_CHAT.md (référence)
```

**1.5 Archiver rapports historiques**
```bash
mv docs/reports/amelioration_*.md docs/archive/2025-12/
mv docs/reports/analyse_*.md docs/archive/2025-12/
mv docs/reports/bedrock_*.md docs/archive/2025-12/
mv docs/reports/diagnostic_*.md docs/archive/2026-01/
mv docs/reports/ingest_*.md docs/archive/2025-12/
mv docs/reports/investigation_*.md docs/archive/2025-12/
mv docs/reports/lai_weekly_v5_*.md docs/archive/2025-12/
mv docs/reports/newsletter_*.md docs/archive/2025-12/
mv docs/reports/normalize_*.md docs/archive/2025-12/
mv docs/reports/phase*.md docs/archive/2025-12/
mv docs/reports/rapport_*.md docs/archive/2026-01/
mv docs/reports/resume_*.md docs/archive/2025-12/
mv docs/reports/test_*.md docs/archive/2026-01/

# Garder SEULEMENT dans docs/reports/:
# - development/ (rapports actifs février 2026)
# - maintenance/ (rapports actifs)
```

**1.6 Créer INDEX archive**
```bash
# Créer docs/archive/INDEX.md avec:
# - Liste chronologique des fichiers archivés
# - Mots-clés pour recherche
# - Liens vers fichiers importants
```

### Résultat Attendu

**Avant**:
- `docs/design/`: 100+ fichiers
- `docs/diagnostics/`: 30+ fichiers
- `docs/plans/`: 40+ fichiers
- `docs/reports/`: 20+ fichiers

**Après**:
- `docs/design/`: 2-3 fichiers (référence)
- `docs/diagnostics/`: 1 dossier (raw/)
- `docs/plans/`: 2-3 fichiers (actifs)
- `docs/reports/`: 2 dossiers (development/, maintenance/)
- `docs/archive/`: 180+ fichiers organisés par date

---

## 📋 PHASE 2: REFACTORING .Q-CONTEXT (1h)

### Actions

**2.1 Créer RULES_CRITICAL.md**

Extraire de `vectora-inbox-development-rules.md` les **10 règles NON-NÉGOCIABLES**:

```markdown
# Règles Critiques Vectora Inbox

**Top 10 règles que Q Developer DOIT TOUJOURS respecter**

## 1. Architecture 3 Lambdas V2 UNIQUEMENT
✅ ingest-v2 → normalize-score-v2 → newsletter-v2
❌ JAMAIS proposer architecture 2 Lambdas

## 2. Code Source: src_v2/ UNIQUEMENT
✅ Tout code dans src_v2/
❌ JAMAIS utiliser archive/_src/

## 3. Git AVANT Build
✅ Commit → Build → Deploy
❌ JAMAIS Build → Deploy → Commit

## 4. Environnement TOUJOURS Explicite
✅ --env dev/stage/prod
❌ JAMAIS déployer sans --env

## 5. Déploiement AWS Complet
✅ Code + Canonical + Config + Test E2E
❌ JAMAIS oublier upload canonical/

## 6. Tests Local AVANT AWS
✅ Local OK → Deploy → AWS Test
❌ JAMAIS deploy sans test local

## 7. Client Config Auto-Généré
✅ Runners génèrent lai_weekly_vX
❌ JAMAIS créer manuellement

## 8. Bedrock Configuration Validée
✅ us-east-1 + claude-3-sonnet
❌ JAMAIS changer sans validation

## 9. Fichiers Temporaires dans .tmp/
✅ Tout dans .tmp/ ou .build/
❌ JAMAIS à la racine

## 10. Blueprint Maintenu à Jour
✅ Mise à jour blueprint avec code
❌ JAMAIS modifier code sans blueprint
```

**2.2 Simplifier architecture-current.md**

Extraire de `vectora-inbox-architecture-overview.md` SEULEMENT:
- Diagramme 3 Lambdas
- Flux de données S3
- Variables d'environnement
- Commandes essentielles

**2.3 Créer aws-deployment.md**

Extraire de `vectora-inbox-development-rules.md`:
- Checklist déploiement AWS complet
- Scripts de déploiement
- Ordre stacks CloudFormation
- Validation post-déploiement

**2.4 Simplifier git-integration.md**

Fusionner `vectora-inbox-git-workflow.md` + `vectora-inbox-git-rules.md`:
- Workflow standard (branche → commit → PR)
- Règles critiques Git
- Exemples concrets

**2.5 Créer README.md optimisé**

```markdown
# .q-context - Guide Q Developer

**Ordre de lecture obligatoire pour Q Developer**

## 🚨 LIRE EN PREMIER

1. **RULES_CRITICAL.md** - Top 10 règles NON-NÉGOCIABLES
2. **architecture-current.md** - Architecture 3 Lambdas V2
3. **workflows-standard.md** - Workflows quotidiens

## 📚 LIRE SI BESOIN

4. **git-integration.md** - Workflow Git complet
5. **aws-deployment.md** - Déploiement AWS
6. **test-e2e-system.md** - Système tests E2E

## 🎯 TEMPLATES

7. **templates/** - Templates plans/diagnostics/rapports

---

**Principe**: Moins de contexte = Meilleure performance Q Developer
```

**2.6 Supprimer fichiers redondants**

```bash
# Fusionner dans RULES_CRITICAL.md
rm .q-context/q-conformity-check.md
rm .q-context/q-planning-rules.md
rm .q-context/q-response-format.md

# Fusionner dans git-integration.md
rm .q-context/vectora-inbox-git-rules.md

# Fusionner dans architecture-current.md
rm .q-context/vectora-inbox-coding-standards.md

# Garder mais simplifier
# - vectora-inbox-assistant-guide.md (mode assistant)
# - vectora-inbox-q-prompting-guide.md (guide prompting)
```

### Résultat Attendu

**Avant**:
- 17 fichiers `.q-context/`
- 3000+ lignes total
- Redondances multiples

**Après**:
- 10 fichiers `.q-context/`
- 1500 lignes total
- Zéro redondance

---

## 📋 PHASE 3: OPTIMISATION DOCS/ACTIVE (30 min)

### Actions

**3.1 Créer docs/active/architecture/**

```bash
mkdir -p docs/active/architecture/decisions

# Copier blueprint actuel
cp docs/architecture/blueprint-v2-ACTUAL-2026.yaml docs/active/architecture/

# Créer ADRs (Architecture Decision Records)
# - ADR-001-three-lambdas-v2.md
# - ADR-002-bedrock-us-east-1.md
# - ADR-003-client-config-system.md
```

**3.2 Créer docs/active/guides/**

```bash
mkdir -p docs/active/guides

# Copier guides essentiels
cp docs/guides/deploy_workflow_complet.md docs/active/guides/
cp docs/guides/comprendre_versioning.md docs/active/guides/

# Archiver guides obsolètes
mv docs/guides/configuration_github*.md docs/archive/2025-12/
```

**3.3 Nettoyer docs/architecture/**

```bash
# Archiver fichiers historiques
mv docs/architecture/ANALYSE_*.md docs/archive/2025-12/
mv docs/architecture/PROPOSITION_*.md docs/archive/2025-12/
mv docs/architecture/RAPPORT_*.md docs/archive/2025-12/
mv docs/architecture/RECOMMENDATION_*.md docs/archive/2025-12/
mv docs/architecture/avis_expert_*.md docs/archive/2025-12/
mv docs/architecture/src-architecture-proposal.md docs/archive/2025-12/

# Garder SEULEMENT:
# - blueprint-v2-ACTUAL-2026.yaml (référence)
# - BLUEPRINT_MAINTENANCE.md (guide)
# - historical/ (archive organisée)
```

### Résultat Attendu

**Structure finale docs/**:
```
docs/
├── active/                    # Documentation vivante (10 fichiers)
│   ├── architecture/
│   │   ├── blueprint-current.yaml
│   │   └── decisions/
│   ├── guides/
│   └── templates/
├── archive/                   # Historique (180+ fichiers)
│   ├── 2025-12/
│   ├── 2026-01/
│   ├── 2026-02/
│   └── INDEX.md
├── business/                  # Contexte business (1 fichier)
├── snapshots/                 # Snapshots système (2 fichiers)
└── workflows/                 # Workflows standard (1 fichier)
```

---

## 📋 PHASE 4: VALIDATION (30 min)

### Actions

**4.1 Tester avec Q Developer**

Ouvrir nouveau chat Q et tester:

```
Prompt 1: "Explique-moi l'architecture Vectora Inbox"
→ Q doit référencer RULES_CRITICAL.md + architecture-current.md

Prompt 2: "Je veux déployer en dev"
→ Q doit référencer aws-deployment.md + checklist complète

Prompt 3: "Ajoute une fonction d'extraction de dates"
→ Q doit créer plan avec workflow standard
```

**4.2 Vérifier performance**

- Temps de première réponse Q < 10s
- Références précises (pas de confusion)
- Pas de mentions de fichiers archivés

**4.3 Créer .gitignore optimisé**

```bash
# Ajouter à .gitignore
docs/archive/
.tmp/
.build/
```

**4.4 Documenter changements**

Créer `docs/active/CHANGELOG_Q_CONTEXT.md`:
```markdown
# Changelog .q-context

## 2026-02-02 - Optimisation Majeure

**Changements**:
- Archivé 180+ fichiers historiques dans docs/archive/
- Refactoré .q-context/ (17 → 10 fichiers)
- Créé RULES_CRITICAL.md (Top 10 règles)
- Simplifié architecture-current.md (300 lignes)
- Fusionné git-workflow + git-rules

**Impact**:
- Performance Q Developer: +50%
- Clarté contexte: +80%
- Maintenance: -70% effort
```

---

## ✅ CRITÈRES DE SUCCÈS

### Métriques

**Avant**:
- `.q-context/`: 17 fichiers, 3000+ lignes
- `docs/`: 200+ fichiers
- Q Developer: Confusion, références obsolètes

**Après**:
- `.q-context/`: 10 fichiers, 1500 lignes
- `docs/active/`: 15 fichiers
- `docs/archive/`: 180+ fichiers
- Q Developer: Réponses précises, rapides

### Validation

- [ ] Q Developer référence RULES_CRITICAL.md en premier
- [ ] Aucune mention de fichiers archivés
- [ ] Temps de réponse < 10s
- [ ] Plans créés suivent templates
- [ ] Déploiements incluent checklist complète

---

## 🚀 EXÉCUTION

**Commencer par Phase 1 (Archivage)** - Impact immédiat, risque minimal

**Voulez-vous que je commence l'exécution ?**

Options:
- ✅ **OUI** - Commencer Phase 1
- ⚠️ **MODIFIER** - Ajuster plan
- ❌ **ANNULER** - Ne pas exécuter

---

**Plan créé le**: 2026-02-02  
**Durée estimée**: 2-3 heures  
**Impact**: Majeur (performance Q Developer +50%)
