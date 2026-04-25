"""
Script de construction de la layer vectora-core avec fix aplatissement scopes
"""

import os
import shutil
import zipfile
from datetime import datetime

def build_vectora_core_layer():
    """Construit la layer vectora-core avec le fix d'aplatissement"""
    
    print("=== Construction Layer vectora-core avec Fix Scopes ===")
    
    # Configuration
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    layer_name = f"vectora-core-scopes-fix-{timestamp}"
    build_dir = "layer_build"
    output_dir = "output/lambda_packages"
    
    # Nettoyage
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Build directory: {build_dir}")
    print(f"Layer name: {layer_name}")
    
    # Copie du code source vectora_core
    src_path = "src_v2/vectora_core"
    dest_path = os.path.join(build_dir, "vectora_core")
    
    if not os.path.exists(src_path):
        print(f"ERREUR: Source path not found: {src_path}")
        return None
    
    print(f"Copie de {src_path} vers {dest_path}")
    shutil.copytree(src_path, dest_path)
    
    # Validation de la structure
    print("\nValidation structure layer:")
    for root, dirs, files in os.walk(dest_path):
        level = root.replace(dest_path, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            if file.endswith('.py'):
                print(f"{subindent}{file}")
    
    # Vérification du fix dans config_loader.py
    config_loader_path = os.path.join(dest_path, "shared", "config_loader.py")
    if os.path.exists(config_loader_path):
        with open(config_loader_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if "flattened_scopes" in content:
                print("OK - Fix d'aplatissement detecte dans config_loader.py")
            else:
                print("ERREUR - Fix d'aplatissement NON detecte dans config_loader.py")
                return None
    else:
        print(f"ERREUR - config_loader.py non trouve: {config_loader_path}")
        return None
    
    # Création du zip
    zip_path = os.path.join(output_dir, f"{layer_name}.zip")
    print(f"\nCréation du zip: {zip_path}")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(build_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arc_path = os.path.relpath(file_path, build_dir)
                zipf.write(file_path, arc_path)
                print(f"  Ajouté: {arc_path}")
    
    # Validation du zip
    zip_size = os.path.getsize(zip_path)
    zip_size_mb = zip_size / (1024 * 1024)
    
    print(f"\n=== Résultats ===")
    print(f"Layer créée: {zip_path}")
    print(f"Taille: {zip_size_mb:.2f} MB")
    
    if zip_size_mb > 50:
        print("ATTENTION: Taille > 50MB (limite AWS Lambda Layer)")
        return None
    else:
        print("OK - Taille acceptable pour AWS Lambda Layer")
    
    # Test d'import
    print("\nTest d'import:")
    import sys
    sys.path.insert(0, dest_path)
    
    try:
        from shared.config_loader import load_canonical_scopes
        print("OK - Import load_canonical_scopes reussi")
        
        from normalization.matcher import match_items_to_domains
        print("OK - Import match_items_to_domains reussi")
        
        print("OK - Tous les imports critiques reussis")
        
    except ImportError as e:
        print(f"ERREUR - Erreur d'import: {e}")
        return None
    finally:
        sys.path.remove(dest_path)
    
    print(f"\nSUCCESS - Layer vectora-core construite avec succes!")
    print(f"Fichier: {zip_path}")
    
    return zip_path

if __name__ == "__main__":
    zip_path = build_vectora_core_layer()
    if zip_path:
        print(f"\nSUCCESS: Layer prête pour déploiement")
        print(f"Commande AWS CLI:")
        print(f"aws lambda publish-layer-version \\")
        print(f"  --layer-name vectora-inbox-vectora-core-dev \\")
        print(f"  --description 'Fix aplatissement scopes complexes - lai_keywords matching' \\")
        print(f"  --zip-file fileb://{zip_path} \\")
        print(f"  --compatible-runtimes python3.11 \\")
        print(f"  --region eu-west-3 \\")
        print(f"  --profile rag-lai-prod")
    else:
        print("FAILED: Erreur lors de la construction")