# Rapport d'audit nommage — Phase 2.1

**Date** : 2026-04-25
**Sprint** : Sprint 001
**Périmètre** : tout le repo hors `archive/` et `scripts/legacy_reference/`
**Auteur** : Claude (modèle Sonnet)

---

## Section 1 — Résumé exécutif

| Catégorie | Occurrences trouvées | Action principale |
|---|---|---|
| **A — vocabulaire `domain*` → `ecosystem*`** | 15 occurrences dans 10 fichiers actifs | Renommer (champs YAML + dossiers + fichiers) |
| **B — stack AWS (`bedrock*`, `lambda`, `s3`)** | 10 occurrences dans 7 fichiers actifs | Renommer `bedrock_config:` → `llm_config:` dans 5 fichiers ; 2 fichiers entiers à archiver |
| **C — concepts hors scope V1 (`newsletter*`, `scoring*`, `matching*`)** | 14 fichiers/dossiers entiers | Archiver (dossiers `canonical/matching/`, `canonical/scoring/`, `canonical/prompts/domain_scoring/`, `canonical/prompts/editorial/` + configs V2/V3 + tests obsolètes) |
| **D — suffixes `_v3` / `_v2` dans zones actives** | 4 fichiers actifs | Remplacer par équivalents V1 |

**Total d'actions** : environ 35 items, dont environ 15 renommages de champs/fichiers et environ 20 archivages.

**Ce qui ne bouge pas** : tous les fichiers dans `docs/design/`, `docs/plans/`, `docs/reports/`, `docs/implementation/` — ils documentent l'historique V2/V3 et doivent être conservés tels quels comme mémoire du projet.

---

## Section 2 — Renommages clés déjà identifiés (croisement avec `datalake_v1_design.md` §13.1)

| Avant (V2/V3) | Après (V1) | Statut | Fichier concerné |
|---|---|---|---|
| `watch_domains` (clé de config client) | `ecosystems` | ✅ Confirmé à renommer | `config/clients/*.yaml` |
| `domain_id` | `ecosystem_id` | ✅ Confirmé à renommer | `canonical/domains/lai_domain_definition.yaml` |
| `watch_domain_resolver` | `ecosystem_resolver` | ⚠️ Non trouvé dans zones actives — OK (legacy archivé) | — |
| `canonical/domains/` | `canonical/ecosystems/` | ✅ Confirmé à renommer | Dossier complet |
| `canonical/scopes/domain_definitions.yaml` | fusionner dans `canonical/ecosystems/{eco}.yaml` | ✅ Confirmé (contenu redondant avec `canonical/domains/lai_domain_definition.yaml`) | `canonical/scopes/domain_definitions.yaml` |
| `canonical/sources/source_catalog_v3.yaml` | `canonical/sources/source_catalog.yaml` | ✅ Déjà fait — `source_catalog.yaml` existe | — |
| `canonical/ingestion/ingestion_profiles_v3.yaml` | `canonical/ingestion/ingestion_profiles.yaml` | ✅ Déjà fait | — |
| `canonical/ingestion/filter_rules_v3.yaml` | `canonical/ingestion/filter_rules.yaml` | ⚠️ Non trouvé — `filter_rules.yaml` n'existe pas du tout (à créer au Niveau 1) | — |
| `canonical/ingestion/source_configs_v3.yaml` | `canonical/ingestion/source_configs.yaml` | ⚠️ Non trouvé — n'existe pas (à créer au Niveau 1) | — |

**Observation** : 3 des renommages prévus dans le design doc sont déjà réalisés ou concernent des fichiers qui n'existent pas encore. Le travail réel porte sur les 5 premiers.

---

## Section 3 — Occurrences trouvées (tableau exhaustif)

### Catégorie A — Vocabulaire `domain*` / `watch_domain*`

