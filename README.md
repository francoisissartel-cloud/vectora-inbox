# Vectora Inbox

Système intelligent de veille et génération de newsletters pour le secteur pharmaceutique.

## 🚀 Démarrage Rapide

**📚 Toute la documentation est centralisée dans [`.q-context/README.md`](.q-context/README.md)**

### Commandes Essentielles
```bash
# Build et deploy dev
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev

# Test
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7

# Promouvoir vers stage
python scripts/deploy/promote.py --to stage --version X.Y.Z
```

### Prérequis
- Python 3.11+
- AWS CLI configuré (profil `rag-lai-prod`)
- Accès compte AWS 786469175371

## 🏗️ Architecture

**Architecture 3 Lambdas V2 (Validée E2E)**

```
ingest-v2 → normalize-score-v2 → newsletter-v2
```

**Client de référence**: lai_weekly_v3  
**Statut**: ✅ Architecture V2 validée E2E

## 🌍 Environnements

| Environnement | Statut | Usage |
|---------------|--------|---------|
| **dev** | ✅ Opérationnel | Développement et tests |
| **stage** | ✅ Opérationnel | Pré-production et validation |
| **prod** | 🚧 À créer | Production clients |

## 📚 Documentation Complète

**Index centralisé**: [`.q-context/README.md`](.q-context/README.md)

**Documents clés**:
- [Gouvernance](.q-context/vectora-inbox-governance.md) - Workflow et règles
- [Architecture](.q-context/vectora-inbox-architecture-overview.md) - Vue technique complète
- [Workflows](.q-context/vectora-inbox-workflows.md) - Scénarios détaillés
- [Guide Q Developer](.q-context/vectora-inbox-q-prompting-guide.md) - Comment prompter Q

---

*Gouvernance opérationnelle - Prêt pour développement*
