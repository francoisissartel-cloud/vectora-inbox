# Inventaire Nettoyage Repo - Vectora Inbox

**Date :** 19 décembre 2025  
**Objectif :** Nettoyage conservateur de la racine du repo  
**Workflow protégé :** lai_weekly_v4 (Lambda ingest V2 + normalize_score V2 + layers Bedrock-only)

---

## 📋 CLASSIFICATION DES ÉLÉMENTS RACINE

### CORE (Intouchable - 0 modification)

| Élément | Type | Justification | Risque si supprimé |
|---------|------|---------------|-------------------|
| `.q-context/` | Dossier | Règles développement Q Developer | CRITIQUE - Perte règles projet |
| `canonical/` | Dossier | Données métier (scopes, prompts) | CRITIQUE - Perte configuration Bedrock |
| `client-config-examples/` | Dossier | Templates configuration clients | CRITIQUE - Perte contrats clients |
| `contracts/` | Dossier | Spécifications Lambda | CRITIQUE - Perte documentation API |
| `docs/` | Dossier | Documentation technique | ÉLEVÉ - Perte historique projet |
| `infra/` | Dossier | Templates CloudFormation | CRITIQUE - Perte infrastructure |
| `scripts/` | Dossier | Scripts déploiement/test | ÉLEVÉ - Perte outils développement |
| `src/` | Dossier | Code historique (pollué mais référencé) | ÉLEVÉ - Potentielles dépendances |
| `src_v2/` | Dossier | Code de référence V2 | CRITIQUE - Moteur principal |
| `tests/` | Dossier | Tests unitaires/intégration | ÉLEVÉ - Perte validation |
| `backup/` | Dossier | Sauvegardes existantes | ÉLEVÉ - Perte historique |
| `output/` | Dossier | Sorties de tests | MOYEN - Données de référence |
| `layer_management/` | Dossier | Gestion layers AWS | ÉLEVÉ - Outils déploiement |
| `.gitignore` | Fichier | Configuration Git | CRITIQUE - Contrôle version |
| `AWS_DEPLOYMENT_SUMMARY.md` | Fichier | Résumé déploiement | ÉLEVÉ - Documentation déploiement |
| `DEPLOY_INSTRUCTIONS.md` | Fichier | Instructions déploiement | ÉLEVÉ - Procédures AWS |
| `global_prompts_s3.yaml` | Fichier | Prompts Bedrock S3 | CRITIQUE - Configuration Bedrock |
| `global_prompts.yaml` | Fichier | Prompts Bedrock locaux | CRITIQUE - Configuration Bedrock |

### BUILD_CURRENT (Artefacts utilisés actuellement)

| Élément | Type | Justification | Risque si supprimé |
|---------|------|---------------|-------------------|
| `layer_v18_working.zip` | Archive | Layer fonctionnelle de référence | ÉLEVÉ - Rollback impossible |
| `vectora-core-matching-bedrock-v19-final.zip` | Archive | Layer actuelle selon deployment_info | CRITIQUE - Layer en production |

### BUILD_OLD (Anciens artefacts de build)

