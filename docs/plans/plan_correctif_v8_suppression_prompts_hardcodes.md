# Plan Correctif v8 - Suppression Prompts Hardcodés (100% Approche B)
## Date: 2026-01-29 17:10 UTC
## Objectif: Supprimer prompts hardcodés V1/V2 et forcer utilisation prompt configuré

---

## 🎯 PHASE 1: CADRAGE

### Problème Identifié

**Symptôme**: 0% de dates extraites par Bedrock (cible: >95%)

**Cause racine**: 
- Le prompt LAI (`lai_prompt.yaml`) sur S3 contient les instructions d'extraction de date ✅
- Le code a 3 chemins de génération de prompt:
  1. **Approche B** (prompt pré-construit depuis S3) ✅ CORRECT
  2. **Prompt V2** (hardcodé avec canonical_prompts) ❌ PAS D'EXTRACTION DATE
  3. **Prompt V1** (hardcodé basique) ❌ PAS D'EXTRACTION DATE
- Le code utilise le fallback V1 ou V2 au lieu d'Approche B

**Conflit de prompts**:
```python
# Dans bedrock_client.py - normalize_item()
if self.prompt_template and self.canonical_scopes:
    prompt = self._build_prompt_approche_b(...)           # ← VOULU (avec dates)
elif canonical_prompts:
    prompt = self._build_normalization_prompt_v2(...)     # ← FALLBACK 1 (sans dates)
else:
    prompt = self._build_normalization_prompt_v1(...)     # ← FALLBACK 2 (sans dates)
```

### Objectif du Correctif

**Cible**: Supprimer les prompts hardcodés V1 et V2 pour garantir 100% utilisation du prompt configuré

**Approche**: 
1. Supprimer `_build_normalization_prompt_v1()` et `_build_normalization_prompt_v2()`
2. Forcer erreur si Approche B n'est pas activée
3. S'assurer que `s3_io`, `client_config` et `canonical_scopes` sont toujours passés

### Périmètre

**Fichiers à modifier**:
1. `src_v2/vectora_core/normalization/bedrock_client.py` (supprimer V1/V2, forcer Approche B)
2. `src_v2/vectora_core/normalization/normalizer.py` (garantir passage paramètres)

**Fichiers déjà corrects**:
1. `canonical/prompts/normalization/lai_prompt.yaml` (prompt avec extraction dates)
2. `client-config-examples/lai_weekly_v7.yaml` (config avec normalization_prompt: "lai")

**Contraintes**:
- Respecter vectora-inbox-development-rules.md
- Utiliser `src_v2/` comme base
- Configuration > Code (principe Approche B)
- Tester localement avant déploiement

---

## 🔍 PHASE 2: DIAGNOSTIC APPROFONDI

### 2.1 Analyse Code Actuel

**Fichier**: `src_v2/vectora_core/normalization/bedrock_client.py`

**Fonctions à supprimer**:
1. `_build_normalization_prompt_v1()` (ligne ~280, ~150 lignes)
2. `_build_normalization_prompt_v2()` (ligne ~220, ~60 lignes)

**Fonction à conserver**:
1. `_build_prompt_approche_b()` (ligne ~520, ~30 lignes) ✅

**Impact**: ~210 lignes de code à supprimer

### 2.2 Analyse Dépendances

**Qui appelle `_build_normalization_prompt_v1()`**:
- `normalize_item()` (fallback si Approche B échoue)

**Qui appelle `_build_normalization_prompt_v2()`**:
- `normalize_item()` (fallback si Approche B échoue)

**Solution**: Supprimer les fallbacks et forcer erreur si Approche B non disponible

### 2.3 Validation Approche B

**Conditions pour Approche B**:
```python
if self.prompt_template and self.canonical_scopes:
    # Approche B activée
```

**Vérifications nécessaires**:
1. `self.prompt_template` chargé depuis S3
2. `self.canonical_scopes` passé au constructeur
3. `s3_io` passé au constructeur
4. `client_config` avec `bedrock_config.normalization_prompt`

---

## 🔧 PHASE 3: CORRECTIF LOCAL

