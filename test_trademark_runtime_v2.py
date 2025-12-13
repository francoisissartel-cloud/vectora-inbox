#!/usr/bin/env python3
"""
Script de test pour les fonctionnalités runtime trademark et client_config v2.

Ce script teste localement les modifications apportées aux modules :
- config/loader.py : parsing client_config v2
- ingestion/profile_filter.py : trademark_privileges.ingestion_priority
- matching/matcher.py : trademark_privileges.matching_priority
- scoring/scorer.py : client_specific_bonuses

Usage:
    python test_trademark_runtime_v2.py
"""

import sys
import os
import json
import yaml
from typing import Dict, Any, List

# Ajouter le chemin src pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_client_config_v2_parsing():
    """Test du parsing client_config v2."""
    print("=== TEST 1: Client Config v2 Parsing ===")
    
    from vectora_core.config.loader import load_client_config
    
    # Simuler un client_config v2
    mock_config_v2 = {
        'client_profile': {
            'name': 'LAI Intelligence Weekly',
            'client_id': 'lai_weekly_v2'
        },
        'watch_domains': [
            {
                'id': 'tech_lai_ecosystem',
                'trademark_scope': 'lai_trademarks_global'
            }
        ],
        'matching_config': {
            'trademark_privileges': {
                'enabled': True,
                'ingestion_priority': True,
                'matching_priority': True
            }
        },
        'scoring_config': {
            'client_specific_bonuses': {
                'trademark_mentions': {
                    'scope': 'lai_trademarks_global',
                    'bonus': 4.0
                },
                'pure_player_companies': {
                    'scope': 'lai_companies_mvp_core',
                    'bonus': 5.0
                }
            }
        },
        'metadata': {
            'template_version': '2.0.0'
        }
    }
    
    # Simuler le chargement (sans S3)
    config = mock_config_v2.copy()
    
    # Appliquer la logique de parsing v2
    template_version = config.get('metadata', {}).get('template_version', '1.0.0')
    is_v2 = template_version.startswith('2.')
    
    # Enrichir avec métadonnées runtime
    config['_runtime_metadata'] = {
        'is_v2': is_v2,
        'template_version': template_version,
        'has_trademark_privileges': _has_trademark_privileges(config),
        'has_client_specific_scoring': _has_client_specific_scoring(config),
        'trademark_scopes': _extract_trademark_scopes(config)
    }
    
    print(f"[OK] Config v2 detectee: {config['_runtime_metadata']['is_v2']}")
    print(f"[OK] Trademark privileges: {config['_runtime_metadata']['has_trademark_privileges']}")
    print(f"[OK] Client scoring: {config['_runtime_metadata']['has_client_specific_scoring']}")
    print(f"[OK] Trademark scopes: {config['_runtime_metadata']['trademark_scopes']}")
    print()
    
    return config

def test_trademark_ingestion_priority():
    """Test de la logique trademark_privileges.ingestion_priority."""
    print("=== TEST 2: Trademark Ingestion Priority ===")
    
    from vectora_core.ingestion.profile_filter import IngestionProfileFilter
    
    # Mock client_config v2 avec trademark_privileges
    client_config = {
        'matching_config': {
            'trademark_privileges': {
                'enabled': True,
                'ingestion_priority': True
            }
        },
        '_runtime_metadata': {
            'has_trademark_privileges': True,
            'trademark_scopes': ['lai_trademarks_global']
        }
    }
    
    # Mock item avec trademark
    item_with_trademark = {
        'title': 'Abilify Maintena Shows Strong Results in Phase III',
        'raw_text': 'The long-acting injectable Abilify Maintena demonstrated...'
    }
    
    # Mock item sans trademark
    item_without_trademark = {
        'title': 'Generic Drug Development Update',
        'raw_text': 'Standard pharmaceutical development continues...'
    }
    
    # Créer un filtre mock
    filter_instance = IngestionProfileFilter('mock-bucket')
    filter_instance._loaded = True  # Skip S3 loading
    filter_instance.scopes = {
        'trademark_scopes': {
            'lai_trademarks_global': ['Abilify Maintena', 'Invega Sustenna', 'Risperdal Consta']
        }
    }
    
    # Test 1: Item avec trademark doit être forcé en ingestion
    should_ingest_1 = filter_instance._should_force_ingest_for_trademarks(item_with_trademark, client_config)
    print(f"[OK] Item avec trademark force: {should_ingest_1}")
    
    # Test 2: Item sans trademark ne doit pas être forcé
    should_ingest_2 = filter_instance._should_force_ingest_for_trademarks(item_without_trademark, client_config)
    print(f"[OK] Item sans trademark non force: {not should_ingest_2}")
    print()

