# Test E2E V15 - Index des Livrables

**Date**: 2026-02-03  
**Client**: lai_weekly_v15  
**Canonical**: v2.2  
**Statut**: ✅ COMPLET

---

## 📁 STRUCTURE DES FICHIERS

```
vectora-inbox/
│
├── .tmp/e2e_v15/                           # Dossier temporaire test
│   ├── payload.json                        # Payload invocation lambdas
│   ├── items_ingested.json                 # 29 items ingérés (26 KB)
│   ├── items_normalized.json               # 29 items normalisés (92 KB)
│   ├── items_analysis.md                   # Analyse détaillée item par item
│   ├── newsletter.md                       # Newsletter générée (vide - 0 items)
│   ├── invoke_normalize.py                 # Script invocation normalisation
│   ├── invoke_newsletter.py                # Script invocation newsletter
│   ├── wait_for_normalized.py              # Script attente fichier S3
│   └── generate_analysis.py                # Script génération analyse
│
├── client-config-examples/production/
│   └── lai_weekly_v15.yaml                 # Config client V15 (8.7 KB)
│
└── docs/reports/e2e/
    ├── test_e2e_v15_resume_executif.md                        # Résumé 1 page ⭐
    ├── test_e2e_v15_rapport_ingestion_normalisation_scoring.md # Rapport complet ⭐⭐
    └── test_e2e_v15_rapport_complet_2026-02-03.md             # Rapport détaillé (avec newsletter)
```

---

## 📄 DESCRIPTION DES LIVRABLES

### 🌟 Rapports Principaux

#### 1. `test_e2e_v15_resume_executif.md` ⭐
**Type**: Résumé exécutif (1 page)  
**Usage**: Présentation rapide, décision go/no-go  
**Contenu**:
- Verdict global
- Métriques clés (tableau comparatif V13/V15)
- Top 5 items relevant
- 3 problèmes critiques
- Actions prioritaires V16

#### 2. `test_e2e_v15_rapport_ingestion_normalisation_scoring.md` ⭐⭐
**Type**: Rapport technique complet  
**Usage**: Analyse détaillée pipeline, debug, amélioration  
**Contenu**:
- Résultats par phase (ingestion, normalisation, scoring)
- Validation 6 objectifs canonical v2.2
- Problèmes identifiés avec preuves
- Comparaison V13/V14/V15
- Top 12 items relevant analysés
- Actions prioritaires avec impact

#### 3. `test_e2e_v15_rapport_complet_2026-02-03.md`
**Type**: Rapport exhaustif (avec newsletter)  
**Usage**: Archive complète du test  
**Contenu**: Tout le rapport technique + section newsletter

---

### 📊 Données Brutes

#### 4. `items_ingested.json` (26 KB)
**Contenu**: 29 items ingérés depuis les sources RSS  
**Structure**:
```json
[
  {
    "item_id": "...",
    "title": "...",
    "source_key": "press_corporate__medincell",
    "published_date": "...",
    "content": "...",
    "url": "..."
  }
]
```

#### 5. `items_normalized.json` (92 KB)
**Contenu**: 29 items normalisés avec scoring  
**Structure**:
```json
[
  {
    "item_id": "...",
    "title": "...",
    "normalized_content": {
      "event_type": "...",
      "entities": {
        "companies": [],
        "molecules": [],
        "technologies": [],
        "trademarks": []
      },
      "dosing_intervals_detected": []
    },
    "domain_scoring": {
      "is_relevant": true,
      "score": 90,
      "confidence": "high",
      "signals_detected": {
        "strong": [],
        "medium": [],
        "weak": []
      },
      "reasoning": "..."
    }
  }
]
```

---

### 📝 Analyses

#### 6. `items_analysis.md`
**Contenu**: Analyse détaillée des 12 items relevant + 10 items non relevant  
**Structure**:
- Pour chaque item relevant:
  - Titre, source, event_type, score
  - Entités détectées (companies, molecules, technologies, trademarks, dosing)
  - Signaux LAI (strong, medium, weak)
  - Reasoning
  - Template retour admin (à remplir)
