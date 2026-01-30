"""
Tests pour le filtre temporel avec détection des dates fallback
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src_v2'))

from datetime import datetime, timedelta
from vectora_core.shared.utils import apply_temporal_filter


def test_temporal_filter_basic():
    """Test filtre temporel basique"""
    items = [
        {'title': 'Recent', 'published_at': '2026-01-20', 'ingested_at': '2026-01-27T10:00:00'},
        {'title': 'Old', 'published_at': '2025-11-24', 'ingested_at': '2026-01-27T10:00:00'},
        {'title': 'Very recent', 'published_at': '2026-01-25', 'ingested_at': '2026-01-27T10:00:00'},
    ]
    
    cutoff_date = '2025-12-28'  # 30 jours avant 2026-01-27
    filtered = apply_temporal_filter(items, cutoff_date, temporal_mode='strict')
    
    assert len(filtered) == 2
    assert filtered[0]['title'] == 'Recent'
    assert filtered[1]['title'] == 'Very recent'
    print("[OK] Test filtre basique")


def test_temporal_filter_fallback_detection():
    """Test détection des dates fallback"""
    items = [
        {
            'title': 'Real date', 
            'published_at': '2025-12-09', 
            'ingested_at': '2026-01-27T10:00:00'
        },
        {
            'title': 'Fallback date', 
            'published_at': '2026-01-27',  # Même jour que ingestion
            'ingested_at': '2026-01-27T10:00:00'
        },
    ]
    
    cutoff_date = '2025-12-01'
    filtered = apply_temporal_filter(items, cutoff_date, temporal_mode='strict')
    
    # Les deux doivent être conservés (>= cutoff)
    assert len(filtered) == 2
    print("[OK] Test detection fallback")


def test_temporal_filter_old_items():
    """Test filtrage items anciens"""
    items = [
        {'title': 'Nov 2025', 'published_at': '2025-11-24', 'ingested_at': '2026-01-27T10:00:00'},
        {'title': 'Dec 2025', 'published_at': '2025-12-09', 'ingested_at': '2026-01-27T10:00:00'},
        {'title': 'Jan 2026', 'published_at': '2026-01-09', 'ingested_at': '2026-01-27T10:00:00'},
    ]
    
    cutoff_date = '2025-12-28'  # 30 jours
    filtered = apply_temporal_filter(items, cutoff_date, temporal_mode='strict')
    
    # Seul Jan 2026 doit être conservé
    assert len(filtered) == 1
    assert filtered[0]['title'] == 'Jan 2026'
    print("[OK] Test filtrage anciens")


def test_temporal_filter_no_date():
    """Test items sans date"""
    items = [
        {'title': 'With date', 'published_at': '2026-01-20', 'ingested_at': '2026-01-27T10:00:00'},
        {'title': 'No date', 'ingested_at': '2026-01-27T10:00:00'},
    ]
    
    cutoff_date = '2025-12-28'
    
    # Mode strict: items sans date exclus
    filtered_strict = apply_temporal_filter(items, cutoff_date, temporal_mode='strict')
    assert len(filtered_strict) == 1
    
    # Mode flexible: items sans date conservés
    filtered_flex = apply_temporal_filter(items, cutoff_date, temporal_mode='flexible')
    assert len(filtered_flex) == 2
    
    print("[OK] Test items sans date")


if __name__ == '__main__':
    print("\nTests filtre temporel\n")
    test_temporal_filter_basic()
    test_temporal_filter_fallback_detection()
    test_temporal_filter_old_items()
    test_temporal_filter_no_date()
    print("\nTous les tests filtre temporel passes!\n")
