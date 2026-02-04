# Résumé Nettoyage Prompts - 2026-02-02

## ✅ Actions réalisées

### 1. Correction client config
- **Fichier** : `client-config-examples/production/lai_weekly_v10.yaml`
- **Changement** : `matching_prompt: "lai_matching"` → `domain_scoring_prompt: "lai_domain_scoring"`
- **Statut** : ✅ Corrigé

### 2. Suppression prompts obsolètes

**Prompts canonical supprimés** :
- ✅ `canonical/prompts/normalization/lai_normalization.yaml`
- ✅ `canonical/prompts/matching/lai_matching.yaml`
- ✅ `canonical/prompts/global_prompts.yaml`

**Fichiers temporaires supprimés** :
- ✅ `.tmp/global_prompts.yaml`
- ✅ `.tmp/lai_prompt_s3.yaml`
- ✅ `.tmp/lai_prompt_stage.yaml`
- ✅ `.tmp/canonical/generic_normalization.yaml`
- ✅ `.tmp/canonical/lai_domain_definition.yaml`
- ✅ `.tmp/canonical/lai_domain_scoring.yaml`

### 3. Prompts actifs conservés

**✅ Structure finale** :
```
canonical/prompts/
├── normalization/
│   └── generic_normalization.yaml      # Appel 1 Bedrock
├── domain_scoring/
│   └── lai_domain_scoring.yaml         # Appel 2 Bedrock
└── editorial/
    └── lai_editorial.yaml              # Newsletter
```

## 📋 Architecture v2.0 validée

**2 appels Bedrock** :
1. **Normalisation générique** (`generic_normalization.yaml`)
   - Extraction entités (companies, molecules, technologies, trademarks, indications)
   - Classification événement
   - Génération résumé
   - Extraction date

2. **Domain scoring LAI** (`lai_domain_scoring.yaml`)
   - Détection signaux (strong/medium/weak)
   - Application matching rules
   - Calcul score 0-100
   - Génération reasoning

## 🎯 Prochaines étapes

1. **Build & Deploy**
   ```bash
   python scripts/build/build_all.py
   python scripts/deploy/deploy_env.py --env dev
   ```

2. **Test E2E**
   ```bash
   python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v10
   ```

3. **Promotion stage**
   ```bash
   python scripts/deploy/promote.py --to stage --version X.Y.Z
   ```

## 📊 Impact

- **Prompts obsolètes supprimés** : 6 fichiers
- **Structure simplifiée** : 3 prompts actifs
- **Configuration corrigée** : lai_weekly_v10.yaml
- **Architecture** : v2.0 validée et nettoyée
