# Scripts de Maintenance

Scripts utilitaires pour maintenir la propreté du repository.

## Scripts Disponibles

### cleanup_tmp.py
Supprime les fichiers temporaires dans `.tmp/` plus anciens que 7 jours.

```bash
python scripts/maintenance/cleanup_tmp.py
```

### cleanup_build.sh
Supprime tous les artefacts de build dans `.build/`.

```bash
./scripts/maintenance/cleanup_build.sh
```

### validate_repo_hygiene.py
Vérifie qu'aucun fichier éphémère n'est présent à la racine.

```bash
python scripts/maintenance/validate_repo_hygiene.py
```

## Utilisation Recommandée

**Avant chaque commit :**
```bash
python scripts/maintenance/validate_repo_hygiene.py
```

**Nettoyage hebdomadaire :**
```bash
python scripts/maintenance/cleanup_tmp.py
./scripts/maintenance/cleanup_build.sh
```
