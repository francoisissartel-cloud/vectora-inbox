# Template Test E2E - Vectora Inbox

**Date**: YYYY-MM-DD  
**Client**: [CLIENT_ID] (ex: lai_weekly_v8)  
**Version moteur**: [VERSION] (ex: 1.3.2)  
**Durée totale**: [X] secondes  
**Statut**: [✅ SUCCÈS / ❌ ÉCHEC / ⚠️ PARTIEL]

---

## 📊 MÉTRIQUES GLOBALES

### Funnel de Conversion
```
Étape                    | Volume | Taux conv | Taux perte | Temps (s)
-------------------------|--------|-----------|------------|----------
Sources scrapées         | [X]    | -         | -          | [X]
Items ingérés            | [X]    | [X]%      | [X]%       | [X]
Items dédupliqués        | [X]    | [X]%      | [X]%       | -
Items normalisés         | [X]    | [X]%      | [X]%       | [X]
Items matchés            | [X]    | [X]%      | [X]%       | -
Items sélectionnés       | [X]    | [X]%      | [X]%       | [X]
TOTAL E2E                | -      | [X]%      | [X]%       | [X]
```

### Performance Technique
```
Métrique                 | Valeur    | Objectif  | Statut
-------------------------|-----------|-----------|--------
Temps total E2E          | [X]s      | <300s     | [✅/❌]
Coût total               | $[X]      | <$1.00    | [✅/❌]
Appels Bedrock           | [X]       | <100      | [✅/❌]
Taux succès Bedrock      | [X]%      | 100%      | [✅/❌]
Taux matching            | [X]%      | >50%      | [✅/❌]
```

### Qualité Signal
```
Métrique                 | Valeur    | Objectif  | Statut
-------------------------|-----------|-----------|--------
LAI score moyen          | [X]/10    | >7.0      | [✅/❌]
Items haute qualité      | [X]%      | >70%      | [✅/❌]
Hallucinations Bedrock   | [X]       | 0         | [✅/❌]
Sections newsletter      | [X]/4     | 3+        | [✅/❌]
Diversité sources        | [X]%      | >60%      | [✅/❌]
```

---

## 🔍 ANALYSE DÉTAILLÉE PAR PHASE

### Phase 1: Ingestion ([X]s - [X]% du temps total)

**Sources configurées**: [X] sources
**Bouquets activés**: [Liste des bouquets]

```
Source                   | Type      | Items | Statut | Qualité
-------------------------|-----------|-------|--------|--------
[source_1]               | corporate | [X]   | [✅/❌] | [A/B/C]
[source_2]               | press     | [X]   | [✅/❌] | [A/B/C]
```

**Problèmes identifiés**:
- [ ] Items trop courts (<10 mots): [X] items
- [ ] Contenu générique: [X] items  
- [ ] Extraction PDF échouée: [X] items
- [ ] Doublons détectés: [X] items

### Phase 2: Normalisation ([X]s - [X]% du temps total)

**Configuration Bedrock**:
- Modèle: [MODEL_ID]
- Région: [REGION]
- Prompt: [PROMPT_NAME]

**Extraction entités**:
```
Type         | Total | Moyenne/item | Items avec | Exemples
-------------|-------|--------------|------------|----------
Companies    | [X]   | [X]          | [X] ([X]%) | [Liste]
Molecules    | [X]   | [X]          | [X] ([X]%) | [Liste]
Technologies | [X]   | [X]          | [X] ([X]%) | [Liste]
Trademarks   | [X]   | [X]          | [X] ([X]%) | [Liste]
```

**Event classification**:
```
Event Type           | Count | %    | Score moyen
---------------------|-------|------|------------
regulatory           | [X]   | [X]% | [X]
partnership          | [X]   | [X]% | [X]
clinical_update      | [X]   | [X]% | [X]
corporate_move       | [X]   | [X]% | [X]
financial_results    | [X]   | [X]% | [X]
other                | [X]   | [X]% | [X]
```

**LAI Relevance Distribution**:
```
LAI Score    | Count | %    | Interprétation
-------------|-------|------|--------------------------------
9-10         | [X]   | [X]% | Très haute pertinence LAI
7-8          | [X]   | [X]% | Haute pertinence LAI
5-6          | [X]   | [X]% | Pertinence LAI moyenne
3-4          | [X]   | [X]% | Pertinence LAI faible
0-2          | [X]   | [X]% | Aucune pertinence LAI
```

**Matching results**:
```
Domaine              | Matchés | Taux    | Confidence
---------------------|---------|---------|------------
tech_lai_ecosystem   | [X]     | [X]%    | [high/medium/low]
regulatory_lai       | [X]     | [X]%    | [high/medium/low]
```

### Phase 3: Newsletter ([X]s - [X]% du temps total)

**Sélection items**:
```
Section              | Max | Sélectionnés | Fill Rate | Score min
---------------------|-----|--------------|-----------|----------
regulatory_updates   | [X] | [X]          | [X]%      | [X]
partnerships_deals   | [X] | [X]          | [X]%      | [X]
clinical_updates     | [X] | [X]          | [X]%      | [X]
others               | [X] | [X]          | [X]%      | [X]
```

**Génération éditoriale**:
- TL;DR: [✅ Succès / ❌ Échec] - [X] bullets
- Introduction: [✅ Succès / ❌ Échec] - [X] paragraphes
- Sections: [X]/4 remplies

---

## 🎯 ANALYSE ITEM PAR ITEM

### Items Sélectionnés Newsletter ([X] items)

#### Item #1: [TITRE]
**Source**: [source_key] | **Score**: [X]/20 | **Section**: [section]

