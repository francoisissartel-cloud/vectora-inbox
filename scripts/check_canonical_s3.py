#!/usr/bin/env python3
"""
Vérifie que tous les fichiers canonical sont sur S3 et détecte les références circulaires
"""

import subprocess
import yaml
from pathlib import Path

PROFILE = "rag-lai-prod"
REGION = "eu-west-3"
BUCKET = "vectora-inbox-data-dev"

def run_aws(cmd):
    full_cmd = f"{cmd} --profile {PROFILE} --region {REGION}"
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    return result.returncode == 0, result.stdout

def get_s3_files():
    """Liste tous les fichiers canonical sur S3"""
    success, stdout = run_aws(f"aws s3 ls s3://{BUCKET}/canonical/ --recursive")
    
    if not success:
        return []
    
    files = []
    for line in stdout.strip().split('\n'):
        if line.strip():
            parts = line.split()
            if len(parts) >= 4:
                path = parts[3]
                files.append(path)
    
    return files

def get_local_files():
    """Liste tous les fichiers canonical locaux"""
    repo_root = Path(__file__).parent.parent
    canonical_dir = repo_root / "canonical"
    
    files = []
    for f in canonical_dir.glob("**/*.yaml"):
        rel_path = f.relative_to(canonical_dir)
        files.append(str(rel_path).replace('\\', '/'))
    
    return files

def download_s3_file(s3_path):
    """Télécharge un fichier depuis S3"""
    success, stdout = run_aws(f"aws s3 cp s3://{BUCKET}/{s3_path} -")
    if success:
        return stdout
    return None

def check_references(file_path, content):
    """Vérifie les références dans un fichier YAML"""
    try:
        data = yaml.safe_load(content)
        refs = []
        
        def find_refs(obj, path=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k in ['canonical_ref', 'import', 'include', 'reference']:
                        refs.append(v)
                    find_refs(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    find_refs(item, f"{path}[{i}]")
        
        find_refs(data)
        return refs
    except:
        return []

def main():
    print("="*80)
    print("VERIFICATION FICHIERS CANONICAL SUR S3")
    print("="*80)
    print()
    
    # Fichiers S3
    print("[1/4] Liste des fichiers sur S3...")
    s3_files = get_s3_files()
    print(f"   Trouves: {len(s3_files)} fichiers\n")
    
    # Fichiers locaux
    print("[2/4] Liste des fichiers locaux...")
    local_files = get_local_files()
    print(f"   Trouves: {len(local_files)} fichiers\n")
    
    # Comparaison
    print("[3/4] Comparaison local <-> S3...")
    s3_names = {f.split('/')[-1] for f in s3_files}
    local_names = {f.split('/')[-1] for f in local_files}
    
    missing_on_s3 = local_names - s3_names
    extra_on_s3 = s3_names - local_names
    
    if missing_on_s3:
        print(f"   [WARNING] {len(missing_on_s3)} fichiers manquants sur S3:")
        for f in sorted(missing_on_s3):
            print(f"      - {f}")
    else:
        print("   [OK] Tous les fichiers locaux sont sur S3")
    
    if extra_on_s3:
        print(f"   [INFO] {len(extra_on_s3)} fichiers supplementaires sur S3:")
        for f in sorted(extra_on_s3):
            print(f"      - {f}")
    
    print()
    
    # Vérification des références
    print("[4/4] Verification des references...")
    print()
    
    all_refs = {}
    for s3_file in s3_files:
        if s3_file.endswith('.yaml'):
            content = download_s3_file(s3_file)
            if content:
                refs = check_references(s3_file, content)
                if refs:
                    all_refs[s3_file] = refs
    
    if all_refs:
        print(f"   Fichiers avec references: {len(all_refs)}")
        for file, refs in all_refs.items():
            print(f"\n   {file}:")
            for ref in refs:
                # Vérifier si la référence existe
                ref_exists = any(ref in s3_file for s3_file in s3_files)
                status = "[OK]" if ref_exists else "[MISSING]"
                print(f"      {status} {ref}")
    else:
        print("   [OK] Aucune reference trouvee")
    
    print()
    print("="*80)
    print("FICHIERS CANONICAL SUR S3")
    print("="*80)
    print()
    
    # Grouper par dossier
    by_folder = {}
    for f in s3_files:
        parts = f.split('/')
        if len(parts) >= 2:
            folder = parts[1]
            if folder not in by_folder:
                by_folder[folder] = []
            by_folder[folder].append(parts[-1])
    
    for folder in sorted(by_folder.keys()):
        print(f"{folder}/")
        for file in sorted(by_folder[folder]):
            print(f"  - {file}")
        print()
    
    print("="*80)
    print("RESUME")
    print("="*80)
    print()
    print(f"Fichiers sur S3: {len(s3_files)}")
    print(f"Fichiers locaux: {len(local_files)}")
    print(f"Manquants sur S3: {len(missing_on_s3)}")
    print(f"Fichiers avec references: {len(all_refs)}")
    print()
    
    if missing_on_s3:
        print("[ACTION REQUISE] Uploader les fichiers manquants:")
        print()
        for f in sorted(missing_on_s3):
            local_path = None
            for lf in local_files:
                if lf.endswith(f):
                    local_path = lf
                    break
            if local_path:
                print(f"aws s3 cp canonical/{local_path} s3://{BUCKET}/canonical/{local_path.replace(chr(92), '/')} --profile {PROFILE}")
        print()

if __name__ == "__main__":
    main()
