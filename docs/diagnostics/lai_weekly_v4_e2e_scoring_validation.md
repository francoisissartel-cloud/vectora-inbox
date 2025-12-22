# Validation E2E Scoring V2 - lai_weekly_v4

**Date :** 21 décembre 2025  
**Objectif :** Validation End-to-End de la correction scoring sans modifier la newsletter  
**Statut :** Phase 5 - Validation production  

---

## 🎯 OBJECTIF DE LA VALIDATION

### Confirmer la Correction en Production

**But :** Vérifier que la correction du bug confidence fonctionne dans le pipeline complet :
```
ingest-v2 → normalize-score-v2 (corrigé) → S3 curated/ → newsletter-v2 (rollback)
```

**Critères de succès :**
- ✅ final_score > 0 pour items LAI pertinents
- ✅ Distribution cohérente des scores
- ✅ Newsletter V2 sélectionne des items (sans bidouilles)
- ✅ Aucune erreur dans les logs

---

## 📋 PLAN DE VALIDATION

### Étape 1 : Mise à Jour de la Layer vectora-core

**Objectif :** Déployer la correction scorer.py en production

**Actions :**
1. **Repackager la layer vectora-core**
   ```bash
   cd c:/Users/franc/OneDrive/Bureau/vectora-inbox
   python scripts/layers/create_vectora_core_layer.py
   ```

2. **Déployer la nouvelle version**
   ```bash
   aws lambda publish-layer-version \
     --layer-name vectora-inbox-vectora-core-dev \
     --zip-file fileb://output/lambda_packages/vectora-core-scoring-fix.zip \
     --compatible-runtimes python3.9 \
     --region eu-west-3 \
     --profile rag-lai-prod
   ```

3. **Mettre à jour Lambda normalize-score-v2**
   ```bash
   aws lambda update-function-configuration \
     --function-name vectora-inbox-normalize-score-v2-dev \
     --layers arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev:NEW_VERSION \
     --region eu-west-3 \
     --profile rag-lai-prod
   ```

### Étape 2 : Exécution Pipeline Complet

**Objectif :** Relancer ingest + normalize_score_v2 pour lai_weekly_v4

**Commandes :**
```bash
# 1. Ingest (pour avoir des données fraîches)
aws lambda invoke \
  --function-name vectora-inbox-ingest-v2-dev \
  --payload '{"client_id": "lai_weekly_v4"}' \
  --region eu-west-3 \
  --profile rag-lai-prod \
  response_ingest.json

# 2. Normalize + Score (avec correction)
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --payload '{"client_id": "lai_weekly_v4"}' \
  --region eu-west-3 \
  --profile rag-lai-prod \
  response_normalize.json
```

### Étape 3 : Vérification S3 curated/

**Objectif :** Analyser les résultats dans S3 pour confirmer la correction

**Téléchargement des données :**
```bash
# Identifier le dernier run
aws s3 ls s3://vectora-inbox-data-dev/curated/lai_weekly_v4/ \
  --recursive --profile rag-lai-prod

# Télécharger les items curated
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v4/2025/12/21/items.json \
  curated_items_post_fix.json --profile rag-lai-prod
```

**Analyse attendue :**
- Items avec matched_domains ont final_score > 0
- Distribution des scores cohérente (0-20 range)
- Items LAI forts (lai_relevance_score >= 8) ont final_score >= 12

### Étape 4 : Test Newsletter V2 (Sans Bidouilles)

**Objectif :** Vérifier que la newsletter fonctionne avec le scoring corrigé

**Commande :**
```bash
aws lambda invoke \
  --function-name vectora-inbox-newsletter-v2-dev \
  --payload '{"client_id": "lai_weekly_v4"}' \
  --region eu-west-3 \
  --profile rag-lai-prod \
  response_newsletter.json
```

**Résultats attendus :**
- Newsletter générée avec succès
- Items sélectionnés (pas de newsletter vide)
- Scores affichés cohérents (pas de 0.0 partout)

---

