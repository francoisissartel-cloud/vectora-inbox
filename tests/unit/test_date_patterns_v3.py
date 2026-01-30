"""Test patterns de dates v3 avec exemples réels"""
import re
import sys
from pathlib import Path

# Ajouter src_v2 au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src_v2"))

from vectora_core.ingest.content_parser import _parse_date_string


def test_date_patterns_real_content():
    """Test avec contenu réel problématique"""
    
    # Exemples réels du diagnostic
    test_cases = [
        ("PRESSRELEASES27 January, 2026Nanexa", "2026-01-27"),
        ("Q2 2026January 28, 2026January", "2026-01-28"),
        ("202609 January 2026RegulatoryCamurus", "2026-01-09"),
        ("December 9, 2025December", "2025-12-09"),
        ("27 January, 2026", "2026-01-27"),
        ("January 28, 2026", "2026-01-28"),
        ("09 January 2026", "2026-01-09"),
    ]
    
    # Patterns v3 avec word boundaries
    patterns = [
        r'\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s*,?\s*\d{4})\b',
        r'\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}\s*,?\s*\d{4})\b',
        r'\b(\d{2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})\b',
    ]
    
    print("\n" + "="*70)
    print("TEST PATTERNS DATES V3 - WORD BOUNDARIES")
    print("="*70 + "\n")
    
    success_count = 0
    for content, expected_date in test_cases:
        matched = False
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                date_str = matches[0]
                parsed_date = _parse_date_string(date_str)
                if parsed_date == expected_date:
                    print(f"[OK] {content[:40]:40} -> {parsed_date}")
                    matched = True
                    success_count += 1
                    break
        
        if not matched:
            print(f"[FAIL] {content[:40]:40} -> NO MATCH (expected {expected_date})")
    
    print(f"\n{'='*70}")
    print(f"RÉSULTAT: {success_count}/{len(test_cases)} tests réussis ({success_count*100//len(test_cases)}%)")
    print(f"{'='*70}\n")
    
    return success_count == len(test_cases)


def test_html_cleaning():
    """Test nettoyage HTML avec separator"""
    from bs4 import BeautifulSoup
    
    print("\n" + "="*70)
    print("TEST NETTOYAGE HTML - SEPARATOR=' '")
    print("="*70 + "\n")
    
    test_cases = [
        ("<div>PRESSRELEASES</div><div>27 January, 2026</div>", "PRESSRELEASES 27 January, 2026"),
        ("<p>Q2 2026</p><p>January 28, 2026</p>", "Q2 2026 January 28, 2026"),
        ("<span>2026</span><span>09 January 2026</span>", "2026 09 January 2026"),
    ]
    
    for html, expected in test_cases:
        # Méthode v3 avec separator
        soup = BeautifulSoup(html, 'html.parser')
        cleaned = soup.get_text(separator=' ', strip=True)
        
        if expected in cleaned:
            print(f"[OK] {html[:40]:40} -> {cleaned}")
        else:
            print(f"[FAIL] {html[:40]:40} -> {cleaned} (expected: {expected})")
    
    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    print("\nTESTS UNITAIRES CORRECTIF V3\n")
    
    # Test 1: Patterns
    patterns_ok = test_date_patterns_real_content()
    
    # Test 2: HTML cleaning
    test_html_cleaning()
    
    # Résultat final
    if patterns_ok:
        print("[SUCCESS] TOUS LES TESTS PASSENT\n")
        sys.exit(0)
    else:
        print("[FAIL] CERTAINS TESTS ECHOUENT\n")
        sys.exit(1)
