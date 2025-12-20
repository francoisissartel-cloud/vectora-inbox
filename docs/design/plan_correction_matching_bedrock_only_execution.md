# Plan de Correction Matching Bedrock-Only - Exécution Structurée

**Date :** 19 décembre 2025  
**Objectif :** Corriger le problème de matching Lambda via architecture Bedrock-only  
**Statut :** 🚀 PLAN D'EXÉCUTION STRUCTURÉ  
**Conformité :** Règles vectora-inbox-development-rules.md

---

## 🎯 CADRAGE GÉNÉRAL

### Problème Identifié
- **Flag `bedrock_only: true`** mal placé dans configuration (niveau racine vs `matching_config`)
- **Bedrock matching fonctionnel** (~20 matchings) mais écrasé par déterministe (0 résultat)
- **Taux de matching actuel :** 0% au lieu de 60-80% attendu

### Solution Architecturale
- **Architecture Bedrock-only** : Un seul système de matching intelligent
- **Configuration pilotée** : Correction structure YAML sans modification code
- **Respect règles V2** : Architecture 3 Lambdas, src_v2/, configuration canonique

### Métriques Cibles
- **Items matchés :** 0/15 → 9-12/15 (60-80%)
- **Temps exécution :** 104s → ~80s (-25%)
- **Qualité :** Matching intelligent Bedrock préservé

---

## 📋 PLAN D'EXÉCUTION PAR PHASES

### PHASE 1 : CADRAGE ET VALIDATION (5 minutes)

**Objectif :** Valider diagnostic et préparer correction

**Actions :**
1. **Vérification configuration actuelle**
   - Confirmer structure problématique dans `lai_weekly_v3.yaml`
   - Valider code existant dans `src_v2/vectora_core/normalization/__init__.py`

2. **Validation environnement AWS**
   - Profil : `rag-lai-prod`
   - Région : `eu-west-3`
   - Lambda : `vectora-inbox-normalize-score-v2-dev`

**Critères de succès :**
- [ ] Configuration problématique confirmée
- [ ] Code bedrock_only existant validé
- [ ] Environnement AWS accessible

---

### PHASE 2 : MODIFICATIONS CONFIGURATION (3 minutes)

**Objectif :** Corriger structure configuration YAML

**Actions :**
1. **Correction `lai_weekly_v3.yaml`**
   ```yaml
   # SUPPRESSION niveau racine
   # bedrock_only: true  # À supprimer
   
   # AJOUT sous matching_config
   matching_config:
     bedrock_only: true                  # NOUVEAU: Désactive matching déterministe
     min_domain_score: 0.20              # Optimisé pour Bedrock-only
     domain_type_thresholds:
       technology: 0.25                  # Abaissé de 0.30
       regulatory: 0.15                  # Abaissé de 0.20
     fallback_min_score: 0.10            # Très permissif pour pure players
   ```

2. **Validation syntaxe YAML**
   ```bash
   python -c "import yaml; yaml.safe_load(open('lai_weekly_v3.yaml'))"
   ```

**Critères de succès :**
- [ ] Flag `bedrock_only` sous `matching_config`
- [ ] Seuils optimisés pour Bedrock-only
- [ ] YAML syntaxiquement valide

---

### PHASE 3 : IMPLÉMENTATION ET TESTS LOCAUX (5 minutes)

**Objectif :** Valider correction avant déploiement

**Actions :**
1. **Test structure configuration**
   ```python
   # Script: test_config_structure.py
   import yaml
   with open('lai_weekly_v3.yaml', 'r') as f:
       config = yaml.safe_load(f)
   bedrock_only = config.get('matching_config', {}).get('bedrock_only')
   assert bedrock_only is True, f"bedrock_only = {bedrock_only}"
   print("✅ Configuration structure OK")
   ```

2. **Validation code existant**
   - Vérifier condition dans `__init__.py` ligne 85
   - Confirmer logique `client_config.get('matching_config', {}).get('bedrock_only', False)`

