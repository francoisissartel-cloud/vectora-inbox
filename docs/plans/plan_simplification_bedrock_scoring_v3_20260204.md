# Plan de Développement - Simplification Bedrock Scoring V3

**Date**: 2026-02-04  
**Objectif**: Simplifier système de prompts Bedrock scoring/matching LAI - Éliminer complexité pure_player/hybrid, passer à prompt flat résolu  
**Durée estimée**: 4-6 heures  
**Risque**: Moyen (modification logique scoring core)  
**Environnements impactés**: dev

---

## 🎯 Contexte et Justification

**Besoin métier**: 
- Système actuel trop complexe: distinction pure_player vs hybrid_company introduit granularité inutile
- Références dynamiques non résolues créent fragilité
- Difficile d'itérer sur feedback (faux positifs/négatifs)
- Maintenance dispersée sur 8+ fichiers

**Impact attendu**: 
- Prompt flat simple, complet, optimisé tokens
- Feedback loop rapide: modifier scope → rebuild prompt → test → commit
- Traçabilité: 1 version prompt = 1 snapshot complet règles
- Scalable: extension future à siRNA, cell therapy, gene therapy

**Contraintes**: 
- Maintenir ou améliorer métriques baseline V17 (64% relevant, score 71.5)
- Pas de régression sur faux négatifs
- Compatible architecture 3 Lambdas V2

---

## 📋 MANIFEST - Fichiers Impactés

### Nouveaux Fichiers
- [ ] `scripts/prompts/build_lai_scoring_prompt.py` - Générateur prompt flat
- [ ] `canonical/prompts/generated/lai_scoring_bedrock_v3.txt` - Prompt flat généré
- [ ] `docs/reports/development/simplification_bedrock_scoring_v3_rapport_20260204.md` - Rapport final

### Fichiers Modifiés
- [ ] `src_v2/vectora_core/normalization/bedrock_scorer.py` - Charger prompt flat au lieu de YAML avec références
- [ ] `VERSION` - Incrément version (actuelle → +0.0.1)

### Fichiers Référencés (lecture seule)
- [ ] `canonical/scopes/technology_scopes.yaml` - Source termes LAI
- [ ] `canonical/scopes/trademark_scopes.yaml` - Source trademarks LAI
- [ ] `canonical/scopes/exclusion_scopes.yaml` - Source exclusions

### Fichiers Archivés (backup)
- [ ] `canonical/prompts/domain_scoring/lai_domain_scoring.yaml` → backup
- [ ] `canonical/domains/lai_domain_definition.yaml` → backup

### Impact S3
- [ ] Upload: `s3://vectora-inbox-config-dev/canonical/prompts/generated/lai_scoring_bedrock_v3.txt`
- [ ] Backup S3: `s3://vectora-inbox-config-dev/canonical/` avant modifications

### Tests
- [ ] Test local: génération prompt
- [ ] Test local: scoring avec prompt flat
- [ ] Test AWS E2E: lai_weekly_v18 vs baseline V17

### Rollback
- Backup local: `.backup/20260204_HHMMSS_avant_simplification_scoring_v3/`
  - Contient: `src_v2/`, `canonical/`, `VERSION`
- Backup S3: `.tmp/backup_canonical_20260204_HHMMSS/`
- Commandes restore documentées

---

## 📋 Plan d'Exécution

### Phase 0: Cadrage ⏱️ 30 min

**Actions**:
- [ ] Lire CRITICAL_RULES.md (règles 1-10)
- [ ] Analyser système actuel:
  - [ ] `canonical/prompts/domain_scoring/lai_domain_scoring.yaml`
  - [ ] `canonical/domains/lai_domain_definition.yaml`
  - [ ] `src_v2/vectora_core/normalization/bedrock_scorer.py`
- [ ] Identifier logique à simplifier:
  - [ ] Éliminer distinction pure_player/hybrid
  - [ ] Éliminer références dynamiques non résolues
  - [ ] Consolider règles matching en logique simple
- [ ] Valider prérequis:
  - [ ] Python 3.11+
  - [ ] AWS CLI configuré (profil rag-lai-prod)
  - [ ] Accès S3 buckets dev

**Livrables Phase 0**:
- [ ] Analyse d'impact documentée (ce plan)
- [ ] Liste prérequis validés
- [ ] Logique simplifiée définie

**✋ CHECKPOINT**: Validation utilisateur avant Phase 1

---

### Phase 1: Préparation ⏱️ 15 min