| Fichier | Champ / Terme trouvé | Contexte | Action proposée |
|---|---|---|---|
| `canonical/domains/` | Nom du dossier | Dossier racine des définitions d'écosystème | **Renommer** → `canonical/ecosystems/` |
| `canonical/domains/lai_domain_definition.yaml` | Nom du fichier | Définition de l'écosystème LAI | **Renommer** → `canonical/ecosystems/lai_ecosystem_definition.yaml` |
| `canonical/domains/lai_domain_definition.yaml` | `domain_id: lai` | Champ d'identifiant | **Renommer** champ → `ecosystem_id: lai` |
| `canonical/domains/lai_domain_definition.yaml` | `domain_name: "Long-Acting Injectables"` | Champ de nom | **Renommer** champ → `ecosystem_name: "Long-Acting Injectables"` |
| `canonical/domains/lai_domain_definition.yaml` | Commentaire `# Single source of truth for Long-Acting Injectables domain` | Commentaire descriptif | **Mettre à jour** → `...ecosystem` |
| `canonical/scopes/domain_definitions.yaml` | Nom du fichier + clé racine `lai_domain_definition:` | Doublon partiel de `canonical/domains/lai_domain_definition.yaml` | **Supprimer** ce fichier après fusion dans `canonical/ecosystems/lai_ecosystem_definition.yaml` |
| `canonical/ingestion/ingestion_profiles.yaml` | `domains: ["tech_lai_ecosystem"]` (lignes 143, 183, 218) | Champ référençant les écosystèmes du client | **Renommer** champ → `ecosystems:` |
| `canonical/prompts/domain_scoring/` | Nom du dossier | Dossier de prompts de scoring d'écosystème | **Renommer** → `canonical/prompts/ecosystem_scoring/` (si conservé) — voir Catégorie C |
| `canonical/prompts/domain_scoring/lai_domain_scoring.yaml` | Nom du fichier + `prompt_id: "lai_domain_scoring"` | Prompt de scoring LAI (hors scope V1 Fondations) | **Archiver** (voir Catégorie C) ; si conservé → `lai_ecosystem_scoring.yaml` |
| `canonical/scoring/scoring_rules.yaml` | `domain_priority_weights:` | Champ de configuration des poids | **Renommer** → `ecosystem_priority_weights:` |
| `canonical/scoring/scoring_rules.yaml` | `no_domain_relevance_penalty:` | Pénalité de scoring | **Renommer** → `no_ecosystem_relevance_penalty:` |
| `canonical/scoring/scoring_rules.yaml` | `no_relevant_domain_penalty:` | Pénalité de scoring | **Renommer** → `no_relevant_ecosystem_penalty:` |
| `config/clients/lai_weekly_v2.4.yaml` | `watch_domains:` | Clé principale de la liste des écosystèmes surveillés | **Renommer** → `ecosystems:` |
| `config/clients/lai_weekly_v2.4.yaml` | `domain_scoring_prompt:`, `enable_domain_scoring:` | Champs de config Bedrock | **Renommer** (ou supprimer le fichier — voir Catégorie C) |
| `config/clients/lai_weekly_v2.4.yaml` | `source_domains:` (×4 dans sections newsletter) | Champ référençant les écosystèmes dans les layouts | **Renommer** → `source_ecosystems:` |
| `config/clients/lai_weekly_v3.1_debug.yaml` | `watch_domains:`, `domain_scoring_prompt:`, `enable_domain_scoring:`, `min_domain_score:`, `source_domains:` (×5) | Mêmes champs que ci-dessus | **Renommer** (ou supprimer le fichier — voir Catégorie C) |

**Observation sur `canonical/matching/README.md`** : ce fichier mentionne `watch_domains` et `domain` de nombreuses fois (25+ occurrences) — mais le dossier `canonical/matching/` entier est hors scope V1. Action : archiver le dossier (voir Catégorie C).

**Docs de référence à conserver sans modification** (mentions historiques légitimes) :
- `canonical/sources/INGESTION_EXPLAINED.md` — mentionne `watch_domains` (documentation du workflow V2/V3, historique)
- `canonical/vectora_inbox_newsletter_pipeline_overview.md` — mentions de `watch_domains` (mais fichier à archiver, voir C)
- `docs/architecture/*.md` — mentions de l'ancien vocabulaire sont dans des contextes explicatifs du pivot

---

### Catégorie B — Stack AWS (`bedrock`, `lambda`, `s3`, `boto`)

