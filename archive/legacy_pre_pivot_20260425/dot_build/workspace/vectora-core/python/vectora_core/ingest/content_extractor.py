import requests
from bs4 import BeautifulSoup
import io
from typing import Optional, List, Dict
import asyncio
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
import logging

logger = logging.getLogger(__name__)

# Configuration limites enrichissement
MAX_ENRICHMENT_PER_SOURCE = 10
MAX_ENRICHMENT_TOTAL = 50
MAX_CONCURRENT_ENRICHMENT = 5

class ContentExtractor:
    """Extraction unifiée HTML/PDF avec trafilatura et PyMuPDF"""
    
    def __init__(self, timeout: int = 15, max_length: int = 3000):
        self.timeout = timeout
        self.max_length = max_length
        self.enrichment_count = 0
    
    def extract(self, url: str) -> Optional[str]:
        """Extrait contenu depuis URL (HTML ou PDF) - version synchrone"""
        try:
            response = requests.get(url, timeout=self.timeout)
            if response.status_code != 200:
                return None
            
            content_type = response.headers.get('content-type', '').lower()
            
            if 'pdf' in content_type:
                return self._extract_pdf(response.content)
            else:
                return self._extract_html(response.content, url)
        
        except Exception as e:
            logger.warning(f"Content extraction failed for {url[:60]}: {e}")
            return None
    
    async def extract_async(self, url: str, session) -> Optional[str]:
        """Extrait contenu depuis URL (HTML ou PDF) - version asynchrone"""
        if not AIOHTTP_AVAILABLE:
            logger.warning("aiohttp not available, falling back to sync extraction")
            return self.extract(url)
        
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                if response.status != 200:
                    return None
                
                content_type = response.headers.get('content-type', '').lower()
                content = await response.read()
                
                if 'pdf' in content_type:
                    return self._extract_pdf(content)
                else:
                    return self._extract_html(content, url)
        
        except Exception as e:
            logger.warning(f"Async content extraction failed for {url[:60]}: {e}")
            return None
    
    async def enrich_items_async(self, items: List[Dict], max_per_source: int = MAX_ENRICHMENT_PER_SOURCE) -> List[Dict]:
        """Enrichit items en parallèle avec limite par source et globale."""
        if not AIOHTTP_AVAILABLE:
            logger.info("aiohttp not available, skipping async enrichment")
            return items
        
        if not items:
            return items
        
        # Grouper par source
        by_source = {}
        for item in items:
            source_key = item.get('source_key', 'unknown')
            if source_key not in by_source:
                by_source[source_key] = []
            by_source[source_key].append(item)
        
        # Sélectionner items à enrichir (limites)
        to_enrich = []
        for source_key, source_items in by_source.items():
            # Filtrer items avec contenu court
            short_items = [item for item in source_items if len(item.get('content', '')) < 300]
            # Limiter par source
            selected = short_items[:max_per_source]
            to_enrich.extend(selected)
            
            if len(short_items) > max_per_source:
                logger.info(f"{source_key}: {len(short_items)} items courts, enrichissement limité à {max_per_source}")
        
        # Limiter total global
        if len(to_enrich) > MAX_ENRICHMENT_TOTAL:
            logger.info(f"Enrichissement limité à {MAX_ENRICHMENT_TOTAL} items (sur {len(to_enrich)} candidats)")
            to_enrich = to_enrich[:MAX_ENRICHMENT_TOTAL]
        
        if not to_enrich:
            logger.info("Aucun item à enrichir")
            return items
        
        logger.info(f"Enrichissement asynchrone de {len(to_enrich)} items avec max {MAX_CONCURRENT_ENRICHMENT} concurrent")
        
        # Enrichir en parallèle avec semaphore
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_ENRICHMENT)
        
        async def enrich_one(item):
            async with semaphore:
                url = item.get('link', '')
                if not url:
                    return
                
                try:
                    async with aiohttp.ClientSession() as session:
                        enriched_content = await self.extract_async(url, session)
                        if enriched_content and len(enriched_content) > len(item.get('content', '')):
                            item['content'] = enriched_content
                            item['enriched'] = True
                            logger.debug(f"Enrichi: {url[:60]} → {len(enriched_content)} chars")
                except Exception as e:
                    logger.warning(f"Enrichissement échoué pour {url[:60]}: {e}")
        
        await asyncio.gather(*[enrich_one(item) for item in to_enrich], return_exceptions=True)
        
        enriched_count = sum(1 for item in items if item.get('enriched', False))
        logger.info(f"Enrichissement terminé: {enriched_count}/{len(to_enrich)} items enrichis")
        
        return items
    
    def _extract_html(self, content: bytes, url: str = "") -> str:
        """Extrait texte depuis HTML avec BeautifulSoup"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            for tag in ['script', 'style', 'nav', 'header', 'footer', 'aside']:
                for elem in soup.find_all(tag):
                    elem.decompose()
            
            main = soup.find('main') or soup.find('article') or soup.find('body')
            if not main:
                main = soup
            
            text = main.get_text(separator=' ', strip=True)
            logger.info(f"HTML extraction: {len(text)} chars")
            return text[:self.max_length]
        except Exception as e:
            logger.error(f"HTML extraction failed: {e}")
            return ""
    
    def _extract_pdf(self, content: bytes) -> str:
        """Extrait texte depuis PDF avec PyMuPDF - FULL TEXT"""
        try:
            from .pdf_extractor import PDFExtractor
            extractor = PDFExtractor()
            result = extractor.extract(content, url="")
            text = result.get('text', '')
            logger.info(f"PDF extraction: {len(text)} chars, {result['metadata']['pages']} pages")
            return text  # Return FULL text, no truncation
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            return ""
