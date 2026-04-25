"""
Parser HTML SIMPLE - Approche directe
Au lieu de chercher des conteneurs complexes, on trouve les liens et on va chercher le contenu complet.
"""

from typing import List, Dict, Any
from bs4 import BeautifulSoup
import requests
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def parse_html_simple(html: str, source_key: str, homepage_url: str) -> List[Dict[str, Any]]:
    """
    Parser simple : trouve les liens, va chercher le contenu complet.
    
    Args:
        html: HTML de la page listing
        source_key: Identifiant de la source
        homepage_url: URL de base pour construire les URLs complètes
    
    Returns:
        Liste d'items avec titre, contenu, date, url
    """
    soup = BeautifulSoup(html, 'html.parser')
    items = []
    
    # ÉTAPE 1: Trouver tous les liens qui ressemblent à des articles
    article_links = find_article_links(soup, homepage_url)
    logger.info(f"[{source_key}] Found {len(article_links)} article links")
    
    # ÉTAPE 2: Pour chaque lien, aller chercher le contenu complet
    for link_info in article_links[:20]:  # Max 20
        try:
            item = extract_full_article(link_info['url'], source_key)
            if item:
                items.append(item)
                logger.info(f"[{source_key}] ✓ Extracted: {item['title'][:60]}")
        except Exception as e:
            logger.warning(f"[{source_key}] Failed to extract {link_info['url']}: {e}")
    
    return items


def find_article_links(soup: BeautifulSoup, homepage_url: str) -> List[Dict[str, Any]]:
    """
    Trouve tous les liens qui ressemblent à des articles.
    Stratégie: chercher des patterns communs dans les URLs.
    """
    links = []
    
    # Patterns d'URLs d'articles (plus précis)
    article_patterns = [
        r'/press-release[s]?/\d{4}/',  # /press-releases/2026/...
        r'/news/\d{4}/',
        r'/\d{4}/\d{2}/',  # /2026/01/...
    ]
    
    for a in soup.find_all('a', href=True):
        href = a.get('href', '')
        
        # Ignorer liens de navigation
        if any(x in href.lower() for x in ['#', 'javascript:', 'mailto:', 'tel:', '?']):
            continue
        
        # Ignorer pages de listing
        if href.endswith('/press-releases/') or href.endswith('/news/') or href.endswith('/media/'):
            continue
        
        # Vérifier si ça ressemble à un article
        is_article = any(re.search(pattern, href, re.I) for pattern in article_patterns)
        
        if is_article:
            # Construire URL complète
            if href.startswith('/'):
                from urllib.parse import urljoin
                full_url = urljoin(homepage_url, href)
            elif href.startswith('http'):
                full_url = href
            else:
                continue
            
            # Extraire titre du lien (si disponible)
            title_hint = a.get_text(strip=True)
            
            links.append({
                'url': full_url,
                'title_hint': title_hint[:100] if len(title_hint) > 20 else None
            })
    
    # Dédupliquer
    seen = set()
    unique_links = []
    for link in links:
        if link['url'] not in seen:
            seen.add(link['url'])
            unique_links.append(link)
    
    return unique_links


def extract_full_article(url: str, source_key: str) -> Dict[str, Any]:
    """
    Va chercher la page complète et extrait tout le contenu.
    Simple et robuste.
    """
    # Fetch la page
    response = requests.get(url, timeout=15, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; VectoraBot/1.0)'
    })
    
    if response.status_code != 200:
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # TITRE: Chercher dans l'ordre de priorité
    title = None
    for selector in ['h1', 'h2', '.title', 'title']:
        elem = soup.find(selector)
        if elem:
            title = elem.get_text(strip=True)
            if len(title) > 10:
                break
    
    if not title or len(title) < 10:
        return None
    
    # CONTENU: Chercher le contenu principal
    content = None
    content_selectors = [
        'article',
        '.content',
        '.post-content',
        'main',
        '.entry-content',
        '.press-release',
        'div[class*="content"]'
    ]
    
    for selector in content_selectors:
        elem = soup.select_one(selector)
        if elem:
            content = elem.get_text(separator=' ', strip=True)
            if len(content) > 200:
                break
    
    # Fallback: prendre tout le body
    if not content or len(content) < 200:
        body = soup.find('body')
        if body:
            content = body.get_text(separator=' ', strip=True)
    
    # Nettoyer le contenu
    content = re.sub(r'\s+', ' ', content).strip()
    
    # DATE: Chercher dans plusieurs endroits
    date = extract_date_from_page(soup, title, content)
    
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    
    return {
        'title': title,
        'content': content[:3000],  # Limiter à 3000 chars
        'url': url,
        'published_at': date,
        'source_key': source_key
    }


def extract_date_from_page(soup: BeautifulSoup, title: str, content: str) -> str:
    """
    Extrait la date depuis la page.
    Cherche dans: <time>, meta tags, patterns dans le texte.
    """
    # 1. Chercher <time datetime="">
    time_elem = soup.find('time', attrs={'datetime': True})
    if time_elem:
        date_str = time_elem.get('datetime')
        parsed = parse_date_string(date_str)
        if parsed:
            return parsed
    
    # 2. Chercher dans meta tags
    meta_date = soup.find('meta', attrs={'property': 'article:published_time'})
    if meta_date:
        date_str = meta_date.get('content', '')
        parsed = parse_date_string(date_str)
        if parsed:
            return parsed
    
    # 3. Chercher pattern de date dans le titre
    date_patterns = [
        r'(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})',
        r'(\d{4}-\d{2}-\d{2})',
        r'(\d{2}/\d{2}/\d{4})',
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, title, re.I)
        if match:
            parsed = parse_date_string(match.group(1))
            if parsed:
                return parsed
    
    # 4. Chercher dans le début du contenu
    for pattern in date_patterns:
        match = re.search(pattern, content[:500], re.I)
        if match:
            parsed = parse_date_string(match.group(1))
            if parsed:
                return parsed
    
    return None


def parse_date_string(date_str: str) -> str:
    """Parse une date string vers YYYY-MM-DD"""
    from dateutil import parser
    try:
        dt = parser.parse(date_str, fuzzy=True)
        return dt.strftime('%Y-%m-%d')
    except:
        return None
