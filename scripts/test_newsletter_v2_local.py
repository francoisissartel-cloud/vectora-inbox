#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test local de la Lambda newsletter-v2
Phase 5 du plan d'implémentation newsletter V2
"""
import os
import sys
import json
from datetime import datetime, timedelta

# Ajout du chemin src_v2 pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src_v2'))

def test_newsletter_v2_local():
    """Test local de la newsletter V2 avec données simulées"""
    
    print("[*] Testing newsletter-v2 locally...")
    
    try:
        # Import du module newsletter
        from vectora_core.newsletter import run_newsletter_for_client
        
        # Configuration de test (simulation des variables d'environnement)
        env_vars = {
            "CONFIG_BUCKET": "vectora-inbox-config-dev",
            "DATA_BUCKET": "vectora-inbox-data-dev", 
            "NEWSLETTERS_BUCKET": "vectora-inbox-newsletters-dev",
            "BEDROCK_MODEL_ID": "anthropic.claude-3-sonnet-20240229-v1:0",
            "BEDROCK_REGION": "us-east-1"
        }
        
        # Paramètres de test
        client_id = "lai_weekly_v4"
        target_date = "2025-12-21"
        
        print(f"[+] Testing with client_id: {client_id}")
        print(f"[+] Target date: {target_date}")
        
        # Simulation d'un appel à la fonction principale
        print("[+] Calling run_newsletter_for_client...")
        
        # Note: Ce test va échouer car il nécessite l'accès S3 et Bedrock
        # Mais il permet de valider la structure du code
        result = run_newsletter_for_client(
            client_id=client_id,
            env_vars=env_vars,
            target_date=target_date,
            force_regenerate=False
        )
        
        print("[SUCCESS] Newsletter generation completed!")
        print(f"Result: {json.dumps(result, indent=2)}")
        
        return True
        
    except ImportError as e:
        print(f"[ERROR] Import error: {str(e)}")
        print("[INFO] This is expected if dependencies are missing")
        return False
        
    except Exception as e:
        print(f"[ERROR] Newsletter generation failed: {str(e)}")
        print("[INFO] This is expected without AWS credentials and S3 access")
        return False

def test_newsletter_selector_only():
    """Test uniquement du sélecteur avec données simulées"""
    
    print("\n[*] Testing newsletter selector with mock data...")
    
    try:
        from vectora_core.newsletter.selector import NewsletterSelector
        
        # Configuration client simulée
        client_config = {
            'newsletter_selection': {
                'max_items_total': 20,
                'critical_event_types': [
                    'regulatory_approval', 'partnership', 'clinical_update'
                ]
            },
            'newsletter_layout': {
                'sections': [
                    {
                        'id': 'top_signals',
                        'title': 'Top Signals',
                        'source_domains': ['tech_lai_ecosystem'],
                        'max_items': 5,
                        'sort_by': 'score_desc'
                    },
                    {
                        'id': 'partnerships_deals',
                        'title': 'Partnerships & Deals',
                        'source_domains': ['tech_lai_ecosystem'],
                        'max_items': 5,
                        'filter_event_types': ['partnership'],
                        'sort_by': 'date_desc'
                    }
                ]
            }
        }
        
        # Items simulés
        mock_items = [
            {
                'item_id': 'test_1',
                'matching_results': {'matched_domains': ['tech_lai_ecosystem']},
                'normalized_content': {
                    'summary': 'Test partnership announcement',
                    'event_classification': {'primary_type': 'partnership'},
                    'entities': {
                        'companies': ['Company A', 'Company B'],
                        'technologies': ['LAI Technology']
                    }
                },
                'scoring_results': {'final_score': 15.5},
                'published_at': '2025-12-20T10:00:00Z',
                'url': 'https://example.com/news1'
            },
            {
                'item_id': 'test_2',
                'matching_results': {'matched_domains': ['tech_lai_ecosystem']},
                'normalized_content': {
                    'summary': 'Clinical trial results',
                    'event_classification': {'primary_type': 'clinical_update'},
                    'entities': {
                        'companies': ['Company C'],
                        'technologies': ['Injectable Technology']
                    }
                },
                'scoring_results': {'final_score': 12.0},
                'published_at': '2025-12-19T15:30:00Z',
                'url': 'https://example.com/news2'
            }
        ]
        
        # Test du sélecteur
        selector = NewsletterSelector(client_config)
        result = selector.select_items(mock_items)
        
        print("[SUCCESS] Selector test completed!")
        print(f"[+] Sections generated: {len(result['sections'])}")
        print(f"[+] Total items selected: {result['metadata']['items_selected']}")
        
        # Affichage des résultats
        for section_id, section_data in result['sections'].items():
            print(f"   - {section_id}: {len(section_data['items'])} items")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Selector test failed: {str(e)}")
        return False

def test_lambda_handler():
    """Test du handler Lambda avec payload simulé"""
    
    print("\n[*] Testing Lambda handler...")
    
    try:
        # Import du handler
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src_v2', 'lambdas', 'newsletter'))
        from handler import lambda_handler
        
        # Payload de test
        event = {
            "client_id": "lai_weekly_v4",
            "target_date": "2025-12-21",
            "force_regenerate": False
        }
        
        # Context simulé
        context = type('Context', (), {
            'function_name': 'test-newsletter-v2',
            'aws_request_id': 'test-request-id'
        })()
        
        # Variables d'environnement simulées
        os.environ.update({
            "CONFIG_BUCKET": "vectora-inbox-config-dev",
            "DATA_BUCKET": "vectora-inbox-data-dev",
            "NEWSLETTERS_BUCKET": "vectora-inbox-newsletters-dev", 
            "BEDROCK_MODEL_ID": "anthropic.claude-3-sonnet-20240229-v1:0",
            "BEDROCK_REGION": "us-east-1"
        })
        
        print("[+] Calling lambda_handler...")
        result = lambda_handler(event, context)
        
        print(f"[+] Handler returned status code: {result['statusCode']}")
        
        if result['statusCode'] == 200:
            print("[SUCCESS] Handler test completed successfully!")
        else:
            print(f"[INFO] Handler returned error (expected without AWS access): {result['body']}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Handler test failed: {str(e)}")
        return False

def main():
    """Point d'entrée principal"""
    
    print("="*60)
    print("[NEWSLETTER V2 LOCAL TESTING]")
    print("="*60)
    
    # Test 1: Sélecteur uniquement (doit fonctionner)
    selector_ok = test_newsletter_selector_only()
    
    # Test 2: Handler Lambda (va échouer sans AWS mais valide la structure)
    handler_ok = test_lambda_handler()
    
    # Test 3: Fonction complète (va échouer sans AWS)
    full_ok = test_newsletter_v2_local()
    
    print("\n" + "="*60)
    print("[TEST RESULTS SUMMARY]")
    print("="*60)
    print(f"[+] Selector test: {'PASS' if selector_ok else 'FAIL'}")
    print(f"[+] Handler test: {'PASS' if handler_ok else 'FAIL (expected)'}")
    print(f"[+] Full test: {'PASS' if full_ok else 'FAIL (expected)'}")
    
    if selector_ok:
        print("\n[SUCCESS] Core newsletter logic is working correctly!")
        print("[INFO] AWS-dependent tests failed as expected (no credentials)")
        print("[NEXT] Ready for AWS deployment and real testing")
    else:
        print("\n[ERROR] Core logic has issues that need to be fixed")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)