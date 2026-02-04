#!/usr/bin/env python3
"""
Script de snapshot: Copie src_v2 et canonical avant modifications
"""

import shutil
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent

def create_snapshot(description=""):
    """Cree snapshot de src_v2 et canonical"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_dir = PROJECT_ROOT / ".snapshots" / timestamp
    
    print(f"\n{'='*80}")
    print(f"CREATION SNAPSHOT")
    print(f"{'='*80}")
    print(f"Timestamp: {timestamp}")
    print(f"Description: {description or 'Aucune'}")
    print()
    
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    
    # Copier src_v2
    src_v2_src = PROJECT_ROOT / "src_v2"
    src_v2_dst = snapshot_dir / "src_v2"
    
    if src_v2_src.exists():
        print(f"[1/2] Copie src_v2/...")
        shutil.copytree(src_v2_src, src_v2_dst, 
                       ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.pytest_cache'))
        print(f"      OK")
    
    # Copier canonical
    canonical_src = PROJECT_ROOT / "canonical"
    canonical_dst = snapshot_dir / "canonical"
    
    if canonical_src.exists():
        print(f"[2/2] Copie canonical/...")
        shutil.copytree(canonical_src, canonical_dst)
        print(f"      OK")
    
    # Metadata
    metadata_file = snapshot_dir / "SNAPSHOT_INFO.txt"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        f.write(f"Snapshot: {timestamp}\n")
        f.write(f"Date: {datetime.now().isoformat()}\n")
        f.write(f"Description: {description}\n")
    
    print()
    print(f"[SUCCESS] Snapshot: .snapshots/{timestamp}/")
    print()
    print(f"Pour comparer:")
    print(f"  python scripts/snapshot/diff_snapshot.py {timestamp}")
    print()
    
    return timestamp

def list_snapshots():
    """Liste snapshots"""
    snapshots_dir = PROJECT_ROOT / ".snapshots"
    
    if not snapshots_dir.exists():
        print("\n[INFO] Aucun snapshot")
        return
    
    snapshots = sorted([d for d in snapshots_dir.iterdir() if d.is_dir()], reverse=True)
    
    if not snapshots:
        print("\n[INFO] Aucun snapshot")
        return
    
    print(f"\nSNAPSHOTS ({len(snapshots)}):")
    for snapshot in snapshots:
        info_file = snapshot / "SNAPSHOT_INFO.txt"
        desc = "N/A"
        if info_file.exists():
            with open(info_file, encoding='utf-8') as f:
                for line in f:
                    if line.startswith('Description:'):
                        desc = line.split(': ', 1)[1].strip()
        print(f"  {snapshot.name} - {desc}")
    print()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Creer snapshot src_v2 + canonical")
    parser.add_argument("--description", "-d", help="Description")
    parser.add_argument("--list", "-l", action="store_true", help="Lister snapshots")
    
    args = parser.parse_args()
    
    if args.list:
        list_snapshots()
    else:
        create_snapshot(args.description or "")

if __name__ == "__main__":
    main()
