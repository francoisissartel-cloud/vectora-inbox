# Phase 2 : Ingestion DEV - lai_weekly_v2 (Résultats Réels)

**Date d'exécution** : 2025-12-11 09:31 UTC  
**Client** : lai_weekly_v2  
**Période** : 30 jours (default_period_days)  
**Environnement** : DEV AWS (rag-lai-prod, eu-west-3)  
**RequestId** : cc7c09a6-da12-402d-a95d-eabde1f62b72

---

## Résumé Exécutif

⚠️ **Exécution partiellement réussie** : Ingestion fonctionnelle mais limitée par ThrottlingExceptions Bedrock  
✅ **Configuration cohérente** : lai_weekly_v2.yaml correctement chargé et résolu  
🔴 **Problème critique** : Limite de débit Bedrock atteinte (ThrottlingException)

---

## 1. Métriques d'Ingestion (Données Réelles)

### 1.1 Sources Traitées
**Total sources configurées** : 8 sources  
**Sources activées** : 8 sources  
**Sources traitées avec succès** :

| Source | Type | Mode | Items Récupérés | Status |
|--------|------|------|----------------|--------|
| press_sector__fiercebiotech | RSS | rss | 25 | ✅ |
| press_sector__endpoints_news | RSS | rss | 24 | ✅ |
| press_corporate__nanexa | HTML | html | 8 | ✅ |
| press_sector__fiercepharma | RSS | rss | 25 | ✅ |
| press_corporate__delsitech | HTML | html | 10 | ✅ |
| press_corporate__medincell | HTML | html | 12 | ✅ |
| press_corporate__camurus | HTML | html | 0 | ⚠️ Structure non reconnue |
| press_corporate__peptron | HTML | html | 0 | 🔴 Erreur SSL |

### 1.2 Métriques Quantitatives
- **Items bruts récupérés** : 104 items
- **Items après filtre temporel** : 104 items (0 items trop anciens)
- **Items envoyés à Bedrock** : 104 items (normalisation en cours)
- **Taux de rétention temporelle** : 100%

### 1.3 Répartition par Type de Source
- **Sources presse (RSS)** : 74 items (71%)
- **Sources corporate (HTML)** : 30 items (29%)
- **Sources en erreur** : 2 sources (25%)

---

## 2. Analyse Qualitative des Sources

### 2.1 Sources Performantes ✅

**FierceBiotech & FiercePharma (RSS)**
- Flux RSS fonctionnels et riches
- 25 items chacun, contenu récent
- Parsing RSS stable

**MedinCell, DelSiTech, Nanexa (HTML)**
- Parsing HTML fonctionnel
- 8-12 items par source
- Contenu corporate LAI pertinent

### 2.2 Sources Problématiques ⚠️🔴

**Camurus (HTML)**
- ⚠️ Structure HTML non reconnue
- 0 items récupérés malgré 43,349 caractères téléchargés
- **Action requise** : Mise à jour de l'extracteur HTML

**Peptron (HTML)**
- 🔴 Erreur SSL : "certificate verify failed: Hostname mismatch"
- **Action requise** : Correction certificat ou bypass SSL pour cette source

---

## 3. Problème Critique : ThrottlingException Bedrock

### 3.1 Symptômes Observés
- **Erreur récurrente** : "Too many requests, please wait before trying again"
- **Tentatives de retry** : 4 tentatives par item avec backoff exponentiel
- **Durée d'exécution** : >7 minutes (toujours en cours)
- **Items normalisés** : Processus interrompu par les limites de débit

### 3.2 Impact sur l'Audit
- **Normalisation incomplète** : Impossible d'analyser les entités détectées
- **Pas d'objets S3** : Aucun fichier normalized/lai_weekly_v2/ créé
- **Blocage Phase 3** : Impossible de continuer sans données normalisées

### 3.3 Causes Probables
1. **Limite de débit Bedrock** : 104 appels simultanés (4 workers parallèles)
2. **Modèle utilisé** : Possiblement un modèle avec limite stricte
3. **Région eu-west-3** : Limites potentiellement plus restrictives

---

## 4. Configuration Client Validée

### 4.1 Résolution des Bouquets ✅
```
Bouquets activés : ['lai_corporate_mvp', 'lai_press_mvp']
Bouquet 'lai_corporate_mvp' résolu : 5 sources
Bouquet 'lai_press_mvp' résolu : 3 sources
Total de sources uniques après résolution : 8
```

### 4.2 Scopes Canonical Chargés ✅
- **Companies** : 4 clés (lai_companies_global, etc.)
- **Molecules** : 5 clés
- **Trademarks** : 1 clé (lai_trademarks_global)
- **Technologies** : 1 clé (lai_keywords)
- **Indications** : 3 clés
- **Exclusions** : 7 clés

### 4.3 Période Temporelle ✅
- **Period_days résolu** : 30 jours (payload: 30)
- **Filtre temporel** : items antérieurs au 2025-11-11 ignorés
- **Résultat** : 100% des items conservés (tous récents)

---

## 5. Leviers d'Action Identifiés

### 5.1 Ingestion (Priorité 1)
1. **Corriger Peptron SSL** : Bypass SSL ou correction certificat
2. **Mettre à jour extracteur Camurus** : Structure HTML changée
3. **Optimiser débit Bedrock** : Réduire workers parallèles ou implémenter rate limiting

### 5.2 Bedrock (Priorité 1 - Critique)
1. **Réduire concurrence** : Passer de 4 à 2 workers parallèles
2. **Implémenter rate limiting** : Délai entre appels Bedrock
3. **Vérifier quotas** : Augmenter limites Bedrock si possible
4. **Modèle alternatif** : Tester avec un modèle moins restrictif

### 5.3 Profils d'Ingestion (Priorité 2)
1. **Valider filtrage** : Une fois Bedrock fonctionnel, vérifier si les 104 items sont pertinents
2. **Ajuster seuils** : Potentiellement réduire le bruit en amont

---

## 6. Recommandations pour la Suite

### 6.1 Correction Immédiate
1. **Résoudre ThrottlingException** avant de continuer Phase 3
2. **Relancer ingestion** avec paramètres Bedrock ajustés
3. **Corriger sources en erreur** (Peptron, Camurus)

### 6.2 Validation Post-Correction
1. **Vérifier objets S3** : s3://vectora-inbox-data-dev/normalized/lai_weekly_v2/
2. **Analyser qualité** : Entités détectées vs attendues
3. **Mesurer économies** : Items filtrés vs normalisés

---

## Conclusion Phase 2

**Status** : 🔴 **Bloqué par limites Bedrock**

**Points positifs** :
- Configuration lai_weekly_v2 fonctionnelle
- Ingestion sources majoritairement réussie (6/8 sources)
- Filtrage temporel opérationnel

**Blocages critiques** :
- ThrottlingException Bedrock empêche normalisation
- 2 sources en erreur (Peptron SSL, Camurus HTML)

**Prochaine étape** :
- Corriger paramètres Bedrock puis relancer
- Une fois normalisé, continuer Phase 3 avec données réelles

---

*Diagnostic Phase 2 basé sur exécution réelle DEV - 2025-12-11 09:31 UTC*