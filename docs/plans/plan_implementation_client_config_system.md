# Plan d'Implémentation: Système Client Config Automatisé

**Date**: 2026-02-02  
**Objectif**: Implémentation propre, cohérente (repo + AWS + Q-Context)

---

## 🎯 Vue d'Ensemble

### Principe
- Garder incrémentation vX pour isolation S3
- Automatiser génération via système de contextes
- Cohérence totale: repo local + AWS S3 + Q-Context

### Composants à Modifier
1. **Repo local**: Structure dossiers + runners
2. **AWS S3**: Upload automatique configs
3. **Q-Context**: Documentation système

---

## 📁 PARTIE 1: Restructuration Repo Local

### 1.1 Structure Dossiers

**Créer**:
```
client-config-examples/
├── production/
│   └── lai_weekly_prod.yaml
├── test/
│   ├── local/
│   │   ├── test_context_001.yaml
│   │   └── test_context_002.yaml
│   └── aws/
│       ├── test_context_001.yaml  # lai_weekly_v1
│       └── test_context_002.yaml  # lai_weekly_v2
├── templates/
│   └── lai_weekly_template.yaml
└── archive/
    ├── lai_weekly_v3.yaml
    └── ...
```

**Commandes**:
```bash
mkdir -p client-config-examples/{production,test/local,test/aws,templates,archive}
mv client-config-examples/lai_weekly_v*.yaml client-config-examples/archive/
```

### 1.2 Template LAI Weekly

**Fichier**: `client-config-examples/templates/lai_weekly_template.yaml`

**Contenu minimal**:
```yaml
client_profile:
  name: "{{NAME}}"
  client_id: "{{CLIENT_ID}}"
  active: true
  language: "en"
  frequency: "weekly"

pipeline:
  newsletter_mode: "latest_run_only"
  default_period_days: 30

bedrock_config:
  normalization_prompt: "generic_normalization"
  matching_prompt: "lai_matching"
  editorial_prompt: "lai_editorial"
  enable_domain_scoring: true

watch_domains:
  - id: "tech_lai_ecosystem"
    type: "technology"
    priority: "high"
    technology_scope: "lai_keywords"
    company_scope: "lai_companies_global"
    molecule_scope: "lai_molecules_global"
    trademark_scope: "lai_trademarks_global"

source_config:
  source_bouquets_enabled:
    - "lai_corporate_mvp"
    - "lai_press_mvp"

matching_config:
  min_domain_score: 0.25
  enable_fallback_mode: true

newsletter_layout:
  sections:
    - id: "regulatory_updates"
      title: "Regulatory Updates"
      max_items: 6
    - id: "partnerships_deals"
      title: "Partnerships & Deals"
      max_items: 4
    - id: "clinical_updates"
      title: "Clinical Updates"
      max_items: 5
    - id: "others"
      title: "Other Signals"
      max_items: 8

metadata:
  test_context_id: "{{CONTEXT_ID}}"
  test_purpose: "{{PURPOSE}}"
  test_environment: "{{ENVIRONMENT}}"
  created_date: "{{DATE}}"
  promoted_from: "{{PROMOTED_FROM}}"
```

### 1.3 Fonction Génération Config

**Fichier**: `tests/utils/config_generator.py` (NOUVEAU)

```python
import yaml
from pathlib import Path
from datetime import datetime

def generate_test_config(
    template_path: str,
    client_id: str,
    context_id: str,
    purpose: str,
    environment: str,
    promoted_from: str = None
) -> dict:
    """Génère config test depuis template."""
    
    with open(template_path) as f:
        template = yaml.safe_load(f)
    
    # Remplacements
    replacements = {
        "{{CLIENT_ID}}": client_id,
        "{{NAME}}": f"LAI Weekly - {context_id} ({environment})",
        "{{CONTEXT_ID}}": context_id,
        "{{PURPOSE}}": purpose,
        "{{ENVIRONMENT}}": environment,
        "{{DATE}}": datetime.now().isoformat(),
        "{{PROMOTED_FROM}}": promoted_from or "null"
    }
    
    config_str = yaml.dump(template)
    for key, value in replacements.items():
        config_str = config_str.replace(key, str(value))
    
    return yaml.safe_load(config_str)

def save_config(config: dict, output_path: str):
    """Sauvegarde config."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
```

---

## 🔧 PARTIE 2: Modification Runners

### 2.1 Runner Local

**Fichier**: `tests/local/test_e2e_runner.py`

**Ajouter**:
```python
from tests.utils.config_generator import generate_test_config, save_config

def create_new_context(purpose, base_client="lai_weekly"):
    # ... code existant ...
    
    # NOUVEAU: Générer client_config
    template_path = PROJECT_ROOT / "client-config-examples" / "templates" / "lai_weekly_template.yaml"
    client_id = f"{base_client}_test_{next_num:03d}"
    
    config = generate_test_config(
        template_path=str(template_path),
        client_id=client_id,
        context_id=context_id,
        purpose=purpose,
        environment="local"
    )
    
    # Sauvegarder config
    config_file = PROJECT_ROOT / "client-config-examples" / "test" / "local" / f"{context_id}.yaml"
    save_config(config, str(config_file))
    
    # Lier au contexte
    context['client_id'] = client_id
    context['client_config_file'] = str(config_file)
    
    print(f"   Config: {config_file}")
```

