#!/usr/bin/env python3
"""
Script pour ajouter les layers nécessaires à la Lambda newsletter-v2
"""
import boto3
from botocore.exceptions import ClientError

def list_available_layers():
    """Liste les layers disponibles"""
    
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    try:
        response = lambda_client.list_layers()
        
        print("[AVAILABLE LAYERS]")
        for layer in response['Layers']:
            layer_name = layer['LayerName']
            latest_version = layer['LatestMatchingVersion']['Version']
            layer_arn = layer['LatestMatchingVersion']['LayerVersionArn']
            
            if 'vectora' in layer_name.lower() or 'common' in layer_name.lower():
                print(f"  - {layer_name}")
                print(f"    Version: {latest_version}")
                print(f"    ARN: {layer_arn}")
                print()
        
        return response['Layers']
        
    except ClientError as e:
        print(f"[ERROR] Failed to list layers: {e}")
        return []

def add_layers_to_lambda():
    """Ajoute les layers nécessaires à la Lambda"""
    
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    function_name = 'vectora-inbox-newsletter-v2'
    
    # ARNs des layers (à ajuster selon les layers disponibles)
    layer_arns = [
        # Layer common-deps pour PyYAML, requests, etc.
        'arn:aws:lambda:us-east-1:786469175371:layer:vectora-common-deps:1'
    ]
    
    try:
        print(f"[+] Adding layers to {function_name}...")
        
        response = lambda_client.update_function_configuration(
            FunctionName=function_name,
            Layers=layer_arns
        )
        
        print(f"[SUCCESS] Layers added successfully")
        print(f"[+] Layers: {layer_arns}")
        
        return True
        
    except ClientError as e:
        print(f"[ERROR] Failed to add layers: {e}")
        return False

def main():
    """Point d'entrée principal"""
    
    print("="*60)
    print("[LAMBDA LAYERS MANAGEMENT]")
    print("="*60)
    
    # Lister les layers disponibles
    print("\n[STEP 1] Listing available layers...")
    layers = list_available_layers()
    
    # Ajouter les layers à la Lambda
    print("\n[STEP 2] Adding layers to Lambda...")
    success = add_layers_to_lambda()
    
    if success:
        print("\n[SUCCESS] Layers configuration completed")
        print("[INFO] Lambda should now have access to PyYAML and other dependencies")
    else:
        print("\n[ERROR] Failed to configure layers")
    
    return success

if __name__ == "__main__":
    main()