| Élément | Type | Justification | Risque si supprimé |
|---------|------|---------------|-------------------|
| `lambda_minimal_v25/` | Dossier | Ancien package Lambda | FAIBLE - Version obsolète |
| `lambda_package_v25/` | Dossier | Ancien package Lambda complet | FAIBLE - Version obsolète |
| `layer_build/` | Dossier | Build temporaire layer | FAIBLE - Artefact temporaire |
| `layer_build_bedrock_only/` | Dossier | Build temporaire layer | FAIBLE - Artefact temporaire |
| `layer_build_v24/` | Dossier | Build temporaire layer | FAIBLE - Artefact temporaire |
| `layer_build_v25/` | Dossier | Build temporaire layer | FAIBLE - Artefact temporaire |
| `layer_build_v26/` | Dossier | Build temporaire layer | FAIBLE - Artefact temporaire |
| `layer_complete_v27/` | Dossier | Build temporaire layer | FAIBLE - Artefact temporaire |
| `layer_v18_check/` | Dossier | Vérification layer | FAIBLE - Artefact temporaire |
| `lambda-handler-minimal-v25.zip` | Archive | Ancien package Lambda | FAIBLE - Version obsolète |
| `lambda-normalize-score-v2-bedrock-pure.zip` | Archive | Ancien package Lambda | FAIBLE - Version obsolète |
| `lambda-normalize-score-v2-debug-v25.zip` | Archive | Ancien package Lambda | FAIBLE - Version obsolète |
| `lambda-normalize-score-v2-fixed.zip` | Archive | Ancien package Lambda | FAIBLE - Version obsolète |
| `vectora-core-bedrock-debug-v25.zip` | Archive | Ancienne layer | FAIBLE - Version obsolète |
| `vectora-core-bedrock-debug-v26.zip` | Archive | Ancienne layer | FAIBLE - Version obsolète |
| `vectora-core-bedrock-only-fixed.zip` | Archive | Ancienne layer | FAIBLE - Version obsolète |
| `vectora-core-bedrock-only-pure.zip` | Archive | Ancienne layer | FAIBLE - Version obsolète |
| `vectora-core-bedrock-only.zip` | Archive | Ancienne layer | FAIBLE - Version obsolète |
| `vectora-core-bedrock-pure-v20.zip` | Archive | Ancienne layer | FAIBLE - Version obsolète |
| `vectora-core-bedrock-pure-v21.zip` | Archive | Ancienne layer | FAIBLE - Version obsolète |
| `vectora-core-bedrock-pure-v22.zip` | Archive | Ancienne layer | FAIBLE - Version obsolète |
| `vectora-core-bedrock-pure-v23.zip` | Archive | Ancienne layer | FAIBLE - Version obsolète |
| `vectora-core-bedrock-pure-v24.zip` | Archive | Ancienne layer | FAIBLE - Version obsolète |
| `vectora-core-complete-v27.zip` | Archive | Ancienne layer | FAIBLE - Version obsolète |
| `vectora-core-layer.zip` | Archive | Ancienne layer | FAIBLE - Version obsolète |
| `vectora-core-matching-bedrock-v18.zip` | Archive | Ancienne layer | FAIBLE - Version obsolète |
| `vectora-core-matching-supprime.zip` | Archive | Ancienne layer | FAIBLE - Version obsolète |

### DEBUG_OUTPUT (Fichiers de debug/sortie)

| Élément | Type | Justification | Risque si supprimé |
|---------|------|---------------|-------------------|
| `debug_payload.json` | JSON | Payload de debug | FAIBLE - Données temporaires |
| `lambda_logs.txt` | Log | Logs Lambda | FAIBLE - Données temporaires |
| `payload.json` | JSON | Payload de test | FAIBLE - Données temporaires |
| `response_final_v25.json` | JSON | Réponse Lambda | FAIBLE - Données temporaires |
| `response_ingest_lai_v4.json` | JSON | Réponse Lambda | FAIBLE - Données temporaires |
| `response_ingest.json` | JSON | Réponse Lambda | FAIBLE - Données temporaires |
| `response_normalize_final.json` | JSON | Réponse Lambda | FAIBLE - Données temporaires |
| `response_normalize_lai_v4.json` | JSON | Réponse Lambda | FAIBLE - Données temporaires |
| `response_normalize_v2.json` | JSON | Réponse Lambda | FAIBLE - Données temporaires |
| `response_normalize.json` | JSON | Réponse Lambda | FAIBLE - Données temporaires |
| `response_success_v26.json` | JSON | Réponse Lambda | FAIBLE - Données temporaires |
| `response_v18.json` | JSON | Réponse Lambda | FAIBLE - Données temporaires |
| `response_v19_test.json` | JSON | Réponse Lambda | FAIBLE - Données temporaires |
| `response_v20.json` | JSON | Réponse Lambda | FAIBLE - Données temporaires |
| `response_v21_final.json` | JSON | Réponse Lambda | FAIBLE - Données temporaires |
| `response_v22_final.json` | JSON | Réponse Lambda | FAIBLE - Données temporaires |
| `response_v23_final.json` | JSON | Réponse Lambda | FAIBLE - Données temporaires |
| `response_v24_final.json` | JSON | Réponse Lambda | FAIBLE - Données temporaires |
| `response_v24_success.json` | JSON | Réponse Lambda | FAIBLE - Données temporaires |
| `response_v24_test.json` | JSON | Réponse Lambda | FAIBLE - Données temporaires |
| `response_v25_final.json` | JSON | Réponse Lambda | FAIBLE - Données temporaires |
| `response_v25_no_layer.json` | JSON | Réponse Lambda | FAIBLE - Données temporaires |
| `response_v25_success.json` | JSON | Réponse Lambda | FAIBLE - Données temporaires |
| `response_v25_test.json` | JSON | Réponse Lambda | FAIBLE - Données temporaires |
| `response.json` | JSON | Réponse Lambda | FAIBLE - Données temporaires |
| `test_lambda_payload.json` | JSON | Payload de test | FAIBLE - Données temporaires |
| `test_payload.json` | JSON | Payload de test | FAIBLE - Données temporaires |

