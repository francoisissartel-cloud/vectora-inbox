# Runbook — Sortir le repo Vectora Inbox de OneDrive

**Version** : 1.0
**Date** : 2026-04-25
**Pour qui** : Frank, exécution depuis VS Code (terminal PowerShell Windows)
**Sprint associé** : `docs/sprints/sprint_003_stabilisation_infrastructure.md`
**Durée estimée** : 30-45 minutes
**Niveau de risque** : moyen — la procédure est sûre **si on suit l'ordre**. Si on saute des étapes (notamment la pause OneDrive ou le commit préalable), on peut corrompre le repo.

---

## À quoi sert ce runbook

Le repo `vectora-inbox - claude` est actuellement à `C:\Users\franc\OneDrive\Bureau\vectora-inbox - claude\`. Comme le bureau Windows de Frank est synchronisé avec OneDrive, le repo est aussi synchronisé en permanence — ce qui crée des risques (verrous transitoires, latence, corruption potentielle pendant l'écriture du datalake).

On déplace le repo vers `C:\Users\franc\dev\vectora-inbox-claude\` (hors OneDrive), et on crée un raccourci sur le bureau pour conserver la commodité d'accès.

**Bonus** : on en profite pour retirer l'espace problématique du nom de dossier (`vectora-inbox - claude` → `vectora-inbox-claude`). Les espaces dans les chemins de projet causent des bugs avec git, Python, et les outils CLI.

---

## ⚠️ Règles de sécurité avant de commencer

1. **Travailler dans PowerShell Windows uniquement**, jamais dans le terminal Cowork. Cowork tourne dans une sandbox Linux qui ne peut pas faire `git` correctement sur le filesystem Windows.
2. **Avoir VS Code fermé** pendant le `Copy-Item` et le `Remove-Item`. Sinon les fichiers sont en lecture par VS Code, la copie peut être incomplète.
3. **Ne pas supprimer l'ancien chemin avant validation complète** du nouveau chemin. On renomme d'abord en `_TO_DELETE_after_validation\`, on attend 24h sans incident, puis on supprime.
4. **OneDrive en pause** pendant la copie. Sinon il peut "voir" les nouveaux fichiers à la cible et essayer de les sync — comportement imprévisible.
5. **À chaque étape avec un ⚠️**, lire avant d'exécuter. Si un truc te semble bizarre, demander à Claude avant de continuer.

---

## Étape 0 — Pré-vérifications (5 min)

### 0.1 Ouvrir PowerShell

- Sur Windows, taper `PowerShell` dans le menu Démarrer.
- **Important** : NE PAS prendre `Windows PowerShell ISE` ni le terminal Cowork. Le terminal cible est PowerShell standard ou Windows Terminal.

### 0.2 Vérifier que le repo actuel est dans un état propre

```powershell
cd "C:\Users\franc\OneDrive\Bureau\vectora-inbox - claude"
git status
```

**Sortie attendue** :
```
On branch <nom-de-la-branche>
nothing to commit, working tree clean
```

**Si `git status` montre des modifications non commitées** :
- ⚠️ STOP. Ne pas continuer le runbook.
- Identifier ce qui n'est pas commité : `git status` puis `git diff`
- Choix : (a) commiter et pousser ces modifs, ou (b) les stasher (`git stash`)
- Reprendre le runbook une fois le tree propre

**Si `git status` montre `Your branch is ahead of 'origin/...' by N commits`** :
- Pousser : `git push`
- Vérifier que le push a réussi : refaire `git status`, on doit avoir "up to date"

### 0.3 Vérifier qu'il n'y a pas de stash en attente

```powershell
git stash list
```

**Sortie attendue** :
```
(rien — aucune sortie)
```

**Si des stashes sont listés** : décider quoi en faire (apply + commit, ou drop). Idéalement résoudre avant le déménagement pour repartir propre.

### 0.4 Snapshot de sécurité — pousser un dernier commit "before-onedrive-move"

Même si le tree est propre, créer un commit vide tag-like pour marquer le point de retour :

```powershell
git commit --allow-empty -m "chore(infra): snapshot before onedrive move"
git push
```

**À quoi ça sert** : si quelque chose tourne mal pendant le déménagement, ce commit existe sur GitHub et tu peux re-cloner le repo from scratch en garantissant de ne rien perdre.

### 0.5 Vérifier le remote GitHub

```powershell
git remote -v
```

**Sortie attendue** :
```
origin  https://github.com/<ton-user>/<ton-repo>.git (fetch)
origin  https://github.com/<ton-user>/<ton-repo>.git (push)
```

Note l'URL — on la vérifiera après le déménagement pour s'assurer qu'elle est intacte.

### 0.6 Vérifier la taille du repo (pour estimer le temps de copie)

```powershell
Get-ChildItem -Path "C:\Users\franc\OneDrive\Bureau\vectora-inbox - claude" -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum | ForEach-Object { "Taille totale : {0:N2} MB ({1} fichiers)" -f ($_.Sum / 1MB), $_.Count }
```

**Sortie attendue** : quelques dizaines de MB, quelques milliers de fichiers (le `.git` représente la majorité).

Note la taille — on la comparera après la copie pour vérifier l'intégrité.

### 0.7 Vérifier l'espace disque libre sur C:

```powershell
Get-PSDrive C | Select-Object Used, Free, @{Name="Free(GB)";Expression={[math]::Round($_.Free / 1GB, 2)}}
```

**Sortie attendue** : au moins **2 GB libres** (large marge — la copie temporaire double l'espace utilisé pendant 24h).

**Si moins de 2 GB libres** : libérer de l'espace avant de continuer, sinon la copie échouera ou ralentira gravement.

---

## Étape 1 — Préparation OneDrive et VS Code (3 min)

### 1.1 ⚠️ Mettre OneDrive en pause

- Cliquer sur l'icône OneDrive dans la barre des tâches (le petit nuage bleu, en bas à droite).
- Cliquer sur l'icône engrenage (Aide et paramètres) → **Suspendre la synchronisation** → choisir **2 heures**.
- L'icône OneDrive change : un petit symbole "pause" apparaît dessus.

**Pourquoi 2h** : largement plus que les 30 min prévues, marge de sécurité.

### 1.2 ⚠️ Fermer VS Code complètement

- Si VS Code est ouvert sur le repo, le fermer (Fichier → Fermer la fenêtre, puis fermer toutes les autres instances de VS Code).
- Vérifier dans le gestionnaire des tâches que `Code.exe` n'apparaît plus.

**Pourquoi** : si VS Code maintient des fichiers ouverts, la copie peut être incomplète et la suppression peut échouer (Permission Denied).

### 1.3 ⚠️ Fermer Cowork

- Cowork peut maintenir le mount du dossier ouvert. Le fermer le temps du déménagement.
- Le rouvrir à l'étape 5 quand on aura la nouvelle cible.

---

## Étape 2 — Créer le dossier cible (1 min)

```powershell
# Créer C:\Users\franc\dev\ s'il n'existe pas
New-Item -ItemType Directory -Force -Path "C:\Users\franc\dev"

