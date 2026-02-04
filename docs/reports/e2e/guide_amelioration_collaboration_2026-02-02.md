# Guide Pratique : Améliorer Notre Collaboration sur Tests E2E

**Date** : 2026-02-02  
**Objectif** : Actions concrètes pour améliorer collaboration Q Developer + Admin

---

## 🎯 3 ACTIONS IMMÉDIATES (Cette Semaine)

### Action 1 : Créer Prompts Magiques

**Créer** : `.q-context/prompts-magiques.md`

```markdown
# Prompts Magiques Vectora Inbox

## Test E2E Complet

**Prompt à copier-coller** :
```
@e2e-complet lai_weekly_v11 baseline:v10

Objectif : [Décrire objectif du test]
```

**Q comprendra automatiquement** :
- Utiliser template docs/templates/TEMPLATE_TEST_E2E_STANDARD.md
- Comparer avec baseline v10
- Workflow complet (build, deploy, test, analyse)
- Télécharger fichiers S3
- Analyser item par item
- Calculer coûts
- Générer rapport exploitable

## Test E2E Rapide (Focus Matching)

**Prompt à copier-coller** :
```
@e2e-matching lai_weekly_v11 baseline:v10

Focus : Phase 2 (normalisation & scoring)
```

## Analyse Fichiers S3 Existants

**Prompt à copier-coller** :
```
@analyse-s3 lai_weekly_v11

Télécharge et analyse :
- ingested_items.json
- normalized_items.json
- Génère rapport détaillé
```

## Comparaison Versions

**Prompt à copier-coller** :
```
@compare v10 v11 v12

Génère tableau comparatif avec évolution métriques
```
```

**Avantage** : Vous copiez-collez, Q sait exactement quoi faire.

### Action 2 : Créer Script E2E Automatisé

**Créer** : `scripts/invoke/invoke_e2e_complete.py`

```python
#!/usr/bin/env python3
"""
Script E2E complet avec analyse automatique.

Usage:
    python scripts/invoke/invoke_e2e_complete.py \
        --client-id lai_weekly_v11 \
        --baseline lai_weekly_v10 \
        --output docs/reports/e2e/test_e2e_v11_rapport_2026-02-02.md

Workflow automatique:
1. Exécute workflow E2E (ingest + normalize + newsletter)
2. Télécharge fichiers S3
3. Analyse résultats
4. Remplit template standard
5. Compare avec baseline
6. Génère rapport complet

Garantit:
- ✅ Aucune étape oubliée
- ✅ Métriques complètes
- ✅ Analyse item par item
- ✅ Coûts calculés
- ✅ Rapport exploitable
"""

import argparse
import json
import subprocess
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Test E2E complet automatisé")
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    
    print(f"🚀 Test E2E complet : {args.client_id}")
    print(f"📊 Baseline : {args.baseline}")
    
    # 1. Exécuter workflow E2E
    print("\n1️⃣ Exécution workflow E2E...")
    subprocess.run([
        "python", "scripts/invoke/invoke_e2e_workflow.py",
        "--client-id", args.client_id,
        "--env", "dev"
    ], check=True)
    
    # 2. Télécharger fichiers S3
    print("\n2️⃣ Téléchargement fichiers S3...")
    subprocess.run([
        "aws", "s3", "cp",
        f"s3://vectora-inbox-data-dev/runs/{args.client_id}/latest/ingested_items.json",
        f".tmp/e2e/{args.client_id}_ingested.json",
        "--profile", "rag-lai-prod"
    ], check=True)
    
    subprocess.run([
        "aws", "s3", "cp",
        f"s3://vectora-inbox-data-dev/runs/{args.client_id}/latest/normalized_items.json",
        f".tmp/e2e/{args.client_id}_normalized.json",
        "--profile", "rag-lai-prod"
    ], check=True)
    
    # 3. Analyser résultats
    print("\n3️⃣ Analyse résultats...")
    subprocess.run([
        "python", "scripts/analysis/analyze_e2e_results.py",
        "--ingested", f".tmp/e2e/{args.client_id}_ingested.json",
        "--normalized", f".tmp/e2e/{args.client_id}_normalized.json",
        "--baseline", args.baseline,
        "--output", args.output
    ], check=True)
    
    print(f"\n✅ Rapport E2E complet généré : {args.output}")

if __name__ == "__main__":
    main()
```

**Avantage** : Une commande, tout est fait automatiquement.

### Action 3 : Ajouter Détection Automatique dans Q Context

**Modifier** : `.q-context/vectora-inbox-development-rules.md`

**Ajouter cette section** :

