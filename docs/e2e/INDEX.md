# Index Rapports E2E - Vectora Inbox

## 📋 Organisation

Tous les rapports de tests End-to-End (E2E) sont centralisés dans ce dossier.

## 📁 Structure

```
docs/reports/e2e/
├── INDEX.md                                    # Ce fichier
├── test_e2e_v11_rapport_2026-02-02.md         # Dernier test (v11)
├── test_e2e_v11_resume_2026-02-02.md          # Résumé v11
├── test_e2e_v10_rapport_2026-02-02.md         # Test v10
└── test_e2e_v10_post_mortem_2026-02-02.md     # Post-mortem v10
```

## 🎯 Convention de Nommage

**Format** : `test_e2e_v{VERSION}_{TYPE}_{DATE}.md`

**Types** :
- `rapport` : Rapport complet du test E2E
- `resume` : Résumé exécutif
- `post_mortem` : Analyse post-mortem (si échec ou problème)

**Exemples** :
- `test_e2e_v11_rapport_2026-02-02.md`
- `test_e2e_v12_resume_2026-02-03.md`
- `test_e2e_v13_post_mortem_2026-02-04.md`

## 📊 Rapports Disponibles

### v11 - Test Prompts Cleanup (2026-02-02)
- **Rapport** : `test_e2e_v11_rapport_2026-02-02.md`
- **Résumé** : `test_e2e_v11_resume_2026-02-02.md`
- **Statut** : ✅ Succès technique, ⚠️ 0 matches
- **Objectif** : Valider cleanup prompts obsolètes

### v10 - Test E2E AWS (2026-02-02)
- **Rapport** : `test_e2e_v10_rapport_2026-02-02.md`
- **Post-mortem** : `test_e2e_v10_post_mortem_2026-02-02.md`
- **Statut** : Voir rapports
- **Objectif** : Test E2E complet AWS

## 🔍 Comment Utiliser

### Pour Q Developer

Lors d'une analyse de tests E2E :
1. Lire `INDEX.md` pour vue d'ensemble
2. Identifier le rapport pertinent par version
3. Analyser le rapport complet
4. Si problème, consulter post-mortem associé

### Pour Créer un Nouveau Rapport

```bash
# Créer rapport dans le bon dossier
docs/reports/e2e/test_e2e_v{VERSION}_{TYPE}_{DATE}.md

# Mettre à jour INDEX.md
# Ajouter entrée dans section "Rapports Disponibles"
```

## 📝 Template Rapport E2E

Voir : `docs/templates/TEMPLATE_TEST_E2E_STANDARD.md`

## 🗂️ Autres Rapports E2E (Archive)

Rapports plus anciens dans :
- `docs/reports/test_e2e_lai_weekly_v5_20260127.md`
- `docs/reports/rapport_test_e2e_v7_extraction_dates.md`
- `docs/reports/development/phase7_test_e2e_aws_domain_scoring_20260202.md`

---

**Dernière mise à jour** : 2026-02-02
