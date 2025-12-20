# Plan de Nettoyage Repo - Vectora Inbox

**Date :** 19 décembre 2025  
**Objectif :** Nettoyage conservateur de la racine du repo  
**Stratégie :** MOVE uniquement, pas de DELETE  
**Workflow protégé :** lai_weekly_v4 (Lambda ingest V2 + normalize_score V2)

---

## 🎯 STRATÉGIE GÉNÉRALE

### Principe Directeur
- **MOVE ONLY** : Aucune suppression définitive
- **PRÉSERVATION TOTALE** : Éléments CORE et TO_REVIEW intouchables
- **ARCHIVAGE ORGANISÉ** : Structure claire pour retrouver les éléments

### Dossiers de Destination
```
backup/
├── old_builds/           # Anciens packages et layers
├── debug_outputs/        # Fichiers JSON et logs temporaires
└── current_builds/       # Builds actuels mais à ranger

layer_management/
└── archive/             # Layers et builds organisés par version
```

---

## 📋 ACTIONS DÉTAILLÉES PAR ÉLÉMENT

### BUILD_CURRENT → MOVE_TO_LAYER_ARCHIVE

| Élément | Action | Destination | Raison |
|---------|--------|-------------|--------|
| `layer_v18_working.zip` | MOVE_TO_LAYER_ARCHIVE | `layer_management/archive/v18/layer_v18_working.zip` | Layer de référence à conserver mais ranger |
| `vectora-core-matching-bedrock-v19-final.zip` | MOVE_TO_LAYER_ARCHIVE | `layer_management/archive/v19/vectora-core-matching-bedrock-v19-final.zip` | Layer actuelle selon deployment_info, à archiver proprement |

### BUILD_OLD → MOVE_TO_BACKUP

#### Dossiers de Build Temporaires
| Élément | Action | Destination | Raison |
|---------|--------|-------------|--------|
| `lambda_minimal_v25/` | MOVE_TO_BACKUP | `backup/old_builds/lambda_packages/lambda_minimal_v25/` | Ancien package Lambda obsolète |
| `lambda_package_v25/` | MOVE_TO_BACKUP | `backup/old_builds/lambda_packages/lambda_package_v25/` | Ancien package Lambda complet obsolète |
| `layer_build/` | MOVE_TO_BACKUP | `backup/old_builds/layer_builds/layer_build/` | Artefact de build temporaire |
| `layer_build_bedrock_only/` | MOVE_TO_BACKUP | `backup/old_builds/layer_builds/layer_build_bedrock_only/` | Artefact de build temporaire |
| `layer_build_v24/` | MOVE_TO_BACKUP | `backup/old_builds/layer_builds/layer_build_v24/` | Artefact de build temporaire |
| `layer_build_v25/` | MOVE_TO_BACKUP | `backup/old_builds/layer_builds/layer_build_v25/` | Artefact de build temporaire |
| `layer_build_v26/` | MOVE_TO_BACKUP | `backup/old_builds/layer_builds/layer_build_v26/` | Artefact de build temporaire |
| `layer_complete_v27/` | MOVE_TO_BACKUP | `backup/old_builds/layer_builds/layer_complete_v27/` | Artefact de build temporaire |
| `layer_v18_check/` | MOVE_TO_BACKUP | `backup/old_builds/layer_builds/layer_v18_check/` | Dossier de vérification temporaire |

#### Archives Lambda Obsolètes
| Élément | Action | Destination | Raison |
|---------|--------|-------------|--------|
| `lambda-handler-minimal-v25.zip` | MOVE_TO_BACKUP | `backup/old_builds/lambda_archives/lambda-handler-minimal-v25.zip` | Version obsolète |
| `lambda-normalize-score-v2-bedrock-pure.zip` | MOVE_TO_BACKUP | `backup/old_builds/lambda_archives/lambda-normalize-score-v2-bedrock-pure.zip` | Version obsolète |
| `lambda-normalize-score-v2-debug-v25.zip` | MOVE_TO_BACKUP | `backup/old_builds/lambda_archives/lambda-normalize-score-v2-debug-v25.zip` | Version obsolète |
| `lambda-normalize-score-v2-fixed.zip` | MOVE_TO_BACKUP | `backup/old_builds/lambda_archives/lambda-normalize-score-v2-fixed.zip` | Version obsolète |

