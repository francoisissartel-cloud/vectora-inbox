"""
Models V3 - Dataclasses pour le moteur d'ingestion V3

Ce module définit tous les modèles de données utilisés par le moteur V3.
Format enrichi avec traçabilité complète pour debugging et qualité.

Responsabilités :
- Structures de données pour items, sources, runs
- Format enrichi avec métadonnées de performance
- Traçabilité complète des filtres appliqués
- Compatibilité avec Lambda Normalize V2
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class StructuredItem:
    """
    Item structuré V3 avec format enrichi.
    
    Contient toutes les métadonnées nécessaires pour le debugging
    et la traçabilité complète du pipeline d'ingestion.
    """
    # Champs de base (compatibles Normalize V2)
    item_id: str
    run_id: str
    source_key: str
    source_type: str
    actor_type: str
    title: str
    url: str
    published_at: Optional[str]         # Date de publication de l'article (YYYY-MM-DD)
    ingested_at: str                    # Date/heure d'ingestion (ISO 8601 UTC)
    content: str
    content_length: int
    language: str
    content_hash: str
    ingestion_profile_used: str
    
    # Champs enrichis V3
    date_extraction: Dict[str, Any] = field(default_factory=dict)     # Métadonnées extraction de date
    filter_analysis: Dict[str, Any] = field(default_factory=dict)     # Analyse complète des filtres
    ingestion_metadata: Dict[str, Any] = field(default_factory=dict)  # Métadonnées de performance
    
    def to_normalize_format(self) -> Dict[str, Any]:
        """
        Convertit l'item au format attendu par Lambda Normalize V2.
        
        Returns:
            Dictionnaire compatible avec Normalize V2
        """
        return {
            "item_id": self.item_id,
            "run_id": self.run_id,
            "source_key": self.source_key,
            "title": self.title,
            "url": self.url,
            "published_at": self.published_at,
            "extraction_date": self.ingested_at,  # Mapping pour compatibilité
            "content": self.content,
            "content_length": self.content_length,
            "language": self.language,
            "content_hash": self.content_hash
        }
    
    def has_passed_all_filters(self) -> bool:
        """
        Vérifie si l'item a passé tous les filtres.
        
        Returns:
            True si tous les filtres sont passés
        """
        return self.filter_analysis.get('passed_all_filters', False)
    
    def get_rejection_reason(self) -> Optional[str]:
        """
        Retourne la raison de rejet si l'item a été filtré.
        
        Returns:
            Raison de rejet ou None si l'item a passé
        """
        if self.has_passed_all_filters():
            return None
        
        # Vérifier chaque filtre
        if not self.filter_analysis.get('period_filter', {}).get('passed', True):
            return "period_filter"
        
        exclusion_filter = self.filter_analysis.get('exclusion_filter', {})
        if not exclusion_filter.get('passed', True):
            return f"exclusion_filter: {exclusion_filter.get('exclusion_reason', 'unknown')}"
        
        lai_filter = self.filter_analysis.get('lai_keyword_filter', {})
        if lai_filter.get('required', False) and not lai_filter.get('passed', True):
            return "lai_keyword_filter"
        
        return "unknown_filter"


@dataclass
class ResolvedSource:
    """
    Source résolue avec toute sa configuration technique.
    
    Combine les données de source_catalog + source_configs + ingestion_profiles.
    """
    source_key: str
    company_id: Optional[str]
    source_type: str
    actor_type: str                     # Résolu dynamiquement
    homepage_url: str
    news_url: str
    ingestion_profile: str              # rss_full | rss_with_fetch | html_generic | html_pdf
    profile_config: Dict[str, Any]      # Contenu du profil (timeout, max_items, etc.)
    listing_selectors: Optional[Dict[str, Any]]  # Selectors custom ou None
    date_selectors: Optional[Dict[str, Any]]     # Selectors date ou None
    prefetch_filter: bool               # true/false
    pagination: Optional[Dict[str, Any]]         # Config pagination ou None
    validated: bool                     # Source validée dans source_configs
    default_language: str = "en"


@dataclass
class SourceReport:
    """
    Rapport de traitement d'une source.
    
    Contient toutes les métriques et informations de qualité
    pour une source donnée lors d'un run.
    """
    source_key: str
    status: str                         # success | partial | failed | skipped
    ingestion_profile_used: str
    items_found: int
    items_with_date: int
    items_with_content: int
    items_passed_filters: int
    avg_date_confidence: float          # Moyenne des confidences de date
    fetch_time_seconds: float
    parse_time_seconds: float
    filter_time_seconds: float
    quality_issues: List[Dict[str, Any]] = field(default_factory=list)  # Problèmes détectés
    errors: List[str] = field(default_factory=list)
    
    def add_quality_issue(self, issue_type: str, description: str, item_url: Optional[str] = None):
        """
        Ajoute un problème de qualité détecté.
        
        Args:
            issue_type: Type de problème (low_date_confidence, parsing_error, etc.)
            description: Description du problème
            item_url: URL de l'item concerné (optionnel)
        """
        issue = {
            "type": issue_type,
            "description": description,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        if item_url:
            issue["item_url"] = item_url
        
        self.quality_issues.append(issue)
    
    def get_success_rate(self) -> float:
        """
        Calcule le taux de succès de la source.
        
        Returns:
            Taux de succès (0.0 à 1.0)
        """
        if self.items_found == 0:
            return 0.0
        return self.items_passed_filters / self.items_found


@dataclass
class RunManifest:
    """
    Manifest complet d'un run d'ingestion.
    
    Contient toutes les informations sur l'exécution :
    identité, configuration, résultats, métriques.
    """
    run_id: str
    client_id: str
    run_date: str
    run_started_at: str
    run_completed_at: str
    period_days: int
    ingestion_mode: str
    from_date: str
    to_date: str
    s3_paths: Dict[str, str]
    source_reports: List[SourceReport]
    stats: Dict[str, Any]               # Totaux agrégés + métriques qualité
    status: str                         # success | partial | failed
    human_summary: str                  # Résumé lisible
    debug_report_path: Optional[str] = None  # Chemin vers debug_report.json
    
    def get_total_duration_seconds(self) -> float:
        """
        Calcule la durée totale du run.
        
        Returns:
            Durée en secondes
        """
        try:
            start = datetime.fromisoformat(self.run_started_at.replace('Z', '+00:00'))
            end = datetime.fromisoformat(self.run_completed_at.replace('Z', '+00:00'))
            return (end - start).total_seconds()
        except (ValueError, AttributeError):
            return 0.0
    
    def get_sources_by_status(self, status: str) -> List[SourceReport]:
        """
        Filtre les sources par statut.
        
        Args:
            status: Statut recherché (success, partial, failed, skipped)
        
        Returns:
            Liste des sources avec ce statut
        """
        return [report for report in self.source_reports if report.status == status]
    
    def get_top_sources_by_items(self, limit: int = 5) -> List[SourceReport]:
        """
        Retourne les sources avec le plus d'items.
        
        Args:
            limit: Nombre maximum de sources à retourner
        
        Returns:
            Liste des top sources triées par nombre d'items
        """
        return sorted(
            self.source_reports,
            key=lambda r: r.items_passed_filters,
            reverse=True
        )[:limit]
    
    def get_slowest_sources(self, limit: int = 3) -> List[SourceReport]:
        """
        Retourne les sources les plus lentes.
        
        Args:
            limit: Nombre maximum de sources à retourner
        
        Returns:
            Liste des sources les plus lentes
        """
        return sorted(
            self.source_reports,
            key=lambda r: r.fetch_time_seconds + r.parse_time_seconds,
            reverse=True
        )[:limit]


@dataclass
class FilterResult:
    """
    Résultat détaillé de l'application des filtres sur un item.
    
    Utilisé pour construire le filter_analysis des StructuredItem.
    """
    passed_all_filters: bool
    period_filter: Dict[str, Any] = field(default_factory=dict)
    exclusion_filter: Dict[str, Any] = field(default_factory=dict)
    lai_keyword_filter: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit le résultat en dictionnaire pour stockage.
        
        Returns:
            Dictionnaire avec tous les résultats de filtres
        """
        return {
            "passed_all_filters": self.passed_all_filters,
            "period_filter": self.period_filter,
            "exclusion_filter": self.exclusion_filter,
            "lai_keyword_filter": self.lai_keyword_filter
        }


@dataclass
class DebugReport:
    """
    Rapport de debug détaillé pour un run.
    
    Contient les analyses de qualité et recommandations d'amélioration.
    """
    run_id: str
    generated_at: str
    sources_analysis: List[Dict[str, Any]] = field(default_factory=list)
    global_recommendations: List[str] = field(default_factory=list)
    performance_summary: Dict[str, Any] = field(default_factory=dict)
    
    def add_source_analysis(self, source_key: str, analysis: Dict[str, Any]):
        """
        Ajoute l'analyse d'une source.
        
        Args:
            source_key: Clé de la source
            analysis: Dictionnaire d'analyse
        """
        analysis["source_key"] = source_key
        self.sources_analysis.append(analysis)
    
    def add_recommendation(self, recommendation: str):
        """
        Ajoute une recommandation globale.
        
        Args:
            recommendation: Texte de la recommandation
        """
        self.global_recommendations.append(recommendation)