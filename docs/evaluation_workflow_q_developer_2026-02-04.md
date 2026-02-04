# Evaluation Workflow Q Developer - Vectora Inbox

**Date**: 2026-02-04  
**Objectif**: Analyser les problemes actuels et proposer ameliorations  
**Statut**: EVALUATION UNIQUEMENT - Aucune modification

---

## 1. DIAGNOSTIC DES PROBLEMES ACTUELS

### 1.1 Probleme: Q ne suit pas le Q Context

**Observations**:
- Q Context existe (14 fichiers dans `.q-context/`)
- Templates disponibles mais peu utilises
- CRITICAL_RULES.md existe mais pas toujours respecte
- Trop de fichiers = dilution de l'information

**Causes identifiees**:
1. **Surcharge cognitive**: 14 fichiers Q context = trop d'info
2. **Manque de hierarchie**: Pas clair quel fichier est prioritaire
3. **Templates generiques**: Pas assez specifiques au contexte reel
4. **Pas de validation automatique**: Q peut ignorer sans consequence

**Impact**:
- Inconsistance dans les reponses
- Oubli de steps critiques (upload S3, tests, etc.)
- Repetition d'erreurs deja corrigees

---

### 1.2 Probleme: Controle des Modifications Insuffisant

**Observations actuelles**:
- Modifications touchent: Lambdas + Prompts Bedrock + Canonical
- Pas de diff systematique avant/apres
- Pas de backup automatique
- Difficile de rollback proprement

