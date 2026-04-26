"""
Content Extractor V3 - Extraction de contenu HTML/PDF

Version V3 du content extractor, adaptée pour le pipeline V3.
Conserve les fonctionnalités éprouvées de V2 avec optimisations.

Responsabilités :
- Extraction de contenu HTML avec BeautifulSoup
- Extraction de contenu PDF via PyMuPDF
- Nettoyage et normalisation du contenu
- Métadonnées d'extraction
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any
import logging
from datetime import datetime

from ..shared.utils import measure_duration_ms

logger = logging.getLogger(__name__)


class ContentExtractionResult:
    """
    Résultat d'extraction de contenu avec métadonnées.
    """
    def __init__(self, content: str, success: bool, content_type: str = "html",
                 duration_ms: int = 0, error: Optional[str] = None,
                 metadata: Optional[Dict] = None):
        self.content = content
        self.success = success
        self.content_type = content_type
        self.duration_ms = duration_ms
        self.error = error
        self.metadata = metadata or {}
        self.extracted_at = datetime.utcnow().isoformat() + "Z"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit le résultat en dictionnaire."""
        return {
            "content": self.content,
            "success": self.success,
            "content_type": self.content_type,
            "content_length": len(self.content),
            "duration_ms": self.duration_ms,
            "error": self.error,
            "metadata": self.metadata,
            "extracted_at": self.extracted_at
        }


