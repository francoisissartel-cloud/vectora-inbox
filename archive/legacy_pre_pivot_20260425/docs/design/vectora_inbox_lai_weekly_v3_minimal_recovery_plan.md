# Vectora Inbox LAI Weekly v3 - Plan Correctif Minimal

**Date** : 2025-12-11  
**Objectif** : Workflow end-to-end pleinement fonctionnel pour lai_weekly_v3  
**Basé sur** : Audit Phase 0 + Timeout engine 300s (104 items normalisés)

---

## Résumé Exécutif

**Problème critique** : Timeout Lambda engine après 300s empêche génération newsletter  
**Solution minimale** : Résoudre timeout + valider workflow complet  
**Périmètre** : Corrections strictement nécessaires, pas d'optimisation

---

## Plan par Phases

### **Phase 1 - Diagnostic technique engine (timeout)**

**Objectif** : Identifier cause racine du timeout 300s

**Fichiers/Ressources concernés** :
- CloudWatch Logs : `vectora-inbox-engine-dev`
- Request ID : `62072987-7726-4e14-9f8a-fa9a333b3ceb`
- Configuration Lambda : Timeout, Memory, Runtime

**Actions prévues** :
1. Analyser logs CloudWatch pour identifier point de blocage
2. Mesurer temps passé par bloc (matching, scoring, newsletter generation)
3. Identifier si timeout vient de limite configurée ou anomalie code
4. Déterminer cause racine : volume (104 items), appels Bedrock, boucle, autre

**Critères de succès** :
- Cause racine identifiée avec précision
- Recommandation technique claire (timeout config vs code fix)
- Temps estimé par phase du pipeline

**Livrable** : `docs/diagnostics/vectora_inbox_lai_weekly_v3_phase2_engine_timeout_diagnostic.md`

---

### **Phase 2 - Corrections minimales + déploiement**

**Objectif** : Appliquer uniquement corrections critiques identifiées Phase 1

**Fichiers/Ressources concernés** :
- Configuration Lambda : `vectora-inbox-engine-dev` (timeout/memory)
- Code runtime si nécessaire : `src/vectora_core/` 
- Scripts déploiement : `scripts/`
- AWS DEV : Config S3 + Lambdas

**Actions prévues** :
1. **Si timeout config** : Augmenter timeout Lambda à 900s (15 min max AWS)
2. **Si anomalie code** : Corriger comportement bloquant identifié
3. **Si désync config** : Synchroniser canonical config repo → AWS S3
4. Redéployer runtime + config vers AWS DEV
5. Valider déploiement (versions, configuration)

**Critères de succès** :
- Lambda engine ne timeout plus sur 104 items
- Configuration AWS synchronisée avec repo local
- Aucune régression fonctionnelle

**Livrable** : `docs/diagnostics/vectora_inbox_lai_weekly_v3_phase3_minimal_fixes_and_deployment.md`

---

### **Phase 3 - Run end-to-end réel lai_weekly_v3**

**Objectif** : Workflow complet fonctionnel en conditions réelles

**Fichiers/Ressources concernés** :
- Lambda : `vectora-inbox-ingest-normalize-dev`
- Lambda : `vectora-inbox-engine-dev`
- Client config : `lai_weekly_v3`
- S3 buckets : Input/Output/Config

**Actions prévues** :
1. **Ingestion/Normalisation** (si pas déjà fait sur période voulue)
   - Payload : `{"client_id":"lai_weekly_v3","period_days":30}`
   - Validation : Items normalisés disponibles S3
   
2. **Engine/Newsletter**
   - Payload cohérent avec client_config v3
   - Validation : Newsletter générée S3 + pas de timeout
   
3. **Métriques end-to-end**
   - Items ingérés/normalisés
   - Items matchés par engine
   - Items sélectionnés newsletter
   - Taille/chemin newsletter S3

**Critères de succès** :
- ✅ Ingestion : 100+ items normalisés
- ✅ Engine : Pas de timeout, newsletter générée
- ✅ Newsletter : Fichier S3 avec contenu réel
- ✅ Métriques : Pipeline complet documenté

**Livrable** : `docs/diagnostics/vectora_inbox_lai_weekly_v3_phase4_e2e_run1_results.md`

---

### **Phase 4 - Synthèse finale (fonctionnel vs optimisation)**

**Objectif** : Diagnostic final et recommandations sans implémentation

**Fichiers/Ressources concernés** :
- Résultats Phase 3
- Newsletter générée
- Métriques performance/coût

**Actions prévues** :
1. Analyser qualité newsletter générée
2. Documenter métriques clés workflow
3. Identifier points d'optimisation futurs (SANS les implémenter)
4. Recommandation : "OK pour continuer" ou "Blocage critique restant"

**Critères de succès** :
- Newsletter réelle générée et analysée
- Workflow end-to-end fonctionnel documenté
- Roadmap optimisation claire (pour plus tard)

**Livrable** : `docs/diagnostics/vectora_inbox_lai_weekly_v3_minimal_recovery_executive_summary.md`

---

## Contraintes d'Exécution

### **Minimalisme Strict**
- ✅ Corriger uniquement ce qui bloque le workflow
- ❌ Pas d'optimisation qualité métier (scoring fin, mots-clés, etc.)
- ❌ Pas de refactoring code non critique
- ❌ Pas d'ajout fonctionnalités

### **Conditions Réelles**
- ✅ Tous appels AWS réels (pas de simulation)
- ✅ Données fraîches (pas d'anciens fichiers)
- ✅ Métriques authentiques du run

### **Environnement AWS**
- **Profil** : `rag-lai-prod`
- **Région** : `eu-west-3`
- **Client** : `lai_weekly_v3`
- **Period_days** : Valeur définie dans client_config v3

---

## Critères de Succès Global

### **Workflow Fonctionnel**
- ✅ Ingestion → Normalisation : 100+ items
- ✅ Engine → Newsletter : Pas timeout, fichier généré
- ✅ End-to-end : < 20 minutes total
- ✅ Coût : < $2/run

### **Qualité Minimale**
- ✅ Newsletter contient items LAI pertinents
- ✅ Pas de crash/erreur bloquante
- ✅ Métriques cohérentes

### **Prêt pour Optimisation**
- ✅ Base technique stable
- ✅ Workflow reproductible
- ✅ Roadmap optimisation documentée

---

## Séquence d'Exécution

1. **Phase 1** : Diagnostic technique → Cause racine timeout
2. **Phase 2** : Corrections minimales → Déploiement AWS
3. **Phase 3** : Run end-to-end → Newsletter générée
4. **Phase 4** : Synthèse → Recommandations

**Durée estimée** : 2-4 heures (selon complexité timeout)

**Point d'arrêt** : Si Phase 3 échoue, documenter échec et s'arrêter (pas de simulation)

---

## Livrables

1. `docs/diagnostics/vectora_inbox_lai_weekly_v3_phase2_engine_timeout_diagnostic.md`
2. `docs/diagnostics/vectora_inbox_lai_weekly_v3_phase3_minimal_fixes_and_deployment.md`
3. `docs/diagnostics/vectora_inbox_lai_weekly_v3_phase4_e2e_run1_results.md`
4. `docs/diagnostics/vectora_inbox_lai_weekly_v3_minimal_recovery_executive_summary.md`

---

**Plan rédigé - Prêt pour exécution Phase 2**