#!/usr/bin/env python3
"""
Test rapide - Vérification que tous les pure players bénéficient de la correction LAI
"""

import sys
import os
from datetime import datetime

# Ajouter le chemin vers src_v3
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src_v3'))

from vectora_core.ingest.config_loader_v3 import CanonicalConfig, load_from_local
from vectora_core.ingest.filter_engine import FilterEngineV3

def test_all_pure_players():
    """Test que tous les pure players ont require_lai_keywords=false"""
    
    print("Test - Tous les Pure Players LAI")
    print("=" * 40)
    
    # Charger la config
    canonical_path = os.path.join(os.path.dirname(__file__), '..', 'canonical')
    canonical_config = load_from_local(canonical_path)
    
    client_config = {
        'ingestion': {
            'ingestion_mode': 'balanced',
            'default_period_days': 7
        }
    }
    
    filter_engine = FilterEngineV3(canonical_config, client_config)
    
    # Liste des pure players depuis company_scopes.yaml
    pure_players = [
        "medincell", "camurus", "delsitech", "nanexa", "peptron",
        "bolder_biotechnology", "cristal_therapeutics", "durect",
        "eupraxia_pharmaceuticals", "foresee_pharmaceuticals", "g2gbio",
        "hanmi_pharmaceutical", "lidds", "taiwan_liposome"
    ]
    
    print(f"Test de {len(pure_players)} pure players:")
    print()
    
    all_success = True
    
    for company_id in pure_players:
        # Résoudre l'actor_type
        actor_type = filter_engine._resolve_actor_type(company_id, f"press_corporate__{company_id}")
        
        # Tester le filtre LAI directement
        from vectora_core.ingest.models import StructuredItem
        
        test_item = StructuredItem(
            item_id=f"test_{company_id}_001",
            run_id="test_all_pure_players",
            source_key=f"press_corporate__{company_id}",
            source_type="press_corporate",
            actor_type=actor_type,
            title=f"{company_id.title()} announces new development",
            url=f"https://{company_id}.com/news/development",
            published_at=datetime.now().isoformat(),
            ingested_at=datetime.now().isoformat(),
            content="Company announces new pharmaceutical development.",
            content_length=50,
            language="en",
            content_hash=f"hash_{company_id}",
            ingestion_profile_used="html_generic"
        )
        
        lai_passed, lai_details = filter_engine._apply_lai_keyword_filter(test_item, actor_type)
        
        # Vérifier les résultats
        is_pure_lai = (actor_type == "pure_lai")
        lai_not_required = not lai_details.get('required', True)
        lai_passes = lai_passed
        
        status = "OK" if (is_pure_lai and lai_not_required and lai_passes) else "ERREUR"
        
        print(f"  {company_id:20} | actor_type: {actor_type:8} | LAI required: {lai_details.get('required', True):5} | Status: {status}")
        
        if status == "ERREUR":
            all_success = False
    
    print()
    print(f"Resultat global: {'SUCCES' if all_success else 'ECHEC'}")
    
    if all_success:
        print("Tous les pure players beneficient de la correction LAI!")
    else:
        print("Certains pure players ont encore des problemes.")
    
    return all_success

if __name__ == "__main__":
    success = test_all_pure_players()
    sys.exit(0 if success else 1)