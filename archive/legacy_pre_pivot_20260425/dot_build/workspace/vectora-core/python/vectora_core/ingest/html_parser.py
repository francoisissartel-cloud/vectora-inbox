from bs4 import BeautifulSoup
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class ParsedItem:
    title: str
    url: str
    date: Optional[str] = None
    summary: Optional[str] = None

class HTMLParser:
    """Parser HTML simplifié avec selectors configurables"""
    
    def parse_listing(self, html: str, config: dict) -> List[ParsedItem]:
        """Parse listing HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        container_selector = config.get('container', 'article')
        containers = soup.select(container_selector)[:20]
        
        items = []
        for container in containers:
            title = self._extract_text(container, ['h1', 'h2', 'h3', '.title'])
            url = self._extract_href(container, 'a')
            
            if title and url:
                items.append(ParsedItem(
                    title=title,
                    url=url,
                    date=self._extract_text(container, ['time', '.date']),
                    summary=self._extract_text(container, ['p', '.excerpt'])
                ))
        
        return items
    
    def _extract_text(self, container, selectors: List[str]) -> str:
        """Extrait texte depuis premier selector trouvé"""
        for selector in selectors:
            elem = container.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
        return ""
    
    def _extract_href(self, container, selector: str) -> str:
        """Extrait href depuis selector"""
        elem = container.select_one(selector)
        return elem.get('href', '') if elem else ""
