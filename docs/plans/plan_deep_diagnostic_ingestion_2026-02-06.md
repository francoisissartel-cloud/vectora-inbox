# Plan Deep Diagnostic - Phase d'Ingestion Vectora Inbox

**Date** : 2026-02-06  
**Contexte** : Échec amélioration filtrage v24 malgré enrichissement `exclusion_scopes.yaml`  
**Objectif** : Comprendre EXACTEMENT comment fonctionne le filtrage d'ingestion et comment le piloter via canonical

---

## 🎯 OBJECTIFS DU DIAGNOSTIC

1. **Comprendre le workflow d'ingestion** : Quels fichiers, quel code, quelle séquence
2. **Identifier les points de filtrage** : Où et comment les items sont filtrés
3. **Mapper code ↔ canonical** : Quels fichiers canonical sont utilisés et comment
4. **Diagnostiquer le bug actuel** : Pourquoi les keywords ajoutés ne filtrent pas
5. **Proposer solution** : Comment piloter le filtrage via canonical SANS modifier le moteur

---

## 📋 QUESTIONS À RÉPONDRE

### Q1 : Workflow d'ingestion complet

- [ ] Quels fichiers code sont exécutés dans quel ordre ?
- [ ] Quelles fonctions sont appelées ?
- [ ] Où se fait le filtrage exactement ?
- [ ] Combien de passes de filtrage ?

### Q2 : Fichiers canonical utilisés

- [ ] Quels fichiers canonical sont chargés depuis S3 ?
- [ ] À quel moment sont-ils chargés (démarrage Lambda vs chaque invocation) ?
- [ ] Comment sont-ils parsés (YAML, JSON) ?
- [ ] Quels champs sont utilisés vs ignorés ?

### Q3 : Logique de filtrage actuelle

- [ ] Comment `_contains_exclusion_keywords()` fonctionne EXACTEMENT ?
- [ ] Quels scopes sont combinés dans `_get_exclusion_terms()` ?
- [ ] Le matching est-il case-sensitive ?
- [ ] Y a-t-il des transformations de texte (strip, normalize) ?
- [ ] Que se passe-t-il si match trouvé (continue, return, flag) ?

### Q4 : Bug actuel

- [ ] Les keywords sont-ils chargés correctement depuis S3 ?
- [ ] Le parsing YAML préserve-t-il les guillemets ?
- [ ] Le matching trouve-t-il les correspondances ?
- [ ] Si match trouvé, l'item est-il vraiment exclu ?
- [ ] Y a-t-il un cache qui empêche le rechargement ?

### Q5 : Architecture cible

- [ ] Comment rendre le moteur 100% générique ?
- [ ] Quels paramètres doivent être dans canonical ?
- [ ] Comment éviter le hardcoding dans le code ?
- [ ] Comment tester le filtrage sans déployer ?

---

## 🔬 MÉTHODOLOGIE DE DIAGNOSTIC

### Phase 1 : Traçage du workflow (1h)

**Objectif** : Comprendre le flux d'exécution complet

#### Étape 1.1 : Lire le code source

- [ ] `src_v2/lambdas/ingest/handler.py` : Point d'entrée
- [ ] `src_v2/vectora_core/ingest/__init__.py` : Orchestration
- [ ] `src_v2/vectora_core/ingest/source_fetcher.py` : Récupération sources
- [ ] `src_v2/vectora_core/ingest/content_parser.py` : Parsing RSS/HTML
- [ ] `src_v2/vectora_core/ingest/ingestion_profiles.py` : **FILTRAGE** ← CRITIQUE
- [ ] `src_v2/vectora_core/shared/utils.py` : Déduplication, validation

#### Étape 1.2 : Créer diagramme de flux

```
handler.lambda_handler()
  ↓
run_ingest_for_client()
  ↓
config_loader.load_client_config()  # Charge client config
config_loader.load_source_catalog()  # Charge sources
initialize_exclusion_scopes()  # ← Charge exclusion_scopes.yaml
  ↓
for each source:
  source_fetcher.fetch_source_content()  # HTTP GET
  content_parser.parse_source_content()  # Parse RSS → items
  ingestion_profiles.apply_ingestion_profile()  # ← FILTRAGE ICI
    ↓
    _apply_corporate_profile()
      ↓
      if is_lai_pure_player:
        for each item:
          if _contains_exclusion_keywords(text):  # ← FILTRE
            continue  # EXCLU
          filtered_items.append(item)  # CONSERVÉ
  ↓
utils.apply_temporal_filter()  # Filtre date
utils.deduplicate_items()  # Déduplication
utils.validate_item()  # Validation
  ↓
s3_io.write_json_to_s3()  # Écriture S3
```

#### Étape 1.3 : Identifier les points de décision

