# Template Test E2E AWS - Vectora Inbox

**Version**: 2.0  
**Date**: 2026-02-02  
**Durée**: ~30 minutes  

---

## 🔧 Infrastructure AWS (À CONNAÎTRE)

### Compte & Région
- **Account ID**: 786469175371
- **Région principale**: eu-west-3
- **Profile AWS CLI**: rag-lai-prod
- **Bedrock région**: us-east-1

### Buckets S3

**Dev**:
```
Config:      s3://vectora-inbox-config-dev/clients/{client_id}.yaml
Data:        s3://vectora-inbox-data-dev/
  - ingested/{client_id}/{YYYY}/{MM}/{DD}/items.json
  - curated/{client_id}/{YYYY}/{MM}/{DD}/items.json
Newsletters: s3://vectora-inbox-newsletters-dev/{client_id}/{YYYY}/{MM}/{DD}/
  - newsletter.md
  - metadata.json
```

**Stage**:
```
Config:      s3://vectora-inbox-config-stage/clients/{client_id}.yaml
Data:        s3://vectora-inbox-data-stage/
Newsletters: s3://vectora-inbox-newsletters-stage/
```

### Lambdas (eu-west-3)

**Dev**:
- `vectora-inbox-ingest-v2-dev`
- `vectora-inbox-normalize-score-v2-dev`
- `vectora-inbox-newsletter-v2-dev`

**Stage**:
- `vectora-inbox-ingest-v2-stage`
- `vectora-inbox-normalize-score-v2-stage`
- `vectora-inbox-newsletter-v2-stage`

---

## ✅ Checklist Pré-Test (5 min)

- [ ] Token SSO valide: `aws sso login --profile rag-lai-prod`
- [ ] Nouveau client_id choisi (ex: lai_weekly_v11)
- [ ] Config client créée localement
- [ ] Lambdas déployées: `aws lambda list-functions --region eu-west-3 --profile rag-lai-prod | findstr vectora-inbox`

**Durées attendues**:
- Ingest: ~20s
- Normalize: ~5-10 min (dépend nombre items)
- Newsletter: ~5s

---

## 🚀 Workflow Test E2E (30 min)

### Étape 1: Créer Config Client (5 min)

```bash
# 1. Copier config existante
cp client-config-examples/production/lai_weekly_v9.yaml \
   client-config-examples/production/lai_weekly_v11.yaml

# 2. Modifier (obligatoire):
#    - client_id: "lai_weekly_v11"
#    - name: "LAI Weekly v11 - Test E2E [date]"
#    - metadata.created_date: "2026-02-XX"
#    - metadata.template_version: "11.0.0"

# 3. Upload S3
aws s3 cp client-config-examples/production/lai_weekly_v11.yaml \
  s3://vectora-inbox-config-dev/clients/lai_weekly_v11.yaml \
  --profile rag-lai-prod

# 4. Vérifier upload
aws s3 ls s3://vectora-inbox-config-dev/clients/ \
  --profile rag-lai-prod | findstr lai_weekly_v11
```

---

### Étape 2: Ingest (1 min)

```bash
# Créer payload
echo {"client_id": "lai_weekly_v11"} > .tmp/payload.json

# Invoquer lambda (synchrone - rapide)
aws lambda invoke \
  --function-name vectora-inbox-ingest-v2-dev \
  --payload file://.tmp/payload.json \
  --region eu-west-3 \
  --profile rag-lai-prod \
  .tmp/ingest_response.json

# Vérifier S3
aws s3 ls s3://vectora-inbox-data-dev/ingested/lai_weekly_v11/ \
  --recursive --profile rag-lai-prod
```

**Validation**:
- StatusCode: 200
- Fichier items.json créé dans S3
- Items ingérés > 20

---

### Étape 3: Normalize & Score (5-10 min)

