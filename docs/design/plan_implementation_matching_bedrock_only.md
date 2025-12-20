# Plan d'Implémentation - Architecture Matching Bedrock-Only

**Date :** 19 décembre 2025  
**Objectif :** Résoudre le problème de matching en simplifiant vers une architecture Bedrock-only  
**Référence :** lai_weekly_v3_phase6_architecture_matching_bedrock_report.md  
**Architecture :** 3 Lambdas V2 (vectora-inbox-development-rules.md)

---

## 🎯 RÉSUMÉ EXÉCUTIF

**Problème identifié :** Architecture de matching hybride complexe et défaillante
- Bedrock matching : Fonctionne partiellement (1 domaine matché)
- Matching déterministe : Défaillant systématiquement (0 domaine)
- Logique combinée : Écrase les résultats Bedrock

**Solution :** Architecture Bedrock-only simplifiée
- Supprimer le matching déterministe
- Optimiser le matching Bedrock existant
- Simplifier la configuration

**Impact attendu :** Taux de matching 60-80% (vs 0% actuellement)

---

## 📋 CADRAGE DU PROJET

### Périmètre

**Inclus :**
- Modification de la logique de matching dans `src_v2/vectora_core/normalization/`
- Optimisation des seuils et configuration Bedrock
- Tests avec données réelles lai_weekly_v3
- Déploiement sur Lambda normalize-score-v2

**Exclus :**
- Modification de l'architecture 3 Lambdas V2 (stable)
- Changement des modèles Bedrock (Sonnet 3 validé)
- Refonte complète des prompts (optimisation uniquement)

### Contraintes Techniques

**Obligatoires (vectora-inbox-development-rules.md) :**
- Architecture 3 Lambdas V2 : `src_v2/lambdas/`
- Code dans `src_v2/vectora_core/`
- Configuration Bedrock : us-east-1, Sonnet 3
- Client de référence : lai_weekly_v3
- Environnement : eu-west-3, profil rag-lai-prod

### Métriques de Succès

**Avant (état actuel) :**
- Taux de matching : 0%
- Items matchés : 0/15
- Domaines matchés : 0

**Après (objectif) :**
- Taux de matching : ≥ 60%
- Items matchés : ≥ 9/15
- Domaines matchés : tech_lai_ecosystem + regulatory_lai

---

## 🏗️ PHASE 1 : ANALYSE ET PRÉPARATION

### 1.1 Audit Code Existant

**Fichiers à analyser :**
```
src_v2/vectora_core/normalization/
├── __init__.py                 # Point d'entrée run_normalize_score_for_client()
├── normalizer.py              # Appels Bedrock normalisation
├── matcher.py                 # Matching déterministe (À DÉSACTIVER)
└── bedrock_client.py          # Client Bedrock spécialisé
```

**Actions :**
- [ ] Identifier la logique de combinaison Bedrock + déterministe
- [ ] Localiser les seuils de configuration
- [ ] Analyser les logs de matching Bedrock réussi
- [ ] Documenter le flux actuel

### 1.2 Analyse Configuration Client

**Fichier :** `s3://vectora-inbox-config-dev/clients/lai_weekly_v3.yaml`

**Sections à examiner :**
```yaml
matching_config:
  min_domain_score: 0.25
  domain_type_thresholds:
    technology: 0.30
    regulatory: 0.20
  enable_fallback_mode: true
  fallback_min_score: 0.15
```

**Actions :**
- [ ] Sauvegarder configuration actuelle
- [ ] Identifier les seuils optimaux pour Bedrock-only
- [ ] Préparer nouvelle configuration simplifiée

### 1.3 Préparation Environnement de Test

**Données de référence :**
- Items LAI réels : 15 items avec scores élevés
- Résultats attendus : Nanexa/Moderna, MedinCell/Teva
- Logs de référence : Bedrock matching partiel réussi

**Actions :**
- [ ] Sauvegarder données de test actuelles
- [ ] Préparer script de validation automatisée
- [ ] Configurer monitoring des métriques

---

## 🔧 PHASE 2 : MODIFICATIONS CORE

### 2.1 Modification Logique de Matching

**Fichier principal :** `src_v2/vectora_core/normalization/__init__.py`

**Modification minimale (5 lignes) :**
```python
# Ligne ~85, après normalisation Bedrock
if client_config.get('matching_config', {}).get('bedrock_only', False):
    # Mode Bedrock-only : utiliser directement les résultats Bedrock
    matched_items = normalized_items
    logger.info("Mode Bedrock-only activé : matching déterministe ignoré")
else:
    # Mode hybride existant (fallback)
    matched_items = matcher.match_items_to_domains(...)
```

**Actions :**
- [ ] Identifier la ligne exacte de combinaison
- [ ] Implémenter le flag `bedrock_only`
- [ ] Ajouter logging approprié
- [ ] Préserver le mode hybride en fallback

### 2.2 Optimisation Configuration Bedrock

