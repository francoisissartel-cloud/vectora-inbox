# Annexes - Scripts Plan Gouvernance

**Date**: 2026-01-30  
**Lié à**: plan_gouvernance_repo_et_environnements.md

---

## ANNEXE A: build_layer_vectora_core.py

**Fichier**: `scripts/build/build_layer_vectora_core.py`

```python
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
    print(f"🔨 Building vectora-core layer version {version}")
    
    # Créer structure temporaire
    build_dir = Path('.build/layers/vectora-core-build')
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True)
    
    python_dir = build_dir / 'python'
    python_dir.mkdir()
    
    # Copier code source
    print("📦 Copying source code...")
    src_dir = Path('src_v2/vectora_core')
    if not src_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {src_dir}")
    
    shutil.copytree(src_dir, python_dir / 'vectora_core')
    
    # Créer archive ZIP
    output_file = Path(f'.build/layers/vectora-core-{version}.zip')
    print(f"📦 Creating ZIP archive: {output_file}")
    
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
    print(f"\n✅ Layer built successfully!")
    print(f"   File: {output_file}")
    print(f"   Version: {version}")
    print(f"   Size: {size_mb:.2f} MB")
    print(f"   SHA256: {checksum[:16]}...")
    
    return str(output_file), version, checksum

if __name__ == '__main__':
    try:
        build_layer()
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)
```

---

## ANNEXE B: deploy_layer.py

**Fichier**: `scripts/deploy/deploy_layer.py`

```python
#!/usr/bin/env python3
"""
Deploy layer vers environnement AWS
Usage: python scripts/deploy/deploy_layer.py --layer-file .build/layers/vectora-core-1.2.3.zip --env dev --layer-name vectora-inbox-vectora-core
"""
import argparse
import boto3
from pathlib import Path

def deploy_layer(layer_file, env, layer_name, dry_run=False):
    """Deploy layer vers AWS"""
    print(f"🚀 Deploying layer to {env}")
    print(f"   Layer file: {layer_file}")
    print(f"   Layer name: {layer_name}-{env}")
    
    if dry_run:
        print("   Mode: DRY RUN (no changes)")
        return
    
    # AWS clients
    session = boto3.Session(profile_name='rag-lai-prod', region_name='eu-west-3')
    s3 = session.client('s3')
    lambda_client = session.client('lambda')
    
    # Upload vers S3
    bucket = f'vectora-inbox-lambda-code-{env}'
    key = f'layers/{Path(layer_file).name}'
    
    print(f"📤 Uploading to s3://{bucket}/{key}")
    s3.upload_file(layer_file, bucket, key)
    
    # Publier layer
    print(f"📦 Publishing layer {layer_name}-{env}")
    
    # Extraire version du nom fichier
    version = Path(layer_file).stem.split('-')[-1]
    description = f"Built from repo - version {version}"
    
    response = lambda_client.publish_layer_version(
        LayerName=f'{layer_name}-{env}',
        Content={'S3Bucket': bucket, 'S3Key': key},
        CompatibleRuntimes=['python3.11', 'python3.12'],
        Description=description
    )
    
    arn = response['LayerVersionArn']
    layer_version = response['Version']
    
    print(f"\n✅ Layer deployed successfully!")
    print(f"   ARN: {arn}")
    print(f"   Version: {layer_version}")
    
    return arn

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Deploy layer to AWS')
    parser.add_argument('--layer-file', required=True, help='Path to layer ZIP file')
    parser.add_argument('--env', required=True, choices=['dev', 'stage', 'prod'], help='Environment')
    parser.add_argument('--layer-name', required=True, help='Layer name (without env suffix)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')
    
    args = parser.parse_args()
    
    try:
        deploy_layer(args.layer_file, args.env, args.layer_name, args.dry_run)
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)
```

---

## ANNEXE C: promote.py

**Fichier**: `scripts/deploy/promote.py`

