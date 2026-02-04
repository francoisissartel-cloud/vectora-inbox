#!/usr/bin/env python3
"""
Vérifie l'alignement entre le repo local et l'environnement AWS dev.
Vérifie: Lambdas, Layers, Canonical, Config clients
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Config
PROFILE = "rag-lai-prod"
REGION = "eu-west-3"
ENV = "dev"

# Buckets
BUCKET_DATA = f"vectora-inbox-data-{ENV}"
BUCKET_CONFIG = f"vectora-inbox-config-{ENV}"
BUCKET_CANONICAL = f"vectora-inbox-data-{ENV}"  # Canonical est dans data bucket

# Lambdas
LAMBDAS = [
    f"vectora-inbox-ingest-v2-{ENV}",
    f"vectora-inbox-normalize-score-v2-{ENV}",
    f"vectora-inbox-newsletter-v2-{ENV}"
]

def run_aws_cmd(cmd):
    """Execute AWS CLI command"""
    full_cmd = f"{cmd} --profile {PROFILE} --region {REGION}"
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr

def check_lambdas():
    """Vérifie les Lambdas déployées"""
    print("=" * 80)
    print("LAMBDAS")
    print("=" * 80)
    
    results = {}
    for lambda_name in LAMBDAS:
        success, stdout, stderr = run_aws_cmd(
            f"aws lambda get-function --function-name {lambda_name}"
        )
        
        if success:
            data = json.loads(stdout)
            config = data['Configuration']
            code = data['Code']
            
            results[lambda_name] = {
                'exists': True,
                'runtime': config['Runtime'],
                'last_modified': config['LastModified'],
                'code_size': config['CodeSize'],
                'layers': len(config.get('Layers', [])),
                'layer_arns': [l['Arn'] for l in config.get('Layers', [])]
            }
            
            print(f"\n[OK] {lambda_name}")
            print(f"   Runtime: {config['Runtime']}")
            print(f"   Last Modified: {config['LastModified']}")
            print(f"   Code Size: {config['CodeSize']:,} bytes")
            print(f"   Layers: {len(config.get('Layers', []))}")
            for layer in config.get('Layers', []):
                arn = layer['Arn']
                version = arn.split(':')[-1]
                layer_name = arn.split(':')[-2]
                print(f"     - {layer_name}:{version}")
        else:
            results[lambda_name] = {'exists': False}
            print(f"\n[MISSING] {lambda_name} - NOT FOUND")
    
    return results

def check_layers():
    """Vérifie les Layers disponibles"""
    print("\n" + "=" * 80)
    print("LAYERS")
    print("=" * 80)
    
    layer_name = f"vectora-inbox-vectora-core-{ENV}"
    success, stdout, stderr = run_aws_cmd(
        f"aws lambda list-layer-versions --layer-name {layer_name} --max-items 5"
    )
    
    if success:
        data = json.loads(stdout)
        versions = data.get('LayerVersions', [])
        
        if versions:
            latest = versions[0]
            print(f"\n[OK] {layer_name}")
            print(f"   Latest Version: {latest['Version']}")
            print(f"   Created: {latest['CreatedDate']}")
            print(f"   Size: {latest.get('CodeSize', 0):,} bytes")
            print(f"\n   Recent versions:")
            for v in versions[:5]:
                print(f"     - v{v['Version']} ({v['CreatedDate']})")
            return {'exists': True, 'latest_version': latest['Version']}
        else:
            print(f"\n[WARNING] {layer_name} - No versions found")
            return {'exists': False}
    else:
        print(f"\n[MISSING] {layer_name} - NOT FOUND")
        return {'exists': False}

def check_canonical():
    """Vérifie le canonical sur S3"""
    print("\n" + "=" * 80)
    print("CANONICAL")
    print("=" * 80)
    
    success, stdout, stderr = run_aws_cmd(
        f"aws s3 ls s3://{BUCKET_CANONICAL}/canonical/ --recursive"
    )
    
    if success:
        files = [line.strip() for line in stdout.strip().split('\n') if line.strip()]
        
        print(f"\n[OK] Canonical files found: {len(files)}")
        
        # Grouper par version
        versions = {}
        for line in files:
            parts = line.split()
            if len(parts) >= 4:
                path = parts[3]
                if 'canonical/' in path:
                    version = path.split('/')[1] if len(path.split('/')) > 1 else 'unknown'
                    if version not in versions:
                        versions[version] = []
                    versions[version].append(path.split('/')[-1])
        
        print("\n   Versions disponibles:")
        for version in sorted(versions.keys(), reverse=True):
            print(f"     - {version}: {len(versions[version])} files")
            for f in sorted(versions[version])[:3]:
                print(f"         {f}")
            if len(versions[version]) > 3:
                print(f"         ... +{len(versions[version])-3} more")
        
        return {'exists': True, 'versions': list(versions.keys())}
    else:
        print(f"\n[MISSING] Canonical bucket not accessible")
        return {'exists': False}

def check_client_configs():
    """Vérifie les configs clients sur S3"""
    print("\n" + "=" * 80)
    print("CLIENT CONFIGS")
    print("=" * 80)
    
    success, stdout, stderr = run_aws_cmd(
        f"aws s3 ls s3://{BUCKET_CONFIG}/clients/"
    )
    
    if success:
        lines = [line.strip() for line in stdout.strip().split('\n') if line.strip()]
        configs = [line.split()[-1] for line in lines if '.yaml' in line]
        
        print(f"\n[OK] Client configs found: {len(configs)}")
        for config in sorted(configs):
            print(f"   - {config}")
        
        return {'exists': True, 'count': len(configs), 'configs': configs}
    else:
        print(f"\n[MISSING] Config bucket not accessible")
        return {'exists': False}

def check_local_repo():
    """Vérifie l'état du repo local"""
    print("\n" + "=" * 80)
    print("LOCAL REPO")
    print("=" * 80)
    
    repo_root = Path(__file__).parent.parent
    
    # Git branch
    result = subprocess.run("git branch --show-current", shell=True, capture_output=True, text=True, cwd=repo_root)
    branch = result.stdout.strip() if result.returncode == 0 else "unknown"
    
    # Git status
    result = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True, cwd=repo_root)
    uncommitted = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
    
    # Last commit
    result = subprocess.run("git log -1 --format=%H|%s|%ci", shell=True, capture_output=True, text=True, cwd=repo_root)
    if result.returncode == 0:
        commit_hash, commit_msg, commit_date = result.stdout.strip().split('|')
        commit_hash_short = commit_hash[:7]
    else:
        commit_hash_short = "unknown"
        commit_msg = "unknown"
        commit_date = "unknown"
    
    # Lambdas locales
    lambdas_dir = repo_root / "src_v2" / "lambdas"
    local_lambdas = [d.name for d in lambdas_dir.iterdir() if d.is_dir() and not d.name.startswith('.')] if lambdas_dir.exists() else []
    
    # Canonical local
    canonical_dir = repo_root / "canonical"
    canonical_files = list(canonical_dir.glob("**/*.yaml")) if canonical_dir.exists() else []
    
    print(f"\nOK Repo: {repo_root}")
    print(f"   Branch: {branch}")
    print(f"   Last commit: {commit_hash_short} - {commit_msg}")
    print(f"   Commit date: {commit_date}")
    print(f"   Uncommitted changes: {uncommitted}")
    print(f"\n   Local lambdas: {len(local_lambdas)}")
    for lam in sorted(local_lambdas):
        print(f"     - {lam}")
    print(f"\n   Local canonical files: {len(canonical_files)}")
    
    return {
        'branch': branch,
        'commit': commit_hash_short,
        'uncommitted': uncommitted,
        'lambdas': local_lambdas,
        'canonical_files': len(canonical_files)
    }