```markdown
## 🤖 DÉTECTION AUTOMATIQUE TESTS E2E (CRITIQUE)

### Règle de Détection

**Q Developer DOIT détecter automatiquement une demande de test E2E si** :

**Triggers détection** :
- Prompt contient "test E2E" ou "test e2e" ou "E2E"
- Prompt contient "invoke_normalize_score_v2.py"
- Prompt contient "lai_weekly_vX" (pattern version)
- Prompt contient "tester" + nom client
- Prompt contient "@e2e" (prompt magique)

### Comportement Obligatoire Après Détection

**Si détection → Q DOIT** :

1. **STOP** : Ne pas exécuter immédiatement
2. **CONSULTER** : Lire section "RÈGLES DE TESTS E2E"
3. **PROPOSER** : Plan complet avec template standard
4. **DEMANDER** : "Voulez-vous A) Test technique simple OU B) Test E2E complet ?"
5. **ATTENDRE** : Validation utilisateur
6. **EXÉCUTER** : Workflow complet après validation

### Exemple Détection

**Prompt utilisateur** :
```
Teste lai_weekly_v11
```

**Q DOIT répondre** :
```
🔍 DÉTECTION : Test E2E

Je détecte une demande de test E2E pour lai_weekly_v11.

Selon Q Context, un test E2E peut être :

A) **Test technique simple** (ce que vous avez demandé)
   - Exécute workflow (ingest + normalize)
   - Vérifie StatusCode 200
   - Rapport basique
   - Durée : ~5 min

B) **Test E2E complet** (recommandé)
   - Utilise template standard
   - Analyse item par item
   - Métriques détaillées
   - Comparaison baseline
   - Coûts calculés
   - Rapport exploitable
   - Durée : ~15 min

Que souhaitez-vous ?
```

### Exception

**Si prompt contient "juste" ou "seulement" ou "quick"** :
```
Fais juste un test rapide de v11
```
→ Q peut exécuter test technique simple sans proposer plan
```

**Avantage** : Q détecte automatiquement et propose le bon workflow.

---

## 🔧 5 ACTIONS MOYEN TERME (Ce Mois)

### Action 4 : Créer Checklist Interactive

**Créer** : `scripts/maintenance/checklist_e2e.py`

```python
#!/usr/bin/env python3
"""
Checklist interactive pré-test E2E.

Usage:
    python scripts/maintenance/checklist_e2e.py

Vérifie:
- Baseline identifiée
- Template copié
- Client config uploadé
- Lambdas déployées
- AWS CLI configuré

Génère prompt optimal pour Q Developer.
"""

def main():
    print("📋 CHECKLIST PRÉ-TEST E2E\n")
    
    # 1. Client ID
    client_id = input("Client ID à tester (ex: lai_weekly_v11) : ")
    
    # 2. Baseline
    baseline = input("Baseline de comparaison (ex: lai_weekly_v10) : ")
    
    # 3. Objectif
    objectif = input("Objectif du test (ex: Valider cleanup prompts) : ")
    
    # 4. Type test
    print("\nType de test :")
    print("1. Test E2E complet (recommandé)")
    print("2. Test technique simple")
    print("3. Focus matching")
    print("4. Focus newsletter")
    type_test = input("Choix (1-4) : ")
    
    # Générer prompt optimal
    print("\n" + "="*60)
    print("✅ PROMPT OPTIMAL POUR Q DEVELOPER")
    print("="*60 + "\n")
    
    if type_test == "1":
        print(f"""Exécute un test E2E complet de {client_id} en utilisant le template 
docs/templates/TEMPLATE_TEST_E2E_STANDARD.md

Baseline : {baseline}

Objectif : {objectif}

Workflow complet :
1. Build & deploy
2. Exécuter workflow E2E (ingest + normalize + newsletter)
3. Télécharger fichiers S3
4. Analyser résultats avec template
5. Analyser item par item
6. Calculer coûts
7. Comparer avec baseline
8. Générer recommandations

Sauvegarde dans : docs/reports/e2e/test_e2e_{client_id.split('_')[-1]}_rapport_2026-02-02.md
""")
    
    print("\n" + "="*60)
    print("📋 Copiez-collez ce prompt dans Q Developer")
    print("="*60)

if __name__ == "__main__":
    main()
```

**Avantage** : Génère le prompt optimal automatiquement.

### Action 5 : Créer Validation Automatique Rapport

**Créer** : `scripts/maintenance/validate_e2e_report.py`

