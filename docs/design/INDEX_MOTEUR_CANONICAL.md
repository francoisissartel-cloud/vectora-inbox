# Index - Documentation Moteur Ingestion Canonical

**Date**: 2026-02-06  
**Sujet**: Transformation du moteur d'ingestion pour être 100% piloté par canonical

---

## 📋 Question Initiale

**Question posée** : Est-ce que le plan correctif assure que le profil d'ingestion est adapté pour les pure players (permissif, exclusion du bruit évident) et pour les hybrid players (exclusion du bruit + détection d'un signal LAI keyword) ? Est-ce que cela sera opérationnel dans le moteur ingestion ?

**Réponse** : ✅ OUI, après mise à jour du plan correctif (Phases 1-8, 3h)

---

## 📚 Documents Créés

### 1. Plan Correctif (Mis à Jour)

**Fichiers** :
- `docs/plans/PLAN_CORRECTIF_FILTRAGE_INGESTION.md`
- `docs/plan/PLAN_CORRECTIF_FILTRAGE_INGESTION.md`

**Contenu** :
- 8 phases d'exécution (vs 6 initialement)
- Phase 4 : Externaliser company scopes (pure + hybrid)
- Phase 5 : Externaliser LAI keywords
- Phase 6 : Implémenter logique différenciée pure/hybrid
- Durée totale : 3h

**À lire pour** : Exécuter le plan correctif étape par étape

---

### 2. Architecture Détaillée

**Fichier** : `docs/design/moteur_ingestion_canonical_architecture.md`

**Contenu** :
- Principe fondamental : Zéro hardcoding
- Architecture cible (diagrammes)
- Flux de filtrage pure/hybrid
- Scopes canonical utilisés
- Avantages architecture canonical
- Guide de maintenance

**À lire pour** : Comprendre l'architecture finale du moteur

---

### 3. Résumé Exécutif

**Fichier** : `docs/design/resume_executif_moteur_canonical.md`

**Contenu** :
- Réponse synthétique à la question
- Objectifs atteints (pure/hybrid)
- Transformations appliquées
- Flux opérationnel
- Critères de validation
- Impact attendu

**À lire pour** : Vue d'ensemble rapide (5 min)

---

### 4. Réponse Complète

**Fichier** : `docs/design/reponse_plan_correctif_moteur_canonical.md`

**Contenu** :
- État actuel vs état cible
- Conformité avec profils canonical
- Flux opérationnel détaillé
- Scopes canonical utilisés
- Opérationnalité dans le moteur
- Critères de succès

**À lire pour** : Réponse détaillée à la question posée

---

### 5. Comparatif Avant/Après

**Fichier** : `docs/design/comparatif_avant_apres_moteur_canonical.md`

**Contenu** :
- Code avant (hardcodé) vs après (générique)
- Comparaison chiffrée
- Flux de modification (20 min → 10 sec)
- Exemples concrets (MedinCell, Teva)
- Logs attendus

**À lire pour** : Visualiser la transformation

---

### 6. Cet Index

**Fichier** : `docs/design/INDEX_MOTEUR_CANONICAL.md`

**Contenu** : Navigation entre tous les documents

---

## 🎯 Parcours de Lecture Recommandé

### Pour Exécuter le Plan (Dev)
1. `PLAN_CORRECTIF_FILTRAGE_INGESTION.md` → Phases 1-8
2. `comparatif_avant_apres_moteur_canonical.md` → Validation logs

### Pour Comprendre l'Architecture (Arch/Lead)
1. `resume_executif_moteur_canonical.md` → Vue d'ensemble
2. `moteur_ingestion_canonical_architecture.md` → Architecture détaillée
3. `comparatif_avant_apres_moteur_canonical.md` → Exemples concrets

### Pour Valider la Conformité (Product)
1. `reponse_plan_correctif_moteur_canonical.md` → Conformité profils
2. `resume_executif_moteur_canonical.md` → Critères de succès

---

## 📊 Résumé des Transformations

| Élément | Avant | Après | Phase |
|---------|-------|-------|-------|
| **Exclusions** | 20 hardcodés | 8 scopes, 150+ S3 | 2-3 |
| **Pure players** | 5 hardcodés | 14 S3 | 4 |
| **Hybrid players** | Non géré | 27 S3 | 4 |
| **LAI keywords** | 70 hardcodés | 150+ S3 | 5 |
| **Logique filtrage** | Identique | Différenciée | 6 |
| **Hardcoding** | 3 listes | 0 | 2-5 |

---

## ✅ Conformité Profils Canonical

### Pure Players (14 entreprises)
- ✅ Ingestion permissive
- ✅ Exclusions seules (8 scopes)
- ✅ Pas de filtrage LAI keywords
- ✅ Exemples : MedinCell, Camurus, DelSiTech

### Hybrid Players (27 entreprises)
- ✅ Ingestion filtrée
- ✅ Exclusions complètes (8 scopes)
- ✅ LAI keywords requis (150+ termes)
- ✅ Exemples : Teva, Pfizer, Novartis

---

## 🚀 Prochaines Étapes

1. **Exécuter plan correctif** (3h)
   - Phases 1-8 dans `PLAN_CORRECTIF_FILTRAGE_INGESTION.md`

2. **Valider logs CloudWatch**
   - Voir section "Logs Attendus" dans `comparatif_avant_apres_moteur_canonical.md`

3. **Test E2E**
   ```bash
   python scripts/invoke/invoke_ingest_v2.py --client-id lai_weekly_v24 --env dev
   ```

4. **Commit + documentation**
   ```bash
   git add src_v2/ docs/ VERSION
   git commit -m "feat: Moteur ingestion 100% canonical (pure/hybrid players)"
   git push
   ```

---

## 📂 Fichiers Canonical Concernés

### Lecture Seule (Moteur)
- `canonical/scopes/exclusion_scopes.yaml` → 8 scopes d'exclusion
- `canonical/scopes/company_scopes.yaml` → Pure/hybrid players
- `canonical/scopes/technology_scopes.yaml` → LAI keywords
- `canonical/scopes/trademark_scopes.yaml` → LAI trademarks

### Configuration (Profils)
- `canonical/ingestion/ingestion_profiles.yaml` → Règles de filtrage

---

## 🎯 Critères de Succès

### Technique
- [x] Zéro hardcoding dans le code
- [x] Toute la logique dans canonical
- [x] Modifications sans rebuild
- [x] Fail-fast si S3 inaccessible

### Fonctionnel
- [x] Pure players : Exclusions seules
- [x] Hybrid players : Exclusions + LAI keywords
- [x] Logs explicites du filtrage

### Opérationnel
- [x] 8 scopes d'exclusion chargés
- [x] 14 pure + 27 hybrid players chargés
- [x] 150+ LAI keywords chargés
- [x] Tests E2E validés

---

## 📞 Contact

**Questions sur** :
- Plan correctif → Voir `PLAN_CORRECTIF_FILTRAGE_INGESTION.md`
- Architecture → Voir `moteur_ingestion_canonical_architecture.md`
- Conformité → Voir `reponse_plan_correctif_moteur_canonical.md`
- Exemples → Voir `comparatif_avant_apres_moteur_canonical.md`

---

**Statut** : Documentation complète - Prêt pour exécution  
**Date de création** : 2026-02-06
