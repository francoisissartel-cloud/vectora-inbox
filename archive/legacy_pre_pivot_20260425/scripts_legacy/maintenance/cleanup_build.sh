#!/bin/bash
# Script de nettoyage des artefacts de build
# Supprime tout le contenu de .build/

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUILD_DIR="$REPO_ROOT/.build"

echo "🧹 Nettoyage artefacts de build"
echo ""

if [ ! -d "$BUILD_DIR" ]; then
    echo "❌ Dossier $BUILD_DIR n'existe pas"
    exit 1
fi

# Compte fichiers avant suppression
file_count=$(find "$BUILD_DIR" -type f ! -name "README.md" | wc -l)

if [ "$file_count" -eq 0 ]; then
    echo "✅ Aucun artefact à supprimer"
    exit 0
fi

echo "📊 $file_count fichier(s) à supprimer"
echo ""

# Suppression (garde README.md)
find "$BUILD_DIR" -type f ! -name "README.md" -delete
find "$BUILD_DIR" -type d -empty -delete

echo "✅ Nettoyage terminé"
