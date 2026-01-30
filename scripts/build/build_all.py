#!/usr/bin/env python3
"""
Build tous les artefacts
Usage: python scripts/build/build_all.py
"""
import subprocess
import sys
from pathlib import Path

def run_script(script_path):
    """Exécuter un script Python"""
    print(f"\n{'='*60}")
    print(f"Running: {script_path}")
    print('='*60)
    
    result = subprocess.run([sys.executable, script_path], capture_output=False)
    
    if result.returncode != 0:
        raise RuntimeError(f"Script failed: {script_path}")

def build_all():
    """Build tous les artefacts"""
    print("[BUILD] Building all artifacts...")
    
    scripts_dir = Path('scripts/build')
    
    # Build layers
    run_script(scripts_dir / 'build_layer_vectora_core.py')
    run_script(scripts_dir / 'build_layer_common_deps.py')
    
    print(f"\n{'='*60}")
    print("[SUCCESS] All artifacts built successfully!")
    print('='*60)

if __name__ == '__main__':
    try:
        build_all()
    except Exception as e:
        print(f"\n[ERROR] Build failed: {e}")
        exit(1)
