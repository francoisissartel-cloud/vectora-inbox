"""
Helpers pour le parser HTML adaptatif.
Fonctions utilitaires pour extraction robuste.
"""

from typing import List
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


def _extract_from_links(soup: BeautifulSoup) -> List:
    """
    Stratégie fallback: Extraire depuis tous les liens avec texte significatif.
    Utilisé quand aucun conteneur structuré n'est trouvé.
    """
    containers = []
    
    # Chercher tous les liens avec texte > 20 chars
    for link in soup.find_all('a', href=True):
        text = link.get_text(strip=True)
        if len(text) > 20 and not text.lower().startswith(('home', 'about', 'contact')):
            # Créer un pseudo-conteneur
            containers.append(link.parent if link.parent else link)
    
    # Dédupliquer
    seen = set()
    unique = []
    for c in containers:
        if id(c) not in seen:
            seen.add(id(c))
            unique.append(c)
    
    return unique[:20]  # Max 20
