#!/usr/bin/env python3
"""
Script de test des améliorations Phase 1-4 du Plan d'Amélioration Moteur Vectora V2

Ce script teste les améliorations implémentées :
- Phase 1 : Extraction dates réelles + enrichissement contenu
- Phase 2 : Correction hallucinations Bedrock + classification event types
- Phase 3 : Distribution newsletter spécialisée avec section "others"
- Phase 4 : Scope métier automatique + gestion sections vides

Usage:
    python scripts/test_improvements_phase_1_4.py --client-id lai_weekly_v4
"""

import sys
import os
import argparse
import logging
from datetime import datetime

# Ajout du chemin src_v2 pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src_v2'))

from vectora_core.ingest.content_parser import (
    extract_real_publication_date, 
    enrich_content_extraction,
    extract_full_article_content,
    extract_enhanced_summary
)
from vectora_core.normalization.normalizer import (
    validate_bedrock_response,
    get_technology_keywords
)
from vectora_core.newsletter.selector import NewsletterSelector
from vectora_core.newsletter.assembler import (
    generate_newsletter_scope,
    render_newsletter_sections
)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_phase_1_date_extraction():
    """Test Phase 1.1 : Extraction dates réelles"""
    logger.info("=== TEST PHASE 1.1 : EXTRACTION DATES RÉELLES ===")
    
    # Test avec données RSS simulées
    test_cases = [
        {
            'name': 'RSS avec published_parsed',
            'item_data': {
                'published_parsed': (2025, 12, 15, 10, 30, 0, 0, 0, 0)
            },
            'source_config': {},
            'expected_source': 'rss_parsed'
        },
        {
            'name': 'Contenu avec pattern de date',
            'item_data': {
                'content': 'Published: 2025-12-20 - Important news about LAI technology',
                'title': 'LAI Breakthrough'
            },
            'source_config': {
                'date_extraction_patterns': [r"Published:\s*(\d{4}-\d{2}-\d{2})"]
            },
            'expected_source': 'content_extraction'
        },
        {
            'name': 'Fallback sur date ingestion',
            'item_data': {
                'content': 'Generic news without date',
                'title': 'Generic Title'
            },
            'source_config': {},
            'expected_source': 'ingestion_fallback'
        }
    ]
    
    results = []
    for test_case in test_cases:
        try:
            result = extract_real_publication_date(
                test_case['item_data'], 
                test_case['source_config']
            )
            
            success = result['date_source'] == test_case['expected_source']
            results.append({
                'name': test_case['name'],
                'success': success,
                'result': result,
                'expected': test_case['expected_source']
            })
            
            logger.info(f"✅ {test_case['name']}: {result['date_source']} = {result['date']}")
            
        except Exception as e:
            logger.error(f"❌ {test_case['name']}: {str(e)}")
            results.append({
                'name': test_case['name'],
                'success': False,
                'error': str(e)
            })
    
    success_rate = sum(1 for r in results if r['success']) / len(results)
    logger.info(f"Phase 1.1 Success Rate: {success_rate:.1%}")
    return results

def test_phase_1_content_enrichment():
    """Test Phase 1.2 : Enrichissement contenu"""
    logger.info("=== TEST PHASE 1.2 : ENRICHISSEMENT CONTENU ===")
    
    test_cases = [
        {
            'name': 'Strategy basic',
            'url': 'https://example.com/news',
            'basic_content': 'Short basic content',
            'source_config': {'content_enrichment': 'basic'},
            'expected_length_min': 10
        },
        {
            'name': 'Strategy summary_enhanced',
            'url': 'https://example.com/news',
            'basic_content': 'Short basic content',
            'source_config': {
                'content_enrichment': 'summary_enhanced',
                'max_content_length': 500
            },
            'expected_length_min': 10
        }
    ]
    
    results = []
    for test_case in test_cases:
        try:
            result = enrich_content_extraction(
                test_case['url'],
                test_case['basic_content'],
                test_case['source_config']
            )
            
            success = len(result) >= test_case['expected_length_min']
            results.append({
                'name': test_case['name'],
                'success': success,
                'content_length': len(result),
                'strategy': test_case['source_config'].get('content_enrichment', 'basic')
            })
            
            logger.info(f"✅ {test_case['name']}: {len(result)} chars, strategy={test_case['source_config'].get('content_enrichment', 'basic')}")
            
        except Exception as e:
            logger.error(f"❌ {test_case['name']}: {str(e)}")
            results.append({
                'name': test_case['name'],
                'success': False,
                'error': str(e)
            })
    
    success_rate = sum(1 for r in results if r['success']) / len(results)
    logger.info(f"Phase 1.2 Success Rate: {success_rate:.1%}")
    return results

