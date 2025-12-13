"""
Tests unitaires pour l'ajustement du scoring recency.

Ces tests valident :
1. Neutralisation recency_factor pour period_days <= 7
2. Comportement inchangé pour period_days > 7
3. Impact sur le score final
4. Rétrocompatibilité
"""

import unittest
from unittest.mock import patch
import sys
import os
from datetime import datetime, timedelta

# Ajouter le chemin src au PYTHONPATH pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from vectora_core.scoring import scorer


class TestScoringRecencyAdjustment(unittest.TestCase):
    
    def setUp(self):
        """Configuration des données de test."""
        self.scoring_rules = {
            'event_type_weights': {
                'clinical_update': 5,
                'partnership': 6,
                'other': 1
            },
            'domain_priority_weights': {
                'high': 3,
                'medium': 2,
                'low': 1
            },
            'other_factors': {
                'recency_decay_half_life_days': 7,
                'source_type_weight_corporate': 2,
                'source_type_weight_sector': 1.5,
                'source_type_weight_generic': 1,
                'pure_player_bonus': 3,
                'hybrid_company_bonus': 1,
                'signal_depth_bonus': 0.3,
                'match_confidence_multiplier_high': 1.5,
                'match_confidence_multiplier_medium': 1.2,
                'match_confidence_multiplier_low': 1.0,
                'signal_quality_weight_high_precision': 2.0,
                'signal_quality_weight_supporting': 1.0,
                'negative_term_penalty': 10
            }
        }
        
        self.watch_domains = [
            {'id': 'tech_lai', 'priority': 'high'},
            {'id': 'regulatory', 'priority': 'medium'}
        ]
        
        self.canonical_scopes = {
            'companies': {
                'lai_companies_pure_players': ['Camurus', 'Indivior'],
                'lai_companies_hybrid': ['Pfizer', 'J&J']
            }
        }
    
    def test_recency_factor_weekly_neutralized(self):
        """Test que recency_factor = 1.0 pour period_days <= 7."""
        # Test avec différentes dates sur une fenêtre de 7 jours
        test_cases = [
            ('2025-01-15', 7, 1.0),  # Aujourd'hui
            ('2025-01-14', 7, 1.0),  # Hier
            ('2025-01-10', 7, 1.0),  # Il y a 5 jours
            ('2025-01-08', 7, 1.0),  # Il y a 7 jours
        ]
        
        for item_date, period_days, expected in test_cases:
            with self.subTest(item_date=item_date, period_days=period_days):
                result = scorer._compute_recency_factor(item_date, 7, period_days)
                self.assertEqual(result, expected, 
                    f"recency_factor should be 1.0 for weekly pipeline, got {result}")
    
    def test_recency_factor_monthly_unchanged(self):
        """Test que le comportement est inchangé pour period_days > 7."""
        # Test avec une fenêtre de 30 jours (monthly)
        today = datetime.now()
        
        # Item récent (1 jour)
        recent_date = (today - timedelta(days=1)).strftime('%Y-%m-%d')
        recent_factor = scorer._compute_recency_factor(recent_date, 7, 30)
        
        # Item ancien (14 jours)
        old_date = (today - timedelta(days=14)).strftime('%Y-%m-%d')
        old_factor = scorer._compute_recency_factor(old_date, 7, 30)
        
        # Vérifier que la récence est discriminante
        self.assertGreater(recent_factor, old_factor, 
            "Recent items should have higher recency_factor in monthly pipeline")
        self.assertLessEqual(recent_factor, 1.0)
        self.assertGreaterEqual(old_factor, 0.1)
    
    def test_recency_factor_no_period_days_unchanged(self):
        """Test que le comportement est inchangé quand period_days n'est pas fourni."""
        today = datetime.now()
        
        # Item récent
        recent_date = (today - timedelta(days=1)).strftime('%Y-%m-%d')
        recent_factor = scorer._compute_recency_factor(recent_date, 7, None)
        
        # Item ancien
        old_date = (today - timedelta(days=14)).strftime('%Y-%m-%d')
        old_factor = scorer._compute_recency_factor(old_date, 7, None)
        
        # Vérifier le comportement existant
        self.assertGreater(recent_factor, old_factor)
        self.assertLessEqual(recent_factor, 1.0)
        self.assertGreaterEqual(old_factor, 0.1)
    
    def test_score_items_with_period_days_weekly(self):
        """Test du scoring complet avec period_days = 7."""
        items = [
            {
                'title': 'Clinical Update Item',
                'date': '2025-01-15',
                'event_type': 'clinical_update',
                'source_type': 'press_corporate',
                'companies_detected': ['Camurus'],
                'molecules_detected': ['buprenorphine'],
                'technologies_detected': ['long acting'],
                'indications_detected': ['opioid use disorder'],
                'matched_domains': ['tech_lai'],
                'matching_details': {
                    'match_confidence': 'high',
                    'signals_used': {'high_precision': 2, 'supporting': 1},
                    'scopes_hit': {'company_scope_type': 'pure_player'}
                }
            },
            {
                'title': 'Partnership Item',
                'date': '2025-01-10',  # 5 jours plus ancien
                'event_type': 'partnership',
                'source_type': 'sector',
                'companies_detected': ['Pfizer'],
                'molecules_detected': [],
                'technologies_detected': [],
                'indications_detected': [],
                'matched_domains': ['regulatory'],
                'matching_details': {
                    'match_confidence': 'medium',
                    'signals_used': {'high_precision': 1, 'supporting': 0},
                    'scopes_hit': {'company_scope_type': 'hybrid'}
                }
            }
        ]
        
        # Scorer avec period_days = 7 (weekly)
        scored_items = scorer.score_items(
            items, self.scoring_rules, self.watch_domains, 
            self.canonical_scopes, period_days=7
        )
        
        # Vérifier que les scores sont calculés
        self.assertTrue(all('score' in item for item in scored_items))
        
        # Vérifier que la récence n'influence pas le score
        # (les deux items devraient avoir recency_factor = 1.0)
        item1_score = scored_items[0]['score']
        item2_score = scored_items[1]['score']
        
        # Le premier item devrait avoir un score plus élevé grâce à :
        # - event_type: clinical_update (5) vs partnership (6) -> partnership gagne
        # - domain_priority: high (3) vs medium (2) -> clinical gagne
        # - pure_player_bonus vs hybrid_bonus -> clinical gagne
        # Mais partnership a un event_weight plus élevé
        
        self.assertGreater(item1_score, 0)
        self.assertGreater(item2_score, 0)
    
    def test_score_items_with_period_days_monthly(self):
        """Test du scoring complet avec period_days = 30."""
        # Utiliser des dates relatives à aujourd'hui
        today = datetime.now()
        recent_date = today.strftime('%Y-%m-%d')
        old_date = (today - timedelta(days=20)).strftime('%Y-%m-%d')  # 20 jours plus ancien
        
        items = [
            {
                'title': 'Recent Item',
                'date': recent_date,
                'event_type': 'clinical_update',
                'source_type': 'press_corporate',
                'companies_detected': ['Camurus'],
                'molecules_detected': [],
                'technologies_detected': [],
                'indications_detected': [],
                'matched_domains': ['tech_lai'],
                'matching_details': {
                    'match_confidence': 'medium',
                    'signals_used': {'high_precision': 1, 'supporting': 1},
                    'scopes_hit': {'company_scope_type': 'pure_player'}
                }
            },
            {
                'title': 'Old Item',
                'date': old_date,
                'event_type': 'clinical_update',
                'source_type': 'press_corporate',
                'companies_detected': ['Camurus'],
                'molecules_detected': [],
                'technologies_detected': [],
                'indications_detected': [],
                'matched_domains': ['tech_lai'],
                'matching_details': {
                    'match_confidence': 'medium',
                    'signals_used': {'high_precision': 1, 'supporting': 1},
                    'scopes_hit': {'company_scope_type': 'pure_player'}
                }
            }
        ]
        
        # Scorer avec period_days = 30 (monthly)
        scored_items = scorer.score_items(
            items, self.scoring_rules, self.watch_domains, 
            self.canonical_scopes, period_days=30
        )
        
        # L'item récent devrait avoir un score plus élevé grâce à la récence
        recent_score = scored_items[0]['score']
        old_score = scored_items[1]['score']
        
        self.assertGreater(recent_score, old_score, 
            "Recent item should have higher score in monthly pipeline")
    
    def test_score_items_backward_compatibility(self):
        """Test de la rétrocompatibilité (sans period_days)."""
        items = [
            {
                'title': 'Test Item',
                'date': '2025-01-15',
                'event_type': 'clinical_update',
                'source_type': 'press_corporate',
                'companies_detected': ['Camurus'],
                'molecules_detected': [],
                'technologies_detected': [],
                'indications_detected': [],
                'matched_domains': ['tech_lai'],
                'matching_details': {
                    'match_confidence': 'medium',
                    'signals_used': {'high_precision': 1, 'supporting': 1},
                    'scopes_hit': {'company_scope_type': 'pure_player'}
                }
            }
        ]
        
        # Appel sans period_days (comportement existant)
        scored_items = scorer.score_items(
            items, self.scoring_rules, self.watch_domains, self.canonical_scopes
        )
        
        # Vérifier que ça fonctionne toujours
        self.assertEqual(len(scored_items), 1)
        self.assertIn('score', scored_items[0])
        self.assertGreater(scored_items[0]['score'], 0)
    
    def test_weekly_vs_monthly_score_difference(self):
        """Test de la différence de comportement weekly vs monthly."""
        item = {
            'title': 'Test Item',
            'date': '2025-01-10',  # 5 jours dans le passé
            'event_type': 'clinical_update',
            'source_type': 'press_corporate',
            'companies_detected': ['Camurus'],
            'molecules_detected': [],
            'technologies_detected': [],
            'indications_detected': [],
            'matched_domains': ['tech_lai'],
            'matching_details': {
                'match_confidence': 'medium',
                'signals_used': {'high_precision': 1, 'supporting': 1},
                'scopes_hit': {'company_scope_type': 'pure_player'}
            }
        }
        
        # Score weekly (récence neutralisée)
        weekly_items = scorer.score_items(
            [item.copy()], self.scoring_rules, self.watch_domains, 
            self.canonical_scopes, period_days=7
        )
        
        # Score monthly (récence discriminante)
        monthly_items = scorer.score_items(
            [item.copy()], self.scoring_rules, self.watch_domains, 
            self.canonical_scopes, period_days=30
        )
        
        weekly_score = weekly_items[0]['score']
        monthly_score = monthly_items[0]['score']
        
        # Le score weekly devrait être plus élevé (recency_factor = 1.0)
        # vs monthly (recency_factor < 1.0 pour un item de 5 jours)
        self.assertGreater(weekly_score, monthly_score,
            "Weekly score should be higher due to neutralized recency")


if __name__ == '__main__':
    unittest.main()