```python
#!/usr/bin/env python3
"""
Valide qu'un rapport E2E est complet.

Usage:
    python scripts/maintenance/validate_e2e_report.py \
        --report docs/reports/e2e/test_e2e_v11_rapport_2026-02-02.md

Vérifie:
- Toutes sections template présentes
- Métriques quantitatives remplies
- Analyse item par item effectuée
- Comparaison baseline effectuée
- Coûts calculés

Output:
- ✅ Rapport complet (100%)
- ⚠️ Rapport partiel (X% complet)
- ❌ Rapport invalide (<50% complet)
"""

import argparse
from pathlib import Path

SECTIONS_REQUISES = [
    "MÉTADONNÉES DU TEST",
    "RÉSUMÉ EXÉCUTIF",
    "PHASE 1 : INGESTION",
    "PHASE 2 : NORMALISATION & SCORING",
    "PHASE 3 : GÉNÉRATION NEWSLETTER",
    "ANALYSE ITEM PAR ITEM",
    "MÉTRIQUES DE PERFORMANCE",
    "ANALYSE COÛTS DÉTAILLÉE",
    "RECOMMANDATIONS D'AMÉLIORATION",
    "DÉCISION FINALE"
]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    
    content = Path(args.report).read_text()
    
    sections_found = []
    sections_missing = []
    
    for section in SECTIONS_REQUISES:
        if section in content:
            sections_found.append(section)
        else:
            sections_missing.append(section)
    
    completude = len(sections_found) / len(SECTIONS_REQUISES) * 100
    
    print(f"\n📊 VALIDATION RAPPORT E2E\n")
    print(f"Fichier : {args.report}")
    print(f"Complétude : {completude:.0f}%\n")
    
    if completude == 100:
        print("✅ RAPPORT COMPLET")
        print("Toutes les sections sont présentes.\n")
    elif completude >= 70:
        print("⚠️ RAPPORT PARTIEL")
        print(f"Sections manquantes ({len(sections_missing)}) :")
        for section in sections_missing:
            print(f"  - {section}")
        print()
    else:
        print("❌ RAPPORT INVALIDE")
        print(f"Trop de sections manquantes ({len(sections_missing)}/{len(SECTIONS_REQUISES)})")
        print()
    
    # Vérifier métriques quantitatives
    has_metrics = "| Métrique |" in content
    has_costs = "Coûts Bedrock" in content
    has_items = "Item #" in content
    
    print("Vérifications supplémentaires :")
    print(f"  {'✅' if has_metrics else '❌'} Métriques quantitatives")
    print(f"  {'✅' if has_costs else '❌'} Analyse coûts")
    print(f"  {'✅' if has_items else '❌'} Analyse item par item")
    print()

if __name__ == "__main__":
    main()
```

**Avantage** : Détecte immédiatement si rapport incomplet.

### Action 6 : Créer Baseline de Référence

**Action** : Refaire test E2E v10 avec template standard

```bash
# 1. Refaire v10 correctement
python scripts/invoke/invoke_e2e_complete.py \
    --client-id lai_weekly_v10 \
    --baseline lai_weekly_v9 \
    --output docs/reports/e2e/test_e2e_v10_baseline_2026-02-02.md

# 2. Marquer comme baseline
cp docs/reports/e2e/test_e2e_v10_baseline_2026-02-02.md \
   docs/reports/e2e/BASELINE_REFERENCE.md

# 3. Documenter
echo "Baseline de référence : lai_weekly_v10 (2026-02-02)" > docs/reports/e2e/BASELINE.txt
```

**Avantage** : Baseline claire pour toutes comparaisons futures.

### Action 7 : Créer Exemples Bons/Mauvais Rapports

**Créer** : `docs/templates/EXEMPLES_RAPPORTS_E2E.md`

```markdown
# Exemples Rapports E2E

## ✅ BON RAPPORT (À Suivre)

**Fichier** : docs/reports/e2e/test_e2e_v10_baseline_2026-02-02.md

**Caractéristiques** :
- ✅ Toutes sections template remplies
- ✅ Métriques quantitatives précises
- ✅ Analyse item par item (29 items)
- ✅ Comparaison baseline (colonnes "vs Baseline")
- ✅ Coûts détaillés (Bedrock + AWS)
- ✅ Recommandations priorisées
- ✅ Décision GO/NO-GO documentée

**Complétude** : 100%

## ❌ MAUVAIS RAPPORT (À Éviter)

**Fichier** : docs/reports/e2e/test_e2e_v11_rapport_2026-02-02.md (version initiale)

**Problèmes** :
- ❌ Sections template manquantes (70%)
- ❌ Métriques superficielles
- ❌ Pas d'analyse item par item
- ❌ Pas de comparaison baseline
- ❌ Pas d'analyse coûts
- ❌ Recommandations vagues

**Complétude** : 30%

## 📊 Comparaison

| Aspect | Bon Rapport | Mauvais Rapport |
|--------|-------------|-----------------|
| Lignes | 800+ | 150 |
| Sections | 10/10 | 3/10 |
| Métriques | 50+ | 5 |
| Items analysés | 29/29 | 0/29 |
| Coûts | Détaillés | Absents |
| Exploitable | ✅ Oui | ❌ Non |
```

