# Phase 2 – Run Ingestion V2 Réel - lai_weekly_v4

**Date :** 19 décembre 2025  
**Durée :** 45 minutes  
**Objectif :** Exécuter ingest_v2 pour lai_weekly_v4 et analyser les résultats

---

## ✅ Commande d'Invocation Utilisée

```bash
aws lambda invoke \
  --function-name vectora-inbox-ingest-v2-dev \
  --payload '{"client_id": "lai_weekly_v4"}' \
  --cli-binary-format raw-in-base64-out \
  --region eu-west-3 \
  --profile rag-lai-prod \
  response_ingest_lai_v4.json
```

**Statut :** ✅ **SUCCÈS** (StatusCode: 200)

---

## 📊 Métriques d'Exécution

### Résultat Global
- **Timestamp début :** 2025-12-19T20:15:29.408104
- **Durée totale :** 18.35 secondes
- **Statut :** success
- **Mode :** balanced (ingestion_mode)
- **Période :** 30 jours (period_days_used)
- **Mode temporel :** strict

### Sources Traitées
- **Sources processées :** 7/8
- **Sources échouées :** 1/8
- **Taux de succès :** 87.5%

### Items Ingérés
- **Items ingérés bruts :** 16
- **Items filtrés :** 0
- **Items dédupliqués :** 1
- **Items finaux :** 15

### Chemin S3
- **Fichier généré :** `s3://vectora-inbox-data-dev/ingested/lai_weekly_v4/2025/12/19/items.json`
- **Taille du fichier :** 12.6 KiB

---

## 🔍 Analyse du Contenu Ingéré

### Répartition par Source
- **press_corporate__delsitech :** 2 items
- **press_corporate__medincell :** 7 items
- **press_corporate__nanexa :** 6 items
- **press_corporate__camurus :** 0 items (source échouée)
- **press_corporate__peptron :** 0 items (source échouée)
- **Sources presse (RSS) :** 0 items

### Sources Actives Identifiées
1. **DelSiTech** (2 items)
   - Événements/conférences (Partnership Opportunities, BIO Convention)
   
2. **MedinCell** (7 items) - **Source la plus productive**
   - Résultats financiers semestriels
   - Soumission NDA Olanzapine LAI (Teva partnership)
   - Grant malaria
   - Nomination Dr Grace Kim
   - Intégration MSCI World Small Cap Index
   - Croissance UZEDY® et pipeline Olanzapine
   - Approbation FDA UZEDY® pour Bipolar I Disorder

3. **Nanexa** (6 items) - **Source très productive**
   - **SIGNAL FORT :** Accord de licence avec Moderna pour PharmaShell®
   - Rapports intermédiaires (janvier-septembre, janvier-juin 2025)
   - Optimisation formulations GLP-1
   - Brevets PharmaShell approuvés au Japon

### Qualité du Contenu
- **Signaux LAI forts détectés :**
  - "Extended-Release Injectable Suspension" (MedinCell/UZEDY®)
  - "Olanzapine LAI" (Long-Acting Injectable)
  - "PharmaShell®-based products" (Nanexa technology)
  - "Once-Monthly Treatment"

- **Événements significatifs :**
  - Soumission NDA FDA pour Olanzapine LAI
  - Partenariat Nanexa-Moderna (USD 500M potentiel)
  - Approbation FDA élargie pour UZEDY®

---

## ⚠️ Sources Échouées

### Sources Non Productives
- **press_corporate__camurus :** 0 items
- **press_corporate__peptron :** 0 items
- **Sources presse RSS :** 0 items (fiercebiotech, fiercepharma, endpoints_news)

### Hypothèses d'Échec
1. **Sources corporate :** Possibles problèmes d'accès HTML ou structure de page modifiée
2. **Sources RSS :** Possibles problèmes de connectivité ou flux RSS indisponibles
3. **Filtrage temporel :** Contenu trop ancien (> 30 jours)

---

## 🎯 Signaux LAI Détectés

### Technologies LAI Identifiées
- **Extended-Release Injectable** (MedinCell/UZEDY®)
- **PharmaShell®** (Nanexa technology platform)
- **Long-Acting Injectable** (Olanzapine LAI)
- **Once-Monthly Treatment** (dosage interval)

### Sociétés LAI Actives
- **MedinCell :** Pure player LAI très actif (7 items)
- **Nanexa :** Technologie PharmaShell® en expansion (6 items)
- **DelSiTech :** Présence événementielle (2 items)

### Molécules/Produits LAI
- **UZEDY® (risperidone)** - Croissance continue
- **Olanzapine LAI** - Soumission NDA en cours
- **GLP-1 formulations** - Optimisation Nanexa

---

## 📈 Performance vs Attentes

### Points Positifs
- ✅ Exécution rapide (18.35s)
- ✅ 15 items finaux de qualité
- ✅ Signaux LAI forts et pertinents
- ✅ Diversité des types d'événements
- ✅ Sociétés pure-player LAI bien représentées

### Points d'Amélioration
- ⚠️ 1 source échouée sur 8 (12.5% échec)
- ⚠️ Sources presse RSS non productives
- ⚠️ Camurus et Peptron absents (sources importantes)

---

## 🔄 Prochaine Étape : Phase 3

**Phase 3 – Run Normalize_Score V2 Réel**

Commande à exécuter :
```bash
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --payload '{"client_id": "lai_weekly_v4"}' \
  --cli-binary-format raw-in-base64-out \
  --region eu-west-3 \
  --profile rag-lai-prod \
  response_normalize_lai_v4.json
```

**Attentes pour Phase 3 :**
- Normalisation des 15 items via Bedrock
- Matching sur domaine unique `tech_lai_ecosystem`
- Scoring et génération fichier curated/
- Analyse des appels Bedrock et coûts

---

**Phase 2 terminée avec succès - 15 items LAI de qualité ingérés**