"""
validate_yaml_regexes.py
------------------------
Charge canonical/sources/source_catalog.yaml et tente de compiler toutes
les regex présentes dans les champs `date_extraction_patterns`.

Usage :
    python scripts/maintenance/validate_yaml_regexes.py

Retourne :
    0 si toutes les regex compilent
    1 si au moins une regex est invalide (message d'erreur affiché)

Utile en pre-commit ou en CI pour détecter rapidement un pattern cassé.
"""

import re
import sys
import yaml
from pathlib import Path


CATALOG_PATH = Path(__file__).parent.parent.parent / "canonical" / "sources" / "source_catalog.yaml"


def validate_regexes(catalog_path: Path) -> list[dict]:
    """Charge le catalogue et compile chaque regex. Retourne la liste des erreurs."""
    with open(catalog_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    errors = []
    for source in data.get("sources", []):
        source_key = source.get("source_key", "<inconnu>")
        for pattern in source.get("date_extraction_patterns", []):
            try:
                re.compile(pattern)
            except re.error as e:
                errors.append({
                    "source_key": source_key,
                    "pattern": pattern,
                    "error": str(e),
                })
    return errors


def main() -> int:
    if not CATALOG_PATH.exists():
        print(f"[ERREUR] Fichier introuvable : {CATALOG_PATH}", file=sys.stderr)
        return 1

    errors = validate_regexes(CATALOG_PATH)

    # Comptage pour le rapport
    with open(CATALOG_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    total = sum(len(s.get("date_extraction_patterns", [])) for s in data.get("sources", []))
    sources_count = len(data.get("sources", []))

    if errors:
        print(f"[ECHEC] {len(errors)} regex invalide(s) sur {total} testées ({sources_count} sources) :\n")
        for err in errors:
            print(f"  source : {err['source_key']}")
            print(f"  pattern: {err['pattern']}")
            print(f"  erreur : {err['error']}\n")
        return 1

    print(f"[OK] {total} regex compilées sans erreur sur {sources_count} sources.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
