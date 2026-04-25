"""
Test de l'ingestion lai_weekly_v6 avec correctif parsing dates
"""
import boto3
import json
from datetime import datetime

def invoke_ingest_v2(client_id='lai_weekly_v6'):
    """Invoke Lambda ingest-v2 pour tester le correctif dates"""
    
    lambda_client = boto3.Session(profile_name='rag-lai-prod', region_name='eu-west-3').client('lambda')
    
    payload = {
        'client_id': client_id,
        'run_mode': 'full'
    }
    
    print(f"\n{'='*60}")
    print(f"TEST INGESTION - Correctif Parsing Dates")
    print(f"{'='*60}")
    print(f"\nClient: {client_id}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"\nInvocation Lambda ingest-v2...")
    
    response = lambda_client.invoke(
        FunctionName='vectora-inbox-ingest-v2-dev',
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    
    result = json.loads(response['Payload'].read())
    
    print(f"\nStatut: {response['StatusCode']}")
    
    if response['StatusCode'] == 200:
        print(f"\n[OK] Ingestion reussie")
        
        if 'body' in result:
            body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
            
            print(f"\nResultats:")
            print(f"  - Sources traitees: {body.get('sources_processed', 0)}")
            print(f"  - Items ingeres: {body.get('total_items', 0)}")
            
            if 'output_path' in body:
                print(f"  - Fichier S3: {body['output_path']}")
        
        return result
    else:
        print(f"\n[ERREUR] Ingestion echouee")
        print(f"Reponse: {json.dumps(result, indent=2)}")
        return None


if __name__ == '__main__':
    result = invoke_ingest_v2('lai_weekly_v6')
    
    if result:
        print(f"\n{'='*60}")
        print("PROCHAINE ETAPE: Analyser les dates extraites")
        print(f"{'='*60}")
        print("\nCommande pour telecharger le fichier:")
        print("aws s3 cp s3://vectora-inbox-data-dev/ingested/lai_weekly_v6/[DATE]/items.json . --profile rag-lai-prod")
        print("\nVerifier les champs 'published_at' dans items.json")
