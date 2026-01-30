#!/usr/bin/env python3
"""
Build common-deps layer avec versioning
Usage: python scripts/build/build_layer_common_deps.py
"""
import os
import shutil
import zipfile
import hashlib
import subprocess
import sys
from pathlib import Path

def get_version():
    """Lire version depuis fichier VERSION"""
    with open('VERSION') as f:
        for line in f:
            if line.startswith('COMMON_DEPS_VERSION='):
                return line.split('=')[1].strip()
    raise ValueError("COMMON_DEPS_VERSION not found in VERSION file")

def calculate_sha256(file_path):
    """Calculer SHA256 d'un fichier"""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def build_layer():
    """Build layer common-deps"""
    version = get_version()
    print(f"[BUILD] Building common-deps layer version {version}")
    
    # Créer structure temporaire
    build_dir = Path('.build/layers/common-deps-build')
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True)
    
    python_dir = build_dir / 'python'
    python_dir.mkdir()
    
    # Installer dépendances
    print("[BUILD] Installing dependencies...")
    requirements_file = Path('src_v2/requirements.txt')
    if not requirements_file.exists():
        raise FileNotFoundError(f"Requirements file not found: {requirements_file}")
    
    subprocess.run([
        sys.executable, '-m', 'pip', 'install',
        '-r', str(requirements_file),
        '-t', str(python_dir),
        '--upgrade'
    ], check=True)
    
    # Créer archive ZIP
    output_file = Path(f'.build/layers/common-deps-{version}.zip')
    print(f"[BUILD] Creating ZIP archive: {output_file}")
    
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(build_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(build_dir)
                zipf.write(file_path, arcname)
    
    # Calculer checksum
    checksum = calculate_sha256(output_file)
    size_mb = output_file.stat().st_size / (1024 * 1024)
    
    # Nettoyer
    shutil.rmtree(build_dir)
    
    # Résumé
    print(f"\n[SUCCESS] Layer built successfully!")
    print(f"   File: {output_file}")
    print(f"   Version: {version}")
    print(f"   Size: {size_mb:.2f} MB")
    print(f"   SHA256: {checksum[:16]}...")
    
    return str(output_file), version, checksum

if __name__ == '__main__':
    try:
        build_layer()
    except Exception as e:
        print(f"[ERROR] {e}")
        exit(1)
