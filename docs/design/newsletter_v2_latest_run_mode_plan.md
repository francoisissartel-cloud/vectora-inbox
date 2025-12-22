# Plan Correctif Newsletter V2 - Mode "Latest Run Only"

**Date :** 21 décembre 2025  
**Objectif :** Modifier la Lambda newsletter-v2 pour utiliser uniquement le dernier run curated  
**Justification :** Cohérence workflow par période de recherche  
**Statut :** Plan correctif - Implémentation immédiate  

---

## Problème Identifié

### Comportement Actuel (Problématique)
- **Période glissante** : Newsletter lit 30 jours de données curated
- **Volume imprévisible** : 45 items (3 jours × 15) au lieu de 15 items attendus
- **Incohérence workflow** : Mélange de runs différents
- **Performance dégradée** : 30 appels S3 au lieu de 1

### Comportement Souhaité (Solution)
- **Latest run only** : Newsletter lit uniquement le dossier target_date
- **Volume prévisible** : 15 items par run (cohérent avec normalize-score-v2)
- **Cohérence parfaite** : Newsletter = résultat du dernier run
- **Performance optimisée** : 1 seul appel S3

---

## Plan d'Implémentation

### Phase 1 : Configuration Client (5 min)

**Objectif :** Ajouter le paramètre de contrôle dans la config client

**Fichier :** `client-config-examples/lai_weekly_v4.yaml`

**Modification :**
```yaml
pipeline:
  newsletter_mode: "latest_run_only"  # Nouveau paramètre
  default_period_days: 30  # Ignoré en mode latest_run_only
```

### Phase 2 : Fonction S3 Optimisée (10 min)

**Objectif :** Créer une fonction de lecture single-date optimisée

**Fichier :** `src_v2/vectora_core/shared/s3_io.py`

**Nouvelle fonction :**
```python
def load_curated_items_single_date(client_id: str, data_bucket: str, target_date: str) -> List[Dict]:
    """
    Charge les items curated pour une date unique (mode latest run).
    
    Args:
        client_id: Identifiant du client
        data_bucket: Bucket de données
        target_date: Date cible (YYYY-MM-DD)
    
    Returns:
        Liste des items curated pour cette date uniquement
    """
```

### Phase 3 : Logique Newsletter Adaptée (10 min)

**Objectif :** Modifier la logique principale pour supporter les deux modes

**Fichier :** `src_v2/vectora_core/newsletter/__init__.py`

**Modification :**
```python
def run_newsletter_for_client(client_id, env_vars, target_date=None, force_regenerate=False):
    # Déterminer le mode de lecture
    newsletter_mode = client_config.get('pipeline', {}).get('newsletter_mode', 'period_based')
    
    if newsletter_mode == 'latest_run_only':
        # Mode cohérent : un seul dossier
        curated_items = s3_io.load_curated_items_single_date(
            client_id, env_vars["DATA_BUCKET"], target_date
        )
    else:
        # Mode legacy : période glissante (rétrocompatibilité)
        curated_items = s3_io.load_curated_items(
            client_id, env_vars["DATA_BUCKET"], from_date, target_date
        )
```

### Phase 4 : Tests et Validation (10 min)

**Objectif :** Valider le nouveau comportement

**Actions :**
1. Test avec mode `latest_run_only`
2. Vérification volume items (15 au lieu de 45)
3. Test rétrocompatibilité mode legacy
4. Validation performance (1 appel S3)

---

## Critères de Succès

### Métriques Attendues

**Avant (mode période) :**
- Items chargés : 45 (3 jours × 15)
- Appels S3 : 30 (scan 30 jours)
- Temps chargement : ~2-3 secondes
- Efficacité sélection : 29% (13/45)

**Après (mode latest run) :**
- Items chargés : 15 (1 jour × 15)
- Appels S3 : 1 (lecture directe)
- Temps chargement : ~0.2 secondes
- Efficacité sélection : 60-80% (9-12/15)

### Validation Fonctionnelle

- ✅ Newsletter générée avec items du target_date uniquement
- ✅ Volume prévisible et cohérent
- ✅ Performance améliorée (10x plus rapide)
- ✅ Rétrocompatibilité préservée
- ✅ Pas de régression qualité

---

## Avantages Business

### Cohérence Workflow
- **Traçabilité parfaite** : Newsletter du 21/12 = Items curated du 21/12
- **Prévisibilité** : Volume constant par newsletter
- **Debugging facilité** : Correspondance 1:1 entre runs

### Performance
- **Génération 10x plus rapide** : 1 appel S3 vs 30
- **Coûts Bedrock prévisibles** : Volume constant d'items
- **Moins de charge AWS** : Réduction drastique des appels S3

### Qualité
- **Signal plus fort** : Items récents et cohérents
- **Moins de bruit** : Pas de mélange entre runs
- **Efficacité sélection améliorée** : 60-80% vs 29%

---

## Risques et Mitigations

### Risque : Volume insuffisant
- **Problème :** 15 items peuvent être insuffisants pour certaines sections
- **Mitigation :** Ajuster `max_items_total` et `max_items` par section

### Risque : Régression rétrocompatibilité
- **Problème :** Clients existants avec mode période
- **Mitigation :** Mode legacy préservé par défaut

### Risque : Dossier target_date vide
- **Problème :** Pas d'items pour la date demandée
- **Mitigation :** Gestion d'erreur gracieuse + fallback optionnel

---

## Timeline d'Exécution

**Total estimé :** 35 minutes

1. **Phase 1** (5 min) : Modification config lai_weekly_v4.yaml
2. **Phase 2** (10 min) : Implémentation load_curated_items_single_date()
3. **Phase 3** (10 min) : Modification logique newsletter principale
4. **Phase 4** (10 min) : Tests et validation

**Prêt pour déploiement :** Immédiat après validation

---

## Conclusion

Cette modification aligne parfaitement la Lambda newsletter-v2 avec les principes Vectora-Inbox :
- **Workflow atomique** par run
- **Performance optimisée**
- **Coûts prévisibles**
- **Qualité supérieure**

Le mode "Latest Run Only" transforme la newsletter d'un agrégateur de période en un **générateur cohérent par run**, respectant l'architecture pipeline de Vectora-Inbox.

---

*Plan Correctif Newsletter V2 - Mode Latest Run*  
*Prêt pour exécution immédiate*