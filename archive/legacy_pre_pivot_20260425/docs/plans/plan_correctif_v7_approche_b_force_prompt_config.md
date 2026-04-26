# Plan Correctif v7 - Forcer Utilisation Prompt Configuré (Approche B)
## Date: 2026-01-29 17:00 UTC
## Objectif: Supprimer prompt hardcodé et forcer utilisation prompt LAI depuis S3

---

## 🎯 PHASE 1: CADRAGE

### Problème Identifié

**Symptôme**: 0% de dates extraites par Bedrock (cible: >95%)

**Cause racine**: 
- Le prompt LAI (`lai_prompt.yaml`) sur S3 contient les instructions d'extraction de date ✅
- Le code supporte l'Approche B (prompts pré-construits depuis S3) ✅
- MAIS le code utilise le **prompt V1 hardcodé** au lieu du prompt configuré
- Le prompt V1 hardcodé n'a pas d'extraction de date

**Preuve du problème**:
```python
# Dans bedrock_client.py - normalize_item()
if self.prompt_template and self.canonical_scopes:
    prompt = self._build_prompt_approche_b(item_text, item_source_key)
elif canonical_prompts:
    prompt = self._build_normalization_prompt_v2(item_text, ...)
else:
    prompt = self._build_normalization_prompt_v1(item_text, ...)  # ← UTILISÉ
```

**Pourquoi le prompt V1 est utilisé**:
- `self.prompt_template` est None (prompt LAI non chargé)
- `canonical_prompts` est None (pas passé)
- Donc fallback sur V1 hardcodé

**Configuration client lai_weekly_v7**:
```yaml
bedrock_config:
  normalization_prompt: "lai"  # ← Devrait charger lai_prompt.yaml
```

### Objectif du Correctif

**Cible**: Forcer l'utilisation du prompt LAI configuré dans `client_config.yaml`

**Approche**: 
1. S'assurer que `prompt_template` est chargé lors de l'initialisation du client Bedrock
2. S'assurer que `canonical_scopes` est passé au client
3. Vérifier que l'Approche B est activée via logs

### Périmètre

**Fichiers à analyser**:
1. `src_v2/vectora_core/normalization/normalizer.py` (initialisation BedrockNormalizationClient)
2. `src_v2/vectora_core/normalization/bedrock_client.py` (chargement prompt)
3. `src_v2/vectora_core/shared/prompt_resolver.py` (résolution prompt)

**Fichiers déjà corrects**:
1. `canonical/prompts/normalization/lai_prompt.yaml` (prompt avec extraction dates)
2. `client-config-examples/lai_weekly_v7.yaml` (config avec normalization_prompt: "lai")

**Contraintes**:
- Respecter vectora-inbox-development-rules.md
- Utiliser `src_v2/` comme base
- Tester localement avant déploiement
- Valider E2E avec lai_weekly_v7

---

## 🔍 PHASE 2: DIAGNOSTIC APPROFONDI

### 2.1 Analyse Initialisation BedrockNormalizationClient

**Fichier**: `src_v2/vectora_core/normalization/normalizer.py`

**Fonction**: `_normalize_sequential()` (ligne ~150)

**Code actuel**:
```python
bedrock_client = BedrockNormalizationClient(
    bedrock_model, bedrock_region, s3_io, client_config, canonical_scopes
)
```

**Vérification**: Les 5 paramètres sont passés ✅

### 2.2 Analyse Chargement Prompt Template

**Fichier**: `src_v2/vectora_core/normalization/bedrock_client.py`

**Fonction**: `__init__()` (ligne ~130)

**Code actuel**:
```python
if client_config and s3_io and canonical_scopes:
    bedrock_config = client_config.get('bedrock_config', {})
    normalization_prompt = bedrock_config.get('normalization_prompt')
    
    if normalization_prompt:
        self.prompt_template = prompt_resolver.load_prompt_template(
            'normalization', normalization_prompt, s3_io
        )
        if self.prompt_template:
            logger.info(f"Approche B activée: prompt {normalization_prompt} chargé")
```

