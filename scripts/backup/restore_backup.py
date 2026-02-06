#!/usr/bin/env python3
"""
Script de restauration backup local
Restaure l'état depuis un backup spécifique
"""

import os
import shutil
import argparse
import json
from datetime import datetime

def restore_backup(backup_id, confirm=False):
    """Restaure depuis un backup"""
    
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
    
    print(f"🔄 Restauration backup: {backup_id}")
    print(f"📅 Créé: {metadata.get('created_at', 'N/A')}")
    print(f"📝 Description: {metadata.get('description', 'N/A')}")
    print(f"📁 Fichiers: {', '.join(metadata.get('files_backed_up', []))}")
    print()
    
    if not confirm:
        response = input("⚠️  Confirmer la restauration? (y/N): ")
        if response.lower() != 'y':
            print("❌ Restauration annulée")
            return False
    
    # Créer backup de sécurité avant restauration
    security_backup = f"before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    security_path = os.path.join(".backup", security_backup)
    os.makedirs(security_path, exist_ok=True)
    
    print(f"🛡️  Backup sécurité: {security_backup}")
    
    # Restaurer src_v2
    if "src_v2/" in metadata.get("files_backed_up", []):
        backup_src = os.path.join(backup_path, "src_v2")
        current_src = "src_v2"
        
        # Backup sécurité
        if os.path.exists(current_src):
            shutil.copytree(current_src, os.path.join(security_path, "src_v2"))
            shutil.rmtree(current_src)
        
        # Restaurer
        shutil.copytree(backup_src, current_src)
        print("✅ src_v2/ restauré")
    
    # Restaurer canonical
    if "canonical/" in metadata.get("files_backed_up", []):
        backup_canonical = os.path.join(backup_path, "canonical")
        current_canonical = "canonical"
        
        # Backup sécurité
        if os.path.exists(current_canonical):
            shutil.copytree(current_canonical, os.path.join(security_path, "canonical"))
            shutil.rmtree(current_canonical)
        
        # Restaurer
        shutil.copytree(backup_canonical, current_canonical)
        print("✅ canonical/ restauré")
    
    # Restaurer VERSION
    if "VERSION" in metadata.get("files_backed_up", []):
        backup_version = os.path.join(backup_path, "VERSION")
        current_version = "VERSION"
        
        # Backup sécurité
        if os.path.exists(current_version):
            shutil.copy2(current_version, os.path.join(security_path, "VERSION"))
        
        # Restaurer
        shutil.copy2(backup_version, current_version)
        print("✅ VERSION restauré")
    
    # Créer metadata backup sécurité
    security_metadata = {
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "description": f"Backup automatique avant restauration de {backup_id}",
        "created_at": datetime.now().isoformat(),
        "restored_from": backup_id,
        "files_backed_up": metadata.get("files_backed_up", [])
    }
    
    with open(os.path.join(security_path, "BACKUP_INFO.json"), "w") as f:
        json.dump(security_metadata, f, indent=2)
    
    print(f"✅ Restauration terminée")
    print(f"🛡️  Backup sécurité disponible: {security_backup}")
    
    return True

def list_backups():
    """Liste tous les backups disponibles"""
    
    backup_root = ".backup"
    if not os.path.exists(backup_root):
        print("❌ Aucun backup trouvé")
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
        print("❌ Aucun backup valide trouvé")
        return
    
    print("📋 Backups disponibles:")
    print()
    for backup_name, metadata in sorted(backups, reverse=True):
        print(f"🗂️  {backup_name}")
        print(f"   📅 Créé: {metadata.get('created_at', 'N/A')}")
        print(f"   📝 Description: {metadata.get('description', 'N/A')}")
        print()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Restaurer backup local")
    parser.add_argument("--backup-id", "-b", help="ID du backup à restaurer")
    parser.add_argument("--list", "-l", action="store_true", help="Lister les backups")
    parser.add_argument("--yes", "-y", action="store_true", help="Confirmer automatiquement")
    
    args = parser.parse_args()
    
    if args.list:
        list_backups()
    elif args.backup_id:
        restore_backup(args.backup_id, args.yes)
    else:
        print("❌ Spécifier --backup-id ou --list")