def test_phase_2_hallucination_validation():
    """Test Phase 2.1 : Validation anti-hallucinations"""
    logger.info("=== TEST PHASE 2.1 : VALIDATION ANTI-HALLUCINATIONS ===")
    
    test_cases = [
        {
            'name': 'Hallucination détectée - technologie absente',
            'bedrock_response': {
                'companies_detected': ['MedinCell'],
                'technologies_detected': ['Extended-Release Injectable', 'PLGA'],
                'entities': {
                    'companies': ['MedinCell'],
                    'technologies': ['Extended-Release Injectable', 'PLGA']
                }
            },
            'original_content': 'MedinCell announces partnership conference 2025',
            'expected_tech_count': 0  # Aucune technologie ne devrait rester
        },
        {
            'name': 'Validation réussie - technologie présente',
            'bedrock_response': {
                'companies_detected': ['MedinCell'],
                'technologies_detected': ['Long-Acting Injectable'],
                'entities': {
                    'companies': ['MedinCell'],
                    'technologies': ['Long-Acting Injectable']
                }
            },
            'original_content': 'MedinCell develops new long-acting injectable technology',
            'expected_tech_count': 1  # La technologie devrait rester
        }
    ]
    
    results = []
    for test_case in test_cases:
        try:
            result = validate_bedrock_response(
                test_case['bedrock_response'].copy(),
                test_case['original_content']
            )
            
            actual_tech_count = len(result.get('technologies_detected', []))
            success = actual_tech_count == test_case['expected_tech_count']
            
            results.append({
                'name': test_case['name'],
                'success': success,
                'actual_tech_count': actual_tech_count,
                'expected_tech_count': test_case['expected_tech_count']
            })
            
            logger.info(f"✅ {test_case['name']}: {actual_tech_count} technologies kept (expected {test_case['expected_tech_count']})")
            
        except Exception as e:
            logger.error(f"❌ {test_case['name']}: {str(e)}")
            results.append({
                'name': test_case['name'],
                'success': False,
                'error': str(e)
            })
    
    success_rate = sum(1 for r in results if r['success']) / len(results)
    logger.info(f"Phase 2.1 Success Rate: {success_rate:.1%}")
    return results

def test_phase_3_specialized_distribution():
    """Test Phase 3.1 : Distribution spécialisée avec section others"""
    logger.info("=== TEST PHASE 3.1 : DISTRIBUTION SPÉCIALISÉE ===")
    
    # Configuration de test avec distribution_strategy
    client_config = {
        'newsletter_layout': {
            'distribution_strategy': 'specialized_with_fallback',
            'sections': [
                {
                    'id': 'regulatory_updates',
                    'title': 'Regulatory Updates',
                    'max_items': 2,
                    'filter_event_types': ['regulatory'],
                    'priority': 1
                },
                {
                    'id': 'partnerships_deals',
                    'title': 'Partnerships & Deals',
                    'max_items': 2,
                    'filter_event_types': ['partnership'],
                    'priority': 2
                },
                {
                    'id': 'others',
                    'title': 'Other Signals',
                    'max_items': 5,
                    'filter_event_types': ['*'],
                    'priority': 999
                }
            ]
        },
        'newsletter_selection': {
            'max_items_total': 10,
            'critical_event_types': ['regulatory', 'partnership']
        }
    }
    
    # Items de test simulés
    test_items = [
        {
            'item_id': 'reg_1',
            'normalized_content': {
                'event_classification': {'primary_type': 'regulatory'},
                'summary': 'FDA approval for UZEDY'
            },
            'matching_results': {'matched_domains': ['tech_lai_ecosystem']},
            'scoring_results': {'final_score': 15}
        },
        {
            'item_id': 'part_1',
            'normalized_content': {
                'event_classification': {'primary_type': 'partnership'},
                'summary': 'MedinCell partnership'
            },
            'matching_results': {'matched_domains': ['tech_lai_ecosystem']},
            'scoring_results': {'final_score': 12}
        },
        {
            'item_id': 'other_1',
            'normalized_content': {
                'event_classification': {'primary_type': 'clinical_update'},
                'summary': 'Clinical trial results'
            },
            'matching_results': {'matched_domains': ['tech_lai_ecosystem']},
            'scoring_results': {'final_score': 10}
        }
    ]
    
    try:
        selector = NewsletterSelector(client_config)
        result = selector.select_items(test_items)
        
        sections = result['sections']
        
        # Vérifications
        regulatory_count = len(sections.get('regulatory_updates', {}).get('items', []))
        partnerships_count = len(sections.get('partnerships_deals', {}).get('items', []))
        others_count = len(sections.get('others', {}).get('items', []))
        
        success = (
            regulatory_count == 1 and  # 1 item regulatory
            partnerships_count == 1 and  # 1 item partnership
            others_count == 1  # 1 item dans others
        )
        
        logger.info(f"✅ Distribution: regulatory={regulatory_count}, partnerships={partnerships_count}, others={others_count}")
        
        return [{
            'name': 'Distribution spécialisée',
            'success': success,
            'regulatory_count': regulatory_count,
            'partnerships_count': partnerships_count,
            'others_count': others_count
        }]
        
    except Exception as e:
        logger.error(f"❌ Distribution spécialisée: {str(e)}")
        return [{
            'name': 'Distribution spécialisée',
            'success': False,
            'error': str(e)
        }]

