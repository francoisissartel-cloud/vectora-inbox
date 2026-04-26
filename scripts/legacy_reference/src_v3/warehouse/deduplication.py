#!/usr/bin/env python3
"""
Gestionnaire de déduplication avancée pour le warehouse
"""

import hashlib
import logging
from typing import List, Dict, Any, Set
from datetime import datetime

logger = logging.getLogger(__name__)

class DeduplicationManager:
    """Gestionnaire de déduplication avancée"""
    
    @staticmethod
    def calculate_content_hash(item) -> str:
        """
        Calculer le hash du contenu d'un item
        Utilise URL + titre + contenu pour un hash robuste
        """
        # Extraire les champs selon le type d'objet
        if hasattr(item, '__dict__'):
            content = getattr(item, 'content', '') or ''
            url = getattr(item, 'url', '') or ''
            title = getattr(item, 'title', '') or ''
        elif isinstance(item, dict):
            content = item.get('content', '') or ''
            url = item.get('url', '') or ''
            title = item.get('title', '') or ''
        else:
            # Fallback pour autres types
            content = str(item)
            url = ''
            title = ''
        
        # Normaliser les chaînes
        content = content.strip()
        url = url.strip()
        title = title.strip()
        
        # Créer la chaîne de hash
        hash_input = f"{url}|{title}|{content}"
        
        # Calculer SHA256
        return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
    
    @staticmethod
    def deduplicate_items_by_hash(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Déduplication d'une liste d'items par content_hash
        Garde le premier item rencontré pour chaque hash
        """
        seen_hashes: Set[str] = set()
        deduplicated: List[Dict[str, Any]] = []
        
        for item in items:
            content_hash = item.get('content_hash')
            
            # Calculer le hash si manquant
            if not content_hash:
                content_hash = DeduplicationManager.calculate_content_hash(item)
                item['content_hash'] = content_hash
            
            # Ajouter si pas déjà vu
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                deduplicated.append(item)
            else:
                logger.debug(f"Item deduplicated: {item.get('item_id', 'unknown')}")
        
        logger.info(f"Deduplication: {len(items)} → {len(deduplicated)} items ({len(items) - len(deduplicated)} duplicates removed)")
        return deduplicated
    
    @staticmethod
    def find_duplicates_in_items(items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Trouver tous les doublons dans une liste d'items
        Retourne un dict {hash: [items_with_same_hash]}
        """
        hash_groups: Dict[str, List[Dict[str, Any]]] = {}
        
        for item in items:
            content_hash = item.get('content_hash')
            
            if not content_hash:
                content_hash = DeduplicationManager.calculate_content_hash(item)
                item['content_hash'] = content_hash
            
            if content_hash not in hash_groups:
                hash_groups[content_hash] = []
            
            hash_groups[content_hash].append(item)
        
        # Garder seulement les groupes avec plus d'un item
        duplicates = {h: items for h, items in hash_groups.items() if len(items) > 1}
        
        return duplicates
    
    @staticmethod
    def merge_duplicate_metadata(items_with_same_hash: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Fusionner les métadonnées d'items avec le même hash
        Garde le plus ancien comme base et ajoute les métadonnées des autres
        """
        if not items_with_same_hash:
            return {}
        
        # Trier par date de publication (plus ancien en premier)
        sorted_items = sorted(
            items_with_same_hash,
            key=lambda x: x.get('published_at', ''),
            reverse=False
        )
        
        # Prendre le plus ancien comme base
        base_item = sorted_items[0].copy()
        
        # Ajouter métadonnées de déduplication
        base_item['deduplication_info'] = {
            'total_occurrences': len(items_with_same_hash),
            'first_seen': base_item.get('published_at'),
            'last_seen': sorted_items[-1].get('published_at'),
            'seen_in_runs': [item.get('warehouse_run_id') for item in items_with_same_hash if item.get('warehouse_run_id')],
            'seen_in_sources': list(set(item.get('source_key') for item in items_with_same_hash if item.get('source_key')))
        }
        
        return base_item