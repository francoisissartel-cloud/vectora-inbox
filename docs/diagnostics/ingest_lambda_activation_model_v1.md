# Diagnostic : Modèle d'activation Lambda ingest V1

**Date** : 2025-01-15  
**Version analysée** : V1 (src/ actuel)  
**Objectif** : Diagnostiquer l'écart entre le modèle d'activation actuel et le modèle cible "scan des client_config actifs"

---

## 1. Résumé exécutif

La Lambda ingest V1 actuelle (`vectora-inbox-ingest-normalize-dev`) **ne peut PAS fonctionner avec un event vide `{}`**. Elle requiert obligatoirement un `client_id` dans l'event d'entrée et ne possède **aucun mécanisme de découverte automatique des clients actifs**.

**Points clés :**
- **Dépendance forte au payload** : `client_id` obligatoire dans l'event
- **Pas de scan des client_config** : aucun code pour parcourir les configs et filtrer sur `active: true`
- **Pas de champ `active`** : le template client_config ne définit pas ce champ
- **Modèle 1-to-1** : une invocation = un client traité
- **Écart majeur** avec le modèle cible qui prévoit un déclenchement sans payload pour traiter tous les clients actifs

Le modèle "scan des client_config actifs" n'est **pas implémenté** dans la V1 actuelle.

---

## 2. Chemin de code et ressources analysées

### Fichiers principaux analysés

**Handlers Lambda :**
- `src/lambdas/ingest_normalize/handler.py` : Handler principal ingest+normalize
- `src/lambdas/engine/handler.py` : Handler engine (matching+scoring+newsletter)

**Modules vectora_core :**
- `src/vectora_core/__init__.py` : Fonctions d'orchestration `run_ingest_normalize_for_client()` et `run_engine_for_client()`
- `src/vectora_core/config/loader.py` : Chargement des configurations depuis S3

**Configurations client :**
- `client-config-examples/lai_weekly_v3.yaml` : Config client MVP actuel
- `client-config-examples/client_config_template.yaml` : Template générique

**Scripts de test :**
- `scripts/events/test_lai_weekly_minimal.json` : Event minimal avec `client_id`
- `scripts/events/test_lai_weekly_full.json` : Event complet avec `client_id`

**Documents de référence :**
- `.q-context/src_lambda_hygiene_v4.md` : Règles d'hygiène et bonnes pratiques
- `contracts/lambdas/ingest_v2.md` : Contrat métier pour la V2 (modèle cible)

### Chemins S3 / canonical utilisés

- **Client configs** : `s3://vectora-inbox-config-dev/clients/{client_id}.yaml`
- **Canonical scopes** : `s3://vectora-inbox-config-dev/canonical/scopes/*.yaml`
- **Source catalog** : `s3://vectora-inbox-config-dev/canonical/sources/source_catalog.yaml`
- **Données ingérées** : `s3://vectora-inbox-data-dev/normalized/{client_id}/{YYYY}/{MM}/{DD}/items.json`

---

## 3. Modèle d'activation actuel

### Signature du handler

**Handler ingest** : `src/lambdas/ingest_normalize/handler.py`
```python
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    client_id = event.get("client_id")
    if not client_id:
        return {"statusCode": 400, "body": {"error": "ConfigurationError", 
                "message": "Le paramètre 'client_id' est obligatoire"}}
```

**Champs de l'event effectivement utilisés :**
- `client_id` (obligatoire) : Identifiant du client à traiter
- `sources` (optionnel) : Liste des sources à traiter (surcharge la config)
- `period_days` (optionnel) : Fenêtre temporelle (surcharge la config)
- `from_date` / `to_date` (optionnel) : Dates explicites

### Découverte des client_config

**Mécanisme actuel :**
1. La Lambda reçoit un `client_id` dans l'event
2. Elle charge la config spécifique : `loader.load_client_config(client_id, config_bucket)`
3. Elle traite uniquement ce client

