#!/usr/bin/env python3
"""
Script de publication de métriques de qualité CloudWatch
Surveille l'efficacité des corrections déployées
"""
import boto3
import json
from datetime import datetime, timedelta
from typing import Dict, Any

def publish_quality_metrics(client_id: str, profile: str = 'rag-lai-prod'):
    """Publie les métriques de qualité dans CloudWatch"""
    
    session = boto3.Session(profile_name=profile)
    s3 = session.client('s3')
    cloudwatch = session.client('cloudwatch')
    
    # Date du jour
    today = datetime.now()
    date_path = today.strftime('%Y/%m/%d')
    
    metrics = []
    
    # 1. Métrique: Taux d'extraction de dates réelles
    try:
        response = s3.get_object(
            Bucket='vectora-inbox-data-dev',
            Key=f'ingested/{client_id}/{date_path}/items.json'
        )
        items = json.loads(response['Body'].read())
        
        total_items = len(items)
        real_dates = 0
        
        for item in items:
            published_at = item.get('published_at', '')[:10]
            ingested_at = item.get('ingested_at', '')[:10]
            if published_at != ingested_at:
                real_dates += 1
        
        real_dates_pct = (real_dates / total_items * 100) if total_items > 0 else 0
        fallback_pct = 100 - real_dates_pct
        
        metrics.append({
            'MetricName': 'RealDatesRate',
            'Value': real_dates_pct,
            'Unit': 'Percent',
            'Timestamp': today
        })
        
        metrics.append({
            'MetricName': 'DatesFallbackRate',
            'Value': fallback_pct,
            'Unit': 'Percent',
            'Timestamp': today
        })
        
        print(f"[OK] Dates reelles: {real_dates_pct:.1f}% ({real_dates}/{total_items})")
        
    except Exception as e:
        print(f"[WARN] Erreur metrique dates: {e}")
    
    # 2. Métrique: Word count moyen
    try:
        avg_word_count = sum(len(item.get('content', '').split()) for item in items) / len(items)
        
        metrics.append({
            'MetricName': 'AvgWordCount',
            'Value': avg_word_count,
            'Unit': 'Count',
            'Timestamp': today
        })
        
        print(f"[OK] Word count moyen: {avg_word_count:.1f} mots")
        
    except Exception as e:
        print(f"[WARN] Erreur metrique word count: {e}")
    
    # 3. Métrique: Taux d'enrichissement de contenu
    try:
        enriched_items = sum(1 for item in items if len(item.get('content', '').split()) > 50)
        enrichment_rate = (enriched_items / total_items * 100) if total_items > 0 else 0
        
        metrics.append({
            'MetricName': 'ContentEnrichmentRate',
            'Value': enrichment_rate,
            'Unit': 'Percent',
            'Timestamp': today
        })
        
        print(f"[OK] Taux d'enrichissement: {enrichment_rate:.1f}%")
        
    except Exception as e:
        print(f"[WARN] Erreur metrique enrichissement: {e}")
    
    # 4. Métrique: Hallucinations détectées (données curées)
    try:
        response = s3.get_object(
            Bucket='vectora-inbox-data-dev',
            Key=f'curated/{client_id}/{date_path}/items.json'
        )
        curated_items = json.loads(response['Body'].read())
        
        total_hallucinations = 0
        items_analyzed = 0
        
        for item in curated_items:
            content = item.get('content', '').lower()
            entities = item.get('normalized_content', {}).get('entities', {})
            
            for category, entity_list in entities.items():
                if isinstance(entity_list, list):
                    for entity in entity_list:
                        if isinstance(entity, str) and len(entity) > 3:
                            if entity.lower() not in content:
                                total_hallucinations += 1
            
            items_analyzed += 1
        
        avg_hallucinations = total_hallucinations / items_analyzed if items_analyzed > 0 else 0
        
        metrics.append({
            'MetricName': 'AvgHallucinationsPerItem',
            'Value': avg_hallucinations,
            'Unit': 'Count',
            'Timestamp': today
        })
        
        print(f"[OK] Hallucinations moyennes: {avg_hallucinations:.2f} par item")
        
    except Exception as e:
        print(f"[WARN] Erreur metrique hallucinations: {e}")
    
    # 5. Métrique: Distribution newsletter
    try:
        response = s3.get_object(
            Bucket='vectora-inbox-newsletters-dev',
            Key=f'{client_id}/{date_path}/newsletter.json'
        )
        newsletter = json.loads(response['Body'].read())
        
        sections = newsletter.get('sections', [])
        filled_sections = sum(1 for s in sections if len(s.get('items', [])) > 0)
        total_sections = len(sections)
        
        distribution_rate = (filled_sections / total_sections * 100) if total_sections > 0 else 0
        
        metrics.append({
            'MetricName': 'NewsletterSectionsFilled',
            'Value': filled_sections,
            'Unit': 'Count',
            'Timestamp': today
        })
        
        metrics.append({
            'MetricName': 'NewsletterDistributionRate',
            'Value': distribution_rate,
            'Unit': 'Percent',
            'Timestamp': today
        })
        
        print(f"[OK] Sections remplies: {filled_sections}/{total_sections} ({distribution_rate:.1f}%)")
        
    except Exception as e:
        print(f"[WARN] Erreur metrique newsletter: {e}")
    
    # Publication des métriques dans CloudWatch
    if metrics:
        try:
            cloudwatch.put_metric_data(
                Namespace='VectoraInbox/Quality',
                MetricData=[{
                    **metric,
                    'Dimensions': [
                        {'Name': 'ClientId', 'Value': client_id},
                        {'Name': 'Environment', 'Value': 'dev'}
                    ]
                } for metric in metrics]
            )
            print(f"\n[OK] {len(metrics)} metriques publiees dans CloudWatch")
            return True
        except Exception as e:
            print(f"\n[ERROR] Erreur publication CloudWatch: {e}")
            return False
    else:
        print("\n[WARN] Aucune metrique a publier")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python publish_quality_metrics.py <client_id> [profile]")
        sys.exit(1)
    
    client_id = sys.argv[1]
    profile = sys.argv[2] if len(sys.argv) > 2 else 'rag-lai-prod'
    
    success = publish_quality_metrics(client_id, profile)
    sys.exit(0 if success else 1)
