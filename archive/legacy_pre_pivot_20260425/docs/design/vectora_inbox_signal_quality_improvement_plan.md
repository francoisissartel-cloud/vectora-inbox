# Plan d'Amélioration Qualité Signal - Vectora Inbox

**Date** : 2025-12-12  
**Objectif** : Corriger la sélection des news LAI et éliminer le bruit HR/Finance  
**Basé sur** : Diagnostic feedback humain et analyse newsletter actuelle  

---

## 🎯 Problèmes à Résoudre

### Problème 1 : News LAI-Strong Manquées
- **Nanexa/Moderna** : PharmaShell® non détecté (encoding ®)
- **UZEDY regulatory** : Trademark non reconnu
- **MedinCell malaria** : Contexte LAI implicite non valorisé

### Problème 2 : Bruit HR/Finance Dominant
- **Pure player bonus trop élevé** : 1.5 permet au bruit de passer
- **Seuil trop bas** : min_score=5 insuffisant
- **Exclusions inefficaces** : Contournées par les bonus

### Problème 3 : Feedback Humain Non Intégré
- **Taux d'intégration** : 20% seulement
- **Configurations canonical** : Non mises à jour avec retours humains

---

## 📋 Plan par Phases

### Phase 1 - Corrections Canonical (P0)
**Durée** : 2h  
**Objectif** : Corriger les configurations de base pour améliorer la détection

#### 1.1 Correction Technology Scopes
**Fichier** : `canonical/scopes/technology_scopes.yaml`

**Actions** :
```yaml
# Ajout variantes PharmaShell pour résoudre problème encoding
technology_terms_high_precision:
  - "PharmaShell®"          # Version avec ®
  - "PharmaShell"           # Version sans ® (fallback)
  - "Pharmashell"           # Variante minuscule
  - "pharma shell"          # Variante séparée
```

#### 1.2 Correction Event Type Patterns
**Fichier** : `canonical/patterns/event_type_patterns.yaml`

**Actions** :
```yaml
# Ajout pattern partenariat pour détecter accords de licence
event_types:
  partnership:
    title_keywords:
      - "license and option agreement"
      - "licensing agreement"
      - "partnership agreement"
      - "collaboration agreement"
      - "strategic partnership"
```

#### 1.3 Amélioration Trademark Scopes
**Fichier** : `canonical/scopes/trademark_scopes.yaml`

**Actions** :
```yaml
# Ajout variantes UZEDY pour améliorer détection
lai_trademarks_global:
  - "Uzedy"
  - "UZEDY"
  - "UZEDY®"
```

#### 1.4 Correction Scoring Rules
**Fichier** : `canonical/scoring/scoring_rules.yaml`

**Actions** :
```yaml
# Réduction pure player bonus
other_factors:
  pure_player_bonus: 1.0     # Réduit de 1.5 à 1.0

# Augmentation seuil sélection
selection_thresholds:
  min_score: 8               # Augmenté de 5 à 8

# Nouveaux bonus contextuels
contextual_bonuses:
  partnership_announcement: 5.0    # Nanexa/Moderna type
  regulatory_milestone: 5.0        # UZEDY approval type
  grant_innovation: 3.0            # MedinCell malaria type
  trademark_mention: 6.0           # UZEDY dans titre

# Nouvelles pénalités contextuelles
contextual_penalties:
  hr_recruitment: -6.0             # "hiring", "seeks"
  financial_reporting: -6.0        # "financial results", "interim report"
  corporate_appointments: -6.0     # "appoints", "chief officer"
  conference_participation: -6.0   # "present at", "participate in"
```

#### 1.5 Renforcement Exclusions
**Fichier** : `canonical/scopes/exclusion_scopes.yaml`

**Actions** :
```yaml
# Termes HR plus précis
hr_recruitment_terms:
  - "hiring"
  - "seeks.*engineer"
  - "seeks.*director"
  - "seeks.*experienced"
  - "job opening"
  - "career opportunity"

# Termes finance plus précis
financial_reporting_terms:
  - "publishes.*financial results"
  - "consolidated.*results"
  - "interim report.*january"
  - "half-year.*results"
  - "quarterly.*results"

# Nouveaux termes corporate
corporate_noise_terms:
  - "appoints.*chief"
  - "management to present"
  - "participate in.*conference"
  - "healthcare conference"
  - "investor.*conference"
```

### Phase 2 - Tests Locaux (P0)
**Durée** : 1h  
**Objectif** : Valider les corrections avant déploiement AWS

#### 2.1 Test Script de Validation
**Fichier** : `test_signal_quality_improvements.py`

**Actions** :
```python
def test_nanexa_moderna_detection():
    # Test détection PharmaShell dans titre Nanexa/Moderna
    
def test_uzedy_trademark_detection():
    # Test détection UZEDY dans news regulatory
    
def test_hr_finance_exclusion():
    # Test exclusion bruit HR/Finance MedinCell/DelSiTech
    
def test_scoring_improvements():
    # Test nouveaux seuils et bonus contextuels
```

#### 2.2 Test avec Items Normalisés Existants
**Source** : `items-normalized-latest.json`

**Validation** :
- Nanexa/Moderna doit être sélectionné (score >8)
- Grace Kim doit être exclu (pénalité corporate)
- Résultats financiers doivent être exclus (pénalité finance)
- Conférences doivent être exclues (pénalité corporate)

