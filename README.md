# Vectora Inbox

Système intelligent de veille et génération de newsletters pour le secteur pharmaceutique.

## 🎯 Contexte Business

**Vectora Inbox = Moteur de newsletters ultra-spécialisées sur des marchés de niche biotech/pharma**

- **Première newsletter**: Long-Acting Injectables (LAI) - 200+ entreprises, aucune newsletter dédiée existante
- **Avantage compétitif**: Expertise métier rare (11 ans pharma) + Capacité technique (Q Developer)
- **Modèle**: Newsletter générique LAI (B2C) + Newsletters sur-mesure (B2B)
- **Vision**: Extension à d'autres niches (siRNA, cell therapy, gene therapy)

📖 **Lire**: [Contexte Business Complet](docs/business/CONTEXTE_BUSINESS_VECTORA.md)

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
- [Blueprint](docs/architecture/blueprint-v2-ACTUAL-2026.yaml) - 📋 **Système complet + Guide d'ajustement**
- [Maintenance Blueprint](docs/architecture/BLUEPRINT_MAINTENANCE.md) - 🔧 **Comment maintenir le blueprint à jour**
- [Workflows](.q-context/vectora-inbox-workflows.md) - Scénarios détaillés
- [Guide Q Developer](.q-context/vectora-inbox-q-prompting-guide.md) - Comment prompter Q
- [Test E2E Gold Standard](.q-context/test-e2e-gold-standard.md) - 🏆 **Modèle de rapport E2E**
- [Guide Génération Rapports E2E](.q-context/guide-generation-rapports-e2e.md) - 📝 **Comment générer rapports E2E**

---

*Gouvernance opérationnelle - Prêt pour développement*
