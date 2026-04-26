# Plan: Workflow E2E Complet - Invocation Lambda

**Date**: 2026-02-02  
**Objectif**: Créer script invocation workflow E2E (ingest → normalize → newsletter)  
**Durée estimée**: 45 min

---

## 🎯 Objectif

Créer `scripts/invoke/invoke_e2e_workflow.py` pour invoquer workflow complet avec client_id dynamique généré par système de contextes.

---

## 📋 Phase 0: Analyse et Validation

### Besoin
- Invoquer 3 Lambdas séquentiellement: ingest-v2 → normalize-score-v2 → newsletter-v2
- Support client_id dynamique (lai_weekly_v1, v2, etc.)
- Intégration avec runner AWS
- Logs consolidés
- Gestion erreurs

### Règles Q-Context Appliquées
- `.q-context/vectora-inbox-development-rules.md` - Architecture 3 Lambdas V2
- `.q-context/vectora-inbox-governance.md` - Scripts standardisés
- Profil AWS: `rag-lai-prod`
- Région: `eu-west-3`

### Validation
- ✅ Architecture 3 Lambdas V2 validée E2E
- ✅ Naming Lambdas: `vectora-inbox-{fonction}-v2-{env}`
- ✅ Workflow: ingest → normalize → newsletter

**Durée**: 5 min

---

## 📋 Phase 1: Créer Script Invoke E2E

### Fichier
`scripts/invoke/invoke_e2e_workflow.py`

### Fonctionnalités
1. Invoquer 3 Lambdas séquentiellement
2. Support multi-env (dev, stage, prod)
3. Logs détaillés par étape
4. Validation réponses
5. Gestion erreurs avec rollback

### Structure
```python
#!/usr/bin/env python3
"""
Invocation workflow E2E complet: ingest → normalize → newsletter.
Conforme règles Q-Context.
"""

import boto3
import json
import argparse
import sys
from datetime import datetime

AWS_PROFILE = "rag-lai-prod"
AWS_REGION = "eu-west-3"

def log(message):
    """Log avec timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def invoke_lambda(function_name, payload, session):
    """Invoque Lambda et retourne résultat."""
    lambda_client = session.client('lambda', region_name=AWS_REGION)
    
    log(f"Invocation: {function_name}")
    log(f"Payload: {json.dumps(payload)}")
    
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    
    result = json.loads(response['Payload'].read())
    status_code = result.get('statusCode', 500)
    
    if status_code == 200:
        log(f"✅ {function_name}: SUCCESS")
    else:
        log(f"❌ {function_name}: FAILED (status {status_code})")
    
    return result

def run_e2e_workflow(client_id, env="dev"):
    """Exécute workflow E2E complet."""
    
    log("="*80)
    log(f"WORKFLOW E2E - {client_id} (env: {env})")
    log("="*80)
    
    session = boto3.Session(profile_name=AWS_PROFILE)
    payload = {"client_id": client_id}
    
    # 1. Ingest
    log("\n📥 ÉTAPE 1/3: INGESTION")
    result_ingest = invoke_lambda(
        f"vectora-inbox-ingest-v2-{env}",
        payload,
        session
    )
    if result_ingest.get('statusCode') != 200:
        log("❌ Workflow arrêté: échec ingestion")
        return False
    
    # 2. Normalize
    log("\n🤖 ÉTAPE 2/3: NORMALISATION & SCORING")
    result_normalize = invoke_lambda(
        f"vectora-inbox-normalize-score-v2-{env}",
        payload,
        session
    )
    if result_normalize.get('statusCode') != 200:
        log("❌ Workflow arrêté: échec normalisation")
        return False
    
    # 3. Newsletter
    log("\n📰 ÉTAPE 3/3: GÉNÉRATION NEWSLETTER")
    result_newsletter = invoke_lambda(
        f"vectora-inbox-newsletter-v2-{env}",
        payload,
        session
    )
    if result_newsletter.get('statusCode') != 200:
        log("❌ Workflow arrêté: échec newsletter")
        return False
    
    log("\n" + "="*80)
    log("✅ WORKFLOW E2E COMPLÉTÉ AVEC SUCCÈS")
    log("="*80)
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Invocation workflow E2E complet"
    )
    parser.add_argument(
        "--client-id",
        required=True,
        help="Client ID (ex: lai_weekly_v1)"
    )
    parser.add_argument(
        "--env",
        default="dev",
        choices=["dev", "stage", "prod"],
        help="Environnement cible"
    )
    
    args = parser.parse_args()
    
    success = run_e2e_workflow(args.client_id, args.env)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
```

**Actions**:
- Créer fichier
- Rendre exécutable: `chmod +x` (Unix) ou pas nécessaire (Windows)

**Durée**: 15 min

---

## 📋 Phase 2: Modifier Runner AWS

### Fichier
`tests/aws/test_e2e_runner.py`