```bash
# Invoquer lambda (ASYNCHRONE - prend 5-10 min)
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --invocation-type Event \
  --payload file://.tmp/payload.json \
  --region eu-west-3 \
  --profile rag-lai-prod \
  .tmp/normalize_response.json

# StatusCode attendu: 202 (asynchrone accepté)

# Attendre 5-10 min puis vérifier S3
aws s3 ls s3://vectora-inbox-data-dev/curated/lai_weekly_v11/ \
  --recursive --profile rag-lai-prod

# Télécharger items normalisés
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v11/2026/02/XX/items.json \
  .tmp/normalized_items.json \
  --profile rag-lai-prod
```

**Validation**:
- StatusCode: 202
- Fichier items.json créé dans curated/ (PAS normalized/)
- 100% items avec domain_scoring
- Taux relevance > 50%

**Vérifier logs si problème**:
```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/vectora-inbox-normalize-score-v2-dev \
  --filter-pattern "lai_weekly_v11" \
  --region eu-west-3 \
  --profile rag-lai-prod \
  --max-items 20
```

---

### Étape 4: Newsletter (1 min)

```bash
# Invoquer lambda (synchrone - rapide)
aws lambda invoke \
  --function-name vectora-inbox-newsletter-v2-dev \
  --payload file://.tmp/payload.json \
  --region eu-west-3 \
  --profile rag-lai-prod \
  .tmp/newsletter_response.json

# Vérifier S3
aws s3 ls s3://vectora-inbox-newsletters-dev/lai_weekly_v11/ \
  --recursive --profile rag-lai-prod

# Télécharger newsletter
aws s3 cp s3://vectora-inbox-newsletters-dev/lai_weekly_v11/2026/02/XX/newsletter.md \
  .tmp/newsletter.md \
  --profile rag-lai-prod
```

**Validation**:
- StatusCode: 200
- Fichier newsletter.md créé
- Items > 0 dans newsletter
- Sections remplies

---

### Étape 5: Analyser Résultats (5 min)

```bash
# Analyser items ingérés
python -c "import json; items=json.load(open('.tmp/ingest_items.json', encoding='utf-8')); print(f'Items ingérés: {len(items)}'); sources={}; [sources.update({item.get('source_key', 'unknown'): sources.get(item.get('source_key', 'unknown'), 0) + 1}) for item in items]; [print(f'  {k}: {v}') for k,v in sorted(sources.items())]"

# Analyser items normalisés
python -c "import json; items=json.load(open('.tmp/normalized_items.json', encoding='utf-8')); with_ds=sum(1 for i in items if i.get('has_domain_scoring')); relevant=sum(1 for i in items if i.get('domain_scoring',{}).get('is_relevant')); scores=[i.get('domain_scoring',{}).get('score',0) for i in items if i.get('has_domain_scoring')]; print(f'Items normalisés: {len(items)}'); print(f'Avec domain_scoring: {with_ds}/{len(items)}'); print(f'LAI relevant: {relevant}/{with_ds}'); print(f'Score moyen: {sum(scores)/len(scores) if scores else 0:.1f}/100')"

# Analyser newsletter
type .tmp\newsletter.md
```

---

## 📊 Métriques Attendues

### Funnel de Conversion
```
Étape                    | Volume | Taux conv | Taux perte | Cible
-------------------------|--------|-----------|------------|-------
Sources scrapées         | X      | -         | -          | ≥2
Items ingérés            | XX     | 100%      | 0%         | >20
Items normalisés         | XX     | XX%       | XX%        | 100%
Items avec domain_scoring| XX     | XX%       | XX%        | 100%
Items LAI relevant       | XX     | XX%       | XX%        | >50%
Items matchés domaine    | XX     | XX%       | XX%        | >50%
Items sélectionnés       | XX     | XX%       | XX%        | 10-20
```

### Métriques Détaillées

