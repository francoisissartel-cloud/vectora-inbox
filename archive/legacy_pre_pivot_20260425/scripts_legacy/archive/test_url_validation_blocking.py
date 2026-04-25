#!/usr/bin/env python3
"""
Test Phase 4.2 - Validation Bloquante des URLs
Vérifie que les URLs problématiques sont maintenant filtrées
"""

import sys
import os
from datetime import datetime

# Ajouter le chemin vers src_v3
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src_v3'))

from vectora_core.ingest.config_loader_v3 import load_from_local
from vectora_core.ingest.parser_html import HTMLParserV3
from vectora_core.ingest.fetcher import Fetcher
from vectora_core.ingest.models import ResolvedSource

def test_url_validation_blocking():
    """Test que la validation bloquante des URLs fonctionne"""
    
    print("Test Phase 4.2 - Validation Bloquante URLs")
    print("=" * 45)
    
    # Charger la config
    canonical_path = os.path.join(os.path.dirname(__file__), '..', 'canonical')
    canonical_config = load_from_local(canonical_path)
    
    # Créer un fetcher et parser
    fetcher = Fetcher()
    parser = HTMLParserV3(fetcher)
    
    # Test cases avec URLs problématiques
    test_cases = [
        {
            "source_key": "press_corporate__delsitech",
            "test_urls": [
                "https://www.delsitech.com/news/article-123/",  # URL valide
                "https://www.delsitech.com/author/milla-runsala/",  # URL à filtrer
                "https://www.delsitech.com/category/events/",  # URL à filtrer
                "https://www.delsitech.com/tag/conference/",  # URL à filtrer
            ]
        },
        {
            "source_key": "press_corporate__camurus", 
            "test_urls": [
                "https://www.camurus.com/media/press-releases/2026/quarterly-results/",  # URL valide
                "https://www.camurus.com/media/press-releases/",  # URL à filtrer (listing)
            ]
        }
    ]
    
    print("Test des patterns d'exclusion configurés:")
    print()
    
    all_success = True
    
    for test_case in test_cases:
        source_key = test_case["source_key"]
        print(f"Source: {source_key}")
        
        # Récupérer la config de la source
        source_config = canonical_config.get_source_config(source_key)
        if not source_config:
            print(f"  ERREUR: Config non trouvée pour {source_key}")
            all_success = False
            continue
        
        # Créer une ResolvedSource simplifiée pour le test
        resolved_source = ResolvedSource(
            source_key=source_key,
            company_id=source_key.split('__')[1] if '__' in source_key else None,
            source_type="press_corporate",
            actor_type="pure_lai",  # Simplifié pour le test
            homepage_url=f"https://www.{source_key.split('__')[1]}.com",
            news_url=source_config.get('news_url', ''),
            ingestion_profile=source_config.get('ingestion_profile', 'html_generic'),
            profile_config={},
            listing_selectors=source_config.get('listing_selectors', {}),
            date_selectors=source_config.get('date_selectors', {}),
            prefetch_filter=False,
            pagination=None,
            validated=True
        )
        
        # Tester chaque URL
        for url in test_case["test_urls"]:
            validation = parser._validate_article_url(url, resolved_source)
            
            is_valid = validation["is_valid"]
            warnings = validation.get("warnings", [])
            url_type = validation.get("url_type", "unknown")
            
            # Déterminer si l'URL devrait être filtrée
            should_be_filtered = any(pattern in url for pattern in ["/author/", "/category/", "/tag/", "/press-releases/?$"])\n            
            # Résultat attendu vs réel
            expected_valid = not should_be_filtered\n            test_passed = (is_valid == expected_valid)\n            \n            status = "OK" if test_passed else "ERREUR"\n            filter_status = "FILTRE" if not is_valid else "PASSE"\n            \n            print(f"  {url}")
            print(f"    Status: {status} | {filter_status} | Type: {url_type}")
            if warnings:
                print(f"    Warnings: {warnings}")
            \n            if not test_passed:\n                all_success = False\n        \n        print()\n    \n    # Test des patterns génériques\n    print("Test des patterns génériques d'exclusion:")\n    print()\n    \n    generic_test_urls = [\n        "https://example.com/news/article-123/",  # Valide\n        "https://example.com/author/john-doe/",   # Générique à filtrer\n        "https://example.com/category/news/",     # Générique à filtrer\n        "https://example.com/page/2",             # Générique à filtrer\n        "https://example.com/press-releases/",    # Générique à filtrer (listing)\n    ]\n    \n    # Source générique pour test\n    generic_source = ResolvedSource(\n        source_key="test_generic",\n        company_id="test",\n        source_type="press_corporate",\n        actor_type="unknown",\n        homepage_url="https://example.com",\n        news_url="https://example.com/news/",\n        ingestion_profile="html_generic",\n        profile_config={},\n        listing_selectors={},  # Pas de patterns spécifiques\n        date_selectors={},\n        prefetch_filter=False,\n        pagination=None,\n        validated=True\n    )\n    \n    for url in generic_test_urls:\n        validation = parser._validate_article_url(url, generic_source)\n        \n        is_valid = validation["is_valid"]\n        warnings = validation.get("warnings", [])\n        url_type = validation.get("url_type", "unknown")\n        \n        # Les patterns génériques devraient filtrer certaines URLs\n        should_be_filtered = any(pattern in url for pattern in ["/author/", "/category/", "/page/", "/press-releases/?$"])\n        expected_valid = not should_be_filtered\n        test_passed = (is_valid == expected_valid)\n        \n        status = "OK" if test_passed else "ERREUR"\n        filter_status = "FILTRE" if not is_valid else "PASSE"\n        \n        print(f"  {url}")
        print(f"    Status: {status} | {filter_status} | Type: {url_type}")
        if warnings:
            print(f"    Warnings: {warnings}")
        \n        if not test_passed:\n            all_success = False\n    \n    print()\n    print(f"Resultat Final: {'SUCCES' if all_success else 'ECHEC'}")\n    \n    if all_success:\n        print("La validation bloquante des URLs fonctionne correctement!")\n        print("Les URLs problematiques seront maintenant filtrees automatiquement.")\n    else:\n        print("Des problemes subsistent avec la validation des URLs.")\n    \n    return all_success\n\nif __name__ == "__main__":\n    success = test_url_validation_blocking()\n    sys.exit(0 if success else 1)