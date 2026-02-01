#!/usr/bin/env python3
"""
Script de build de tous les Lambda Layers.
Conforme aux règles de gestion des layers V2.
"""

import os
import sys
import json
import shutil
import zipfile
import subprocess
from pathlib import Path
from datetime import datetime

# Configuration
AWS_PROFILE = "rag-lai-prod"
AWS_REGION = "eu-west-3"

def log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)

def get_git_info():
    """Récupère les informations Git actuelles"""
    try:
        sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True).strip()
        
        try:
            tag = subprocess.check_output(["git", "describe", "--exact-match", "--tags", "HEAD"], text=True).strip()
        except:
            tag = None
        
        return {"sha": sha, "branch": branch, "tag": tag}
    except Exception as e:
        log(f"[WARNING] Impossible de recuperer info Git: {e}")
        return {"sha": "unknown", "branch": "unknown", "tag": None}

def read_version(layer_name):
    """Lit la version depuis le fichier VERSION"""
    version_file = Path("VERSION")
    
    if not version_file.exists():
        log("[ERROR] Fichier VERSION non trouve")
        sys.exit(1)
    
    with open(version_file, "r") as f:
        for line in f:
            if layer_name.upper() in line:
                return line.split("=")[1].strip()
    
    log(f"[ERROR] Version {layer_name} non trouvee dans VERSION")
    sys.exit(1)

def build_vectora_core():
    """Build layer vectora-core"""
    log("=== Build vectora-core ===")
    
    version = read_version("VECTORA_CORE_VERSION")
    log(f"Version: {version}")
    
    workspace = Path(".build/workspace/vectora-core")
    workspace.mkdir(parents=True, exist_ok=True)
    
    python_dir = workspace / "python"
    python_dir.mkdir(exist_ok=True)
    
    src_core = Path("src_v2/vectora_core")
    dest_core = python_dir / "vectora_core"
    
    if dest_core.exists():
        shutil.rmtree(dest_core)
    
    shutil.copytree(src_core, dest_core)
    log("[OK] vectora_core copie")
    
    zip_name = f"vectora-core-{version}.zip"
    zip_path = Path(".build/layers") / zip_name
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in python_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(workspace)
                zipf.write(file_path, arcname)
    
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    log(f"[OK] Layer cree: {zip_name} ({size_mb:.1f}MB)")
    
    return {
        "layer_name": "vectora-core",
        "version": version,
        "zip_path": str(zip_path),
        "size_mb": round(size_mb, 2)
    }

def build_common_deps():
    """Build layer common-deps"""
    log("=== Build common-deps ===")
    
    version = read_version("COMMON_DEPS_VERSION")
    log(f"Version: {version}")
    
    workspace = Path(".build/workspace/common-deps")
    workspace.mkdir(parents=True, exist_ok=True)
    
    python_dir = workspace / "python"
    python_dir.mkdir(exist_ok=True)
    
    requirements = Path("src_v2/requirements.txt")
    if not requirements.exists():
        log(f"[ERROR] requirements.txt non trouve: {requirements}")
        sys.exit(1)
    
    log("Installation dependances...")
    pip_cmd = f"pip install -r {requirements} -t {python_dir} --quiet --no-binary PyYAML"
    result = subprocess.run(pip_cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        log(f"[ERROR] Installation echouee: {result.stderr}")
        sys.exit(1)
    
    log("[OK] Dependances installees")
    
    for pattern in ["*.dist-info", "__pycache__", "*.pyc"]:
        for path in python_dir.rglob(pattern):
            if path.is_dir():
                shutil.rmtree(path)
            elif path.is_file():
                path.unlink()
    
    zip_name = f"common-deps-{version}.zip"
    zip_path = Path(".build/layers") / zip_name
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in python_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(workspace)
                zipf.write(file_path, arcname)
    
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    log(f"[OK] Layer cree: {zip_name} ({size_mb:.1f}MB)")
    
    return {
        "layer_name": "common-deps",
        "version": version,
        "zip_path": str(zip_path),
        "size_mb": round(size_mb, 2)
    }

def create_manifest(layers_info):
    """Crée le manifest.json global"""
    git_info = get_git_info()
    
    manifest = {
        "build_date": datetime.now().isoformat(),
        "git_sha": git_info["sha"],
        "git_branch": git_info["branch"],
        "git_tag": git_info["tag"],
        "layers": layers_info
    }
    
    manifest_path = Path(".build/layers/manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    log(f"[OK] Manifest cree: {manifest_path}")
    return manifest

def main():
    log("=== Build All Lambda Layers ===")
    
    try:
        layers_info = []
        
        log("\n[1/2] Build vectora-core")
        vectora_core_info = build_vectora_core()
        layers_info.append(vectora_core_info)
        
        log("\n[2/2] Build common-deps")
        common_deps_info = build_common_deps()
        layers_info.append(common_deps_info)
        
        log("\n[3/3] Creation manifest")
        manifest = create_manifest(layers_info)
        
        log("\n[SUCCESS] BUILD TERMINE")
        log("\nLayers crees:")
        for layer in layers_info:
            log(f"  - {layer['layer_name']}-{layer['version']}.zip ({layer['size_mb']}MB)")
        
        log(f"\nGit SHA: {manifest['git_sha'][:8]}")
        log(f"Git Branch: {manifest['git_branch']}")
        if manifest['git_tag']:
            log(f"Git Tag: {manifest['git_tag']}")
        
        log("\nProchaines etapes:")
        log("1. python scripts/layers/deploy_layer.py --layer all --env dev")
        log("2. python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7")
        
    except Exception as e:
        log(f"[ERROR] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
