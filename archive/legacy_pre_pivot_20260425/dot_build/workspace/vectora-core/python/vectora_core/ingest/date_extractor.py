from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from functools import lru_cache
import re
import logging

logger = logging.getLogger(__name__)

@dataclass
class DateResult:
    date: str
    source: str
    confidence: float

class DateExtractor:
    """Extraction unifiée de dates avec cascade simple - v2.0"""
    
    def extract(self, item_data: dict, raw_html: Optional[str] = None, pdf_metadata: Optional[dict] = None) -> DateResult:
        """Cascade: PDF → HTML → RSS → Text → URL → Fallback"""
        
        logger.info(f"[DATE_EXTRACT_V2] Starting extraction with content length: {len(item_data.get('content', ''))}")
        
        # PDF metadata (highest priority for PDFs)
        if pdf_metadata and pdf_metadata.get('creation_date'):
            date = pdf_metadata['creation_date']
            if date:
                return DateResult(date, "pdf_metadata", 0.95)
        
        if raw_html:
            date = self._extract_from_html(raw_html)
            if date:
                return DateResult(date, "html_metadata", 0.95)
        
        if 'published' in item_data:
            date = self._parse_date_string(item_data['published'])
            if date:
                return DateResult(date, "rss_pubdate", 0.90)
        
        text = f"{item_data.get('title', '')} {item_data.get('summary', '')} {item_data.get('content', '')[:1000]}"
        logger.info(f"[DATE_EXTRACT_V2] Text for extraction ({len(text)} chars): {text[:200]}")
        date = self._extract_from_text(text)
        if date:
            return DateResult(date, "text_extraction", 0.85)
        
        date = self._extract_from_url(item_data.get('link', ''))
        if date:
            return DateResult(date, "url_pattern", 0.60)
        
        return DateResult(datetime.now().strftime('%Y-%m-%d'), "fallback", 0.0)
    
    def _extract_from_html(self, html: str) -> Optional[str]:
        """Extrait date depuis JSON-LD, meta tags, <time>, et texte visible"""
        from bs4 import BeautifulSoup
        import json
        
        if not html:
            logger.info("[DATE_HTML] No HTML provided")
            return None
        
        logger.info(f"[DATE_HTML] Analyzing {len(html)} chars")
        soup = BeautifulSoup(html, 'html.parser')
        
        # JSON-LD
        scripts = soup.find_all('script', type='application/ld+json')
        logger.info(f"[DATE_HTML] Found {len(scripts)} JSON-LD scripts")
        
        for i, script in enumerate(scripts, 1):
            try:
                data = json.loads(script.string)
                logger.info(f"[DATE_HTML] Script {i}: type={type(data).__name__}")
                
                # Gérer @graph
                if isinstance(data, dict) and '@graph' in data:
                    logger.info(f"[DATE_HTML] Found @graph with {len(data['@graph'])} nodes")
                    for j, node in enumerate(data['@graph'], 1):
                        if isinstance(node, dict):
                            node_type = node.get('@type', 'Unknown')
                            logger.info(f"[DATE_HTML] Node {j}: @type={node_type}")
                            for key in ['datePublished', 'dateCreated', 'uploadDate']:
                                if key in node:
                                    logger.info(f"[DATE_HTML] Found {key}={node[key]}")
                                    parsed = self._parse_date_string(node[key])
                                    if parsed:
                                        logger.info(f"[DATE_HTML] SUCCESS: {parsed}")
                                        return parsed
                
                # Objet simple
                elif isinstance(data, dict):
                    for key in ['datePublished', 'dateCreated', 'uploadDate']:
                        if key in data:
                            logger.info(f"[DATE_HTML] Found {key}={data[key]}")
                            parsed = self._parse_date_string(data[key])
                            if parsed:
                                logger.info(f"[DATE_HTML] SUCCESS: {parsed}")
                                return parsed
            except Exception as e:
                logger.warning(f"[DATE_HTML] JSON-LD error: {e}")
        
        logger.info("[DATE_HTML] No date in JSON-LD, trying meta tags")
        
        # Meta tags
        for meta in soup.find_all('meta'):
            if meta.get('property') in ['article:published_time', 'datePublished', 'og:published_time']:
                date_val = meta.get('content', '')
                if date_val:
                    logger.info(f"[DATE_HTML] Found meta {meta.get('property')}={date_val}")
                    parsed = self._parse_date_string(date_val)
                    if parsed:
                        logger.info(f"[DATE_HTML] SUCCESS from meta: {parsed}")
                        return parsed
        
        # <time> tag
        time_tag = soup.find('time')
        if time_tag:
            date_val = time_tag.get('datetime') or time_tag.get_text()
            logger.info(f"[DATE_HTML] Found <time>={date_val}")
            parsed = self._parse_date_string(date_val)
            if parsed:
                logger.info(f"[DATE_HTML] SUCCESS from <time>: {parsed}")
                return parsed
        
        # NOUVEAU: Extraire texte visible et chercher date
        logger.info("[DATE_HTML] No structured date, trying visible text")
        visible_text = soup.get_text(separator=' ', strip=True)
        logger.info(f"[DATE_HTML] Extracted {len(visible_text)} chars of visible text")
        
        # Chercher date dans les premiers 3000 chars du texte visible
        date_from_text = self._extract_from_text(visible_text[:3000])
        if date_from_text:
            logger.info(f"[DATE_HTML] SUCCESS from visible text: {date_from_text}")
            return date_from_text
        
        logger.info("[DATE_HTML] No date found")
        return None
    
    def _extract_from_text(self, text: str) -> Optional[str]:
        """Extraction robuste avec patterns multiples + dateutil.parser"""
        from dateutil import parser
        import re
        
        if not text:
            return None
        
        logger.info(f"[DATE_TEXT] Analyzing {len(text)} chars")
        
        # Nettoyer espaces manquants ("10November2025" → "10 November 2025")
        text = re.sub(r'(\d)(January|February|March|April|May|June|July|August|September|October|November|December)', r'\1 \2', text, flags=re.IGNORECASE)
        text = re.sub(r'(\d{4})([A-Z])', r'\1 \2', text)
        
        # Chercher dans tout le texte fourni (limité à 3000 chars par l'appelant)
        search_text = text
        
        # Patterns exhaustifs couvrant tous les formats courants
        patterns = [
            # Formats avec jour de semaine (PRIORITÉ MAX)
            r'(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            r'(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})',
            
            # Formats US: "February 10, 2026" ou "Feb 10, 2026"
            r'([A-Z][a-z]+\.?\s+\d{1,2},?\s+\d{4})',
            
            # Formats EU: "10 February 2026" ou "10 Feb 2026"
            r'(\d{1,2}\s+[A-Z][a-z]+\.?\s+\d{4})',
            
            # Formats ISO: "2026-02-10"
            r'(\d{4}-\d{2}-\d{2})',
            
            # Formats slash: "02/10/2026" ou "10/02/2026"
            r'(\d{1,2}/\d{1,2}/\d{4})',
            
            # Formats avec tirets: "10-02-2026"
            r'(\d{1,2}-\d{1,2}-\d{4})',
        ]
        
        # Essayer chaque pattern
        for i, pattern in enumerate(patterns, 1):
            matches = re.findall(pattern, search_text, re.IGNORECASE)
            if matches:
                logger.info(f"[DATE_TEXT] Pattern {i} found {len(matches)} matches")
                for match in matches[:5]:  # Tester jusqu'à 5 matches
                    match_str = match if isinstance(match, str) else ' '.join(match)
                    # Nettoyer le match (enlever ponctuation superflue)
                    match_str = match_str.strip(' .,;:-')
                    logger.info(f"[DATE_TEXT] Trying: '{match_str}'")
                    
                    try:
                        # Parser avec dateutil (très permissif)
                        dt = parser.parse(match_str, fuzzy=False, dayfirst=False)
                        
                        # Validation: date raisonnable (pas trop ancienne, pas trop future)
                        year_diff = abs(dt.year - datetime.now().year)
                        if year_diff <= 5:  # Dans une fenêtre de ±5 ans
                            result = dt.strftime('%Y-%m-%d')
                            logger.info(f"[DATE_TEXT] SUCCESS: {result}")
                            return result
                        else:
                            logger.info(f"[DATE_TEXT] Rejected (year {dt.year} too far): {dt}")
                    except Exception as e:
                        logger.debug(f"[DATE_TEXT] Parse failed for '{match_str}': {e}")
                        continue
        
        # PAS de fuzzy parsing - trop de faux positifs
        logger.info("[DATE_TEXT] No date found with strict patterns")
        return None
    
    def _extract_from_url(self, url: str) -> Optional[str]:
        """Extrait date depuis patterns URL"""
        patterns = [
            r'/(\d{4})/(\d{2})/(\d{2})/',
            r'/(\d{4})-(\d{2})-(\d{2})/',
            r'date=(\d{4}-\d{2}-\d{2})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                if len(match.groups()) == 3:
                    return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
                else:
                    return match.group(1)
        
        return None
    
    def _parse_date_string(self, date_str: str) -> Optional[str]:
        """Parse string date vers format ISO (avec cache LRU)"""
        return _parse_date_string_cached(date_str)


@lru_cache(maxsize=1000)
def _parse_date_string_cached(date_str: str) -> Optional[str]:
    """Parse string date vers format ISO avec cache LRU pour performance."""
    try:
        from dateutil import parser
        dt = parser.parse(date_str)
        return dt.strftime('%Y-%m-%d')
    except:
        return None