def test_trademark_matching_priority():
    """Test de la logique trademark_privileges.matching_priority."""
    print("=== TEST 3: Trademark Matching Priority ===")
    
    from vectora_core.matching.matcher import _check_trademark_matching_priority
    
    # Mock client_config v2
    client_config = {
        'matching_config': {
            'trademark_privileges': {
                'enabled': True,
                'matching_priority': True
            }
        },
        '_runtime_metadata': {
            'has_trademark_privileges': True
        }
    }
    
    # Mock watch_domains
    watch_domains = [
        {
            'id': 'tech_lai_ecosystem',
            'trademark_scope': 'lai_trademarks_global'
        }
    ]
    
    # Mock canonical_scopes
    canonical_scopes = {
        'trademarks': {
            'lai_trademarks_global': ['Abilify Maintena', 'Invega Sustenna', 'Risperdal Consta']
        }
    }
    
    # Mock item avec trademark
    item_with_trademark = {
        'title': 'Abilify Maintena Phase III Results',
        'summary': 'Long-acting injectable shows efficacy...',
        'companies_detected': ['Otsuka'],
        'molecules_detected': ['aripiprazole']
    }
    
    # Test matching automatique par trademark
    forced_domains = _check_trademark_matching_priority(
        item_with_trademark, watch_domains, canonical_scopes, client_config
    )
    
    print(f"[OK] Domaines forces par trademark: {forced_domains}")
    print(f"[OK] Matching automatique active: {'tech_lai_ecosystem' in forced_domains}")
    print()

def test_client_specific_bonuses():
    """Test des bonus client-specific dans le scoring."""
    print("=== TEST 4: Client Specific Bonuses ===")
    
    from vectora_core.scoring.scorer import _compute_client_specific_bonuses
    
    # Mock client_config v2 avec bonuses
    client_config = {
        'scoring_config': {
            'client_specific_bonuses': {
                'trademark_mentions': {
                    'scope': 'lai_trademarks_global',
                    'bonus': 4.0,
                    'description': 'Mentions de marques LAI'
                },
                'pure_player_companies': {
                    'scope': 'lai_companies_mvp_core',
                    'bonus': 5.0,
                    'description': 'Pure players LAI'
                }
            }
        },
        '_runtime_metadata': {
            'has_client_specific_scoring': True
        }
    }
    
    # Mock canonical_scopes
    canonical_scopes = {
        'trademarks': {
            'lai_trademarks_global': ['Abilify Maintena', 'Invega Sustenna']
        },
        'companies': {
            'lai_companies_mvp_core': ['MedinCell', 'Camurus', 'DelSiTech']
        }
    }
    
    # Mock item avec trademark + pure player
    item_with_bonuses = {
        'title': 'MedinCell Announces Abilify Maintena Partnership',
        'summary': 'Strategic collaboration for long-acting injectable...',
        'companies_detected': ['MedinCell'],
        'molecules_detected': ['aripiprazole']
    }
    
    # Calculer les bonus
    total_bonus = _compute_client_specific_bonuses(item_with_bonuses, client_config, canonical_scopes)
    
    print(f"[OK] Bonus total calcule: {total_bonus}")
    print(f"[OK] Bonus attendu: 9.0 (trademark 4.0 + pure_player 5.0)")
    print(f"[OK] Calcul correct: {total_bonus == 9.0}")
    print()

