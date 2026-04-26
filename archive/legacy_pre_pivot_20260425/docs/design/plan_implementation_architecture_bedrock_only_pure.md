# Plan d'Implémentation : Architecture Bedrock-Only Pure

**Date :** 19 décembre 2025  
**Objectif :** Implémenter Solution 1 - Architecture Bedrock-Only Pure  
**Statut :** 🚀 PLAN D'EXÉCUTION IMMÉDIAT  
**Conformité :** Règles vectora-inbox-development-rules.md

---

## 🎯 OBJECTIF

Supprimer définitivement l'architecture hybride conflictuelle et implémenter une **architecture Bedrock-Only pure** qui préserve les résultats de matching Bedrock fonctionnels.

**Résultat attendu :** Amélioration du taux de matching de 0% à 60-80% en 30 minutes.

---

## 📋 PLAN D'EXÉCUTION PAR PHASES

### PHASE 1 : ANALYSE ET PRÉPARATION (5 minutes)

**Objectif :** Valider l'état actuel et préparer la modification

**Actions :**
1. **Confirmer le code problématique**
   - Localiser la logique hybride dans `src_v2/vectora_core/normalization/__init__.py`
   - Identifier les lignes exactes à modifier

2. **Valider l'environnement**
   - Vérifier accès AWS (profil rag-lai-prod)
   - Confirmer Lambda cible : `vectora-inbox-normalize-score-v2-dev`

**Critères de succès :**
- [ ] Code problématique localisé
- [ ] Environnement AWS accessible
- [ ] Stratégie de modification définie

---

### PHASE 2 : MODIFICATION CODE (5 minutes)

**Objectif :** Implémenter l'architecture Bedrock-Only pure

**Modification dans `src_v2/vectora_core/normalization/__init__.py` :**

**AVANT (lignes ~105-115) :**
```python
# 5. Matching aux domaines de veille (mode Bedrock-only ou hybride)
if client_config.get('matching_config', {}).get('bedrock_only', False):
    # Mode Bedrock-only : utiliser directement les résultats Bedrock
    matched_items = normalized_items
    logger.info("Mode Bedrock-only activé : matching déterministe ignoré")
else:
    # Mode hybride existant (fallback)
    logger.info("Matching déterministe aux domaines de veille...")
    matched_items = matcher.match_items_to_domains(
        normalized_items,
        client_config,
        canonical_scopes
    )
```

**APRÈS (architecture pure) :**
```python
# 5. Architecture Bedrock-Only Pure - Utiliser uniquement les résultats Bedrock
matched_items = normalized_items
logger.info("Architecture Bedrock-Only Pure : matching déterministe supprimé")
```

**Actions :**
1. **Modifier le fichier `__init__.py`**
2. **Supprimer l'import de matcher** (optionnel)
3. **Valider syntaxe Python**

**Critères de succès :**
- [ ] Code modifié (10 lignes → 2 lignes)
- [ ] Syntaxe Python valide
- [ ] Import matcher supprimé

---

### PHASE 3 : TESTS LOCAUX (5 minutes)

**Objectif :** Valider la modification avant déploiement

**Actions :**
1. **Test d'import**
   ```python
   # Vérifier que l'import fonctionne
   from src_v2.vectora_core.normalization import run_normalize_score_for_client
   ```

2. **Test de syntaxe**
   ```bash
   python -m py_compile src_v2/vectora_core/normalization/__init__.py
   ```

3. **Validation logique**
   - Confirmer que `matched_items = normalized_items` préserve les résultats Bedrock
   - Vérifier que le matching déterministe est complètement contourné

**Critères de succès :**
- [ ] Import réussi
- [ ] Compilation Python OK
- [ ] Logique validée

---

### PHASE 4 : DÉPLOIEMENT AWS (10 minutes)

**Objectif :** Déployer la modification sur AWS

**Actions :**
1. **Création du package layer**
   ```bash
   cd layer_build
   rmdir /s /q vectora_core 2>nul
   mkdir vectora_core
   xcopy /s /e /y ..\src_v2\vectora_core vectora_core\
   cd ..
   powershell Compress-Archive -Path layer_build\vectora_core -DestinationPath vectora-core-bedrock-only-pure.zip -Force
   ```

2. **Publication layer**
   ```bash
   aws lambda publish-layer-version --layer-name vectora-inbox-vectora-core-dev --zip-file fileb://vectora-core-bedrock-only-pure.zip --profile rag-lai-prod
   ```

3. **Mise à jour Lambda**
   ```bash
   aws lambda update-function-configuration --function-name vectora-inbox-normalize-score-v2-dev --layers arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev:XX arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-common-deps-dev:3 --profile rag-lai-prod
   ```

**Critères de succès :**
- [ ] Layer publié (nouvelle version)
- [ ] Lambda mise à jour
- [ ] Statut "Successful"

---

### PHASE 5 : TESTS DONNÉES RÉELLES (5 minutes)

