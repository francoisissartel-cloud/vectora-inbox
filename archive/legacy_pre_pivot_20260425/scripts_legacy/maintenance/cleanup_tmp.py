#!/usr/bin/env python3
"""
Script de nettoyage des fichiers temporaires
Supprime les fichiers dans .tmp/ plus anciens que 7 jours
"""
import os
import time
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
TMP_DIR = REPO_ROOT / ".tmp"
MAX_AGE_DAYS = 7

def cleanup_old_files():
    """Supprime fichiers > MAX_AGE_DAYS jours"""
    if not TMP_DIR.exists():
        print(f"❌ Dossier {TMP_DIR} n'existe pas")
        return
    
    now = time.time()
    max_age_seconds = MAX_AGE_DAYS * 86400
    deleted_count = 0
    
    for root, dirs, files in os.walk(TMP_DIR):
        for file in files:
            if file == "README.md":
                continue
            
            filepath = Path(root) / file
            file_age = now - filepath.stat().st_mtime
            
            if file_age > max_age_seconds:
                try:
                    filepath.unlink()
                    deleted_count += 1
                    print(f"🗑️  Supprimé: {filepath.relative_to(REPO_ROOT)}")
                except Exception as e:
                    print(f"❌ Erreur: {filepath.relative_to(REPO_ROOT)} - {e}")
    
    print(f"\n✅ {deleted_count} fichier(s) supprimé(s)")

if __name__ == "__main__":
    print(f"🧹 Nettoyage fichiers .tmp/ > {MAX_AGE_DAYS} jours\n")
    cleanup_old_files()
