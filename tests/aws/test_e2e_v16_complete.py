#!/usr/bin/env python3
"""
Test E2E AWS Complet V16 - Pipeline Complet avec Tracabilite Detaillee

Invoque le pipeline complet sur AWS:
1. Ingest (Lambda ingest-v2)
2. Normalize + Score (Lambda normalize-score-v2)
3. Analyse detaillee item par item
"""

import sys
import json
import boto3
import time
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src_v2"))

def invoke_lambda(function_name, payload, region='eu-west-3', profile='rag-lai-prod'):
    """Invoque une Lambda AWS"""
    session = boto3.Session(profile_name=profile)
    lambda_client = session.client('lambda', region_name=region)
    
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    
    result = json.loads(response['Payload'].read())
    return result

def download_s3_file(bucket, key, region='eu-west-3', profile='rag-lai-prod'):
    """Telecharge un fichier depuis S3"""
    session = boto3.Session(profile_name=profile)
    s3_client = session.client('s3', region_name=region)
    
    response = s3_client.get_object(Bucket=bucket, Key=key)
    content = response['Body'].read().decode('utf-8')
    return json.loads(content)

def run_e2e_pipeline_v16():
    """Execute pipeline E2E complet pour V16"""
    print("="*80)
    print("TEST E2E AWS COMPLET V16 - PIPELINE COMPLET")
    print("="*80)
    print("Client: lai_weekly_v16")
    print("Env: dev")
    print("")
    
    client_id = 'lai_weekly_v16'
    config_bucket = 'vectora-inbox-config-dev'
    data_bucket = 'vectora-inbox-data-dev'
    
    # ETAPE 1: INGESTION
    print("\n" + "="*80)
    print("ETAPE 1/3: INGESTION")
    print("="*80)
    
    ingest_payload = {
        'client_id': client_id,
        'period_days': 7,
        'ingestion_mode': 'balanced'
    }
    
    print(f"Invocation Lambda ingest-v2-dev...")
    ingest_result = invoke_lambda('vectora-inbox-ingest-v2-dev', ingest_payload)
    
    print(f"[OK] Ingestion terminee")
    print(f"   Status: {ingest_result.get('status')}")
    print(f"   Items ingeres: {ingest_result.get('items_final', 0)}")
    print(f"   Sources: {ingest_result.get('sources_processed', 0)}")
    print(f"   Temps: {ingest_result.get('execution_time_seconds', 0):.1f}s")
    
    if ingest_result.get('items_final', 0) == 0:
        print("[ERROR] Aucun item ingere - Arret du test")
        return False
    
    # Attendre un peu
    time.sleep(2)
    
    # ETAPE 2: NORMALIZE + SCORE
    print("\n" + "="*80)
    print("ETAPE 2/3: NORMALIZE + SCORE")
    print("="*80)
    
    normalize_payload = {
        'client_id': client_id,
        'enable_domain_scoring': True
    }
    
    print(f"Invocation Lambda normalize-score-v2-dev...")
    normalize_result = invoke_lambda('vectora-inbox-normalize-score-v2-dev', normalize_payload)
    
    print(f"[OK] Normalisation terminee")
    print(f"   Status: {normalize_result.get('status')}")
    print(f"   Items normalises: {normalize_result.get('items_normalized', 0)}")
    print(f"   Items relevant: {normalize_result.get('items_relevant', 0)}")
    print(f"   Temps: {normalize_result.get('execution_time_seconds', 0):.1f}s")
    
    # ETAPE 3: ANALYSE DETAILLEE
    print("\n" + "="*80)
    print("ETAPE 3/3: ANALYSE DETAILLEE")
    print("="*80)
    
    # Telecharger items normalises
    current_date = datetime.now().strftime('%Y/%m/%d')
    items_key = f"normalized/{client_id}/{current_date}/items.json"
    
    print(f"Telechargement items depuis S3...")
    print(f"   Bucket: {data_bucket}")
    print(f"   Key: {items_key}")
    
    try:
        items = download_s3_file(data_bucket, items_key)
        print(f"[OK] {len(items)} items telecharges")
    except Exception as e:
        print(f"[ERROR] Echec telechargement: {e}")
        return False
    
    # Analyse item par item
    print("\n" + "-"*80)
    print("ANALYSE ITEM PAR ITEM")
    print("-"*80)
    
    for i, item in enumerate(items, 1):
        ds = item.get('domain_scoring', {})
        entities = item.get('normalized_content', {}).get('entities', {})
        
        status = "[OK]" if ds.get('is_relevant') else "[NO]"
        print(f"\n{status} Item {i}/{len(items)}: {item.get('title', '')[:70]}...")
        print(f"   Source: {item.get('source_key')}")
        print(f"   Event: {item.get('normalized_content', {}).get('event_classification', {}).get('primary_type')}")
        print(f"   Score: {ds.get('score', 0)}/100 (confidence: {ds.get('confidence', 'N/A')})")
        print(f"   Entities:")
        print(f"      Companies: {entities.get('companies', [])}")
        print(f"      Technologies: {entities.get('technologies', [])}")
        print(f"      Dosing: {entities.get('dosing_intervals', [])}")
        print(f"      Trademarks: {entities.get('trademarks', [])}")
        
        signals = ds.get('signals_detected', {})
        print(f"   Signals: {len(signals.get('strong', []))} strong, {len(signals.get('medium', []))} medium")
        print(f"   Reasoning: {ds.get('reasoning', '')[:100]}...")
    
    # Statistiques
    print("\n" + "="*80)
    print("STATISTIQUES GLOBALES")
    print("="*80)
    
    total = len(items)
    relevant = sum(1 for i in items if i.get('domain_scoring', {}).get('is_relevant'))
    relevant_pct = (relevant / total * 100) if total > 0 else 0
    avg_score = sum(i.get('domain_scoring', {}).get('score', 0) for i in items) / total if total > 0 else 0
    
    companies_count = sum(1 for i in items if i.get('normalized_content', {}).get('entities', {}).get('companies'))
    tech_count = sum(1 for i in items if i.get('normalized_content', {}).get('entities', {}).get('technologies'))
    dosing_count = sum(1 for i in items if i.get('normalized_content', {}).get('entities', {}).get('dosing_intervals'))
    
    print(f"Total items: {total}")
    print(f"Items relevant: {relevant} ({relevant_pct:.1f}%)")
    print(f"Score moyen: {avg_score:.1f}/100")
    print(f"Companies detectees: {companies_count} items")
    print(f"Technologies detectees: {tech_count} items")
    print(f"Dosing intervals detectes: {dosing_count} items")
    
    # Sauvegarder
    output_dir = project_root / ".tmp" / "e2e_v16_aws"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "items.json", 'w', encoding='utf-8') as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    
    with open(output_dir / "summary.json", 'w', encoding='utf-8') as f:
        json.dump({
            'test_date': datetime.now().isoformat(),
            'client_id': client_id,
            'total_items': total,
            'items_relevant': relevant,
            'relevant_rate': relevant_pct,
            'avg_score': avg_score,
            'companies_detected': companies_count,
            'technologies_detected': tech_count,
            'dosing_detected': dosing_count,
            'ingest_result': ingest_result,
            'normalize_result': normalize_result
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n[OK] Resultats sauvegardes: {output_dir}")
    
    # Verdict
    print("\n" + "="*80)
    print("VERDICT")
    print("="*80)
    
    if relevant_pct >= 54.0:
        print(f"[OK] Taux pertinence: {relevant_pct:.1f}% >= 54%")
        print("[OK] QUALITE VALIDEE - V16 OPERATIONNEL SUR AWS")
        return True
    else:
        print(f"[WARN] Taux pertinence: {relevant_pct:.1f}% < 54%")
        return False

if __name__ == "__main__":
    success = run_e2e_pipeline_v16()
    sys.exit(0 if success else 1)
