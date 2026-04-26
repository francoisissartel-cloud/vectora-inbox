#!/usr/bin/env python3
"""
Gestionnaire de reconstitution d'items par client et période
"""

import json
import logging
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional
from pathlib import Path

from .ingested_warehouse import IngestedWarehouse
from .client_mappings import ClientMappingManager
from .deduplication import DeduplicationManager

logger = logging.getLogger(__name__)

class ReconstitutionManager:
    """Gestionnaire de reconstitution d'items pour les clients"""
    
    def __init__(self):
        self.client_mapping_manager = ClientMappingManager()
    
    def reconstitute_items_for_client(self, client_id: str, client_config: Dict[str, Any], 
                                    reference_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Reconstituer tous les items pour un client selon sa configuration
        
        Args:
            client_id: ID du client
            client_config: Configuration du client
            reference_date: Date de référence (défaut: maintenant)
            
        Returns:
            Liste d'items reconstitués pour normalize_score
        """
        if reference_date is None:
            reference_date = datetime.now()
        
        logger.info(f"Reconstituting items for client {client_id}")
        
        # 1. Résoudre l'écosystème
        ecosystem = self._resolve_ecosystem(client_id, client_config)
        if not ecosystem:
            logger.error(f"No ecosystem found for client {client_id}")
            return []
        
        # 2. Résoudre les sources du client
        client_sources = self._resolve_client_sources(client_id, client_config)
        if not client_sources:
            logger.error(f"No sources found for client {client_id}")
            return []
        
        # 3. Récupérer la période
        period_days = self._get_period_days(client_config)
        
        # 4. Reconstituer depuis le warehouse
        warehouse = IngestedWarehouse(ecosystem)
        items = warehouse.get_items_for_client_period(
            client_sources=client_sources,
            period_days=period_days,
            reference_date=reference_date
        )
        
        # 5. Conversion au format normalize_score
        normalized_items = self._convert_to_normalize_format(items)
        
        logger.info(f"Reconstituted {len(normalized_items)} items for client {client_id}")
        return normalized_items
    
    def _resolve_ecosystem(self, client_id: str, client_config: Dict[str, Any]) -> Optional[str]:
        """Résoudre l'écosystème pour un client"""
        # Méthode 1: Depuis watch_domains
        ecosystem = self.client_mapping_manager.resolve_ecosystem_from_watch_domains(client_config)
        if ecosystem:
            return ecosystem
        
        # Méthode 2: Depuis client_mappings.json
        ecosystem = self.client_mapping_manager.get_ecosystem_for_client(client_id)
        if ecosystem:
            return ecosystem
        
        # Méthode 3: Défaut pour clients LAI
        if any(keyword in client_id.lower() for keyword in ['lai', 'medincell', 'camurus', 'nanexa', 'mvp']):
            return "tech_lai_ecosystem"
        
        return None
    
    def _resolve_client_sources(self, client_id: str, client_config: Dict[str, Any]) -> List[str]:
        """Résoudre les sources pour un client"""
        # Méthode 1: Depuis client_mappings.json
        sources = self.client_mapping_manager.get_sources_for_client(client_id)
        if sources:
            return sources
        
        # Méthode 2: Déduire depuis les bouquets du client_config
        bouquets = client_config.get('ingestion', {}).get('source_bouquets', [])
        if bouquets:
            return self._resolve_sources_from_bouquets(bouquets)
        
        # Méthode 3: Sources par défaut selon le client
        default_sources = self._get_default_sources_for_client(client_id)
        return default_sources
    
    def _resolve_sources_from_bouquets(self, bouquets: List[str]) -> List[str]:
        """Résoudre les sources depuis les bouquets (logique simplifiée)"""
        # Mapping bouquet → sources (à adapter selon la configuration réelle)
        bouquet_mapping = {
            'test_medincell_only': ['press_corporate__medincell'],
            'lai_full_mvp': [
                'press_corporate__medincell',
                'press_corporate__camurus',
                'press_corporate__nanexa',
                'press_corporate__pfizer',
                'press_sector__fiercepharma',
                'press_sector__endpoints_news'
            ]
        }
        
        all_sources = []
        for bouquet in bouquets:
            sources = bouquet_mapping.get(bouquet, [])
            all_sources.extend(sources)
        
        return list(set(all_sources))  # Déduplication
    
    def _get_default_sources_for_client(self, client_id: str) -> List[str]:
        """Sources par défaut selon le client"""
        if 'medincell' in client_id.lower():
            return ['press_corporate__medincell']
        elif 'camurus' in client_id.lower():
            return ['press_corporate__camurus']
        elif 'nanexa' in client_id.lower():
            return ['press_corporate__nanexa']
        elif 'lai' in client_id.lower() or 'mvp' in client_id.lower():
            return [
                'press_corporate__medincell',
                'press_corporate__camurus',
                'press_corporate__nanexa',
                'press_sector__fiercepharma',
                'press_sector__endpoints_news'
            ]
        else:
            return []
    
    def _get_period_days(self, client_config: Dict[str, Any]) -> int:
        """Récupérer la période en jours depuis la config client"""
        return client_config.get('ingestion', {}).get('default_period_days', 200)
    
    def _convert_to_normalize_format(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convertir les items warehouse au format attendu par normalize_score
        Compatible avec StructuredItem.to_normalize_format()
        """
        normalized_items = []
        
        for item in items:
            # Format de base compatible avec normalize_score
            normalized_item = {
                'item_id': item.get('item_id'),
                'run_id': item.get('warehouse_run_id') or item.get('run_id'),
                'source_key': item.get('source_key'),
                'title': item.get('title'),
                'url': item.get('url'),
                'published_at': item.get('published_at'),
                'content': item.get('content'),
                'content_hash': item.get('content_hash'),
                'ingested_at': item.get('warehouse_ingested_at') or item.get('ingested_at')
            }
            
            # Ajouter métadonnées optionnelles si présentes
            optional_fields = [
                'summary', 'author', 'language', 'source_type', 'company_id',
                'date_extraction', 'filter_analysis', 'matching_analysis'
            ]
            
            for field in optional_fields:
                if field in item:
                    normalized_item[field] = item[field]
            
            normalized_items.append(normalized_item)
        
        return normalized_items
    
    def generate_normalize_input_file(self, client_id: str, client_config: Dict[str, Any], 
                                    output_path: str, reference_date: Optional[datetime] = None) -> int:
        """
        Générer le fichier normalize_input.json pour un client
        
        Args:
            client_id: ID du client
            client_config: Configuration du client
            output_path: Chemin du fichier de sortie
            reference_date: Date de référence
            
        Returns:
            Nombre d'items dans le fichier généré
        """
        # Reconstituer les items
        items = self.reconstitute_items_for_client(client_id, client_config, reference_date)
        
        # Écrire le fichier
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Generated normalize_input.json with {len(items)} items at {output_path}")
        return len(items)