- [ ] Ligne X : Chargement `exclusion_scopes.yaml`
- [ ] Ligne Y : Appel `_contains_exclusion_keywords()`
- [ ] Ligne Z : Décision `continue` vs `append`

---

### Phase 2 : Analyse du filtrage actuel (1h)

**Objectif** : Comprendre pourquoi le filtrage ne fonctionne pas

#### Étape 2.1 : Activer logs DEBUG

```python
# Modifier temporairement ingestion_profiles.py
logger.setLevel(logging.DEBUG)

# Ajouter logs détaillés dans _contains_exclusion_keywords()
def _contains_exclusion_keywords(text: str) -> bool:
    text_lower = text.lower()
    exclusion_terms = _get_exclusion_terms()
    
    logger.debug(f"Checking exclusion for text: {text_lower[:100]}")
    logger.debug(f"Exclusion terms loaded: {len(exclusion_terms)}")
    
    for keyword in exclusion_terms:
        if keyword.lower() in text_lower:
            logger.debug(f"MATCH FOUND: '{keyword}' in text")
            return True
    
    logger.debug("No exclusion match found")
    return False
```

#### Étape 2.2 : Tester avec logs

```bash
# Déployer avec logs DEBUG
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev

# Invoquer et récupérer logs
python scripts/invoke/invoke_ingest_v2.py --client-id lai_weekly_v24 --env dev

# Analyser logs CloudWatch
aws logs tail /aws/lambda/vectora-inbox-ingest-v2-dev --since 5m --profile rag-lai-prod --region eu-west-3 | findstr /C:"BIO" /C:"exclusion" /C:"MATCH"
```

#### Étape 2.3 : Analyser les résultats

- [ ] Les keywords sont-ils chargés ? (log "Exclusion scopes chargés: X catégories")
- [ ] Combien de terms dans `exclusion_terms` ? (log "Exclusion terms loaded: X")
- [ ] Le matching trouve-t-il "BIO International Convention" ? (log "MATCH FOUND")
- [ ] Si match, l'item est-il exclu ? (log "Item corporate exclu (bruit)")

---

### Phase 3 : Analyse des fichiers canonical (30min)

**Objectif** : Comprendre quels fichiers sont utilisés et comment

#### Étape 3.1 : Lister les fichiers canonical chargés

```bash
# Chercher tous les appels à s3_io.read_yaml_from_s3() dans le code
grep -r "read_yaml_from_s3" src_v2/vectora_core/ingest/
grep -r "load_.*_config" src_v2/vectora_core/shared/config_loader.py
```

**Fichiers identifiés** :
- [ ] `client_configs/{client_id}.yaml` : Config client
- [ ] `canonical/sources/source_catalog.yaml` : Catalogue sources
- [ ] `canonical/scopes/exclusion_scopes.yaml` : Keywords exclusion
- [ ] `canonical/ingestion/ingestion_profiles.yaml` : Profils ingestion (utilisé ?)

#### Étape 3.2 : Analyser l'utilisation de chaque fichier

**`exclusion_scopes.yaml`** :
- Chargé par : `initialize_exclusion_scopes()` (ligne 14-23)
- Utilisé par : `_get_exclusion_terms()` (ligne 25-35)
- Scopes lus : `hr_content`, `financial_generic`, `hr_recruitment_terms`, `financial_reporting_terms`
- Scopes IGNORÉS : `esg_generic`, `event_generic`, `corporate_noise_terms`, `anti_lai_routes`

**`ingestion_profiles.yaml`** :
- Chargé par : ❓ (à vérifier)
- Utilisé par : ❓ (à vérifier)
- Impact : ❓ (à vérifier)

#### Étape 3.3 : Identifier les gaps

- [ ] Quels scopes sont définis mais non utilisés ?
- [ ] Quels paramètres sont définis mais non utilisés ?
- [ ] Y a-t-il des fichiers canonical inutiles ?

---

### Phase 4 : Test de validation (30min)

**Objectif** : Valider la compréhension avec un test contrôlé

#### Étape 4.1 : Test minimal

```yaml
# Créer exclusion_scopes_test.yaml avec 1 seul keyword
hr_content:
  - test_keyword_unique_12345
```

```python
# Créer item de test avec ce keyword
test_item = {
    'title': 'Test avec test_keyword_unique_12345',
    'content': 'Contenu de test'
}
```

**Attendu** : Item EXCLU  
**Si item CONSERVÉ** : Le filtrage ne fonctionne PAS

#### Étape 4.2 : Test avec keyword réel

```yaml
hr_content:
  - BIO International Convention
```

**Attendu** : Item "BIO International Convention 2025" EXCLU  
**Si item CONSERVÉ** : Problème de matching ou de logique

---

### Phase 5 : Diagnostic du bug (1h)

