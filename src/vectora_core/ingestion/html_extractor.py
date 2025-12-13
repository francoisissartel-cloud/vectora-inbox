"""
Module d'extraction HTML configurable.

Ce module implémente la couche d'extracteurs spécifiques avec configuration
déclarative, tout en préservant le fallback sur le parser générique.
"""

import logging
import re
import yaml
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class ConfigurableHTMLExtractor:
    """Extracteur HTML configurable avec fallback générique."""
    
    def __init__(self, config_bucket: Optional[str] = None):
        """
        Initialise l'extracteur avec la configuration.
        
        Args:
            config_bucket: Bucket S3 pour charger la configuration (optionnel)
        """
        self.extractors = {}
        self.global_settings = {}
        self._load_extractor_configs(config_bucket)
    
    def _load_extractor_configs(self, config_bucket: Optional[str] = None):
        """
        Charge les configurations d'extracteurs depuis le fichier YAML.
        
        Args:
            config_bucket: Bucket S3 (non utilisé pour l'instant, lecture locale)
        """
        try:
            # Pour l'instant, lecture locale du fichier
            # TODO: Implémenter le chargement depuis S3 si config_bucket fourni
            config_path = "canonical/sources/html_extractors.yaml"
            
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                
                self.extractors = config.get('extractors', {})
                self.global_settings = config.get('global_settings', {})
                
                logger.info(f"Configuration d'extracteurs chargée: {len(self.extractors)} extracteurs")
                
            except FileNotFoundError:
                logger.warning(f"Fichier de configuration {config_path} non trouvé, utilisation du parser générique uniquement")
                self.extractors = {}
                self.global_settings = {}
        
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration d'extracteurs: {e}")
            self.extractors = {}
            self.global_settings = {}
    
    def extract_items(
        self, 
        html_content: str, 
        source_key: str, 
        source_type: str, 
        source_meta: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Extrait les items avec configuration spécifique ou générique.
        
        Args:
            html_content: Contenu HTML de la page
            source_key: Identifiant de la source
            source_type: Type de source
            source_meta: Métadonnées de la source
        
        Returns:
            Tuple (items, errors)
        """
        if source_key in self.extractors:
            logger.info(f"Utilisation de l'extracteur spécifique pour {source_key}")
            return self._extract_with_config(html_content, source_key, source_type, source_meta)
        else:
            logger.info(f"Utilisation du parser générique pour {source_key}")
            return self._extract_with_heuristics(html_content, source_key, source_type, source_meta)
    
    def _extract_with_config(
        self, 
        html_content: str, 
        source_key: str, 
        source_type: str, 
        source_meta: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Extraction avec configuration spécifique.
        
        Args:
            html_content: Contenu HTML
            source_key: Identifiant de la source
            source_type: Type de source
            source_meta: Métadonnées de la source
        
        Returns:
            Tuple (items, errors)
        """
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            error_msg = "BeautifulSoup non installé"
            return [], [error_msg]
        
        config = self.extractors[source_key]
        errors = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Utiliser base_url de la config ou extraire depuis source_meta
            base_url = config.get('base_url') or self._extract_base_url(source_meta)
            
            # Trouver le conteneur principal
            container_selectors = config['selectors']['container'].split(', ')
            container = None
            
            for selector in container_selectors:
                container = soup.select_one(selector.strip())
                if container:
                    break
            
            if not container:
                error_msg = f"Conteneur non trouvé avec sélecteurs: {config['selectors']['container']}"
                logger.warning(f"Source {source_key} : {error_msg}")
                errors.append(error_msg)
                # Fallback sur le body entier
                container = soup
            
            # Extraire les items
            item_selectors = config['selectors']['item'].split(', ')
            item_elements = []
            
            for selector in item_selectors:
                elements = container.select(selector.strip())
                item_elements.extend(elements)
                if len(item_elements) >= config.get('max_items', 20):
                    break
            
            # Limiter le nombre d'items
            max_items = config.get('max_items', self.global_settings.get('default_max_items', 20))
            item_elements = item_elements[:max_items]
            
            items = []
            for element in item_elements:
                item = self._extract_item_with_selectors(element, config, source_key, source_type, base_url)
                if item:
                    items.append(item)
            
            if not items and not errors:
                error_msg = "Aucun item extrait avec la configuration spécifique"
                errors.append(error_msg)
            
            logger.info(f"Source {source_key} : {len(items)} items extraits avec extracteur spécifique")
            return items, errors
        
        except Exception as e:
            error_msg = f"Erreur avec extracteur spécifique: {e}"
            logger.error(f"Source {source_key} : {error_msg}")
            return [], [error_msg]
    
    def _extract_item_with_selectors(
        self, 
        element, 
        config: Dict[str, Any], 
        source_key: str, 
        source_type: str, 
        base_url: str
    ) -> Optional[Dict[str, Any]]:
        """
        Extrait un item depuis un élément avec les sélecteurs de configuration.
        
        Args:
            element: Élément BeautifulSoup
            config: Configuration de l'extracteur
            source_key: Identifiant de la source
            source_type: Type de source
            base_url: URL de base
        
        Returns:
            Item extrait ou None
        """
        try:
            selectors = config['selectors']
            
            # Extraire l'URL
            url = self._extract_with_selector(element, selectors['url'], 'href')
            if not url:
                return None
            
            # Résoudre l'URL relative
            url = self._resolve_url(url, base_url)
            if not url:
                return None
            
            # Extraire le titre
            title = self._extract_with_selector(element, selectors['title'], 'text')
            if not title or len(title.strip()) < 3:
                return None
            
            # Extraire la description
            description = ''
            if 'description' in selectors:
                description = self._extract_with_selector(element, selectors['description'], 'text') or ''
            
            # Extraire la date
            date_str = ''
            if 'date' in selectors:
                date_str = self._extract_with_selector(element, selectors['date'], 'text')
                if not date_str:
                    # Essayer l'attribut datetime
                    date_str = self._extract_with_selector(element, selectors['date'], 'datetime')
            
            # Parser la date
            published_at = self._parse_date_with_format(date_str, config.get('date_format'))
            
            return {
                'title': title.strip(),
                'url': url,
                'published_at': published_at,
                'raw_text': description.strip(),
                'source_key': source_key,
                'source_type': source_type
            }
        
        except Exception as e:
            logger.debug(f"Erreur lors de l'extraction d'item avec sélecteurs: {e}")
            return None
    
    def _extract_with_selector(self, element, selector: str, attribute: str) -> Optional[str]:
        """
        Extrait une valeur depuis un élément avec un sélecteur CSS.
        
        Args:
            element: Élément BeautifulSoup
            selector: Sélecteur CSS (peut contenir plusieurs sélecteurs séparés par des virgules)
            attribute: Attribut à extraire ('text', 'href', 'datetime', etc.)
        
        Returns:
            Valeur extraite ou None
        """
        selectors = [s.strip() for s in selector.split(',')]
        
        for sel in selectors:
            try:
                target = element.select_one(sel)
                if target:
                    if attribute == 'text':
                        return target.get_text(strip=True)
                    else:
                        return target.get(attribute)
            except Exception:
                continue
        
        return None
    
    def _parse_date_with_format(self, date_str: str, date_format: Optional[str]) -> str:
        """
        Parse une date avec le format spécifié ou les formats par défaut.
        
        Args:
            date_str: Chaîne de date
            date_format: Format de date spécifique (optionnel)
        
        Returns:
            Date au format YYYY-MM-DD
        """
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d')
        
        date_str = date_str.strip()
        
        # Essayer le format spécifique d'abord
        if date_format:
            try:
                dt = datetime.strptime(date_str, date_format)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                pass
        
        # Essayer les formats par défaut
        default_formats = self.global_settings.get('default_date_patterns', [
            '%Y-%m-%d', '%B %d, %Y', '%d %B %Y', '%d/%m/%Y', '%m/%d/%Y', '%Y.%m.%d'
        ])
        
        for fmt in default_formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # Fallback avec dateutil si disponible
        try:
            from dateutil import parser as date_parser
            dt = date_parser.parse(date_str)
            return dt.strftime('%Y-%m-%d')
        except (ImportError, ValueError):
            pass
        
        # Dernière chance avec regex
        iso_match = re.search(r'\\d{4}-\\d{2}-\\d{2}', date_str)
        if iso_match:
            return iso_match.group()
        
        # Fallback: date actuelle
        return datetime.now().strftime('%Y-%m-%d')
    
    def _extract_base_url(self, source_meta: Dict[str, Any]) -> str:
        """
        Extrait l'URL de base depuis les métadonnées de la source.
        
        Args:
            source_meta: Métadonnées de la source
        
        Returns:
            URL de base
        """
        from urllib.parse import urlparse
        
        html_url = source_meta.get('html_url', '')
        homepage_url = source_meta.get('homepage_url', '')
        
        url = html_url or homepage_url
        if url:
            parsed = urlparse(url)
            return f"{parsed.scheme}://{parsed.netloc}"
        
        return ''
    
    def _resolve_url(self, url: str, base_url: str) -> str:
        """
        Résout les URLs relatives.
        
        Args:
            url: URL à résoudre
            base_url: URL de base
        
        Returns:
            URL absolue
        """
        if not url:
            return ''
        
        if url.startswith(('http://', 'https://')):
            return url
        
        if base_url:
            return urljoin(base_url, url)
        
        return url
    
    def _extract_with_heuristics(
        self, 
        html_content: str, 
        source_key: str, 
        source_type: str, 
        source_meta: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Extraction avec heuristiques génériques (fallback).
        
        Args:
            html_content: Contenu HTML
            source_key: Identifiant de la source
            source_type: Type de source
            source_meta: Métadonnées de la source
        
        Returns:
            Tuple (items, errors)
        """
        # Importer les fonctions du parser générique
        from .parser import _parse_html_page
        
        return _parse_html_page(html_content, source_key, source_type, source_meta)