| Métrique | Cible | Validation |
|----------|-------|------------|
| **Ingest** |
| Items ingérés | > 20 | ✅ / ❌ |
| Sources actives | ≥ 2 | ✅ / ❌ |
| Durée | < 60s | ✅ / ❌ |
| **Normalize** |
| Items normalisés | 100% | ✅ / ❌ |
| Avec domain_scoring | 100% | ✅ / ❌ |
| Taux relevance | > 50% | ✅ / ❌ |
| Score moyen | 30-70 | ✅ / ❌ |
| Durée | < 15min | ✅ / ❌ |
| **Entités Extraites** |
| Companies | >0 | ✅ / ❌ |
| Molecules | >0 | ✅ / ❌ |
| Technologies | >0 | ✅ / ❌ |
| Trademarks | >0 | ✅ / ❌ |
| **Newsletter** |
| Items sélectionnés | 10-20 | ✅ / ❌ |
| Sections remplies | 4/4 | ✅ / ❌ |
| TLDR présent | Oui | ✅ / ❌ |
| Durée | < 60s | ✅ / ❌ |

---

## 🚨 Problèmes Fréquents

### Token SSO expiré
```
Error: Token has expired and refresh failed
Solution: aws sso login --profile rag-lai-prod
```

### Bucket introuvable
```
Error: NoSuchBucket
Solution: Vérifier noms buckets dans section Infrastructure
```

### Timeout lambda
```
Error: Read timeout
Solution: Utiliser --invocation-type Event pour normalize (asynchrone)
```

### Fichier items.json introuvable
```
Cherché: normalized/
Correct: curated/
```

### Région incorrecte
```
Erreur: Function not found in us-east-1
Solution: Utiliser --region eu-west-3
```

---

## 🛠️ Script Python Automatisé (Optionnel)

**Fichier**: `scripts/test/run_e2e_aws.py`

```python
#!/usr/bin/env python3
"""Test E2E AWS automatisé."""
import boto3, json, time, sys
from datetime import datetime

REGION = 'eu-west-3'
PROFILE = 'rag-lai-prod'

def run_e2e(client_id, env='dev'):
    session = boto3.Session(profile_name=PROFILE)
    lambda_client = session.client('lambda', region_name=REGION)
    s3_client = session.client('s3', region_name=REGION)
    
    payload = {"client_id": client_id}
    
    print(f"=== Test E2E: {client_id} ({env}) ===\n")
    
    # 1. Ingest
    print("[1/3] Ingest...")
    r = lambda_client.invoke(
        FunctionName=f'vectora-inbox-ingest-v2-{env}',
        Payload=json.dumps(payload)
    )
    print(f"  StatusCode: {r['StatusCode']}")
    
    # 2. Normalize (asynchrone)
    print("[2/3] Normalize & Score (asynchrone, 5-10 min)...")
    r = lambda_client.invoke(
        FunctionName=f'vectora-inbox-normalize-score-v2-{env}',
        InvocationType='Event',
        Payload=json.dumps(payload)
    )
    print(f"  StatusCode: {r['StatusCode']}")
    print("  Attente 5 min...")
    time.sleep(300)
    
    # 3. Newsletter
    print("[3/3] Newsletter...")
    r = lambda_client.invoke(
        FunctionName=f'vectora-inbox-newsletter-v2-{env}',
        Payload=json.dumps(payload)
    )
    print(f"  StatusCode: {r['StatusCode']}")
    
    print("\n=== Test terminé ===")
    print("Vérifier résultats dans S3")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_e2e_aws.py <client_id> [env]")
        sys.exit(1)
    run_e2e(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'dev')
```

**Usage**:
```bash
python scripts/test/run_e2e_aws.py lai_weekly_v11 dev
```

---

## 🔍 Analyse Qualité Items

### Validation Items Sélectionnés (Top 5)

Pour chaque item sélectionné, valider:

#### Item #1: [Titre]
- **Source**: [source_key]
- **Event type**: [type]
- **Score final**: X.X/20
- **Section**: [section]