**Fichier :** `s3://vectora-inbox-config-dev/clients/lai_weekly_v3.yaml`

**Nouvelle configuration simplifiée :**
```yaml
matching_config:
  # NOUVEAU: Mode Bedrock-only
  bedrock_only: true
  
  # Configuration simplifiée
  min_relevance_score: 0.20        # Seuil unique
  max_domains_per_item: 2          # Limite raisonnable
  
  # Seuils par type (optionnel)
  domain_type_thresholds:
    technology: 0.25               # Légèrement plus strict
    regulatory: 0.15               # Plus permissif
  
  # Mode fallback conservé
  enable_fallback_mode: true
  fallback_min_score: 0.10         # Très permissif pour pure players
  
  # Diagnostic
  enable_diagnostic_mode: true
```

**Actions :**
- [ ] Créer nouvelle version de configuration
- [ ] Tester avec différents seuils
- [ ] Valider avec items de référence
- [ ] Documenter les changements

### 2.3 Optimisation Prompts Bedrock

**Fichier :** `s3://vectora-inbox-config-dev/canonical/prompts/global_prompts.yaml`

**Améliorations ciblées :**
- Clarifier les critères de matching pour LAI
- Améliorer la reconnaissance des pure players
- Optimiser la détection des technologies LAI

**Actions :**
- [ ] Analyser les prompts actuels
- [ ] Identifier les améliorations spécifiques
- [ ] Tester les modifications sur items de référence
- [ ] Valider la cohérence des résultats

---

## 🚀 PHASE 3 : IMPLÉMENTATION

### 3.1 Développement Local

**Environnement :**
```bash
cd src_v2/
python -m pytest tests/unit/test_bedrock_matcher.py
python -m pytest tests/integration/test_bedrock_matching_integration.py
```

**Actions :**
- [ ] Implémenter les modifications dans `src_v2/`
- [ ] Exécuter tests unitaires
- [ ] Valider avec données de test
- [ ] Corriger les régressions éventuelles

### 3.2 Tests d'Intégration

**Script de test :**
```bash
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v3
```

**Validation :**
- [ ] Vérifier activation du mode Bedrock-only
- [ ] Contrôler les logs de matching
- [ ] Mesurer le taux de matching
- [ ] Analyser la distribution par domaine

### 3.3 Construction des Layers

**Layer vectora-core mise à jour :**
```bash
cd src_v2/
zip -r ../vectora-core-bedrock-only.zip vectora_core/
```

**Actions :**
- [ ] Construire le nouveau layer vectora-core
- [ ] Valider la taille (< 50MB)
- [ ] Tester l'import local
- [ ] Préparer pour déploiement

---

## ☁️ PHASE 4 : DÉPLOIEMENT AWS

### 4.1 Mise à Jour Configuration

**Upload configuration client :**
```bash
aws s3 cp lai_weekly_v3_bedrock_only.yaml \
  s3://vectora-inbox-config-dev/clients/lai_weekly_v3.yaml \
  --region eu-west-3 \
  --profile rag-lai-prod
```

**Actions :**
- [ ] Sauvegarder configuration actuelle
- [ ] Uploader nouvelle configuration
- [ ] Valider la syntaxe YAML
- [ ] Tester le chargement

### 4.2 Déploiement Layer

**Mise à jour layer vectora-core :**
```bash
aws lambda publish-layer-version \
  --layer-name vectora-inbox-vectora-core-dev \
  --zip-file fileb://vectora-core-bedrock-only.zip \
  --compatible-runtimes python3.9 \
  --region eu-west-3 \
  --profile rag-lai-prod
```

**Actions :**
- [ ] Publier nouvelle version du layer
- [ ] Noter le numéro de version
- [ ] Mettre à jour la Lambda normalize-score-v2
- [ ] Valider le déploiement

### 4.3 Mise à Jour Lambda

**Update function configuration :**
```bash
aws lambda update-function-configuration \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --layers arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev:NEW_VERSION \
  --region eu-west-3 \
  --profile rag-lai-prod
```

**Actions :**
- [ ] Mettre à jour la configuration Lambda
- [ ] Vérifier les variables d'environnement
- [ ] Tester l'invocation
- [ ] Monitorer les logs CloudWatch

---

## 🧪 PHASE 5 : TESTS DONNÉES RÉELLES

### 5.1 Test de Validation E2E

**Commande de test :**
```bash
python scripts/invoke/invoke_normalize_score_v2.py \
  --client-id lai_weekly_v3 \
  --date 2025-12-19
```

**Métriques à mesurer :**
- Nombre d'items traités
- Taux de matching global
- Distribution par domaine
- Temps d'exécution
- Coût Bedrock

### 5.2 Analyse des Résultats

**Items de référence à valider :**

**Item 1 - Nanexa/Moderna (Score 14.9) :**
```json
{
  "title": "Nanexa and Moderna enter into license and option agreement for PharmaShell®-based products",
  "expected_domains": ["tech_lai_ecosystem"],
  "expected_match": true
}
```