**Critères de succès :**
- [ ] Test configuration locale réussi
- [ ] Code existant compatible confirmé
- [ ] Aucune modification code requise

---

### PHASE 4 : DÉPLOIEMENT AWS (3 minutes)

**Objectif :** Déployer configuration corrigée sur AWS

**Actions :**
1. **Upload configuration S3**
   ```bash
   aws s3 cp lai_weekly_v3.yaml \
     s3://vectora-inbox-config-dev/clients/lai_weekly_v3.yaml \
     --profile rag-lai-prod \
     --region eu-west-3
   ```

2. **Validation upload**
   ```bash
   aws s3 ls s3://vectora-inbox-config-dev/clients/lai_weekly_v3.yaml \
     --profile rag-lai-prod
   ```

3. **Vérification configuration S3**
   ```bash
   aws s3 cp s3://vectora-inbox-config-dev/clients/lai_weekly_v3.yaml \
     lai_weekly_v3_from_s3.yaml --profile rag-lai-prod
   grep -A5 "matching_config:" lai_weekly_v3_from_s3.yaml
   ```

**Critères de succès :**
- [ ] Upload S3 réussi
- [ ] Configuration S3 = configuration locale
- [ ] Flag `bedrock_only: true` sous `matching_config` confirmé

---

### PHASE 5 : TESTS DONNÉES RÉELLES (10 minutes)

**Objectif :** Valider correction avec données réelles LAI

**Actions :**
1. **Invocation Lambda avec force_reprocess**
   ```bash
   # Payload test
   {
     "client_id": "lai_weekly_v3",
     "force_reprocess": true,
     "scoring_mode": "balanced"
   }
   ```

2. **Exécution et monitoring**
   ```bash
   aws lambda invoke \
     --function-name vectora-inbox-normalize-score-v2-dev \
     --payload '{"client_id":"lai_weekly_v3","force_reprocess":true}' \
     --profile rag-lai-prod \
     --region eu-west-3 \
     response.json
   ```

3. **Analyse logs CloudWatch**
   - Rechercher : "Mode Bedrock-only activé : matching déterministe ignoré"
   - Vérifier absence : "Matching déterministe aux domaines de veille"

**Critères de succès :**
- [ ] Lambda exécutée sans erreur (StatusCode: 200)
- [ ] Log "Mode Bedrock-only activé" présent
- [ ] Log "Matching déterministe" absent
- [ ] Items matchés > 0

---

### PHASE 6 : RETOUR SYNTHÈSE AVEC MÉTRIQUES (5 minutes)

**Objectif :** Documenter résultats et métriques d'amélioration

**Actions :**
1. **Collecte métriques**
   ```json
   {
     "items_processed": 15,
     "items_matched": "X",
     "matching_rate": "X%",
     "processing_time_ms": "X",
     "bedrock_calls": 30,
     "cost_estimate": "$0.XX"
   }
   ```

2. **Comparaison avant/après**
   | Métrique | Avant | Après | Amélioration |
   |----------|-------|-------|--------------|
   | Items matchés | 0/15 (0%) | X/15 (X%) | +X% |
   | Temps exécution | 104s | Xs | -X% |
   | Bedrock matching | Écrasé | Préservé | Corrigé |

3. **Validation items de référence**
   - Nanexa/Moderna Partnership → `tech_lai_ecosystem`
   - MedinCell/Teva NDA → `tech_lai_ecosystem` + `regulatory_lai`
   - Camurus Clinical Update → `tech_lai_ecosystem`

**Critères de succès :**
- [ ] Amélioration taux matching ≥ 60%
- [ ] Items LAI parfaits matchés
- [ ] Performance maintenue ou améliorée
- [ ] Documentation complète

---

## 🛠️ SCRIPTS D'EXÉCUTION

### Script Principal : `execute_bedrock_only_fix.py`

