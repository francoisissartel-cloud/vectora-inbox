#!/usr/bin/env python3
"""
Script de validation des configurations de sources V3
Detecte automatiquement les limitations temporelles dangereuses
"""

import yaml
import re
import sys
from pathlib import Path

def validate_source_configs():
    """Valide toutes les configurations de sources pour detecter les limitations temporelles"""
    
    config_path = Path("canonical/ingestion/source_configs_v3.yaml")
    
    if not config_path.exists():
        print(f"ERREUR: {config_path} introuvable")
        return False
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    sources = config.get('sources', {})
    issues_found = []
    
    # Patterns dangereux a detecter
    year_patterns = [
        r'202[0-9]',  # 2020-2029
        r'/202[0-9]/',  # /2024/, /2025/, etc.
        r'year-202[0-9]',  # year-2024, etc.
    ]
    
    print("VALIDATION DES CONFIGURATIONS DE SOURCES")
    print("=" * 60)
    
    for source_key, source_config in sources.items():
        if not isinstance(source_config, dict):
            continue
            
        print(f"\nValidation: {source_key}")
        
        # Verifier les listing_selectors
        listing_selectors = source_config.get('listing_selectors', {})
        if listing_selectors:
            
            # Verifier container
            container = listing_selectors.get('container', '')
            if container:
                for pattern in year_patterns:
                    if re.search(pattern, container):
                        issue = f"ERREUR {source_key}: container contient une limitation temporelle: '{container}'"
                        issues_found.append(issue)
                        print(f"  {issue}")
            
            # Verifier url_pattern
            url_pattern = listing_selectors.get('url_pattern', '')
            if url_pattern:
                for pattern in year_patterns:
                    if re.search(pattern, url_pattern):
                        issue = f"ERREUR {source_key}: url_pattern contient une limitation temporelle: '{url_pattern}'"
                        issues_found.append(issue)
                        print(f"  {issue}")
        
        # Verifier date_selectors
        date_selectors = source_config.get('date_selectors', {})
        if date_selectors:
            css_selector = date_selectors.get('css', '')
            if css_selector:
                for pattern in year_patterns:
                    if re.search(pattern, css_selector):
                        issue = f"ERREUR {source_key}: date_selectors.css contient une limitation temporelle: '{css_selector}'"
                        issues_found.append(issue)
                        print(f"  {issue}")
        
        # Si pas d'issues trouvees pour cette source
        if not any(source_key in issue for issue in issues_found):
            print(f"  Configuration OK")
    
    print("\n" + "=" * 60)
    print("RESUME DE LA VALIDATION")
    print("=" * 60)
    
    if issues_found:
        print(f"PROBLEMES CRITIQUES DETECTES: {len(issues_found)}")
        for issue in issues_found:
            print(f"  {issue}")
        
        print("\nACTIONS REQUISES:")
        print("1. Corriger les patterns identifies")
        print("2. Utiliser des patterns generiques sans annee")
        print("3. Re-tester avec --period-days 200")
        print("4. Verifier que les articles anciens sont trouves")
        
        return False
    else:
        print("TOUTES LES CONFIGURATIONS SONT VALIDES")
        print("Aucune limitation temporelle detectee")
        return True

def main():
    """Point d'entree principal"""
    print("VALIDATION DES CONFIGURATIONS DE SOURCES V3")
    print("Detection des limitations temporelles dangereuses")
    print()
    
    is_valid = validate_source_configs()
    
    if not is_valid:
        print("\nVALIDATION ECHOUEE - Corrections requises")
        sys.exit(1)
    else:
        print("\nVALIDATION REUSSIE - Configurations OK")
        sys.exit(0)

if __name__ == "__main__":
    main()