"""
Tests unitaires pour le module bedrock_matcher.

Tests de base pour valider la structure et les imports du nouveau module
sans exécuter d'appels Bedrock réels.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Ajouter le chemin src au PYTHONPATH pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from vectora_core.matching import bedrock_matcher


class TestBedrockMatcherStructure(unittest.TestCase):
    """Tests de structure et d'imports du module bedrock_matcher."""
    
    def test_module_imports(self):
        """Test que le module s'importe correctement."""
        self.assertTrue(hasattr(bedrock_matcher, 'match_watch_domains_with_bedrock'))
        self.assertTrue(hasattr(bedrock_matcher, '_build_domains_context'))
        self.assertTrue(hasattr(bedrock_matcher, '_build_matching_prompt'))
        self.assertTrue(hasattr(bedrock_matcher, '_call_bedrock_matching'))
        self.assertTrue(hasattr(bedrock_matcher, '_parse_bedrock_matching_response'))
    
    def test_function_signatures(self):
        """Test que les fonctions ont les bonnes signatures."""
        import inspect
        
        # Test signature fonction principale
        sig = inspect.signature(bedrock_matcher.match_watch_domains_with_bedrock)
        params = list(sig.parameters.keys())
        expected_params = ['normalized_item', 'watch_domains', 'canonical_scopes', 'bedrock_model_id', 'bedrock_region']
        self.assertEqual(params, expected_params)
        
        # Test paramètre par défaut
        self.assertEqual(sig.parameters['bedrock_region'].default, "us-east-1")
    
    def test_build_domains_context_basic(self):
        """Test de base pour _build_domains_context."""
        watch_domains = [
            {
                'id': 'test_domain',
                'type': 'technology',
                'company_scope': 'test_companies'
            }
        ]
        
        canonical_scopes = {
            'companies': {
                'test_companies': ['Company A', 'Company B']
            }
        }
        
        result = bedrock_matcher._build_domains_context(watch_domains, canonical_scopes)
        
        self.assertIsInstance(result, str)
        self.assertIn('test_domain', result)
        self.assertIn('technology', result)
        self.assertIn('Company A', result)
    
    def test_parse_bedrock_response_valid_json(self):
        """Test parsing d'une réponse JSON valide."""
        response_text = '''
        {
            "domain_evaluations": [
                {
                    "domain_id": "tech_lai_ecosystem",
                    "is_relevant": true,
                    "relevance_score": 0.85,
                    "confidence": "high",
                    "reasoning": "Test reasoning",
                    "matched_entities": {
                        "companies": ["MedinCell"],
                        "technologies": ["LAI"]
                    }
                }
            ]
        }
        '''
        
        result = bedrock_matcher._parse_bedrock_matching_response(response_text)
        
        self.assertIsInstance(result, dict)
        self.assertIn('matched_domains', result)
        self.assertIn('domain_relevance', result)
        self.assertEqual(result['matched_domains'], ['tech_lai_ecosystem'])
        self.assertIn('tech_lai_ecosystem', result['domain_relevance'])
    
    def test_parse_bedrock_response_invalid_json(self):
        """Test parsing d'une réponse JSON invalide."""
        response_text = "Invalid JSON response"
        
        result = bedrock_matcher._parse_bedrock_matching_response(response_text)
        
        # Doit retourner structure vide en cas d'erreur
        self.assertEqual(result, {
            "matched_domains": [],
            "domain_relevance": {}
        })
    
    @patch('vectora_core.matching.bedrock_matcher._call_bedrock_matching')
    def test_match_watch_domains_with_error_handling(self, mock_bedrock_call):
        """Test gestion d'erreurs avec fallback."""
        # Simuler une erreur Bedrock
        mock_bedrock_call.side_effect = Exception("Bedrock error")
        
        normalized_item = {
            'title': 'Test item',
            'summary': 'Test summary',
            'entities': {},
            'event_type': 'other'
        }
        
        watch_domains = [{'id': 'test_domain', 'type': 'technology'}]
        canonical_scopes = {}
        
        result = bedrock_matcher.match_watch_domains_with_bedrock(
            normalized_item, watch_domains, canonical_scopes, 'test-model'
        )
        
        # Doit retourner structure vide en cas d'erreur (fallback)
        self.assertEqual(result, {
            "matched_domains": [],
            "domain_relevance": {}
        })


class TestPromptCanonicalise(unittest.TestCase):
    """Tests pour valider le prompt canonicalisé."""
    
    def test_prompt_structure_in_yaml(self):
        """Test que le prompt est bien structuré dans le YAML."""
        import yaml
        from pathlib import Path
        
        # Charger le fichier YAML
        yaml_path = Path(__file__).parent.parent.parent / 'canonical' / 'prompts' / 'global_prompts.yaml'
        
        with open(yaml_path, 'r', encoding='utf-8') as f:
            prompts = yaml.safe_load(f)
        
        # Vérifier la structure
        self.assertIn('matching', prompts)
        self.assertIn('matching_watch_domains_v2', prompts['matching'])
        
        prompt_config = prompts['matching']['matching_watch_domains_v2']
        self.assertIn('system_instructions', prompt_config)
        self.assertIn('user_template', prompt_config)
        self.assertIn('bedrock_config', prompt_config)
        
        # Vérifier les placeholders
        user_template = prompt_config['user_template']
        self.assertIn('{{item_title}}', user_template)
        self.assertIn('{{item_summary}}', user_template)
        self.assertIn('{{item_entities}}', user_template)
        self.assertIn('{{domains_context}}', user_template)


if __name__ == '__main__':
    unittest.main()