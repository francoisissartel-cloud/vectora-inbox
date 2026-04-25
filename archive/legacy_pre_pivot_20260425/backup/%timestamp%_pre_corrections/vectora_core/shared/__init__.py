"""
Vectora Core V2 - Modules Partagés

Ce package contient les modules partagés entre toutes les Lambdas V2 :
- Configuration et chargement depuis S3
- Opérations S3 standardisées  
- Modèles de données communs
- Utilitaires transverses

Ces modules sont utilisés par :
- Lambda ingest V2
- Lambda normalize-score V2  
- Lambda newsletter V2
"""

# Pas d'exports directs - chaque Lambda importe ce dont elle a besoin