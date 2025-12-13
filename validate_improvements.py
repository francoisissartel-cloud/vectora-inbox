#!/usr/bin/env python3
"""
Script de validation des améliorations selon le plan d'amélioration Phase 5.
Teste les modifications apportées et compare avec les résultats précédents.
"""

import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImprovementValidator:
    """Validateur des améliorations apportées au système."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.canonical_path = self.project_root / "canonical"
        
    def validate_phase1_corrections(self) -> Dict[str, bool]:
        """Valide les corrections critiques de la Phase 1."""
        logger.info("=== VALIDATION PHASE 1: Corrections Critiques ===")
        
        results = {}
        
        # 1.1 Vérifier enrichissement technology_scopes
        tech_scopes_path = self.canonical_path / "scopes" / "technology_scopes.yaml"
        with open(tech_scopes_path, 'r', encoding='utf-8') as f:
            tech_scopes = yaml.safe_load(f)
        
        lai_keywords = tech_scopes.get('lai_keywords', {})
        tech_terms = lai_keywords.get('technology_terms_high_precision', [])
        
        required_terms = ["PharmaShell®", "SiliaShell®", "BEPO®", "LAI", "extended-release injectable", "long-acting injectable"]
        missing_terms = [term for term in required_terms if term not in tech_terms]
        
        results['technology_scopes_enriched'] = len(missing_terms) == 0
        if missing_terms:
            logger.error(f"Termes manquants dans technology_scopes: {missing_terms}")
        else:
            logger.info("✅ Technology scopes enrichis correctement")
        
        # 1.2 Vérifier UZEDY dans trademark_scopes
        trademark_scopes_path = self.canonical_path / "scopes" / "trademark_scopes.yaml"
        with open(trademark_scopes_path, 'r', encoding='utf-8') as f:
            trademark_scopes = yaml.safe_load(f)
        
        lai_trademarks = trademark_scopes.get('lai_trademarks_global', [])
        results['uzedy_in_trademarks'] = 'Uzedy' in lai_trademarks
        
        if results['uzedy_in_trademarks']:
            logger.info("✅ UZEDY présent dans lai_trademarks_global")
        else:
            logger.error("❌ UZEDY manquant dans lai_trademarks_global")
        
        # 1.3 Vérifier exclusions anti-LAI
        exclusion_scopes_path = self.canonical_path / "scopes" / "exclusion_scopes.yaml"
        with open(exclusion_scopes_path, 'r', encoding='utf-8') as f:
            exclusion_scopes = yaml.safe_load(f)
        
        anti_lai_routes = exclusion_scopes.get('anti_lai_routes', [])
        required_exclusions = ["oral tablet", "oral capsule", "oral drug", "oral medication"]
        missing_exclusions = [term for term in required_exclusions if term not in anti_lai_routes]
        
        results['anti_lai_exclusions_added'] = len(missing_exclusions) == 0
        if missing_exclusions:
            logger.error(f"Exclusions anti-LAI manquantes: {missing_exclusions}")
        else:
            logger.info("✅ Exclusions anti-LAI ajoutées correctement")
        
        # 1.4 Vérifier ajustements scoring
        scoring_rules_path = self.canonical_path / "scoring" / "scoring_rules.yaml"
        with open(scoring_rules_path, 'r', encoding='utf-8') as f:
            scoring_rules = yaml.safe_load(f)
        
        other_factors = scoring_rules.get('other_factors', {})
        
        # Vérifier pure_player_bonus réduit
        pure_player_bonus = other_factors.get('pure_player_bonus', 0)
        results['pure_player_bonus_reduced'] = pure_player_bonus == 1.5
        
        # Vérifier nouveaux bonus
        technology_bonus = other_factors.get('technology_bonus', 0)
        trademark_bonus = other_factors.get('trademark_bonus', 0)
        regulatory_bonus = other_factors.get('regulatory_bonus', 0)
        oral_route_penalty = other_factors.get('oral_route_penalty', 0)
        
        results['bonus_increased'] = (
            technology_bonus == 4.0 and 
            trademark_bonus == 5.0 and 
            regulatory_bonus == 6.0 and
            oral_route_penalty == -10
        )
        
        if results['bonus_increased']:
            logger.info("✅ Bonus signaux LAI augmentés et pénalité orale ajoutée")
        else:
            logger.error(f"❌ Problème avec les bonus: tech={technology_bonus}, trademark={trademark_bonus}, reg={regulatory_bonus}, oral_penalty={oral_route_penalty}")
        
        return results
    
    def validate_phase2_ingestion(self) -> Dict[str, bool]:
        """Valide les améliorations d'ingestion de la Phase 2."""
        logger.info("=== VALIDATION PHASE 2: Ingestion Sélective ===")
        
        results = {}
        
        # Vérifier profils d'ingestion mis à jour
        ingestion_profiles_path = self.canonical_path / "ingestion" / "ingestion_profiles.yaml"
        with open(ingestion_profiles_path, 'r', encoding='utf-8') as f:
            ingestion_profiles = yaml.safe_load(f)
        
        profiles = ingestion_profiles.get('profiles', {})
        
        # Vérifier corporate_pure_player_broad
        corporate_profile = profiles.get('corporate_pure_player_broad', {})
        exclusion_scopes = corporate_profile.get('signal_requirements', {}).get('exclusion_scopes', [])
        
        required_exclusions = [
            "exclusion_scopes.anti_lai_routes",
            "exclusion_scopes.hr_recruitment_terms",
            "exclusion_scopes.financial_reporting_terms"
        ]
        
        missing_exclusions = [exc for exc in required_exclusions if exc not in exclusion_scopes]
        results['corporate_profile_updated'] = len(missing_exclusions) == 0
        
        if results['corporate_profile_updated']:
            logger.info("✅ Profil corporate pure player mis à jour avec nouvelles exclusions")
        else:
            logger.error(f"❌ Exclusions manquantes dans profil corporate: {missing_exclusions}")
        
        # Vérifier press_technology_focused
        press_profile = profiles.get('press_technology_focused', {})
        sector_press_reqs = press_profile.get('signal_requirements', {}).get('sector_press_requirements')
        
        results['press_profile_updated'] = sector_press_reqs is not None
        if results['press_profile_updated']:
            logger.info("✅ Profil presse sectorielle mis à jour avec critères stricts")
        else:
            logger.error("❌ Profil presse sectorielle non mis à jour")
        
        return results
    
    def validate_phase3_matching(self) -> Dict[str, bool]:
        """Valide le matching contextuel de la Phase 3."""
        logger.info("=== VALIDATION PHASE 3: Matching Contextuel ===")
        
        results = {}
        
        # Vérifier règles de matching mises à jour
        matching_rules_path = self.canonical_path / "matching" / "domain_matching_rules.yaml"
        with open(matching_rules_path, 'r', encoding='utf-8') as f:
            matching_rules = yaml.safe_load(f)
        
        # Vérifier technology profile
        tech_profiles = matching_rules.get('technology_profiles', {})
        tech_complex = tech_profiles.get('technology_complex', {})
        entity_reqs = tech_complex.get('entity_requirements', {})
        sources = entity_reqs.get('sources', [])
        
        results['trademark_source_added'] = 'trademark' in sources
        if results['trademark_source_added']:
            logger.info("✅ Source trademark ajoutée aux entity requirements")
        else:
            logger.error("❌ Source trademark manquante dans entity requirements")
        
        # Vérifier pattern matching
        technology_rule = matching_rules.get('technology', {})
        pattern_matching = technology_rule.get('pattern_matching')
        
        results['pattern_matching_added'] = pattern_matching is not None
        if results['pattern_matching_added']:
            logger.info("✅ Pattern matching ajouté pour LAI")
        else:
            logger.error("❌ Pattern matching manquant")
        
        # Vérifier code matcher.py
        matcher_path = self.project_root / "src" / "vectora_core" / "matching" / "matcher.py"
        with open(matcher_path, 'r', encoding='utf-8') as f:
            matcher_code = f.read()
        
        results['contextual_matching_implemented'] = 'def contextual_matching(' in matcher_code
        if results['contextual_matching_implemented']:
            logger.info("✅ Fonction contextual_matching implémentée")
        else:
            logger.error("❌ Fonction contextual_matching manquante")
        
        return results
    
    def validate_phase4_scoring(self) -> Dict[str, bool]:
        """Valide le scoring contextuel de la Phase 4."""
        logger.info("=== VALIDATION PHASE 4: Scoring Contextuel ===")
        
        results = {}
        
        # Vérifier nouvelles règles de scoring
        scoring_rules_path = self.canonical_path / "scoring" / "scoring_rules.yaml"
        with open(scoring_rules_path, 'r', encoding='utf-8') as f:
            scoring_rules = yaml.safe_load(f)
        
        # Vérifier contextual_scoring
        contextual_scoring = scoring_rules.get('contextual_scoring')
        results['contextual_scoring_added'] = contextual_scoring is not None
        
        if contextual_scoring:
            pure_players = contextual_scoring.get('pure_players', {})
            context_multipliers = pure_players.get('context_multipliers', {})
            
            required_multipliers = ['regulatory_milestone', 'partnership_bigpharma', 'grant_funding', 'clinical_update']
            missing_multipliers = [m for m in required_multipliers if m not in context_multipliers]
            
            results['context_multipliers_complete'] = len(missing_multipliers) == 0
            if results['context_multipliers_complete']:
                logger.info("✅ Context multipliers complets pour pure players")
            else:
                logger.error(f"❌ Context multipliers manquants: {missing_multipliers}")
        
        # Vérifier contextual_penalties
        contextual_penalties = scoring_rules.get('contextual_penalties')
        results['contextual_penalties_added'] = contextual_penalties is not None
        
        if contextual_penalties:
            required_penalties = ['hr_content', 'financial_only', 'anti_lai_route']
            missing_penalties = [p for p in required_penalties if p not in contextual_penalties]
            
            results['penalties_complete'] = len(missing_penalties) == 0
            if results['penalties_complete']:
                logger.info("✅ Pénalités contextuelles complètes")
            else:
                logger.error(f"❌ Pénalités manquantes: {missing_penalties}")
        
        # Vérifier recency_bonuses
        recency_bonuses = scoring_rules.get('recency_bonuses')
        results['recency_bonuses_added'] = recency_bonuses is not None
        
        if recency_bonuses:
            logger.info("✅ Bonus récence ajoutés")
        
        # Vérifier code scorer.py
        scorer_path = self.project_root / "src" / "vectora_core" / "scoring" / "scorer.py"
        with open(scorer_path, 'r', encoding='utf-8') as f:
            scorer_code = f.read()
        
        results['contextual_scoring_implemented'] = 'def compute_contextual_score(' in scorer_code
        if results['contextual_scoring_implemented']:
            logger.info("✅ Fonction compute_contextual_score implémentée")
        else:
            logger.error("❌ Fonction compute_contextual_score manquante")
        
        return results
    
    def generate_validation_report(self) -> Dict[str, Any]:
        """Génère un rapport de validation complet."""
        logger.info("=== GÉNÉRATION RAPPORT DE VALIDATION ===")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'validation_results': {},
            'summary': {},
            'recommendations': []
        }
        
        # Valider chaque phase
        phase1_results = self.validate_phase1_corrections()
        phase2_results = self.validate_phase2_ingestion()
        phase3_results = self.validate_phase3_matching()
        phase4_results = self.validate_phase4_scoring()
        
        report['validation_results'] = {
            'phase1_corrections_critiques': phase1_results,
            'phase2_ingestion_selective': phase2_results,
            'phase3_matching_contextuel': phase3_results,
            'phase4_scoring_contextuel': phase4_results
        }
        
        # Calculer le résumé
        all_results = {**phase1_results, **phase2_results, **phase3_results, **phase4_results}
        total_checks = len(all_results)
        passed_checks = sum(1 for result in all_results.values() if result)
        
        report['summary'] = {
            'total_checks': total_checks,
            'passed_checks': passed_checks,
            'failed_checks': total_checks - passed_checks,
            'success_rate': round((passed_checks / total_checks) * 100, 2) if total_checks > 0 else 0,
            'overall_status': 'PASSED' if passed_checks == total_checks else 'FAILED'
        }
        
        # Générer recommandations
        if report['summary']['overall_status'] == 'PASSED':
            report['recommendations'] = [
                "✅ Toutes les validations sont passées avec succès",
                "✅ Les modifications peuvent être déployées sur AWS",
                "✅ Procéder au test complet avec génération de newsletter",
                "✅ Comparer avec les anciennes newsletters pour mesurer la progression"
            ]
        else:
            failed_checks = [check for check, result in all_results.items() if not result]
            report['recommendations'] = [
                f"❌ {len(failed_checks)} vérifications ont échoué",
                f"❌ Corriger les problèmes suivants: {', '.join(failed_checks)}",
                "❌ Ne pas déployer tant que toutes les validations ne passent pas",
                "❌ Revoir les modifications et relancer la validation"
            ]
        
        return report
    
    def save_validation_report(self, report: Dict[str, Any], output_path: str = None):
        """Sauvegarde le rapport de validation."""
        if output_path is None:
            output_path = self.project_root / "validation_report.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Rapport de validation sauvegardé: {output_path}")


def main():
    """Point d'entrée principal."""
    project_root = Path(__file__).parent
    validator = ImprovementValidator(str(project_root))
    
    # Générer le rapport de validation
    report = validator.generate_validation_report()
    
    # Sauvegarder le rapport
    validator.save_validation_report(report)
    
    # Afficher le résumé
    summary = report['summary']
    logger.info(f"\n=== RÉSUMÉ DE VALIDATION ===")
    logger.info(f"Status: {summary['overall_status']}")
    logger.info(f"Vérifications réussies: {summary['passed_checks']}/{summary['total_checks']} ({summary['success_rate']}%)")
    
    # Afficher les recommandations
    logger.info(f"\n=== RECOMMANDATIONS ===")
    for rec in report['recommendations']:
        logger.info(rec)
    
    # Code de sortie
    exit_code = 0 if summary['overall_status'] == 'PASSED' else 1
    return exit_code


if __name__ == "__main__":
    exit(main())