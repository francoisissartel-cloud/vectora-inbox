#!/usr/bin/env python3
"""
Tests locaux pour la logique period_days dans ingest-normalize.

Ce script teste les différents cas d'usage de la résolution period_days
et du filtre temporel avant normalisation Bedrock.
"""

import sys
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from vectora_core.utils.config_utils import resolve_period_days
from vectora_core import _apply_temporal_filter


def test_resolve_period_days():
    """Test de la fonction resolve_period_days avec différents cas."""
    print("=== Test resolve_period_days ===")
    
    # Cas A : period_days dans le payload (priorité 1)
    result = resolve_period_days(14, {"pipeline": {"default_period_days": 30}})
    assert result == 14, f"Attendu 14, reçu {result}"
    print("OK Cas A : Payload prioritaire (14 jours)")
    
    # Cas B : period_days dans client_config (priorité 2)
    result = resolve_period_days(None, {"pipeline": {"default_period_days": 30}})
    assert result == 30, f"Attendu 30, reçu {result}"
    print("OK Cas B : Client config (30 jours)")
    
    # Cas C : fallback global (priorité 3)
    result = resolve_period_days(None, {})
    assert result == 7, f"Attendu 7, reçu {result}"
    print("OK Cas C : Fallback global (7 jours)")
    
    # Cas D : client sans section pipeline
    result = resolve_period_days(None, {"other_config": "value"})
    assert result == 7, f"Attendu 7, reçu {result}"
    print("OK Cas D : Client sans pipeline (7 jours)")
    
    print()


def test_temporal_filter():
    """Test du filtre temporel sur des items avec différentes dates."""
    print("=== Test filtre temporel ===")
    
    # Créer des items de test avec différentes dates
    today = datetime.now()
    items = [
        {
            "title": "Item récent (2 jours)",
            "published_at": (today - timedelta(days=2)).strftime('%Y-%m-%d'),
            "url": "https://example.com/recent"
        },
        {
            "title": "Item moyen (15 jours)",
            "published_at": (today - timedelta(days=15)).strftime('%Y-%m-%d'),
            "url": "https://example.com/medium"
        },
        {
            "title": "Item ancien (45 jours)",
            "published_at": (today - timedelta(days=45)).strftime('%Y-%m-%d'),
            "url": "https://example.com/old"
        },
        {
            "title": "Item sans date",
            "url": "https://example.com/no-date"
        },
        {
            "title": "Item date invalide",
            "published_at": "invalid-date",
            "url": "https://example.com/invalid"
        }
    ]
    
    # Test avec period_days = 7
    cutoff_7_days = (today - timedelta(days=7)).strftime('%Y-%m-%d')
    filtered_7 = _apply_temporal_filter(items, cutoff_7_days)
    assert len(filtered_7) == 1, f"Attendu 1 item (7 jours), reçu {len(filtered_7)}"
    assert "récent" in filtered_7[0]["title"], "L'item récent devrait être conservé"
    print("OK Filtre 7 jours : 1 item conserve")
    
    # Test avec period_days = 30
    cutoff_30_days = (today - timedelta(days=30)).strftime('%Y-%m-%d')
    filtered_30 = _apply_temporal_filter(items, cutoff_30_days)
    assert len(filtered_30) == 2, f"Attendu 2 items (30 jours), reçu {len(filtered_30)}"
    print("OK Filtre 30 jours : 2 items conserves")
    
    # Test avec period_days = 60 (tous les items avec date valide)
    cutoff_60_days = (today - timedelta(days=60)).strftime('%Y-%m-%d')
    filtered_60 = _apply_temporal_filter(items, cutoff_60_days)
    assert len(filtered_60) == 3, f"Attendu 3 items (60 jours), reçu {len(filtered_60)}"
    print("OK Filtre 60 jours : 3 items conserves")
    
    print()


def test_lai_weekly_v2_config():
    """Test avec la configuration réelle lai_weekly_v2."""
    print("=== Test configuration lai_weekly_v2 ===")
    
    # Configuration lai_weekly_v2 (extrait)
    lai_config = {
        "pipeline": {
            "default_period_days": 30,
            "notes": "Fenêtre temporelle LAI Weekly v2 - 30 jours pour couvrir cycles longs"
        }
    }
    
    # Test sans override payload
    result = resolve_period_days(None, lai_config)
    assert result == 30, f"Attendu 30 jours pour lai_weekly_v2, reçu {result}"
    print("OK lai_weekly_v2 sans override : 30 jours")
    
    # Test avec override payload
    result = resolve_period_days(7, lai_config)
    assert result == 7, f"Attendu 7 jours (override), reçu {result}"
    print("OK lai_weekly_v2 avec override : 7 jours")
    
    print()


def simulate_ingest_normalize_execution():
    """Simulation d'une exécution complète ingest-normalize avec period_days."""
    print("=== Simulation exécution ingest-normalize ===")
    
    # Payload Lambda simulé
    event = {
        "client_id": "lai_weekly_v2"
        # Pas de period_days dans le payload
    }
    
    # Configuration client simulée
    client_config = {
        "pipeline": {
            "default_period_days": 30
        }
    }
    
    # Items bruts simulés
    today = datetime.now()
    raw_items = [
        {"title": "MedinCell Partnership", "published_at": (today - timedelta(days=5)).strftime('%Y-%m-%d')},
        {"title": "Camurus Clinical Update", "published_at": (today - timedelta(days=20)).strftime('%Y-%m-%d')},
        {"title": "Old Peptron News", "published_at": (today - timedelta(days=50)).strftime('%Y-%m-%d')},
    ]
    
    # Étape 1 : Résoudre period_days
    resolved_period = resolve_period_days(event.get("period_days"), client_config)
    print(f"Period days résolu : {resolved_period}")
    
    # Étape 2 : Appliquer le filtre temporel
    cutoff_date = (today - timedelta(days=resolved_period)).strftime('%Y-%m-%d')
    filtered_items = _apply_temporal_filter(raw_items, cutoff_date)
    
    print(f"Items avant filtre : {len(raw_items)}")
    print(f"Items après filtre : {len(filtered_items)}")
    print(f"Items filtrés : {[item['title'] for item in filtered_items]}")
    
    # Vérification : avec 30 jours, on devrait avoir 2 items (5 et 20 jours)
    assert len(filtered_items) == 2, f"Attendu 2 items avec 30 jours, reçu {len(filtered_items)}"
    print("OK Simulation reussie : 2 items conserves sur 3")
    
    print()


def main():
    """Exécute tous les tests."""
    print("Tests locaux : period_days dans ingest-normalize\n")
    
    try:
        test_resolve_period_days()
        test_temporal_filter()
        test_lai_weekly_v2_config()
        simulate_ingest_normalize_execution()
        
        print("Tous les tests sont passes avec succes !")
        print("\nResume des validations :")
        print("  OK Resolution period_days (payload > client_config > fallback)")
        print("  OK Filtre temporel sur items bruts")
        print("  OK Compatibilite lai_weekly_v2 (30 jours)")
        print("  OK Gestion des items sans date (ignores)")
        print("  OK Simulation complete ingest-normalize")
        
    except Exception as e:
        print(f"ERREUR lors des tests : {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()