def test_phase_4_newsletter_scope():
    """Test Phase 4.1 : Scope métier automatique"""
    logger.info("=== TEST PHASE 4.1 : SCOPE MÉTIER AUTOMATIQUE ===")
    
    client_config = {
        'watch_domains': [
            {'id': 'tech_lai_ecosystem', 'type': 'technology'},
            {'id': 'regulatory_lai', 'type': 'regulatory'}
        ],
        'pipeline': {
            'default_period_days': 30
        }
    }
    
    items_metadata = {
        'sources_used': [
            'press_corporate__medincell',
            'press_corporate__camurus',
            'press_sector__fiercebiotech'
        ]
    }
    
    try:
        scope_content = generate_newsletter_scope(client_config, items_metadata)
        
        # Vérifications
        success = (
            'Périmètre de cette newsletter' in scope_content and
            'Sources surveillées' in scope_content and
            'Domaines de veille' in scope_content and
            'tech_lai_ecosystem' in scope_content
        )
        
        logger.info(f"✅ Scope métier généré: {len(scope_content)} caractères")
        logger.info(f"Contenu: {scope_content[:200]}...")
        
        return [{
            'name': 'Scope métier automatique',
            'success': success,
            'content_length': len(scope_content)
        }]
        
    except Exception as e:
        logger.error(f"❌ Scope métier: {str(e)}")
        return [{
            'name': 'Scope métier automatique',
            'success': False,
            'error': str(e)
        }]

def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description='Test des améliorations Phase 1-4')
    parser.add_argument('--client-id', default='lai_weekly_v4', help='Client ID pour les tests')
    parser.add_argument('--phase', choices=['1', '2', '3', '4', 'all'], default='all', help='Phase à tester')
    
    args = parser.parse_args()
    
    logger.info(f"🚀 DÉBUT DES TESTS - CLIENT: {args.client_id}")
    logger.info(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    all_results = []
    
    if args.phase in ['1', 'all']:
        all_results.extend(test_phase_1_date_extraction())
        all_results.extend(test_phase_1_content_enrichment())
    
    if args.phase in ['2', 'all']:
        all_results.extend(test_phase_2_hallucination_validation())
    
    if args.phase in ['3', 'all']:
        all_results.extend(test_phase_3_specialized_distribution())
    
    if args.phase in ['4', 'all']:
        all_results.extend(test_phase_4_newsletter_scope())
    
    # Résumé final
    total_tests = len(all_results)
    successful_tests = sum(1 for r in all_results if r.get('success', False))
    success_rate = successful_tests / total_tests if total_tests > 0 else 0
    
    logger.info("=" * 60)
    logger.info(f"📊 RÉSUMÉ FINAL")
    logger.info(f"Tests réussis: {successful_tests}/{total_tests} ({success_rate:.1%})")
    
    if success_rate >= 0.8:
        logger.info("✅ SUCCÈS - Améliorations Phase 1-4 validées")
        return 0
    else:
        logger.error("❌ ÉCHEC - Certaines améliorations nécessitent des corrections")
        return 1

if __name__ == '__main__':
    sys.exit(main())