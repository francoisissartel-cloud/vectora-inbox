#!/usr/bin/env python3
"""
Deploy complet vers environnement
Usage: python scripts/deploy/deploy_env.py --env dev [--dry-run]
"""
import argparse
import subprocess
import sys
from pathlib import Path

def get_version(artifact):
    """Lire version depuis fichier VERSION"""
    with open('VERSION') as f:
        for line in f:
            if line.startswith(f'{artifact}_VERSION='):
                return line.split('=')[1].strip()
    raise ValueError(f"{artifact}_VERSION not found in VERSION file")

def deploy_env(env, dry_run=False):
    """Deploy vers environnement"""
    print(f"[DEPLOY] Deploying to {env} environment")
    
    if dry_run:
        print("   Mode: DRY RUN (no changes)")
    
    # Récupérer versions
    vectora_core_version = get_version('VECTORA_CORE')
    common_deps_version = get_version('COMMON_DEPS')
    
    print(f"\n[INFO] Versions:")
    print(f"   vectora-core: {vectora_core_version}")
    print(f"   common-deps: {common_deps_version}")
    
    # Deploy vectora-core layer
    print(f"\n{'='*60}")
    print("Deploying vectora-core layer...")
    print('='*60)
    
    vectora_core_file = f'.build/layers/vectora-core-{vectora_core_version}.zip'
    if not Path(vectora_core_file).exists():
        raise FileNotFoundError(f"Layer file not found: {vectora_core_file}. Run 'python scripts/build/build_all.py' first.")
    
    cmd = [
        sys.executable, 'scripts/deploy/deploy_layer.py',
        '--layer-file', vectora_core_file,
        '--env', env,
        '--layer-name', 'vectora-inbox-vectora-core'
    ]
    if dry_run:
        cmd.append('--dry-run')
    
    subprocess.run(cmd, check=True)
    
    # Deploy common-deps layer
    print(f"\n{'='*60}")
    print("Deploying common-deps layer...")
    print('='*60)
    
    common_deps_file = f'.build/layers/common-deps-{common_deps_version}.zip'
    if not Path(common_deps_file).exists():
        raise FileNotFoundError(f"Layer file not found: {common_deps_file}. Run 'python scripts/build/build_all.py' first.")
    
    cmd = [
        sys.executable, 'scripts/deploy/deploy_layer.py',
        '--layer-file', common_deps_file,
        '--env', env,
        '--layer-name', 'vectora-inbox-common-deps'
    ]
    if dry_run:
        cmd.append('--dry-run')
    
    subprocess.run(cmd, check=True)
    
    print(f"\n{'='*60}")
    print(f"[SUCCESS] Deployment to {env} completed successfully!")
    print('='*60)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Deploy to environment')
    parser.add_argument('--env', required=True, choices=['dev', 'stage', 'prod'], help='Environment')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')
    
    args = parser.parse_args()
    
    try:
        deploy_env(args.env, args.dry_run)
    except Exception as e:
        print(f"\n[ERROR] Deployment failed: {e}")
        exit(1)