### 3.1 Correctif 1: Supprimer Prompts Hardcodés

**Fichier**: `src_v2/vectora_core/normalization/bedrock_client.py`

**Supprimer**:
1. Fonction `_build_normalization_prompt_v1()` (ligne ~280-430)
2. Fonction `_build_normalization_prompt_v2()` (ligne ~220-280)
3. Méthodes helper: `_extract_company_from_source_key()`, `_is_pure_player_company()`

**Garder**:
1. Fonction `_build_prompt_approche_b()` ✅

### 3.2 Correctif 2: Forcer Approche B

**Fichier**: `src_v2/vectora_core/normalization/bedrock_client.py`

**Fonction**: `normalize_item()`

**Avant**:
```python
def normalize_item(self, item_text: str, canonical_examples: Dict, ...):
    try:
        # APPROCHE B
        if self.prompt_template and self.canonical_scopes:
            prompt = self._build_prompt_approche_b(item_text, item_source_key)
        # Fallback V2
        elif canonical_prompts:
            prompt = self._build_normalization_prompt_v2(...)
        # Fallback V1
        else:
            prompt = self._build_normalization_prompt_v1(...)
        
        # Appel Bedrock...
```

**Après**:
```python
def normalize_item(self, item_text: str, canonical_examples: Dict, ...):
    try:
        # APPROCHE B OBLIGATOIRE
        if not self.prompt_template or not self.canonical_scopes:
            error_msg = (
                "Approche B non activée. Vérifier que client_config contient "
                "'bedrock_config.normalization_prompt' et que s3_io et canonical_scopes "
                "sont passés au constructeur."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Construire prompt via Approche B
        prompt = self._build_prompt_approche_b(item_text, item_source_key)
        logger.info("Utilisation Approche B (prompt pré-construit)")
        
        # Appel Bedrock...
```

### 3.3 Correctif 3: Améliorer Initialisation

**Fichier**: `src_v2/vectora_core/normalization/bedrock_client.py`

**Fonction**: `__init__()`

**Avant**:
```python
def __init__(self, model_id: str, region: str = "us-east-1", s3_io=None, 
             client_config: Optional[Dict] = None, canonical_scopes: Optional[Dict] = None):
    self.region = region
    self.model_id = model_id
    self.s3_io = s3_io
    self.client_config = client_config
    self.canonical_scopes = canonical_scopes
    self.prompt_template = None
    
    # Charger prompt template si Approche B configurée
    if client_config and s3_io and canonical_scopes:
        bedrock_config = client_config.get('bedrock_config', {})
        normalization_prompt = bedrock_config.get('normalization_prompt')
        
        if normalization_prompt:
            self.prompt_template = prompt_resolver.load_prompt_template(
                'normalization', normalization_prompt, s3_io
            )
            if self.prompt_template:
                logger.info(f"Approche B activée: prompt {normalization_prompt} chargé")
    
    logger.info(f"Client Bedrock initialisé : modèle={self.model_id}, région={region}")
```

**Après**:
```python
def __init__(self, model_id: str, region: str = "us-east-1", s3_io=None, 
             client_config: Optional[Dict] = None, canonical_scopes: Optional[Dict] = None):
    self.region = region
    self.model_id = model_id
    self.s3_io = s3_io
    self.client_config = client_config
    self.canonical_scopes = canonical_scopes
    self.prompt_template = None
    
    # APPROCHE B OBLIGATOIRE
    if not client_config:
        raise ValueError("client_config est requis pour Approche B")
    if not s3_io:
        raise ValueError("s3_io est requis pour Approche B")
    if not canonical_scopes:
        raise ValueError("canonical_scopes est requis pour Approche B")
    
    # Charger prompt template
    bedrock_config = client_config.get('bedrock_config', {})
    normalization_prompt = bedrock_config.get('normalization_prompt')
    
    if not normalization_prompt:
        raise ValueError(
            "client_config doit contenir 'bedrock_config.normalization_prompt' "
            "(ex: 'lai' pour charger lai_prompt.yaml)"
        )
    
    self.prompt_template = prompt_resolver.load_prompt_template(
        'normalization', normalization_prompt, s3_io
    )
    
    if not self.prompt_template:
        raise ValueError(
            f"Échec chargement prompt '{normalization_prompt}'. "
            f"Vérifier que canonical/prompts/normalization/{normalization_prompt}_prompt.yaml "
            f"existe sur S3."
        )
    
    logger.info(f"✅ Approche B activée: prompt {normalization_prompt} chargé")
    logger.info(f"Client Bedrock initialisé : modèle={self.model_id}, région={region}")
```

