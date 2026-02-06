#!/usr/bin/env python3
"""
Script de backup local pour Vectora Inbox
Crée une copie complète de src_v2/ et canonical/ avec horodatage
"""

import os
import shutil
import argparse
from datetime import datetime
import json

def create_backup(description=""):
    """Crée un backup local horodaté"""
    
    # Timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Nom backup
    backup_name = f"{timestamp}"
    if description:
        # Nettoyer description pour nom fichier
        clean_desc = "".join(c for c in description if c.isalnum() or c in (' ', '-', '_')).rstrip()
        clean_desc = clean_desc.replace(' ', '_').lower()
        backup_name += f"_{clean_desc}"
    
    # Dossier backup
    backup_dir = os.path.join(".backup", backup_name)
    
    # Créer dossier
    os.makedirs(backup_dir, exist_ok=True)
    
    print(f"[BACKUP] Creation backup: {backup_name}")
    
    # Copier src_v2
    if os.path.exists("src_v2"):
        print("  [COPY] src_v2/...")
        shutil.copytree("src_v2", os.path.join(backup_dir, "src_v2"))
    
    # Copier canonical
    if os.path.exists("canonical"):
        print("  [COPY] canonical/...")
        shutil.copytree("canonical", os.path.join(backup_dir, "canonical"))
    
    # Copier VERSION
    if os.path.exists("VERSION"):
        shutil.copy2("VERSION", backup_dir)
    
    # Créer metadata
    metadata = {
        "timestamp": timestamp,
        "description": description,
        "created_at": datetime.now().isoformat(),
        "files_backed_up": []
    }
    
    if os.path.exists("src_v2"):
        metadata["files_backed_up"].append("src_v2/")
    if os.path.exists("canonical"):
        metadata["files_backed_up"].append("canonical/")
    if os.path.exists("VERSION"):
        metadata["files_backed_up"].append("VERSION")
    
    # Sauver metadata
    with open(os.path.join(backup_dir, "BACKUP_INFO.json"), "w") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"[OK] Backup cree: .backup/{backup_name}")
    print(f"[INFO] Fichiers sauves: {', '.join(metadata['files_backed_up'])}")
    
    return backup_name

def list_backups():
    """Liste tous les backups disponibles"""
    
    backup_root = ".backup"
    if not os.path.exists(backup_root):
        print("[ERROR] Aucun backup trouve")
        return
    
    backups = []
    for item in os.listdir(backup_root):
        backup_path = os.path.join(backup_root, item)
        if os.path.isdir(backup_path):
            info_file = os.path.join(backup_path, "BACKUP_INFO.json")
            if os.path.exists(info_file):
                with open(info_file) as f:
                    metadata = json.load(f)
                backups.append((item, metadata))
    
    if not backups:
        print("[ERROR] Aucun backup valide trouve")
        return
    
    print("[LIST] Backups disponibles:")
    print()
    for backup_name, metadata in sorted(backups, reverse=True):
        print(f"  {backup_name}")
        print(f"   Cree: {metadata.get('created_at', 'N/A')}")
        print(f"   Description: {metadata.get('description', 'N/A')}")
        print(f"   Fichiers: {', '.join(metadata.get('files_backed_up', []))}")
        print()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backup local Vectora Inbox")
    parser.add_argument("--description", "-d", help="Description du backup")
    parser.add_argument("--list", "-l", action="store_true", help="Lister les backups")
    
    args = parser.parse_args()
    
    if args.list:
        list_backups()
    else:
        create_backup(args.description or "")