#!/usr/bin/env python3
"""
Build vectora-core layer avec versioning
Usage: python scripts/build/build_layer_vectora_core.py
"""
import os
import shutil
import zipfile
import hashlib
from pathlib import Path
from datetime import datetime

def get_version():
    """Lire version depuis fichier VERSION"""
    with open('VERSION') as f:
        for line in f:
            if line.startswith('VECTORA_CORE_VERSION='):
                return line.split('=')[1].strip()
    raise ValueError("VECTORA_CORE_VERSION not found in VERSION file")

def calculate_sha256(file_path):
    """Calculer SHA256 d'un fichier"""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def build_layer():
    """Build layer vectora-core"""
    version = get_version()
    print(f"[BUILD] Building vectora-core layer version {version}")
    
    # Créer structure temporaire
    build_dir = Path('.build/layers/vectora-core-build')
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True)
    
    python_dir = build_dir / 'python'
    python_dir.mkdir()
    
    # Copier code source
    print("[BUILD] Copying source code...")
    src_dir = Path('src_v2/vectora_core')
    if not src_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {src_dir}")
    
    shutil.copytree(src_dir, python_dir / 'vectora_core')
    
    # Créer archive ZIP
    output_file = Path(f'.build/layers/vectora-core-{version}.zip')
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
