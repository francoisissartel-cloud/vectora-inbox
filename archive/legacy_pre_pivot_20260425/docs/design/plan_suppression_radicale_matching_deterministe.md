# Plan de Suppression Radicale du Matching Déterministe

**Date :** 19 décembre 2025  
**Objectif :** Supprimer physiquement tout le système de matching déterministe  
**Statut :** 🚀 PLAN D'EXÉCUTION IMMÉDIAT  
**Conformité :** Règles vectora-inbox-development-rules.md

---

## 🎯 OBJECTIF

**SUPPRIMER RADICALEMENT** toute trace du matching déterministe au profit du matching Bedrock uniquement.

**Problème identifié :** 4 jours d'échecs car nous modifions la **logique de choix** entre deux systèmes au lieu de **supprimer physiquement** l'un des deux systèmes.

**Résultat attendu :** Amélioration du taux de matching de 0% à 60-80% en 30 minutes.

---

## 🔍 ANALYSE DU PROBLÈME RACINE

### Erreur Fondamentale des 4 Derniers Jours

**❌ CE QUE NOUS FAISIONS (INCORRECT) :**
- Modifier la condition `if bedrock_only` 
- Changer la configuration client
- Contourner le matching déterministe
- **RÉSULTAT :** Les deux systèmes continuent d'exister et de se battre

**✅ CE QUE NOUS DEVONS FAIRE (CORRECT) :**
- Supprimer physiquement l'import de `matcher`
- Supprimer physiquement tous les appels à `matcher.match_items_to_domains()`
- Supprimer physiquement toute logique de fallback
- **RÉSULTAT :** Un seul système de matching (Bedrock)

### Architecture Actuelle Conflictuelle

```
Normalisation Bedrock → matching_results dans normalized_items
         ↓
Logique de choix (if bedrock_only)
         ↓
Matching déterministe → ÉCRASE les résultats Bedrock
         ↓
matched_items = résultats écrasés (0 items matchés)
```

### Architecture Cible Pure

```
Normalisation Bedrock → matching_results dans normalized_items
         ↓
matched_items = normalized_items (DIRECT)
         ↓
Résultats Bedrock préservés (60-80% matching)
```

---

## 📋 PLAN D'EXÉCUTION PAR PHASES

### PHASE 1 : ANALYSE ET PRÉPARATION (5 minutes)

**Objectif :** Identifier tous les éléments à supprimer physiquement

**Actions :**
1. **Localiser le code à supprimer**
   - Import : `from . import normalizer, matcher, scorer`
   - Logique hybride complète (lignes ~105-115)
   - Tous les appels à `matcher.match_items_to_domains()`

2. **Valider l'environnement AWS**
   - Profil : `rag-lai-prod`
   - Lambda cible : `vectora-inbox-normalize-score-v2-dev`

**Critères de succès :**
- [ ] Code à supprimer identifié précisément
- [ ] Environnement AWS accessible
- [ ] Stratégie de suppression définie

---

### PHASE 2 : SUPPRESSION RADICALE (5 minutes)

**Objectif :** Supprimer physiquement tout le système déterministe

**Fichier cible :** `src_v2/vectora_core/normalization/__init__.py`

**SUPPRESSION 1 - Import matcher :**
```python
# AVANT (ligne ~11)
from . import normalizer, matcher, scorer

# APRÈS
from . import normalizer, scorer
```

**SUPPRESSION 2 - Logique hybride complète :**
```python
# AVANT (lignes ~105-115) - SUPPRIMER ENTIÈREMENT
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

# APRÈS - REMPLACER PAR
# 5. Architecture Bedrock-Only Pure - Matching déterministe supprimé
matched_items = normalized_items
logger.info("Architecture Bedrock-Only Pure : matching déterministe supprimé")
```

**Actions :**
1. **Supprimer l'import de matcher**
2. **Supprimer toute la logique hybride (10 lignes)**
3. **Remplacer par assignation directe (2 lignes)**
4. **Valider syntaxe Python**

**Critères de succès :**
- [ ] Import matcher supprimé
- [ ] Logique hybride supprimée (10 lignes → 2 lignes)
- [ ] Syntaxe Python valide
- [ ] Aucune référence à matcher restante

---

### PHASE 3 : VALIDATION LOCALE (5 minutes)

**Objectif :** Valider que la suppression est complète et fonctionnelle

**Actions :**
1. **Test d'import**
   ```python
   from src_v2.vectora_core.normalization import run_normalize_score_for_client
   ```

2. **Test de syntaxe**
   ```bash
   python -m py_compile src_v2/vectora_core/normalization/__init__.py
   ```

