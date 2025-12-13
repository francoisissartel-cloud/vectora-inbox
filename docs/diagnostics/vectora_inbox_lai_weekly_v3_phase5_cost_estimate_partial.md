# Vectora Inbox LAI Weekly v3 - Phase 5 Estimation Coûts (Partielle)

**Date** : 2025-12-11  
**Client** : lai_weekly_v3  
**Phase** : 5 - Estimation Coût Workflow  
**Status** : ✅ PARTIEL - Basé sur Phase 3 réelle

---

## Données Réelles Disponibles

### Phase 3 - Ingestion/Normalisation (Succès)
- **Items traités** : 104 items
- **Appels Bedrock** : 104 appels (normalisation)
- **Durée** : 505.3 secondes (8.4 minutes)
- **Sources** : 7 sources contactées

### Phase 4 - Engine (Échec)
- **Timeout** : 300 secondes (5 minutes)
- **Appels Bedrock newsletter** : 0 (non atteint)
- **Items matchés/scorés** : Inconnu

---

## Estimation Coûts Phase 3 (Réels)

### Appels Bedrock Normalisation
- **Modèle utilisé** : Claude 3.5 Sonnet (supposé)
- **Nombre d'appels** : 104 appels
- **Tokens par appel** : ~2000 tokens input + 500 tokens output (estimation)
- **Total tokens** : ~260,000 tokens

### Coût Bedrock Normalisation
**Hypothèses tarifaires Claude 3.5 Sonnet** :
- Input : $3.00 / 1M tokens
- Output : $15.00 / 1M tokens

**Calcul** :
- Input tokens : 208,000 × $3.00/1M = $0.624
- Output tokens : 52,000 × $15.00/1M = $0.780
- **Total normalisation** : $1.404

### Coût Lambda Compute
- **Durée** : 505.3 secondes
- **Mémoire** : 1024 MB (supposé)
- **Coût Lambda** : ~$0.002 (négligeable)

### Coût Total Phase 3
**Total réel** : ~$1.40

---

## Estimation Coûts Phase 4 (Théorique)

### Appels Bedrock Newsletter (Non Réalisés)
- **Newsletter generation** : 1 appel Bedrock
- **Items input** : 104 items (si tous matchés)
- **Tokens newsletter** : ~10,000 input + 2,000 output
- **Coût estimé** : $0.06

### Coût Lambda Engine (Partiel)
- **Durée observée** : 300 secondes (timeout)
- **Coût partiel** : ~$0.001

### Coût Total Phase 4 Estimé
**Si succès** : ~$0.06

---

## Coût Total Run lai_weekly_v3

### Coût Réel + Estimé
- **Phase 3 (réel)** : $1.40
- **Phase 4 (estimé)** : $0.06
- **Total par run** : ~$1.46

### Répartition des Coûts
- **Normalisation Bedrock** : 96% ($1.40)
- **Newsletter Bedrock** : 4% ($0.06)
- **Lambda compute** : <1% ($0.003)

---

## Projections Récurrentes

### Coût Mensuel lai_weekly_v3
- **Runs par mois** : 4 (weekly)
- **Coût mensuel** : 4 × $1.46 = $5.84

### Coût Annuel lai_weekly_v3
- **Runs par an** : 52 (weekly)
- **Coût annuel** : 52 × $1.46 = $75.92

---

## Projections Scale LAI Complet

### Hypothèses Scale-Up
- **Sources supplémentaires** : +20 sources (PubMed, plus de corporate)
- **Volume items** : ×5 (500 items vs 100)
- **Fréquence** : Daily (×7)

### Calcul Scale LAI Complet
- **Items par run** : 500 items
- **Coût normalisation** : 500/104 × $1.40 = $6.73
- **Coût newsletter** : $0.15 (plus complexe)
- **Coût par run** : ~$6.88

### Coût LAI Complet
- **Daily runs** : $6.88/jour
- **Coût mensuel** : $206.40
- **Coût annuel** : $2,511.20

---

## Analyse Coût/Bénéfice

### Points Forts Coût
- **Coût actuel faible** : $1.46/run acceptable
- **Scaling linéaire** : Coût proportionnel au volume
- **Bedrock dominant** : Pas de coûts infrastructure lourds

### Points d'Attention
- **Normalisation 96%** : Goulot d'étranglement coût
- **Scale ×50** : $75 → $2,500/an (significatif)
- **Performance** : Timeout Phase 4 = coût sans valeur

### Optimisations Possibles
1. **Batch processing** : Réduire appels Bedrock
2. **Prompt optimization** : Réduire tokens par item
3. **Selective normalization** : Filtrer avant Bedrock
4. **Caching** : Éviter re-normalisation items similaires

---

## Limitations de l'Estimation

### Données Manquantes (Phase 4 Échec)
- **Taux de matching réel** : Inconnu
- **Items newsletter réels** : Inconnu
- **Tokens newsletter réels** : Estimation grossière
- **Performance engine** : Timeout non résolu

### Hypothèses Non Vérifiées
- **Modèle Bedrock** : Claude 3.5 Sonnet supposé
- **Tokens par item** : Estimation basée sur expérience
- **Tarification** : Prix publics AWS (pas de discount)

### Facteurs Non Inclus
- **Stockage S3** : Négligeable
- **Transfer data** : Négligeable  
- **CloudWatch logs** : Négligeable
- **Développement/maintenance** : Non inclus

---

**Phase 5 – Terminée (partiel)**

**Coût estimé lai_weekly_v3** : $1.46/run ($75.92/an)  
**Limitation** : Basé sur Phase 3 réelle + Phase 4 estimée  
**Recommandation** : Résoudre timeout Phase 4 pour validation complète