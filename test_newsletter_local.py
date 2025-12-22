#!/usr/bin/env python3
"""
Test local de la logique newsletter V2
Valide la sélection, déduplication et assemblage sans déploiement
"""

import sys
import os
import json
import logging
from datetime import datetime

# Ajouter src_v2 au path pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src_v2'))

from vectora_core.newsletter import selector, assembler

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_test_data():
    """Charge les données de test"""
    logger.info("Chargement des données de test...")
    
    # Charger les items curated
    with open('test_curated_items.json', 'r', encoding='utf-8') as f:
        curated_items = json.load(f)
    
    # Charger la config client
    with open('lai_weekly_v4.yaml', 'r', encoding='utf-8') as f:
        import yaml
        client_config = yaml.safe_load(f)
    
    logger.info(f"Items curated chargés: {len(curated_items)}")
    logger.info(f"Config client chargée: {client_config['client_profile']['name']}")
    
    return curated_items, client_config

def test_selection_logic(curated_items, client_config):
    """Test de la logique de sélection"""
    logger.info("\n=== TEST SÉLECTION ET DÉDUPLICATION ===")
    
    # Test du sélecteur
    selected_items = selector.select_and_deduplicate_items(curated_items, client_config)
    
    # Analyse des résultats
    total_selected = sum(len(section['items']) for section in selected_items.values())
    logger.info(f"Items sélectionnés au total: {total_selected}")
    
    for section_id, section_data in selected_items.items():
        items_count = len(section_data['items'])
        logger.info(f"Section {section_id}: {items_count} items")
        
        # Afficher les premiers items de chaque section
        for i, item in enumerate(section_data['items'][:2]):  # Premiers 2 items
            score = item.get('scoring_results', {}).get('final_score', 0)
            title = item.get('normalized_content', {}).get('summary', 'No title')[:60]
            logger.info(f"  [{i+1}] Score: {score:.1f} - {title}...")
    
    return selected_items

def test_assembler_logic(selected_items, client_config):
    """Test de l'assemblage des formats"""
    logger.info("\n=== TEST ASSEMBLAGE FORMATS ===")
    
    # Contenu éditorial factice pour le test
    editorial_content = {
        "tldr": "This week's LAI ecosystem shows continued innovation with partnership activity and clinical advances.",
        "introduction": "Executive intelligence on Long-Acting Injectable technologies and ecosystem developments.",
        "bedrock_calls": {
            "tldr_generation": {"status": "success"},
            "introduction_generation": {"status": "success"}
        }
    }
    
    # Test de l'assembleur
    newsletter_result = assembler.assemble_newsletter(
        selected_items, editorial_content, client_config, "2025-12-20"
    )
    
    # Analyse des résultats
    markdown_length = len(newsletter_result['markdown'])
    json_sections = len(newsletter_result['json']['sections'])
    
    logger.info(f"Newsletter Markdown générée: {markdown_length} caractères")
    logger.info(f"Métadonnées JSON: {json_sections} sections")
    logger.info(f"Manifest généré: {newsletter_result['manifest']['status']}")
    
    # Sauvegarder les résultats pour inspection
    with open('test_newsletter.md', 'w', encoding='utf-8') as f:
        f.write(newsletter_result['markdown'])
    
    with open('test_newsletter.json', 'w', encoding='utf-8') as f:
        json.dump(newsletter_result['json'], f, indent=2, ensure_ascii=False)
    
    logger.info("Fichiers de test sauvegardés: test_newsletter.md, test_newsletter.json")
    
    return newsletter_result

def analyze_selection_quality(curated_items, selected_items):
    """Analyse la qualité de la sélection"""
    logger.info("\n=== ANALYSE QUALITÉ SÉLECTION ===")
    
    total_curated = len(curated_items)
    total_selected = sum(len(section['items']) for section in selected_items.values())
    
    # Analyse des scores
    all_scores = []
    for item in curated_items:
        score = item.get('scoring_results', {}).get('final_score', 0)
        all_scores.append(score)
    
    selected_scores = []
    for section_data in selected_items.values():
        for item in section_data['items']:
            score = item.get('scoring_results', {}).get('final_score', 0)
            selected_scores.append(score)
    
    avg_curated_score = sum(all_scores) / len(all_scores) if all_scores else 0
    avg_selected_score = sum(selected_scores) / len(selected_scores) if selected_scores else 0
    
    logger.info(f"Taux de sélection: {total_selected}/{total_curated} ({total_selected/total_curated*100:.1f}%)")
    logger.info(f"Score moyen curated: {avg_curated_score:.1f}")
    logger.info(f"Score moyen sélectionné: {avg_selected_score:.1f}")
    
    # Analyse des domaines matchés
    matched_domains_count = 0
    fallback_count = 0
    
    for item in curated_items:
        matched_domains = item.get('matching_results', {}).get('matched_domains', [])
        if matched_domains:
            matched_domains_count += 1
        else:
            fallback_count += 1
    
    logger.info(f"Items avec matched_domains: {matched_domains_count} ({matched_domains_count/total_curated*100:.1f}%)")
    logger.info(f"Items en mode fallback: {fallback_count} ({fallback_count/total_curated*100:.1f}%)")

def main():
    """Fonction principale de test"""
    logger.info("=== DÉBUT DES TESTS NEWSLETTER V2 ===")
    
    try:
        # Chargement des données
        curated_items, client_config = load_test_data()
        
        # Test de la sélection
        selected_items = test_selection_logic(curated_items, client_config)
        
        # Test de l'assemblage
        newsletter_result = test_assembler_logic(selected_items, client_config)
        
        # Analyse de la qualité
        analyze_selection_quality(curated_items, selected_items)
        
        logger.info("\n=== TESTS TERMINÉS AVEC SUCCÈS ===")
        logger.info("Vérifiez les fichiers: test_newsletter.md, test_newsletter.json")
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors des tests: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)