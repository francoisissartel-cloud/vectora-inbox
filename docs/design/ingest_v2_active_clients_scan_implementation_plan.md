# Plan d'implémentation : Lambda ingest V2 avec scan des client_config actifs

**Date** : 2025-01-15  
**Objectif** : Implémenter le modèle d'activation cible dans `src_v2` pour supporter le déclenchement sans payload avec scan automatique des clients actifs  
**Base** : Architecture V2 existante dans `src_v2/` (conforme aux règles d'hygiène V4)  
**Périmètre** : Modification uniquement de `src_v2`, pas de modification de `src/` (V1)

---

## 1. Cadrage et analyse de l'existant

### 1.1 État actuel de src_v2

**Architecture V2 validée :**
- ✅ **3 Lambdas séparées** : ingest, normalize_score, newsletter
- ✅ **Handler minimal** : `src_v2/lambdas/ingest/handler.py` délègue tout à `vectora_core`
- ✅ **Vectora_core structuré** : modules shared + spécifiques par Lambda
- ✅ **Fonction d'orchestration** : `run_ingest_for_client()` dans `vectora_core/ingest/__init__.py`
- ✅ **Config loader** : `vectora_core/shared/config_loader.py` avec fonctions S3

**Écart identifié :**
- ❌ **`client_id` obligatoire** : Handler retourne erreur 400 si absent
- ❌ **Pas de scan S3** : Aucune fonction pour lister les client_config
- ❌ **Pas de champ `active`** : Template client_config ne le définit pas
- ❌ **Modèle 1-to-1** : Une invocation = un client traité

### 1.2 Modèle cible à atteindre

**Comportement souhaité :**
1. **Event vide `{}` supporté** : Déclenchement EventBridge sans payload
2. **Scan automatique** : Lister tous les `clients/*.yaml` dans S3
3. **Filtrage `active: true`** : Traiter uniquement les clients actifs
4. **Boucle multi-clients** : Une invocation peut traiter N clients
5. **Rétrocompatibilité** : `{"client_id": "specific"}` continue de fonctionner

### 1.3 Contraintes et règles

**Respect strict des règles d'hygiène V4 :**
- ✅ **Simplicité** : Pas de sur-architecture, réutiliser l'existant
- ✅ **Générique** : Piloté par config, pas de logique hardcodée
- ✅ **Architecture V2** : Maintenir la séparation 3 Lambdas
- ✅ **Handler minimal** : Logique dans vectora_core uniquement
- ✅ **Config-driven** : Tout comportement défini par client_config + canonical

**Contraintes techniques :**
- ✅ **Environnement AWS** : eu-west-3, profil rag-lai-prod, buckets existants
- ✅ **Rétrocompatibilité** : Pas de breaking change pour les events existants
- ✅ **Observabilité** : Logs structurés par client, métriques détaillées
- ✅ **Gestion d'erreurs** : Un échec client ne bloque pas les autres

---

## 2. Plan d'exécution par phases

### Phase 1 : Préparation et extension du config_loader (1-2h)

**Objectif** : Ajouter les fonctions de découverte des clients actifs

**Modifications :**

1. **Extension de `config_loader.py`** :
   ```python
   # Nouvelles fonctions à ajouter
   def list_client_configs(config_bucket: str) -> List[str]
   def load_all_client_configs(config_bucket: str) -> Dict[str, Dict[str, Any]]
   def filter_active_clients(client_configs: Dict[str, Dict[str, Any]]) -> List[str]
   ```

2. **Ajout du champ `active` dans les templates** :
   - `client-config-examples/client_config_template.yaml`
   - `client-config-examples/lai_weekly_v3.yaml`

**Fichiers modifiés :**
- `src_v2/vectora_core/shared/config_loader.py` (ajout 3 fonctions)
- `client-config-examples/client_config_template.yaml` (ajout champ)
- `client-config-examples/lai_weekly_v3.yaml` (ajout champ)

**Tests locaux Phase 1 :**
- Test unitaire des nouvelles fonctions config_loader
- Validation du chargement des configs avec champ `active`
- Test de filtrage sur `active: true/false`

**Critères de succès Phase 1 :**
- ✅ Fonctions de scan S3 opérationnelles
- ✅ Champ `active` présent dans les templates
- ✅ Tests unitaires passent
- ✅ Pas de régression sur les fonctions existantes

### Phase 2 : Extension de l'orchestration ingest (2-3h)

**Objectif** : Créer la fonction multi-clients dans `vectora_core/ingest`

**Modifications :**

1. **Nouvelle fonction d'orchestration** :
   ```python
   # Dans src_v2/vectora_core/ingest/__init__.py
   def run_ingest_for_active_clients(
       env_vars: Dict[str, Any],
       dry_run: bool = False,
       **kwargs
   ) -> Dict[str, Any]
   ```

2. **Gestion des erreurs par client** :
   - Un échec sur un client ne bloque pas les autres
   - Collecte des statistiques par client
   - Logs structurés avec client_id en contexte

3. **Métriques agrégées** :
   - Nombre de clients traités/échoués
   - Items totaux ingérés
   - Temps d'exécution par client et global

**Fichiers modifiés :**
- `src_v2/vectora_core/ingest/__init__.py` (ajout fonction + refactor)

**Tests locaux Phase 2 :**
- Test avec 1 client actif (cas nominal)
- Test avec 2+ clients actifs (cas multi-clients)
- Test avec 1 client actif + 1 inactif (filtrage)
- Test avec échec sur 1 client (isolation des erreurs)
- Test mode dry_run multi-clients

**Critères de succès Phase 2 :**
- ✅ Fonction multi-clients opérationnelle
- ✅ Gestion d'erreurs isolée par client
- ✅ Métriques agrégées correctes
- ✅ Tests locaux passent
- ✅ Rétrocompatibilité préservée

### Phase 3 : Modification du handler pour event optionnel (1h)

**Objectif** : Rendre `client_id` optionnel dans le handler

**Modifications :**

1. **Handler adapté** :
   ```python
   # Dans src_v2/lambdas/ingest/handler.py
   def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
       client_id = event.get("client_id")
       
       if client_id:
           # Mode single-client (existant)
           result = run_ingest_for_client(client_id=client_id, ...)
       else:
           # Mode multi-clients (nouveau)
           result = run_ingest_for_active_clients(...)
   ```

2. **Validation des paramètres** :
   - Event vide `{}` accepté
   - Paramètres globaux (dry_run, period_days) appliqués à tous les clients
   - Paramètres spécifiques (sources) ignorés en mode multi-clients

**Fichiers modifiés :**
- `src_v2/lambdas/ingest/handler.py` (modification logique de routage)

**Tests locaux Phase 3 :**
- Test event vide `{}`
- Test event avec `{"dry_run": true}`
- Test event avec `{"client_id": "specific"}` (rétrocompatibilité)
- Test event avec paramètres mixtes

**Critères de succès Phase 3 :**
- ✅ Event vide accepté sans erreur
- ✅ Routage correct single vs multi-clients
- ✅ Rétrocompatibilité totale
- ✅ Tests locaux passent

### Phase 4 : Tests d'intégration locaux (2-3h)

**Objectif** : Valider le workflow complet en local avec données réelles

**Scénarios de test :**

1. **Test E2E avec client MVP** :
   - Config `lai_weekly_v3.yaml` avec `active: true`
   - Event vide `{}`
   - Vérification ingestion complète

2. **Test multi-clients simulé** :
   - Créer `lai_weekly_v3_test.yaml` avec `active: false`
   - Vérifier filtrage correct

3. **Test de robustesse** :
   - Client avec config invalide
   - Client avec sources inaccessibles
   - Vérifier isolation des erreurs

4. **Test de performance** :
   - Mesurer temps d'exécution vs mode single-client
   - Vérifier pas de régression significative

**Outils de test :**
- Script Python local simulant l'invocation Lambda
- Données de test avec configs multiples
- Mocks S3 pour éviter les appels réels

**Métriques attendues :**
- ✅ Temps d'exécution < 2x le mode single-client
- ✅ Taux de succès > 95% sur clients valides
- ✅ Isolation complète des erreurs par client
- ✅ Logs structurés et exploitables

**Critères de succès Phase 4 :**
- ✅ Tous les scénarios de test passent
- ✅ Métriques dans les seuils acceptables
- ✅ Pas de régression fonctionnelle
- ✅ Logs et observabilité satisfaisants

### Phase 5 : Packaging et déploiement AWS (1-2h)

**Objectif** : Déployer la Lambda V2 modifiée vers AWS dev

**Prérequis :**
- ✅ Tous les tests locaux Phase 4 réussis
- ✅ Config `lai_weekly_v3.yaml` mise à jour avec `active: true`
- ✅ Validation manuelle du comportement attendu

**Étapes de déploiement :**

1. **Packaging de la Lambda** :
   - Utiliser les scripts existants de packaging V2
   - Vérifier taille < 50MB (conformité règles V4)
   - Créer le ZIP avec vectora_core + handler

2. **Déploiement vers dev** :
   ```bash
   aws lambda update-function-code \
     --function-name vectora-inbox-ingest-dev \
     --zip-file fileb://ingest-v2.zip \
     --profile rag-lai-prod --region eu-west-3
   ```

3. **Test de déploiement** :
   - Invocation avec event vide via CLI
   - Vérification des logs CloudWatch
   - Validation des données S3 générées

**Critères de succès Phase 5 :**
- ✅ Déploiement sans erreur
- ✅ Lambda répond correctement aux invocations
- ✅ Event vide `{}` fonctionne en AWS
- ✅ Données ingérées présentes dans S3

### Phase 6 : Tests de validation AWS et rapport final (1h)

**Objectif** : Valider le comportement en environnement AWS réel

**Tests de validation AWS :**

1. **Test event vide** :
   ```bash
   aws lambda invoke --function-name vectora-inbox-ingest-dev \
     --payload '{}' response.json \
     --profile rag-lai-prod --region eu-west-3
   ```

2. **Test rétrocompatibilité** :
   ```bash
   aws lambda invoke --function-name vectora-inbox-ingest-dev \
     --payload '{"client_id": "lai_weekly_v3"}' response.json \
     --profile rag-lai-prod --region eu-west-3
   ```

3. **Validation des données** :
   - Vérifier présence des items dans S3 `ingested/`
   - Comparer avec les résultats attendus des tests locaux
   - Valider les métriques dans CloudWatch

**Rapport final :**

Document de synthèse contenant :
- ✅ **Résumé des modifications** : Fonctions ajoutées, fichiers modifiés
- ✅ **Résultats des tests** : Locaux et AWS, métriques de performance
- ✅ **Validation du modèle cible** : Event vide, scan clients actifs, multi-clients
- ✅ **Impact et rétrocompatibilité** : Confirmation aucun breaking change
- ✅ **Recommandations** : Prochaines étapes, améliorations possibles

**Critères de succès Phase 6 :**
- ✅ Tests AWS réussis
- ✅ Comportement conforme au modèle cible
- ✅ Rapport final complet et documenté
- ✅ Validation par les parties prenantes

---

## 3. Livrables et fichiers modifiés

### 3.1 Fichiers de code modifiés

**Core modifications :**
- `src_v2/vectora_core/shared/config_loader.py` : +3 fonctions scan clients
- `src_v2/vectora_core/ingest/__init__.py` : +1 fonction multi-clients
- `src_v2/lambdas/ingest/handler.py` : Logique de routage event

**Configuration templates :**
- `client-config-examples/client_config_template.yaml` : +champ active
- `client-config-examples/lai_weekly_v3.yaml` : +active: true

### 3.2 Nouveaux fichiers de test

**Tests unitaires :**
- `tests/unit/test_config_loader_v2.py` : Tests des fonctions de scan
- `tests/unit/test_ingest_multi_clients.py` : Tests orchestration multi-clients

**Tests d'intégration :**
- `tests/integration/test_ingest_v2_active_scan.py` : Tests E2E complets

### 3.3 Documentation

**Plans et rapports :**
- `docs/design/ingest_v2_active_clients_scan_implementation_plan.md` : Ce document
- `docs/reports/ingest_v2_active_scan_implementation_report.md` : Rapport final

**Scripts de déploiement :**
- `scripts/deploy_ingest_v2_active_scan.py` : Script de packaging et déploiement

---

## 4. Estimation et planning

### 4.1 Estimation par phase

| Phase | Durée estimée | Complexité | Risque |
|-------|---------------|------------|--------|
| Phase 1 : Config loader | 1-2h | Faible | Faible |
| Phase 2 : Orchestration | 2-3h | Moyen | Moyen |
| Phase 3 : Handler | 1h | Faible | Faible |
| Phase 4 : Tests locaux | 2-3h | Moyen | Moyen |
| Phase 5 : Déploiement | 1-2h | Faible | Faible |
| Phase 6 : Validation | 1h | Faible | Faible |
| **Total** | **8-12h** | **Moyen** | **Faible** |

### 4.2 Points de validation

**Checkpoints obligatoires :**
- ✅ **Fin Phase 1** : Tests unitaires config_loader passent
- ✅ **Fin Phase 2** : Tests unitaires orchestration passent
- ✅ **Fin Phase 4** : Tests d'intégration locaux réussis
- ✅ **Fin Phase 5** : Déploiement AWS sans erreur
- ✅ **Fin Phase 6** : Validation complète du modèle cible

**Critères d'arrêt :**
- ❌ **Échec tests Phase 4** : Retour en Phase 2-3 pour correction
- ❌ **Échec déploiement Phase 5** : Investigation et correction
- ❌ **Régression fonctionnelle** : Rollback et analyse

---

## 5. Validation du respect des règles d'hygiène V4

### 5.1 Conformité architecture

- ✅ **Architecture 3 Lambdas V2** : Pas de modification de la séparation
- ✅ **Handler minimal** : Logique dans vectora_core uniquement
- ✅ **Modules shared vs spécifiques** : Nouvelles fonctions au bon endroit
- ✅ **Imports relatifs** : Respect des conventions V2

### 5.2 Conformité environnement AWS

- ✅ **Région eu-west-3** : Tous les déploiements dans la région de référence
- ✅ **Profil rag-lai-prod** : Utilisation exclusive du profil établi
- ✅ **Buckets existants** : Réutilisation des buckets vectora-inbox-*-dev
- ✅ **Conventions de nommage** : Respect des patterns établis

### 5.3 Conformité design générique

- ✅ **Config-driven** : Comportement piloté par client_config.active
- ✅ **Pas de logique hardcodée** : Aucun if client_id == "specific"
- ✅ **Générique** : Fonctionne pour tout client avec active: true
- ✅ **Évolutif** : Base solide pour futures fonctionnalités

---

## 6. Conclusion et prochaines étapes

### 6.1 Objectif de ce plan

Ce plan d'implémentation permet d'atteindre le **modèle d'activation cible** pour la Lambda ingest V2 :
- ✅ **Event vide `{}` supporté**
- ✅ **Scan automatique des client_config**
- ✅ **Filtrage sur `active: true`**
- ✅ **Boucle multi-clients**
- ✅ **Rétrocompatibilité totale**

### 6.2 Bénéfices attendus

**Opérationnels :**
- Déclenchement EventBridge sans payload complexe
- Gestion centralisée de l'activation des clients
- Réduction des erreurs de configuration manuelle

**Techniques :**
- Architecture V2 préservée et renforcée
- Base solide pour l'extension aux autres Lambdas (normalize_score, newsletter)
- Observabilité améliorée avec métriques par client

### 6.3 Prochaines étapes après implémentation

1. **Extension aux autres Lambdas** : Appliquer le même pattern à normalize_score et newsletter
2. **EventBridge automation** : Configurer les triggers automatiques
3. **Monitoring avancé** : Alertes sur échecs clients, métriques business
4. **Documentation utilisateur** : Guide d'activation/désactivation des clients

---

**Prêt pour exécution** : Ce plan est prêt à être exécuté en autonomie après validation et accord.