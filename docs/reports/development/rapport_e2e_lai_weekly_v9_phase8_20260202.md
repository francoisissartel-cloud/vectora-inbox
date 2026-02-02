# Rapport E2E Phase 8 - LAI_WEEKLY_V9 - Test Domain Scoring

**Date**: 2026-02-02  
**Client**: lai_weekly_v9  
**Objectif**: Valider architecture 2 appels Bedrock (generic_normalization + lai_domain_scoring)  
**Statut**: 🟡 PARTIEL - Infrastructure prête, domain scoring non exécuté

---

## 📊 RÉSUMÉ EXÉCUTIF

### ✅ Réalisations Phase 8

1. **Script d'invocation ingest-v2 créé** : `scripts/invoke/invoke_ingest_v2.py`
2. **Ingestion lai_weekly_v9 réussie** : 28 items ingérés
3. **Configuration client uploadée** : `lai_weekly_v9.yaml` avec `enable_domain_scoring: true`
4. **Prompts canonical uploadés** :
   - `canonical/prompts/domain_scoring/lai_domain_scoring.yaml`
   - `canonical/domains/lai_domain_definition.yaml`
5. **Code normalizer modifié** :
   - Ajout paramètre `enable_domain_scoring` dans toute la chaîne
   - Logique conditionnelle pour 2ème appel Bedrock
   - Flag `has_domain_scoring` ajouté aux items
6. **Layer v51 déployé** : Contient les modifications du normalizer
7. **Lambda mise à jour** : `vectora-inbox-normalize-score-v2-dev` utilise layer v51

### 🚨 Problème Bloquant

**Domain scoring NON exécuté** malgré :
- `enable_domain_scoring: true` dans configuration
- Flag correctement lu et logué : "Domain scoring activé: True"
- Prompts et domains uploadés sur S3
- Code modifié pour appeler le domain scorer

**Cause identifiée** : Erreur de chargement des prompts canonical
```
[ERROR] Impossible de charger les prompts canonical: argument of type 'NoneType' is not iterable
```

---

## 📈 MÉTRIQUES OBTENUES

### Ingestion
- **Items ingérés** : 28
- **Statut** : ✅ Succès
- **Temps** : ~20s

### Normalisation (avec layer v51)
- **Items input** : 28
- **Items normalized** : 28 (100%)
- **Items matched** : 0 (0%)
- **Items scored** : 28 (100%)
- **Temps d'exécution** : 70.3s
- **Items avec domain_scoring** : 0 ❌
- **Items avec has_domain_scoring=False** : 28 ✅

### Comparaison Temps d'Exécution

| Run | Temps | Delta | Commentaire |
|-----|-------|-------|-------------|
| v9 sans config | 92.3s | baseline | 1 appel Bedrock |
| v9 avec config (erreur prompts) | 237.9s | +158% | Tentative 2 appels |
| v9 avec config (erreur prompts) | 216.4s | +134% | Tentative 2 appels |
| v9 avec layer v51 | 70.3s | -24% | 1 appel seulement |

**Observation** : Le temps de 70s confirme qu'un seul appel Bedrock est exécuté.

---

## 🔍 ANALYSE DÉTAILLÉE

### Structure Items.json (v51)

```json
{
  "item_id": "...",
  "normalized_at": "...",
  "effective_date": "2025-12-10",
  "date_metadata": {
    "source": "bedrock",
    "bedrock_date": "2025-12-10",
    "bedrock_confidence": 1.0,
    "published_at": "2026-02-02"
  },
  "normalized_content": {
    "summary": "...",
    "event_classification": {...},
    "entities": {...}
  },
  "matching_results": {
    "matched_domains": [],
    "domain_relevance": {},
    "bedrock_matching_used": true
  },
  "scoring_results": {...},
  "has_domain_scoring": false  // ✅ Flag présent mais False
}
```

**Observations** :
- ✅ Flag `has_domain_scoring` présent (code exécuté)
- ❌ Valeur `false` sur tous les items (domain scoring non appelé)
- ❌ Section `domain_scoring` absente

