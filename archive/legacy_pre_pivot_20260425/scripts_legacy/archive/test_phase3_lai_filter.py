#!/usr/bin/env python3
"""
Script de test pour valider la correction du filtrage LAI (Phase 3)
Test que les pure_lai n'ont plus require_lai_keywords=true
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src_v3'))

from vectora_core.ingest.config_loader_v3 import load_from_local
from vectora_core.ingest.source_router import SourceRouter
from vectora_core.ingest.filter_engine import FilterEngineV3
from vectora_core.ingest.models import StructuredItem
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_lai_filter_correction():
    """Test que la correction du filtre LAI fonctionne pour pure_lai."""
    
    print("Test Phase 3 - Correction filtrage LAI")
    print("=" * 40)
    
    try:
        # Charger la config
        canonical_path = os.path.join(os.path.dirname(__file__), '..', 'canonical')
        config = load_from_local(canonical_path)
        
        # Créer un client config de test
        client_config = {
            "client_id": "test",
            "ingestion": {
                "ingestion_mode": "balanced",
                "default_period_days": 50
            }
        }
        
        # Créer le filter engine
        filter_engine = FilterEngineV3(config, client_config)
        
        # Créer un item de test Nanexa (pure_lai)
        test_item = StructuredItem(
            item_id="test_nanexa_item",
            run_id="test_run",
            source_key="press_corporate__nanexa",
            source_type="press_corporate",
            actor_type="pure_lai",  # Sera résolu par le filter engine
            title="Nanexa announces exercise of warrants",
            url="https://nanexa.com/mfn_news/test/",
            published_at="2026-04-02",
            ingested_at=datetime.utcnow().isoformat() + "Z",
            content="Nanexa AB announces exercise of warrants for subscription of shares.",
            content_length=100,
            language="en",
            content_hash="test_hash",
            ingestion_profile_used="html_generic"
        )
        
        print("\\n1. Test item Nanexa (pure_lai):")
        print(f"   Title: {test_item.title}")
        print(f"   Actor type: {test_item.actor_type}")
        
        # Appliquer le filtre LAI directement
        lai_passed, lai_details = filter_engine._apply_lai_keyword_filter(test_item, "pure_lai")
        
        print("\\n2. Resultat filtre LAI:")
        print(f"   Required: {lai_details.get('required', 'N/A')}")
        print(f"   Passed: {lai_details.get('passed', 'N/A')}")
        print(f"   Failure reason: {lai_details.get('failure_reason', 'None')}")
        
        # Vérifier le résultat attendu
        if lai_details.get('required') == False and lai_details.get('passed') == True:
            print("   SUCCES: pure_lai n'a plus require_lai_keywords=true")
            return True
        else:
            print("   ECHEC: pure_lai a encore require_lai_keywords=true")
            return False
            
    except Exception as e:
        print(f"\\nErreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_hybrid_still_requires_lai():
    """Test que les hybrid ont toujours require_lai_keywords=true."""
    
    print("\\n3. Test hybrid (doit garder require_lai_keywords=true):")
    
    try:
        # Charger la config
        canonical_path = os.path.join(os.path.dirname(__file__), '..', 'canonical')
        config = load_from_local(canonical_path)
        
        client_config = {
            "client_id": "test",
            "ingestion": {
                "ingestion_mode": "balanced",
                "default_period_days": 50
            }
        }
        
        filter_engine = FilterEngineV3(config, client_config)
        
        # Créer un item de test Pfizer (hybrid)
        test_item = StructuredItem(
            item_id="test_pfizer_item",
            run_id="test_run",
            source_key="press_corporate__pfizer",
            source_type="press_corporate",
            actor_type="hybrid",
            title="Pfizer announces new drug development",
            url="https://www.pfizer.com/news/test/",
            published_at="2026-04-02",
            ingested_at=datetime.utcnow().isoformat() + "Z",
            content="Pfizer announces development of new pharmaceutical product.",
            content_length=100,
            language="en",
            content_hash="test_hash",
            ingestion_profile_used="html_generic"
        )
        
        # Appliquer le filtre LAI
        lai_passed, lai_details = filter_engine._apply_lai_keyword_filter(test_item, "hybrid")
        
        print(f"   Required: {lai_details.get('required', 'N/A')}")
        print(f"   Passed: {lai_details.get('passed', 'N/A')}")
        
        # Vérifier que hybrid a toujours require_lai_keywords=true
        if lai_details.get('required') == True:
            print("   SUCCES: hybrid garde require_lai_keywords=true")
            return True
        else:
            print("   ECHEC: hybrid n'a plus require_lai_keywords=true")
            return False
            
    except Exception as e:
        print(f"   Erreur: {e}")
        return False

def test_full_filter_pipeline():
    """Test du pipeline complet de filtrage."""
    
    print("\\n4. Test pipeline complet:")
    
    try:
        canonical_path = os.path.join(os.path.dirname(__file__), '..', 'canonical')
        config = load_from_local(canonical_path)
        
        client_config = {
            "client_id": "test",
            "ingestion": {
                "ingestion_mode": "balanced",
                "default_period_days": 50
            }
        }
        
        filter_engine = FilterEngineV3(config, client_config)
        
        # Item Nanexa avec contenu LAI (devrait passer)
        nanexa_item = StructuredItem(
            item_id="test_nanexa_lai",
            run_id="test_run",
            source_key="press_corporate__nanexa",
            source_type="press_corporate",
            actor_type="pure_lai",
            title="Nanexa Demonstrates Feasibility of Quarterly Semaglutide Dosing with PharmaShell",
            url="https://nanexa.com/mfn_news/test-lai/",
            published_at="2026-04-02",
            ingested_at=datetime.utcnow().isoformat() + "Z",
            content="Nanexa's PharmaShell platform enables quarterly semaglutide dosing.",
            content_length=100,
            language="en",
            content_hash="test_hash_lai",
            ingestion_profile_used="html_generic"
        )
        
        # Item Nanexa sans contenu LAI (devrait aussi passer car pure_lai)
        nanexa_item_no_lai = StructuredItem(
            item_id="test_nanexa_no_lai",
            run_id="test_run",
            source_key="press_corporate__nanexa",
            source_type="press_corporate",
            actor_type="pure_lai",
            title="Nanexa announces exercise of warrants",
            url="https://nanexa.com/mfn_news/test-no-lai/",
            published_at="2026-04-02",
            ingested_at=datetime.utcnow().isoformat() + "Z",
            content="Nanexa announces exercise of warrants for subscription of shares.",
            content_length=100,
            language="en",
            content_hash="test_hash_no_lai",
            ingestion_profile_used="html_generic"
        )
        
        # Tester les deux items
        items = [nanexa_item, nanexa_item_no_lai]
        accepted, rejected = filter_engine.filter_items(items, company_id="nanexa")
        
        print(f"   Items testes: {len(items)}")
        print(f"   Items acceptes: {len(accepted)}")
        print(f"   Items rejetes: {len(rejected)}")
        
        # Vérifier les résultats
        if len(accepted) == 2 and len(rejected) == 0:
            print("   SUCCES: Tous les items pure_lai passent (avec et sans LAI keywords)")
            
            # Vérifier les détails du filtre LAI
            for item in accepted:
                lai_filter = item.filter_analysis.get('lai_keyword_filter', {})
                print(f"   Item '{item.title[:30]}...': required={lai_filter.get('required', 'N/A')}")
            
            return True
        else:
            print("   ECHEC: Items pure_lai rejetes incorrectement")
            for item in rejected:
                reason = item.get_rejection_reason()
                print(f"     Rejete: {item.title[:30]}... - Raison: {reason}")
            return False
            
    except Exception as e:
        print(f"   Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Phase 3 - Test correction filtrage LAI")
    
    success1 = test_lai_filter_correction()
    success2 = test_hybrid_still_requires_lai()
    success3 = test_full_filter_pipeline()
    
    if success1 and success2 and success3:
        print("\\nPhase 3 - Correction filtrage LAI implementee avec succes!")
        print("Prochaine etape: Phase 4 - Activation validation bloquante")
    else:
        print("\\nPhase 3 - Problemes detectes dans la correction")
        sys.exit(1)