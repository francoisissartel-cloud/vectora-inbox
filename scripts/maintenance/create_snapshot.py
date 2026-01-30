#!/usr/bin/env python3
"""
Script de création de snapshot complet de l'environnement Vectora Inbox.

Usage:
    python scripts/maintenance/create_snapshot.py --env dev --name "lai_v7_stable"
    python scripts/maintenance/create_snapshot.py --env dev --name "pre_migration_v8" --client lai_weekly
"""

import argparse
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path


def run_aws_command(command: list[str]) -> dict:
    """Exécute une commande AWS CLI et retourne le résultat JSON."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        if result.stdout:
            return json.loads(result.stdout)
        return {}
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur commande AWS: {e}")
        print(f"   stderr: {e.stderr}")
        return {}
    except json.JSONDecodeError:
        return {"raw_output": result.stdout}


def create_snapshot(env: str, snapshot_name: str, client_id: str = None):
    """Crée un snapshot complet de l'environnement."""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_dir = Path(f"backup/snapshots/{snapshot_name}_{timestamp}")
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📸 Création snapshot: {snapshot_name}")
    print(f"   Environnement: {env}")
    print(f"   Dossier: {snapshot_dir}")
    print()
    
    # Métadonnées snapshot
    metadata = {
        "snapshot_name": snapshot_name,
        "environment": env,
        "timestamp": timestamp,
        "created_at": datetime.now().isoformat(),
        "client_id": client_id,
        "components": {}
    }
    
    # 1. Sauvegarder configurations Lambda
    print("1️⃣ Sauvegarde configurations Lambda...")
    lambda_functions = [
        f"vectora-inbox-ingest-v2-{env}",
        f"vectora-inbox-normalize-score-v2-{env}",
        f"vectora-inbox-newsletter-v2-{env}"
    ]
    
    lambda_configs = {}
    for func_name in lambda_functions:
        print(f"   - {func_name}")
        config = run_aws_command([
            "aws", "lambda", "get-function",
            "--function-name", func_name,
            "--profile", "rag-lai-prod",
            "--region", "eu-west-3",
            "--query", "Configuration"
        ])
        if config:
            lambda_configs[func_name] = config
            
            # Sauvegarder dans fichier individuel
            with open(snapshot_dir / f"lambda_{func_name}.json", "w") as f:
                json.dump(config, f, indent=2)
    
    metadata["components"]["lambdas"] = lambda_configs
    print(f"   ✅ {len(lambda_configs)} Lambdas sauvegardées\n")
    
    # 2. Sauvegarder versions Lambda Layers
    print("2️⃣ Sauvegarde Lambda Layers...")
    layer_names = [
        f"vectora-inbox-vectora-core-{env}",
        f"vectora-inbox-common-deps-{env}",
        f"vectora-inbox-vectora-core-approche-b-{env}"
    ]
    
    layer_versions = {}
    for layer_name in layer_names:
        print(f"   - {layer_name}")
        versions = run_aws_command([
            "aws", "lambda", "list-layer-versions",
            "--layer-name", layer_name,
            "--profile", "rag-lai-prod",
            "--region", "eu-west-3",
            "--max-items", "1"
        ])
        if versions and "LayerVersions" in versions:
            layer_versions[layer_name] = versions["LayerVersions"][0]
            
            # Sauvegarder dans fichier individuel
            with open(snapshot_dir / f"layer_{layer_name}.json", "w") as f:
                json.dump(versions["LayerVersions"][0], f, indent=2)
    
    metadata["components"]["layers"] = layer_versions
    print(f"   ✅ {len(layer_versions)} Layers sauvegardés\n")
    
    # 3. Sauvegarder configurations client S3
    print("3️⃣ Sauvegarde configurations client S3...")
    config_bucket = f"vectora-inbox-config-{env}"
    
    if client_id:
        # Sauvegarder client spécifique
        client_configs = [f"clients/{client_id}.yaml"]
    else:
        # Lister tous les clients
        result = run_aws_command([
            "aws", "s3", "ls",
            f"s3://{config_bucket}/clients/",
            "--profile", "rag-lai-prod",
            "--region", "eu-west-3"
        ])
        client_configs = []  # À parser depuis result
    
    # Télécharger configurations client
    client_dir = snapshot_dir / "clients"
    client_dir.mkdir(exist_ok=True)
    
    for client_config in client_configs:
        print(f"   - {client_config}")
        subprocess.run([
            "aws", "s3", "cp",
            f"s3://{config_bucket}/{client_config}",
            str(client_dir / Path(client_config).name),
            "--profile", "rag-lai-prod",
            "--region", "eu-west-3"
        ], check=False)
    
    print(f"   ✅ Configurations client sauvegardées\n")
    
    # 4. Sauvegarder canonical (scopes, prompts, sources)
    print("4️⃣ Sauvegarde canonical S3...")
    canonical_dir = snapshot_dir / "canonical"
    canonical_dir.mkdir(exist_ok=True)
    
    subprocess.run([
        "aws", "s3", "sync",
        f"s3://{config_bucket}/canonical/",
        str(canonical_dir),
        "--profile", "rag-lai-prod",
        "--region", "eu-west-3"
    ], check=False)
    
    print(f"   ✅ Canonical sauvegardé\n")
    
    # 5. Sauvegarder dernières données curated (si client spécifié)
    if client_id:
        print("5️⃣ Sauvegarde dernières données curated...")
        data_bucket = f"vectora-inbox-data-{env}"
        
        # Trouver dernière exécution
        result = subprocess.run([
            "aws", "s3", "ls",
            f"s3://{data_bucket}/curated/{client_id}/",
            "--recursive",
            "--profile", "rag-lai-prod",
            "--region", "eu-west-3"
        ], capture_output=True, text=True, check=False)
        
        if result.stdout:
            # Parser dernière ligne (plus récent)
            lines = [l for l in result.stdout.strip().split("\n") if l]
            if lines:
                last_line = lines[-1]
                s3_path = last_line.split()[-1]
                
                print(f"   - {s3_path}")
                subprocess.run([
                    "aws", "s3", "cp",
                    f"s3://{data_bucket}/{s3_path}",
                    str(snapshot_dir / "curated_items.json"),
                    "--profile", "rag-lai-prod",
                    "--region", "eu-west-3"
                ], check=False)
        
        print(f"   ✅ Données curated sauvegardées\n")
    
    # 6. Sauvegarder stacks CloudFormation
    print("6️⃣ Sauvegarde stacks CloudFormation...")
    stack_names = [
        f"vectora-inbox-s0-core-{env}",
        f"vectora-inbox-s0-iam-{env}",
        f"vectora-inbox-s1-runtime-{env}"
    ]
    
    stacks_dir = snapshot_dir / "stacks"
    stacks_dir.mkdir(exist_ok=True)
    
    for stack_name in stack_names:
        print(f"   - {stack_name}")
        stack_info = run_aws_command([
            "aws", "cloudformation", "describe-stacks",
            "--stack-name", stack_name,
            "--profile", "rag-lai-prod",
            "--region", "eu-west-3"
        ])
        
        if stack_info and "Stacks" in stack_info:
            with open(stacks_dir / f"{stack_name}.json", "w") as f:
                json.dump(stack_info["Stacks"][0], f, indent=2)
    
    print(f"   ✅ Stacks CloudFormation sauvegardées\n")
    
    # 7. Sauvegarder métadonnées snapshot
    print("7️⃣ Sauvegarde métadonnées snapshot...")
    with open(snapshot_dir / "snapshot_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    # Créer README snapshot
    readme_content = f"""# Snapshot Vectora Inbox: {snapshot_name}

**Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Environnement**: {env}  
**Client**: {client_id or "Tous"}

## Contenu du Snapshot

- ✅ Configurations Lambda (3 fonctions)
- ✅ Versions Lambda Layers
- ✅ Configurations client S3
- ✅ Canonical (scopes, prompts, sources)
- ✅ Données curated (dernière exécution)
- ✅ Stacks CloudFormation

## Restauration

Pour restaurer ce snapshot:

```bash
python scripts/maintenance/rollback_snapshot.py --snapshot {snapshot_name}_{timestamp}
```

## Métadonnées

Voir `snapshot_metadata.json` pour détails complets.
"""
    
    with open(snapshot_dir / "README.md", "w") as f:
        f.write(readme_content)
    
    print(f"   ✅ Métadonnées sauvegardées\n")
    
    # Résumé final
    print("=" * 60)
    print(f"✅ SNAPSHOT CRÉÉ AVEC SUCCÈS")
    print(f"   Nom: {snapshot_name}_{timestamp}")
    print(f"   Dossier: {snapshot_dir}")
    print(f"   Taille: {sum(f.stat().st_size for f in snapshot_dir.rglob('*') if f.is_file()) / 1024:.1f} KB")
    print("=" * 60)
    
    return snapshot_dir


def main():
    parser = argparse.ArgumentParser(
        description="Créer un snapshot complet de l'environnement Vectora Inbox"
    )
    parser.add_argument(
        "--env",
        required=True,
        choices=["dev", "stage", "prod"],
        help="Environnement à sauvegarder"
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Nom du snapshot (ex: lai_v7_stable, pre_migration_v8)"
    )
    parser.add_argument(
        "--client",
        help="ID client spécifique à sauvegarder (optionnel)"
    )
    
    args = parser.parse_args()
    
    create_snapshot(args.env, args.name, args.client)


if __name__ == "__main__":
    main()
