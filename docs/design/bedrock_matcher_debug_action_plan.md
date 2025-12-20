# Plan d'Action - Debug Matching Bedrock Fonctionnel

**Date :** 19 décembre 2025  
**Version :** 1.0  
**Objectif :** Identifier et corriger pourquoi bedrock_matcher.py retourne 0% matching  
**Conformité :** 100% vectora-inbox-development-rules.md  
**Durée estimée :** 60 minutes  

---

## 🎯 CONTEXTE ET PROBLÈME

### Situation Actuelle
- **Architecture Bedrock-Only :** ✅ Implémentée dans src_v2
- **Appels Bedrock :** ✅ 30 appels (15 normalisation + 15 matching)
- **Résultat matching :** ❌ 0% systématiquement
- **Layer v24 :** ✅ Déployée avec corrections

### Problème Identifié
`bedrock_matcher.py` retourne systématiquement `{"matched_domains": [], "domain_relevance": {}}` malgré des appels Bedrock réussis.

---

## 📋 PLAN D'ACTION - 4 PHASES

### Phase 1 : Test Layer v24 Actuelle (10 min)

**Objectif :** Valider que les corrections architecturales sont déployées

**Actions :**
1. **Test E2E avec layer v24**
   ```bash
   aws lambda invoke \
     --function-name vectora-inbox-normalize-score-v2-dev \
     --payload '{"client_id": "lai_weekly_v4"}' \
     --region eu-west-3 \
     --profile rag-lai-prod \
     response_v24_test.json
   ```

2. **Analyser logs CloudWatch**
   - Vérifier "Architecture Bedrock-Only Pure : matching déterministe supprimé"
   - Confirmer "Matching Bedrock V2: X/15 items matchés"
   - Identifier si X > 0

3. **Validation résultat**
   - Si X > 0 → Problème résolu, documenter succès
   - Si X = 0 → Continuer Phase 2

### Phase 2 : Debug bedrock_matcher.py (20 min)

**Objectif :** Identifier pourquoi les appels Bedrock ne produisent pas de matches

#### 2.1 Ajout Logs Debug (5 min)

**Fichier :** `src_v2/vectora_core/normalization/bedrock_matcher.py`

**Modifications :**
```python
def match_item_to_domains_bedrock(...):
    logger.info(f"DEBUG: watch_domains reçus: {len(watch_domains)} domaines")
    logger.info(f"DEBUG: watch_domains détail: {[d.get('id') for d in watch_domains]}")
    
    if not watch_domains:
        logger.debug("Aucun domaine de veille configuré")
        return {"matched_domains": [], "domain_relevance": {}}
    
    # Appel Bedrock
    response_text = _call_bedrock_matching(...)
    logger.info(f"DEBUG: Réponse Bedrock brute: {response_text[:200]}...")
    
    # Parse réponse
    matching_result = _parse_bedrock_matching_response(response_text)
    logger.info(f"DEBUG: Résultat parsé: {matching_result}")
    
    # Application seuils
    filtered_result = _apply_matching_thresholds(matching_result, matching_config)
    logger.info(f"DEBUG: Après seuils: {filtered_result}")
    
    return filtered_result
```

#### 2.2 Vérification Configuration (5 min)

**Fichier :** `client-config-examples/lai_weekly_v4.yaml`

**Validation :**
```yaml
watch_domains:
  - id: tech_lai_ecosystem
    type: technology
    company_scope: lai_companies_global
    technology_scope: lai_keywords
    min_domain_score: 0.25
  - id: regulatory_lai
    type: regulatory
    company_scope: lai_companies_global
    min_domain_score: 0.20
```

#### 2.3 Test Prompts Bedrock (10 min)

**Vérifier :** `canonical/prompts/global_prompts.yaml`

**Section critique :**
```yaml
matching:
  matching_watch_domains_v2:
    user_template: |
      Analyze this item and determine relevance to watch domains.
      
      ITEM:
      Title: {{item_title}}
      Summary: {{item_summary}}
      Entities: {{item_entities}}
      
      DOMAINS:
      {{domains_context}}
      
      Return JSON: {"domain_evaluations": [...]}
```

### Phase 3 : Test Isolé Bedrock Matcher (15 min)

**Objectif :** Tester bedrock_matcher.py avec un item simple

#### 3.1 Script Test Isolé

**Fichier :** `scripts/test_bedrock_matcher_debug.py`

```python
import sys
sys.path.append('src_v2')

from vectora_core.normalization.bedrock_matcher import match_item_to_domains_bedrock
from vectora_core.shared import config_loader

# Item test simple
test_item = {
    "title": "Nanexa and Moderna Partnership",
    "normalized_content": {
        "entities": {
            "companies": ["Nanexa", "Moderna"],
            "technologies": ["PharmaShell"]
        }
    }
}

# Configuration test
watch_domains = [
    {
        "id": "tech_lai_ecosystem",
        "type": "technology",
        "company_scope": "lai_companies_global",
        "min_domain_score": 0.25
    }
]

# Test
result = match_item_to_domains_bedrock(
    test_item, watch_domains, {}, {}, {}, 
    "anthropic.claude-3-sonnet-20240229-v1:0"
)

print(f"Résultat: {result}")
```

#### 3.2 Exécution Test

