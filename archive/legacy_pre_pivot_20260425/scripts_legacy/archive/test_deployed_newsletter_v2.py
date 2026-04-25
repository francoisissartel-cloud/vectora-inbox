#!/usr/bin/env python3
"""
Test de la Lambda newsletter-v2 déployée
"""
import json
import boto3
import time

def test_deployed_lambda():
    """Test la Lambda déployée sur AWS"""
    
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    function_name = 'vectora-inbox-newsletter-v2'
    
    payload = {
        'client_id': 'lai_weekly_v4',
        'target_date': '2025-12-21',
        'force_regenerate': False
    }
    
    print("[*] Testing deployed Lambda newsletter-v2...")
    print(f"[+] Function: {function_name}")
    print(f"[+] Payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Attendre que la Lambda soit prête
        print("[+] Waiting for Lambda to be ready...")
        time.sleep(10)
        
        print("[+] Invoking Lambda...")
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        print(f"\n[RESPONSE]")
        print(f"Status Code: {response['StatusCode']}")
        print(f"Result: {json.dumps(result, indent=2)}")
        
        if response['StatusCode'] == 200 and result.get('statusCode') == 200:
            print(f"\n[SUCCESS] Lambda test passed!")
            
            # Afficher les métriques
            body = result.get('body', {})
            if isinstance(body, dict):
                print(f"[+] Items processed: {body.get('items_processed', 'N/A')}")
                print(f"[+] Items selected: {body.get('items_selected', 'N/A')}")
                print(f"[+] Newsletter generated: {body.get('newsletter_generated', 'N/A')}")
                
                if 'selection_metadata' in body:
                    metadata = body['selection_metadata']
                    print(f"[+] Matching efficiency: {metadata.get('matching_efficiency', 0):.2%}")
            
            return True
        else:
            print(f"\n[ERROR] Lambda test failed")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] Lambda invocation failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_deployed_lambda()
    
    if success:
        print("\n[SUCCESS] Newsletter V2 Lambda is working correctly on AWS!")
    else:
        print("\n[ERROR] Newsletter V2 Lambda test failed")