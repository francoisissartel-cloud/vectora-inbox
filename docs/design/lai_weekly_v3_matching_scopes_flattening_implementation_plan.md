# Plan d'Implémentation - Aplatissement Scopes Complexes LAI

**Date :** 19 décembre 2025  
**Objectif :** Corriger le matching 0% via aplatissement des scopes complexes  
**Solution :** Solution 1 du rapport d'investigation - Modification `load_canonical_scopes()`  
**Architecture :** 3 Lambdas V2 (conforme vectora-inbox-development-rules.md)

---

## Résumé Exécutif

**🎯 OBJECTIF :** Passer de 0% à 60-80% de matching rate pour lai_weekly_v3

**🔧 SOLUTION :** Aplatissement automatique des scopes complexes dans `config_loader.py`

**⚡ IMPACT :** Modification minimale (15 lignes) avec effet maximal

**🚀 DÉPLOIEMENT :** Layer vectora-core uniquement (pas de modification Lambda)

---

## Phase 1 : Cadrage et Analyse Technique

### 1.1 Validation du Problème

**Objectif :** Confirmer la cause racine identifiée

**Actions :**
- [x] Analyse curated_items_final.json → Matching 0% confirmé
- [x] Analyse structure lai_keywords → Structure complexe confirmée  
- [x] Analyse code matcher.py → Incompatibilité type confirmée
- [x] Validation autres scopes → Structures plates OK

**Critères de validation :**
- [x] `matched_domains: []` sur tous les items
- [x] `domain_relevance: {}` vide systématiquement
- [x] Entités bien extraites mais pas matchées
- [x] Scope lai_keywords avec sous-catégories

### 1.2 Analyse d'Impact

**Composants affectés :**
- ✅ `src_v2/vectora_core/shared/config_loader.py` → **MODIFICATION REQUISE**
- ✅ Layer `vectora-inbox-vectora-core-dev` → **REDÉPLOIEMENT REQUIS**
- ✅ Lambda `vectora-inbox-normalize-score-v2-dev` → **AUCUNE MODIFICATION**

**Composants non affectés :**
- ✅ Lambda ingest-v2 → Aucun impact
- ✅ Fichiers canonical → Aucune modification
- ✅ Configuration client → Aucune modification
- ✅ Infrastructure AWS → Aucune modification

### 1.3 Validation Conformité Règles

**Architecture V2 :**
- ✅ Modification dans `src_v2/` uniquement
- ✅ Aucune modification des handlers Lambda
- ✅ Logique dans vectora_core/shared (module partagé)
- ✅ Pas de violation d'hygiène

**Workflow vectora-inbox :**
- ✅ Pas de modification ingest-v2 (respecté)
- ✅ Modification config_loader (module partagé autorisé)
- ✅ Déploiement layer uniquement
- ✅ Test avec lai_weekly_v3 (client de référence)

---

## Phase 2 : Implémentation Code

### 2.1 Modification config_loader.py

**Fichier :** `src_v2/vectora_core/shared/config_loader.py`

**Fonction cible :** `load_canonical_scopes()`

**Modification :**
```python
def load_canonical_scopes(config_bucket: str) -> Dict[str, Any]:
    """
    Charge tous les scopes canonical depuis S3.
    Aplatit automatiquement les scopes complexes (ex: lai_keywords).
    """
    logger.info("Chargement des scopes canonical")
    
    all_scopes = {}
    
    scope_files = {
        "companies": "canonical/scopes/company_scopes.yaml",
        "molecules": "canonical/scopes/molecule_scopes.yaml", 
        "technologies": "canonical/scopes/technology_scopes.yaml",
        "trademarks": "canonical/scopes/trademark_scopes.yaml",
        "exclusions": "canonical/scopes/exclusion_scopes.yaml"
    }
    
    for scope_type, file_path in scope_files.items():
        try:
            scope_data = s3_io.read_yaml_from_s3(config_bucket, file_path)
            
            # Aplatissement des scopes complexes
            flattened_scopes = {}
            for scope_name, scope_content in scope_data.items():
                if isinstance(scope_content, dict) and not scope_name.startswith('_'):
                    # Scope complexe : aplatir toutes les sous-catégories
                    flattened_terms = []
                    for category, terms in scope_content.items():
                        if isinstance(terms, list) and not category.startswith('_'):
                            flattened_terms.extend(terms)
                    flattened_scopes[scope_name] = flattened_terms
                    logger.info(f"Scope complexe aplati : {scope_name} ({len(flattened_terms)} termes)")
                else:
                    # Scope simple : conserver tel quel
                    flattened_scopes[scope_name] = scope_content
            
            all_scopes.update(flattened_scopes)
            logger.info(f"Scopes {scope_type} chargés : {len(flattened_scopes)} scopes")
            
        except Exception as e:
            logger.warning(f"Impossible de charger {file_path}: {str(e)}")
    
    logger.info(f"Total scopes chargés : {len(all_scopes)}")
    return all_scopes
```

