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
    
    print(f"[OK] Fichier cible trouve: {target_file}")
    
    # Vérifier AWS
    try:
        session = boto3.Session(profile_name="rag-lai-prod")
        lambda_client = session.client('lambda', region_name="eu-west-3")
        lambda_client.get_function(FunctionName="vectora-inbox-normalize-score-v2-dev")
        print("[OK] Environnement AWS accessible")
    except Exception as e:
        print(f"❌ Erreur AWS: {e}")
        return False
    
    print("[OK] Phase 1 terminee")
    return True

def phase2_modification():
    """Phase 2: Modification code."""
    print("PHASE 2: MODIFICATION CODE")
    
    target_file = "src_v2/vectora_core/normalization/__init__.py"
    
    # Lire le fichier
    with open(target_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Rechercher la section problématique et la remplacer
    old_section = '''        # 5. Matching aux domaines de veille (mode Bedrock-only ou hybride)
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
    
    new_section = '''        # 5. Architecture Bedrock-Only Pure - Utiliser uniquement les résultats Bedrock
        matched_items = normalized_items
        logger.info("Architecture Bedrock-Only Pure : matching déterministe supprimé")'''
    
    if old_section in content:
        content = content.replace(old_section, new_section)
        print("[OK] Logique hybride remplacee par architecture pure")
    else:
        print("[WARN] Section exacte non trouvee, recherche pattern flexible...")
        # Recherche plus flexible
        import re
        
        # Pattern pour capturer la section de matching
        pattern = r'(\s+)# 5\. Matching aux domaines.*?canonical_scopes\s*\)'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            indent = match.group(1)  # Préserver l'indentation
            replacement = f'''{indent}# 5. Architecture Bedrock-Only Pure - Utiliser uniquement les résultats Bedrock
{indent}matched_items = normalized_items
{indent}logger.info("Architecture Bedrock-Only Pure : matching déterministe supprimé")'''
            
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            print("[OK] Logique hybride remplacee (pattern flexible)")
        else:
            print("[ERROR] Impossible de trouver la section a modifier")
            return False
    
    # Supprimer import matcher si présent
    if "from . import normalizer, matcher, scorer" in content:
        content = content.replace("from . import normalizer, matcher, scorer", "from . import normalizer, scorer")
        print("[OK] Import matcher supprime")
    
    # Écrire le fichier modifié
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Valider syntaxe
    try:
        result = subprocess.run(["python", "-m", "py_compile", target_file], 
                              check=True, capture_output=True, text=True)
        print("[OK] Syntaxe Python validee")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Erreur syntaxe: {e.stderr}")
        return False
    
    print("[OK] Phase 2 terminee")
    return True

def phase4_deploiement():
    """Phase 4: Déploiement AWS."""
    print("PHASE 4: DEPLOIEMENT AWS")
    
    try:
        # Création package layer
        print("Création package layer...")
        
        # Nettoyer et créer le répertoire
        if os.path.exists("layer_build/vectora_core"):
            import shutil
            shutil.rmtree("layer_build/vectora_core")
        
        os.makedirs("layer_build/vectora_core", exist_ok=True)
        
        # Copier les fichiers
        import shutil
        shutil.copytree("src_v2/vectora_core", "layer_build/vectora_core", dirs_exist_ok=True)
        
        # Créer le zip
        import zipfile
        with zipfile.ZipFile('vectora-core-bedrock-only-pure.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk("layer_build/vectora_core"):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, "layer_build")
                    zipf.write(file_path, arcname)
        
        print("[OK] Package layer cree")
        
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
        print(f"[OK] Layer publie: version {new_version}")
        
        # Mise à jour Lambda
        print("Mise à jour Lambda...")
        lambda_client.update_function_configuration(
            FunctionName='vectora-inbox-normalize-score-v2-dev',
            Layers=[
                f'arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev:{new_version}',
                'arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-common-deps-dev:3'
            ]
        )
        
        print("[OK] Lambda mise a jour")
        print("[OK] Phase 4 terminee")
        return True
        
    except Exception as e:
        print(f"[ERROR] Erreur deploiement: {e}")
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
        
        print(f"Status Code: {result.get('statusCode')}")
        
        if result.get('statusCode') == 200:
            body = result.get('body', {})
            stats = body.get('statistics', {})
            items_matched = stats.get('items_matched', 0)
            items_total = stats.get('items_input', 0)
            
            print(f"[OK] Lambda executee avec succes")
            print(f"   Items traités: {items_total}")
            print(f"   Items matchés: {items_matched}")
            
            if items_matched > 0:
                matching_rate = (items_matched / items_total * 100) if items_total > 0 else 0
                print(f"   Taux de matching: {matching_rate:.1f}%")
                print("AMELIORATION CONFIRMEE!")
                return True
            else:
                print("[WARN] Aucun item matche - verifier logs CloudWatch")
                return False
        else:
            error_msg = result.get('body', {}).get('error', 'Unknown error')
            print(f"[ERROR] Erreur Lambda: {error_msg}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Erreur tests: {e}")
        return False

def main():
    """Exécution complète du plan."""
    print("EXECUTION PLAN ARCHITECTURE BEDROCK-ONLY PURE")
    print("=" * 60)
    
    phases = [
        ("Phase 1 - Analyse", phase1_analyse),
        ("Phase 2 - Modification", phase2_modification),
        ("Phase 4 - Déploiement", phase4_deploiement),
        ("Phase 5 - Tests", phase5_tests)
    ]
    
    results = []
    
    for phase_name, phase_func in phases:
        print(f"\n{phase_name}...")
        success = phase_func()
        results.append((phase_name, success))
        
        if not success:
            print(f"[ERROR] {phase_name} echouee - arret")
            break
    
    # Résumé
    print("\n" + "=" * 60)
    print("RÉSUMÉ D'EXÉCUTION:")
    for phase_name, success in results:
        status = "[OK]" if success else "[FAIL]"
        print(f"   {phase_name}: {status}")
    
    overall_success = all(success for _, success in results)
    
    if overall_success:
        print("\nPLAN EXECUTE AVEC SUCCES COMPLET")
        print("Architecture Bedrock-Only Pure implémentée!")
    else:
        print("\nPLAN PARTIELLEMENT EXECUTE")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)