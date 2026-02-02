# Recommandation Finale: Client Config + Isolation S3

**Date**: 2026-02-02  
**Besoin**: Test E2E complet avec données fraîches (pas de réutilisation)

---

## 🎯 Votre Besoin (Validé)

**Workflow E2E complet requis**:
```
Ingestion → Normalisation → Matching → Editorial
```

**Problème actuel**:
- Réutiliser `lai_weekly_v8` → Q trouve données existantes sur S3
- Q bypass ingestion et réutilise `s3://vectora-inbox-data-dev/ingested/lai_weekly_v8/`
- Pas de test E2E complet

**Solution actuelle (lai_weekly_v9, v10...)**:
- ✅ Nouveau client_id = nouveau dossier S3
- ✅ Pas de données existantes
- ✅ Workflow E2E complet garanti
- ❌ Mais incrémentation manuelle confuse

---

## ✅ Solution Recommandée: Système Hybride

### Principe

**Garder l'incrémentation vX MAIS l'automatiser et la lier aux contextes**

### Architecture

```
client-config-examples/
├── production/
│   └── lai_weekly_prod.yaml          # Production stable
├── test/
│   ├── test_context_001_local.yaml   # Local: lai_weekly_test_001
│   ├── test_context_001_aws.yaml     # AWS: lai_weekly_v1
│   ├── test_context_002_local.yaml   # Local: lai_weekly_test_002
│   └── test_context_002_aws.yaml     # AWS: lai_weekly_v2
└── templates/
    └── lai_weekly_template.yaml
```

### Mapping Contexte → Client ID → S3

| Contexte | Environnement | Client ID | Dossier S3 |
|----------|---------------|-----------|------------|
| test_context_001 | local | lai_weekly_test_001 | N/A (local) |
| test_context_001 | aws | lai_weekly_v1 | s3://.../lai_weekly_v1/ |
| test_context_002 | local | lai_weekly_test_002 | N/A (local) |
| test_context_002 | aws | lai_weekly_v2 | s3://.../lai_weekly_v2/ |

**Avantages**:
- ✅ Chaque test AWS = nouveau client_id (v1, v2, v3...)
- ✅ Nouveau dossier S3 = pas de données anciennes
- ✅ Workflow E2E complet garanti
- ✅ Traçabilité via test_context_id
- ✅ Génération automatique

---

## 🔧 Implémentation

### 1. Génération Automatique Client ID

**Runner local**:
```python
def create_new_context(purpose):
    next_num = max(existing, default=0) + 1
    context_id = f"test_context_{next_num:03d}"
    
    # Client ID local (pas de S3)
    client_id = f"lai_weekly_test_{next_num:03d}"
    
    # Générer config
    config = generate_config(
        template="lai_weekly_template.yaml",
        client_id=client_id,
        context_id=context_id,
        environment="local"
    )
```

**Runner AWS**:
```python
def create_aws_context(local_context_id, purpose):
    # Trouver prochain numéro vX
    existing_v = [extract_version(c['client_id']) for c in aws_history]
    next_v = max(existing_v, default=0) + 1
    
    # Client ID AWS (nouveau dossier S3)
    client_id = f"lai_weekly_v{next_v}"
    
    # Générer config
    config = generate_config(
        template="lai_weekly_template.yaml",
        client_id=client_id,
        context_id=context_id,
        environment="aws",
        promoted_from=local_context_id
    )
```

### 2. Métadonnées Complètes

**Config test**:
```yaml
client_profile:
  client_id: "lai_weekly_v1"
  name: "LAI Weekly - Test Context 001 (AWS)"

metadata:
  test_context_id: "test_context_001"
  test_purpose: "Validation domain scoring fix"
  test_environment: "aws_dev"
  promoted_from_local: "lai_weekly_test_001"
  s3_isolation: true  # Nouveau dossier S3 garanti
  created_date: "2026-02-02"
```

### 3. Nettoyage S3 Automatique

**Option 1: Nettoyage manuel après test**
```bash
# Après test réussi, archiver données S3
python scripts/maintenance/archive_test_data.py --client-id lai_weekly_v1
```

