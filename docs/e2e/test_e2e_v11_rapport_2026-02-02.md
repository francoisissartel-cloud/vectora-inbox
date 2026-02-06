# Test E2E lai_weekly_v11 - Rapport 2026-02-02

## ✅ Résultats Test E2E

### Étapes Complétées

**1. AWS SSO Login** ✅
- Token rafraîchi avec succès

**2. Deploy Dev** ✅
- vectora-core layer v53 déployé
- common-deps layer v14 déployé
- 3 Lambdas mises à jour avec nouveaux layers

**3. Upload Config v11** ✅
- `lai_weekly_v11.yaml` uploadé vers S3 dev

**4. Ingestion** ✅
- Lambda: `vectora-inbox-ingest-v2-dev`
- StatusCode: 200
- Durée: ~21s

**5. Normalize & Score** ✅
- Lambda: `vectora-inbox-normalize-score-v2-dev`
- StatusCode: 200
- Durée: 149.5s (~2.5 min)

## 📊 Statistiques

```
Items input:      29
Items normalized: 29  (100%)
Items matched:    0   (⚠️ Aucun match)
Items scored:     29  (100%)
Processing time:  147.9s
```

## ⚠️ Observation Critique

**Items matched: 0**

Tous les items ont été normalisés et scorés, mais **aucun n'a matché** avec le domaine LAI.

### Causes Possibles

1. **Domain scoring trop strict** ?
   - Prompt `lai_domain_scoring.yaml` rejette tous les items
   - Seuils de matching trop élevés

2. **Données ingérées non LAI** ?
   - Sources ne contiennent pas de signaux LAI
   - Période de 30 jours sans actualité LAI

3. **Configuration matching** ?
   - `min_domain_score: 0.25` trop élevé ?
   - `min_confidence_level: "low"` pas appliqué ?

## 🔍 Prochaines Actions Recommandées

### 1. Analyser les items normalisés
```bash
# Télécharger items normalisés depuis S3
aws s3 cp s3://vectora-inbox-data-dev/runs/lai_weekly_v11/latest/normalized_items.json . --profile rag-lai-prod

# Examiner:
# - Quelles entités détectées ?
# - Quels event_type ?
# - Quelles technologies mentionnées ?
```

### 2. Vérifier logs Lambda
```bash
# Logs normalize-score
aws logs tail /aws/lambda/vectora-inbox-normalize-score-v2-dev --follow --profile rag-lai-prod

# Chercher:
# - Appels Bedrock domain_scoring
# - Scores calculés
# - Raisons de rejet
```

### 3. Tester avec données connues LAI

Créer un test avec item LAI garanti :
- MedinCell + UZEDY®
- Microspheres technology
- Partnership event

### 4. Ajuster seuils si nécessaire

Si items LAI légitimes rejetés :
```yaml
matching_config:
  min_domain_score: 0.15  # Réduire de 0.25 → 0.15
```

## ✅ Validation Architecture v2.0

**Prompts actifs confirmés** :
- ✅ `generic_normalization.yaml` utilisé (29 items normalisés)
- ✅ `lai_domain_scoring.yaml` utilisé (29 items scorés)
- ✅ Pas d'erreur "prompt not found"
- ✅ Cleanup prompts obsolètes validé

**Architecture 2 appels Bedrock** :
- ✅ Appel 1 : Normalisation (29/29 succès)
- ✅ Appel 2 : Domain scoring (29/29 exécutés, 0 matches)

## 📝 Conclusion

**Succès technique** : Pipeline fonctionne correctement
- Build ✅
- Deploy ✅
- Ingestion ✅
- Normalisation ✅
- Domain scoring ✅

**Attention qualité** : 0 matches sur 29 items
- Nécessite investigation des données
- Possiblement ajustement seuils ou prompt

---

**Prochaine étape** : Analyser `normalized_items.json` pour comprendre pourquoi 0 matches