| Fichier | Terme trouvé | Contexte | Action proposée |
|---|---|---|---|
| `canonical/prompts/normalization/generic_normalization.yaml` | `bedrock_config:` (section de config LLM) | Section définissant les paramètres de l'appel LLM (max_tokens, temperature, anthropic_version) | **Renommer** section → `llm_config:` |
| `canonical/prompts/normalization/generic_normalization.yaml` | `anthropic_version: "bedrock-2023-05-31"` | Valeur de la version API (chaîne imposée par l'API Anthropic directe) | **Garder la valeur** telle quelle (c'est une constante API, pas du vocabulaire interne) |
| `canonical/prompts/domain_scoring/lai_domain_scoring.yaml` | `bedrock_config:` + `anthropic_version: "bedrock-2023-05-31"` | Idem | **Archiver** le fichier (hors scope V1) — si conservé, renommer section → `llm_config:` |
| `canonical/prompts/editorial/lai_editorial.yaml` | `bedrock_config:` (×2) + `anthropic_version: "bedrock-2023-05-31"` (×2) | Idem | **Archiver** le fichier (hors scope V1) |
| `config/clients/lai_weekly_v2.4.yaml` | `bedrock_config:` (section racine du fichier) | Section de config LLM du client | **Supprimer/remplacer** le fichier (voir Catégorie C) |
| `config/clients/lai_weekly_v3.1_debug.yaml` | `bedrock_config:` (section racine du fichier) | Idem | **Supprimer/remplacer** le fichier (voir Catégorie C) |
| `canonical/README.md` | `"Contrats des Lambdas : voir contracts/lambdas/"` | Référence historique à l'ancienne architecture Lambda | **Garder** (doc historique, pas du code actif) |
| `canonical/sources/INGESTION_EXPLAINED.md` | `src/lambdas/ingest_normalize/handler.py` | Référence historique au handler Lambda | **Garder** (doc historique) |
| `canonical/vectora_inbox_newsletter_pipeline_overview.md` | `bedrock_client.py` (×2) | Références à l'ancien client Bedrock | **Archiver** le fichier entier (voir Catégorie C) |
| `tests/unit/test_bedrock_date_extraction.py` | Nom de fichier + contenu | Test unitaire de l'ancien client Bedrock | **Archiver** (tests V2/V3, à réécrire pour V1) |
| `tests/unit/test_bedrock_matcher.py` | Nom de fichier + contenu | Test unitaire du matcher Bedrock | **Archiver** |
| `tests/unit/test_bedrock_retry.py` | Nom de fichier + contenu | Test unitaire du retry Bedrock | **Archiver** |
| `tests/integration/test_bedrock_matching_integration.py` | Nom de fichier + contenu | Test d'intégration du matching Bedrock | **Archiver** |

---

### Catégorie C — Concepts hors scope V1 (`newsletter*`, `scoring*`, `matching*`)

**Rappel** : V1 Fondations = ingestion + normalisation → datalake (raw + curated). Ni newsletter, ni matching, ni scoring ne font partie du scope V1. Ces consommateurs seront développés après.

| Fichier / Dossier | Concept concerné | Action proposée |
|---|---|---|
| `canonical/matching/` (dossier entier) | Matching (hors scope V1) | **Archiver** le dossier → `archive/canonical_v2_matching/` |
| `canonical/matching/domain_matching_rules.yaml` | Règles de matching par type de domaine | Inclus dans l'archivage ci-dessus |
| `canonical/matching/README.md` | Doc du matching | Inclus dans l'archivage ci-dessus |
| `canonical/scoring/` (dossier entier) | Scoring (hors scope V1) | **Archiver** le dossier → `archive/canonical_v2_scoring/` |
| `canonical/scoring/scoring_rules.yaml` | Règles de scoring | Inclus dans l'archivage ci-dessus |
| `canonical/scoring/scoring_examples.md` | Exemples de scoring | Inclus dans l'archivage ci-dessus |
| `canonical/prompts/domain_scoring/` (dossier entier) | Prompt de scoring LAI (hors scope V1) | **Archiver** le dossier → `archive/canonical_v2_prompts_scoring/` |
| `canonical/prompts/editorial/` (dossier entier) | Prompts éditoriaux newsletter (hors scope V1) | **Archiver** le dossier → `archive/canonical_v2_prompts_editorial/` |
| `canonical/vectora_inbox_newsletter_pipeline_overview.md` | Overview de l'ancien pipeline newsletter | **Archiver** → `archive/canonical_v2_docs/` |
| `config/clients/lai_weekly_v2.4.yaml` | Config client V2.4 avec newsletter_*, bedrock_config, watch_domains | **Supprimer** (à remplacer par un config V1 au Niveau 1) |
| `config/clients/lai_weekly_v3.1_debug.yaml` | Config client V3.1 DEBUG avec mêmes sections | **Supprimer** (idem) |
| `tests/unit/test_newsletter_selector_v2.py` | Test du sélecteur newsletter V2 | **Archiver** |
| `tests/unit/test_config_loader_domain_scoring.py` | Test du loader de config pour domain scoring | **Archiver** |
| `tests/local/test_e2e_domain_scoring_complete.py` | Test E2E du domain scoring | **Archiver** |
| `tests/local/test_e2e_domain_scoring_local.py` | Test E2E domain scoring local | **Archiver** |
| `tests/unit/test_scoring_recency.py` | Test de la logique de scoring par récence | **Archiver** |
| `tests/unit/test_normalization_open_world.py` | Test de la normalisation open world (V2/V3) | **Évaluer** — à conserver si la logique est réutilisable en V1, sinon archiver |
| `tests/local/test_e2e_runner.py` | Runner E2E local (référence domaine scoring) | **Évaluer** — lire avant de décider |
| `tests/aws/test_e2e_runner.py` | Runner E2E AWS | **Archiver** (dépend AWS) |

