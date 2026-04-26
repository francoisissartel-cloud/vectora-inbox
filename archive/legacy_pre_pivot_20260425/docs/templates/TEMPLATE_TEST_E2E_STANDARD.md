# Template Test E2E Standard - Vectora Inbox

**Version Template** : 1.0  
**Date création** : 2026-01-30  
**Usage** : Test end-to-end complet du workflow Vectora Inbox

---

## 📋 MÉTADONNÉES DU TEST

**Client testé** : [lai_weekly_vX]  
**Date exécution** : [YYYY-MM-DD]  
**Environnement** : [dev/stage/prod]  
**Durée totale** : [XX minutes]  
**Statut** : [✅ SUCCÈS / ⚠️ PARTIEL / ❌ ÉCHEC]  
**Testeur** : [Nom]  
**Objectif** : [Validation baseline / Test après modification / Comparaison versions]

---

## 🎯 RÉSUMÉ EXÉCUTIF (5 minutes de lecture)

### Métriques Clés

```
Métrique                          | Valeur        | vs Baseline | Statut
----------------------------------|---------------|-------------|--------
Items ingérés                     | XX            | +X%         | ✅/⚠️/❌
Items normalisés                  | XX (XX%)      | +X%         | ✅/⚠️/❌
Items matchés                     | XX (XX%)      | +X%         | ✅/⚠️/❌
Items newsletter                  | XX (XX%)      | +X%         | ✅/⚠️/❌
Temps total E2E                   | XXs           | +Xs         | ✅/⚠️/❌
Coût total                        | $X.XX         | +$X.XX      | ✅/⚠️/❌
Taux succès pipeline              | XX%           | +X%         | ✅/⚠️/❌
```

### Funnel de Conversion

```
Étape                    | Volume | Taux conv | Taux perte | vs Baseline
-------------------------|--------|-----------|------------|-------------
Sources scrapées         | X      | -         | -          | -
Items ingérés            | XX     | 100%      | 0%         | +X%
Items dédupliqués        | XX     | XX%       | XX%        | +X%
Items normalisés         | XX     | XX%       | XX%        | +X%
Items matchés            | XX     | XX%       | XX%        | +X%
Items après dédup v2     | XX     | XX%       | XX%        | +X%
Items newsletter         | XX     | XX%       | XX%        | +X%
```

### Verdict Global

**✅ D'ACCORD** / **❌ PAS D'ACCORD** avec la performance du moteur

