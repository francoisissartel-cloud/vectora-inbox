#!/usr/bin/env python3
"""
Script de build pour le handler normalize_score_v2.
Conforme aux règles d'hygiène V4 - handler minimal sans dépendances.
"""

import os
import sys
import shutil
import zipfile
import tempfile
from pathlib import Path

# Configuration
LAMBDA_NAME = "vectora-inbox-normalize-score-v2-dev"
CODE_BUCKET = "vectora-inbox-lambda-code-dev"

def log(message):
    import datetime
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def build_handler_package():
    """Crée le package handler minimal (sans dépendances)."""
    log("Création du package handler minimal...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        package_dir = Path(temp_dir) / "lambda_package"
        package_dir.mkdir()
        
        # Copier uniquement le handler
        src_handler = Path("src_v2/lambdas/normalize_score/handler.py")
        if not src_handler.exists():
            log(f"[ERREUR] Handler non trouvé: {src_handler}")
            sys.exit(1)
        
        shutil.copy2(src_handler, package_dir / "handler.py")
        log(f"[OK] Handler copié: {src_handler}")
        
        # Vérifier la taille (doit être <1MB)
        package_size = sum(f.stat().st_size for f in package_dir.rglob('*') if f.is_file())
        package_size_kb = package_size / 1024
        
        log(f"[OK] Taille du package: {package_size_kb:.1f}KB")
        
        if package_size > 1024 * 1024:  # 1MB
            log(f"[ATTENTION] Package volumineux: {package_size_kb:.1f}KB")
        
        # Créer le ZIP
        zip_path = Path(temp_dir) / f"{LAMBDA_NAME}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in package_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(package_dir)
                    zipf.write(file_path, arcname)
        
        zip_size_kb = zip_path.stat().st_size / 1024
        log(f"[OK] Package ZIP créé: {zip_size_kb:.1f}KB")
        
        # Copier le ZIP vers le répertoire de sortie
        output_zip = Path(f"{LAMBDA_NAME}-handler-only.zip")
        shutil.copy2(zip_path, output_zip)
        
        log(f"[OK] Package handler sauvegardé: {output_zip}")
        
        return output_zip

def validate_handler_imports():
    """Valide que le handler peut importer vectora_core (sera fourni par layer)."""
    log("Validation des imports du handler...")
    
    try:
        # Test d'import sans exécution
        import ast
        
        handler_file = Path("src_v2/lambdas/normalize_score/handler.py")
        with open(handler_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parser le code pour vérifier les imports
        tree = ast.parse(content)
        
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        # Vérifier l'import vectora_core
        vectora_core_imports = [imp for imp in imports if 'vectora_core' in imp]
        
        if vectora_core_imports:
            log(f"[OK] Imports vectora_core détectés: {vectora_core_imports}")
        else:
            log("[ATTENTION] Aucun import vectora_core détecté")
        
        log("[OK] Validation syntaxique réussie")
        
    except Exception as e:
        log(f"[ERREUR] Validation imports échouée: {str(e)}")
        sys.exit(1)

def main():
    log("=== Build Handler normalize_score_v2 (minimal) ===")
    
    try:
        # 1. Validation des imports
        validate_handler_imports()
        
        # 2. Build du package
        package_path = build_handler_package()
        
        log(f"[SUCCES] Handler packagé: {package_path}")
        log("Le handler est prêt pour déploiement avec layers")
        
        # Afficher les layers requis
        with open("vectora_core_layer_arn.txt", "r") as f:
            vectora_core_arn = f.read().strip()
        with open("common_deps_layer_arn.txt", "r") as f:
            common_deps_arn = f.read().strip()
        
        log(f"Layers requis:")
        log(f"  - vectora-core: {vectora_core_arn}")
        log(f"  - common-deps: {common_deps_arn}")
        
    except Exception as e:
        log(f"[ERREUR] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()