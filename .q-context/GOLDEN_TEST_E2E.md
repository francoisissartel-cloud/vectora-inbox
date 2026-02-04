# Golden Test E2E - Baseline Vectora Inbox

**Version**: V17 (2026-02-03)  
**Client**: lai_weekly_v17  
**Statut**: REFERENCE STABLE - Ne pas modifier  
**Source**: docs/reports/e2e/test_e2e_v17_rapport_2026-02-03.md

---

## BASELINE METRIQUES (CIBLE)

| Metrique | Valeur V17 | Seuil Min | Seuil Max | Statut |
|----------|------------|-----------|-----------|--------|
| Items ingeres | 31 | 25 | 40 | ✅ |
| Companies detectees | 74% (23/31) | 70% | 100% | ✅ |
| Items relevant | 64% (20/31) | 60% | 80% | ✅ |
| Score moyen | 71.5 | 65 | 85 | ✅ |
| Faux negatifs | 0 | 0 | 1 | ✅ |
| Domain scoring | 100% (31/31) | 100% | 100% | ✅ |

**Verdict V17**: ✅ SUCCES COMPLET - Tous objectifs atteints

---

## CONTEXTE V17

### Versions
- **vectora-core**: 1.4.2 (layer dev:55)
- **canonical**: 2.3
- **client**: lai_weekly_v17
- **environnement**: dev
- **date**: 2026-02-03

### Objectif Test
Validation corrections V16:
- Fix detection companies (0% → 74%)
- Fix items relevant (41% → 64%)
- Validation sur donnees fraiches

### Resultats
- +74% companies detectees vs V15
- +23% items relevant vs V15
- 0 faux negatifs detectes
- Workflow complet fonctionnel

---

## FORMAT RAPPORT STANDARD

**Tout nouveau test E2E DOIT suivre ce format**:

### 1. Resume Executif

```markdown
## Resume Executif

[Verdict]: SUCCES / ATTENTION / ECHEC

[Description courte du test]

Resultats cles:
- Companies: X% (objectif 70%+) [Statut]
- Items relevant: X% (objectif 60%+) [Statut]
- Faux negatifs: X (objectif 0) [Statut]

[Decision]: MERGE / CORRIGER / ROLLBACK
```

---

### 2. Metriques Comparatives

```markdown
## Metriques

| Metrique | V17 | VX | Evolution | Cible | Statut |
|----------|-----|-----|-----------|-------|--------|
| Items ingeres | 31 | X | +X% | 25-35 | ✅/❌ |
| Companies | 74% | X% | +X% | ≥70% | ✅/❌ |
| Items relevant | 64% | X% | +X% | ≥60% | ✅/❌ |
| Score moyen | 71.5 | X | +X | 65-85 | ✅/❌ |
| Domain scoring | 100% | X% | +X% | 100% | ✅/❌ |
| Faux negatifs | 0 | X | +X | ≤1 | ✅/❌ |
```

---

### 3. Distribution Sources

```markdown
## Distribution des Sources

| Source | Items |
|--------|-------|
| press_corporate__medincell | X |
| press_corporate__nanexa | X |
| press_sector__fiercepharma | X |
| [...]

**Total**: X items de Y sources
```

**V17 Reference**:
- 31 items de 7 sources
- Medincell: 8, Nanexa: 6, Fiercepharma: 5

---

### 4. Distribution Scores

```markdown
## Distribution des Scores

| Plage | Nombre | % |
|-------|--------|---|
| 80-100 | X | X% |
| 60-79 | X | X% |
| 40-59 | X | X% |
| 0-39 | X | X% |
| 0 (rejete) | X | X% |

**Items relevant**: X/Y (Z%)
**Items rejetes**: X/Y (Z%)
```

**V17 Reference**:
- 80-100: 11 (35%)
- 60-79: 6 (19%)
- 0 (rejete): 11 (35%)

---

### 5. Top 5 Items Relevant

```markdown
## Top 5 Items Relevant

### 1. [Titre] (Score: X)
- **Companies**: [liste]
- **Molecules**: [liste]
- **Technologies**: [liste]
- **Dosing**: [intervalle]
- **Signaux forts**: [liste]
- **Event**: [type]

[Repeter pour items 2-5]
```

**V17 Reference Top 1**:
- Medincell/Teva - NDA Submission (Score: 90)
- Companies: Medincell, Teva
- Molecules: olanzapine
- Technologies: extended-release injectable
- Dosing: once-monthly

---

### 6. Analyse Faux Negatifs

```markdown
## Analyse Faux Negatifs

**Items rejetes**: X
**Items suspects** (rejetes mais avec signaux LAI): X

### Analyse Items Suspects

[Pour chaque item suspect]:
- **Titre**: [titre]
- **Technologies**: [liste]
- **Rejet justifie**: OUI / NON
- **Raison**: [explication]

**Conclusion**: X faux negatifs detectes
```

**V17 Reference**:
- 11 items rejetes
- 3 items suspects analyses
- 0 faux negatifs (tous rejets justifies)

---

### 7. Validation Cas d'Usage

