"""
Système de Cache URL Client-Spécifique pour Vectora Inbox
Chaque client a son propre cache pour éviter les faux négatifs entre clients.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from ..shared.utils import calculate_content_hash

logger = logging.getLogger(__name__)


class ClientSpecificUrlCache:
    """Gestionnaire de cache URL spécifique à un client"""
    
    def __init__(self, client_id: str, cache_base_dir: str = "cache/clients"):
        self.client_id = client_id
        self.cache_dir = Path(cache_base_dir) / client_id
        self.cache_file = self.cache_dir / "url_cache.json"
        self.metadata_file = self.cache_dir / "metadata.json"
        
        # Créer le dossier client si nécessaire
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Charger le cache existant
        self.cache_data = self._load_cache()
        
        # Sauvegarder immédiatement pour créer les fichiers
        if not self.cache_file.exists():
            self._save_cache()
        
        logger.info(f"ClientSpecificUrlCache initialized for {client_id} - {len(self.cache_data.get('url_entries', {}))} entries loaded")
    
    def _load_cache(self) -> Dict[str, Any]:
        """Charge le cache depuis le fichier JSON"""
        if not self.cache_file.exists():
            return self._create_empty_cache()
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Valider la structure
            if not isinstance(cache_data, dict) or 'url_entries' not in cache_data:
                logger.warning(f"Invalid cache structure for {self.client_id}, creating new cache")
                return self._create_empty_cache()
            
            return cache_data
            
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Failed to load cache for {self.client_id}, creating new one: {e}")
            return self._create_empty_cache()
    
    def _create_empty_cache(self) -> Dict[str, Any]:
        """Crée une structure de cache vide"""
        return {
            "cache_metadata": {
                "version": "2.0",
                "client_id": self.client_id,
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
            logger.error(f"Failed to save cache for {self.client_id}: {e}")
    
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
        
        logger.debug(f"Cache hit for {url} (client: {self.client_id}): using cached result")
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
            "client_id": self.client_id,
            "ingestion_mode": ingestion_mode,
            "first_seen": current_time,
            "last_processed": current_time,
            "status": result.get('status', 'unknown'),
            "rejection_reason": result.get('rejection_reason'),
            "content_hash": result.get('content_hash'),
            "source_key": result.get('source_key'),
            "filter_results": result.get('filter_results', {}),
            "processing_stats": {
                "fetch_time": result.get('fetch_time', 0),
                "parse_time": result.get('parse_time', 0)
            }
        }
        
        # Mettre à jour ou créer l'entrée
        url_entries = self.cache_data.setdefault('url_entries', {})
        
        if url in url_entries:
            # Conserver first_seen si l'entrée existe déjà
            cache_entry['first_seen'] = url_entries[url].get('first_seen', current_time)
        
        url_entries[url] = cache_entry
        
        # Sauvegarder
        self._save_cache()
        
        logger.debug(f"Cache updated for {url} (client: {self.client_id}): status={cache_entry['status']}")
    
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
            logger.info(f"Cleaned up {len(expired_urls)} expired cache entries for client {self.client_id}")
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
            "client_id": self.client_id,
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
            logger.info(f"Invalidated cache entry for {url} (client: {self.client_id})")
    
    def clear_cache(self):
        """Vide complètement le cache"""
        self.cache_data = self._create_empty_cache()
        self._save_cache()
        logger.info(f"Cache cleared completely for client {self.client_id}")
    
    def has_url(self, url: str) -> bool:
        """Vérifier si cette URL est en cache pour ce client"""
        url_entries = self.cache_data.get('url_entries', {})
        return url in url_entries
    
    def get_url_count(self) -> int:
        """Nombre total d'URLs en cache"""
        return len(self.cache_data.get('url_entries', {}))
    
    def get_hit_count(self) -> int:
        """Nombre de hits (approximatif basé sur les accès)"""
        # Cette métrique nécessiterait un tracking plus sophistiqué
        # Pour l'instant, on retourne 0
        return 0
    
    def get_miss_count(self) -> int:
        """Nombre de misses (approximatif)"""
        # Cette métrique nécessiterait un tracking plus sophistiqué
        # Pour l'instant, on retourne 0
        return 0
    
    def get_hit_rate(self) -> float:
        """Taux de hit (approximatif)"""
        # Cette métrique nécessiterait un tracking plus sophistiqué
        # Pour l'instant, on retourne 0.0
        return 0.0
    
    def count_unique_urls(self) -> int:
        """URLs uniques à ce client (nécessiterait analyse cross-client)"""
        # Pour l'instant, retourne le total
        return self.get_url_count()
    
    def get_storage_size(self) -> int:
        """Taille du cache en bytes"""
        try:
            return self.cache_file.stat().st_size if self.cache_file.exists() else 0
        except:
            return 0


