# Plan de Diagnostic Runtime - Vectora Inbox Engine vs Ingest

**Date** : 2025-12-12  
**Objectif** : Diagnostic complet et réaliste du workflow Vectora Inbox en environnement DEV  
**Focus** : Causes réelles du fallback newsletter et répartition des rôles entre Lambdas  

---

## 🎯 Objectif Global

Expliquer clairement la cause du fallback newsletter (pourquoi la newsletter ne passe pas par le chemin Bedrock "normal").
Vérifier si les deux Lambdas exécutent bien le bon code (ingest vs engine) et le bon handler.
Vérifier les permissions S3 (lecture/écriture sur les bons buckets/prefixes) et pointer les manques.
Comparer le workflow voulu vs le workflow réellement exécuté.

---

## 📋 Plan de Travail Structuré

### Phase 0 – Recap & Contexte
**Durée estimée** : 15 min  
**Objectif** : Établir la baseline du workflow attendu

- Rappeler le workflow lai_weekly_v3 attendu :
  - Ingestion + normalisation
  - Matching + scoring  
  - Génération newsletter (avec cache S3, Bedrock, fallback éventuel)
- Lister les évolutions majeures récentes :
  - Ajout de Bedrock pour matching/scoring
  - Migration Bedrock us-east-1 / eu-west-3
  - Priorités P0, P1, P3

**Livrable** : Contexte documenté dans ce plan

---

### Phase 1 – Audit Métier des Deux Lambdas (Côté Repo)
**Durée estimée** : 30 min  
**Objectif** : Analyser les responsabilités métier prévues dans le code

**Actions** :
- Analyser `src/lambdas/ingest_normalize/...`
- Analyser `src/lambdas/engine/...`
- Identifier les responsabilités métier de chaque Lambda
- Détecter les chevauchements potentiels
- Identifier les TODO/commentaires contradictoires

**Livrable** : `docs/diagnostics/vectora_inbox_engine_vs_ingest_code_responsibilities.md`

---

### Phase 2 – Audit Déploiement AWS (Handlers, Env Vars, Régions)
**Durée estimée** : 20 min  
**Objectif** : Vérifier la configuration AWS réelle des Lambdas

**Actions** :
- Pour `vectora-inbox-ingest-normalize-dev` et `vectora-inbox-engine-dev` :
  - Récupérer handler via `aws lambda get-function-configuration`
  - Vérifier rôle IAM
  - Analyser variables d'environnement (BEDROCK_MODEL_ID, BEDROCK_REGION, buckets S3)
  - Vérifier CodeSha et date de mise à jour
- Confirmer que le handler engine pointe vers le bon code

**Livrable** : `docs/diagnostics/vectora_inbox_engine_vs_ingest_lambda_config_audit.md`

---

### Phase 3 – Audit IAM & S3 (Permissions Réelles)
**Durée estimée** : 25 min  
**Objectif** : Vérifier les permissions S3 et IAM réelles

**Actions** :
- Analyser les politiques IAM attachées aux rôles des deux Lambdas
- Vérifier permissions S3 :
  - Lambda engine : s3:GetObject + s3:PutObject sur buckets data, prefixes newsletter/, cache/
  - Lambda ingest-normalize : lecture/écriture normalized/, logs d'ingestion
- Identifier permissions manquantes et doublons

**Livrable** : `docs/diagnostics/vectora_inbox_engine_vs_ingest_iam_and_s3_permissions.md`

---

### Phase 4 – Traçage d'un Run Réel lai_weekly_v3
**Durée estimée** : 45 min  
**Objectif** : Exécuter et tracer un run complet réel

**Actions** :
- Lancer run réel lai_weekly_v3 avec period_days=7
- Invocation ingestion-normalisation avec payload JSON + `--cli-binary-format raw-in-base64-out`
- Invocation engine avec même méthode
- Analyser logs CloudWatch des deux Lambdas
- Tracer :
  - Normalisation Bedrock appelée ?
  - Matching/scoring exécuté ?
  - Newsletter : génération Bedrock vs fallback ?
  - Moment exact du fallback et condition déclenchante
  - Erreurs S3 (AccessDenied, etc.) ?
  - Engine exécute-t-il encore du code d'ingestion ?

**Livrable** : `docs/diagnostics/vectora_inbox_lai_weekly_v3_e2e_runtime_trace.md`

---

### Phase 5 – Synthèse & Recommandations
**Durée estimée** : 30 min  
**Objectif** : Produire un diagnostic final avec recommandations

**Actions** :
- Créer carte claire du workflow actuel (réel vs théorique)
- Identifier causes exactes du fallback newsletter
- Lister écarts design envisagé vs comportement réel
- Identifier points qui fonctionnent bien
- Proposer recommandations structurantes sans les implémenter

**Livrable** : `docs/diagnostics/vectora_inbox_engine_vs_ingest_final_runtime_diagnostic.md`

---

## 🔧 Consignes Techniques

### Invocation Lambda
- Utiliser systématiquement `--cli-binary-format raw-in-base64-out`
- Payload JSON valide uniquement
- Profil AWS : `rag-lai-prod`

### Analyse
- Données réelles uniquement, pas de simulation
- Focus sur les logs CloudWatch réels
- Identifier les erreurs techniques précises

### Documentation
- Chaque phase produit un livrable documenté
- Synthèse finale lisible et actionnable
- Recommandations priorisées sans implémentation

---

## 📊 Métriques de Succès

À la fin de ce diagnostic, nous devrons pouvoir répondre clairement à :

1. **Pourquoi la newsletter est encore en fallback ?**
2. **Quelle Lambda fait quoi aujourd'hui, exactement ?**
3. **Quelles permissions/configs AWS manquent pour que le workflow soit sain ?**
4. **Quels seraient les 2-3 correctifs les plus simples pour rendre le pipeline robuste ?**

---

**Prêt pour exécution phase par phase.**