**Décisions moteur**:
- Normalisé: [✅/❌] - Entités: [liste]
- Matché: [✅/❌] - Domaine: [domaine] (score [X], confidence [level])
- Scoré: [X]/20 - Bonuses: [liste] | Penalties: [liste]
- Sélectionné: [✅/❌] - Rang: #[X]

**Évaluation humaine**:
- [ ] ✅ D'ACCORD avec toutes les décisions
- [ ] ❌ Normalisation incorrecte: [détail]
- [ ] ❌ Matching incorrect: [détail]
- [ ] ❌ Score incorrect: [détail]
- [ ] ❌ Sélection incorrecte: [détail]

**Commentaire**: [Espace pour analyse détaillée]

---

### Items Matchés Non Sélectionnés ([X] items)

#### Item #[X]: [TITRE]
**Source**: [source_key] | **Score**: [X]/20 | **Raison exclusion**: [raison]

**Évaluation humaine**:
- [ ] ✅ D'ACCORD avec l'exclusion
- [ ] ❌ Devrait être sélectionné: [justification]

---

### Items Non Matchés ([X] items)

**Validation des rejets**:
- [ ] ✅ Tous les rejets justifiés
- [ ] ❌ Items mal rejetés: [liste avec justification]

---

## 🔧 ANALYSE DES FICHIERS CANONICAL

### Configuration Client
**Fichier**: `clients/[CLIENT_ID].yaml`

**Paramètres clés**:
```yaml
watch_domains:
  - tech_lai_ecosystem: [paramètres]
  - regulatory_lai: [paramètres]

scoring_config:
  bonuses: [liste]
  penalties: [liste]

newsletter_layout:
  sections: [X] sections configurées
```

### Scopes Utilisés
**Fichiers canonical**:
- `lai_companies_global.yaml`: [X] companies
- `lai_molecules_global.yaml`: [X] molecules  
- `lai_keywords.yaml`: [X] keywords
- `lai_trademarks_global.yaml`: [X] trademarks

**Efficacité scopes**:
- Companies détectées: [X]% des items
- Molecules détectées: [X]% des items
- Technologies détectées: [X]% des items

### Prompts Bedrock
**Normalisation**: `canonical/prompts/normalization/[PROMPT].yaml`
**Matching**: `canonical/prompts/matching/[PROMPT].yaml`

**Résolution {{ref:}}**: [✅ Succès / ❌ Échec]

---

## 📈 COMPARAISON HISTORIQUE

### Évolution Métriques (vs version précédente)
```
Métrique                 | Actuel | Précédent | Évolution
-------------------------|--------|-----------|----------
Taux conversion E2E      | [X]%   | [Y]%      | [+/-Z]%
Coût par run             | $[X]   | $[Y]      | [+/-$Z]
Temps E2E                | [X]s   | [Y]s      | [+/-Z]s
LAI score moyen          | [X]    | [Y]       | [+/-Z]
Taux matching            | [X]%   | [Y]%      | [+/-Z]%
```

### Améliorations Observées
- [✅ Amélioration 1]: [description et impact]
- [✅ Amélioration 2]: [description et impact]

### Régressions Observées  
- [❌ Régression 1]: [description et impact]
- [❌ Régression 2]: [description et impact]

---

## 🚨 PROBLÈMES IDENTIFIÉS

### Priorité CRITIQUE
1. **[Problème 1]**: [Description]
   - Impact: [impact]
   - Solution: [solution proposée]
   - Effort: [estimation]

### Priorité HAUTE
1. **[Problème 1]**: [Description]
   - Impact: [impact]  
   - Solution: [solution proposée]
   - Effort: [estimation]

### Priorité MOYENNE
1. **[Problème 1]**: [Description]
   - Impact: [impact]
   - Solution: [solution proposée]
   - Effort: [estimation]

---

## 🎯 RECOMMANDATIONS

### Actions Immédiates (Semaine 1)
- [ ] [Action 1]: [description et justification]
- [ ] [Action 2]: [description et justification]

### Actions Court Terme (Mois 1)
- [ ] [Action 1]: [description et justification]
- [ ] [Action 2]: [description et justification]

### Actions Long Terme (Trimestre 1)
- [ ] [Action 1]: [description et justification]
- [ ] [Action 2]: [description et justification]

---

## 📋 DÉCISION FINALE

### Statut Global du Moteur
🟢 **MOTEUR EXCELLENT** - Prêt production  
🟡 **MOTEUR BON** - Ajustements mineurs requis  
🟠 **MOTEUR MOYEN** - Améliorations nécessaires  
🔴 **MOTEUR PROBLÉMATIQUE** - Corrections majeures requises  

### Justification
**Points forts**:
- [Point fort 1]
- [Point fort 2]

**Points d'amélioration**:
- [Point amélioration 1]
- [Point amélioration 2]

### Recommandation Déploiement
- [ ] ✅ **DÉPLOIEMENT IMMÉDIAT** recommandé
- [ ] ⚠️ **DÉPLOIEMENT CONDITIONNEL** après corrections [liste]
- [ ] ❌ **DÉPLOIEMENT DIFFÉRÉ** jusqu'à résolution [problèmes]

---

## 💬 FEEDBACK UTILISATEUR

### Évaluation Template
Ce template vous permet-il d'évaluer efficacement le moteur ?
- [ ] ✅ OUI - Format adapté et complet
- [ ] ❌ NON - Améliorations nécessaires: [détails]

### Métriques Manquantes
Quelles métriques ajouteriez-vous ?
- [Métrique 1]: [justification]
- [Métrique 2]: [justification]

### Commentaires Généraux
[Espace pour feedback sur le moteur et le template]

---

**Template Test E2E - Version 1.0**  
**Créé le**: 2026-01-31  
**Usage**: Copier ce template pour chaque test E2E  
**Objectif**: Standardiser l'évaluation et permettre comparaisons temporelles