**Item 2 - MedinCell/Teva (Score 13.8) :**
```json
{
  "title": "Teva Pharmaceuticals Announces NDA Submission for Olanzapine Extended-Release Injectable",
  "expected_domains": ["tech_lai_ecosystem", "regulatory_lai"],
  "expected_match": true
}
```

**Actions :**
- [ ] Vérifier le matching des items de référence
- [ ] Analyser les scores de confiance
- [ ] Valider la cohérence des domaines
- [ ] Documenter les améliorations

### 5.3 Tests de Régression

**Validation non-régression :**
- [ ] Items non-LAI restent non-matchés
- [ ] Seuils de qualité préservés
- [ ] Performance globale maintenue
- [ ] Coûts Bedrock contrôlés

---

## 📊 PHASE 6 : RETOUR SYNTHÈSE AVEC MÉTRIQUES

### 6.1 Métriques de Performance

**Avant/Après Comparaison :**

| Métrique | Avant | Après | Amélioration |
|----------|-------|-------|--------------|
| Taux de matching | 0% | ≥60% | +60pp |
| Items matchés | 0/15 | ≥9/15 | +9 items |
| Domaines tech_lai | 0 | ≥5 | +5 items |
| Domaines regulatory | 0 | ≥4 | +4 items |
| Temps d'exécution | 163s | ~120s | -26% |
| Complexité code | Hybride | Simple | -50% |

### 6.2 Métriques de Qualité

**Validation qualitative :**
- [ ] Pure players LAI correctement identifiés
- [ ] Technologies LAI reconnues
- [ ] Événements réglementaires matchés
- [ ] Faux positifs minimisés

### 6.3 Métriques Opérationnelles

**Impact système :**
- [ ] Réduction des points de défaillance
- [ ] Simplification de la maintenance
- [ ] Amélioration du debugging
- [ ] Réduction des coûts de développement

### 6.4 Rapport Final

**Document de synthèse :**
```
docs/diagnostics/matching_bedrock_only_implementation_report.md
```

**Contenu :**
- Résumé des modifications apportées
- Métriques avant/après détaillées
- Analyse des items de référence
- Recommandations pour l'évolution
- Plan de monitoring continu

---

## 🔄 WORKFLOW VECTORA-INBOX RESPECTÉ

### Conformité Architecture V2

**✅ Respect des règles obligatoires :**
- Architecture 3 Lambdas V2 préservée
- Code dans `src_v2/vectora_core/`
- Handlers délèguent à vectora_core
- Configuration Bedrock validée (us-east-1, Sonnet 3)
- Client de référence lai_weekly_v3

### Conformité Déploiement

**✅ Ordre des stacks respecté :**
- S0-core : Buckets S3 (inchangé)
- S0-iam : Rôles IAM (inchangé)
- S1-runtime : Lambdas (mise à jour layer uniquement)

### Conformité Tests

**✅ Validation E2E :**
- Tests unitaires : `test_bedrock_matcher.py`
- Tests d'intégration : `test_bedrock_matching_integration.py`
- Client de référence : lai_weekly_v3
- Métriques de validation définies

---

## 📅 PLANNING D'EXÉCUTION

### Timeline Recommandée

**Jour 1 : Phases 1-2 (Analyse + Modifications)**
- Audit code existant (2h)
- Modifications core (3h)
- Tests locaux (2h)

**Jour 2 : Phase 3 (Implémentation)**
- Développement local (3h)
- Tests d'intégration (2h)
- Construction layers (1h)

**Jour 3 : Phases 4-5 (Déploiement + Tests)**
- Déploiement AWS (2h)
- Tests données réelles (3h)
- Analyse résultats (2h)

**Jour 4 : Phase 6 (Synthèse)**
- Métriques finales (2h)
- Rapport de synthèse (2h)
- Documentation (1h)

### Critères de Validation par Phase

**Phase 1 :** Code analysé, configuration préparée
**Phase 2 :** Modifications implémentées, tests locaux OK
**Phase 3 :** Tests d'intégration passés, layers construits
**Phase 4 :** Déploiement réussi, Lambda fonctionnelle
**Phase 5 :** Taux de matching ≥60%, items de référence matchés
**Phase 6 :** Rapport complet, métriques documentées

---

## 🎯 OBJECTIF FINAL

**Résultat attendu :** Architecture de matching simplifiée et performante
- **Technique :** Bedrock-only, configuration simplifiée
- **Fonctionnel :** Taux de matching 60-80%
- **Opérationnel :** Maintenance réduite, debugging simplifié
- **Évolutif :** Base solide pour améliorations futures

**Validation finale :** Items LAI de référence correctement matchés avec l'architecture 3 Lambdas V2 préservée et les règles vectora-inbox respectées.

---

*Plan d'Implémentation - Architecture Matching Bedrock-Only*  
*Date : 19 décembre 2025*  
*Statut : 📋 PRÊT POUR EXÉCUTION AUTONOME*