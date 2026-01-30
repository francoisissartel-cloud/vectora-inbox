# Annexe - Convention Nommage Fichiers Prompts (Recommandation Expert)

**Date**: 2026-01-29 20:30 UTC  
**Sujet**: Éviter confusion avec fichiers `lai_prompt.yaml` identiques

---

## 🚨 PROBLÈME IDENTIFIÉ

### Structure Actuelle (Problématique)
```
canonical/prompts/
├── normalization/
│   └── lai_prompt.yaml          # ⚠️ Même nom
├── matching/
│   └── lai_prompt.yaml          # ⚠️ Même nom
└── editorial/
    └── lai_prompt.yaml          # ⚠️ Même nom
```

### Risques

1. **Confusion développeur** :
   - "Quel `lai_prompt.yaml` dois-je modifier ?"
   - Risque d'éditer le mauvais fichier

2. **Erreurs de déploiement** :
   - Upload du mauvais fichier sur S3
   - Écrasement accidentel

3. **Logs peu clairs** :
   - "Erreur chargement lai_prompt.yaml" → Lequel ?
   - Debugging difficile

4. **Versioning Git** :
   - Historique confus (3 fichiers même nom)
   - Pull requests ambiguës

5. **Documentation** :
   - "Modifier lai_prompt.yaml" → Pas assez précis
   - Onboarding nouveaux développeurs compliqué

---

## ✅ SOLUTION RECOMMANDÉE : Nommage Explicite par Phase

### Option 1 : Préfixe Phase (RECOMMANDÉ)

**Structure** :
```
canonical/prompts/
├── normalization/
│   └── lai_normalization.yaml       # ✅ Explicite
├── matching/
│   └── lai_matching.yaml            # ✅ Explicite
└── editorial/
    └── lai_editorial.yaml           # ✅ Explicite
```

**Avantages** :
- ✅ Nom de fichier unique et explicite
- ✅ Facile à identifier dans logs : "Chargement lai_editorial.yaml"
- ✅ Pas de confusion possible
- ✅ Grep/recherche efficace : `grep -r "lai_editorial"`
- ✅ Git history clair

**Configuration client** :
```yaml
bedrock_config:
  normalization_prompt: "lai_normalization"    # Nom fichier explicite
  matching_prompt: "lai_matching"              # Nom fichier explicite
  editorial_prompt: "lai_editorial"            # Nom fichier explicite
```

**Code (prompt_resolver.py)** :
```python
# Ligne 31 - Construction chemin
prompt_key = f"canonical/prompts/{prompt_type}/{vertical}_prompt.yaml"

# DEVIENT
prompt_key = f"canonical/prompts/{prompt_type}/{vertical}.yaml"
```

**Exemple appel** :
```python
# normalize-score-v2
prompt_resolver.load_prompt_template('normalization', 'lai_normalization', s3_io, config_bucket)
# → canonical/prompts/normalization/lai_normalization.yaml

# bedrock_matcher
prompt_resolver.load_prompt_template('matching', 'lai_matching', s3_io, config_bucket)
# → canonical/prompts/matching/lai_matching.yaml

# newsletter-v2
prompt_resolver.load_prompt_template('editorial', 'lai_editorial', s3_io, config_bucket)
# → canonical/prompts/editorial/lai_editorial.yaml
```

---

### Option 2 : Suffixe Phase (Alternative)

**Structure** :
```
canonical/prompts/
├── normalization/
│   └── lai_norm.yaml
├── matching/
│   └── lai_match.yaml
└── editorial/
    └── lai_edit.yaml
```

**Avantages** :
- ✅ Noms courts
- ✅ Toujours explicites

**Inconvénients** :
- ⚠️ Abréviations moins claires (`norm`, `match`, `edit`)
- ⚠️ Moins professionnel

---

### Option 3 : Garder `_prompt.yaml` mais avec préfixe (Compromis)

**Structure** :
```
canonical/prompts/
├── normalization/
│   └── lai_normalization_prompt.yaml
├── matching/
│   └── lai_matching_prompt.yaml
└── editorial/
    └── lai_editorial_prompt.yaml
```

