# Plan Diagnostic - Régression Matching Post Canonical v2.2

**Date**: 2026-02-03  
**Problème**: Matching fonctionnel v13 → 0% matching v14 après plan amélioration  
**Objectif**: Identifier la cause de la régression

---

## 📋 CONTEXTE

### Avant (E2E v13 - Matin)

**Rapport**: `retour admin run test_e2e_v13_analyse_complete_29_items_2026-02-03.md`

- ✅ Matching fonctionnel
- ✅ Items matchés avec succès
- ✅ Scores cohérents

### Après (E2E v14 - Après-midi)

**Plan appliqué**: `plan_amelioration_canonical_e2e_v13_FINAL_2026-02-03.md`

- ❌ 0% matching (v12 et v14)
- ❌ Scores très bas (max 3.3 vs attendu 25+)
- ❌ 0 companies détectées
- ❌ 0 technologies détectées

---

## 🔍 HYPOTHÈSES À VÉRIFIER

### Hypothèse 1: Fichiers Canonical Manquants/Incorrects sur S3

**Probabilité**: ÉLEVÉE

**À vérifier**:
1. Tous les fichiers canonical v2.2 sont-ils sur S3 dev?
2. Les contenus correspondent-ils aux fichiers locaux?
3. Y a-t-il des fichiers corrompus ou tronqués?

**Actions**:
```bash
# Comparer tailles fichiers local vs S3
aws s3 ls s3://vectora-inbox-config-dev/canonical/ --recursive --profile rag-lai-prod --region eu-west-3

# Télécharger et comparer checksums
aws s3 cp s3://vectora-inbox-config-dev/canonical/domains/lai_domain_definition.yaml ./s3_lai_domain.yaml
diff canonical/domains/lai_domain_definition.yaml ./s3_lai_domain.yaml
```

### Hypothèse 2: Modifications Canonical Trop Strictes

**Probabilité**: ÉLEVÉE

**À vérifier**:
1. `financial_results` base_score = 0 → Combien d'items financial_results?
2. `hybrid_company` boost = 0 → Combien d'items hybrid sans signaux?
3. Exclusions manufacturing → Combien d'items exclus?
4. Règles rule_5 et rule_6 → Combien d'items rejetés?

**Actions**:
```bash
# Analyser 1 item normalisé pour voir les champs
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v14/2026/02/03/items.json ./
cat items.json | jq '.[0] | {event_type, companies_detected, technologies_detected, domain_scoring}'
```

### Hypothèse 3: Problème de Normalisation (Entités Non Détectées)

**Probabilité**: TRÈS ÉLEVÉE

**Observation**: 0 companies + 0 technologies détectées

**À vérifier**:
1. Le prompt `generic_normalization.yaml` fonctionne-t-il?
2. Les champs `dosing_intervals_detected` sont-ils extraits?
3. Le champ `title` est-il présent?
4. Bedrock retourne-t-il les bonnes entités?

**Actions**:
```bash
# Vérifier structure item normalisé
cat items.json | jq '.[0] | keys'
cat items.json | jq '.[0] | {title, companies_detected, technologies_detected, dosing_intervals_detected}'
```

### Hypothèse 4: Problème de Domain Scoring (Calcul Scores)

**Probabilité**: MOYENNE

**À vérifier**:
1. Le prompt `lai_domain_scoring.yaml` est-il correct sur S3?
2. Les CRITICAL RULES sont-elles appliquées?
3. Le boost conditionnel hybrid_company fonctionne-t-il?
4. Les scores sont-ils calculés avec la bonne formule?

**Actions**:
```bash
# Vérifier domain_scoring dans items
cat items.json | jq '.[0].domain_scoring | {is_relevant, score, confidence, signals_detected, score_breakdown}'
```

### Hypothèse 5: Données v13 Incompatibles

**Probabilité**: FAIBLE

**À vérifier**:
1. Les données v13 ont-elles été normalisées avec quel canonical?
2. Y a-t-il un cache ou des données pré-calculées?
3. Les items sont-ils corrompus?

**Actions**:
```bash
# Vérifier métadonnées items v13
cat items.json | jq '.[0] | {source_key, ingestion_date, normalization_version}'
```

### Hypothèse 6: Lambda Utilise Ancien Canonical (Cache)

**Probabilité**: FAIBLE

**À vérifier**:
1. Lambda charge-t-elle bien canonical v2.2?
2. Y a-t-il un cache au niveau Lambda?
3. Les logs confirment-ils le chargement de v2.2?

**Actions**:
```bash
# Vérifier logs Lambda pour voir version chargée
aws logs tail /aws/lambda/vectora-inbox-normalize-score-v2-dev --since 30m --profile rag-lai-prod --region eu-west-3 | grep "lai_domain_definition"
```

---

## 🔄 PLAN D'EXÉCUTION DIAGNOSTIC

