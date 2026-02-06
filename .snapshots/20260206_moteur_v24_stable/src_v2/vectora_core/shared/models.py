"""
Data Models pour Vectora Inbox V2.

Ce module définit les modèles de données utilisés dans l'ingestion :
- Item : Représentation d'un article/contenu ingéré
- Source : Métadonnées d'une source de contenu
- ClientConfig : Configuration d'un client
- IngestionResult : Résultat d'une opération d'ingestion

Responsabilités :
- Définir les structures de données avec validation
- Fournir des méthodes utilitaires pour la manipulation des données
- Assurer la cohérence des formats entre les modules
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class Item:
    """
    Représente un item de contenu ingéré.
    
    Attributes:
        item_id: Identifiant unique de l'item
        source_key: Identifiant de la source d'origine
        source_type: Type de source (rss, html, api)
        title: Titre de l'item
        content: Contenu textuel complet
        url: URL de l'item original
        published_at: Date de publication (YYYY-MM-DD)
        ingested_at: Timestamp d'ingestion (ISO8601)
        language: Code langue détecté
        content_hash: Hash SHA256 du contenu
        metadata: Métadonnées supplémentaires
    """
    item_id: str
    source_key: str
    source_type: str
    title: str
    content: str
    url: str
    published_at: str
    ingested_at: str
    language: str
    content_hash: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'item en dictionnaire pour sérialisation JSON."""
        return {
            'item_id': self.item_id,
            'source_key': self.source_key,
            'source_type': self.source_type,
            'title': self.title,
            'content': self.content,
            'url': self.url,
            'published_at': self.published_at,
            'ingested_at': self.ingested_at,
            'language': self.language,
            'content_hash': self.content_hash,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Item':
        """Crée un item depuis un dictionnaire."""
        return cls(
            item_id=data['item_id'],
            source_key=data['source_key'],
            source_type=data['source_type'],
            title=data['title'],
            content=data['content'],
            url=data['url'],
            published_at=data['published_at'],
            ingested_at=data['ingested_at'],
            language=data['language'],
            content_hash=data['content_hash'],
            metadata=data.get('metadata', {})
        )
    
    def is_valid(self) -> bool:
        """Valide la cohérence de l'item."""
        required_fields = [
            self.item_id, self.source_key, self.source_type,
            self.title, self.content, self.url, self.published_at
        ]
        return all(field for field in required_fields)


@dataclass
class Source:
    """
    Représente une source de contenu avec ses métadonnées.
    
    Attributes:
        source_key: Identifiant unique de la source
        source_type: Type de source (press_corporate, press_sector, etc.)
        ingestion_mode: Mode d'ingestion (rss, html, api)
        homepage_url: URL de la page d'accueil
        rss_url: URL du flux RSS (si applicable)
        html_url: URL de la page HTML (si applicable)
        api_url: URL de l'API (si applicable)
        enabled: Source activée ou non
        default_language: Langue par défaut du contenu
        ingestion_profile: Profil d'ingestion à appliquer
        tags: Tags associés à la source
        metadata: Métadonnées supplémentaires
    """
    source_key: str
    source_type: str
    ingestion_mode: str
    homepage_url: str
    rss_url: Optional[str] = None
    html_url: Optional[str] = None
    api_url: Optional[str] = None
    enabled: bool = True
    default_language: str = 'en'
    ingestion_profile: str = 'default_broad'
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialise les champs optionnels."""
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}
    
    def get_ingestion_url(self) -> Optional[str]:
        """Retourne l'URL à utiliser selon le mode d'ingestion."""
        if self.ingestion_mode == 'rss':
            return self.rss_url
        elif self.ingestion_mode == 'html':
            return self.html_url
        elif self.ingestion_mode == 'api':
            return self.api_url
        else:
            return None
    
    def is_valid(self) -> bool:
        """Valide la cohérence de la source."""
        if not self.source_key or not self.source_type or not self.ingestion_mode:
            return False
        
        # Vérifier que l'URL correspondant au mode d'ingestion existe
        ingestion_url = self.get_ingestion_url()
        return ingestion_url is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit la source en dictionnaire."""
        return {
            'source_key': self.source_key,
            'source_type': self.source_type,
            'ingestion_mode': self.ingestion_mode,
            'homepage_url': self.homepage_url,
            'rss_url': self.rss_url,
            'html_url': self.html_url,
            'api_url': self.api_url,
            'enabled': self.enabled,
            'default_language': self.default_language,
            'ingestion_profile': self.ingestion_profile,
            'tags': self.tags,
            'metadata': self.metadata
        }


@dataclass
class ClientConfig:
    """
    Représente la configuration d'un client.
    
    Attributes:
        client_id: Identifiant unique du client
        client_profile: Profil du client (nom, langue, etc.)
        pipeline: Configuration du pipeline (period_days, etc.)
        source_config: Configuration des sources (bouquets, sources extra)
        metadata: Métadonnées supplémentaires
    """
    client_id: str
    client_profile: Dict[str, Any]
    pipeline: Dict[str, Any]
    source_config: Dict[str, Any]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialise les champs optionnels."""
        if self.metadata is None:
            self.metadata = {}
    
    def get_default_period_days(self) -> int:
        """Retourne la valeur par défaut de period_days."""
        return self.pipeline.get('default_period_days', 7)
    
    def get_enabled_bouquets(self) -> List[str]:
        """Retourne la liste des bouquets activés."""
        return self.source_config.get('source_bouquets_enabled', [])
    
    def get_extra_sources(self) -> List[str]:
        """Retourne la liste des sources supplémentaires."""
        return self.source_config.get('sources_extra_enabled', [])


@dataclass
class IngestionResult:
    """
    Représente le résultat d'une opération d'ingestion.
    
    Attributes:
        client_id: Identifiant du client
        execution_date: Date d'exécution (ISO8601)
        sources_processed: Nombre de sources traitées
        items_ingested: Nombre d'items ingérés
        items_filtered_out: Nombre d'items filtrés (trop anciens)
        items_deduplicated: Nombre d'items dédupliqués
        s3_output_path: Chemin S3 de sortie
        execution_time_seconds: Temps d'exécution en secondes
        dry_run: Mode simulation activé ou non
        errors: Liste des erreurs rencontrées
        warnings: Liste des avertissements
    """
    client_id: str
    execution_date: str
    sources_processed: int = 0
    items_ingested: int = 0
    items_filtered_out: int = 0
    items_deduplicated: int = 0
    s3_output_path: str = ""
    execution_time_seconds: float = 0.0
    dry_run: bool = False
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        """Initialise les champs optionnels."""
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
    
    def add_error(self, error: str) -> None:
        """Ajoute une erreur au résultat."""
        self.errors.append(error)
        logger.error(f"Erreur d'ingestion pour {self.client_id}: {error}")
    
    def add_warning(self, warning: str) -> None:
        """Ajoute un avertissement au résultat."""
        self.warnings.append(warning)
        logger.warning(f"Avertissement d'ingestion pour {self.client_id}: {warning}")
    
    def is_success(self) -> bool:
        """Indique si l'ingestion s'est déroulée sans erreur critique."""
        return len(self.errors) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit le résultat en dictionnaire pour sérialisation."""
        return {
            'client_id': self.client_id,
            'execution_date': self.execution_date,
            'sources_processed': self.sources_processed,
            'items_ingested': self.items_ingested,
            'items_filtered_out': self.items_filtered_out,
            'items_deduplicated': self.items_deduplicated,
            's3_output_path': self.s3_output_path,
            'execution_time_seconds': self.execution_time_seconds,
            'dry_run': self.dry_run,
            'errors': self.errors,
            'warnings': self.warnings,
            'success': self.is_success()
        }