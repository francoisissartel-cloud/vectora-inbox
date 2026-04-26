# Plan de Correction : Matching Bedrock dans normalize_score_v2

**Date :** 17 décembre 2025  
**Objectif :** Corriger l'erreur d'import `_call_bedrock_with_retry` dans le matching Bedrock V2  
**Durée estimée :** 2h15 (7 phases de 15-30 min chacune)  
**Environnement :** eu-west-3, profil rag-lai-prod, compte 786469175371

---

## 1. Rappel du contexte

### 1.1 Situation actuelle
- **normalize_score_v2** : Normalisation et scoring fonctionnels (15/15 items traités)
- **Matching Bedrock** : 0% d'items matchés aux domaines `tech_lai_ecosystem` et `regulatory_lai`
- **Erreur critique** : `cannot import name '_call_bedrock_with_retry' from 'vectora_core.normalization.bedrock_client'`
- **Impact métier** : Newsletter vide malgré des scores élevés (jusqu'à 13.8)

### 1.2 Architecture V2 validée
- **Workflow** : `vectora-inbox-ingest-v2` → `vectora-inbox-normalize-score-v2` → newsletter
- **Code existant** : `src_v2/vectora_core/normalization/` avec bedrock_client.py et bedrock_matcher.py
- **Référence V1** : `/src/vectora_core/normalization/bedrock_client.py` avec fonction `_call_bedrock_with_retry` fonctionnelle

### 1.3 Problème technique identifié
Le module `bedrock_matcher.py` V2 tente d'importer `_call_bedrock_with_retry` depuis `bedrock_client.py` V2, mais cette fonction n'existe pas dans la version V2. Elle existe uniquement dans la V1 qui fonctionne.

---

## 2. Phase 1 – Audit du code Bedrock V1 vs V2

### 2.1 Fichiers à analyser

**V2 (architecture cible)** :
- `src_v2/vectora_core/normalization/bedrock_client.py` - Client Bedrock V2 (incomplet)
- `src_v2/vectora_core/normalization/bedrock_matcher.py` - Module matching V2 (import cassé)
- `src_v2/vectora_core/normalization/normalizer.py` - Orchestrateur normalisation V2

**V1 (référence fonctionnelle)** :
- `src/vectora_core/normalization/bedrock_client.py` - Client Bedrock V1 (fonctionnel)
- `src/lambdas/ingest_normalize/handler.py` - Handler V1 (référence config)

### 2.2 Différences à documenter

**Appels Bedrock V1 (fonctionnel)** :
- Fonction `_call_bedrock_with_retry()` avec gestion ThrottlingException
- Région par défaut : `us-east-1` (variable `BEDROCK_REGION`)
- Modèle : `anthropic.claude-3-sonnet-20240229-v1:0` (variable `BEDROCK_MODEL_ID`)
- Retry : 3 tentatives avec backoff exponentiel + jitter
- Client : `boto3.client('bedrock-runtime', region_name=region)`

**Appels Bedrock V2 (incomplet)** :
- Classe `BedrockNormalizationClient` avec méthode `normalize_item()`
- Fonction `_call_bedrock_with_retry_v1()` (nom différent, non exportée)
- Import cassé dans `bedrock_matcher.py` : `from .bedrock_client import _call_bedrock_with_retry`

### 2.3 Configuration Bedrock validée V1
- **Région** : `us-east-1` (observée dans le code V1)
- **Modèle** : `anthropic.claude-3-sonnet-20240229-v1:0` (utilisé avec succès)
- **ARN complet** : Géré automatiquement par boto3
- **Timeout** : Géré par les retries (3 tentatives max)

---

## 3. Phase 2 – Design d'une API Bedrock unique dans bedrock_client.py

### 3.1 API proposée : Fonction unifiée

**Choix architectural** : Fonction simple plutôt que classe pour respecter les règles d'hygiène V4

```python
def call_bedrock_with_retry(
    model_id: str,
    request_body: Dict[str, Any],
    max_retries: int = 3,
    base_delay: float = 0.5
) -> str:
    """
    Appelle Bedrock avec retry automatique (API unifiée V2).
    
    Args:
        model_id: Identifiant du modèle Bedrock
        request_body: Corps de la requête (format Claude Messages API)
        max_retries: Nombre maximum de tentatives
        base_delay: Délai de base pour le backoff
    
    Returns:
        Texte de réponse de Bedrock
    """
```

### 3.2 Fonctions support à exposer

**Fonctions publiques** (utilisables par normalizer.py et bedrock_matcher.py) :
- `call_bedrock_with_retry()` - API principale unifiée
- `get_bedrock_client()` - Factory client boto3

**Fonctions privées** (internes au module) :
- `_parse_bedrock_response()` - Parsing JSON avec fallback
- `_create_fallback_result()` - Structure vide en cas d'erreur

### 3.3 Gestion des paramètres

**Variables d'environnement** (alignées sur V1) :
- `BEDROCK_REGION` : Région Bedrock (défaut: `us-east-1`)
- `BEDROCK_MODEL_ID` : Modèle à utiliser (défaut: `anthropic.claude-3-sonnet-20240229-v1:0`)

**Paramètres de retry** (alignés sur V1) :
- `max_retries` : 3 tentatives (défaut V1)
- `base_delay` : 0.5s (défaut V1)
- Backoff exponentiel : `base_delay * (2 ** attempt) + jitter`

---

## 4. Phase 3 – Implémentation dans src_v2/vectora_core/normalization/bedrock_client.py

### 4.1 Modifications à apporter

**Ajout de la fonction manquante** :
- Copier `_call_bedrock_with_retry()` depuis V1 vers V2
- Renommer en `call_bedrock_with_retry()` (sans underscore pour export public)
- Conserver exactement la même logique de retry et gestion d'erreurs

**Factorisation de duplication** :
- Supprimer `_call_bedrock_with_retry_v1()` (doublon)
- Utiliser la nouvelle fonction unifiée dans `BedrockNormalizationClient`
- Maintenir la compatibilité avec `normalize_item()`

### 4.2 Code à implémenter

```python
# Fonction principale à ajouter
def call_bedrock_with_retry(model_id: str, request_body: Dict[str, Any], 
                           max_retries: int = 3, base_delay: float = 0.5) -> str:
    # COPIE EXACTE de la logique V1 fonctionnelle
    
# Mise à jour de la classe existante
class BedrockNormalizationClient:
    def normalize_item(self, ...):
        # Utiliser call_bedrock_with_retry() au lieu de _call_bedrock_with_retry_v1()
```

### 4.3 Respect des règles d'hygiène

**Conformité src_lambda_hygiene_v4.md** :
- Aucune nouvelle dépendance externe
- Aucun script dans `/src`
- Réutilisation de l'infrastructure boto3 existante
- Code simple et testable (< 80 lignes par fonction)

---

## 5. Phase 4 – Adaptation de bedrock_matcher.py (et éventuellement normalizer.py)

### 5.1 Correction de l'import cassé

**Problème actuel** :
```python
# bedrock_matcher.py ligne ~95
from .bedrock_client import _call_bedrock_with_retry  # ❌ FONCTION INEXISTANTE
```

**Solution** :
```python
# bedrock_matcher.py ligne ~95
from .bedrock_client import call_bedrock_with_retry  # ✅ FONCTION PUBLIQUE
```

### 5.2 Adaptation de la fonction _call_bedrock_matching()

**Code actuel** (ligne ~95 de bedrock_matcher.py) :
```python
def _call_bedrock_matching(prompt: str, bedrock_model_id: str, bedrock_region: str) -> str:
    from .bedrock_client import _call_bedrock_with_retry  # ❌ IMPORT CASSÉ
    # ...
    return _call_bedrock_with_retry(bedrock_model_id, request_body)  # ❌ APPEL CASSÉ
```

**Code corrigé** :
```python
def _call_bedrock_matching(prompt: str, bedrock_model_id: str, bedrock_region: str) -> str:
    from .bedrock_client import call_bedrock_with_retry  # ✅ IMPORT CORRIGÉ
    # ...
    return call_bedrock_with_retry(bedrock_model_id, request_body)  # ✅ APPEL CORRIGÉ
```

### 5.3 Vérification de normalizer.py

**Vérifier si normalizer.py utilise aussi bedrock_client** :
- Contrôler les imports depuis bedrock_client
- S'assurer de la compatibilité avec la nouvelle API
- Maintenir la logique d'orchestration existante

---

## 6. Phase 5 – Tests locaux (sans polluer /src)

### 6.1 Tests d'import et de structure

**Script de test** : `scripts/test_bedrock_matching_local.py`
```python
# Test 1 : Vérifier que l'import fonctionne
from src_v2.vectora_core.normalization.bedrock_matcher import match_watch_domains_with_bedrock

# Test 2 : Vérifier que la fonction call_bedrock_with_retry existe
from src_v2.vectora_core.normalization.bedrock_client import call_bedrock_with_retry

# Test 3 : Simuler un appel matching (sans vraie requête Bedrock)
```

### 6.2 Tests avec données MVP

**Données de test** : Items du lai_weekly_v3 (dernière exécution ingest)
- Item MedinCell + Teva + olanzapine LAI (score 13.8)
- Item UZEDY® (trademark LAI)
- Watch_domains : `tech_lai_ecosystem`, `regulatory_lai`

**Validation attendue** :
- Appel Bedrock réussi (pas d'erreur d'import)
- Réponse JSON parsée correctement
- Au moins 1 domaine matché pour les items LAI pertinents

### 6.3 Métriques de test

**Coût estimé** :
- ~800 tokens par item (prompt + réponse)
- 15 items MVP × 800 tokens = 12,000 tokens
- Coût : ~$0.036 par run complet

**Latence estimée** :
- 1-2 secondes par appel Bedrock
- 15 items × 2s = 30 secondes max (séquentiel)
- Parallélisation possible en Phase 6

---

## 7. Phase 6 – Déploiement AWS + tests réels

### 7.1 Plan de déploiement

**Lambda cible** : `vectora-inbox-normalize-score-v2`
- **Région** : eu-west-3
- **Profil** : rag-lai-prod
- **Compte** : 786469175371

**Commandes de déploiement** :
```bash
# 1. Package du code V2 corrigé
python scripts/package_normalize_score_v2.py

# 2. Déploiement via AWS CLI
aws lambda update-function-code \
  --function-name vectora-inbox-normalize-score-v2 \
  --zip-file fileb://normalize-score-v2-YYYYMMDD-HHMMSS.zip \
  --region eu-west-3 --profile rag-lai-prod

# 3. Mise à jour des variables d'environnement si nécessaire
aws lambda update-function-configuration \
  --function-name vectora-inbox-normalize-score-v2 \
  --environment Variables='{
    "BEDROCK_REGION":"us-east-1",
    "BEDROCK_MODEL_ID":"anthropic.claude-3-sonnet-20240229-v1:0"
  }' \
  --region eu-west-3 --profile rag-lai-prod
```

### 7.2 Tests réels après déploiement

**Déclenchement de la Lambda** :
```bash
# Test avec le dernier run ingest lai_weekly_v3
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2 \
  --payload '{"client_id":"lai_weekly_v3","period_days":30}' \
  --region eu-west-3 --profile rag-lai-prod \
  response.json
```

**Collecte des logs CloudWatch** :
```bash
# Logs de la Lambda normalize-score-v2
aws logs filter-log-events \
  --log-group-name /aws/lambda/vectora-inbox-normalize-score-v2 \
  --start-time $(date -d '5 minutes ago' +%s)000 \
  --region eu-west-3 --profile rag-lai-prod
```

### 7.3 Validation des résultats

**Métriques de succès** :
- Aucune erreur d'import `_call_bedrock_with_retry`
- Au moins 5/15 items matchés aux domaines LAI
- Temps d'exécution total < 2 minutes
- Aucune régression sur la normalisation (15/15 items traités)

---

## 8. Phase 7 – Rapport de diagnostic

### 8.1 Création du rapport final

**Fichier** : `docs/diagnostics/normalize_score_v2_matching_fix_report.md`

**Contenu obligatoire** :
- Nombre d'items normalisés vs matchés vs non matchés
- Exemples concrets de matching réussi (input → output Bedrock → domaine choisi)
- Comparaison avant/après correction (0% → X% de matching)
- Analyse de la qualité des résultats Bedrock

### 8.2 Métriques détaillées à collecter

**Statistiques de matching** :
- Items traités : X/15
- Items matchés tech_lai_ecosystem : X
- Items matchés regulatory_lai : X
- Items non matchés : X (avec raisons)

**Exemples de matching réussi** :
```json
{
  "item_title": "MedinCell's Partner Teva Pharmaceuticals Announces...",
  "bedrock_input": {
    "entities": ["MedinCell", "Teva", "olanzapine", "Extended-Release Injectable"]
  },
  "bedrock_output": {
    "matched_domains": ["tech_lai_ecosystem", "regulatory_lai"],
    "relevance_scores": {"tech_lai_ecosystem": 0.85, "regulatory_lai": 0.72}
  },
  "final_decision": "Matché aux 2 domaines"
}
```

### 8.3 Recommandations d'amélioration

**Optimisations techniques** :
- Parallélisation des appels Bedrock (ThreadPoolExecutor)
- Cache des réponses pour items similaires
- Seuils adaptatifs par domaine

**Optimisations métier** :
- Ajustement des prompts selon les patterns d'erreur
- Enrichissement des scopes canonical
- Monitoring des coûts Bedrock

**Optimisations coût** :
- Estimation du coût mensuel (X runs × $0.036)
- Comparaison coût/bénéfice vs matching déterministe
- Recommandations de fréquence optimale

---

## 9. Critères de succès et livrables

### 9.1 Critères techniques

**Correction de l'erreur** :
- ✅ Import `call_bedrock_with_retry` fonctionnel
- ✅ Aucune erreur lors de l'exécution de normalize_score_v2
- ✅ API Bedrock unifiée et réutilisable

**Performance** :
- ✅ Temps d'exécution total < 2 minutes
- ✅ Taux de succès Bedrock > 95%
- ✅ Aucune régression sur la normalisation

### 9.2 Critères métier

**Amélioration du matching** :
- ✅ Taux de matching > 0% (actuellement 0%)
- ✅ Items LAI pertinents matchés (MedinCell+Teva, UZEDY®)
- ✅ Domaines tech_lai_ecosystem et regulatory_lai alimentés

**Qualité des résultats** :
- ✅ Matching cohérent avec les entités détectées
- ✅ Scores de pertinence réalistes (0.4-1.0)
- ✅ Pas de faux positifs massifs

### 9.3 Livrables finaux

**Code mis à jour** :
- `src_v2/vectora_core/normalization/bedrock_client.py` - API unifiée
- `src_v2/vectora_core/normalization/bedrock_matcher.py` - Import corrigé
- `scripts/test_bedrock_matching_local.py` - Tests locaux

**Documentation** :
- `docs/design/bedrock_matching_v2_fix_plan.md` - Ce plan (✅)
- `docs/diagnostics/normalize_score_v2_matching_fix_report.md` - Rapport final

**Lambda fonctionnelle** :
- `vectora-inbox-normalize-score-v2` avec matching Bedrock actif
- Logs CloudWatch avec métriques de matching
- Données S3 `curated/` avec champs `bedrock_matched_domains`

---

## 10. Planning d'exécution

### 10.1 Séquencement des phases

| Phase | Durée | Dépendances | Livrables |
|-------|-------|-------------|-----------|
| 1. Audit V1 vs V2 | 15 min | - | Analyse comparative |
| 2. Design API | 15 min | Phase 1 | Spécification technique |
| 3. Implémentation | 30 min | Phase 2 | Code bedrock_client.py |
| 4. Adaptation matcher | 15 min | Phase 3 | Code bedrock_matcher.py |
| 5. Tests locaux | 30 min | Phase 4 | Script de validation |
| 6. Déploiement AWS | 20 min | Phase 5 | Lambda mise à jour |
| 7. Rapport final | 20 min | Phase 6 | Documentation complète |

**Durée totale** : 2h15 (135 minutes)

### 10.2 Points de validation

**Après Phase 3** : Import `call_bedrock_with_retry` réussi
**Après Phase 5** : Tests locaux sans erreur d'import
**Après Phase 6** : Matching > 0% en production
**Après Phase 7** : Documentation complète et métriques validées

---

## 11. Gestion des risques

### 11.1 Risques techniques identifiés

**Risque 1** : Régression sur la normalisation existante
- **Probabilité** : Faible (modification isolée du matching)
- **Impact** : Élevé (15 items non normalisés)
- **Mitigation** : Tests de non-régression en Phase 5

**Risque 2** : Coût Bedrock plus élevé que prévu
- **Probabilité** : Moyenne (double appel Bedrock)
- **Impact** : Faible ($0.036 par run)
- **Mitigation** : Monitoring des coûts en Phase 7

**Risque 3** : Latence trop élevée
- **Probabilité** : Moyenne (15 appels séquentiels)
- **Impact** : Moyen (timeout Lambda)
- **Mitigation** : Parallélisation en optimisation future

### 11.2 Plan de rollback

**Si échec en Phase 6** :
1. Restaurer la version précédente de la Lambda
2. Désactiver le matching Bedrock (feature flag)
3. Maintenir la normalisation fonctionnelle
4. Analyser les logs d'erreur pour correction

---

**Plan validé et prêt pour exécution**  
**Estimation** : 2h15 de travail concentré  
**Objectif** : Matching Bedrock fonctionnel dans normalize_score_v2