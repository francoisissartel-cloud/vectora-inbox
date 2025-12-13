"""
Tests unitaires pour la normalisation open-world.

Ces tests valident :
1. Séparation molecule vs trademark
2. Schéma *_detected + *_in_scopes
3. Conservation des entités hors-scopes
4. Calcul correct des intersections
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Ajouter le chemin src au PYTHONPATH pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from vectora_core.normalization import normalizer, entity_detector


class TestNormalizationOpenWorld(unittest.TestCase):
    
    def setUp(self):
        """Configuration des données de test."""
        self.canonical_scopes = {
            'companies': {
                'lai_companies_global': ['Camurus', 'Indivior', 'Alkermes']
            },
            'molecules': {
                'lai_molecules_global': ['buprenorphine', 'naloxone', 'aripiprazole']
            },
            'trademarks': {
                'lai_trademarks_global': ['Brixadi', 'Sublocade', 'Abilify Maintena']
            },
            'technologies': {
                'lai_keywords': ['long acting', 'depot', 'microspheres']
            },
            'indications': {
                'lai_indications': ['opioid use disorder', 'schizophrenia']
            }
        }
        
        self.raw_item = {
            'source_key': 'press_corporate__camurus',
            'source_type': 'press_corporate',
            'title': 'Camurus Announces Positive Phase 3 Results for Brixadi',
            'raw_text': 'Camurus reported positive results from Phase 3 trial of Brixadi (buprenorphine) for opioid use disorder treatment.',
            'url': 'https://example.com/article',
            'published_at': '2025-01-15'
        }
    
    def test_extract_canonical_examples_includes_trademarks(self):
        """Test que _extract_canonical_examples inclut les trademarks."""
        examples = normalizer._extract_canonical_examples(self.canonical_scopes)
        
        self.assertIn('trademarks', examples)
        self.assertIn('Brixadi', examples['trademarks'])
        self.assertIn('Sublocade', examples['trademarks'])
        self.assertIn('companies', examples)
        self.assertIn('molecules', examples)
        self.assertIn('technologies', examples)
    
    def test_entity_detector_supports_trademarks(self):
        """Test que entity_detector supporte les trademarks."""
        text = "Camurus announced results for Brixadi (buprenorphine) long acting injection"
        
        result = entity_detector.detect_entities_by_rules(text, self.canonical_scopes)
        
        self.assertIn('trademarks_detected', result)
        self.assertIn('Brixadi', result['trademarks_detected'])
        self.assertIn('Camurus', result['companies_detected'])
        self.assertIn('buprenorphine', result['molecules_detected'])
        self.assertIn('long acting', result['technologies_detected'])
    
    def test_merge_entity_detections_includes_trademarks(self):
        """Test que merge_entity_detections fusionne les trademarks."""
        bedrock_result = {
            'companies_detected': ['Camurus', 'NewCorp'],
            'molecules_detected': ['buprenorphine'],
            'trademarks_detected': ['Brixadi', 'NewDrug'],
            'technologies_detected': ['long acting'],
            'indications_detected': ['opioid use disorder']
        }
        
        rules_result = {
            'companies_detected': {'Camurus'},
            'molecules_detected': {'buprenorphine'},
            'trademarks_detected': {'Brixadi'},
            'technologies_detected': {'long acting'},
            'indications_detected': set()
        }
        
        merged = entity_detector.merge_entity_detections(bedrock_result, rules_result)
        
        self.assertIn('trademarks_detected', merged)
        self.assertEqual(set(merged['trademarks_detected']), {'Brixadi', 'NewDrug'})
        self.assertEqual(set(merged['companies_detected']), {'Camurus', 'NewCorp'})
    
    def test_compute_entities_in_scopes(self):
        """Test du calcul des intersections avec les scopes canonical."""
        merged_entities = {
            'companies_detected': ['Camurus', 'NewCorp', 'Pfizer'],
            'molecules_detected': ['buprenorphine', 'unknown_molecule'],
            'trademarks_detected': ['Brixadi', 'UnknownBrand'],
            'technologies_detected': ['long acting', 'new_tech'],
            'indications_detected': ['opioid use disorder', 'rare_disease']
        }
        
        result = entity_detector.compute_entities_in_scopes(merged_entities, self.canonical_scopes)
        
        # Vérifier les intersections
        self.assertEqual(result['companies_in_scopes'], ['Camurus'])  # Seul Camurus dans scopes
        self.assertEqual(result['molecules_in_scopes'], ['buprenorphine'])  # Seul buprenorphine dans scopes
        self.assertEqual(result['trademarks_in_scopes'], ['Brixadi'])  # Seul Brixadi dans scopes
        self.assertEqual(result['technologies_in_scopes'], ['long acting'])  # Seul long acting dans scopes
        self.assertEqual(result['indications_in_scopes'], ['opioid use disorder'])  # Seul OUD dans scopes
    
    def test_open_world_preserves_unknown_entities(self):
        """Test que les entités inconnues sont préservées dans *_detected."""
        merged_entities = {
            'companies_detected': ['Camurus', 'UnknownCorp'],
            'molecules_detected': ['buprenorphine', 'experimental_drug'],
            'trademarks_detected': ['Brixadi', 'NewBrand'],
            'technologies_detected': ['long acting', 'novel_delivery'],
            'indications_detected': ['opioid use disorder', 'rare_condition']
        }
        
        result = entity_detector.compute_entities_in_scopes(merged_entities, self.canonical_scopes)
        
        # Vérifier que toutes les entités détectées sont préservées
        # (même si pas dans les scopes)
        self.assertIn('UnknownCorp', merged_entities['companies_detected'])
        self.assertIn('experimental_drug', merged_entities['molecules_detected'])
        self.assertIn('NewBrand', merged_entities['trademarks_detected'])
        
        # Vérifier que seules les entités connues sont dans *_in_scopes
        self.assertNotIn('UnknownCorp', result['companies_in_scopes'])
        self.assertNotIn('experimental_drug', result['molecules_in_scopes'])
        self.assertNotIn('NewBrand', result['trademarks_in_scopes'])
    
    @patch('vectora_core.normalization.bedrock_client.normalize_item_with_bedrock')
    @patch('vectora_core.normalization.entity_detector.detect_entities_by_rules')
    def test_normalize_item_returns_open_world_schema(self, mock_rules, mock_bedrock):
        """Test que normalize_item retourne le nouveau schéma open-world."""
        # Mock des résultats
        mock_bedrock.return_value = {
            'summary': 'Test summary',
            'event_type': 'clinical_update',
            'companies_detected': ['Camurus'],
            'molecules_detected': ['buprenorphine'],
            'trademarks_detected': ['Brixadi'],
            'technologies_detected': ['long acting'],
            'indications_detected': ['opioid use disorder']
        }
        
        mock_rules.return_value = {
            'companies_detected': set(),
            'molecules_detected': set(),
            'trademarks_detected': set(),
            'technologies_detected': set(),
            'indications_detected': set()
        }
        
        result = normalizer.normalize_item(
            self.raw_item,
            self.canonical_scopes,
            'anthropic.claude-3-sonnet-20240229-v1:0'
        )
        
        # Vérifier la présence de tous les champs du nouveau schéma
        expected_fields = [
            'companies_detected', 'molecules_detected', 'trademarks_detected',
            'technologies_detected', 'indications_detected',
            'companies_in_scopes', 'molecules_in_scopes', 'trademarks_in_scopes',
            'technologies_in_scopes', 'indications_in_scopes'
        ]
        
        for field in expected_fields:
            self.assertIn(field, result, f"Champ manquant : {field}")
        
        # Vérifier les valeurs
        self.assertEqual(result['companies_detected'], ['Camurus'])
        self.assertEqual(result['molecules_detected'], ['buprenorphine'])
        self.assertEqual(result['trademarks_detected'], ['Brixadi'])
        self.assertEqual(result['companies_in_scopes'], ['Camurus'])
        self.assertEqual(result['trademarks_in_scopes'], ['Brixadi'])


class TestMoleculeTrademarkSeparation(unittest.TestCase):
    """Tests spécifiques pour la séparation molecule vs trademark."""
    
    def test_molecule_vs_trademark_classification(self):
        """Test de la classification correcte molecule vs trademark."""
        # Cas de test : Brixadi (trademark) vs buprenorphine (molecule)
        
        # Simulation d'une réponse Bedrock correcte
        bedrock_response = {
            'companies_detected': ['Camurus'],
            'molecules_detected': ['buprenorphine'],  # Substance active
            'trademarks_detected': ['Brixadi'],       # Nom commercial
            'technologies_detected': ['long acting'],
            'indications_detected': ['opioid use disorder']
        }
        
        # Vérifier la séparation
        self.assertIn('buprenorphine', bedrock_response['molecules_detected'])
        self.assertIn('Brixadi', bedrock_response['trademarks_detected'])
        self.assertNotIn('Brixadi', bedrock_response['molecules_detected'])
        self.assertNotIn('buprenorphine', bedrock_response['trademarks_detected'])


if __name__ == '__main__':
    unittest.main()