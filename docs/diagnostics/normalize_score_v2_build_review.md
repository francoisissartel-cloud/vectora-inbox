# Audit et Diagnostic : Processus de Build normalize_score_v2

**Date** : 16 janvier 2025  
**Auditeur** : Amazon Q Developer  
**Mode** : Audit et remise au carré du process de build  
**Référence** : Règles d'hygiène V4 + Architecture src_v2  

---

## 1. Résumé du Contexte

### 1.1 Situation Actuelle

La lambda `vectora-inbox-normalize-score-v2-dev` a été récemment déployée avec succès via les scripts :
- `deploy_normalize_score_v2.py` : Script de déploiement principal
- `fix_yaml_dependency.py` : Correction spécifique PyYAML
- `fix_all_dependencies.py` : Ajout de toutes les dépendances

Le déploiement fonctionne techniquement mais présente des divergences avec les règles d'hygiène V4 établies pour maintenir `/src_v2` propre et éviter les "usines à gaz".

### 1.2 Règles d'Hygiène V4 Applicables au Build

- **Interdiction absolue** de copier des libs tierces dans `/src_v2/`
- **Obligation** d'utiliser Lambda Layers pour les dépendances
- **Taille max handler** : 5MB (code source uniquement)
- **Architecture 3 Lambdas V2** : handlers minimaux + vectora_core via layers
- **Process de build standard** : scripts dans `/scripts/`, pas de hacks
- **Environnement AWS de référence** : eu-west-3, profil rag-lai-prod

---

## 2. Ce qui est Conforme aux Règles d'Hygiène

### 2.1 ✅ Architecture et Structure

- **Source propre** : `src_v2/lambdas/normalize_score/handler.py` minimal et conforme
- **Vectora_core séparé** : `src_v2/vectora_core/` bien structuré sans pollution
- **Conventions AWS** : Profil `rag-lai-prod`, région `eu-west-3`, compte `786469175371`
- **Nommage conforme** : `vectora-inbox-normalize-score-v2-dev`
- **Variables d'environnement** : Configuration standardisée (CONFIG_BUCKET, DATA_BUCKET, etc.)

### 2.2 ✅ Logique de Déploiement

- **Vérifications préalables** : Validation environnement AWS, buckets, rôles IAM
- **Upload S3** : Package stocké dans `vectora-inbox-lambda-code-dev`
- **Configuration Bedrock** : Modèle et région correctement configurés
- **Test automatique** : Invocation de test post-déploiement

### 2.3 ✅ Généricité

- **Pas de hardcoding client** : Configuration pilotée par `client_config` et `canonical`
- **Handler générique** : Délégation à `vectora_core.normalization`
- **Variables d'environnement** : Paramétrage externe des buckets et modèles

---

## 3. Ce qui N'est PAS Conforme ou Fragile

### 3.1 ❌ Violation Majeure : Packaging des Dépendances

**Problème** : Les scripts `fix_yaml_dependency.py` et `fix_all_dependencies.py` installent directement les dépendances dans le package Lambda.

```python
# Dans fix_all_dependencies.py - VIOLATION des règles V4
pip_command = f"pip install {package} -t {package_dir} --no-deps"
```

**Violations identifiées** :
- Installation directe dans le package Lambda (contraire à la règle layers)
- Taille du package potentiellement >5MB (observé : risque de dépassement)
- Pas d'utilisation des Lambda Layers obligatoires
- Process de build non-standard (pip direct vs layers)

### 3.2 ❌ Scripts de Fix Ad-Hoc

**Problème** : Création de scripts de "fix" spécifiques au lieu d'un process de build standard.

**Scripts problématiques** :
- `fix_yaml_dependency.py` : Hack spécifique PyYAML
- `fix_all_dependencies.py` : Installation manuelle de toutes les deps

**Risques** :
- **Whack-a-mole** : Un script de fix par problème de dépendance
- **Maintenance impossible** : Pas de process reproductible
- **Fragmentation** : 3 scripts différents pour 1 déploiement
- **Non-scalable** : Que faire pour la prochaine Lambda ?

### 3.3 ❌ Absence de Lambda Layers

**Problème** : Aucune utilisation des Lambda Layers pourtant obligatoires selon les règles V4.

**Layers manquants** :
- `vectora-core` : Devrait contenir `vectora_core/`
- `common-deps` : Devrait contenir PyYAML, requests, feedparser, etc.