```markdown
## Validation Cas d'Usage Specifiques

- [ ] Item avec dosing dans titre: [Statut]
- [ ] Item grant/funding: [Statut]
- [ ] Item pure_player: [Statut]
- [ ] Item manufacturing generique: [Statut]
- [ ] Item hybrid company: [Statut]
```

**V17 Reference**:
- ✅ Dosing dans titre: Detecte (Nanexa semaglutide "monthly")
- ✅ Pure player: Score eleve (Medincell 90, Camurus 85)
- ✅ Manufacturing generique: Non present

---

### 8. Recommandations

```markdown
## Recommandations

### Court Terme (Avant Merge)
1. [Action priorite critique]
2. [Action priorite haute]

### Moyen Terme (Post-Merge)
1. [Amelioration]
2. [Optimisation]

### Long Terme
1. [Evolution]
2. [Extension]
```

---

### 9. Annexes

```markdown
## Annexes

### Fichiers Generes
- `.tmp/vX_ingested.json` - X items ingeres
- `.tmp/vX_curated.json` - X items normalises
- `docs/reports/e2e/test_e2e_vX_rapport_YYYY-MM-DD.md` - Rapport complet

### Commandes Executees
[Liste commandes AWS CLI]

### Versions
- vectora-core: X.Y.Z
- canonical: X.Y
- client: lai_weekly_vX
- environnement: dev
```

---

## SCRIPT ANALYSE RAPIDE

```bash
# Telecharger resultats
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_vX/YYYY/MM/DD/items.json .tmp/vX_curated.json --profile rag-lai-prod

# Metriques essentielles
python -c "
import json
items = json.load(open('.tmp/vX_curated.json', encoding='utf-8'))

# Calculs
total = len(items)
with_ds = sum(1 for i in items if i.get('has_domain_scoring'))
relevant = sum(1 for i in items if i.get('domain_scoring',{}).get('is_relevant'))
companies = sum(1 for i in items if i.get('normalized_content',{}).get('entities',{}).get('companies'))
scores = [i.get('domain_scoring',{}).get('score',0) for i in items if i.get('has_domain_scoring')]
avg_score = sum(scores)/len(scores) if scores else 0

# Affichage
print(f'Items ingeres: {total}')
print(f'Domain scoring: {with_ds}/{total} ({with_ds/total*100:.0f}%)')
print(f'Companies: {companies}/{total} ({companies/total*100:.0f}%)')
print(f'Relevant: {relevant}/{with_ds} ({relevant/with_ds*100:.0f}%)')
print(f'Score moyen: {avg_score:.1f}')

# Comparaison V17
print(f'\nComparaison vs V17:')
print(f'Companies: {companies/total*100:.0f}% vs 74% (seuil 70%)')
print(f'Relevant: {relevant/with_ds*100:.0f}% vs 64% (seuil 60%)')
print(f'Score moyen: {avg_score:.1f} vs 71.5 (seuil 65-85)')
"
```

---

## CRITERES DECISION

### ✅ SUCCES (Merge immediat)
- Toutes metriques >= seuils min
- 0-1 faux negatifs
- Aucune regression vs V17

### ⚠️ ATTENTION (Merge avec reserves)
- 1-2 metriques < seuils (mais proches)
- Justification claire
- Plan correction court terme

### ❌ ECHEC (Rollback requis)
- 3+ metriques < seuils
- Faux negatifs > 1
- Regression majeure vs V17

---

## EXEMPLE COMPLET V17

### Resume Executif V17
```
✅ SUCCES COMPLET - Tous objectifs atteints

Corrections V16 validees sur donnees fraiches:
- Companies: 74% (objectif 70%+) ✅
- Items relevant: 64% (objectif 60%+) ✅
- Faux negatifs: 0 ✅

Decision: MERGE IMMEDIAT dans develop
```

### Metriques V17
```
| Metrique | V15 | V17 | Evolution | Cible | Statut |
|----------|-----|-----|-----------|-------|--------|
| Items | 29 | 31 | +2 | 25-35 | ✅ |
| Companies | 0% | 74% | +74% | ≥70% | ✅ |
| Relevant | 41% | 64% | +23% | ≥60% | ✅ |
| Score moyen | 81.7 | 71.5 | -10.2 | 65-85 | ✅ |
```

### Top 1 Item V17
```
1. Medincell/Teva - NDA Submission (Score: 90)
   - Companies: Medincell, Teva
   - Molecules: olanzapine
   - Technologies: extended-release injectable
   - Dosing: once-monthly
   - Signaux: Pure player + trademark TEV-'749
   - Event: Regulatory
```

---

## UTILISATION PAR Q DEVELOPER

**Q DOIT**:
1. Lire ce fichier AVANT tout test E2E
2. Suivre format rapport EXACTEMENT
3. Comparer metriques vs baseline V17
4. Utiliser script analyse rapide
5. Appliquer criteres decision

**Q NE DOIT JAMAIS**:
- Inventer nouveau format rapport
- Ignorer comparaison vs V17
- Merge sans validation metriques
- Modifier ce fichier (reference stable)

---

**Golden Test cree**: 2026-02-04  
**Base sur**: V17 (2026-02-03)  
**Statut**: REFERENCE STABLE  
**Prochaine revision**: Apres 10+ tests reussis