**Objectif** : Identifier EXACTEMENT pourquoi le filtrage échoue

#### Étape 5.1 : Hypothèses à tester

**Hypothèse 1** : Cache Lambda
- [ ] Le cache `_exclusion_scopes_cache` n'est pas rechargé
- [ ] Test : Redéployer layers et re-tester
- [ ] Résultat : ❌ Toujours 24-25 items

**Hypothèse 2** : Parsing YAML avec guillemets
- [ ] Les guillemets sont inclus dans les strings
- [ ] Test : Retirer guillemets et re-tester
- [ ] Résultat : ❌ Toujours 24-25 items

**Hypothèse 3** : Matching ne fonctionne pas
- [ ] Le code `keyword.lower() in text.lower()` échoue
- [ ] Test : Logs DEBUG pour voir les matches
- [ ] Résultat : ✅ Match trouvé MAIS item pas exclu

**Hypothèse 4** : Logique d'exclusion inversée
- [ ] `if _contains_exclusion_keywords()` devrait être `if NOT`
- [ ] Test : Vérifier la logique ligne 138
- [ ] Résultat : À tester

**Hypothèse 5** : Filtrage se fait APRÈS écriture S3
- [ ] Les items sont écrits AVANT le filtrage
- [ ] Test : Vérifier l'ordre des étapes
- [ ] Résultat : À tester

#### Étape 5.2 : Analyse des logs CloudWatch

```bash
# Récupérer logs détaillés
aws logs get-log-events \
  --log-group-name /aws/lambda/vectora-inbox-ingest-v2-dev \
  --log-stream-name [LATEST] \
  --limit 500 \
  --profile rag-lai-prod \
  --region eu-west-3 > .tmp/lambda_logs_detailed.json

# Chercher patterns
cat .tmp/lambda_logs_detailed.json | grep -i "BIO\|exclusion\|filtered\|conservé"
```

#### Étape 5.3 : Test unitaire local

```python
# Créer test_ingestion_filter.py
from src_v2.vectora_core.ingest import ingestion_profiles

# Simuler chargement scopes
ingestion_profiles._exclusion_scopes_cache = {
    'hr_content': ['BIO International Convention', 'test keyword']
}

# Test
text = "BIO International Convention 2025 Boston"
result = ingestion_profiles._contains_exclusion_keywords(text)
print(f"Match found: {result}")  # Attendu: True

# Si False → Bug dans le code
# Si True → Bug dans la logique d'exclusion
```

---

### Phase 6 : Solution et implémentation (1h)

**Objectif** : Corriger le bug et valider la solution

#### Étape 6.1 : Identifier la solution

**Si bug dans le code** :
- Corriger la logique de filtrage
- Rebuild + redeploy
- Test E2E

**Si bug dans canonical** :
- Ajuster format des keywords
- Upload S3
- Test E2E

**Si architecture inadéquate** :
- Proposer refactoring
- Créer plan d'implémentation
- Valider avec utilisateur

#### Étape 6.2 : Implémenter la solution

- [ ] Modifier fichiers nécessaires
- [ ] Tester localement si possible
- [ ] Déployer sur dev
- [ ] Valider avec lai_weekly_v24
- [ ] Mesurer impact (items filtrés)

#### Étape 6.3 : Documenter la solution

- [ ] Créer rapport diagnostic
- [ ] Documenter le bug trouvé
- [ ] Documenter la solution appliquée
- [ ] Mettre à jour le plan d'amélioration

---

## 📊 LIVRABLES ATTENDUS

### 1. Rapport de diagnostic complet

**Fichier** : `docs/diagnostics/deep_diagnostic_ingestion_phase_2026-02-06.md`

**Contenu** :
- Workflow d'ingestion détaillé (diagramme)
- Mapping code ↔ canonical
- Points de filtrage identifiés
- Bug root cause analysis
- Solution proposée
- Tests de validation

### 2. Diagramme de flux annoté

**Fichier** : `docs/architecture/ingestion_workflow_detailed.md`

**Contenu** :
- Flux complet avec numéros de ligne
- Fichiers canonical chargés à chaque étape
- Points de décision (if/else)
- Variables d'état (cache, flags)

### 3. Guide d'amélioration canonical

**Fichier** : `docs/guides/guide_amelioration_filtrage_ingestion.md`

**Contenu** :
- Comment ajouter keywords d'exclusion
- Quels scopes sont utilisés vs ignorés
- Format des keywords (avec/sans guillemets, regex)
- Comment tester les modifications
- Checklist de validation

### 4. Plan d'amélioration corrigé

**Fichier** : `docs/plans/plan_amelioration_ingestion_v24_2026-02-06.md` (mise à jour)

**Contenu** :
- Diagnostic du bug
- Solution validée
- Impact mesuré
- Prochaines étapes

