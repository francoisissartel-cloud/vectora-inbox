# Deep Evaluation - Test E2E v11 et Collaboration Q Developer

**Date** : 2026-02-02  
**Contexte** : Analyse post-test E2E lai_weekly_v11  
**Objectif** : Comprendre les lacunes et améliorer la collaboration

---

## 🎯 CE QUI ÉTAIT ATTENDU

### Documentation Existante

**Template E2E Standard** : `docs/templates/TEMPLATE_TEST_E2E_STANDARD.md`
- ✅ Existe depuis 2026-01-30
- ✅ 500+ lignes de structure détaillée
- ✅ Guide d'utilisation complet
- ✅ Métriques quantitatives précises
- ✅ Analyse item par item
- ✅ Comparaison baseline
- ✅ Coûts détaillés par phase

**Règles Q Context** : `.q-context/vectora-inbox-development-rules.md`
- ✅ Section "RÈGLES DE TESTS E2E"
- ✅ Référence explicite au template
- ✅ Workflow standardisé
- ✅ Prompt recommandé pour Q

---

## ❌ CE QUI N'A PAS ÉTÉ FAIT

### 1. Template Standard Ignoré

**Attendu** :
```markdown
## 📊 PHASE 1 : INGESTION

### Métriques Ingestion

**Volume** :
- Items récupérés : 29 items
- Items dédupliqués : 0 items (0%)
- Items filtrés : 0 items (0%)
- Items finaux : 29 items

**Performance** :
- Temps total : 21s
- Temps moyen/source : 10.5s
- Taux succès sources : 100% (2/2 sources)

**Sources Scrapées** :

| Source | Type | Items | Statut | vs Baseline |
|--------|------|-------|--------|-------------|
| source_1 | corporate | 15 | ✅ | +2 |
| source_2 | press | 14 | ✅ | +1 |
```

**Réalisé** :
```markdown
**4. Ingestion** ✅
- Lambda: `vectora-inbox-ingest-v2-dev`
- StatusCode: 200
- Durée: ~21s
```

**Manque** :
- ❌ Détail des sources scrapées
- ❌ Distribution word count
- ❌ Items pertinents vs bruit
- ❌ Comparaison baseline
- ❌ Fichier S3 généré

### 2. Analyse Item par Item Absente

**Attendu** :
```markdown
## 🔍 ANALYSE ITEM PAR ITEM

### Items Sélectionnés Newsletter (Top 29)

#### Item #1 : [TITRE]

**Source** : medincel_corporate
**Titre** : "MedinCell announces partnership with..."
**Date** : 2026-01-28
**URL** : https://...

##### Décisions Moteur

- **Normalisé** : ✅ Oui
- **Domaine matché** : tech_lai_ecosystem (score 0.85, confidence high)
- **Score final** : 12.5/20
- **Sélectionné newsletter** : ❌ Non (0 matches)
- **Section newsletter** : N/A

##### Justifications Moteur

- **Normalisation** : 
  - Companies: ["MedinCell", "Partner X"]
  - Technologies: ["microspheres", "long-acting"]
  - Trademarks: ["UZEDY®"]
  - Event: partnership
  
- **Matching** : "Item rejected: domain_score 0.15 < min_threshold 0.25"
- **Scoring** : Base 8 (partnership) + pure_player (+5.0) + trademark (+4.0) = 17.0
- **Sélection** : Rejeté au matching (score domain trop faible)

##### Évaluation Humaine

❌ **PAS D'ACCORD** avec le rejet

**Détail des désaccords** :
- [x] Matching incorrect (devrait matcher avec score 0.85)
- [x] Score trop bas (17.0 devrait suffire)
- [ ] Autre

**Commentaire** :
Item clairement LAI (MedinCell + UZEDY® + microspheres) rejeté à tort.
Problème probable: prompt domain_scoring trop strict ou seuil min_domain_score trop élevé.
```

**Réalisé** :
```markdown
## ⚠️ Observation Critique

**Items matched: 0**

Tous les items ont été normalisés et scorés, mais **aucun n'a matché** avec le domaine LAI.
```

**Manque** :
- ❌ Analyse des 29 items individuellement
- ❌ Justifications moteur pour chaque item
- ❌ Évaluation humaine (d'accord/pas d'accord)
- ❌ Détail des entités extraites
- ❌ Raisons précises de rejet

### 3. Métriques Quantitatives Manquantes

