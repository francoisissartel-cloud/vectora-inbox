# Sprint 001 — Audit nommage canonical (Phase 2.1)

**Statut** : ⏸ Planifié
**Palier** : Pré-Niveau 1 (Phase 2.1 — nettoyage vocabulaire legacy)
**Date prévue** : après validation Sprint 000
**Date effective** : (à remplir à l'exécution)
**Estimation** : ~1h30
**Durée réelle** : (à remplir post-exécution)
**Modèle recommandé** : 🟡 Sonnet
**Justification du modèle** : l'audit implique de distinguer les occurrences à renommer de celles à garder, de croiser avec le design existant, et de rédiger des propositions d'action nuancées. Sonnet offre le jugement nécessaire pour éviter les faux positifs (ex : "domain" dans un URL vs vocabulaire V3).

---

## Objectif

Produire un **rapport d'audit exhaustif** `docs/architecture/naming_audit_phase21.md` listant toutes les occurrences de vocabulaire legacy V2/V3 encore présentes dans le repo (hors `archive/` et `scripts/legacy_reference/`), avec une proposition d'action pour chacune.

Ce rapport est la seule livraison de Sprint 001. Le refactor effectif des renommages est un **Sprint 002 distinct**, qui sera exécuté une fois le rapport validé par Frank.

---

## Critère de fin testable

- [ ] `docs/architecture/naming_audit_phase21.md` existe et est lisible
- [ ] Le rapport couvre les 4 catégories de vocabulaire ci-dessous (voir section Tâches)
- [ ] Chaque occurrence a une proposition d'action : `renommer → X` / `supprimer` / `garder tel quel (justification)`
- [ ] La section "renommages clés" du §13.1 de `datalake_v1_design.md` est croisée avec les occurrences trouvées
- [ ] Aucun fichier dans `archive/` ou `scripts/legacy_reference/` n'est inclus dans l'audit (legacy intentionnel)
- [ ] Le rapport est commité et pushé sur la branche en cours
- [ ] Frank valide le rapport → Sprint 002 peut être planifié

---

## Tâches détaillées (dans l'ordre d'exécution)

### Étape 1 — Cadrage du périmètre (5 min)

Définir les **zones à auditer** (tout le repo hors exclusions) :

**Inclus dans l'audit** :
- `canonical/` — fichiers YAML
- `config/` — fichiers YAML et Python
- `src_vectora_inbox_v1/` — fichiers Python (probablement vide à ce stade)
- `scripts/` — Python (hors `scripts/legacy_reference/`)
- `docs/` — fichiers Markdown (hors `docs/diagnostics/` legacy)
- Fichiers racine : `README.md`, `STATUS.md`, `CLAUDE.md`, `pyproject.toml`, `.env.example`

**Exclus** (legacy intentionnel, à ne pas toucher) :
- `archive/` (état pré-pivot archivé)
- `scripts/legacy_reference/` (code V2/V3 conservé pour capitalisation)

### Étape 2 — Scan vocabulaire legacy (30 min)

Rechercher les 4 catégories de vocabulaire à migrer, en utilisant des grep/recherches dans les zones incluses.

**Catégorie A — Nommage écosystème** (à renommer → `ecosystem*`)
Termes : `domain`, `watch_domain`, `domain_id`, `domain_resolver`, `watch_domain_resolver`, `domains/`

**Catégorie B — Stack AWS abandonnée** (à supprimer ou retirer)
Termes : `bedrock`, `lambda`, `aws`, `s3`, `boto`, `cloudformation`, `iam`

**Catégorie C — Concepts hors scope V1** (à supprimer ou archiver)
Termes : `newsletter`, `scoring`, `matching`, `report` (dans les noms de modules/vars, pas dans les docs de reporting Niveau 3)

**Catégorie D — Fichiers avec suffixe _v3** (à consolider)
Pattern : `*_v3.yaml`, `*_v3.py`, `*_v2.yaml`

### Étape 3 — Rédaction du rapport (40 min)

Créer `docs/architecture/naming_audit_phase21.md` avec :

**Section 1 — Résumé exécutif** : nombre d'occurrences par catégorie, actions proposées (rename / supprimer / garder).

**Section 2 — Renommages clés déjà identifiés** (repris de `datalake_v1_design.md` §13.1) :

| Avant | Après | Statut |
|---|---|---|
| `watch_domains` (dans client_config) | `ecosystems` | À confirmer |
| `domain_id` | `ecosystem_id` | À confirmer |
| `watch_domain_resolver` | `ecosystem_resolver` | À confirmer |
| `canonical/domains/` | `canonical/ecosystems/` | À confirmer |
| `canonical/scopes/domain_definitions.yaml` | fusionné dans `canonical/ecosystems/{eco}.yaml` | À confirmer |
| `canonical/sources/source_catalog_v3.yaml` | `canonical/sources/source_catalog.yaml` | À confirmer |
| `canonical/ingestion/ingestion_profiles_v3.yaml` | `canonical/ingestion/ingestion_profiles.yaml` | À confirmer |
| `canonical/ingestion/filter_rules_v3.yaml` | `canonical/ingestion/filter_rules.yaml` | À confirmer |
| `canonical/ingestion/source_configs_v3.yaml` | `canonical/ingestion/source_configs.yaml` | À confirmer |

**Section 3 — Occurrences trouvées** : tableau exhaustif par fichier.

| Fichier | Ligne / Champ | Terme trouvé | Catégorie | Action proposée |
|---|---|---|---|---|
| (à remplir lors de l'exécution) | | | | |

**Section 4 — Fichiers `_v3` à consolider** : liste des fichiers avec leur action.

**Section 5 — Occurrences à garder telles quelles** : liste avec justification (ex: mentions dans l'historique d'un ADR, ou dans un commentaire explicatif).

### Étape 4 — Commit + push (5 min)

- Commit : `docs(architecture): add naming audit report phase 2.1`
- Push sur la branche en cours

### Étape 5 — Point de validation avec Frank

Frank lit le rapport et valide (ou demande des corrections). Une fois validé :
- Sprint 002 peut être planifié (exécution des renommages)
- Fermer Sprint 001 (remplir bilan post-exécution)

---

## Fichiers créés / modifiés / supprimés

**✨ Créés** :
- `docs/architecture/naming_audit_phase21.md`

**📝 Modifiés** : aucun

**🗑️ Supprimés** : aucun

---

## Règles à suivre (références CLAUDE.md)

- §3 (Plan → Validation → Exécution) : valider le rapport avant de passer à Sprint 002
- §6 (Conventions Git) : commit `docs(architecture): ...`
- §17 (Small batches) : 1 seul commit (le rapport entier, justifié comme livrable atomique)
- §20 (Modèles) : **Sonnet** — jugement nécessaire pour qualifier chaque occurrence

---

## Points de validation par Frank

| # | Quand | Quoi |
|---|---|---|
| 1 | Avant exécution | Valider ce plan (objectif, critère, périmètre d'audit) |
| 2 | Après rédaction du rapport (étape 3) | Frank valide le rapport d'audit avant commit et avant Sprint 002 |

---

## Risques identifiés

| # | Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|---|
| 1 | Occurrences manquées dans le scan | Faible | Moyen | Scanner par termes ET par patterns de fichiers. Sprint 002 peut corriger les oublis. |
| 2 | Scope creep : vouloir corriger en même temps qu'auditer | Moyenne | Moyen | Règle ferme : Sprint 001 = audit uniquement. Aucune modification de fichier hors rapport. |
| 3 | Vocabulaire legacy dans archive/ scanné par erreur | Faible | Faible | Exclure explicitement `archive/` et `scripts/legacy_reference/` dans chaque grep. |
| 4 | Un terme ambigu (ex: "domain" dans un nom de domaine web) | Moyenne | Faible | Dans le rapport, colonne "Contexte" pour distinguer vocabulaire V3 de contexte web neutre. |

---

## Dépendances

- Phase 2.0 (ménage repo) : ✅ exécutée
- Sprint 000 (remise en ordre méthodologique) : ✅ validé (condition de démarrage de Sprint 001)
- `datalake_v1_design.md` §13.1 (renommages clés identifiés) : ✅ disponible
- CLAUDE.md V1.5 : ✅ en place

---

## Bilan post-exécution

À remplir UNE FOIS le sprint terminé.

### Durée réelle vs estimation

- Estimé : ~1h30
- Réel : (à remplir)
- Écart : (justifier si > 50%)

### Commits effectués

- (à remplir)

### Difficultés rencontrées

- (à remplir)

### Décisions prises en cours de route

- (à remplir — si majeures, créer une ADR)

### Ce qui reste pour le prochain sprint

- (normalement : Sprint 002 — exécution des renommages validés)

### Validation Frank

- Date de validation : (à remplir)
- Commentaires éventuels :

---

*Sprint 001 — fin du document.*