def generate_summary(results):
    """Génère un résumé de l'alignement"""
    print("\n" + "=" * 80)
    print("RÉSUMÉ ALIGNEMENT")
    print("=" * 80)
    
    issues = []
    
    # Lambdas
    lambdas_ok = sum(1 for r in results['lambdas'].values() if r.get('exists'))
    if lambdas_ok < len(LAMBDAS):
        issues.append(f"[MISSING] {len(LAMBDAS) - lambdas_ok}/{len(LAMBDAS)} Lambdas manquantes")
    else:
        print(f"\n[OK] Lambdas: {lambdas_ok}/{len(LAMBDAS)} deployees")
    
    # Layers
    if results['layers'].get('exists'):
        print(f"[OK] Layer: v{results['layers']['latest_version']}")
    else:
        issues.append("[MISSING] Layer manquant")
    
    # Canonical
    if results['canonical'].get('exists'):
        print(f"[OK] Canonical: {len(results['canonical']['versions'])} versions")
    else:
        issues.append("[MISSING] Canonical manquant")
    
    # Configs
    if results['client_configs'].get('exists'):
        print(f"[OK] Client configs: {results['client_configs']['count']}")
    else:
        issues.append("[MISSING] Client configs manquants")
    
    # Repo local
    if results['local']['uncommitted'] > 0:
        issues.append(f"[WARNING] {results['local']['uncommitted']} changements non commites")
    
    print(f"\n{'='*80}")
    if issues:
        print("[WARNING] PROBLEMES DETECTES:")
        for issue in issues:
            print(f"   {issue}")
        print("\n[FAIL] REPO ET AWS DEV NON ALIGNES")
    else:
        print("[OK] REPO ET AWS DEV ALIGNES")
    print(f"{'='*80}\n")
    
    return len(issues) == 0

def main():
    print(f"\n{'='*80}")
    print(f"VÉRIFICATION ALIGNEMENT REPO <-> AWS DEV")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Environment: {ENV}")
    print(f"{'='*80}\n")
    
    results = {
        'local': check_local_repo(),
        'lambdas': check_lambdas(),
        'layers': check_layers(),
        'canonical': check_canonical(),
        'client_configs': check_client_configs()
    }
    
    aligned = generate_summary(results)
    
    # Sauvegarder résultats
    output_file = Path(__file__).parent.parent / ".tmp" / "alignment_check.json"
    output_file.parent.mkdir(exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"Résultats sauvegardés: {output_file}")
    
    return 0 if aligned else 1

if __name__ == "__main__":
    sys.exit(main())
