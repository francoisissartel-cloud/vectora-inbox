"""
Script de test local pour valider le chargement des scopes d'ingestion.
Verifie que tous les scopes sont correctement charges depuis les fichiers YAML.
"""

import sys
import os
import yaml
from pathlib import Path

# Ajouter le chemin src_v2 au PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src_v2"))

def test_exclusion_scopes():
    """Test du chargement des exclusion scopes."""
    print("\n=== Test Exclusion Scopes ===")
    
    yaml_path = project_root / "canonical" / "scopes" / "exclusion_scopes.yaml"
    
    with open(yaml_path, 'r', encoding='utf-8') as f:
        scopes = yaml.safe_load(f)
    
    expected_scopes = [
        'hr_content', 'financial_generic', 'hr_recruitment_terms', 
        'financial_reporting_terms', 'esg_generic', 'event_generic', 
        'corporate_noise_terms', 'anti_lai_routes'
    ]
    
    print(f"[OK] Fichier charge: {yaml_path}")
    print(f"[OK] Nombre de categories: {len(scopes)}")
    
    for scope_name in expected_scopes:
        if scope_name in scopes:
            terms = scopes[scope_name]
            if isinstance(terms, list):
                print(f"  [OK] Scope '{scope_name}': {len(terms)} termes")
            else:
                print(f"  [FAIL] Scope '{scope_name}': Format invalide")
        else:
            print(f"  [FAIL] Scope '{scope_name}': MANQUANT")
    
    total_terms = 0
    for scope_name in expected_scopes:
        if scope_name in scopes and isinstance(scopes[scope_name], list):
            total_terms += len(scopes[scope_name])
    
    print(f"\n[OK] Total termes d'exclusion: {total_terms}")
    return total_terms > 0

def test_company_scopes():
    """Test du chargement des company scopes."""
    print("\n=== Test Company Scopes ===")
    
    yaml_path = project_root / "canonical" / "scopes" / "company_scopes.yaml"
    
    with open(yaml_path, 'r', encoding='utf-8') as f:
        scopes = yaml.safe_load(f)
    
    pure_players = scopes.get('lai_companies_pure_players', [])
    hybrid_players = scopes.get('lai_companies_hybrid', [])
    
    print(f"[OK] Fichier charge: {yaml_path}")
    print(f"[OK] Pure players: {len(pure_players)} entreprises")
    print(f"  Exemples: {', '.join(pure_players[:5])}")
    print(f"[OK] Hybrid players: {len(hybrid_players)} entreprises")
    print(f"  Exemples: {', '.join(hybrid_players[:5])}")
    
    expected_pure = ['MedinCell', 'Camurus', 'DelSiTech', 'Nanexa', 'Peptron']
    expected_hybrid = ['Teva Pharmaceutical', 'AbbVie', 'Novartis', 'Pfizer']
    
    for company in expected_pure:
        if company in pure_players:
            print(f"  [OK] Pure player '{company}' trouve")
        else:
            print(f"  [FAIL] Pure player '{company}' MANQUANT")
    
    for company in expected_hybrid:
        if company in hybrid_players:
            print(f"  [OK] Hybrid player '{company}' trouve")
        else:
            print(f"  [WARN] Hybrid player '{company}' non trouve")
    
    return len(pure_players) > 0 and len(hybrid_players) > 0

def test_lai_keywords():
    """Test du chargement des LAI keywords."""
    print("\n=== Test LAI Keywords ===")
    
    tech_yaml_path = project_root / "canonical" / "scopes" / "technology_scopes.yaml"
    trademark_yaml_path = project_root / "canonical" / "scopes" / "trademark_scopes.yaml"
    
    with open(tech_yaml_path, 'r', encoding='utf-8') as f:
        tech_scopes = yaml.safe_load(f)
    
    with open(trademark_yaml_path, 'r', encoding='utf-8') as f:
        trademark_scopes = yaml.safe_load(f)
    
    print(f"[OK] Fichier technology_scopes charge")
    print(f"[OK] Fichier trademark_scopes charge")
    
    keywords = []
    lai_keywords_section = tech_scopes.get('lai_keywords', {})
    
    for scope in ['core_phrases', 'technology_terms_high_precision', 'interval_patterns']:
        scope_terms = lai_keywords_section.get(scope, [])
        keywords.extend(scope_terms)
        print(f"  [OK] Scope '{scope}': {len(scope_terms)} termes")
    
    trademarks = trademark_scopes.get('lai_trademarks_global', [])
    keywords.extend(trademarks)
    print(f"  [OK] Trademarks: {len(trademarks)} termes")
    
    print(f"\n[OK] Total LAI keywords: {len(keywords)}")
    print(f"  Exemples: {', '.join(str(k) for k in keywords[:10])}")
    
    return len(keywords) > 0

def test_ingestion_profiles_import():
    """Test de l'import du module ingestion_profiles."""
    print("\n=== Test Import Module ===")
    
    try:
        from vectora_core.ingest import ingestion_profiles
        print("[OK] Module ingestion_profiles importe")
        
        functions = [
            'initialize_exclusion_scopes',
            'initialize_company_scopes',
            'initialize_lai_keywords',
            '_is_pure_player',
            '_is_hybrid_player',
            '_filter_by_exclusions_only',
            '_filter_by_exclusions_and_lai'
        ]
        
        for func_name in functions:
            if hasattr(ingestion_profiles, func_name):
                print(f"  [OK] Fonction '{func_name}' trouvee")
            else:
                print(f"  [FAIL] Fonction '{func_name}' MANQUANTE")
                return False
        
        return True
    except Exception as e:
        print(f"[FAIL] Erreur d'import: {e}")
        return False

def main():
    """Execute tous les tests."""
    print("=" * 60)
    print("Test Local - Chargement Scopes Ingestion v1.7.0")
    print("=" * 60)
    
    results = {
        'exclusion_scopes': test_exclusion_scopes(),
        'company_scopes': test_company_scopes(),
        'lai_keywords': test_lai_keywords(),
        'module_import': test_ingestion_profiles_import()
    }
    
    print("\n" + "=" * 60)
    print("Resume des Tests")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n[SUCCESS] Tous les tests sont passes!")
        print("\nProchaines etapes:")
        print("1. Build layer: python scripts/layers/build_vectora_core_layer.py --env dev")
        print("2. Deploy layer: python scripts/deploy/deploy_vectora_core_layer.py --env dev")
        print("3. Test E2E: python scripts/invoke/invoke_ingest_v2.py --client-id lai_weekly_v24 --env dev")
        return 0
    else:
        print("\n[ERROR] Certains tests ont echoue.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