class ContentExtractorV3:
    """
    Extracteur de contenu V3 pour HTML et PDF.
    """
    
    def __init__(self, timeout: int = 15, max_length: int = 50000):
        """
        Initialise l'extracteur.
        
        Args:
            timeout: Timeout pour les requêtes HTTP
            max_length: Longueur maximale du contenu extrait
        """
        self.timeout = timeout
        self.max_length = max_length
        logger.debug(f"ContentExtractorV3 initialisé (timeout={timeout}s, max_length={max_length})")
    
    def extract_from_response_content(self, content: bytes, content_type: str, 
                                    url: str = "") -> ContentExtractionResult:
        """
        Extrait le contenu depuis des bytes de réponse HTTP.
        
        Args:
            content: Contenu brut (bytes)
            content_type: Type MIME du contenu
            url: URL source (pour logging)
        
        Returns:
            Résultat d'extraction avec métadonnées
        """
        start_time = datetime.now()
        
        try:
            if 'pdf' in content_type.lower():
                result = self._extract_pdf(content)
                duration_ms = measure_duration_ms(start_time)
                
                return ContentExtractionResult(
                    content=result,
                    success=bool(result),
                    content_type="pdf",
                    duration_ms=duration_ms,
                    metadata={"source_url": url}
                )
            else:
                result = self._extract_html(content, url)
                duration_ms = measure_duration_ms(start_time)
                
                return ContentExtractionResult(
                    content=result,
                    success=bool(result),
                    content_type="html",
                    duration_ms=duration_ms,
                    metadata={"source_url": url}
                )
        
        except Exception as e:
            duration_ms = measure_duration_ms(start_time)
            logger.error(f"Erreur d'extraction pour {url}: {e}")
            
            return ContentExtractionResult(
                content="",
                success=False,
                content_type="unknown",
                duration_ms=duration_ms,
                error=str(e),
                metadata={"source_url": url}
            )
    
    def extract_from_url(self, url: str) -> ContentExtractionResult:
        """
        Extrait le contenu directement depuis une URL.
        
        Args:
            url: URL à extraire
        
        Returns:
            Résultat d'extraction
        """
        start_time = datetime.now()
        
        try:
            logger.debug(f"Extraction depuis URL: {url}")
            
            response = requests.get(url, timeout=self.timeout)
            if response.status_code != 200:
                duration_ms = measure_duration_ms(start_time)
                return ContentExtractionResult(
                    content="",
                    success=False,
                    duration_ms=duration_ms,
                    error=f"HTTP {response.status_code}",
                    metadata={"source_url": url}
                )
            
            content_type = response.headers.get('content-type', '')
            return self.extract_from_response_content(response.content, content_type, url)
        
        except Exception as e:
            duration_ms = measure_duration_ms(start_time)
            logger.error(f"Erreur lors du fetch de {url}: {e}")
            
            return ContentExtractionResult(
                content="",
                success=False,
                duration_ms=duration_ms,
                error=str(e),
                metadata={"source_url": url}
            )
    
    def _extract_html(self, content: bytes, url: str = "") -> str:
        """
        Extrait le texte principal depuis HTML.
        
        Args:
            content: Contenu HTML brut
            url: URL source (pour logging)
        
        Returns:
            Texte extrait et nettoyé
        """
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Supprimer les éléments non-pertinents
            for tag in ['script', 'style', 'nav', 'header', 'footer', 'aside', 'menu']:
                for elem in soup.find_all(tag):
                    elem.decompose()
            
            # Supprimer les classes/IDs typiques de navigation
            for selector in ['.nav', '.navigation', '.menu', '.sidebar', '.footer', '.header']:
                for elem in soup.select(selector):
                    elem.decompose()
            
            # Chercher le contenu principal dans l'ordre de priorité
            main_content = None
            
            # 1. Balises sémantiques
            for tag in ['main', 'article']:
                main_content = soup.find(tag)
                if main_content:
                    logger.debug(f"Contenu trouvé dans <{tag}>")
                    break
            
            # 2. Classes typiques de contenu
            if not main_content:
                for class_name in ['.content', '.post-content', '.entry-content', '.article-content', 
                                 '.press-release-content', '.news-content']:
                    main_content = soup.select_one(class_name)
                    if main_content:
                        logger.debug(f"Contenu trouvé dans {class_name}")
                        break
            
            # 3. Fallback sur body
            if not main_content:
                main_content = soup.find('body') or soup
                logger.debug("Fallback sur body/document complet")
            
            # Extraire le texte
            text = main_content.get_text(separator=' ', strip=True)
            
            # Nettoyer le texte
            text = self._clean_extracted_text(text)
            
            # Limiter la longueur
            if len(text) > self.max_length:
                text = text[:self.max_length]
                logger.debug(f"Texte tronqué à {self.max_length} caractères")
            
            logger.debug(f"HTML extraction: {len(text)} caractères")
            return text
        
        except Exception as e:
            logger.error(f"Erreur extraction HTML: {e}")
            return ""
    
    def _extract_pdf(self, content: bytes) -> str:
        """
        Extrait le texte depuis PDF.
        
        Args:
            content: Contenu PDF brut
        
        Returns:
            Texte extrait
        """
        try:
            # Essayer d'importer le PDF extractor V2
            from ..ingest.pdf_extractor import PDFExtractor
            
            extractor = PDFExtractor()
            result = extractor.extract(content, url="")
            text = result.get('text', '')
            
            # Nettoyer le texte
            text = self._clean_extracted_text(text)
            
            logger.debug(f"PDF extraction: {len(text)} caractères, {result['metadata']['pages']} pages")
            return text
        
        except ImportError:
            logger.warning("PDFExtractor non disponible, extraction PDF ignorée")
            return ""
        except Exception as e:
            logger.error(f"Erreur extraction PDF: {e}")
            return ""
    
    def _clean_extracted_text(self, text: str) -> str:
        """
        Nettoie le texte extrait.
        
        Args:
            text: Texte brut
        
        Returns:
            Texte nettoyé
        """
        if not text:
            return ""
        
        # Supprimer les espaces multiples
        text = ' '.join(text.split())
        
        # Supprimer les caractères de contrôle
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
        
        # Supprimer les lignes très courtes répétitives (navigation, etc.)
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if len(line) > 10:  # Garder seulement les lignes substantielles
                cleaned_lines.append(line)
        
        return ' '.join(cleaned_lines)


def create_content_extractor(timeout: int = 15, max_length: int = 50000) -> ContentExtractorV3:
    """
    Factory function pour créer un ContentExtractorV3.
    
    Args:
        timeout: Timeout pour les requêtes HTTP
        max_length: Longueur maximale du contenu
    
    Returns:
        Instance de ContentExtractorV3
    """
    return ContentExtractorV3(timeout=timeout, max_length=max_length)