3. **Vérification suppression complète**
   ```bash
   # Vérifier qu'aucune référence à matcher ne reste
   findstr /s "matcher" src_v2\vectora_core\normalization\__init__.py
   ```

**Critères de succès :**
- [ ] Import réussi
- [ ] Compilation Python OK
- [ ] Aucune référence à matcher trouvée
- [ ] Logique simplifiée validée

---

### PHASE 4 : DÉPLOIEMENT AWS (10 minutes)

**Objectif :** Déployer la suppression sur AWS

**Actions :**
1. **Création du package layer**
   ```bash
   cd layer_build
   rmdir /s /q vectora_core 2>nul
   mkdir vectora_core
   xcopy /s /e /y ..\src_v2\vectora_core vectora_core\
   cd ..
   powershell Compress-Archive -Path layer_build\vectora_core -DestinationPath vectora-core-matching-supprime.zip -Force
   ```

2. **Publication layer**
   ```bash
   aws lambda publish-layer-version --layer-name vectora-inbox-vectora-core-dev --zip-file fileb://vectora-core-matching-supprime.zip --profile rag-lai-prod
   ```

3. **Mise à jour Lambda**
   ```bash
   aws lambda update-function-configuration --function-name vectora-inbox-normalize-score-v2-dev --layers arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev:XX arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-common-deps-dev:3 --profile rag-lai-prod
   ```

**Critères de succès :**
- [ ] Layer publié (nouvelle version)
- [ ] Lambda mise à jour avec nouveau layer
- [ ] Statut "Successful"
- [ ] Aucune erreur de déploiement

---

### PHASE 5 : TESTS DONNÉES RÉELLES (5 minutes)

**Objectif :** Valider que la suppression résout le problème de matching

**Actions :**
1. **Invocation Lambda**
   ```bash
   aws lambda invoke --function-name vectora-inbox-normalize-score-v2-dev --payload '{"client_id":"lai_weekly_v3","force_reprocess":true}' --profile rag-lai-prod response.json
   ```

2. **Analyse résultats**
   ```bash
   # Vérifier StatusCode: 200
   # Extraire items_matched depuis response.json
   type response.json | findstr "items_matched"
   ```

3. **Vérification logs CloudWatch**
   - **DOIT APPARAÎTRE :** "Architecture Bedrock-Only Pure : matching déterministe supprimé"
   - **NE DOIT PLUS APPARAÎTRE :** "Matching déterministe aux domaines de veille"
   - **NE DOIT PLUS APPARAÎTRE :** "Matching combiné: 0 items matchés"

**Critères de succès :**
- [ ] Lambda exécutée (StatusCode: 200)
- [ ] Log "Architecture Bedrock-Only Pure" présent
- [ ] Log "Matching déterministe" absent
- [ ] Items matchés > 0 (vs 0 actuellement)
- [ ] Amélioration confirmée

---

## 🎯 MÉTRIQUES DE SUCCÈS

### Métriques Techniques
- [ ] **Code simplifié** : 10 lignes → 2 lignes
- [ ] **Import supprimé** : `matcher` absent
- [ ] **Layer déployé** : Nouvelle version publiée
- [ ] **Lambda mise à jour** : Statut "Successful"

### Métriques Métier
- [ ] **Items matchés** : > 0 (vs 0 actuellement)
- [ ] **Taux de matching** : ≥ 60% (objectif 60-80%)
- [ ] **Matching Bedrock préservé** : Résultats non écrasés
- [ ] **Performance maintenue** : Temps d'exécution stable

### Métriques de Validation
- [ ] **Log confirmé** : "Architecture Bedrock-Only Pure"
- [ ] **Log absent** : "Matching déterministe aux domaines"
- [ ] **Log absent** : "Matching combiné: 0 items matchés"
- [ ] **Pas de régression** : Normalisation maintenue

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

## 🔧 SCRIPT D'EXÉCUTION

### Script Principal : `execute_suppression_matching_deterministe.py`

