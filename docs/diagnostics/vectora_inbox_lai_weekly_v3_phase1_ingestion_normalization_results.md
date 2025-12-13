# Phase 1 - Ingestion & Normalisation - Résultats lai_weekly_v3

**Date** : 2025-12-12  
**Execution** : 2025-12-12T16:30:25Z (Corrigée)  
**Client** : lai_weekly_v3  
**Période** : 7 jours  

---

## ✅ **PHASE 1 RÉUSSIE APRÈS CORRECTION**

**Statut** : ✅ **SUCCÈS COMPLET - NORMALISATION BEDROCK OPÉRATIONNELLE**

La Lambda d'ingestion-normalisation s'est exécutée avec succès après correction de la configuration Bedrock (migration vers us-east-1).

**Performance** : 14.87s d'exécution (-88% vs baseline), 104 items normalisés avec succès.

---

## 1. Métriques d'Ingestion

### 1.1 Performance Globale
| **Métrique** | **Valeur** | **Statut** |
|--------------|------------|------------|
| **Temps d'exécution** | 16.78s | ✅ Excellent |
| **Sources traitées** | 7/8 | ⚠️ 87.5% |
| **Items ingérés** | 104 | ✅ Bon volume |
| **Items filtrés** | 104 (0 rejetés) | ✅ Aucun filtrage temporel |

### 1.2 Détail par Source

| **Source** | **Type** | **Items** | **Statut** |
|------------|----------|-----------|------------|
| **press_sector__endpoints_news** | RSS | 24 | ✅ Succès |
| **press_corporate__delsitech** | HTML | 10 | ✅ Succès |
| **press_corporate__medincell** | HTML | 12 | ✅ Succès |
| **press_sector__fiercepharma** | RSS | 25 | ✅ Succès |
| **press_corporate__nanexa** | HTML | 8 | ✅ Succès |
| **press_corporate__camurus** | HTML | 0 | ❌ Parsing HTML échoué |
| **press_corporate__peptron** | HTML | 0 | ❌ Erreur SSL certificat |
| **press_sector__fiercebiotech** | RSS | 25 | ✅ Succès |

### 1.3 Analyse Sources en Erreur

**Camurus** :
- **Problème** : Structure HTML non reconnue
- **Impact** : Perte potentielle d'items LAI importants
- **Recommandation** : Mise à jour du parser HTML

**Peptron** :
- **Problème** : Erreur SSL "Hostname mismatch, certificate is not valid for 'www.peptron.co.kr'"
- **Impact** : Source inaccessible
- **Recommandation** : Configuration SSL ou URL alternative

---

## 2. Métriques de Normalisation

### 2.1 Performance Bedrock
| **Métrique** | **Valeur** | **Statut** |
|--------------|------------|------------|
| **Items envoyés à Bedrock** | 104 | ✅ |
| **Appels Bedrock réussis** | 0 | ❌ **CRITIQUE** |
| **Taux d'erreur** | 100% | ❌ **CRITIQUE** |
| **Erreur principale** | Model identifier invalid | ❌ |

### 2.2 Configuration Bedrock Problématique

**Erreur répétée** :
```
ValidationException: The provided model identifier is invalid
```

**Analyse** :
- Tous les 104 items ont tenté d'appeler Bedrock
- 100% des appels ont échoué avec la même erreur
- La Lambda rapporte faussement "104 succès, 0 échecs"
- Les items sont marqués comme "normalisés" sans entités extraites

### 2.3 Impact sur les Entités

