"""
Test d'integration avec simulation de donnees reelles LAI v6
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src_v2'))

from datetime import datetime
from vectora_core.ingest.content_parser import extract_real_publication_date
from vectora_core.shared.utils import apply_temporal_filter


def simulate_lai_v6_items():
    """Simule les items LAI v6 avec vraies dates dans le contenu"""
    
    items = [
        {
            'title': 'MedinCell + Teva Olanzapine NDA',
            'content': 'December 9, 2025December 9, 2025 MedinCell announces Teva submission',
            'summary': '',
            'published_at': None  # A extraire
        },
        {
            'title': 'MedinCell Malaria Grant',
            'content': 'November 24, 2025 Gates Foundation grant for malaria prevention',
            'summary': '',
            'published_at': None
        },
        {
            'title': 'Nanexa Semaglutide Monthly',
            'content': '27 January, 2026 Nanexa announces monthly semaglutide formulation',
            'summary': '',
            'published_at': None
        },
        {
            'title': 'Camurus Oclaiz FDA',
            'content': 'Released 09 January 2026 FDA accepts Oclaiz application',
            'summary': '',
            'published_at': None
        },
    ]
    
    return items


def test_integration_date_extraction():
    """Test extraction dates sur donnees simulees"""
    print("\n=== Test Integration: Extraction Dates ===\n")
    
    items = simulate_lai_v6_items()
    
    source_configs = {
        'medincell': {
            'date_extraction_patterns': [
                r'(\w+ \d{1,2}, \d{4})\w*'
            ]
        },
        'nanexa': {
            'date_extraction_patterns': [
                r'(\d{1,2} \w+, \d{4})'
            ]
        },
        'camurus': {
            'date_extraction_patterns': [
                r'(\d{2} \w+ \d{4})'
            ]
        }
    }
    
    # Extraire les dates
    for i, item in enumerate(items):
        if 'MedinCell' in item['title']:
            config = source_configs['medincell']
        elif 'Nanexa' in item['title']:
            config = source_configs['nanexa']
        elif 'Camurus' in item['title']:
            config = source_configs['camurus']
        else:
            config = {}
        
        result = extract_real_publication_date(item, config)
        item['published_at'] = result['date']
        item['date_source'] = result['date_source']
        
        print(f"{i+1}. {item['title'][:40]}")
        print(f"   Date extraite: {item['published_at']} (source: {item['date_source']})")
    
    # Verifier les dates extraites
    assert items[0]['published_at'] == '2025-12-09'
    assert items[1]['published_at'] == '2025-11-24'
    assert items[2]['published_at'] == '2026-01-27'
    assert items[3]['published_at'] == '2026-01-09'
    
    print("\n[OK] Toutes les dates extraites correctement")
    return items


def test_integration_temporal_filter(items):
    """Test filtre temporel sur donnees avec vraies dates"""
    print("\n=== Test Integration: Filtre Temporel ===\n")
    
    # Ajouter ingested_at
    for item in items:
        item['ingested_at'] = '2026-01-27T10:00:00'
    
    # Filtre 30 jours
    cutoff_date = '2025-12-28'  # 30 jours avant 2026-01-27
    
    print(f"Cutoff date: {cutoff_date} (30 jours)")
    print(f"Items avant filtre: {len(items)}")
    
    filtered = apply_temporal_filter(items, cutoff_date, temporal_mode='strict')
    
    print(f"Items apres filtre: {len(filtered)}")
    print("\nItems conserves:")
    for item in filtered:
        print(f"  - {item['title'][:40]} ({item['published_at']})")
    
    print("\nItems filtres (trop anciens):")
    filtered_titles = [i['title'] for i in filtered]
    for item in items:
        if item['title'] not in filtered_titles:
            print(f"  - {item['title'][:40]} ({item['published_at']})")
    
    # Verifier le filtrage
    # Items >= 2025-12-28: Nanexa (2026-01-27), Camurus (2026-01-09)
    # Items < 2025-12-28: MedinCell NDA (2025-12-09), MedinCell Grant (2025-11-24)
    assert len(filtered) == 2
    assert 'Nanexa' in filtered[0]['title'] or 'Nanexa' in filtered[1]['title']
    assert 'Camurus' in filtered[0]['title'] or 'Camurus' in filtered[1]['title']
    
    print("\n[OK] Filtre temporel fonctionne correctement")
    print(f"[OK] {len(items) - len(filtered)} items anciens filtres (>30 jours)")


def test_integration_impact():
    """Affiche l'impact du correctif"""
    print("\n=== Impact du Correctif ===\n")
    
    print("AVANT (problematique):")
    print("  - Toutes les dates: 2026-01-27 (date ingestion)")
    print("  - Items conserves: 4/4 (100%)")
    print("  - Filtre temporel: INEFFICACE")
    
    print("\nAPRES (corrige):")
    print("  - Dates reelles extraites: 2025-12-09, 2025-11-24, 2026-01-27, 2026-01-09")
    print("  - Items conserves: 2/4 (50%)")
    print("  - Filtre temporel: EFFICACE")
    
    print("\nBenefices:")
    print("  + Chronologie reelle respectee")
    print("  + Filtre 30 jours fonctionnel")
    print("  + Reduction volume traite (-50%)")
    print("  + Newsletter avec vraies dates")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("TEST INTEGRATION - Correctif Parsing Dates LAI v6")
    print("="*60)
    
    items = test_integration_date_extraction()
    test_integration_temporal_filter(items)
    test_integration_impact()
    
    print("\n" + "="*60)
    print("TOUS LES TESTS D'INTEGRATION PASSES")
    print("="*60 + "\n")
