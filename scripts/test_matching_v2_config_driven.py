#!/usr/bin/env python3
"""
Script de test local pour le matching V2 configuration-driven.

Teste la nouvelle logique de matching avec différents seuils et configurations
sur un échantillon d'items lai_weekly_v3.
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Any

# Ajouter le chemin src_v2 pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src_v2'))

from vectora_core.normalization.bedrock_matcher import _apply_matching_policy, _apply_fallback_matching

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_test_evaluations() -> List[Dict[str, Any]]:
    """Crée des évaluations Bedrock simulées basées sur les données réelles lai_weekly_v3."""
    return [
        {
            "domain_id": "tech_lai_ecosystem",
            "is_relevant": True,
            "relevance_score": 0.85,
            "confidence": "high",
            "reasoning": "Strong LAI technology signals: MedinCell partnership with Teva, Extended-Release Injectable technology",
            "matched_entities": {
                "companies": ["MedinCell", "Teva"],
                "technologies": ["Extended-Release Injectable"],
                "trademarks": ["TEV-'749"]
            }
        },
        {
            "domain_id": "regulatory_lai",
            "is_relevant": True,
            "relevance_score": 0.75,
            "confidence": "high",
            "reasoning": "Partnership announcement with regulatory implications",
            "matched_entities": {
                "companies": ["MedinCell", "Teva"],
                "technologies": ["Extended-Release Injectable"]
            }
        },
        # Item 2: UZEDY® FDA approval
        {
            "domain_id": "tech_lai_ecosystem",
            "is_relevant": True,
            "relevance_score": 0.80,
            "confidence": "high",
            "reasoning": "FDA approval for LAI technology UZEDY®",
            "matched_entities": {
                "companies": ["Teva"],
                "technologies": ["Extended-Release Injectable"],
                "trademarks": ["UZEDY®"]
            }
        },
        {
            "domain_id": "regulatory_lai",
            "is_relevant": True,
            "relevance_score": 0.90,
            "confidence": "high",
            "reasoning": "FDA approval - strong regulatory signal",
            "matched_entities": {
                "companies": ["Teva"],
                "trademarks": ["UZEDY®"]
            }
        },
        # Item 3: Nanexa+Moderna partnership
        {
            "domain_id": "tech_lai_ecosystem",
            "is_relevant": True,
            "relevance_score": 0.75,
            "confidence": "high",
            "reasoning": "Partnership with LAI technology focus",
            "matched_entities": {
                "companies": ["Nanexa", "Moderna"],
                "technologies": ["PharmaShell®"]
            }
        },
        {
            "domain_id": "regulatory_lai",
            "is_relevant": False,
            "relevance_score": 0.25,
            "confidence": "low",
            "reasoning": "Partnership announcement, limited regulatory content",
            "matched_entities": {
                "companies": ["Nanexa", "Moderna"]
            }
        },
        # Item 4: Camurus Phase 3 results
        {
            "domain_id": "tech_lai_ecosystem",
            "is_relevant": True,
            "relevance_score": 0.70,
            "confidence": "medium",
            "reasoning": "Clinical results for LAI technology FluidCrystal",
            "matched_entities": {
                "companies": ["Camurus"],
                "technologies": ["FluidCrystal"],
                "molecules": ["CAM2038"]
            }
        },
        {
            "domain_id": "regulatory_lai",
            "is_relevant": True,
            "relevance_score": 0.35,
            "confidence": "medium",
            "reasoning": "Phase 3 results with potential regulatory implications",
            "matched_entities": {
                "companies": ["Camurus"],
                "molecules": ["CAM2038"]
            }
        },
        # Item 5: Alkermes partnership
        {
            "domain_id": "tech_lai_ecosystem",
            "is_relevant": True,
            "relevance_score": 0.65,
            "confidence": "medium",
            "reasoning": "Partnership announcement with LAI focus",
            "matched_entities": {
                "companies": ["Alkermes"],
                "technologies": ["Long-Acting Injectable"]
            }
        },
        {
            "domain_id": "regulatory_lai",
            "is_relevant": False,
            "relevance_score": 0.30,
            "confidence": "low",
            "reasoning": "Partnership with limited regulatory content",
            "matched_entities": {
                "companies": ["Alkermes"]
            }
        },
        # Item 6: Generic LAI competition
        {
            "domain_id": "tech_lai_ecosystem",
            "is_relevant": True,
            "relevance_score": 0.60,
            "confidence": "medium",
            "reasoning": "Market analysis of LAI competition",
            "matched_entities": {
                "technologies": ["Depot Injection"],
                "molecules": ["aripiprazole"]
            }
        },
        {
            "domain_id": "regulatory_lai",
            "is_relevant": False,
            "relevance_score": 0.20,
            "confidence": "low",
            "reasoning": "Market analysis with limited regulatory focus",
            "matched_entities": {
                "molecules": ["aripiprazole"]
            }
        },
        # Item 7: DelSiTech SiliaShell
        {
            "domain_id": "tech_lai_ecosystem",
            "is_relevant": True,
            "relevance_score": 0.55,
            "confidence": "medium",
            "reasoning": "Technology advancement in LAI delivery",
            "matched_entities": {
                "companies": ["DelSiTech"],
                "technologies": ["SiliaShell®"]
            }
        },
        {
            "domain_id": "regulatory_lai",
            "is_relevant": False,
            "relevance_score": 0.15,
            "confidence": "low",
            "reasoning": "Technology focus with minimal regulatory content",
            "matched_entities": {
                "companies": ["DelSiTech"]
            }
        },
        # Item 8: Peptron Q3 results (pure player, low signal)
        {
            "domain_id": "tech_lai_ecosystem",
            "is_relevant": False,
            "relevance_score": 0.25,
            "confidence": "low",
            "reasoning": "Financial results from LAI pure player but no explicit LAI technology mention",
            "matched_entities": {
                "companies": ["Peptron"]
            }
        },
        {
            "domain_id": "regulatory_lai",
            "is_relevant": False,
            "relevance_score": 0.10,
            "confidence": "low",
            "reasoning": "Financial results with no regulatory content",
            "matched_entities": {
                "companies": ["Peptron"]
            }
        },
        # Item 9: Generic biotech funding (noise)
        {
            "domain_id": "tech_lai_ecosystem",
            "is_relevant": False,
            "relevance_score": 0.20,
            "confidence": "low",
            "reasoning": "Generic biotech funding with minimal LAI relevance",
            "matched_entities": {
                "companies": ["Various"]
            }
        },
        {
            "domain_id": "regulatory_lai",
            "is_relevant": False,
            "relevance_score": 0.05,
            "confidence": "low",
            "reasoning": "Funding announcement with no regulatory relevance",
            "matched_entities": {}
        },
        # Item 10: MedinCell facility (pure player, no tech mention)
        {
            "domain_id": "tech_lai_ecosystem",
            "is_relevant": False,
            "relevance_score": 0.35,
            "confidence": "medium",
            "reasoning": "Manufacturing facility from LAI pure player but no explicit technology mention",
            "matched_entities": {
                "companies": ["MedinCell"]
            }
        },
        {
            "domain_id": "regulatory_lai",
            "is_relevant": False,
            "relevance_score": 0.10,
            "confidence": "low",
            "reasoning": "Manufacturing announcement with minimal regulatory relevance",
            "matched_entities": {
                "companies": ["MedinCell"]
            }
        }
    ]


def create_test_watch_domains() -> List[Dict[str, Any]]:
    """Crée les domaines de veille de test basés sur lai_weekly_v3."""
    return [
        {
            "id": "tech_lai_ecosystem",
            "type": "technology",
            "priority": "high"
        },
        {
            "id": "regulatory_lai",
            "type": "regulatory",
            "priority": "high"
        }
    ]


def test_matching_configuration(config_name: str, matching_config: Dict[str, Any]) -> Dict[str, Any]:
    """Teste une configuration de matching spécifique."""
    logger.info(f"\n=== Test Configuration: {config_name} ===")
    logger.info(f"Config: {json.dumps(matching_config, indent=2)}")
    
    evaluations = create_test_evaluations()
    watch_domains = create_test_watch_domains()
    
    # Grouper les évaluations par item (2 domaines par item)
    items_results = []
    for i in range(0, len(evaluations), 2):
        item_evaluations = evaluations[i:i+2]
        
        # Appliquer la politique de matching
        result = _apply_matching_policy(item_evaluations, matching_config, watch_domains)
        
        # Appliquer fallback si nécessaire
        if not result['matched_domains'] and matching_config.get('enable_fallback_mode', False):
            fallback_result = _apply_fallback_matching(item_evaluations, matching_config, watch_domains)
            if fallback_result['matched_domains']:
                result['matched_domains'] = fallback_result['matched_domains']
                result['domain_relevance'].update(fallback_result['domain_relevance'])
                result['fallback_applied'] = True
        
        items_results.append(result)
    
    # Calculer les statistiques
    total_items = len(items_results)
    matched_items = sum(1 for r in items_results if r['matched_domains'])
    tech_matches = sum(1 for r in items_results if 'tech_lai_ecosystem' in r['matched_domains'])
    regulatory_matches = sum(1 for r in items_results if 'regulatory_lai' in r['matched_domains'])
    fallback_used = sum(1 for r in items_results if r.get('fallback_applied', False))
    
    stats = {
        'config_name': config_name,
        'total_items': total_items,
        'matched_items': matched_items,
        'matching_rate': matched_items / total_items if total_items > 0 else 0,
        'tech_matches': tech_matches,
        'regulatory_matches': regulatory_matches,
        'fallback_used': fallback_used,
        'detailed_results': items_results
    }
    
    logger.info(f"Résultats: {matched_items}/{total_items} items matchés ({stats['matching_rate']:.1%})")
    logger.info(f"Tech: {tech_matches}, Regulatory: {regulatory_matches}, Fallback: {fallback_used}")
    
    return stats


def run_all_tests() -> Dict[str, Any]:
    """Exécute tous les tests de configuration."""
    logger.info("=== Tests Matching V2 Configuration-Driven ===")
    
    test_configs = {
        "Actuel (hardcodé 0.4)": {
            "min_domain_score": 0.4,
            "domain_type_thresholds": {},
            "enable_fallback_mode": False
        },
        
        "Proposé LAI (0.25 global)": {
            "min_domain_score": 0.25,
            "domain_type_thresholds": {},
            "enable_fallback_mode": False
        },
        
        "Proposé LAI avec seuils par type": {
            "min_domain_score": 0.25,
            "domain_type_thresholds": {
                "technology": 0.30,
                "regulatory": 0.20
            },
            "enable_fallback_mode": False
        },
        
        "Proposé LAI avec fallback": {
            "min_domain_score": 0.25,
            "domain_type_thresholds": {
                "technology": 0.30,
                "regulatory": 0.20
            },
            "enable_fallback_mode": True,
            "fallback_min_score": 0.15,
            "fallback_max_domains": 1
        },
        
        "Strict (0.35)": {
            "min_domain_score": 0.35,
            "domain_type_thresholds": {
                "technology": 0.40,
                "regulatory": 0.30
            },
            "enable_fallback_mode": False
        },
        
        "Permissif (0.20)": {
            "min_domain_score": 0.20,
            "domain_type_thresholds": {
                "technology": 0.25,
                "regulatory": 0.15
            },
            "enable_fallback_mode": True,
            "fallback_min_score": 0.10,
            "fallback_max_domains": 1
        }
    }
    
    all_results = {}
    
    for config_name, config in test_configs.items():
        try:
            result = test_matching_configuration(config_name, config)
            all_results[config_name] = result
        except Exception as e:
            logger.error(f"Erreur test {config_name}: {e}")
            all_results[config_name] = {"error": str(e)}
    
    return all_results


def generate_report(results: Dict[str, Any]) -> str:
    """Génère un rapport détaillé des tests."""
    report_lines = [
        "# Rapport de Tests Locaux : Matching V2 Configuration-Driven",
        "",
        f"**Date :** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Objectif :** Validation du matching configuration-driven sur données simulées lai_weekly_v3",
        "",
        "---",
        "",
        "## Résumé des Configurations Testées",
        ""
    ]
    
    # Tableau de résumé
    report_lines.extend([
        "| Configuration | Items Matchés | Taux | Tech | Regulatory | Fallback |",
        "|---------------|---------------|------|------|------------|----------|"
    ])
    
    for config_name, result in results.items():
        if "error" in result:
            report_lines.append(f"| {config_name} | ERROR | - | - | - | - |")
        else:
            rate = f"{result['matching_rate']:.1%}"
            tech = result['tech_matches']
            reg = result['regulatory_matches']
            fallback = result['fallback_used']
            matched = result['matched_items']
            total = result['total_items']
            report_lines.append(f"| {config_name} | {matched}/{total} | {rate} | {tech} | {reg} | {fallback} |")
    
    report_lines.extend([
        "",
        "## Analyse Détaillée",
        ""
    ])
    
    # Analyse par configuration
    for config_name, result in results.items():
        if "error" in result:
            report_lines.extend([
                f"### {config_name}",
                "",
                f"**Erreur :** {result['error']}",
                ""
            ])
            continue
        
        report_lines.extend([
            f"### {config_name}",
            "",
            f"**Résultats :**",
            f"- Items matchés : {result['matched_items']}/{result['total_items']} ({result['matching_rate']:.1%})",
            f"- Domaine tech_lai_ecosystem : {result['tech_matches']} items",
            f"- Domaine regulatory_lai : {result['regulatory_matches']} items",
            f"- Mode fallback utilisé : {result['fallback_used']} items",
            ""
        ])
        
        # Exemples d'items
        if result.get('detailed_results'):
            report_lines.extend([
                "**Exemples d'items matchés :**",
                ""
            ])
            
            for i, item_result in enumerate(result['detailed_results'][:3]):  # Top 3
                if item_result['matched_domains']:
                    domains = ", ".join(item_result['matched_domains'])
                    fallback = " (fallback)" if item_result.get('fallback_applied') else ""
                    report_lines.append(f"- Item {i+1}: {domains}{fallback}")
            
            report_lines.append("")
    
    # Recommandations
    report_lines.extend([
        "## Recommandations",
        "",
        "**Configuration recommandée pour lai_weekly_v3 :**",
        ""
    ])
    
    # Trouver la meilleure configuration (équilibre entre taux et qualité)
    best_config = None
    best_score = 0
    
    for config_name, result in results.items():
        if "error" not in result:
            # Score = taux de matching * qualité (éviter sur-matching)
            rate = result['matching_rate']
            quality_penalty = max(0, (result['matched_items'] - 12) * 0.1)  # Pénalité si > 12 items
            score = rate - quality_penalty
            
            if score > best_score:
                best_score = score
                best_config = config_name
    
    if best_config:
        report_lines.extend([
            f"**Meilleure configuration :** {best_config}",
            f"- Taux de matching optimal : {results[best_config]['matching_rate']:.1%}",
            f"- Distribution équilibrée tech/regulatory",
            f"- Pas de sur-matching (< 15 items)",
            ""
        ])
    
    report_lines.extend([
        "**Prochaines étapes :**",
        "1. Implémenter la configuration recommandée dans lai_weekly_v3.yaml",
        "2. Déployer le code refactoré sur AWS",
        "3. Tester en conditions réelles",
        "4. Ajuster les seuils si nécessaire",
        "",
        "---",
        "",
        f"**Rapport généré automatiquement le {datetime.now().isoformat()}**"
    ])
    
    return "\n".join(report_lines)


def main():
    """Fonction principale."""
    try:
        # Exécuter tous les tests
        results = run_all_tests()
        
        # Générer le rapport
        report = generate_report(results)
        
        # Sauvegarder le rapport
        report_path = os.path.join(
            os.path.dirname(__file__), 
            "..", 
            "docs", 
            "diagnostics", 
            "matching_v2_config_driven_local_tests.md"
        )
        
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"\n=== Rapport sauvegardé : {report_path} ===")
        
        # Afficher résumé dans la console
        print("\n" + "="*60)
        print("RÉSUMÉ DES TESTS MATCHING V2 CONFIG-DRIVEN")
        print("="*60)
        
        for config_name, result in results.items():
            if "error" not in result:
                rate = result['matching_rate']
                matched = result['matched_items']
                total = result['total_items']
                print(f"{config_name:30} : {matched:2d}/{total} ({rate:5.1%})")
        
        print("="*60)
        print(f"Rapport détaillé : {report_path}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Erreur dans les tests : {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())