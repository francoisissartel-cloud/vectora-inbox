#!/usr/bin/env python3
"""
Test simple de la migration Bedrock vers us-east-1.
"""

import os
import sys
import json
import time
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from vectora_core.normalization.bedrock_client import normalize_item_with_bedrock

def test_bedrock_migration():
    """Test de migration Bedrock vers us-east-1."""
    
    print("Test Migration Bedrock vers us-east-1")
    print("=" * 50)
    
    # Configuration des variables d'environnement
    os.environ['BEDROCK_REGION'] = 'us-east-1'
    os.environ['BEDROCK_MODEL_ID'] = 'us.anthropic.claude-sonnet-4-5-20250929-v1:0'
    
    print(f"BEDROCK_REGION: {os.environ['BEDROCK_REGION']}")
    print(f"BEDROCK_MODEL_ID: {os.environ['BEDROCK_MODEL_ID']}")
    print()
    
    # Test: Normalisation d'un item
    print("Test: Normalisation Bedrock")
    print("-" * 30)
    
    test_item = """
    UZEDY (olanzapine) Extended-Release Injectable Suspension Receives FDA Approval
    
    Nanexa AB and Moderna Therapeutics announce FDA approval of UZEDY, a novel 
    long-acting injectable formulation of olanzapine for the treatment of schizophrenia 
    and bipolar I disorder. The PharmaShell technology enables once-monthly dosing.
    """
    
    canonical_examples = {
        'companies': ['Nanexa', 'Moderna Therapeutics', 'Pfizer', 'Novartis'],
        'molecules': ['olanzapine', 'risperidone', 'aripiprazole'],
        'technologies': ['Extended-Release Injectable', 'PharmaShell', 'LAI', 'microspheres']
    }
    
    try:
        start_time = time.time()
        result = normalize_item_with_bedrock(
            item_text=test_item,
            model_id=os.environ['BEDROCK_MODEL_ID'],
            canonical_examples=canonical_examples
        )
        end_time = time.time()
        
        print(f"Latence: {end_time - start_time:.2f}s")
        print(f"Resume: {result.get('summary', 'N/A')[:100]}...")
        print(f"Companies: {result.get('companies_detected', [])}")
        print(f"Molecules: {result.get('molecules_detected', [])}")
        print(f"Technologies: {result.get('technologies_detected', [])}")
        print("Test normalisation: SUCCES")
        
        return True
        
    except Exception as e:
        print(f"Test normalisation: ECHEC - {e}")
        return False

def compare_regions():
    """Compare les performances eu-west-3 vs us-east-1."""
    
    print("\nComparaison Regions: eu-west-3 vs us-east-1")
    print("=" * 50)
    
    test_item = "Pfizer announces positive Phase III results for their new LAI formulation."
    canonical_examples = {
        'companies': ['Pfizer', 'Novartis'],
        'molecules': ['olanzapine'],
        'technologies': ['LAI', 'Extended-Release Injectable']
    }
    
    regions_to_test = [
        ('eu-west-3', 'eu.anthropic.claude-sonnet-4-5-20250929-v1:0'),
        ('us-east-1', 'us.anthropic.claude-sonnet-4-5-20250929-v1:0')
    ]
    
    results = {}
    
    for region, model_id in regions_to_test:
        print(f"\nTest region: {region}")
        print(f"Modele: {model_id}")
        
        os.environ['BEDROCK_REGION'] = region
        os.environ['BEDROCK_MODEL_ID'] = model_id
        
        try:
            start_time = time.time()
            result = normalize_item_with_bedrock(
                item_text=test_item,
                model_id=model_id,
                canonical_examples=canonical_examples
            )
            end_time = time.time()
            
            latency = end_time - start_time
            results[region] = {
                'latency': latency,
                'success': True,
                'summary_length': len(result.get('summary', '')),
                'companies_count': len(result.get('companies_detected', [])),
                'molecules_count': len(result.get('molecules_detected', [])),
                'technologies_count': len(result.get('technologies_detected', []))
            }
            
            print(f"Latence: {latency:.2f}s")
            print(f"Resume: {len(result.get('summary', ''))} chars")
            print(f"Companies: {len(result.get('companies_detected', []))}")
            print("Succes")
            
        except Exception as e:
            results[region] = {
                'latency': None,
                'success': False,
                'error': str(e)
            }
            print(f"Echec: {e}")
    
    # Comparaison finale
    print("\nComparaison Finale")
    print("-" * 30)
    
    if results['eu-west-3']['success'] and results['us-east-1']['success']:
        eu_latency = results['eu-west-3']['latency']
        us_latency = results['us-east-1']['latency']
        
        print(f"Latence eu-west-3: {eu_latency:.2f}s")
        print(f"Latence us-east-1: {us_latency:.2f}s")
        
        if us_latency < eu_latency:
            improvement = ((eu_latency - us_latency) / eu_latency) * 100
            print(f"us-east-1 plus rapide de {improvement:.1f}%")
        else:
            degradation = ((us_latency - eu_latency) / eu_latency) * 100
            print(f"us-east-1 plus lent de {degradation:.1f}%")
    
    return results

if __name__ == "__main__":
    # Test de base
    success = test_bedrock_migration()
    
    if success:
        # Comparaison régions
        comparison_results = compare_regions()
        
        # Sauvegarde des résultats
        results_file = "bedrock_migration_test_results.json"
        with open(results_file, 'w') as f:
            json.dump(comparison_results, f, indent=2)
        
        print(f"\nResultats sauvegardes dans: {results_file}")
    
    print("\nTest termine")