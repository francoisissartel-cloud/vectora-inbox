# Scripts Backup Local - Vectora Inbox

## 🎯 Vue d'ensemble

Scripts pour gérer les backups locaux de `src_v2/` et `canonical/` sans dépendance Git.

## 📁 Structure Backup

```
.backup/
├── 20260204_143022_avant_optimisation/
│   ├── src_v2/              # Copie complète code
│   ├── canonical/           # Copie complète config
│   ├── VERSION              # Version actuelle
│   └── BACKUP_INFO.json     # Metadata
├── 20260204_151530_avant_test/
└── before_restore_20260204_160000/  # Backup auto avant restore
```

## 🛠️ Scripts Disponibles

### 1. `create_local_backup.py`
Crée un backup horodaté complet.

```bash
# Backup avec description
python scripts/backup/create_local_backup.py --description "Avant optimisation prompts"

# Backup simple
python scripts/backup/create_local_backup.py
```

### 2. `list_backups.py`
Liste tous les backups disponibles.

```bash
python scripts/backup/list_backups.py
```

### 3. `compare_with_backup.py`
Compare l'état actuel avec un backup.

```bash
# Comparaison simple
python scripts/backup/compare_with_backup.py --backup-id 20260204_143022

# Comparaison détaillée
python scripts/backup/compare_with_backup.py --backup-id 20260204_143022 --detailed
```

### 4. `restore_backup.py`
Restaure depuis un backup (avec backup sécurité automatique).

```bash
# Restauration interactive
python scripts/backup/restore_backup.py --backup-id 20260204_143022

# Restauration automatique
python scripts/backup/restore_backup.py --backup-id 20260204_143022 --yes

# Lister backups disponibles
python scripts/backup/restore_backup.py --list
```

## 🔄 Workflow Recommandé

### 1. Avant Modification
```bash
# Créer backup
python scripts/backup/create_local_backup.py --description "Avant modification X"
```

### 2. Pendant Développement
```bash
# Comparer changements
python scripts/backup/compare_with_backup.py --backup-id 20260204_143022 --detailed
```

### 3. Si Problème
```bash
# Restaurer backup
python scripts/backup/restore_backup.py --backup-id 20260204_143022
```

## 🛡️ Sécurités

- **Backup automatique**: Avant chaque restauration
- **Confirmation**: Demande confirmation avant restauration
- **Metadata**: Chaque backup contient ses informations
- **Horodatage**: Noms uniques avec timestamp

## 📊 Avantages vs Git

| Aspect | Backup Local | Git |
|--------|--------------|-----|
| **Simplicité** | ✅ Très simple | ⚠️ Complexe |
| **Rapidité** | ✅ Instantané | ⚠️ Plus lent |
| **Comparaison** | ✅ Diff direct | ✅ Git diff |
| **Historique** | ⚠️ Limité | ✅ Complet |
| **Collaboration** | ❌ Local seul | ✅ Équipe |
| **Traçabilité** | ⚠️ Basique | ✅ Complète |

## 🎯 Cas d'Usage Idéaux

- **Développement solo rapide**
- **Tests d'optimisation**
- **Modifications expérimentales**
- **Rollback immédiat**

## ⚠️ Limitations

- Pas d'historique Git
- Pas de collaboration
- Stockage local uniquement
- Pas de merge automatique