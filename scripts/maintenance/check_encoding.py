#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validation d'encodage - Détecte les caractères Unicode problématiques
Usage: python scripts/maintenance/check_encoding.py [path]
"""
import re
import sys
import io
from pathlib import Path
from typing import List, Tuple

# Forcer UTF-8 pour stdout sur Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def check_file(filepath: Path) -> List[Tuple[int, str]]:
    """Vérifie un fichier pour caractères Unicode problématiques"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return [(0, f"[ERROR] Cannot read file: {e}")]
    
    # Patterns problématiques
    emoji_pattern = re.compile(r'[\U0001F300-\U0001F9FF]')  # Emojis
    arrow_pattern = re.compile(r'[→←↑↓⇒⇐⇑⇓]')  # Flèches Unicode
    special_pattern = re.compile(r'[⚠️💡📦🎯✅❌🔥📋🚀]')  # Symboles courants
    
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        # Skip commentaires et docstrings (autorisés)
        stripped = line.strip()
        if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
            continue
        
        # Détecter problèmes
        if emoji_pattern.search(line):
            issues.append((i, f"Emoji detected: {line.strip()[:60]}..."))
        elif arrow_pattern.search(line):
            issues.append((i, f"Unicode arrow detected: {line.strip()[:60]}..."))
        elif special_pattern.search(line):
            issues.append((i, f"Special symbol detected: {line.strip()[:60]}..."))
    
    return issues

def main():
    """Point d'entrée principal"""
    # Déterminer chemin à scanner
    if len(sys.argv) > 1:
        scan_path = Path(sys.argv[1])
    else:
        scan_path = Path('scripts')
    
    if not scan_path.exists():
        print(f"[ERROR] Path not found: {scan_path}")
        sys.exit(1)
    
    print(f"[CHECK] Scanning Python files in: {scan_path}")
    print(f"[CHECK] Looking for Unicode characters that may cause encoding issues...")
    print()
    
    # Scanner tous les fichiers Python
    total_files = 0
    files_with_issues = 0
    total_issues = 0
    
    for py_file in scan_path.rglob('*.py'):
        total_files += 1
        issues = check_file(py_file)
        
        if issues:
            files_with_issues += 1
            total_issues += len(issues)
            print(f"[WARNING] {py_file}:")
            for line_num, message in issues:
                print(f"  Line {line_num}: {message}")
            print()
    
    # Résumé
    print("=" * 60)
    print(f"[SUMMARY] Scanned {total_files} Python files")
    print(f"[SUMMARY] Found {total_issues} issues in {files_with_issues} files")
    
    if files_with_issues > 0:
        print()
        print("[ACTION] Fix these issues by:")
        print("  1. Replace emojis with [PREFIX] tags (e.g., [OK], [ERROR])")
        print("  2. Replace Unicode arrows with ASCII -> or <-")
        print("  3. See .q-context/vectora-inbox-coding-standards.md for details")
        sys.exit(1)
    else:
        print("[OK] No encoding issues found!")
        sys.exit(0)

if __name__ == '__main__':
    main()
