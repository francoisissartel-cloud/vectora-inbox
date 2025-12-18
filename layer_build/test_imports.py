#!/usr/bin/env python3
"""Test des imports critiques pour validation du layer"""

import sys
import os

# Ajouter le répertoire python au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

def test_critical_imports():
    """Test tous les imports critiques"""
    
    results = {}
    
    # Test PyYAML
    try:
        import yaml
        test_data = {"test": "value"}
        yaml_str = yaml.dump(test_data)
        parsed = yaml.safe_load(yaml_str)
        results['yaml'] = f"[OK] Version: {getattr(yaml, '__version__', 'unknown')}"
    except Exception as e:
        results['yaml'] = f"[FAILED] {str(e)}"
    
    # Test requests
    try:
        import requests
        results['requests'] = f"[OK] Version: {requests.__version__}"
    except Exception as e:
        results['requests'] = f"[FAILED] {str(e)}"
    
    # Test feedparser
    try:
        import feedparser
        results['feedparser'] = f"[OK] Version: {getattr(feedparser, '__version__', 'unknown')}"
    except Exception as e:
        results['feedparser'] = f"[FAILED] {str(e)}"
    
    # Test beautifulsoup4
    try:
        import bs4
        results['beautifulsoup4'] = f"[OK] Version: {bs4.__version__}"
    except Exception as e:
        results['beautifulsoup4'] = f"[FAILED] {str(e)}"
    
    return results

if __name__ == "__main__":
    print("Test des imports critiques du layer...")
    results = test_critical_imports()
    
    for package, status in results.items():
        print(f"{package}: {status}")
    
    # Vérifier si tous les tests passent
    all_passed = all("[OK]" in status for status in results.values())
    
    if all_passed:
        print("\n[SUCCESS] TOUS LES IMPORTS RÉUSSIS - Layer prêt")
        exit(0)
    else:
        print("\n[ERROR] CERTAINS IMPORTS ÉCHOUÉS - Layer à corriger")
        exit(1)