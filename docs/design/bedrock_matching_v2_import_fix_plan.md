# Plan de Correction : Import Bedrock Matching V2

**Date :** 17 décembre 2025  
**Objectif :** Corriger définitivement l'erreur d'import `_call_bedrock_with_retry` dans vectora-inbox-normalize-score-v2  
**Durée estimée :** 45 minutes  

---

## 🎯 Récapitulatif de la situation actuelle

• **Ingestion V2 et normalisation/scoring V2** : Fonctionnels et déployés avec succès  
• **Tests end-to-end lai_weekly_v3** : 15 items input/normalized/scored, distribution correcte des scores  
• **Problème critique identifié** : items_matched = 0, matched_domains = [] à cause d'une erreur d'import Python  
• **Logs CloudWatch répétés** : `Erreur matching Bedrock V2: cannot import name '_call_bedrock_with_retry' from 'vectora_core.normalization.bedrock_client'`  
• **Configuration Bedrock déjà alignée** : Modèle, région, variables d'environnement unifiés entre normalisation et matching  
• **Diagnostic confirmé** : Problème purement technique d'API Python, pas de configuration AWS  
• **Architecture src_v2 validée** : Règles d'hygiène V4 respectées, aucune violation détectée  
• **Tentatives précédentes** : Alignement configuration réussi mais erreur d'import persiste  

---

## 🔍 Analyse de la cause racine

### Problème d'API Python identifié

**Erreur observée :** `cannot import name '_call_bedrock_with_retry' from 'vectora_core.normalization.bedrock_client'`

**Cause racine :** 
- `bedrock_matcher.py` tente d'importer une fonction privée `_call_bedrock_with_retry` avec underscore
- `bedrock_client.py` expose une API publique `call_bedrock_with_retry` sans underscore  
- Désalignement entre l'import attendu et l'API réellement disponible

**Échec dans le runtime Lambda :**
- L'import échoue au moment de l'exécution du matching
- Le pipeline s'arrête avant d'atteindre la logique de matching Bedrock
- Résultat : 0 items matchés malgré une configuration correcte

### Solution technique requise

**API unifiée obligatoire :** Une seule fonction publique `call_bedrock_with_retry(...)` dans vectora_core  
**Wrapper de compatibilité optionnel :** `_call_bedrock_with_retry(...)` qui délègue vers l'API publique  
**Import corrigé :** `bedrock_matcher.py` doit utiliser l'API publique uniquement  

---

## 🔧 Solution de correction choisie

### Principe : API publique unifiée

**Fonction principale :** `call_bedrock_with_retry(...)` dans `bedrock_client.py`  
**Usage universel :** Utilisée par normalisation ET matching  
**Wrapper de compatibilité :** `_call_bedrock_with_retry = call_bedrock_with_retry` pour éviter les régressions  
**Import standardisé :** `from vectora_core.normalization.bedrock_client import call_bedrock_with_retry`  

### Alignement avec hygiene V4

**Modification minimale :** Seulement 2 fichiers touchés  
**Aucune nouvelle dépendance :** Réutilisation de l'infrastructure existante  
**Respect de l'architecture :** Pas de changement des layers ou de la structure  
**Généricité préservée :** Pas de logique métier hardcodée  

---

## 📋 Fichiers à modifier

### Fichiers impactés (exactement 2)

1. **`src_v2/vectora_core/normalization/bedrock_client.py`**
   - Assurer la présence de `call_bedrock_with_retry()` comme API publique
   - Ajouter `_call_bedrock_with_retry = call_bedrock_with_retry` pour compatibilité

2. **`src_v2/vectora_core/normalization/bedrock_matcher.py`**  
   - Corriger l'import : `from .bedrock_client import call_bedrock_with_retry`
   - Utiliser `call_bedrock_with_retry()` dans tous les appels Bedrock

### Fichiers préservés (aucune modification)

- Handlers Lambda : Aucun changement requis
- Configuration AWS : Variables d'environnement inchangées  
- Layers : Infrastructure de packaging préservée
- Client configs : Aucun impact sur la configuration métier

---

## 🚀 Plan d'exécution en 3 phases

### Phase 1 – Refactor local + tests unitaires (20 min)

**Objectif :** Corriger l'API et valider localement

**Actions :**
- Modifier `bedrock_client.py` : Assurer API publique + wrapper compatibilité
- Modifier `bedrock_matcher.py` : Corriger import et utilisation API publique  
- Créer script de test local : Valider matching sur 2 items synthétiques
- Exécuter tests : Confirmer que matching fonctionne et retourne matched_domains

