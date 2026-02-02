# Checklist Déploiement AWS - OBLIGATOIRE

**RÈGLE CRITIQUE**: Un déploiement AWS n'est JAMAIS complet sans vérifier TOUS les composants.

---

## 🚨 COMPOSANTS OBLIGATOIRES D'UN DÉPLOIEMENT

### 1. Code Lambda (Layers)
- [ ] Build layers (vectora-core + common-deps)
- [ ] Deploy layers vers AWS
- [ ] Update Lambda functions avec nouveaux layers

### 2. Fichiers Canonical S3
- [ ] Vérifier fichiers canonical modifiés localement
- [ ] Upload vers S3 (vectora-inbox-config-{env}/canonical/)
- [ ] Vérifier présence sur S3 après upload

### 3. Client Configs
- [ ] Vérifier client_config modifiés
- [ ] Upload vers S3 si nécessaire
- [ ] Valider structure YAML

### 4. Validation Post-Déploiement
- [ ] Test E2E AWS avec client réel
- [ ] Vérifier logs Lambda (pas d'erreurs FileNotFound)
- [ ] Confirmer résultats attendus

---

## 📋 WORKFLOW DÉPLOIEMENT COMPLET

### Étape 1: Identifier Changements
```bash
# Quels fichiers ont changé?
git status
git diff HEAD~1
```

**Questions à se poser**:
- Ai-je modifié du code Python? → Build + Deploy layers
- Ai-je modifié canonical/? → Upload S3
- Ai-je modifié client-config? → Upload S3
- Ai-je ajouté de nouveaux fichiers canonical? → Upload S3

### Étape 2: Build (si code modifié)
```bash
python scripts/build/build_all.py
```

### Étape 3: Deploy Layers (si code modifié)
```bash
python scripts/deploy/deploy_env.py --env dev
```

### Étape 4: Upload Canonical (si canonical/ modifié)
```bash
# Vérifier d'abord ce qui existe sur S3
aws s3 ls s3://vectora-inbox-config-dev/canonical/ --recursive --profile rag-lai-prod

# Upload fichiers modifiés
aws s3 sync canonical/ s3://vectora-inbox-config-dev/canonical/ --profile rag-lai-prod

# Vérifier upload
aws s3 ls s3://vectora-inbox-config-dev/canonical/prompts/domain_scoring/ --profile rag-lai-prod
```

### Étape 5: Validation E2E
```bash
python scripts/invoke/invoke_e2e_workflow.py --client-id lai_weekly_v9 --env dev
```

---

## 🔍 DÉTECTION PROBLÈMES CANONICAL

### Symptômes
- Lambda logs: "FileNotFoundError: canonical/prompts/domain_scoring/..."
- Lambda logs: "No such key: canonical/domains/..."
- Tests locaux OK, tests AWS KO

### Diagnostic
```bash
# 1. Vérifier fichiers locaux
ls canonical/prompts/domain_scoring/
ls canonical/domains/

# 2. Vérifier S3
aws s3 ls s3://vectora-inbox-config-dev/canonical/prompts/domain_scoring/ --profile rag-lai-prod
aws s3 ls s3://vectora-inbox-config-dev/canonical/domains/ --profile rag-lai-prod

# 3. Comparer
diff <(ls canonical/prompts/domain_scoring/) <(aws s3 ls s3://vectora-inbox-config-dev/canonical/prompts/domain_scoring/ --profile rag-lai-prod | awk '{print $4}')
```

### Solution
```bash
# Upload manquants
aws s3 sync canonical/ s3://vectora-inbox-config-dev/canonical/ --profile rag-lai-prod --dryrun
aws s3 sync canonical/ s3://vectora-inbox-config-dev/canonical/ --profile rag-lai-prod
```

---

## 📊 MATRICE DÉPLOIEMENT

| Changement | Build | Deploy Layer | Upload Canonical | Upload Config | Test E2E |
|------------|-------|--------------|------------------|---------------|----------|
| Code Python | ✅ | ✅ | ❌ | ❌ | ✅ |
| Canonical prompts | ❌ | ❌ | ✅ | ❌ | ✅ |
| Canonical domains | ❌ | ❌ | ✅ | ❌ | ✅ |
| Client config | ❌ | ❌ | ❌ | ✅ | ✅ |
| Code + Canonical | ✅ | ✅ | ✅ | ❌ | ✅ |

---

## 🎯 RÈGLES Q DEVELOPER

### AVANT de dire "Déploiement complété"

**TOUJOURS vérifier**:
1. Ai-je créé/modifié des fichiers dans canonical/?
2. Ces fichiers existent-ils sur S3?
3. Le test E2E AWS passe-t-il?

### JAMAIS assumer

❌ "Le code est déployé donc c'est bon"
❌ "Les fichiers canonical sont déjà sur S3"
❌ "Ça marche en local donc ça marchera sur AWS"

✅ "J'ai vérifié que TOUS les fichiers nécessaires sont sur S3"
✅ "J'ai lancé un test E2E AWS pour confirmer"
✅ "J'ai consulté les logs Lambda pour vérifier"

### Phrase magique

**"Un déploiement AWS = Code + Data + Validation"**

---

## 🔧 Script Automatisé (TODO)

Créer `scripts/deploy/deploy_complete.py`:
```python
# 1. Détecte changements (git diff)
# 2. Build si code modifié
# 3. Deploy layers si code modifié
# 4. Upload canonical si canonical/ modifié
# 5. Upload configs si client-config modifié
# 6. Test E2E automatique
# 7. Rapport complet
```

---

## 📝 Exemple Réel: Domain Scoring

**Changements**:
- Code: config_loader.py (charge domain_scoring)
- Canonical: canonical/prompts/domain_scoring/lai_domain_scoring.yaml (nouveau)
- Canonical: canonical/domains/lai_domain_definition.yaml (nouveau)

**Déploiement requis**:
1. ✅ Build layers (code modifié)
2. ✅ Deploy layers (code modifié)
3. ✅ Upload canonical/prompts/domain_scoring/ (nouveau fichier)
4. ✅ Upload canonical/domains/ (nouveau fichier)
5. ✅ Test E2E AWS

**Si oublié étape 3-4**: Lambda crash avec FileNotFoundError

---

**Dernière mise à jour**: 2026-02-02  
**Statut**: RÈGLES OBLIGATOIRES - À RESPECTER SYSTÉMATIQUEMENT
