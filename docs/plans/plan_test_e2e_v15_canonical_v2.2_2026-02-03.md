# Plan Test E2E v15 - Validation Canonical v2.2 avec Données Fraîches

**Date**: 2026-02-03  
**Client**: lai_weekly_v15  
**Canonical**: v2.2  
**Objectif**: Valider améliorations plan v2.2 avec données fraîches et analyse item par item  
**Durée estimée**: 2-3 heures

---

## 🎯 OBJECTIFS DU TEST

### Objectif Principal

**Valider que le plan d'amélioration canonical v2.2 a amélioré le moteur Vectora-Inbox**

### Objectifs Spécifiques

1. **Tester avec données fraîches** (ingestion nouvelle)
2. **Analyser item par item** le workflow complet:
   - Pourquoi ingéré?
   - Comment normalisé?
   - Comment scoré?
   - Pourquoi matché/rejeté?
3. **Identifier faux positifs/négatifs** pour affiner canonical
4. **Fournir retour admin détaillé** pour itération suivante
5. **Mesurer amélioration vs v13/v14**

---

## 📋 PRÉ-REQUIS (10 min)

### Checklist Technique

- [ ] Token SSO valide: `aws sso login --profile rag-lai-prod`
- [ ] Canonical v2.2 déployé sur dev (vérifié précédemment ✅)
- [ ] Lambdas opérationnelles
- [ ] Python 3.11+ disponible
- [ ] Espace disque: ~100 MB pour données

### Vérifications Préalables

```bash
# 1. Vérifier token SSO
aws sts get-caller-identity --profile rag-lai-prod

# 2. Vérifier canonical v2.2 sur S3
aws s3 ls s3://vectora-inbox-config-dev/canonical/domains/ --profile rag-lai-prod --region eu-west-3

# 3. Vérifier lambdas
aws lambda list-functions --region eu-west-3 --profile rag-lai-prod | findstr vectora-inbox

# 4. Créer dossier temporaire
mkdir .tmp\e2e_v15
```

---

## 🔄 WORKFLOW COMPLET (2-3h)

### PHASE 1: Préparation Client v15 (15 min)

#### Étape 1.1: Créer Config Client

```bash
# Copier base v14
cp client-config-examples/production/lai_weekly_v14.yaml \
   client-config-examples/production/lai_weekly_v15.yaml
```

**Modifications requises**:
```yaml
client_profile:
  name: "LAI Intelligence Weekly v15 (Test E2E Canonical v2.2 - Données Fraîches)"
  client_id: "lai_weekly_v15"

metadata:
  template_version: "15.0.0"
  created_date: "2026-02-03"
  canonical_version: "2.2"
  created_by: "Test E2E - Validation Canonical v2.2 avec données fraîches"
  
  creation_notes: |
    Test E2E v15 avec données fraîches pour valider:
    - Amélioration ingestion (max_content_length 2000)
    - Détection dosing_intervals
    - Exclusions corporate_move/manufacturing/financial
    - Hybrid_company boost conditionnel
    - CRITICAL RULES anti-hallucination
```

#### Étape 1.2: Upload Config

```bash
# Upload vers S3 dev
aws s3 cp client-config-examples/production/lai_weekly_v15.yaml \
  s3://vectora-inbox-config-dev/clients/lai_weekly_v15.yaml \
  --profile rag-lai-prod --region eu-west-3

# Vérifier
aws s3 ls s3://vectora-inbox-config-dev/clients/ --profile rag-lai-prod --region eu-west-3 | findstr lai_weekly_v15
```

**Validation**: ✅ Fichier présent sur S3

---

### PHASE 2: Ingestion (30 min)

#### Étape 2.1: Lancer Ingestion

```bash
# Créer payload
echo {"client_id": "lai_weekly_v15"} > .tmp/e2e_v15/payload.json

# Invoquer lambda ingest
aws lambda invoke \
  --function-name vectora-inbox-ingest-v2-dev \
  --payload file://.tmp/e2e_v15/payload.json \
  --region eu-west-3 \
  --profile rag-lai-prod \
  .tmp/e2e_v15/ingest_response.json

# Lire réponse
type .tmp\e2e_v15\ingest_response.json
```