**Conséquences** :
- Package Lambda volumineux (>5MB limite recommandée)
- Duplication des dépendances entre Lambdas
- Cold start dégradé
- Violation des bonnes pratiques AWS

### 3.4 ❌ Gestion des Dépendances Non-Standard

**Problème** : Installation des dépendances via pip direct au lieu d'un requirements.txt standard.

```python
# ANTI-PATTERN observé
REQUIRED_PACKAGES = [
    "PyYAML",
    "requests", 
    "feedparser",
    "beautifulsoup4",
    "python-dateutil"
]
```

**Manque** :
- Pas de `requirements.txt` explicite dans `src_v2/lambdas/normalize_score/`
- Pas de versioning des dépendances
- Pas de lock file pour la reproductibilité

---

## 4. Risques à Moyen Terme

### 4.1 Risque de Régression Architecturale

- **Retour aux mauvaises pratiques** : Tentation de copier les dépendances dans `/src_v2/`
- **Pollution progressive** : Chaque nouvelle dépendance = nouveau script de fix
- **Abandon des layers** : Process actuel ne pousse pas vers les layers

### 4.2 Risque de Maintenance

- **Scripts de fix non-maintenus** : Qui va maintenir `fix_yaml_dependency.py` ?
- **Process non-documenté** : Pas de documentation du process de build standard
- **Dépendance aux scripts** : Impossible de déployer sans les 3 scripts

### 4.3 Risque de Performance

- **Packages volumineux** : Cold start dégradé sur toutes les Lambdas
- **Duplication des deps** : Même problème sur ingest_v2 et newsletter_v2
- **Coûts AWS** : Stockage et transfert des packages volumineux

### 4.4 Risque de Conformité

- **Violation continue des règles V4** : Process actuel ne respecte pas les layers
- **Exemple négatif** : Autres développeurs vont copier ce pattern
- **Audit futur** : Process actuel ne passera pas un audit d'hygiène

---

## 5. Recommandations Concrètes

### 5.1 Recommandation Principale : Passage aux Lambda Layers

**Cible** : Architecture conforme V4 avec 2 Lambda Layers
- `vectora-core-layer` : Contient uniquement `vectora_core/`
- `common-deps-layer` : Contient PyYAML, requests, feedparser, beautifulsoup4, python-dateutil

**Bénéfices** :
- Handlers <1MB (conforme règle 5MB)
- Réutilisation entre les 3 Lambdas V2
- Process de build standard et reproductible
- Conformité totale aux règles V4

### 5.2 Recommandation Alternative : MVP Sans Layers

**Si les layers sont trop complexes à court terme** :
- Garder le packaging direct MAIS avec un script de build unique et propre
- Créer un `requirements.txt` explicite avec versions lockées
- Supprimer les scripts de fix ad-hoc
- Documenter le process temporaire

**Limite** : Cette approche reste non-conforme V4 mais acceptable en MVP.

---

## 6. Plan de Remise au Carré du Build normalize_score_v2

### 6.1 Cible Recommandée : Architecture avec Lambda Layers

**Objectif** : Passage direct à l'architecture avec 2 Lambda Layers en respectant strictement `src_lambda_hygiene_v4.md`.

**Avantages** :
- Conformité totale aux règles V4
- Réutilisabilité pour ingest_v2 et newsletter_v2
- Process de build standard et maintenable
- Performance optimale (handlers <1MB)

### 6.2 Étapes du Plan (8 étapes)

#### Étape 1 : Création du requirements.txt explicite
- Créer `src_v2/lambdas/normalize_score/requirements.txt` avec versions exactes :
  ```
  PyYAML==6.0.3
  requests==2.32.5
  feedparser==6.0.12
  beautifulsoup4==4.14.3
  python-dateutil==2.9.0
  ```

#### Étape 2 : Script de création des Lambda Layers
- Créer `scripts/create_lambda_layers.py` :
  - Layer `vectora-core` : Package `src_v2/vectora_core/`
  - Layer `common-deps` : Install depuis requirements.txt
- Déploiement des layers sur AWS

#### Étape 3 : Modification du handler pour utiliser les layers
- Vérifier que `src_v2/lambdas/normalize_score/handler.py` importe correctement
- Tester les imports localement avec les layers

#### Étape 4 : Script de build standard
- Créer `scripts/build_normalize_score_v2.py` :
  - Package uniquement le handler (sans dépendances)
  - Référence aux layers ARN
  - Validation taille <1MB

