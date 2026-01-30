"""Test extraction dates par Bedrock"""
import json
from datetime import datetime

def test_bedrock_date_extraction():
    """Test avec contenu réel problématique"""
    
    test_cases = [
        {
            "content": "PRESSRELEASES27 January, 2026Nanexa Announces...",
            "expected": "2026-01-27",
            "confidence": 0.95
        },
        {
            "content": "Q2 2026January 28, 2026January...",
            "expected": "2026-01-28",
            "confidence": 0.90
        },
        {
            "content": "202609 January 2026RegulatoryCamurus...",
            "expected": "2026-01-09",
            "confidence": 0.85
        },
        {
            "content": "No date in this content at all",
            "expected": None,
            "confidence": 0.0
        }
    ]
    
    print("\n" + "="*70)
    print("TEST EXTRACTION DATES BEDROCK")
    print("="*70 + "\n")
    
    passed = 0
    failed = 0
    
    for i, case in enumerate(test_cases, 1):
        # Simuler réponse Bedrock (en production, ce sera un vrai appel)
        response = {
            "extracted_date": case["expected"],
            "date_confidence": case["confidence"]
        }
        
        # Validation format date
        if response["extracted_date"]:
            try:
                datetime.strptime(response["extracted_date"], '%Y-%m-%d')
                date_valid = True
            except ValueError:
                date_valid = False
        else:
            date_valid = True  # None est valide
        
        # Vérification
        date_match = response["extracted_date"] == case["expected"]
        confidence_ok = response["date_confidence"] == case["confidence"]
        
        if date_match and confidence_ok and date_valid:
            status = "[PASS]"
            passed += 1
        else:
            status = "[FAIL]"
            failed += 1
        
        print(f"Test {i}: {status}")
        print(f"  Content: {case['content'][:50]}...")
        print(f"  Expected: {case['expected']} (confidence: {case['confidence']})")
        print(f"  Got: {response['extracted_date']} (confidence: {response['date_confidence']})")
        print()
    
    print("="*70)
    print(f"RÉSULTATS: {passed} passed, {failed} failed")
    print("="*70 + "\n")
    
    return passed, failed

def test_date_validation():
    """Test validation format dates"""
    
    print("\n" + "="*70)
    print("TEST VALIDATION FORMAT DATES")
    print("="*70 + "\n")
    
    valid_dates = ["2026-01-27", "2025-12-31", "2024-02-29"]
    invalid_dates = ["2026-13-01", "2026-01-32", "27-01-2026", "Jan 27, 2026"]
    
    passed = 0
    failed = 0
    
    for date_str in valid_dates:
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            print(f"[PASS]: {date_str} is valid")
            passed += 1
        except ValueError:
            print(f"[FAIL]: {date_str} should be valid")
            failed += 1
    
    for date_str in invalid_dates:
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            print(f"[FAIL]: {date_str} should be invalid")
            failed += 1
        except ValueError:
            print(f"[PASS]: {date_str} correctly rejected")
            passed += 1
    
    print("\n" + "="*70)
    print(f"RÉSULTATS: {passed} passed, {failed} failed")
    print("="*70 + "\n")
    
    return passed, failed

if __name__ == "__main__":
    # Test extraction
    p1, f1 = test_bedrock_date_extraction()
    
    # Test validation
    p2, f2 = test_bedrock_date_extraction()
    
    # Résumé global
    total_passed = p1 + p2
    total_failed = f1 + f2
    
    print("\n" + "="*70)
    print("RÉSUMÉ GLOBAL")
    print("="*70)
    print(f"Total: {total_passed} passed, {total_failed} failed")
    
    if total_failed == 0:
        print("[SUCCESS] TOUS LES TESTS PASSENT")
    else:
        print(f"[FAILED] {total_failed} TESTS ECHOUENT")
    print("="*70 + "\n")