# Vérifier qu'il existe
Test-Path "C:\Users\franc\dev"
```

**Sortie attendue** : `True`

⚠️ NE PAS créer `C:\Users\franc\dev\vectora-inbox-claude\` à la main. Le `Copy-Item` à l'étape suivante va le créer en copiant.

---

## Étape 3 — Copier le repo vers la nouvelle cible (5-15 min selon taille)

### 3.1 Lancer la copie

```powershell
Copy-Item -Path "C:\Users\franc\OneDrive\Bureau\vectora-inbox - claude" `
          -Destination "C:\Users\franc\dev\vectora-inbox-claude" `
          -Recurse -Force
```

**Sortie attendue** : aucune sortie console (ou des messages de progression). Le prompt revient quand c'est fini.

**Durée** : 30 secondes à plusieurs minutes selon la taille. Si OneDrive avait des fichiers en mode "à la demande" (placeholder), la copie va les télécharger d'abord — ça peut prendre plus longtemps.

### 3.2 Vérifier que la copie a bien créé le dossier

```powershell
Test-Path "C:\Users\franc\dev\vectora-inbox-claude"
Test-Path "C:\Users\franc\dev\vectora-inbox-claude\.git"
Test-Path "C:\Users\franc\dev\vectora-inbox-claude\CLAUDE.md"
```

**Sortie attendue** : `True` × 3.

### 3.3 Comparer la taille avec l'original

```powershell
$old = (Get-ChildItem -Path "C:\Users\franc\OneDrive\Bureau\vectora-inbox - claude" -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum)
$new = (Get-ChildItem -Path "C:\Users\franc\dev\vectora-inbox-claude" -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum)
"Ancien : {0:N2} MB ({1} fichiers)" -f ($old.Sum / 1MB), $old.Count
"Nouveau : {0:N2} MB ({1} fichiers)" -f ($new.Sum / 1MB), $new.Count
```

**Sortie attendue** : les deux lignes doivent afficher des chiffres **identiques** (à quelques bytes près si OneDrive a touché à un timestamp, mais le nombre de fichiers doit être pile pareil).

⚠️ **Si les chiffres ne correspondent pas** : STOP. Demander à Claude. Probables causes : copie interrompue, OneDrive pas vraiment en pause, fichiers en placeholder non téléchargés.

---

## Étape 4 — Tester le repo dans le nouveau chemin (5 min)

### 4.1 Aller dans le nouveau chemin

```powershell
cd "C:\Users\franc\dev\vectora-inbox-claude"
pwd
```

**Sortie attendue** : `Path: C:\Users\franc\dev\vectora-inbox-claude`

### 4.2 Tester git

```powershell
git status
```

**Sortie attendue** :
```
On branch <nom-de-la-branche>
Your branch is up to date with 'origin/...'
nothing to commit, working tree clean
```

⚠️ **Si erreur "fatal: not a git repository"** : la copie du `.git/` a foiré. STOP, demander à Claude.

⚠️ **Si erreur "fatal: index file corrupt"** : `.git/index.lock` ou `.git/index` est corrompu. Souvent récupérable :
```powershell
Remove-Item .git\index.lock -ErrorAction SilentlyContinue
git reset
git status
```
Si toujours cassé : demander à Claude.

### 4.3 Vérifier le remote (doit être identique à l'étape 0.5)

```powershell
git remote -v
```

**Sortie attendue** : la même URL `origin  https://github.com/...` qu'à l'étape 0.5.

