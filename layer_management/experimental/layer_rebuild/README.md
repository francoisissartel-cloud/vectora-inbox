# Layer Rebuild - EXPÉRIMENTAL

**Statut :** ⚠️ **EXPÉRIMENTAL - APPROCHE ABANDONNÉE**  
**Rôle :** Reconstruction layer avec boto3/botocore  
**Utilisé par :** Aucune Lambda V2

## Contenu

- `python/` : Dépendances complètes incluant boto3/botocore

## ⚠️ STATUT

**APPROCHE ABANDONNÉE** - V2 utilise boto3 via runtime Lambda.  
**CANDIDAT À SUPPRESSION** après évaluation (Phase 4).

## Historique

Test d'une layer "tout-en-un" avec AWS SDK inclus.  
Redondant avec layer_build/ + runtime Lambda boto3.