**Actions**:
- [ ] **Backup local OBLIGATOIRE** (règle critique #3 - backup src_v2/ + canonical/ + VERSION):
  ```bash
  python scripts/backup/create_local_backup.py --description "Avant simplification scoring v3"
  ```
  **Note**: Ce script backup automatiquement:
  - `src_v2/` (code Lambda modifié en Phase 3)
  - `canonical/` (prompts générés en Phase 2)
  - `VERSION` (incrémenté en Phase 3)
- [ ] Vérifier backup créé:
  ```bash
  python scripts/backup/list_backups.py
  ```
- [ ] **Backup S3 canonical** (règle critique #5):
  ```bash
  aws s3 sync s3://vectora-inbox-config-dev/canonical/ .tmp/backup_canonical_$(date +%Y%m%d_%H%M%S)/ --profile rag-lai-prod --region eu-west-3
  ```
- [ ] Créer dossier prompts generated:
  ```bash
  mkdir canonical\prompts\generated
  ```
- [ ] Documenter backup dans MANIFEST (ci-dessus)

**Livrables Phase 1**:
- [ ] Backup local créé et vérifié
- [ ] Backup S3 canonical créé
- [ ] Environnement prêt

**✋ CHECKPOINT**: Validation utilisateur avant Phase 2

---

### Phase 2: Implémentation Générateur Prompt ⏱️ 45 min

**Actions**:
- [ ] Créer `scripts/prompts/build_lai_scoring_prompt.py`:
  - [ ] Charger scopes YAML (technology, trademark, exclusion)
  - [ ] Extraire termes par catégorie (core, tech, intervals, trademarks, exclusions)
  - [ ] Construire prompt flat avec:
    - [ ] Header (version, date, sources)
    - [ ] Mission et définition LAI
    - [ ] Matching logic (strong/medium/exclusions)
    - [ ] Scoring rules (base scores, boosts, recency)
    - [ ] Critical rules (pas de distinction company type)
    - [ ] Output format (JSON)
    - [ ] Full term lists (tous les termes expandés)
  - [ ] Sauvegarder dans `canonical/prompts/generated/lai_scoring_bedrock_v3.txt`
  - [ ] Logger stats (nombre termes par catégorie)
- [ ] Test local générateur:
  ```bash
  python scripts/prompts/build_lai_scoring_prompt.py
  ```
- [ ] Vérifier prompt généré:
  - [ ] Fichier créé
  - [ ] Format correct
  - [ ] Tous les termes présents
  - [ ] Taille raisonnable (< 10K tokens)

**Livrables Phase 2**:
- [ ] Générateur créé et testé
- [ ] Prompt flat v3.0 généré
- [ ] Stats termes validées

**✋ CHECKPOINT**: Validation utilisateur avant Phase 3

---

### Phase 3: Modification Lambda Scorer ⏱️ 30 min

**Actions**:
- [ ] Modifier `src_v2/vectora_core/normalization/bedrock_scorer.py`:
  - [ ] Ajouter fonction `load_scoring_prompt_flat(s3_client, config_bucket)`:
    - [ ] Charger depuis S3: `canonical/prompts/generated/lai_scoring_bedrock_v3.txt`
    - [ ] Retourner string prompt complet
  - [ ] Modifier fonction `score_item_with_bedrock()`:
    - [ ] Accepter `prompt_template: str` (prompt flat)
    - [ ] Construire user_message avec item data
    - [ ] Utiliser prompt_template comme system message Bedrock
    - [ ] Parser réponse JSON
  - [ ] Modifier orchestration:
    - [ ] Charger prompt flat une fois au début
    - [ ] Passer prompt à chaque appel scoring
- [ ] Incrémenter `VERSION`:
  - [ ] Lire version actuelle
  - [ ] +0.0.1 (patch)
  - [ ] Écrire nouvelle version
- [ ] Test syntaxe:
  ```bash
  python -m py_compile src_v2/vectora_core/normalization/bedrock_scorer.py
  ```

**Livrables Phase 3**:
- [ ] bedrock_scorer.py modifié
- [ ] VERSION incrémentée
- [ ] Syntaxe validée

**✋ CHECKPOINT**: Validation utilisateur avant Phase 4

---

### Phase 4: Tests Locaux ⏱️ 45 min

**Actions**:
- [ ] Créer test local générateur:
  ```bash
  python scripts/prompts/build_lai_scoring_prompt.py
  ```
  - [ ] Vérifier prompt généré
  - [ ] Compter termes (core: 13, tech: 58, intervals: 15, trademarks: 78, exclusions: 25)
- [ ] Test local scoring (si script test existe):
  - [ ] Charger prompt flat
  - [ ] Scorer 3-5 items test
  - [ ] Vérifier format réponse JSON
  - [ ] Vérifier logique matching (strong/medium/exclusions)
- [ ] Validation manuelle prompt:
  - [ ] Lire prompt généré
  - [ ] Vérifier clarté instructions
  - [ ] Vérifier tous termes présents
  - [ ] Vérifier règles critiques (pas distinction company type)

**Livrables Phase 4**:
- [ ] Générateur validé localement
- [ ] Prompt flat validé manuellement
- [ ] Logique scoring testée (si possible)

**✋ CHECKPOINT**: Validation utilisateur avant Phase 5

---

### Phase 5: Déploiement Dev ⏱️ 30 min

**Actions**:
- [ ] Upload prompt flat vers S3:
  ```bash
  aws s3 cp canonical/prompts/generated/lai_scoring_bedrock_v3.txt s3://vectora-inbox-config-dev/canonical/prompts/generated/lai_scoring_bedrock_v3.txt --profile rag-lai-prod --region eu-west-3
  ```
- [ ] Build layers (règle critique #5):
  ```bash
  python scripts/build/build_all.py
  ```
- [ ] Deploy dev (règle critique #4 - env explicite):
  ```bash
  python scripts/deploy/deploy_env.py --env dev
  ```
- [ ] Vérifier déploiement:
  - [ ] Logs CloudFormation
  - [ ] Lambda versions mises à jour
  - [ ] Variables environnement correctes

**Livrables Phase 5**:
- [ ] Prompt flat sur S3 dev
- [ ] Layers buildées
- [ ] Lambda déployée dev

**✋ CHECKPOINT**: Validation utilisateur avant Phase 6

---

### Phase 6: Test E2E AWS Dev ⏱️ 60 min

**Actions**:
- [ ] Créer nouveau client_id test (règle critique #7):
  - [ ] `lai_weekly_v18` (incrément depuis V17 baseline)
- [ ] Créer config client (copie lai_weekly_v7.yaml):
  ```bash
  cp canonical/clients/lai_weekly_v7.yaml canonical/clients/lai_weekly_v18.yaml
  ```
- [ ] Upload config client:
  ```bash
  aws s3 cp canonical/clients/lai_weekly_v18.yaml s3://vectora-inbox-config-dev/canonical/clients/lai_weekly_v18.yaml --profile rag-lai-prod --region eu-west-3
  ```
- [ ] Exécuter workflow E2E complet:
  ```bash
  # Ingest
  aws lambda invoke --function-name vectora-inbox-ingest-v2-dev --payload "{\"client_id\":\"lai_weekly_v18\"}" .tmp/ingest_v18_response.json --profile rag-lai-prod --region eu-west-3
  
  # Normalize (asynchrone - attendre 5-10 min)
  aws lambda invoke --function-name vectora-inbox-normalize-score-v2-dev --invocation-type Event --payload "{\"client_id\":\"lai_weekly_v18\"}" .tmp/normalize_v18_response.json --profile rag-lai-prod --region eu-west-3
  
  # Attendre 10 min
  
  # Télécharger résultats
  aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v18/2026/02/04/items.json .tmp/v18_curated.json --profile rag-lai-prod
  ```
- [ ] Analyser résultats V18:
  ```bash
  python -c "import json; items=json.load(open('.tmp/v18_curated.json', encoding='utf-8')); with_ds=sum(1 for i in items if i.get('has_domain_scoring')); relevant=sum(1 for i in items if i.get('domain_scoring',{}).get('is_relevant')); companies=sum(1 for i in items if i.get('normalized_content',{}).get('entities',{}).get('companies')); scores=[i.get('domain_scoring',{}).get('score',0) for i in items if i.get('has_domain_scoring')]; print(f'Items: {len(items)}'); print(f'Domain scoring: {with_ds}/{len(items)} ({with_ds/len(items)*100:.0f}%)'); print(f'Companies: {companies}/{len(items)} ({companies/len(items)*100:.0f}%)'); print(f'Relevant: {relevant}/{with_ds} ({relevant/with_ds*100:.0f}%)'); print(f'Score moyen: {sum(scores)/len(scores):.1f}')"
  ```
- [ ] Comparer vs baseline V17 (voir GOLDEN_TEST_E2E.md):
  - [ ] Items ingérés: V18 vs V17 (31)
  - [ ] Companies: V18 vs V17 (74%)
  - [ ] Items relevant: V18 vs V17 (64%)
  - [ ] Score moyen: V18 vs V17 (71.5)
  - [ ] Faux négatifs: V18 vs V17 (0)
  - [ ] Domain scoring: V18 vs V17 (100%)

**Livrables Phase 6**:
- [ ] Test E2E V18 exécuté
- [ ] Résultats analysés
- [ ] Comparaison vs V17 documentée

**Verdict**:
- ✅ SUCCÈS: Toutes métriques >= seuils V17
- ⚠️ ATTENTION: 1-2 métriques < seuils
- ❌ ÉCHEC: 3+ métriques < seuils

**✋ CHECKPOINT**: Validation utilisateur avant Phase 7

---

### Phase 7: Rapport et Finalisation ⏱️ 30 min

**Actions**:
- [ ] Créer rapport final `docs/reports/development/simplification_bedrock_scoring_v3_rapport_20260204.md`:
  - [ ] Résumé exécutif (verdict)
  - [ ] Métriques comparatives V17 vs V18
  - [ ] Distribution sources/scores
  - [ ] Top 5 items relevant
  - [ ] Analyse faux négatifs (si présents)
  - [ ] Recommandations
  - [ ] Annexes (fichiers, commandes, versions)
- [ ] Si SUCCÈS:
  - [ ] Archiver backup:
    ```bash
    python scripts/backup/archive_backup.py --backup-id YYYYMMDD_HHMMSS --success
    ```
  - [ ] Commit et push:
    ```bash
    git add .
    git commit -m "feat: Simplification Bedrock scoring V3 - Prompt flat résolu, élimination pure_player/hybrid"
    git push
    ```
  - [ ] Documenter dans ce plan: statut TERMINÉ
- [ ] Si ÉCHEC:
  - [ ] Analyser causes (logs Lambda, réponses Bedrock)
  - [ ] Rollback local:
    ```bash
    python scripts/backup/restore_backup.py --backup-id YYYYMMDD_HHMMSS
    ```
  - [ ] Rollback S3:
    ```bash
    aws s3 sync .tmp/backup_canonical_YYYYMMDD_HHMMSS/ s3://vectora-inbox-config-dev/canonical/ --profile rag-lai-prod --region eu-west-3
    ```
  - [ ] Documenter causes échec
  - [ ] Recommencer Phase 2-3 avec corrections

**Livrables Phase 7**:
- [ ] Rapport final créé
- [ ] Backup archivé (si succès)
- [ ] Code commité (si succès)
- [ ] Rollback effectué (si échec)

---

## ✅ Critères de Succès

**Fonctionnels**:
- [ ] Prompt flat généré automatiquement depuis scopes YAML
- [ ] Lambda charge prompt flat depuis S3
- [ ] Scoring fonctionne avec prompt flat (pas de références dynamiques)
- [ ] Logique simplifiée: pas de distinction pure_player/hybrid

**Techniques**:
- [ ] Générateur Python fonctionnel
- [ ] Prompt flat < 10K tokens
- [ ] Tous termes scopes présents dans prompt
- [ ] Format JSON réponse Bedrock valide

**Performance**:
- [ ] Métriques V18 >= seuils V17:
  - [ ] Items relevant: >= 64%
  - [ ] Score moyen: >= 71.5
  - [ ] Faux négatifs: 0
  - [ ] Domain scoring: 100%
- [ ] Aucune régression détectée

**Gouvernance**:
- [ ] Tests local avant AWS (règle #6)
- [ ] Backup local créé (règle #3)
- [ ] Environnement explicite (règle #4)
- [ ] Déploiement complet code + data + test (règle #5)
- [ ] Code dans src_v2/ (règle #2)
- [ ] Temporaires dans .tmp/ (règle #9)

---

## 🚨 Plan de Rollback

**En cas de problème critique**:

1. **Stop immédiat** de l'exécution
2. **Diagnostic rapide** (< 10 min):
   - [ ] Logs Lambda CloudWatch
   - [ ] Réponses Bedrock (.tmp/normalize_v18_response.json)
   - [ ] Erreurs S3 (prompt flat manquant?)
3. **Rollback local**:
   ```bash
   python scripts/backup/restore_backup.py --backup-id YYYYMMDD_HHMMSS
   ```
4. **Rollback S3 canonical**:
   ```bash
   aws s3 sync .tmp/backup_canonical_YYYYMMDD_HHMMSS/ s3://vectora-inbox-config-dev/canonical/ --profile rag-lai-prod --region eu-west-3
   ```
5. **Rollback Lambda** (si nécessaire):
   ```bash
   # Redéployer version précédente
   python scripts/deploy/deploy_env.py --env dev --version [VERSION_PRECEDENTE]
   ```
6. **Analyse post-mortem** et plan correctif

**Commandes rollback rapide**:
```bash
# Restaurer backup local
python scripts/backup/restore_backup.py --backup-id [ID_BACKUP]

# Restaurer S3 canonical
aws s3 sync .tmp/backup_canonical_[TIMESTAMP]/ s3://vectora-inbox-config-dev/canonical/ --profile rag-lai-prod --region eu-west-3

# Rebuild et redeploy version précédente
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev
```

---

## 📊 Métriques et Suivi

**Métriques à surveiller**:
- [ ] Temps génération prompt: < 5 sec
- [ ] Taille prompt flat: < 10K tokens
- [ ] Temps scoring Bedrock: < 3 sec/item (inchangé)
- [ ] Taux succès Bedrock: 100%
- [ ] Métriques métier V18 vs V17

**Baseline V17 (référence)**:
```
Items ingérés:       31
Companies:           74%
Items relevant:      64%
Score moyen:         71.5
Faux négatifs:       0
Domain scoring:      100%
```

**Suivi post-déploiement**:
- [ ] Monitoring 24h logs Lambda
- [ ] Validation métriques métier
- [ ] Feedback utilisateur sur qualité scoring

---

## 📝 Notes et Observations

**Décisions prises**:
1. **Prompt flat vs références dynamiques**: Flat choisi pour simplicité, traçabilité, performance
2. **Élimination pure_player/hybrid**: Focus sur signaux LAI uniquement, pas type entreprise
3. **Générateur Python**: Automatisation rebuild prompt après modification scopes
4. **Version prompt**: v3.0 (breaking change logique scoring)

**Points d'attention**:
1. **Taille prompt**: Surveiller tokens, optimiser si > 10K
2. **Feedback loop**: Tester cycle complet (modifier scope → rebuild → test)
3. **Compatibilité**: Vérifier pas de régression sur items edge cases
4. **Documentation**: Maintenir guide utilisation générateur

**Améliorations futures**:
1. **Multi-domaines**: Template générique pour siRNA, cell therapy, gene therapy
2. **Versioning prompt**: Système versions automatique (v3.0, v3.1, v3.2...)
3. **CI/CD**: Hook pre-commit pour rebuild prompt si scopes modifiés
4. **Métriques**: Dashboard comparaison versions prompts

---

## 🔄 Workflow Feedback Loop (Post-Déploiement)

**Cycle d'amélioration continue**:

1. **Run E2E hebdomadaire**:
   ```bash
   # Nouveau client_id chaque semaine
   python scripts/invoke/invoke_e2e_workflow.py --client-id lai_weekly_v19 --env dev
   ```

2. **Analyser résultats**:
   - [ ] Identifier 5-10 faux positifs
   - [ ] Identifier 5-10 faux négatifs
   - [ ] Documenter patterns

3. **Ajuster scopes**:
   - [ ] Ajouter termes manquants dans `technology_scopes.yaml`
   - [ ] Ajouter exclusions dans `exclusion_scopes.yaml`
   - [ ] Ajouter trademarks dans `trademark_scopes.yaml`

4. **Rebuild prompt**:
   ```bash
   python scripts/prompts/build_lai_scoring_prompt.py
   ```

5. **Test local**:
   - [ ] Vérifier prompt généré
   - [ ] Compter nouveaux termes

6. **Deploy et test**:
   ```bash
   aws s3 cp canonical/prompts/generated/lai_scoring_bedrock_v3.txt s3://vectora-inbox-config-dev/canonical/prompts/generated/lai_scoring_bedrock_v3.txt --profile rag-lai-prod --region eu-west-3
   python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v19 --env dev
   ```

7. **Valider amélioration**:
   - [ ] Comparer métriques v19 vs v18
   - [ ] Mesurer réduction faux positifs/négatifs

8. **Commit**:
   ```bash
   git add canonical/scopes/ canonical/prompts/generated/
   git commit -m "feat: Ajout termes X, Y, Z - Fix faux positifs A, B"
   git push
   ```

**Traçabilité Git**:
```bash
# Historique modifications prompt
git log --oneline canonical/prompts/generated/lai_scoring_bedrock_v3.txt

# Diff entre versions
git diff v3.0..v3.1 canonical/prompts/generated/lai_scoring_bedrock_v3.txt
```

---

**Plan créé le**: 2026-02-04  
**Dernière mise à jour**: 2026-02-04  
**Statut**: EN ATTENTE VALIDATION UTILISATEUR - Phase 0 complétée
