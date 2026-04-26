# Niveau 2 — Cœur : plan de palier

**Statut** : ⏸ À démarrer (après validation critère de fin Niveau 1)
**Document parent** : `docs/architecture/datalake_v1_design.md` §13

> Ce document sera étoffé une fois le Niveau 1 validé. Pour l'instant : objectif, critère de fin, liste haute niveau des composants.

---

## Objectif

Rendre le moteur utilisable au quotidien sur les **8 sources MVP LAI**, avec le workflow complet d'onboarding d'une nouvelle source.

---

## Critère de fin testable

```bash
# Run complet sur toutes les sources MVP
python scripts/run_pipeline.py --client mvp_test_30days
# → ingère les 8 sources LAI, normalise, produit gap_report.json + health.json

# Onboarding d'une 9e source
python scripts/onboard_source.py --source press_corporate__taiwan_liposome
# → discovery + validation + promotion automatique si PASSED
# → la source est ensuite ingérable par tout client incluant son bouquet
```

---

## Composants à livrer (en plus du Niveau 1)

**Ingest enrichi** : parser HTML, filtres (period, lai_keywords, exclusions), prefetch_filter, source_router, indexes secondaires raw.

**Normalize enrichi** : validator anti-hallucinations, resolver canonical_id companies, retry LLM complet (3 niveaux), indexes secondaires curated, curation_log opérationnel.

**Module sources/** (nouveau) : discovery, validation, promotion, candidates, scripts CLI (discover_source, validate_source, promote_source, onboard_source, list_candidates).

**Stats minimaux** : `stats/health.py` (health.json), `stats/gap_report.py` (gap_report.json).

**Scripts runtime enrichis** : run_ingest.py avec --resume/--retry-failed/--source/--bouquet/--no-cache, run_normalize.py avec --retry-failed/--max-items.

**Canonical complet** : 8 sources LAI MVP validées, bouquet `lai_full_mvp`, tous les scopes LAI (company, molecule, technology, trademark, indication).

---

## Mini-sprints prévus

À définir au démarrage du Niveau 2. Estimation : **12-18 mini-sprints**.

---

*Niveau 2 — Cœur — plan de palier. Créé lors de Sprint 000. À étoffer après validation Niveau 1.*