### 4.4 Test de commit + push

```powershell
git commit --allow-empty -m "chore(infra): test commit after onedrive move (sprint 003)"
git push
```

**Sortie attendue** : push qui passe sans erreur.

⚠️ Si erreur : demander à Claude. Possible : configuration credentials git, mauvais remote, etc.

---

## Étape 5 — Reconfigurer VS Code (3 min)

### 5.1 Ouvrir VS Code

- Lancer VS Code depuis le menu Démarrer.

### 5.2 Ouvrir le nouveau dossier

- File → Open Folder → naviguer vers `C:\Users\franc\dev\vectora-inbox-claude` → Sélectionner un dossier.
- VS Code charge le workspace.

### 5.3 Retirer l'ancien dossier des "récents"

- File → Open Recent → la liste s'affiche.
- Pour `C:\Users\franc\OneDrive\Bureau\vectora-inbox - claude` : passer la souris dessus, cliquer sur l'icône poubelle ou le `X` à droite.
- ⚠️ Si tu ne fais pas ce nettoyage, tu risques d'ouvrir l'ancien dossier par erreur plus tard.

### 5.4 Tester un commit depuis VS Code

Ouvrir l'onglet Source Control de VS Code (icône git dans la barre latérale gauche) :
- Vérifier que la branche affichée en bas à gauche est correcte.
- Vérifier que les changements éventuels (None pour l'instant) s'affichent normalement.

Pas besoin de commiter pour de vrai à cette étape, juste vérifier que l'UI git de VS Code reconnaît le repo.

---

## Étape 6 — Reprendre OneDrive (1 min)

### 6.1 Reprendre la sync OneDrive

- Cliquer sur l'icône OneDrive dans la barre des tâches.
- Cliquer sur l'engrenage → **Reprendre la synchronisation**.
- L'icône OneDrive redevient normale.

⚠️ **À ce stade**, OneDrive va voir l'ancien dossier `C:\Users\franc\OneDrive\Bureau\vectora-inbox - claude` toujours présent. Il ne faut pas qu'il commence à re-sync ce dossier vers le nouveau chemin (il ne le fera pas, car le nouveau chemin n'est PAS dans OneDrive — mais s'il y a moindre doute, garder OneDrive en pause encore un peu).

---

## Étape 7 — Reconnecter Cowork au nouveau dossier (3 min)

### 7.1 Ouvrir Cowork

- Lancer l'application Claude desktop.

### 7.2 Sélectionner le nouveau dossier de travail

- Dans Cowork, ouvrir le sélecteur de dossier (icône folder ou paramètres workspace).
- Choisir `C:\Users\franc\dev\vectora-inbox-claude`.
- Cowork remonte le nouveau dossier dans sa sandbox.

### 7.3 Test de lecture

Demander à Claude (dans une nouvelle conversation Cowork ou la conversation en cours) :
> Lis `STATUS.md` à la racine et dis-moi la dernière date de mise à jour.

Claude doit pouvoir lire le fichier et retourner une réponse cohérente. Si erreur "fichier introuvable" : le mount Cowork pointe encore vers l'ancien chemin. Refaire l'étape 7.2.

---

## Étape 8 — Renommer (pas supprimer) l'ancien chemin (2 min)

⚠️ **Ne pas supprimer définitivement** l'ancien dossier tout de suite. On le renomme pour le rendre invisible et inutilisable, mais récupérable si besoin pendant 24h.

```powershell
# Aller au parent
cd "C:\Users\franc\OneDrive\Bureau"

# Renommer
Rename-Item -Path "vectora-inbox - claude" -NewName "_TO_DELETE_after_validation_vectora-inbox-claude_20260425"

# Vérifier
ls "C:\Users\franc\OneDrive\Bureau\" | Where-Object { $_.Name -like "*vectora*" -or $_.Name -like "_TO_DELETE*" }
```

**Sortie attendue** : seul le dossier `_TO_DELETE_after_validation_...` apparaît, pas l'ancien nom.

OneDrive va sync ce renommage (il sera visible online avec le nouveau nom). C'est OK.

---

## Étape 9 — Créer le raccourci sur le bureau (3 min)

### 9.1 Méthode rapide (clic droit)

- Aller dans le dossier `C:\Users\franc\dev\` via l'Explorateur Windows.
- Clic droit sur `vectora-inbox-claude` → Envoyer vers → Bureau (créer un raccourci).
- Le raccourci `vectora-inbox-claude - Raccourci.lnk` apparaît sur le bureau.
- Renommer en `vectora-inbox-claude.lnk` (ou le nom que tu préfères).

### 9.2 Méthode PowerShell (alternative)

```powershell
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\OneDrive\Bureau\vectora-inbox-claude.lnk")
$Shortcut.TargetPath = "C:\Users\franc\dev\vectora-inbox-claude"
$Shortcut.Save()
```

### 9.3 Tester le raccourci

- Double-cliquer sur le raccourci.
- L'Explorateur Windows ouvre `C:\Users\franc\dev\vectora-inbox-claude`. ✓

⚠️ Note : ce raccourci est lui-même synchronisé par OneDrive (puisqu'il est sur le bureau). Pas grave — un fichier `.lnk` fait quelques Ko, sans impact. La cible (le repo) reste bien hors OneDrive.

---

## Étape 10 — Validation finale (5 min)

Cocher mentalement chaque case :

- [ ] `dir C:\Users\franc\dev\vectora-inbox-claude` montre le repo entier
- [ ] `git status` dans ce dossier ne donne aucune erreur
- [ ] Le commit de test à l'étape 4.4 est visible sur GitHub
- [ ] VS Code ouvre le nouveau dossier sans erreur
- [ ] Cowork lit le `STATUS.md` du nouveau dossier
- [ ] Le raccourci sur le bureau fonctionne
- [ ] L'ancien dossier est renommé en `_TO_DELETE_after_validation_...` (pas supprimé)

Si **toutes** les cases sont cochées : le déménagement est réussi. Continue le Sprint 003 (correction du bug regex + update STATUS.md, fait par Claude depuis Cowork sur le nouveau chemin).

---

## Étape 11 — Suppression définitive de l'ancien chemin (à faire APRÈS 24h sans incident)

⚠️ **Ne PAS faire cette étape immédiatement**. Attendre **au moins 24h** d'utilisation du nouveau chemin sans incident.

Quand tu es serein :

```powershell
# Vérification que tu es bien sur le NOUVEAU chemin (pas en train de supprimer accidentellement le bon)
cd "C:\Users\franc\dev\vectora-inbox-claude"
pwd  # doit afficher C:\Users\franc\dev\vectora-inbox-claude

# Suppression définitive de l'ancien
Remove-Item -Path "C:\Users\franc\OneDrive\Bureau\_TO_DELETE_after_validation_vectora-inbox-claude_20260425" -Recurse -Force
```

OneDrive va sync la suppression (le dossier disparaît aussi de OneDrive online). C'est ce qu'on veut.

---

## En cas de problème — plan de récupération

### Cas A — La copie a foiré, le nouveau chemin est cassé

- L'ancien chemin existe toujours (pas encore renommé/supprimé), tu n'as rien perdu.
- Supprimer le nouveau chemin foireux : `Remove-Item -Path "C:\Users\franc\dev\vectora-inbox-claude" -Recurse -Force`
- Reprendre à l'étape 3.

### Cas B — Le nouveau chemin marche mais tu as déjà supprimé l'ancien et tu trouves un truc qui manque

- Re-cloner le repo depuis GitHub : `git clone https://github.com/<ton-user>/<ton-repo>.git C:\Users\franc\dev\vectora-inbox-claude-fresh`
- Comparer avec le chemin cassé pour identifier ce qui manque.
- Si c'était un fichier gitignored (`.env` notamment) — il n'est pas sur GitHub, et il est perdu. Le recréer à partir de `.env.example`.

### Cas C — Conflit OneDrive (fichier marqué `<filename> (Frank's PC)`)

- OneDrive a créé une copie de conflit. Identifier laquelle est la bonne (par date de modification généralement).
- Garder la bonne, supprimer la copie de conflit.
- Vérifier `git status` après nettoyage.

### Cas D — `.env` n'a pas été copié (parce que gitignored ET OneDrive en mode placeholder)

- Sortie attendue de `Test-Path "C:\Users\franc\dev\vectora-inbox-claude\.env"` : `False`.
- Le `.env` existe encore à l'ancien chemin si pas encore supprimé.
- Le copier manuellement : `Copy-Item -Path "C:\Users\franc\OneDrive\Bureau\_TO_DELETE_..._vectora-inbox-claude_20260425\.env" -Destination "C:\Users\franc\dev\vectora-inbox-claude\.env"`

---

## Après le runbook — la suite du Sprint 003

Une fois ce runbook terminé et validé :

1. Tu reviens dans Cowork (Claude) et tu dis : *"Le déménagement OneDrive est OK. On enchaîne sur le bug regex et le STATUS.md."*
2. Claude (depuis Cowork sur le nouveau chemin) :
   - Corrige `canonical/sources/source_catalog.yaml` (bug `r"..."`)
   - Crée `scripts/maintenance/validate_yaml_regexes.py`
   - Met à jour `STATUS.md`
   - Met à jour `docs/architecture/future_optimizations.md` (#10 marqué fait)
3. Tu fais les commits depuis VS Code (commandes données par Claude).
4. Sprint 003 fermé. On enchaîne sur Sprint 004 (ADRs + design doc).

---

*Runbook V1.0 — fin du document. À mettre à jour si la procédure évolue.*