**Exemple concret (aujourd'hui)**:
```
Modification:
- bedrock_client.py (Prompt Caching)
- lai_domain_definition.yaml (v2.0 -> v2.1)
- VERSION (1.4.2 -> 1.4.3)

Probleme: Pas de vue d'ensemble des impacts
```

**Causes**:
1. **Pas de manifest de changements**: Fichiers modifies non listes
2. **Pas de diff pre-commit**: Git commit sans review
3. **Pas de backup S3**: Canonical ecrase sans backup
4. **Versioning partiel**: VERSION existe mais pas pour canonical

**Impact**:
- Risque de regression non detectee
- Impossible de comparer versions
- Rollback complexe

---

### 1.3 Probleme: Tests E2E Inconsistants

**Observations**:
- 20+ rapports E2E dans `docs/reports/e2e/`
- Formats differents (v10, v11, v15, v17)
- Metriques variables selon les tests
- Pas de baseline stable

**Exemple**:
```
V15: 29 items, 0% companies (BUG)
V17: 31 items, 74% companies (FIXE)

Mais format rapport different, metriques differentes
```

**Causes**:
1. **Pas de test de reference**: Chaque test reinvente le format
2. **Template non suivi**: test-e2e-aws-template.md existe mais pas utilise
3. **Metriques ad-hoc**: Chaque test ajoute/retire des metriques
4. **Pas de comparaison automatique**: Comparaison manuelle V15 vs V17

**Impact**:
- Impossible de mesurer progression
- Regressions non detectees
- Temps perdu a reformater

---

## 2. ANALYSE Q CONTEXT ACTUEL

### 2.1 Fichiers Q Context (14 fichiers)

**Structure actuelle**:
```
.q-context/
├── CRITICAL_RULES.md           # 10 regles - BON
├── vectora-inbox-governance.md # Workflow Git - BON
├── architecture.md             # Architecture generale
├── aws-deployment.md           # Deployment AWS
├── git-workflow.md             # Git workflow
├── vectora-inbox-development-rules.md
├── vectora-inbox-layer-management-rules.md
├── q-planning-guide.md
├── q-usage-guide.md
├── prompts-magiques.md
├── vectora-inbox-assistant-guide.md
├── vectora-inbox-q-prompting-guide.md
├── README.md
└── templates/
    ├── plan-development-template.md
    ├── plan-diagnostic-template.md
    ├── report-final-template.md
    └── test-e2e-aws-template.md
```

**Problemes identifies**:
1. **Trop de fichiers**: 14 fichiers = surcharge
2. **Redondance**: Plusieurs fichiers couvrent memes sujets
3. **Pas de priorite claire**: Quel fichier lire en premier?
4. **Templates peu utilises**: Existent mais Q ne les suit pas

**Ce qui marche**:
- ✅ CRITICAL_RULES.md: Clair, concis, actionnable
- ✅ vectora-inbox-governance.md: Workflow Git bien defini
- ✅ test-e2e-aws-template.md: Complet et detaille

**Ce qui ne marche pas**:
- ❌ Trop de fichiers "guide" generiques
- ❌ Pas de checklist pre-action
- ❌ Pas de validation automatique

---

### 2.2 Test E2E V17: Le Meilleur Exemple

**Pourquoi V17 est excellent**:
```markdown
# Structure claire
1. Resume executif (verdict immediat)
2. Metriques comparatives (V15 vs V17)
3. Distribution sources/scores
4. Top 5 items relevant
5. Analyse faux negatifs (0 detectes)
6. Validation cas d'usage
7. Recommandations actionnables
8. Annexes (fichiers, commandes, versions)
```

**Metriques completes**:
- Items ingeres: 31
- Companies: 23/31 (74%)
- Items relevant: 20/31 (64%)
- Score moyen: 71.5
- Faux negatifs: 0
- Distribution scores
- Distribution sources

**Ce qui le rend reproductible**:
- Client ID: lai_weekly_v17
- Date: 2026-02-03
- Versions: vectora-core 1.4.2, canonical 2.3
- Fichiers generes listes
- Commandes executees documentees

---

## 3. PLAN D'AMELIORATION PROPOSE

### 3.1 Simplifier Q Context (Priorite HAUTE)

**Objectif**: Reduire 14 fichiers a 3 fichiers essentiels

**Proposition**:
```
.q-context/
├── 00-START-HERE.md           # Point d'entree unique
├── CRITICAL_RULES.md           # 10 regles (INCHANGE)
└── GOLDEN_TEST_E2E.md          # Test de reference V17
```

**00-START-HERE.md** (NOUVEAU):
```markdown
# Q Developer - Point d'Entree Vectora Inbox

## Avant TOUTE action, lire dans l'ordre:

1. **CRITICAL_RULES.md** (2 min)
   - 10 regles NON-NEGOCIABLES
   - Checklist pre-action

2. **GOLDEN_TEST_E2E.md** (5 min)
   - Test de reference V17
   - Metriques baseline
   - Format rapport standard

3. **Ce fichier** (3 min)
   - Workflow modifications
   - Checklist validation
   - Commandes essentielles

## Workflow Modification (OBLIGATOIRE)

### Etape 1: Planification (AVANT code)
- [ ] Lire CRITICAL_RULES.md
- [ ] Identifier fichiers impactes (Lambda/Prompt/Canonical)
- [ ] Creer MANIFEST.md listant tous les changements
- [ ] Valider avec utilisateur

### Etape 2: Backup (AVANT modification)
- [ ] Git: Creer branche feature/xxx
- [ ] S3: Backup canonical si modifie
- [ ] Documenter versions actuelles

### Etape 3: Modification (Code)
- [ ] Modifier fichiers selon MANIFEST
- [ ] Incrementer VERSION
- [ ] Commit (AVANT build)

### Etape 4: Validation (Tests)
- [ ] Build + Deploy dev
- [ ] Upload S3 si canonical modifie
- [ ] Test E2E selon GOLDEN_TEST_E2E.md
- [ ] Comparer metriques vs baseline

### Etape 5: Documentation (Rapport)
- [ ] Creer rapport selon format GOLDEN_TEST_E2E.md
- [ ] Lister fichiers modifies
- [ ] Documenter metriques
- [ ] Proposer merge si succes

## Commandes Essentielles

# Build
python scripts/build/build_all.py

# Deploy dev
python scripts/deploy/deploy_env.py --env dev

# Upload canonical (si modifie)
aws s3 sync canonical/ s3://vectora-inbox-data-dev/canonical/ --profile rag-lai-prod

# Test E2E
python scripts/invoke/invoke_normalize_score_v2.py --event lai_weekly_vX

# Backup S3 (avant modification)
aws s3 sync s3://vectora-inbox-data-dev/canonical/ .tmp/backup_canonical/ --profile rag-lai-prod
```

**Avantages**:
- 1 point d'entree clair
- Workflow obligatoire
- Checklist systematique
- Reduit surcharge cognitive

---

### 3.2 Golden Test E2E (Priorite HAUTE)

**Objectif**: Figer V17 comme test de reference

**Proposition**: Creer `.q-context/GOLDEN_TEST_E2E.md`

**Contenu**:
```markdown
# Golden Test E2E - Baseline Vectora Inbox

**Version**: V17 (2026-02-03)
**Client**: lai_weekly_v17
**Statut**: REFERENCE STABLE - Ne pas modifier

## Baseline Metriques (CIBLE)

| Metrique | Valeur V17 | Seuil Min | Seuil Max |
|----------|------------|-----------|-----------|
| Items ingeres | 31 | 25 | 40 |
| Companies detectees | 74% | 70% | 100% |
| Items relevant | 64% | 60% | 80% |
| Score moyen | 71.5 | 65 | 85 |
| Faux negatifs | 0 | 0 | 1 |
| Domain scoring | 100% | 100% | 100% |

## Format Rapport Standard

Tout nouveau test E2E DOIT suivre ce format:

### 1. Resume Executif
- Verdict: SUCCES / ECHEC
- Comparaison vs V17
- Decision: MERGE / CORRIGER

### 2. Metriques Comparatives
- Tableau V17 vs VX
- Evolution en %
- Statut vs seuils

### 3. Distribution
- Sources (tableau)
- Scores (plages)

### 4. Top 5 Items Relevant
- Titre, companies, molecules, technologies
- Score et justification

### 5. Analyse Faux Negatifs
- Liste items rejetes suspects
- Validation rejets justifies

### 6. Validation Cas d'Usage
- Dosing dans titre
- Pure player
- Manufacturing generique
- Grant/funding

### 7. Recommandations
- Court terme (avant merge)
- Moyen terme (post-merge)
- Long terme

### 8. Annexes
- Fichiers generes
- Commandes executees
- Versions (vectora-core, canonical, client)

## Script Comparaison Automatique

python scripts/test/compare_e2e.py --baseline v17 --current vX
```

**Avantages**:
- Baseline stable
- Format standardise
- Comparaison automatique
- Metriques objectives

---

### 3.3 Manifest de Changements (Priorite MOYENNE)

**Objectif**: Tracer tous les fichiers modifies

**Proposition**: Creer `MANIFEST.md` pour chaque modification

**Format**:
```markdown
# Manifest Changements - [Titre Modification]

**Date**: 2026-02-04
**Branche**: feature/xxx
**Objectif**: [Description]

## Fichiers Modifies

### Lambdas (src_v2/)
- [ ] src_v2/vectora_core/normalization/bedrock_client.py
  - Ligne 250-280: Ajout Prompt Caching
  - Impact: Latence Bedrock -80%

### Prompts Bedrock (canonical/prompts/)
- [ ] Aucun

### Canonical (canonical/)
- [ ] canonical/domains/lai_domain_definition.yaml
  - v2.0 -> v2.1
  - Suppression 19 exemples inline
  - Reduction 25.8% tokens

### Configuration
- [ ] VERSION: 1.4.2 -> 1.4.3

## Impact S3

### Fichiers a uploader
- [ ] s3://vectora-inbox-data-dev/canonical/domains/lai_domain_definition.yaml

### Backup requis
- [ ] Backup lai_domain_definition.yaml v2.0

## Tests Requis

- [ ] Test local: Validation structure
- [ ] Test AWS: lai_weekly_vX
- [ ] Comparaison vs V17 baseline

## Rollback Plan

Si echec:
1. Restaurer lai_domain_definition.yaml v2.0 depuis backup
2. Rollback bedrock_client.py via Git
3. Rebuild + redeploy version 1.4.2
```

**Avantages**:
- Vue d'ensemble impacts
- Checklist validation
- Plan rollback clair
- Traçabilite complete

---

### 3.4 Script Comparaison E2E (Priorite MOYENNE)

**Objectif**: Automatiser comparaison tests

**Proposition**: Creer `scripts/test/compare_e2e.py`

**Fonctionnalites**:
```python
# Compare 2 tests E2E
python scripts/test/compare_e2e.py --baseline v17 --current v18

# Output:
# ================================================================================
# COMPARAISON E2E: V17 (baseline) vs V18 (current)
# ================================================================================
#
# Metriques:
#   Items ingeres:       31 -> 28 (-9.7%)  [WARNING: < seuil 25]
#   Companies:           74% -> 82% (+10.8%) [OK]
#   Items relevant:      64% -> 71% (+10.9%) [OK]
#   Score moyen:         71.5 -> 68.2 (-4.6%) [OK]
#   Faux negatifs:       0 -> 1 (+1) [WARNING]
#
# Verdict: ATTENTION - 2 warnings detectes
#
# Recommandation: Investiguer baisse items ingeres et faux negatif
```

**Avantages**:
- Comparaison automatique
- Detection regressions
- Verdict objectif
- Gain temps

---

### 3.5 Backup Automatique S3 (Priorite BASSE)

**Objectif**: Backup canonical avant modification

**Proposition**: Script `scripts/backup/backup_canonical_s3.py`

**Fonctionnalites**:
```bash
# Backup avant modification
python scripts/backup/backup_canonical_s3.py --env dev

# Output:
# Backup cree: s3://vectora-inbox-data-dev/canonical_backups/2026-02-04_143022/
#   - domains/lai_domain_definition.yaml
#   - prompts/domain_scoring/lai_domain_scoring.yaml
#   - scopes/company_scopes.yaml
#   [...]
#
# Restore si besoin:
# python scripts/backup/restore_canonical_s3.py --backup 2026-02-04_143022 --env dev
```

**Avantages**:
- Rollback facile
- Historique versions
- Securite

---

## 4. PLAN D'IMPLEMENTATION

### Phase 1: Simplification Q Context (1h)

**Actions**:
1. Creer `.q-context/00-START-HERE.md`
2. Creer `.q-context/GOLDEN_TEST_E2E.md` (copie V17)
3. Archiver 11 autres fichiers dans `.q-context/archive/`
4. Tester avec Q sur une modification simple

**Validation**:
- Q lit 00-START-HERE.md en premier
- Q suit workflow obligatoire
- Q utilise format GOLDEN_TEST_E2E.md

---

### Phase 2: Manifest + Comparaison (2h)

**Actions**:
1. Creer template `MANIFEST.md`
2. Creer script `scripts/test/compare_e2e.py`
3. Tester sur prochaine modification

**Validation**:
- MANIFEST cree avant modification
- Comparaison automatique vs V17
- Verdict objectif

---

### Phase 3: Backup S3 (1h)

**Actions**:
1. Creer script `scripts/backup/backup_canonical_s3.py`
2. Creer script `scripts/backup/restore_canonical_s3.py`
3. Integrer dans workflow

**Validation**:
- Backup automatique avant upload
- Restore fonctionne
- Historique conserve

---

## 5. BENEFICES ATTENDUS

### Court Terme (Semaine 1)
- ✅ Q suit workflow systematiquement
- ✅ Moins d'oublis (upload S3, tests, etc.)
- ✅ Rapports E2E standardises

### Moyen Terme (Mois 1)
- ✅ Comparaison automatique tests
- ✅ Detection regressions immediate
- ✅ Rollback facile si probleme

### Long Terme (Mois 3+)
- ✅ Historique complet modifications
- ✅ Metriques progression claires
- ✅ Confiance dans stabilite systeme

---

## 6. RISQUES ET MITIGATIONS

### Risque 1: Q ignore toujours le Q Context

**Mitigation**:
- Reduire a 3 fichiers essentiels
- Workflow obligatoire avec checklist
- Validation utilisateur a chaque etape

### Risque 2: Scripts complexes non utilises

**Mitigation**:
- Scripts simples et focalisés
- Documentation claire
- Integration progressive

### Risque 3: Overhead processus

**Mitigation**:
- Automatiser maximum (comparaison, backup)
- Checklist rapide (5 min)
- Benefices > cout

---

## 7. CONCLUSION

### Problemes Identifies
1. ❌ Q Context trop complexe (14 fichiers)
2. ❌ Pas de controle modifications
3. ❌ Tests E2E inconsistants

### Solutions Proposees
1. ✅ Simplifier a 3 fichiers essentiels
2. ✅ Manifest + Backup systematiques
3. ✅ Golden Test V17 comme reference

### Prochaines Etapes
1. Valider plan avec utilisateur
2. Implementer Phase 1 (Simplification)
3. Tester sur prochaine modification
4. Ajuster selon feedback

---

**Evaluation creee**: 2026-02-04  
**Statut**: PROPOSITION - Aucune modification effectuee  
**Decision**: Attente validation utilisateur
