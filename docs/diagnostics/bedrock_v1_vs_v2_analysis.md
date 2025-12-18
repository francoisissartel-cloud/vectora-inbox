# Analyse Comparative : Bedrock V1 vs V2

**Date** : 16 janvier 2025  
**Objectif** : Identifier les bonnes pratiques V1 à appliquer à V2  

---

## 1. Différences Critiques Identifiées

### 1.1 Gestion du Modèle Bedrock

**V1 (fonctionnel) :**
```python
# Dans bedrock_client.py V1
def get_bedrock_client():
    region = os.environ.get('BEDROCK_REGION', 'us-east-1')
    return boto3.client('bedrock-runtime', region_name=region)

# Appel direct avec modèle depuis env var
bedrock_model_id = env_vars.get('BEDROCK_MODEL_ID')
```

**V2 (problématique) :**
```python
# Dans bedrock_client.py V2 - AVANT correction
def __init__(self, model_id: str, region: str = "us-east-1"):
    self.model_id = model_id  # Utilise directement le modèle configuré
```

**✅ Correction appliquée V2 :**
```python
# Fallback automatique sur modèle fonctionnel
if model_id == "anthropic.claude-3-5-sonnet-20241022-v2:0":
    logger.warning(f"Modèle {model_id} nécessite inference profile, fallback sur Haiku")
    self.model_id = "anthropic.claude-3-haiku-20240307-v1:0"
```

### 1.2 Format d'Appel Bedrock

**V1 (fonctionnel) :**
```python
request_body = {
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 1000,
    "messages": [
        {
            "role": "user",
            "content": prompt
        }
    ],
    "temperature": 0.0
}

response = client.invoke_model(
    modelId=model_id,
    body=json.dumps(request_body)
)
```

**V2 (identique) :**
```python
# Format identique - pas de problème ici
body = {
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 1000,
    "temperature": 0.0,
    "messages": [...]
}
```

### 1.3 Gestion d'Erreurs Bedrock

**V1 (robuste) :**
```python
def _call_bedrock_with_retry(model_id, request_body, max_retries=3):
    for attempt in range(max_retries + 1):
        try:
            response = client.invoke_model(modelId=model_id, body=json.dumps(request_body))
            # Parsing immédiat
            response_body = json.loads(response['body'].read())
            content = response_body.get('content', [])
            if content and len(content) > 0:
                response_text = content[0].get('text', '')
            return response_text
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'ThrottlingException':
                # Retry avec backoff
                delay = base_delay * (2 ** attempt) + random.uniform(0, 0.1)
                time.sleep(delay)
                continue
            else:
                raise  # Autres erreurs : pas de retry
```

**V2 (moins robuste) :**
```python
# Gestion d'erreurs moins détaillée
except ClientError as e:
    error_code = e.response.get("Error", {}).get("Code", "Unknown")
    if error_code == "ValidationException":
        raise Exception("Paramètres Bedrock invalides")
```

### 1.4 Variables d'Environnement

**V1 (pattern observé) :**
```python
# Dans handler.py V1
env_vars = {
    "ENV": os.environ.get("ENV", "dev"),
    "CONFIG_BUCKET": os.environ.get("CONFIG_BUCKET"),
    "DATA_BUCKET": os.environ.get("DATA_BUCKET"),
    "BEDROCK_MODEL_ID": os.environ.get("BEDROCK_MODEL_ID"),
    # Pas de BEDROCK_REGION explicite - utilise défaut us-east-1
}
```

**V2 (pattern actuel) :**
```python
# Variables similaires mais avec BEDROCK_REGION explicite
"BEDROCK_REGION": env_vars["BEDROCK_REGION"]
```

---

## 2. Bonnes Pratiques V1 à Appliquer

### 2.1 Stratégie de Fallback Modèle

**Principe V1 :** Robustesse par défaut
- Utilise des valeurs par défaut sûres
- Gestion gracieuse des erreurs de configuration

**Application V2 :**
```python
def get_working_bedrock_model(configured_model: str) -> str:
    """Retourne un modèle Bedrock fonctionnel avec fallback."""
    # Modèles problématiques nécessitant inference profile
    problematic_models = [
        "anthropic.claude-3-5-sonnet-20241022-v2:0"
    ]
    
    # Modèles de fallback testés et fonctionnels
    fallback_models = [
        "anthropic.claude-3-haiku-20240307-v1:0",
        "anthropic.claude-3-5-haiku-20241022-v1:0"
    ]
    
    if configured_model in problematic_models:
        logger.warning(f"Modèle {configured_model} nécessite inference profile")
        return fallback_models[0]
    
    return configured_model
```

### 2.2 Gestion d'Erreurs Robuste

