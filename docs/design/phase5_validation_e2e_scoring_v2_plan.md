# Plan Phase 5 - Validation E2E Scoring V2 Corrigé

**Date :** 21 décembre 2025  
**Objectif :** Validation End-to-End de la correction scoring dans le workflow 3 Lambdas  
**Statut :** Phase 5 - Exécution validation production  

---

## 🎯 OBJECTIF ET CONTRAINTES

### Objectif Principal

**Valider que la correction du bug confidence fonctionne en production :**
- final_score > 0 pour items LAI avec matched_domains
- Newsletter V2 sélectionne des items (sans bidouilles)
- Pipeline 3 Lambdas stable et fonctionnel

### Contraintes Strictes

**Respect vectora-inbox-development-rules.md :**
- ✅ Architecture 3 Lambdas V2 obligatoire
- ✅ Code basé sur src_v2/ uniquement
- ✅ Handlers délèguent à vectora_core
- ✅ Configuration pilote le comportement
- ✅ Bedrock us-east-1 + Claude 3 Sonnet validé

**Workflow des 3 Lambdas :**
```
ingest-v2 → normalize-score-v2 (corrigé) → newsletter-v2 (rollback)
     ↓              ↓                           ↓
S3 ingested/   S3 curated/              S3 newsletters/
```

---

## 📋 PLAN D'EXÉCUTION EN 4 PHASES

### Phase 5.1 : Préparation Infrastructure

**Objectif :** Déployer la correction scorer.py en production

#### 5.1.1 Repackaging Layer vectora-core

```bash
# Navigation vers le projet
cd c:/Users/franc/OneDrive/Bureau/vectora-inbox

# Construction de la layer avec scorer.py corrigé
python scripts/layers/create_vectora_core_layer.py

# Vérification du package généré
ls -la output/lambda_packages/vectora-core-*.zip
```

**Validation :**
- [ ] Package vectora-core généré avec succès
- [ ] Taille < 50MB (conformité règles V4)
- [ ] scorer.py corrigé inclus dans le package

#### 5.1.2 Déploiement Layer AWS

```bash
# Déploiement nouvelle version layer
aws lambda publish-layer-version \
  --layer-name vectora-inbox-vectora-core-dev \
  --zip-file fileb://output/lambda_packages/vectora-core-scoring-fix.zip \
  --compatible-runtimes python3.9 \
  --region eu-west-3 \
  --profile rag-lai-prod

# Récupération du numéro de version
NEW_VERSION=$(aws lambda list-layer-versions \
  --layer-name vectora-inbox-vectora-core-dev \
  --region eu-west-3 \
  --profile rag-lai-prod \
  --query 'LayerVersions[0].Version' \
  --output text)

echo "Nouvelle version layer: $NEW_VERSION"
```

**Validation :**
- [ ] Layer déployée avec succès
- [ ] Numéro de version récupéré
- [ ] Aucune erreur de déploiement

#### 5.1.3 Mise à Jour Lambda normalize-score-v2

```bash
# Mise à jour de la Lambda avec nouvelle layer
aws lambda update-function-configuration \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --layers arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev:$NEW_VERSION \
  --region eu-west-3 \
  --profile rag-lai-prod

# Vérification de la mise à jour
aws lambda get-function-configuration \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --region eu-west-3 \
  --profile rag-lai-prod \
  --query 'Layers[0].Arn'
```

**Validation :**
- [ ] Lambda mise à jour avec nouvelle layer
- [ ] ARN layer confirmé
- [ ] Configuration cohérente

### Phase 5.2 : Exécution Pipeline Complet

**Objectif :** Relancer ingest + normalize_score_v2 pour lai_weekly_v4

#### 5.2.1 Exécution Ingest V2

```bash
# Payload pour ingest
cat > payload_ingest.json << EOF
{
  "client_id": "lai_weekly_v4"
}
EOF

# Exécution Lambda ingest-v2
aws lambda invoke \
  --function-name vectora-inbox-ingest-v2-dev \
  --payload file://payload_ingest.json \
  --region eu-west-3 \
  --profile rag-lai-prod \
  response_ingest.json

# Vérification résultat
cat response_ingest.json | jq '.statusCode, .body.status, .body.items_processed'
```

**Validation :**
- [ ] StatusCode: 200
- [ ] Status: "completed"
- [ ] Items ingérés > 0
- [ ] Aucune erreur dans CloudWatch

#### 5.2.2 Exécution Normalize-Score V2 (Corrigé)

```bash
# Payload pour normalize-score
cat > payload_normalize.json << EOF
{
  "client_id": "lai_weekly_v4"
}
EOF

# Exécution Lambda normalize-score-v2 avec correction
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --payload file://payload_normalize.json \
  --region eu-west-3 \
  --profile rag-lai-prod \
  response_normalize.json

# Vérification résultat
cat response_normalize.json | jq '.statusCode, .body.status, .body.statistics'
```

