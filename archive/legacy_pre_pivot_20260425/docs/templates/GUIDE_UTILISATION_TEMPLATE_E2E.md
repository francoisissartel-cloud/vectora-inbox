# Guide d'Utilisation - Template Test E2E Standard

**Date** : 2026-01-30  
**Version** : 1.0  
**Objectif** : Standardiser les tests E2E Vectora Inbox pour comparaison temporelle

---

## 🎯 Pourquoi ce Template ?

### Problème Résolu

Avant ce template, vos tests E2E variaient en :
- **Format** : Structure différente entre v3, v4, v6
- **Métriques** : Indicateurs pas toujours identiques
- **Profondeur** : Analyse plus ou moins détaillée
- **Comparabilité** : Difficile de comparer lai_weekly_v7 vs v8

### Bénéfices du Template

1. **Comparabilité temporelle** : Même structure = comparaison facile
2. **Efficacité avec Q** : Q sait exactement quoi remplir
3. **Traçabilité** : Impact visible de chaque modification
4. **Debugging rapide** : Identifier quelle étape régresse

---

## 📋 Comment Utiliser ce Template

### Étape 1 : Copier le Template

```bash
# Créer un nouveau test E2E
cp docs/templates/TEMPLATE_TEST_E2E_STANDARD.md \
   docs/reports/test_e2e_lai_weekly_v8_[DATE].md
```

### Étape 2 : Prompter Q Developer

**Prompt recommandé** :

```
Je veux faire un test E2E complet de lai_weekly_v8 en utilisant le template 
standard dans docs/templates/TEMPLATE_TEST_E2E_STANDARD.md

Baseline de comparaison : docs/reports/rapport_e2e_complet_lai_weekly_v6_20260127.md

Objectif : Valider l'impact de [modification récente : ex. nouveau prompt matching]

Remplis le template avec :
1. Toutes les métriques quantitatives (volumes, coûts, temps)
2. Analyse item par item avec justifications moteur
3. Comparaison vs baseline v6
4. Recommandations d'amélioration priorisées

Exécute le workflow complet :
- python scripts/invoke/invoke_ingest_v2.py --client-id lai_weekly_v8
- python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v8
- python scripts/invoke/invoke_newsletter_v2.py --client-id lai_weekly_v8
```

### Étape 3 : Q Remplit le Template

Q va automatiquement :
- Exécuter les 3 lambdas
- Télécharger les fichiers S3
- Analyser les résultats
- Remplir toutes les sections du template
- Comparer avec la baseline

### Étape 4 : Validation Humaine

Vous complétez les sections "Évaluation Humaine" :
- ✅ D'ACCORD / ❌ PAS D'ACCORD pour chaque item
- Commentaires sur les décisions moteur
- Suggestions d'amélioration

---

## 📊 Sections du Template

### Section 1 : Résumé Exécutif (5 min lecture)

**Contenu** :
- Métriques clés avec comparaison baseline
- Funnel de conversion complet
- Verdict global en 3 points

**Usage** : Lecture rapide pour décision GO/NO-GO

### Section 2 : Phase 1 - Ingestion

**Contenu** :
- Métriques volume (items, sources, dédup)
- Performance (temps, taux succès)
- Distribution word count
- Items pertinents vs bruit

**Usage** : Diagnostiquer problèmes d'ingestion

### Section 3 : Phase 2 - Normalisation & Scoring

**Contenu** :
- Extraction entités (molecules, trademarks, etc.)
- Event classification
- LAI relevance scores
- Matching results par domaine
- Scoring distribution

**Usage** : Évaluer qualité Bedrock et matching

### Section 4 : Phase 3 - Génération Newsletter

**Contenu** :
- Funnel sélection items
- Répartition sections
- Génération éditoriale (TL;DR, intro)
- Fichiers générés

**Usage** : Valider qualité newsletter finale

### Section 5 : Analyse Item par Item

**Contenu** :
- Items sélectionnés newsletter (détail complet)
- Items matchés non sélectionnés
- Items non matchés (validation rejets)
- Évaluation humaine pour chaque item

**Usage** : Comprendre chaque décision moteur

### Section 6 : Métriques de Performance

**Contenu** :
- Métriques techniques (temps, coût, succès)
- Métriques qualité (précision, diversité)
- Métriques business (ROI, scalabilité)

**Usage** : Valider objectifs performance