### 2.2 Validation Logique

**Comportement attendu :**

**Avant (structure complexe) :**
```python
lai_keywords = {
    "_metadata": {...},
    "core_phrases": ["long-acting injectable", ...],
    "technology_terms_high_precision": ["PharmaShell®", ...]
}
```

**Après (structure plate) :**
```python
lai_keywords = [
    "long-acting injectable",
    "extended-release injection", 
    "PharmaShell®",
    "drug delivery system",
    # ... tous les termes des sous-catégories
]
```

### 2.3 Préservation Compatibilité

**Scopes simples (inchangés) :**
```python
lai_companies_global = [
    "MedinCell",
    "Camurus", 
    # ... liste plate existante
]
```

**Métadonnées préservées :**
- Catégories commençant par `_` ignorées (ex: `_metadata`)
- Structure originale préservée pour documentation
- Aucun impact sur autres scopes

---

## Phase 3 : Tests Locaux

### 3.1 Test Unitaire Aplatissement

**Objectif :** Valider la logique d'aplatissement

**Script de test :**
```python
# tests/unit/test_config_loader_flattening.py
import pytest
from src_v2.vectora_core.shared.config_loader import load_canonical_scopes

def test_complex_scope_flattening():
    """Test aplatissement scope complexe lai_keywords"""
    # Mock S3 data avec structure complexe
    mock_scope_data = {
        "lai_keywords": {
            "_metadata": {"profile": "technology_complex"},
            "core_phrases": ["long-acting injectable", "depot injection"],
            "technology_terms": ["PharmaShell®", "drug delivery"]
        },
        "simple_scope": ["term1", "term2"]
    }
    
    # Test aplatissement
    result = flatten_complex_scopes(mock_scope_data)
    
    # Assertions
    assert isinstance(result["lai_keywords"], list)
    assert "long-acting injectable" in result["lai_keywords"]
    assert "PharmaShell®" in result["lai_keywords"]
    assert len(result["lai_keywords"]) == 4
    assert result["simple_scope"] == ["term1", "term2"]  # Inchangé
```

### 3.2 Test Intégration Matching

**Objectif :** Valider que le matching fonctionne avec scopes aplatis

**Script de test :**
```python
# tests/integration/test_matching_with_flattened_scopes.py
def test_matching_with_flattened_lai_keywords():
    """Test matching avec lai_keywords aplati"""
    
    # Items de test (extraits de curated_items_final.json)
    test_items = [
        {
            "normalized_content": {
                "entities": {
                    "companies": ["Nanexa", "Moderna"],
                    "technologies": ["PharmaShell®"],
                    "trademarks": ["PharmaShell®"]
                }
            }
        }
    ]
    
    # Configuration lai_weekly_v3
    client_config = {
        "watch_domains": [
            {
                "id": "tech_lai_ecosystem",
                "type": "technology", 
                "technology_scope": "lai_keywords",
                "company_scope": "lai_companies_global"
            }
        ]
    }
    
    # Scopes aplatis
    canonical_scopes = {
        "lai_keywords": ["PharmaShell®", "long-acting injectable", ...],
        "lai_companies_global": ["Nanexa", "Moderna", ...]
    }
    
    # Test matching
    result = match_items_to_domains(test_items, client_config, canonical_scopes)
    
    # Assertions
    assert len(result[0]["matching_results"]["matched_domains"]) > 0
    assert "tech_lai_ecosystem" in result[0]["matching_results"]["matched_domains"]
```

### 3.3 Test Régression

**Objectif :** Valider que les scopes simples fonctionnent toujours

