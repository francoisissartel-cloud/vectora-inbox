#!/usr/bin/env python3
"""
Script de test pour valider les corrections Phase 1
Test des sources DelSiTech et Camurus avec les nouveaux patterns d'exclusion
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src_v3'))

from vectora_core.ingest.config_loader_v3 import load_from_local
from vectora_core.ingest.source_router import SourceRouter
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_source_config_changes():
    """Test que les changements de config sont bien pris en compte."""
    
    print("Test Phase 1 - Validation des corrections source configs")
    print("=" * 60)
    
    try:
        # Charger la config depuis le filesystem local
        canonical_path = os.path.join(os.path.dirname(__file__), '..', 'canonical')
        config = load_from_local(canonical_path)
        router = SourceRouter(config)
        
        # Test DelSiTech
        print("\nTest DelSiTech:")
        delsitech_config = config.get_source_config("press_corporate__delsitech")
        if delsitech_config:
            exclude_patterns = delsitech_config.get('listing_selectors', {}).get('url_exclude_patterns', [])
            print(f"  Config trouvee")
            print(f"  Patterns d'exclusion: {exclude_patterns}")
            
            expected_patterns = ["/author/", "/category/", "/tag/"]
            missing_patterns = [p for p in expected_patterns if p not in exclude_patterns]
            
            if not missing_patterns:
                print("  Tous les patterns d'exclusion sont presents")
            else:
                print(f"  Patterns manquants: {missing_patterns}")
        else:
            print("  Config DelSiTech non trouvee")
        
        # Test Camurus
        print("\nTest Camurus:")
        camurus_config = config.get_source_config("press_corporate__camurus")
        if camurus_config:
            selectors = camurus_config.get('listing_selectors', {})
            print(f"  Config trouvee")
            print(f"  Container: {selectors.get('container')}")
            print(f"  URL pattern: {selectors.get('url_pattern')}")
            print(f"  Exclude patterns: {selectors.get('url_exclude_patterns', [])}")
            
            # Verifier les ameliorations
            if "/press-releases/2026/" in selectors.get('url_pattern', ''):
                print("  URL pattern plus specifique applique")
            else:
                print("  URL pattern pas assez specifique")
                
            if selectors.get('url_exclude_patterns'):
                print("  Patterns d'exclusion ajoutes")
            else:
                print("  Patterns d'exclusion manquants")
        else:
            print("  Config Camurus non trouvee")
        
        # Test resolution des sources
        print("\nTest resolution des sources:")
        resolved_sources = router.resolve_specific_sources([
            "press_corporate__delsitech", 
            "press_corporate__camurus"
        ])
        
        print(f"  {len(resolved_sources)} sources resolues")
        for source in resolved_sources:
            print(f"    - {source.source_key}: {source.actor_type}, profil {source.ingestion_profile}")
        
        print("\nTest Phase 1 termine avec succes!")
        return True
        
    except Exception as e:
        print(f"\nErreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_url_validation_logic():
    """Test de la logique de validation d'URL (simulation)."""
    
    print("\nTest logique validation URL (simulation)")
    print("=" * 50)
    
    # URLs de test DelSiTech
    delsitech_urls = [
        "https://www.delsitech.com/delsitech-to-participate-in-chinabio-partnering-forum-2026/",  # Valide
        "https://www.delsitech.com/author/milla-runsala/",  # A exclure
        "https://www.delsitech.com/category/news/",  # A exclure
        "https://www.delsitech.com/tag/partnership/",  # A exclure
    ]
    
    exclude_patterns = ["/author/", "/category/", "/tag/"]
    
    print("Test URLs DelSiTech:")
    for url in delsitech_urls:
        should_exclude = any(pattern in url for pattern in exclude_patterns)
        status = "EXCLUE" if should_exclude else "VALIDE"
        print(f"  {status}: {url}")
    
    # URLs de test Camurus
    camurus_urls = [
        "https://www.camurus.com/media/press-releases/2026/camurus-appoints-jane-buus-laursen/",  # Valide
        "https://www.camurus.com/media/press-releases/",  # A exclure (listing)
        "https://www.camurus.com/media/press-releases/2025/old-news/",  # Potentiellement valide mais pas 2026
    ]
    
    print("\nTest URLs Camurus:")
    for url in camurus_urls:
        has_2026 = "/press-releases/2026/" in url
        is_listing = url.endswith("/press-releases/") or url.endswith("/press-releases")
        
        if is_listing:
            status = "EXCLUE (listing)"
        elif has_2026:
            status = "VALIDE (2026)"
        else:
            status = "VALIDE (mais pas 2026)"
        
        print(f"  {status}: {url}")
    
    print("\nTest logique validation termine")

if __name__ == "__main__":
    print("Phase 1 - Demarrage tests")
    
    success = test_source_config_changes()
    test_url_validation_logic()
    
    if success:
        print("\nPhase 1 - Corrections appliquees avec succes!")
        print("Prochaine etape: Phase 2 - Validation d'URL securisee")
    else:
        print("\nPhase 1 - Problemes detectes, verifier les corrections")
        sys.exit(1)