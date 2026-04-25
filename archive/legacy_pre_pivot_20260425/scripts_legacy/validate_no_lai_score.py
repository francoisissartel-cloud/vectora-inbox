#!/usr/bin/env python3
"""
Script de validation: Vérifier l'absence de lai_relevance_score dans items.json
"""
import json
import sys
import boto3

def validate_items_json(bucket, key):
    """Télécharge et valide items.json depuis S3"""
    s3 = boto3.client('s3', region_name='eu-west-3')
    
    try:
        # Télécharger le fichier
        response = s3.get_object(Bucket=bucket, Key=key)
        items = json.loads(response['Body'].read().decode('utf-8'))
        
        print(f"✅ Fichier téléchargé: {len(items)} items")
        
        # Vérifier chaque item
        errors = []
        for i, item in enumerate(items):
            normalized_content = item.get('normalized_content', {})
            
            if 'lai_relevance_score' in normalized_content:
                errors.append(f"Item {i} ({item.get('item_id', 'unknown')}): lai_relevance_score={normalized_content['lai_relevance_score']}")
        
        # Résultats
        if errors:
            print(f"\n❌ ÉCHEC: {len(errors)} items contiennent lai_relevance_score:")
            for error in errors[:10]:  # Afficher max 10 erreurs
                print(f"  - {error}")
            return False
        else:
            print("\n✅ SUCCÈS: Aucun item ne contient lai_relevance_score")
            print(f"   Tous les {len(items)} items sont conformes")
            return True
            
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return False

if __name__ == "__main__":
    bucket = "vectora-inbox-data-dev"
    key = "clients/lai_weekly_v7/items.json"
    
    print(f"Validation de s3://{bucket}/{key}")
    success = validate_items_json(bucket, key)
    sys.exit(0 if success else 1)