```python
#!/usr/bin/env python3
"""
Suppression radicale du matching déterministe.
"""

import os
import subprocess
import json
import boto3
import re

def phase1_analyse():
    """Phase 1: Analyse et préparation."""
    print("PHASE 1: ANALYSE ET PREPARATION")
    
    target_file = "src_v2/vectora_core/normalization/__init__.py"
    if not os.path.exists(target_file):
        print(f"ERREUR: {target_file} non trouvé")
        return False
    
    # Vérifier présence du code à supprimer
    with open(target_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "from . import normalizer, matcher, scorer" not in content:
        print("⚠️ Import matcher déjà supprimé")
    else:
        print("✅ Import matcher trouvé - à supprimer")
    
    if "matcher.match_items_to_domains" not in content:
        print("⚠️ Appel matcher déjà supprimé")
    else:
        print("✅ Appel matcher trouvé - à supprimer")
    
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

def phase2_suppression():
    """Phase 2: Suppression radicale."""
    print("PHASE 2: SUPPRESSION RADICALE")
    
    target_file = "src_v2/vectora_core/normalization/__init__.py"
    
    with open(target_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # SUPPRESSION 1: Import matcher
    if "from . import normalizer, matcher, scorer" in content:
        content = content.replace(
            "from . import normalizer, matcher, scorer",
            "from . import normalizer, scorer"
        )
        print("✅ Import matcher supprimé")
    
    # SUPPRESSION 2: Logique hybride complète
    # Pattern pour capturer toute la section de matching
    pattern = r'# 5\. .*?(?=\n        # [6-9]\.|$)'
    
    replacement = '''# 5. Architecture Bedrock-Only Pure - Matching déterministe supprimé
        matched_items = normalized_items
        logger.info("Architecture Bedrock-Only Pure : matching déterministe supprimé")'''
    
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        print("✅ Logique hybride supprimée")
    else:
        print("❌ Pattern de suppression non trouvé")
        return False
    
    # Écrire le fichier modifié
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Validation syntaxe
    try:
        subprocess.run(["python", "-m", "py_compile", target_file], check=True, capture_output=True)
        print("✅ Syntaxe Python validée")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur syntaxe: {e}")
        return False
    
    print("✅ Phase 2 terminée")
    return True

def phase3_validation():
    """Phase 3: Validation locale."""
    print("PHASE 3: VALIDATION LOCALE")
    
    target_file = "src_v2/vectora_core/normalization/__init__.py"
    
    # Test d'import
    try:
        import sys
        sys.path.insert(0, '.')
        from src_v2.vectora_core.normalization import run_normalize_score_for_client
        print("✅ Import réussi")
    except Exception as e:
        print(f"❌ Erreur import: {e}")
        return False
    
    # Vérifier suppression complète
    with open(target_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "matcher" in content:
        print("❌ Références à matcher encore présentes")
        return False
    else:
        print("✅ Aucune référence à matcher trouvée")
    
    print("✅ Phase 3 terminée")
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
            "cd ..; Compress-Archive -Path layer_build\\vectora_core -DestinationPath vectora-core-matching-supprime.zip -Force"
        ], check=True)
        
        # Publication layer
        print("Publication layer...")
        session = boto3.Session(profile_name="rag-lai-prod")
        lambda_client = session.client('lambda', region_name="eu-west-3")
        
        with open('vectora-core-matching-supprime.zip', 'rb') as f:
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
                print("🎉 SUPPRESSION RÉUSSIE - MATCHING BEDROCK FONCTIONNEL!")
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
    print("🚀 SUPPRESSION RADICALE DU MATCHING DÉTERMINISTE")
    print("=" * 60)
    
    phases = [
        ("Phase 1 - Analyse", phase1_analyse),
        ("Phase 2 - Suppression", phase2_suppression),
        ("Phase 3 - Validation", phase3_validation),
        ("Phase 4 - Déploiement", phase4_deploiement),
        ("Phase 5 - Tests", phase5_tests)
    ]
    
    for phase_name, phase_func in phases:
        print(f"\n{phase_name}...")
        if not phase_func():
            print(f"❌ {phase_name} échouée - arrêt")
            return False
    
    print("\n" + "=" * 60)
    print("🎉 SUPPRESSION RADICALE RÉUSSIE")
    print("Matching déterministe supprimé - Matching Bedrock fonctionnel!")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
```

---

## 🎯 RÉSUMÉ EXÉCUTIF

### Problème Résolu
- **4 jours d'échecs** dus à une erreur de compréhension architecturale
- **Modification de la logique de choix** au lieu de **suppression physique**
- **Conflit permanent** entre matching Bedrock et déterministe

### Solution Appliquée
- **Suppression radicale** de tout le système déterministe
- **Préservation exclusive** du matching Bedrock
- **Simplification du code** : 10 lignes → 2 lignes

### Impact Attendu
- **Taux de matching** : 0% → 60-80%
- **Architecture** : Hybride conflictuelle → Bedrock-Only pure
- **Maintenance** : Code simplifié et prévisible

### Durée d'Exécution
- **Total** : 30 minutes
- **Risque** : Très faible (simplification)
- **Rollback** : Immédiat si nécessaire

---

## 🚀 COMMANDE D'EXÉCUTION

```bash
python execute_suppression_matching_deterministe.py
```

---

*Plan de Suppression Radicale du Matching Déterministe*  
*Date : 19 décembre 2025*  
*Statut : 🚀 PRÊT POUR EXÉCUTION IMMÉDIATE*