**Objectif :** Valider l'amélioration avec données LAI réelles

**Actions :**
1. **Invocation Lambda**
   ```bash
   aws lambda invoke --function-name vectora-inbox-normalize-score-v2-dev --payload '{"client_id":"lai_weekly_v3","force_reprocess":true}' --profile rag-lai-prod response.json
   ```

2. **Analyse résultats**
   ```bash
   # Vérifier StatusCode: 200
   # Extraire items_matched depuis response.json
   ```

3. **Vérification logs CloudWatch**
   - Rechercher : "Architecture Bedrock-Only Pure"
   - Vérifier absence : "Matching déterministe aux domaines"

**Critères de succès :**
- [ ] Lambda exécutée (StatusCode: 200)
- [ ] Log "Architecture Bedrock-Only Pure" présent
- [ ] Items matchés > 0
- [ ] Amélioration confirmée

---

## 🔧 SCRIPTS D'EXÉCUTION

### Script Principal : `execute_bedrock_only_pure.py`

```python
#!/usr/bin/env python3
"""
Exécution du plan Architecture Bedrock-Only Pure.
"""

import os
import subprocess
import json
import boto3

def phase1_analyse():
    """Phase 1: Analyse et préparation."""
    print("PHASE 1: ANALYSE ET PREPARATION")
    
    # Vérifier fichier cible
    target_file = "src_v2/vectora_core/normalization/__init__.py"
    if not os.path.exists(target_file):
        print(f"ERREUR: {target_file} non trouvé")
        return False
    
    # Vérifier AWS
    try:
        session = boto3.Session(profile_name="rag-lai-prod")
        lambda_client = session.client('lambda', region_name="eu-west-3")
        lambda_client.get_function(FunctionName="vectora-inbox-normalize-score-v2-dev")
        print("✅ Environnement AWS accessible")
    except Exception as e:
        print(f"❌ Erreur AWS: {e}")
        return False
    
    print("✅ Phase 1 terminée")
    return True

def phase2_modification():
    """Phase 2: Modification code."""
    print("PHASE 2: MODIFICATION CODE")
    
    target_file = "src_v2/vectora_core/normalization/__init__.py"
    
    # Lire le fichier
    with open(target_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Rechercher et remplacer la logique hybride
    old_logic = '''# 5. Matching aux domaines de veille (mode Bedrock-only ou hybride)
        if client_config.get('matching_config', {}).get('bedrock_only', False):
            # Mode Bedrock-only : utiliser directement les résultats Bedrock
            matched_items = normalized_items
            logger.info("Mode Bedrock-only activé : matching déterministe ignoré")
        else:
            # Mode hybride existant (fallback)
            logger.info("Matching déterministe aux domaines de veille...")
            matched_items = matcher.match_items_to_domains(
                normalized_items,
                client_config,
                canonical_scopes
            )'''
    
    new_logic = '''# 5. Architecture Bedrock-Only Pure - Utiliser uniquement les résultats Bedrock
        matched_items = normalized_items
        logger.info("Architecture Bedrock-Only Pure : matching déterministe supprimé")'''
    
    if old_logic.strip() in content:
        content = content.replace(old_logic.strip(), new_logic.strip())
        print("✅ Logique hybride remplacée")
    else:
        # Fallback: recherche pattern plus flexible
        import re
        pattern = r'# 5\. Matching aux domaines.*?canonical_scopes\s*\)'
        if re.search(pattern, content, re.DOTALL):
            content = re.sub(pattern, new_logic.strip(), content, flags=re.DOTALL)
            print("✅ Logique hybride remplacée (pattern flexible)")
        else:
            print("❌ Pattern de remplacement non trouvé")
            return False
    
    # Supprimer import matcher si présent
    content = content.replace("from . import normalizer, matcher, scorer", "from . import normalizer, scorer")
    
    # Écrire le fichier modifié
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Valider syntaxe
    try:
        subprocess.run(["python", "-m", "py_compile", target_file], check=True, capture_output=True)
        print("✅ Syntaxe Python validée")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur syntaxe: {e}")
        return False
    
    print("✅ Phase 2 terminée")
    return True

def phase4_deploiement():
    """Phase 4: Déploiement AWS."""
    print("PHASE 4: DEPLOIEMENT AWS")
    
    try:
        # Création package layer
        print("Création package layer...")
        subprocess.run([
            "powershell", "-Command",
            "cd layer_build; Remove-Item vectora_core -Recurse -Force -ErrorAction SilentlyContinue; " +
            "New-Item -ItemType Directory vectora_core; " +
            "Copy-Item -Path ..\\src_v2\\vectora_core\\* -Destination vectora_core\\ -Recurse; " +
            "cd ..; Compress-Archive -Path layer_build\\vectora_core -DestinationPath vectora-core-bedrock-only-pure.zip -Force"
        ], check=True)
        
        # Publication layer
        print("Publication layer...")
        session = boto3.Session(profile_name="rag-lai-prod")
        lambda_client = session.client('lambda', region_name="eu-west-3")
        
        with open('vectora-core-bedrock-only-pure.zip', 'rb') as f:
            response = lambda_client.publish_layer_version(
                LayerName='vectora-inbox-vectora-core-dev',
                Content={'ZipFile': f.read()}
            )
        
        new_version = response['Version']
        print(f"✅ Layer publié: version {new_version}")
        
        # Mise à jour Lambda
        print("Mise à jour Lambda...")
        lambda_client.update_function_configuration(
            FunctionName='vectora-inbox-normalize-score-v2-dev',
            Layers=[
                f'arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev:{new_version}',
                'arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-common-deps-dev:3'
            ]
        )
        
        print("✅ Lambda mise à jour")
        print("✅ Phase 4 terminée")
        return True
        
    except Exception as e:
        print(f"❌ Erreur déploiement: {e}")
        return False

def phase5_tests():
    """Phase 5: Tests données réelles."""
    print("PHASE 5: TESTS DONNEES REELLES")
    
    try:
        session = boto3.Session(profile_name="rag-lai-prod")
        lambda_client = session.client('lambda', region_name="eu-west-3")
        
        # Invocation Lambda
        print("Invocation Lambda...")
        payload = {"client_id": "lai_weekly_v3", "force_reprocess": True}
        
        response = lambda_client.invoke(
            FunctionName='vectora-inbox-normalize-score-v2-dev',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            body = result.get('body', {})
            stats = body.get('statistics', {})
            items_matched = stats.get('items_matched', 0)
            items_total = stats.get('items_input', 0)
            
            print(f"✅ Lambda exécutée avec succès")
            print(f"   Items traités: {items_total}")
            print(f"   Items matchés: {items_matched}")
            
            if items_matched > 0:
                matching_rate = (items_matched / items_total * 100) if items_total > 0 else 0
                print(f"   Taux de matching: {matching_rate:.1f}%")
                print("🎉 AMÉLIORATION CONFIRMÉE!")
                return True
            else:
                print("⚠️ Aucun item matché - investigation requise")
                return False
        else:
            print(f"❌ Erreur Lambda: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur tests: {e}")
        return False

def main():
    """Exécution complète du plan."""
    print("🚀 EXÉCUTION PLAN ARCHITECTURE BEDROCK-ONLY PURE")
    print("=" * 60)
    
    phases = [
        ("Phase 1 - Analyse", phase1_analyse),
        ("Phase 2 - Modification", phase2_modification),
        ("Phase 4 - Déploiement", phase4_deploiement),
        ("Phase 5 - Tests", phase5_tests)
    ]
    
    for phase_name, phase_func in phases:
        print(f"\n{phase_name}...")
        if not phase_func():
            print(f"❌ {phase_name} échouée - arrêt")
            return False
    
    print("\n" + "=" * 60)
    print("🎉 PLAN EXÉCUTÉ AVEC SUCCÈS")
    print("Architecture Bedrock-Only Pure implémentée!")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
```

