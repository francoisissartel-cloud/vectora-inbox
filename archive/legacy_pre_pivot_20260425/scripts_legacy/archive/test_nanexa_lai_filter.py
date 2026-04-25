#!/usr/bin/env python3
"""
Test spécifique Nanexa - Phase 3.3
Vérifie que le filtre LAI keywords n'est plus appliqué aux pure_lai
"""

import sys
import os
import json
from datetime import datetime

# Ajouter le chemin vers src_v3
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src_v3'))

from vectora_core.ingest.config_loader_v3 import CanonicalConfig, load_from_local
from vectora_core.ingest.filter_engine import FilterEngineV3
from vectora_core.ingest.models import StructuredItem

def test_nanexa_lai_filter():
    """Test que Nanexa (pure_lai) n'a pas de filtre LAI obligatoire"""
    
    print("Test Phase 3.3 - Nanexa LAI Filter")
    print("=" * 50)
    
    # 1. Charger la config canonique depuis le filesystem local
    canonical_path = os.path.join(os.path.dirname(__file__), '..', 'canonical')
    canonical_config = load_from_local(canonical_path)
    
    # 2. Config client de test
    client_config = {
        'ingestion': {
            'ingestion_mode': 'balanced',
            'default_period_days': 7
        }
    }
    
    # 3. Initialiser le filter engine
    filter_engine = FilterEngineV3(canonical_config, client_config)
    
    # 4. Vérifier la résolution d'actor_type pour Nanexa
    print("\nDiagnostic Actor Type:")
    actor_type = filter_engine._resolve_actor_type("nanexa", "press_corporate__nanexa")
    print(f"   Company ID: nanexa")
    print(f"   Source Key: press_corporate__nanexa")
    print(f"   Resolved Actor Type: {actor_type}")
    
    # 5. Vérifier les règles de filtrage
    print("\nRegles de Filtrage:")
    filter_rules = canonical_config.filter_rules.get('filter_rules', {})
    if actor_type in filter_rules:
        actor_rules = filter_rules[actor_type]
        require_lai = actor_rules.get('require_lai_keywords', True)
        print(f"   Actor Type: {actor_type}")
        print(f"   require_lai_keywords: {require_lai}")
        print(f"   lai_keyword_scopes: {actor_rules.get('lai_keyword_scopes', [])}")
    else:
        print(f"   Aucune regle trouvee pour actor_type: {actor_type}")
    
    # 6. Créer un item de test Nanexa (sans keywords LAI)
    test_item = StructuredItem(
        item_id="test_nanexa_001",
        run_id="test_run_phase3_3",
        source_key="press_corporate__nanexa",
        source_type="press_corporate",
        actor_type=actor_type,  # Sera résolu dynamiquement
        title="Nanexa announces quarterly results",
        url="https://nanexa.com/news/quarterly-results-2026",
        published_at=datetime.now().isoformat(),
        ingested_at=datetime.now().isoformat(),
        content="The company reported strong financial performance this quarter.",
        content_length=65,
        language="en",
        content_hash="test_hash_123",
        ingestion_profile_used="html_generic"
    )
    
    # 7. Tester le filtre LAI spécifiquement
    print("\nTest Filtre LAI:")
    lai_passed, lai_details = filter_engine._apply_lai_keyword_filter(test_item, actor_type)
    
    print(f"   Item Title: {test_item.title}")
    print(f"   Actor Type: {actor_type}")
    print(f"   LAI Filter Passed: {lai_passed}")
    print(f"   LAI Filter Required: {lai_details.get('required', 'N/A')}")
    print(f"   Failure Reason: {lai_details.get('failure_reason', 'None')}")
    
    # 8. Test complet avec tous les filtres
    print("\nTest Filtrage Complet:")
    filter_result = filter_engine._apply_all_filters(test_item, actor_type)
    
    print(f"   Passed All Filters: {filter_result.passed_all_filters}")
    print(f"   Period Filter: {filter_result.period_filter.get('passed', 'N/A')}")
    print(f"   Exclusion Filter: {filter_result.exclusion_filter.get('passed', 'N/A')}")
    print(f"   LAI Filter: {filter_result.lai_keyword_filter.get('passed', 'N/A')}")
    
    # 9. Validation des critères de succès
    print("\nCriteres de Succes:")
    success_criteria = []
    
    # Critère 1: Actor type doit être pure_lai
    if actor_type == "pure_lai":
        success_criteria.append("OK Nanexa resolu comme pure_lai")
    else:
        success_criteria.append(f"ERREUR Nanexa resolu comme {actor_type} au lieu de pure_lai")
    
    # Critère 2: LAI filter ne doit pas être requis
    if not lai_details.get('required', True):
        success_criteria.append("OK LAI keywords non requis pour pure_lai")
    else:
        success_criteria.append("ERREUR LAI keywords encore requis pour pure_lai")
    
    # Critère 3: LAI filter doit passer
    if lai_passed:
        success_criteria.append("OK LAI filter passe pour pure_lai")
    else:
        success_criteria.append("ERREUR LAI filter echoue pour pure_lai")
    
    # Critère 4: Filtrage global doit passer
    if filter_result.passed_all_filters:
        success_criteria.append("OK Filtrage complet passe")
    else:
        success_criteria.append("ERREUR Filtrage complet echoue")
    
    for criterion in success_criteria:
        print(f"   {criterion}")
    
    # 10. Résultat final
    all_success = all("OK" in criterion for criterion in success_criteria)
    
    print(f"\nResultat Final: {'SUCCES' if all_success else 'ECHEC'}")
    
    if all_success:
        print("   La correction du filtrage LAI pour pure_lai fonctionne correctement!")
    else:
        print("   Des problemes subsistent avec le filtrage LAI pour pure_lai.")
    
    return all_success

if __name__ == "__main__":
    success = test_nanexa_lai_filter()
    sys.exit(0 if success else 1)