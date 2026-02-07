# Audit Fichiers Canonical S3 - Lambda Ingestion v1.7.0

**Date**: 2026-02-07  
**Bucket**: vectora-inbox-config-dev  
**Objectif**: Verifier presence de tous les fichiers canonical necessaires

---

## 📋 Fichiers Necessaires pour Lambda Ingest-v2

### 1. Configuration Client
**Chemin**: `clients/{client_id}.yaml`
**Status**: ✅ PRESENT
**Exemple**: `clients/lai_weekly_v24.yaml`
**Utilisation**: Configuration du client (sources, period_days, etc.)

### 2. Source Catalog
**Chemin**: `canonical/sources/source_catalog.yaml`
**Status**: ✅ PRESENT (7.5 KB, 2026-02-06)
**Utilisation**: 
- Liste des sources RSS/HTML disponibles
- Bouquets de sources (lai_corporate_mvp, lai_press_mvp)
- Metadata sources (URL, type, company_id, etc.)

### 3. Exclusion Scopes
**Chemin**: `canonical/scopes/exclusion_scopes.yaml`
**Status**: ✅ PRESENT (4.5 KB, 2026-02-06)
**Utilisation**: 
- Termes d'exclusion pour filtrage (hr_content, financial_generic, etc.)
- Charge par initialize_exclusion_scopes()
- 8+ categories d'exclusion

### 4. Company Scopes
**Chemin**: `canonical/scopes/company_scopes.yaml`
**Status**: ✅ PRESENT (5.0 KB, 2025-12-10)
**Utilisation**:
- Liste pure players LAI (14 entreprises)
- Liste hybrid players (27 entreprises)
- Charge par initialize_company_scopes()

### 5. Technology Scopes
**Chemin**: `canonical/scopes/technology_scopes.yaml`
**Status**: ✅ PRESENT (4.6 KB, 2025-12-13)
**Utilisation**:
- LAI keywords (core_phrases, technology_terms_high_precision, interval_patterns)
- Charge par initialize_lai_keywords()
- ~83 termes technologiques

### 6. Trademark Scopes
**Chemin**: `canonical/scopes/trademark_scopes.yaml`
**Status**: ✅ PRESENT (1.2 KB, 2026-01-30)
**Utilisation**:
- Trademarks LAI globaux (Uzedy, Bydureon, Invega, etc.)
- Charge par initialize_lai_keywords()
- ~76 trademarks

### 7. Ingestion Profiles (Optionnel)
**Chemin**: `canonical/ingestion/ingestion_profiles.yaml`
**Status**: ✅ PRESENT (10.8 KB, 2026-02-06)
**Utilisation**: Profiles d'ingestion (non utilise actuellement par le code v1.7.0)

---

## ✅ Verification S3

### Commande Executee
```bash
aws s3 ls s3://vectora-inbox-config-dev/canonical/ --recursive
```

### Resultats
```
✅ canonical/sources/source_catalog.yaml (7.5 KB)
✅ canonical/scopes/exclusion_scopes.yaml (4.5 KB)
✅ canonical/scopes/company_scopes.yaml (5.0 KB)
✅ canonical/scopes/technology_scopes.yaml (4.6 KB)
✅ canonical/scopes/trademark_scopes.yaml (1.2 KB)
✅ canonical/ingestion/ingestion_profiles.yaml (10.8 KB)
```

**Conclusion**: Tous les fichiers necessaires sont presents sur S3 ✅

---

## 🔍 Analyse Probleme Ingestion (0 items)

### Hypotheses

#### 1. Sources RSS Vides ❓
**Probabilite**: HAUTE
**Raison**: Les sources RSS corporate (MedinCell, Camurus, etc.) publient rarement
**Verification**: Tester manuellement les URLs RSS

#### 2. Filtrage Trop Strict ❓
**Probabilite**: MOYENNE
**Raison**: Nouveau filtrage avec 122 termes d'exclusion vs 20 avant
**Impact**: Possible sur-filtrage

#### 3. Parsing RSS Echoue ❓
**Probabilite**: FAIBLE
**Raison**: Logs montrent "0 items recuperes" (pas d'erreur de parsing)

#### 4. Date Extraction Patterns Manquants ❓
**Probabilite**: MOYENNE
**Raison**: Sources sans dates extraites = filtrees par filtre temporel

---

## 🔧 Actions Recommandees

### Action 1: Verifier URLs RSS Manuellement
```bash
# Tester une source RSS
curl "https://www.medincell.com/feed/" -I
```

### Action 2: Verifier Logs Detailles
```bash
aws logs tail /aws/lambda/vectora-inbox-ingest-v2-dev --since 5m --format short \
  --profile rag-lai-prod --region eu-west-3 | findstr "items parsed"
```

### Action 3: Tester avec Mode Broad
Modifier temporairement ingestion_mode dans client config:
```yaml
pipeline:
  ingestion_mode: "broad"  # Au lieu de "balanced"
```

### Action 4: Verifier Source Catalog
```bash
aws s3 cp s3://vectora-inbox-config-dev/canonical/sources/source_catalog.yaml - \
  --profile rag-lai-prod --region eu-west-3 | grep -A 10 "medincell"
```

---

## 📊 Diagnostic Complet

### Logs Lambda (Derniere Execution)
```
[INFO] Etape 2.5 : Initialisation des exclusion scopes depuis S3
[INFO] Exclusion scopes charges: 11 categories ✅
[INFO] Etape 2.6 : Initialisation des company scopes depuis S3
[INFO] Company scopes: 14 pure players, 27 hybrid players ✅
[INFO] Etape 2.7 : Initialisation des LAI keywords depuis S3
[INFO] LAI keywords: 159 termes charges ✅

[INFO] Source press_corporate__medincell : 0 items recuperes ❌
[INFO] Source press_corporate__camurus : 0 items recuperes ❌
[INFO] Source press_sector__fiercebiotech : 0 items recuperes ❌
[INFO] Total items apres profils : 0 depuis 7 sources ❌
```

**Analyse**: 
- ✅ Tous les scopes charges correctement
- ❌ Aucun item recupere depuis les sources RSS
- ❌ Probleme en amont du filtrage (parsing ou sources vides)

---

## 🎯 Prochaines Etapes

### Etape 1: Verifier Source Catalog
Extraire et analyser le source_catalog.yaml pour verifier:
- URLs RSS valides
- Champs enabled=true
- Champs ingestion_mode != "none"
- Date extraction patterns presents

### Etape 2: Tester Manuellement une Source
Creer un script de test pour:
- Fetcher une URL RSS
- Parser le contenu
- Verifier si items sont extraits

### Etape 3: Analyser Logs Parsing
Chercher dans les logs:
- Erreurs de parsing RSS
- Erreurs de connexion HTTP
- Timeouts

### Etape 4: Tester avec Source Active
Identifier une source RSS avec publications recentes:
- FierceBiotech (presse sectorielle)
- Endpoints News (presse sectorielle)

---

## 📝 Conclusion

**Fichiers Canonical**: ✅ Tous presents et charges correctement

**Probleme Ingestion**: ❌ Sources RSS ne retournent aucun item
- Pas un probleme de scopes S3
- Pas un probleme de filtrage (0 items avant filtrage)
- Probleme probable: Sources RSS vides ou parsing echoue

**Recommandation**: Analyser le source_catalog.yaml et tester manuellement les URLs RSS

---

**Rapport cree le**: 2026-02-07 09:10  
**Auteur**: Q Developer
