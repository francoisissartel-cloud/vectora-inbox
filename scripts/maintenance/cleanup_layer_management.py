#!/usr/bin/env python3
"""
Script de nettoyage des dossiers redondants dans .build/
Conforme aux nouvelles règles de gestion des layers.
"""

import os
import shutil
from pathlib import Path

def log(message):
    print(f"[CLEANUP] {message}", flush=True)

def cleanup_build_redundancies():
    """Supprime les dossiers redondants dans .build/"""
    
    build_dir = Path(".build")
    
    if not build_dir.exists():
        log("Dossier .build/ n'existe pas, rien a nettoyer")
        return
    
    # Dossiers à supprimer (redondants)
    redundant_dirs = [
        build_dir / "layer_build",
        build_dir / "layer_fix",
        build_dir / "layer_vectora_core_approche_b",
        build_dir / "python"
    ]
    
    for dir_path in redundant_dirs:
        if dir_path.exists():
            log(f"Suppression: {dir_path}")
            shutil.rmtree(dir_path)
            log(f"[OK] Supprime: {dir_path}")
        else:
            log(f"[SKIP] Deja absent: {dir_path}")
    
    # Créer structure optimale
    workspace_dir = build_dir / "workspace"
    workspace_dir.mkdir(exist_ok=True)
    log(f"[OK] Cree: {workspace_dir}")
    
    layers_dir = build_dir / "layers"
    layers_dir.mkdir(exist_ok=True)
    log(f"[OK] Cree: {layers_dir}")
    
    log("[OK] Nettoyage .build/ termine")

def cleanup_experimental_layers():
    """Supprime les layers expérimentales non utilisées"""
    
    experimental_dir = Path("layer_management/experimental")
    
    if not experimental_dir.exists():
        log("Dossier experimental/ n'existe pas, rien a nettoyer")
        return
    
    # Dossiers à supprimer
    experimental_layers = [
        experimental_dir / "layer_minimal",
        experimental_dir / "layer_rebuild"
    ]
    
    for dir_path in experimental_layers:
        if dir_path.exists():
            log(f"Suppression: {dir_path}")
            shutil.rmtree(dir_path)
            log(f"[OK] Supprime: {dir_path}")
        else:
            log(f"[SKIP] Deja absent: {dir_path}")
    
    log("[OK] Nettoyage experimental/ termine")

def create_archive_structure():
    """Crée la structure d'archive mensuelle"""
    
    archive_dir = Path("layer_management/archive")
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    # Créer dossier pour le mois actuel
    from datetime import datetime
    current_month = datetime.now().strftime("%Y-%m")
    month_dir = archive_dir / current_month
    month_dir.mkdir(exist_ok=True)
    
    log(f"[OK] Structure archive creee: {month_dir}")

def main():
    log("=== Nettoyage Layer Management ===")
    
    try:
        # Phase 1: Nettoyer .build/
        log("\n[Phase 1] Nettoyage .build/")
        cleanup_build_redundancies()
        
        # Phase 2: Nettoyer experimental/
        log("\n[Phase 2] Nettoyage experimental/")
        cleanup_experimental_layers()
        
        # Phase 3: Créer structure archive
        log("\n[Phase 3] Creation structure archive")
        create_archive_structure()
        
        log("\n[SUCCESS] Nettoyage termine")
        log("\nProchaines etapes:")
        log("1. Verifier que .build/ contient uniquement workspace/ et layers/")
        log("2. Archiver backup/old_builds/ vers S3 si necessaire")
        log("3. Executer: python scripts/layers/build_all.py")
        
    except Exception as e:
        log(f"[ERROR] {str(e)}")
        raise

if __name__ == "__main__":
    main()
