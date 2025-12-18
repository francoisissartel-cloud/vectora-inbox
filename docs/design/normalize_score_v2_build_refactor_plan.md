# Plan de Remise au Carré : Build normalize_score_v2 avec Lambda Layers

**Date** : 16 janvier 2025  
**Objectif** : Refactoring complet du processus de build pour respecter les règles d'hygiène V4  
**Décisions validées** : Architecture Layers + Suppression scripts fix + Process standard + Priorité HAUTE  

---

## 1. Vue d'Ensemble du Plan

### 1.1 Objectif Final
Transformer le processus de build actuel (non-conforme V4) vers une architecture avec Lambda Layers respectant strictement `src_lambda_hygiene_v4.md`.

### 1.2 Architecture Cible
- **Handler** : `<1MB` (code source uniquement)
- **Layer vectora-core** : `src_v2/vectora_core/` (~5MB)
- **Layer common-deps** : PyYAML, requests, feedparser, beautifulsoup4, python-dateutil (~10MB)
- **Process standardisé** : 4 étapes (layers → build → deploy → invoke)

### 1.3 Bénéfices Attendus
- Conformité totale règles V4
- Réutilisabilité pour ingest_v2 et newsletter_v2
- Performance optimisée (cold start <3s)
- Maintenance simplifiée

---

## 2. Plan d'Exécution par Phases

### Phase 1 : Préparation et Requirements (30 min)
**Objectif** : Créer les fondations du nouveau processus

#### Tâches Phase 1
1. **Créer requirements.txt explicite**
   - Fichier : `src_v2/lambdas/normalize_score/requirements.txt`
   - Versions exactes des dépendances observées

2. **Créer structure scripts standardisée**
   - Dossiers : `scripts/layers/`, `scripts/build/`, `scripts/deploy/`, `scripts/invoke/`

3. **Validation environnement AWS**
   - Vérifier profil `rag-lai-prod`, région `eu-west-3`
   - Vérifier buckets existants

#### Livrables Phase 1
- `src_v2/lambdas/normalize_score/requirements.txt`
- Structure `scripts/` organisée
- Environnement AWS validé

---

### Phase 2 : Création des Lambda Layers (45 min)
**Objectif** : Créer et déployer les 2 layers obligatoires

#### Tâches Phase 2
1. **Script création vectora-core layer**
   - Fichier : `scripts/layers/create_vectora_core_layer.py`
   - Package `src_v2/vectora_core/` uniquement
   - Déploiement sur AWS avec nom `vectora-inbox-vectora-core-dev`

2. **Script création common-deps layer**
   - Fichier : `scripts/layers/create_common_deps_layer.py`
   - Installation depuis requirements.txt
   - Déploiement sur AWS avec nom `vectora-inbox-common-deps-dev`

3. **Validation des layers**
   - Vérifier tailles (<50MB chacun)
   - Tester imports localement

#### Livrables Phase 2
- Layer `vectora-inbox-vectora-core-dev` déployé
- Layer `vectora-inbox-common-deps-dev` déployé
- ARNs des layers récupérés

---

### Phase 3 : Refactoring Build Handler (30 min)
**Objectif** : Créer le processus de build du handler minimal

#### Tâches Phase 3
1. **Script build handler**
   - Fichier : `scripts/build/build_normalize_score_v2.py`
   - Package uniquement `handler.py` (sans dépendances)
   - Validation taille <1MB

2. **Validation handler**
   - Vérifier imports `vectora_core` fonctionnent
   - Tester structure du package

#### Livrables Phase 3
- Script `build_normalize_score_v2.py` fonctionnel
- Handler packagé <1MB validé

---

### Phase 4 : Refactoring Déploiement (30 min)
**Objectif** : Adapter le déploiement pour utiliser les layers

#### Tâches Phase 4
1. **Nouveau script déploiement**
   - Fichier : `scripts/deploy/deploy_normalize_score_v2_layers.py`
   - Basé sur `deploy_normalize_score_v2.py` existant
   - Ajout des layers ARN à la configuration Lambda
   - Suppression installation dépendances

2. **Test déploiement**
   - Déployer avec les layers
   - Vérifier configuration Lambda

#### Livrables Phase 4
- Script déploiement avec layers fonctionnel
- Lambda déployée avec layers

---

### Phase 5 : Tests et Validation (30 min)
**Objectif** : Valider le fonctionnement complet