### Section 7 : Analyse Coûts Détaillée

**Contenu** :
- Coûts Bedrock par type d'appel
- Coûts AWS (Lambda, S3, CloudWatch)
- Projections (hebdo, mensuel, annuel)

**Usage** : Contrôler budget opérationnel

### Section 8 : Recommandations d'Amélioration

**Contenu** :
- Priorité CRITIQUE (Semaine 1)
- Priorité HAUTE (Mois 1)
- Priorité MOYENNE (Trimestre 1)

**Usage** : Planifier améliorations moteur

### Section 9 : Décision Finale

**Contenu** :
- Statut global (🟢/🟡/🔴)
- Justification (points forts, améliorations, risques)
- Recommandation déploiement
- Timeline actions

**Usage** : Décision GO/NO-GO production

---

## 🔄 Workflow Recommandé

### Test Baseline (Première fois)

1. **Exécuter test E2E** avec template
2. **Sauvegarder comme baseline** : `test_e2e_lai_weekly_v7_baseline_[DATE].md`
3. **Noter métriques clés** dans un fichier de suivi

### Test Après Modification

1. **Copier template** : `test_e2e_lai_weekly_v8_[DATE].md`
2. **Prompter Q** avec référence baseline v7
3. **Q remplit template** avec comparaison vs baseline
4. **Valider humainement** les décisions moteur
5. **Décider** : garder modification ou rollback

### Test Périodique (Monitoring)

1. **Exécuter test E2E** chaque semaine/mois
2. **Comparer avec baseline** précédente
3. **Détecter régressions** automatiquement
4. **Ajuster moteur** si nécessaire

---

## 📈 Métriques de Suivi Recommandées

### Créer un Fichier de Suivi

`docs/reports/SUIVI_METRIQUES_E2E.md` :

```markdown
# Suivi Métriques E2E - Vectora Inbox

| Version | Date       | Items Ingérés | Taux Matching | Items Newsletter | Coût  | Temps |
|---------|------------|---------------|---------------|------------------|-------|-------|
| v6      | 2026-01-27 | 18            | 61%           | 6                | $0.35 | 112s  |
| v7      | 2026-02-03 | 20            | 65%           | 7                | $0.38 | 105s  |
| v8      | 2026-02-10 | 22            | 70%           | 8                | $0.40 | 98s   |
```

### Graphiques Recommandés

1. **Évolution taux matching** (objectif : >60%)
2. **Évolution coût par run** (objectif : <$2)
3. **Évolution temps E2E** (objectif : <600s)
4. **Évolution items newsletter** (objectif : 15-25)

---

## 🎯 Cas d'Usage Typiques

### Cas 1 : Tester Nouveau Prompt Matching

**Contexte** : Vous modifiez `canonical/prompts/matching/lai_prompt.yaml`

**Workflow** :
1. Baseline : Test E2E v7 avant modification
2. Modification : Nouveau prompt matching
3. Test : E2E v8 avec nouveau prompt
4. Comparaison : Taux matching v7 vs v8
5. Décision : Garder si taux matching +5%

### Cas 2 : Tester Nouveau Scope Entités

**Contexte** : Vous ajoutez 20 nouvelles molecules dans `canonical/scopes/lai_molecules_global.yaml`

**Workflow** :
1. Baseline : Test E2E v7 avant ajout
2. Modification : Ajout 20 molecules
3. Test : E2E v8 avec nouveau scope
4. Comparaison : Extraction entités v7 vs v8
5. Décision : Garder si +10% molecules détectées

### Cas 3 : Tester Nouveau Seuil Scoring

**Contexte** : Vous modifiez `min_domain_score: 0.25 → 0.30` dans config client

**Workflow** :
1. Baseline : Test E2E v7 avec seuil 0.25
2. Modification : Seuil 0.30
3. Test : E2E v8 avec nouveau seuil
4. Comparaison : Items matchés v7 vs v8
5. Décision : Garder si -20% bruit sans perte signal

### Cas 4 : Monitoring Hebdomadaire

**Contexte** : Aucune modification, juste monitoring qualité

**Workflow** :
1. Exécuter test E2E chaque lundi
2. Comparer avec semaine précédente
3. Alerter si régression >10% sur métrique clé
4. Investiguer cause régression
5. Corriger si nécessaire

---

## 🚀 Prompts Recommandés pour Q

### Prompt Test E2E Complet

