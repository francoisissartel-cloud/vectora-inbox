"""
Universal Format Detector
Automatically detects RSS, HTML, or PDF content
"""
import logging
import feedparser
from typing import Optional

logger = logging.getLogger(__name__)


class UniversalFormatDetector:
    """Detect content format: RSS, HTML, or PDF"""
    
    def detect(self, url: str, content: bytes, content_type: str = "") -> str:
        """
        Detect format from URL, headers, and content
        
        Args:
            url: Source URL
            content: Raw content bytes
            content_type: Content-Type header value
            
        Returns:
            'rss', 'html', 'pdf', or 'unknown'
        """
        # 1. Check URL extension
        url_lower = url.lower()
        if url_lower.endswith('.pdf'):
            logger.info(f"Format detected from URL extension: PDF ({url})")
            return 'pdf'
        
        if url_lower.endswith('.xml') or url_lower.endswith('.rss') or '/rss' in url_lower or '/feed' in url_lower:
            logger.info(f"Format detected from URL pattern: RSS ({url})")
            return 'rss'
        
        # 2. Check Content-Type header
        if content_type:
            content_type_lower = content_type.lower()
            if 'application/pdf' in content_type_lower:
                logger.info(f"Format detected from Content-Type: PDF ({url})")
                return 'pdf'
            
            if any(rss_type in content_type_lower for rss_type in ['application/rss', 'application/xml', 'text/xml', 'application/atom']):
                logger.info(f"Format detected from Content-Type: RSS ({url})")
                return 'rss'
            
            if 'text/html' in content_type_lower:
                # Could still be RSS, check content
                pass
        
        # 3. Check content magic bytes and structure
        try:
            # Check PDF magic bytes
            if content[:4] == b'%PDF':
                logger.info(f"Format detected from magic bytes: PDF ({url})")
                return 'pdf'
            
            # Try to decode as text
            text_content = content.decode('utf-8', errors='ignore')[:1000]
            
            # Check for RSS/XML structure
            if self._is_rss_content(text_content):
                logger.info(f"Format detected from content structure: RSS ({url})")
                return 'rss'
            
            # Check for HTML
            if self._is_html_content(text_content):
                logger.info(f"Format detected from content structure: HTML ({url})")
                return 'html'
            
        except Exception as e:
            logger.warning(f"Error analyzing content for {url}: {e}")
        
        # Default to HTML
        logger.info(f"Format defaulted to HTML ({url})")
        return 'html'
    
    def _is_rss_content(self, text: str) -> bool:
        """Check if content looks like RSS/XML feed"""
        text_lower = text.lower()
        
        # Check for RSS/Atom indicators
        rss_indicators = [
            '<rss',
            '<feed',
            '<channel>',
            'xmlns="http://www.w3.org/2005/atom"',
            'xmlns="http://purl.org/rss/'
        ]
        
        return any(indicator in text_lower for indicator in rss_indicators)
    
    def _is_html_content(self, text: str) -> bool:
        """Check if content looks like HTML"""
        text_lower = text.lower()
        
        # Check for HTML indicators
        html_indicators = [
            '<!doctype html',
            '<html',
            '<head>',
            '<body>'
        ]
        
        return any(indicator in text_lower for indicator in html_indicators)
