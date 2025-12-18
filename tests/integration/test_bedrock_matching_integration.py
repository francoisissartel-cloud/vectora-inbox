"""
Tests d'intégration pour le matching Bedrock.

Tests sur des données réelles du MVP lai_weekly_v3 pour valider
le fonctionnement end-to-end du matching Bedrock.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json

# Ajouter le chemin src au PYTHONPATH pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from vectora_core.matching import bedrock_matcher


class TestBedrockMatchingIntegration(unittest.TestCase):
    """Tests d'intégration avec données réelles du MVP."""
    
    def setUp(self):
        """Configuration des données de test."""
        # Item représentatif du MVP lai_weekly_v3
        self.test_item = {
            'title': "MedinCell's Partner Teva Pharmaceuticals Announces the New Drug Application Submission to U.S. FDA for Olanzapine Extended-Release Injectable Suspension",
            'summary': "MedinCell partners with Teva to develop long-acting injectable formulations using BEPO technology platform for olanzapine treatment.",
            'entities': {
                'companies': ['MedinCell', 'Teva Pharmaceuticals'],
                'molecules': ['olanzapine'],
                'technologies': ['Extended-Release Injectable', 'BEPO'],
                'trademarks': ['TEV-749', 'mdc-TJK'],
                'indications': ['schizophrenia']
            },
            'event_type': 'regulatory'
        }
        
        # Configuration watch_domains du MVP
        self.watch_domains = [
            {
                'id': 'tech_lai_ecosystem',
                'type': 'technology',
                'priority': 'high',
                'company_scope': 'lai_companies_global',
                'technology_scope': 'lai_keywords',
                'molecule_scope': 'lai_molecules_global',
                'trademark_scope': 'lai_trademarks_global'
            },
            {
                'id': 'regulatory_lai',
                'type': 'regulatory',
                'priority': 'high',
                'company_scope': 'lai_companies_global',
                'technology_scope': 'lai_keywords',
                'trademark_scope': 'lai_trademarks_global'
            }
        ]
        
        # Scopes canonical simplifiés
        self.canonical_scopes = {
            'companies': {
                'lai_companies_global': ['MedinCell', 'Teva Pharmaceutical', 'Camurus', 'Nanexa']
            },
            'technologies': {
                'lai_keywords': {
                    'core_phrases': ['Extended-Release Injectable', 'Long-Acting Injectable', 'BEPO'],
                    'technology_terms_high_precision': ['depot injection', 'once-monthly injection']
                }
            },
            'molecules': {
                'lai_molecules_global': ['olanzapine', 'risperidone', 'buprenorphine']
            },
            'trademarks': {
                'lai_trademarks_global': ['UZEDY', 'TEV-749', 'BEPO', 'PharmaShell']
            }
        }
    
    def test_build_domains_context(self):
        """Test construction du contexte des domaines."""
        context = bedrock_matcher._build_domains_context(self.watch_domains, self.canonical_scopes)
        
        self.assertIsInstance(context, str)
        self.assertIn('tech_lai_ecosystem', context)
        self.assertIn('regulatory_lai', context)
        self.assertIn('MedinCell', context)
        self.assertIn('Extended-Release Injectable', context)
        self.assertIn('olanzapine', context)
        
        # Vérifier la structure
        lines = context.split('\n')
        self.assertTrue(any('1. tech_lai_ecosystem' in line for line in lines))
        self.assertTrue(any('2. regulatory_lai' in line for line in lines))
    
    def test_build_matching_prompt(self):
        """Test construction du prompt de matching."""
        domains_context = bedrock_matcher._build_domains_context(self.watch_domains, self.canonical_scopes)
        prompt = bedrock_matcher._build_matching_prompt(self.test_item, domains_context)
        
        self.assertIsInstance(prompt, str)
        self.assertIn(self.test_item['title'], prompt)
        self.assertIn(self.test_item['summary'], prompt)
        self.assertIn('MedinCell', prompt)
        self.assertIn('tech_lai_ecosystem', prompt)
        self.assertIn('domain_evaluations', prompt)
        self.assertIn('JSON only', prompt)
    
    def test_parse_valid_bedrock_response(self):
        """Test parsing d'une réponse Bedrock valide."""
        mock_response = {
            "domain_evaluations": [
                {
                    "domain_id": "tech_lai_ecosystem",
                    "is_relevant": True,
                    "relevance_score": 0.85,
                    "confidence": "high",
                    "reasoning": "Article discusses MedinCell's BEPO technology partnership with Teva for LAI development",
                    "matched_entities": {
                        "companies": ["MedinCell", "Teva Pharmaceuticals"],
                        "technologies": ["Extended-Release Injectable", "BEPO"],
                        "molecules": ["olanzapine"]
                    }
                },
                {
                    "domain_id": "regulatory_lai",
                    "is_relevant": True,
                    "relevance_score": 0.75,
                    "confidence": "medium",
                    "reasoning": "FDA submission mentioned for LAI formulation",
                    "matched_entities": {
                        "companies": ["Teva Pharmaceuticals"],
                        "molecules": ["olanzapine"]
                    }
                }
            ]
        }
        
        response_text = json.dumps(mock_response)
        result = bedrock_matcher._parse_bedrock_matching_response(response_text)
        
        # Vérifier la structure
        self.assertIn('matched_domains', result)
        self.assertIn('domain_relevance', result)
        
        # Vérifier les domaines matchés
        self.assertEqual(len(result['matched_domains']), 2)
        self.assertIn('tech_lai_ecosystem', result['matched_domains'])
        self.assertIn('regulatory_lai', result['matched_domains'])
        
        # Vérifier les détails de pertinence
        self.assertIn('tech_lai_ecosystem', result['domain_relevance'])
        self.assertEqual(result['domain_relevance']['tech_lai_ecosystem']['score'], 0.85)
        self.assertEqual(result['domain_relevance']['tech_lai_ecosystem']['confidence'], 'high')
    
    def test_parse_low_score_response(self):
        """Test parsing avec scores faibles (sous le seuil)."""
        mock_response = {
            "domain_evaluations": [
                {
                    "domain_id": "tech_lai_ecosystem",
                    "is_relevant": True,
                    "relevance_score": 0.2,  # Sous le seuil de 0.4
                    "confidence": "low",
                    "reasoning": "Weak technology signals",
                    "matched_entities": {}
                }
            ]
        }
        
        response_text = json.dumps(mock_response)
        result = bedrock_matcher._parse_bedrock_matching_response(response_text)
        
        # Doit être rejeté à cause du score faible
        self.assertEqual(len(result['matched_domains']), 0)
        
        # Mais doit être présent dans domain_relevance pour debug
        self.assertIn('tech_lai_ecosystem', result['domain_relevance'])
        self.assertIn('rejected_reason', result['domain_relevance']['tech_lai_ecosystem'])
    
    @patch('vectora_core.matching.bedrock_matcher._call_bedrock_matching')
    def test_full_matching_workflow_success(self, mock_bedrock_call):
        """Test du workflow complet avec succès."""
        # Mock de la réponse Bedrock
        mock_response = {
            "domain_evaluations": [
                {
                    "domain_id": "tech_lai_ecosystem",
                    "is_relevant": True,
                    "relevance_score": 0.85,
                    "confidence": "high",
                    "reasoning": "Strong LAI technology signals",
                    "matched_entities": {
                        "companies": ["MedinCell"],
                        "technologies": ["Extended-Release Injectable", "BEPO"]
                    }
                }
            ]
        }
        
        mock_bedrock_call.return_value = json.dumps(mock_response)
        
        # Appel de la fonction principale
        result = bedrock_matcher.match_watch_domains_with_bedrock(
            self.test_item,
            self.watch_domains,
            self.canonical_scopes,
            'anthropic.claude-3-sonnet-20240229-v1:0'
        )
        
        # Vérifications
        self.assertEqual(len(result['matched_domains']), 1)
        self.assertIn('tech_lai_ecosystem', result['matched_domains'])
        self.assertEqual(result['domain_relevance']['tech_lai_ecosystem']['score'], 0.85)
        
        # Vérifier que Bedrock a été appelé
        mock_bedrock_call.assert_called_once()
    
    @patch('vectora_core.matching.bedrock_matcher._call_bedrock_matching')
    def test_full_matching_workflow_error(self, mock_bedrock_call):
        """Test du workflow complet avec erreur Bedrock."""
        # Simuler une erreur Bedrock
        mock_bedrock_call.side_effect = Exception("Bedrock timeout")
        
        # Appel de la fonction principale
        result = bedrock_matcher.match_watch_domains_with_bedrock(
            self.test_item,
            self.watch_domains,
            self.canonical_scopes,
            'anthropic.claude-3-sonnet-20240229-v1:0'
        )
        
        # Doit retourner structure vide (fallback)
        self.assertEqual(result['matched_domains'], [])
        self.assertEqual(result['domain_relevance'], {})
        self.assertIn('bedrock_error', result)
    
    def test_empty_watch_domains(self):
        """Test avec aucun watch_domain configuré."""
        result = bedrock_matcher.match_watch_domains_with_bedrock(
            self.test_item,
            [],  # Aucun domaine
            self.canonical_scopes,
            'anthropic.claude-3-sonnet-20240229-v1:0'
        )
        
        # Doit retourner structure vide
        self.assertEqual(result['matched_domains'], [])
        self.assertEqual(result['domain_relevance'], {})


if __name__ == '__main__':
    # Exécuter les tests avec verbosité
    unittest.main(verbosity=2)