### TO_REVIEW (Incertitude - pas de modification)

| Élément | Type | Justification | Risque si supprimé |
|---------|------|---------------|-------------------|
| `$null` | Fichier | Fichier suspect, origine inconnue | INCONNU - Analyse nécessaire |
| `handler.py` | Script | Handler racine, potentiel doublon | MOYEN - Potentiel point d'entrée |
| `check_latest_logs.py` | Script | Script debug, doublon possible avec scripts/ | MOYEN - Outil de debug |
| `check_recent_logs.py` | Script | Script debug, doublon possible avec scripts/ | MOYEN - Outil de debug |
| `check_results.py` | Script | Script debug, doublon possible avec scripts/ | MOYEN - Outil de debug |
| `debug_config_loading.py` | Script | Script debug spécifique | MOYEN - Outil de debug |
| `execute_bedrock_only_fix.py` | Script | Script correction spécifique | MOYEN - Correction appliquée |
| `execute_bedrock_only_pure.py` | Script | Script correction spécifique | MOYEN - Correction appliquée |
| `execute_suppression_matching_deterministe.py` | Script | Script correction spécifique | MOYEN - Correction appliquée |
| `lai_weekly_v3_from_s3_check.yaml` | Config | Configuration test | MOYEN - Config de validation |
| `lai_weekly_v3_from_s3.yaml` | Config | Configuration test | MOYEN - Config de validation |
| `lai_weekly_v3.yaml` | Config | Configuration client | ÉLEVÉ - Config client active |
| `lai_weekly_v3.yaml.backup` | Config | Sauvegarde configuration | MOYEN - Sauvegarde manuelle |
| `quick_test_bedrock_only.py` | Script | Test rapide | MOYEN - Outil de test |
| `test_*.py` (15 fichiers) | Scripts | Scripts de test divers | MOYEN - Outils de développement |

---

## 📊 RÉSUMÉ STATISTIQUES

| Catégorie | Nombre d'éléments | Taille estimée | Action prévue |
|-----------|-------------------|----------------|---------------|
| **CORE** | 16 éléments | N/A | AUCUNE - Intouchable |
| **BUILD_CURRENT** | 2 éléments | ~50MB | MOVE_TO_LAYER_ARCHIVE |
| **BUILD_OLD** | 25 éléments | ~500MB | MOVE_TO_BACKUP |
| **DEBUG_OUTPUT** | 25 éléments | ~5MB | MOVE_TO_DEBUG_ARCHIVE |
| **TO_REVIEW** | 32 éléments | ~10MB | AUCUNE - Analyse manuelle |

---

## ⚠️ RISQUES IDENTIFIÉS

### Risques Critiques (Aucune action)
- Modification accidentelle de src_v2/ ou canonical/
- Suppression de layers actuellement déployées
- Perte de configuration Bedrock active

### Risques Modérés (Actions conservatrices)
- Scripts de debug potentiellement utiles → TO_REVIEW
- Configurations de test → TO_REVIEW  
- Handlers racine → TO_REVIEW

### Risques Faibles (Actions sûres)
- Anciens builds → MOVE_TO_BACKUP
- Fichiers JSON temporaires → MOVE_TO_DEBUG_ARCHIVE
- Dossiers de build temporaires → MOVE_TO_BACKUP

---

## 🎯 RECOMMANDATIONS

### Actions Immédiates (Phase 2)
1. **Créer plan détaillé** pour BUILD_OLD et DEBUG_OUTPUT uniquement
2. **Préserver** tous éléments CORE et TO_REVIEW
3. **Archiver** BUILD_CURRENT dans layer_management/archive/

### Actions Différées (Analyse manuelle)
1. **Analyser** scripts TO_REVIEW pour doublons avec scripts/
2. **Valider** configurations TO_REVIEW avec équipe
3. **Décider** du sort des handlers racine

### Validation Continue
1. **Tester** workflow lai_weekly_v4 après chaque action
2. **Vérifier** layer vectora-core version 6 reste active
3. **Confirmer** aucun impact sur déploiement AWS

---

**Inventaire Repo Cleanup V1**  
**Approche ultra-conservatrice - Préservation workflow E2E**  
**Prochaine étape : Plan détaillé Phase 2**