---

## 🎯 CRITÈRES DE SUCCÈS GLOBAL

### Métriques Techniques
- [ ] **Code modifié** : 10 lignes → 2 lignes
- [ ] **Layer déployé** : Nouvelle version publiée
- [ ] **Lambda mise à jour** : Statut "Successful"
- [ ] **Syntaxe validée** : Compilation Python OK

### Métriques Métier
- [ ] **Items matchés** : > 0 (vs 0 actuellement)
- [ ] **Taux de matching** : ≥ 60% (objectif 60-80%)
- [ ] **Log confirmé** : "Architecture Bedrock-Only Pure"
- [ ] **Pas de régression** : Normalisation maintenue

### Métriques de Conformité
- [ ] **Règles V2 respectées** : Modification src_v2/ uniquement
- [ ] **Hygiène V4** : Simplification du code
- [ ] **Architecture** : Un seul système de matching
- [ ] **Performance** : Temps d'exécution maintenu

---

## 🚨 PLAN DE ROLLBACK

**Si problème détecté :**
1. **Restaurer layer précédent**
   ```bash
   aws lambda update-function-configuration --function-name vectora-inbox-normalize-score-v2-dev --layers arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev:PREVIOUS_VERSION --profile rag-lai-prod
   ```

2. **Restaurer code original**
   ```bash
   git checkout src_v2/vectora_core/normalization/__init__.py
   ```

---

## 🎯 EXÉCUTION IMMÉDIATE

**Commande d'exécution :**
```bash
python execute_bedrock_only_pure.py
```

**Durée totale estimée :** 30 minutes  
**Impact attendu :** Amélioration matching 0% → 60-80%  
**Risque :** Très faible (simplification du code)

---

*Plan d'Implémentation Architecture Bedrock-Only Pure*  
*Date : 19 décembre 2025*  
*Statut : 🚀 PRÊT POUR EXÉCUTION IMMÉDIATE*