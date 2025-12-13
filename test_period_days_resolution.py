#!/usr/bin/env python3
"""
Test local de la résolution de period_days.

Ce script teste la nouvelle logique de résolution de la période temporelle
selon la hiérarchie : payload > client_config > fallback global.
"""

import sys
import os
import yaml
import json
from typing import Dict, Any, Optional

# Ajouter le chemin vers vectora_core
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from vectora_core.utils.config_utils import resolve_period_days


def load_client_config(client_id: str) -> Dict[str, Any]:
    """Charge une configuration client depuis les exemples."""
    config_path = f"client-config-examples/{client_id}.yaml"
    
    if not os.path.exists(config_path):
        print(f"Configuration {config_path} non trouvee")
        return {}
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def test_resolution_case(
    case_name: str,
    payload_period_days: Optional[int],
    client_config: Dict[str, Any],
    expected: int
):
    """Teste un cas de résolution et affiche le résultat."""
    print(f"\n=== {case_name} ===")
    print(f"Payload period_days: {payload_period_days}")
    
    pipeline_config = client_config.get('pipeline', {})
    client_default = pipeline_config.get('default_period_days')
    print(f"Client default_period_days: {client_default}")
    
    result = resolve_period_days(payload_period_days, client_config)
    print(f"Résultat: {result} jours")
    print(f"Attendu: {expected} jours")
    
    if result == expected:
        print("SUCCES")
    else:
        print("ECHEC")
    
    return result == expected


def main():
    """Exécute tous les tests de résolution."""
    print("Test de la resolution de period_days")
    print("=" * 50)
    
    # Charger les configurations
    lai_weekly_v2 = load_client_config("lai_weekly_v2")
    template_v2 = load_client_config("client_template_v2")
    empty_config = {}
    
    # Tests
    tests = [
        # Test 1: Override payload avec LAI Weekly v2
        ("Override payload (LAI Weekly v2)", 7, lai_weekly_v2, 7),
        
        # Test 2: Configuration client LAI Weekly v2
        ("Config client (LAI Weekly v2)", None, lai_weekly_v2, 30),
        
        # Test 3: Configuration client template v2
        ("Config client (Template v2)", None, template_v2, 7),
        
        # Test 4: Fallback global
        ("Fallback global", None, empty_config, 7),
        
        # Test 5: Payload invalide
        ("Payload invalide", -5, lai_weekly_v2, 30),
        
        # Test 6: Config client invalide
        ("Config client invalide", None, {"pipeline": {"default_period_days": "invalid"}}, 7),
    ]
    
    # Exécuter les tests
    success_count = 0
    total_count = len(tests)
    
    for case_name, payload, config, expected in tests:
        if test_resolution_case(case_name, payload, config, expected):
            success_count += 1
    
    # Résumé
    print(f"\n{'=' * 50}")
    print(f"Resultats: {success_count}/{total_count} tests reussis")
    
    if success_count == total_count:
        print("Tous les tests sont passes !")
        return 0
    else:
        print("Certains tests ont echoue")
        return 1


if __name__ == "__main__":
    sys.exit(main())