---

## 🚀 PLAN D'EXÉCUTION

### Jour 1 : Diagnostic (3h)

**Matin (2h)** :
- Phase 1 : Traçage workflow (1h)
- Phase 2 : Analyse filtrage (1h)

**Après-midi (1h)** :
- Phase 3 : Analyse canonical (30min)
- Phase 4 : Test validation (30min)

### Jour 2 : Solution (2h)

**Matin (1h)** :
- Phase 5 : Diagnostic bug (1h)

**Après-midi (1h)** :
- Phase 6 : Solution + validation (1h)

### Jour 3 : Documentation (1h)

- Rédaction rapports
- Mise à jour plans
- Validation finale

**Total** : 6h sur 3 jours

---

## 🎯 CRITÈRES DE SUCCÈS

### Succès du diagnostic

- [ ] Workflow d'ingestion 100% compris et documenté
- [ ] Tous les fichiers canonical mappés
- [ ] Bug root cause identifié
- [ ] Solution proposée et validée

### Succès de l'implémentation

- [ ] Items ingérés v24 : <20 (vs 24 actuellement)
- [ ] Items conférences : 0 (vs 3 actuellement)
- [ ] Items rapports financiers : 0 (vs 3 actuellement)
- [ ] Items corporate générique : 0 (vs 3 actuellement)
- [ ] Items pertinents : ≥7 (pas de faux négatifs)
- [ ] Taux pertinence : >50% (vs 29% actuellement)

### Succès de la documentation

- [ ] Guide utilisable par Q Developer
- [ ] Diagramme clair et précis
- [ ] Plan d'amélioration validé
- [ ] Tests reproductibles

---

## 🔧 OUTILS ET COMMANDES

### Analyse du code

```bash
# Chercher tous les appels de filtrage
grep -n "_contains_exclusion" src_v2/vectora_core/ingest/*.py

# Chercher chargement canonical
grep -n "read_yaml_from_s3" src_v2/vectora_core/**/*.py

# Chercher hardcoded keywords
grep -n "EXCLUSION_KEYWORDS\|LAI_KEYWORDS" src_v2/vectora_core/ingest/*.py
```

### Test local du filtrage

```python
# test_filtrage_local.py
import sys
sys.path.insert(0, 'src_v2')

from vectora_core.ingest import ingestion_profiles

# Simuler scopes
ingestion_profiles._exclusion_scopes_cache = {
    'hr_content': ['BIO International Convention']
}

# Test
text = "BIO International Convention 2025 Boston"
result = ingestion_profiles._contains_exclusion_keywords(text)
print(f"Exclusion match: {result}")
```

### Analyse logs Lambda

```bash
# Logs récents
aws logs tail /aws/lambda/vectora-inbox-ingest-v2-dev --since 10m --profile rag-lai-prod --region eu-west-3

# Filtrer par pattern
aws logs filter-log-events \
  --log-group-name /aws/lambda/vectora-inbox-ingest-v2-dev \
  --filter-pattern "exclusion" \
  --profile rag-lai-prod \
  --region eu-west-3
```

---

## 📝 NOTES ET OBSERVATIONS

### Observations actuelles

1. ✅ Keywords ajoutés dans `hr_content` : "BIO International Convention", "Bio Europe Spring", "TIDES Asia"
2. ✅ Fichier uploadé sur S3 : `s3://vectora-inbox-config-dev/canonical/scopes/exclusion_scopes.yaml`
3. ✅ Layers redéployés : v67/v28
4. ✅ Test matching manuel : `"bio international convention" in text: True`
5. ❌ Items toujours présents : 25 items (vs 24 avant)
6. ❌ Items conférences NON filtrés : "BIO International Convention 2025" toujours là

### Hypothèses en cours

- **Hypothèse A** : Le code ne filtre PAS pour les pure players (FAUX - code ligne 138 filtre)
- **Hypothèse B** : Cache Lambda (TESTÉ - redéployé, toujours pas filtré)
- **Hypothèse C** : Guillemets YAML (TESTÉ - retirés, toujours pas filtré)
- **Hypothèse D** : Logique inversée ou bug dans le code (À TESTER)
- **Hypothèse E** : Filtrage se fait ailleurs ou est bypassé (À TESTER)

---

## 🎯 PROCHAINES ÉTAPES IMMÉDIATES

1. **Activer logs DEBUG** dans `ingestion_profiles.py`
2. **Redéployer** avec logs
3. **Invoquer** lai_weekly_v24
4. **Analyser logs** CloudWatch pour voir EXACTEMENT ce qui se passe
5. **Identifier** le bug root cause
6. **Corriger** et valider

---

**Plan créé** : 2026-02-06  
**Statut** : Prêt pour exécution  
**Durée estimée** : 6h sur 3 jours