**Attendu** :
```markdown
## 📈 MÉTRIQUES DE PERFORMANCE

### Métriques Techniques

| Métrique | Valeur | Objectif | Statut |
|----------|--------|----------|--------|
| Temps d'exécution E2E | 170.5s | <600s | ✅ |
| Coût par run | $0.42 | <$2.00 | ✅ |
| Taux de succès Bedrock | 100% | >95% | ✅ |
| Taux de matching | 0% | >50% | ❌ |
| Précision matching | N/A | >80% | ❌ |

### Métriques Qualité

| Métrique | Valeur | Objectif | Statut |
|----------|--------|----------|--------|
| Items haute qualité newsletter | 0% | >70% | ❌ |
| Signaux LAI pertinents | 0% | >90% | ❌ |
| Diversité sources | 100% | >60% | ✅ |
| Sections newsletter remplies | 0% | >75% | ❌ |
```

**Réalisé** :
```markdown
## 📊 Statistiques

```
Items input:      29
Items normalized: 29  (100%)
Items matched:    0   (⚠️ Aucun match)
Items scored:     29  (100%)
Processing time:  147.9s
```
```

**Manque** :
- ❌ Comparaison avec objectifs
- ❌ Statut ✅/❌ pour chaque métrique
- ❌ Métriques qualité
- ❌ Métriques business

### 4. Analyse Coûts Absente

**Attendu** :
```markdown
## 💰 ANALYSE COÛTS DÉTAILLÉE

### Coûts Bedrock

**Appels par type** :

| Type Appel | Nombre | Tokens In | Tokens Out | Coût Unit | Coût Total |
|------------|--------|-----------|------------|-----------|------------|
| Normalisation | 29 | ~1500 | ~300 | $0.0045 | $0.13 |
| Domain scoring | 29 | ~2000 | ~400 | $0.0060 | $0.17 |
| TOTAL | 58 | ~3500 | ~700 | - | $0.30 |

**Modèle** : `anthropic.claude-3-5-sonnet-20240229-v1:0`
**Région** : `us-east-1`
**Prix** : $3/1M input tokens, $15/1M output tokens

### Coûts AWS

| Service | Coût ($) | % Total |
|---------|----------|---------|
| Bedrock | 0.30 | 71% |
| Lambda | 0.08 | 19% |
| S3 | 0.02 | 5% |
| CloudWatch | 0.02 | 5% |
| TOTAL | 0.42 | 100% |
```

**Réalisé** :
```markdown
[Aucune analyse coûts]
```

**Manque** :
- ❌ Coûts Bedrock détaillés
- ❌ Coûts AWS par service
- ❌ Projections (hebdo, mensuel, annuel)
- ❌ Comparaison baseline

### 5. Fichiers S3 Non Analysés

**Attendu** :
```bash
# Télécharger et analyser fichiers S3
aws s3 cp s3://vectora-inbox-data-dev/runs/lai_weekly_v11/latest/ingested_items.json .
aws s3 cp s3://vectora-inbox-data-dev/runs/lai_weekly_v11/latest/normalized_items.json .

# Analyser contenu
python scripts/analysis/analyze_items.py --input normalized_items.json
```

**Réalisé** :
```markdown
### 1. Analyser les items normalisés
```bash
# Télécharger items normalisés depuis S3
aws s3 cp s3://vectora-inbox-data-dev/runs/lai_weekly_v11/latest/normalized_items.json . --profile rag-lai-prod
```
```

**Manque** :
- ❌ Fichiers non téléchargés
- ❌ Contenu non analysé
- ❌ Entités non extraites
- ❌ Scores non examinés

---

## 🔍 ANALYSE DES CAUSES

### Cause 1 : Template Non Utilisé

**Pourquoi** :
- Q n'a pas été explicitement prompté avec référence au template
- Prompt utilisateur : "je veux que tu revienne a # Build & deploy..." (focus sur exécution, pas sur rapport)
- Q a créé un rapport minimal au lieu d'utiliser le template standard

**Impact** :
- Rapport superficiel (150 lignes vs 500+ attendues)
- Métriques manquantes
- Pas d'analyse item par item
- Pas de comparaison baseline

### Cause 2 : Workflow Incomplet

**Étapes manquantes** :
1. ❌ Téléchargement fichiers S3
2. ❌ Analyse contenu fichiers
3. ❌ Extraction métriques détaillées
4. ❌ Calcul coûts
5. ❌ Comparaison baseline

**Pourquoi** :
- Focus sur exécution technique (build, deploy, invoke)
- Pas de phase "analyse post-exécution"
- Pas de prompt explicite pour analyse détaillée

### Cause 3 : Absence de Baseline

**Problème** :
- Aucune baseline définie pour lai_weekly_v11
- Pas de comparaison avec v10
- Impossible de mesurer progression/régression

**Impact** :
- Colonnes "vs Baseline" vides
- Pas de contexte pour interpréter métriques
- Pas de décision GO/NO-GO possible

### Cause 4 : Prompt Utilisateur Imprécis

