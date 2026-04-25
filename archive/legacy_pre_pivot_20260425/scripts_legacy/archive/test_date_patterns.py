import re
from datetime import datetime

def _parse_date_string(date_str):
    """Parse une chaîne de date"""
    if not date_str:
        return None
    
    date_str = date_str.strip()
    # Ajouter un espace entre chiffre et mois si absent
    date_str = re.sub(r'(\d)(January|February|March|April|May|June|July|August|September|October|November|December)', r'\1 \2', date_str, flags=re.IGNORECASE)
    # Ajouter un espace entre mois et année si absent
    date_str = re.sub(r'(January|February|March|April|May|June|July|August|September|October|November|December)(\d{4})', r'\1 \2', date_str, flags=re.IGNORECASE)
    
    date_formats = [
        '%Y-%m-%d',
        '%d %B %Y',
        '%B %d, %Y',
        '%d %b %Y',
    ]
    
    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    return None

# Test cases depuis les items réels
test_cases = [
    "09 January 2026RegulatoryCamurus announces FDA acceptance",
    "30 December 2025RegulatoryChange in number of shares",
    "16 December 2025Camurus and Gubra enter into",
    "28 November 2025RegulatoryChange in number",
    "January 28, 2026 January 28, 2026",  # MedinCell
    "December 9, 2025 December 9, 2025",  # MedinCell
]

print("=== TEST EXTRACTION DATES ===\n")

patterns = [
    r'(\d{1,2}\s*(?:January|February|March|April|May|June|July|August|September|October|November|December)\s*\d{4})',
    r'(\d{4}-\d{2}-\d{2})',
]

for test in test_cases:
    print(f"Test: {test[:60]}")
    
    # Nettoyer titre
    title_clean = re.sub(r'(\d{4})([A-Z])', r'\1 \2', test)
    print(f"  Nettoyé: {title_clean[:60]}")
    
    found = False
    for pattern in patterns:
        matches = re.findall(pattern, title_clean, re.IGNORECASE)
        if matches:
            print(f"  Pattern matched: {pattern[:40]}")
            print(f"  Matches: {matches}")
            parsed = _parse_date_string(matches[0])
            if parsed:
                print(f"  ✓ Date extraite: {parsed}")
                found = True
                break
    
    if not found:
        print(f"  ✗ Aucune date extraite")
    print()
