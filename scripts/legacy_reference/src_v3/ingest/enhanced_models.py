"""
Enhanced Models V3 - Extensions pour observabilité complète

Ajoute les métriques business, coûts, et traçabilité avancée
pour le pilotage et l'analyse des runs d'ingestion.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from .models import RunManifest, SourceReport, StructuredItem


@dataclass
class EnhancedRunManifest(RunManifest):
    """
    Manifest enrichi avec métriques business et coûts.
    
    Ajoute toutes les informations nécessaires pour le pilotage :
    - Coûts estimés (Lambda, S3, réseau)
    - Métriques business (taux de succès, qualité)
    - Bouquets activés et leur contribution
    - Analyse comparative vs runs précédents
    """
    
    # Informations de configuration
    bouquets_activated: List[str] = field(default_factory=list)
    sources_requested: List[str] = field(default_factory=list)
    sources_skipped_reasons: Dict[str, str] = field(default_factory=dict)
    
    # Métriques business
    business_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Coûts estimés
    estimated_costs: Dict[str, float] = field(default_factory=dict)
    
    # Comparaison avec runs précédents
    comparison_metrics: Optional[Dict[str, Any]] = None
    
    def calculate_business_metrics(self, final_items: List[StructuredItem], 
                                 rejected_items: List[StructuredItem]) -> Dict[str, Any]:
        """
        Calcule les métriques business du run.
        
        Returns:
            Dictionnaire avec toutes les métriques business
        """
        total_items = len(final_items) + len(rejected_items)
        
        # Taux de succès global
        success_rate = len(final_items) / max(total_items, 1)
        
        # Analyse par source
        source_performance = {}
        for report in self.source_reports:
            if report.items_found > 0:
                source_performance[report.source_key] = {
                    "success_rate": report.items_passed_filters / report.items_found,
                    "items_per_second": report.items_found / max(report.fetch_time_seconds + report.parse_time_seconds, 1),
                    "quality_score": report.avg_date_confidence,
                    "contribution_pct": (report.items_passed_filters / max(len(final_items), 1)) * 100
                }
        
        # Analyse des rejets par filtre
        rejection_breakdown = self._analyze_rejection_patterns(rejected_items)
        
        # Efficacité des bouquets
        bouquet_efficiency = self._calculate_bouquet_efficiency()
        
        return {
            "success_rate": success_rate,
            "items_per_minute": len(final_items) / max(self.get_total_duration_seconds() / 60, 1),
            "avg_quality_score": sum(r.avg_date_confidence for r in self.source_reports if r.avg_date_confidence > 0) / max(len(self.source_reports), 1),
            "source_performance": source_performance,
            "rejection_breakdown": rejection_breakdown,
            "bouquet_efficiency": bouquet_efficiency,
            "top_contributors": self._get_top_contributors(final_items),
            "quality_distribution": self._get_quality_distribution()
        }
    
    def calculate_estimated_costs(self) -> Dict[str, float]:
        """
        Estime les coûts du run (Lambda, S3, réseau).
        
        Returns:
            Dictionnaire avec coûts estimés en USD
        """
        duration_minutes = self.get_total_duration_seconds() / 60
        
        # Coût Lambda (512MB, durée)
        lambda_cost = duration_minutes * 0.0000083334  # $0.0000083334 per GB-second
        
        # Coût S3 (stockage + requêtes)
        total_data_mb = sum(len(json.dumps(item.__dict__)) for item in self._get_all_items()) / (1024 * 1024)
        s3_storage_cost = total_data_mb * 0.000023  # $0.023 per GB/month (prorated)
        s3_requests_cost = len(self.source_reports) * 0.0004 / 1000  # $0.0004 per 1000 requests
        
        # Coût réseau (estimation basée sur le nombre de requêtes)
        network_requests = sum(1 + (report.items_found if 'fetch' in report.ingestion_profile_used else 0) 
                             for report in self.source_reports)
        network_cost = network_requests * 0.00001  # Estimation
        
        total_cost = lambda_cost + s3_storage_cost + s3_requests_cost + network_cost
        
        return {
            "lambda_execution": round(lambda_cost, 6),
            "s3_storage": round(s3_storage_cost, 6),
            "s3_requests": round(s3_requests_cost, 6),
            "network": round(network_cost, 6),
            "total": round(total_cost, 6),
            "cost_per_item": round(total_cost / max(len(self._get_final_items()), 1), 6)
        }
    
    def _analyze_rejection_patterns(self, rejected_items: List[StructuredItem]) -> Dict[str, Any]:
        """Analyse les patterns de rejet pour identifier les optimisations possibles"""
        
        patterns = {
            "by_filter": {"period": 0, "exclusion": 0, "lai_keywords": 0, "validation": 0},
            "by_source": {},
            "by_actor_type": {},
            "common_exclusion_terms": {},
            "missing_lai_keywords": []
        }
        
        for item in rejected_items:
            reason = item.get_rejection_reason()
            if not reason:
                continue
                
            # Par filtre
            if "period_filter" in reason:
                patterns["by_filter"]["period"] += 1
            elif "exclusion_filter" in reason:
                patterns["by_filter"]["exclusion"] += 1
                # Extraire le terme d'exclusion
                if ":" in reason:
                    term = reason.split(":")[-1].strip()
                    patterns["common_exclusion_terms"][term] = patterns["common_exclusion_terms"].get(term, 0) + 1
            elif "lai_keyword_filter" in reason:
                patterns["by_filter"]["lai_keywords"] += 1
            else:
                patterns["by_filter"]["validation"] += 1
            
            # Par source
            source = item.source_key
            if source not in patterns["by_source"]:
                patterns["by_source"][source] = {"total": 0, "reasons": {}}
            patterns["by_source"][source]["total"] += 1
            patterns["by_source"][source]["reasons"][reason] = patterns["by_source"][source]["reasons"].get(reason, 0) + 1
            
            # Par actor_type
            actor_type = item.actor_type
            patterns["by_actor_type"][actor_type] = patterns["by_actor_type"].get(actor_type, 0) + 1
        
        return patterns
    
    def _calculate_bouquet_efficiency(self) -> Dict[str, Any]:
        """Calcule l'efficacité de chaque bouquet activé"""
        
        efficiency = {}
        
        for bouquet in self.bouquets_activated:
            # Sources du bouquet (à récupérer depuis la config)
            bouquet_sources = [r for r in self.source_reports if r.source_key.startswith(bouquet)]
            
            if bouquet_sources:
                total_items = sum(r.items_passed_filters for r in bouquet_sources)
                total_time = sum(r.fetch_time_seconds + r.parse_time_seconds for r in bouquet_sources)
                avg_quality = sum(r.avg_date_confidence for r in bouquet_sources) / len(bouquet_sources)
                
                efficiency[bouquet] = {
                    "sources_count": len(bouquet_sources),
                    "total_items": total_items,
                    "items_per_minute": total_items / max(total_time / 60, 1),
                    "avg_quality": avg_quality,
                    "cost_efficiency": total_items / max(total_time * 0.0000083334, 0.000001)  # items per dollar
                }
        
        return efficiency
    
    def _get_top_contributors(self, final_items: List[StructuredItem]) -> List[Dict[str, Any]]:
        """Identifie les sources qui contribuent le plus au résultat final"""
        
        source_contributions = {}
        for item in final_items:
            source = item.source_key
            if source not in source_contributions:
                source_contributions[source] = {"count": 0, "quality_sum": 0}
            source_contributions[source]["count"] += 1
            # Ajouter la qualité si disponible
            date_confidence = item.date_extraction.get("confidence", 0)
            source_contributions[source]["quality_sum"] += date_confidence
        
        # Calculer le score de contribution (quantité × qualité)
        contributors = []
        for source, data in source_contributions.items():
            avg_quality = data["quality_sum"] / data["count"] if data["count"] > 0 else 0
            contribution_score = data["count"] * avg_quality
            contributors.append({
                "source": source,
                "items": data["count"],
                "avg_quality": avg_quality,
                "contribution_score": contribution_score,
                "percentage": (data["count"] / len(final_items)) * 100
            })
        
        return sorted(contributors, key=lambda x: x["contribution_score"], reverse=True)[:5]
    
    def _get_quality_distribution(self) -> Dict[str, int]:
        """Distribution de la qualité des sources"""
        
        distribution = {"excellent": 0, "good": 0, "fair": 0, "poor": 0}
        
        for report in self.source_reports:
            confidence = report.avg_date_confidence
            if confidence >= 0.9:
                distribution["excellent"] += 1
            elif confidence >= 0.7:
                distribution["good"] += 1
            elif confidence >= 0.5:
                distribution["fair"] += 1
            else:
                distribution["poor"] += 1
        
        return distribution
    
    def _get_all_items(self) -> List[StructuredItem]:
        """Récupère tous les items (acceptés + rejetés) - à implémenter selon le contexte"""
        # Cette méthode devra être appelée avec les items en paramètre
        return []
    
    def _get_final_items(self) -> List[StructuredItem]:
        """Récupère les items finaux - à implémenter selon le contexte"""
        # Cette méthode devra être appelée avec les items en paramètre
        return []
    
    def generate_executive_summary(self) -> str:
        """
        Génère un résumé exécutif pour le pilotage business.
        
        Returns:
            Résumé exécutif en texte
        """
        if not self.business_metrics:
            return "Business metrics not calculated"
        
        duration_min = self.get_total_duration_seconds() / 60
        success_rate = self.business_metrics.get("success_rate", 0)
        total_cost = self.estimated_costs.get("total", 0)
        items_count = self.stats.get("items_funnel", {}).get("final", 0)
        
        summary_parts = [
            f"🎯 **{self.client_id}** - {self.ingestion_mode.upper()} mode",
            f"⏱️ Duration: {duration_min:.1f}min | 💰 Cost: ${total_cost:.4f} (${self.estimated_costs.get('cost_per_item', 0):.4f}/item)",
            f"📊 Success: {success_rate:.1%} | Items: {items_count} | Quality: {self.business_metrics.get('avg_quality_score', 0):.2f}",
        ]
        
        # Top contributors
        top_contributors = self.business_metrics.get("top_contributors", [])[:2]
        if top_contributors:
            contrib_text = ", ".join([f"{c['source']} ({c['items']} items)" for c in top_contributors])
            summary_parts.append(f"🏆 Top: {contrib_text}")
        
        # Issues
        issues = []
        if self.business_metrics.get("avg_quality_score", 1) < 0.7:
            issues.append("low quality")
        if success_rate < 0.8:
            issues.append("low success rate")
        if duration_min > 5:
            issues.append("slow execution")
        
        if issues:
            summary_parts.append(f"⚠️ Issues: {', '.join(issues)}")
        
        return " | ".join(summary_parts)


