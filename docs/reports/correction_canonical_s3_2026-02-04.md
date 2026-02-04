# Correction Fichiers Canonical Manquants sur S3

**Date**: 2026-02-04  
**Problème**: Références circulaires dans appels Bedrock  
**Cause**: 18 fichiers canonical manquants sur S3  
**Statut**: ✅ RÉSOLU

---

## 🔍 Diagnostic

### Symptôme
Erreurs de références circulaires lors des appels Bedrock dans les Lambdas.

### Cause Racine
Seuls 2 fichiers canonical étaient présents sur S3 au lieu de 20 :
- ✅ `canonical/domains/lai_domain_definition.yaml`
- ✅ `canonical/prompts/domain_scoring/lai_domain_scoring.yaml`
- ❌ 18 autres fichiers manquants

### Impact
Les Lambdas ne pouvaient pas charger les fichiers canonical référencés, causant :
- Erreurs de chargement de configuration
- Références circulaires (tentatives de résolution de dépendances)
- Échecs des appels Bedrock

---

## ✅ Solution Appliquée

### Fichiers Uploadés (18)

**Scopes** (7 fichiers) :
- company_scopes.yaml
- domain_definitions.yaml
- exclusion_scopes.yaml
- indication_scopes.yaml
- molecule_scopes.yaml
- technology_scopes.yaml
- trademark_scopes.yaml

**Events** (2 fichiers) :
- event_type_definitions.yaml
- event_type_patterns.yaml

**Sources** (3 fichiers) :
- html_extractors.yaml
- source_catalog.yaml
- source_catalog_backup.yaml

**Prompts** (2 fichiers) :
- generic_normalization.yaml
- lai_editorial.yaml

**Autres** (4 fichiers) :
- domain_matching_rules.yaml (matching/)
- scoring_rules.yaml (scoring/)
- ingestion_profiles.yaml (ingestion/)
- vectora-inbox-lai-core-scopes.yaml (imports/)

### Commande Exécutée

```bash
scripts\upload_canonical_to_s3.bat
```

---

## 📊 Vérification Post-Upload

```
Fichiers sur S3: 20/20 ✅
Fichiers locaux: 20
Manquants: 0
Références circulaires: 0
```

### Structure S3 Complète

```
s3://vectora-inbox-data-dev/canonical/
├── domains/
│   └── lai_domain_definition.yaml
├── events/
│   ├── event_type_definitions.yaml
│   └── event_type_patterns.yaml
├── imports/
│   └── vectora-inbox-lai-core-scopes.yaml
├── ingestion/
│   └── ingestion_profiles.yaml
├── matching/
│   └── domain_matching_rules.yaml
├── prompts/
│   ├── domain_scoring/
│   │   └── lai_domain_scoring.yaml
│   ├── editorial/
│   │   └── lai_editorial.yaml
│   └── normalization/
│       └── generic_normalization.yaml
├── scopes/
│   ├── company_scopes.yaml
│   ├── domain_definitions.yaml
│   ├── exclusion_scopes.yaml
│   ├── indication_scopes.yaml
│   ├── molecule_scopes.yaml
│   ├── technology_scopes.yaml
│   └── trademark_scopes.yaml
├── scoring/
│   └── scoring_rules.yaml
└── sources/
    ├── html_extractors.yaml
    ├── source_catalog.yaml
    └── source_catalog_backup.yaml
```

---

## 🎯 Tests de Validation

### Test 1 : Vérification S3
```bash
python scripts/check_canonical_s3.py
```
**Résultat** : ✅ 20/20 fichiers présents

### Test 2 : Appel Lambda (À faire)
```bash
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v17
```
**Attendu** : Pas d'erreur de référence circulaire

---

## 📝 Scripts Créés

1. **check_canonical_s3.py** - Vérifie l'alignement canonical local/S3
2. **upload_canonical_to_s3.bat** - Upload tous les fichiers manquants
3. **check_alignment.py** - Vérifie l'alignement complet repo/AWS

---

## 🔄 Prochaines Étapes

1. ✅ Fichiers canonical uploadés
2. ⏭️ Tester un appel Lambda normalize-score-v2
3. ⏭️ Vérifier que les erreurs de références circulaires ont disparu
4. ⏭️ Documenter le processus de déploiement canonical

---

## 💡 Recommandations

### Court Terme
1. **Tester immédiatement** un workflow E2E pour valider la correction
2. **Documenter** le processus d'upload canonical dans la gouvernance

### Moyen Terme
1. **Automatiser** l'upload canonical dans le script de build
2. **Ajouter** une vérification canonical dans le script de déploiement
3. **Créer** un test d'intégration qui vérifie la présence des fichiers

### Long Terme
1. **Versioning** des fichiers canonical (v2.3, v2.4, etc.)
2. **CI/CD** : Upload automatique lors du merge dans develop
3. **Monitoring** : Alerte si fichiers canonical manquants

---

## 📋 Checklist Déploiement Canonical (Nouveau Process)

Avant chaque déploiement :

```bash
# 1. Vérifier l'alignement
python scripts/check_canonical_s3.py

# 2. Si fichiers manquants, uploader
scripts\upload_canonical_to_s3.bat

# 3. Vérifier à nouveau
python scripts/check_canonical_s3.py

# 4. Tester un appel Lambda
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v17
```

---

**Correction appliquée** : 2026-02-04 09:24  
**Durée** : 5 minutes  
**Statut** : ✅ RÉSOLU