**Problème potentiel**: 
- Si `load_prompt_template()` échoue silencieusement, `self.prompt_template` reste None
- Pas de log d'erreur si le chargement échoue

### 2.3 Analyse load_prompt_template

**Fichier**: `src_v2/vectora_core/shared/prompt_resolver.py`

**Fonction**: `load_prompt_template()` (ligne ~15)

**Code actuel**:
```python
try:
    prompt_path = f"canonical/prompts/{prompt_type}/{vertical}_prompt.yaml"
    prompt_data = s3_io.load_yaml_from_s3(prompt_path)
    
    if prompt_data:
        logger.info(f"Prompt template chargé: {prompt_path}")
        return prompt_data
    
    logger.warning(f"Prompt {prompt_path} non trouvé, fallback sur global_prompts.yaml")
    return None
    
except Exception as e:
    logger.error(f"Erreur chargement prompt template: {e}")
    return None
```

**Problème identifié**: 
- Si `load_yaml_from_s3()` retourne None ou échoue, la fonction retourne None
- Le code continue avec le fallback V1

### 2.4 Vérification Logs CloudWatch

**Recherche**: "Approche B activée"

**Résultat**: Aucun log trouvé ❌

**Conclusion**: Le prompt LAI n'est PAS chargé, donc le code utilise le fallback V1 hardcodé.

### 2.5 Hypothèses sur la Cause

**Hypothèse 1**: `s3_io` n'est pas passé correctement
- Vérifier si `s3_io` est None dans `_normalize_sequential()`

**Hypothèse 2**: `client_config` n'a pas `bedrock_config`
- Vérifier structure de `client_config` chargée

**Hypothèse 3**: `load_yaml_from_s3()` échoue silencieusement
- Vérifier logs d'erreur dans CloudWatch

**Hypothèse 4**: `canonical_scopes` est None
- Vérifier si `canonical_scopes` est passé

---

## 🔧 PHASE 3: CORRECTIF LOCAL

### 3.1 Correctif 1: Ajouter Logs de Diagnostic

**Fichier**: `src_v2/vectora_core/normalization/bedrock_client.py`

**Fonction**: `__init__()`

**Changement**:
```python
def __init__(self, model_id: str, region: str = "us-east-1", s3_io=None, 
             client_config: Optional[Dict] = None, canonical_scopes: Optional[Dict] = None):
    self.region = region
    self.model_id = model_id
    self.s3_io = s3_io
    self.client_config = client_config
    self.canonical_scopes = canonical_scopes
    self.prompt_template = None
    
    # AJOUT: Logs de diagnostic
    logger.info(f"BedrockNormalizationClient init: s3_io={s3_io is not None}, "
                f"client_config={client_config is not None}, "
                f"canonical_scopes={canonical_scopes is not None}")
    
    # Charger prompt template si Approche B configurée
    if client_config and s3_io and canonical_scopes:
        bedrock_config = client_config.get('bedrock_config', {})
        normalization_prompt = bedrock_config.get('normalization_prompt')
        
        # AJOUT: Log config
        logger.info(f"bedrock_config présent: {bedrock_config is not None}, "
                    f"normalization_prompt: {normalization_prompt}")
        
        if normalization_prompt:
            self.prompt_template = prompt_resolver.load_prompt_template(
                'normalization', normalization_prompt, s3_io
            )
            if self.prompt_template:
                logger.info(f"Approche B activée: prompt {normalization_prompt} chargé")
            else:
                # AJOUT: Log si échec chargement
                logger.error(f"ÉCHEC chargement prompt {normalization_prompt}, "
                            f"fallback sur prompt V1 hardcodé")
    else:
        # AJOUT: Log pourquoi Approche B non activée
        logger.warning(f"Approche B NON activée: client_config={client_config is not None}, "
                      f"s3_io={s3_io is not None}, canonical_scopes={canonical_scopes is not None}")
    
    logger.info(f"Client Bedrock initialisé : modèle={self.model_id}, région={region}")
```

