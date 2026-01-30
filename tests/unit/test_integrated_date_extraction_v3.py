"""Test intégré extraction dates v3 - HTML -> nettoyage -> patterns"""
import re
import sys
from pathlib import Path

# Ajouter src_v2 au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src_v2"))

from vectora_core.ingest.content_parser import _clean_html_content, _parse_date_string


def test_integrated_date_extraction():
    """Test flux complet: HTML -> nettoyage -> extraction"""
    
    print("\n" + "="*70)
    print("TEST INTEGRE EXTRACTION DATES V3")
    print("="*70 + "\n")
    
    # Cas réels avec HTML
    test_cases = [
        {
            "html": "<div>PRESSRELEASES</div><div>27 January, 2026</div><div>Nanexa</div>",
            "expected_date": "2026-01-27",
            "description": "Nanexa press release"
        },
        {
            "html": "<p>Q2 2026</p><p>January 28, 2026</p><p>January</p>",
            "expected_date": "2026-01-28",
            "description": "MedinCell Q2"
        },
        {
            "html": "<span>2026</span><span>09 January 2026</span><span>Regulatory</span><span>Camurus</span>",
            "expected_date": "2026-01-09",
            "description": "Camurus regulatory"
        },
        {
            "html": "<div>December 9, 2025</div><div>December</div>",
            "expected_date": "2025-12-09",
            "description": "December date"
        },
    ]
    
    # Patterns v3
    patterns = [
        r'\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s*,?\s*\d{4})\b',
        r'\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}\s*,?\s*\d{4})\b',
        r'\b(\d{2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})\b',
    ]
    
    success_count = 0
    
    for test_case in test_cases:
        html = test_case["html"]
        expected = test_case["expected_date"]
        desc = test_case["description"]
        
        # Étape 1: Nettoyage HTML avec separator=' '
        cleaned = _clean_html_content(html)
        
        # Étape 2: Extraction avec patterns
        matched = False
        for pattern in patterns:
            matches = re.findall(pattern, cleaned, re.IGNORECASE)
            if matches:
                date_str = matches[0]
                parsed_date = _parse_date_string(date_str)
                if parsed_date == expected:
                    print(f"[OK] {desc:25} -> {parsed_date}")
                    print(f"     Cleaned: {cleaned[:60]}")
                    matched = True
                    success_count += 1
                    break
        
        if not matched:
            print(f"[FAIL] {desc:25} -> NO MATCH (expected {expected})")
            print(f"       Cleaned: {cleaned[:60]}")
    
    print(f"\n{'='*70}")
    print(f"RESULTAT: {success_count}/{len(test_cases)} tests reussis ({success_count*100//len(test_cases)}%)")
    print(f"{'='*70}\n")
    
    return success_count == len(test_cases)


if __name__ == "__main__":
    print("\nTEST INTEGRE CORRECTIF V3\n")
    
    success = test_integrated_date_extraction()
    
    if success:
        print("[SUCCESS] TOUS LES TESTS PASSENT\n")
        sys.exit(0)
    else:
        print("[FAIL] CERTAINS TESTS ECHOUENT\n")
        sys.exit(1)