**Validation**:
- StatusCode: 200 ✅
- Items ingérés: > 20 ✅

#### Étape 2.2: Télécharger Items Ingérés

```bash
# Trouver le chemin exact (date du jour)
aws s3 ls s3://vectora-inbox-data-dev/ingested/lai_weekly_v15/ \
  --recursive --profile rag-lai-prod --region eu-west-3

# Télécharger (adapter date)
aws s3 cp s3://vectora-inbox-data-dev/ingested/lai_weekly_v15/2026/02/03/items.json \
  .tmp/e2e_v15/items_ingested.json \
  --profile rag-lai-prod --region eu-west-3
```

#### Étape 2.3: Analyser Items Ingérés

```bash
# Statistiques globales
python -c "import json; items=json.load(open('.tmp/e2e_v15/items_ingested.json', encoding='utf-8')); print(f'Total items ingérés: {len(items)}'); sources={}; [sources.update({item.get('source_key', 'unknown'): sources.get(item.get('source_key', 'unknown'), 0) + 1}) for item in items]; print('\nRépartition par source:'); [print(f'  {k}: {v}') for k,v in sorted(sources.items(), key=lambda x: -x[1])]"

# Sauvegarder liste items pour analyse
python -c "import json; items=json.load(open('.tmp/e2e_v15/items_ingested.json', encoding='utf-8')); with open('.tmp/e2e_v15/items_list.txt', 'w', encoding='utf-8') as f: [f.write(f'{i+1}. {item.get(\"title\", \"NO TITLE\")[:100]}... ({item.get(\"source_key\", \"unknown\")})\n') for i, item in enumerate(items)]"

# Afficher liste
type .tmp\e2e_v15\items_list.txt
```

**📝 ANALYSE ADMIN - Ingestion**:

Pour chaque source, noter:
- ✅ / ❌ Source pertinente pour LAI?
- ✅ / ❌ Items ingérés de qualité?
- ✅ / ❌ Filtrage ingestion efficace?

**Observations**:
```
Source 1 (press_corporate__medincell): X items
- Qualité: ✅ / ⚠️ / ❌
- Commentaire: [...]

Source 2 (press_sector__fiercebiotech): X items
- Qualité: ✅ / ⚠️ / ❌
- Commentaire: [...]

[etc.]
```

---

### PHASE 3: Normalisation & Scoring (60-90 min)

#### Étape 3.1: Lancer Normalisation

```bash
# Invoquer lambda (ASYNCHRONE - 5-10 min)
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --invocation-type Event \
  --payload file://.tmp/e2e_v15/payload.json \
  --region eu-west-3 \
  --profile rag-lai-prod \
  .tmp/e2e_v15/normalize_response.json

# Vérifier acceptation
type .tmp\e2e_v15\normalize_response.json
```

**Validation**: StatusCode 202 (asynchrone accepté) ✅

#### Étape 3.2: Attendre et Vérifier

```bash
# Attendre 10 minutes
echo Attente 10 minutes pour normalisation...
timeout /t 600

# Vérifier présence fichier
aws s3 ls s3://vectora-inbox-data-dev/curated/lai_weekly_v15/ \
  --recursive --profile rag-lai-prod --region eu-west-3
```

#### Étape 3.3: Télécharger Items Normalisés

```bash
# Télécharger (adapter date)
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v15/2026/02/03/items.json \
  .tmp/e2e_v15/items_normalized.json \
  --profile rag-lai-prod --region eu-west-3
```

#### Étape 3.4: Analyser Statistiques Globales

