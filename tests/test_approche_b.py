"""
Script de test pour valider l'Approche B - Prompts Pre-construits

Test l'implementation complete:
1. Chargement prompt template
2. Resolution references {{ref:}}
3. Construction prompt final
4. Comparaison avec V1
"""

import sys
import os
import yaml

# Ajouter src_v2 au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src_v2'))

from vectora_core.shared import prompt_resolver


def test_load_prompt_template():
    """Test 1: Chargement du prompt template"""
    print("\n" + "="*80)
    print("TEST 1: Chargement du prompt template")
    print("="*80)
    
    # Mock s3_io pour test local
    class MockS3IO:
        def load_yaml_from_s3(self, path):
            # Charger depuis fichier local
            local_path = os.path.join('canonical', 'prompts', 'normalization', 'lai_prompt.yaml')
            if os.path.exists(local_path):
                with open(local_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            return None
    
    mock_s3 = MockS3IO()
    prompt_template = prompt_resolver.load_prompt_template('normalization', 'lai', mock_s3)
    
    if prompt_template:
        print("[OK] Prompt template charge avec succes")
        print(f"   Vertical: {prompt_template.get('metadata', {}).get('vertical')}")
        print(f"   Version: {prompt_template.get('metadata', {}).get('version')}")
        print(f"   Description: {prompt_template.get('metadata', {}).get('description')}")
        return True, prompt_template
    else:
        print("[FAIL] Echec chargement prompt template")
        return False, None


def test_resolve_references(prompt_template):
    """Test 2: Resolution des references {{ref:}}"""
    print("\n" + "="*80)
    print("TEST 2: Resolution des references {{ref:}}")
    print("="*80)
    
    # Charger scopes canonical depuis fichier local
    canonical_scopes = {}
    
    # Charger technology_scopes.yaml
    tech_path = os.path.join('canonical', 'scopes', 'technology_scopes.yaml')
    if os.path.exists(tech_path):
        with open(tech_path, 'r', encoding='utf-8') as f:
            tech_data = yaml.safe_load(f)
            canonical_scopes['technologies'] = tech_data
    
    # Charger company_scopes.yaml
    company_path = os.path.join('canonical', 'scopes', 'company_scopes.yaml')
    if os.path.exists(company_path):
        with open(company_path, 'r', encoding='utf-8') as f:
            company_data = yaml.safe_load(f)
            canonical_scopes['companies'] = company_data
    
    # Charger molecule_scopes.yaml
    molecule_path = os.path.join('canonical', 'scopes', 'molecule_scopes.yaml')
    if os.path.exists(molecule_path):
        with open(molecule_path, 'r', encoding='utf-8') as f:
            molecule_data = yaml.safe_load(f)
            canonical_scopes['molecules'] = molecule_data
    
    # Charger trademark_scopes.yaml
    trademark_path = os.path.join('canonical', 'scopes', 'trademark_scopes.yaml')
    if os.path.exists(trademark_path):
        with open(trademark_path, 'r', encoding='utf-8') as f:
            trademark_data = yaml.safe_load(f)
            canonical_scopes['trademarks'] = trademark_data
    
    print(f"Scopes charges: {list(canonical_scopes.keys())}")
    
    # Test resolution d'une reference simple
    user_template = prompt_template.get('user_template', '')
    
    # Compter les references
    import re
    refs = re.findall(r'\{\{ref:([^}]+)\}\}', user_template)
    print(f"\nReferences trouvees dans le template: {len(refs)}")
    for ref in refs:
        print(f"  - {{{{ref:{ref}}}}}")
    
    # Resoudre les references
    resolved = prompt_resolver.resolve_references(user_template, canonical_scopes)
    
    # Verifier qu'il n'y a plus de references non resolues
    remaining_refs = re.findall(r'\{\{ref:([^}]+)\}\}', resolved)
    
    if len(remaining_refs) == 0:
        print(f"\n[OK] Toutes les references resolues ({len(refs)} references)")
        print(f"   Taille template original: {len(user_template)} caracteres")
        print(f"   Taille template resolu: {len(resolved)} caracteres")
        return True, resolved, canonical_scopes
    else:
        print(f"\n[FAIL] References non resolues: {remaining_refs}")
        return False, None, None


def test_build_prompt(prompt_template, canonical_scopes):
    """Test 3: Construction du prompt final"""
    print("\n" + "="*80)
    print("TEST 3: Construction du prompt final")
    print("="*80)
    
    # Variables de test
    test_item_text = """
    TITLE: MedinCell Announces Positive Phase 3 Results for UZEDY
    
    CONTENT: MedinCell, a pharmaceutical company specializing in long-acting injectable 
    formulations, today announced positive results from its Phase 3 clinical trial of UZEDY 
    (risperidone extended-release injectable suspension) for the treatment of schizophrenia. 
    The once-monthly subcutaneous injection demonstrated superior efficacy compared to placebo.
    """
    
    variables = {
        'item_text': test_item_text.strip()
    }
    
    # Construire le prompt
    final_prompt = prompt_resolver.build_prompt(
        prompt_template,
        canonical_scopes,
        variables
    )
    
    # Verifications
    checks = [
        ('item_text substitue', test_item_text.strip() in final_prompt),
        ('Pas de {{ref:}} restant', '{{ref:' not in final_prompt),
        ('Pas de {{item_text}} restant', '{{item_text}}' not in final_prompt),
        ('Contient "MedinCell"', 'MedinCell' in final_prompt),
        ('Contient "UZEDY"', 'UZEDY' in final_prompt)
    ]
    
    all_passed = all(check[1] for check in checks)
    
    print("\nVerifications:")
    for check_name, passed in checks:
        status = "[OK]" if passed else "[FAIL]"
        print(f"  {status} {check_name}")
    
    print(f"\nTaille prompt final: {len(final_prompt)} caracteres")
    print(f"Nombre de lignes: {len(final_prompt.splitlines())}")
    
    if all_passed:
        print("\n[OK] Prompt final construit avec succes")
        
        # Afficher un extrait du prompt
        print("\n--- EXTRAIT DU PROMPT (200 premiers caracteres) ---")
        print(final_prompt[:200] + "...")
        print("--- FIN EXTRAIT ---")
        
        return True, final_prompt
    else:
        print("\n[FAIL] Echec construction prompt final")
        return False, None


def test_compare_with_v1(final_prompt):
    """Test 4: Comparaison avec V1 (hardcode)"""
    print("\n" + "="*80)
    print("TEST 4: Comparaison avec V1")
    print("="*80)
    
    # Elements cles qui doivent etre presents (comme dans V1)
    v1_elements = [
        'LAI TECHNOLOGY FOCUS',
        'Long-Acting Injectable',
        'long-acting injectable',  # Version minuscule depuis core_phrases
        'extended-release injection',  # Version depuis core_phrases
        'depot injection',  # Version minuscule depuis core_phrases
        'TASK:',
        'RESPONSE FORMAT',
        'JSON only'
    ]
    
    print("\nVerification presence elements V1:")
    all_present = True
    for element in v1_elements:
        present = element in final_prompt
        status = "[OK]" if present else "[FAIL]"
        print(f"  {status} {element}")
        if not present:
            all_present = False
    
    if all_present:
        print("\n[OK] Tous les elements V1 presents dans Approche B")
        print("   -> Compatibilite V1 assuree")
        return True
    else:
        print("\n[WARN] Certains elements V1 manquants")
        print("   -> Verifier compatibilite")
        return False


def run_all_tests():
    """Execute tous les tests"""
    print("\n" + "="*80)
    print("TESTS APPROCHE B - PROMPTS PRE-CONSTRUITS")
    print("="*80)
    print("Client: lai_weekly_v5")
    print("Date: 2025-12-23")
    
    results = {}
    
    # Test 1: Chargement
    success, prompt_template = test_load_prompt_template()
    results['load_template'] = success
    
    if not success:
        print("\n[FAIL] ECHEC: Impossible de continuer sans prompt template")
        return results
    
    # Test 2: Resolution references
    success, resolved, canonical_scopes = test_resolve_references(prompt_template)
    results['resolve_references'] = success
    
    if not success:
        print("\n[FAIL] ECHEC: Impossible de continuer sans resolution des references")
        return results
    
    # Test 3: Construction prompt
    success, final_prompt = test_build_prompt(prompt_template, canonical_scopes)
    results['build_prompt'] = success
    
    if not success:
        print("\n[FAIL] ECHEC: Impossible de continuer sans prompt final")
        return results
    
    # Test 4: Comparaison V1
    success = test_compare_with_v1(final_prompt)
    results['compare_v1'] = success
    
    # Resume final
    print("\n" + "="*80)
    print("RESUME DES TESTS")
    print("="*80)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for test_name, passed_test in results.items():
        status = "[OK] PASS" if passed_test else "[FAIL] FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nResultat: {passed}/{total} tests reussis")
    
    if passed == total:
        print("\n[SUCCESS] TOUS LES TESTS REUSSIS - APPROCHE B VALIDEE")
    else:
        print(f"\n[WARN] {total - passed} test(s) echoue(s)")
    
    return results


if __name__ == "__main__":
    results = run_all_tests()
    
    # Code de sortie
    all_passed = all(results.values())
    sys.exit(0 if all_passed else 1)
