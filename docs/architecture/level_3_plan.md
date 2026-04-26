# Niveau 3 — Maquillage : plan de palier

**Statut** : ⏸ À démarrer (après validation critère de fin Niveau 2)
**Document parent** : `docs/architecture/datalake_v1_design.md` §13

> Ce document sera étoffé une fois le Niveau 2 validé. Pour l'instant : objectif, critère de fin, liste haute niveau des composants.

---

## Objectif

Rendre le moteur **stable, observable, et documenté** pour un usage long terme sans surveillance.

---

## Critère de fin testable

- Le rapport hebdomadaire `report_full.md` est généré automatiquement et lisible sans contexte
- Le moteur tourne sans surveillance pendant plusieurs semaines
- Les incidents sont diagnostiquables via les outils de validation/maintenance
- Les sources actives sont revalidées trimestriellement, les cassures sont détectées avant d'affecter silencieusement l'ingestion
- La documentation est suffisante pour qu'une autre personne reprenne le projet

---

## Composants à livrer (en plus du Niveau 2)

**Stats avancés** : stats_daily.jsonl, rapports markdown (report_raw, report_curated, report_sources, report_full), CLI generate_report.py.

**Maintenance** : scripts recompute_stats, rebuild_indexes, rebuild_cache, validate_datalake, validate_cache, revalidate_all. Module sources/revalidator.py.

**Robustesse** : cost cap LLM réellement appliqué avec alerte, tests unitaires complets (canonicalisation, item_id, indexes, parsers, filters, validator), tests d'intégration pipeline E2E.

**Documentation** : README src_vectora_inbox_v1/, runbooks à jour, inventaire sources validées.

---

## Mini-sprints prévus

À définir au démarrage du Niveau 3. Estimation : **8-12 mini-sprints**.

---

*Niveau 3 — Maquillage — plan de palier. Créé lors de Sprint 000. À étoffer après validation Niveau 2.*