#### 2.3 Critères de Succès Tests Locaux
- ✅ Nanexa/Moderna détecté avec score >10
- ✅ Bruit HR/Finance score <5 (sous seuil)
- ✅ Newsletter simulée : 80%+ signal LAI authentique
- ✅ Pas de régression sur items LAI-strong existants

### Phase 3 - Déploiement AWS (P0)
**Durée** : 30min  
**Objectif** : Déployer les corrections validées

#### 3.1 Synchronisation Configurations
**Actions** :
```bash
# Upload configurations corrigées
aws s3 cp canonical/scopes/technology_scopes.yaml s3://vectora-inbox-config-dev/canonical/scopes/
aws s3 cp canonical/patterns/event_type_patterns.yaml s3://vectora-inbox-config-dev/canonical/patterns/
aws s3 cp canonical/scopes/trademark_scopes.yaml s3://vectora-inbox-config-dev/canonical/scopes/
aws s3 cp canonical/scoring/scoring_rules.yaml s3://vectora-inbox-config-dev/canonical/scoring/
aws s3 cp canonical/scopes/exclusion_scopes.yaml s3://vectora-inbox-config-dev/canonical/scopes/
```

#### 3.2 Test End-to-End AWS
**Actions** :
```bash
# Test ingestion avec nouvelles configs
aws lambda invoke --function-name vectora-inbox-ingest-normalize-dev \
  --payload '{"client_id":"lai_weekly_v3","period_days":1}' \
  --cli-binary-format raw-in-base64-out out-test-ingest.json

# Test engine avec nouvelles configs  
aws lambda invoke --function-name vectora-inbox-engine-dev \
  --payload '{"client_id":"lai_weekly_v3","period_days":1}' \
  --cli-binary-format raw-in-base64-out out-test-engine.json
```

#### 3.3 Validation Newsletter Améliorée
**Critères** :
- Nanexa/Moderna présent dans newsletter
- Bruit HR/Finance absent
- 4-5 items LAI authentiques sélectionnés
- Pas de régression qualité

### Phase 4 - Validation et Monitoring (P1)
**Durée** : 1h  
**Objectif** : Confirmer l'amélioration et monitorer la stabilité

#### 4.1 Comparaison Avant/Après
**Métriques** :
- Taux détection signaux LAI-strong : avant 25% → cible 80%+
- Taux exclusion bruit HR/Finance : avant 0% → cible 80%+
- Précision newsletter : avant 20% → cible 70%+

#### 4.2 Tests de Non-Régression
**Validation** :
- Items LAI-strong historiques toujours détectés
- Pas de sur-exclusion signaux authentiques
- Performance système maintenue

#### 4.3 Documentation Résultats
**Fichier** : `docs/diagnostics/signal_quality_improvement_results.md`

**Contenu** :
- Métriques avant/après
- Items LAI-strong récupérés
- Bruit éliminé
- Recommandations suite

---

## 🎯 Résultats Attendus

### Après Phase 1-3 (Corrections P0)
- ✅ **Nanexa/Moderna détecté** : PharmaShell reconnu, score >10
- ✅ **UZEDY regulatory détecté** : Trademark reconnu, bonus regulatory
- ✅ **Bruit HR/Finance éliminé** : Pénalités contextuelles efficaces
- ✅ **Seuil adapté** : min_score=8 filtre le bruit résiduel
- ✅ **Newsletter qualité** : 70-80% signal LAI authentique

### Métriques Cibles
| **Métrique** | **Avant** | **Après P0** | **Amélioration** |
|--------------|-----------|--------------|------------------|
| **Signaux LAI-strong détectés** | 25% (1/4) | 80% (3-4/4) | **+55%** |
| **Bruit HR/Finance exclu** | 0% (0/4) | 80% (3-4/4) | **+80%** |
| **Précision newsletter** | 20% | 70-80% | **+50-60%** |
| **Score Nanexa/Moderna** | ~5 | >10 | **+100%** |

---

## ⚠️ Points d'Attention

### Risques Identifiés
1. **Sur-exclusion** : Seuil trop élevé pourrait exclure signaux faibles mais pertinents
2. **Encoding** : Problèmes persistants avec caractères spéciaux (®, ™)
3. **Régression** : Perte d'items LAI-strong actuellement détectés

### Mesures de Mitigation
1. **Tests exhaustifs** : Validation sur dataset historique
2. **Rollback plan** : Sauvegarde configurations actuelles
3. **Monitoring** : Suivi métriques post-déploiement

### Critères d'Arrêt
- Régression >10% sur items LAI-strong existants
- Sur-exclusion >20% signaux authentiques
- Performance système dégradée >50%

---

## 🚀 Prochaines Étapes

### Validation Plan
1. **Revue technique** : Validation approche et paramètres
2. **Approbation** : Accord pour exécution phases 1-3
3. **Calendrier** : Planification exécution (2-3h total)

### Post-Corrections P0
1. **Analyse résultats** : Métriques détaillées amélioration
2. **Plan P1** : Améliorations architecture (scoring contextuel)
3. **Plan P2** : Intégration feedback humain automatisée

---

**Ce plan corrige spécifiquement les 3 problèmes identifiés sans ajouter Moderna aux scopes, en se concentrant sur l'amélioration de la détection des signaux LAI authentiques et l'élimination du bruit HR/Finance.**