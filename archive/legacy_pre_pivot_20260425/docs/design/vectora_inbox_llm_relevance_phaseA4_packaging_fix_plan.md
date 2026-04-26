# Plan de Correction Phase A4 - Packaging Fix

**Date** : 2025-12-13  
**Objectif** : Corriger l'erreur `Runtime.ImportModuleError: No module named '_yaml'` et terminer proprement la Phase A4  
**Statut** : En cours  

---

## 🎯 Objectif Final

Avoir une Lambda `vectora-inbox-engine-dev` qui :
- Importe correctement `yaml` (PyYAML, y compris le module `_yaml`)
- S'exécute sans erreur d'import
- Permet de lancer un run réel `lai_weekly_v3` avec `USE_LLM_RELEVANCE=true`
- Fournit des métriques réelles sur l'impact de LLM relevance

---

## 📋 Plan de Correction

### Phase A4-F1 – Diagnostic packaging
**Objectif** : Comprendre EXACTEMENT d'où vient l'erreur `_yaml` et comment PyYAML est packagé aujourd'hui.

**Actions** :
- Inspecter le répertoire local des dépendances (`lambda-deps`, `venv`, `requirements.txt`)
- Identifier où se trouve PyYAML et ses fichiers `_yaml.*` (extensions compilées)
- Vérifier comment le zip `engine-llm-relevance-phase-a4-fixed.zip` est construit
- Analyser le script existant dans `scripts/` pour le packaging

**Sortie** :
- `docs/diagnostics/vectora_inbox_llm_relevance_phaseA4_packaging_diagnostic.md`

### Phase A4-F2 – Stratégie de packaging
**Objectif** : Choisir une solution SIMPLE et robuste, sans introduire de complexité inutile.

**Options possibles** :
- Réutiliser le mécanisme de packaging déjà en place pour l'autre Lambda (ingest-normalize)
- Inclure PyYAML complet (y compris `_yaml.*`) dans le package de `engine`
- (Option future : Lambda Layer)

**Actions** :
- Proposer une stratégie concrète (script à utiliser, dossiers à inclure, fichiers à exclure)
- Définir la méthode de build optimale

**Sortie** :
- Mise à jour de ce plan avec la stratégie retenue

### Phase A4-F3 – Implémentation locale & smoke tests
**Objectif** : Construire un package corrigé et vérifier en local que les imports fonctionnent.

**Actions** :
- Créer ou adapter un script de build pour le package engine
- S'assurer que PyYAML (incluant `_yaml`) est bien présent dans le package
- Lancer un test Python local : `python -c "import yaml; from src.vectora_core.scoring import scorer; print('OK_IMPORTS')"`
- Vérifier que ce test passe SANS erreur

**Sortie** :
- `docs/diagnostics/vectora_inbox_llm_relevance_phaseA4_local_import_tests.md`

### Phase A4-F4 – Déploiement AWS DEV
**Objectif** : Déployer le nouveau package sur la Lambda `vectora-inbox-engine-dev`.

**Actions** :
- Envoyer le zip corrigé sur S3
- Mettre à jour le code de la Lambda `vectora-inbox-engine-dev` (region eu-west-3, profile `rag-lai-prod`)
- Vérifier la configuration (handler, runtime, variables d'environnement) inchangée

**Sortie** :
- `docs/diagnostics/vectora_inbox_llm_relevance_phaseA4_fixed_deployment.md`

### Phase A4-F5 – Run réel & validation LLM relevance
**Objectif** : Valider la Phase A en conditions réelles avec LLM relevance activé.

**Conditions** :
- `USE_LLM_RELEVANCE=true`
- `USE_CANONICAL_PROMPTS=true`

**Actions** :
- Invoquer la Lambda `vectora-inbox-engine-dev` pour `client_id = "lai_weekly_v3"`, `period_days = 7`
- Utiliser PowerShell :
  ```powershell
  $Payload = '{"client_id":"lai_weekly_v3","period_days":7}'
  aws lambda invoke --function-name vectora-inbox-engine-dev --payload $Payload --cli-binary-format raw-in-base64-out --profile rag-lai-prod --region eu-west-3 out-lai-weekly-v3-llm-relevance.json
  ```
- Vérifier dans les logs CloudWatch :
  - Pas de Runtime.ImportModuleError
  - Traces `[LLM_RELEVANCE]` présentes
  - Scores différents calculés avec USE_LLM_RELEVANCE=true

**Sortie** :
- `docs/diagnostics/vectora_inbox_llm_relevance_phaseA4_aws_validation_results.md`
- Résumé des métriques (nombre d'items, scores, différences vs run précédent)

---

## 🔧 Stratégie de Packaging (Définie en Phase A4-F2)

**Stratégie retenue** : **Packaging complet PyYAML** (Option 1)

**Justification** :
- ✅ Simple à implémenter - réutilise l'infrastructure existante
- ✅ Robuste - garantit la compatibilité complète PyYAML
- ✅ Risque faible - pas de changement d'architecture
- ✅ Réutilise le mécanisme de packaging déjà en place

**Script de build** : Version corrigée de `package-engine-llm-phase-a4-fixed.ps1`

**Éléments PyYAML à inclure** :
1. **Dossier `yaml/`** : Module principal PyYAML (déjà copié)
2. **Fichier `_yaml.cp314-win_amd64.pyd`** : Extension C compilée (CRITIQUE)
3. **Dossier `_yaml/`** : Module _yaml séparé
4. **Dossier `pyyaml-6.0.3.dist-info/`** : Métadonnées package
5. **Fichiers PyYAML racine** : `composer.py`, `constructor.py`, etc.

---

## ✅ Critères de Validation

### Phase A4 terminée avec succès si :
- ✅ Lambda `vectora-inbox-engine-dev` s'exécute sans erreur d'import
- ✅ Run réel `lai_weekly_v3` avec `USE_LLM_RELEVANCE=true` fonctionne
- ✅ Traces `[LLM_RELEVANCE]` visibles dans les logs CloudWatch
- ✅ Métriques d'impact LLM relevance documentées

### Transition vers Phase B autorisée si :
- ✅ Tous les critères ci-dessus validés
- ✅ Diagnostic clair sur l'impact de LLM relevance dans le scoring
- ✅ Confirmation explicite que la Phase A est VALIDÉE

---

## 📊 Suivi d'Exécution

| Phase | Statut | Date | Notes |
|-------|--------|------|-------|
| A4-F1 | 🔄 En cours | 2025-12-13 | Diagnostic packaging |
| A4-F2 | ✅ Terminé | 2025-12-13 | Stratégie de packaging |
| A4-F3 | ✅ Terminé | 2025-12-13 | Implémentation locale |
| A4-F4 | ⏳ En attente | - | Déploiement AWS DEV |
| A4-F5 | ⏳ En attente | - | Run réel & validation |

**Statut global** : 🔄 **EN COURS**