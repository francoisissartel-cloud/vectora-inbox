# Vectora Inbox Engine Lambda - Phase 2 Packaging

**Date** : 2025-12-11  
**Phase** : 2 - Préparation packaging ENGINE uniquement  
**Status** : ✅ TERMINÉ

---

## Script Packaging Créé

### Script Principal
**Fichier** : `scripts/package-engine-simple.ps1`

**Fonctionnalités** :
- Packaging ENGINE uniquement (pas de code ingest)
- Copie sélective des composants nécessaires
- Validation de l'intégrité du package
- Génération de `engine-only.zip` (17.4 MB)

### Contenu du Package

#### ✅ Code Engine
- `src/lambdas/engine/handler.py` : Handler spécifique engine
- `vectora_core/` : Logique métier commune (matching, scoring, newsletter)

#### ✅ Dépendances
- `boto3`, `botocore` : AWS SDK
- `requests`, `urllib3`, `certifi` : HTTP clients
- `feedparser`, `bs4` : Parsing HTML/RSS
- `yaml`, `dateutil` : Utilitaires
- Tous les `.dist-info` nécessaires

#### ❌ Code Exclu
- **Aucun code ingest** : `src/lambdas/ingest_normalize/` absent
- **Aucune dépendance ingest** : PUBMED_API_KEY_PARAM non nécessaire

---

## Validation Handler

### Handler Engine Confirmé
**Chemin** : `src.lambdas.engine.handler.lambda_handler`

**Fonctions** :
- Point d'entrée : `lambda_handler(event, context)`
- Appel métier : `run_engine_for_client()` depuis `vectora_core`
- Responsabilités : Matching, scoring, génération newsletter
- Variables d'environnement : CONFIG_BUCKET, DATA_BUCKET, NEWSLETTERS_BUCKET, BEDROCK_MODEL_ID

### Validation Code
```python
# Import correct depuis vectora_core
from vectora_core import run_engine_for_client

# Appel de la fonction engine
result = run_engine_for_client(
    client_id=client_id,
    period_days=period_days,
    from_date=from_date,
    to_date=to_date,
    target_date=target_date,
    env_vars=env_vars
)
```

---

## Tests de Validation

### ✅ Package Créé
- **Fichier** : `engine-only.zip`
- **Taille** : 17.4 MB (vs 18.3 MB actuel)
- **Réduction** : ~0.9 MB (code ingest supprimé)

### ✅ Handler Présent
- **Chemin dans ZIP** : `src/lambdas/engine/handler.py`
- **Fonction** : `lambda_handler` disponible
- **Import** : `vectora_core` accessible

### ✅ Dépendances Complètes
- Toutes les dépendances nécessaires pour l'engine
- Aucune dépendance spécifique à l'ingest
- Structure compatible AWS Lambda

---

## Comparaison Avant/Après

### Avant (Problématique)
```
Lambda engine-dev:
├── handler.py (MAUVAIS - handler générique)
├── src/lambdas/engine/handler.py (BON mais non utilisé)
├── src/lambdas/ingest_normalize/handler.py (MAUVAIS - code ingest)
└── vectora_core/

Handler configuré: handler.lambda_handler (INCORRECT)
```

### Après (Correct)
```
engine-only.zip:
├── src/lambdas/engine/handler.py (POINT D'ENTRÉE)
├── vectora_core/ (logique métier)
└── dependencies/ (AWS, HTTP, parsing)

Handler à configurer: src.lambdas.engine.handler.lambda_handler (CORRECT)
```

---

## Prochaines Étapes Phase 3

1. **Upload S3** : `s3://vectora-inbox-lambda-code-dev/lambda/engine/latest.zip`
2. **Update Lambda** : `aws lambda update-function-code`
3. **Update Handler** : `aws lambda update-function-configuration --handler src.lambdas.engine.handler.lambda_handler`
4. **Validation** : Timeout 900s maintenu

---

## Critères de Succès Phase 2 ✅

- [x] Script packaging engine opérationnel
- [x] Zip engine-only.zip généré avec bon contenu (17.4 MB)
- [x] Handler engine validé : `src.lambdas.engine.handler.lambda_handler`
- [x] Aucune dépendance vers le code ingest
- [x] Package prêt pour déploiement Phase 3

---

**Phase 2 terminée - Package ENGINE prêt pour déploiement**