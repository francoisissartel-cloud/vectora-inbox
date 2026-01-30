"""
Test extraction dates avec vraies données S3
Phase 3 - Plan correctif v2 parsing dates
"""
import boto3
import json
from datetime import datetime

def test_real_date_extraction():
    """Télécharge items réels et vérifie extraction dates"""
    
    s3 = boto3.client('s3', region_name='eu-west-3')
    
    # Télécharger items ingérés récents
    date_str = datetime.now().strftime('%Y/%m/%d')
    key = f'ingested/lai_weekly_v6/{date_str}/items.json'
    
    print(f"\n{'='*70}")
    print(f"TEST EXTRACTION DATES RÉELLES")
    print(f"{'='*70}\n")
    print(f"Téléchargement: s3://vectora-inbox-data-dev/{key}")
    
    try:
        response = s3.get_object(
            Bucket='vectora-inbox-data-dev',
            Key=key
        )
        items = json.loads(response['Body'].read())
    except Exception as e:
        print(f"[ERREUR] Erreur telechargement: {e}")
        return False
    
    print(f"[OK] {len(items)} items telecharges\n")
    
    # Analyser les dates
    fallback_count = 0
    real_date_count = 0
    date_sources = {}
    
    for item in items:
        published_at = item.get('published_at')
        ingested_at = item.get('ingested_at', '')[:10]
        
        # Compter les sources de dates si disponible
        metadata = item.get('metadata', {})
        date_source = metadata.get('date_source', 'unknown')
        date_sources[date_source] = date_sources.get(date_source, 0) + 1
        
        if published_at == ingested_at:
            fallback_count += 1
        else:
            real_date_count += 1
            print(f"  [OK] {item['title'][:60]}...")
            print(f"     Date: {published_at} | Source: {item['source_key']}")
    
    print(f"\n{'='*70}")
    print(f"RESULTATS")
    print(f"{'='*70}\n")
    print(f"Total items:      {len(items)}")
    print(f"Vraies dates:     {real_date_count} ({real_date_count*100//len(items) if items else 0}%)")
    print(f"Dates fallback:   {fallback_count} ({fallback_count*100//len(items) if items else 0}%)")
    
    if date_sources:
        print(f"\nSources de dates:")
        for source, count in sorted(date_sources.items(), key=lambda x: -x[1]):
            print(f"  - {source}: {count}")
    
    # Objectif: >70% vraies dates
    success = real_date_count > len(items) * 0.7 if items else False
    
    print(f"\n{'='*70}")
    if success:
        print(f"[SUCCES] TEST REUSSI: {real_date_count}/{len(items)} vraies dates extraites (>70%)")
    else:
        print(f"[ECHEC] TEST ECHOUE: Seulement {real_date_count}/{len(items)} vraies dates (<70%)")
    print(f"{'='*70}\n")
    
    return success

if __name__ == '__main__':
    success = test_real_date_extraction()
    exit(0 if success else 1)