#### Tâches Phase 5
1. **Script invocation standardisé**
   - Fichier : `scripts/invoke/invoke_normalize_score_v2.py`
   - Events de test prédéfinis
   - Format `--cli-binary-format raw-in-base64-out`

2. **Tests fonctionnels**
   - Test avec client `lai_weekly_v3`
   - Validation performance (cold start)
   - Comparaison avec version actuelle

#### Livrables Phase 5
- Script invocation fonctionnel
- Tests passants avec layers
- Métriques de performance

---

### Phase 6 : Nettoyage et Documentation (15 min)
**Objectif** : Finaliser la migration et nettoyer

#### Tâches Phase 6
1. **Archivage scripts obsolètes**
   - Déplacer `fix_yaml_dependency.py`, `fix_all_dependencies.py` vers `backup/`
   - Archiver `deploy_normalize_score_v2.py` (version actuelle)

2. **Documentation**
   - Mettre à jour `scripts/README.md`
   - Documenter le nouveau processus 4 étapes

#### Livrables Phase 6
- Scripts obsolètes archivés
- Documentation à jour
- Processus standard documenté

---

## 3. Détails Techniques par Phase

### Phase 1 - Requirements.txt
```
# src_v2/lambdas/normalize_score/requirements.txt
PyYAML==6.0.3
requests==2.32.5
feedparser==6.0.12
beautifulsoup4==4.14.3
python-dateutil==2.9.0
```

### Phase 2 - Layers ARN Cibles
```
vectora-core-layer: arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev:1
common-deps-layer: arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-common-deps-dev:1
```

### Phase 3 - Handler Package Cible
```
handler.py                    # ~2KB
└── (pas de dépendances)      # Total <1MB
```

### Phase 4 - Configuration Lambda Cible
```python
{
    "FunctionName": "vectora-inbox-normalize-score-v2-dev",
    "Runtime": "python3.11",
    "Layers": [
        "arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev:1",
        "arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-common-deps-dev:1"
    ],
    "Environment": {
        "Variables": {
            "ENV": "dev",
            "CONFIG_BUCKET": "vectora-inbox-config-dev",
            "DATA_BUCKET": "vectora-inbox-data-dev",
            "BEDROCK_MODEL_ID": "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "BEDROCK_REGION": "us-east-1"
        }
    }
}
```

---

## 4. Commandes Finales Cibles

```bash
# Processus complet en 4 étapes
python scripts/layers/create_lambda_layers.py
python scripts/build/build_normalize_score_v2.py  
python scripts/deploy/deploy_normalize_score_v2_layers.py
python scripts/invoke/invoke_normalize_score_v2.py --event lai_weekly_v3
```

---

## 5. Critères de Validation par Phase

### Phase 1 ✅
- [ ] `requirements.txt` créé avec versions exactes
- [ ] Structure `scripts/` organisée
- [ ] Environnement AWS accessible

### Phase 2 ✅  
- [ ] Layer vectora-core déployé (<10MB)
- [ ] Layer common-deps déployé (<15MB)
- [ ] ARNs récupérés et fonctionnels

### Phase 3 ✅
- [ ] Handler packagé <1MB
- [ ] Imports vectora_core validés
- [ ] Structure package correcte

### Phase 4 ✅
- [ ] Lambda déployée avec layers
- [ ] Configuration layers appliquée
- [ ] Variables d'environnement correctes

### Phase 5 ✅
- [ ] Invocation réussie avec lai_weekly_v3
- [ ] Performance maintenue ou améliorée
- [ ] Pas d'erreurs d'import

### Phase 6 ✅
- [ ] Scripts obsolètes archivés
- [ ] Documentation mise à jour
- [ ] Processus reproductible

---

## 6. Plan de Rollback

En cas de problème, rollback possible via :
1. Restaurer `deploy_normalize_score_v2.py` depuis backup
2. Redéployer avec l'ancien processus
3. Supprimer les layers créés
4. Analyser les erreurs avant nouvelle tentative

---

## 7. Prochaines Étapes Post-Migration

1. **Appliquer à ingest_v2** : Réutiliser les layers créés
2. **Préparer newsletter_v2** : Même architecture layers
3. **Généraliser le processus** : Template pour futures Lambdas
4. **Optimiser les layers** : Monitoring taille et performance

---

**Prêt pour l'exécution phase par phase. Commencer par Phase 1 ?**