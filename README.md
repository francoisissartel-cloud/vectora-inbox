# Vectora Inbox

Système intelligent de veille et génération de newsletters pour le secteur pharmaceutique.

## 🏗️ Architecture

**Architecture 3 Lambdas V2 (Validée E2E)**

```
ingest-v2 → normalize-score-v2 → newsletter-v2
```

## 📁 Structure du Repository

### Dossiers Principaux
- `src_v2/` : Code source V2 (RÉFÉRENCE)
- `canonical/` : Configurations métier (scopes, prompts, sources)
- `client-config-examples/` : Templates configurations clients
- `infra/` : Infrastructure as Code (CloudFormation)
- `scripts/` : Scripts utilitaires et déploiement
- `tests/` : Tests unitaires et intégration
- `docs/` : Documentation technique
- `contracts/` : Contrats API des Lambdas

### Dossiers Temporaires (Non Versionnés)
- `.tmp/` : Fichiers éphémères (events, responses, logs)
- `.build/` : Artefacts de build (layers, packages)
- `archive/` : Code legacy (référence historique)

## 🚀 Démarrage Rapide

### Prérequis
- Python 3.11+
- AWS CLI configuré (profil `rag-lai-prod`)
- Accès compte AWS 786469175371

### Installation
```bash
# Installer dépendances
pip install -r src_v2/requirements.txt

# Valider hygiène repository
python scripts/maintenance/validate_repo_hygiene.py
```

### Workflow Standard (Gouvernance en Place)

**Principe**: Repo local = Source unique de vérité

```bash
# 1. Build artefacts
python scripts/build/build_all.py

# 2. Deploy vers dev
python scripts/deploy/deploy_env.py --env dev

# 3. Tester
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7

# 4. Promouvoir vers stage
python scripts/deploy/promote.py --to stage --version X.Y.Z
```

**Guides**:
- 💬 Comment prompter Q: `COMMENT_PROMPTER_Q.md`
- 🛡️ Règles gouvernance: `GOUVERNANCE.md`
- 📚 Workflow détaillé: `docs/workflows/developpement_standard.md`

### Tests Locaux
```bash
# Test ingest-v2
python scripts/invoke/invoke_ingest_v2.py --client-id lai_weekly_v3

# Test normalize-score-v2
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v3
```

## 📋 Règles d'Hygiène

### Racine Propre
- ✅ Aucun fichier temporaire à la racine
- ✅ Outputs scripts dans `.tmp/`
- ✅ Builds dans `.build/`
- ✅ Commits vérifiés avec `.gitignore`

### Nettoyage
```bash
# Supprimer fichiers temporaires > 7 jours
python scripts/maintenance/cleanup_tmp.py

# Supprimer tous les artefacts de build
./scripts/maintenance/cleanup_build.sh

# Valider avant commit
python scripts/maintenance/validate_repo_hygiene.py
```

## 📚 Documentation

- **Règles de développement** : `.q-context/vectora-inbox-development-rules.md`
- **Architecture V2** : `docs/design/vectora_inbox_v2_engine_overview.md`
- **Contrats Lambdas** : `contracts/lambdas/`

## 🔧 Configuration AWS

**Région principale** : eu-west-3 (Paris)  
**Région Bedrock** : us-east-1 (Virginie)  
**Profil CLI** : rag-lai-prod  
**Compte** : 786469175371

## ✅ Validation E2E

**Client de référence** : lai_weekly_v3  
**Dernière validation** : 18 décembre 2025  
**Statut** : ✅ Architecture V2 validée E2E

---

*Pour plus de détails, consulter `.q-context/vectora-inbox-development-rules.md`*
