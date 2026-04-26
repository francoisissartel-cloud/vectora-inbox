"""
Run Reporter V3 - Génère les rapports et manifests de run
Produit le run_manifest.json avec résumé lisible et métriques complètes.

Responsabilités :
- Générer run_manifest.json avec toutes les métriques
- Créer human_summary lisible
- Produire debug_report.json avec recommandations
- Calculer les stats agrégées et métriques de qualité
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

from .models import RunManifest, SourceReport, StructuredItem, DebugReport

logger = logging.getLogger(__name__)


class RunReporter:
    """Générateur de rapports pour les runs d'ingestion V3"""
    
    def __init__(self, run_id: str, client_config: Dict[str, Any], run_started_at: str):
        self.run_id = run_id
        self.client_config = client_config
        self.run_started_at = run_started_at
        self.run_completed_at = datetime.utcnow().isoformat() + "Z"
        
        # Extraire les infos du client_config
        self.client_id = client_config.get('client_id', run_id.split('__')[0])
        self.period_days = client_config.get('ingestion', {}).get('default_period_days', 7)
        self.ingestion_mode = client_config.get('ingestion', {}).get('ingestion_mode', 'balanced')
        
        logger.info(f"RunReporter initialized for run: {run_id}")
    
    def generate_run_manifest(self, source_reports: List[SourceReport], final_items: List[StructuredItem],
                            rejected_items: List[StructuredItem], output_paths: Dict[str, str]) -> RunManifest:
        """
        Génère le run_manifest complet avec toutes les métriques
        
        Args:
            source_reports: Rapports de toutes les sources traitées
            final_items: Items finaux après tous les filtres
            rejected_items: Items rejetés par les filtres
            output_paths: Chemins des fichiers générés
        
        Returns:
            RunManifest complet
        """
        logger.info("Generating run manifest...")
        
        # Calculer les dates de période
        from_date, to_date = self._calculate_period_dates()
        
        # Générer les stats agrégées
        stats = self._calculate_aggregate_stats(source_reports, final_items, rejected_items)
        
        # Générer le résumé lisible
        human_summary = self._generate_human_summary(source_reports, final_items, rejected_items, stats)
        
        # Déterminer le statut global
        status = self._determine_run_status(source_reports, final_items)
        
        # Créer le manifest
        manifest = RunManifest(
            run_id=self.run_id,
            client_id=self.client_id,
            run_date=datetime.utcnow().strftime('%Y-%m-%d'),
            run_started_at=self.run_started_at,
            run_completed_at=self.run_completed_at,
            period_days=self.period_days,
            ingestion_mode=self.ingestion_mode,
            from_date=from_date,
            to_date=to_date,
            s3_paths=output_paths,
            source_reports=source_reports,
            stats=stats,
            status=status,
            human_summary=human_summary
        )
        
        # Générer le debug report
        debug_report = self._generate_debug_report(source_reports, final_items, rejected_items)
        if debug_report:
            debug_path = self._write_debug_report(debug_report)
            manifest.debug_report_path = debug_path
        
        logger.info(f"Run manifest generated - status: {status}, final_items: {len(final_items)}")
        return manifest
    
    def _calculate_period_dates(self) -> tuple[str, str]:
        """Calcule les dates de début et fin de période"""
        to_date = datetime.utcnow().strftime('%Y-%m-%d')
        from_date = (datetime.utcnow() - timedelta(days=self.period_days)).strftime('%Y-%m-%d')
        return from_date, to_date
    
    def _calculate_aggregate_stats(self, source_reports: List[SourceReport], 
                                 final_items: List[StructuredItem], 
                                 rejected_items: List[StructuredItem]) -> Dict[str, Any]:
        """Calcule toutes les statistiques agrégées"""
        
        # Stats de base
        total_sources = len(source_reports)
        sources_processed = len([r for r in source_reports if r.status in ['success', 'partial']])
        sources_failed = len([r for r in source_reports if r.status == 'failed'])
        sources_skipped = len([r for r in source_reports if r.status == 'skipped'])
        
        # Funnel d'items
        total_items_found = sum(r.items_found for r in source_reports)
        items_with_date = sum(r.items_with_date for r in source_reports)
        items_with_content = sum(r.items_with_content for r in source_reports)
        
        # Analyse des rejets par filtre
        rejection_analysis = self._analyze_rejections(rejected_items)
        
        # Métriques de performance
        total_fetch_time = sum(r.fetch_time_seconds for r in source_reports)
        total_parse_time = sum(r.parse_time_seconds for r in source_reports)
        total_filter_time = sum(r.filter_time_seconds for r in source_reports)
        
        # Durée totale du run
        try:
            start = datetime.fromisoformat(self.run_started_at.replace('Z', '+00:00'))
            end = datetime.fromisoformat(self.run_completed_at.replace('Z', '+00:00'))
            total_duration = (end - start).total_seconds()
        except:
            total_duration = 0.0
        
        # Qualité moyenne
        avg_date_confidence = self._calculate_avg_date_confidence(source_reports)
        
        return {
            "sources": {
                "total": total_sources,
                "processed": sources_processed,
                "failed": sources_failed,
                "skipped": sources_skipped
            },
            "items_funnel": {
                "found": total_items_found,
                "with_date": items_with_date,
                "with_content": items_with_content,
                "after_period_filter": total_items_found - rejection_analysis.get('period_filter', 0),
                "after_exclusion_filter": total_items_found - rejection_analysis.get('period_filter', 0) - rejection_analysis.get('exclusion_filter', 0),
                "after_lai_filter": total_items_found - sum(rejection_analysis.values()),
                "final": len(final_items)
            },
            "rejection_analysis": rejection_analysis,
            "performance": {
                "total_duration_seconds": total_duration,
                "fetch_time_seconds": total_fetch_time,
                "parse_time_seconds": total_parse_time,
                "filter_time_seconds": total_filter_time,
                "avg_time_per_source": total_duration / max(sources_processed, 1)
            },
            "quality": {
                "avg_date_confidence": avg_date_confidence,
                "content_extraction_rate": items_with_content / max(total_items_found, 1),
                "date_extraction_rate": items_with_date / max(total_items_found, 1)
            }
        }
    
    def _analyze_rejections(self, rejected_items: List[StructuredItem]) -> Dict[str, int]:
        """Analyse les raisons de rejet des items"""
        
        rejection_counts = {
            "period_filter": 0,
            "exclusion_filter": 0,
            "lai_keyword_filter": 0,
            "validation_error": 0,
            "unknown": 0
        }
        
        for item in rejected_items:
            reason = item.get_rejection_reason()
            if not reason:
                continue
                
            if "period_filter" in reason:
                rejection_counts["period_filter"] += 1
            elif "exclusion_filter" in reason:
                rejection_counts["exclusion_filter"] += 1
            elif "lai_keyword_filter" in reason:
                rejection_counts["lai_keyword_filter"] += 1
            elif "validation" in reason:
                rejection_counts["validation_error"] += 1
            else:
                rejection_counts["unknown"] += 1
        
        return rejection_counts
    
    def _calculate_avg_date_confidence(self, source_reports: List[SourceReport]) -> float:
        """Calcule la confiance moyenne d'extraction de date"""
        
        confidences = [r.avg_date_confidence for r in source_reports if r.avg_date_confidence > 0]
        return sum(confidences) / len(confidences) if confidences else 0.0
    
    def _generate_human_summary(self, source_reports: List[SourceReport], 
                              final_items: List[StructuredItem], 
                              rejected_items: List[StructuredItem],
                              stats: Dict[str, Any]) -> str:
        """Génère un résumé lisible du run"""
        
        duration = stats["performance"]["total_duration_seconds"]
        sources_processed = stats["sources"]["processed"]
        sources_skipped = stats["sources"]["skipped"]
        
        # Ligne principale
        summary_lines = [
            f"Run {self.run_id} completed in {duration:.0f}s."
        ]
        
        # Sources
        if sources_skipped > 0:
            skipped_sources = [r.source_key for r in source_reports if r.status == 'skipped']
            skipped_reasons = []
            for report in source_reports:
                if report.status == 'skipped' and report.errors:
                    reason = report.errors[0].lower()
                    if 'validated: false' in reason or 'not validated' in reason:
                        skipped_reasons.append(f"{report.source_key}=not_validated")
                    elif 'no items' in reason:
                        skipped_reasons.append(f"{report.source_key}=no_items")
                    else:
                        skipped_reasons.append(f"{report.source_key}=error")
            
            summary_lines.append(
                f"{sources_processed} sources processed ({sources_skipped} skipped: {', '.join(skipped_reasons[:3])})."
            )
        else:
            summary_lines.append(f"{sources_processed} sources processed.")
        
        # Funnel d'items
        funnel = stats["items_funnel"]
        summary_lines.append(
            f"{funnel['found']} items extracted → {funnel['after_period_filter']} after period filter → "
            f"{funnel['after_exclusion_filter']} after exclusions → {funnel['after_lai_filter']} after LAI keywords → "
            f"{funnel['final']} after dedup."
        )
        
        # Top sources
        top_sources = sorted(source_reports, key=lambda r: r.items_passed_filters, reverse=True)[:3]
        if top_sources and top_sources[0].items_passed_filters > 0:
            top_source_names = [f"{r.source_key} ({r.items_passed_filters} items)" for r in top_sources if r.items_passed_filters > 0]
            summary_lines.append(f"Top sources: {', '.join(top_source_names)}.")
        
        # Sources lentes
        slowest_sources = sorted(source_reports, key=lambda r: r.fetch_time_seconds + r.parse_time_seconds, reverse=True)[:2]
        if slowest_sources and slowest_sources[0].fetch_time_seconds > 5:
            slow_names = [f"{r.source_key} ({r.fetch_time_seconds + r.parse_time_seconds:.0f}s)" for r in slowest_sources[:2]]
            summary_lines.append(f"Slowest sources: {', '.join(slow_names)}.")
        
        # Problèmes de qualité
        quality_issues = []
        avg_confidence = stats["quality"]["avg_date_confidence"]
        if avg_confidence < 0.7:
            low_confidence_sources = [r.source_key for r in source_reports if r.avg_date_confidence < 0.6]
            if low_confidence_sources:
                quality_issues.append(f"{', '.join(low_confidence_sources[:2])} date extraction low confidence ({avg_confidence:.2f} avg)")
        
        content_rate = stats["quality"]["content_extraction_rate"]
        if content_rate < 0.8:
            quality_issues.append(f"content extraction rate low ({content_rate:.1%})")
        
        if quality_issues:
            summary_lines.append(f"Quality issues: {', '.join(quality_issues)}.")
        
        return " ".join(summary_lines)
    
    def _determine_run_status(self, source_reports: List[SourceReport], final_items: List[StructuredItem]) -> str:
        """Détermine le statut global du run"""
        
        failed_sources = [r for r in source_reports if r.status == 'failed']
        successful_sources = [r for r in source_reports if r.status == 'success']
        
        if len(failed_sources) == len(source_reports):
            return "failed"
        elif len(failed_sources) > 0:
            return "partial"
        elif len(final_items) == 0:
            return "partial"
        else:
            return "success"
    
    def _generate_debug_report(self, source_reports: List[SourceReport], 
                             final_items: List[StructuredItem], 
                             rejected_items: List[StructuredItem]) -> Optional[DebugReport]:
        """Génère un rapport de debug détaillé"""
        
        debug_report = DebugReport(
            run_id=self.run_id,
            generated_at=datetime.utcnow().isoformat() + "Z"
        )
        
        # Analyser chaque source
        for report in source_reports:
            source_analysis = {
                "status": report.status,
                "items_found": report.items_found,
                "items_passed_filters": report.items_passed_filters,
                "avg_date_confidence": report.avg_date_confidence,
                "fetch_time_seconds": report.fetch_time_seconds,
                "parse_time_seconds": report.parse_time_seconds,
                "quality_issues": report.quality_issues,
                "errors": report.errors
            }
            
            # Recommandations spécifiques à la source
            recommendations = []
            if report.avg_date_confidence < 0.6:
                recommendations.append("Consider adding date_selectors to improve date extraction")
            if report.items_with_content / max(report.items_found, 1) < 0.7:
                recommendations.append("Review content extraction selectors")
            if report.fetch_time_seconds > 10:
                recommendations.append("Source is slow, consider timeout adjustment")
            
            source_analysis["recommendations"] = recommendations
            debug_report.add_source_analysis(report.source_key, source_analysis)
        
        # Recommandations globales
        avg_confidence = sum(r.avg_date_confidence for r in source_reports if r.avg_date_confidence > 0) / max(len(source_reports), 1)
        if avg_confidence < 0.7:
            debug_report.add_recommendation("Overall date extraction confidence is low - review date_selectors configuration")
        
        failed_sources = [r for r in source_reports if r.status == 'failed']
        if len(failed_sources) > len(source_reports) * 0.3:
            debug_report.add_recommendation("High failure rate - check network connectivity and source availability")
        
        # Résumé de performance
        debug_report.performance_summary = {
            "total_sources": len(source_reports),
            "avg_fetch_time": sum(r.fetch_time_seconds for r in source_reports) / max(len(source_reports), 1),
            "avg_parse_time": sum(r.parse_time_seconds for r in source_reports) / max(len(source_reports), 1),
            "avg_date_confidence": avg_confidence,
            "content_extraction_rate": sum(r.items_with_content for r in source_reports) / max(sum(r.items_found for r in source_reports), 1)
        }
        
        return debug_report
    
    def _write_debug_report(self, debug_report: DebugReport) -> Optional[str]:
        """Debug report generation disabled - information now included in run_complete.json"""
        logger.info("Debug report generation disabled - all information included in run_complete.json")
        return None