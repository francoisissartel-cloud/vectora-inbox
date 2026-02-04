# Nettoyage Prompts Obsolètes - 2026-02-02

## Contexte

Architecture v2.0 : 2 appels Bedrock
1. Normalisation générique (`generic_normalization.yaml`)
2. Domain scoring LAI (`lai_domain_scoring.yaml`)

## Problème identifié

`lai_weekly_v10.yaml` référence `matching_prompt: "lai_matching"` qui est obsolète.

## Actions à réaliser

### 1. Correction client config

**Fichier** : `client-config-examples/production/lai_weekly_v10.yaml`

**Avant** :
```yaml
bedrock_config:
  normalization_prompt: "generic_normalization"
  matching_prompt: "lai_matching"  # ❌ OBSOLÈTE
  editorial_prompt: "lai_editorial"
  enable_domain_scoring: true
```

**Après** :
```yaml
bedrock_config:
  normalization_prompt: "generic_normalization"
  domain_scoring_prompt: "lai_domain_scoring"  # ✅ CORRECT
  editorial_prompt: "lai_editorial"
  enable_domain_scoring: true
```

### 2. Suppression prompts obsolètes

**Prompts canonical obsolètes** :
- [ ] `canonical/prompts/normalization/lai_normalization.yaml` - Remplacé par generic_normalization
- [ ] `canonical/prompts/matching/lai_matching.yaml` - Remplacé par lai_domain_scoring
- [ ] `canonical/prompts/global_prompts.yaml` - Ancien système centralisé

**Fichiers temporaires** :
- [ ] `.tmp/global_prompts.yaml`
- [ ] `.tmp/lai_prompt_s3.yaml`
- [ ] `.tmp/lai_prompt_stage.yaml`
- [ ] `.tmp/canonical/generic_normalization.yaml`
- [ ] `.tmp/canonical/lai_domain_definition.yaml`
- [ ] `.tmp/canonical/lai_domain_scoring.yaml`

### 3. Prompts à CONSERVER

**✅ Prompts actifs** :
- `canonical/prompts/normalization/generic_normalization.yaml` - Appel 1 Bedrock
- `canonical/prompts/domain_scoring/lai_domain_scoring.yaml` - Appel 2 Bedrock
- `canonical/prompts/editorial/lai_editorial.yaml` - Newsletter

### 4. Vérification code

**Fichiers à vérifier** :
- `src_v2/vectora_core/shared/config_loader.py` - load_canonical_prompts()
- `src_v2/vectora_core/normalization/bedrock_domain_scorer.py`

**Validation** : Le code charge déjà correctement les prompts v2.0 ✅

## Ordre d'exécution

1. ✅ Corriger `lai_weekly_v10.yaml`
2. ✅ Supprimer prompts obsolètes canonical
3. ✅ Nettoyer fichiers .tmp
4. ✅ Tester E2E avec lai_weekly_v10

## Validation

```bash
# Test local
python tests/local/test_e2e_domain_scoring_local.py

# Test AWS
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v10
```

## Statut

- [ ] Corrections appliquées
- [ ] Tests validés
- [ ] Déployé sur dev
- [ ] Déployé sur stage
