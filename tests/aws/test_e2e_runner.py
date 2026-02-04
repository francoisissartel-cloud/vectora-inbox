#!/usr/bin/env python3
"""
Runner unifié pour tests E2E AWS avec validation obligatoire du test local.
BLOQUE le déploiement AWS si aucun test local n'a réussi.
"""

import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
REGISTRY_PATH = PROJECT_ROOT / "tests" / "contexts" / "registry.json"
CONTEXTS_AWS_DIR = PROJECT_ROOT / "tests" / "contexts" / "aws"
CONTEXTS_LOCAL_DIR = PROJECT_ROOT / "tests" / "contexts" / "local"

AWS_PROFILE = "rag-lai-prod"
AWS_REGION = "eu-west-3"

# Import config generator
sys.path.insert(0, str(PROJECT_ROOT))
from tests.utils.config_generator import generate_test_config, save_config
import boto3
import yaml

def load_registry():
    """Charge le registre des contextes."""
    with open(REGISTRY_PATH) as f:
        return json.load(f)

def save_registry(registry):
    """Sauvegarde le registre."""
    with open(REGISTRY_PATH, 'w') as f:
        json.dump(registry, f, indent=2)

def check_local_success():
    """Vérifie qu'un test local a réussi avant AWS."""
    registry = load_registry()
    
    if not registry['rules']['aws_deploy_blocked_without_local_success']:
        print("⚠️  Règle de blocage désactivée (non recommandé)")
        return True, None
    
    current_local = registry['contexts']['local'].get('current')
    if not current_local:
        print("\n" + "="*80)
        print("❌ DÉPLOIEMENT AWS BLOQUÉ")
        print("="*80)
        print("Raison: Aucun test local exécuté")
        print("\nActions requises:")
        print("1. Créer contexte: python tests/local/test_e2e_runner.py --new-context 'description'")
        print("2. Exécuter test: python tests/local/test_e2e_runner.py --run")
        print("3. Vérifier succès: python tests/local/test_e2e_runner.py --status")
        print("4. Revenir ici si succès")
        print("="*80)
        return False, None
    
    # Vérifier succès du test local
    for entry in registry['contexts']['local']['history']:
        if entry['id'] == current_local:
            if entry['success'] is True:
                print(f"[OK] Test local valide: {current_local}")
                return True, current_local
            else:
                print("\n" + "="*80)
                print("❌ DÉPLOIEMENT AWS BLOQUÉ")
                print("="*80)
                print(f"Raison: Test local {current_local} n'a pas réussi")
                print(f"Status: {entry.get('status', 'unknown')}")
                print("\nActions requises:")
                print("1. Corriger les erreurs du test local")
                print("2. Ré-exécuter: python tests/local/test_e2e_runner.py --run")
                print("3. Revenir ici si succès")
                print("="*80)
                return False, None
    
    return False, None

def create_aws_context(local_context_id, purpose):
    """Crée un contexte AWS promu depuis un contexte local."""
    registry = load_registry()
    
    # Trouver prochain vX
    existing_v = []
    for c in registry['contexts']['aws']['history']:
        if 'client_id' in c and c['client_id'].startswith('lai_weekly_v'):
            try:
                v = int(c['client_id'].replace('lai_weekly_v', ''))
                existing_v.append(v)
            except ValueError:
                pass
    
    next_v = max(existing_v, default=0) + 1
    next_num = len(registry['contexts']['aws']['history']) + 1
    context_id = f"test_context_{next_num:03d}"
    client_id = f"lai_weekly_v{next_v}"
    
    # Récupérer client_id local
    local_context_file = CONTEXTS_LOCAL_DIR / f"{local_context_id}.json"
    with open(local_context_file) as f:
        local_ctx = json.load(f)
    local_client_id = local_ctx.get('client_id', 'unknown')
    
    context = {
        "id": context_id,
        "created": datetime.now().isoformat(),
        "purpose": purpose,
        "status": "created",
        "success": None,
        "promoted_from_local": local_context_id,
        "client_id": client_id,
        "results": None
    }
    
    # Générer client_config
    template_path = PROJECT_ROOT / "client-config-examples" / "templates" / "lai_weekly_template.yaml"
    config = generate_test_config(
        template_path=str(template_path),
        client_id=client_id,
        context_id=context_id,
        purpose=purpose,
        environment="aws_dev",
        promoted_from=local_client_id
    )
    
    # Sauvegarder config localement
    config_file = PROJECT_ROOT / "client-config-examples" / "test" / "aws" / f"{context_id}.yaml"
    save_config(config, str(config_file))
    context['client_config_file'] = str(config_file)
    
    # Upload vers S3
    s3_path = upload_config_to_s3(config, client_id, env="dev")
    context['s3_config_path'] = s3_path
    
    # Sauvegarder contexte
    context_file = CONTEXTS_AWS_DIR / f"{context_id}.json"
    context_file.parent.mkdir(parents=True, exist_ok=True)
    with open(context_file, 'w') as f:
        json.dump(context, f, indent=2)
    
    # Mettre à jour registre
    registry['contexts']['aws']['current'] = context_id
    registry['contexts']['aws']['history'].append({
        "id": context_id,
        "created": context['created'],
        "purpose": purpose,
        "status": "created",
        "success": None,
        "promoted_from_local": local_context_id,
        "client_id": client_id
    })
    registry['last_updated'] = datetime.now().isoformat()
    save_registry(registry)
    
    print(f"[OK] Contexte AWS cree: {context_id}")
    print(f"   Client ID: {context['client_id']}")
    print(f"   Promu depuis: {local_context_id}")
    print(f"   Config local: {config_file}")
    print(f"   Config S3: {s3_path}")
    
    return context