```python
#!/usr/bin/env python3
"""
Promouvoir version entre environnements
Usage: python scripts/deploy/promote.py --to stage --version 1.2.3
"""
import argparse
import boto3
from pathlib import Path

def get_layer_arn(session, layer_name, env):
    """Récupérer ARN du layer le plus récent"""
    lambda_client = session.client('lambda')
    
    response = lambda_client.list_layer_versions(
        LayerName=f'{layer_name}-{env}',
        MaxItems=1
    )
    
    if not response['LayerVersions']:
        raise ValueError(f"No layer found: {layer_name}-{env}")
    
    return response['LayerVersions'][0]['LayerVersionArn']

def update_lambda_layers(session, function_name, new_layer_arns):
    """Mettre à jour layers d'une Lambda"""
    lambda_client = session.client('lambda')
    
    print(f"   Updating {function_name}")
    
    response = lambda_client.update_function_configuration(
        FunctionName=function_name,
        Layers=new_layer_arns
    )
    
    return response

def promote(from_env, to_env, version, dry_run=False):
    """Promouvoir version entre environnements"""
    print(f"🚀 Promoting from {from_env} to {to_env}")
    print(f"   Version: {version}")
    
    if dry_run:
        print("   Mode: DRY RUN (no changes)")
        return
    
    session = boto3.Session(profile_name='rag-lai-prod', region_name='eu-west-3')
    s3 = session.client('s3')
    lambda_client = session.client('lambda')
    
    # 1. Copier layers S3
    print("\n📦 Copying layers...")
    source_bucket = f'vectora-inbox-lambda-code-{from_env}'
    target_bucket = f'vectora-inbox-lambda-code-{to_env}'
    
    # Lister layers à copier
    layer_files = [
        f'layers/vectora-core-{version}.zip',
        f'layers/common-deps-{version}.zip'
    ]
    
    for layer_file in layer_files:
        print(f"   Copying {layer_file}")
        copy_source = {'Bucket': source_bucket, 'Key': layer_file}
        s3.copy_object(CopySource=copy_source, Bucket=target_bucket, Key=layer_file)
    
    # 2. Publier layers dans env cible
    print("\n📦 Publishing layers in target env...")
    
    layer_arns = []
    for layer_name in ['vectora-inbox-vectora-core', 'vectora-inbox-common-deps']:
        layer_file = f'layers/{layer_name.split("-")[-1]}-{version}.zip'
        
        response = lambda_client.publish_layer_version(
            LayerName=f'{layer_name}-{to_env}',
            Content={'S3Bucket': target_bucket, 'S3Key': layer_file},
            CompatibleRuntimes=['python3.11', 'python3.12'],
            Description=f'Promoted from {from_env} - version {version}'
        )
        
        layer_arns.append(response['LayerVersionArn'])
        print(f"   Published: {response['LayerVersionArn']}")
    
    # 3. Mettre à jour Lambdas
    print("\n🔄 Updating Lambdas...")
    
    lambdas = [
        f'vectora-inbox-ingest-v2-{to_env}',
        f'vectora-inbox-normalize-score-v2-{to_env}',
        f'vectora-inbox-newsletter-v2-{to_env}'
    ]
    
    for lambda_name in lambdas:
        update_lambda_layers(session, lambda_name, layer_arns)
    
    # 4. Copier canonical
    print("\n📄 Copying canonical...")
    
    # Sync canonical
    source_prefix = 'canonical/'
    
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=source_bucket, Prefix=source_prefix):
        for obj in page.get('Contents', []):
            source_key = obj['Key']
            copy_source = {'Bucket': source_bucket, 'Key': source_key}
            s3.copy_object(CopySource=copy_source, Bucket=target_bucket, Key=source_key)
            print(f"   Copied: {source_key}")
    
    print(f"\n✅ Promotion completed successfully!")
    print(f"   {from_env} → {to_env}")
    print(f"   Version: {version}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Promote version between environments')
    parser.add_argument('--from', dest='from_env', default='dev', choices=['dev', 'stage'], help='Source environment')
    parser.add_argument('--to', dest='to_env', required=True, choices=['stage', 'prod'], help='Target environment')
    parser.add_argument('--version', required=True, help='Version to promote')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')
    
    args = parser.parse_args()
    
    try:
        promote(args.from_env, args.to_env, args.version, args.dry_run)
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)
```

---

## ANNEXE D: build_all.py

**Fichier**: `scripts/build/build_all.py`

```python
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
    print("🔨 Building all artifacts...")
    
    scripts_dir = Path('scripts/build')
    
    # Build layers
    run_script(scripts_dir / 'build_layer_vectora_core.py')
    run_script(scripts_dir / 'build_layer_common_deps.py')
    
    print(f"\n{'='*60}")
    print("✅ All artifacts built successfully!")
    print('='*60)

if __name__ == '__main__':
    try:
        build_all()
    except Exception as e:
        print(f"\n❌ Build failed: {e}")
        exit(1)
```

---

## ANNEXE E: Modifications vectora-inbox-development-rules.md

**Sections à ajouter**:

### 1. Après "🏗️ ENVIRONNEMENT AWS DE RÉFÉRENCE"

```markdown
## 🚫 RÈGLES GOUVERNANCE (CRITIQUE)

### Source Unique de Vérité

**Principe**: Repo local = SEULE source de vérité

Toute modification du code, des layers, ou des configurations DOIT:
1. Être faite dans le repo local
2. Être commitée dans Git
3. Passer par les scripts build/deploy

### Interdiction Modification Directe AWS

❌ **INTERDIT**:
- `aws lambda update-function-code` (manuel)
- `aws s3 cp fichier.zip s3://...` (manuel)
- Édition dans console AWS
- Copie dev→stage sans scripts
- Création layers sans versioning

✅ **OBLIGATOIRE**:
- Modifier code dans repo local
- `python scripts/build/build_all.py`
- `python scripts/deploy/deploy_env.py --env dev`
- `python scripts/deploy/promote.py --to stage`

**Exception**: Debugging urgent avec validation post-facto obligatoire.

### Versioning Obligatoire

Chaque artefact a une version explicite dans fichier `VERSION`.

**Format**: MAJOR.MINOR.PATCH (ex: 1.2.3)

**Règles incrémentation**:
- MAJOR: Breaking changes
- MINOR: Nouvelles fonctionnalités
- PATCH: Corrections bugs

**Exemple**:
```
VECTORA_CORE_VERSION=1.2.3
# Nouvelle fonctionnalité → 1.3.0
# Correction bug → 1.2.4
# Breaking change → 2.0.0
```

### Workflow Standard

**Développement**:
1. Modifier code dans `src_v2/`
2. Incrémenter version dans `VERSION`
3. Build: `python scripts/build/build_all.py`
4. Deploy dev: `python scripts/deploy/deploy_env.py --env dev`
5. Test dev: `python scripts/test/test_e2e.py --env dev`

**Promotion**:
6. Promouvoir: `python scripts/deploy/promote.py --to stage --version X.Y.Z`
7. Test stage: `python scripts/test/test_e2e.py --env stage`

**Commit**:
8. `git add .`
9. `git commit -m "feat: description"`
10. `git push`
```

---

**Annexes Scripts - Version 1.0**  
**Date**: 2026-01-30  
**Lié à**: plan_gouvernance_repo_et_environnements.md