```
Exécute un test E2E complet de lai_weekly_v8 en utilisant le template 
docs/templates/TEMPLATE_TEST_E2E_STANDARD.md

Baseline : docs/reports/rapport_e2e_complet_lai_weekly_v6_20260127.md

Remplis toutes les sections du template avec :
- Métriques quantitatives précises
- Comparaison vs baseline (colonnes "vs Baseline")
- Analyse item par item avec justifications
- Recommandations priorisées

Sauvegarde le résultat dans :
docs/reports/test_e2e_lai_weekly_v8_[DATE].md
```

### Prompt Test Rapide (Focus Matching)

```
Exécute un test E2E de lai_weekly_v8 en te concentrant sur la phase 2 
(normalisation & scoring).

Utilise le template docs/templates/TEMPLATE_TEST_E2E_STANDARD.md mais 
remplis uniquement :
- Résumé exécutif
- Phase 2 complète
- Métriques matching détaillées
- Recommandations matching

Baseline : lai_weekly_v7

Objectif : Valider impact nouveau prompt matching
```

### Prompt Comparaison Versions

```
Compare les tests E2E de lai_weekly_v6, v7, v8 :
- docs/reports/rapport_e2e_complet_lai_weekly_v6_20260127.md
- docs/reports/test_e2e_lai_weekly_v7_[DATE].md
- docs/reports/test_e2e_lai_weekly_v8_[DATE].md

Génère un rapport de comparaison avec :
- Évolution métriques clés (tableau)
- Graphiques tendances (ASCII art)
- Analyse régression/progression
- Recommandations stratégiques

Sauvegarde dans :
docs/reports/comparaison_v6_v7_v8_[DATE].md
```

---

## 📝 Checklist Avant Test E2E

### Préparation Environnement

- [ ] AWS CLI configuré (profil `rag-lai-prod`)
- [ ] Accès S3 buckets dev validé
- [ ] Lambdas déployées et actives
- [ ] Configuration client à jour dans S3

### Préparation Baseline

- [ ] Baseline précédente identifiée
- [ ] Métriques baseline notées
- [ ] Objectifs du test définis

### Exécution Test

- [ ] Template copié avec bon nom
- [ ] Q prompté avec instructions claires
- [ ] Workflow complet exécuté (3 lambdas)
- [ ] Fichiers S3 téléchargés

### Validation Résultats

- [ ] Template complètement rempli
- [ ] Comparaison baseline effectuée
- [ ] Évaluation humaine complétée
- [ ] Recommandations priorisées
- [ ] Décision finale documentée

---

## 🔧 Personnalisation du Template

### Ajouter une Section Custom

Si vous voulez tracker une métrique spécifique :

```markdown
## 📊 ANALYSE CUSTOM : [NOM MÉTRIQUE]

### Métriques Spécifiques

**Volume** :
- [Métrique 1] : XX
- [Métrique 2] : XX

**Comparaison Baseline** :
- [Métrique 1] : +X% vs baseline
- [Métrique 2] : +X% vs baseline

### Analyse

[Votre analyse custom]
```

### Adapter pour Autre Client

Le template est conçu pour `lai_weekly_vX` mais adaptable :

1. Remplacer "LAI" par votre domaine
2. Adapter sections newsletter (regulatory, partnerships, etc.)
3. Modifier scopes entités (molecules → autres)
4. Ajuster objectifs métriques

---

## 📞 Support

### Questions Fréquentes

**Q : Dois-je remplir toutes les sections ?**  
R : Oui pour test complet, mais vous pouvez faire des tests partiels (focus matching, focus newsletter, etc.)

**Q : Combien de temps prend un test E2E ?**  
R : 30-60 minutes (exécution + analyse + remplissage template)

**Q : Quelle fréquence de tests recommandée ?**  
R : Hebdomadaire pour monitoring, après chaque modification majeure

**Q : Comment comparer 3+ versions ?**  
R : Utiliser le prompt "Comparaison Versions" pour générer un rapport consolidé

### Amélioration Continue

Ce template évoluera avec vos besoins. Suggestions bienvenues dans :
`docs/templates/SUGGESTIONS_TEMPLATE.md`

---

**Guide d'Utilisation - Version 1.0**  
**Date** : 2026-01-30  
**Auteur** : Équipe Vectora Inbox  
**Statut** : Prêt pour utilisation