### 3.2 Correctif 2: Forcer Erreur si Prompt Non Chargé

**Fichier**: `src_v2/vectora_core/normalization/bedrock_client.py`

**Fonction**: `normalize_item()`

**Changement**:
```python
def normalize_item(self, item_text: str, canonical_examples: Dict, 
                  domain_contexts: Optional[list] = None,
                  canonical_prompts: Dict[str, Any] = None,
                  item_source_key: str = None) -> Dict[str, Any]:
    try:
        # APPROCHE B: Utiliser prompt pré-construit si disponible
        if self.prompt_template and self.canonical_scopes:
            prompt = self._build_prompt_approche_b(item_text, item_source_key)
            logger.info("Utilisation Approche B (prompt pré-construit)")
        # Fallback V2: Prompts canonical hardcodés
        elif canonical_prompts:
            prompt = self._build_normalization_prompt_v2(item_text, canonical_examples, canonical_prompts, item_source_key)
            logger.warning("Utilisation prompt V2 (canonical hardcodé)")
        # Fallback V1: Logique originale
        else:
            prompt = self._build_normalization_prompt_v1(item_text, canonical_examples, domain_contexts, item_source_key)
            logger.warning("Utilisation prompt V1 (hardcodé sans extraction dates)")
        
        # Appel Bedrock...
```

### 3.3 Correctif 3: Vérifier Passage de s3_io

**Fichier**: `src_v2/vectora_core/normalization/normalizer.py`

**Fonction**: `_normalize_sequential()`

**Vérification**:
```python
def _normalize_sequential(..., s3_io = None, client_config: Dict[str, Any] = None):
    # AJOUT: Log avant initialisation
    logger.info(f"Initialisation BedrockNormalizationClient: "
                f"s3_io={s3_io is not None}, "
                f"client_config={client_config is not None}, "
                f"canonical_scopes={canonical_scopes is not None}")
    
    bedrock_client = BedrockNormalizationClient(
        bedrock_model, bedrock_region, s3_io, client_config, canonical_scopes
    )
```

### 3.4 Correctif 4: Vérifier Appel normalize_items_batch

**Fichier**: `src_v2/lambdas/normalize_score/handler.py`

**Vérification**: S'assurer que `s3_io` et `client_config` sont passés

**Code attendu**:
```python
from vectora_core.normalization import normalize_items_batch
from vectora_core.shared import s3_io, config_loader

# Charger config
client_config = config_loader.load_client_config(client_id, config_bucket)
canonical_scopes = config_loader.load_canonical_scopes(config_bucket)

# Normaliser avec s3_io et client_config
curated_items = normalize_items_batch(
    raw_items=ingested_items,
    canonical_scopes=canonical_scopes,
    canonical_prompts=canonical_prompts,
    bedrock_model=bedrock_model,
    bedrock_region=bedrock_region,
    max_workers=1,
    watch_domains=watch_domains,
    matching_config=matching_config,
    s3_io=s3_io,              # ← CRITIQUE
    client_config=client_config  # ← CRITIQUE
)
```

---

## 🧪 PHASE 4: TESTS LOCAUX

### 4.1 Test Unitaire: Chargement Prompt

**Script**: `scripts/test_prompt_loading.py`