**Validation :**
- [ ] StatusCode: 200
- [ ] Status: "completed"
- [ ] Items normalisés et scorés
- [ ] Statistiques cohérentes
- [ ] Aucune erreur de scoring dans logs

#### 5.2.3 Vérification CloudWatch Logs

```bash
# Vérification logs normalize-score-v2
aws logs filter-log-events \
  --log-group-name /aws/lambda/vectora-inbox-normalize-score-v2-dev \
  --start-time $(date -d '10 minutes ago' +%s)000 \
  --region eu-west-3 \
  --profile rag-lai-prod \
  --query 'events[?contains(message, `ERROR`) || contains(message, `final_score`)]'
```

**Validation :**
- [ ] Aucune erreur "TypeError" (bug confidence corrigé)
- [ ] Messages "final_score" avec valeurs > 0
- [ ] Logs propres sans exceptions masquées

### Phase 5.3 : Analyse Résultats S3 curated/

**Objectif :** Vérifier que la correction fonctionne dans les données

#### 5.3.1 Téléchargement Items Curated

```bash
# Identification du dernier run
LATEST_RUN=$(aws s3 ls s3://vectora-inbox-data-dev/curated/lai_weekly_v4/ \
  --recursive --profile rag-lai-prod | \
  grep items.json | sort | tail -1 | awk '{print $4}')

echo "Dernier run: $LATEST_RUN"

# Téléchargement des items curated
aws s3 cp s3://vectora-inbox-data-dev/$LATEST_RUN \
  curated_items_post_correction.json \
  --profile rag-lai-prod
```

**Validation :**
- [ ] Fichier curated téléchargé avec succès
- [ ] Items présents dans le fichier
- [ ] Structure JSON valide

#### 5.3.2 Analyse Automatisée des Scores

```python
# Script d'analyse (à exécuter localement)
python << 'EOF'
import json

with open('curated_items_post_correction.json', 'r') as f:
    items = json.load(f)

print(f"=== ANALYSE POST-CORRECTION ===")
print(f"Items analysés: {len(items)}")

# Analyse des final_score
scores = []
items_with_score = 0
items_with_matched_domains = 0
items_with_errors = 0

for item in items:
    scoring_results = item.get("scoring_results", {})
    final_score = scoring_results.get("final_score", 0)
    matched_domains = item.get("matching_results", {}).get("matched_domains", [])
    
    if "error" in scoring_results:
        items_with_errors += 1
        print(f"❌ Erreur: {item.get('item_id')} - {scoring_results.get('error')}")
    
    if matched_domains:
        items_with_matched_domains += 1
        
    if final_score > 0:
        items_with_score += 1
        scores.append(final_score)

print(f"\n📊 Résultats:")
print(f"   Items avec matched_domains: {items_with_matched_domains}")
print(f"   Items avec final_score > 0: {items_with_score}")
print(f"   Items avec erreurs: {items_with_errors}")

if scores:
    print(f"   Score min: {min(scores):.1f}")
    print(f"   Score max: {max(scores):.1f}")
    print(f"   Score moyen: {sum(scores)/len(scores):.1f}")
    
    # Items sélectionnables
    selectable = [s for s in scores if s >= 12]
    print(f"   Items sélectionnables (>= 12): {len(selectable)}")

# Validation correction
correction_success = (items_with_score > 0 and items_with_errors == 0)
print(f"\n🏆 CORRECTION: {'✅ RÉUSSIE' if correction_success else '❌ ÉCHOUÉE'}")
EOF
```

**Validation :**
- [ ] Items avec matched_domains ont final_score > 0
- [ ] Aucune erreur de scoring
- [ ] Distribution des scores cohérente
- [ ] Items sélectionnables (score >= 12) présents

### Phase 5.4 : Test Newsletter V2 (Sans Bidouilles)

**Objectif :** Vérifier que newsletter fonctionne avec scoring corrigé

#### 5.4.1 Exécution Newsletter V2

```bash
# Payload pour newsletter
cat > payload_newsletter.json << EOF
{
  "client_id": "lai_weekly_v4"
}
EOF

# Exécution Lambda newsletter-v2 (avec rollback des bidouilles)
aws lambda invoke \
  --function-name vectora-inbox-newsletter-v2-dev \
  --payload file://payload_newsletter.json \
  --region eu-west-3 \
  --profile rag-lai-prod \
  response_newsletter.json

# Vérification résultat
cat response_newsletter.json | jq '.statusCode, .body.status, .body.items_selected'
```

**Validation :**
- [ ] StatusCode: 200
- [ ] Status: "success"
- [ ] Items sélectionnés > 0 (pas de newsletter vide)
- [ ] Newsletter générée dans S3