#### Étape 5 : Script de déploiement standard
- Modifier `deploy_normalize_score_v2.py` :
  - Utiliser les layers ARN
  - Supprimer l'installation des dépendances
  - Garder la logique de configuration

#### Étape 6 : Commande d'invocation CLI standard
- Créer `scripts/invoke_normalize_score_v2.py` :
  - Commande standardisée avec `--cli-binary-format raw-in-base64-out`
  - Events de test prédéfinis
  - Validation des réponses

#### Étape 7 : Tests et validation
- Tester le déploiement avec layers
- Valider les performances (cold start)
- Tester avec le client `lai_weekly_v3`

#### Étape 8 : Nettoyage et archivage
- **SUPPRIMER** : `fix_yaml_dependency.py`, `fix_all_dependencies.py`
- **ARCHIVER** : `deploy_normalize_score_v2.py` (version actuelle)
- **DOCUMENTER** : Process de build standard dans `/scripts/README.md`

### 6.3 Structure Cible des Scripts

```
scripts/
├── layers/
│   ├── create_lambda_layers.py          # Création des 2 layers
│   └── update_lambda_layers.py          # Mise à jour des layers
├── build/
│   ├── build_normalize_score_v2.py      # Build handler uniquement
│   └── validate_build.py                # Validation taille/imports
├── deploy/
│   ├── deploy_normalize_score_v2.py     # Déploiement avec layers
│   └── deploy_all_lambdas_v2.py         # Déploiement des 3 Lambdas
└── invoke/
    ├── invoke_normalize_score_v2.py     # Invocation standardisée
    └── test_events/
        ├── lai_weekly_v3.json           # Event de test
        └── minimal_test.json            # Event minimal
```

### 6.4 Commandes Cibles Finales

```bash
# 1. Création des layers (une fois)
python scripts/layers/create_lambda_layers.py

# 2. Build du handler
python scripts/build/build_normalize_score_v2.py

# 3. Déploiement
python scripts/deploy/deploy_normalize_score_v2.py

# 4. Test
python scripts/invoke/invoke_normalize_score_v2.py --event lai_weekly_v3
```

---

## 7. Décisions Clés à Prendre

### 7.1 Décision 1 : Layers Maintenant ou MVP Temporaire ?

**Option A - Layers maintenant (RECOMMANDÉ)** :
- ✅ Conformité totale V4
- ✅ Réutilisable pour les autres Lambdas
- ✅ Performance optimale
- ❌ Plus de travail initial

**Option B - MVP sans layers temporaire** :
- ✅ Plus rapide à implémenter
- ✅ Garde le déploiement fonctionnel
- ❌ Non-conforme V4
- ❌ Dette technique

### 7.2 Décision 2 : Suppression Immédiate des Scripts de Fix ?

**Recommandation** : Suppression après validation du nouveau process
- Garder temporairement pour rollback
- Supprimer dès que le nouveau process est validé
- Archiver dans `/backup/scripts/` si nécessaire

### 7.3 Décision 3 : Généralisation aux 3 Lambdas V2 ?

**Recommandation** : Oui, mais par étapes
1. Valider sur `normalize_score_v2` d'abord
2. Appliquer à `ingest_v2` 
3. Appliquer à `newsletter_v2` (quand elle sera créée)

### 7.4 Décision 4 : Niveau de Priorité ?

**Recommandation** : Priorité HAUTE
- Risque de régression architecturale si on attend
- Process actuel non-maintenable à moyen terme
- Exemple négatif pour les autres développeurs

---

## 8. Conclusion et Prochaines Étapes

### 8.1 Verdict Global

Le déploiement actuel de `normalize_score_v2` **fonctionne mais viole les règles d'hygiène V4**. Les scripts de fix créent une dette technique et un risque de régression architecturale.

### 8.2 Action Recommandée

**Passage immédiat aux Lambda Layers** selon le plan en 8 étapes pour :
- Respecter les règles d'hygiène V4
- Créer un process de build standard et maintenable  
- Préparer la réutilisation pour les autres Lambdas V2

### 8.3 Critères de Succès

- ✅ Handler `normalize_score_v2` <1MB
- ✅ 2 Lambda Layers créés et fonctionnels
- ✅ Scripts de fix supprimés
- ✅ Process de build documenté et reproductible
- ✅ Performance maintenue ou améliorée
- ✅ Conformité totale aux règles V4

**Prêt pour l'exécution du plan de remise au carré.**