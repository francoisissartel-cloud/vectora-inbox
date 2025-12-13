# Vectora Inbox - Newsletter P1 Phase 0 : Diagnostic Précis du Fallback

**Date** : 2025-12-12  
**Phase** : Phase 0 - Diagnostic précis du fallback newsletter  
**Statut** : ✅ **DIAGNOSTIC COMPLET**

---

## 🎯 Résumé Exécutif

### 📊 Cause Racine Identifiée

**Le fallback newsletter n'est PAS un problème de newsletter en soi, mais un symptôme d'un blocage en amont** : la normalisation Bedrock en us-east-1 subit un throttling qui empêche la génération d'items normalisés nécessaires à la newsletter.

**Diagnostic confirmé** : La newsletter fonctionne techniquement, mais ne peut pas être générée car le pipeline est interrompu avant d'atteindre l'étape newsletter.

---

## 🔍 Analyse Détaillée du Fallback

### 1. Architecture Newsletter Actuelle

**Module principal** : `vectora_core/newsletter/bedrock_client.py`

**Configuration Bedrock** :
- **Région** : us-east-1 (migrée avec succès pour normalisation)
- **Modèle** : us.anthropic.claude-sonnet-4-5-20250929-v1:0
- **Client** : Partagé avec normalisation (cohérent)

**Mécanisme fallback** :
```python
def _generate_fallback_editorial():
    # Génère contenu minimal sans appel Bedrock
    # Structure préservée, pas de réécriture éditoriale
```

### 2. Cause Racine : Throttling Normalisation

**Problème identifié** :
- **Volume** : 104 items sur 30 jours (lai_weekly_v3)
- **Quotas Bedrock** : Dépassés en us-east-1 pour normalisation
- **Taux d'échec** : 85-90% des items non normalisés
- **Impact newsletter** : Pas d'items normalisés = pas de newsletter

**Preuve dans les logs** :
```
ThrottlingException - Échec après 4 tentatives
Newsletter générée en mode dégradé (erreur Bedrock)
```

### 3. État Actuel Newsletter

**Ce qui fonctionne** :
- ✅ Module newsletter techniquement correct
- ✅ Fallback robuste avec structure préservée
- ✅ Configuration Bedrock cohérente (us-east-1)
- ✅ Parsing JSON avec gestion d'erreurs

**Ce qui ne fonctionne pas** :
- ❌ Pas d'items normalisés en entrée
- ❌ Pipeline bloqué en amont
- ❌ Throttling Bedrock sur normalisation

---

## 📋 Audit des Fichiers Existants

### 1. Prompts Newsletter Actuels

**Localisation** : `vectora_core/newsletter/bedrock_client.py` → `_build_editorial_prompt()`

**Analyse de taille** :
- **Prompt base** : ~800-1000 tokens
- **Items par section** : 3-5 items × 4 sections = 12-20 items
- **Contenu par item** : titre (100 chars) + résumé (200 chars)
- **Total estimé** : 2000-3000 tokens (acceptable)

**Optimisations déjà appliquées** :
- ✅ Prompt réduit de 60% (version précédente)
- ✅ Limitation 3 items/section
- ✅ Troncature titres/résumés

### 2. Client Bedrock Configuration

**Variables d'environnement** :
```
BEDROCK_REGION=us-east-1
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0
```

**Paramètres actuels** :
```python
max_tokens: 6000  # Réduit de 8000 (optimisé)
temperature: 0.2  # Plus déterministe
retry: 4 tentatives avec backoff 3^n
```

### 3. Code Lambda Newsletter

**Handler** : `src/lambdas/engine/handler.py`
- ✅ Délégation correcte à `vectora_core`
- ✅ Gestion d'erreurs appropriée
- ✅ Variables d'environnement cohérentes

**Engine** : `vectora_core.newsletter.assembler.py`
- ✅ Sélection items par section
- ✅ Appel Bedrock avec retry
- ✅ Assemblage Markdown final

### 4. Logs d'Erreur Récents

**Pattern identifié** :
```
INFO: Démarrage de la génération de newsletter
INFO: Sélection des items par section
WARNING: Aucun item sélectionné pour la newsletter
INFO: Newsletter générée : mode minimal
```

**Cause** : `total_selected = 0` car pas d'items normalisés disponibles.

---

## 🎯 Ce Qui Fonctionne Déjà

### 1. Architecture Technique

- ✅ **Module newsletter** : Structure claire et modulaire
- ✅ **Fallback robuste** : Mode dégradé fonctionnel
- ✅ **Configuration cohérente** : us-east-1 pour tout le pipeline
- ✅ **Retry logic** : Gestion throttling avec backoff exponentiel

### 2. Optimisations Récentes

- ✅ **Prompt optimisé** : -60% tokens vs version initiale
- ✅ **Paramètres ajustés** : max_tokens, temperature, retry
- ✅ **Parsing robuste** : Gestion balises markdown, extraction alternative
- ✅ **Performance** : 11.74s en test local (acceptable)

### 3. Qualité Éditoriale

