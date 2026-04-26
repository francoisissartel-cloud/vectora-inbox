"""
Parser HTML V3 - Parsing des pages HTML avec selectors configurables

Ce module parse les pages HTML selon les profils html_generic et html_pdf.
Il utilise les listing_selectors de source_configs pour extraire les liens,
avec fallback progressif vers des patterns génériques.

Responsabilités :
- Parsing HTML avec selectors configurés ou fallback
- Extraction de liens d'articles avec résolution d'URLs relatives
- Fetch et extraction de contenu pour chaque article
- Extraction de dates guidée par date_selectors
- Gestion de la pagination
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime
from urllib.parse import urljoin, urlparse
import re
from bs4 import BeautifulSoup

from .models import ResolvedSource, StructuredItem
from .fetcher import Fetcher, FetchResult
from .content_extractor import ContentExtractorV3
from .date_extractor import DateExtractorV3
from ..shared.utils import calculate_content_hash, calculate_item_id, measure_duration_ms

logger = logging.getLogger(__name__)


class HTMLParsingResult:
    """
    Résultat du parsing HTML avec métadonnées.
    """
    def __init__(self, items: List[StructuredItem], success: bool,
                 items_found: int = 0, pages_processed: int = 0,
                 fallback_triggered: bool = False, duration_ms: int = 0,
                 error: Optional[str] = None):
        self.items = items
        self.success = success
        self.items_found = items_found
        self.pages_processed = pages_processed
        self.fallback_triggered = fallback_triggered
        self.duration_ms = duration_ms
        self.error = error


class HTMLParserV3:
    """
    Parser HTML V3 avec selectors configurables et fallback progressif.
    """
    
    def __init__(self, fetcher: Fetcher, url_cache=None):
        """
        Initialise le parser HTML.
        
        Args:
            fetcher: Instance de fetcher pour les requêtes HTTP
            url_cache: Cache URL optionnel pour éviter les refetch
        """
        self.fetcher = fetcher
        self.url_cache = url_cache
        self.content_extractor = ContentExtractorV3()
        self.date_extractor = DateExtractorV3()
        
        # Statistiques de cache
        self.cache_stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "urls_cached": 0
        }
        
        logger.info(f"HTMLParserV3 initialisé (cache: {'activé' if url_cache else 'désactivé'})")
    
    def parse_html_source(self, source: ResolvedSource, run_id: str, client_config=None) -> HTMLParsingResult:
        """
        Parse une source HTML selon sa configuration.
        
        Args:
            source: Source résolue avec configuration
            run_id: ID du run en cours
            client_config: Configuration client pour le cache
        
        Returns:
            Résultat du parsing avec items et métadonnées
        """
        start_time = datetime.now()
        logger.info(f"Parsing HTML : {source.source_key} (profil: {source.ingestion_profile})")
        
        try:
            # Fetch des pages (avec pagination si configurée)
            fetch_results = self.fetcher.fetch_paginated_content(source)
            if not fetch_results or not any(r.success for r in fetch_results):
                duration_ms = measure_duration_ms(start_time)
                return HTMLParsingResult(
                    items=[],
                    success=False,
                    duration_ms=duration_ms,
                    error="Aucune page HTML fetchée avec succès"
                )
            
            # Extraire les liens depuis toutes les pages
            all_article_urls = []
            fallback_triggered = False
            
            for i, fetch_result in enumerate(fetch_results):
                if not fetch_result.success:
                    logger.warning(f"Page {i} échouée, ignorée")
                    continue
                
                urls, used_fallback = self._extract_article_urls(fetch_result.content, source)
                all_article_urls.extend(urls)
                if used_fallback:
                    fallback_triggered = True
                
                logger.debug(f"Page {i} : {len(urls)} liens trouvés")
            
            # Déduplication des URLs
            unique_urls = list(dict.fromkeys(all_article_urls))  # Préserve l'ordre
            logger.info(f"Total : {len(unique_urls)} liens uniques trouvés")
            
            if not unique_urls:
                duration_ms = measure_duration_ms(start_time)
                return HTMLParsingResult(
                    items=[],
                    success=True,
                    items_found=0,
                    pages_processed=len([r for r in fetch_results if r.success]),
                    fallback_triggered=fallback_triggered,
                    duration_ms=duration_ms
                )
            
            # Limiter le nombre d'articles selon le profil
            max_items = source.profile_config.get('max_items', 30)
            urls_to_process = unique_urls[:max_items]
            
            if len(unique_urls) > max_items:
                logger.info(f"Limitation à {max_items} articles (sur {len(unique_urls)} trouvés)")
            
            # Traiter chaque article
            items = []
            for i, article_url in enumerate(urls_to_process):
                try:
                    item = self._process_article(article_url, source, run_id, client_config)
                    if item:
                        items.append(item)
                        logger.debug(f"Article {i+1}/{len(urls_to_process)} traité : {item.title[:50]}...")
                    else:
                        logger.debug(f"Article {i+1} ignoré (traitement échoué ou cache hit)")
                
                except Exception as e:
                    logger.warning(f"Erreur lors du traitement de l'article {i+1} ({article_url}): {e}")
                    continue
            
            duration_ms = measure_duration_ms(start_time)
            logger.info(f"Parsing HTML terminé : {len(items)} items créés")
            
            return HTMLParsingResult(
                items=items,
                success=True,
                items_found=len(unique_urls),
                pages_processed=len([r for r in fetch_results if r.success]),
                fallback_triggered=fallback_triggered,
                duration_ms=duration_ms
            )
        
        except Exception as e:
            duration_ms = measure_duration_ms(start_time)
            logger.error(f"Erreur lors du parsing HTML de {source.source_key}: {e}")
            return HTMLParsingResult(
                items=[],
                success=False,
                duration_ms=duration_ms,
                error=str(e)
            )
    
    def _extract_article_urls(self, html_content: str, source: ResolvedSource) -> Tuple[List[str], bool]:
        """
        Extrait les URLs d'articles depuis le HTML avec fallback progressif.
        
        Args:
            html_content: Contenu HTML de la page
            source: Source résolue avec selectors
        
        Returns:
            Tuple (liste des URLs, fallback_utilisé)
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        fallback_triggered = False
        
        # Méthode 1 : Selectors configurés
        if source.listing_selectors:
            urls = self._extract_with_configured_selectors(soup, source)
            if urls:
                logger.debug(f"URLs trouvées avec selectors configurés : {len(urls)}")
                return self._resolve_relative_urls(urls, source.homepage_url), False
        
        # Méthode 2 : URL pattern configuré
        if source.listing_selectors and source.listing_selectors.get('url_pattern'):
            urls = self._extract_with_url_pattern(soup, source)
            if urls:
                logger.debug(f"URLs trouvées avec pattern configuré : {len(urls)}")
                return self._resolve_relative_urls(urls, source.homepage_url), False
        
        # Méthode 3 : Fallback patterns génériques
        logger.debug("Utilisation des patterns de fallback")
        fallback_triggered = True
        urls = self._extract_with_fallback_patterns(soup, source)
        
        return self._resolve_relative_urls(urls, source.homepage_url), fallback_triggered
    
    def _extract_with_configured_selectors(self, soup: BeautifulSoup, source: ResolvedSource) -> List[str]:
        """
        Extrait URLs avec les selectors configurés.
        
        Args:
            soup: Soup BeautifulSoup
            source: Source avec listing_selectors
        
        Returns:
            Liste des URLs trouvées
        """
        selectors = source.listing_selectors
        if not selectors:
            return []
        
        urls = []
        
        # Container + link selector
        container_selector = selectors.get('container')
        link_selector = selectors.get('link', 'a')
        
        if container_selector:
            logger.debug(f"Recherche avec container: {container_selector}")
            containers = soup.select(container_selector)
            logger.debug(f"Containers trouvés : {len(containers)}")
            
            for container in containers:
                links = container.select(link_selector) if link_selector != 'a' else container.find_all('a')
                for link in links:
                    href = link.get('href')
                    if href:
                        urls.append(href)
        
        return urls
    
    def _extract_with_url_pattern(self, soup: BeautifulSoup, source: ResolvedSource) -> List[str]:
        """
        Extrait URLs avec pattern d'URL configuré.
        
        Args:
            soup: Soup BeautifulSoup
            source: Source avec url_pattern
        
        Returns:
            Liste des URLs trouvées
        """
        url_pattern = source.listing_selectors.get('url_pattern')
        if not url_pattern:
            return []
        
        logger.debug(f"Recherche avec URL pattern: {url_pattern}")
        
        urls = []
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href')
            if href and url_pattern in href:
                urls.append(href)
        
        logger.debug(f"URLs matchant le pattern : {len(urls)}")
        return urls
    
    def _extract_with_fallback_patterns(self, soup: BeautifulSoup, source: ResolvedSource) -> List[str]:
        """
        Extrait URLs avec patterns de fallback génériques.
        
        Args:
            soup: Soup BeautifulSoup
            source: Source résolue
        
        Returns:
            Liste des URLs trouvées
        """
        urls = []
        
        # Patterns de fallback par ordre de priorité
        fallback_selectors = [
            'article a',
            '.news a',
            '.press a',
            '.post a',
            'main a',
            '.content a'
        ]
        
        for selector in fallback_selectors:
            links = soup.select(selector)
            if links:
                logger.debug(f"Fallback selector '{selector}' : {len(links)} liens")
                for link in links:
                    href = link.get('href')
                    if href:
                        urls.append(href)
                break  # Utiliser le premier selector qui trouve des résultats
        
        # Si aucun selector ne fonctionne, chercher par patterns d'URL
        if not urls:
            logger.debug("Fallback vers patterns d'URL génériques")
            url_patterns = [
                r'/press-release',
                r'/news/',
                r'/media/',
                r'/\d{4}/',  # Année dans l'URL
            ]
            
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href')
                if href:
                    for pattern in url_patterns:
                        if re.search(pattern, href, re.IGNORECASE):
                            urls.append(href)
                            break
        
        return urls
    
    def _resolve_relative_urls(self, urls: List[str], base_url: str) -> List[str]:
        """
        Résout les URLs relatives en URLs absolues.
        
        Args:
            urls: Liste des URLs (relatives ou absolues)
            base_url: URL de base pour résolution
        
        Returns:
            Liste des URLs absolues
        """
        resolved_urls = []
        
        for url in urls:
            if not url:
                continue
            
            # Si déjà absolue, garder telle quelle
            if url.startswith(('http://', 'https://')):
                resolved_urls.append(url)
            else:
                # Résoudre via urljoin
                resolved_url = urljoin(base_url, url)
                resolved_urls.append(resolved_url)
        
        return resolved_urls
    
    def _validate_article_url(self, url: str, source: ResolvedSource) -> dict:
        """
        Valide une URL sans la bloquer - retourne des métadonnées.
        
        Args:
            url: URL à valider
            source: Source résolue avec patterns d'exclusion
        
        Returns:
            Dictionnaire avec résultat de validation
        """
        validation_result = {
            "is_valid": True,
            "warnings": [],
            "url_type": "article"
        }
        
        # Patterns d'exclusion depuis config
        exclude_patterns = []
        if source.listing_selectors and 'url_exclude_patterns' in source.listing_selectors:
            exclude_patterns = source.listing_selectors['url_exclude_patterns']
        
        # Vérifier chaque pattern d'exclusion
        for pattern in exclude_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                validation_result["is_valid"] = False
                validation_result["warnings"].append(f"Matches exclude pattern: {pattern}")
                validation_result["url_type"] = "excluded"
                break
        
        # Patterns génériques d'exclusion (fallback)
        generic_exclude_patterns = [
            r'/author/',
            r'/category/',
            r'/tag/',
            r'/page/\d+',
            r'/(press-releases|news)/?$',  # Pages de listing
        ]
        
        if validation_result["is_valid"]:
            for pattern in generic_exclude_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    validation_result["is_valid"] = False
                    validation_result["warnings"].append(f"Matches generic exclude pattern: {pattern}")
                    validation_result["url_type"] = "generic_excluded"
                    break
        
        return validation_result
    
    def _process_article(self, article_url: str, source: ResolvedSource, run_id: str, client_config=None) -> Optional[StructuredItem]:
        """
        Traite un article individuel (fetch + extraction + date).
        
        Args:
            article_url: URL de l'article
            source: Source résolue
            run_id: ID du run
            client_config: Configuration client pour le cache
        
        Returns:
            StructuredItem ou None si échec
        """
        try:
            # Vérifier le cache AVANT tout traitement coûteux
            if self.url_cache and client_config:
                should_use_cache, cached_result = self.url_cache.should_use_cache(article_url, client_config)
                
                if should_use_cache:
                    self.cache_stats["cache_hits"] += 1
                    logger.debug(f"Cache HIT pour {article_url} - skip complètement cet item")
                    return None  # SKIP COMPLET : ne pas créer d'item
                else:
                    self.cache_stats["cache_misses"] += 1
                    logger.debug(f"Cache MISS pour {article_url} - traitement complet")
            # Si pas de cache configuré, ne pas incrémenter les stats
            
            # Validation avec mode bloquant activé (Phase 4.1)
            validation = self._validate_article_url(article_url, source)
            
            # Mode bloquant activé
            if not validation["is_valid"]:
                logger.info(f"URL filtrée : {article_url} - {validation['warnings']}")
                return None  # Skip cet article
            else:
                logger.debug(f"URL validation passed for {article_url}")
            
            # Continue le traitement normal...
            
            # Fetch de l'article
            fetch_start = datetime.now()
            fetch_result = self.fetcher.fetch_article_content(article_url, source)
            fetch_duration = measure_duration_ms(fetch_start)
            
            if not fetch_result.success:
                logger.debug(f"Fetch échoué pour {article_url}: {fetch_result.error}")
                return None
            
            # Extraction du contenu
            extract_start = datetime.now()
            content_result = self.content_extractor.extract_from_response_content(
                fetch_result.content.encode('utf-8'),
                fetch_result.headers.get('content-type', 'text/html'),
                article_url
            )
            extract_duration = measure_duration_ms(extract_start)
            
            if not content_result.success or not content_result.content:
                logger.debug(f"Extraction de contenu échouée pour {article_url}")
                return None
            
            # Extraction du titre depuis HTML
            soup = BeautifulSoup(fetch_result.content, 'html.parser')
            title = self._extract_title(soup, article_url)
            
            if not title:
                logger.debug(f"Titre non trouvé pour {article_url}")
                return None
            
            # Extraction de date (avec guidage si configuré)
            item_data = {
                'title': title,
                'content': content_result.content,
                'link': article_url
            }
            
            date_result = self.date_extractor.extract(
                item_data,
                raw_html=fetch_result.content,
                date_selectors=source.date_selectors
            )
            
            # Créer le StructuredItem avec métadonnées de validation
            ingestion_metadata = {
                "fetch_duration_ms": fetch_duration,
                "parse_duration_ms": extract_duration,
                "content_extraction_method": "html_article",
                "fallback_triggered": False,
                "url_validation": validation  # Ajout des métadonnées de validation
            }
            
            item = self._create_structured_item(
                source=source,
                run_id=run_id,
                title=title,
                url=article_url,
                content=content_result.content,
                date_result=date_result,
                ingestion_metadata=ingestion_metadata
            )
            
            # Mettre à jour le cache pour les nouveaux items
            if self.url_cache and client_config:
                cache_entry = {
                    "status": "processed",
                    "rejection_reason": None,
                    "content_hash": item.content_hash,
                    "source_key": item.source_key,
                    "title": item.title,
                    "published_at": item.published_at,
                    "filter_results": {}
                }
                self.url_cache.update_cache_entry(article_url, cache_entry, client_config)
                self.cache_stats["urls_cached"] += 1
            
            return item
        
        except Exception as e:
            logger.warning(f"Erreur lors du traitement de {article_url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup, url: str) -> str:
        """
        Extrait le titre depuis HTML.
        
        Args:
            soup: Soup BeautifulSoup
            url: URL pour logging
        
        Returns:
            Titre extrait ou chaîne vide
        """
        # Ordre de priorité pour le titre - <title> en premier pour Taiwan Liposome
        title_selectors = [
            'title',  # Déplacé en premier pour Taiwan Liposome
            'h1',
            '.title',
            '.post-title',
            '.article-title',
            '.entry-title'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                # Réduire la limite à 5 caractères pour Taiwan Liposome
                if title and len(title) > 5:  # Réduit de 10 à 5
                    return title
        
        logger.debug(f"Aucun titre trouvé pour {url}")
        return ""
    
    def _create_structured_item(self, source: ResolvedSource, run_id: str, title: str,
                              url: str, content: str, date_result, 
                              ingestion_metadata: Dict[str, Any]) -> StructuredItem:
        """
        Crée un StructuredItem V3 depuis les données extraites.
        
        Args:
            source: Source résolue
            run_id: ID du run
            title: Titre de l'article
            url: URL de l'article
            content: Contenu extrait
            date_result: Résultat d'extraction de date
            ingestion_metadata: Métadonnées d'ingestion
        
        Returns:
            StructuredItem V3 complet
        """
        # Calculer les hashes et IDs
        item_id = calculate_item_id(source.source_key, url)
        content_hash = calculate_content_hash(content)
        
        # Construire les métadonnées de date
        date_extraction = {
            "date_found": bool(date_result.date),
            "date_source": date_result.source,
            "confidence": date_result.confidence,
            "raw_date_text": date_result.raw_date_text,
            "extraction_method": date_result.extraction_method
        }
        
        return StructuredItem(
            item_id=item_id,
            run_id=run_id,
            source_key=source.source_key,
            source_type=source.source_type,
            actor_type=source.actor_type,
            title=title,
            url=url,
            published_at=date_result.date if date_result.date else None,
            ingested_at=datetime.utcnow().isoformat() + "Z",
            content=content,
            content_length=len(content),
            language=source.default_language,
            content_hash=content_hash,
            ingestion_profile_used=source.ingestion_profile,
            date_extraction=date_extraction,
            filter_analysis={},  # Sera rempli par le filter_engine
            ingestion_metadata=ingestion_metadata
        )


def create_html_parser(fetcher: Fetcher, url_cache=None) -> HTMLParserV3:
    """
    Factory function pour créer un HTMLParserV3.
    
    Args:
        fetcher: Instance de fetcher
        url_cache: Cache URL optionnel
    
    Returns:
        Instance de HTMLParserV3
    """
    return HTMLParserV3(fetcher, url_cache)