"""
Module d'extraction HTML robuste avec fallback pour P0-3.

Ce module améliore la robustesse de l'extraction HTML pour éviter
les pertes de contenu comme l'item Nanexa/Moderna.
"""

import logging
import time
import random
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


def extract_content_with_fallback(url: str, title: str, max_retries: int = 2) -> Optional[str]:
    """
    Extraction HTML avec fallback robuste pour éviter les pertes de contenu.
    
    Args:
        url: URL à extraire
        title: Titre de l'item (pour fallback)
        max_retries: Nombre maximum de tentatives
    
    Returns:
        Contenu extrait ou None si échec complet
    """
    for attempt in range(max_retries):
        try:
            # Tentative extraction HTML normale
            content = _extract_html_content_safe(url, timeout=10)
            
            if content and len(content.strip()) > 50:
                logger.info(f"HTML extraction successful for {url} (attempt {attempt + 1})")
                return content
                
        except Exception as e:
            logger.warning(f"HTML extraction attempt {attempt + 1} failed for {url}: {e}")
            
            if attempt < max_retries - 1:
                # Délai avant retry avec jitter
                delay = 2 + random.uniform(0, 1)
                time.sleep(delay)
    
    # Fallback : utiliser le titre comme contenu minimal
    if title and len(title.strip()) > 10:
        fallback_content = _create_title_based_content(title, url)
        logger.info(f"Using title fallback for {url}")
        return fallback_content
    
    logger.error(f"Complete extraction failure for {url}")
    return None


def _extract_html_content_safe(url: str, timeout: int = 10) -> Optional[str]:
    """
    Extraction HTML sécurisée avec gestion d'erreur.
    
    Args:
        url: URL à extraire
        timeout: Timeout en secondes
    
    Returns:
        Contenu HTML extrait ou None
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        
        # Headers pour éviter les blocages
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
        
        # Vérifier que c'est du HTML
        content_type = response.headers.get('content-type', '').lower()
        if 'html' not in content_type:
            logger.warning(f"Non-HTML content type for {url}: {content_type}")
            return None
        
        # Parser avec BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extraire le contenu principal avec plusieurs stratégies
        content = _extract_main_content(soup)
        
        if content and len(content.strip()) > 50:
            return content
        else:
            logger.warning(f"Extracted content too short for {url}: {len(content) if content else 0} chars")
            return None
            
    except requests.exceptions.Timeout:
        logger.warning(f"Timeout extracting {url}")
        raise
    except requests.exceptions.RequestException as e:
        logger.warning(f"Request error for {url}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error extracting {url}: {e}")
        raise


def _extract_main_content(soup) -> str:
    """
    Extrait le contenu principal d'une page avec plusieurs stratégies.
    
    Args:
        soup: Objet BeautifulSoup
    
    Returns:
        Contenu principal extrait
    """
    content_parts = []
    
    # Stratégie 1: Chercher les balises de contenu principal
    main_selectors = [
        'main', 'article', '.content', '.main-content', 
        '.post-content', '.entry-content', '.article-content',
        '#content', '#main', '.news-content'
    ]
    
    for selector in main_selectors:
        try:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(separator=' ', strip=True)
                if len(text) > 100:  # Contenu substantiel
                    content_parts.append(text)
                    break
        except Exception:
            continue
    
    # Stratégie 2: Si pas de contenu principal, chercher les paragraphes
    if not content_parts:
        paragraphs = soup.find_all('p')
        for p in paragraphs[:10]:  # Limiter à 10 paragraphes
            text = p.get_text(strip=True)
            if len(text) > 20:  # Paragraphe substantiel
                content_parts.append(text)
    
    # Stratégie 3: Fallback sur le titre et meta description
    if not content_parts:
        title = soup.find('title')
        if title:
            content_parts.append(title.get_text(strip=True))
        
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            content_parts.append(meta_desc.get('content'))
    
    return ' '.join(content_parts)


def _create_title_based_content(title: str, url: str) -> str:
    """
    Crée un contenu minimal basé sur le titre pour fallback.
    
    Args:
        title: Titre de l'item
        url: URL de l'item
    
    Returns:
        Contenu minimal formaté
    """
    return f"""Title: {title}

Content extraction failed for this URL. Analysis based on title only.
This appears to be a pharmaceutical industry news item that requires manual review.

Source URL: {url}
Extraction Status: Title-only fallback
Extraction Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Note: This item should be reviewed manually to ensure no important LAI-related content is missed."""


def create_minimal_item_from_title(raw_item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Crée un item minimal basé uniquement sur le titre quand l'extraction échoue.
    
    Args:
        raw_item: Item brut avec au moins title et url
    
    Returns:
        Item normalisé minimal
    """
    title = raw_item.get('title', '')
    url = raw_item.get('url', '')
    source_key = raw_item.get('source_key', '')
    
    # Extraire des entités basiques depuis le titre
    companies_detected = _extract_companies_from_title(title)
    technologies_detected = _extract_technologies_from_title(title)
    trademarks_detected = _extract_trademarks_from_title(title)
    
    return {
        'source_key': source_key,
        'source_type': raw_item.get('source_type', ''),
        'title': title,
        'summary': f"Content extraction failed. Title-based analysis: {title}",
        'url': url,
        'date': raw_item.get('published_at', datetime.now().strftime('%Y-%m-%d')),
        'companies_detected': companies_detected,
        'molecules_detected': [],
        'technologies_detected': technologies_detected,
        'trademarks_detected': trademarks_detected,
        'indications_detected': [],
        'event_type': 'other',
        'domain_relevance_score': 0.3,  # Score réduit pour items partiels
        'extraction_status': 'title_only_fallback'
    }


