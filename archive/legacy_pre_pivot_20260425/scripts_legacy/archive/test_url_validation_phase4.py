#!/usr/bin/env python3
"""
Test Phase 4.2 - Validation Bloquante des URLs
Verifie que les URLs problematiques sont maintenant filtrees
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
    
    # Creer un fetcher et parser
    fetcher = Fetcher()
    parser = HTMLParserV3(fetcher)
    
    # Test cases avec URLs problematiques
    test_cases = [
        {
            "source_key": "press_corporate__delsitech",
            "test_urls": [
                "https://www.delsitech.com/news/article-123/",  # URL valide
                "https://www.delsitech.com/author/milla-runsala/",  # URL a filtrer
                "https://www.delsitech.com/category/events/",  # URL a filtrer
                "https://www.delsitech.com/tag/conference/",  # URL a filtrer
            ]
        },
        {
            "source_key": "press_corporate__camurus", 
            "test_urls": [
                "https://www.camurus.com/media/press-releases/2026/quarterly-results/",  # URL valide
                "https://www.camurus.com/media/press-releases/",  # URL a filtrer (listing)
            ]
        }
    ]
    
    print("Test des patterns d'exclusion configures:")
    print()
    
    all_success = True
    
    for test_case in test_cases:
        source_key = test_case["source_key"]
        print(f"Source: {source_key}")
        
        # Recuperer la config de la source
        source_config = canonical_config.get_source_config(source_key)
        if not source_config:
            print(f"  ERREUR: Config non trouvee pour {source_key}")
            all_success = False
            continue
        
        # Creer une ResolvedSource simplifiee pour le test
        resolved_source = ResolvedSource(
            source_key=source_key,
            company_id=source_key.split('__')[1] if '__' in source_key else None,
            source_type="press_corporate",
            actor_type="pure_lai",  # Simplifie pour le test
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
            
            # Determiner si l'URL devrait etre filtree
            should_be_filtered = (
                "/author/" in url or 
                "/category/" in url or 
                "/tag/" in url or 
                url.endswith("/media/press-releases/") or
                url.endswith("/press-releases/")
            )
            
            # Resultat attendu vs reel
            expected_valid = not should_be_filtered
            test_passed = (is_valid == expected_valid)
            
            status = "OK" if test_passed else "ERREUR"
            filter_status = "FILTRE" if not is_valid else "PASSE"
            
            print(f"  {url}")
            print(f"    Status: {status} | {filter_status} | Type: {url_type}")
            if warnings:
                print(f"    Warnings: {warnings}")
            
            if not test_passed:
                all_success = False
        
        print()
    
    print(f"Resultat Final: {'SUCCES' if all_success else 'ECHEC'}")
    
    if all_success:
        print("La validation bloquante des URLs fonctionne correctement!")
        print("Les URLs problematiques seront maintenant filtrees automatiquement.")
    else:
        print("Des problemes subsistent avec la validation des URLs.")
    
    return all_success

if __name__ == "__main__":
    success = test_url_validation_blocking()
    sys.exit(0 if success else 1)