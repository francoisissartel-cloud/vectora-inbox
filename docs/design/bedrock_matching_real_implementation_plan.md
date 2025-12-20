# Plan d'Implémentation - Solution Matching Bedrock Réel

**Date :** 19 décembre 2025  
**Version :** 1.0  
**Objectif :** Résoudre définitivement le problème de matching 0% en implémentant une vraie architecture Bedrock-Only Pure  
**Client MVP :** lai_weekly_v4  
**Conformité :** 100% vectora-inbox-development-rules.md  

---

## 🎯 RÉSUMÉ EXÉCUTIF

### Problème Identifié
**Cause racine :** Le normalizer.py ligne 109 force un matching vide hardcodé :
```python
bedrock_matching_result = {'matched_domains': [], 'domain_relevance': {}}
```

### Solution Architecturale
**Implémentation d'un matching Bedrock sémantique réel** qui :
- Utilise les prompts canonical existants
- Respecte les seuils configurés dans client_config
- Maintient l'architecture 3 Lambdas V2
- Reste conforme aux règles de développement

### Résultats Attendus
- **Matching rate** : 60-80% (vs 0% actuel)
- **Items premium matchés** : Nanexa-Moderna, UZEDY®, Olanzapine NDA
- **Performance** : +30-60s, +$0.02-0.03 par run

---

## 📋 STRUCTURE DU PLAN - 4 PHASES

### Phase 1 - Implémentation Code (45min)
**Objectif :** Créer le module bedrock_matcher.py et corriger normalizer.py

### Phase 2 - Amélioration Scopes (15min)  
**Objectif :** Ajouter trademarks manquants détectés par Bedrock

### Phase 3 - Déploiement AWS (30min)
**Objectif :** Rebuild layer, upload et mise à jour Lambda

### Phase 4 - Tests et Validation (45min)
**Objectif :** Valider le matching avec lai_weekly_v4 et synthèse

---

## 🔧 PHASE 1 - IMPLÉMENTATION CODE

### 1.1 Création Module Bedrock Matcher

**Fichier :** `src_v2/vectora_core/normalization/bedrock_matcher.py`

**Fonctionnalités :**
- Matching sémantique via Bedrock
- Utilisation prompts canonical
- Application seuils configurés
- Gestion d'erreurs robuste

### 1.2 Correction Normalizer

**Fichier :** `src_v2/vectora_core/normalization/normalizer.py`

**Modifications :**
- Ligne 109 : Remplacement matching vide par appel bedrock_matcher
- Ajout paramètre canonical_prompts
- Gestion conditionnelle (si watch_domains configurés)

### 1.3 Mise à Jour Module Principal

**Fichier :** `src_v2/vectora_core/normalization/__init__.py`

**Modifications :**
- Passage canonical_prompts au normalizer
- Maintien compatibilité existante

### Validation Phase 1
- [ ] Code conforme règles V2 (src_v2/ uniquement)
- [ ] Handlers non modifiés
- [ ] Architecture 3 Lambdas préservée
- [ ] Imports relatifs corrects

---

## 📊 PHASE 2 - AMÉLIORATION SCOPES

### 2.1 Ajout Trademarks Technologiques

**Fichier :** `canonical/scopes/trademark_scopes.yaml`

**Ajouts :**
```yaml
- PharmaShell®
- PharmaShell  
- BEPO®
- BEPO
- SiliaShell®
- SiliaShell
```

### Validation Phase 2
- [ ] Trademarks détectés par Bedrock ajoutés
- [ ] Format YAML respecté
- [ ] Pas de doublons

---

## ⚙️ PHASE 3 - DÉPLOIEMENT AWS

### 3.1 Rebuild Layer Vectora-Core

```bash
# Préparation environnement
cd layer_build
rm -rf vectora_core/
cp -r ../src_v2/vectora_core .

# Création package
zip -r ../vectora-core-matching-bedrock-v18.zip vectora_core/
```

### 3.2 Upload Layer AWS

```bash
aws lambda publish-layer-version \
  --layer-name vectora-inbox-vectora-core-dev \
  --zip-file fileb://vectora-core-matching-bedrock-v18.zip \
  --profile rag-lai-prod \
  --region eu-west-3
```

### 3.3 Mise à Jour Lambda

```bash
aws lambda update-function-configuration \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --layers arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev:18 \
  --profile rag-lai-prod \
  --region eu-west-3
```

### 3.4 Upload Scopes Mis à Jour

```bash
aws s3 cp canonical/scopes/trademark_scopes.yaml \
  s3://vectora-inbox-config-dev/canonical/scopes/trademark_scopes.yaml \
  --profile rag-lai-prod
```

### Validation Phase 3
- [ ] Layer version 18 créée
- [ ] Lambda mise à jour avec nouvelle layer
- [ ] Scopes uploadés sur S3
- [ ] Pas d'erreurs déploiement

---

## 🧪 PHASE 4 - TESTS ET VALIDATION

### 4.1 Test Fonctionnel

```bash
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --payload '{"client_id": "lai_weekly_v4"}' \
  --cli-binary-format raw-in-base64-out \
  --profile rag-lai-prod \
  response_v18.json
```

