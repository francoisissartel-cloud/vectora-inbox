"""Validation correctif v3 - Analyse données S3"""
import boto3
import json
import sys
from datetime import datetime


def validate_date_extraction_v3(bucket: str, key: str):
    """
    Valide l'extraction de dates après déploiement v3
    
    Args:
        bucket: Bucket S3 (ex: vectora-inbox-data-dev)
        key: Clé S3 (ex: ingested/lai_weekly_v6/2026/01/29/items.json)
    """
    try:
        s3 = boto3.client('s3', region_name='eu-west-3')
        
        print(f"\n{'='*70}")
        print(f"VALIDATION CORRECTIF V3 - EXTRACTION DATES")
        print(f"{'='*70}\n")
        print(f"Bucket: {bucket}")
        print(f"Key: {key}\n")
        
        # Télécharger items
        response = s3.get_object(Bucket=bucket, Key=key)
        items = json.loads(response['Body'].read())
        
        print(f"Items total: {len(items)}\n")
        
        # Analyser extraction dates
        real_dates = 0
        fallback_dates = 0
        by_source = {}
        
        for item in items:
            source = item['source_key']
            published = item['published_at']
            ingested = item['ingested_at'][:10]
            
            # Initialiser stats source
            if source not in by_source:
                by_source[source] = {'total': 0, 'real': 0, 'fallback': 0}
            
            by_source[source]['total'] += 1
            
            # Vérifier si date réelle ou fallback
            if published == ingested:
                fallback_dates += 1
                by_source[source]['fallback'] += 1
            else:
                real_dates += 1
                by_source[source]['real'] += 1
        
        # Afficher résultats globaux
        print(f"{'='*70}")
        print(f"RESULTATS GLOBAUX")
        print(f"{'='*70}\n")
        print(f"Vraies dates extraites: {real_dates}/{len(items)} ({real_dates*100//len(items)}%)")
        print(f"Dates fallback:         {fallback_dates}/{len(items)} ({fallback_dates*100//len(items)}%)\n")
        
        # Afficher par source
        print(f"{'='*70}")
        print(f"RESULTATS PAR SOURCE")
        print(f"{'='*70}\n")
        print(f"{'Source':<35} {'Real':<8} {'Fallback':<10} {'%':<5}")
        print(f"{'-'*70}")
        
        for source in sorted(by_source.keys()):
            stats = by_source[source]
            pct = stats['real']*100//stats['total'] if stats['total'] else 0
            print(f"{source[:34]:<35} {stats['real']:<8} {stats['fallback']:<10} {pct}%")
        
        # Vérifier objectif
        print(f"\n{'='*70}")
        target_pct = 70
        success = real_dates >= len(items) * target_pct / 100
        
        if success:
            print(f"[SUCCESS] Objectif atteint: {real_dates*100//len(items)}% >= {target_pct}%")
        else:
            print(f"[FAIL] Objectif non atteint: {real_dates*100//len(items)}% < {target_pct}%")
        
        print(f"{'='*70}\n")
        
        return success
        
    except Exception as e:
        print(f"[ERROR] {e}\n")
        return False


if __name__ == "__main__":
    # Configuration par défaut
    bucket = "vectora-inbox-data-dev"
    
    # Utiliser date du jour ou argument
    if len(sys.argv) > 1:
        date_str = sys.argv[1]  # Format: 2026-01-29
    else:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    # Construire clé S3
    year, month, day = date_str.split('-')
    key = f"ingested/lai_weekly_v6/{year}/{month}/{day}/items.json"
    
    # Valider
    success = validate_date_extraction_v3(bucket, key)
    
    sys.exit(0 if success else 1)
