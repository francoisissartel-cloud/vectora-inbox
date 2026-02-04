"""
Script de nettoyage des fichiers temporaires du diagnostic v14.

Usage:
    python scripts/cleanup_diagnostic_v14.py
"""

import os
from pathlib import Path

# Fichiers temporaires à supprimer
TEMP_FILES = [
    "temp_items_v13.json",
    "temp_items_v14.json",
    "temp_items_v15.json",  # Si créé pendant les tests
]

def cleanup():
    """Supprime les fichiers temporaires du diagnostic."""
    root_dir = Path(__file__).parent.parent
    
    deleted_count = 0
    not_found_count = 0
    
    print("🧹 Nettoyage des fichiers temporaires du diagnostic v14...\n")
    
    for filename in TEMP_FILES:
        filepath = root_dir / filename
        
        if filepath.exists():
            try:
                filepath.unlink()
                print(f"✅ Supprimé: {filename}")
                deleted_count += 1
            except Exception as e:
                print(f"❌ Erreur lors de la suppression de {filename}: {e}")
        else:
            print(f"⏭️  Ignoré (non trouvé): {filename}")
            not_found_count += 1
    
    print(f"\n📊 Résumé:")
    print(f"   - Fichiers supprimés: {deleted_count}")
    print(f"   - Fichiers non trouvés: {not_found_count}")
    print(f"   - Total: {len(TEMP_FILES)}")
    
    if deleted_count > 0:
        print("\n✅ Nettoyage terminé avec succès!")
    else:
        print("\n⚠️  Aucun fichier à nettoyer.")

if __name__ == "__main__":
    cleanup()
