# Phase 0 - Préparation Client lai_weekly_v6 - TERMINÉE

**Date**: 2026-01-27
**Durée**: ~5 minutes
**Statut**: ✅ SUCCÈS

---

## RÉSUMÉ EXÉCUTIF

✅ **Configuration client lai_weekly_v6 créée et uploadée**
✅ **Environnement Lambda vérifié et opérationnel**
✅ **Layers Approche B confirmés**
✅ **Prompts LAI présents sur S3**
✅ **Prêt pour Phase 1 - Ingestion**

---

## 0.1 CRÉATION CONFIGURATION CLIENT

### Fichier créé
- **Source**: `client-config-examples/lai_weekly_v5.yaml`
- **Destination**: `client-config-examples/lai_weekly_v6.yaml`
- **Taille**: 8.7 KB

### Modifications v5 → v6

**Identité client**:
- ✅ client_id: `lai_weekly_v5` → `lai_weekly_v6`
- ✅ client_profile.name: `v5 (Tech Focus)` → `v6 (Fresh Run Test)`
- ✅ notification_email: `lai-weekly-v6@vectora.com`
- ✅ template_version: `5.0.0` → `6.0.0`
- ✅ created_date: `2026-01-27`

**NOUVEAU - Filtrage items courts**:
```yaml
source_config:
  content_filters:
    min_word_count: 50
    exclude_patterns:
      - "Download attachment"
      - "View attachment"
      - "Read more"
```

**OPTIMISÉ - Déduplication renforcée**:
```yaml
deduplication:
  enabled: true
  similarity_threshold: 0.75  # v5: 0.8
  prefer_critical_events: true
  prefer_higher_score: true
  company_based_dedup: true  # NOUVEAU
```

---

## 0.2 UPLOAD CONFIGURATION S3

### Commande exécutée
```bash
aws s3 cp client-config-examples/lai_weekly_v6.yaml s3://vectora-inbox-config-dev/clients/lai_weekly_v6.yaml --profile rag-lai-prod --region eu-west-3
```

### Résultat
✅ **Upload réussi**: `8.5 KiB` transférés
✅ **Fichier S3**: `s3://vectora-inbox-config-dev/clients/lai_weekly_v6.yaml`
✅ **Timestamp**: `2026-01-27 10:44:41`
✅ **Taille**: `8664 bytes`

### Validation
```bash
aws s3 ls s3://vectora-inbox-config-dev/clients/lai_weekly_v6.yaml
# Output: 2026-01-27 10:44:41       8664 lai_weekly_v6.yaml
```

---

## 0.3 VÉRIFICATION ENVIRONNEMENT

### Lambdas déployées
✅ **3 Lambdas vectora-inbox opérationnelles**:
```
vectora-inbox-ingest-v2-dev
vectora-inbox-normalize-score-v2-dev
vectora-inbox-newsletter-v2-dev
```

### Layers Approche B (normalize-score-v2)
✅ **2 Layers attachés**:
```
arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-common-deps-dev:4
arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-approche-b-dev:2
```

### Prompts LAI sur S3
✅ **Prompts canonical présents**:
```
canonical/prompts/normalization/lai_prompt.yaml  (2.3 KB)
canonical/prompts/matching/lai_prompt.yaml       (1.5 KB)
canonical/prompts/global_prompts.yaml            (12.6 KB)
```

### Checklist finale
- ✅ Lambda ingest-v2 déployée et opérationnelle
- ✅ Lambda normalize-score-v2 avec layers Approche B
- ✅ Lambda newsletter-v2 déployée
- ✅ Prompts LAI sur S3
- ✅ Client config lai_weekly_v6 sur S3
- ✅ Accès CloudWatch Logs disponible

---

## DIFFÉRENCES CLÉS v6 vs v5

### Améliorations v6

**1. Filtrage pré-normalisation**:
- Exclusion items < 50 mots
- Patterns génériques exclus ("Download attachment", etc.)
- Réduction bruit avant appels Bedrock

**2. Déduplication optimisée**:
- Seuil abaissé: 0.8 → 0.75 (plus strict)
- Déduplication basée entreprise activée
- Meilleure gestion pure players (Nanexa, MedinCell)

**3. Objectif test**:
- v5: Test corrections déployées
- v6: Test E2E complet workflow Ingestion → Normalisation → Newsletter

---

## PROCHAINES ÉTAPES

### Phase 1 - Ingestion
**Commande**:
```bash
# Créer event_ingest_v6.json
echo {"client_id": "lai_weekly_v6"} > event_ingest_v6.json

# Invoquer Lambda
aws lambda invoke --function-name vectora-inbox-ingest-v2-dev --cli-binary-format raw-in-base64-out --payload file://event_ingest_v6.json response_ingest_v6.json --profile rag-lai-prod --region eu-west-3
```

**Monitoring**:
```bash
aws logs tail /aws/lambda/vectora-inbox-ingest-v2-dev --follow --profile rag-lai-prod --region eu-west-3
```

---

## FICHIERS GÉNÉRÉS

### Configuration
- ✅ `client-config-examples/lai_weekly_v6.yaml` (local)
- ✅ `s3://vectora-inbox-config-dev/clients/lai_weekly_v6.yaml` (S3)

### Prochains fichiers (Phase 1+)
- `event_ingest_v6.json` - Event invocation ingestion
- `response_ingest_v6.json` - Réponse Lambda ingestion
- `items_ingested_v6.json` - Items ingérés depuis S3
- `event_normalize_v6.json` - Event invocation normalisation
- `response_normalize_v6.json` - Réponse Lambda normalisation
- `items_curated_v6.json` - Items curated depuis S3
- `event_newsletter_v6.json` - Event invocation newsletter
- `response_newsletter_v6.json` - Réponse Lambda newsletter
- `newsletter_v6.md` - Newsletter générée depuis S3

---

## NOTES TECHNIQUES

### Filtrage items courts
Le paramètre `min_word_count: 50` sera appliqué:
- **Où**: Lambda ingest-v2 (si supporté) ou normalize-score-v2
- **Impact attendu**: Réduction ~30-40% items courts détectés en v5
- **Bénéfice**: Économie appels Bedrock, meilleure qualité signal

### Déduplication renforcée
Le paramètre `similarity_threshold: 0.75` sera appliqué:
- **Où**: Lambda newsletter-v2
- **Impact attendu**: Meilleure détection doublons Nanexa (6 items similaires en v5)
- **Bénéfice**: Newsletter plus diversifiée, moins de redondance

### Approche B validée
Les prompts pré-construits LAI seront utilisés:
- **Normalisation**: `canonical/prompts/normalization/lai_prompt.yaml`
- **Matching**: `canonical/prompts/matching/lai_prompt.yaml`
- **Validation**: Logs CloudWatch confirmeront "Approche B activée"

---

**Phase 0 - Préparation Client lai_weekly_v6**
**Version 1.0 - 2026-01-27**
**Statut: ✅ SUCCÈS - Prêt pour Phase 1**