class URLCache:
    """Classe de compatibilité - redirige vers ClientSpecificUrlCache"""
    
    def __init__(self, cache_dir: str = "cache/urls", client_id: str = None):
        if client_id is None:
            raise ValueError("client_id is required for URLCache. Use ClientSpecificUrlCache directly.")
        
        logger.warning("URLCache is deprecated. Use ClientSpecificUrlCache directly.")
        self._cache = ClientSpecificUrlCache(client_id)
    
    def should_use_cache(self, url: str, client_config: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        return self._cache.should_use_cache(url, client_config)
    
    def update_cache_entry(self, url: str, result: Dict[str, Any], client_config: Dict[str, Any]):
        return self._cache.update_cache_entry(url, result, client_config)
    
    def cleanup_expired_entries(self, client_config: Dict[str, Any]):
        return self._cache.cleanup_expired_entries(client_config)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        return self._cache.get_cache_stats()
    
    def invalidate_url(self, url: str):
        return self._cache.invalidate_url(url)
    
    def clear_cache(self):
        return self._cache.clear_cache()


class CrossClientCacheAnalyzer:
    """Analyseur pour comparer les caches entre clients"""
    
    def __init__(self, cache_base_dir: str = "cache/clients"):
        self.cache_base_dir = Path(cache_base_dir)
    
    def get_all_clients(self) -> List[str]:
        """Retourne la liste de tous les clients ayant un cache"""
        if not self.cache_base_dir.exists():
            return []
        
        clients = []
        for client_dir in self.cache_base_dir.iterdir():
            if client_dir.is_dir() and (client_dir / "url_cache.json").exists():
                clients.append(client_dir.name)
        
        return clients
    
    def analyze_overlap(self, client_a: str, client_b: str) -> Dict[str, Any]:
        """Analyse l'overlap entre deux clients"""
        cache_a = ClientSpecificUrlCache(client_a)
        cache_b = ClientSpecificUrlCache(client_b)
        
        urls_a = set(cache_a.cache_data.get('url_entries', {}).keys())
        urls_b = set(cache_b.cache_data.get('url_entries', {}).keys())
        
        shared_urls = urls_a.intersection(urls_b)
        
        return {
            "client_a": client_a,
            "client_b": client_b,
            "urls_a": len(urls_a),
            "urls_b": len(urls_b),
            "shared_urls": len(shared_urls),
            "overlap_rate": len(shared_urls) / max(len(urls_a), len(urls_b)) * 100 if urls_a or urls_b else 0,
            "shared_url_list": list(shared_urls)
        }
    
    def generate_cross_client_report(self) -> Dict[str, Any]:
        """Génère un rapport complet cross-client"""
        clients = self.get_all_clients()
        
        if len(clients) < 2:
            return {"error": "Need at least 2 clients for cross-client analysis"}
        
        overlaps = []
        for i, client_a in enumerate(clients):
            for client_b in clients[i+1:]:
                overlap = self.analyze_overlap(client_a, client_b)
                overlaps.append(overlap)
        
        # Stats globales
        all_urls = set()
        client_stats = {}
        
        for client in clients:
            cache = ClientSpecificUrlCache(client)
            urls = set(cache.cache_data.get('url_entries', {}).keys())
            all_urls.update(urls)
            client_stats[client] = {
                "url_count": len(urls),
                "cache_size": cache.get_storage_size()
            }
        
        return {
            "clients": clients,
            "client_stats": client_stats,
            "overlaps": overlaps,
            "global_stats": {
                "total_unique_urls": len(all_urls),
                "total_clients": len(clients)
            }
        }