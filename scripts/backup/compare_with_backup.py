#!/usr/bin/env python3
"""
Script de comparaison avec backup local
Compare l'état actuel avec un backup spécifique
"""

import os
import argparse
import json
import filecmp
from pathlib import Path

def compare_with_backup(backup_id, detailed=False):
    """Compare l'état actuel avec un backup"""
    
    backup_path = os.path.join(".backup", backup_id)
    
    if not os.path.exists(backup_path):
        print(f"❌ Backup {backup_id} introuvable")
        return False
    
    # Lire metadata
    info_file = os.path.join(backup_path, "BACKUP_INFO.json")
    if not os.path.exists(info_file):
        print(f"❌ Metadata backup {backup_id} introuvable")
        return False
    
    with open(info_file) as f:
        metadata = json.load(f)
    
    print(f"🔍 Comparaison avec backup: {backup_id}")
    print(f"📅 Créé: {metadata.get('created_at', 'N/A')}")
    print(f"📝 Description: {metadata.get('description', 'N/A')}")
    print()
    
    has_changes = False
    
    # Comparer src_v2
    if "src_v2/" in metadata.get("files_backed_up", []):
        backup_src = os.path.join(backup_path, "src_v2")
        current_src = "src_v2"
        
        if os.path.exists(current_src):
            changes = compare_directories(backup_src, current_src, "src_v2", detailed)
            if changes:
                has_changes = True
        else:
            print("❌ src_v2/ supprimé depuis backup")
            has_changes = True
    
    # Comparer canonical
    if "canonical/" in metadata.get("files_backed_up", []):
        backup_canonical = os.path.join(backup_path, "canonical")
        current_canonical = "canonical"
        
        if os.path.exists(current_canonical):
            changes = compare_directories(backup_canonical, current_canonical, "canonical", detailed)
            if changes:
                has_changes = True
        else:
            print("❌ canonical/ supprimé depuis backup")
            has_changes = True
    
    # Comparer VERSION
    if "VERSION" in metadata.get("files_backed_up", []):
        backup_version = os.path.join(backup_path, "VERSION")
        current_version = "VERSION"
        
        if os.path.exists(current_version):
            if not filecmp.cmp(backup_version, current_version, shallow=False):
                print("📝 VERSION modifié")
                if detailed:
                    with open(backup_version) as f:
                        backup_content = f.read().strip()
                    with open(current_version) as f:
                        current_content = f.read().strip()
                    print(f"   Backup: {backup_content}")
                    print(f"   Actuel: {current_content}")
                has_changes = True
        else:
            print("❌ VERSION supprimé depuis backup")
            has_changes = True
    
    if not has_changes:
        print("✅ Aucune modification détectée")
    
    return has_changes

def compare_directories(backup_dir, current_dir, name, detailed=False):
    """Compare deux dossiers"""
    
    dcmp = filecmp.dircmp(backup_dir, current_dir)
    has_changes = False
    
    # Fichiers ajoutés
    if dcmp.right_only:
        print(f"➕ {name}/ - Fichiers ajoutés: {len(dcmp.right_only)}")
        if detailed:
            for f in dcmp.right_only[:5]:  # Limiter à 5
                print(f"   + {f}")
            if len(dcmp.right_only) > 5:
                print(f"   ... et {len(dcmp.right_only) - 5} autres")
        has_changes = True
    
    # Fichiers supprimés
    if dcmp.left_only:
        print(f"➖ {name}/ - Fichiers supprimés: {len(dcmp.left_only)}")
        if detailed:
            for f in dcmp.left_only[:5]:
                print(f"   - {f}")
            if len(dcmp.left_only) > 5:
                print(f"   ... et {len(dcmp.left_only) - 5} autres")
        has_changes = True
    
    # Fichiers modifiés
    if dcmp.diff_files:
        print(f"📝 {name}/ - Fichiers modifiés: {len(dcmp.diff_files)}")
        if detailed:
            for f in dcmp.diff_files[:5]:
                print(f"   ~ {f}")
            if len(dcmp.diff_files) > 5:
                print(f"   ... et {len(dcmp.diff_files) - 5} autres")
        has_changes = True
    
    # Récursif pour sous-dossiers
    for subdir in dcmp.common_dirs:
        backup_subdir = os.path.join(backup_dir, subdir)
        current_subdir = os.path.join(current_dir, subdir)
        sub_changes = compare_directories(backup_subdir, current_subdir, f"{name}/{subdir}", detailed)
        if sub_changes:
            has_changes = True
    
    return has_changes

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Comparer avec backup local")
    parser.add_argument("--backup-id", "-b", required=True, help="ID du backup à comparer")
    parser.add_argument("--detailed", "-d", action="store_true", help="Affichage détaillé")
    
    args = parser.parse_args()
    
    compare_with_backup(args.backup_id, args.detailed)