**Évaluation**:
- ✅ / ❌ Normalisation correcte
- ✅ / ❌ Entités extraites pertinentes
- ✅ / ❌ Domain scoring cohérent
- ✅ / ❌ Score justifié
- ✅ / ❌ Sélection newsletter appropriée

**Commentaire**: [Observations]

[Répéter pour items 2-5]

### Validation Items Rejetés (Échantillon)

Vérifier que les rejets sont justifiés:

#### Item rejeté #1: [Titre]
- **Raison rejet**: [score trop bas / non matché / etc.]
- **Évaluation**: ✅ Rejet justifié / ❌ Devrait être sélectionné

[Répéter pour 3-5 items rejetés]

---

## 💰 Analyse Coûts

### Coûts Bedrock
```
Type Appel           | Nombre | Tokens In | Tokens Out | Coût
---------------------|--------|-----------|------------|---------
Normalisation        | XX     | ~XXXX     | ~XXX       | $X.XX
Domain Scoring       | XX     | ~XXXX     | ~XXX       | $X.XX
TL;DR                | X      | ~XXXX     | ~XXX       | $X.XX
Introduction         | X      | ~XXXX     | ~XXX       | $X.XX
TOTAL                | XX     | ~XXXX     | ~XXX       | $X.XX
```

**Modèle**: anthropic.claude-3-sonnet-20240229-v1:0  
**Région**: us-east-1  
**Prix**: $3/1M input, $15/1M output

### Projections
```
Fréquence            | Coût/période | Coût annuel
---------------------|--------------|-------------
Hebdomadaire         | $X.XX        | $XX.XX
Bi-hebdomadaire      | $X.XX        | $XX.XX
Mensuel              | $X.XX        | $XX.XX
```

---

## 🎯 Décision Finale

### Statut Global

🟢 **MOTEUR PRÊT POUR PRODUCTION**  
🟡 **PRÊT AVEC AJUSTEMENTS MINEURS**  
🔴 **NON PRÊT - CORRECTIONS REQUISES**

### Justification

**Points forts**:
1. [Point fort 1]
2. [Point fort 2]
3. [Point fort 3]

**Points d'amélioration**:
1. [Point amélioration 1]
2. [Point amélioration 2]

**Actions requises avant production**:
1. [Action priorité critique]
2. [Action priorité haute]

---

## 📝 Template Rapport

**Fichier**: `docs/reports/test_e2e_aws_{client_id}_{date}.md`

```markdown
# Rapport Test E2E AWS - {client_id}

**Date**: {date}
**Environnement**: {env}
**Durée**: {durée}

## Résultats

| Étape | Statut | Items Input | Items Output | Durée |
|-------|--------|-------------|--------------|-------|
| Ingest | ✅/❌ | - | X | Xs |
| Normalize | ✅/❌ | X | X (Y relevant) | Xmin |
| Newsletter | ✅/❌ | X | X | Xs |

## Métriques Détaillées

### Ingest
- Items ingérés: X
- Sources: Y
- Répartition: [détails]

### Normalize
- Items normalisés: X/X (100%)
- Avec domain_scoring: X/X (100%)
- LAI relevant: X/X (Y%)
- Score moyen: X/100

### Newsletter
- Items sélectionnés: X
- Sections remplies: X/4
- Taille: X caractères

## Problèmes Détectés
[Liste]

## Conclusion
✅ / ⚠️ / ❌
```

---

## 💡 Conseils Q Developer

1. **Toujours vérifier** token SSO avant test long
2. **Utiliser asynchrone** pour normalize (>60s)
3. **Chercher dans curated/** pas normalized/
4. **Région eu-west-3** pour lambdas
5. **Éviter emojis** dans scripts (Windows)
6. **Nouveau client_id** à chaque test (données fraîches)

---

**Template Version**: 2.0  
**Dernière mise à jour**: 2026-02-02  
**Temps test**: ~30 minutes  
**Taux succès attendu**: 90%