**Option 2: TTL automatique**
```yaml
# Dans config test
metadata:
  s3_ttl_days: 7  # Supprimer données S3 après 7 jours
```

---

## 📋 Workflow Complet

### Test E2E Complet

```bash
# 1. Créer contexte local
python tests/local/test_e2e_runner.py --new-context "Test domain scoring"
# → Génère: lai_weekly_test_001 (pas de S3)

# 2. Test local
python tests/local/test_e2e_runner.py --run
# → Test avec données locales

# 3. Deploy AWS
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev

# 4. Promouvoir vers AWS
python tests/aws/test_e2e_runner.py --promote "Validation E2E"
# → Génère: lai_weekly_v1 (nouveau dossier S3)
# → Upload config vers S3: s3://vectora-inbox-config-dev/clients/lai_weekly_v1.yaml

# 5. Test AWS E2E complet
python tests/aws/test_e2e_runner.py --run
# → Ingestion: s3://.../ingested/lai_weekly_v1/2026/02/02/items.json
# → Normalisation: s3://.../curated/lai_weekly_v1/2026/02/02/items.json
# → Newsletter: s3://.../newsletters/lai_weekly_v1/2026/02/02/newsletter.md
```

**Résultat**:
- ✅ Workflow E2E complet (ingestion → newsletter)
- ✅ Données fraîches (nouveau dossier S3)
- ✅ Traçabilité (lié à test_context_001)
- ✅ Automatisé (pas d'incrémentation manuelle)

---

## 🎯 Comparaison Solutions

| Aspect | Actuel (v9, v10...) | Recommandé (automatisé) |
|--------|---------------------|-------------------------|
| **Nouveau dossier S3** | ✅ Oui | ✅ Oui |
| **Workflow E2E complet** | ✅ Oui | ✅ Oui |
| **Incrémentation** | ❌ Manuelle | ✅ Automatique |
| **Traçabilité** | ⚠️ Partielle | ✅ Complète |
| **Génération config** | ❌ Manuelle | ✅ Automatique |
| **Lien contexte** | ❌ Aucun | ✅ Direct |

---

## 📊 Structure S3 Résultante

```
s3://vectora-inbox-data-dev/
├── ingested/
│   ├── lai_weekly_v1/          # Test context 001
│   │   └── 2026/02/02/items.json
│   ├── lai_weekly_v2/          # Test context 002
│   │   └── 2026/02/03/items.json
│   └── lai_weekly_prod/        # Production
│       └── 2026/02/04/items.json
└── curated/
    ├── lai_weekly_v1/
    ├── lai_weekly_v2/
    └── lai_weekly_prod/
```

**Avantages**:
- ✅ Isolation complète entre tests
- ✅ Pas de collision données
- ✅ Workflow E2E garanti
- ✅ Facile à nettoyer (supprimer dossier)

---

## 🔑 Règles pour Q Developer

**Q DOIT TOUJOURS**:
1. Générer nouveau client_id pour chaque test AWS (v1, v2, v3...)
2. Vérifier que dossier S3 n'existe pas avant test
3. Uploader config vers S3 avant invocation Lambda
4. Lier client_id au test_context_id dans métadonnées

**Q NE DOIT JAMAIS**:
1. Réutiliser client_id d'un test précédent
2. Bypasser ingestion si données S3 existent
3. Créer client_id manuellement sans contexte

---

## ✅ Recommandation Finale

**Adopter système hybride**:
- Garder incrémentation vX pour isolation S3
- Automatiser génération via système de contextes
- Lier chaque vX à un test_context_id
- Générer configs automatiquement

**Avantages**:
- ✅ Répond à votre besoin (workflow E2E complet)
- ✅ Élimine incrémentation manuelle
- ✅ Traçabilité complète
- ✅ Cohérence système

**Prochaine étape**:
Implémenter génération automatique dans runners (1-2h)

---

**Recommandation**: ✅ ADOPTER SYSTÈME HYBRIDE  
**Priorité**: 🔥 HAUTE  
**Effort**: 1-2h implémentation