**Prompt utilisateur** :
```
je veux que tu revienne a # Build & deploy
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev

# Test E2E
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v10
```

**Problème** :
- Focus sur commandes techniques
- Pas de mention du template E2E
- Pas de demande d'analyse détaillée
- Pas de référence à la baseline

**Prompt attendu** :
```
Exécute un test E2E complet de lai_weekly_v11 en utilisant le template 
docs/templates/TEMPLATE_TEST_E2E_STANDARD.md

Baseline : lai_weekly_v10 (docs/reports/e2e/test_e2e_v10_rapport_2026-02-02.md)

Workflow complet :
1. Build & deploy
2. Ingestion
3. Normalize & score
4. Télécharger fichiers S3
5. Analyser résultats
6. Remplir template avec métriques détaillées
7. Comparer avec baseline v10
8. Générer recommandations

Sauvegarde dans : docs/reports/e2e/test_e2e_v11_rapport_2026-02-02.md
```

### Cause 5 : Q Context Non Consulté

**Q aurait dû** :
1. Lire `.q-context/vectora-inbox-development-rules.md`
2. Voir section "RÈGLES DE TESTS E2E"
3. Identifier template standard
4. Proposer utilisation du template

**Pourquoi Q ne l'a pas fait** :
- Prompt utilisateur trop directif (commandes techniques)
- Pas de phase "planification" avant exécution
- Pas de validation du plan avec utilisateur

---

## 💡 RECOMMANDATIONS D'AMÉLIORATION

### 1. Enrichir Règles Q Context

**Ajouter dans `.q-context/vectora-inbox-development-rules.md`** :

```markdown
### Test E2E : Workflow Obligatoire

**Q Developer DOIT TOUJOURS suivre ce workflow pour test E2E** :

1. **Planification** (AVANT exécution)
   - Identifier baseline de comparaison
   - Confirmer utilisation template standard
   - Valider plan avec utilisateur

2. **Exécution Technique**
   - Build & deploy
   - Ingestion
   - Normalize & score
   - Newsletter (si applicable)

3. **Collecte Données** (OBLIGATOIRE)
   - Télécharger fichiers S3 (ingested, normalized, newsletter)
   - Extraire logs Lambda
   - Calculer métriques Bedrock

4. **Analyse Détaillée** (OBLIGATOIRE)
   - Remplir template standard
   - Analyser item par item
   - Comparer avec baseline
   - Calculer coûts

5. **Recommandations**
   - Identifier problèmes
   - Prioriser actions
   - Proposer solutions

**Prompt type pour Q** :
"Exécute un test E2E complet de [client_id] avec template standard et baseline [version]"
```

### 2. Créer Script Automatisé

**Nouveau script** : `scripts/invoke/invoke_e2e_complete.py`

```python
"""
Script E2E complet avec analyse automatique.

Usage:
    python scripts/invoke/invoke_e2e_complete.py \
        --client-id lai_weekly_v11 \
        --baseline lai_weekly_v10 \
        --template docs/templates/TEMPLATE_TEST_E2E_STANDARD.md \
        --output docs/reports/e2e/test_e2e_v11_rapport_2026-02-02.md

Workflow:
1. Exécute workflow E2E (ingest + normalize + newsletter)
2. Télécharge fichiers S3
3. Analyse résultats
4. Remplit template
5. Compare avec baseline
6. Génère rapport final
"""
```

**Avantages** :
- ✅ Workflow standardisé
- ✅ Pas d'étape oubliée
- ✅ Métriques automatiques
- ✅ Rapport complet garanti

### 3. Améliorer Prompts Utilisateur

**Mauvais prompt** :
```
Fais un test E2E de lai_weekly_v11
```

**Bon prompt** :
```
Exécute un test E2E complet de lai_weekly_v11 en utilisant le template 
docs/templates/TEMPLATE_TEST_E2E_STANDARD.md

Baseline : lai_weekly_v10

Workflow complet :
1. Build & deploy
2. Exécution E2E (ingest + normalize + newsletter)
3. Téléchargement fichiers S3
4. Analyse détaillée avec template
5. Comparaison baseline
6. Recommandations priorisées

Sauvegarde dans : docs/reports/e2e/test_e2e_v11_rapport_2026-02-02.md
```

### 4. Créer Checklist Pré-Test

**Nouveau fichier** : `docs/templates/CHECKLIST_PRE_TEST_E2E.md`

