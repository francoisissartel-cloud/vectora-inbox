# Diagnostic : Premier Run End-to-End de la Lambda Engine

**Date** : 2025-01-15  
**Auteur** : Amazon Q Developer  
**Statut** : ⏳ **EN ATTENTE D'EXÉCUTION**

---

## Résumé exécutif

Ce document documente le premier run end-to-end complet du workflow Vectora Inbox en DEV :
- **ingest-normalize** : Ingestion et normalisation des sources
- **engine** : Matching, scoring et génération de newsletter

**Statut** : ⏳ À compléter après l'exécution du test

---

## Contexte du test

### Configuration

**Client** : `lai_weekly`  
**Période** : 7 jours (period_days: 7)  
**Date d'exécution** : [À compléter]  
**Environnement** : DEV (eu-west-3)

### Infrastructure

**Lambdas déployées** :
- `vectora-inbox-ingest-normalize-dev`
- `vectora-inbox-engine-dev`

**Buckets S3** :
- Config : `vectora-inbox-config-dev`
- Data : `vectora-inbox-data-dev`
- Newsletters : `vectora-inbox-newsletters-dev`

**Modèle Bedrock** : `eu.anthropic.claude-sonnet-4-5-20250929-v1:0` (inference profile EU cross-region)

**Concurrence Lambda** : 1 (mode mono-instance pour éviter throttling)

---

## Résultats de l'exécution

### Phase 1 : Ingest-Normalize

**Commande** :
```powershell
aws lambda invoke --function-name vectora-inbox-ingest-normalize-dev --payload file://test-event-ingest.json out-ingest-lai-weekly.json
```

**Résultats** :
- ⏳ Status code : [À compléter]
- ⏳ Sources traitées : [À compléter]
- ⏳ Items ingérés : [À compléter]
- ⏳ Items normalisés : [À compléter]
- ⏳ Temps d'exécution : [À compléter] secondes
- ⏳ Chemin S3 output : [À compléter]

**Observations** :
- [À compléter après exécution]

### Phase 2 : Engine

**Commande** :
```powershell
aws lambda invoke --function-name vectora-inbox-engine-dev --payload file://test-event-engine.json out-engine-lai-weekly.json
```

**Résultats** :
- ⏳ Status code : [À compléter]
- ⏳ Items analysés : [À compléter]
- ⏳ Items matchés : [À compléter]
- ⏳ Items sélectionnés : [À compléter]
- ⏳ Sections générées : [À compléter]
- ⏳ Temps d'exécution : [À compléter] secondes
- ⏳ Chemin S3 output : [À compléter]

**Observations** :
- [À compléter après exécution]

---

## Analyse de la newsletter générée

### Structure

**Titre** : [À compléter]

**Introduction** : [À compléter]

**TL;DR** :
- [À compléter]

**Sections** :
1. [Section 1] : [X] items
2. [Section 2] : [Y] items

**Footer** : [À compléter]

### Qualité éditoriale

**Ton** : [À évaluer]
- ✅ / ⚠️ / ❌ Respecte le tone défini (executive)
- ✅ / ⚠️ / ❌ Respecte le voice défini (concise)
- ✅ / ⚠️ / ❌ Respecte la langue définie

**Contenu** :
- ✅ / ⚠️ / ❌ Pas d'hallucinations détectées
- ✅ / ⚠️ / ❌ Noms de sociétés/molécules préservés
- ✅ / ⚠️ / ❌ Reformulations pertinentes et concises
- ✅ / ⚠️ / ❌ URLs présentes et valides

**Pertinence** :
- ✅ / ⚠️ / ❌ Items sélectionnés pertinents pour le client
- ✅ / ⚠️ / ❌ Scoring cohérent (items importants en premier)
- ✅ / ⚠️ / ❌ Sections bien organisées

---

## Métriques techniques

### Appels Bedrock

**Ingest-Normalize** :
- ⏳ Nombre d'appels : [À compléter]
- ⏳ Throttles détectés : [À compléter]
- ⏳ Retries effectués : [À compléter]

**Engine** :
- ⏳ Nombre d'appels : [À compléter]
- ⏳ Throttles détectés : [À compléter]
- ⏳ Retries effectués : [À compléter]

### Performance

**Temps d'exécution total** : [À compléter] secondes
- Ingest-Normalize : [X] secondes
- Engine : [Y] secondes

**Mémoire utilisée** :
- Ingest-Normalize : [À compléter] MB
- Engine : [À compléter] MB

---

## Problèmes rencontrés

### Problème 1 : [Titre]

**Description** : [À compléter si applicable]

**Solution** : [À compléter si applicable]

### Problème 2 : [Titre]

**Description** : [À compléter si applicable]

**Solution** : [À compléter si applicable]

---

## Recommandations d'ajustement

### Prompts Bedrock

- [ ] [Recommandation 1]
- [ ] [Recommandation 2]

### Scoring

- [ ] [Recommandation 1]
- [ ] [Recommandation 2]

### Configuration client

- [ ] [Recommandation 1]
- [ ] [Recommandation 2]

### Infrastructure

- [ ] [Recommandation 1]
- [ ] [Recommandation 2]

---

## Logs CloudWatch

### Ingest-Normalize

```
[À compléter avec les logs pertinents]
```

### Engine

```
[À compléter avec les logs pertinents]
```

---

## Conclusion

**Statut final** : ⏳ [À compléter : ✅ GREEN / ⚠️ AMBER / ❌ RED]

**Synthèse** : [À compléter après exécution]

**Prochaines étapes** :
1. [À compléter]
2. [À compléter]
3. [À compléter]

---

**Auteur** : Amazon Q Developer  
**Date de création** : 2025-01-15  
**Version** : 1.0 (Template)