def upload_config_to_s3(config: dict, client_id: str, env: str) -> str:
    """Upload config vers S3."""
    s3 = boto3.client('s3', region_name=AWS_REGION)
    bucket = f"vectora-inbox-config-{env}"
    key = f"clients/{client_id}.yaml"
    
    config_yaml = yaml.dump(config, default_flow_style=False, sort_keys=False)
    
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=config_yaml.encode('utf-8'),
        ContentType='application/x-yaml'
    )
    
    s3_path = f"s3://{bucket}/{key}"
    print(f"[OK] Config uploaded to {s3_path}")
    return s3_path

def update_context_status(context_id, status, success=None, results=None):
    """Met à jour le statut d'un contexte AWS."""
    context_file = CONTEXTS_AWS_DIR / f"{context_id}.json"
    with open(context_file) as f:
        context = json.load(f)
    
    context['status'] = status
    if success is not None:
        context['success'] = success
    if results:
        context['results'] = results
    context['updated'] = datetime.now().isoformat()
    
    with open(context_file, 'w') as f:
        json.dump(context, f, indent=2)
    
    # Mettre à jour registre
    registry = load_registry()
    for entry in registry['contexts']['aws']['history']:
        if entry['id'] == context_id:
            entry['status'] = status
            entry['success'] = success
            break
    registry['last_updated'] = datetime.now().isoformat()
    save_registry(registry)

def run_aws_e2e_test(context):
    """Exécute le test E2E sur AWS."""
    print(f"\n{'='*80}")
    print(f"[AWS] TEST E2E AWS - {context['id']}")
    print(f"{'='*80}")
    print(f"Client ID: {context['client_id']}")
    print(f"Purpose: {context['purpose']}")
    print(f"Promu depuis: {context['promoted_from_local']}")
    print()
    
    client_id = context['client_id']
    
    try:
        # Invoke workflow E2E complet
        print(f"[RUN] Invocation workflow E2E complet (ingest -> normalize -> newsletter)...")
        result = subprocess.run(
            [
                sys.executable,
                "scripts/invoke/invoke_e2e_workflow.py",
                "--client-id", client_id,
                "--env", "dev"
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=900  # 15 min max
        )
        
        # Afficher output
        if result.stdout:
            print(result.stdout)
        
        if result.returncode == 0:
            print(f"[OK] Workflow E2E AWS reussi")
            update_context_status(
                context['id'],
                'completed',
                success=True,
                results={'timestamp': datetime.now().isoformat()}
            )
            return True
        else:
            print(f"[FAIL] Workflow E2E AWS echoue")
            if result.stderr:
                print(result.stderr)
            update_context_status(context['id'], 'failed', success=False)
            return False
    
    except Exception as e:
        print(f"[FAIL] Erreur: {e}")
        update_context_status(context['id'], 'failed', success=False)
        return False

def main():
    parser = argparse.ArgumentParser(description="Runner unifié tests E2E AWS")
    parser.add_argument("--promote", metavar="PURPOSE", help="Promouvoir contexte local vers AWS")
    parser.add_argument("--run", action="store_true", help="Exécuter test AWS sur contexte actuel")
    parser.add_argument("--status", action="store_true", help="Afficher statut contexte AWS actuel")
    parser.add_argument("--list", action="store_true", help="Lister tous les contextes AWS")
    parser.add_argument("--force", action="store_true", help="Forcer (ignorer validation locale - NON RECOMMANDÉ)")
    
    args = parser.parse_args()
    
    if args.promote:
        # Vérifier test local
        if not args.force:
            success, local_context = check_local_success()
            if not success:
                sys.exit(1)
        else:
            print("⚠️  Mode FORCE activé - validation locale ignorée")
            local_context = "forced"
        
        # Créer contexte AWS
        context = create_aws_context(local_context, args.promote)
        print("\n[OK] Contexte AWS pret. Executez maintenant:")
        print(f"   python tests/aws/test_e2e_runner.py --run")
    
    elif args.run:
        registry = load_registry()
        context_id = registry['contexts']['aws'].get('current')
        
        if not context_id:
            print("❌ Aucun contexte AWS actif. Créez-en un avec --promote")
            sys.exit(1)
        
        context_file = CONTEXTS_AWS_DIR / f"{context_id}.json"
        with open(context_file) as f:
            context = json.load(f)
        
        success = run_aws_e2e_test(context)
        sys.exit(0 if success else 1)
    
    elif args.status:
        registry = load_registry()
        context_id = registry['contexts']['aws'].get('current')
        
        if context_id:
            context_file = CONTEXTS_AWS_DIR / f"{context_id}.json"
            with open(context_file) as f:
                context = json.load(f)
            
            print(f"\n📊 Contexte AWS actuel: {context['id']}")
            print(f"   Client ID: {context['client_id']}")
            print(f"   Purpose: {context['purpose']}")
            print(f"   Status: {context['status']}")
            print(f"   Success: {context.get('success', 'N/A')}")
            print(f"   Promu depuis: {context['promoted_from_local']}")
        else:
            print("❌ Aucun contexte AWS actif")
    
    elif args.list:
        registry = load_registry()
        print("\n📋 Historique contextes AWS:")
        for entry in reversed(registry['contexts']['aws']['history']):
            status_icon = "✅" if entry.get('success') else "❌" if entry.get('success') is False else "⏳"
            print(f"   {status_icon} {entry['id']} - {entry['purpose']} (from {entry['promoted_from_local']})")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
