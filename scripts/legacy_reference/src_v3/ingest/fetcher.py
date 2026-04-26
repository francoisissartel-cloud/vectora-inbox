"""
Fetcher V3 - Récupération HTTP avec retry/backoff

Ce module gère toutes les opérations de fetch HTTP pour l'ingestion V3.
Il est piloté par les profils d'ingestion et gère les retry, timeout,
rate limiting et pagination selon la configuration de chaque source.

Responsabilités :
- Fetch HTTP avec retry/backoff exponentiel
- Timeout configuré par profil d'ingestion
- Rate limiting entre sources
- Gestion de la pagination
- User-Agent réaliste
- Métadonnées de performance
"""

from typing import Dict, Any, Optional, List
import logging
import time
import requests
from datetime import datetime
from urllib.parse import urljoin, urlparse
import random

from .models import ResolvedSource
from ..shared.utils import measure_duration_ms

logger = logging.getLogger(__name__)


class FetchResult:
    """
    Résultat d'un fetch HTTP avec métadonnées.
    """
    def __init__(self, url: str, success: bool, content: str = "", 
                 status_code: Optional[int] = None, duration_ms: int = 0,
                 error: Optional[str] = None, headers: Optional[Dict] = None):
        self.url = url
        self.success = success
        self.content = content
        self.status_code = status_code
        self.duration_ms = duration_ms
        self.error = error
        self.headers = headers or {}
        self.fetched_at = datetime.utcnow().isoformat() + "Z"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit le résultat en dictionnaire pour logging."""
        return {
            "url": self.url,
            "success": self.success,
            "status_code": self.status_code,
            "content_length": len(self.content) if self.content else 0,
            "duration_ms": self.duration_ms,
            "error": self.error,
            "fetched_at": self.fetched_at
        }


class Fetcher:
    """
    Fetcher HTTP V3 avec retry/backoff et rate limiting.
    """
    
    def __init__(self):
        """Initialise le fetcher avec configuration par défaut."""
        self.session = requests.Session()
        
        # Headers anti-détection simplifiés (moins suspects)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br'
        })
        
        # Rate limiting : temps minimum entre deux requêtes (augmenté pour Fierce)
        self.min_delay_between_requests = 2.0  # secondes (plus conservateur)
        self.last_request_time = 0
        
        logger.info("Fetcher V3 initialisé avec headers anti-détection")
    
    def fetch_source_content(self, source: ResolvedSource) -> FetchResult:
        """
        Fetch le contenu principal d'une source (page de listing).
        
        Args:
            source: Source résolue avec sa configuration
        
        Returns:
            Résultat du fetch avec contenu et métadonnées
        """
        logger.info(f"Fetch de la source : {source.source_key} ({source.news_url})")
        
        # Configuration depuis le profil
        timeout = source.profile_config.get('fetch_timeout_seconds', 30)
        max_retries = 3
        
        return self._fetch_with_retry(
            url=source.news_url,
            timeout=timeout,
            max_retries=max_retries,
            context=f"source_{source.source_key}"
        )
    
    def fetch_article_content(self, article_url: str, source: ResolvedSource) -> FetchResult:
        """
        Fetch le contenu d'un article individuel.
        
        Args:
            article_url: URL de l'article à fetcher
            source: Source résolue (pour config timeout)
        
        Returns:
            Résultat du fetch avec contenu et métadonnées
        """
        logger.debug(f"Fetch article : {article_url}")
        
        # Résoudre l'URL relative en absolue si nécessaire
        if article_url.startswith('/'):
            base_url = source.homepage_url
            article_url = urljoin(base_url, article_url)
        
        # Configuration depuis le profil
        timeout = source.profile_config.get('fetch_timeout_seconds', 30)
        max_retries = 2  # Moins de retry pour les articles individuels
        
        return self._fetch_with_retry(
            url=article_url,
            timeout=timeout,
            max_retries=max_retries,
            context=f"article_{source.source_key}",
            extra_headers={'Referer': source.news_url}
        )
    
    def fetch_paginated_content(self, source: ResolvedSource) -> List[FetchResult]:
        """
        Fetch le contenu avec pagination si configurée.
        
        Args:
            source: Source résolue avec config pagination
        
        Returns:
            Liste des résultats de fetch (une par page)
        """
        pagination_config = source.pagination
        if not pagination_config or not pagination_config.get('enabled', False):
            # Pas de pagination, fetch simple
            return [self.fetch_source_content(source)]
        
        logger.info(f"Fetch avec pagination pour {source.source_key}")
        
        results = []
        max_pages = pagination_config.get('max_pages', 1)
        pattern = pagination_config.get('pattern', '?page={n}')
        
        for page_num in range(max_pages):
            # Construire l'URL de la page
            if page_num == 0:
                # Page 0 = URL de base
                page_url = source.news_url
            else:
                # Pages suivantes selon le pattern
                page_url = source.news_url + pattern.format(n=page_num)
            
            logger.debug(f"Fetch page {page_num} : {page_url}")
            
            # Fetch la page
            timeout = source.profile_config.get('fetch_timeout_seconds', 30)
            result = self._fetch_with_retry(
                url=page_url,
                timeout=timeout,
                max_retries=2,
                context=f"page_{page_num}_{source.source_key}"
            )
            
            results.append(result)
            
            # Si la page échoue, arrêter la pagination
            if not result.success:
                logger.warning(f"Page {page_num} échouée, arrêt de la pagination")
                break
            
            # Si la page est vide ou très courte, arrêter
            if len(result.content) < 500:
                logger.info(f"Page {page_num} courte ({len(result.content)} chars), fin de pagination")
                break
        
        logger.info(f"Pagination terminée : {len(results)} pages fetchées")
        return results
    
    def _fetch_with_retry(self, url: str, timeout: int, max_retries: int, 
                         context: str = "", extra_headers: Dict[str, str] = None) -> FetchResult:
        """
        Fetch une URL avec retry/backoff exponentiel.
        
        Args:
            url: URL à fetcher
            timeout: Timeout en secondes
            max_retries: Nombre maximum de tentatives
            context: Contexte pour logging
        
        Returns:
            Résultat du fetch
        """
        start_time = datetime.now()
        
        for attempt in range(max_retries + 1):
            try:
                # Rate limiting : attendre si nécessaire
                self._apply_rate_limiting()
                
                # Tentative de fetch
                logger.debug(f"Tentative {attempt + 1}/{max_retries + 1} : {url}")
                
                # Créer une nouvelle session pour cette requête (anti-détection)
                session = requests.Session()
                session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9'
                })
                
                # Préparer les headers pour cette requête
                headers = {}
                if extra_headers:
                    headers.update(extra_headers)
                
                response = session.get(
                    url,
                    timeout=timeout,
                    allow_redirects=True,
                    headers=headers
                )
                
                session.close()
                
                duration_ms = measure_duration_ms(start_time)
                
                # Vérifier le status code
                if response.status_code == 200:
                    logger.debug(f"✅ Fetch réussi : {url} ({duration_ms}ms)")
                    return FetchResult(
                        url=url,
                        success=True,
                        content=response.text,
                        status_code=response.status_code,
                        duration_ms=duration_ms,
                        headers=dict(response.headers)
                    )
                else:
                    logger.warning(f"Status code {response.status_code} pour {url}")
                    
                    # Certains codes ne méritent pas de retry
                    if response.status_code in [404, 403, 401]:
                        return FetchResult(
                            url=url,
                            success=False,
                            status_code=response.status_code,
                            duration_ms=duration_ms,
                            error=f"HTTP {response.status_code}"
                        )
            
            except requests.exceptions.Timeout:
                duration_ms = measure_duration_ms(start_time)
                logger.warning(f"Timeout ({timeout}s) pour {url} - tentative {attempt + 1}")
                if attempt == max_retries:
                    return FetchResult(
                        url=url,
                        success=False,
                        duration_ms=duration_ms,
                        error="Timeout"
                    )
            
            except requests.exceptions.ConnectionError as e:
                duration_ms = measure_duration_ms(start_time)
                logger.warning(f"Erreur de connexion pour {url} : {e}")
                if attempt == max_retries:
                    return FetchResult(
                        url=url,
                        success=False,
                        duration_ms=duration_ms,
                        error=f"Connection error: {str(e)}"
                    )
            
            except Exception as e:
                duration_ms = measure_duration_ms(start_time)
                logger.error(f"Erreur inattendue pour {url} : {e}")
                return FetchResult(
                    url=url,
                    success=False,
                    duration_ms=duration_ms,
                    error=f"Unexpected error: {str(e)}"
                )
            
            # Backoff exponentiel avant retry
            if attempt < max_retries:
                backoff_delay = (2 ** attempt) + random.uniform(0, 1)
                logger.debug(f"Attente {backoff_delay:.1f}s avant retry")
                time.sleep(backoff_delay)
        
        # Toutes les tentatives ont échoué
        duration_ms = measure_duration_ms(start_time)
        return FetchResult(
            url=url,
            success=False,
            duration_ms=duration_ms,
            error=f"Max retries ({max_retries}) exceeded"
        )
    
    def _apply_rate_limiting(self):
        """
        Applique le rate limiting entre les requêtes.
        """
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_delay_between_requests:
            sleep_time = self.min_delay_between_requests - time_since_last_request
            logger.debug(f"Rate limiting : attente {sleep_time:.1f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def is_valid_url(self, url: str) -> bool:
        """
        Vérifie si une URL est valide et fetchable.
        
        Args:
            url: URL à vérifier
        
        Returns:
            True si l'URL semble valide
        """
        if not url:
            return False
        
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False
    
    def resolve_relative_url(self, relative_url: str, base_url: str) -> str:
        """
        Résout une URL relative en URL absolue.
        
        Args:
            relative_url: URL relative ou absolue
            base_url: URL de base pour résolution
        
        Returns:
            URL absolue
        """
        if not relative_url:
            return ""
        
        # Si déjà absolue, retourner telle quelle
        if relative_url.startswith(('http://', 'https://')):
            return relative_url
        
        # Résoudre via urljoin
        return urljoin(base_url, relative_url)
    
    def close(self):
        """Ferme la session HTTP."""
        if self.session:
            self.session.close()
            logger.debug("Session HTTP fermée")


def create_fetcher() -> Fetcher:
    """
    Factory function pour créer un Fetcher.
    
    Returns:
        Instance de Fetcher configurée
    """
    return Fetcher()