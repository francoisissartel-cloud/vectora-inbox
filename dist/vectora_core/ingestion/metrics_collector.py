"""
Module de collecte de métriques d'ingestion par source.

Ce module collecte et expose des métriques détaillées sur l'ingestion
de chaque source pour identifier les sources problématiques.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class IngestionMetrics:
    """Collecteur de métriques d'ingestion par source."""
    
    def __init__(self):
        self.metrics = {}
        self.start_time = datetime.now()
    
    def record_source_metrics(self, source_key: str, metrics_data: Dict[str, Any]):
        """
        Enregistre les métriques d'une source.
        
        Args:
            source_key: Identifiant de la source
            metrics_data: Données de métriques contenant :
                - pages_fetched: nombre de pages récupérées
                - items_found: nombre d'items candidats trouvés
                - items_valid: nombre d'items valides retenus
                - items_with_date: nombre d'items avec date détectée
                - execution_time: temps d'exécution en secondes
                - errors: liste des erreurs rencontrées
                - fetch_success: succès de la récupération HTTP
                - parse_success: succès du parsing
        """
        self.metrics[source_key] = {
            'timestamp': datetime.now().isoformat(),
            'pages_fetched': metrics_data.get('pages_fetched', 0),
            'items_found': metrics_data.get('items_found', 0),
            'items_valid': metrics_data.get('items_valid', 0),
            'items_with_date': metrics_data.get('items_with_date', 0),
            'execution_time': metrics_data.get('execution_time', 0),
            'errors': metrics_data.get('errors', []),
            'fetch_success': metrics_data.get('fetch_success', False),
            'parse_success': metrics_data.get('parse_success', False),
            'status': self._calculate_status(metrics_data)
        }
        
        logger.info(f"Métriques enregistrées pour {source_key}: {self.metrics[source_key]['status']}")
    
    def _calculate_status(self, metrics_data: Dict[str, Any]) -> str:
        """
        Calcule le statut d'une source basé sur ses métriques.
        
        Args:
            metrics_data: Données de métriques
        
        Returns:
            Statut: 'OK', 'WARNING', 'ERROR'
        """
        if not metrics_data.get('fetch_success', False):
            return 'ERROR'
        
        if not metrics_data.get('parse_success', False):
            return 'ERROR'
        
        items_valid = metrics_data.get('items_valid', 0)
        if items_valid == 0:
            return 'ERROR'
        elif items_valid < 3:
            return 'WARNING'
        else:
            return 'OK'
    
    def get_source_metrics(self, source_key: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les métriques d'une source spécifique.
        
        Args:
            source_key: Identifiant de la source
        
        Returns:
            Métriques de la source ou None si non trouvée
        """
        return self.metrics.get(source_key)
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """
        Génère un rapport de synthèse des métriques.
        
        Returns:
            Rapport de synthèse avec statistiques globales
        """
        total_sources = len(self.metrics)
        sources_ok = sum(1 for m in self.metrics.values() if m['status'] == 'OK')
        sources_warning = sum(1 for m in self.metrics.values() if m['status'] == 'WARNING')
        sources_error = sum(1 for m in self.metrics.values() if m['status'] == 'ERROR')
        
        total_items = sum(m['items_valid'] for m in self.metrics.values())
        total_items_with_date = sum(m['items_with_date'] for m in self.metrics.values())
        
        return {
            'timestamp': datetime.now().isoformat(),
            'execution_duration': (datetime.now() - self.start_time).total_seconds(),
            'summary': {
                'total_sources': total_sources,
                'sources_ok': sources_ok,
                'sources_warning': sources_warning,
                'sources_error': sources_error,
                'success_rate': (sources_ok / total_sources * 100) if total_sources > 0 else 0,
                'total_items_extracted': total_items,
                'total_items_with_date': total_items_with_date,
                'date_detection_rate': (total_items_with_date / total_items * 100) if total_items > 0 else 0
            },
            'sources': self.metrics
        }
    
    def generate_markdown_report(self) -> str:
        """
        Génère un rapport au format Markdown.
        
        Returns:
            Rapport formaté en Markdown
        """
        report = self.generate_summary_report()
        
        md = f"""# Rapport de métriques d'ingestion corporate HTML

**Date d'exécution** : {report['timestamp']}  
**Durée d'exécution** : {report['execution_duration']:.2f} secondes  

## Synthèse

| Métrique | Valeur |
|----------|--------|
| Sources totales | {report['summary']['total_sources']} |
| Sources OK | {report['summary']['sources_ok']} |
| Sources WARNING | {report['summary']['sources_warning']} |
| Sources ERROR | {report['summary']['sources_error']} |
| **Taux de succès** | **{report['summary']['success_rate']:.1f}%** |
| Items extraits | {report['summary']['total_items_extracted']} |
| Items avec date | {report['summary']['total_items_with_date']} |
| **Taux de détection de date** | **{report['summary']['date_detection_rate']:.1f}%** |

## Détail par source

| Source | Statut | Items | Dates | Temps | Erreurs |
|--------|--------|-------|-------|-------|---------|
"""
        
        for source_key, metrics in report['sources'].items():
            status_emoji = {'OK': '🟢', 'WARNING': '🟡', 'ERROR': '🔴'}.get(metrics['status'], '❓')
            errors_count = len(metrics['errors'])
            
            md += f"| `{source_key}` | {status_emoji} {metrics['status']} | {metrics['items_valid']} | {metrics['items_with_date']} | {metrics['execution_time']:.1f}s | {errors_count} |\n"
        
        # Ajouter les détails des erreurs si présentes
        error_sources = {k: v for k, v in report['sources'].items() if v['errors']}
        if error_sources:
            md += "\n## Détail des erreurs\n\n"
            for source_key, metrics in error_sources.items():
                md += f"### {source_key}\n\n"
                for error in metrics['errors']:
                    md += f"- {error}\n"
                md += "\n"
        
        return md
    
    def save_report_to_file(self, file_path: str, format: str = 'json'):
        """
        Sauvegarde le rapport dans un fichier.
        
        Args:
            file_path: Chemin du fichier de sortie
            format: Format de sortie ('json' ou 'markdown')
        """
        try:
            if format == 'json':
                report = self.generate_summary_report()
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
            elif format == 'markdown':
                report_md = self.generate_markdown_report()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(report_md)
            else:
                raise ValueError(f"Format non supporté: {format}")
            
            logger.info(f"Rapport sauvegardé dans {file_path} (format: {format})")
        
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du rapport: {e}")


def create_source_metrics(
    source_key: str,
    fetch_success: bool,
    parse_success: bool,
    items_found: int,
    items_valid: int,
    items_with_date: int,
    execution_time: float,
    errors: List[str] = None
) -> Dict[str, Any]:
    """
    Crée un dictionnaire de métriques pour une source.
    
    Args:
        source_key: Identifiant de la source
        fetch_success: Succès de la récupération HTTP
        parse_success: Succès du parsing
        items_found: Nombre d'items candidats trouvés
        items_valid: Nombre d'items valides retenus
        items_with_date: Nombre d'items avec date détectée
        execution_time: Temps d'exécution en secondes
        errors: Liste des erreurs (optionnel)
    
    Returns:
        Dictionnaire de métriques
    """
    return {
        'pages_fetched': 1 if fetch_success else 0,
        'items_found': items_found,
        'items_valid': items_valid,
        'items_with_date': items_with_date,
        'execution_time': execution_time,
        'errors': errors or [],
        'fetch_success': fetch_success,
        'parse_success': parse_success
    }