## 📊 CRITÈRES DE VALIDATION DÉTAILLÉS

### Métriques Techniques

**1. Scoring Results Structure**
```json
{
  "scoring_results": {
    "base_score": "> 0 pour items LAI",
    "bonuses": "Non vide pour items avec entités LAI",
    "penalties": "Appropriées selon contexte",
    "final_score": "> 0 pour items pertinents",
    "score_breakdown": {
      "domain_relevance_factor": "> 0.05 pour matched_domains",
      "scoring_mode": "balanced"
    }
  }
}
```

**2. Distribution des Scores Attendue**
- **Items LAI forts (lai_score >= 8) :** final_score 12-20
- **Items LAI moyens (lai_score 6-7) :** final_score 8-12
- **Items LAI faibles (lai_score 0-5) :** final_score 0-8

**3. Taux de Sélection Newsletter**
- **Avant correction :** 0/15 items sélectionnés
- **Après correction :** 6-8/15 items sélectionnés (40-53%)

### Métriques Métier

**1. Cohérence lai_relevance_score ↔ final_score**
- Corrélation positive forte
- Items avec lai_score = 10 en tête de classement
- Items avec lai_score = 0 exclus ou en queue

**2. Pertinence des Items Sélectionnés**
- Nanexa/Moderna Partnership (lai_score 8) → sélectionné
- UZEDY FDA Approval (lai_score 10) → sélectionné  
- Rapports financiers (lai_score 0) → exclus

**3. Qualité de la Newsletter**
- Sections non vides
- Ordre de tri cohérent
- Scores affichés réalistes (pas de 0.0)

---

## 🔍 SCRIPT D'ANALYSE POST-VALIDATION

### Analyse Automatisée des Résultats

```python
#!/usr/bin/env python3
"""
Script d'analyse des résultats de validation E2E
"""

import json
import statistics

def analyze_curated_results(file_path):
    """Analyse les résultats curated post-correction"""
    
    with open(file_path, 'r') as f:
        items = json.load(f)
    
    print(f"=== ANALYSE VALIDATION E2E ===")
    print(f"Items analysés: {len(items)}")
    
    # Analyse des scores
    scores = []
    items_with_score = 0
    items_with_errors = 0
    
    for item in items:
        scoring_results = item.get("scoring_results", {})
        final_score = scoring_results.get("final_score", 0)
        
        if "error" in scoring_results:
            items_with_errors += 1
            print(f"❌ Erreur: {item.get('item_id')} - {scoring_results.get('error')}")
        
        if final_score > 0:
            items_with_score += 1
            scores.append(final_score)
    
    print(f"\n📊 Résultats Scoring:")
    print(f"   Items avec final_score > 0: {items_with_score}/{len(items)} ({items_with_score/len(items)*100:.1f}%)")
    print(f"   Items avec erreurs: {items_with_errors}")
    
    if scores:
        print(f"   Score min: {min(scores):.1f}")
        print(f"   Score max: {max(scores):.1f}")
        print(f"   Score moyen: {statistics.mean(scores):.1f}")
        print(f"   Score médian: {statistics.median(scores):.1f}")
        
        # Items sélectionnables
        selectable = [s for s in scores if s >= 12]
        print(f"   Items sélectionnables (>= 12): {len(selectable)}/{len(items)} ({len(selectable)/len(items)*100:.1f}%)")
    
    # Analyse de cohérence lai_score ↔ final_score
    print(f"\n🔗 Cohérence LAI ↔ Final:")
    lai_final_pairs = []
    
    for item in items:
        lai_score = item.get("normalized_content", {}).get("lai_relevance_score", 0)
        final_score = item.get("scoring_results", {}).get("final_score", 0)
        lai_final_pairs.append((lai_score, final_score))
    
    # Tri par lai_score décroissant
    lai_final_pairs.sort(key=lambda x: x[0], reverse=True)
    
    for lai, final in lai_final_pairs[:10]:  # Top 10
        status = "✅" if (lai >= 8 and final >= 12) or (lai <= 5 and final <= 8) else "⚠️"
        print(f"   {status} LAI: {lai:2d} → Final: {final:5.1f}")
    
    return items_with_score > 0 and items_with_errors == 0

if __name__ == "__main__":
    success = analyze_curated_results("curated_items_post_fix.json")
    print(f"\n🏆 VALIDATION: {'✅ SUCCÈS' if success else '❌ ÉCHEC'}")
```