### 2.2 Runner AWS

**Fichier**: `tests/aws/test_e2e_runner.py`

**Ajouter**:
```python
from tests.utils.config_generator import generate_test_config, save_config
import boto3

def create_aws_context(local_context_id, purpose):
    # ... code existant ...
    
    # Trouver prochain vX
    existing_v = []
    for c in registry['contexts']['aws']['history']:
        if 'client_id' in c and c['client_id'].startswith('lai_weekly_v'):
            v = int(c['client_id'].replace('lai_weekly_v', ''))
            existing_v.append(v)
    
    next_v = max(existing_v, default=0) + 1
    client_id = f"lai_weekly_v{next_v}"
    
    # Générer config
    template_path = PROJECT_ROOT / "client-config-examples" / "templates" / "lai_weekly_template.yaml"
    
    # Récupérer client_id local
    local_context_file = CONTEXTS_LOCAL_DIR / f"{local_context_id}.json"
    with open(local_context_file) as f:
        local_ctx = json.load(f)
    local_client_id = local_ctx.get('client_id', 'unknown')
    
    config = generate_test_config(
        template_path=str(template_path),
        client_id=client_id,
        context_id=context_id,
        purpose=purpose,
        environment="aws_dev",
        promoted_from=local_client_id
    )
    
    # Sauvegarder localement
    config_file = PROJECT_ROOT / "client-config-examples" / "test" / "aws" / f"{context_id}.yaml"
    save_config(config, str(config_file))
    
    # Upload vers S3
    upload_config_to_s3(config, client_id, env="dev")
    
    # Lier au contexte
    context['client_id'] = client_id
    context['client_config_file'] = str(config_file)
    context['s3_config_path'] = f"s3://vectora-inbox-config-dev/clients/{client_id}.yaml"
    
    print(f"   Config local: {config_file}")
    print(f"   Config S3: {context['s3_config_path']}")

def upload_config_to_s3(config: dict, client_id: str, env: str):
    """Upload config vers S3."""
    s3 = boto3.client('s3', region_name=AWS_REGION)
    bucket = f"vectora-inbox-config-{env}"
    key = f"clients/{client_id}.yaml"
    
    config_yaml = yaml.dump(config, default_flow_style=False, sort_keys=False)
    
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=config_yaml.encode('utf-8'),
        ContentType='application/x-yaml'
    )
    
    print(f"✅ Config uploaded to s3://{bucket}/{key}")
```

---

## ☁️ PARTIE 3: Cohérence AWS S3

### 3.1 Structure S3 Résultante

**Après implémentation**:
```
s3://vectora-inbox-config-dev/
└── clients/
    ├── lai_weekly_prod.yaml      # Production
    ├── lai_weekly_v1.yaml         # Test context 001
    ├── lai_weekly_v2.yaml         # Test context 002
    └── lai_weekly_v3.yaml         # Test context 003

s3://vectora-inbox-data-dev/
├── ingested/
│   ├── lai_weekly_v1/            # Isolé
│   ├── lai_weekly_v2/            # Isolé
│   └── lai_weekly_prod/
└── curated/
    ├── lai_weekly_v1/
    ├── lai_weekly_v2/
    └── lai_weekly_prod/
```

### 3.2 Nettoyage S3 (Optionnel)

**Script**: `scripts/maintenance/cleanup_test_s3.py`

```python
import boto3
from datetime import datetime, timedelta

def cleanup_old_test_data(days=7, env="dev"):
    """Supprime données test S3 > X jours."""
    s3 = boto3.client('s3')
    
    buckets = [
        f"vectora-inbox-config-{env}",
        f"vectora-inbox-data-{env}",
        f"vectora-inbox-newsletters-{env}"
    ]
    
    cutoff = datetime.now() - timedelta(days=days)
    
    for bucket in buckets:
        # Lister objets lai_weekly_v*
        response = s3.list_objects_v2(Bucket=bucket, Prefix="")
        
        for obj in response.get('Contents', []):
            if 'lai_weekly_v' in obj['Key']:
                if obj['LastModified'].replace(tzinfo=None) < cutoff:
                    print(f"Deleting: s3://{bucket}/{obj['Key']}")
                    s3.delete_object(Bucket=bucket, Key=obj['Key'])
```

---

## 📚 PARTIE 4: Mise à Jour Q-Context

### 4.1 Nouveau Document

**Fichier**: `.q-context/vectora-inbox-client-config-system.md`

