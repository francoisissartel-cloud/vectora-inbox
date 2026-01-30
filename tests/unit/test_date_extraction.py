"""
Tests unitaires pour l'extraction des dates de publication
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src_v2'))

from datetime import datetime
from vectora_core.ingest.content_parser import extract_real_publication_date, _parse_date_string


def test_rss_parsed_date():
    """Test extraction date depuis published_parsed"""
    class MockEntry:
        published_parsed = (2025, 11, 24, 10, 30, 0, 0, 0, 0)
    
    result = extract_real_publication_date(MockEntry(), {})
    assert result['date'] == '2025-11-24'
    assert result['date_source'] == 'rss_parsed'
    print("[OK] Test RSS parsed")


def test_content_extraction_medincell():
    """Test extraction date depuis contenu MedinCell"""
    entry = {
        'content': 'Published on December 9, 2025December 9, 2025',
        'title': 'MedinCell NDA',
        'summary': ''
    }
    
    source_config = {
        'date_extraction_patterns': [
            r'(\w+ \d{1,2}, \d{4})\w*'
        ]
    }
    
    result = extract_real_publication_date(entry, source_config)
    assert result['date'] == '2025-12-09'
    assert result['date_source'] == 'content_extraction'
    print("[OK] Test MedinCell content")


def test_content_extraction_nanexa():
    """Test extraction date depuis contenu Nanexa"""
    entry = {
        'content': 'Press release 27 January, 2026',
        'title': 'Nanexa Semaglutide',
        'summary': ''
    }
    
    source_config = {
        'date_extraction_patterns': [
            r'(\d{1,2} \w+, \d{4})'
        ]
    }
    
    result = extract_real_publication_date(entry, source_config)
    assert result['date'] == '2026-01-27'
    assert result['date_source'] == 'content_extraction'
    print("[OK] Test Nanexa content")


def test_content_extraction_camurus():
    """Test extraction date depuis contenu Camurus"""
    entry = {
        'content': 'Released 09 January 2026',
        'title': 'Camurus Oclaiz',
        'summary': ''
    }
    
    source_config = {
        'date_extraction_patterns': [
            r'(\d{2} \w+ \d{4})'
        ]
    }
    
    result = extract_real_publication_date(entry, source_config)
    assert result['date'] == '2026-01-09'
    assert result['date_source'] == 'content_extraction'
    print("[OK] Test Camurus content")


def test_fallback_date():
    """Test fallback sur date d'ingestion"""
    entry = {
        'content': 'No date here',
        'title': 'Test',
        'summary': ''
    }
    
    result = extract_real_publication_date(entry, {})
    assert result['date_source'] == 'ingestion_fallback'
    assert result['date'] == datetime.now().strftime('%Y-%m-%d')
    print("[OK] Test fallback")


def test_parse_date_formats():
    """Test parsing de différents formats de dates"""
    test_cases = [
        ('2025-11-24', '2025-11-24'),
        ('November 24, 2025', '2025-11-24'),
        ('24 November 2025', '2025-11-24'),
        ('27 January, 2026', '2026-01-27'),
        ('09 January 2026', '2026-01-09'),
    ]
    
    for input_date, expected in test_cases:
        result = _parse_date_string(input_date)
        assert result == expected, f"Failed for {input_date}: got {result}, expected {expected}"
    
    print("[OK] Test parse formats")


if __name__ == '__main__':
    print("\nTests unitaires extraction dates\n")
    test_rss_parsed_date()
    test_content_extraction_medincell()
    test_content_extraction_nanexa()
    test_content_extraction_camurus()
    test_fallback_date()
    test_parse_date_formats()
    print("\nTous les tests unitaires passes!\n")
