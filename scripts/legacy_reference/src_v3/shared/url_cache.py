"""
Système de Cache URL pour Vectora Inbox
Évite le reprocessing d'URLs déjà traitées dans le même contexte.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from ..shared.utils import calculate_content_hash

logger = logging.getLogger(__name__)


class URLCache:
    """Gestionnaire de cache URL intelligent pour l'ingestion"""
    
    def __init__(self, cache_dir: str = "cache/urls"):
        self.cache_dir = Path(cache_dir)
        self.cache_file = self.cache_dir / "url_cache_main.json"
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        
        # Créer le dossier si nécessaire
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Charger le cache existant
        self.cache_data = self._load_cache()
        
        # Sauvegarder immédiatement pour créer les fichiers
        if not self.cache_file.exists():
            self._save_cache()
        
        logger.info(f"URLCache initialized - {len(self.cache_data.get('url_entries', {}))} entries loaded")
    
    def _load_cache(self) -> Dict[str, Any]:
        """Charge le cache depuis le fichier JSON"""
        if not self.cache_file.exists():
            return self._create_empty_cache()
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Valider la structure
            if not isinstance(cache_data, dict) or 'url_entries' not in cache_data:
                logger.warning("Invalid cache structure, creating new cache")
                return self._create_empty_cache()
            
            return cache_data
            
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Failed to load cache, creating new one: {e}")
            return self._create_empty_cache()
    
    def _create_empty_cache(self) -> Dict[str, Any]:
        """Crée une structure de cache vide"""
        return {
            "cache_metadata": {
                "version": "1.0",
                "created_at": datetime.utcnow().isoformat() + "Z",
                "last_cleanup": datetime.utcnow().isoformat() + "Z"
            },
            "url_entries": {}
        }
    
    def _save_cache(self):
        """Sauvegarde le cache sur disque"""
        try:
            # Mettre à jour les métadonnées
            self.cache_data["cache_metadata"]["last_updated"] = datetime.utcnow().isoformat() + "Z"
            
            # Écrire le fichier principal
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_data, f, indent=2, ensure_ascii=False)
            
            # Écrire les métadonnées séparément
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_data["cache_metadata"], f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def should_use_cache(self, url: str, client_config: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Détermine si le cache doit être utilisé pour cette URL
        
        Returns:
            (should_use, cached_result): Tuple avec booléen et données cachées si applicable
        """
        # Vérifier si le cache est activé
        ingestion_config = client_config.get('ingestion', {})
        if not ingestion_config.get('use_url_cache', False):
            return False, None
        
        # Vérifier si l'URL est en cache
        url_entries = self.cache_data.get('url_entries', {})
        if url not in url_entries:
            return False, None
        
        cached_entry = url_entries[url]
        
        # Vérifier la cohérence du mode d'ingestion
        current_mode = ingestion_config.get('ingestion_mode', 'balanced')
        cached_mode = cached_entry.get('ingestion_mode')
        
        cache_settings = ingestion_config.get('cache_settings', {})
        invalidate_on_mode_change = cache_settings.get('invalidate_on_mode_change', True)
        
        if invalidate_on_mode_change and cached_mode != current_mode:
            logger.debug(f"Cache miss for {url}: mode changed from {cached_mode} to {current_mode}")
            return False, None
        
        # Vérifier l'expiration
        max_age_days = cache_settings.get('max_age_days', 30)
        last_processed = datetime.fromisoformat(cached_entry['last_processed'].replace('Z', '+00:00'))
        expiry_date = last_processed + timedelta(days=max_age_days)
        
        if datetime.now(last_processed.tzinfo) > expiry_date:
            logger.debug(f"Cache miss for {url}: entry expired")
            return False, None
        
        logger.debug(f"Cache hit for {url}: using cached result")
        return True, cached_entry
    
    def update_cache_entry(self, url: str, result: Dict[str, Any], client_config: Dict[str, Any]):
        """Met à jour une entrée du cache avec les résultats du processing"""
        
        # Vérifier si le cache est activé
        ingestion_config = client_config.get('ingestion', {})
        if not ingestion_config.get('use_url_cache', False):
            return
        
        current_time = datetime.utcnow().isoformat() + "Z"
        ingestion_mode = ingestion_config.get('ingestion_mode', 'balanced')
        
        # Créer l'entrée de cache
        cache_entry = {
            "ingestion_mode": ingestion_mode,
            "first_seen": current_time,
            "last_processed": current_time,
            "status": result.get('status', 'unknown'),
            "rejection_reason": result.get('rejection_reason'),
            "content_hash": result.get('content_hash'),
            "source_key": result.get('source_key'),
            "filter_results": result.get('filter_results', {})
        }
        
        # Mettre à jour ou créer l'entrée
        url_entries = self.cache_data.setdefault('url_entries', {})
        
        if url in url_entries:
            # Conserver first_seen si l'entrée existe déjà
            cache_entry['first_seen'] = url_entries[url].get('first_seen', current_time)
        
        url_entries[url] = cache_entry
        
        # Sauvegarder
        self._save_cache()
        
        logger.debug(f"Cache updated for {url}: status={cache_entry['status']}")
    
    def cleanup_expired_entries(self, client_config: Dict[str, Any]):
        """Nettoie les entrées expirées du cache"""
        
        ingestion_config = client_config.get('ingestion', {})
        cache_settings = ingestion_config.get('cache_settings', {})
        max_age_days = cache_settings.get('max_age_days', 30)
        
        current_time = datetime.utcnow()
        url_entries = self.cache_data.get('url_entries', {})
        
        expired_urls = []
        
        for url, entry in url_entries.items():
            try:
                last_processed = datetime.fromisoformat(entry['last_processed'].replace('Z', '+00:00'))
                expiry_date = last_processed + timedelta(days=max_age_days)
                
                if current_time.replace(tzinfo=last_processed.tzinfo) > expiry_date:
                    expired_urls.append(url)
                    
            except (ValueError, KeyError) as e:
                logger.warning(f"Invalid date in cache entry for {url}: {e}")
                expired_urls.append(url)
        
        # Supprimer les entrées expirées
        for url in expired_urls:
            del url_entries[url]
        
        if expired_urls:
            logger.info(f"Cleaned up {len(expired_urls)} expired cache entries")
            self.cache_data["cache_metadata"]["last_cleanup"] = current_time.isoformat() + "Z"
            self._save_cache()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du cache"""
        url_entries = self.cache_data.get('url_entries', {})
        
        # Compter par statut
        status_counts = {}
        mode_counts = {}
        
        for entry in url_entries.values():
            status = entry.get('status', 'unknown')
            mode = entry.get('ingestion_mode', 'unknown')
            
            status_counts[status] = status_counts.get(status, 0) + 1
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
        
        return {
            "total_entries": len(url_entries),
            "status_breakdown": status_counts,
            "mode_breakdown": mode_counts,
            "cache_metadata": self.cache_data.get("cache_metadata", {}),
            "cache_file_path": str(self.cache_file)
        }
    
    def invalidate_url(self, url: str):
        """Invalide une URL spécifique du cache"""
        url_entries = self.cache_data.get('url_entries', {})
        if url in url_entries:
            del url_entries[url]
            self._save_cache()
            logger.info(f"Invalidated cache entry for {url}")
    
    def clear_cache(self):
        """Vide complètement le cache"""
        self.cache_data = self._create_empty_cache()
        self._save_cache()
        logger.info("Cache cleared completely")