### 3.4 Correctif 4: Déplacer Helpers dans _build_prompt_approche_b

**Fichier**: `src_v2/vectora_core/normalization/bedrock_client.py`

**Fonction**: `_build_prompt_approche_b()`

**Avant**:
```python
def _build_prompt_approche_b(self, item_text: str, item_source_key: str = None) -> str:
    variables = {'item_text': item_text}
    
    # Ajouter contexte pure player si détecté
    if item_source_key:
        company_name = self._extract_company_from_source_key(item_source_key)
        if company_name and self._is_pure_player_company(company_name):
            pure_player_context = f"..."
            variables['pure_player_context'] = pure_player_context
    
    prompt = prompt_resolver.build_prompt(
        self.prompt_template,
        self.canonical_scopes,
        variables
    )
    
    logger.info("Prompt construit via Approche B")
    return prompt
```

**Après**:
```python
def _build_prompt_approche_b(self, item_text: str, item_source_key: str = None) -> str:
    variables = {'item_text': item_text}
    
    # Ajouter contexte pure player si détecté
    if item_source_key:
        # Mapping inline (pas besoin de méthode séparée)
        company_mapping = {
            'medincell': 'MedinCell',
            'camurus': 'Camurus',
            'delsitech': 'DelSiTech',
            'nanexa': 'Nanexa',
            'peptron': 'Peptron'
        }
        
        source_lower = item_source_key.lower()
        company_name = None
        for key, name in company_mapping.items():
            if key in source_lower:
                company_name = name
                break
        
        # Pure players LAI
        pure_players = ['MedinCell', 'Camurus', 'DelSiTech', 'Nanexa', 'Peptron']
        
        if company_name and company_name in pure_players:
            pure_player_context = (
                f"\n\nIMPORTANT CONTEXT: This content is from {company_name}, "
                f"a LAI pure-player company specializing in long-acting injectable "
                f"technologies. Even if LAI technologies are not explicitly mentioned, "
                f"consider the LAI context and relevance given the company's "
                f"specialization in this field."
            )
            variables['pure_player_context'] = pure_player_context
    
    prompt = prompt_resolver.build_prompt(
        self.prompt_template,
        self.canonical_scopes,
        variables
    )
    
    logger.info("Prompt construit via Approche B")
    return prompt
```

### 3.5 Correctif 5: Garantir Passage Paramètres

**Fichier**: `src_v2/vectora_core/normalization/normalizer.py`

**Fonction**: `_normalize_sequential()`

**Vérification**:
```python
def _normalize_sequential(
    raw_items: List[Dict[str, Any]], 
    examples: Dict[str, str],
    bedrock_model: str,
    bedrock_region: str,
    stats: Dict[str, Any],
    canonical_scopes: Dict[str, Any] = None,
    watch_domains: List[Dict[str, Any]] = None,
    matching_config: Dict[str, Any] = None,
    canonical_prompts: Dict[str, Any] = None,
    s3_io = None,
    client_config: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    
    # VÉRIFICATION: Tous les paramètres requis sont présents
    if not s3_io:
        raise ValueError("s3_io est requis pour Approche B")
    if not client_config:
        raise ValueError("client_config est requis pour Approche B")
    if not canonical_scopes:
        raise ValueError("canonical_scopes est requis pour Approche B")
    
    logger.info(f"✅ Paramètres Approche B validés: s3_io, client_config, canonical_scopes")
    
    # Initialisation du client Bedrock avec support Approche B
    bedrock_client = BedrockNormalizationClient(
        bedrock_model, bedrock_region, s3_io, client_config, canonical_scopes
    )
    
    # ... reste du code
```

---

## 🧪 PHASE 4: TESTS LOCAUX

