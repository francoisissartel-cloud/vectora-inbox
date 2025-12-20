"""
Tests unitaires pour l'aplatissement des scopes complexes.
"""

import pytest
from unittest.mock import patch, MagicMock
from src_v2.vectora_core.shared.config_loader import load_canonical_scopes


def test_complex_scope_flattening():
    """Test aplatissement scope complexe lai_keywords"""
    
    # Mock des données S3 avec structure complexe
    mock_scope_data = {
        "lai_keywords": {
            "_metadata": {"profile": "technology_complex"},
            "core_phrases": ["long-acting injectable", "depot injection"],
            "technology_terms": ["PharmaShell®", "drug delivery"]
        },
        "simple_scope": ["term1", "term2"]
    }
    
    # Mock de s3_io.read_yaml_from_s3
    with patch('src_v2.vectora_core.shared.s3_io.read_yaml_from_s3') as mock_s3_read:
        mock_s3_read.return_value = mock_scope_data
        
        # Test de la fonction
        result = load_canonical_scopes("test-bucket")
        
        # Assertions
        assert isinstance(result["lai_keywords"], list)
        assert "long-acting injectable" in result["lai_keywords"]
        assert "depot injection" in result["lai_keywords"]
        assert "PharmaShell®" in result["lai_keywords"]
        assert "drug delivery" in result["lai_keywords"]
        assert len(result["lai_keywords"]) == 4
        
        # Scope simple inchangé
        assert result["simple_scope"] == ["term1", "term2"]
        
        # Métadonnées ignorées
        assert "_metadata" not in str(result["lai_keywords"])


def test_simple_scope_preservation():
    """Test que les scopes simples sont préservés"""
    
    mock_scope_data = {
        "lai_companies_global": ["MedinCell", "Camurus", "Nanexa"],
        "simple_list": ["item1", "item2"]
    }
    
    with patch('src_v2.vectora_core.shared.s3_io.read_yaml_from_s3') as mock_s3_read:
        mock_s3_read.return_value = mock_scope_data
        
        result = load_canonical_scopes("test-bucket")
        
        # Scopes simples inchangés
        assert result["lai_companies_global"] == ["MedinCell", "Camurus", "Nanexa"]
        assert result["simple_list"] == ["item1", "item2"]


def test_empty_complex_scope():
    """Test gestion des scopes complexes vides"""
    
    mock_scope_data = {
        "empty_complex": {
            "_metadata": {"profile": "test"},
            "empty_category": []
        }
    }
    
    with patch('src_v2.vectora_core.shared.s3_io.read_yaml_from_s3') as mock_s3_read:
        mock_s3_read.return_value = mock_scope_data
        
        result = load_canonical_scopes("test-bucket")
        
        # Scope complexe vide devient liste vide
        assert result["empty_complex"] == []


if __name__ == "__main__":
    pytest.main([__file__])