```bash
cd c:\Users\franc\OneDrive\Bureau\vectora-inbox
python scripts/test_bedrock_matcher_debug.py
```

### Phase 4 : Correction et Validation (15 min)

**Objectif :** Corriger le problème identifié et valider

#### 4.1 Corrections Possibles

**Problème A : Seuils trop stricts**
```python
# Dans matching_config
min_domain_score: 0.10  # Au lieu de 0.25
```

**Problème B : Prompts incorrects**
```yaml
# Simplifier le prompt
user_template: |
  Is this item about {{domains_context}}?
  Item: {{item_title}}
  Answer: {"domain_evaluations": [{"domain_id": "tech_lai_ecosystem", "is_relevant": true/false, "relevance_score": 0.0-1.0}]}
```

**Problème C : Parsing JSON défaillant**
```python
def _parse_bedrock_matching_response(response_text: str):
    try:
        # Nettoyer la réponse
        clean_text = response_text.strip()
        if clean_text.startswith('```json'):
            clean_text = clean_text[7:-3]
        
        result = json.loads(clean_text)
        return result
    except Exception as e:
        logger.error(f"Erreur parsing: {e}, texte: {response_text}")
        return {"domain_evaluations": []}
```

#### 4.2 Déploiement Correction

```bash
# Rebuild layer
cd layer_build_v24
powershell -Command "Compress-Archive -Path * -DestinationPath ../vectora-core-bedrock-debug-v25.zip -Force"

# Deploy layer
aws lambda publish-layer-version \
  --layer-name vectora-inbox-vectora-core-dev \
  --zip-file fileb://vectora-core-bedrock-debug-v25.zip \
  --region eu-west-3 \
  --profile rag-lai-prod

# Update Lambda
aws lambda update-function-configuration \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --layers arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev:25 \
  --region eu-west-3 \
  --profile rag-lai-prod
```

#### 4.3 Test Final

```bash
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --payload '{"client_id": "lai_weekly_v4"}' \
  --region eu-west-3 \
  --profile rag-lai-prod \
  response_v25_final.json
```

---

## 📊 CRITÈRES DE SUCCÈS

### Métriques Attendues
- **Matching rate :** > 30% (5+ items sur 15)
- **Logs debug :** Réponses Bedrock visibles
- **Domaines matchés :** tech_lai_ecosystem présent
- **Temps exécution :** < 120 secondes

### Validation Logs
```
[INFO] DEBUG: watch_domains reçus: 2 domaines
[INFO] DEBUG: Réponse Bedrock brute: {"domain_evaluations": [{"domain_id": "tech_lai_ecosystem", "is_relevant": true, "relevance_score": 0.8}]}
[INFO] DEBUG: Après seuils: {"matched_domains": ["tech_lai_ecosystem"]}
[INFO] Matching Bedrock V2: 7/15 items matchés (46.7%)
```

---

## 🔒 CONFORMITÉ RÈGLES VECTORA-INBOX

### Architecture V2 Respectée
- ✅ Modifications uniquement dans `src_v2/vectora_core`
- ✅ Aucune modification handlers
- ✅ Configuration pilotée (lai_weekly_v4.yaml)
- ✅ Logs standardisés CloudWatch

### Hygiène V4 Respectée
- ✅ Ajout logs debug temporaires
- ✅ Pas de nouvelles dépendances
- ✅ Code modulaire préservé
- ✅ Tests isolés dans scripts/

### Environnement AWS Conforme
- ✅ Région eu-west-3 (Lambda)
- ✅ Région us-east-1 (Bedrock)
- ✅ Profil rag-lai-prod
- ✅ Conventions nommage -v2-dev

---

## 📋 CHECKLIST EXÉCUTION

### Avant Démarrage
- [ ] Layer v24 déployée et active
- [ ] Client lai_weekly_v4 configuré
- [ ] Accès CloudWatch logs
- [ ] Scripts de test préparés

### Phase 1 - Test Layer v24
- [ ] Invocation Lambda réussie
- [ ] Logs "Architecture Bedrock-Only Pure" présents
- [ ] Matching rate identifié (0% ou >0%)

### Phase 2 - Debug bedrock_matcher.py
- [ ] Logs debug ajoutés
- [ ] Configuration lai_weekly_v4 validée
- [ ] Prompts global_prompts.yaml vérifiés

### Phase 3 - Test Isolé
- [ ] Script test_bedrock_matcher_debug.py créé
- [ ] Test local réussi
- [ ] Problème racine identifié

### Phase 4 - Correction
- [ ] Correction appliquée
- [ ] Layer v25 déployée
- [ ] Test E2E final réussi
- [ ] Matching rate > 30%

---

## 🎯 RÉSULTAT ATTENDU

**Après exécution de ce plan :**
- Matching Bedrock fonctionnel avec rate > 30%
- Logs debug permettant monitoring continu
- Architecture Bedrock-Only validée E2E
- Base solide pour Phase 5 (Newsletter)

**En cas d'échec :**
- Problème racine documenté précisément
- Logs détaillés pour investigation approfondie
- Options alternatives identifiées

---

*Plan d'Action - Debug Matching Bedrock Fonctionnel*  
*Conformité 100% vectora-inbox-development-rules.md*  
*Objectif : Matching rate 0% → 30%+ en 60 minutes*