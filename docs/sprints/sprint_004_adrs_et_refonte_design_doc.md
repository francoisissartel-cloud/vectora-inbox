# Sprint 004 — ADRs post-audit + refonte du design doc

**Statut** : ⏸ Planifié (bloqué jusqu'à validation Sprint 003)
**Palier** : Pré-Niveau 1 (mise à niveau post-audit Opus)
**Date prévue** : après validation Sprint 003
**Date effective** : (à remplir à l'exécution)
**Estimation** : ~3h
**Durée réelle** : (à remplir post-exécution)
**Modèle recommandé** : 🟡 Sonnet
**Justification du modèle** : Rédaction structurée d'ADRs (5 fiches) + edits chirurgicaux dans un long document de design (~1100 lignes). Pas de raisonnement architectural nouveau (les décisions sont déjà tranchées par l'audit Opus + validation Frank), mais beaucoup de cohérence à maintenir entre les sections. Sonnet calibré.

---

## Objectif

Matérialiser les 5 décisions architecturales validées par Frank suite à l'audit Opus, sous forme d'ADRs versionnées dans `docs/decisions/`, et réécrire les sections concernées de `datalake_v1_design.md` pour passer de V1.4 à V1.5 cohérente avec les nouvelles décisions.

---

## Critère de fin testable

- [ ] 5 ADRs créées dans `docs/decisions/`, numérotées 011 à 015, statut `Accepté`
- [ ] L'ADR 006 (`006-format-jsonl-append-only.md`) est annotée `Partiellement superseded by ADR 011` (les items restent JSONL, les indexes deviennent SQLite)
- [ ] L'ADR 009 (`009-reprise-discovery-validation.md`) est annotée `Superseded by ADR 013` (onboarding par paliers)
- [ ] `datalake_v1_design.md` passe à V1.5, avec les sections suivantes refondues :
  - §3.1 (arborescence du datalake) — pas d'`indexes/` JSON, ajout `index.db` SQLite
  - §3.4 (format curated) — ajout de la section `signals` factuels
  - §4 (indexes) — réécrit autour de SQLite
  - §5.2 / §5.3 (multi-tagging et update in-place) — retirés ou reportés à un futur palier
  - §6.4 (étape NORMALIZE) — ajout du calcul des signaux après LLM, avant write
  - §6.5 (workflow d'onboarding) — restructuré : Validation en N2, Discovery en N3, Promotion supprimée (manuelle)
  - §7 (cache d'URL) — réécrit : structure SQLite (table `url_cache`)
  - §11 (canonical) — `source_configs.yaml` retiré (pas créé en V1), `parsing_config.yaml` enrichi avec date_patterns par source_type
  - §12 (code) — `datalake/indexes.py` retiré, `cli.py` ajouté (Typer), `normalize/signals.py` ajouté, `sources/discovery.py` retiré
- [ ] Le résumé §15 du design doc est mis à jour pour refléter les nouvelles décisions
- [ ] `STATUS.md` : tableau des décisions architecturales mis à jour (5 nouvelles lignes, ADR 006 et 009 annotées)
- [ ] Aucune section du design doc V1.5 ne contredit une autre section ou une ADR
- [ ] Sprint 004 commité et poussé

---

## Tâches détaillées (dans l'ordre d'exécution)

### Phase A — ADRs (Cowork, ~1h30)

1. **Lire l'ADR 005 ou 008** comme référence de format (au démarrage du sprint, pour calibrer le ton et la structure attendue dans le projet).
2. **Créer ADR 011** `docs/decisions/011-sqlite-pour-indexes-et-cache.md` :
   - Contexte : tension §5.1 de l'audit Opus
   - Décision : SQLite pour indexes + cache, JSONL conservé pour items
   - Justification : ACID natif, suppression de ~300 lignes de code maison, lookup et requêtes composées triviaux, stdlib (zéro dépendance)
   - Conséquences : disparition de `datalake/indexes.py`, simplification de `raw.py` et `curated.py`, impact sur §3.1 / §4 / §7 du design doc
   - Statut : `Accepté`
3. **Créer ADR 012** `docs/decisions/012-cli-unifiee-typer.md` :
   - Contexte : tension §5.3 de l'audit Opus
   - Décision : CLI unifiée `vectora <group> <verb>` via Typer, 3 groupes (`run`, `source`, `maintenance`)
   - Justification : 20+ scripts ingérables pour solo non-dev, pattern standard, --help discoverable
   - Conséquences : `src_vectora_inbox_v1/cli.py` unique remplace `scripts/*.py`, dépendance Typer ajoutée à `pyproject.toml`
   - Statut : `Accepté`
4. **Créer ADR 013** `docs/decisions/013-onboarding-source-par-paliers.md` :
   - Contexte : tension §5.4 de l'audit Opus
   - Décision : Validation au Niveau 2, Discovery au Niveau 3+, Promotion supprimée (manuelle)
   - Justification : 8 sources MVP déjà connues, Discovery = 30%+ du budget N2 pour 0 source à découvrir, Promotion = 3 lignes de Python remplacées par édition manuelle YAML
   - Conséquences : `sources/discovery.py` et `sources/promoters.py` retirés du Niveau 2, `sources/validation.py` reste, `sources/revalidator.py` reste (Niveau 3)
   - Statut : `Accepté`
   - Note : **supersedes ADR 009** (à mettre à jour aussi)
5. **Créer ADR 014** `docs/decisions/014-signaux-factuels-curated.md` :
   - Contexte : tension §5.6 de l'audit Opus
   - Décision : pas de scoring dans le curated (datalake reste neutre), MAIS ajout d'une section `signals` factuelle calculée déterministe (sans LLM)
   - Justification : permet aux consommateurs (newsletter) de scorer rapidement, sans imposer d'opinion ; coût zéro USD, ~50ms par item
   - Conséquences : nouveau module `normalize/signals.py`, schéma curated enrichi (§3.4 du design)
   - Statut : `Accepté`
   - Niveau d'implémentation : Niveau 2
6. **Créer ADR 015** `docs/decisions/015-pydantic-pour-modeles-de-donnees.md` :
   - Contexte : tension additionnelle §A de l'audit Opus
   - Décision : Pydantic V2 pour tous les modèles (RawItem, CuratedItem, SourceConfig, ClientConfig, EcosystemConfig)
   - Justification : validation runtime, type hints exploités par VS Code (auto-complétion pour Frank), serialization JSON gratuite, détection des changements de schéma
   - Conséquences : remplace les dataclasses prévues, dépendance Pydantic V2 ajoutée
   - Statut : `Accepté`
7. **Mettre à jour ADR 006** `docs/decisions/006-format-jsonl-append-only.md` : ajouter en haut un encadré `> Partiellement superseded by ADR 011 (2026-04-25) : les items restent JSONL append-only, mais les indexes et le cache passent à SQLite. Voir ADR 011 pour la justification.`
8. **Mettre à jour ADR 009** `docs/decisions/009-reprise-discovery-validation.md` : ajouter en haut un encadré `> Superseded by ADR 013 (2026-04-25) : l'onboarding est désormais découpé par paliers (Validation N2, Discovery N3+, Promotion manuelle). Voir ADR 013.`

### Phase B — Refonte design doc (Cowork, ~1h30)

9. **Lire `datalake_v1_design.md` V1.4 dans son intégralité** (déjà fait pendant l'audit, mais re-skim pour préparer les edits).
10. **Mettre à jour l'en-tête** : version `V1.5`, date, ajout d'un changelog "Changements V1.5" :
    - SQLite pour indexes + cache (ADR 011)
    - CLI unifiée Typer (ADR 012)
    - Onboarding par paliers (ADR 013)
    - Signaux factuels dans le curated (ADR 014)
    - Pydantic pour les modèles (ADR 015)
    - Suppression du multi-tagging in-place (différé)
11. **Réécrire §3.1** (arborescence du datalake) :
    - Retirer tous les fichiers `indexes/*.json`
    - Ajouter `index.db` (SQLite unique)
    - Retirer `_cache/url_cache_*.json` (la table `url_cache` est dans `index.db`)
    - Conserver `items/YYYY/MM/items.jsonl` raw et curated
12. **Réécrire §3.4** (format curated) :
    - Ajouter la section `signals` avec exemple JSON (champs : `is_pure_player_source`, `is_corporate_source`, `is_sector_press`, `mentions_trademark`, `mentions_regulatory_body`, `mentions_clinical_phase`, `title_length`, `content_word_count`, `days_since_published`)
    - Préciser que ces champs sont calculés sans LLM, après normalisation, par `normalize/signals.py`
13. **Réécrire §4** (indexes) en entier autour de SQLite :
    - Schéma SQL minimal (table `items`, table `url_cache`)
    - Suppression du concept "fichiers JSON par index"
    - Section "Lookup et requêtes composées" devient triviale (`SELECT WHERE ...`)
    - Section "Rebuild" : `vectora maintenance rebuild-indexes` re-scanne les JSONL et reconstruit la DB
    - Section sur l'atomicité : ACID natif, plus de risque d'incohérence partielle
14. **Modifier §5.2 et §5.3** (multi-tagging) :
    - §5.2 : "L'enrichissement de tags lors de re-ingestion est différé. En MVP single-écosystème, c'est sans objet. Quand le multi-tagging deviendra réel (Niveau 3+), on adoptera la stratégie de l'overlay sidecar (cf. tension §5.2 de l'audit Opus)."
    - §5.3 : retirer la coordination cache + datalake pour multi-tag, simplifier en : "Si URL déjà en cache `ingested` : skip total. Pas d'ajout de tag. (Différé)."
15. **Modifier §6.4** (étape NORMALIZE) :
    - Étape 7bis : "Calcul des signaux factuels (`normalize/signals.py`) — déterministe, sans LLM, ~50ms"
    - Référence à ADR 014
16. **Réécrire §6.5** (workflow d'onboarding) :
    - Renommer la section : "Workflow d'onboarding de source — découpage par paliers"
    - Niveau 2 : Validation seule. Frank crée la config source à la main dans `source_catalog.yaml`, puis `vectora source validate --source X` teste.
    - Niveau 3 : Discovery automatique + Revalidation périodique
    - Hors scope V1 : Promotion automatisée
    - Référence ADR 013
17. **Réécrire §7** (cache d'URL) :
    - Structure : table SQLite `url_cache (url_canonical TEXT, ecosystem TEXT, status TEXT, item_id TEXT, rejection_reason TEXT, ...)`, clé primaire `(url_canonical, ecosystem)`
    - Comportement (3 cas) : inchangé
    - Maintenance : `vectora maintenance rebuild-cache --ecosystem X` re-scanne le datalake et reconstruit la table
18. **Modifier §11.1** (structure cible canonical) :
    - Retirer `canonical/ingestion/source_configs.yaml` (n'est pas créé en V1)
    - Mention dans `parsing_config.yaml` que les date_patterns sont indexés par `source_type` (pas par source individuelle)
19. **Modifier §12.1** (arborescence du code) :
    - Retirer `datalake/indexes.py` (remplacé par SQLite via SQLAlchemy ou sqlite3 direct dans `datalake/db.py`)
    - Ajouter `datalake/db.py` (helper SQLite : connexion, schéma, requêtes courantes)
    - Retirer `scripts/` séparés, ajouter `cli.py` (Typer)
    - Retirer `sources/discovery.py` et `sources/promoters.py` du Niveau 2 (déplacer en N3 ou supprimer)
    - Ajouter `normalize/signals.py`
20. **Modifier §15** (résumé ultra-condensé) : 6-7 lignes mises à jour pour refléter SQLite, CLI unifiée, signaux, Pydantic, onboarding par paliers.
21. **Relire le doc V1.5 en entier** : vérifier la cohérence transversale (notamment que rien dans §3 ne contredit §11 ou §12, que les références aux scripts sont à jour, etc.).

### Phase C — Mise à jour STATUS.md (Cowork, ~15 min)

22. **Modifier `STATUS.md`** tableau "Décisions architecturales clés" :
    - Ajouter 5 lignes (ADR 011 à 015)
    - Annoter la ligne ADR 006 et ADR 009 (mentionner les supersedes)
    - Mettre à jour "Où on en est aujourd'hui" : "Sprint 004 terminé, Sprint 005 prêt"
    - Mettre à jour la date de dernière mise à jour

### Phase D — Commits (VS Code Frank, ~15 min)

23. **Frank commit + push** depuis VS Code (Cowork ne peut pas commit fiable). Suggestion de découpage des commits :
    - `docs(decisions): add ADR 011 SQLite for indexes and cache`
    - `docs(decisions): add ADR 012 unified CLI with Typer`
    - `docs(decisions): add ADR 013 onboarding source by levels`
    - `docs(decisions): add ADR 014 factual signals in curated`
    - `docs(decisions): add ADR 015 Pydantic for data models`
    - `docs(decisions): mark ADR 006 and 009 as superseded`
    - `docs(architecture): refactor datalake_v1_design.md to V1.5`
    - `docs(status): update STATUS.md after sprint 004`
    - Soit en bloc : `docs: sprint 004 — ADRs and design doc V1.5` si Frank préfère.

---

## Fichiers créés / modifiés / supprimés

**✨ Créés** :
- `docs/decisions/011-sqlite-pour-indexes-et-cache.md`
- `docs/decisions/012-cli-unifiee-typer.md`
- `docs/decisions/013-onboarding-source-par-paliers.md`
- `docs/decisions/014-signaux-factuels-curated.md`
- `docs/decisions/015-pydantic-pour-modeles-de-donnees.md`

**📝 Modifiés** :
- `docs/architecture/datalake_v1_design.md` (V1.4 → V1.5, sections §3, §4, §5, §6, §7, §11, §12, §15)
- `docs/decisions/006-format-jsonl-append-only.md` (annotation supersede partiel)
- `docs/decisions/009-reprise-discovery-validation.md` (annotation supersede)
- `STATUS.md` (tableau des décisions, section "Où on en est", date)

**🗑️ Supprimés** :
- Aucun

---

## Règles à suivre (références CLAUDE.md)

- §3 (Plan → Validation → Exécution) : sprint validé par Frank avant exécution
- §9 (où mettre quoi) : ADRs vont dans `docs/decisions/`, design dans `docs/architecture/`
- §16.2 (ADRs immutables) : on n'efface pas ADR 006 ou 009, on les annote
- §16.3 (workflow de mise à jour) : ADR + design + STATUS.md doivent être commités cohérents ensemble
- §17 (small batches) : commit après chaque ADR + un commit pour la refonte design + un commit STATUS — au moins 7 commits
- §18 (un sprint = un fichier) : ce sprint est dans son propre fichier ; les ADRs sont des livrables, pas des sprints

---

## Points de validation par Frank

- ⏸ **Avant exécution** : valider ce sprint dans son ensemble
- ⏸ **Après ADR 011** (la plus structurante) : Frank lit, valide ou demande retouches. Si OK, on enchaîne les 4 autres.
- ⏸ **Après les 5 ADRs** : Frank confirme avant qu'on attaque la refonte du design doc (qui découle des ADRs)
- ⏸ **Après refonte design V1.5** : Frank lit le diff complet (avec git diff ou via VS Code), valide la cohérence
- ⏸ **Avant push final** : Frank valide les commits

---

## Risques identifiés

| # | Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|---|
| 1 | Une ADR contredit une autre ou contredit le design V1.5 | Moyenne | Moyen | Relecture transversale en fin de phase B avant commit. Si incohérence : on corrige et on note dans le bilan. |
| 2 | Le design V1.5 perd des informations utiles de V1.4 par mauvaise refonte | Faible | Élevé | Frank lit le diff complet (pas juste le résultat) avant validation. Comparaison V1.4 ↔ V1.5 explicite. |
| 3 | Frank découvre en lisant les ADRs qu'il a mal compris une recommandation de l'audit | Moyenne | Élevé | Si ça arrive : on s'arrête, on rediscute, on ajuste. Les ADRs sont à statut `Proposed` jusqu'à validation explicite, pas `Accepté` par défaut. |
| 4 | Le sprint dérape au-delà de 4h (CLAUDE.md §18) | Moyenne | Faible | Si on dépasse : on commit ce qui est fait, on poursuit en Sprint 004bis. Pas de mégasprint. |
| 5 | Conflit avec CLAUDE.md §17 si un commit dépasse 5 fichiers | Faible | Faible | Découpage en plusieurs commits (1 par ADR, 1 par section refondue si gros, 1 STATUS). |

---

## Dépendances

- ✅ Sprint 003 (stabilisation infrastructure) — terminé et validé. Le repo doit être hors OneDrive avant qu'on touche aux docs (sinon on prend les risques OneDrive sur du travail délicat).
- ✅ Audit Opus — livré (`docs/architecture/audit_opus_response_20260425.md`)
- ✅ Validation Frank des 6 questions de l'audit — fait dans la conversation, à matérialiser dans la note de session
- ✅ ADR 005 ou 008 — existante (sert de référence de format pour les nouvelles ADRs)

Si une dépendance manque : Sprint 003 d'abord. Sinon on travaille dans OneDrive et on prend des risques inutiles.

---

## Bilan post-exécution

À remplir UNE FOIS le sprint terminé. Ne pas pré-remplir.

### Durée réelle vs estimation

- Estimé : ~3h
- Réel : (à remplir)
- Écart : (justifier si > 50%)

### Commits effectués

- (à remplir)

### Difficultés rencontrées

(à remplir)

### Décisions prises en cours de route

(à remplir)

### Ce qui reste pour le prochain sprint

Sprint 005 enchaîne directement après celui-ci : refonte du `level_1_plan.md` autour du walking skeleton + medincell HTML, et refonte de CLAUDE.md V1.6 (extraction §15 et §20 vers runbooks).

### Validation Frank

- Date de validation : (à remplir)
- Commentaires éventuels :

---

*Sprint 004 — fin du document.*
