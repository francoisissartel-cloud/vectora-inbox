import sys
sys.path.insert(0, 'c:/Users/franc/OneDrive/Bureau/vectora-inbox')

from src_v2.vectora_core.ingest.date_extractor import DateExtractor
import requests

print("="*80)
print("TEST PFIZER - EXTRACTION DATE")
print("="*80)

url = 'https://www.pfizer.com/news/press-release/press-release-detail/pfizers-ultra-long-acting-injectable-glp-1-ra-shows-robust'

try:
    response = requests.get(url, timeout=10)
    html = response.text
    
    extractor = DateExtractor()
    
    # Test 1: HTML metadata
    print("\n[TEST 1] HTML metadata")
    result = extractor._extract_from_html(html)
    print(f"Result: {result}")
    
    # Test 2: Text extraction
    print("\n[TEST 2] Text extraction")
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()[:1000]
    result = extractor._extract_from_text(text)
    print(f"Result: {result}")
    print(f"Expected: 2026-02-10")
    
    if result:
        print(f"\nSTATUS: OK - Date extracted: {result}")
    else:
        print(f"\nSTATUS: FAIL - No date extracted")
        
except Exception as e:
    print(f"ERROR: {e}")

print("="*80)
