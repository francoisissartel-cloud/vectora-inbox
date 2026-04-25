#!/usr/bin/env python3
"""
Analyse les différences entre config-dev et data-dev canonical
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime

PROFILE = "rag-lai-prod"
CONFIG_BUCKET = "vectora-inbox-config-dev"
DATA_BUCKET = "vectora-inbox-data-dev"

def run_aws(cmd):
    """Exécute une commande AWS CLI"""
    full_cmd = f"{cmd} --profile {PROFILE}"
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    return result.returncode == 0, result.stdout

def get_s3_files(bucket, prefix="canonical/"):
    """Liste les fichiers S3 avec métadonnées"""
    success, stdout = run_aws(f"aws s3 ls s3://{bucket}/{prefix} --recursive")
    
    files = {}
    if success:
        for line in stdout.strip().split('\n'):
            if line.strip():
                parts = line.split()
                if len(parts) >= 4:
                    date = parts[0]
                    time = parts[1]
                    size = int(parts[2])
                    path = parts[3]
                    filename = path.split('/')[-1]
                    
                    files[path] = {
                        'filename': filename,
                        'size': size,
                        'date': f"{date} {time}",
                        'path': path
                    }
    
    return files

def compare_files(config_files, data_files):
    """Compare les fichiers entre les deux buckets"""
    
    config_only = set(config_files.keys()) - set(data_files.keys())
    data_only = set(data_files.keys()) - set(config_files.keys())
    common = set(config_files.keys()) & set(data_files.keys())
    
    different = []
    for path in common:
        if config_files[path]['size'] != data_files[path]['size']:
            different.append({
                'path': path,
                'config_size': config_files[path]['size'],
                'data_size': data_files[path]['size'],
                'config_date': config_files[path]['date'],
                'data_date': data_files[path]['date']
            })
    
    return {
        'config_only': sorted(config_only),
        'data_only': sorted(data_only),
        'different': different
    }

def main():
    print("="*80)
    print("ANALYSE DOUBLONS S3 CANONICAL")
    print("="*80)
    print()
    
    # Récupérer les fichiers
    print("[1/3] Récupération des fichiers config-dev...")
    config_files = get_s3_files(CONFIG_BUCKET)
    print(f"   Trouvés: {len(config_files)} fichiers")
    
    print("[2/3] Récupération des fichiers data-dev...")
    data_files = get_s3_files(DATA_BUCKET)
    print(f"   Trouvés: {len(data_files)} fichiers")
    
    print("[3/3] Comparaison...")
    comparison = compare_files(config_files, data_files)
    print()
    
    # Afficher les résultats
    print("="*80)
    print("RÉSULTATS")
    print("="*80)
    print()
    
    print(f"📊 STATISTIQUES")
    print(f"   Config-dev: {len(config_files)} fichiers")
    print(f"   Data-dev:   {len(data_files)} fichiers")
    print(f"   Communs:    {len(config_files) - len(comparison['config_only'])} fichiers")
    print()
    
    # Fichiers uniquement dans config-dev
    if comparison['config_only']:
        print(f"📁 UNIQUEMENT DANS CONFIG-DEV ({len(comparison['config_only'])} fichiers)")
        print()
        for path in comparison['config_only']:
            info = config_files[path]
            print(f"   {path}")
            print(f"      Taille: {info['size']:,} bytes")
            print(f"      Date:   {info['date']}")
        print()
    
    # Fichiers uniquement dans data-dev
    if comparison['data_only']:
        print(f"📁 UNIQUEMENT DANS DATA-DEV ({len(comparison['data_only'])} fichiers)")
        print()
        for path in comparison['data_only']:
            info = data_files[path]
            print(f"   {path}")
            print(f"      Taille: {info['size']:,} bytes")
            print(f"      Date:   {info['date']}")
        print()
    
    # Fichiers différents
    if comparison['different']:
        print(f"⚠️  FICHIERS DIFFÉRENTS ({len(comparison['different'])} fichiers)")
        print()
        for diff in comparison['different']:
            print(f"   {diff['path']}")
            print(f"      Config-dev: {diff['config_size']:,} bytes ({diff['config_date']})")
            print(f"      Data-dev:   {diff['data_size']:,} bytes ({diff['data_date']})")
            
            size_diff = diff['config_size'] - diff['data_size']
            if size_diff > 0:
                print(f"      → Config-dev est PLUS GROS de {size_diff:,} bytes")
            else:
                print(f"      → Data-dev est PLUS GROS de {abs(size_diff):,} bytes")
            print()
    
    # Recommandations
    print("="*80)
    print("RECOMMANDATIONS")
    print("="*80)
    print()
    
    if len(config_files) > len(data_files):
        print("✅ CONFIG-DEV est plus complet ({} vs {} fichiers)".format(
            len(config_files), len(data_files)))
        print("   → Recommandation: Garder CONFIG-DEV comme source unique")
    elif len(data_files) > len(config_files):
        print("⚠️  DATA-DEV a plus de fichiers ({} vs {})".format(
            len(data_files), len(config_files)))
        print("   → Recommandation: Vérifier les fichiers manquants dans config-dev")
    else:
        print("ℹ️  Même nombre de fichiers ({})".format(len(config_files)))
    
    print()
    
    if comparison['different']:
        print(f"⚠️  {len(comparison['different'])} fichiers ont des versions différentes")
        print("   → Action requise: Décider quelle version garder")
        print()
        print("   Fichiers critiques à vérifier:")
        for diff in comparison['different']:
            if 'prompt' in diff['path'] or 'scope' in diff['path']:
                print(f"      - {diff['path']}")
    
    print()
    print("="*80)
    print("PROCHAINES ÉTAPES")
    print("="*80)
    print()
    print("1. Examiner les fichiers différents (surtout les prompts)")
    print("2. Décider quelle version garder pour chaque fichier")
    print("3. Exécuter le script de correction: .tmp/fix_s3_canonical_duplicates.bat")
    print("4. Vérifier l'alignement après correction")
    print()
    
    # Sauvegarder le rapport
    report_path = Path(".tmp/s3_canonical_comparison.json")
    report_path.parent.mkdir(exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            'date': datetime.now().isoformat(),
            'config_bucket': CONFIG_BUCKET,
            'data_bucket': DATA_BUCKET,
            'config_files_count': len(config_files),
            'data_files_count': len(data_files),
            'comparison': comparison
        }, f, indent=2)
    
    print(f"📄 Rapport JSON sauvegardé: {report_path}")
    print()

if __name__ == "__main__":
    main()