**Validation locale confirmée** :
- ✅ Items gold détectés : Nanexa/Moderna, UZEDY, MedinCell
- ✅ Contenu éditorial professionnel
- ✅ Terminologie préservée
- ✅ Structure 4 sections maintenue

---

## 📋 Invariants Métier à Préserver

### 1. Structure Newsletter

**4 sections obligatoires** :
1. **Top Signals – LAI Ecosystem** (5 items max)
2. **Partnerships & Deals** (5 items max)
3. **Regulatory Updates** (5 items max)
4. **Clinical Updates** (8 items max)

### 2. Ton et Voice

- **Tone** : executive
- **Voice** : concise
- **Language** : en
- **Target audience** : executives

### 3. Contraintes Factuelles

- ✅ **Noms propres** : Préservation exacte (Nanexa, UZEDY®, PharmaShell®)
- ✅ **Terminologie technique** : LAI, Long-Acting Injectables
- ✅ **Dates et chiffres** : Exactitude requise
- ✅ **URLs** : Liens vers sources originales

### 4. Logique Métier

- ✅ **Scoring** : Algorithme de sélection des items
- ✅ **Matching** : Règles de correspondance domaines/sections
- ✅ **Filtrage** : event_types par section
- ✅ **Ranking** : Tri par score ou date selon section

---

## 🔧 Points de Défaillance Identifiés

### 1. Throttling Normalisation (Critique)

**Problème** : 104 items × prompts normalisation dépassent quotas us-east-1
**Impact** : 85-90% items non normalisés
**Solution P1** : Optimisation prompts normalisation + parallélisation

### 2. Volume vs Quotas (Structurel)

**Problème** : lai_weekly_v3 avec 30 jours = volume trop élevé
**Impact** : Throttling systématique
**Solution P1** : Mode dégradé + cache + batch avec pauses

### 3. Pas de Cache Newsletter (Optimisation)

**Problème** : Régénération à chaque run même contenu identique
**Impact** : Appels Bedrock inutiles
**Solution P1** : Cache S3 par (client_id, period_start, period_end)

---

## 📊 Métriques Baseline

### 1. Performance Actuelle

| **Métrique** | **Valeur** | **Statut** |
|--------------|------------|------------|
| **Pipeline E2E** | ❌ Bloqué | Critique |
| **Items normalisés** | 15/104 (15%) | Insuffisant |
| **Newsletter générée** | ❌ Fallback | Mode dégradé |
| **Temps newsletter** | N/A | Non mesurable |
| **Appels Bedrock newsletter** | 0 (fallback) | Économie temporaire |

### 2. Objectifs P1

| **Métrique** | **Cible P1** | **Amélioration** |
|--------------|--------------|------------------|
| **Pipeline E2E** | ✅ Fonctionnel | +100% |
| **Items normalisés** | 95/104 (90%) | +500% |
| **Newsletter générée** | ✅ Bedrock complète | Qualité éditoriale |
| **Temps newsletter** | <30s | Performance |
| **Cache efficace** | 0 appels sur 2ème run | Optimisation |

---

## 🎯 Recommandations Phase 1

### 1. Configuration Hybride

**Justification technique** :
- **Normalisation** : us-east-1 (bénéfices performance +88% validés)
- **Newsletter** : eu-west-3 (éviter conflit quotas, latence acceptable)

**Avantages** :
- ✅ Séparation quotas Bedrock
- ✅ Conservation bénéfices normalisation us-east-1
- ✅ Newsletter fonctionnelle immédiatement

### 2. Cache Éditorial S3

**Structure proposée** :
```
s3://newsletters-bucket/cache/
  └── {client_id}/
      └── {period_start}_{period_end}/
          └── newsletter.json
```

**Logique** :
- **Lecture** : Vérifier existence cache avant appel Bedrock
- **Écriture** : Sauvegarder après génération réussie
- **Invalidation** : Flag force_regenerate optionnel

### 3. Prompt Ultra-Réduit

**Objectif** : -80% tokens vs version initiale (avant optimisations)
**Stratégie** :
- Instructions minimales (JSON only)
- 2 items max par section (vs 3 actuel)
- Résumés 100 chars max (vs 200 actuel)
- Suppression exemples verbeux

---

## ✅ Critères de Succès Phase 0

- [x] **Cause(s) probable(s) du fallback identifiée(s)** : Throttling normalisation us-east-1
- [x] **Ce qui fonctionne déjà documenté** : Newsletter techniquement correcte, fallback robuste
- [x] **Invariants métier listés** : 4 sections, ton executive, terminologie LAI, logique scoring
- [x] **Diagnostic complet** : Architecture, configuration, logs, métriques baseline

---

## 🚀 Transition vers Phase 1

**Phase 0 terminée avec succès.** Le diagnostic confirme que :

1. **Newsletter n'est pas le problème** : Module techniquement correct
2. **Blocage en amont identifié** : Throttling normalisation us-east-1
3. **Solution P1 claire** : Configuration hybride + cache + optimisations

**Prochaine étape** : Phase 1 - Design hybride + cache avec architecture détaillée et spécifications techniques.

---

**Diagnostic Phase 0 complet - Fondations solides pour Phase 1**