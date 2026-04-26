"""
Date Extractor V3 - Extraction de dates avec guidage par source_configs

Version V3 du date extractor avec support pour le guidage par date_selectors
depuis source_configs_v3.yaml. Conserve la cascade éprouvée de V2 mais
permet d'optimiser l'extraction selon la configuration de chaque source.

Responsabilités :
- Cascade d'extraction robuste (JSON-LD → Meta → Time → RSS → Text → URL)
- Guidage par date_selectors pour optimiser l'extraction
- Métadonnées de qualité (confidence, source, méthode)
- Logging détaillé pour debugging
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from functools import lru_cache
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class DateResult:
    """
    Résultat d'extraction de date avec métadonnées V3.
    """
    date: str                    # Date au format YYYY-MM-DD
    source: str                  # Source de la date (json_ld, meta_tag, etc.)
    confidence: float            # Confidence 0.0-1.0
    raw_date_text: str = ""      # Texte brut avant parsing
    extraction_method: str = ""  # Méthode précise utilisée


class DateExtractorV3:
    """
    Extracteur de dates V3 avec guidage par configuration.
    
    Conserve la cascade éprouvée de V2 mais permet d'optimiser
    l'extraction selon les date_selectors de chaque source.
    """
    
    def extract(self, item_data: Dict[str, Any], raw_html: Optional[str] = None, 
                date_selectors: Optional[Dict[str, Any]] = None,
                pdf_metadata: Optional[Dict] = None) -> DateResult:
        """
        Extrait la date avec guidage optionnel par date_selectors.
        
        Args:
            item_data: Données de l'item (titre, contenu, etc.)
            raw_html: HTML brut de la page (optionnel)
            date_selectors: Configuration de guidage depuis source_configs
            pdf_metadata: Métadonnées PDF (optionnel)
        
        Returns:
            DateResult avec date et métadonnées
        """
        logger.debug(f"Extraction de date avec guidage: {bool(date_selectors)}")
        
        # Si date_selectors fourni, essayer les méthodes guidées en priorité
        if date_selectors and raw_html:
            guided_result = self._extract_with_guidance(raw_html, date_selectors)
            if guided_result:
                logger.info(f"✅ Date trouvée avec guidage: {guided_result.date} ({guided_result.source})")
                return guided_result
        
        # Cascade classique V2 si pas de guidage ou guidage échoué
        logger.debug("Utilisation de la cascade classique")
        
        # PDF metadata (highest priority for PDFs)
        if pdf_metadata and pdf_metadata.get('creation_date'):
            date = pdf_metadata['creation_date']
            if date:
                parsed = self._parse_date_string(date)
                if parsed:
                    return DateResult(
                        date=parsed,
                        source="pdf_metadata",
                        confidence=0.95,
                        raw_date_text=date,
                        extraction_method="PDF creation_date"
                    )
        
        # HTML metadata
        if raw_html:
            html_result = self._extract_from_html(raw_html)
            if html_result:
                return html_result
        
        # RSS pubDate
        if 'published' in item_data:
            date = self._parse_date_string(item_data['published'])
            if date:
                return DateResult(
                    date=date,
                    source="rss_pubdate",
                    confidence=0.90,
                    raw_date_text=item_data['published'],
                    extraction_method="RSS pubDate"
                )
        
        # Text extraction
        text = f"{item_data.get('title', '')} {item_data.get('summary', '')} {item_data.get('content', '')[:1000]}"
        if text.strip():
            text_result = self._extract_from_text(text)
            if text_result:
                return text_result
        
        # URL pattern
        url = item_data.get('link', '') or item_data.get('url', '')
        if url:
            url_result = self._extract_from_url(url)
            if url_result:
                return url_result
        
        # Fallback - PAS de date du jour, retourner échec
        logger.warning("Aucune date trouvée, échec d'extraction")
        return DateResult(
            date="",
            source="none",
            confidence=0.0,
            raw_date_text="",
            extraction_method="extraction_failed"
        )
    
    def _extract_with_guidance(self, html: str, date_selectors: Dict[str, Any]) -> Optional[DateResult]:
        """
        Extrait date avec guidage par date_selectors.
        
        Args:
            html: HTML brut
            date_selectors: Configuration de guidage
        
        Returns:
            DateResult ou None si échec
        """
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html, 'html.parser')
        strategy = date_selectors.get('strategy')
        css_selector = date_selectors.get('css')
        
        logger.debug(f"Guidage: strategy={strategy}, css={css_selector}")
        
        # Stratégie 1 : CSS selector spécifique
        if css_selector:
            logger.debug(f"Recherche avec CSS selector: {css_selector}")
            elements = soup.select(css_selector)
            if elements:
                for element in elements[:3]:  # Tester les 3 premiers
                    text = element.get_text(strip=True)
                    if text:
                        logger.debug(f"Texte trouvé dans selector: {text}")
                        parsed = self._parse_date_string(text)
                        if parsed:
                            return DateResult(
                                date=parsed,
                                source="css_selector",
                                confidence=0.90,
                                raw_date_text=text,
                                extraction_method=f"CSS selector: {css_selector}"
                            )
        
        # Stratégie 2 : JSON-LD prioritaire
        if strategy == "json_ld_graph":
            logger.debug("Stratégie JSON-LD @graph prioritaire")
            json_result = self._extract_from_json_ld(soup, prioritize_graph=True)
            if json_result:
                return json_result
        
        # Stratégie 3 : Text extraction prioritaire
        if strategy == "text_extraction":
            logger.debug("Stratégie text extraction prioritaire")
            visible_text = soup.get_text(separator=' ', strip=True)
            text_result = self._extract_from_text(visible_text[:2000])
            if text_result:
                return text_result
        
        return None
    
    def _extract_from_html(self, html: str) -> Optional[DateResult]:
        """Extrait date depuis HTML (JSON-LD, meta tags, time tag, texte visible)."""
        from bs4 import BeautifulSoup
        
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # JSON-LD
        json_result = self._extract_from_json_ld(soup)
        if json_result:
            return json_result
        
        # Meta tags
        meta_result = self._extract_from_meta_tags(soup)
        if meta_result:
            return meta_result
        
        # Time tag
        time_result = self._extract_from_time_tag(soup)
        if time_result:
            return time_result
        
        # Texte visible
        visible_text = soup.get_text(separator=' ', strip=True)
        if visible_text:
            text_result = self._extract_from_text(visible_text[:3000])
            if text_result:
                return text_result
        
        return None
    
    def _extract_from_json_ld(self, soup, prioritize_graph: bool = False) -> Optional[DateResult]:
        """Extrait date depuis JSON-LD."""
        import json
        
        scripts = soup.find_all('script', type='application/ld+json')
        logger.debug(f"Trouvé {len(scripts)} scripts JSON-LD")
        
        for script in scripts:
            try:
                data = json.loads(script.string)
                
                # Gérer @graph
                if isinstance(data, dict) and '@graph' in data:
                    for node in data['@graph']:
                        if isinstance(node, dict):
                            for key in ['datePublished', 'dateCreated', 'uploadDate']:
                                if key in node:
                                    parsed = self._parse_date_string(node[key])
                                    if parsed:
                                        return DateResult(
                                            date=parsed,
                                            source="json_ld",
                                            confidence=0.95,
                                            raw_date_text=node[key],
                                            extraction_method=f"JSON-LD @graph {key}"
                                        )
                
                # Objet simple
                elif isinstance(data, dict):
                    for key in ['datePublished', 'dateCreated', 'uploadDate']:
                        if key in data:
                            parsed = self._parse_date_string(data[key])
                            if parsed:
                                return DateResult(
                                    date=parsed,
                                    source="json_ld",
                                    confidence=0.95,
                                    raw_date_text=data[key],
                                    extraction_method=f"JSON-LD {key}"
                                )
            except Exception as e:
                logger.debug(f"Erreur JSON-LD: {e}")
        
        return None
    
    def _extract_from_meta_tags(self, soup) -> Optional[DateResult]:
        """Extrait date depuis meta tags."""
        meta_properties = [
            'article:published_time',
            'datePublished',
            'og:published_time',
            'article:published',
            'pubdate'
        ]
        
        for meta in soup.find_all('meta'):
            prop = meta.get('property') or meta.get('name')
            if prop in meta_properties:
                date_val = meta.get('content', '')
                if date_val:
                    parsed = self._parse_date_string(date_val)
                    if parsed:
                        return DateResult(
                            date=parsed,
                            source="meta_tag",
                            confidence=0.95,
                            raw_date_text=date_val,
                            extraction_method=f"Meta tag {prop}"
                        )
        
        return None
    
    def _extract_from_time_tag(self, soup) -> Optional[DateResult]:
        """Extrait date depuis balise <time>."""
        time_tag = soup.find('time')
        if time_tag:
            date_val = time_tag.get('datetime') or time_tag.get_text(strip=True)
            if date_val:
                parsed = self._parse_date_string(date_val)
                if parsed:
                    return DateResult(
                        date=parsed,
                        source="time_tag",
                        confidence=0.90,
                        raw_date_text=date_val,
                        extraction_method="HTML <time> tag"
                    )
        
        return None
    
    def _extract_from_text(self, text: str) -> Optional[DateResult]:
        """Extraction robuste depuis texte visible."""
        from dateutil import parser
        
        if not text:
            return None
        
        # Nettoyer espaces manquants
        text = re.sub(r'(\d)(January|February|March|April|May|June|July|August|September|October|November|December)', 
                     r'\1 \2', text, flags=re.IGNORECASE)
        
        # Patterns exhaustifs
        patterns = [
            # Formats avec jour de semaine (PRIORITÉ MAX)
            r'(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            r'(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})',
            
            # Formats US: "February 10, 2026"
            r'([A-Z][a-z]+\.?\s+\d{1,2},?\s+\d{4})',
            
            # Formats EU: "10 February 2026"
            r'(\d{1,2}\s+[A-Z][a-z]+\.?\s+\d{4})',
            
            # Formats ISO: "2026-02-10"
            r'(\d{4}-\d{2}-\d{2})',
            
            # Formats slash: "02/10/2026"
            r'(\d{1,2}/\d{1,2}/\d{4})',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                for match in matches[:3]:  # Tester les 3 premiers
                    match_str = match if isinstance(match, str) else ' '.join(match)
                    match_str = match_str.strip(' .,;:-')
                    
                    try:
                        dt = parser.parse(match_str, fuzzy=False, dayfirst=False)
                        
                        # Validation: date raisonnable
                        year_diff = abs(dt.year - datetime.now().year)
                        if year_diff <= 5:
                            return DateResult(
                                date=dt.strftime('%Y-%m-%d'),
                                source="text_extraction",
                                confidence=0.80,
                                raw_date_text=match_str,
                                extraction_method="Text pattern matching"
                            )
                    except Exception:
                        continue
        
        return None
    
    def _extract_from_url(self, url: str) -> Optional[DateResult]:
        """Extrait date depuis patterns URL."""
        patterns = [
            r'/(\d{4})/(\d{2})/(\d{2})/',
            r'/(\d{4})-(\d{2})-(\d{2})/',
            r'date=(\d{4}-\d{2}-\d{2})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                if len(match.groups()) == 3:
                    date = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
                else:
                    date = match.group(1)
                
                return DateResult(
                    date=date,
                    source="url_pattern",
                    confidence=0.60,
                    raw_date_text=match.group(0),
                    extraction_method="URL pattern"
                )
        
        return None
    
    def _parse_date_string(self, date_str: str) -> Optional[str]:
        """Parse string date vers format ISO (avec cache LRU)."""
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


def create_date_extractor() -> DateExtractorV3:
    """
    Factory function pour créer un DateExtractorV3.
    
    Returns:
        Instance de DateExtractorV3
    """
    return DateExtractorV3()