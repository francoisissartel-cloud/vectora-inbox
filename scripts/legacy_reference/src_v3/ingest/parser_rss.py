"""
Parser RSS V3 - Parsing des flux RSS avec profils configurables

Ce module parse les flux RSS selon les profils d'ingestion V3 :
- rss_full : contenu complet dans le feed, pas de fetch individuel
- rss_with_fetch : listing RSS + fetch article complet + prefetch_filter optionnel

Responsabilités :
- Parsing RSS via feedparser
- Prefetch filter pour économiser les requêtes HTTP
- Extraction de contenu complet si nécessaire
- Extraction de dates guidée
- Métadonnées de performance
"""

from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import feedparser

from .models import ResolvedSource, StructuredItem
from .fetcher import Fetcher, FetchResult
from .content_extractor import ContentExtractorV3
from .date_extractor import DateExtractorV3
from .config_loader_v3 import CanonicalConfig
from ..shared.utils import calculate_content_hash, calculate_item_id, measure_duration_ms

logger = logging.getLogger(__name__)


class RSSParsingResult:
    """
    Résultat du parsing RSS avec métadonnées.
    """
    def __init__(self, items: List[StructuredItem], success: bool,
                 items_found: int = 0, items_prefetch_skipped: int = 0,
                 duration_ms: int = 0, error: Optional[str] = None):
        self.items = items
        self.success = success
        self.items_found = items_found
        self.items_prefetch_skipped = items_prefetch_skipped
        self.duration_ms = duration_ms
        self.error = error


