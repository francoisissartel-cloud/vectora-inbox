# Layer Build - Production V2

**Statut :** ✅ **ACTIF - CRITIQUE**  
**Rôle :** Construction de la layer vectora-inbox-common-deps-v2  
**Utilisé par :** Lambdas ingest-v2, normalize-score-v2

## Contenu

- `python/` : Dépendances communes optimisées
- `test_imports.py` : Tests d'imports
- `vectora-inbox-common-deps-v2.zip` : Package layer déployé

## Dépendances Incluses

- **PyYAML** : Parsing configurations YAML
- **requests** : Appels HTTP
- **feedparser** : Parsing RSS/Atom
- **beautifulsoup4** : Parsing HTML
- **certifi/urllib3** : HTTPS sécurisé
- **charset_normalizer** : Gestion encodage

## ⚠️ ATTENTION

**NE PAS SUPPRIMER** - Layer critique pour le pipeline V2