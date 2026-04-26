#!/usr/bin/env python3
"""
Utilitaires de gestion mémoire warehouse
"""

import json
from pathlib import Path
from typing import List, Dict, Iterator


class MemoryManager:
    """Gestionnaire de mémoire pour warehouse"""
    
    @staticmethod
    def stream_large_file(file_path: Path, chunk_size: int = 1000):
        """Lire gros fichier par chunks"""
        with open(file_path, 'r', encoding='utf-8') as f:
            chunk = []
            for line in f:
                chunk.append(json.loads(line.strip()))
                if len(chunk) >= chunk_size:
                    yield chunk
                    chunk = []
            if chunk:
                yield chunk
    
    @staticmethod
    def optimize_item_loading(items: List[Dict], required_fields: List[str]) -> List[Dict]:
        """Optimiser chargement items en gardant seulement champs requis"""
        optimized_items = []
        for item in items:
            optimized_item = {
                field: item.get(field) 
                for field in required_fields 
                if field in item
            }
            optimized_items.append(optimized_item)
        return optimized_items
            