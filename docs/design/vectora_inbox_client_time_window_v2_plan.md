# Vectora Inbox - Plan de design pour la fenêtre temporelle client v2

**Date :** 2024-12-19  
**Objectif :** Définir la configuration de la fenêtre temporelle au niveau client_config v2

## 🎯 Objectif métier

Permettre à chaque client de définir sa fenêtre temporelle par défaut dans sa configuration, tout en gardant la possibilité d'override via le payload Lambda.

**Exemple concret :** LAI Weekly veut une fenêtre de 30 jours par défaut, sans avoir à modifier les scripts ou payloads.

## 📋 Spécification technique

### 1. Structure dans client_config v2

Ajout d'une nouvelle section `pipeline` dans le client_config :

```yaml
# ============================================================================
# CONFIGURATION DU PIPELINE
# ============================================================================
# Paramètres généraux du pipeline d'ingestion et de génération

pipeline:
  # Fenêtre temporelle par défaut (en jours)
  # Utilisée si period_days n'est pas fourni dans le payload Lambda
  default_period_days: 30
  
  # Documentation
  notes: "Fenêtre de 30 jours adaptée au cycle LAI (développement long)"
```

### 2. Hiérarchie de priorité

**Ordre de résolution (du plus prioritaire au moins prioritaire) :**

1. **Payload Lambda explicite :** `event["period_days"]` → Override absolu
2. **Configuration client :** `client_config.pipeline.default_period_days` → Valeur par défaut du client
3. **Fallback global :** 7 jours → Sécurité si aucune config

### 3. Logique d'implémentation

#### Fonction de résolution
```python
def resolve_period_days(
    payload_period_days: Optional[int],
    client_config: Dict[str, Any]
) -> int:
    """
    Résout la période à utiliser selon la hiérarchie de priorité.
    
    Returns:
        int: Nombre de jours à utiliser
    """
    # 1. Priorité au payload
    if payload_period_days is not None:
        logger.info(f"Utilisation period_days du payload : {payload_period_days}")
        return payload_period_days
    
    # 2. Configuration client
    client_period = client_config.get('pipeline', {}).get('default_period_days')
    if client_period is not None:
        logger.info(f"Utilisation default_period_days du client : {client_period}")
        return client_period
    
    # 3. Fallback global
    logger.info("Utilisation du fallback global : 7 jours")
    return 7
```

#### Points d'intégration
- **`run_ingest_normalize_for_client()`** : Résoudre avant l'appel aux modules d'ingestion
- **`run_engine_for_client()`** : Résoudre avant l'appel à `date_utils.compute_date_range()`

### 4. Mise à jour des configurations

#### Template v2 (`client_template_v2.yaml`)
```yaml
pipeline:
  # Fenêtre temporelle par défaut pour ce client
  # Valeurs typiques : 7 (hebdomadaire), 14 (bi-hebdomadaire), 30 (mensuel)
  default_period_days: 7
  
  notes: "Ajustez selon la fréquence de votre newsletter et la dynamique de votre secteur"
```

#### LAI Weekly v2 (`lai_weekly_v2.yaml`)
```yaml
pipeline:
  # Fenêtre de 30 jours adaptée au cycle LAI
  # Les développements LAI sont longs, nécessitent une fenêtre plus large
  default_period_days: 30
  
  notes: "Fenêtre étendue pour capturer les signaux LAI sur cycle long"
```

## 🧪 Cas de test

### Test 1 : Override payload
```json
{"client_id": "lai_weekly_v2", "period_days": 7}
```
**Attendu :** 7 jours (override du payload)

### Test 2 : Configuration client
```json
{"client_id": "lai_weekly_v2"}
```
**Attendu :** 30 jours (depuis client_config.pipeline.default_period_days)

### Test 3 : Fallback global
```json
{"client_id": "client_sans_config"}
```
**Attendu :** 7 jours (fallback si pas de config)

### Test 4 : Compatibilité ascendante
```json
{"client_id": "lai_weekly", "period_days": 14}
```
**Attendu :** 14 jours (ancien client, comportement inchangé)

## 🔄 Migration et compatibilité

### Clients existants
- **Aucun impact :** Les clients v1 continuent de fonctionner
- **Fallback préservé :** 7 jours si pas de configuration
- **Scripts existants :** Continuent de fonctionner avec period_days explicite

### Nouveaux clients
- **Template v2 :** Inclut la section pipeline par défaut
- **Documentation :** Guide pour choisir la bonne valeur
- **Validation :** Vérification que la valeur est cohérente (> 0, < 365)

## 📊 Impact sur les composants

### Composants modifiés
- **`vectora_core/__init__.py`** : Ajout de la logique de résolution
- **`client_template_v2.yaml`** : Ajout de la section pipeline
- **`lai_weekly_v2.yaml`** : Configuration spécifique 30 jours

### Composants inchangés
- **Handlers Lambda** : Aucune modification
- **`date_utils.py`** : Logique existante préservée
- **Scripts existants** : Fonctionnent sans modification

## 🚀 Plan de déploiement

### Phase 1 : Implémentation locale
1. Ajouter la fonction `resolve_period_days()`
2. Intégrer dans les fonctions orchestrales
3. Mettre à jour les configurations client

### Phase 2 : Tests locaux
1. Tests unitaires de la fonction de résolution
2. Tests d'intégration avec différents clients
3. Validation des cas d'usage

### Phase 3 : Déploiement AWS DEV
1. Sync des configurations vers S3
2. Update des Lambdas
3. Tests end-to-end

### Phase 4 : Validation
1. Tests avec lai_weekly_v2 (30 jours)
2. Tests d'override (7 jours)
3. Validation des logs et métriques

## 📝 Documentation utilisateur

### Pour les développeurs
```yaml
# Configuration de la fenêtre temporelle
pipeline:
  default_period_days: 30  # Nombre de jours par défaut
```

### Pour les utilisateurs métier
- **7 jours :** Newsletter hebdomadaire, secteur dynamique
- **14 jours :** Newsletter bi-hebdomadaire, secteur modéré
- **30 jours :** Newsletter mensuelle, secteur à cycle long (ex: LAI)

---

**Conclusion :** Cette approche offre la flexibilité demandée tout en préservant la compatibilité et la simplicité d'usage.