#### Archives Layer Obsolètes
| Élément | Action | Destination | Raison |
|---------|--------|-------------|--------|
| `vectora-core-bedrock-debug-v25.zip` | MOVE_TO_BACKUP | `backup/old_builds/layer_archives/vectora-core-bedrock-debug-v25.zip` | Version obsolète |
| `vectora-core-bedrock-debug-v26.zip` | MOVE_TO_BACKUP | `backup/old_builds/layer_archives/vectora-core-bedrock-debug-v26.zip` | Version obsolète |
| `vectora-core-bedrock-only-fixed.zip` | MOVE_TO_BACKUP | `backup/old_builds/layer_archives/vectora-core-bedrock-only-fixed.zip` | Version obsolète |
| `vectora-core-bedrock-only-pure.zip` | MOVE_TO_BACKUP | `backup/old_builds/layer_archives/vectora-core-bedrock-only-pure.zip` | Version obsolète |
| `vectora-core-bedrock-only.zip` | MOVE_TO_BACKUP | `backup/old_builds/layer_archives/vectora-core-bedrock-only.zip` | Version obsolète |
| `vectora-core-bedrock-pure-v20.zip` | MOVE_TO_BACKUP | `backup/old_builds/layer_archives/vectora-core-bedrock-pure-v20.zip` | Version obsolète |
| `vectora-core-bedrock-pure-v21.zip` | MOVE_TO_BACKUP | `backup/old_builds/layer_archives/vectora-core-bedrock-pure-v21.zip` | Version obsolète |
| `vectora-core-bedrock-pure-v22.zip` | MOVE_TO_BACKUP | `backup/old_builds/layer_archives/vectora-core-bedrock-pure-v22.zip` | Version obsolète |
| `vectora-core-bedrock-pure-v23.zip` | MOVE_TO_BACKUP | `backup/old_builds/layer_archives/vectora-core-bedrock-pure-v23.zip` | Version obsolète |
| `vectora-core-bedrock-pure-v24.zip` | MOVE_TO_BACKUP | `backup/old_builds/layer_archives/vectora-core-bedrock-pure-v24.zip` | Version obsolète |
| `vectora-core-complete-v27.zip` | MOVE_TO_BACKUP | `backup/old_builds/layer_archives/vectora-core-complete-v27.zip` | Version obsolète |
| `vectora-core-layer.zip` | MOVE_TO_BACKUP | `backup/old_builds/layer_archives/vectora-core-layer.zip` | Version obsolète |
| `vectora-core-matching-bedrock-v18.zip` | MOVE_TO_BACKUP | `backup/old_builds/layer_archives/vectora-core-matching-bedrock-v18.zip` | Version obsolète |
| `vectora-core-matching-supprime.zip` | MOVE_TO_BACKUP | `backup/old_builds/layer_archives/vectora-core-matching-supprime.zip` | Version obsolète |

### DEBUG_OUTPUT → MOVE_TO_DEBUG_ARCHIVE

#### Fichiers JSON de Réponse
| Élément | Action | Destination | Raison |
|---------|--------|-------------|--------|
| `debug_payload.json` | MOVE_TO_DEBUG_ARCHIVE | `backup/debug_outputs/payloads/debug_payload.json` | Payload de debug temporaire |
| `payload.json` | MOVE_TO_DEBUG_ARCHIVE | `backup/debug_outputs/payloads/payload.json` | Payload de test temporaire |
| `test_lambda_payload.json` | MOVE_TO_DEBUG_ARCHIVE | `backup/debug_outputs/payloads/test_lambda_payload.json` | Payload de test temporaire |
| `test_payload.json` | MOVE_TO_DEBUG_ARCHIVE | `backup/debug_outputs/payloads/test_payload.json` | Payload de test temporaire |