#### 5.4.2 Vérification Newsletter Générée

```bash
# Téléchargement newsletter générée
NEWSLETTER_PATH=$(aws s3 ls s3://vectora-inbox-newsletters-dev/lai_weekly_v4/ \
  --recursive --profile rag-lai-prod | \
  grep newsletter.md | sort | tail -1 | awk '{print $4}')

aws s3 cp s3://vectora-inbox-newsletters-dev/$NEWSLETTER_PATH \
  newsletter_post_correction.md \
  --profile rag-lai-prod

# Vérification contenu
head -20 newsletter_post_correction.md
grep "Score:" newsletter_post_correction.md | head -5
```

**Validation :**
- [ ] Newsletter Markdown générée
- [ ] Contenu présent (pas vide)
- [ ] Scores affichés > 0 (pas de 0.0 partout)
- [ ] Structure cohérente

---

## 📊 CRITÈRES DE SUCCÈS

### Critères Techniques

1. **Scoring Fonctionnel**
   - [ ] final_score > 0 pour items avec matched_domains
   - [ ] Aucune erreur TypeError dans logs
   - [ ] Distribution scores cohérente (0-20 range)

2. **Pipeline Stable**
   - [ ] Toutes les Lambdas StatusCode: 200
   - [ ] Temps d'exécution < 3min par Lambda
   - [ ] Aucune régression performance

3. **Newsletter Opérationnelle**
   - [ ] Items sélectionnés sans bidouilles
   - [ ] Scores affichés réalistes
   - [ ] Structure Markdown correcte

### Critères Métier

1. **Qualité Sélection**
   - [ ] 6-8 items sélectionnés (vs 0 avant)
   - [ ] Items LAI forts en tête
   - [ ] Cohérence lai_relevance_score ↔ final_score

2. **Autorité Matching**
   - [ ] Seuls items avec matched_domains dans newsletter
   - [ ] Aucun fallback sur lai_relevance_score
   - [ ] Respect strict des source_domains par section

---

## 🔄 ACTIONS POST-VALIDATION

### Si Validation Réussie ✅

1. **Documentation**
   - Marquer correction comme validée en production
   - Mettre à jour métriques de référence
   - Documenter nouveaux seuils performance

2. **Reprise newsletter_v2_implementation_plan_lai_weekly_v4.md**
   - Supprimer les modes fallback identifiés
   - Finaliser implémentation newsletter propre
   - Déployer version finale

3. **Monitoring**
   - Alertes sur final_score = 0 pour items matchés
   - Métriques distribution scores
   - Surveillance qualité newsletter

### Si Validation Échouée ❌

1. **Diagnostic Approfondi**
   - Analyser logs détaillés
   - Vérifier version layer déployée
   - Identifier cas d'échec restants

2. **Correction Additionnelle**
   - Retour Phase 4 si nécessaire
   - Tests unitaires renforcés
   - Validation locale approfondie

3. **Rollback si Critique**
   - Restaurer version précédente
   - Analyser impact autres clients
   - Replanifier correction

---

## 📋 CHECKLIST D'EXÉCUTION

### Pré-Exécution
- [ ] Backup configuration actuelle
- [ ] Vérification environnement AWS (profil rag-lai-prod)
- [ ] Confirmation région eu-west-3
- [ ] Scripts de rollback préparés

### Exécution Phase 5.1
- [ ] Layer vectora-core repackagée
- [ ] Layer déployée AWS
- [ ] Lambda normalize-score-v2 mise à jour
- [ ] Configuration vérifiée

### Exécution Phase 5.2
- [ ] Ingest-v2 exécutée avec succès
- [ ] Normalize-score-v2 exécutée avec succès
- [ ] Logs vérifiés (aucune erreur)
- [ ] Métriques cohérentes

### Exécution Phase 5.3
- [ ] Items curated téléchargés
- [ ] Analyse scores automatisée
- [ ] Correction validée techniquement
- [ ] Métriques conformes aux attentes

### Exécution Phase 5.4
- [ ] Newsletter-v2 exécutée
- [ ] Newsletter générée et téléchargée
- [ ] Contenu vérifié (scores réalistes)
- [ ] Sélection sans bidouilles confirmée

---

## 🎯 RÉSULTAT ATTENDU

**Avant correction :**
```json
{
  "items_with_final_score_gt_0": 0,
  "newsletter_items_selected": 0,
  "status": "❌ Pipeline cassé"
}
```

**Après correction (objectif) :**
```json
{
  "items_with_final_score_gt_0": 8,
  "items_selectable_score_gte_12": 6,
  "newsletter_items_selected": 6,
  "status": "✅ Pipeline opérationnel"
}
```

---

*Plan Phase 5 - Validation E2E Scoring V2*  
*Prêt pour exécution selon règles vectora-inbox-development-rules.md*