```bash
# Statistiques normalization
python -c "import json; items=json.load(open('.tmp/e2e_v15/items_normalized.json', encoding='utf-8')); print(f'Total items: {len(items)}'); relevant=[i for i in items if i.get('domain_scoring', {}).get('is_relevant')]; print(f'Items relevant: {len(relevant)} ({len(relevant)/len(items)*100:.1f}%%)'); scores=[i['domain_scoring']['score'] for i in relevant]; print(f'Score moyen: {sum(scores)/len(scores) if scores else 0:.1f}'); print(f'Score min: {min(scores) if scores else 0}'); print(f'Score max: {max(scores) if scores else 0}')"

# Répartition scores
python -c "import json; items=json.load(open('.tmp/e2e_v15/items_normalized.json', encoding='utf-8')); relevant=[i for i in items if i.get('domain_scoring', {}).get('is_relevant')]; high=sum(1 for i in relevant if i['domain_scoring']['score']>=70); med=sum(1 for i in relevant if 40<=i['domain_scoring']['score']<70); low=sum(1 for i in relevant if i['domain_scoring']['score']<40); print(f'Scores élevés (≥70): {high}'); print(f'Scores moyens (40-69): {med}'); print(f'Scores bas (<40): {low}')"
```

#### Étape 3.5: Analyser Item par Item (CRITIQUE)

**Créer fichier d'analyse détaillée**:

```bash
# Générer rapport item par item
python scripts/analyze/analyze_items_detailed.py \
  --input .tmp/e2e_v15/items_normalized.json \
  --output .tmp/e2e_v15/items_analysis.md
```