**Note sur `canonical/sources/source_catalog_backup.yaml`** : un fichier "backup" existe à côté du `source_catalog.yaml`. Il n'est mentionné dans aucune config. → **Supprimer** (doublon non versionné, redondant avec git).

---

### Catégorie D — Fichiers `_v3` / `_v2` dans les zones actives

| Fichier | Type | Action proposée |
|---|---|---|
| `config/clients/lai_weekly_v3.1_debug.yaml` | Config client V3 DEBUG | **Supprimer** (traité dans Catégorie C) |
| `config/clients/lai_weekly_v2.4.yaml` | Config client V2 | **Supprimer** (traité dans Catégorie C) |
| `tests/unit/test_date_patterns_v3.py` | Test de patterns de dates V3 | **Évaluer** — la logique de parsing de dates est pertinente pour V1 ; renommer → `test_date_patterns.py` si réutilisée, sinon archiver |
| `tests/unit/test_integrated_date_extraction_v3.py` | Test d'extraction de dates intégré V3 | **Évaluer** — idem, logique utile en V1 |

**Docs avec `_v2`/`_v3` dans leur nom** (hors `archive/`) : entièrement dans `docs/design/`, `docs/plans/`, `docs/reports/`. Ce sont des documents historiques — **garder tels quels** (voir Section 5).

---

## Section 4 — Fichiers `_v3` et `_v2` dans la zone active : synthèse

| Fichier | Statut actuel | Pendant V1 | Sprint pour agir |
|---|---|---|---|
| `config/clients/lai_weekly_v3.1_debug.yaml` | Config client debug V3 avec newsletter/bedrock | À supprimer | Sprint 002 |
| `config/clients/lai_weekly_v2.4.yaml` | Config client V2 avec newsletter/bedrock | À supprimer, remplacer par V1 | Sprint 002 + Niveau 1 |
| `tests/unit/test_date_patterns_v3.py` | Tests de parsing de dates (logique réutilisable) | Évaluer + renommer | Sprint 002 (décision) |
| `tests/unit/test_integrated_date_extraction_v3.py` | Tests extraction de dates intégré | Évaluer + renommer | Sprint 002 (décision) |

---

## Section 5 — Occurrences à garder telles quelles