### Modifications
```python
def run_aws_e2e_test(context):
    """Exécute le test E2E sur AWS."""
    print(f"\n{'='*80}")
    print(f"☁️  TEST E2E AWS - {context['id']}")
    print(f"{'='*80}")
    print(f"Client ID: {context['client_id']}")
    print(f"Purpose: {context['purpose']}")
    print()
    
    client_id = context['client_id']
    
    try:
        # Invoke workflow E2E complet
        print(f"🚀 Invocation workflow E2E complet...")
        result = subprocess.run(
            [
                sys.executable,
                "scripts/invoke/invoke_e2e_workflow.py",
                "--client-id", client_id,
                "--env", "dev"
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=900  # 15 min max
        )
        
        # Afficher output
        if result.stdout:
            print(result.stdout)
        
        if result.returncode == 0:
            print("✅ Workflow E2E AWS réussi")
            update_context_status(
                context['id'],
                'completed',
                success=True,
                results={'timestamp': datetime.now().isoformat()}
            )
            return True
        else:
            print(f"❌ Workflow E2E AWS échoué")
            if result.stderr:
                print(result.stderr)
            update_context_status(context['id'], 'failed', success=False)
            return False
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        update_context_status(context['id'], 'failed', success=False)
        return False
```

**Actions**:
- Remplacer fonction `run_aws_e2e_test()`
- Tester avec contexte existant

**Durée**: 10 min

---

## 📋 Phase 3: Tests et Validation

### Test 1: Invocation Directe
```bash
python scripts/invoke/invoke_e2e_workflow.py --client-id lai_weekly_v1 --env dev
```

**Validation**:
- ✅ 3 Lambdas invoquées séquentiellement
- ✅ Logs clairs par étape
- ✅ StatusCode 200 pour chaque Lambda
- ✅ Données S3 créées

### Test 2: Via Runner AWS
```bash
# Créer contexte local
python tests/local/test_e2e_runner.py --new-context "Test workflow E2E"
python tests/local/test_e2e_runner.py --run

# Promouvoir et tester AWS
python tests/aws/test_e2e_runner.py --promote "Validation workflow E2E"
python tests/aws/test_e2e_runner.py --run
```

**Validation**:
- ✅ Client_id généré automatiquement (ex: lai_weekly_v10)
- ✅ Config uploadé vers S3
- ✅ Workflow E2E complet exécuté
- ✅ Contexte mis à jour avec succès

**Durée**: 10 min

---

## 📋 Phase 4: Documentation Q-Context

### Fichier
`.q-context/vectora-inbox-development-rules.md`

### Ajout Section
```markdown
## 🚀 INVOCATION WORKFLOW E2E

### Script Standardisé

**Fichier**: `scripts/invoke/invoke_e2e_workflow.py`

**Usage**:
```bash
python scripts/invoke/invoke_e2e_workflow.py --client-id lai_weekly_v1 --env dev
```

**Workflow**:
1. Ingest: `vectora-inbox-ingest-v2-{env}`
2. Normalize: `vectora-inbox-normalize-score-v2-{env}`
3. Newsletter: `vectora-inbox-newsletter-v2-{env}`

**Intégration Runner AWS**:
Le runner AWS utilise automatiquement ce script pour tests E2E complets.

### Règles Q Developer

**Q DOIT**:
- Utiliser `invoke_e2e_workflow.py` pour tests E2E AWS
- Invoquer workflow complet (pas seulement normalize)
- Vérifier succès de chaque étape

**Q NE DOIT JAMAIS**:
- Invoquer Lambdas individuellement pour test E2E
- Bypasser une étape du workflow
```

**Actions**:
- Ajouter section dans development-rules.md
- Mettre à jour exemples

**Durée**: 10 min

---

## 📋 Phase 5: Nettoyage et Finalisation

### Actions
1. Supprimer fichiers temporaires
2. Vérifier .gitignore
3. Créer rapport final

### Rapport Final
`docs/reports/development/workflow_e2e_invocation_implementation.md`

**Contenu**:
- Objectif atteint
- Fichiers créés/modifiés
- Tests effectués
- Métriques (temps, coût)

**Durée**: 5 min

---

## 📊 Résumé des Phases

| Phase | Description | Durée | Fichiers |
|-------|-------------|-------|----------|
| 0 | Analyse | 5 min | - |
| 1 | Script invoke E2E | 15 min | `invoke_e2e_workflow.py` |
| 2 | Modifier runner AWS | 10 min | `test_e2e_runner.py` |
| 3 | Tests | 10 min | - |
| 4 | Documentation | 10 min | `development-rules.md` |
| 5 | Finalisation | 5 min | Rapport |
| **TOTAL** | | **45 min** | **3 fichiers** |

---

## ✅ Critères de Succès

- [ ] Script `invoke_e2e_workflow.py` créé et fonctionnel
- [ ] Runner AWS modifié et testé
- [ ] Workflow E2E complet validé (ingest → normalize → newsletter)
- [ ] Client_id dynamique supporté
- [ ] Documentation Q-Context mise à jour
- [ ] Tests passés avec succès
- [ ] Rapport final créé

---

## 🔑 Points Clés Q-Context

1. **Architecture 3 Lambdas V2**: Respectée
2. **Naming conventions**: `vectora-inbox-{fonction}-v2-{env}`
3. **Profil AWS**: `rag-lai-prod`
4. **Région**: `eu-west-3`
5. **Scripts standardisés**: Dans `scripts/invoke/`
6. **Logs**: Timestamp + messages clairs
7. **Gestion erreurs**: Arrêt workflow si échec

---

**Plan créé**: 2026-02-02  
**Prêt pour exécution**: ✅ OUI  
**Validation requise**: Utilisateur confirme démarrage
