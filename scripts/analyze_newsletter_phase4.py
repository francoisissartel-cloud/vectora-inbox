"""
Script d'analyse de newsletter pour Phase 4 - Validation End-to-End
Usage: python scripts/analyze_newsletter_phase4.py newsletter.json
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# Scopes pure players pour validation
PURE_PLAYERS = [
    'MedinCell', 'Camurus', 'DelSiTech', 'Nanexa', 'Peptron',
    'Bolder BioTechnology', 'Cristal Therapeutics', 'Durect',
    'Eupraxia Pharmaceuticals', 'Foresee Pharmaceuticals', 'G2GBio',
    'Hanmi Pharmaceutical', 'LIDDS', 'Taiwan Liposome'
]

HYBRID = [
    'AbbVie', 'Alkermes', 'Amgen', 'Ascendis Pharma', 'Astellas Pharma',
    'AstraZeneca', 'Bayer', 'Eli Lilly', 'Ferring', 'Gilead Sciences',
    'GlaxoSmithKline', 'Ipsen', 'Janssen', 'Janssen Pharmaceuticals',
    'Jazz Pharmaceuticals', 'Johnson & Johnson', 'Lundbeck', 'Luye Pharma',
    'Merck & Co', 'Novartis', 'Novo Nordisk', 'Otsuka', 'Pfizer',
    'Sanofi', 'Takeda Pharmaceutical', 'Teva Pharmaceutical', 'ViiV Healthcare'
]


def analyze_newsletter(newsletter_path: str) -> Dict[str, Any]:
    """Analyse la newsletter et calcule les métriques Phase 4."""
    
    with open(newsletter_path, 'r', encoding='utf-8') as f:
        newsletter = json.load(f)
    
    items = newsletter.get('items', [])
    
    # Métriques de base
    total_items = len(items)
    
    # Classifier les items
    pure_player_items = []
    hybrid_items = []
    other_items = []
    
    for item in items:
        companies = item.get('companies_detected', [])
        
        # Identifier le type
        is_pure = any(c in PURE_PLAYERS for c in companies)
        is_hybrid = any(c in HYBRID for c in companies)
        
        if is_pure:
            pure_player_items.append(item)
        elif is_hybrid:
            hybrid_items.append(item)
        else:
            other_items.append(item)
    
    # Calculer les métriques
    pure_player_count = len(pure_player_items)
    hybrid_count = len(hybrid_items)
    other_count = len(other_items)
    
    pure_player_pct = (pure_player_count / total_items * 100) if total_items > 0 else 0
    
    # Afficher les résultats
    print("\n" + "="*80)
    print("PHASE 4 - ANALYSE NEWSLETTER LAI")
    print("="*80)
    
    print(f"\n📊 MÉTRIQUES GLOBALES")
    print(f"   Total items: {total_items}")
    print(f"   Pure players: {pure_player_count} ({pure_player_pct:.1f}%)")
    print(f"   Hybrid: {hybrid_count} ({hybrid_count/total_items*100 if total_items > 0 else 0:.1f}%)")
    print(f"   Other: {other_count} ({other_count/total_items*100 if total_items > 0 else 0:.1f}%)")
    
    # Objectifs MVP
    print(f"\n🎯 OBJECTIFS MVP")
    print(f"   LAI precision: À valider manuellement (objectif ≥80%)")
    print(f"   Pure player %: {pure_player_pct:.1f}% (objectif ≥50%) {'✅' if pure_player_pct >= 50 else '❌'}")
    print(f"   False positives: À valider manuellement (objectif 0)")
    
    # Détail des pure players
    if pure_player_items:
        print(f"\n✅ PURE PLAYERS DÉTECTÉS ({pure_player_count})")
        for i, item in enumerate(pure_player_items, 1):
            companies = [c for c in item.get('companies_detected', []) if c in PURE_PLAYERS]
            score = item.get('score', 0)
            title = item.get('title', 'N/A')[:60]
            print(f"   {i}. {companies[0]} (score: {score:.1f}) - {title}...")
    
    # Détail des hybrid
    if hybrid_items:
        print(f"\n⚠️  HYBRID DÉTECTÉS ({hybrid_count})")
        for i, item in enumerate(hybrid_items, 1):
            companies = [c for c in item.get('companies_detected', []) if c in HYBRID]
            score = item.get('score', 0)
            title = item.get('title', 'N/A')[:60]
            matching_details = item.get('matching_details', {})
            confidence = matching_details.get('match_confidence', 'N/A')
            print(f"   {i}. {companies[0]} (score: {score:.1f}, conf: {confidence}) - {title}...")
    
    # Validation manuelle requise
    print(f"\n📋 VALIDATION MANUELLE REQUISE")
    print(f"   Pour chaque item, classifier:")
    print(f"   - ✅ Vrai positif LAI (news pertinente sur LAI)")
    print(f"   - ❌ Faux positif (news non-LAI ou hors scope)")
    
    print(f"\n" + "="*80)
    
    # Décision GO/NO-GO
    print(f"\n🚦 DÉCISION GO/NO-GO")
    
    if pure_player_pct >= 50:
        print(f"   Pure player %: 🟢 GREEN (≥50%)")
    elif pure_player_pct >= 30:
        print(f"   Pure player %: 🟡 AMBER (30-50%)")
    else:
        print(f"   Pure player %: 🔴 RED (<30%)")
    
    print(f"   LAI precision: ⚪ À valider manuellement")
    print(f"   False positives: ⚪ À valider manuellement")
    
    print(f"\n" + "="*80 + "\n")
    
    return {
        'total_items': total_items,
        'pure_player_count': pure_player_count,
        'pure_player_pct': pure_player_pct,
        'hybrid_count': hybrid_count,
        'other_count': other_count,
        'pure_player_items': pure_player_items,
        'hybrid_items': hybrid_items
    }


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python scripts/analyze_newsletter_phase4.py newsletter.json")
        sys.exit(1)
    
    newsletter_path = sys.argv[1]
    
    if not Path(newsletter_path).exists():
        print(f"❌ Fichier introuvable: {newsletter_path}")
        sys.exit(1)
    
    analyze_newsletter(newsletter_path)