```markdown
# Système Client Config - Tests E2E

**Principe**: 1 contexte test = 1 client_config dédié = 1 dossier S3 isolé

## Mapping Contexte → Client ID

| Contexte | Environnement | Client ID | Dossier S3 |
|----------|---------------|-----------|------------|
| test_context_001 | local | lai_weekly_test_001 | N/A |
| test_context_001 | aws | lai_weekly_v1 | s3://.../lai_weekly_v1/ |
| test_context_002 | local | lai_weekly_test_002 | N/A |
| test_context_002 | aws | lai_weekly_v2 | s3://.../lai_weekly_v2/ |

## Génération Automatique

**Local**:
```bash
python tests/local/test_e2e_runner.py --new-context "Test X"
# → Génère: lai_weekly_test_001
# → Config: client-config-examples/test/local/test_context_001.yaml
```

**AWS**:
```bash
python tests/aws/test_e2e_runner.py --promote "Validation"
# → Génère: lai_weekly_v1
# → Config local: client-config-examples/test/aws/test_context_001.yaml
# → Config S3: s3://vectora-inbox-config-dev/clients/lai_weekly_v1.yaml
```

## Isolation S3 Garantie

Chaque test AWS crée:
- Nouveau client_id (v1, v2, v3...)
- Nouveau dossier S3 (pas de données anciennes)
- Workflow E2E complet (ingestion → newsletter)

## Règles Q Developer

**Q DOIT**:
- Générer client_id automatiquement via runners
- Uploader config vers S3 avant test AWS
- Vérifier isolation S3 (nouveau dossier)

**Q NE DOIT JAMAIS**:
- Créer lai_weekly_vX manuellement
- Réutiliser client_id d'un test précédent
- Bypasser ingestion si données S3 existent
```

### 4.2 Mise à Jour Index

**Fichier**: `.q-context/README.md`

**Ajouter**:
```markdown
### 3. **Développement**
- [`vectora-inbox-test-e2e-system.md`] - Système tests E2E
- [`vectora-inbox-client-config-system.md`] - 🆕 Système client config automatisé
```

### 4.3 Mise à Jour Development Rules

**Fichier**: `.q-context/vectora-inbox-development-rules.md`

**Ajouter section**:
```markdown
## 📋 RÈGLES CLIENT CONFIG POUR TESTS E2E

**Q DOIT TOUJOURS**:
1. Générer client_config automatiquement via runners
2. Utiliser naming: lai_weekly_test_XXX (local), lai_weekly_vX (AWS)
3. Uploader config vers S3 avant test AWS
4. Vérifier isolation S3 (nouveau dossier)

**Workflow**:
```bash
# Local: génère lai_weekly_test_001
python tests/local/test_e2e_runner.py --new-context "Test X"

# AWS: génère lai_weekly_v1 + upload S3
python tests/aws/test_e2e_runner.py --promote "Validation"
```

**Isolation S3 garantie**: Chaque vX = nouveau dossier S3 = workflow E2E complet
```

---

## 📋 PARTIE 5: Checklist Implémentation

### Phase 1: Restructuration (30 min)
- [ ] Créer structure dossiers
- [ ] Créer template lai_weekly_template.yaml
- [ ] Archiver lai_weekly_v3-v9
- [ ] Créer config production

### Phase 2: Code (1h)
- [ ] Créer tests/utils/config_generator.py
- [ ] Modifier tests/local/test_e2e_runner.py
- [ ] Modifier tests/aws/test_e2e_runner.py
- [ ] Ajouter upload S3 dans runner AWS

### Phase 3: Q-Context (30 min)
- [ ] Créer vectora-inbox-client-config-system.md
- [ ] Mettre à jour README.md
- [ ] Mettre à jour development-rules.md

### Phase 4: Test (30 min)
- [ ] Créer premier contexte local
- [ ] Vérifier génération config
- [ ] Promouvoir vers AWS
- [ ] Vérifier upload S3
- [ ] Tester workflow E2E complet

### Phase 5: Documentation (15 min)
- [ ] Créer README dans client-config-examples/
- [ ] Documenter structure
- [ ] Exemples commandes

---

## 🎯 Résultat Final

### Cohérence Repo
```
client-config-examples/
├── production/          ✅ Configs prod
├── test/
│   ├── local/          ✅ Configs test local
│   └── aws/            ✅ Configs test AWS
├── templates/          ✅ Template réutilisable
└── archive/            ✅ Anciens configs
```

### Cohérence AWS
```
s3://vectora-inbox-config-dev/clients/
├── lai_weekly_prod.yaml    ✅ Production
├── lai_weekly_v1.yaml      ✅ Test context 001
└── lai_weekly_v2.yaml      ✅ Test context 002

s3://vectora-inbox-data-dev/
├── ingested/lai_weekly_v1/ ✅ Isolé
└── curated/lai_weekly_v1/  ✅ Isolé
```

### Cohérence Q-Context
- ✅ Système documenté
- ✅ Règles claires pour Q
- ✅ Exemples concrets

---

## ⏱️ Estimation Totale

**Temps**: 2h30  
**Complexité**: Moyenne  
**Impact**: Haute (cohérence système E2E)

---

**Plan d'implémentation**: ✅ COMPLET  
**Prêt pour exécution**: ✅ OUI  
**Validation requise**: Utilisateur confirme approche