**Avantages** :
- ✅ Explicite avec suffixe `_prompt`
- ✅ Cohérent avec convention actuelle

**Inconvénients** :
- ⚠️ Noms plus longs
- ⚠️ Redondant (dossier `prompts/` déjà explicite)

---

## 🎯 RECOMMANDATION FINALE : Option 1

### Nommage Recommandé

```
canonical/prompts/
├── normalization/
│   ├── lai_normalization.yaml           # LAI
│   ├── gene_therapy_normalization.yaml  # Gene Therapy
│   └── oncology_normalization.yaml      # Oncology
├── matching/
│   ├── lai_matching.yaml
│   ├── gene_therapy_matching.yaml
│   └── oncology_matching.yaml
└── editorial/
    ├── lai_editorial.yaml
    ├── gene_therapy_editorial.yaml
    └── oncology_editorial.yaml
```

### Pattern de Nommage

**Format** : `{vertical}_{phase}.yaml`

**Exemples** :
- `lai_normalization.yaml` : Prompt LAI pour normalisation
- `lai_matching.yaml` : Prompt LAI pour matching
- `lai_editorial.yaml` : Prompt LAI pour éditorial
- `gene_therapy_normalization.yaml` : Prompt Gene Therapy pour normalisation

### Configuration Client

```yaml
# lai_weekly_v7.yaml
bedrock_config:
  normalization_prompt: "lai_normalization"
  matching_prompt: "lai_matching"
  editorial_prompt: "lai_editorial"

# gene_therapy_weekly.yaml
bedrock_config:
  normalization_prompt: "gene_therapy_normalization"
  matching_prompt: "gene_therapy_matching"
  editorial_prompt: "gene_therapy_editorial"
```

### Modification Code

**prompt_resolver.py** :
```python
def load_prompt_template(prompt_type: str, vertical: str, s3_io, config_bucket: str):
    """
    Charge un prompt template depuis canonical/prompts/.
    
    Args:
        prompt_type: Type de prompt (normalization, matching, editorial)
        vertical: Nom du prompt (ex: "lai_normalization", "gene_therapy_editorial")
        s3_io: Module s3_io pour accès S3
        config_bucket: Bucket S3 de configuration
    
    Returns:
        Dict contenant le prompt template ou None si non trouvé
    """
    try:
        # Chemin du prompt spécifique
        prompt_key = f"canonical/prompts/{prompt_type}/{vertical}.yaml"
        prompt_data = s3_io.read_yaml_from_s3(config_bucket, prompt_key)
        
        if prompt_data:
            logger.info(f"Prompt template chargé: {prompt_key}")
            return prompt_data
        
        logger.warning(f"Prompt {prompt_key} non trouvé")
        return None
        
    except Exception as e:
        logger.error(f"Erreur chargement prompt template: {e}")
        return None
```

**Appels** :
```python
# normalize-score-v2
normalization_prompt = client_config['bedrock_config']['normalization_prompt']
# normalization_prompt = "lai_normalization"

prompt_template = prompt_resolver.load_prompt_template(
    'normalization', 
    normalization_prompt,  # "lai_normalization"
    s3_io,
    config_bucket
)
# → Charge canonical/prompts/normalization/lai_normalization.yaml
```

---

## 📋 PLAN DE MIGRATION

### Étape 1 : Renommer Fichiers Existants

**Commandes** :
```bash
# Normalization
mv canonical/prompts/normalization/lai_prompt.yaml \
   canonical/prompts/normalization/lai_normalization.yaml

# Matching
mv canonical/prompts/matching/lai_prompt.yaml \
   canonical/prompts/matching/lai_matching.yaml

# Editorial (nouveau)
# Créer directement avec le bon nom
# canonical/prompts/editorial/lai_editorial.yaml
```

### Étape 2 : Modifier Configurations Clients

**Fichiers à modifier** :
- `client-config-examples/lai_weekly_v3.yaml`
- `client-config-examples/lai_weekly_v6.yaml`
- `client-config-examples/lai_weekly_v7.yaml`

**Changement** :
```yaml
# AVANT
bedrock_config:
  normalization_prompt: "lai"
  matching_prompt: "lai"

# APRÈS
bedrock_config:
  normalization_prompt: "lai_normalization"
  matching_prompt: "lai_matching"
  editorial_prompt: "lai_editorial"
```

