"""
Tests unitaires pour le mécanisme de retry Bedrock.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from botocore.exceptions import ClientError

from vectora_core.normalization.bedrock_client import _call_bedrock_with_retry


class TestBedrockRetry(unittest.TestCase):
    """Tests pour le wrapper de retry Bedrock."""
    
    def setUp(self):
        """Configuration des tests."""
        self.model_id = "eu.anthropic.claude-sonnet-4-5-20250929-v1:0"
        self.request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "messages": [{"role": "user", "content": "Test"}]
        }
    
    @patch('vectora_core.normalization.bedrock_client.get_bedrock_client')
    @patch('vectora_core.normalization.bedrock_client.time.sleep')
    def test_retry_on_throttling_success_on_second_attempt(self, mock_sleep, mock_get_client):
        """Test : retry réussi après une ThrottlingException."""
        # Mock du client Bedrock
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # Première tentative : ThrottlingException
        throttling_error = ClientError(
            {'Error': {'Code': 'ThrottlingException', 'Message': 'Too many requests'}},
            'InvokeModel'
        )
        
        # Deuxième tentative : succès
        success_response = {
            'body': MagicMock()
        }
        success_response['body'].read.return_value = json.dumps({
            'content': [{'text': '{"summary": "Test", "event_type": "other"}'}]
        }).encode('utf-8')
        
        mock_client.invoke_model.side_effect = [throttling_error, success_response]
        
        # Appel de la fonction
        result = _call_bedrock_with_retry(self.model_id, self.request_body, max_retries=3)
        
        # Vérifications
        self.assertEqual(mock_client.invoke_model.call_count, 2)
        self.assertEqual(mock_sleep.call_count, 1)
        self.assertIn("summary", result)
    
    @patch('vectora_core.normalization.bedrock_client.get_bedrock_client')
    @patch('vectora_core.normalization.bedrock_client.time.sleep')
    def test_retry_exhausted_after_max_retries(self, mock_sleep, mock_get_client):
        """Test : échec après épuisement des retries."""
        # Mock du client Bedrock
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # Toutes les tentatives échouent avec ThrottlingException
        throttling_error = ClientError(
            {'Error': {'Code': 'ThrottlingException', 'Message': 'Too many requests'}},
            'InvokeModel'
        )
        mock_client.invoke_model.side_effect = throttling_error
        
        # Appel de la fonction - doit lever une exception
        with self.assertRaises(ClientError):
            _call_bedrock_with_retry(self.model_id, self.request_body, max_retries=2)
        
        # Vérifications : 3 tentatives (1 initiale + 2 retries)
        self.assertEqual(mock_client.invoke_model.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)
    
    @patch('vectora_core.normalization.bedrock_client.get_bedrock_client')
    def test_no_retry_on_non_throttling_error(self, mock_get_client):
        """Test : pas de retry sur une erreur non-throttling."""
        # Mock du client Bedrock
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # Erreur de validation (pas de throttling)
        validation_error = ClientError(
            {'Error': {'Code': 'ValidationException', 'Message': 'Invalid input'}},
            'InvokeModel'
        )
        mock_client.invoke_model.side_effect = validation_error
        
        # Appel de la fonction - doit lever une exception immédiatement
        with self.assertRaises(ClientError):
            _call_bedrock_with_retry(self.model_id, self.request_body, max_retries=3)
        
        # Vérifications : une seule tentative, pas de retry
        self.assertEqual(mock_client.invoke_model.call_count, 1)
    
    @patch('vectora_core.normalization.bedrock_client.get_bedrock_client')
    def test_success_on_first_attempt(self, mock_get_client):
        """Test : succès dès la première tentative."""
        # Mock du client Bedrock
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # Succès immédiat
        success_response = {
            'body': MagicMock()
        }
        success_response['body'].read.return_value = json.dumps({
            'content': [{'text': '{"summary": "Test OK", "event_type": "clinical_update"}'}]
        }).encode('utf-8')
        
        mock_client.invoke_model.return_value = success_response
        
        # Appel de la fonction
        result = _call_bedrock_with_retry(self.model_id, self.request_body, max_retries=3)
        
        # Vérifications
        self.assertEqual(mock_client.invoke_model.call_count, 1)
        self.assertIn("summary", result)


if __name__ == '__main__':
    unittest.main()
