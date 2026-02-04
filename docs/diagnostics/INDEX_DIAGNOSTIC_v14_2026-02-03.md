# Index - Fichiers Générés par Diagnostic v14

**Date** : 2026-02-03  
**Durée diagnostic** : 45 minutes  
**Statut** : ✅ COMPLET

---

## 📄 RAPPORTS GÉNÉRÉS

### 1. Rapport Complet (10 pages)

**Fichier** : `docs/diagnostics/diagnostic_regression_matching_v14_2026-02-03.md`

**Contenu** :
- Analyse détaillée de la régression
- Comparaison V13 vs V14 item par item
- Identification de la cause racine
- Plan de correction détaillé
- Leçons apprises et actions préventives

**Pour qui** : Développeurs, analyse technique approfondie

---

### 2. Résumé Exécutif (3 pages)

**Fichier** : `docs/diagnostics/RESUME_EXECUTIF_v14_2026-02-03.md`

**Contenu** :
- Problème et impact chiffré
- Cause racine expliquée
- 3 options de solution (A, B, C)
- Plan d'action immédiat
- Critères de succès

**Pour qui** : Admin, décision stratégique

---

### 3. Synthèse 5 Minutes

**Fichier** : `docs/diagnostics/SYNTHESE_5MIN_v14_2026-02-03.md`

**Contenu** :
- Problème en 1 phrase
- Cause en 1 exemple JSON
- 3 options résumées
- Décision à prendre

**Pour qui** : Admin pressé, vue d'ensemble rapide

---

### 4. Guide Option B (Workaround)

**Fichier** : `docs/diagnostics/GUIDE_OPTION_B_WORKAROUND_2026-02-03.md`

**Contenu** :
- Guide pas-à-pas (5 étapes)
- Commandes exactes à exécuter
- Validation et rollback
- Durée : 5 minutes

**Pour qui** : Admin qui veut débloquer immédiatement

---

## 🔧 SCRIPTS GÉNÉRÉS

### 1. Script Comparaison V13 vs V14

**Fichier** : `scripts/compare_v13_v14.py`

**Usage** :
```bash
python scripts/compare_v13_v14.py
```

**Sortie** :
- Comparaison item par item (5 premiers)
- Stats globales (relevant, scores moyens)
- Différences de signaux détectés

---

### 2. Script Analyse Structure Items

**Fichier** : `scripts/diagnostic_item_structure.py`

**Usage** :
```bash
python scripts/diagnostic_item_structure.py
```

**Sortie** :
- Top-level keys
- Champs entités (présents/manquants)
- Contenu normalized_content
- Domain_scoring

---

## 📊 DONNÉES TÉLÉCHARGÉES

### 1. Items V13 (Baseline)

**Fichier** : `temp_items_v13.json`

**Source** : `s3://vectora-inbox-data-dev/curated/lai_weekly_v13/2026/02/03/items.json`

**Contenu** : 29 items normalisés et scorés (version fonctionnelle)

---

### 2. Items V14 (Cassé)

**Fichier** : `temp_items_v14.json`

**Source** : `s3://vectora-inbox-data-dev/curated/lai_weekly_v14/2026/02/03/items.json`

**Contenu** : 29 items normalisés et scorés (version avec régression)

---

## 📋 CHECKLIST UTILISATION

### Pour Admin Pressé (5 min)

1. ✅ Lire `SYNTHESE_5MIN_v14_2026-02-03.md`
2. ✅ Choisir option (A, B ou C)
3. ✅ Si Option B : Suivre `GUIDE_OPTION_B_WORKAROUND_2026-02-03.md`

### Pour Développeur (30 min)

1. ✅ Lire `diagnostic_regression_matching_v14_2026-02-03.md`
2. ✅ Analyser les données avec `scripts/compare_v13_v14.py`
3. ✅ Investiguer le code `src_v2/vectora_core/normalization/normalizer.py`
4. ✅ Implémenter Option A (correction code)

### Pour Analyse Approfondie (1h)

1. ✅ Lire tous les rapports
2. ✅ Exécuter les scripts de diagnostic
3. ✅ Analyser les items JSON manuellement
4. ✅ Vérifier les logs Lambda
5. ✅ Tester les corrections localement

---

## 🎯 PROCHAINES ÉTAPES

### Immédiat (Aujourd'hui)

- [ ] Admin choisit option (A, B ou C)
- [ ] Implémenter la solution choisie
- [ ] Tester avec lai_weekly_v15
- [ ] Valider les métriques

### Court Terme (Cette Semaine)

- [ ] Si Option B choisie : Implémenter Option A en parallèle
- [ ] Créer tests de régression automatiques
- [ ] Documenter les leçons apprises
- [ ] Mettre à jour la gouvernance

### Moyen Terme (Ce Mois)

- [ ] Ajouter validation entités dans le pipeline
- [ ] Créer métriques de référence automatiques
- [ ] Améliorer les alertes de régression
- [ ] Former l'équipe sur les bonnes pratiques

---

## 📞 CONTACT

**Questions sur le diagnostic** : Voir les rapports détaillés  
**Problèmes d'implémentation** : Consulter les guides pas-à-pas  
**Besoin d'aide** : Relire ce fichier index

---

**Diagnostic créé** : 2026-02-03  
**Auteur** : Q Developer  
**Statut** : ✅ PRÊT POUR ACTION