**OU manuellement** (si script n'existe pas):

```python
import json

items = json.load(open('.tmp/e2e_v15/items_normalized.json', encoding='utf-8'))

with open('.tmp/e2e_v15/items_analysis.md', 'w', encoding='utf-8') as f:
    f.write("# Analyse Détaillée Items v15\n\n")
    
    # Items relevant
    relevant = [i for i in items if i.get('domain_scoring', {}).get('is_relevant')]
    f.write(f"## Items Relevant ({len(relevant)})\n\n")
    
    for idx, item in enumerate(sorted(relevant, key=lambda x: x['domain_scoring']['score'], reverse=True), 1):
        ds = item.get('domain_scoring', {})
        f.write(f"### Item {idx}/{len(relevant)}: {item.get('title', 'NO TITLE')[:80]}...\n\n")
        f.write(f"- **Source**: {item.get('source_key', 'unknown')}\n")
        f.write(f"- **Event type**: {item.get('normalized_content', {}).get('event_type', 'unknown')}\n")
        f.write(f"- **Score**: {ds.get('score', 0)}/100\n")
        f.write(f"- **Confidence**: {ds.get('confidence', 'unknown')}\n\n")
        
        # Entités
        entities = item.get('normalized_content', {}).get('entities', {})
        f.write(f"**Entités détectées**:\n")
        f.write(f"- Companies: {entities.get('companies', [])}\n")
        f.write(f"- Molecules: {entities.get('molecules', [])}\n")
        f.write(f"- Technologies: {entities.get('technologies', [])}\n")
        f.write(f"- Trademarks: {entities.get('trademarks', [])}\n")
        f.write(f"- Dosing intervals: {item.get('normalized_content', {}).get('dosing_intervals_detected', [])}\n\n")
        
        # Signaux
        signals = ds.get('signals_detected', {})
        f.write(f"**Signaux LAI**:\n")
        f.write(f"- Strong: {signals.get('strong', [])}\n")
        f.write(f"- Medium: {signals.get('medium', [])}\n")
        f.write(f"- Weak: {signals.get('weak', [])}\n\n")
        
        # Reasoning
        f.write(f"**Reasoning**: {ds.get('reasoning', 'N/A')}\n\n")
        
        # Template pour retour admin
        f.write(f"**📝 RETOUR ADMIN**:\n")
        f.write(f"- Devrait matcher? ✅ OUI / ❌ NON\n")
        f.write(f"- Score cohérent? ✅ OUI / ❌ NON\n")
        f.write(f"- Signaux corrects? ✅ OUI / ❌ NON\n")
        f.write(f"- Commentaire: [...]\n\n")
        f.write("---\n\n")
    
    # Items non relevant
    non_relevant = [i for i in items if not i.get('domain_scoring', {}).get('is_relevant')]
    f.write(f"## Items Non Relevant ({len(non_relevant)})\n\n")
    
    for idx, item in enumerate(non_relevant[:10], 1):  # Top 10 seulement
        ds = item.get('domain_scoring', {})
        f.write(f"### Item {idx}/10: {item.get('title', 'NO TITLE')[:80]}...\n\n")
        f.write(f"- **Source**: {item.get('source_key', 'unknown')}\n")
        f.write(f"- **Event type**: {item.get('normalized_content', {}).get('event_type', 'unknown')}\n")
        f.write(f"- **Score**: {ds.get('score', 0)}\n")
        f.write(f"- **Reasoning**: {ds.get('reasoning', 'N/A')}\n\n")
        
        f.write(f"**📝 RETOUR ADMIN**:\n")
        f.write(f"- Rejet justifié? ✅ OUI / ❌ NON (devrait matcher)\n")
        f.write(f"- Commentaire: [...]\n\n")
        f.write("---\n\n")

print("Analyse générée: .tmp/e2e_v15/items_analysis.md")
```

**Exécuter**:
```bash
python .tmp\e2e_v15\generate_analysis.py
```

#### Étape 3.6: Remplir Retours Admin

**Ouvrir fichier**: `.tmp/e2e_v15/items_analysis.md`

**Pour CHAQUE item relevant**, remplir:
- ✅ / ❌ Devrait matcher?
- ✅ / ❌ Score cohérent?
- ✅ / ❌ Signaux corrects?
- Commentaire détaillé

**Pour items non relevant (échantillon)**, remplir:
- ✅ / ❌ Rejet justifié?
- Commentaire si faux négatif

---

### PHASE 4: Newsletter (15 min)

#### Étape 4.1: Générer Newsletter

```bash
# Invoquer lambda
aws lambda invoke \
  --function-name vectora-inbox-newsletter-v2-dev \
  --payload file://.tmp/e2e_v15/payload.json \
  --region eu-west-3 \
  --profile rag-lai-prod \
  .tmp/e2e_v15/newsletter_response.json

# Télécharger newsletter
aws s3 cp s3://vectora-inbox-newsletters-dev/lai_weekly_v15/2026/02/03/newsletter.md \
  .tmp/e2e_v15/newsletter.md \
  --profile rag-lai-prod --region eu-west-3

# Afficher
type .tmp\e2e_v15\newsletter.md
```

#### Étape 4.2: Évaluer Newsletter

**Checklist**:
- [ ] Items sélectionnés: 10-20
- [ ] Sections remplies: 4/4
- [ ] TLDR présent et pertinent
- [ ] Intro cohérente
- [ ] Items bien répartis par section
- [ ] Pas de doublons
- [ ] Qualité rédactionnelle

**📝 RETOUR ADMIN - Newsletter**:
```
Qualité globale: ✅ Excellente / ⚠️ Acceptable / ❌ Insuffisante

Points forts:
- [...]

Points d'amélioration:
- [...]
```

---

### PHASE 5: Comparaison v13/v14/v15 (30 min)

#### Étape 5.1: Compiler Métriques

| Métrique | V13 | V14 | V15 | Évolution |
|----------|-----|-----|-----|-----------|
| **Items ingérés** | 29 | 29 | ? | ? |
| **Items relevant** | 14 (48%) | 12 (41%) | ? | ? |
| **Score moyen** | 38.3 | 80.0 | ? | ? |
| **Faux positifs** | 5 (36%) | 0 (0%) | ? | ? |
| **Faux négatifs** | 1 (7%) | 1 (6%) | ? | ? |
| **Companies détectées** | Oui | Non ❌ | ? | ? |
| **Dosing intervals détectés** | Non | Oui ✅ | ? | ? |

#### Étape 5.2: Identifier Améliorations/Régressions

**Améliorations v15 vs v14**:
1. [...]
2. [...]

**Régressions v15 vs v14**:
1. [...]
2. [...]

**Problèmes persistants**:
1. [...]
2. [...]

---

## 📊 RAPPORT FINAL (30 min)

### Structure Rapport

**Fichier**: `docs/reports/e2e/test_e2e_v15_rapport_complet_2026-02-03.md`

```markdown
# Rapport Test E2E v15 - Validation Canonical v2.2

**Date**: 2026-02-03
**Client**: lai_weekly_v15
**Canonical**: v2.2
**Type données**: Fraîches (ingestion nouvelle)

## 📊 Résultats Globaux

| Métrique | Valeur | Cible | Statut |
|----------|--------|-------|--------|
| Items ingérés | X | >20 | ✅/❌ |
| Items relevant | X (Y%) | >50% | ✅/❌ |
| Score moyen | X | 30-70 | ✅/❌ |
| Faux positifs | X | 0 | ✅/❌ |
| Faux négatifs | X | 0 | ✅/❌ |

## 🎯 Validation Objectifs Plan v2.2

### Objectif 1: Exclusion Corporate Move Sans Tech
**Statut**: ✅ / ⚠️ / ❌
**Preuve**: [...]

### Objectif 2: Exclusion Manufacturing Sans Tech
**Statut**: ✅ / ⚠️ / ❌
**Preuve**: [...]

### Objectif 3: Détection Dosing Intervals
**Statut**: ✅ / ⚠️ / ❌
**Preuve**: [...]

### Objectif 4: Exclusion Financial Results
**Statut**: ✅ / ⚠️ / ❌
**Preuve**: [...]

### Objectif 5: Anti-Hallucination
**Statut**: ✅ / ⚠️ / ❌
**Preuve**: [...]

### Objectif 6: Hybrid Company Boost Conditionnel
**Statut**: ✅ / ⚠️ / ❌
**Preuve**: [...]

## 📝 Retours Admin Détaillés

[Copier depuis items_analysis.md]

## 🔧 Recommandations Amélioration

### Priorité 1 (Critique)
1. [...]

### Priorité 2 (Important)
1. [...]

### Priorité 3 (Nice to Have)
1. [...]

## 🎯 Verdict Final

**Statut**: ✅ SUCCÈS / ⚠️ SUCCÈS PARTIEL / ❌ ÉCHEC

**Justification**: [...]

**Prochaines étapes**: [...]
```

---

## ✅ CHECKLIST FINALE

### Validation Technique

- [ ] Toutes les phases exécutées sans erreur
- [ ] Tous les fichiers téléchargés depuis S3
- [ ] Analyses générées et complètes
- [ ] Métriques calculées
- [ ] Comparaison v13/v14/v15 faite

### Validation Qualité

- [ ] Tous les items relevant analysés
- [ ] Échantillon items non relevant analysé
- [ ] Faux positifs identifiés
- [ ] Faux négatifs identifiés
- [ ] Retours admin remplis pour chaque item

### Livrables

- [ ] Rapport complet généré
- [ ] Fichier items_analysis.md complété
- [ ] Recommandations formulées
- [ ] Verdict final documenté

---

## 🎯 CRITÈRES DE SUCCÈS

### Succès Complet ✅

- Items relevant: ≥50%
- Faux positifs: 0
- Faux négatifs: ≤1
- Companies détectées: >0
- Dosing intervals détectés: >0
- Tous les objectifs plan v2.2 validés

### Succès Partiel ⚠️

- Items relevant: 40-49%
- Faux positifs: 1-2
- Faux négatifs: 2-3
- 4-5 objectifs plan v2.2 validés

### Échec ❌

- Items relevant: <40%
- Faux positifs: >2
- Faux négatifs: >3
- <4 objectifs plan v2.2 validés

---

## 📝 NOTES IMPORTANTES

1. **Données fraîches**: Ce test utilise une nouvelle ingestion, pas les données v13/v14
2. **Analyse item par item**: Critique pour identifier patterns et affiner canonical
3. **Retours admin détaillés**: Permettent itération rapide sur canonical
4. **Comparaison versions**: Mesure progrès réel du moteur
5. **Temps requis**: 2-3h pour analyse complète et qualitative

---

**Plan créé**: 2026-02-03  
**Durée estimée**: 2-3 heures  
**Statut**: ⏳ PRÊT POUR EXÉCUTION