| Fichier | Terme/Occurrence | Justification |
|---|---|---|
| `canonical/sources/INGESTION_EXPLAINED.md` | `watch_domains`, `lambda`, `bedrock` | Documentation historique du workflow V2/V3, valeur pédagogique conservée |
| `canonical/README.md` | `"Contrats des Lambdas"` | Référence à une doc historique, pas du code actif |
| `canonical/domains/lai_domain_definition.yaml` | Commentaire `# Conceptual definition for Bedrock understanding` | Commentaire explicatif, pas du vocabulaire opérationnel ; peut être mis à jour "pour plus de clarté" mais n'est pas bloquant |
| `canonical/domains/lai_domain_definition.yaml` | `anthropic_version: "bedrock-2023-05-31"` dans la config LLM | Valeur de chaîne imposée par l'API Anthropic directe — **ne pas changer la valeur**, renommer seulement la clé parente (`bedrock_config:` → `llm_config:`) |
| Tous les fichiers dans `docs/design/` | `bedrock`, `newsletter`, `matching`, `domain`, `v3`, `v2` | ~100 fichiers de documentation historique des phases V2/V3. Mémoire du projet. Aucun n'est exécuté. **Ne pas toucher.** |
| Tous les fichiers dans `docs/plans/` | Idem | Idem |
| Tous les fichiers dans `docs/reports/` | Idem | Idem |
| Tous les fichiers dans `docs/implementation/` | Idem | Idem |
| Tous les fichiers dans `docs/guides/` | Idem | Idem |
| Tous les fichiers dans `docs/amélioration moteur/` | Idem | Idem |
| Tous les fichiers dans `docs/snapshots/` | Idem | Idem |
| Tous les fichiers dans `docs/llm_domain_gating*.md` | `domain` dans nom de fichier | Documentation historique d'un concept V2 |
| `tests/utils/config_generator.py` | À vérifier | Utilitaire de test — vérifier si référence bedrock/domain avant de décider |
| `canonical/ingestion/README.md` | `domains: [...]` dans exemples de code | Exemples à mettre à jour lors du renommage des champs réels |
| `canonical/imports/vectora-inbox-lai-core-scopes.yaml` | Contenu non vérifié lors de cet audit | **À vérifier lors de Sprint 002** avant de décider |

---

## Synthèse des actions pour Sprint 002

Sprint 002 exécutera les actions dans cet ordre de priorité :

### Priorité 1 — Renommages critiques (bloquants pour Niveau 1)

1. **Créer `canonical/ecosystems/`** et y déplacer + renommer `lai_domain_definition.yaml` → `lai_ecosystem_definition.yaml`
2. **Mettre à jour les champs** dans `lai_ecosystem_definition.yaml` : `domain_id` → `ecosystem_id`, `domain_name` → `ecosystem_name`
3. **Supprimer `canonical/scopes/domain_definitions.yaml`** après vérification que le contenu est couvert par `lai_ecosystem_definition.yaml`
4. **Renommer `bedrock_config:` → `llm_config:`** dans `canonical/prompts/normalization/generic_normalization.yaml` (seul prompt V1)
5. **Renommer `domains:` → `ecosystems:`** dans `canonical/ingestion/ingestion_profiles.yaml` (3 occurrences)

### Priorité 2 — Archivages (nettoyer avant Niveau 1)

6. Archiver `canonical/matching/` → `archive/canonical_v2_matching/`
7. Archiver `canonical/scoring/` → `archive/canonical_v2_scoring/`
8. Archiver `canonical/prompts/domain_scoring/` → `archive/canonical_v2_prompts_scoring/`
9. Archiver `canonical/prompts/editorial/` → `archive/canonical_v2_prompts_editorial/`
10. Archiver `canonical/vectora_inbox_newsletter_pipeline_overview.md` → `archive/canonical_v2_docs/`
11. Supprimer `config/clients/lai_weekly_v2.4.yaml` et `lai_weekly_v3.1_debug.yaml`
12. Archiver les tests V2/V3 (`test_bedrock_*.py`, `test_newsletter_*.py`, `test_e2e_domain_scoring_*.py`, etc.)
13. Supprimer `canonical/sources/source_catalog_backup.yaml`

### Priorité 3 — Renommages non-bloquants pour Niveau 1

14. Renommer dossier `canonical/prompts/domain_scoring/` si non archivé
15. Mettre à jour `canonical/ingestion/README.md` pour remplacer exemples `domains:` par `ecosystems:`
16. Évaluer et décider pour `test_date_patterns_v3.py` et `test_integrated_date_extraction_v3.py`
17. Vérifier `canonical/imports/vectora-inbox-lai-core-scopes.yaml`

### Non-urgent (Niveau 2 ou 3)

- Renommage des champs dans `canonical/scoring/scoring_rules.yaml` (dossier à archiver de toute façon)
- Renommage des champs dans les futurs configs clients V1 (ils seront écrits directement en V1)

---

*Rapport d'audit Phase 2.1 — Sprint 001 — à valider par Frank avant exécution dans Sprint 002.*