**Pas de scan des configs :**
- Aucun code pour lister les fichiers dans `s3://vectora-inbox-config-dev/clients/`
- Aucun filtrage sur un champ `active: true`
- Aucune boucle pour traiter plusieurs clients

### Event minimal nécessaire

**Pour lancer l'ingest du client MVP actuel :**
```json
{
  "client_id": "lai_weekly_v3"
}
```

**Un event vide `{}` est impossible** car le handler retourne immédiatement une erreur 400.

### Dépendances fortes au payload

- **`client_id` obligatoire** : Échec immédiat si absent
- **Pas de fallback** : Aucun mécanisme de découverte automatique
- **Modèle 1-to-1** : Une invocation Lambda = un client traité

---

## 4. Écart vs modèle cible

### Modèle cible (selon contrat ingest_v2.md et règles d'hygiène)

**Vision :**
1. **Event vide `{}` supporté** : Déclenchement par EventBridge sans payload
2. **Scan automatique** : Parcourir tous les client_config dans S3
3. **Filtrage sur `active: true`** : Traiter uniquement les clients actifs
4. **Boucle multi-clients** : Une invocation peut traiter plusieurs clients
5. **Event avec overrides optionnel** : `{"client_id": "...", "dry_run": true}` pour forcer un client spécifique

### Implémentation V1 actuelle

**Réalité :**
1. **Event vide impossible** : Erreur 400 immédiate
2. **Pas de scan** : Attend un `client_id` fourni
3. **Pas de champ `active`** : Non défini dans le template client_config
4. **Modèle 1-to-1** : Une invocation = un client
5. **`client_id` toujours obligatoire** : Même pour les overrides

### Points de divergence principaux

| Aspect | Modèle cible | V1 actuelle | Écart |
|--------|--------------|-------------|-------|
| Event vide `{}` | ✅ Supporté | ❌ Erreur 400 | **MAJEUR** |
| Scan client_config | ✅ Automatique | ❌ Inexistant | **MAJEUR** |
| Champ `active` | ✅ Requis | ❌ Absent | **MAJEUR** |
| Multi-clients | ✅ Une invocation → N clients | ❌ 1-to-1 | **MAJEUR** |
| Découverte auto | ✅ Pilotée par config | ❌ Pilotée par event | **MAJEUR** |

---

## 5. Recommandations de patchs (sans les appliquer)

### Option A : Patch minimal pour event vide

**Objectif** : Rendre l'event optionnel et scanner les clients actifs

**Modifications :**
1. **Handler** (`src/lambdas/ingest_normalize/handler.py`) :
   - Rendre `client_id` optionnel
   - Si absent, appeler une nouvelle fonction `discover_active_clients()`
   - Boucler sur les clients découverts

2. **Config loader** (`src/vectora_core/config/loader.py`) :
   - Ajouter `list_client_configs(config_bucket)` pour scanner S3
   - Ajouter `filter_active_clients(client_configs)` pour filtrer sur `active: true`

3. **Template client_config** :
   - Ajouter le champ `active: true/false` dans la section `client_profile`

4. **Client MVP** (`client-config-examples/lai_weekly_v3.yaml`) :
   - Ajouter `active: true`

**Fichiers concernés :**
- `src/lambdas/ingest_normalize/handler.py` (modification mineure)
- `src/vectora_core/config/loader.py` (ajout 2 fonctions)
- `client-config-examples/client_config_template.yaml` (ajout champ)
- `client-config-examples/lai_weekly_v3.yaml` (ajout champ)

**Respect des règles d'hygiène V4 :**
- ✅ **Simplicité** : Patch minimal, pas de sur-architecture
- ✅ **Générique** : Piloté par config, pas de logique hardcodée
- ✅ **Pas d'usine à gaz** : Réutilise les modules existants
- ✅ **Layers** : Logique dans vectora_core, handler minimal