**Justification en 3 points** :
1. [Point fort principal]
2. [Point d'amélioration principal]
3. [Décision recommandée]

---

## 📊 PHASE 1 : INGESTION

### Commande Exécutée

```bash
[Commande exacte utilisée]
```

### Métriques Ingestion

**Volume** :
- Items récupérés : XX items
- Items dédupliqués : XX items (XX%)
- Items filtrés : XX items (XX%)
- Items finaux : XX items

**Performance** :
- Temps total : XXs
- Temps moyen/source : Xs
- Taux succès sources : XX% (X/X sources)

**Sources Scrapées** :

```
Source                          | Type      | Items | Statut | vs Baseline
--------------------------------|-----------|-------|--------|-------------
[source_1]                      | corporate | X     | ✅     | +X
[source_2]                      | press     | X     | ✅     | +X
[source_3]                      | corporate | X     | ❌     | -X
```

### Distribution Word Count

```
Range        | Count | %    | vs Baseline
-------------|-------|------|-------------
0-10 mots    | X     | XX%  | +X%
11-20 mots   | X     | XX%  | +X%
21-50 mots   | X     | XX%  | +X%
51+ mots     | X     | XX%  | +X%
```

### Items Pertinents LAI Identifiés

**Haute pertinence** (X items) :
1. ✅ [Titre item] (XX mots) - [Raison pertinence]
2. ✅ [Titre item] (XX mots) - [Raison pertinence]

**Bruit détecté** (X items) :
- Items trop courts : X items (<20 mots)
- Items hors-sujet : X items
- Items génériques : X items

### Fichier Généré

**Path S3** : `s3://vectora-inbox-data-dev/ingested/[client]/[date]/items.json`  
**Taille** : XX KB  
**Structure** : ✅ Conforme / ❌ Problème détecté

---

## 📊 PHASE 2 : NORMALISATION & SCORING

### Commande Exécutée

```bash
[Commande exacte utilisée]
```

### Métriques Normalisation

**Volume** :
- Items input : XX items
- Items normalisés : XX items (XX%)
- Items erreur : XX items (XX%)

**Performance** :
- Temps total : XXs
- Temps moyen/item : Xs
- Appels Bedrock : XX (XX normalisation + XX matching)

**Extraction Entités** :

```
Type         | Total | Moyenne/item | Items avec | vs Baseline
-------------|-------|--------------|------------|-------------
Molecules    | X     | X.XX         | X (XX%)    | +X
Trademarks   | X     | X.XX         | X (XX%)    | +X
Companies    | X     | X.XX         | X (XX%)    | +X
Technologies | X     | X.XX         | X (XX%)    | +X
```

### Event Classification

```
Event Type           | Count | %    | vs Baseline
---------------------|-------|------|-------------
regulatory           | X     | XX%  | +X%
partnership          | X     | XX%  | +X%
clinical_update      | X     | XX%  | +X%
corporate_move       | X     | XX%  | +X%
financial_results    | X     | XX%  | +X%
safety_signal        | X     | XX%  | +X%
other                | X     | XX%  | +X%
```

### LAI Relevance Scores

```
LAI Score    | Count | %    | vs Baseline
-------------|-------|------|-------------
10           | X     | XX%  | +X%
9            | X     | XX%  | +X%
8            | X     | XX%  | +X%
7            | X     | XX%  | +X%
5-6          | X     | XX%  | +X%
0-4          | X     | XX%  | +X%
```

**Statistiques** :
- Score moyen : X.X (vs X.X baseline)
- Score médian : X.X (vs X.X baseline)
- High relevance (≥8) : XX items (XX%)

### Matching Results

**Volume matching** :
- Items à matcher : XX items
- Items matchés : XX items (XX%)
- Items non-matchés : XX items (XX%)

**Domaine tech_lai_ecosystem** :

```
Confidence   | Count | %    | Score range | vs Baseline
-------------|-------|------|-------------|-------------
high         | X     | XX%  | 0.7-0.8     | +X%
medium       | X     | XX%  | 0.6         | +X%
low          | X     | XX%  | 0.25-0.5    | +X%
```

### Scoring Results

**Distribution scores finaux** :

```
Score Range    | Count | %    | Catégorie   | vs Baseline
---------------|-------|------|-------------|-------------
12.0-15.0      | X     | XX%  | Excellent   | +X%
10.0-11.9      | X     | XX%  | Très bon    | +X%
6.0-9.9        | X     | XX%  | Moyen       | +X%
3.0-5.9        | X     | XX%  | Faible      | +X%
0.0-2.9        | X     | XX%  | Très faible | +X%
```

**Statistiques** :
- Score min : X.X
- Score max : X.X
- Score moyen : X.X (vs X.X baseline)
- Score médian : X.X (vs X.X baseline)

### Fichier Généré

**Path S3** : `s3://vectora-inbox-data-dev/curated/[client]/[date]/items.json`  
**Taille** : XX KB (vs XX KB ingested = ×X.X enrichissement)  
**Structure** : ✅ Conforme / ❌ Problème détecté

---

## 📊 PHASE 3 : GÉNÉRATION NEWSLETTER

### Commande Exécutée

```bash
[Commande exacte utilisée]
```

### Sélection Items

**Funnel sélection** :

```
Étape                    | Volume | Taux    | vs Baseline
-------------------------|--------|---------|-------------
Items curated            | XX     | 100%    | +X%
Items matchés            | XX     | XX%     | +X%
Items après dédup        | XX     | XX%     | +X%
Items sélectionnés       | XX     | XX%     | +X%
```

**Déduplication v2** :
- Items dédupliqués : X items
- Similarity threshold : 0.XX
- Company-based dedup : ✅ Activé / ❌ Désactivé

### Répartition Sections

```
Section              | Max | Sélectionnés | Fill Rate | Trimés | vs Baseline
---------------------|-----|--------------|-----------|--------|-------------
regulatory_updates   | X   | X            | XX%       | X      | +X
partnerships_deals   | X   | X            | XX%       | X      | +X
clinical_updates     | X   | X            | XX%       | X      | +X
others               | X   | X            | XX%       | X      | +X
```

### Génération Éditoriale Bedrock

**TL;DR generation** :
- Status : ✅ Success / ❌ Échec
- Bullets : X
- Qualité : [Excellent/Bon/Moyen/Faible]

**Introduction generation** :
- Status : ✅ Success / ❌ Échec
- Longueur : X paragraphes
- Ton : [Exécutif/Technique/Autre]

**Performance** :
- Temps total : ~Xs
- Appels Bedrock : X (TL;DR + Introduction)

### Fichiers Générés

**Path S3** : `s3://vectora-inbox-newsletters-dev/[client]/[date]/`

**Fichiers** :
- `newsletter.md` (XX KB) - Newsletter Markdown
- `newsletter.json` - Newsletter JSON structuré
- `manifest.json` - Métadonnées génération

---

## 🔍 ANALYSE ITEM PAR ITEM

### Items Sélectionnés Newsletter (Top X)

---

#### Item #1 : [TITRE]

**Source** : [source_key]  
**Titre** : "[titre complet]"  
**Date** : [YYYY-MM-DD]  
**URL** : [url]

##### Décisions Moteur

- **Normalisé** : ✅ Oui / ❌ Non
- **Domaine matché** : [tech_lai_ecosystem] (score X.X, confidence [high/medium/low])
- **Score final** : XX.X/20
- **Sélectionné newsletter** : ✅ Oui (rang #X)
- **Section newsletter** : [regulatory_updates/partnerships_deals/clinical_updates/others]

##### Justifications Moteur

- **Normalisation** : [Résumé des entités extraites et classification]
- **Matching** : "[Citation justification Bedrock]"
- **Scoring** : Base X + [bonus_1] (+X.X) + [bonus_2] (+X.X) = XX.X
- **Sélection** : [Raison inclusion : score élevé, event critique, etc.]

##### Évaluation Humaine

✅ **D'ACCORD** avec toutes les décisions du moteur  
❌ **PAS D'ACCORD** avec certaines décisions

**Détail des désaccords** :
- [ ] Normalisation incorrecte
- [ ] Matching incorrect (mauvais domaine)
- [ ] Score trop élevé/trop bas
- [ ] Sélection newsletter incorrecte
- [ ] Section incorrecte (devrait être [autre_section])
- [ ] Autre : _______________

**Commentaire** :  
_[Espace pour commentaire détaillé]_

---

[Répéter pour chaque item sélectionné]

---

### Items Matchés Non Sélectionnés (X items)

---

#### Item #X : [TITRE]

**Source** : [source_key]  
**Titre** : "[titre complet]"  
**Date** : [YYYY-MM-DD]

##### Décisions Moteur

- **Normalisé** : ✅ Oui
- **Domaine matché** : [domaine] (score X.X, confidence [level])
- **Score final** : X.X/20
- **Sélectionné newsletter** : ❌ Non (score trop faible / trimé)
- **Raison exclusion** : [Raison précise]

##### Justifications Moteur

- **Normalisation** : [Résumé]
- **Matching** : "[Citation]"
- **Scoring** : [Breakdown]
- **Sélection** : [Raison exclusion]

##### Évaluation Humaine

✅ **D'ACCORD** avec l'exclusion newsletter  
❌ **PAS D'ACCORD** avec les décisions du moteur

**Détail des désaccords** :
- [ ] Normalisation incorrecte
- [ ] Matching incorrect
- [ ] Score trop élevé/trop bas
- [ ] Devrait être sélectionné
- [ ] Autre : _______________

**Commentaire** :  
_[Espace pour commentaire détaillé]_

---

[Répéter pour items matchés non sélectionnés significatifs]

---

### Items Non Matchés (X items)

#### Validation des Rejets

**Ces items ont été correctement rejetés par le matching (score <0.25)** :

1. **[Titre]** - Score X.X - [Raison rejet]
2. **[Titre]** - Score X.X - [Raison rejet]
3. **[Titre]** - Score X.X - [Raison rejet]

##### Évaluation Globale des Rejets

✅ **D'ACCORD** - Tous les rejets sont justifiés  
❌ **PAS D'ACCORD** - Certains items auraient dû être matchés

**Items qui auraient dû être matchés** :  
_[Lister les items mal rejetés]_

**Commentaire** :  
_[Espace pour commentaire sur la qualité du filtrage]_

---

## 📈 MÉTRIQUES DE PERFORMANCE

### Métriques Techniques

```
Métrique                          | Valeur        | Objectif    | Statut
----------------------------------|---------------|-------------|--------
Temps d'exécution E2E             | XXs           | <600s       | ✅/❌
Coût par run                      | $X.XX         | <$2.00      | ✅/❌
Taux de succès Bedrock            | XX%           | >95%        | ✅/❌
Taux de matching                  | XX%           | >50%        | ✅/❌
Précision matching                | XX%           | >80%        | ✅/❌
```

### Métriques Qualité

```
Métrique                          | Valeur        | Objectif    | Statut
----------------------------------|---------------|-------------|--------
Items haute qualité newsletter    | XX%           | >70%        | ✅/❌
Signaux LAI pertinents            | XX%           | >90%        | ✅/❌
Diversité sources                 | XX%           | >60%        | ✅/❌
Sections newsletter remplies      | XX%           | >75%        | ✅/❌
```

### Métriques Business

```
Métrique                          | Valeur        | Objectif    | Statut
----------------------------------|---------------|-------------|--------
ROI vs alternatives               | XX%           | >90%        | ✅/❌
Newsletter prête publication      | Oui/Non       | Oui         | ✅/❌
Scalabilité (items max)           | XX items      | >50 items   | ✅/❌
```

---

## 💰 ANALYSE COÛTS DÉTAILLÉE

### Coûts Bedrock

**Appels par type** :

```
Type Appel           | Nombre | Tokens In | Tokens Out | Coût Unit | Coût Total
---------------------|--------|-----------|------------|-----------|------------
Normalisation        | XX     | ~XXXX     | ~XXX       | $X.XXX    | $X.XX
Matching             | XX     | ~XXXX     | ~XXX       | $X.XXX    | $X.XX
TL;DR                | X      | ~XXXX     | ~XXX       | $X.XXX    | $X.XX
Introduction         | X      | ~XXXX     | ~XXX       | $X.XXX    | $X.XX
TOTAL                | XX     | ~XXXX     | ~XXX       | -         | $X.XX
```

**Modèle** : `anthropic.claude-3-5-sonnet-20240229-v1:0`  
**Région** : `us-east-1`  
**Prix** : $3/1M input tokens, $15/1M output tokens

### Coûts AWS

```
Service              | Coût ($)  | % Total
---------------------|-----------|--------
Bedrock              | X.XX      | XX%
Lambda               | X.XX      | XX%
S3                   | X.XX      | XX%
CloudWatch           | X.XX      | XX%
TOTAL                | X.XX      | 100%
```

### Projections

```
Fréquence            | Coût/période | Coût annuel
---------------------|--------------|-------------
Run hebdomadaire     | $X.XX        | $XX.XX
Run bi-hebdomadaire  | $X.XX        | $XX.XX
Run mensuel          | $X.XX        | $XX.XX
```

---

## 🔧 RECOMMANDATIONS D'AMÉLIORATION

### Priorité CRITIQUE (Semaine 1)

#### 1. [Titre Recommandation]

**Problème** : [Description problème observé]  
**Impact** : [Impact sur qualité/coût/performance]  
**Solution** : [Solution proposée]

```yaml
# Exemple de modification config/code
[code ou config proposé]
```

**Impact attendu** :
- Métrique 1 : +X%
- Métrique 2 : -X%

---

### Priorité HAUTE (Mois 1)

#### 2. [Titre Recommandation]

[Même structure que priorité critique]

---

### Priorité MOYENNE (Trimestre 1)

#### 3. [Titre Recommandation]

[Même structure]

---

## 🎯 VALIDATION READINESS PRODUCTION

### ✅ Critères Validés

- [x] Workflow E2E fonctionnel sans erreur critique
- [x] Performance acceptable (<10 minutes)
- [x] Coûts maîtrisés (<$2 par run)
- [x] Qualité signaux LAI élevée (>80% précision)
- [x] Newsletter format professionnel
- [x] Architecture stable

### ⚠️ Critères Partiels

- [x] Volume newsletter suffisant : X items (vs 15-25 souhaités) ⚠️
- [x] Distribution sections équilibrée : X/4 sections remplies ⚠️
- [x] Diversité temporelle : [Statut] ⚠️

### 🔧 Actions Requises Avant Production

1. **[Action 1]** (Priorité Critique)
2. **[Action 2]** (Priorité Haute)
3. **[Action 3]** (Priorité Moyenne)

---

## 📋 DÉCISION FINALE

### Statut Global du Moteur

🟢 **MOTEUR PRÊT POUR PRODUCTION**  
🟡 **MOTEUR PRÊT AVEC AJUSTEMENTS MINEURS**  
🔴 **MOTEUR NON PRÊT - CORRECTIONS MAJEURES REQUISES**

### Justification

**Points forts** :
1. [Point fort 1]
2. [Point fort 2]
3. [Point fort 3]

**Points d'amélioration** :
1. [Point amélioration 1]
2. [Point amélioration 2]
3. [Point amélioration 3]

**Risques identifiés** :
1. [Risque 1]
2. [Risque 2]

### Recommandation

✅ **DÉPLOIEMENT PRODUCTION RECOMMANDÉ** après correction des X points priorité critique  
⚠️ **DÉPLOIEMENT CONDITIONNEL** après validation des corrections  
❌ **DÉPLOIEMENT NON RECOMMANDÉ** - Corrections majeures requises

### Timeline Recommandée

- **Semaine 1** : [Actions]
- **Semaine 2** : [Actions]
- **Semaine 3** : [Actions]
- **Mois 1** : [Actions]

---

## 💬 FEEDBACK UTILISATEUR

### Évaluation Globale de ce Test

Ce test E2E vous a-t-il permis d'évaluer correctement les décisions du moteur ?

✅ **OUI** - Le format est adapté et complet  
❌ **NON** - Des améliorations sont nécessaires

### Suggestions d'Amélioration du Test

_[Espace pour suggestions sur le format, le contenu, la structure]_

### Commentaires Généraux sur le Moteur

_[Espace pour commentaires généraux sur la performance du moteur Vectora-Inbox]_

---

## 📎 ANNEXES

### Fichiers Générés

- `ingested_items.json` - Items ingérés bruts
- `curated_items.json` - Items enrichis normalisés
- `newsletter.md` - Newsletter finale Markdown
- `newsletter.json` - Newsletter finale JSON
- `manifest.json` - Métadonnées génération

### Commandes Utilisées

```bash
# Ingestion
[commande]

# Normalisation
[commande]

# Newsletter
[commande]

# Téléchargement S3
[commandes]
```

### Logs Pertinents

```
[Extraits de logs CloudWatch si pertinent]
```

---

**Document généré le** : [YYYY-MM-DD]  
**Version Template** : 1.0  
**Prochaine évaluation** : [Date]  
**Contact** : Équipe Vectora-Inbox pour questions techniques