class RSSParserV3:
    """
    Parser RSS V3 avec support des profils et prefetch filter.
    """
    
    def __init__(self, canonical_config: CanonicalConfig, fetcher: Fetcher, url_cache=None):
        """
        Initialise le parser RSS.
        
        Args:
            canonical_config: Configuration canonical pour les filtres
            fetcher: Instance de fetcher pour les requêtes HTTP
            url_cache: Cache URL optionnel pour éviter les refetch
        """
        self.canonical_config = canonical_config
        self.fetcher = fetcher
        self.url_cache = url_cache
        self.content_extractor = ContentExtractorV3()
        self.date_extractor = DateExtractorV3()
        logger.info(f"RSSParserV3 initialisé (cache: {'activé' if url_cache else 'désactivé'})")
    
    def parse_rss_source(self, source: ResolvedSource, run_id: str, client_config=None) -> RSSParsingResult:
        """
        Parse une source RSS selon son profil.
        
        Args:
            source: Source résolue avec configuration
            run_id: ID du run en cours
            client_config: Configuration client pour le cache
        
        Returns:
            Résultat du parsing avec items et métadonnées
        """
        start_time = datetime.now()
        logger.info(f"Parsing RSS : {source.source_key} (profil: {source.ingestion_profile})")
        
        try:
            # Fetch du flux RSS
            fetch_result = self.fetcher.fetch_source_content(source)
            if not fetch_result.success:
                duration_ms = measure_duration_ms(start_time)
                return RSSParsingResult(
                    items=[],
                    success=False,
                    duration_ms=duration_ms,
                    error=f"Fetch RSS échoué: {fetch_result.error}"
                )
            
            # Parse du flux RSS
            feed = feedparser.parse(fetch_result.content)
            if not feed.entries:
                duration_ms = measure_duration_ms(start_time)
                logger.warning(f"Aucune entrée dans le flux RSS de {source.source_key}")
                return RSSParsingResult(
                    items=[],
                    success=True,
                    items_found=0,
                    duration_ms=duration_ms
                )
            
            logger.info(f"Flux RSS parsé : {len(feed.entries)} entrées trouvées")
            
            # Traitement selon le profil
            if source.ingestion_profile == "rss_full":
                result = self._parse_rss_full(feed, source, run_id, client_config)
            elif source.ingestion_profile == "rss_with_fetch":
                result = self._parse_rss_with_fetch(feed, source, run_id, client_config)
            else:
                duration_ms = measure_duration_ms(start_time)
                return RSSParsingResult(
                    items=[],
                    success=False,
                    duration_ms=duration_ms,
                    error=f"Profil RSS non supporté: {source.ingestion_profile}"
                )
            
            result.duration_ms = measure_duration_ms(start_time)
            logger.info(f"Parsing RSS terminé : {len(result.items)} items créés")
            return result
        
        except Exception as e:
            duration_ms = measure_duration_ms(start_time)
            logger.error(f"Erreur lors du parsing RSS de {source.source_key}: {e}")
            return RSSParsingResult(
                items=[],
                success=False,
                duration_ms=duration_ms,
                error=str(e)
            )
    
    def _parse_rss_full(self, feed, source: ResolvedSource, run_id: str, client_config=None) -> RSSParsingResult:
        """
        Parse un flux RSS avec contenu complet (pas de fetch individuel).
        
        Args:
            feed: Flux RSS parsé par feedparser
            source: Source résolue
            run_id: ID du run
            client_config: Configuration client pour le cache
        
        Returns:
            Résultat du parsing
        """
        logger.debug(f"Mode rss_full pour {source.source_key}")
        
        items = []
        max_items = source.profile_config.get('max_items', 50)
        cache_hits = 0
        cache_misses = 0
        
        for i, entry in enumerate(feed.entries[:max_items]):
            try:
                # Données de base depuis le feed
                title = self._clean_title(entry.get('title', ''))
                url = entry.get('link', '')
                summary = entry.get('summary', '')
                content = entry.get('content', [{}])[0].get('value', '') if entry.get('content') else summary
                
                if not title or not url:
                    logger.debug(f"Entrée {i+1} ignorée (titre ou URL manquant)")
                    continue
                
                # Vérifier le cache AVANT tout traitement coûteux
                if self.url_cache and client_config:
                    should_use_cache, cached_result = self.url_cache.should_use_cache(url, client_config)
                    
                    if should_use_cache:
                        cache_hits += 1
                        logger.debug(f"Cache HIT pour {url} - skip complètement cet item")
                        continue  # SKIP COMPLET : ne pas créer d'item
                    else:
                        cache_misses += 1
                        logger.debug(f"Cache MISS pour {url} - traitement complet")
                # Si pas de cache configuré, ne pas incrémenter les stats
                
                # Extraction de date
                item_data = {
                    'title': title,
                    'summary': summary,
                    'content': content,
                    'published': entry.get('published', ''),
                    'link': url
                }
                
                date_result = self.date_extractor.extract(item_data)
                
                # Créer le StructuredItem
                item = self._create_structured_item(
                    source=source,
                    run_id=run_id,
                    title=title,
                    url=url,
                    content=content,
                    date_result=date_result,
                    ingestion_metadata={
                        "fetch_duration_ms": 0,  # Pas de fetch individuel
                        "parse_duration_ms": 0,
                        "content_extraction_method": "rss_content",
                        "fallback_triggered": False,
                        "cache_hit": False  # Tous les items créés sont des cache miss
                    }
                )
                
                items.append(item)
                
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
                    self.url_cache.update_cache_entry(url, cache_entry, client_config)
                
                logger.debug(f"Item RSS créé : {title[:50]}...")
            
            except Exception as e:
                logger.warning(f"Erreur lors du traitement de l'entrée {i+1}: {e}")
                continue
        
        logger.info(f"RSS full terminé : {len(items)} items, cache: {cache_hits} hits/{cache_misses} misses")
        
        return RSSParsingResult(
            items=items,
            success=True,
            items_found=len(feed.entries),
            items_prefetch_skipped=0
        )
    
    def _parse_rss_with_fetch(self, feed, source: ResolvedSource, run_id: str, client_config=None) -> RSSParsingResult:
        """
        Parse un flux RSS avec fetch des articles complets.
        
        Args:
            feed: Flux RSS parsé par feedparser
            source: Source résolue
            run_id: ID du run
            client_config: Configuration client pour le cache
        
        Returns:
            Résultat du parsing
        """
        logger.debug(f"Mode rss_with_fetch pour {source.source_key} (prefetch_filter: {source.prefetch_filter})")
        
        items = []
        max_items = source.profile_config.get('max_items', 30)
        prefetch_skipped = 0
        cache_hits = 0
        cache_misses = 0
        
        # Charger les keywords pour prefetch_filter si activé
        prefetch_keywords = []
        if source.prefetch_filter:
            prefetch_keywords = self._load_prefetch_keywords()
            logger.info(f"Prefetch filter activé avec {len(prefetch_keywords)} keywords")
        
        for i, entry in enumerate(feed.entries[:max_items]):
            try:
                # Données de base depuis le feed
                title = self._clean_title(entry.get('title', ''))
                url = entry.get('link', '')
                summary = entry.get('summary', '')
                
                if not title or not url:
                    logger.debug(f"Entrée {i+1} ignorée (titre ou URL manquant)")
                    continue
                
                # Prefetch filter : vérifier si l'article mérite d'être fetchés
                if source.prefetch_filter and prefetch_keywords:
                    if not self._should_fetch_article(title, summary, prefetch_keywords):
                        logger.debug(f"Article skippé par prefetch filter : {title[:50]}...")
                        prefetch_skipped += 1
                        continue
                
                # Vérifier le cache AVANT tout traitement coûteux
                if self.url_cache and client_config:
                    should_use_cache, cached_result = self.url_cache.should_use_cache(url, client_config)
                    
                    if should_use_cache:
                        cache_hits += 1
                        logger.debug(f"Cache HIT pour {url} - skip complètement cet item")
                        # SKIP COMPLET : ne pas créer d'item, ne pas appliquer de filtres
                        continue
                    else:
                        cache_misses += 1
                        logger.debug(f"Cache MISS pour {url} - traitement complet")
                # Si pas de cache configuré, ne pas incrémenter les stats
                
                # Traitement complet pour les items non-cachés
                # Fetch de l'article complet
                fetch_start = datetime.now()
                fetch_result = self.fetcher.fetch_article_content(url, source)
                fetch_duration = measure_duration_ms(fetch_start)
                
                if not fetch_result.success:
                    logger.warning(f"Fetch échoué pour {url}: {fetch_result.error}")
                    continue
                
                # Extraction du contenu
                extract_start = datetime.now()
                content_result = self.content_extractor.extract_from_response_content(
                    fetch_result.content.encode('utf-8'),
                    'text/html',
                    url
                )
                extract_duration = measure_duration_ms(extract_start)
                
                content = content_result.content if content_result.success else summary
                content_extraction_method = "html_article" if content_result.success else "rss_summary"
                fallback_triggered = not content_result.success
                
                # Extraction de date (avec HTML si disponible)
                item_data = {
                    'title': title,
                    'summary': summary,
                    'content': content,
                    'published': entry.get('published', ''),
                    'link': url
                }
                
                date_result = self.date_extractor.extract(
                    item_data,
                    raw_html=fetch_result.content if 'fetch_result' in locals() and fetch_result.success else None,
                    date_selectors=source.date_selectors
                )
                
                # Créer le StructuredItem
                item = self._create_structured_item(
                    source=source,
                    run_id=run_id,
                    title=title,
                    url=url,
                    content=content,
                    date_result=date_result,
                    ingestion_metadata={
                        "fetch_duration_ms": fetch_duration,
                        "parse_duration_ms": extract_duration,
                        "content_extraction_method": content_extraction_method,
                        "fallback_triggered": fallback_triggered,
                        "cache_hit": False  # Tous les items créés sont des cache miss
                    }
                )
                
                items.append(item)
                
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
                    self.url_cache.update_cache_entry(url, cache_entry, client_config)
                
                logger.debug(f"Item RSS+fetch créé : {title[:50]}...")
            
            except Exception as e:
                logger.warning(f"Erreur lors du traitement de l'entrée {i+1}: {e}")
                continue
        
        logger.info(f"RSS with fetch terminé : {len(items)} items, {prefetch_skipped} skippés par prefetch, cache: {cache_hits} hits/{cache_misses} misses")
        
        return RSSParsingResult(
            items=items,
            success=True,
            items_found=len(feed.entries),
            items_prefetch_skipped=prefetch_skipped
        )
    
    def _load_prefetch_keywords(self) -> List[str]:
        """
        Charge les keywords pour le prefetch filter depuis canonical.
        
        Returns:
            Liste des keywords LAI pour prefetch
        """
        try:
            # Charger les scopes depuis filter_rules_v3.yaml
            prefetch_config = self.canonical_config.filter_rules.get('prefetch_filter', {})
            keyword_scopes = prefetch_config.get('keyword_scopes', [])
            
            if not keyword_scopes:
                logger.warning("Aucun keyword_scope configuré pour prefetch_filter")
                return []
            
            # Récupérer tous les keywords des scopes
            keywords = self.canonical_config.get_lai_keywords(keyword_scopes)
            logger.debug(f"Keywords prefetch chargés : {len(keywords)} termes")
            return keywords
        
        except Exception as e:
            logger.error(f"Erreur lors du chargement des keywords prefetch : {e}")
            return []
    
    def _should_fetch_article(self, title: str, summary: str, keywords: List[str]) -> bool:
        """
        Détermine si un article doit être fetchés selon le prefetch filter.
        
        Args:
            title: Titre de l'article
            summary: Résumé de l'article
            keywords: Liste des keywords LAI
        
        Returns:
            True si l'article doit être fetchés
        """
        if not keywords:
            return True  # Pas de filtre, fetch tout
        
        # Combiner titre et résumé pour la recherche
        text_to_search = f"{title} {summary}".lower()
        
        # Chercher au moins 1 keyword
        for keyword in keywords:
            if keyword.lower() in text_to_search:
                logger.debug(f"Keyword trouvé '{keyword}' → fetch article")
                return True
        
        return False
    
    def _clean_title(self, title: str) -> str:
        """
        Nettoie le titre RSS (supprime HTML, etc.).
        
        Args:
            title: Titre brut
        
        Returns:
            Titre nettoyé
        """
        if not title:
            return ""
        
        # Supprimer les balises HTML si présentes
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(title, 'html.parser')
        clean_title = soup.get_text(strip=True)
        
        return clean_title
    
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


def create_rss_parser(canonical_config: CanonicalConfig, fetcher: Fetcher) -> RSSParserV3:
    """
    Factory function pour créer un RSSParserV3.
    
    Args:
        canonical_config: Configuration canonical
        fetcher: Instance de fetcher
    
    Returns:
        Instance de RSSParserV3
    """
    return RSSParserV3(canonical_config, fetcher)