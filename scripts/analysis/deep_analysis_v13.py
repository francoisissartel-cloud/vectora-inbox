#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyse détaillée E2E lai_weekly_v13.
Analyse complète: Lambda, Bedrock, items, matching, scoring.
"""

import json
import sys
import io
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def load_items():
    with open('.tmp/e2e/lai_weekly_v13/curated_items.json', encoding='utf-8') as f:
        return json.load(f)

def analyze_items(items):
    """Analyse détaillée de tous les items"""
    
    matched = [i for i in items if i.get('domain_scoring', {}).get('is_relevant')]
    not_matched = [i for i in items if not i.get('domain_scoring', {}).get('is_relevant')]
    
    # Statistiques par source
    by_source = defaultdict(lambda: {'total': 0, 'matched': 0})
    for item in items:
        source = item.get('source_type', 'unknown')
        by_source[source]['total'] += 1
        if item.get('domain_scoring', {}).get('is_relevant'):
            by_source[source]['matched'] += 1
    
    # Statistiques par type d'événement
    by_event = defaultdict(lambda: {'total': 0, 'matched': 0})
    for item in items:
        event_type = item.get('normalized_content', {}).get('event_classification', {}).get('primary_type', 'unknown')
        by_event[event_type]['total'] += 1
        if item.get('domain_scoring', {}).get('is_relevant'):
            by_event[event_type]['matched'] += 1
    
    # Statistiques par signaux
    signal_stats = {'strong': defaultdict(int), 'medium': defaultdict(int), 'weak': defaultdict(int)}
    for item in matched:
        signals = item.get('domain_scoring', {}).get('signals_detected', {})
        for level in ['strong', 'medium', 'weak']:
            for signal in signals.get(level, []):
                signal_stats[level][signal] += 1
    
    return {
        'matched': matched,
        'not_matched': not_matched,
        'by_source': dict(by_source),
        'by_event': dict(by_event),
        'signal_stats': signal_stats
    }

def print_report(items, analysis):
    """Génère le rapport détaillé"""
    
    print(f"\n{'='*80}")
    print(f"RAPPORT DÉTAILLÉ E2E LAI_WEEKLY_V13")
    print(f"{'='*80}\n")
    
    # Vue d'ensemble
    print(f"## 📊 VUE D'ENSEMBLE\n")
    print(f"- Items totaux: {len(items)}")
    print(f"- Items matchés: {len(analysis['matched'])} ({len(analysis['matched'])/len(items)*100:.1f}%)")
    print(f"- Items non matchés: {len(analysis['not_matched'])} ({len(analysis['not_matched'])/len(items)*100:.1f}%)")
    
    # Par source
    print(f"\n## 📡 ANALYSE PAR SOURCE\n")
    for source, stats in sorted(analysis['by_source'].items()):
        rate = stats['matched']/stats['total']*100 if stats['total'] > 0 else 0
        print(f"- {source}: {stats['matched']}/{stats['total']} ({rate:.1f}%)")
    
    # Par type d'événement
    print(f"\n## 🎯 ANALYSE PAR TYPE D'ÉVÉNEMENT\n")
    for event, stats in sorted(analysis['by_event'].items(), key=lambda x: x[1]['matched'], reverse=True):
        rate = stats['matched']/stats['total']*100 if stats['total'] > 0 else 0
        print(f"- {event}: {stats['matched']}/{stats['total']} ({rate:.1f}%)")
    
    # Signaux détectés
    print(f"\n## 🔍 SIGNAUX DÉTECTÉS (Items matchés)\n")
    for level in ['strong', 'medium', 'weak']:
        if analysis['signal_stats'][level]:
            print(f"\n### {level.upper()} signals:")
            for signal, count in sorted(analysis['signal_stats'][level].items(), key=lambda x: x[1], reverse=True):
                print(f"  - {signal}: {count}x")
    
    # Items matchés détaillés
    print(f"\n{'='*80}")
    print(f"## ✅ ITEMS MATCHÉS ({len(analysis['matched'])})")
    print(f"{'='*80}\n")
    
    for i, item in enumerate(sorted(analysis['matched'], key=lambda x: x.get('domain_scoring', {}).get('score', 0), reverse=True), 1):
        ds = item.get('domain_scoring', {})
        nc = item.get('normalized_content', {})
        
        print(f"\n### [{i}] {item.get('title', 'N/A')[:80]}")
        print(f"- **Source**: {item.get('source_key', 'N/A')}")
        print(f"- **Date**: {item.get('effective_date', 'N/A')}")
        print(f"- **Event**: {nc.get('event_classification', {}).get('primary_type', 'N/A')}")
        print(f"- **Domain Score**: {ds.get('score', 0)} ({ds.get('confidence', 'N/A')})")
        print(f"- **Final Score**: {item.get('scoring_results', {}).get('final_score', 0)}")
        
        # Entités
        entities = nc.get('entities', {})
        if any(entities.values()):
            print(f"- **Entités**:")
            for etype, elist in entities.items():
                if elist:
                    print(f"  - {etype}: {', '.join(elist)}")
        
        # Signaux
        signals = ds.get('signals_detected', {})
        if any(signals.get(l, []) for l in ['strong', 'medium', 'weak']):
            print(f"- **Signaux**:")
            for level in ['strong', 'medium', 'weak']:
                if signals.get(level):
                    print(f"  - {level}: {', '.join(signals[level])}")
        
        # Reasoning
        reasoning = ds.get('reasoning', '')
        if reasoning:
            print(f"- **Reasoning**: {reasoning}")
        
        # Score breakdown
        breakdown = ds.get('score_breakdown', {})
        if breakdown:
            print(f"- **Score Breakdown**:")
            print(f"  - Base: {breakdown.get('base_score', 0)}")
            if breakdown.get('entity_boosts'):
                print(f"  - Boosts: {breakdown['entity_boosts']}")
            print(f"  - Recency: +{breakdown.get('recency_boost', 0)}")
            print(f"  - Penalty: {breakdown.get('confidence_penalty', 0)}")
    
    # Items non matchés détaillés
    print(f"\n{'='*80}")
    print(f"## ❌ ITEMS NON MATCHÉS ({len(analysis['not_matched'])})")
    print(f"{'='*80}\n")
    
    for i, item in enumerate(analysis['not_matched'], 1):
        ds = item.get('domain_scoring', {})
        nc = item.get('normalized_content', {})
        
        print(f"\n### [{i}] {item.get('title', 'N/A')[:80]}")
        print(f"- **Source**: {item.get('source_key', 'N/A')}")
        print(f"- **Date**: {item.get('effective_date', 'N/A')}")
        print(f"- **Event**: {nc.get('event_classification', {}).get('primary_type', 'N/A')}")
        print(f"- **Reasoning**: {ds.get('reasoning', 'N/A')}")
        
        # Entités (pour comprendre pourquoi pas matché)
        entities = nc.get('entities', {})
        if any(entities.values()):
            print(f"- **Entités détectées**:")
            for etype, elist in entities.items():
                if elist:
                    print(f"  - {etype}: {', '.join(elist)}")
        else:
            print(f"- **Entités**: Aucune entité LAI détectée")

def main():
    items = load_items()
    analysis = analyze_items(items)
    print_report(items, analysis)

if __name__ == '__main__':
    main()
