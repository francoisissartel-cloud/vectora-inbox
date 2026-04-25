#!/usr/bin/env python3
"""
Script de test pour valider les améliorations Phase 2
Test de la validation d'URL non-bloquante et des métriques de qualité
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src_v3'))

from vectora_core.ingest.config_loader_v3 import load_from_local
from vectora_core.ingest.source_router import SourceRouter
from vectora_core.ingest.parser_html import HTMLParserV3
from vectora_core.ingest.fetcher import Fetcher
from vectora_core.ingest.enhanced_run_reporter import EnhancedRunReporter
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_url_validation_function():
    """Test de la fonction de validation d'URL."""
    
    print("Test Phase 2 - Validation d'URL non-bloquante")
    print("=" * 50)
    
    try:
        # Charger la config
        canonical_path = os.path.join(os.path.dirname(__file__), '..', 'canonical')
        config = load_from_local(canonical_path)
        router = SourceRouter(config)
        
        # Résoudre DelSiTech pour tester
        delsitech_sources = router.resolve_specific_sources(["press_corporate__delsitech"])
        if not delsitech_sources:
            print("  Erreur: Source DelSiTech non résolue")
            return False
        
        delsitech_source = delsitech_sources[0]
        
        # Créer un parser HTML pour tester la validation
        fetcher = Fetcher()
        parser = HTMLParserV3(fetcher)
        
        # URLs de test
        test_urls = [
            "https://www.delsitech.com/delsitech-to-participate-in-chinabio-partnering-forum-2026/",  # Valide
            "https://www.delsitech.com/author/milla-runsala/",  # À exclure
            "https://www.delsitech.com/category/news/",  # À exclure
            "https://www.delsitech.com/tag/partnership/",  # À exclure
            "https://www.delsitech.com/some-regular-news/",  # Valide
        ]
        
        print("\\nTest validation URLs DelSiTech:")
        validation_results = []
        
        for url in test_urls:
            result = parser._validate_article_url(url, delsitech_source)
            validation_results.append(result)
            
            status = "VALIDE" if result["is_valid"] else "EXCLUE"
            warnings = ", ".join(result["warnings"]) if result["warnings"] else "Aucun"
            print(f"  {status}: {url}")
            print(f"    Type: {result['url_type']}, Warnings: {warnings}")
        
        # Vérifier les résultats attendus
        expected_invalid = [
            "https://www.delsitech.com/author/milla-runsala/",
            "https://www.delsitech.com/category/news/",
            "https://www.delsitech.com/tag/partnership/"
        ]
        
        actual_invalid = [url for i, url in enumerate(test_urls) if not validation_results[i]["is_valid"]]
        
        if set(expected_invalid) == set(actual_invalid):
            print("\\n  Validation d'URL fonctionne correctement")
            return True
        else:
            print(f"\\n  Erreur: URLs invalides attendues {expected_invalid}")
            print(f"         URLs invalides détectées {actual_invalid}")
            return False
            
    except Exception as e:
        print(f"\\nErreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_quality_metrics():
    """Test des métriques de qualité."""
    
    print("\\nTest métriques de qualité")
    print("=" * 30)
    
    try:
        # Créer un reporter pour tester
        client_config = {"client_id": "test"}
        reporter = EnhancedRunReporter("test_run", client_config, "2026-04-21T10:00:00Z")
        
        # Simuler des résultats de validation
        validation_results = [
            {"is_valid": True, "warnings": [], "url_type": "article"},
            {"is_valid": False, "warnings": ["Matches exclude pattern: /author/"], "url_type": "excluded"},
            {"is_valid": False, "warnings": ["Matches exclude pattern: /category/"], "url_type": "excluded"},
            {"is_valid": True, "warnings": [], "url_type": "article"},
            {"is_valid": False, "warnings": ["Matches generic exclude pattern: /tag/"], "url_type": "generic_excluded"},
        ]
        
        # Ajouter les métriques (nécessite d'abord créer un source report)
        from vectora_core.ingest.models import SourceReport
        
        source_report = SourceReport(
            source_key="press_corporate__delsitech",
            status="success",
            ingestion_profile_used="html_generic",
            items_found=5,
            items_with_date=4,
            items_with_content=5,
            items_passed_filters=2,
            avg_date_confidence=0.8,
            fetch_time_seconds=1.0,
            parse_time_seconds=2.0,
            filter_time_seconds=0.5,
            quality_issues=[],
            errors=[]
        )
        
        reporter.source_reports = [source_report]
        
        # Ajouter les métriques de validation
        reporter.add_url_validation_metrics("press_corporate__delsitech", validation_results)
        
        # Vérifier que les métriques ont été ajoutées
        updated_report = reporter.source_reports[0]
        if hasattr(updated_report, 'quality_metrics'):
            metrics = updated_report.quality_metrics
            print(f"  URLs validées: {metrics.get('urls_validated', 0)}")
            print(f"  URLs invalides: {metrics.get('invalid_urls_detected', 0)}")
            print(f"  Taux de validation: {metrics.get('url_validation_rate', 0):.2%}")
            print(f"  Types d'exclusion: {metrics.get('exclusion_breakdown', {})}")
            
            # Vérifier les valeurs attendues
            if (metrics.get('urls_validated') == 5 and 
                metrics.get('invalid_urls_detected') == 3 and
                abs(metrics.get('url_validation_rate', 0) - 0.4) < 0.01):
                print("  Métriques de qualité correctes")
                return True
            else:
                print("  Erreur dans les métriques calculées")
                print(f"    Attendu: 5 URLs, 3 invalides, 40% taux")
                print(f"    Obtenu: {metrics.get('urls_validated')} URLs, {metrics.get('invalid_urls_detected')} invalides, {metrics.get('url_validation_rate', 0):.1%} taux")
                return False
        else:
            print("  Erreur: Métriques de qualité non ajoutées")
            print(f"  Attributs du report: {dir(updated_report)}")
            return False
            
    except Exception as e:
        print(f"\\nErreur lors du test métriques: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """Test d'intégration des améliorations Phase 2."""
    
    print("\\nTest d'intégration Phase 2")
    print("=" * 30)
    
    # Vérifier que les patterns d'exclusion de Phase 1 sont toujours là
    try:
        canonical_path = os.path.join(os.path.dirname(__file__), '..', 'canonical')
        config = load_from_local(canonical_path)
        
        delsitech_config = config.get_source_config("press_corporate__delsitech")
        exclude_patterns = delsitech_config.get('listing_selectors', {}).get('url_exclude_patterns', [])
        
        expected_patterns = ["/author/", "/category/", "/tag/"]
        if all(pattern in exclude_patterns for pattern in expected_patterns):
            print("  Phase 1 patterns toujours présents")
        else:
            print("  Erreur: Patterns Phase 1 manquants")
            return False
        
        # Vérifier que la validation utilise ces patterns
        router = SourceRouter(config)
        delsitech_source = router.resolve_specific_sources(["press_corporate__delsitech"])[0]
        
        fetcher = Fetcher()
        parser = HTMLParserV3(fetcher)
        
        # Test avec URL d'auteur (doit être exclue)
        result = parser._validate_article_url("https://www.delsitech.com/author/test/", delsitech_source)
        if not result["is_valid"] and "/author/" in str(result["warnings"]):
            print("  Intégration Phase 1 + Phase 2 réussie")
            return True
        else:
            print("  Erreur: Intégration Phase 1 + Phase 2 échouée")
            return False
            
    except Exception as e:
        print(f"\\nErreur lors du test d'intégration: {e}")
        return False

if __name__ == "__main__":
    print("Phase 2 - Demarrage tests validation URL securisee")
    
    success1 = test_url_validation_function()
    success2 = test_quality_metrics()
    success3 = test_integration()
    
    if success1 and success2 and success3:
        print("\\nPhase 2 - Validation d'URL securisee implementee avec succes!")
        print("Prochaine etape: Phase 3 - Correction du filtrage LAI")
    else:
        print("\\nPhase 2 - Problemes detectes, verifier les implementations")
        sys.exit(1)