# Analyse: Invocation Lambda pour Tests E2E

**Date**: 2026-02-02  
**Problème**: Invocation Lambda pas intégrée au système de contextes

---

## 🔍 Problème Actuel

### Runner AWS
```python
# tests/aws/test_e2e_runner.py
def run_aws_e2e_test(context):
    client_id = context['client_id']  # Ex: lai_weekly_v1
    
    # Appelle script externe
    result = subprocess.run(
        [sys.executable, "scripts/invoke/invoke_normalize_score_v2.py", "--event", client_id],
        ...
    )
```

### Script Invoke
```python
# scripts/invoke/invoke_normalize_score_v2.py
def get_test_event(event_name):
    events = {
        "lai_weekly_v3": {"client_id": "lai_weekly_v3"},
        "lai_weekly_v7": {"client_id": "lai_weekly_v7"},
        # ...hardcodé
    }
```

**Problèmes**:
1. ❌ Events hardcodés (v3, v7, v8, v9)
2. ❌ Pas de support dynamique pour `lai_weekly_v1`, `v2`, etc.
3. ❌ Runner AWS ne peut pas passer client_id dynamiquement
4. ❌ Pas d'invocation workflow complet (ingest → normalize → newsletter)

---

## ✅ Recommandations

### Option 1: Modifier Script Invoke (Simple)

**Ajouter support client_id dynamique**:

```python
# scripts/invoke/invoke_normalize_score_v2.py
parser.add_argument("--client-id", help="Client ID dynamique")

if args.client_id:
    event_data = {"client_id": args.client_id}
else:
    event_data = get_test_event(args.event)
```

**Avantages**:
- ✅ Minimal (5 lignes)
- ✅ Rétrocompatible
- ✅ Fonctionne immédiatement

**Inconvénients**:
- ⚠️ Pas de workflow complet (seulement normalize)

### Option 2: Créer Invoke E2E Complet (Recommandé)

**Nouveau script**: `scripts/invoke/invoke_e2e_workflow.py`

```python
def invoke_e2e_workflow(client_id, env="dev"):
    """Invoque workflow complet: ingest → normalize → newsletter."""
    
    # 1. Ingest
    invoke_lambda("vectora-inbox-ingest-v2-dev", {"client_id": client_id})
    
    # 2. Normalize
    invoke_lambda("vectora-inbox-normalize-score-v2-dev", {"client_id": client_id})
    
    # 3. Newsletter
    invoke_lambda("vectora-inbox-newsletter-v2-dev", {"client_id": client_id})
```

**Avantages**:
- ✅ Workflow E2E complet
- ✅ Un seul appel depuis runner
- ✅ Logs consolidés
- ✅ Gestion erreurs centralisée

**Inconvénients**:
- ⚠️ Plus de code (50 lignes)

### Option 3: Intégrer dans Runner AWS (Optimal)

**Modifier runner AWS pour invoquer directement**:

```python
# tests/aws/test_e2e_runner.py
import boto3

def invoke_lambda_direct(function_name, payload):
    """Invoque Lambda directement via boto3."""
    lambda_client = boto3.client('lambda', region_name=AWS_REGION)
    
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    
    return json.loads(response['Payload'].read())

def run_aws_e2e_test(context):
    client_id = context['client_id']
    
    # Workflow E2E complet
    print("🚀 1/3 Ingestion...")
    invoke_lambda_direct(f"vectora-inbox-ingest-v2-{env}", {"client_id": client_id})
    
    print("🚀 2/3 Normalisation...")
    invoke_lambda_direct(f"vectora-inbox-normalize-score-v2-{env}", {"client_id": client_id})
    
    print("🚀 3/3 Newsletter...")
    invoke_lambda_direct(f"vectora-inbox-newsletter-v2-{env}", {"client_id": client_id})
```

**Avantages**:
- ✅ Workflow E2E complet
- ✅ Pas de script externe
- ✅ Contrôle total
- ✅ Logs intégrés au runner

**Inconvénients**:
- ⚠️ Duplication logique invoke

---

## 🎯 Recommandation Finale

**Adopter Option 2 + Option 1**:

1. **Court terme**: Modifier `invoke_normalize_score_v2.py` pour support `--client-id`
2. **Moyen terme**: Créer `invoke_e2e_workflow.py` pour workflow complet
3. **Long terme**: Intégrer dans runner AWS

---

## 📋 Implémentation Option 1 (Immédiat)

### Modifier invoke_normalize_score_v2.py

```python
parser.add_argument("--client-id", help="Client ID dynamique (ex: lai_weekly_v1)")

# Dans main()
if args.client_id:
    event_data = {"client_id": args.client_id}
    log(f"Event dynamique: {event_data}")
else:
    event_data = get_test_event(args.event)
```

### Modifier runner AWS

```python
# tests/aws/test_e2e_runner.py
result = subprocess.run(
    [sys.executable, "scripts/invoke/invoke_normalize_score_v2.py", 
     "--client-id", client_id],  # Passer client_id dynamiquement
    ...
)
```

**Temps**: 10 min  
**Impact**: Immédiat  
**Risque**: Faible

---

## 📋 Implémentation Option 2 (Recommandé)

### Créer invoke_e2e_workflow.py

```python
#!/usr/bin/env python3
"""
Invocation workflow E2E complet: ingest → normalize → newsletter.
"""

import boto3
import json
import argparse

def invoke_lambda(function_name, payload, region, profile):
    """Invoque Lambda et retourne résultat."""
    session = boto3.Session(profile_name=profile)
    lambda_client = session.client('lambda', region_name=region)
    
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    
    return json.loads(response['Payload'].read())

def run_e2e_workflow(client_id, env="dev", region="eu-west-3", profile="rag-lai-prod"):
    """Exécute workflow E2E complet."""
    
    print(f"🚀 Workflow E2E pour {client_id} (env: {env})")
    
    # 1. Ingest
    print("\n1/3 Ingestion...")
    result1 = invoke_lambda(
        f"vectora-inbox-ingest-v2-{env}",
        {"client_id": client_id},
        region, profile
    )
    print(f"✅ Ingest: {result1.get('statusCode')}")
    
    # 2. Normalize
    print("\n2/3 Normalisation...")
    result2 = invoke_lambda(
        f"vectora-inbox-normalize-score-v2-{env}",
        {"client_id": client_id},
        region, profile
    )
    print(f"✅ Normalize: {result2.get('statusCode')}")
    
    # 3. Newsletter
    print("\n3/3 Newsletter...")
    result3 = invoke_lambda(
        f"vectora-inbox-newsletter-v2-{env}",
        {"client_id": client_id},
        region, profile
    )
    print(f"✅ Newsletter: {result3.get('statusCode')}")
    
    return all(r.get('statusCode') == 200 for r in [result1, result2, result3])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--env", default="dev")
    args = parser.parse_args()
    
    success = run_e2e_workflow(args.client_id, args.env)
    sys.exit(0 if success else 1)
```

### Modifier runner AWS

```python
result = subprocess.run(
    [sys.executable, "scripts/invoke/invoke_e2e_workflow.py",
     "--client-id", client_id,
     "--env", "dev"],
    ...
)
```

**Temps**: 30 min  
**Impact**: Workflow E2E complet  
**Risque**: Faible

---

## 🎯 Plan d'Action

### Phase 1: Quick Fix (10 min)
- [ ] Modifier `invoke_normalize_score_v2.py` (ajouter `--client-id`)
- [ ] Modifier `tests/aws/test_e2e_runner.py` (passer `--client-id`)
- [ ] Tester avec `lai_weekly_v1`

### Phase 2: Workflow Complet (30 min)
- [ ] Créer `scripts/invoke/invoke_e2e_workflow.py`
- [ ] Modifier runner AWS pour utiliser nouveau script
- [ ] Tester workflow complet

### Phase 3: Documentation (15 min)
- [ ] Mettre à jour `.q-context/vectora-inbox-development-rules.md`
- [ ] Ajouter exemples invocation

---

**Recommandation**: ✅ Implémenter Phase 1 immédiatement, Phase 2 ensuite  
**Priorité**: 🔥 HAUTE (cohérence système E2E)