def _extract_companies_from_title(title: str) -> List[str]:
    """
    Extrait les noms de sociétés depuis le titre avec patterns connus.
    
    Args:
        title: Titre de l'item
    
    Returns:
        Liste des sociétés détectées
    """
    companies = []
    title_lower = title.lower()
    
    # Sociétés LAI connues
    known_companies = [
        'Nanexa', 'MedinCell', 'DelSiTech', 'Moderna', 'Pfizer', 'Teva',
        'Johnson & Johnson', 'Novartis', 'Roche', 'AbbVie', 'Eli Lilly'
    ]
    
    for company in known_companies:
        if company.lower() in title_lower:
            companies.append(company)
    
    return companies


def _extract_technologies_from_title(title: str) -> List[str]:
    """
    Extrait les technologies depuis le titre avec patterns LAI.
    
    Args:
        title: Titre de l'item
    
    Returns:
        Liste des technologies détectées
    """
    technologies = []
    title_lower = title.lower()
    
    # Technologies LAI connues
    lai_patterns = [
        ('extended-release injectable', 'Extended-Release Injectable'),
        ('long-acting injectable', 'Long-Acting Injectable'),
        ('pharmashell', 'PharmaShell®'),
        ('silishell', 'SiliaShell®'),
        ('depot injection', 'depot injection'),
        ('once-monthly', 'once-monthly injection'),
        ('lai', 'LAI')
    ]
    
    for pattern, normalized in lai_patterns:
        if pattern in title_lower:
            technologies.append(normalized)
    
    return technologies


def _extract_trademarks_from_title(title: str) -> List[str]:
    """
    Extrait les marques déposées depuis le titre.
    
    Args:
        title: Titre de l'item
    
    Returns:
        Liste des marques détectées
    """
    trademarks = []
    title_lower = title.lower()
    
    # Marques LAI connues
    known_trademarks = [
        'UZEDY®', 'PharmaShell®', 'SiliaShell®', 'BEPO®'
    ]
    
    for trademark in known_trademarks:
        if trademark.lower().replace('®', '') in title_lower:
            trademarks.append(trademark)
    
    return trademarks


def normalize_item_with_robust_extraction(
    raw_item: Dict[str, Any],
    canonical_scopes: Dict[str, Any],
    bedrock_model_id: str,
    watch_domains: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Normalise un item avec extraction HTML robuste et fallback.
    
    Args:
        raw_item: Item brut contenant title, url, raw_text, etc.
        canonical_scopes: Scopes canonical chargés
        bedrock_model_id: Identifiant du modèle Bedrock
        watch_domains: Domaines à surveiller
    
    Returns:
        Item normalisé avec gestion d'erreur améliorée
    """
    from vectora_core.normalization import bedrock_client, entity_detector
    from vectora_core.normalization.domain_context_builder import DomainContextBuilder
    
    logger.debug(f"Robust normalization for item: {raw_item.get('title', '')[:50]}...")
    
    # Construire le texte complet pour analyse
    raw_text = raw_item.get('raw_text', '')
    title = raw_item.get('title', '')
    url = raw_item.get('url', '')
    
    # Si pas de contenu, essayer extraction avec fallback
    if not raw_text or len(raw_text.strip()) < 50:
        logger.info(f"Attempting robust content extraction for: {title}")
        raw_text = extract_content_with_fallback(url, title)
    
    # Si toujours pas de contenu, créer item minimal
    if not raw_text:
        logger.warning(f"Creating minimal item from title: {title}")
        return create_minimal_item_from_title(raw_item)
    
    # Construire le texte complet pour Bedrock
    full_text = f"{title} {raw_text}"
    
    # Détection par règles
    rules_result = entity_detector.detect_entities_by_rules(full_text, canonical_scopes)
    
    # Préparer des exemples pour Bedrock
    from vectora_core.normalization.normalizer import _extract_canonical_examples_enhanced
    canonical_examples = _extract_canonical_examples_enhanced(canonical_scopes)
    
    # Construire les contextes de domaines
    domain_contexts = []
    if watch_domains:
        domain_builder = DomainContextBuilder(canonical_scopes)
        domain_contexts = domain_builder.build_domain_contexts(watch_domains)
    
    # Appeler Bedrock avec gestion d'erreur
    try:
        bedrock_result = bedrock_client.normalize_item_with_bedrock(
            full_text,
            bedrock_model_id,
            canonical_examples,
            domain_contexts
        )
        
        # Vérifier que la normalisation a produit un résultat valide
        if not bedrock_result.get('summary') or len(bedrock_result['summary'].strip()) < 10:
            logger.warning(f"Bedrock produced empty summary for: {title}")
            # Fallback sur item minimal
            return create_minimal_item_from_title(raw_item)
        
    except Exception as e:
        logger.error(f"Bedrock normalization failed for {title}: {e}")
        return create_minimal_item_from_title(raw_item)
    
    # Fusionner les résultats
    merged_entities = entity_detector.merge_entity_detections(bedrock_result, rules_result)
    
    # Construire l'item normalisé
    normalized_item = {
        'source_key': raw_item.get('source_key'),
        'source_type': raw_item.get('source_type'),
        'title': raw_item.get('title'),
        'summary': bedrock_result.get('summary', ''),
        'url': raw_item.get('url'),
        'date': raw_item.get('published_at'),
        'companies_detected': merged_entities['companies_detected'],
        'molecules_detected': merged_entities['molecules_detected'],
        'technologies_detected': merged_entities['technologies_detected'],
        'indications_detected': merged_entities['indications_detected'],
        'event_type': bedrock_result.get('event_type', 'other'),
        'domain_relevance': bedrock_result.get('domain_relevance', []),
        'extraction_status': 'success'
    }
    
    return normalized_item