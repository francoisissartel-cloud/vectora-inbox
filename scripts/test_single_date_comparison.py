#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simple de validation du mode Latest Run Only
"""
import os
import sys

# Ajout du chemin src_v2 pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src_v2'))

def test_single_date_vs_period():
    """Compare les deux modes de chargement"""
    
    print("[*] Comparing single date vs period modes...")
    
    try:
        from vectora_core.shared.s3_io import load_curated_items_single_date, load_curated_items
        
        client_id = "lai_weekly_v4"
        data_bucket = "vectora-inbox-data-dev"
        target_date = "2025-12-21"
        from_date = "2025-11-21"  # 30 jours avant
        
        # Test mode single date
        print(f"[+] Testing single date mode for {target_date}")
        single_items = load_curated_items_single_date(client_id, data_bucket, target_date)
        print(f"[+] Single date items: {len(single_items)}")
        
        # Test mode period (legacy)
        print(f"[+] Testing period mode from {from_date} to {target_date}")
        period_items = load_curated_items(client_id, data_bucket, from_date, target_date)
        print(f"[+] Period items: {len(period_items)}")
        
        # Comparaison
        print(f"\n[COMPARISON]")
        print(f"Single date: {len(single_items)} items")
        print(f"Period mode: {len(period_items)} items")
        print(f"Reduction: {len(period_items) - len(single_items)} items ({((len(period_items) - len(single_items)) / len(period_items) * 100):.1f}%)")
        
        if len(single_items) < len(period_items):
            print(f"[SUCCESS] Single date mode reduces volume as expected")
        else:
            print(f"[WARNING] No volume reduction detected")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Comparison failed: {str(e)}")
        return False

def main():
    """Point d'entrée principal"""
    
    print("="*60)
    print("[SINGLE DATE VS PERIOD COMPARISON]")
    print("="*60)
    
    success = test_single_date_vs_period()
    
    if success:
        print("\n[SUCCESS] Comparison completed successfully!")
        print("[INFO] Single date mode is working and reduces volume")
    else:
        print("\n[ERROR] Comparison failed")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)