@dataclass 
class RunTracker:
    """
    Tracker pour gérer l'historique et la comparaison des runs.
    
    Maintient un index des runs et permet la comparaison
    avec les runs précédents pour détecter les régressions.
    """
    
    def __init__(self, storage_path: str = "output/runs"):
        self.storage_path = storage_path
    
    def register_run(self, manifest: EnhancedRunManifest) -> None:
        """Enregistre un nouveau run dans l'index"""
        # TODO: Implémenter l'indexation des runs
        pass
    
    def get_previous_runs(self, client_id: str, limit: int = 5) -> List[EnhancedRunManifest]:
        """Récupère les runs précédents pour comparaison"""
        # TODO: Implémenter la récupération des runs précédents
        return []
    
    def compare_with_previous(self, current_manifest: EnhancedRunManifest) -> Dict[str, Any]:
        """Compare le run actuel avec les précédents"""
        
        previous_runs = self.get_previous_runs(current_manifest.client_id, limit=3)
        if not previous_runs:
            return {"status": "no_previous_runs"}
        
        # Calculer les moyennes des runs précédents
        prev_items = sum(r.stats.get("items_funnel", {}).get("final", 0) for r in previous_runs) / len(previous_runs)
        prev_duration = sum(r.get_total_duration_seconds() for r in previous_runs) / len(previous_runs)
        prev_success_rate = sum(r.business_metrics.get("success_rate", 0) for r in previous_runs) / len(previous_runs)
        
        # Comparaison actuelle
        current_items = current_manifest.stats.get("items_funnel", {}).get("final", 0)
        current_duration = current_manifest.get_total_duration_seconds()
        current_success_rate = current_manifest.business_metrics.get("success_rate", 0)
        
        return {
            "status": "compared",
            "items_change": {
                "current": current_items,
                "previous_avg": prev_items,
                "change_pct": ((current_items - prev_items) / max(prev_items, 1)) * 100
            },
            "duration_change": {
                "current": current_duration,
                "previous_avg": prev_duration,
                "change_pct": ((current_duration - prev_duration) / max(prev_duration, 1)) * 100
            },
            "success_rate_change": {
                "current": current_success_rate,
                "previous_avg": prev_success_rate,
                "change_pct": ((current_success_rate - prev_success_rate) / max(prev_success_rate, 0.01)) * 100
            }
        }