**Impact :** Faible, rétrocompatible (si `client_id` fourni, comportement inchangé)

### Option B : Refactor structuré pour design générique

**Objectif** : Aligner complètement sur le design piloté par `client_config + canonical`

**Modifications :**
1. **Orchestration** (`src/vectora_core/__init__.py`) :
   - Créer `run_ingest_for_all_active_clients()` 
   - Refactorer `run_ingest_normalize_for_client()` pour séparer ingest et normalize
   - Ajouter gestion des erreurs par client (un échec ne bloque pas les autres)

2. **Config management** :
   - Ajouter cache des client_configs pour éviter les re-lectures S3
   - Ajouter validation des configs (champs obligatoires, cohérence)
   - Ajouter métriques par client (succès/échec, durée, items traités)

3. **Event handling** :
   - Supporter les patterns : `{}`, `{"dry_run": true}`, `{"client_id": "specific"}`
   - Ajouter logging structuré par client
   - Ajouter mode debug avec statistiques détaillées

**Fichiers concernés :**
- `src/vectora_core/__init__.py` (refactor majeur)
- `src/vectora_core/config/loader.py` (ajout cache et validation)
- `src/lambdas/ingest_normalize/handler.py` (simplification)
- Tous les client_config (ajout champ `active`)

**Respect des règles d'hygiène V4 :**
- ✅ **Générique** : Aucune logique client-specific hardcodée
- ✅ **Config-driven** : Tout piloté par client_config et canonical
- ✅ **Observabilité** : Métriques et logs par client
- ⚠️ **Complexité** : Plus de code, mais bien structuré

**Impact :** Modéré, nécessite tests approfondis

### Option C : Migration vers V2 (contrat ingest_v2.md)

**Objectif** : Basculer vers l'architecture 3 Lambdas V2 avec contrats métier

**Modifications :**
1. **Nouvelle Lambda ingest** (`src_v2/lambdas/ingest/`) :
   - Handler dédié uniquement à l'ingestion (pas de normalisation)
   - Support natif du scan des clients actifs
   - Respect strict du contrat `ingest_v2.md`

2. **Séparation ingest/normalize** :
   - Lambda ingest → S3 `ingested/`
   - Lambda normalize-score → S3 `normalized/`
   - Chaînage via EventBridge ou Step Functions

3. **Architecture V2 complète** :
   - Utiliser `src_v2/` comme base (déjà validé selon les règles V4)
   - 3 Lambdas séparées : ingest, normalize-score, newsletter
   - Déploiements indépendants

**Fichiers concernés :**
- Nouveau : `src_v2/lambdas/ingest/handler.py`
- Nouveau : `src_v2/vectora_core/ingest/__init__.py`
- Migration : Tous les client_config vers le nouveau format
- Infra : Nouvelles stacks CloudFormation

**Respect des règles d'hygiène V4 :**
- ✅ **Architecture V2** : Conforme à `src_v2/` validé
- ✅ **Séparation des responsabilités** : 3 Lambdas focalisées
- ✅ **Contrats métier** : Respect strict des spécifications
- ✅ **Évolutivité** : Base solide pour futures fonctionnalités

**Impact :** Majeur, nécessite migration complète mais apporte une base solide

---

## 6. Conclusion

La Lambda ingest V1 actuelle est **incompatible** avec le modèle d'activation cible. Elle nécessite des modifications pour supporter :

1. **Event vide `{}`** avec découverte automatique des clients
2. **Champ `active`** dans les client_config
3. **Scan S3** pour lister les configurations disponibles
4. **Boucle multi-clients** dans une seule invocation

**Recommandation** : Commencer par l'**Option A (patch minimal)** pour valider le concept, puis évoluer vers l'**Option C (V2)** pour une architecture pérenne.

L'Option A permet de débloquer rapidement le cas d'usage "déclenchement sans payload" tout en préservant la compatibilité existante.