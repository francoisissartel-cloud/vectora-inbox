#!/usr/bin/env python3
"""
Test local des profils d'ingestion.

Ce script teste la logique de filtrage d'ingestion sans AWS,
en utilisant des données de test simulées.
"""

import sys
import os
import json
from typing import Dict, Any, List

# Ajouter le chemin vers vectora_core
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def create_test_item(title: str, text: str, source_key: str) -> Dict[str, Any]:
    """Crée un item de test."""
    return {
        'title': title,
        'url': f'https://example.com/{title.lower().replace(" ", "-")}',
        'published_at': '2024-12-19',
        'raw_text': text,
        'source_key': source_key,
        'source_type': 'press_corporate'
    }

def test_profile_filter():
    """Test principal du filtre de profils."""
    print("=== Test Local des Profils d'Ingestion ===")
    
    # Simuler des items de test
    test_items = [
        # Items LAI évidents (doivent passer)
        create_test_item(
            "MedinCell Announces Long-Acting Injectable Results",
            "MedinCell reported positive results for their long-acting injectable formulation using PLGA microspheres for monthly injection.",
            "press_corporate__medincell"
        ),
        create_test_item(
            "Camurus Receives FDA Approval for Depot Injection",
            "Camurus announced FDA approval for their extended-release injection using FluidCrystal technology for q4w dosing.",
            "press_corporate__camurus"
        ),
        
        # Items RH/ESG (doivent être filtrés pour pure players)
        create_test_item(
            "MedinCell Hires New Chief Human Resources Officer",
            "MedinCell announced the appointment of a new CHRO to lead diversity and inclusion initiatives and employee benefits programs.",
            "press_corporate__medincell"
        ),
        
        # Items presse généraliste (doivent être filtrés)
        create_test_item(
            "Generic Drug Market Trends in 2024",
            "The generic pharmaceutical market continues to grow with new oral tablet formulations and cost reduction strategies.",
            "press_sector__fiercepharma"
        ),
        
        # Items presse avec signaux LAI (doivent passer)
        create_test_item(
            "Alkermes Reports Strong Q4 Results for Aristada",
            "Alkermes reported strong quarterly results driven by their long-acting injectable antipsychotic Aristada for monthly injection.",
            "press_sector__fiercepharma"
        )
    ]
    
    print(f"Nombre d'items de test : {len(test_items)}")
    
    # Simuler la configuration (sans S3)
    mock_profiles = {
        'corporate_pure_player_broad': {
            'strategy': 'broad_ingestion',
            'signal_requirements': {
                'mode': 'exclude_only',
                'exclusion_scopes': ['exclusion_scopes.hr_content']
            }
        },
        'press_technology_focused': {
            'strategy': 'multi_signal_ingestion',
            'signal_requirements': {
                'mode': 'require_multi_signals',
                'required_signal_groups': [
                    {
                        'group_id': 'entity_signals',
                        'scopes': ['lai_companies_global'],
                        'min_matches': 1,
                        'weight': 2.0
                    },
                    {
                        'group_id': 'technology_signals',
                        'scopes': ['lai_keywords.core_phrases'],
                        'min_matches': 1,
                        'weight': 2.0
                    }
                ],
                'combination_logic': 'entity_signals AND technology_signals',
                'minimum_total_weight': 3.0
            }
        }
    }
    
    mock_source_catalog = {
        'press_corporate__medincell': {'ingestion_profile': 'corporate_pure_player_broad'},
        'press_corporate__camurus': {'ingestion_profile': 'corporate_pure_player_broad'},
        'press_sector__fiercepharma': {'ingestion_profile': 'press_technology_focused'}
    }
    
    mock_scopes = {
        'exclusion_scopes': {
            'hr_content': [
                'human resources', 'CHRO', 'diversity and inclusion', 
                'employee benefits', 'hiring', 'appointment'
            ]
        },
        'company_scopes': {
            'lai_companies_global': [
                'MedinCell', 'Camurus', 'Alkermes', 'DelSiTech', 'Nanexa'
            ]
        },
        'technology_scopes': {
            'lai_keywords': {
                'core_phrases': [
                    'long-acting injectable', 'extended-release injection',
                    'depot injection', 'monthly injection', 'q4w'
                ]
            }
        }
    }
    
    # Créer un filtre mock
    class MockProfileFilter:
        def __init__(self):
            self.profiles = mock_profiles
            self.source_catalog = mock_source_catalog
            self.scopes = mock_scopes
            self._loaded = True
        
        def load_configurations(self):
            pass
        
        def _get_profile_for_source(self, source_key: str):
            return self.source_catalog.get(source_key, {}).get('ingestion_profile')
        
        def _build_analysis_text(self, item: Dict[str, Any]) -> str:
            return f"{item.get('title', '')} {item.get('raw_text', '')}".strip()
        
        def _detect_signals_in_scope(self, text: str, scope_key: str) -> int:
            keywords = self._get_keywords_for_scope(scope_key)
            text_lower = text.lower()
            matches = 0
            for keyword in keywords:
                if isinstance(keyword, str) and keyword.lower() in text_lower:
                    matches += 1
            return matches
        
        def _get_keywords_for_scope(self, scope_key: str) -> List[str]:
            if scope_key == 'exclusion_scopes.hr_content':
                return self.scopes['exclusion_scopes']['hr_content']
            elif scope_key == 'lai_companies_global':
                return self.scopes['company_scopes']['lai_companies_global']
            elif scope_key == 'lai_keywords.core_phrases':
                return self.scopes['technology_scopes']['lai_keywords']['core_phrases']
            return []
        
        def apply_filter(self, item: Dict[str, Any], source_key: str) -> bool:
            profile_name = self._get_profile_for_source(source_key)
            if not profile_name:
                return True
            
            profile = self.profiles.get(profile_name)
            if not profile:
                return True
            
            strategy = profile.get('strategy', 'no_filtering')
            text = self._build_analysis_text(item)
            
            if strategy == 'broad_ingestion':
                # Vérifier exclusions
                signal_req = profile.get('signal_requirements', {})
                exclusion_scopes = signal_req.get('exclusion_scopes', [])
                for exclusion_scope in exclusion_scopes:
                    if self._detect_signals_in_scope(text, exclusion_scope) > 0:
                        return False
                return True
            
            elif strategy == 'multi_signal_ingestion':
                signal_req = profile.get('signal_requirements', {})
                required_groups = signal_req.get('required_signal_groups', [])
                
                group_results = {}
                for group in required_groups:
                    group_id = group.get('group_id')
                    scopes = group.get('scopes', [])
                    min_matches = group.get('min_matches', 1)
                    
                    matches = 0
                    for scope in scopes:
                        matches += self._detect_signals_in_scope(text, scope)
                    
                    group_results[group_id] = matches >= min_matches
                
                # Évaluer la logique AND
                return all(group_results.values())
            
            return True
    
    # Tester le filtrage
    filter_instance = MockProfileFilter()
    results = []
    
    print("\n=== Résultats du Filtrage ===")
    for item in test_items:
        source_key = item['source_key']
        should_ingest = filter_instance.apply_filter(item, source_key)
        
        profile_name = filter_instance._get_profile_for_source(source_key)
        
        results.append({
            'title': item['title'],
            'source_key': source_key,
            'profile': profile_name or 'default_broad',
            'ingested': should_ingest
        })
        
        status = "[INGERE]" if should_ingest else "[FILTRE]"
        print(f"{status} | {item['title'][:50]}... | {source_key} | {profile_name}")
    
    # Statistiques
    ingested = sum(1 for r in results if r['ingested'])
    filtered = len(results) - ingested
    retention_rate = ingested / len(results) * 100
    
    print(f"\n=== Statistiques ===")
    print(f"Total items : {len(results)}")
    print(f"Items ingérés : {ingested}")
    print(f"Items filtrés : {filtered}")
    print(f"Taux de rétention : {retention_rate:.1f}%")
    
    # Validation des attentes
    print(f"\n=== Validation ===")
    expected_results = {
        "MedinCell Announces Long-Acting Injectable Results": True,  # LAI évident
        "Camurus Receives FDA Approval for Depot Injection": True,   # LAI évident
        "MedinCell Hires New Chief Human Resources Officer": False,  # RH filtré
        "Generic Drug Market Trends in 2024": False,                # Presse généraliste
        "Alkermes Reports Strong Q4 Results for Aristada": True     # Presse avec signaux LAI
    }
    
    all_correct = True
    for result in results:
        expected = expected_results.get(result['title'])
        if expected is not None and result['ingested'] != expected:
            print(f"[ERREUR]: {result['title']} - Attendu: {expected}, Obtenu: {result['ingested']}")
            all_correct = False
    
    if all_correct:
        print("[OK] Tous les résultats correspondent aux attentes")
        return True
    else:
        print("[ERREUR] Certains résultats ne correspondent pas aux attentes")
        return False

if __name__ == "__main__":
    success = test_profile_filter()
    sys.exit(0 if success else 1)