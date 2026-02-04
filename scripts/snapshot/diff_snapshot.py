#!/usr/bin/env python3
"""
Script de diff: Compare etat actuel avec snapshot
"""

import sys
import difflib
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent

def compare_files(file1, file2):
    """Compare 2 fichiers et retourne diff"""
    try:
        with open(file1, encoding='utf-8') as f:
            lines1 = f.readlines()
        with open(file2, encoding='utf-8') as f:
            lines2 = f.readlines()
        
        diff = list(difflib.unified_diff(lines1, lines2, 
                                         fromfile=str(file1), 
                                         tofile=str(file2),
                                         lineterm=''))
        return diff
    except:
        return None

def find_modified_files(snapshot_dir, current_dir, base_path=""):
    """Trouve fichiers modifies"""
    modified = []
    added = []
    deleted = []
    
    snapshot_files = set()
    current_files = set()
    
    if snapshot_dir.exists():
        for f in snapshot_dir.rglob('*'):
            if f.is_file():
                rel_path = f.relative_to(snapshot_dir)
                snapshot_files.add(rel_path)
    
    if current_dir.exists():
        for f in current_dir.rglob('*'):
            if f.is_file() and '__pycache__' not in str(f):
                rel_path = f.relative_to(current_dir)
                current_files.add(rel_path)
    
    # Fichiers modifies
    for rel_path in snapshot_files & current_files:
        snapshot_file = snapshot_dir / rel_path
        current_file = current_dir / rel_path
        
        try:
            with open(snapshot_file, 'rb') as f1, open(current_file, 'rb') as f2:
                if f1.read() != f2.read():
                    modified.append(str(rel_path))
        except:
            pass
    
    # Fichiers ajoutes
    added = [str(p) for p in (current_files - snapshot_files)]
    
    # Fichiers supprimes
    deleted = [str(p) for p in (snapshot_files - current_files)]
    
    return sorted(modified), sorted(added), sorted(deleted)

def diff_snapshot(snapshot_id, show_diff=False):
    """Compare avec snapshot"""
    
    snapshot_dir = PROJECT_ROOT / ".snapshots" / snapshot_id
    
    if not snapshot_dir.exists():
        print(f"[ERREUR] Snapshot introuvable: {snapshot_id}")
        return
    
    print(f"\n{'='*80}")
    print(f"COMPARAISON AVEC SNAPSHOT {snapshot_id}")
    print(f"{'='*80}")
    print()
    
    # Comparer src_v2
    print("[1/2] src_v2/")
    snapshot_src = snapshot_dir / "src_v2"
    current_src = PROJECT_ROOT / "src_v2"
    
    modified, added, deleted = find_modified_files(snapshot_src, current_src)
    
    if modified:
        print(f"  Modifies ({len(modified)}):")
        for f in modified:
            print(f"    M {f}")
    if added:
        print(f"  Ajoutes ({len(added)}):")
        for f in added:
            print(f"    + {f}")
    if deleted:
        print(f"  Supprimes ({len(deleted)}):")
        for f in deleted:
            print(f"    - {f}")
    
    if not (modified or added or deleted):
        print(f"  Aucun changement")
    
    print()
    
    # Comparer canonical
    print("[2/2] canonical/")
    snapshot_can = snapshot_dir / "canonical"
    current_can = PROJECT_ROOT / "canonical"
    
    modified_can, added_can, deleted_can = find_modified_files(snapshot_can, current_can)
    
    if modified_can:
        print(f"  Modifies ({len(modified_can)}):")
        for f in modified_can:
            print(f"    M {f}")
    if added_can:
        print(f"  Ajoutes ({len(added_can)}):")
        for f in added_can:
            print(f"    + {f}")
    if deleted_can:
        print(f"  Supprimes ({len(deleted_can)}):")
        for f in deleted_can:
            print(f"    - {f}")
    
    if not (modified_can or added_can or deleted_can):
        print(f"  Aucun changement")
    
    print()
    print(f"{'='*80}")
    
    total_changes = len(modified) + len(added) + len(deleted) + len(modified_can) + len(added_can) + len(deleted_can)
    print(f"TOTAL: {total_changes} changement(s)")
    print(f"{'='*80}")
    print()
    
    # Afficher diff si demande
    if show_diff and (modified or modified_can):
        print("\nDIFF DETAILLE:")
        print("="*80)
        
        for f in modified[:5]:  # Max 5 fichiers
            snapshot_file = snapshot_src / f
            current_file = current_src / f
            diff = compare_files(snapshot_file, current_file)
            if diff:
                print(f"\n--- {f}")
                for line in diff[:50]:  # Max 50 lignes
                    print(line)
        
        for f in modified_can[:5]:
            snapshot_file = snapshot_can / f
            current_file = current_can / f
            diff = compare_files(snapshot_file, current_file)
            if diff:
                print(f"\n--- {f}")
                for line in diff[:50]:
                    print(line)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Comparer avec snapshot")
    parser.add_argument("snapshot_id", help="ID snapshot (timestamp)")
    parser.add_argument("--diff", "-d", action="store_true", help="Afficher diff detaille")
    
    args = parser.parse_args()
    
    diff_snapshot(args.snapshot_id, args.diff)

if __name__ == "__main__":
    main()
