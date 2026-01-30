"""
Validation complète du correctif dates
Phase 3 - Plan correctif v2 parsing dates
"""
import boto3
import json
from datetime import datetime, timedelta

def validate_date_fix():
    """Valide que le correctif fonctionne"""
    
    s3 = boto3.client('s3', region_name='eu-west-3')
    
    print(f"\n{'='*70}")
    print(f"VALIDATION CORRECTIF PARSING DATES")
    print(f"{'='*70}\n")
    
    # Télécharger items
    date_str = datetime.now().strftime('%Y/%m/%d')
    key = f'ingested/lai_weekly_v6/{date_str}/items.json'
    
    print(f"Source: s3://vectora-inbox-data-dev/{key}\n")
    
    try:
        response = s3.get_object(
            Bucket='vectora-inbox-data-dev',
            Key=key
        )
        items = json.loads(response['Body'].read())
    except Exception as e:
        print(f"[ERREUR] Erreur: {e}\n")
        return False
    
    # Métriques extraction
    fallback = sum(1 for i in items if i.get('published_at') == i.get('ingested_at', '')[:10])
    real_dates = len(items) - fallback
    
    print(f"[EXTRACTION DATES]")
    print(f"{'-'*70}")
    print(f"Total items:        {len(items)}")
    print(f"Vraies dates:       {real_dates} ({real_dates*100//len(items) if items else 0}%)")
    print(f"Dates fallback:     {fallback} ({fallback*100//len(items) if items else 0}%)")
    
    extraction_ok = real_dates > len(items)*0.7
    print(f"Statut:             {'[OK]' if extraction_ok else '[ECHEC]'}")
    
    # Métriques filtre temporel
    cutoff = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    old_items = [i for i in items if i.get('published_at', '') < cutoff]
    
    print(f"\n[FILTRE TEMPOREL]")
    print(f"{'-'*70}")
    print(f"Cutoff (30j):       {cutoff}")
    print(f"Items récents:      {len(items)-len(old_items)} ({(len(items)-len(old_items))*100//len(items) if items else 0}%)")
    print(f"Items anciens:      {len(old_items)} ({len(old_items)*100//len(items) if items else 0}%)")
    
    filter_ok = len(old_items) > len(items)*0.2
    print(f"Statut:             {'[OK]' if filter_ok else '[ECHEC]'}")
    
    # Exemples dates extraites
    print(f"\n[EXEMPLES DATES EXTRAITES]")
    print(f"{'-'*70}")
    count = 0
    for item in items:
        if item.get('published_at') != item.get('ingested_at', '')[:10]:
            print(f"  {item['published_at']} | {item['source_key'][:25]:25} | {item['title'][:40]}...")
            count += 1
            if count >= 5:
                break
    
    if count == 0:
        print("  [ATTENTION] Aucune vraie date extraite")
    
    # Résultat global
    success = extraction_ok and filter_ok
    
    print(f"\n{'='*70}")
    if success:
        print(f"[SUCCES] VALIDATION REUSSIE")
        print(f"   - Extraction dates: {real_dates}/{len(items)} (>70%)")
        print(f"   - Filtre temporel: {len(old_items)}/{len(items)} filtres (>20%)")
    else:
        print(f"[ECHEC] VALIDATION ECHOUEE")
        if not extraction_ok:
            print(f"   - Extraction dates insuffisante: {real_dates}/{len(items)} (<70%)")
        if not filter_ok:
            print(f"   - Filtre temporel inefficace: {len(old_items)}/{len(items)} (<20%)")
    print(f"{'='*70}\n")
    
    return success

if __name__ == '__main__':
    success = validate_date_fix()
    exit(0 if success else 1)
