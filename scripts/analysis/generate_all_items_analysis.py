#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère l'analyse détaillée de TOUS les items (matchés et non matchés).
"""

import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def load_items():
    with open('.tmp/e2e/lai_weekly_v13/curated_items.json', encoding='utf-8') as f:
        return json.load(f)

def format_item_analysis(item, index, total):
    """Formate l'analyse détaillée d'un item"""
    
    ds = item.get('domain_scoring', {})
    nc = item.get('normalized_content', {})
    is_matched = ds.get('is_relevant', False)
    
    # Header
    status = "✅ MATCHÉ" if is_matched else "❌ NON MATCHÉ"
    title = item.get('title', 'N/A')[:100]
    
    output = f"\n### Item {index}/{total}: {status}\n\n"
    output += f"**{title}**\n\n"
    
    # Métadonnées de base
    output += f"- **Source**: {item.get('source_key', 'N/A')}\n"
    output += f"- **Date**: {item.get('effective_date', 'N/A')}\n"
    output += f"- **Type événement**: {nc.get('event_classification', {}).get('primary_type', 'N/A')}\n"
    output += f"- **URL**: {item.get('url', 'N/A')}\n\n"
    
    # Résumé
    summary = nc.get('summary', 'N/A')
    output += f"**Résumé**: {summary}\n\n"
    
    # Entités extraites (Bedrock appel #1)
    entities = nc.get('entities', {})
    output += "**Entités extraites (Normalisation)**:\n"
    has_entities = False
    for etype, elist in entities.items():
        if elist:
            has_entities = True
            output += f"- {etype}: {', '.join(elist)}\n"
    if not has_entities:
        output += "- Aucune entité LAI détectée\n"
    output += "\n"
    
    if is_matched:
        # Item matché - analyse détaillée
        output += f"**Domain Score**: {ds.get('score', 0)}/100 (confidence: {ds.get('confidence', 'N/A')})\n\n"
        
        # Signaux détectés
        signals = ds.get('signals_detected', {})
        output += "**Signaux LAI détectés**:\n"
        for level in ['strong', 'medium', 'weak']:
            sig_list = signals.get(level, [])
            if sig_list:
                output += f"- **{level.upper()}**: {', '.join(sig_list)}\n"
        output += "\n"
        
        # Score breakdown
        breakdown = ds.get('score_breakdown', {})
        if breakdown:
            output += "**Calcul du score**:\n"
            output += f"- Score de base: {breakdown.get('base_score', 0)}\n"
            
            boosts = breakdown.get('entity_boosts', {})
            if boosts:
                output += f"- Boosts entités:\n"
                for boost_type, boost_val in boosts.items():
                    output += f"  - {boost_type}: +{boost_val}\n"
            
            recency = breakdown.get('recency_boost', 0)
            if recency:
                output += f"- Boost récence: +{recency}\n"
            
            penalty = breakdown.get('confidence_penalty', 0)
            if penalty:
                output += f"- Pénalité confiance: {penalty}\n"
            
            output += f"- **TOTAL: {ds.get('score', 0)}**\n\n"
        
        # Reasoning Bedrock
        reasoning = ds.get('reasoning', '')
        output += f"**Explication Bedrock**: {reasoning}\n\n"
        
        # Pourquoi c'est pertinent
        output += "**💡 Pourquoi cet item est pertinent pour LAI**:\n"
        
        # Analyser les signaux forts
        strong_signals = signals.get('strong', [])
        if strong_signals:
            output += "- **Signaux forts détectés**:\n"
            for sig in strong_signals:
                if 'pure_player' in sig.lower():
                    company = sig.split(':')[-1].strip()
                    output += f"  - {company} est un pure player LAI (entreprise 100% dédiée aux LAI)\n"
                elif 'trademark' in sig.lower():
                    trademark = sig.split(':')[-1].strip()
                    output += f"  - {trademark} est une marque LAI reconnue\n"
        
        # Analyser les signaux moyens
        medium_signals = signals.get('medium', [])
        if medium_signals:
            output += "- **Signaux moyens détectés**:\n"
            for sig in medium_signals:
                if 'hybrid_company' in sig.lower():
                    company = sig.split(':')[-1].strip()
                    output += f"  - {company} développe des produits LAI (parmi d'autres)\n"
                elif 'technology' in sig.lower():
                    tech = sig.split(':')[-1].strip()
                    output += f"  - Technologie LAI mentionnée: {tech}\n"
                elif 'dosing_interval' in sig.lower():
                    interval = sig.split(':')[-1].strip()
                    output += f"  - Intervalle de dosage LAI: {interval}\n"
        
        # Type d'événement
        event_type = nc.get('event_classification', {}).get('primary_type', '')
        if event_type in ['regulatory', 'clinical_update', 'partnership']:
            output += f"- **Type d'événement pertinent**: {event_type} (événements clés pour le secteur LAI)\n"
        
        output += "\n"
        
    else:
        # Item non matché - explication
        output += f"**Domain Score**: 0 (non pertinent)\n\n"
        
        # Reasoning Bedrock
        reasoning = ds.get('reasoning', 'N/A')
        output += f"**Explication Bedrock**: {reasoning}\n\n"
        
        # Pourquoi NON pertinent
        output += "**💡 Pourquoi cet item N'EST PAS pertinent pour LAI**:\n"
        
        # Analyser les raisons
        if 'no LAI signal' in reasoning.lower() or 'no signal' in reasoning.lower():
            output += "- **Aucun signal LAI détecté**: L'item ne mentionne ni entreprise LAI, ni technologie LAI, ni produit LAI\n"
        
        if 'oligonucleotide' in reasoning.lower():
            output += "- **Technologie non-LAI**: Oligonucléotides (pas une formulation injectable à action prolongée)\n"
        
        if 'financial calendar' in reasoning.lower() or 'financial result' in reasoning.lower():
            output += "- **Contenu administratif**: Publication de calendrier ou résultats financiers sans mention de produit LAI\n"
        
        if 'conference' in reasoning.lower() or 'convention' in reasoning.lower():
            output += "- **Événement générique**: Annonce de participation à une conférence sans contenu LAI spécifique\n"
        
        if 'stock index' in reasoning.lower() or 'msci' in reasoning.lower():
            output += "- **Actualité boursière**: Information sur les indices boursiers, non pertinent pour la veille technologique LAI\n"
        
        # Vérifier si c'est une entreprise LAI mais sans contenu pertinent
        source = item.get('source_key', '')
        if any(company in source.lower() for company in ['medincell', 'nanexa', 'camurus']):
            output += "- **Note**: Bien que la source soit une entreprise LAI, le contenu spécifique de cet item n'est pas pertinent pour la newsletter\n"
        
        output += "\n"
    
    output += "---\n"
    return output

def main():
    items = load_items()
    
    # Séparer matchés et non matchés
    matched = [i for i in items if i.get('domain_scoring', {}).get('is_relevant')]
    not_matched = [i for i in items if not i.get('domain_scoring', {}).get('is_relevant')]
    
    # Trier matchés par score décroissant
    matched_sorted = sorted(matched, key=lambda x: x.get('domain_scoring', {}).get('score', 0), reverse=True)
    
    print("\n" + "="*80)
    print("ANALYSE DÉTAILLÉE DE TOUS LES ITEMS (29)")
    print("="*80 + "\n")
    
    print(f"📊 **Vue d'ensemble**: {len(matched)} items matchés, {len(not_matched)} items non matchés\n")
    
    print("\n" + "="*80)
    print("## PARTIE 1: ITEMS MATCHÉS (14)")
    print("="*80 + "\n")
    
    for i, item in enumerate(matched_sorted, 1):
        print(format_item_analysis(item, i, len(matched)))
    
    print("\n" + "="*80)
    print("## PARTIE 2: ITEMS NON MATCHÉS (15)")
    print("="*80 + "\n")
    
    for i, item in enumerate(not_matched, 1):
        print(format_item_analysis(item, i, len(not_matched)))

if __name__ == '__main__':
    main()