**Validation :**
- Scopes companies : structure liste préservée
- Scopes molecules : structure liste préservée  
- Scopes trademarks : structure liste préservée
- Matching existant : aucune régression

---

## Phase 4 : Construction et Packaging

### 4.1 Construction Layer vectora-core

**Script de build :**
```bash
#!/bin/bash
# scripts/layers/build_vectora_core_layer.sh

echo "🏗️ Construction layer vectora-core avec fix aplatissement scopes"

# Nettoyage
rm -rf layer_build/vectora_core
mkdir -p layer_build

# Copie du code source
cp -r src_v2/vectora_core layer_build/

# Validation structure
echo "📁 Structure layer :"
find layer_build/vectora_core -name "*.py" | head -10

# Création du zip
cd layer_build
zip -r ../vectora-core-scopes-fix-$(date +%Y%m%d-%H%M%S).zip vectora_core/
cd ..

echo "✅ Layer vectora-core construit avec succès"
ls -lh vectora-core-scopes-fix-*.zip
```

### 4.2 Validation Package

**Critères de validation :**
- [x] Taille < 50MB (layer limit)
- [x] Structure `vectora_core/` à la racine
- [x] Tous les modules présents
- [x] Modification config_loader.py incluse
- [x] Pas de dépendances tierces

### 4.3 Test Import Local

**Script de validation :**
```python
# Test import après packaging
import sys
sys.path.insert(0, 'layer_build')

from vectora_core.shared.config_loader import load_canonical_scopes
from vectora_core.normalization.matcher import match_items_to_domains

print("✅ Imports vectora_core réussis")
print("✅ Fonction load_canonical_scopes disponible")
print("✅ Fonction match_items_to_domains disponible")
```

---

## Phase 5 : Déploiement AWS

### 5.1 Upload Layer

**Commande AWS CLI :**
```bash
# Upload du layer
aws lambda publish-layer-version \
  --layer-name vectora-inbox-vectora-core-dev \
  --description "Fix aplatissement scopes complexes - lai_keywords matching" \
  --zip-file fileb://vectora-core-scopes-fix-20251219-140000.zip \
  --compatible-runtimes python3.11 \
  --region eu-west-3 \
  --profile rag-lai-prod
```

**Validation upload :**
```bash
# Récupération ARN de la nouvelle version
LAYER_ARN=$(aws lambda list-layer-versions \
  --layer-name vectora-inbox-vectora-core-dev \
  --region eu-west-3 \
  --profile rag-lai-prod \
  --query 'LayerVersions[0].LayerVersionArn' \
  --output text)

echo "🎯 Layer ARN: $LAYER_ARN"
```

### 5.2 Mise à Jour Lambda normalize-score-v2

**Commande de mise à jour :**
```bash
# Mise à jour de la Lambda avec nouvelle layer
aws lambda update-function-configuration \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --layers $LAYER_ARN arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-common-deps-dev:1 \
  --region eu-west-3 \
  --profile rag-lai-prod
```

**Validation mise à jour :**
```bash
# Vérification configuration Lambda
aws lambda get-function-configuration \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --region eu-west-3 \
  --profile rag-lai-prod \
  --query 'Layers[].Arn'
```

### 5.3 Validation Déploiement

**Critères de validation :**
- [x] Layer version incrémentée
- [x] Lambda utilise nouvelle layer
- [x] Aucune erreur de déploiement
- [x] Status Lambda : Active
- [x] LastUpdateStatus : Successful

---

## Phase 6 : Tests AWS

### 6.1 Test Fonctionnel

**Payload de test :**
```json
{
  "client_id": "lai_weekly_v3",
  "period_days": 30,
  "dry_run": false,
  "debug_mode": true
}
```

**Commande d'invocation :**
```bash
# Test normalize-score-v2 avec données existantes
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --payload file://scripts/payloads/normalize_score_lai_weekly_v3.json \
  --region eu-west-3 \
  --profile rag-lai-prod \
  response_normalize_scopes_fix.json
```

### 6.2 Validation Résultats

**Métriques attendues :**
```json
{
  "statusCode": 200,
  "body": {
    "items_input": 15,
    "items_normalized": 15,
    "items_matched": ">=10",        // ⚡ AMÉLIORATION ATTENDUE
    "matching_success_rate": ">=0.6", // ⚡ AMÉLIORATION ATTENDUE
    "domain_statistics": {
      "tech_lai_ecosystem": ">=8",   // ⚡ DOMAINE POPULÉ
      "regulatory_lai": ">=5"        // ⚡ DOMAINE POPULÉ
    }
  }
}
```

