#!/usr/bin/env python3
"""
Alias pour lister les backups locaux
"""

import sys
import os

# Ajouter le chemin du script principal
sys.path.append(os.path.dirname(__file__))

from create_local_backup import list_backups

if __name__ == "__main__":
    list_backups()