**Avantage** : Exemples concrets pour Q Developer.

### Action 8 : Enrichir Q Context avec Workflow Visuel

**Ajouter dans** : `.q-context/vectora-inbox-development-rules.md`

```markdown
## 📊 WORKFLOW VISUEL TEST E2E

### Workflow Complet (À Suivre)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. DÉTECTION                                                │
│    Prompt contient "test E2E" ou "lai_weekly_vX"           │
│    → Q détecte automatiquement                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. CONSULTATION Q CONTEXT                                   │
│    Q lit : .q-context/vectora-inbox-development-rules.md   │
│    Section : RÈGLES DE TESTS E2E                           │
│    Template : docs/templates/TEMPLATE_TEST_E2E_STANDARD.md │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. PROPOSITION PLAN                                         │
│    Q propose : Test technique OU Test E2E complet          │
│    Q demande : Validation utilisateur                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. EXÉCUTION TECHNIQUE                                      │
│    - Build & deploy                                         │
│    - Ingestion (invoke_ingest_v2.py)                       │
│    - Normalize & score (invoke_normalize_score_v2.py)      │
│    - Newsletter (invoke_newsletter_v2.py)                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. COLLECTE DONNÉES                                         │
│    - Télécharger ingested_items.json                       │
│    - Télécharger normalized_items.json                     │
│    - Télécharger newsletter.md                             │
│    - Extraire logs Lambda                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. ANALYSE DÉTAILLÉE                                        │
│    - Remplir template standard                              │
│    - Analyser item par item (29 items)                     │
│    - Calculer métriques (50+ métriques)                    │
│    - Calculer coûts (Bedrock + AWS)                        │
│    - Comparer avec baseline                                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. RECOMMANDATIONS                                          │
│    - Identifier problèmes                                   │
│    - Prioriser actions (Critique/Haute/Moyenne)            │
│    - Proposer solutions                                     │
│    - Décision GO/NO-GO                                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 8. VALIDATION                                               │
│    - Vérifier complétude rapport (validate_e2e_report.py)  │
│    - Confirmer 100% sections remplies                       │
│    - Sauvegarder dans docs/reports/e2e/                    │
└─────────────────────────────────────────────────────────────┘
```

### Workflow Minimal (À Éviter)

```
Prompt → Exécution technique → Rapport basique
```

**Problème** : Pas d'analyse, pas exploitable
```

**Avantage** : Workflow visuel clair pour Q Developer.

---

## 📋 CHECKLIST COLLABORATION AMÉLIORÉE

### Pour Vous (Admin)

**Avant de prompter Q** :
- [ ] Définir objectif clair du test
- [ ] Identifier baseline de comparaison
- [ ] Décider : test technique OU test E2E complet
- [ ] Utiliser prompt magique OU prompt détaillé
- [ ] Référencer template si test E2E complet

**Prompts recommandés** :
```
✅ "@e2e-complet lai_weekly_v11 baseline:v10"
✅ "Propose-moi un plan pour tester v11 selon standards projet"
✅ "Teste v11 avec template docs/templates/TEMPLATE_TEST_E2E_STANDARD.md"

❌ "Teste v11"
❌ "Fais un test E2E de v11"
```

### Pour Q Developer

**Avant d'exécuter** :
- [ ] Détecter si demande test E2E
- [ ] Consulter Q Context
- [ ] Identifier template standard
- [ ] Proposer plan complet
- [ ] Demander validation utilisateur
- [ ] Attendre confirmation

**Après exécution** :
- [ ] Télécharger fichiers S3
- [ ] Analyser résultats
- [ ] Remplir template
- [ ] Comparer baseline
- [ ] Calculer coûts
- [ ] Valider complétude rapport

---

## 🎯 RÉSUMÉ : 3 CHANGEMENTS CLÉS

### 1. Prompts Magiques

**Vous** : Copiez-collez `@e2e-complet lai_weekly_v11 baseline:v10`  
**Q** : Sait exactement quoi faire

### 2. Script Automatisé

**Vous** : `python scripts/invoke/invoke_e2e_complete.py --client-id v11 --baseline v10`  
**Résultat** : Rapport complet garanti

### 3. Détection Automatique

**Q** : Détecte "test E2E" → Propose plan → Demande validation  
**Résultat** : Pas d'étape oubliée

---

**Guide créé le** : 2026-02-02  
**Objectif** : Actions concrètes pour améliorer collaboration  
**Prochaine étape** : Implémenter Action 1, 2, 3 cette semaine
