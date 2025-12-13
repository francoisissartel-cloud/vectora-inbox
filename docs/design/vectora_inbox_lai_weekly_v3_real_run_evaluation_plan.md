# Plan d'Évaluation Complète - Vectora Inbox LAI Weekly v3 (Conditions Réelles)

**Date** : 2025-12-12  
**Client** : lai_weekly_v3  
**Environnement** : dev  
**Profil AWS** : rag-lai-prod  
**Repo local** : C:\Users\franc\OneDrive\Bureau\vectora-inbox

---

## Objectif Global

Évaluation complète et réaliste du workflow Vectora Inbox en conditions réelles sur un run complet lai_weekly_v3 pour :
- Comprendre exactement ce qui se passe à chaque étape
- Vérifier l'utilisation correcte de la config client + canonical (moteur générique)
- Quantifier le bruit et la qualité de détection
- Produire des recommandations priorisées P0/P1/P2

---

## Contraintes Techniques

✅ **Exécutions réelles uniquement** : Lambdas AWS vectora-inbox-ingest-normalize-dev + vectora-inbox-engine-dev  
✅ **Client unique** : lai_weekly_v3 (pas de simulation, pas d'autres clients)  
✅ **Invocations validées** : Utiliser méthodes d'invocation qui ont déjà fonctionné  
✅ **Pas de modification métier** : Observer et expliquer, ne pas patcher la logique  

---

## Phase 1 - Ingestion & Normalisation (Réel)

### 1.1 Objectifs
- Lancer vectora-inbox-ingest-normalize-dev pour lai_weekly_v3
- Collecter métriques d'ingestion et normalisation
- Analyser filtrage par ingestion_profiles
- Vérifier utilisation du canonical dans la normalisation Bedrock

### 1.2 Commandes d'Exécution

```bash
# Invocation Lambda ingest-normalize (période 7 jours)
aws lambda invoke \
  --function-name vectora-inbox-ingest-normalize-dev \
  --cli-binary-format raw-in-base64-out \
  --payload '{"client_id":"lai_weekly_v3","period_days":7}' \
  --profile rag-lai-prod \
  out-ingest-normalize-phase1.json

# Consultation logs détaillés
aws logs tail /aws/lambda/vectora-inbox-ingest-normalize-dev \
  --since 30m \
  --profile rag-lai-prod \
  > logs-ingest-normalize-phase1.txt
```

### 1.3 Métriques à Collecter
- **Ingestion** : Nombre d'items scrappés par source (RSS vs HTML)
- **Filtrage** : % filtrés par ingestion_profiles
- **Normalisation** : Items envoyés à Bedrock, taux de succès, temps d'exécution
- **Entités** : Présence companies, molecules, technologies, indications, trademarks
- **Erreurs** : Sources en erreur, throttling Bedrock

### 1.4 Fichier de Diagnostic
`docs/diagnostics/vectora_inbox_lai_weekly_v3_phase1_ingestion_normalization_results.md`

---

## Phase 2 - Matching (Domaines, Scopes, Genericité)

### 2.1 Objectifs
- Lancer vectora-inbox-engine-dev sur le corpus normalisé de Phase 1
- Observer la phase matching : domaines, scopes canonical, technology profiles
- Vérifier utilisation de client-config-examples/lai_weekly_v3.yaml
- Analyser règles domain_matching_rules.yaml

### 2.2 Commandes d'Exécution

```bash
# Invocation Lambda engine (même execution_date que Phase 1)
aws lambda invoke \
  --function-name vectora-inbox-engine-dev \
  --cli-binary-format raw-in-base64-out \
  --payload '{"client_id":"lai_weekly_v3","execution_date":"[DATE_FROM_PHASE1]"}' \
  --profile rag-lai-prod \
  out-engine-phase2.json

# Logs détaillés matching
aws logs tail /aws/lambda/vectora-inbox-engine-dev \
  --since 30m \
  --profile rag-lai-prod \
  > logs-engine-matching-phase2.txt
```

### 2.3 Métriques à Collecter
- **Volume** : Items normalisés → items matchés
- **Domaines** : Répartition par watch_domain (tech_lai_ecosystem, etc.)
- **Signaux** : Technologies, molecules, trademarks, companies détectés
- **Règles** : Application technology_complex, exclusions
- **Exemples** : Items gold (match) vs bruit (rejet) avec justification

### 2.4 Fichier de Diagnostic
`docs/diagnostics/vectora_inbox_lai_weekly_v3_phase2_matching_results.md`

---

## Phase 3 - Scoring & Sélection

### 3.1 Objectifs
- Analyser la phase scoring sur les items matchés de Phase 2
- Vérifier utilisation scoring_rules.yaml + config client
- Quantifier impact des bonus/malus (pure players, trademarks, event_type, recency)
- Analyser seuils et sélection finale

### 3.2 Métriques à Collecter
- **Volume** : Items matchés → items scorés
- **Distribution** : Histogramme des scores
- **Seuils** : min_score, top_n utilisés
- **Bonus/Malus** : Impact quantifié par type
- **Sélection** : Items retenus pour newsletter

### 3.3 Fichier de Diagnostic
`docs/diagnostics/vectora_inbox_lai_weekly_v3_phase3_scoring_selection_results.md`

---

## Phase 4 - Newsletter (Génération Finale)

### 4.1 Objectifs
- Vérifier génération newsletter finale
- Analyser présence/absence items gold vs bruit résiduel
- Vérifier utilisation des sorties scoring/matching
- Évaluer qualité éditoriale

### 4.2 Métriques à Collecter
- **Volume** : Items scorés → items newsletter
- **Sections** : Structure générée
- **Qualité** : Items gold présents (Nanexa/Moderna, UZEDY, MedinCell)
- **Bruit** : HR, finance, corporate moves résiduels
- **Performance** : Temps génération, succès Bedrock

### 4.3 Fichier de Diagnostic
`docs/diagnostics/vectora_inbox_lai_weekly_v3_phase4_newsletter_results.md`

---

## Phase 5 - Synthèse Globale & Recommandations

### 5.1 Objectifs
- Produire rapport exécutif complet
- Synthétiser métriques clés par phase
- Expliquer utilisation config client + canonical
- Quantifier bruit résiduel et qualité détection
- Lister recommandations P0/P1/P2

### 5.2 Analyses Transversales
- **Métriques globales** : Volumes, ratios, temps par phase
- **Utilisation config** : Moteur générique vs câblage dur
- **Qualité signal** : Taux de détection items gold, maîtrise bruit
- **Performance** : Temps d'exécution, stabilité, coûts
- **Points forts** : Ce qui fonctionne bien
- **Optimisations** : Ce qui doit être amélioré

### 5.3 Fichier de Synthèse
`docs/diagnostics/vectora_inbox_lai_weekly_v3_real_run_evaluation_executive_summary.md`

---

## Scripts de Support

### Scripts d'Analyse Locale
```bash
# Script extraction métriques S3
scripts/analyze_s3_metrics.py lai_weekly_v3 [execution_date]

# Script analyse logs Lambda
scripts/parse_lambda_logs.py [log_file] --phase [ingestion|matching|scoring|newsletter]

# Script comparaison items gold vs bruit
scripts/analyze_signal_quality.py lai_weekly_v3 [execution_date]
```

### Fichiers de Configuration Analysés
- `client-config-examples/lai_weekly_v3.yaml`
- `config/canonical/domain_matching_rules.yaml`
- `config/canonical/scoring_rules.yaml`
- `config/canonical/ingestion_profiles.yaml`

---

## Livrables Attendus

### Diagnostics par Phase
1. `phase1_ingestion_normalization_results.md`
2. `phase2_matching_results.md`
3. `phase3_scoring_selection_results.md`
4. `phase4_newsletter_results.md`

### Synthèse Finale
5. `real_run_evaluation_executive_summary.md`

### Métriques Clés
- **Volumes** : Items par étape (ingestion → newsletter)
- **Ratios** : Taux de filtrage, matching, sélection
- **Temps** : Performance par phase
- **Qualité** : Taux détection gold, niveau bruit résiduel
- **Recommandations** : P0/P1/P2 priorisées

---

## Critères de Succès

✅ **Exécution complète** : Toutes les phases exécutées en réel  
✅ **Métriques collectées** : Volumes, ratios, temps, qualité par phase  
✅ **Config validée** : Utilisation correcte lai_weekly_v3.yaml + canonical  
✅ **Signal analysé** : Items gold détectés, bruit quantifié  
✅ **Recommandations** : P0/P1/P2 priorisées pour améliorer MVP  

---

**Prêt pour exécution** : Phase 1 - Ingestion & Normalisation