### Étape 3 : Modifier prompt_resolver.py

**Changement ligne 31** :
```python
# AVANT
prompt_key = f"canonical/prompts/{prompt_type}/{vertical}_prompt.yaml"

# APRÈS
prompt_key = f"canonical/prompts/{prompt_type}/{vertical}.yaml"
```

### Étape 4 : Upload S3

**Commandes** :
```bash
# Upload prompts renommés
aws s3 cp canonical/prompts/normalization/lai_normalization.yaml \
  s3://vectora-inbox-config-dev/canonical/prompts/normalization/lai_normalization.yaml \
  --region eu-west-3 --profile rag-lai-prod

aws s3 cp canonical/prompts/matching/lai_matching.yaml \
  s3://vectora-inbox-config-dev/canonical/prompts/matching/lai_matching.yaml \
  --region eu-west-3 --profile rag-lai-prod

aws s3 cp canonical/prompts/editorial/lai_editorial.yaml \
  s3://vectora-inbox-config-dev/canonical/prompts/editorial/lai_editorial.yaml \
  --region eu-west-3 --profile rag-lai-prod

# Upload configs clients
aws s3 cp client-config-examples/lai_weekly_v7.yaml \
  s3://vectora-inbox-config-dev/clients/lai_weekly_v7.yaml \
  --region eu-west-3 --profile rag-lai-prod
```

### Étape 5 : Déployer Layer v11

**Inclure** :
- `prompt_resolver.py` modifié (ligne 31)
- Tous les autres fichiers vectora_core

### Étape 6 : Tests E2E

**Vérifier** :
- [ ] Prompt normalization chargé : `lai_normalization.yaml`
- [ ] Prompt matching chargé : `lai_matching.yaml`
- [ ] Prompt editorial chargé : `lai_editorial.yaml`
- [ ] Logs clairs : "Chargement lai_normalization.yaml"
- [ ] Pas de régression fonctionnelle

---

## 📊 COMPARAISON OPTIONS

| Critère | Option 1 (Préfixe) | Option 2 (Suffixe) | Option 3 (Compromis) | Actuel |
|---------|---------------------|--------------------|-----------------------|--------|
| Clarté | ✅ Excellent | ⚠️ Moyen | ✅ Bon | ❌ Mauvais |
| Unicité | ✅ Unique | ✅ Unique | ✅ Unique | ❌ Dupliqué |
| Longueur | ✅ Raisonnable | ✅ Court | ⚠️ Long | ✅ Court |
| Professionnalisme | ✅ Élevé | ⚠️ Moyen | ✅ Élevé | ⚠️ Moyen |
| Extensibilité | ✅ Excellent | ✅ Bon | ✅ Excellent | ✅ Bon |
| Logs clairs | ✅ Très clair | ✅ Clair | ✅ Très clair | ❌ Ambigu |
| Maintenance | ✅ Facile | ✅ Facile | ✅ Facile | ❌ Difficile |

**Recommandation** : **Option 1** (Préfixe phase)

---

## 🎯 RÉSUMÉ

### Problème
3 fichiers `lai_prompt.yaml` identiques → Confusion, erreurs, logs ambigus

### Solution
Nommage explicite : `{vertical}_{phase}.yaml`

### Exemples
- `lai_normalization.yaml` ✅
- `lai_matching.yaml` ✅
- `lai_editorial.yaml` ✅

### Bénéfices
1. ✅ Noms uniques et explicites
2. ✅ Logs clairs et traçables
3. ✅ Maintenance facilitée
4. ✅ Pas de confusion possible
5. ✅ Extensible à d'autres verticaux

### Impact
- Modification `prompt_resolver.py` (1 ligne)
- Renommage 2 fichiers existants
- Création 1 nouveau fichier avec bon nom
- Mise à jour configs clients
- Tests E2E pour validation

**Temps estimé** : +30 minutes au plan initial (total 3h30)

---

**Recommandation finale** : Implémenter Option 1 dans le plan correctif pour éviter toute confusion future.
