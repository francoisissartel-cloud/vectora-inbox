# Guide Rapide - Option B : Workaround Domain Scoring

**Durée estimée** : 5 minutes  
**Objectif** : Débloquer le matching en permettant l'inférence des pure_player companies

---

## ÉTAPE 1 : Modifier le Prompt (2 min)

**Fichier** : `canonical/prompts/domain_scoring/lai_domain_scoring.yaml`

**Changement** : Assouplir les CRITICAL RULES

```yaml
# TROUVER (ligne ~10)
  CRITICAL RULES FOR SIGNAL DETECTION:
  1. Only detect signals EXPLICITLY present in the normalized item
  2. DO NOT infer, assume, or hallucinate signals not provided
  3. If a technology/molecule/term is not in entities_detected, DO NOT add it
  4. Base your evaluation ONLY on the normalized data provided
  5. When in doubt, be conservative - reject rather than false positive

# REMPLACER PAR
  CRITICAL RULES FOR SIGNAL DETECTION:
  1. Detect signals from normalized_content.entities when available
  2. If entities.companies is empty, infer companies from title and content
  3. For pure_player companies, use this reference list:
     - Nanexa (Sweden) - PharmaShell technology
     - Camurus (Sweden) - FluidCrystal technology
     - MedinCell (France) - BEPO technology
     - Delsitech (Sweden) - Biodegradable microspheres
     - Peptron (South Korea) - Long-acting peptides
  4. For hybrid companies (Teva, Eli Lilly, Novo Nordisk), only boost if other LAI signals present
  5. Be conservative but not overly strict - balance precision and recall
  
  COMPANY DETECTION STRATEGY:
  - If "Nanexa" in title or content → pure_player_company: Nanexa
  - If "Camurus" in title or content → pure_player_company: Camurus
  - If "MedinCell" in title or content → pure_player_company: MedinCell
  - If "Delsitech" in title or content → pure_player_company: Delsitech
  - If "Peptron" in title or content → pure_player_company: Peptron
```

---

## ÉTAPE 2 : Incrémenter VERSION (30 sec)

**Fichier** : `VERSION`

```bash
# MODIFIER
CANONICAL_VERSION=2.2

# EN
CANONICAL_VERSION=2.3
```

---

## ÉTAPE 3 : Commit (30 sec)

```bash
git add canonical/prompts/domain_scoring/lai_domain_scoring.yaml VERSION
git commit -m "fix(canonical): workaround pure_player detection via text inference

Permet au domain_scoring d'inférer les pure_player companies depuis le texte
quand entities.companies est vide.

Résout régression v14: 0 pure_player détectés → perte 25 points/item

WORKAROUND temporaire en attendant fix normalizer.py

CANONICAL_VERSION: 2.2 → 2.3"
```

---

## ÉTAPE 4 : Déployer Canonical (1 min)

```bash
# Upload vers S3 dev
aws s3 cp canonical/prompts/domain_scoring/lai_domain_scoring.yaml \
  s3://vectora-inbox-config-dev/canonical/prompts/domain_scoring/lai_domain_scoring.yaml \
  --profile rag-lai-prod \
  --region eu-west-3

# Vérifier upload
aws s3 ls s3://vectora-inbox-config-dev/canonical/prompts/domain_scoring/ \
  --profile rag-lai-prod \
  --region eu-west-3
```

---

## ÉTAPE 5 : Tester (1 min)

```bash
# Créer lai_weekly_v15 avec canonical_version: "2.3"
# Modifier clients/lai_weekly_v15.yaml:
#   canonical_version: "2.3"

# Tester
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v15

# Vérifier résultats
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v15/2026/02/03/items.json ./temp_items_v15.json \
  --profile rag-lai-prod \
  --region eu-west-3

# Analyser
python -c "import json; items = json.load(open('temp_items_v15.json', encoding='utf-8')); item = items[0]; print(f'Score: {item[\"domain_scoring\"][\"score\"]}'); print(f'Signals: {item[\"domain_scoring\"][\"signals_detected\"]}')"
```

---

## VALIDATION

**Critères de succès** :

- [ ] `pure_player_company: Nanexa` détecté dans Item 1
- [ ] `pure_player_company: Camurus` détecté dans Item 3
- [ ] `pure_player_company: MedinCell` détecté dans Item 2
- [ ] Score moyen ≥ 38.0 (vs 33.1 en v14)
- [ ] Items relevant ≥ 14/29 (vs 12/29 en v14)

---

## ROLLBACK (si problème)

```bash
# Restaurer canonical v2.2
git checkout HEAD~1 canonical/prompts/domain_scoring/lai_domain_scoring.yaml VERSION

# Re-déployer
aws s3 cp canonical/prompts/domain_scoring/lai_domain_scoring.yaml \
  s3://vectora-inbox-config-dev/canonical/prompts/domain_scoring/lai_domain_scoring.yaml \
  --profile rag-lai-prod \
  --region eu-west-3
```

---

## PROCHAINE ÉTAPE

Une fois le workaround validé, passer à **Option A** (corriger normalizer.py) pour solution propre.

---

**Durée totale** : 5 minutes  
**Risque** : Faible (workaround conservateur)  
**Réversible** : Oui (rollback en 1 min)