---

## 📋 CHECKLIST DE VALIDATION

### Pré-Validation

- [ ] Layer vectora-core mise à jour avec scorer.py corrigé
- [ ] Lambda normalize-score-v2 utilise la nouvelle layer
- [ ] Aucune modification de configuration (lai_weekly_v4.yaml)
- [ ] Newsletter V2 avec rollback des bidouilles effectué

### Exécution

- [ ] Ingest-v2 exécuté avec succès (StatusCode: 200)
- [ ] Normalize-score-v2 exécuté avec succès (StatusCode: 200)
- [ ] Aucune erreur dans CloudWatch Logs
- [ ] Items curated générés dans S3

### Validation Résultats

- [ ] final_score > 0 pour items avec matched_domains
- [ ] Distribution des scores cohérente (pas tous à 0.0)
- [ ] Items LAI forts ont final_score >= 12
- [ ] Corrélation positive lai_relevance_score ↔ final_score

### Test Newsletter

- [ ] Newsletter-v2 exécutée avec succès
- [ ] Items sélectionnés (pas de newsletter vide)
- [ ] Scores affichés réalistes dans Markdown
- [ ] Ordre de tri cohérent par final_score

---

## 🎯 RÉSULTATS ATTENDUS

### Avant Correction (Référence)

```json
{
  "items_processed": 15,
  "items_with_final_score_gt_0": 0,
  "newsletter_items_selected": 0,
  "status": "❌ Pipeline cassé"
}
```

### Après Correction (Objectif)

```json
{
  "items_processed": 15,
  "items_with_final_score_gt_0": 8,
  "items_selectable_score_gte_12": 6,
  "newsletter_items_selected": 6,
  "score_distribution": {
    "min": 0.0,
    "max": 18.5,
    "mean": 7.2,
    "median": 5.1
  },
  "status": "✅ Pipeline fonctionnel"
}
```

---

## 🔄 ACTIONS POST-VALIDATION

### Si Validation Réussie

1. **Documentation mise à jour**
   - Marquer la correction comme validée
   - Mettre à jour les métriques de référence
   - Documenter les nouveaux seuils de performance

2. **Monitoring renforcé**
   - Alertes sur final_score = 0 pour items LAI
   - Métriques de distribution des scores
   - Surveillance taux de sélection newsletter

3. **Communication**
   - Informer que le pipeline LAI est opérationnel
   - Documenter les améliorations de qualité
   - Planifier déploiement sur autres clients

### Si Validation Échouée

1. **Diagnostic approfondi**
   - Analyser les logs détaillés
   - Identifier les cas d'échec restants
   - Vérifier la version de layer déployée

2. **Correction additionnelle**
   - Retour en Phase 4 si nécessaire
   - Tests unitaires supplémentaires
   - Validation locale renforcée

3. **Rollback si critique**
   - Restaurer version précédente si instabilité
   - Analyser impact sur autres clients
   - Planifier nouvelle tentative

---

## 🏆 CONCLUSION PHASE 5

La Phase 5 valide que la correction du scoring V2 fonctionne en conditions réelles de production. 

**Succès attendu :**
- Pipeline lai_weekly_v4 entièrement fonctionnel
- Newsletter V2 génère du contenu LAI pertinent
- Architecture propre sans bidouilles côté newsletter

**Impact métier :**
- Passage de 0% à 40-53% d'items sélectionnables
- Qualité de newsletter améliorée
- Scoring cohérent avec la pertinence LAI

---

*Validation E2E Scoring V2 - Phase 5*  
*Confirmation production de la correction*