# Sprint 003 — Stabilisation infrastructure (sortie OneDrive + bug regex)

**Statut** : ✅ Validé
**Palier** : Pré-Niveau 1 (mise à niveau post-audit Opus)
**Date prévue** : 2026-04-25 ou 2026-04-26
**Date effective** : 2026-04-26
**Estimation** : ~1h30
**Durée réelle** : ~1h (réparti sur deux sessions Cowork)
**Modèle recommandé** : 🟡 Sonnet
**Justification du modèle** : Rédaction d'un runbook critique (un mauvais runbook fait perdre des fichiers à Frank). Précision exigée. Sonnet calibré pour ça. Haiku trop léger pour la responsabilité.

---

## Objectif

Sortir le repo de OneDrive (vers un dossier hors-sync, avec raccourci sur le bureau pour la commodité) et corriger le bug critique des regex préfixées `r"..."` dans `source_catalog.yaml`. À la fin du sprint, le repo tourne sur un chemin stable hors OneDrive et la première bombe à retardement est désamorcée.

---

## Critère de fin testable

- [ ] Le repo est physiquement à `C:\Users\franc\dev\vectora-inbox-claude\` (vérifié via `dir C:\Users\franc\dev\` dans cmd Windows)
- [ ] Un raccourci `vectora-inbox-claude.lnk` est sur le bureau et l'ouvrir lance VS Code sur le bon chemin
- [ ] Le repo OneDrive d'origine `C:\Users\franc\OneDrive\Bureau\vectora-inbox - claude\` est supprimé (ou renommé `_TO_DELETE_after_validation\` en attente confirmation)
- [ ] `git status` depuis VS Code dans le nouveau chemin retourne sans erreur
- [ ] Un commit de test passe : `chore(repo): test commit after onedrive move`
- [ ] Un push de test passe vers la branche en cours
- [ ] Cowork peut monter le nouveau dossier (test : reading `STATUS.md` depuis Cowork sur le nouveau chemin fonctionne)
- [ ] Toutes les regex `r"..."` dans `canonical/sources/source_catalog.yaml` sont corrigées (chaînes YAML normales, échappement double-backslash si nécessaire)
- [ ] `python -c "import yaml, re; [re.compile(p) for src in yaml.safe_load(open('canonical/sources/source_catalog.yaml'))['sources'] for p in src.get('date_extraction_patterns', [])]"` exécute sans erreur
- [ ] `STATUS.md` mis à jour : ligne "Difficultés rencontrées" → résolution OneDrive, retrait du #10 du backlog `future_optimizations` (marqué "fait")
- [ ] Sprint 003 commité et poussé

---

## Tâches détaillées (dans l'ordre d'exécution)

### Phase A — Préparation (Cowork, ~30 min)

1. **Claude rédige le runbook** `docs/runbooks/move_repo_out_of_onedrive.md` avec :
   - Diagnostic préalable (git status propre, push récent fait, pas de stash en attente)
   - Snapshot de sécurité : commit + push de tout l'état actuel pour que rien ne se perde si l'opération foire
   - Création du dossier cible `C:\Users\franc\dev\` puis sous-dossier `vectora-inbox-claude\`
   - Pause OneDrive (clic droit icône OneDrive → Pause sync 2h) pour éviter qu'il ré-aspire pendant le `mv`
   - Commande PowerShell de copie : `Copy-Item -Path "C:\Users\franc\OneDrive\Bureau\vectora-inbox - claude" -Destination "C:\Users\franc\dev\vectora-inbox-claude" -Recurse`
   - Vérification post-copie : comparaison de tailles (`Get-ChildItem -Recurse | Measure-Object -Property Length -Sum`)
   - Test git dans le nouveau chemin avant suppression de l'ancien
   - Création du raccourci bureau via PowerShell ou clic droit
   - Reconfiguration VS Code (Open Folder vers le nouveau chemin, retrait de l'ancien des "récents")
   - Suppression de l'ancien chemin (renommage en `_TO_DELETE_after_validation\` d'abord, suppression définitive après 24h de validation)
   - Reprise de OneDrive sync
   - Validation finale (test commit + push)
2. **Claude corrige le bug regex** dans `canonical/sources/source_catalog.yaml` :
   - Pour chaque source corporate (medincell, camurus, delsitech, nanexa, peptron) : retirer le `r` préfixe et passer en chaîne YAML simple. Exemple :
     ```yaml
     # AVANT (bug)
     - r"(\w+ \d{1,2}, \d{4})\w*"
     # APRÈS (correct)
     - "(\\w+ \\d{1,2}, \\d{4})\\w*"
     ```
   - Vérifier que YAML interprète bien `\\w` comme un backslash + w (à benchmarker en local).
   - Alternative plus propre si le double-backslash est confusant pour Frank : utiliser le bloc litteral `|` :
     ```yaml
     - |
       (\w+ \d{1,2}, \d{4})\w*
     ```
   - Choisir une convention et l'appliquer aux 5 sources de manière homogène.
3. **Claude écrit un script de test** `scripts/maintenance/validate_yaml_regexes.py` (~15 lignes) qui charge `source_catalog.yaml`, compile chaque regex, et reporte les erreurs. Sera utile pour CI plus tard.
4. **Claude met à jour `STATUS.md`** :
   - Section "Où on en est aujourd'hui" : "Sprint 003 (stabilisation infrastructure) en cours"
   - Tableau des difficultés rencontrées : ajouter une ligne pour la sortie OneDrive (résolution = sprint 003)
   - Backlog "future_optimizations" : marquer #10 comme "fait" (et faire la même chose dans `future_optimizations.md` lui-même)

### Phase B — Validation Frank (Frank lit, Cowork attend)

5. **Frank lit le runbook** `docs/runbooks/move_repo_out_of_onedrive.md`. S'il a des questions ou des inconforts, Claude clarifie. Sinon GO.

### Phase C — Exécution (VS Code Windows / terminal Frank, ~30 min)

6. **Frank exécute le runbook** étape par étape depuis VS Code (terminal PowerShell). À chaque étape importante, il confirme à Claude que ça s'est bien passé.
7. **Frank teste** : `git status`, commit de test, push de test depuis le nouveau chemin.
8. **Frank ferme VS Code** sur l'ancien chemin, le rouvre sur le nouveau, vérifie que le workspace est propre.

### Phase D — Reconnexion Cowork + commit final (Cowork ou VS Code, ~15 min)

9. **Frank monte le nouveau dossier dans Cowork** (sélection de dossier de travail dans l'interface Cowork). À partir de cet instant, Cowork voit `C:\Users\franc\dev\vectora-inbox-claude\` comme workspace.
10. **Claude vérifie depuis Cowork** que la lecture du repo fonctionne : `Read STATUS.md` retourne le contenu attendu.
11. **Frank commit + push** depuis VS Code :
    - `feat(infra): move repo out of OneDrive to C:\Users\franc\dev\vectora-inbox-claude`
    - `fix(canonical): strip Python r-prefix from regex strings in source_catalog.yaml`
    - `docs(runbook): add move_repo_out_of_onedrive runbook`
    - `docs(status): update STATUS.md after sprint 003`
    Soit en plusieurs commits si Frank préfère, soit un seul `chore(infra): sprint 003 — stabilization`.
12. **Sprint 003 marqué `✅ Validé`** dans son propre fichier (Bilan post-exécution rempli).

---

## Fichiers créés / modifiés / supprimés

**✨ Créés** :
- `docs/runbooks/move_repo_out_of_onedrive.md` (runbook pas-à-pas)
- `scripts/maintenance/validate_yaml_regexes.py` (script de test rapide)

**📝 Modifiés** :
- `canonical/sources/source_catalog.yaml` (bug regex corrigé sur 5 sources corporate)
- `STATUS.md` (entrée Sprint 003, difficulté OneDrive résolue, #10 backlog marqué fait)
- `docs/architecture/future_optimizations.md` (#10 marqué fait avec date et lien sprint)

**🗑️ Supprimés** :
- `C:\Users\franc\OneDrive\Bureau\vectora-inbox - claude\` (ancien emplacement, après 24h de validation par Frank)

**📦 Déplacés** :
- L'intégralité du repo : `C:\Users\franc\OneDrive\Bureau\vectora-inbox - claude\` → `C:\Users\franc\dev\vectora-inbox-claude\`

---

## Règles à suivre (références CLAUDE.md)

- §0 (Claude est architecte mais demande validation pour les changements structurants) : sortie OneDrive est structurant → validation Frank explicite à chaque étape critique
- §3 (Plan → Validation → Exécution) : ce sprint EST le plan ; Frank le valide avant que Claude rédige le runbook
- §6 (conventions Git) : commits format `<type>(<scope>): <message>`
- §11 (en cas d'erreur, Claude n'invente pas, demande à Frank)
- §13 (Cowork rédige, VS Code exécute) : strict respect ici, le déménagement *doit* être fait depuis VS Code Windows
- §14 (checklist avant commit) : vérifier qu'aucun secret n'apparaît, conventions OK
- §17 (small batches) : commit fréquent, surtout après chaque phase A/B/C/D
- §19 (résilience aux plantages) : la phase A doit être commitée avant la phase C, pour que si OneDrive corrompt quelque chose pendant le `mv`, on retombe sur le commit propre

---

## Points de validation par Frank

- ⏸ **Avant exécution Phase A** : Frank valide ce sprint dans son ensemble (le présent document) — c'est la validation que tu vas faire en lisant ce fichier.
- ⏸ **Après Phase A** (rédaction du runbook par Claude) : Frank lit le runbook, le critique si besoin. Pas d'exécution tant qu'il n'est pas serein dessus.
- ⏸ **Pendant Phase C** (exécution par Frank) : à chaque étape importante du runbook (snapshot fait, copie réussie, git OK dans nouveau chemin), Frank reporte à Claude. En cas de blocage, Claude aide en temps réel.
- ⏸ **Après Phase D** : Frank confirme que tout tourne depuis le nouveau chemin et autorise la suppression de l'ancien.

---

## Risques identifiés

| # | Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|---|
| 1 | OneDrive sync pendant la copie crée des conflits / fichiers fantômes | Moyenne | Élevé | Mettre OneDrive en pause AVANT la copie. Vérification de tailles post-copie. |
| 2 | `.git/index.lock` reste verrouillé pendant la copie, repo cible cassé | Moyenne | Moyen | Faire un commit propre + fermer VS Code AVANT la copie. Si ça arrive : supprimer manuellement `.git/index.lock` dans la cible. |
| 3 | Frank lance les commandes dans le mauvais terminal (Cowork au lieu de VS Code) | Faible | Élevé | Runbook explicite "PowerShell Windows uniquement, pas le terminal Cowork". Capture d'écran de l'icône à utiliser. |
| 4 | Régression regex YAML : la correction casse autre chose | Faible | Moyen | Script `validate_yaml_regexes.py` lancé après la correction. Si erreur, on reprend. |
| 5 | Cowork ne retrouve pas le nouveau dossier (mount cassé) | Faible | Faible | Réouvrir Cowork après le déménagement, sélectionner le nouveau dossier explicitement. Backup plan : continuer le sprint depuis VS Code (Claude Code) en attendant. |
| 6 | Suppression prématurée de l'ancien chemin avant validation complète | Moyenne | Élevé | Renommer en `_TO_DELETE_after_validation\` d'abord, suppression définitive après 24h sans incident. |

---

## Dépendances

- ✅ Audit Opus livré (`docs/architecture/audit_opus_response_20260425.md`) — fait
- ✅ Validation Frank des 6 questions de l'audit — fait (réponses données dans la conversation, à matérialiser dans une note de session ou dans le bilan ci-dessous)
- ✅ État du repo propre (pas de modifs non commitées au moment du démarrage Phase A)
- ✅ Accès écriture sur `C:\Users\franc\dev\` (à créer si n'existe pas, mais Frank a les droits utilisateur)

Si une dépendance manque, le sprint ne peut pas démarrer. Notamment : si une modif non commitée traîne, Claude la signale et propose un commit avant de poursuivre.

---

## Bilan post-exécution

À remplir UNE FOIS le sprint terminé. Ne pas pré-remplir.

### Durée réelle vs estimation

- Estimé : ~1h30
- Réel : ~1h (deux sessions Cowork distinctes)
- Écart : -30 min. Phase OneDrive exécutée par Frank indépendamment. Phase regex + script automatisée efficacement via Python.

### Commits effectués

À faire par Frank depuis VS Code (conformément à §13 CLAUDE.md — git depuis Windows uniquement) :
- `fix(canonical): strip Python r-prefix from regex strings in source_catalog.yaml` (28 patterns, 5 sources)
- `feat(maintenance): add validate_yaml_regexes.py script`
- `docs(status): sprint 003 complete — OneDrive moved, regex fixed, STATUS updated`

### Difficultés rencontrées

Aucune difficulté technique lors de la correction regex. La substitution automatique via `re.sub(r'\br"([^"]*)"', ...)` a géré proprement les 28 occurrences sans faux positifs.

**Correction additionnelle (2026-04-26)** : 7 patterns `r"..."` détectés dans `canonical/parsing/parsing_config.yaml` — corrigés vers `"\\..."` (double-backslash pour YAML double-quoted).

### Décisions prises en cours de route

- Convention regex YAML choisie : **single-quoted strings** `'...'` (pas de double-backslash, pas de bloc littéral `|`). Lisible, cohérent avec la façon dont les patterns sont utilisés en Python (`re.compile(pattern)`).

### Ce qui reste pour le prochain sprint

Les Sprints 004 et 005 (ADRs + design + plans + CLAUDE.md) s'exécutent depuis le nouveau chemin `C:\Users\franc\dev\vectora-inbox-claude\`.

### Validation Frank

- Date de validation : 2026-04-26
- Commentaires éventuels : OneDrive OK. Bug regex OK. STATUS à jour.

---

*Sprint 003 — fin du document.*
