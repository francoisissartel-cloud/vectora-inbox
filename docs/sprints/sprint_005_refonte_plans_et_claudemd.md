# Sprint 005 — Refonte level_1_plan + CLAUDE.md V1.6

**Statut** : ⛔ Superseded by Sprint 006 — sera renuméroté Sprint 008 et exécuté dans le nouveau repo vectora
**Palier** : Pré-Niveau 1 (mise à niveau post-audit Opus)
**Date prévue** : après validation Sprint 004
**Date effective** : (à remplir à l'exécution)
**Estimation** : ~2h30
**Durée réelle** : (à remplir post-exécution)
**Modèle recommandé** : 🟡 Sonnet
**Justification du modèle** : Réécriture de plan de palier (8 mini-sprints à séquencer en walking skeleton) et refonte d'un document central (CLAUDE.md). Demande de la rigueur dans le découpage des sprints L1-S1 à L1-S8 et de la précision dans l'extraction des sections §15/§20 vers des runbooks. Sonnet calibré.

---

## Objectif

Refondre `level_1_plan.md` autour du walking skeleton (Sprint L1-S1 = E2E avec mocks, Sprints suivants = remplacement progressif des mocks) et autour de medincell HTML comme source pilote ; et refondre `CLAUDE.md` en V1.6 par extraction des sections §15 (gestion coûts) et §20 (gestion modèles) vers des runbooks dédiés, avec ajout d'un encadré §6 sur la limite Cowork pour les commits autonomes. À la fin du sprint, tous les documents sont alignés et le projet est prêt à attaquer le Sprint L1-S1 (premier code V1).

---

## Critère de fin testable

- [ ] `docs/architecture/level_1_plan.md` est en V2, structuré autour du walking skeleton, source pilote = medincell (HTML), 8 sprints L1-S1 à L1-S8 décrits brièvement (1 paragraphe chacun)
- [ ] L'estimation Niveau 1 est passée de "8-12h" à "12-16h" (justifiée par le choix HTML au lieu de RSS)
- [ ] `CLAUDE.md` est en V1.6 avec :
  - §15 condensé (~20 lignes), pointant vers `docs/runbooks/cost_management.md`
  - §20 condensé (~20 lignes), pointant vers `docs/runbooks/model_selection.md`
  - §6 enrichi d'un encadré explicite "Autonomie commit + push : Claude Code dans VS Code uniquement, jamais depuis Cowork"
  - Numéro de version à jour, changelog V1.6 ajouté
- [ ] `docs/runbooks/cost_management.md` créé avec le contenu intégral de l'ancien §15
- [ ] `docs/runbooks/model_selection.md` créé avec le contenu intégral de l'ancien §20
- [ ] `STATUS.md` final mis à jour : Sprint 005 terminé, "Prochaine étape" = "Sprint L1-S1 — Bootstrap walking skeleton"
- [ ] Aucune référence interne (lien, mention de §X) cassée par les renommages/extractions
- [ ] Sprint 005 commité et poussé

---

## Tâches détaillées (dans l'ordre d'exécution)

### Phase A — Refonte `level_1_plan.md` (Cowork, ~1h)

1. **Lire le `level_1_plan.md` V1 actuel** pour identifier ce qui change vs ce qui reste.
2. **Réécrire l'en-tête** : version V2, changelog "Changements V2" :
   - Approche walking skeleton (au lieu de bottom-up)
   - Source pilote = medincell HTML (au lieu de "1 source RSS")
   - Estimation 12-16h (au lieu de 8-12h)
   - SQLite pour indexes (référence ADR 011)
   - CLI unifiée Typer (référence ADR 012)
3. **Réécrire la section "Objectif"** :
   - Pipeline bout-en-bout sur 1 source HTML (medincell), 1 item LAI
   - Approche walking skeleton : E2E dégradé d'abord, raffiné progressivement
   - Toujours config-driven dès le départ
4. **Réécrire la section "Critère de fin testable"** :
   - `vectora run pipeline --client mvp_test_30days --source press_corporate__medincell` produit 1 item raw + 1 item curated
   - Note : la commande change de `python scripts/run_pipeline.py` à `vectora run pipeline` (CLI unifiée)
5. **Réécrire la section "Composants à livrer"** en regroupant par sprint walking skeleton plutôt que par groupe technique :
   - Sprint L1-S1 : Bootstrap + skeleton mocké (orchestrator, fetcher mock, parser mock, LLM mock, datalake mock)
   - Sprint L1-S2 : Datalake réel (SQLite + JSONL append, item_id, lookup) — remplace mock storage
   - Sprint L1-S3 : Fetcher HTTP réel + parser HTML (medincell) — remplace 2 mocks
   - Sprint L1-S4 : LLM réel (Anthropic Claude Sonnet via API) + Pydantic models — remplace mock LLM
   - Sprint L1-S5 : Config-driven (chargement YAML canonical + client) — remplace les hardcoded
   - Sprint L1-S6 : Detect gap + retry minimal LLM
   - Sprint L1-S7 : Tests unitaires des fonctions critiques (item_id, url_canonicalization, parser HTML medincell)
   - Sprint L1-S8 : Polish + smoke test final
6. **Réécrire la section "Séquencement"** :
   - Diagramme : à chaque sprint, le pipeline tourne. Sprint N remplace un mock du sprint N-1.
   - Pas de phase "tout est cassé entre les sprints"
7. **Réécrire la section "Mini-sprints prévus"** : tableau avec ID, titre, objectif court, modèle. Tous Sonnet sauf si justifié sinon. Estimations individuelles plausibles (1-2h chaque).
8. **Réécrire la section "Contraintes et principes"** :
   - 1 seule source : medincell
   - Parser HTML : sélecteurs CSS spécifiques medincell (BeautifulSoup)
   - Filtres désactivés en N1 (accept-all)
   - SQLite + JSONL pour le datalake
   - CLI unifiée dès Sprint L1-S1
   - Pydantic dès Sprint L1-S4
   - Tests minimaux (cf. CLAUDE.md §8)

### Phase B — Création des runbooks (Cowork, ~30 min)

9. **Créer `docs/runbooks/cost_management.md`** :
   - Copier intégralement le contenu de CLAUDE.md §15 actuel (~150 lignes)
   - Ajouter en-tête : titre, statut, lien retour vers CLAUDE.md §15 condensé
   - Vérifier que les références internes restent cohérentes
10. **Créer `docs/runbooks/model_selection.md`** :
    - Copier intégralement le contenu de CLAUDE.md §20 actuel (~130 lignes)
    - Ajouter en-tête : titre, statut, lien retour vers CLAUDE.md §20 condensé
    - Vérifier les références internes

### Phase C — Refonte `CLAUDE.md` V1.6 (Cowork, ~45 min)

11. **Lire CLAUDE.md V1.5 actuel** pour identifier toutes les références croisées qui pourraient être cassées par l'extraction.
12. **Mettre à jour l'en-tête CLAUDE.md** : version V1.6, date, changelog "Changements V1.6" :
    - Extraction §15 vers `docs/runbooks/cost_management.md`
    - Extraction §20 vers `docs/runbooks/model_selection.md`
    - Encadré §6 sur la limite Cowork pour les commits
13. **Réécrire CLAUDE.md §15** en version condensée (~20 lignes) :
    - Garder les principes essentiels : 2 types de coûts (Pro vs API), garde-fous techniques (cap par run, tracking, alerte mensuelle), règle "annoncer le coût avant de lancer"
    - Renvoyer au runbook pour : projections détaillées, ordres de grandeur, recommandations pratiques, garde-fous Anthropic Console
14. **Réécrire CLAUDE.md §20** en version condensée (~20 lignes) :
    - Garder les principes essentiels : 3 modèles (Haiku/Sonnet/Opus), Sonnet par défaut pour le code, règle "Claude annonce le modèle recommandé avant chaque sprint"
    - Renvoyer au runbook pour : tableau détaillé des usages, comment changer de modèle, gestion des fenêtres de conversation, discipline de session
15. **Enrichir CLAUDE.md §6** : ajouter un encadré clair (avant la sous-section "Push") :
    > **Limite Cowork — important pour la discipline §6** : l'autonomie de Claude pour faire commit + push (cf. ci-dessous) ne s'applique **que dans Claude Code (VS Code)**. Depuis Cowork, Claude **n'exécute jamais** `git commit` ni `git push` — il prépare les fichiers et donne à Frank les commandes exactes à lancer depuis VS Code. Raison : la sandbox Linux de Cowork n'a pas accès git fiable au filesystem Windows, même après la sortie OneDrive. Cette règle complète CLAUDE.md §13.
16. **Vérifier toutes les références §X dans CLAUDE.md** : si un §X ailleurs dans le document référence une partie déplacée du §15 ou §20, mettre à jour le lien (vers le runbook).
17. **Vérifier les références dans `STATUS.md`** : la section "Comment naviguer dans le projet" mentionne "Quel modèle (Haiku/Sonnet/Opus) utiliser pour quelle tâche → CLAUDE.md §20" — à actualiser pour pointer vers le runbook.
18. **Vérifier les références dans les sprints existants** (000, 001, 002) : si un sprint cite "CLAUDE.md §15" ou "§20", mettre à jour vers les runbooks. (Probablement aucun, mais on vérifie.)

### Phase D — Mise à jour `STATUS.md` (Cowork, ~10 min)

19. **Modifier `STATUS.md`** :
    - Section "Où on en est aujourd'hui" : "Sprint 005 terminé. Prêt pour Sprint L1-S1 (Niveau 1 — Bootstrap walking skeleton)."
    - Roadmap : marquer "Mise à niveau post-audit Opus" comme ✅ Fait (couvre sprints 003, 004, 005)
    - Tableau "Comment naviguer dans le projet" : ajouter lignes vers les 2 nouveaux runbooks
    - Date de dernière mise à jour
20. **Vérifier la cohérence d'ensemble** : tous les liens internes fonctionnent, aucune référence morte, le passage à Sprint L1-S1 est explicite.

### Phase E — Commits (VS Code Frank, ~15 min)

21. **Frank commit + push** depuis VS Code. Découpage suggéré :
    - `docs(runbooks): extract cost management from CLAUDE.md`
    - `docs(runbooks): extract model selection from CLAUDE.md`
    - `docs(rules): refactor CLAUDE.md to V1.6 (extract §15 §20, add §6 Cowork note)`
    - `docs(architecture): refactor level_1_plan.md to V2 (walking skeleton + medincell HTML)`
    - `docs(status): update STATUS.md after sprint 005`
    - Soit en bloc : `docs: sprint 005 — refactor plans and CLAUDE.md`

---

## Fichiers créés / modifiés / supprimés

**✨ Créés** :
- `docs/runbooks/cost_management.md` (extraction de CLAUDE.md §15)
- `docs/runbooks/model_selection.md` (extraction de CLAUDE.md §20)

**📝 Modifiés** :
- `docs/architecture/level_1_plan.md` (V1 → V2, refonte walking skeleton + medincell HTML)
- `CLAUDE.md` (V1.5 → V1.6, §15 et §20 condensés, §6 enrichi)
- `STATUS.md` (Sprint 005 terminé, navigation enrichie, roadmap)
- `docs/sprints/sprint_000_*.md` à `docs/sprints/sprint_002_*.md` (si références §15/§20 trouvées — peu probable)

**🗑️ Supprimés** :
- Aucun (les sections de CLAUDE.md sont déplacées, pas supprimées)

---

## Règles à suivre (références CLAUDE.md)

- §3 (Plan → Validation → Exécution) : sprint validé par Frank avant exécution
- §9 (où mettre quoi) : runbooks vont dans `docs/runbooks/`
- §10 (en cas de désaccord) : si Claude pense qu'une recommandation de l'audit Opus est mal interprétée par Frank, le dire avant d'exécuter
- §13 (Cowork rédige, VS Code commit) : strict
- §17 (small batches) : commit après chaque livrable significatif
- §18 (un sprint = un fichier) : ce sprint dans son propre fichier, pas mélangé avec L1-S1
- §16.3 (workflow de mise à jour) : tout doit être commité cohérent ensemble

---

## Points de validation par Frank

- ⏸ **Avant exécution** : valider ce sprint
- ⏸ **Après refonte level_1_plan V2** : Frank lit, valide la pertinence du walking skeleton et du découpage en 8 sprints. Si retouche : on ajuste avant la phase B.
- ⏸ **Après création des 2 runbooks** : Frank valide qu'aucune information critique n'est perdue dans l'extraction
- ⏸ **Après refonte CLAUDE.md V1.6** : Frank lit le diff complet (V1.5 → V1.6) et valide
- ⏸ **Avant push final** : Frank valide les commits et le passage Sprint L1-S1

---

## Risques identifiés

| # | Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|---|
| 1 | L'extraction §15/§20 perd ou déforme une règle importante | Moyenne | Moyen | Diff exhaustif comparant l'avant/après. Frank valide explicitement. |
| 2 | Le walking skeleton du level_1_plan V2 est mal séquencé (ex: SQLite arrive après le LLM) | Moyenne | Moyen | Relire le séquencement à voix haute : "à la fin de chaque sprint, qu'est-ce que je peux observer tourner ?" Si la réponse n'est pas claire, on rééquilibre. |
| 3 | Le sprint dérape au-delà de 4h | Moyenne | Faible | Découper en Sprint 005a et 005b si dépassement (a = level_1_plan, b = CLAUDE.md). Pas de mégasprint. |
| 4 | Référence interne cassée (§X qui pointe vers du contenu déplacé) | Élevée | Faible | Audit final des liens avant commit. Grep `CLAUDE.md §15` et `CLAUDE.md §20` dans tout le repo. |
| 5 | Frank revient sur une décision en lisant les docs raffinés | Faible | Élevé | Si ça arrive : on s'arrête, on rediscute, on ré-amende ADRs si besoin. Pas de honte à itérer. |
| 6 | `docs/runbooks/` n'existe pas encore comme dossier | Très élevée | Aucun | Créer le dossier en début de phase B (fait au passage par Write tool). |

---

## Dépendances

- ✅ Sprint 003 (stabilisation infrastructure) — terminé et validé
- ✅ Sprint 004 (ADRs + refonte design doc V1.5) — terminé et validé
- ✅ Audit Opus — livré
- ✅ ADR 011 (SQLite) et ADR 012 (CLI Typer) — acceptées (référencées dans le level_1_plan V2)
- ✅ ADR 015 (Pydantic) — acceptée (référencée dans le level_1_plan V2)

Si une dépendance manque : on traite la dépendance d'abord. Notamment, sans Sprint 004, le level_1_plan V2 ne peut pas référencer les ADRs.

---

## Bilan post-exécution

À remplir UNE FOIS le sprint terminé. Ne pas pré-remplir.

### Durée réelle vs estimation

- Estimé : ~2h30
- Réel : (à remplir)
- Écart : (justifier si > 50%)

### Commits effectués

- (à remplir)

### Difficultés rencontrées

(à remplir)

### Décisions prises en cours de route

(à remplir)

### Ce qui reste pour le prochain sprint

Sprint L1-S1 — Bootstrap + walking skeleton mocké (premier code V1, voir level_1_plan.md V2 pour le détail). Conditions remplies pour démarrer : repo hors OneDrive, design V1.5 stable, plan N1 V2 cohérent, CLAUDE.md V1.6 à jour, ADRs en place.

### Validation Frank

- Date de validation : (à remplir)
- Commentaires éventuels :

---

*Sprint 005 — fin du document.*