- Pour chaque item non relevant:
  - Titre, source, score, reasoning
  - Template retour admin

---

### ⚙️ Configuration

#### 7. `lai_weekly_v15.yaml` (8.7 KB)
**Contenu**: Configuration client V15  
**Modifications vs V14**:
- client_id: lai_weekly_v14 → lai_weekly_v15
- name: "v14 (Test Canonical v2.2)" → "v15 (Test E2E Canonical v2.2 - Données Fraîches)"
- template_version: 14.0.0 → 15.0.0
- created_by: "Test E2E - Validation Canonical v2.2 avec données fraîches"

---

### 🛠️ Scripts Utilitaires

#### 8. Scripts Python
- `invoke_normalize.py` - Invocation lambda normalisation
- `invoke_newsletter.py` - Invocation lambda newsletter
- `wait_for_normalized.py` - Attente fichier S3 (polling 30s)
- `generate_analysis.py` - Génération items_analysis.md

---

## 📊 MÉTRIQUES GLOBALES

### Ingestion
- Items ingérés: **29**
- Sources: 7 (corporate: 4, press: 3)
- Durée: ~20 secondes

### Normalisation
- Items traités: **29/29** (100%)
- Entités extraites: molecules, technologies, trademarks, dosing intervals
- Durée: ~3 minutes

### Scoring
- Items relevant: **12/29 (41.4%)**
- Score moyen: **81.7/100**
- Distribution: 11 items ≥70, 1 item 40-69, 0 items <40

---

## 🎯 RÉSULTATS CLÉS

### ✅ Succès
- Exclusions corporate_move: ✅
- Exclusions financial_results: ✅
- Détection dosing_intervals: ✅
- Scores cohérents: ✅

### ❌ Problèmes
- Régression companies: ❌ (0 détectées)
- Faux négatif Quince: ❌ (once-monthly non détecté)
- Faux positif Eli Lilly: ⚠️ (manufacturing)

---

## 🔗 LIENS S3

### Fichiers sur AWS S3 (dev)

**Config**:
- `s3://vectora-inbox-config-dev/clients/lai_weekly_v15.yaml`

**Données**:
- `s3://vectora-inbox-data-dev/ingested/lai_weekly_v15/2026/02/03/items.json`
- `s3://vectora-inbox-data-dev/curated/lai_weekly_v15/2026/02/03/items.json`

**Newsletter**:
- `s3://vectora-inbox-newsletters-dev/lai_weekly_v15/2026/02/03/newsletter.md`
- `s3://vectora-inbox-newsletters-dev/lai_weekly_v15/2026/02/03/newsletter.json`
- `s3://vectora-inbox-newsletters-dev/lai_weekly_v15/2026/02/03/manifest.json`

---

## 🚀 PROCHAINES ÉTAPES

### Actions Immédiates (V16)

1. **Restaurer détection companies** (2h)
   - Modifier `config/prompts/generic_normalization.yaml`
   - Ajouter extraction companies_detected

2. **Résoudre faux négatif Quince** (1h)
   - Améliorer extraction dosing_intervals depuis titre
   - Ajouter "once-monthly" dans patterns prioritaires

3. **Exclure Eli Lilly manufacturing** (30min)
   - Ajouter "injectables and devices" aux exclusions
   - Renforcer rule_6

### Test E2E V16

**Objectif**: Valider corrections priorité 1  
**Critères succès**:
- Companies détectées: >0 ✅
- Faux négatif Quince: résolu ✅
- Faux positif Eli Lilly: résolu ✅
- Items relevant: ≥50% ✅

---

## 📞 CONTACT

**Créé par**: Amazon Q Developer  
**Date**: 2026-02-03  
**Durée test**: ~1h30  
**Statut**: ✅ COMPLET - PRÊT POUR V16

---

**Note**: Ce test E2E V15 confirme la stabilité du canonical v2.2 (résultats identiques à V14) et identifie 3 corrections prioritaires pour V16.
