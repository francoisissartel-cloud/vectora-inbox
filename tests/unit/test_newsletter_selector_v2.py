"""
Test unitaire pour la nouvelle logique de sélection Newsletter V2
Valide les 4 étapes de sélection selon le design
"""
import unittest
from unittest.mock import Mock
import sys
import os

# Ajouter le chemin vers vectora_core
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src_v2'))

from vectora_core.newsletter.selector import NewsletterSelector

class TestNewsletterSelector(unittest.TestCase):
    
    def setUp(self):
        """Configuration de test avec lai_weekly_v4"""
        self.client_config = {
            'newsletter_selection': {
                'max_items_total': 20,
                'critical_event_types': ['regulatory_approval', 'partnership', 'clinical_update'],
                'trimming_policy': {
                    'preserve_critical_events': True,
                    'min_items_per_section': 1,
                    'max_section_dominance': 0.6
                },
                'deduplication': {
                    'enabled': True,
                    'prefer_critical_events': True
                }
            },
            'newsletter_layout': {
                'sections': [
                    {
                        'id': 'partnerships',
                        'title': 'Partnerships',
                        'source_domains': ['tech_lai_ecosystem'],
                        'filter_event_types': ['partnership'],
                        'max_items': 3,
                        'sort_by': 'date_desc'
                    },
                    {
                        'id': 'top_signals',
                        'title': 'Top Signals',
                        'source_domains': ['tech_lai_ecosystem'],
                        'max_items': 5,
                        'sort_by': 'score_desc'
                    }
                ]
            }
        }
        self.selector = NewsletterSelector(self.client_config)
    
    def test_filter_by_matching(self):
        """Test Étape 1: Filtrage par matching"""
        items = [
            {
                'item_id': '1',
                'matching_results': {'matched_domains': ['tech_lai_ecosystem']},
                'scoring_results': {'final_score': 15.0}
            },
            {
                'item_id': '2', 
                'matching_results': {'matched_domains': []},
                'scoring_results': {'final_score': 18.0}
            },
            {
                'item_id': '3',
                'matching_results': {'matched_domains': ['tech_lai_ecosystem']},
                'scoring_results': {'final_score': 12.0}
            }
        ]
        
        filtered = self.selector._filter_by_matching(items)
        
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0]['item_id'], '1')
        self.assertEqual(filtered[1]['item_id'], '3')
    
    def test_effective_score_calculation(self):
        """Test du calcul de l'effective_score"""
        # Cas 1: final_score > 0
        item1 = {
            'scoring_results': {'final_score': 15.0},
            'normalized_content': {'lai_relevance_score': 8}
        }
        self.assertEqual(self.selector._get_effective_score(item1), 15.0)
        
        # Cas 2: final_score = 0, lai_relevance_score > 0
        item2 = {
            'scoring_results': {'final_score': 0},
            'normalized_content': {'lai_relevance_score': 7}
        }
        self.assertEqual(self.selector._get_effective_score(item2), 14.0)  # 7 * 2
        
        # Cas 3: Les deux à 0
        item3 = {
            'scoring_results': {'final_score': 0},
            'normalized_content': {'lai_relevance_score': 0}
        }
        self.assertEqual(self.selector._get_effective_score(item3), 0)
    
    def test_critical_event_detection(self):
        """Test de détection des événements critiques"""
        critical_item = {
            'normalized_content': {
                'event_classification': {'primary_type': 'partnership'}
            }
        }
        regular_item = {
            'normalized_content': {
                'event_classification': {'primary_type': 'market_update'}
            }
        }
        
        self.assertTrue(self.selector._is_critical_event(critical_item))
        self.assertFalse(self.selector._is_critical_event(regular_item))
    
    def test_deduplication_with_critical_priority(self):
        """Test déduplication avec priorité aux événements critiques"""
        duplicates = [
            {
                'item_id': '1',
                'scoring_results': {'final_score': 18.0},
                'normalized_content': {
                    'event_classification': {'primary_type': 'market_update'},
                    'entities': {'companies': ['Company A']}
                },
                'published_at': '2025-12-21'
            },
            {
                'item_id': '2',
                'scoring_results': {'final_score': 15.0},
                'normalized_content': {
                    'event_classification': {'primary_type': 'partnership'},
                    'entities': {'companies': ['Company A']}
                },
                'published_at': '2025-12-21'
            }
        ]
        
        best = self.selector._select_best_duplicate(duplicates)
        
        # L'événement critique doit être sélectionné même avec un score plus faible
        self.assertEqual(best['item_id'], '2')
        self.assertEqual(best['normalized_content']['event_classification']['primary_type'], 'partnership')
    
    def test_section_distribution(self):
        """Test de distribution en sections"""
        items = [
            {
                'item_id': '1',
                'matching_results': {'matched_domains': ['tech_lai_ecosystem']},
                'scoring_results': {'final_score': 18.0},
                'normalized_content': {'event_classification': {'primary_type': 'partnership'}},
                'published_at': '2025-12-21T10:00:00Z'
            },
            {
                'item_id': '2',
                'matching_results': {'matched_domains': ['tech_lai_ecosystem']},
                'scoring_results': {'final_score': 16.0},
                'normalized_content': {'event_classification': {'primary_type': 'clinical_update'}},
                'published_at': '2025-12-21T09:00:00Z'
            }
        ]
        
        sections = self.selector._distribute_to_sections(items)
        
        # Vérifier que les sections sont créées
        self.assertIn('top_signals', sections)
        self.assertIn('partnerships', sections)
        
        # L'item partnership doit être dans la section partnerships
        partnerships_items = sections['partnerships']['items']
        self.assertEqual(len(partnerships_items), 1)
        self.assertEqual(partnerships_items[0]['item_id'], '1')
    
    def test_full_selection_workflow(self):
        """Test du workflow complet de sélection"""
        curated_items = [
            {
                'item_id': '1',
                'matching_results': {'matched_domains': ['tech_lai_ecosystem']},
                'scoring_results': {'final_score': 18.0},
                'normalized_content': {
                    'event_classification': {'primary_type': 'partnership'},
                    'entities': {'companies': ['Nanexa'], 'trademarks': []}
                },
                'published_at': '2025-12-21T10:00:00Z'
            },
            {
                'item_id': '2',
                'matching_results': {'matched_domains': []},  # Non matché
                'scoring_results': {'final_score': 20.0},
                'normalized_content': {'event_classification': {'primary_type': 'clinical_update'}},
                'published_at': '2025-12-21T09:00:00Z'
            },
            {
                'item_id': '3',
                'matching_results': {'matched_domains': ['tech_lai_ecosystem']},
                'scoring_results': {'final_score': 15.0},
                'normalized_content': {
                    'event_classification': {'primary_type': 'regulatory_approval'},
                    'entities': {'companies': ['Teva'], 'trademarks': []}
                },
                'published_at': '2025-12-21T08:00:00Z'
            }
        ]
        
        result = self.selector.select_items(curated_items)
        
        # Vérifications des métadonnées
        metadata = result['metadata']
        self.assertEqual(metadata['total_items_processed'], 3)
        self.assertEqual(metadata['items_after_matching_filter'], 2)  # Item 2 filtré
        self.assertEqual(metadata['selection_policy_version'], '2.0')
        self.assertGreaterEqual(metadata['critical_events_preserved'], 1)
        
        # Vérifications des sections
        sections = result['sections']
        total_selected = sum(len(section['items']) for section in sections.values())
        self.assertGreater(total_selected, 0)
        self.assertEqual(total_selected, metadata['items_selected'])

if __name__ == '__main__':
    unittest.main()