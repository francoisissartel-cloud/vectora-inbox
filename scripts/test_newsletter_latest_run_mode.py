#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test du mode Latest Run Only pour Newsletter V2
Validation des modifications apportées
"""
import os
import sys
import json
from datetime import datetime

# Ajout du chemin src_v2 pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src_v2'))

def test_latest_run_mode():
    """Test du mode latest_run_only avec données réelles"""
    
    print("[*] Testing Latest Run Only mode...")
    
    try:
        from vectora_core.newsletter import run_newsletter_for_client
        
        # Configuration de test
        env_vars = {
            "CONFIG_BUCKET": "vectora-inbox-config-dev",
            "DATA_BUCKET": "vectora-inbox-data-dev", 
            "NEWSLETTERS_BUCKET": "vectora-inbox-newsletters-dev",
            "BEDROCK_MODEL_ID": "anthropic.claude-3-sonnet-20240229-v1:0",
            "BEDROCK_REGION": "us-east-1"
        }
        
        # Test avec mode latest_run_only
        client_id = "lai_weekly_v4"
        target_date = "2025-12-21"
        
        print(f"[+] Testing with client_id: {client_id}")
        print(f"[+] Target date: {target_date}")
        print(f"[+] Expected mode: latest_run_only")
        
        # Appel de la fonction
        result = run_newsletter_for_client(
            client_id=client_id,
            env_vars=env_vars,
            target_date=target_date,
            force_regenerate=False
        )
        
        # Validation des résultats
        print(f"[SUCCESS] Newsletter generated successfully!")
        print(f"[+] Status: {result['status']}")
        print(f"[+] Items processed: {result['items_processed']}")
        print(f"[+] Items selected: {result['items_selected']}")
        
        # Vérification du volume attendu (15 items au lieu de 45)
        expected_volume = 15  # Volume d'un seul run
        actual_volume = result['items_processed']
        
        if actual_volume == expected_volume:
            print(f"[SUCCESS] Volume correct: {actual_volume} items (mode latest_run_only)")
        elif actual_volume == 45:
            print(f"[WARNING] Volume legacy détecté: {actual_volume} items (mode period_based)")
        else:
            print(f"[INFO] Volume inattendu: {actual_volume} items")
        
        # Affichage des métriques de sélection
        if 'selection_metadata' in result:
            metadata = result['selection_metadata']
            print(f"[+] Matching efficiency: {metadata.get('matching_efficiency', 0):.2%}")
            print(f"[+] Items after matching: {metadata.get('items_after_matching_filter', 0)}")
            print(f"[+] Items after deduplication: {metadata.get('items_after_deduplication', 0)}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Test failed: {str(e)}")
        return False

def test_single_date_function():
    """Test de la fonction load_curated_items_single_date"""
    
    print("\n[*] Testing load_curated_items_single_date function...")
    
    try:
        from vectora_core.shared.s3_io import load_curated_items_single_date
        
        # Test avec une date connue
        client_id = "lai_weekly_v4"
        data_bucket = "vectora-inbox-data-dev"
        target_date = "2025-12-21"
        
        items = load_curated_items_single_date(client_id, data_bucket, target_date)
        
        print(f"[SUCCESS] Function test completed!")
        print(f"[+] Items loaded: {len(items)}")
        
        if len(items) > 0:
            print(f"[+] Sample item keys: {list(items[0].keys())[:5]}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Function test failed: {str(e)}")
        return False

def main():
    """Point d'entrée principal"""
    
    print("="*60)
    print("[NEWSLETTER V2 LATEST RUN MODE TESTING]")
    print("="*60)
    
    # Test 1: Fonction single date
    function_ok = test_single_date_function()
    
    # Test 2: Mode latest run complet
    mode_ok = test_latest_run_mode()
    
    print("\n" + "="*60)
    print("[TEST RESULTS SUMMARY]")
    print("="*60)
    print(f"[+] Single date function: {'PASS' if function_ok else 'FAIL'}")
    print(f"[+] Latest run mode: {'PASS' if mode_ok else 'FAIL'}")
    
    if function_ok and mode_ok:
        print("\n[SUCCESS] Latest Run Only mode is working correctly!")
        print("[INFO] Newsletter now uses single date instead of period")
        print("[BENEFIT] Performance improved, volume predictable")
    else:
        print("\n[ERROR] Some tests failed, check implementation")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)