```python
#!/usr/bin/env python3
"""
Exécution automatisée du plan de correction bedrock_only.
Respecte les phases définies et génère rapport de synthèse.
"""

import yaml
import json
import boto3
import time
from datetime import datetime

def phase1_cadrage():
    """Phase 1: Cadrage et validation."""
    print("🎯 PHASE 1: CADRAGE ET VALIDATION")
    
    # Vérification configuration
    with open('lai_weekly_v3.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Diagnostic problème
    root_bedrock_only = config.get('bedrock_only')
    matching_bedrock_only = config.get('matching_config', {}).get('bedrock_only')
    
    print(f"   bedrock_only niveau racine: {root_bedrock_only}")
    print(f"   bedrock_only sous matching_config: {matching_bedrock_only}")
    
    if matching_bedrock_only is True:
        print("✅ Configuration déjà corrigée")
        return True
    elif root_bedrock_only is True:
        print("⚠️ Configuration à corriger (niveau racine)")
        return False
    else:
        print("❌ Flag bedrock_only manquant")
        return False

def phase2_modifications():
    """Phase 2: Modifications configuration."""
    print("🔧 PHASE 2: MODIFICATIONS CONFIGURATION")
    
    # La configuration est déjà corrigée dans lai_weekly_v3.yaml
    # Validation uniquement
    with open('lai_weekly_v3.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    bedrock_only = config.get('matching_config', {}).get('bedrock_only')
    if bedrock_only is True:
        print("✅ Configuration structure correcte")
        return True
    else:
        print("❌ Configuration structure incorrecte")
        return False

def phase4_deploiement():
    """Phase 4: Déploiement AWS."""
    print("🚀 PHASE 4: DÉPLOIEMENT AWS")
    
    try:
        session = boto3.Session(profile_name="rag-lai-prod")
        s3 = session.client('s3', region_name="eu-west-3")
        
        # Upload configuration
        s3.upload_file(
            'lai_weekly_v3.yaml',
            'vectora-inbox-config-dev',
            'clients/lai_weekly_v3.yaml'
        )
        print("✅ Configuration uploadée vers S3")
        return True
        
    except Exception as e:
        print(f"❌ Erreur déploiement: {e}")
        return False

def phase5_tests_donnees_reelles():
    """Phase 5: Tests données réelles."""
    print("🧪 PHASE 5: TESTS DONNÉES RÉELLES")
    
    try:
        session = boto3.Session(profile_name="rag-lai-prod")
        lambda_client = session.client('lambda', region_name="eu-west-3")
        
        # Payload test
        payload = {
            "client_id": "lai_weekly_v3",
            "force_reprocess": True,
            "scoring_mode": "balanced"
        }
        
        print("   Invocation Lambda...")
        start_time = time.time()
        
        response = lambda_client.invoke(
            FunctionName="vectora-inbox-normalize-score-v2-dev",
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        execution_time = time.time() - start_time
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            body = result.get('body', {})
            stats = body.get('statistics', {})
            
            items_matched = stats.get('items_matched', 0)
            items_total = stats.get('items_input', 15)
            matching_rate = (items_matched / items_total * 100) if items_total > 0 else 0
            
            print(f"✅ Lambda exécutée avec succès")
            print(f"   Items matchés: {items_matched}/{items_total} ({matching_rate:.1f}%)")
            print(f"   Temps d'exécution: {execution_time:.1f}s")
            
            return {
                'success': True,
                'items_matched': items_matched,
                'items_total': items_total,
                'matching_rate': matching_rate,
                'execution_time': execution_time,
                'processing_time_ms': body.get('processing_time_ms', 0)
            }
        else:
            print(f"❌ Erreur Lambda: {result}")
            return {'success': False}
            
    except Exception as e:
        print(f"❌ Erreur tests: {e}")
        return {'success': False}

def phase6_synthese(test_results):
    """Phase 6: Retour synthèse avec métriques."""
    print("📊 PHASE 6: RETOUR SYNTHÈSE AVEC MÉTRIQUES")
    
    if not test_results.get('success'):
        print("❌ Tests échoués - pas de métriques disponibles")
        return
    
    # Métriques avant/après
    metrics_before = {
        'items_matched': 0,
        'matching_rate': 0.0,
        'execution_time': 104.0
    }
    
    metrics_after = {
        'items_matched': test_results.get('items_matched', 0),
        'matching_rate': test_results.get('matching_rate', 0.0),
        'execution_time': test_results.get('execution_time', 0)
    }
    
    # Calcul améliorations
    improvement_rate = metrics_after['matching_rate'] - metrics_before['matching_rate']
    improvement_time = ((metrics_before['execution_time'] - metrics_after['execution_time']) / metrics_before['execution_time']) * 100
    
    print("\n📈 MÉTRIQUES D'AMÉLIORATION:")
    print(f"   Taux de matching: {metrics_before['matching_rate']:.1f}% → {metrics_after['matching_rate']:.1f}% (+{improvement_rate:.1f}%)")
    print(f"   Items matchés: {metrics_before['items_matched']} → {metrics_after['items_matched']}")
    print(f"   Temps d'exécution: {metrics_before['execution_time']:.1f}s → {metrics_after['execution_time']:.1f}s ({improvement_time:+.1f}%)")
    
    # Validation objectifs
    success_criteria = {
        'matching_rate_target': metrics_after['matching_rate'] >= 60.0,
        'items_matched_target': metrics_after['items_matched'] >= 9,
        'performance_maintained': metrics_after['execution_time'] <= 90.0
    }
    
    print("\n🎯 VALIDATION OBJECTIFS:")
    for criterion, met in success_criteria.items():
        status = "✅" if met else "❌"
        print(f"   {criterion}: {status}")
    
    overall_success = all(success_criteria.values())
    
    if overall_success:
        print("\n🎉 CORRECTION RÉUSSIE - Tous les objectifs atteints!")
    else:
        print("\n⚠️ CORRECTION PARTIELLE - Certains objectifs non atteints")
    
    return overall_success

def main():
    """Exécution complète du plan."""
    print("🚀 EXÉCUTION PLAN CORRECTION MATCHING BEDROCK-ONLY")
    print("=" * 60)
    
    # Phase 1: Cadrage
    if not phase1_cadrage():
        print("❌ Phase 1 échouée - arrêt")
        return False
    
    # Phase 2: Modifications
    if not phase2_modifications():
        print("❌ Phase 2 échouée - arrêt")
        return False
    
    # Phase 3: Tests locaux (implicite - configuration validée)
    print("✅ PHASE 3: TESTS LOCAUX (configuration validée)")
    
    # Phase 4: Déploiement
    if not phase4_deploiement():
        print("❌ Phase 4 échouée - arrêt")
        return False
    
    # Phase 5: Tests données réelles
    test_results = phase5_tests_donnees_reelles()
    
    # Phase 6: Synthèse
    success = phase6_synthese(test_results)
    
    print("=" * 60)
    if success:
        print("🎉 PLAN EXÉCUTÉ AVEC SUCCÈS")
    else:
        print("⚠️ PLAN PARTIELLEMENT EXÉCUTÉ")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
```

---

## 🎯 EXÉCUTION ET VALIDATION

### Commande d'Exécution
```bash
python execute_bedrock_only_fix.py
```

### Critères de Succès Global
- [ ] **Configuration corrigée** : Flag sous `matching_config`
- [ ] **Déploiement réussi** : Upload S3 sans erreur
- [ ] **Lambda fonctionnelle** : StatusCode 200
- [ ] **Amélioration confirmée** : Taux matching ≥ 60%
- [ ] **Performance maintenue** : Temps ≤ 90s

### Rollback si Nécessaire
```bash
# Restaurer configuration précédente
aws s3 cp lai_weekly_v3.yaml.backup \
  s3://vectora-inbox-config-dev/clients/lai_weekly_v3.yaml \
  --profile rag-lai-prod
```

---

*Plan de Correction Matching Bedrock-Only - Exécution Structurée*  
*Date : 19 décembre 2025*  
*Statut : 🚀 PRÊT POUR EXÉCUTION*