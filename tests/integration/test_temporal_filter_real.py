"""
Test filtre temporel avec vraies données
Phase 3 - Plan correctif v2 parsing dates
"""
import boto3
import json
from datetime import datetime, timedelta

def test_temporal_filter_real():
    """Vérifie que le filtre temporel fonctionne avec vraies dates"""
    
    s3 = boto3.client('s3', region_name='eu-west-3')
    
    # Télécharger items
    date_str = datetime.now().strftime('%Y/%m/%d')
    key = f'ingested/lai_weekly_v6/{date_str}/items.json'
    
    print(f"\n{'='*70}")
    print(f"TEST FILTRE TEMPOREL")
    print(f"{'='*70}\n")
    print(f"Téléchargement: s3://vectora-inbox-data-dev/{key}")
    
    try:
        response = s3.get_object(
            Bucket='vectora-inbox-data-dev',
            Key=key
        )
        items = json.loads(response['Body'].read())
    except Exception as e:
        print(f"[ERREUR] Erreur téléchargement: {e}")
        return False
    
    print(f"[OK] {len(items)} items téléchargés\n")
    
    # Calculer cutoff (30 jours)
    cutoff_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    # Compter items avant/après cutoff
    recent = []
    old = []
    
    for item in items:
        pub_date = item.get('published_at', '')
        if pub_date >= cutoff_date:
            recent.append(item)
        else:
            old.append(item)
    
    print(f"Cutoff date (30 jours): {cutoff_date}\n")
    
    print(f"Items RÉCENTS (>= cutoff): {len(recent)}")
    for item in recent[:5]:
        print(f"  [OK] {item['published_at']} - {item['title'][:50]}...")
    if len(recent) > 5:
        print(f"  ... et {len(recent)-5} autres")
    
    print(f"\nItems ANCIENS (< cutoff): {len(old)}")
    for item in old[:5]:
        print(f"  [OLD] {item['published_at']} - {item['title'][:50]}...")
    if len(old) > 5:
        print(f"  ... et {len(old)-5} autres")
    
    # Objectif: au moins 20% d'items filtrés
    filter_rate = len(old) / len(items) if items else 0
    
    print(f"\n{'='*70}")
    print(f"RESULTATS")
    print(f"{'='*70}\n")
    print(f"Total items:        {len(items)}")
    print(f"Items conservés:    {len(recent)} ({len(recent)*100//len(items) if items else 0}%)")
    print(f"Items filtrés:      {len(old)} ({int(filter_rate*100)}%)")
    print(f"Efficacité filtre:  {int(filter_rate*100)}%")
    
    success = filter_rate > 0.2
    
    print(f"\n{'='*70}")
    if success:
        print(f"[SUCCES] TEST REUSSI: Filtre efficace ({int(filter_rate*100)}% filtres, >20%)")
    else:
        print(f"[ECHEC] TEST ECHOUE: Filtre inefficace ({int(filter_rate*100)}% filtres, <20%)")
    print(f"{'='*70}\n")
    
    return success

if __name__ == '__main__':
    success = test_temporal_filter_real()
    exit(0 if success else 1)