### Logs CloudWatch - Indices Clés

```
[INFO] Domain scoring activé: True
[ERROR] Impossible de charger les prompts canonical: argument of type 'NoneType' is not iterable
[INFO] Watch domains configurés: 1
[WARNING] Prompt matching non trouvé, utilisation du prompt par défaut
```

**Diagnostic** :
1. Le flag `enable_domain_scoring` est bien lu et à `True`
2. Une erreur se produit lors du chargement des prompts canonical
3. Le code continue sans domain scoring (gestion d'erreur silencieuse)

---

## 🐛 CAUSE RACINE

### Problème : Chargement Prompts Canonical

Le code dans `normalizer.py` ligne ~250 :

```python
if enable_domain_scoring:
    logger.info("Domain scoring activé - exécution du 2ème appel Bedrock")
    try:
        from .bedrock_domain_scorer import score_item_for_domain
        
        # Charger domain definition
        domain_definition = canonical_scopes.get('domains', {}).get('lai_domain_definition', {})
        if domain_definition:
            domain_scoring_prompt = canonical_prompts.get('domain_scoring', {}).get('lai_domain_scoring', {})
            if domain_scoring_prompt:
                # Appel domain scorer
            else:
                logger.warning("Prompt domain_scoring/lai_domain_scoring non trouvé")
        else:
            logger.warning("Domain definition lai_domain_definition non trouvée")
    except Exception as e:
        logger.error(f"Erreur domain scoring: {str(e)}")
```

**Hypothèses** :
1. `canonical_scopes.get('domains')` retourne `None` ou `{}`
2. `canonical_prompts.get('domain_scoring')` retourne `None` ou `{}`
3. Le chargement des prompts/domains échoue en amont dans `config_loader.py`

---

## 🔧 ACTIONS CORRECTIVES NÉCESSAIRES

### Priorité CRITIQUE

1. **Débugger config_loader.py**
   - Ajouter logs détaillés dans `load_canonical_prompts()`
   - Vérifier structure retournée pour `domain_scoring`
   - Vérifier structure retournée pour `domains`

2. **Vérifier structure S3**
   ```bash
   aws s3 ls s3://vectora-inbox-config-dev/canonical/prompts/domain_scoring/ --recursive
   aws s3 ls s3://vectora-inbox-config-dev/canonical/domains/ --recursive
   ```

3. **Tester chargement local**
   ```python
   from vectora_core.shared import config_loader
   prompts = config_loader.load_canonical_prompts('vectora-inbox-config-dev')
   print(prompts.get('domain_scoring'))
   ```

4. **Ajouter logs dans normalizer**
   ```python
   logger.info(f"canonical_scopes keys: {list(canonical_scopes.keys())}")
   logger.info(f"canonical_prompts keys: {list(canonical_prompts.keys())}")
   logger.info(f"domains in scopes: {list(canonical_scopes.get('domains', {}).keys())}")
   logger.info(f"domain_scoring in prompts: {list(canonical_prompts.get('domain_scoring', {}).keys())}")
   ```

5. **Rebuild layer v52 avec logs**
6. **Redéployer et tester**

---

## 📋 CHECKLIST VALIDATION PHASE 8

### Infrastructure ✅
- [x] Script invoke_ingest_v2.py créé
- [x] Configuration lai_weekly_v9.yaml uploadée
- [x] Prompts domain_scoring uploadés
- [x] Domains lai_domain_definition uploadé
- [x] Code normalizer modifié
- [x] Layer v51 déployé
- [x] Lambda mise à jour

### Fonctionnel ❌
- [x] Flag enable_domain_scoring lu correctement
- [x] Flag has_domain_scoring ajouté aux items
- [ ] Prompts canonical chargés correctement
- [ ] Domain definition chargée correctement
- [ ] Domain scorer appelé
- [ ] Section domain_scoring présente dans items
- [ ] 2 appels Bedrock exécutés
- [ ] Temps d'exécution +40-70% vs baseline

### Tests E2E ⏳
- [x] Ingestion lai_weekly_v9
- [x] Normalisation lai_weekly_v9
- [ ] Domain scoring validé
- [ ] Rapport E2E complet
- [ ] Comparaison v8 vs v9
- [ ] Décision GO/NO-GO stage

---

## 🎯 PROCHAINES ÉTAPES

### Phase 8bis : Debug & Fix (Urgent)

1. **Investiguer config_loader** (30 min)
   - Lire code `load_canonical_prompts()`
   - Identifier pourquoi `domain_scoring` n'est pas chargé
   - Vérifier structure attendue vs réelle

2. **Corriger chargement** (30 min)
   - Modifier `config_loader.py` si nécessaire
   - Ou ajuster structure S3 si nécessaire
   - Rebuild layer v52

3. **Tester à nouveau** (15 min)
   - Redéployer layer v52
   - Relancer normalisation lai_weekly_v9
   - Vérifier présence domain_scoring dans items

4. **Valider E2E** (30 min)
   - Télécharger items.json
   - Analyser structure domain_scoring
   - Comparer v8 vs v9
   - Créer rapport final

### Phase 9 : Promotion Stage (si Phase 8bis OK)

1. Promouvoir version 1.4.0 vers stage
2. Tester en stage avec lai_weekly_v7
3. Valider métriques stage
4. Comparer dev vs stage

---

## 📎 FICHIERS GÉNÉRÉS

**Scripts créés** :
- `scripts/invoke/invoke_ingest_v2.py` ✅
- `.tmp/analyse_v8_vs_v9.py` ✅

**Configurations uploadées** :
- `s3://vectora-inbox-data-dev/client-configs/lai_weekly_v9.yaml` ✅
- `s3://vectora-inbox-data-dev/canonical/prompts/domain_scoring/lai_domain_scoring.yaml` ✅
- `s3://vectora-inbox-data-dev/canonical/domains/lai_domain_definition.yaml` ✅

**Résultats téléchargés** :
- `.tmp/items_lai_weekly_v8_phase8.json` (baseline)
- `.tmp/items_lai_weekly_v9_phase8.json` (sans config)
- `.tmp/items_lai_weekly_v9_phase8_v2.json` (avec config, erreur prompts)
- `.tmp/items_lai_weekly_v9_phase8_final.json` (avec config, erreur prompts)
- `.tmp/items_lai_weekly_v9_phase8_v51.json` (layer v51, domain scoring non exécuté)

**Layers déployés** :
- Layer v51 : `arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev:51`

---

## 💡 LEÇONS APPRISES

1. **Importance des logs détaillés** : L'erreur "argument of type 'NoneType' is not iterable" était silencieuse
2. **Validation structure S3** : Uploader les fichiers ne suffit pas, il faut vérifier le chargement
3. **Tests unitaires manquants** : `config_loader.load_canonical_prompts()` devrait avoir des tests
4. **Gestion d'erreur trop permissive** : Le `try/except` cache le problème au lieu de le remonter
5. **Métriques de temps précieuses** : Le temps d'exécution est un excellent indicateur (70s vs 216s)

---

## 🎓 RECOMMANDATIONS FUTURES

1. **Ajouter tests unitaires** pour `config_loader`
2. **Améliorer logs** dans toute la chaîne de chargement
3. **Validation stricte** des configurations au démarrage
4. **Fail-fast** : Arrêter l'exécution si prompts manquants (plutôt que continuer silencieusement)
5. **Métriques CloudWatch** : Tracker le nombre d'appels Bedrock par exécution

---

**Rapport créé le** : 2026-02-02 15:50  
**Analysé par** : Amazon Q Developer  
**Statut** : 🟡 PARTIEL - Infrastructure OK, Debug nécessaire  
**Version** : VECTORA_CORE 1.4.0 (layer v51)  
**Prochaine action** : Investiguer config_loader.py