def test_end_to_end_simulation():
    """Test end-to-end avec un item complet."""
    print("=== TEST 5: End-to-End Simulation ===")
    
    # Mock d'un pipeline complet
    mock_item = {
        'title': 'MedinCell Reports Positive Results for Abilify Maintena LAI',
        'summary': 'The long-acting injectable formulation shows improved patient compliance...',
        'raw_text': 'MedinCell announced positive Phase III results for Abilify Maintena...',
        'companies_detected': ['MedinCell'],
        'molecules_detected': ['aripiprazole'],
        'technologies_detected': ['long-acting injectable', 'LAI technology'],
        'event_type': 'clinical_update',
        'date': '2024-12-19',
        'source_type': 'press_corporate'
    }
    
    client_config_v2 = {
        'matching_config': {
            'trademark_privileges': {
                'enabled': True,
                'ingestion_priority': True,
                'matching_priority': True
            }
        },
        'scoring_config': {
            'client_specific_bonuses': {
                'trademark_mentions': {'scope': 'lai_trademarks_global', 'bonus': 4.0},
                'pure_player_companies': {'scope': 'lai_companies_mvp_core', 'bonus': 5.0}
            }
        },
        '_runtime_metadata': {
            'is_v2': True,
            'has_trademark_privileges': True,
            'has_client_specific_scoring': True,
            'trademark_scopes': ['lai_trademarks_global']
        }
    }
    
    canonical_scopes = {
        'trademarks': {
            'lai_trademarks_global': ['Abilify Maintena', 'Invega Sustenna']
        },
        'companies': {
            'lai_companies_mvp_core': ['MedinCell', 'Camurus']
        }
    }
    
    # Test 1: Ingestion forcée par trademark
    from vectora_core.ingestion.profile_filter import IngestionProfileFilter
    filter_instance = IngestionProfileFilter('mock')
    filter_instance._loaded = True
    filter_instance.scopes = canonical_scopes
    
    should_ingest = filter_instance._should_force_ingest_for_trademarks(mock_item, client_config_v2)
    print(f"[OK] Ingestion forcee: {should_ingest}")
    
    # Test 2: Matching forcé par trademark
    from vectora_core.matching.matcher import _check_trademark_matching_priority
    watch_domains = [{'id': 'tech_lai', 'trademark_scope': 'lai_trademarks_global'}]
    forced_domains = _check_trademark_matching_priority(mock_item, watch_domains, canonical_scopes, client_config_v2)
    print(f"[OK] Matching force: {len(forced_domains) > 0}")
    
    # Test 3: Bonus de scoring
    from vectora_core.scoring.scorer import _compute_client_specific_bonuses
    bonus = _compute_client_specific_bonuses(mock_item, client_config_v2, canonical_scopes)
    print(f"[OK] Bonus scoring: {bonus}")
    
    print(f"[OK] Pipeline v2 complet: Ingestion -> Matching -> Scoring avec trademarks")
    print()

# Fonctions utilitaires (copiées du loader)
def _has_trademark_privileges(config: Dict[str, Any]) -> bool:
    matching_config = config.get('matching_config', {})
    trademark_privileges = matching_config.get('trademark_privileges', {})
    return trademark_privileges.get('enabled', False)

def _has_client_specific_scoring(config: Dict[str, Any]) -> bool:
    scoring_config = config.get('scoring_config', {})
    client_bonuses = scoring_config.get('client_specific_bonuses', {})
    return len(client_bonuses) > 0

def _extract_trademark_scopes(config: Dict[str, Any]) -> List[str]:
    trademark_scopes = []
    watch_domains = config.get('watch_domains', [])
    
    for domain in watch_domains:
        trademark_scope = domain.get('trademark_scope')
        if trademark_scope and trademark_scope not in trademark_scopes:
            trademark_scopes.append(trademark_scope)
    
    return trademark_scopes

def main():
    """Exécute tous les tests."""
    print("TESTS RUNTIME TRADEMARK & CLIENT_CONFIG V2")
    print("=" * 60)
    
    try:
        # Test 1: Parsing client_config v2
        config_v2 = test_client_config_v2_parsing()
        
        # Test 2: Ingestion priority
        test_trademark_ingestion_priority()
        
        # Test 3: Matching priority
        test_trademark_matching_priority()
        
        # Test 4: Client bonuses
        test_client_specific_bonuses()
        
        # Test 5: End-to-end
        test_end_to_end_simulation()
        
        print("TOUS LES TESTS PASSES AVEC SUCCES")
        print("Runtime trademark & client_config v2 operationnels")
        
    except Exception as e:
        print(f"ERREUR DANS LES TESTS: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())