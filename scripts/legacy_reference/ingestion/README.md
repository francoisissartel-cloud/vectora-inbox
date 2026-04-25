# Scripts d'Ingestion V3 - Organisation

## 🎯 Scripts Principaux

### `run_ingestion.py` - Script Universel
**LE script principal pour toutes les ingestions V3**

```bash
# Depuis la racine du repo (wrapper)
python ingest.py lai_weekly_v3.1 --sources press_corporate__medincell --period-days 200

# Ou directement
python scripts/ingestion/run_ingestion.py lai_weekly_v3.1 --sources press_corporate__medincell --period-days 200
```

### `test_mvp_sources.py` - Test Batch MVP
**Test automatique de toutes les sources MVP**

```bash
python scripts/ingestion/test_mvp_sources.py
```

## 📁 Organisation du Repo

```
vectora-inbox/
├── ingest.py                           # Wrapper simple à la racine
├── scripts/
│   ├── ingestion/                      # Scripts d'ingestion V3
│   │   ├── run_ingestion.py           # Script universel principal
│   │   ├── test_mvp_sources.py        # Test batch MVP
│   │   └── README.md                  # Cette documentation
│   ├── analysis/                       # Scripts d'analyse actifs
│   ├── deploy/                         # Scripts de déploiement
│   ├── invoke/                         # Scripts d'invocation Lambda
│   ├── maintenance/                    # Scripts de maintenance
│   └── archive/                        # Anciens scripts (41 fichiers)
└── output/runs/                        # Résultats d'ingestion
```

## 🚀 Usage Recommandé

### Commandes Courantes

```bash
# Test source unique
python ingest.py lai_weekly_v3.1 --sources press_corporate__medincell --period-days 200

# Test toutes sources MVP
python scripts/ingestion/test_mvp_sources.py

# Ingestion production standard
python ingest.py lai_weekly_v3.1

# Debug avec mode broad
python ingest.py lai_weekly_v3.1 --mode broad --period-days 7
```

### Paramètres Disponibles

| Paramètre | Description | Exemple |
|-----------|-------------|---------|
| `client_config` | Config client | `lai_weekly_v3.1` |
| `--sources` | Sources spécifiques | `press_corporate__medincell` |
| `--period-days` | Période en jours | `200` |
| `--mode` | Mode ingestion | `balanced`, `strict`, `broad` |
| `--bouquets` | Bouquets sources | `lai_corporate_mvp` |

## 📊 Résultats

Tous les résultats dans `output/runs/{run_id}/` :
- `ingested_items.json` - Items finaux
- `rejected_items.json` - Items filtrés
- `run_manifest.json` - Métadonnées complètes

## 🧹 Nettoyage Effectué

- **41 anciens scripts de test** → `scripts/archive/`
- **14 anciens scripts d'analyse** → `scripts/archive/`
- **Script universel** → `scripts/ingestion/run_ingestion.py`
- **Wrapper simple** → `ingest.py` (racine)

## 🔧 Architecture

- **Moteur V3** : Utilise `src_v3/vectora_core`
- **Configs** : `client-config-examples/production/` et `config/clients/`
- **Canonical** : `canonical/ingestion/`
- **Pas de dépendances externes** : Tout intégré