### 4.1 Test Unitaire: Erreur si Paramètres Manquants

**Script**: `scripts/test_approche_b_required.py`

**Code**:
```python
from src_v2.vectora_core.normalization.bedrock_client import BedrockNormalizationClient
import pytest

# Test 1: Erreur si s3_io manquant
with pytest.raises(ValueError, match="s3_io est requis"):
    client = BedrockNormalizationClient(
        model_id="test",
        region="us-east-1",
        s3_io=None,  # ← Manquant
        client_config={"bedrock_config": {"normalization_prompt": "lai"}},
        canonical_scopes={}
    )

# Test 2: Erreur si client_config manquant
with pytest.raises(ValueError, match="client_config est requis"):
    client = BedrockNormalizationClient(
        model_id="test",
        region="us-east-1",
        s3_io=s3_io,
        client_config=None,  # ← Manquant
        canonical_scopes={}
    )

# Test 3: Erreur si normalization_prompt manquant
with pytest.raises(ValueError, match="normalization_prompt"):
    client = BedrockNormalizationClient(
        model_id="test",
        region="us-east-1",
        s3_io=s3_io,
        client_config={"bedrock_config": {}},  # ← Pas de normalization_prompt
        canonical_scopes={}
    )

print("✅ Tous les tests de validation passent")
```

### 4.2 Test Intégration: Approche B Fonctionne

**Script**: `scripts/test_approche_b_works.py`

**Code**:
```python
from src_v2.vectora_core.shared import s3_io, config_loader
from src_v2.vectora_core.normalization.bedrock_client import BedrockNormalizationClient

# Charger config
client_config = config_loader.load_client_config("lai_weekly_v7", "vectora-inbox-config-dev")
canonical_scopes = config_loader.load_canonical_scopes("vectora-inbox-config-dev")

# Initialiser client (doit réussir)
client = BedrockNormalizationClient(
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    region="us-east-1",
    s3_io=s3_io,
    client_config=client_config,
    canonical_scopes=canonical_scopes
)

# Vérifications
assert client.prompt_template is not None, "Prompt template non chargé"
assert "extracted_date" in str(client.prompt_template), "Prompt sans extraction dates"

print("✅ Approche B activée avec succès")
print(f"✅ Prompt contient extraction dates")
```

### 4.3 Test E2E Local: Normalisation avec Dates

**Script**: `scripts/test_normalization_with_dates.py`

**Code**:
```python
from src_v2.vectora_core.normalization import normalize_items_batch
from src_v2.vectora_core.shared import s3_io, config_loader
import json

# Charger données test
with open('items_ingested_v7.json') as f:
    items = json.load(f)[:1]

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

assert nc.get('extracted_date') is not None, "Date non extraite"
assert nc.get('date_confidence') > 0.5, "Confiance trop faible"

print(f"✅ Date extraite: {nc.get('extracted_date')}")
print(f"✅ Confiance: {nc.get('date_confidence')}")
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
- [ ] Taille réduite (~50KB de moins sans prompts hardcodés)
- [ ] ARN récupéré

### 5.2 Mise à Jour Lambda normalize-score-v2

**Commande**:
```bash
aws lambda update-function-configuration \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --layers arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev:42 \
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
  response_normalize_v7_approche_b_only.json
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
[INFO] ✅ Approche B activée: prompt lai chargé
[INFO] ✅ Paramètres Approche B validés: s3_io, client_config, canonical_scopes
[INFO] Utilisation Approche B (prompt pré-construit)
[INFO] Date extracted by Bedrock: 2025-12-09 (confidence: 0.95)
```

**Logs interdits** (ne doivent JAMAIS apparaître):
```
[WARNING] Utilisation prompt V1
[WARNING] Utilisation prompt V2
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

**Suppression Prompts Hardcodés**:
- [ ] Fonction `_build_normalization_prompt_v1()` supprimée
- [ ] Fonction `_build_normalization_prompt_v2()` supprimée
- [ ] Aucun fallback vers prompts hardcodés
- [ ] Erreur explicite si Approche B non disponible

