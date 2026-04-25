#!/usr/bin/env python3
"""
Script de validation de l'hygiène du repository
Vérifie qu'aucun fichier éphémère n'est à la racine
"""
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent

FORBIDDEN_PATTERNS = [
    "event_*.json",
    "payload*.json",
    "response_*.json",
    "items_*.json",
    "ingested_items_*.json",
    "newsletter_*.json",
    "logs_*.txt",
    "bedrock_logs.json",
    "*.zip",
    "*_arn.txt",
    "execute_*.py",
    "phase6_*.py",
    "phase7_*.py",
]

def validate_root():
    """Vérifie la propreté de la racine"""
    violations = []
    
    for pattern in FORBIDDEN_PATTERNS:
        matches = list(REPO_ROOT.glob(pattern))
        for match in matches:
            if match.is_file():
                violations.append(match.name)
    
    if violations:
        print("VIOLATIONS DETECTEES A LA RACINE:\n")
        for v in violations:
            print(f"  - {v}")
        print(f"\nDeplacer vers .tmp/ ou .build/")
        return False
    else:
        print("Repository propre - Aucune violation")
        return True

if __name__ == "__main__":
    print("Validation hygiene repository\n")
    success = validate_root()
    exit(0 if success else 1)
