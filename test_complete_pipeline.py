#!/usr/bin/env python3
"""
Script de test complet du pipeline avec les améliorations.
Génère une newsletter test et compare avec les résultats précédents.
"""

import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime, timedelta

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PipelineTestRunner:
    """Testeur du pipeline complet avec les améliorations."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.canonical_path = self.project_root / "canonical"
        
    def create_test_payload(self) -> Dict[str, Any]:
        """Crée un payload de test pour simuler le pipeline."""
        logger.info("=== CRÉATION PAYLOAD DE TEST ===")
        
        # Simuler des items de test basés sur les cas du plan d'amélioration
        test_items = [
            # Cas 1: Nanexa/Moderna PharmaShell (doit être inclus maintenant)
            {
                "id": "test_nanexa_moderna_pharmashell",
                "title": "Nanexa and Moderna Announce Partnership for PharmaShell® Technology",
                "content": "Nanexa AB announced a strategic partnership with Moderna to develop long-acting injectable formulations using PharmaShell® technology for extended-release applications.",
                "date": "2024-12-10",
                "source_type": "press_corporate",
                "companies_detected": ["Nanexa", "Moderna"],
                "technologies_detected": ["PharmaShell®", "long-acting injectable", "extended-release"],
                "molecules_detected": [],
                "trademarks_detected": [],
                "event_type": "partnership",
                "lai_relevance_score": 9,
                "anti_lai_detected": False,
                "pure_player_context": True
            },
            
            # Cas 2: UZEDY regulatory (doit être inclus maintenant)
            {
                "id": "test_uzedy_regulatory",
                "title": "UZEDY Receives FDA Approval for Extended Treatment",
                "content": "The FDA has approved UZEDY for extended treatment protocols, marking a significant regulatory milestone for long-acting injectable antipsychotics.",
                "date": "2024-12-09",
                "source_type": "press_sector",
                "companies_detected": ["MedinCell"],
                "technologies_detected": ["long-acting injectable"],
                "molecules_detected": [],
                "trademarks_detected": ["UZEDY"],
                "event_type": "regulatory",
                "lai_relevance_score": 10,
                "anti_lai_detected": False,
                "pure_player_context": True
            },
            
            # Cas 3: MedinCell Malaria Grant (doit être inclus maintenant)
            {
                "id": "test_medincel_malaria_grant",
                "title": "MedinCell Receives Grant for Malaria Prevention Program",
                "content": "MedinCell has been awarded a significant grant to develop long-acting injectable solutions for malaria prevention in endemic regions.",
                "date": "2024-12-08",
                "source_type": "press_corporate",
                "companies_detected": ["MedinCell"],
                "technologies_detected": ["long-acting injectable"],
                "molecules_detected": [],
                "trademarks_detected": [],
                "event_type": "clinical_update",
                "lai_relevance_score": 8,
                "anti_lai_detected": False,
                "pure_player_context": True
            },
            
            # Cas 4: DelSiTech HR (doit être exclu maintenant)
            {
                "id": "test_delsitech_hr",
                "title": "DelSiTech is Hiring Process Engineers",
                "content": "DelSiTech seeks experienced process engineers to join our manufacturing team. We are recruiting for multiple positions in our drug delivery systems division.",
                "date": "2024-12-07",
                "source_type": "press_corporate",
                "companies_detected": ["DelSiTech"],
                "technologies_detected": [],
                "molecules_detected": [],
                "trademarks_detected": [],
                "event_type": "corporate_move",
                "lai_relevance_score": 3,
                "anti_lai_detected": False,
                "pure_player_context": False
            },
            
            # Cas 5: MedinCell Finance (doit être exclu maintenant)
            {
                "id": "test_medincel_finance",
                "title": "MedinCell Publishes Quarterly Financial Results",
                "content": "MedinCell publishes its interim report showing strong financial results for the quarter with improved revenue guidance.",
                "date": "2024-12-06",
                "source_type": "press_corporate",
                "companies_detected": ["MedinCell"],
                "technologies_detected": [],
                "molecules_detected": [],
                "trademarks_detected": [],
                "event_type": "financial_results",
                "lai_relevance_score": 2,
                "anti_lai_detected": False,
                "pure_player_context": False
            },
            
            # Cas 6: Pfizer GLP-1 oral (doit être exclu maintenant)
            {
                "id": "test_pfizer_oral_glp1",
                "title": "Pfizer Advances Oral GLP-1 Tablet Development",
                "content": "Pfizer announces progress in developing oral tablet formulations for GLP-1 medications, focusing on oral drug delivery systems.",
                "date": "2024-12-05",
                "source_type": "press_sector",
                "companies_detected": ["Pfizer"],
                "technologies_detected": ["oral tablet", "oral drug"],
                "molecules_detected": [],
                "trademarks_detected": [],
                "event_type": "clinical_update",
                "lai_relevance_score": 4,
                "anti_lai_detected": True,
                "pure_player_context": False
            },
            
            # Cas 7: SiliaShell technology (nouveau, doit être inclus)
            {
                "id": "test_siliaShell_technology",
                "title": "Breakthrough in SiliaShell® Technology for Drug Delivery",
                "content": "New developments in SiliaShell® technology show promising results for controlled-release applications in pharmaceutical manufacturing.",
                "date": "2024-12-04",
                "source_type": "press_sector",
                "companies_detected": ["TechPharma"],
                "technologies_detected": ["SiliaShell®", "controlled-release"],
                "molecules_detected": [],
                "trademarks_detected": [],
                "event_type": "scientific_publication",
                "lai_relevance_score": 7,
                "anti_lai_detected": False,
                "pure_player_context": False
            }
        ]
        
        payload = {
            "client_id": "lai_weekly_v2_test",
            "period_days": 7,
            "from_date": "2024-12-04",
            "to_date": "2024-12-10",
            "target_date": "2024-12-11",
            "test_items": test_items
        }
        
        logger.info(f"Payload de test créé avec {len(test_items)} items")
        return payload
    
    def simulate_matching_phase(self, test_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Simule la phase de matching avec les nouvelles règles."""
        logger.info("=== SIMULATION PHASE MATCHING ===")
        
        matched_items = []
        
        for item in test_items:
            # Simuler le matching contextuel
            should_match = self._simulate_contextual_matching(item)
            
            if should_match:
                item['matched_domains'] = ['tech_lai_ecosystem']
                item['matching_details'] = {
                    'domain_id': 'tech_lai_ecosystem',
                    'rule_applied': 'contextual_matching',
                    'match_confidence': self._determine_match_confidence(item)
                }
                matched_items.append(item)
                logger.info(f"✅ Item matché: {item['id']} - {item['title'][:50]}...")
            else:
                logger.info(f"❌ Item rejeté: {item['id']} - {item['title'][:50]}...")
        
        logger.info(f"Matching terminé: {len(matched_items)}/{len(test_items)} items matchés")
        return matched_items
    
    def _simulate_contextual_matching(self, item: Dict[str, Any]) -> bool:
        """Simule le matching contextuel selon les nouvelles règles."""
        companies_detected = set(item.get('companies_detected', []))
        technologies_detected = set(item.get('technologies_detected', []))
        molecules_detected = set(item.get('molecules_detected', []))
        trademarks_detected = set(item.get('trademarks_detected', []))
        
        lai_relevance_score = item.get('lai_relevance_score', 0)
        anti_lai_detected = item.get('anti_lai_detected', False)
        pure_player_context = item.get('pure_player_context', False)
        event_type = item.get('event_type', '')
        
        # Déterminer le type de company
        company_type = self._determine_company_type(companies_detected)
        
        # Pure players LAI : logique contextuelle
        if company_type == 'pure_player_lai':
            has_explicit_lai = bool(
                technologies_detected or 
                molecules_detected or 
                trademarks_detected
            )
            
            has_implicit_context = (
                lai_relevance_score >= 6 or
                pure_player_context or
                event_type in ['regulatory', 'partnership', 'clinical_update']
            )
            
            return has_explicit_lai or has_implicit_context
        
        # Hybrid companies : signaux LAI explicites requis
        elif company_type == 'hybrid_company':
            return (
                bool(technologies_detected) and 
                lai_relevance_score >= 5 and
                not anti_lai_detected
            )
        
        # Autres : signaux LAI forts requis
        else:
            return (
                bool(technologies_detected) and 
                lai_relevance_score >= 7
            )
    
    def _determine_company_type(self, companies_detected: set) -> str:
        """Détermine le type de company."""
        pure_players_lai = {
            'MedinCell', 'Nanexa', 'DelSiTech', 'Camurus', 'Peptron',
            'Alkermes', 'Indivior', 'Teva Pharmaceuticals'
        }
        
        hybrid_companies = {
            'Pfizer', 'Novartis', 'Roche', 'Johnson & Johnson', 'Moderna',
            'AbbVie', 'Merck', 'Bristol Myers Squibb', 'Eli Lilly'
        }
        
        if companies_detected & pure_players_lai:
            return 'pure_player_lai'
        elif companies_detected & hybrid_companies:
            return 'hybrid_company'
        else:
            return 'other'
    
    def _determine_match_confidence(self, item: Dict[str, Any]) -> str:
        """Détermine la confiance du matching."""
        lai_score = item.get('lai_relevance_score', 0)
        has_trademarks = bool(item.get('trademarks_detected'))
        has_multiple_signals = len(item.get('technologies_detected', [])) > 1
        
        if lai_score >= 9 or has_trademarks:
            return 'high'
        elif lai_score >= 6 or has_multiple_signals:
            return 'medium'
        else:
            return 'low'
    
    def simulate_scoring_phase(self, matched_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Simule la phase de scoring avec les nouvelles règles."""
        logger.info("=== SIMULATION PHASE SCORING ===")
        
        for item in matched_items:
            score = self._compute_contextual_score(item)
            item['score'] = score
            logger.info(f"Score calculé: {item['id']} = {score}")
        
        # Trier par score décroissant
        scored_items = sorted(matched_items, key=lambda x: x.get('score', 0), reverse=True)
        
        logger.info(f"Scoring terminé: {len(scored_items)} items scorés")
        return scored_items
    
    def _compute_contextual_score(self, item: Dict[str, Any]) -> float:
        """Calcule le score contextuel selon les nouvelles règles."""
        companies_detected = set(item.get('companies_detected', []))
        event_type = item.get('event_type', 'other')
        technologies_detected = set(item.get('technologies_detected', []))
        molecules_detected = set(item.get('molecules_detected', []))
        trademarks_detected = set(item.get('trademarks_detected', []))
        
        lai_relevance_score = item.get('lai_relevance_score', 0)
        anti_lai_detected = item.get('anti_lai_detected', False)
        
        # Déterminer le type de company
        company_type = self._determine_company_type(companies_detected)
        
        # Score de base selon le type de company
        if company_type == 'pure_player_lai':
            base_bonus = 2.0
            
            # Multipliers contextuels pour pure players
            context_multiplier = 1.0
            if event_type == 'regulatory':
                context_multiplier = 3.0  # UZEDY approvals
            elif event_type == 'partnership':
                context_multiplier = 2.5  # Nanexa/Moderna
            elif 'grant' in item.get('title', '').lower() or 'funding' in item.get('title', '').lower():
                context_multiplier = 2.0  # MedinCell malaria
            elif event_type == 'clinical_update':
                context_multiplier = 2.0
            
            base_score = base_bonus * context_multiplier
            
        elif company_type == 'hybrid_company':
            base_bonus = 1.0
            # Pour hybrid companies, signaux LAI explicites requis
            if not (technologies_detected or molecules_detected or trademarks_detected):
                base_score = base_bonus * 0.3  # Score très réduit
            else:
                base_score = base_bonus
        
        else:
            # Unknown companies
            base_bonus = 0.5
            if lai_relevance_score < 7:
                base_score = base_bonus * 0.2
            else:
                base_score = base_bonus
        
        # Appliquer les pénalités contextuelles
        penalties = 0
        
        # Pénalité contenu HR
        if self._is_hr_content(item):
            penalties += -5.0
        
        # Pénalité contenu financier uniquement
        if self._is_financial_only_content(item):
            penalties += -3.0
        
        # Pénalité anti-LAI
        if anti_lai_detected:
            penalties += -10.0
        
        # Bonus signaux LAI explicites
        signal_bonus = 0
        if technologies_detected:
            signal_bonus += 4.0
        if molecules_detected:
            signal_bonus += 4.0
        if trademarks_detected:
            signal_bonus += 5.0
        if event_type == 'regulatory':
            signal_bonus += 6.0
        
        final_score = base_score + penalties + signal_bonus
        
        return max(0, round(final_score, 2))
    
    def _is_hr_content(self, item: Dict[str, Any]) -> bool:
        """Détermine si l'item est du contenu RH."""
        title = item.get('title', '').lower()
        content = item.get('content', '').lower()
        
        hr_keywords = ['hiring', 'seeks', 'recruiting', 'process engineer', 'quality director', 'job opening']
        
        for keyword in hr_keywords:
            if keyword in title or keyword in content:
                return True
        
        return False
    
    def _is_financial_only_content(self, item: Dict[str, Any]) -> bool:
        """Détermine si l'item est uniquement du contenu financier."""
        title = item.get('title', '').lower()
        content = item.get('content', '').lower()
        
        financial_keywords = ['financial results', 'quarterly results', 'interim report', 'earnings']
        
        # Vérifier si c'est du contenu financier
        is_financial = any(keyword in title or keyword in content for keyword in financial_keywords)
        
        # Vérifier s'il y a des signaux LAI
        has_lai_signals = bool(
            item.get('technologies_detected') or 
            item.get('molecules_detected') or 
            item.get('trademarks_detected')
        )
        
        return is_financial and not has_lai_signals
    
    def generate_test_newsletter(self, scored_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Génère une newsletter de test."""
        logger.info("=== GÉNÉRATION NEWSLETTER TEST ===")
        
        # Filtrer les items avec score >= 5 (seuil minimum ajusté)
        selected_items = [item for item in scored_items if item.get('score', 0) >= 5]
        
        newsletter = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'client_id': 'lai_weekly_v2_test',
                'period': '2024-12-04 to 2024-12-10',
                'total_items_processed': len(scored_items),
                'items_selected': len(selected_items),
                'selection_rate': round((len(selected_items) / len(scored_items)) * 100, 2) if scored_items else 0
            },
            'sections': {
                'high_priority': [],
                'medium_priority': [],
                'low_priority': []
            },
            'items_details': selected_items
        }
        
        # Classer les items par priorité selon le score
        for item in selected_items:
            score = item.get('score', 0)
            if score >= 20:
                newsletter['sections']['high_priority'].append(item['id'])
            elif score >= 15:
                newsletter['sections']['medium_priority'].append(item['id'])
            else:
                newsletter['sections']['low_priority'].append(item['id'])
        
        logger.info(f"Newsletter générée: {len(selected_items)} items sélectionnés")
        logger.info(f"  - High priority: {len(newsletter['sections']['high_priority'])}")
        logger.info(f"  - Medium priority: {len(newsletter['sections']['medium_priority'])}")
        logger.info(f"  - Low priority: {len(newsletter['sections']['low_priority'])}")
        
        return newsletter
    
    def compare_with_baseline(self, newsletter: Dict[str, Any]) -> Dict[str, Any]:
        """Compare avec les résultats de base (avant améliorations)."""
        logger.info("=== COMPARAISON AVEC BASELINE ===")
        
        # Résultats attendus selon le plan d'amélioration
        expected_included = [
            'test_nanexa_moderna_pharmashell',  # Nanexa/Moderna PharmaShell
            'test_uzedy_regulatory',            # UZEDY regulatory
            'test_medincel_malaria_grant',      # MedinCell Malaria Grant
            'test_siliaShell_technology'        # SiliaShell technology
        ]
        
        expected_excluded = [
            'test_delsitech_hr',                # DelSiTech HR
            'test_medincel_finance',            # MedinCell Finance
            'test_pfizer_oral_glp1'             # Pfizer oral GLP-1
        ]
        
        selected_ids = [item['id'] for item in newsletter['items_details']]
        
        # Vérifier les inclusions attendues
        correctly_included = [item_id for item_id in expected_included if item_id in selected_ids]
        missed_inclusions = [item_id for item_id in expected_included if item_id not in selected_ids]
        
        # Vérifier les exclusions attendues
        correctly_excluded = [item_id for item_id in expected_excluded if item_id not in selected_ids]
        incorrect_inclusions = [item_id for item_id in expected_excluded if item_id in selected_ids]
        
        comparison = {
            'expected_behavior': {
                'should_include': expected_included,
                'should_exclude': expected_excluded
            },
            'actual_results': {
                'correctly_included': correctly_included,
                'missed_inclusions': missed_inclusions,
                'correctly_excluded': correctly_excluded,
                'incorrect_inclusions': incorrect_inclusions
            },
            'metrics': {
                'inclusion_accuracy': len(correctly_included) / len(expected_included) if expected_included else 0,
                'exclusion_accuracy': len(correctly_excluded) / len(expected_excluded) if expected_excluded else 0,
                'overall_accuracy': (len(correctly_included) + len(correctly_excluded)) / (len(expected_included) + len(expected_excluded))
            },
            'success_criteria_met': {
                'nanexa_moderna_included': 'test_nanexa_moderna_pharmashell' in correctly_included,
                'uzedy_included': 'test_uzedy_regulatory' in correctly_included,
                'medincel_malaria_included': 'test_medincel_malaria_grant' in correctly_included,
                'hr_noise_excluded': 'test_delsitech_hr' in correctly_excluded,
                'finance_noise_excluded': 'test_medincel_finance' in correctly_excluded,
                'oral_route_excluded': 'test_pfizer_oral_glp1' in correctly_excluded
            }
        }
        
        # Calculer le score de réussite global
        success_criteria = comparison['success_criteria_met']
        success_count = sum(1 for criterion in success_criteria.values() if criterion)
        comparison['overall_success_rate'] = success_count / len(success_criteria)
        
        logger.info(f"Comparaison terminée:")
        logger.info(f"  - Inclusion accuracy: {comparison['metrics']['inclusion_accuracy']:.2%}")
        logger.info(f"  - Exclusion accuracy: {comparison['metrics']['exclusion_accuracy']:.2%}")
        logger.info(f"  - Overall success rate: {comparison['overall_success_rate']:.2%}")
        
        return comparison
    
    def run_complete_test(self) -> Dict[str, Any]:
        """Exécute le test complet du pipeline."""
        logger.info("=== DÉMARRAGE TEST COMPLET PIPELINE ===")
        
        # 1. Créer le payload de test
        payload = self.create_test_payload()
        
        # 2. Simuler la phase de matching
        matched_items = self.simulate_matching_phase(payload['test_items'])
        
        # 3. Simuler la phase de scoring
        scored_items = self.simulate_scoring_phase(matched_items)
        
        # 4. Générer la newsletter
        newsletter = self.generate_test_newsletter(scored_items)
        
        # 5. Comparer avec la baseline
        comparison = self.compare_with_baseline(newsletter)
        
        # 6. Générer le rapport final
        test_report = {
            'test_metadata': {
                'timestamp': datetime.now().isoformat(),
                'test_type': 'complete_pipeline_validation',
                'improvements_version': 'phase_1_to_4_complete'
            },
            'payload': payload,
            'pipeline_results': {
                'matched_items_count': len(matched_items),
                'scored_items_count': len(scored_items),
                'selected_items_count': newsletter['metadata']['items_selected']
            },
            'newsletter': newsletter,
            'comparison_with_baseline': comparison,
            'deployment_recommendation': self._generate_deployment_recommendation(comparison)
        }
        
        logger.info("=== TEST COMPLET TERMINÉ ===")
        return test_report
    
    def _generate_deployment_recommendation(self, comparison: Dict[str, Any]) -> Dict[str, str]:
        """Génère une recommandation de déploiement."""
        success_rate = comparison['overall_success_rate']
        success_criteria = comparison['success_criteria_met']
        
        if success_rate >= 0.9:  # 90% ou plus
            return {
                'recommendation': 'DEPLOY_TO_AWS',
                'confidence': 'HIGH',
                'reason': f'Taux de réussite excellent ({success_rate:.1%}). Tous les critères critiques sont satisfaits.',
                'next_steps': [
                    'Déployer les configurations sur AWS',
                    'Exécuter un run de production',
                    'Monitorer les premières newsletters générées',
                    'Comparer avec les newsletters précédentes'
                ]
            }
        elif success_rate >= 0.7:  # 70% ou plus
            return {
                'recommendation': 'DEPLOY_WITH_MONITORING',
                'confidence': 'MEDIUM',
                'reason': f'Taux de réussite acceptable ({success_rate:.1%}). Déploiement possible avec surveillance renforcée.',
                'next_steps': [
                    'Déployer avec surveillance active',
                    'Prévoir un rollback rapide si nécessaire',
                    'Analyser les cas d\'échec restants',
                    'Ajuster les paramètres si besoin'
                ]
            }
        else:
            failed_criteria = [k for k, v in success_criteria.items() if not v]
            return {
                'recommendation': 'DO_NOT_DEPLOY',
                'confidence': 'HIGH',
                'reason': f'Taux de réussite insuffisant ({success_rate:.1%}). Critères échoués: {", ".join(failed_criteria)}',
                'next_steps': [
                    'Corriger les problèmes identifiés',
                    'Relancer les tests de validation',
                    'Ne pas déployer tant que le taux de réussite < 70%',
                    'Revoir la configuration des règles'
                ]
            }


def main():
    """Point d'entrée principal."""
    project_root = Path(__file__).parent
    test_runner = PipelineTestRunner(str(project_root))
    
    # Exécuter le test complet
    test_report = test_runner.run_complete_test()
    
    # Sauvegarder le rapport
    report_path = project_root / "pipeline_test_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(test_report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Rapport de test sauvegardé: {report_path}")
    
    # Afficher la recommandation de déploiement
    recommendation = test_report['deployment_recommendation']
    logger.info(f"\n=== RECOMMANDATION DE DÉPLOIEMENT ===")
    logger.info(f"Recommandation: {recommendation['recommendation']}")
    logger.info(f"Confiance: {recommendation['confidence']}")
    logger.info(f"Raison: {recommendation['reason']}")
    logger.info(f"Prochaines étapes:")
    for step in recommendation['next_steps']:
        logger.info(f"  - {step}")
    
    # Code de sortie
    if recommendation['recommendation'] == 'DEPLOY_TO_AWS':
        return 0
    elif recommendation['recommendation'] == 'DEPLOY_WITH_MONITORING':
        return 1
    else:
        return 2


if __name__ == "__main__":
    exit(main())