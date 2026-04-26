# Sprint 002 — Exécution des renommages Phase 2.1

**Statut** : 🔵 En cours
**Palier** : Pré-Niveau 1 (Phase 2.1 — nettoyage vocabulaire legacy)
**Date effective** : 2026-04-25
**Estimation** : ~2h
**Modèle recommandé** : 🟡 Sonnet
**Dépend de** : Sprint 001 ✅ (rapport d'audit validé)

---

## Objectif

Exécuter toutes les actions identifiées dans `docs/architecture/naming_audit_phase21.md` :
renommages de vocabulaire legacy (`domain*` → `ecosystem*`, `bedrock_config:` → `llm_config:`),
archivages des dossiers hors scope V1, suppressions des configs/tests obsolètes.

## Critère de fin testable

- [ ] `canonical/ecosystems/lai_ecosystem_definition.yaml` existe (renommé depuis `canonical/domains/`)
- [ ] `canonical/domains/` n'existe plus
- [ ] `canonical/scopes/domain_definitions.yaml` supprimé
- [ ] `bedrock_config:` absent de `canonical/prompts/normalization/generic_normalization.yaml`
- [ ] `domains:` absent de `canonical/ingestion/ingestion_profiles.yaml`
- [ ] `canonical/matching/`, `canonical/scoring/` absents (archivés)
- [ ] `canonical/prompts/domain_scoring/`, `canonical/prompts/editorial/` absents (archivés)
- [ ] `config/clients/` ne contient plus de configs V2/V3
- [ ] Tests `test_bedrock_*.py`, `test_newsletter_selector_v2.py`, `test_e2e_domain_scoring_*.py` absents de `tests/`

## Plan d'exécution (5 commits)

| Commit | Actions | Fichiers |
|---|---|---|
| 1 | Rename canonical/domains/ → ecosystems/, champs domain_id/domain_name | 2 fichiers |
| 2 | bedrock_config: → llm_config: + domains: → ecosystems: | 2 fichiers |
| 3 | Archiver canonical/matching/ + canonical/scoring/ | ménage en bloc |
| 4 | Archiver canonical/prompts hors scope V1 | ménage en bloc |
| 5 | Supprimer configs clients + tests obsolètes + source_catalog_backup | ménage en bloc |

---

## Bilan post-exécution

### Commits effectués

- (à remplir)

### Difficultés rencontrées

- (à remplir)

### Validation Frank

- Date : (à remplir)
