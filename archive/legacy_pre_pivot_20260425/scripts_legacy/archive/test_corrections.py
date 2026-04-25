"""
Test rapide des corrections d'extraction
"""
import sys
sys.path.insert(0, 'c:/Users/franc/OneDrive/Bureau/vectora-inbox')

from src_v2.vectora_core.ingest.date_extractor import DateExtractor
from src_v2.vectora_core.ingest.content_extractor import ContentExtractor
import requests

print("="*80)
print("TEST CORRECTIONS INGESTION")
print("="*80)

# Test 1: Extraction date Nanexa
print("\n[TEST 1] Extraction date Nanexa")
print("-"*80)
url_nanexa = 'https://nanexa.com/mfn_news/nanexa-and-moderna-enter-into-license-and-option-agreement-for-the-development-of-pharmashell-based-products/'
try:
    response = requests.get(url_nanexa, timeout=10)
    if response.status_code == 200:
        html = response.text
        extractor = DateExtractor()
        result = extractor._extract_from_html(html)
        print(f"Result: {result}")
        print(f"Expected: 2025-12-10")
        print(f"Status: {'OK' if result == '2025-12-10' else 'FAIL'}")
    else:
        print(f"HTTP Error: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: Extraction date Pfizer
print("\n[TEST 2] Extraction date Pfizer")
print("-"*80)
url_pfizer = 'https://www.pfizer.com/news/press-release/press-release-detail/pfizers-ultra-long-acting-injectable-glp-1-ra-shows-robust'
try:
    response = requests.get(url_pfizer, timeout=10)
    if response.status_code == 200:
        html = response.text
        extractor = DateExtractor()
        result = extractor._extract_from_html(html)
        print(f"Result: {result}")
        print(f"Expected: 2026-02-10 (or similar)")
        print(f"Status: {'OK' if result else 'FAIL'}")
    else:
        print(f"HTTP Error: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")

# Test 3: Enrichissement contenu Pfizer
print("\n[TEST 3] Enrichissement contenu Pfizer")
print("-"*80)
try:
    extractor = ContentExtractor(max_length=3000)
    content = extractor.extract(url_pfizer)
    if content:
        print(f"Length: {len(content)} chars")
        print(f"Words: {len(content.split())} words")
        print(f"Preview: {content[:200]}...")
        print(f"Status: {'OK' if len(content) > 500 else 'FAIL (too short)'}")
    else:
        print("No content extracted")
        print("Status: FAIL")
except Exception as e:
    print(f"Error: {e}")

# Test 4: Scraping Camurus
print("\n[TEST 4] Scraping Camurus")
print("-"*80)
url_camurus = 'https://www.camurus.com/media/press-releases/'
try:
    response = requests.get(url_camurus, timeout=10)
    if response.status_code == 200:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Tester différents selectors
        articles = soup.find_all('article')
        divs = soup.find_all('div', class_=lambda x: x and ('news' in x.lower() or 'press' in x.lower()) if x else False)
        
        print(f"Found {len(articles)} <article> tags")
        print(f"Found {len(divs)} news/press divs")
        
        if articles:
            print("\nFirst article:")
            article = articles[0]
            title = article.find(['h1', 'h2', 'h3'])
            link = article.find('a', href=True)
            print(f"  Title: {title.get_text() if title else 'N/A'}")
            print(f"  Link: {link.get('href') if link else 'N/A'}")
        
        print(f"Status: {'OK' if articles or divs else 'FAIL (no containers found)'}")
    else:
        print(f"HTTP Error: {response.status_code}")
        print("Status: FAIL")
except Exception as e:
    print(f"Error: {e}")
    print("Status: FAIL")

print("\n" + "="*80)
print("FIN DES TESTS")
print("="*80)