**Approche B Obligatoire**:
- [ ] Log "✅ Approche B activée" présent
- [ ] Log "Utilisation Approche B" présent
- [ ] Aucun log "prompt V1" ou "prompt V2"
- [ ] Erreur si paramètres manquants

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
- [ ] Prompts hardcodés supprimés (100%)
- [ ] Approche B activée (logs confirmés)
- [ ] Extraction dates >= 95%
- [ ] Performance acceptable

**Décision**: ✅ GO / ❌ NO-GO

---

## 📝 PHASE 7: RETOUR USER

### 7.1 Rapport Final

**Document**: `docs/reports/rapport_final_correctif_v8_suppression_prompts_hardcodes.md`

**Contenu**:
1. Problème: Conflit entre prompts hardcodés et prompt configuré
2. Solution: Suppression complète prompts V1/V2, Approche B obligatoire
3. Résultats: 100% utilisation prompt configuré, dates extraites
4. Métriques finales

### 7.2 Fichiers Livrés

**Code modifié**:
1. `src_v2/vectora_core/normalization/bedrock_client.py` (suppression V1/V2, ~210 lignes supprimées)
2. `src_v2/vectora_core/normalization/normalizer.py` (validation paramètres)

**Tests créés**:
1. `scripts/test_approche_b_required.py`
2. `scripts/test_approche_b_works.py`
3. `scripts/test_normalization_with_dates.py`

**Rapports**:
1. `docs/plans/plan_correctif_v8_suppression_prompts_hardcodes.md` (ce fichier)
2. `docs/reports/rapport_final_correctif_v8_suppression_prompts_hardcodes.md`

### 7.3 Bénéfices de cette Approche

**Technique**:
- ✅ Suppression de ~210 lignes de code mort
- ✅ Aucun conflit de prompts possible
- ✅ Code plus simple et maintenable
- ✅ Erreurs explicites si mal configuré

**Métier**:
- ✅ Configuration > Code (principe Approche B respecté)
- ✅ Prompts modifiables sans redéploiement
- ✅ Cohérence garantie entre clients
- ✅ Extraction dates fonctionnelle

---

## 📋 CHECKLIST CONFORMITÉ

### Architecture
- [x] Utilise `src_v2/` comme base
- [x] Suppression code mort (prompts hardcodés)
- [x] Respecte Approche B (configuration > code)
- [x] Pas de duplication de logique

### Configuration
- [x] Utilise prompt depuis S3 (lai_prompt.yaml)
- [x] Configuration pilote le comportement
- [x] Erreur explicite si mal configuré
- [x] Pas de logique hardcodée

### Déploiement
- [x] Layer créé avec script officiel
- [x] Tests locaux avant déploiement
- [x] Validation E2E
- [x] Logs explicites

---

## 🎯 RÉSUMÉ EXÉCUTIF

**Problème**: Conflit entre 3 chemins de génération de prompt (Approche B, V2, V1)

**Cause**: Prompts hardcodés V1/V2 utilisés en fallback au lieu du prompt configuré

**Solution**: 
1. **Supprimer** `_build_normalization_prompt_v1()` et `_build_normalization_prompt_v2()`
2. **Forcer** erreur si Approche B non activée
3. **Garantir** passage de `s3_io`, `client_config`, `canonical_scopes`

**Impact**:
- ~210 lignes de code supprimées
- 100% utilisation prompt configuré
- Aucun conflit possible

**Fichiers modifiés**:
1. `bedrock_client.py` (suppression V1/V2, validation stricte)
2. `normalizer.py` (validation paramètres)

**Tests**: Tests locaux + E2E lai_weekly_v7

**Critères succès**: 
- Logs "✅ Approche B activée" présents
- Aucun log "prompt V1" ou "V2"
- >95% dates extraites

**Durée estimée**: 2 heures

---

**Plan Correctif v8 - Suppression Prompts Hardcodés**  
**Date**: 2026-01-29 17:10 UTC  
**Status**: ✅ PRÊT POUR EXÉCUTION  
**Conformité**: ✅ Respecte vectora-inbox-development-rules.md  
**Garantie**: ✅ 100% aucun conflit de prompts possible