### 4.2 Métriques de Validation

**Critères de succès :**
- [ ] **StatusCode :** 200 (Lambda s'exécute)
- [ ] **Matching rate :** > 60% (9+ items sur 15)
- [ ] **Domaines matchés :** tech_lai_ecosystem présent
- [ ] **Items premium :** Nanexa-Moderna, UZEDY®, Olanzapine matchés
- [ ] **Temps d'exécution :** < 180s (acceptable)

### 4.3 Analyse Détaillée

**Téléchargement résultats :**
```bash
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v4/2025/12/19/items.json \
  ./analysis/curated_v18.json --profile rag-lai-prod
```

**Vérifications :**
- [ ] Structure matching_results correcte
- [ ] Champs bedrock_matching_used: true
- [ ] Domain_relevance avec scores
- [ ] Matched_domains non vide

### Validation Phase 4
- [ ] Tests passés avec succès
- [ ] Métriques conformes aux attentes
- [ ] Pas de régression fonctionnelle

---

## 📋 CHECKLIST CONFORMITÉ RÈGLES V2

### Architecture Respectée
- [ ] **Code dans src_v2/ uniquement** (pas de modification /src)
- [ ] **Handlers minimalistes** (délégation vectora_core)
- [ ] **Structure modulaire** (bedrock_matcher dans normalization/)
- [ ] **3 Lambdas V2** (architecture préservée)

### Hygiène Code Respectée  
- [ ] **Pas de dépendances tierces** ajoutées
- [ ] **Imports relatifs** corrects
- [ ] **Pas de stubs** ou contournements
- [ ] **Logique métier** dans vectora_core

### Configuration Respectée
- [ ] **Bedrock us-east-1** maintenu
- [ ] **Modèle Sonnet 3** conservé
- [ ] **Variables d'environnement** standard
- [ ] **Profil rag-lai-prod** utilisé

### Déploiement Respecté
- [ ] **Layer vectora-core** mise à jour
- [ ] **Nommage -v2-dev** respecté
- [ ] **Région eu-west-3** principale
- [ ] **Outputs sauvegardés** si nécessaire

---

## 🎯 MÉTRIQUES DE SUCCÈS

### Métriques Techniques
- **Matching rate cible :** > 60%
- **Temps d'exécution max :** < 180s  
- **Coût supplémentaire max :** < $0.05
- **Taux d'erreur :** < 5%

### Métriques Métier
- **Items premium matchés :** ≥ 4 items
- **Domaine tech_lai_ecosystem :** ≥ 8 items
- **Score moyen items matchés :** > 10
- **Entités détectées :** ≥ 30 entités

### Métriques Qualité
- **Pas de régression :** Normalisation 100%
- **Logs propres :** Pas d'erreurs critiques
- **Structure données :** Conforme contrat
- **Compatibilité :** Autres clients non impactés

---

## 🚨 PLAN DE ROLLBACK

### Si Problème Critique
1. **Rollback layer :**
```bash
aws lambda update-function-configuration \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --layers arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev:17 \
  --profile rag-lai-prod
```

2. **Restaurer scopes :**
```bash
git checkout HEAD~1 -- canonical/scopes/trademark_scopes.yaml
aws s3 cp canonical/scopes/trademark_scopes.yaml s3://vectora-inbox-config-dev/canonical/scopes/
```

### Critères de Rollback
- Lambda ne s'exécute pas (StatusCode ≠ 200)
- Erreurs critiques dans logs
- Matching rate < 10% (pire qu'avant)
- Temps d'exécution > 300s

---

## 📊 LIVRABLES ATTENDUS

### Documentation
- [ ] **Plan d'exécution :** Ce document
- [ ] **Rapport d'implémentation :** Résultats de chaque phase
- [ ] **Tests de validation :** Métriques et comparaisons
- [ ] **Synthèse finale :** Recommandations et prochaines étapes

### Code
- [ ] **bedrock_matcher.py :** Module de matching Bedrock
- [ ] **normalizer.py :** Corrections pour matching réel
- [ ] **trademark_scopes.yaml :** Trademarks enrichis

### Déploiement
- [ ] **Layer v18 :** Package vectora-core mis à jour
- [ ] **Lambda mise à jour :** Configuration avec nouvelle layer
- [ ] **Scopes S3 :** Configuration canonical mise à jour

---

## 🎯 CONCLUSION

Cette solution résout définitivement le problème de matching récurrent en :

1. **Implémentant un vrai matching Bedrock** (vs matching vide hardcodé)
2. **Respectant intégralement les règles V2** (architecture, hygiène, déploiement)
3. **Maintenant la compatibilité** (pas de breaking changes)
4. **Optimisant les performances** (appels Bedrock contrôlés)

**Résultat attendu :** Architecture Bedrock-Only Pure fonctionnelle avec matching sémantique intelligent pour lai_weekly_v4 et tous les futurs clients.

---

*Plan d'Implémentation - Solution Matching Bedrock Réel*  
*Conforme vectora-inbox-development-rules.md*  
*Prêt pour exécution immédiate*