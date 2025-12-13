# Vectora Inbox - Diagnostic du comportement actuel de period_days

**Date :** 2024-12-19  
**Objectif :** Diagnostiquer comment la période temporelle (period_days) est gérée actuellement dans Vectora Inbox

## 🔍 Analyse du code existant

### 1. Points d'entrée Lambda

#### `src/lambdas/ingest_normalize/handler.py`
- **Paramètre accepté :** `period_days` (optionnel) dans l'événement Lambda
- **Transmission :** Passé directement à `run_ingest_normalize_for_client()`
- **Aucune valeur par défaut** dans le handler

#### `src/lambdas/engine/handler.py`
- **Paramètre accepté :** `period_days` (optionnel) dans l'événement Lambda
- **Transmission :** Passé directement à `run_engine_for_client()`
- **Aucune valeur par défaut** dans le handler

### 2. Fonctions orchestrales dans vectora_core

#### `src/vectora_core/__init__.py` - `run_ingest_normalize_for_client()`
- **Paramètre :** `period_days: Optional[int] = None`
- **Utilisation :** Aucune utilisation directe dans cette fonction
- **Transmission :** Pas de transmission explicite aux modules d'ingestion

#### `src/vectora_core/__init__.py` - `run_engine_for_client()`
- **Paramètre :** `period_days: Optional[int] = None`
- **Utilisation :** 
  - Passé à `date_utils.compute_date_range(period_days, from_date, to_date)`
  - Passé à `scorer.score_items()` pour le calcul de recency

### 3. Logique de calcul des dates

#### `src/vectora_core/utils/date_utils.py` - `compute_date_range()`
```python
def compute_date_range(
    period_days: Optional[int] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
) -> Tuple[str, str]:
```

**Logique actuelle :**
1. Si `from_date` ET `to_date` sont fournis → utiliser ces valeurs
2. Sinon, si `period_days` est fourni → calculer `from_date = aujourd'hui - period_days`
3. **Sinon → FALLBACK : 7 jours par défaut**

### 4. Scripts de test actuels

#### `scripts/test-engine-lai-weekly.ps1`
- **Valeur codée en dur :** `$PERIOD_DAYS = 7`
- **Payload :** `{"client_id": "lai_weekly", "period_days": 7}`

#### `scripts/test-ingest-normalize-profiles-dev.ps1`
- **Valeur codée en dur :** `$PERIOD_DAYS = 7`
- **Payload :** `{"client_id": "lai_weekly", "period_days": 7}`

## 📊 Comportement actuel documenté

### Cas d'usage 1 : Payload avec period_days
```json
{"client_id": "lai_weekly", "period_days": 30}
```
**Résultat :** Fenêtre de 30 jours (aujourd'hui - 30 jours → aujourd'hui)

### Cas d'usage 2 : Payload sans period_days
```json
{"client_id": "lai_weekly"}
```
**Résultat :** Fenêtre de 7 jours par défaut (fallback dans `date_utils.compute_date_range()`)

### Cas d'usage 3 : Payload avec dates explicites
```json
{"client_id": "lai_weekly", "from_date": "2024-12-01", "to_date": "2024-12-15"}
```
**Résultat :** Fenêtre explicite (period_days ignoré)

## ⚠️ Problèmes identifiés

### 1. Pas de source de vérité centralisée
- La période par défaut (7 jours) est codée en dur dans `date_utils.py`
- Aucune configuration au niveau client
- Impossible de personnaliser par client sans modifier le code

### 2. Incohérence dans les scripts
- Tous les scripts passent explicitement `period_days: 7`
- Masque le comportement par défaut réel
- Pas de test du fallback

### 3. Manque de flexibilité métier
- Pour LAI Weekly : besoin de 30 jours par défaut
- Actuellement : obligation de passer `period_days: 30` dans chaque payload
- Pas de moyen de configurer au niveau client

## 🎯 Objectifs de la refactorisation

1. **Source de vérité dans client_config :** Définir `default_period_days` dans la configuration client
2. **Hiérarchie de priorité :**
   - Payload `period_days` (override)
   - Client config `default_period_days`
   - Fallback global (7 jours)
3. **Compatibilité ascendante :** Maintenir le comportement existant
4. **Tests adaptés :** Scripts testant les deux modes (avec/sans override)

## 📋 Prochaines étapes

1. **Design v2 :** Proposer la structure dans client_config v2
2. **Implémentation :** Adapter le code pour lire la config client
3. **Tests :** Valider les différents cas d'usage
4. **Déploiement :** Mise à jour des Lambdas en DEV
5. **Validation :** Tests end-to-end sur AWS

---

**Conclusion :** Le système actuel fonctionne mais manque de flexibilité. La refactorisation permettra une configuration par client tout en maintenant la compatibilité.