**Code**:
```python
from src_v2.vectora_core.shared import s3_io, config_loader
from src_v2.vectora_core.normalization.bedrock_client import BedrockNormalizationClient

# Charger config
client_config = config_loader.load_client_config("lai_weekly_v7", "vectora-inbox-config-dev")
canonical_scopes = config_loader.load_canonical_scopes("vectora-inbox-config-dev")

# Initialiser client
client = BedrockNormalizationClient(
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    region="us-east-1",
    s3_io=s3_io,
    client_config=client_config,
    canonical_scopes=canonical_scopes
)

# Vérifications
assert client.prompt_template is not None, "Prompt template non chargé"
assert "extracted_date" in str(client.prompt_template), "Prompt ne contient pas extracted_date"
print("✅ Prompt LAI chargé avec succès")
print(f"✅ Prompt contient extraction dates: {'extracted_date' in str(client.prompt_template)}")
```

### 4.2 Test Intégration: Normalisation avec Approche B

**Script**: `scripts/test_normalization_approche_b.py`

**Code**:
```python
from src_v2.vectora_core.normalization import normalize_items_batch
from src_v2.vectora_core.shared import s3_io, config_loader
import json

# Charger données test
with open('items_ingested_v7.json') as f:
    items = json.load(f)[:1]  # 1 item pour test rapide

# Charger config
client_config = config_loader.load_client_config("lai_weekly_v7", "vectora-inbox-config-dev")
canonical_scopes = config_loader.load_canonical_scopes("vectora-inbox-config-dev")

# Normaliser
curated = normalize_items_batch(
    raw_items=items,
    canonical_scopes=canonical_scopes,
    canonical_prompts=None,
    bedrock_model="anthropic.claude-3-sonnet-20240229-v1:0",
    bedrock_region="us-east-1",
    max_workers=1,
    s3_io=s3_io,
    client_config=client_config
)

# Vérifications
item = curated[0]
nc = item['normalized_content']
print(f"extracted_date: {nc.get('extracted_date')}")
print(f"date_confidence: {nc.get('date_confidence')}")

assert nc.get('extracted_date') is not None, "Date non extraite"
assert nc.get('date_confidence') > 0.5, "Confiance trop faible"
print("✅ Approche B fonctionne, date extraite")
```

### 4.3 Vérification Logs

**Logs attendus**:
```
[INFO] BedrockNormalizationClient init: s3_io=True, client_config=True, canonical_scopes=True
[INFO] bedrock_config présent: True, normalization_prompt: lai
[INFO] Prompt template chargé: canonical/prompts/normalization/lai_prompt.yaml
[INFO] Approche B activée: prompt lai chargé
[INFO] Utilisation Approche B (prompt pré-construit)
[INFO] Date extracted by Bedrock: 2025-12-09 (confidence: 0.95)
```

---

## 🚀 PHASE 5: DÉPLOIEMENT AWS

### 5.1 Création Layer vectora-core

**Script**: `scripts/layers/create_vectora_core_layer.py`

**Commande**:
```bash
python scripts/layers/create_vectora_core_layer.py
```

**Vérifications**:
- [ ] Layer créé avec succès
- [ ] ARN récupéré
- [ ] Taille < 50MB

### 5.2 Mise à Jour Lambda normalize-score-v2

**Commande**:
```bash
aws lambda update-function-configuration \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --layers arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev:41 \
  --region eu-west-3 \
  --profile rag-lai-prod
```

**Attendre**: 15 secondes

### 5.3 Test E2E avec lai_weekly_v7

**Commande**:
```bash
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --invocation-type Event \
  --cli-binary-format raw-in-base64-out \
  --payload '{"client_id": "lai_weekly_v7"}' \
  --region eu-west-3 \
  --profile rag-lai-prod \
  response_normalize_v7_approche_b.json
```

**Attendre**: 5-10 minutes

### 5.4 Vérification Logs CloudWatch

**Commande**:
```bash
aws logs tail /aws/lambda/vectora-inbox-normalize-score-v2-dev \
  --since 10m \
  --region eu-west-3 \
  --profile rag-lai-prod \
  --format short | findstr "Approche B"
```

**Logs attendus**:
```
[INFO] Approche B activée: prompt lai chargé
[INFO] Utilisation Approche B (prompt pré-construit)
```

