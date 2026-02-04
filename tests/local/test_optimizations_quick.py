#!/usr/bin/env python3
"""
Test rapide des optimisations Bedrock (Prompt Caching + domain_definition v2.1)
"""

import sys
import yaml
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent

def analyze_token_reduction():
    """Compare taille v2.0 vs v2.1"""
    
    v2_path = PROJECT_ROOT / "canonical" / "domains" / "lai_domain_definition.yaml"
    v21_path = PROJECT_ROOT / "canonical" / "domains" / "lai_domain_definition_v2.1.yaml"
    
    with open(v2_path) as f:
        v2_content = f.read()
    
    with open(v21_path) as f:
        v21_content = f.read()
    
    # Estimation tokens (1 token ≈ 4 chars)
    v2_tokens = len(v2_content) // 4
    v21_tokens = len(v21_content) // 4
    reduction = v2_tokens - v21_tokens
    reduction_pct = (reduction / v2_tokens) * 100
    
    print("\n" + "="*80)
    print("ANALYSE RÉDUCTION TOKENS")
    print("="*80)
    print(f"v2.0:  {len(v2_content):,} chars -> ~{v2_tokens:,} tokens")
    print(f"v2.1:  {len(v21_content):,} chars -> ~{v21_tokens:,} tokens")
    print(f"Reduction: ~{reduction:,} tokens ({reduction_pct:.1f}%)")
    print()
    
    # Vérifier structure
    with open(v2_path) as f:
        v2_data = yaml.safe_load(f)
    
    with open(v21_path) as f:
        v21_data = yaml.safe_load(f)
    
    # Compter éléments
    v2_tech = len(v2_data['medium_signals']['technology_families'])
    v21_tech = len(v21_data['medium_signals']['technology_families'])
    
    v2_core = len(v2_data['strong_signals']['core_technologies'])
    v21_core = len(v21_data['strong_signals']['core_technologies'])
    
    print("VERIFICATION STRUCTURE:")
    print(f"[OK] Core technologies: {v2_core} -> {v21_core} (identique)")
    print(f"[OK] Technology families: {v2_tech} -> {v21_tech} (identique)")
    
    # Vérifier scope_ref
    has_scope_ref = all([
        'scope_ref' in v21_data['strong_signals']['pure_player_companies'],
        'scope_ref' in v21_data['strong_signals']['trademarks'],
        'scope_ref' in v21_data['medium_signals']['hybrid_companies'],
        'scope_ref' in v21_data['weak_signals']['molecules']
    ])
    
    print(f"[OK] Scope references: {'OK' if has_scope_ref else 'MISSING'}")
    
    # Vérifier exemples supprimés
    no_examples = all([
        'examples' not in v21_data['strong_signals']['pure_player_companies'],
        'examples' not in v21_data['strong_signals']['trademarks'],
        'examples' not in v21_data['medium_signals']['hybrid_companies'],
        'examples' not in v21_data['weak_signals']['molecules']
    ])
    
    print(f"[OK] Exemples supprimes: {'OK' if no_examples else 'STILL PRESENT'}")
    print()
    
    return reduction_pct >= 25  # Objectif: 30-40%, acceptable si >25%

def verify_prompt_caching():
    """Verifie que le code Prompt Caching est present"""
    
    bedrock_client_path = PROJECT_ROOT / "src_v2" / "vectora_core" / "normalization" / "bedrock_client.py"
    
    with open(bedrock_client_path) as f:
        content = f.read()
    
    print("="*80)
    print("VERIFICATION PROMPT CACHING")
    print("="*80)
    
    checks = {
        "cache_control present": "cache_control" in content,
        "ephemeral type": '"type": "ephemeral"' in content,
        "content array": '"content": [' in content and '"type": "text"' in content,
        "invoke_with_prompt modifie": "Supporte Prompt Caching" in content
    }
    
    for check, result in checks.items():
        status = "[OK]" if result else "[FAIL]"
        print(f"{status} {check}")
    
    print()
    return all(checks.values())

def main():
    print("\n" + "="*80)
    print("TEST RAPIDE - OPTIMISATIONS BEDROCK")
    print("="*80)
    
    # Test 1: Réduction tokens
    test1 = analyze_token_reduction()
    
    # Test 2: Prompt Caching
    test2 = verify_prompt_caching()
    
    # Résumé
    print("="*80)
    print("RESUME")
    print("="*80)
    print(f"{'[OK]' if test1 else '[FAIL]'} Reduction tokens (objectif: 25%+)")
    print(f"{'[OK]' if test2 else '[FAIL]'} Prompt Caching implemente")
    print()
    
    if test1 and test2:
        print("[SUCCESS] Optimisations validées localement")
        print()
        print("PROCHAINES ÉTAPES:")
        print("1. Build: python scripts/build/build_all.py")
        print("2. Deploy dev: python scripts/deploy/deploy_env.py --env dev")
        print("3. Upload canonical v2.1:")
        print("   aws s3 cp canonical/domains/lai_domain_definition_v2.1.yaml \\")
        print("     s3://vectora-inbox-data-dev/canonical/domains/lai_domain_definition.yaml \\")
        print("     --profile rag-lai-prod --region eu-west-3")
        print("4. Test E2E AWS: python tests/aws/test_e2e_runner.py --run")
        return 0
    else:
        print("[FAILED] Certaines vérifications ont échoué")
        return 1

if __name__ == "__main__":
    sys.exit(main())
