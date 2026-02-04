#!/usr/bin/env python3
"""
Runner unifié pour tests E2E locaux avec gestion automatique des contextes.
Empêche la réutilisation de données anciennes et force la création de nouveaux contextes.
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
REGISTRY_PATH = PROJECT_ROOT / "tests" / "contexts" / "registry.json"
CONTEXTS_LOCAL_DIR = PROJECT_ROOT / "tests" / "contexts" / "local"

# Import config generator
sys.path.insert(0, str(PROJECT_ROOT))
from tests.utils.config_generator import generate_test_config, save_config

def load_registry():
    """Charge le registre des contextes."""
    if not REGISTRY_PATH.exists():
        return {
            "version": "1.0.0",
            "contexts": {"local": {"current": None, "history": []}, "aws": {"current": None, "history": []}},
            "rules": {"local_test_required": True, "aws_deploy_blocked_without_local_success": True}
        }
    with open(REGISTRY_PATH) as f:
        return json.load(f)

def save_registry(registry):
    """Sauvegarde le registre."""
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_PATH, 'w') as f:
        json.dump(registry, f, indent=2)

def create_new_context(purpose, base_client="lai_weekly"):
    """Crée un nouveau contexte de test local."""
    registry = load_registry()
    
    # Trouver le prochain numéro
    existing = [int(c['id'].split('_')[-1]) for c in registry['contexts']['local']['history'] if c['id'].startswith('test_context_')]
    next_num = max(existing, default=0) + 1
    context_id = f"test_context_{next_num:03d}"
    client_id = f"{base_client}_test_{next_num:03d}"
    
    context = {
        "id": context_id,
        "created": datetime.now().isoformat(),
        "purpose": purpose,
        "status": "created",
        "success": None,
        "client_id": client_id,
        "test_items": [],
        "results": None
    }
    
    # Générer client_config
    template_path = PROJECT_ROOT / "client-config-examples" / "templates" / "lai_weekly_template.yaml"
    config = generate_test_config(
        template_path=str(template_path),
        client_id=client_id,
        context_id=context_id,
        purpose=purpose,
        environment="local"
    )
    
    # Sauvegarder config
    config_file = PROJECT_ROOT / "client-config-examples" / "test" / "local" / f"{context_id}.yaml"
    save_config(config, str(config_file))
    context['client_config_file'] = str(config_file)
    
    # Sauvegarder contexte
    context_file = CONTEXTS_LOCAL_DIR / f"{context_id}.json"
    context_file.parent.mkdir(parents=True, exist_ok=True)
    with open(context_file, 'w') as f:
        json.dump(context, f, indent=2)
    
    # Mettre à jour registre
    registry['contexts']['local']['current'] = context_id
    registry['contexts']['local']['history'].append({
        "id": context_id,
        "created": context['created'],
        "purpose": purpose,
        "status": "created",
        "success": None
    })
    registry['last_updated'] = datetime.now().isoformat()
    save_registry(registry)
    
    print(f"[OK] Nouveau contexte cree: {context_id}")
    print(f"   Client ID: {context['client_id']}")
    print(f"   Purpose: {purpose}")
    print(f"   Fichier: {context_file}")
    print(f"   Config: {config_file}")
    
    return context

def get_current_context():
    """Récupère le contexte local actuel."""
    registry = load_registry()
    context_id = registry['contexts']['local'].get('current')
    
    if not context_id:
        print("[ERROR] Aucun contexte actif. Creez-en un avec --new-context")
        return None
    
    context_file = CONTEXTS_LOCAL_DIR / f"{context_id}.json"
    if not context_file.exists():
        print(f"[ERROR] Fichier contexte introuvable: {context_file}")
        return None
    
    with open(context_file) as f:
        return json.load(f)

def update_context_status(context_id, status, success=None, results=None):
    """Met à jour le statut d'un contexte."""
    context_file = CONTEXTS_LOCAL_DIR / f"{context_id}.json"
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
    for entry in registry['contexts']['local']['history']:
        if entry['id'] == context_id:
            entry['status'] = status
            entry['success'] = success
            break
    registry['last_updated'] = datetime.now().isoformat()
    save_registry(registry)

def run_local_e2e_test(context, test_type="complete"):
    """Exécute le test E2E local."""
    print(f"\n{'='*80}")
    print(f"[TEST] E2E LOCAL - {context['id']}")
    print(f"{'='*80}")
    print(f"Client ID: {context['client_id']}")
    print(f"Purpose: {context['purpose']}")
    print(f"Test type: {test_type}")
    print()
    
    # Importer et exécuter le test
    sys.path.insert(0, str(PROJECT_ROOT / "src_v2"))
    
    if test_type == "complete":
        from tests.local.test_e2e_domain_scoring_complete import test_e2e_domain_scoring_complete
        success = test_e2e_domain_scoring_complete()
    else:
        print(f"[ERROR] Type de test inconnu: {test_type}")
        return False
    
    # Mettre à jour contexte
    update_context_status(
        context['id'],
        status='completed' if success else 'failed',
        success=success,
        results={'test_type': test_type, 'timestamp': datetime.now().isoformat()}
    )
    
    return success

def check_local_success_before_aws():
    """Vérifie qu'un test local a réussi avant de permettre le déploiement AWS."""
    registry = load_registry()
    
    if not registry['rules']['local_test_required']:
        return True
    
    current_local = registry['contexts']['local'].get('current')
    if not current_local:
        print("[BLOCKED] Aucun test local execute")
        print("   Executez d'abord: python tests/local/test_e2e_runner.py --new-context 'description'")
        return False
    
    # Vérifier succès
    for entry in registry['contexts']['local']['history']:
        if entry['id'] == current_local:
            if entry['success'] is True:
                print(f"[OK] Test local {current_local} valide avec succes")
                return True
            else:
                print(f"[BLOCKED] Test local {current_local} n'a pas reussi")
                print("   Corrigez les erreurs avant de deployer sur AWS")
                return False
    
    return False

def main():
    parser = argparse.ArgumentParser(description="Runner unifié tests E2E locaux")
    parser.add_argument("--new-context", metavar="PURPOSE", help="Créer nouveau contexte de test")
    parser.add_argument("--run", action="store_true", help="Exécuter test sur contexte actuel")
    parser.add_argument("--status", action="store_true", help="Afficher statut contexte actuel")
    parser.add_argument("--list", action="store_true", help="Lister tous les contextes")
    parser.add_argument("--test-type", default="complete", choices=["complete", "quick"], help="Type de test")
    
    args = parser.parse_args()
    
    if args.new_context:
        create_new_context(args.new_context)
    
    elif args.run:
        context = get_current_context()
        if context:
            success = run_local_e2e_test(context, args.test_type)
            sys.exit(0 if success else 1)
    
    elif args.status:
        context = get_current_context()
        if context:
            print(f"\n[STATUS] Contexte actuel: {context['id']}")
            print(f"   Client ID: {context['client_id']}")
            print(f"   Purpose: {context['purpose']}")
            print(f"   Status: {context['status']}")
            print(f"   Success: {context.get('success', 'N/A')}")
            print(f"   Created: {context['created']}")
    
    elif args.list:
        registry = load_registry()
        print("\n[LIST] Historique contextes locaux:")
        for entry in reversed(registry['contexts']['local']['history']):
            status_icon = "[OK]" if entry.get('success') else "[FAIL]" if entry.get('success') is False else "[PEND]"
            print(f"   {status_icon} {entry['id']} - {entry['purpose']} ({entry['status']})")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
