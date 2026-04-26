# Vectora Inbox LAI Weekly v2 - Plan d'Enquête Qualité (Run #2)

## Contexte
Analyse qualitative approfondie du run #2 de lai_weekly_v2 pour comprendre :
- Pourquoi la newsletter contient encore du bruit (HR, finance) 
- Pourquoi la news Nanexa/Moderna n'apparaît pas
- Comment améliorer le signal/noise ratio

## Phase 0 : Plan d'Exécution ✅
- [x] Création de ce plan d'enquête
- [x] Structure des livrables par phase

## Phase 1 : Analyse Qualitative Newsletter Actuelle (Run #2)
**Objectif** : Analyser chacun des 5 items de la newsletter générée

**Livrable** : `docs/diagnostics/vectora_inbox_lai_weekly_v2_run2_newsletter_quality_analysis.md`

**Contenu** :
- Pour chaque item de newsletter :
  - Titre et source
  - Classification métier (LAI-strong, LAI-weak, non-LAI, à exclure)
  - Analyse du pipeline (ingestion → matching → scoring)
  - Explication de la présence dans le top 5

**Questions clés** :
- Pourquoi DelSiTech HR (2 postes) arrive dans le top 5 ?
- Comment MedinCell finance passe les filtres LAI ?
- Quelle est la vraie pertinence LAI de chaque item ?

## Phase 2 : Traçage Nanexa/Moderna
**Objectif** : Trace complète de la news manquante dans le pipeline

**News cible** : "Nanexa and Moderna enter into license and option agreement for the development of PharmaShell®-based products" (10 décembre, site Nanexa)

**Livrable** : `docs/diagnostics/vectora_inbox_nanexa_moderna_trace.md`

**Étapes de trace** :
1. **Ingestion** : Présence dans scraping HTML Nanexa ?
2. **Normalisation** : Item normalisé par Bedrock ? Scopes détectés ?
3. **Matching** : Matché sur tech_lai_ecosystem ? Échec sur quel test ?
4. **Scoring** : Si matché, pourquoi pas dans top 5 ?

**Questions clés** :
- À quelle étape exacte cette news disparaît ?
- Défaillance technique ou configuration ?

## Phase 3 : Analyse Sources de Bruit
**Objectif** : Cartographier les types de bruit et leurs causes

**Livrable** : `docs/diagnostics/vectora_inbox_lai_weekly_v2_noise_sources_analysis.md`

**Classification du bruit** :
- HR/recrutement
- Finance/résultats
- Corporate générique
- ESG/sustainability

**Analyse par type** :
- Où le pipeline échoue (ingestion, normalisation, matching, scoring)
- Leviers d'amélioration par couche

**Questions clés** :
- Pourquoi les exclusion_scopes ne filtrent pas le HR ?
- Les matching rules sont-elles trop permissives ?
- Les poids de scoring favorisent-ils le bruit ?

## Phase 4 : Propositions d'Ajustement
**Objectif** : Plan d'amélioration concret sans implémentation

**Livrable** : `docs/design/vectora_inbox_lai_weekly_v2_signal_noise_improvement_plan.md`

**Ajustements P0** (config uniquement) :
- Renforcement exclusion_scopes.yaml
- Ajustement poids scoring_rules.yaml
- Seuils de pertinence LLM

**Ajustements P1** (code/prompts) :
- Amélioration gating LLM
- Enrichissement keywords automatique
- Adaptation pure players vs hybrid

**Pour chaque proposition** :
- Fichiers impactés
- Bénéfice attendu
- Risques/points d'attention

## Phase 5 : Synthèse Exécutive
**Objectif** : Résumé actionnable pour décision

**Livrable** : `docs/diagnostics/vectora_inbox_lai_weekly_v2_e2e_run2_quality_executive_summary.md`

**Contenu** :
- Faiblesses actuelles identifiées
- Ce qui marche bien vs fragile
- Ordre recommandé des corrections (P0 → P1)
- Impact business attendu

## Méthodologie d'Investigation

### Sources de Données
- Newsletter générée (run #2)
- Logs d'exécution Lambda
- Outputs intermédiaires (scraping, normalisation, matching, scoring)
- Configuration canonique et client

### Outils d'Analyse
- Trace des items individuels dans le pipeline
- Analyse comparative des scores
- Mapping des règles de matching appliquées
- Audit des exclusions et inclusions

### Critères de Succès
- Identification précise du point de perte Nanexa/Moderna
- Explication claire de chaque item de bruit dans newsletter
- Plan d'amélioration priorisé et actionnable
- Recommandations équilibrées (impact vs effort)

---

**Status** : Phase 0 complétée ✅
**Prochaine étape** : Phase 1 - Analyse qualitative newsletter