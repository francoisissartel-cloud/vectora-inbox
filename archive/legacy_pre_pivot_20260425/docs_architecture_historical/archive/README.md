# Blueprints Archivés

Fichiers obsolètes conservés pour référence historique uniquement.

---

## blueprint-v2-OBSOLETE-20251218.yaml

**Date**: 18 décembre 2025  
**Raison**: Architecture divergente avec infra déployée et moteur actuel

### Obsolescences Majeures

| Élément | Blueprint Obsolète | Réalité Actuelle |
|---------|-------------------|------------------|
| **Architecture** | 3 Lambdas V2 | 2 Lambdas (ingest-normalize + engine) |
| **Noms Lambdas** | ingest-v2, normalize-score-v2, newsletter-v2 | ingest-normalize, engine |
| **Modèle Bedrock** | Claude Sonnet 3 (us-east-1) | Claude Sonnet 4.5 EU inference profile |
| **Client référence** | lai_weekly_v3 | lai_weekly_v7 |
| **Système prompts** | Absent | Prompts canoniques avec références dynamiques |
| **Versioning** | Absent | Fichier VERSION avec 6 versions |
| **Runtime** | Python 3.11 | Python 3.12 |

### Remplacement

**Blueprint actuel**: `docs/architecture/blueprint-v2-ACTUAL-2026.yaml`

**Documentation de référence**:
- `.q-context/` - Gouvernance et workflows
- `infra/*.yaml` - CloudFormation (état déployé)
- `VERSION` - Versioning sémantique

---

**Date d'archivage**: 2026-01-31  
**Archivé par**: Mise à jour blueprint pour refléter état réel du moteur