#### Réponses Lambda
| Élément | Action | Destination | Raison |
|---------|--------|-------------|--------|
| `response_final_v25.json` | MOVE_TO_DEBUG_ARCHIVE | `backup/debug_outputs/responses/response_final_v25.json` | Réponse Lambda temporaire |
| `response_ingest_lai_v4.json` | MOVE_TO_DEBUG_ARCHIVE | `backup/debug_outputs/responses/response_ingest_lai_v4.json` | Réponse Lambda temporaire |
| `response_ingest.json` | MOVE_TO_DEBUG_ARCHIVE | `backup/debug_outputs/responses/response_ingest.json` | Réponse Lambda temporaire |
| `response_normalize_final.json` | MOVE_TO_DEBUG_ARCHIVE | `backup/debug_outputs/responses/response_normalize_final.json` | Réponse Lambda temporaire |
| `response_normalize_lai_v4.json` | MOVE_TO_DEBUG_ARCHIVE | `backup/debug_outputs/responses/response_normalize_lai_v4.json` | Réponse Lambda temporaire |
| `response_normalize_v2.json` | MOVE_TO_DEBUG_ARCHIVE | `backup/debug_outputs/responses/response_normalize_v2.json` | Réponse Lambda temporaire |
| `response_normalize.json` | MOVE_TO_DEBUG_ARCHIVE | `backup/debug_outputs/responses/response_normalize.json` | Réponse Lambda temporaire |
| `response_success_v26.json` | MOVE_TO_DEBUG_ARCHIVE | `backup/debug_outputs/responses/response_success_v26.json` | Réponse Lambda temporaire |
| `response_v18.json` | MOVE_TO_DEBUG_ARCHIVE | `backup/debug_outputs/responses/response_v18.json` | Réponse Lambda temporaire |
| `response_v19_test.json` | MOVE_TO_DEBUG_ARCHIVE | `backup/debug_outputs/responses/response_v19_test.json` | Réponse Lambda temporaire |
| `response_v20.json` | MOVE_TO_DEBUG_ARCHIVE | `backup/debug_outputs/responses/response_v20.json` | Réponse Lambda temporaire |
| `response_v21_final.json` | MOVE_TO_DEBUG_ARCHIVE | `backup/debug_outputs/responses/response_v21_final.json` | Réponse Lambda temporaire |
| `response_v22_final.json` | MOVE_TO_DEBUG_ARCHIVE | `backup/debug_outputs/responses/response_v22_final.json` | Réponse Lambda temporaire |
| `response_v23_final.json` | MOVE_TO_DEBUG_ARCHIVE | `backup/debug_outputs/responses/response_v23_final.json` | Réponse Lambda temporaire |
| `response_v24_final.json` | MOVE_TO_DEBUG_ARCHIVE | `backup/debug_outputs/responses/response_v24_final.json` | Réponse Lambda temporaire |
| `response_v24_success.json` | MOVE_TO_DEBUG_ARCHIVE | `backup/debug_outputs/responses/response_v24_success.json` | Réponse Lambda temporaire |
| `response_v24_test.json` | MOVE_TO_DEBUG_ARCHIVE | `backup/debug_outputs/responses/response_v24_test.json` | Réponse Lambda temporaire |
| `response_v25_final.json` | MOVE_TO_DEBUG_ARCHIVE | `backup/debug_outputs/responses/response_v25_final.json` | Réponse Lambda temporaire |
| `response_v25_no_layer.json` | MOVE_TO_DEBUG_ARCHIVE | `backup/debug_outputs/responses/response_v25_no_layer.json` | Réponse Lambda temporaire |
| `response_v25_success.json` | MOVE_TO_DEBUG_ARCHIVE | `backup/debug_outputs/responses/response_v25_success.json` | Réponse Lambda temporaire |
| `response_v25_test.json` | MOVE_TO_DEBUG_ARCHIVE | `backup/debug_outputs/responses/response_v25_test.json` | Réponse Lambda temporaire |
| `response.json` | MOVE_TO_DEBUG_ARCHIVE | `backup/debug_outputs/responses/response.json` | Réponse Lambda temporaire |

#### Logs
| Élément | Action | Destination | Raison |
|---------|--------|-------------|--------|
| `lambda_logs.txt` | MOVE_TO_DEBUG_ARCHIVE | `backup/debug_outputs/logs/lambda_logs.txt` | Logs Lambda temporaires |

---

## 🚫 ÉLÉMENTS NON TOUCHÉS

### CORE (Préservation totale)
- Tous les dossiers et fichiers critiques listés dans l'inventaire
- Aucune action sur ces éléments

### TO_REVIEW (Analyse manuelle requise)
- 32 éléments marqués pour révision manuelle
- Aucune action automatique sur ces éléments
- Analyse ultérieure nécessaire pour déterminer s'ils sont des doublons

---

## 📊 RÉSUMÉ DES ACTIONS

| Type d'Action | Nombre d'éléments | Taille estimée | Destination |
|---------------|-------------------|----------------|-------------|
| **MOVE_TO_LAYER_ARCHIVE** | 2 éléments | ~50MB | `layer_management/archive/` |
| **MOVE_TO_BACKUP** | 25 éléments | ~500MB | `backup/old_builds/` |
| **MOVE_TO_DEBUG_ARCHIVE** | 25 éléments | ~5MB | `backup/debug_outputs/` |
| **NO_ACTION** | 48 éléments | N/A | Restent en place |

---

## ⚠️ PRÉCAUTIONS DE SÉCURITÉ

### Avant Exécution
1. **Vérifier** que layer vectora-core version 6 est bien active
2. **Confirmer** que workflow lai_weekly_v4 fonctionne
3. **Sauvegarder** état actuel si nécessaire

### Pendant Exécution
1. **Créer** dossiers de destination avant déplacement
2. **Vérifier** chaque déplacement réussi
3. **Arrêter** en cas d'erreur

### Après Exécution
1. **Tester** workflow lai_weekly_v4
2. **Vérifier** que aucun élément CORE n'a été modifié
3. **Documenter** résultats dans rapport final

---

## 🎯 VALIDATION POST-NETTOYAGE

### Tests Obligatoires
- [ ] Workflow lai_weekly_v4 fonctionne
- [ ] Layer vectora-core version 6 active
- [ ] Aucun fichier CORE modifié
- [ ] Tous les éléments déplacés sont accessibles

### Métriques de Succès
- **Racine nettoyée** : 52 éléments déplacés
- **Éléments préservés** : 48 éléments intacts
- **Workflow fonctionnel** : lai_weekly_v4 opérationnel
- **Rollback possible** : Tous éléments récupérables

---

**Plan de Nettoyage Repo V1**  
**Approche ultra-conservatrice - Déplacements uniquement**  
**Prochaine étape : Exécution Phase 3**