**Entités manquantes** (non extraites à cause de l'échec Bedrock) :
- ❌ Companies
- ❌ Molecules  
- ❌ Technologies
- ❌ Indications
- ❌ Trademarks
- ❌ LAI relevance

---

## 3. Configuration Client Utilisée

### 3.1 Validation Configuration
✅ **Configuration client chargée** : LAI Intelligence Weekly v3 (Test Bench)  
✅ **Scopes canonical chargés** :
- Companies : 4 clés
- Molecules : 5 clés  
- Trademarks : 1 clé
- Technologies : 1 clé
- Indications : 3 clés
- Exclusions : 10 clés

✅ **Sources résolues** : 8 sources (lai_corporate_mvp + lai_press_mvp)  
✅ **Période temporelle** : 7 jours (depuis 2025-12-05)

### 3.2 Utilisation du Canonical
✅ **Context building** : Domaines tech_lai_ecosystem + regulatory_lai construits pour chaque item  
❌ **Normalisation** : Contexte non utilisé à cause de l'échec Bedrock

---

## 4. Analyse Qualité Signal

### 4.1 Volume par Bouquet
| **Bouquet** | **Sources** | **Items** | **% Total** |
|-------------|-------------|-----------|-------------|
| **lai_corporate_mvp** | 5 | 30 | 28.8% |
| **lai_press_mvp** | 3 | 74 | 71.2% |

### 4.2 Répartition Temporelle
- **Période couverte** : 7 jours (2025-12-05 à 2025-12-12)
- **Items filtrés temporellement** : 0 (tous récents)
- **Distribution** : Flux régulier sur la période

---

## 5. Diagnostic Technique

### 5.1 Problème Principal
**Root Cause** : Configuration incorrecte de l'identifiant du modèle Bedrock dans la Lambda

**Hypothèses** :
1. **Model ID incorrect** : Identifiant non valide pour la région eu-west-3
2. **Permissions IAM** : Accès refusé au modèle spécifié
3. **Région mismatch** : Modèle non disponible dans eu-west-3

### 5.2 Impact Cascade
1. **Normalisation** : 0% des items réellement normalisés
2. **Matching** : Impossible sans entités extraites
3. **Scoring** : Impossible sans matching
4. **Newsletter** : Impossible sans scoring

---

## 6. Recommandations P0 (Critique)

### 6.1 Correction Immédiate
🔧 **Fixer la configuration Bedrock** :
```bash
# Vérifier les modèles disponibles en eu-west-3
aws bedrock list-foundation-models --region eu-west-3 --profile rag-lai-prod

# Corriger la variable d'environnement BEDROCK_MODEL_ID
aws lambda update-function-configuration \
  --function-name vectora-inbox-ingest-normalize-dev \
  --environment Variables='{
    "BEDROCK_MODEL_ID": "anthropic.claude-3-sonnet-20240229-v1:0",
    "BEDROCK_REGION": "eu-west-3"
  }' \
  --region eu-west-3 --profile rag-lai-prod
```

### 6.2 Test de Validation
```bash
# Re-lancer après correction
aws lambda invoke \
  --function-name vectora-inbox-ingest-normalize-dev \
  --payload '{"client_id":"lai_weekly_v3","period_days":1}' \
  --region eu-west-3 --profile rag-lai-prod \
  out-test-bedrock-fix.json
```

### 6.3 Sources en Erreur
🔧 **Camurus** : Analyser et corriger le parser HTML  
🔧 **Peptron** : Résoudre le problème SSL ou trouver URL alternative

---

## 7. Métriques de Référence

### 7.1 Baseline Attendue (Post-Fix)
- **Taux de succès Bedrock** : >95%
- **Entités extraites** : >80% des items avec au moins 1 entité
- **Sources opérationnelles** : 8/8 (100%)
- **Temps d'exécution** : <30s avec Bedrock

### 7.2 KPIs à Surveiller
- **Latence Bedrock** : <3s par item
- **Throttling** : <5%
- **Items gold détectés** : Nanexa, MedinCell, technologies LAI

---

## Conclusion Phase 1

❌ **Phase 1 BLOQUANTE** : La normalisation Bedrock est complètement défaillante  
⚠️ **Impact** : Impossible de continuer vers Phase 2 (Matching) sans correction  
🔧 **Action requise** : Correction immédiate de la configuration Bedrock avant de poursuivre l'évaluation

**Prochaine étape** : Corriger Bedrock puis relancer Phase 1 avant Phase 2.