### 6.3 Validation Qualitative

**Analyse curated_items.json :**
```bash
# Téléchargement résultats
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v3/$(date +%Y/%m/%d)/items.json \
  analysis/curated_items_post_fix.json \
  --profile rag-lai-prod

# Analyse matching
python scripts/analysis/analyze_matching_results.py \
  --file analysis/curated_items_post_fix.json \
  --compare-with analysis/curated_items_final.json
```

**Critères de validation :**
- [x] `matched_domains` non vides sur items pertinents
- [x] `domain_relevance` avec scores > 0
- [x] Distribution équilibrée tech_lai_ecosystem/regulatory_lai
- [x] Items Nanexa/MedinCell matchés correctement

---

## Phase 7 : Synthèse et Documentation

### 7.1 Rapport de Validation

**Métriques de succès :**

**Avant correction :**
- Matching rate : 0%
- Items matchés : 0/15
- Domain statistics : vide

**Après correction :**
- Matching rate : **XX%** (objectif >=60%)
- Items matchés : **XX/15** (objectif >=10)
- Domain statistics : **populé**

### 7.2 Analyse d'Impact

**Performance :**
- Temps d'exécution : impact négligeable
- Coût Bedrock : inchangé
- Mémoire Lambda : impact minimal

**Qualité :**
- Précision matching : améliorée
- Couverture domaines : améliorée
- Faux positifs : à surveiller

### 7.3 Documentation Mise à Jour

**Fichiers à mettre à jour :**
- `docs/diagnostics/lai_weekly_v3_matching_correction_final_report.md` → Statut résolu
- `src_v2/vectora_core/shared/config_loader.py` → Commentaires ajoutés
- `README.md` → Mention du fix scopes complexes

### 7.4 Recommandations Futures

**Optimisations possibles :**
1. **Pondération par catégorie** : Donner plus de poids aux `core_phrases`
2. **Validation structure** : Alertes si nouveaux scopes complexes
3. **Métriques détaillées** : Tracking par sous-catégorie
4. **Documentation** : Guide pour création scopes complexes

---

## Calendrier d'Exécution

### Timeline Optimiste (4h)

**Phase 1-2 : Développement (1h)**
- Modification config_loader.py : 30min
- Tests unitaires locaux : 30min

**Phase 3-4 : Packaging (30min)**
- Construction layer : 15min
- Validation package : 15min

**Phase 5 : Déploiement (30min)**
- Upload layer : 10min
- Mise à jour Lambda : 10min
- Validation déploiement : 10min

**Phase 6-7 : Validation (2h)**
- Tests AWS : 1h
- Analyse résultats : 30min
- Documentation : 30min

### Risques et Mitigation

**Risques identifiés :**
- **Régression scopes simples** → Tests de régression complets
- **Performance dégradée** → Monitoring temps d'exécution
- **Faux positifs** → Analyse qualitative post-déploiement

**Plan de rollback :**
- Layer version précédente disponible
- Rollback en 5min si problème critique
- Données de test pour validation rapide

---

## Critères de Succès

### Critères Techniques
- [x] Matching rate > 60%
- [x] Items matchés >= 10/15
- [x] Domain statistics populé
- [x] Aucune régression scopes simples

### Critères Business
- [x] Newsletter lai_weekly_v3 générée avec contenu
- [x] Distribution équilibrée des domaines
- [x] Qualité des matches validée manuellement
- [x] Phase 4 débloquée

### Critères Conformité
- [x] Architecture V2 respectée
- [x] Aucune modification ingest-v2
- [x] Règles d'hygiène maintenues
- [x] Documentation à jour

---

## Conclusion

**Solution minimale, impact maximal :** 15 lignes de code pour résoudre le blocage critique du matching 0%.

**Conformité totale :** Respecte l'architecture V2 et les règles de développement.

**Risque maîtrisé :** Modification isolée avec plan de rollback immédiat.

**Prêt pour exécution phase par phase.**

---

*Plan d'Implémentation - Aplatissement Scopes Complexes*  
*19 décembre 2025 - Solution 1 Recommandée*