### Étape 1: Vérifier Fichiers S3 (PRIORITAIRE)

**Objectif**: Confirmer que tous les fichiers canonical v2.2 sont sur S3

**Actions**:
1. Lister tous les fichiers canonical sur S3
2. Comparer tailles avec fichiers locaux
3. Télécharger et comparer contenus clés:
   - `lai_domain_definition.yaml`
   - `generic_normalization.yaml`
   - `lai_domain_scoring.yaml`

**Critère succès**: Tous les fichiers identiques local vs S3

### Étape 2: Analyser 1 Item Normalisé (PRIORITAIRE)

**Objectif**: Comprendre pourquoi 0 companies/technologies détectées

**Actions**:
1. Télécharger items.json de v14
2. Analyser structure du 1er item
3. Vérifier présence de:
   - `title`
   - `companies_detected`
   - `technologies_detected`
   - `dosing_intervals_detected`
   - `domain_scoring.signals_detected`
   - `domain_scoring.score_breakdown`

**Critère succès**: Identifier champs manquants ou vides

### Étape 3: Comparer Item v13 (Avant) vs v14 (Après)

**Objectif**: Identifier différences de normalisation

**Actions**:
1. Télécharger 1 item de v13 (matin - fonctionnel)
2. Télécharger 1 item de v14 (après-midi - cassé)
3. Comparer structure et valeurs
4. Identifier ce qui a changé

**Critère succès**: Trouver la différence clé

### Étape 4: Vérifier Logs Lambda Détaillés

**Objectif**: Voir ce que Bedrock retourne réellement

**Actions**:
1. Récupérer logs complets du run v14
2. Chercher les réponses Bedrock pour normalisation
3. Chercher les réponses Bedrock pour domain_scoring
4. Vérifier si erreurs ou warnings

**Critère succès**: Comprendre ce que Bedrock retourne

### Étape 5: Tester avec 1 Item Isolé

**Objectif**: Reproduire le problème de manière contrôlée

**Actions**:
1. Prendre 1 item qui devrait matcher (ex: MedinCell + BEPO)
2. Le normaliser localement avec canonical v2.2
3. Comparer avec résultat AWS
4. Identifier divergence

**Critère succès**: Reproduire le problème localement

### Étape 6: Rollback Test (Si Nécessaire)

**Objectif**: Confirmer que le problème vient du plan v2.2

**Actions**:
1. Créer lai_weekly_v15 avec canonical_version: "2.1"
2. Tester avec mêmes données v13
3. Comparer résultats v14 (v2.2) vs v15 (v2.1)

**Critère succès**: v15 fonctionne, v14 ne fonctionne pas

---

## 📊 CHECKLIST DIAGNOSTIC

### Fichiers Canonical S3

- [ ] `lai_domain_definition.yaml` présent et correct
- [ ] `generic_normalization.yaml` présent et correct
- [ ] `lai_domain_scoring.yaml` présent et correct
- [ ] `exclusion_scopes.yaml` présent et correct
- [ ] `source_catalog.yaml` présent et correct
- [ ] Tous les fichiers ont la bonne taille
- [ ] Aucun fichier corrompu

### Structure Items Normalisés

- [ ] Champ `title` présent
- [ ] Champ `companies_detected` présent (et non vide?)
- [ ] Champ `technologies_detected` présent (et non vide?)
- [ ] Champ `dosing_intervals_detected` présent
- [ ] Champ `domain_scoring` présent
- [ ] Champ `domain_scoring.signals_detected` présent
- [ ] Champ `domain_scoring.score_breakdown` présent

### Scores et Matching

- [ ] Scores calculés (non null)
- [ ] Scores > 0 pour au moins quelques items
- [ ] `is_relevant` = true pour au moins quelques items
- [ ] Signaux détectés (strong/medium/weak)
- [ ] Score_breakdown cohérent

### Logs Lambda

- [ ] Canonical v2.2 chargé (8478 caractères)
- [ ] Pas d'erreurs de parsing YAML
- [ ] Bedrock répond correctement
- [ ] Pas de throttling ou timeouts

---

## 🎯 RÉSULTAT ATTENDU

À la fin de ce diagnostic, nous devons savoir:

1. **Quel fichier** est incorrect ou manquant
2. **Quelle modification** du plan a cassé le matching
3. **Comment corriger** le problème

---

## 📝 RAPPORT À PRODUIRE

**Fichier**: `diagnostic_regression_matching_v14_2026-02-03.md`

**Contenu**:
1. Cause racine identifiée
2. Fichiers/modifications problématiques
3. Comparaison avant/après
4. Plan de correction
5. Actions préventives pour éviter régression future

---

**Plan créé**: 2026-02-03  
**Durée estimée**: 30-45 minutes  
**Statut**: ⏳ EN ATTENTE VALIDATION ADMIN
