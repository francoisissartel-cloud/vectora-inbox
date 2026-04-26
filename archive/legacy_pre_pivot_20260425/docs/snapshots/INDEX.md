# Snapshots Index

Liste des snapshots disponibles pour rollback.

## 📸 Qu'est-ce qu'un Snapshot ?

Un snapshot est une sauvegarde complète de l'état d'un environnement à un instant T, incluant:
- Configuration des Lambdas (layers, env vars, timeout, memory)
- Fichiers de configuration S3 (canonical, clients)
- Métadonnées des données S3

## 🎯 Utilisation

### Créer un Snapshot

```bash
# Snapshot automatique (nom généré)
python scripts/maintenance/create_snapshot.py --env dev

# Snapshot avec nom personnalisé
python scripts/maintenance/create_snapshot.py --env stage --name "pre_deploy_v124"
```

### Restaurer depuis Snapshot

Les snapshots sont utilisés automatiquement par:
- `scripts/deploy/promote.py` (snapshot avant promotion)
- `scripts/deploy/rollback.py` (snapshot avant rollback)

En cas d'échec, le système restaure automatiquement le snapshot.

## 📋 Snapshots Disponibles

| Date | Nom | Environnement | Fichier |
|------|-----|---------------|----------|
| (Aucun snapshot créé pour le moment) | | | |

---

**Note**: Les snapshots sont créés automatiquement lors des promotions et rollbacks.
