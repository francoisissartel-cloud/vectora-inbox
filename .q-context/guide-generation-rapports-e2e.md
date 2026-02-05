# Guide: Génération de Rapports E2E Tests

**Objectif**: Générer un rapport E2E complet avec métriques opérationnelles pour piloter le workflow Vectora Inbox.

## 📋 Format de Référence

**Fichier golden standard**: `test-e2e-gold-standard.md`

Ce fichier est le **modèle exact** à reproduire pour tout nouveau test E2E.

## 🎯 Quand Générer un Rapport E2E

- Après chaque run de test complet (ingest → normalize-score → newsletter)
- Après modification des prompts de normalisation ou domain scoring
- Après changement de version des Lambdas
- Pour valider une nouvelle version client (ex: lai_weekly_v24, v25, etc.)

## 📝 Structure du Rapport (À Reproduire Exactement)

### 1. En-tête
```markdown
# Rapport Détaillé E2E - {client_id} {ENV}

**Date**: YYYY-MM-DD
**Client**: {client_id}
**Environnement**: {env}
```

### 2. Métriques de Performance ⚡
- Temps d'exécution par phase (ingest, normalize-score, newsletter)
- Throughput (items/seconde)
- Temps moyen par item

### 3. Métriques Bedrock 🤖
- Nombre d'appels API (total, normalization, scoring)
- Consommation tokens (input, output)
- Coûts unitaires (par item, par appel, par item pertinent)

### 4. Volumétrie Détaillée 📊
- Pipeline complet: ingestion → normalisation → scoring → filtrage
- Taux de conversion à chaque étape

### 5. Projections Coûts 💰
- Par fréquence d'exécution (hebdo, quotidien, 2x/jour)
- Par volume d'items (50, 100, 500)

### 6. KPIs Pilotage 🎯
- Performance (temps E2E, throughput, disponibilité)
- Qualité (taux normalisation, taux pertinence, score moyen)
- Coûts (coût/item, coût/run, coût mensuel)
- Recommandations

### 7. Statistiques Globales 📊
- Total items, items pertinents, items non-pertinents
- Score moyen, min, max

### 8. Items Pertinents (Détail) ✅
Pour chaque item pertinent:
```markdown
### Item X/Y

**Titre**: {title}
**Source**: {source}
**Date**: {date}
**URL**: {url}

#### 📝 Normalisation (1er appel Bedrock)
**Summary**: {summary}
**Entités détectées**:
- Companies: {list}
- Technologies: {list}
- Molecules: {list}
- Trademarks: {list}
- Indications: {list}
- Dosing intervals: {list}
**Event type**: {type}

#### 🎯 Domain Scoring (2ème appel Bedrock)
**Score**: {score}/100
**Confidence**: {confidence}
**Is relevant**: {true/false}
**Signaux détectés**:
- Strong: {list}
- Medium: {list}
- Weak: {list}
- Exclusions: {list}
**Score breakdown**: {détail calcul}
**Reasoning**: {explication}
```

### 9. Items Non-Pertinents (Résumé) ❌
Pour chaque item non-pertinent:
```markdown
### Item X/Y

**Titre**: {title}
**Source**: {source}
**Date**: {date}
**Entités détectées**: {résumé}
**Raison du rejet**: {reasoning}
```

### 10. Analyse par Catégorie 🔍
- Par type d'événement
- Par signal fort détecté

## 🛠️ Comment Générer le Rapport

### Étape 1: Extraire les Données

**Source des données**:
- Fichier curated: `tests/data_snapshots/{client_id}_curated.json`
- Logs CloudWatch (optionnel pour métriques temps réel)

**Script de référence**: `.tmp/generate_detailed_report.py`

### Étape 2: Calculer les Métriques

**Métriques estimées** (si logs CloudWatch indisponibles):
```python
metrics = {
    'ingest_duration_ms': 2500,  # ~2.5s pour 32 items
    'normalize_duration_ms': 95000,  # ~95s pour 64 appels Bedrock
    'newsletter_duration_ms': 1500,  # ~1.5s
    'items_ingested': len(items),
    'items_normalized': len([i for i in items if 'normalized_content' in i]),
    'items_relevant': len([i for i in items if i.get('domain_scoring', {}).get('is_relevant')]),
    'bedrock_calls': items_normalized * 2,  # 2 appels par item
    'input_tokens': bedrock_calls * 3000,  # ~3K tokens/appel
    'output_tokens': bedrock_calls * 500   # ~500 tokens/appel
}
```

**Pricing Bedrock**:
- Input: $0.003 / 1K tokens
- Output: $0.015 / 1K tokens

### Étape 3: Générer le Markdown

**Template**: Utiliser `test-e2e-gold-standard.md` comme référence exacte

**Sections obligatoires**:
1. ⚡ Métriques de Performance
2. 🤖 Métriques Bedrock
3. 📊 Volumétrie Détaillée
4. 💰 Projections Coûts
5. 🎯 KPIs Pilotage
6. 📊 Statistiques Globales
7. ✅ Items Pertinents (détail complet)
8. ❌ Items Non-Pertinents (résumé)
9. 🔍 Analyse par Catégorie

## 📦 Livrables

Pour chaque test E2E, générer:

1. **Rapport complet**: `test_e2e_{client_id}_rapport_detaille_{date}_avec_metriques.md`
2. **Métriques JSON**: `test_e2e_{client_id}_metriques_{date}.json`
3. **Golden test data**: `tests/data_snapshots/golden_test_{client_id}_{date}.json`

## 🎯 Prompt pour Q Developer

```
Génère un rapport E2E complet pour le client {client_id} en utilisant le format 
exact de test-e2e-gold-standard.md. 

Données source: tests/data_snapshots/{client_id}_curated.json

Le rapport doit inclure:
- Métriques de performance (temps, throughput)
- Métriques Bedrock (appels, tokens, coûts)
- Volumétrie détaillée
- Projections coûts
- KPIs pilotage
- Détail de tous les items pertinents
- Résumé des items non-pertinents
- Analyse par catégorie

Utilise les mêmes sections, emojis, et structure que le golden standard.
```

## 📚 Fichiers de Référence

- **Golden standard**: `.q-context/test-e2e-gold-standard.md`
- **Script génération**: `.tmp/generate_detailed_report.py`
- **Script enrichissement**: `.tmp/enrich_report_with_metrics.py`
- **Index rapports**: `docs/reports/e2e/INDEX_RAPPORTS_V23.md`

---

**Note**: Ce format est validé et utilisé pour le pilotage opérationnel. Ne pas modifier la structure sans validation.
