import requests
from bs4 import BeautifulSoup
import re

# Tester le flux RSS FiercePharma
url_rss = "https://www.fiercepharma.com/rss/xml"

print("=== TEST FLUX RSS FIERCEPHARMA ===\n")

try:
    response = requests.get(url_rss, timeout=10)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Trouver l'item Genentech
    items = soup.find_all('item')
    print(f"Total items dans le flux: {len(items)}\n")
    
    for item in items[:5]:  # Premiers 5 items
        title = item.find('title')
        if title and 'Genentech' in title.text:
            print(f"ITEM TROUVÉ: {title.text[:80]}\n")
            
            # Vérifier tous les champs de date
            pubDate = item.find('pubDate')
            dc_date = item.find('dc:date')
            
            print(f"pubDate: {pubDate.text if pubDate else 'N/A'}")
            print(f"dc:date: {dc_date.text if dc_date else 'N/A'}")
            
            # Contenu
            description = item.find('description')
            if description:
                print(f"\nDescription: {description.text[:200]}")
            
            # Chercher date dans le contenu
            content = description.text if description else ""
            date_pattern = r'(Feb|January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}'
            matches = re.findall(date_pattern, content, re.IGNORECASE)
            print(f"\nDates trouvées dans contenu: {matches}")
            
            break
    
except Exception as e:
    print(f"Erreur: {e}")