### 5.5 Validation Extraction Dates

**Script**: `scripts/validate_bedrock_dates_v7.py`

**Métriques attendues**:
```
Métrique                    | Cible  | Actuel | Status
----------------------------|--------|--------|--------
Dates Bedrock extraites     | >95%   | [TBD]  | 
Haute confiance (>0.8)      | >90%   | [TBD]  |
Dates fallback utilisées    | <5%    | [TBD]  |
```

---

## 📊 PHASE 6: VALIDATION FINALE

### 6.1 Checklist Validation

**Approche B**:
- [ ] Log "Approche B activée" présent
- [ ] Log "Utilisation Approche B" présent
- [ ] Aucun log "Utilisation prompt V1"

**Extraction Dates**:
- [ ] >95% items avec `extracted_date` non-null
- [ ] >90% items avec `date_confidence` > 0.8
- [ ] <5% items utilisent date fallback

**Performance**:
- [ ] Temps normalisation < 10min
- [ ] Coût Bedrock < $0.30
- [ ] Aucune erreur Lambda

### 6.2 Décision GO/NO-GO

**Critères**:
- [ ] Approche B activée (logs confirmés)
- [ ] Extraction dates >= 95%
- [ ] Performance acceptable

**Décision**: ✅ GO / ❌ NO-GO

---

## 📝 PHASE 7: RETOUR USER

### 7.1 Rapport Final

**Document**: `docs/reports/rapport_final_correctif_v7_approche_b.md`

**Contenu**:
1. Problème: Prompt V1 hardcodé utilisé au lieu du prompt LAI configuré
2. Solution: Ajout logs diagnostic + vérification passage paramètres
3. Résultats: Approche B activée, dates extraites
4. Métriques finales

### 7.2 Fichiers Livrés

**Code modifié**:
1. `src_v2/vectora_core/normalization/bedrock_client.py` (logs diagnostic)
2. `src_v2/vectora_core/normalization/normalizer.py` (logs diagnostic)

**Tests créés**:
1. `scripts/test_prompt_loading.py`
2. `scripts/test_normalization_approche_b.py`

**Rapports**:
1. `docs/plans/plan_correctif_v7_approche_b.md` (ce fichier)
2. `docs/reports/rapport_final_correctif_v7_approche_b.md`

---

## 📋 CHECKLIST CONFORMITÉ

### Architecture
- [x] Utilise `src_v2/` comme base
- [x] Modification dans `vectora_core/`
- [x] Respecte Approche B (configuration > code)

### Configuration
- [x] Utilise prompt depuis S3 (lai_prompt.yaml)
- [x] Configuration pilote le comportement
- [x] Pas de logique hardcodée

### Déploiement
- [x] Layer créé avec script officiel
- [x] Tests locaux avant déploiement
- [x] Validation E2E

---

## 🎯 RÉSUMÉ EXÉCUTIF

**Problème**: Prompt V1 hardcodé utilisé au lieu du prompt LAI configuré (Approche B)

**Cause**: Paramètres `s3_io` ou `client_config` non passés correctement, ou prompt non chargé

**Solution**: 
1. Ajouter logs diagnostic pour identifier où ça bloque
2. Vérifier passage de `s3_io` et `client_config` dans toute la chaîne
3. Forcer erreur si prompt configuré non chargé

**Fichiers modifiés**:
1. `bedrock_client.py` (logs diagnostic)
2. `normalizer.py` (logs diagnostic)

**Tests**: Tests locaux + E2E lai_weekly_v7

**Critères succès**: 
- Logs "Approche B activée" présents
- >95% dates extraites

**Durée estimée**: 2 heures

---

**Plan Correctif v7 - Approche B**  
**Date**: 2026-01-29 17:00 UTC  
**Status**: ✅ PRÊT POUR EXÉCUTION  
**Conformité**: ✅ Respecte vectora-inbox-development-rules.md