```markdown
# Checklist Pré-Test E2E

## Avant de Lancer Test

- [ ] Baseline identifiée (version précédente)
- [ ] Template copié avec bon nom
- [ ] Client config uploadé sur S3
- [ ] Lambdas déployées et actives
- [ ] AWS CLI configuré

## Prompt Q Developer

- [ ] Référence template standard
- [ ] Référence baseline
- [ ] Demande workflow complet
- [ ] Demande analyse détaillée
- [ ] Spécifie output path

## Validation Post-Test

- [ ] Fichiers S3 téléchargés
- [ ] Template complètement rempli
- [ ] Métriques quantitatives présentes
- [ ] Analyse item par item effectuée
- [ ] Comparaison baseline effectuée
- [ ] Coûts calculés
- [ ] Recommandations priorisées
```

### 5. Ajouter Validation Automatique

**Nouveau script** : `scripts/maintenance/validate_e2e_report.py`

```python
"""
Valide qu'un rapport E2E est complet.

Usage:
    python scripts/maintenance/validate_e2e_report.py \
        --report docs/reports/e2e/test_e2e_v11_rapport_2026-02-02.md

Vérifie:
- Toutes les sections du template présentes
- Métriques quantitatives remplies
- Analyse item par item effectuée
- Comparaison baseline effectuée
- Coûts calculés
- Recommandations présentes

Output:
- ✅ Rapport complet
- ⚠️ Rapport partiel (liste sections manquantes)
- ❌ Rapport invalide
"""
```

---

## 🎯 PLAN D'ACTION IMMÉDIAT

### Semaine 1 : Corriger Test v11

1. **Refaire test E2E v11 correctement**
   - Utiliser template standard
   - Baseline v10
   - Workflow complet
   - Analyse détaillée

2. **Télécharger fichiers S3 v11**
   ```bash
   aws s3 cp s3://vectora-inbox-data-dev/runs/lai_weekly_v11/latest/ingested_items.json .
   aws s3 cp s3://vectora-inbox-data-dev/runs/lai_weekly_v11/latest/normalized_items.json .
   ```

3. **Analyser les 29 items individuellement**
   - Pourquoi 0 matches ?
   - Quelles entités détectées ?
   - Quels scores domain_scoring ?
   - Problème prompt ou seuil ?

### Semaine 2 : Améliorer Processus

1. **Enrichir Q Context**
   - Ajouter workflow E2E obligatoire
   - Ajouter exemples prompts
   - Ajouter checklist

2. **Créer script automatisé**
   - `invoke_e2e_complete.py`
   - Workflow complet automatique
   - Rapport garanti complet

3. **Créer validation automatique**
   - `validate_e2e_report.py`
   - Vérifier complétude rapport
   - Alerter si sections manquantes

### Mois 1 : Standardiser

1. **Refaire tous les tests E2E passés**
   - v10 avec template standard
   - v9 avec template standard
   - v8 avec template standard

2. **Créer baseline de référence**
   - Identifier meilleure version
   - Documenter comme baseline
   - Utiliser pour comparaisons futures

3. **Former Q Developer**
   - Exemples de bons rapports
   - Exemples de mauvais rapports
   - Workflow à suivre systématiquement

---

## 📊 MÉTRIQUES DE SUCCÈS

### Rapport E2E Complet

**Critères validation** :
- ✅ Toutes sections template remplies
- ✅ Métriques quantitatives présentes
- ✅ Analyse item par item effectuée
- ✅ Comparaison baseline effectuée
- ✅ Coûts calculés
- ✅ Recommandations priorisées
- ✅ Décision GO/NO-GO documentée

### Collaboration Q Developer

**Critères succès** :
- ✅ Q consulte Q Context avant exécution
- ✅ Q propose utilisation template
- ✅ Q demande validation plan
- ✅ Q exécute workflow complet
- ✅ Q génère rapport complet
- ✅ Q compare avec baseline

---

## 💬 CONCLUSION

### Ce Qui N'a Pas Fonctionné

1. **Template ignoré** : Rapport minimal au lieu de template standard
2. **Workflow incomplet** : Exécution technique sans analyse
3. **Baseline absente** : Pas de comparaison possible
4. **Prompt imprécis** : Focus commandes au lieu de résultat attendu
5. **Q Context non consulté** : Règles E2E non appliquées

### Ce Qui Doit Changer

1. **Prompts utilisateur** : Toujours référencer template et baseline
2. **Workflow Q** : Phase planification avant exécution
3. **Q Context** : Enrichir règles E2E avec workflow obligatoire
4. **Automatisation** : Script E2E complet pour garantir complétude
5. **Validation** : Script validation rapport pour détecter lacunes

### Prochaine Étape

**Refaire test E2E v11 correctement** avec :
- Template standard
- Baseline v10
- Workflow complet
- Analyse détaillée
- Rapport exploitable pour admin

---

**Évaluation créée le** : 2026-02-02  
**Objectif** : Améliorer collaboration Q Developer sur tests E2E  
**Statut** : Plan d'action défini, prêt pour exécution