**Principe V1 :** Retry intelligent avec backoff
- Retry uniquement sur ThrottlingException
- Backoff exponentiel avec jitter
- Échec rapide sur autres erreurs

**Application V2 :**
```python
def invoke_bedrock_with_v1_retry(client, model_id, body, max_retries=3):
    """Appel Bedrock avec la stratégie de retry V1."""
    import random
    import time
    
    for attempt in range(max_retries + 1):
        try:
            response = client.invoke_model(
                modelId=model_id,
                body=json.dumps(body)
            )
            
            # Parsing V1 exact
            response_body = json.loads(response['body'].read())
            content = response_body.get('content', [])
            
            if content and len(content) > 0:
                return content[0].get('text', '')
            else:
                raise Exception("Réponse Bedrock vide")
                
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            
            if error_code == 'ThrottlingException' and attempt < max_retries:
                # Backoff V1 exact
                delay = 0.5 * (2 ** attempt) + random.uniform(0, 0.1)
                logger.warning(f"Throttling - retry dans {delay:.2f}s")
                time.sleep(delay)
                continue
            else:
                # Échec immédiat pour autres erreurs
                raise Exception(f"Erreur Bedrock {error_code}: {str(e)}")
    
    raise Exception("Échec après tous les retries")
```

### 2.3 Configuration Bedrock Simplifiée

**Principe V1 :** Configuration minimale et robuste
- Région par défaut us-east-1
- Modèle depuis variable d'environnement
- Pas de sur-configuration

**Application V2 :**
```python
class BedrockClientV1Style:
    def __init__(self, model_id: str = None, region: str = None):
        # Style V1 : valeurs par défaut robustes
        self.region = region or os.environ.get('BEDROCK_REGION', 'us-east-1')
        configured_model = model_id or os.environ.get('BEDROCK_MODEL_ID')
        
        # Fallback automatique sur modèle fonctionnel
        self.model_id = get_working_bedrock_model(configured_model)
        
        # Client simple
        self.client = boto3.client('bedrock-runtime', region_name=self.region)
        
        logger.info(f"Bedrock client V1-style: {self.model_id} @ {self.region}")
```

---

## 3. Corrections Prioritaires V2

### 3.1 P0 - Modèle Bedrock (CRITIQUE)

**Problème :** Modèle configuré nécessite inference profile
**Solution V1 :** Fallback automatique sur modèle fonctionnel
**Status :** ✅ Corrigé dans le code local

### 3.2 P0 - Format d'Appel (OK)

**Problème :** Format d'appel Bedrock
**Solution V1 :** Format identique déjà utilisé
**Status :** ✅ Pas de problème

### 3.3 P1 - Gestion d'Erreurs (AMÉLIORATION)

**Problème :** Gestion d'erreurs moins robuste que V1
**Solution V1 :** Adopter la stratégie de retry V1
**Status :** ⚠️ Partiellement corrigé

### 3.4 P1 - Variables d'Environnement (CONFIGURATION)

**Problème :** Modèle configuré non fonctionnel
**Solution V1 :** Changer la variable d'environnement
**Status :** 🔄 En cours (Alternative 2)

---

## 4. Plan d'Application Immédiat

### 4.1 Solution Immédiate (5 min)

**Changer la variable d'environnement BEDROCK_MODEL_ID :**
```bash
# De (problématique)
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0

# Vers (fonctionnel)
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
```

### 4.2 Solution Durable (30 min)

**Déployer le code corrigé avec fallback automatique :**
- Fallback intégré dans BedrockNormalizationClient
- Gestion d'erreurs améliorée style V1
- Retry robuste avec backoff

### 4.3 Solution Optimale (1h)

**Créer inference profile pour le modèle original :**
```bash
aws bedrock create-inference-profile \
  --inference-profile-name "lai-sonnet-profile" \
  --model-source "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0"
```

---

## 5. Métriques de Validation

### 5.1 Avant Application (État Actuel)
- Succès Bedrock : 0%
- Items matchés : 0/15
- Temps d'exécution : 51.8s
- Erreur : "Paramètres Bedrock invalides"

### 5.2 Après Application (Attendu)
- Succès Bedrock : > 90%
- Items matchés : > 5/15
- Temps d'exécution : < 20s
- Erreur : Aucune

---

## 6. Conclusion

Les bonnes pratiques V1 identifiées sont :

1. **Fallback automatique** sur modèle fonctionnel
2. **Gestion d'erreurs robuste** avec retry intelligent
3. **Configuration simple** avec valeurs par défaut sûres
4. **Parsing réponse cohérent** avec validation

La solution immédiate (changement variable d'environnement) devrait résoudre 90% du problème en utilisant directement un modèle fonctionnel testé.