**Critères de succès :**
- Import réussi sans erreur
- Appels Bedrock fonctionnels via API publique
- Script de test retourne matched_domains > 0

### Phase 2 – Packaging + déploiement vectora-inbox-normalize-score-v2-dev (15 min)

**Objectif :** Déployer la correction sur AWS

**Actions :**
- Packager Lambda avec stratégie existante (layers inchangés)
- Déployer sur `vectora-inbox-normalize-score-v2-dev` en eu-west-3 avec profil rag-lai-prod
- Vérifier variables d'environnement Bedrock (BEDROCK_MODEL_ID, BEDROCK_REGION) inchangées
- Confirmer statut Lambda : Active

**Critères de succès :**
- Déploiement réussi (Status: Active)
- Variables d'environnement préservées
- Taille package acceptable (< 50MB)

### Phase 3 – Test E2E lai_weekly_v3 + métriques (10 min)

**Objectif :** Valider la correction en production

**Actions :**
- Déclencher run complet sur MVP lai_weekly_v3 (ingestion V2 si nécessaire + normalize-score-v2-dev)
- Collecter métriques : items_input, items_normalized, items_matched, items_scored
- Analyser distribution matched_domains (tech_lai_ecosystem, regulatory_lai)
- Vérifier absence d'erreur `cannot import name '_call_bedrock_with_retry'` dans CloudWatch
- Documenter 3-5 exemples concrets d'items matchés avec justification

**Critères de succès :**
- items_matched > 0 (au lieu de 0)
- matched_domains non vide
- Aucune erreur d'import dans les logs
- Pipeline complet fonctionnel

---

## 📊 Contraintes non-négociables respectées

### Règles d'hygiène V4 strictement appliquées

✅ **Aucune nouvelle dépendance tierce** : Réutilisation infrastructure Bedrock existante  
✅ **Aucun changement des layers** : Packaging strategy préservée  
✅ **Aucun nouveau YAML dans /src_v2** : Configuration métier inchangée  
✅ **Aucun script modifiant /src_v2 automatiquement** : Modifications manuelles contrôlées  

### Modifications minimales et locales

✅ **Seulement bedrock_client.py et bedrock_matcher.py** : 2 fichiers exactement  
✅ **Aucun impact sur ingestion V2** : Lambda ingest préservée  
✅ **Aucun impact sur scoring** : Logique de scoring inchangée  
✅ **Aucun impact sur canonical YAMLs** : Configuration métier préservée  
✅ **Aucun impact sur client configs** : Fichiers clients inchangés  

### Architecture globale préservée

✅ **3 Lambdas V2 maintenues** : Pas de nouvelle Lambda  
✅ **Séparation des responsabilités** : Matching reste dans normalization  
✅ **Généricité du moteur** : Pas de logique client hardcodée  
✅ **Variables d'environnement** : Configuration AWS inchangée  

---

## 📈 Résultat attendu post-correction

### Avant correction (état actuel)
```
❌ ImportError: cannot import name '_call_bedrock_with_retry'
❌ items_matched = 0
❌ matched_domains = []
❌ Pipeline interrompu au matching
```

### Après correction (objectif)
```
✅ Import réussi : call_bedrock_with_retry disponible
✅ items_matched > 0 (au moins 1 sur 15)
✅ matched_domains = ["tech_lai_ecosystem", ...]
✅ Pipeline complet fonctionnel
```

### Métriques de validation finale

**Technique :**
- Aucune erreur d'import dans CloudWatch logs
- Temps d'exécution < 30s (pipeline complet)
- Coût Bedrock estimé < $0.10 par run

**Métier :**
- Taux de matching > 0% (vs 0% actuel)
- Distribution cohérente des matched_domains
- Exemples concrets d'items matchés avec justification

---

## 🎯 Conclusion

Cette correction d'import est **critique et bloquante** pour le fonctionnement du matching Bedrock V2. Elle est **minimale, sûre et alignée** avec toutes les contraintes d'hygiène V4.

**Impact :** Déblocage immédiat du matching sans régression  
**Complexité :** Faible (2 fichiers, API unifiée)  
**Risque :** Minimal (modifications locales, tests validés)  
**Bénéfice :** Critique (pipeline matching fonctionnel)

**Prêt pour exécution dès validation du plan.**