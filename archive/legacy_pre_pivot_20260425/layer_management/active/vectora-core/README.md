# Layer vectora-core

**Nom AWS** : `vectora-inbox-vectora-core-dev`  
**Version actuelle** : 1.2.3  
**Statut** : ✅ Actif

---

## 📋 DESCRIPTION

Layer contenant le code métier `vectora_core` utilisé par les 3 Lambdas V2 :
- `ingest/` : Ingestion et parsing de sources
- `normalization/` : Normalisation Bedrock, matching, scoring
- `newsletter/` : Assemblage et génération éditoriale
- `shared/` : Modules partagés (config_loader, s3_io, models, utils)

---

## 📦 CONTENU

```
python/
└── vectora_core/
    ├── ingest/
    │   ├── __init__.py
    │   ├── content_parser.py
    │   ├── ingestion_profiles.py
    │   └── source_fetcher.py
    ├── normalization/
    │   ├── __init__.py
    │   ├── bedrock_client.py
    │   ├── bedrock_matcher.py
    │   ├── matcher.py
    │   ├── normalizer.py
    │   └── scorer.py
    ├── newsletter/
    │   ├── __init__.py
    │   ├── assembler.py
    │   ├── bedrock_editor.py
    │   └── selector.py
    ├── shared/
    │   ├── __init__.py
    │   ├── config_loader.py
    │   ├── models.py
    │   ├── prompt_resolver.py
    │   ├── s3_io.py
    │   └── utils.py
    └── __init__.py
```

---

## 🔄 BUILD

```bash
# Build layer
python scripts/layers/build_vectora_core.py

# Ou build tous les layers
python scripts/layers/build_all.py
```

---

## 🚀 DEPLOY

```bash
# Deploy vers dev
python scripts/layers/deploy_layer.py --layer vectora-core --env dev

# Deploy vers stage
python scripts/layers/deploy_layer.py --layer vectora-core --env stage
```

---

## 📊 MÉTADONNÉES

Voir `manifest.json` pour :
- Version actuelle
- Git SHA du build
- ARN AWS (dev/stage)
- Taille du layer
- Date de build

---

## 📚 DOCUMENTATION

- **Source code** : `src_v2/vectora_core/`
- **Règles** : `.q-context/vectora-inbox-layer-management-rules.md`
- **Blueprint** : `docs/architecture/blueprint-v2-ACTUAL-2026.yaml`
