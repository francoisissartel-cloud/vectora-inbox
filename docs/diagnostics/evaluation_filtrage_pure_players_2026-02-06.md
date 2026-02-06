# Évaluation : Améliorer Filtrage Pure Players LAI

**Date** : 2026-02-06  
**Objectif** : Filtrer le bruit évident (conférences, rapports financiers, corporate) même pour les pure players LAI

---

## 🔍 SITUATION ACTUELLE

### Code actuel (ligne 127-145)

```python
if is_lai_pure_player:
    logger.info(f"Pure player LAI détecté : {company_id} - ingestion large avec exclusions minimales")
    filtered_items = []
    
    for item in items:
        title = item.get('title', '').lower()
        content = item.get('content', '').lower()
        text = f"{title} {content}"
        
        # Exclure le bruit évident
        if _contains_exclusion_keywords(text):  # ← DÉJÀ ACTIF !
            logger.debug(f"Item corporate exclu (bruit) : {item.get('title', '')[:50]}...")
            continue
        
        filtered_items.append(item)
```

### Fonction `_contains_exclusion_keywords()` (ligne 207-217)

```python
def _contains_exclusion_keywords(text: str) -> bool:
    text_lower = text.lower()
    exclusion_terms = _get_exclusion_terms()  # Charge depuis S3
    
    for keyword in exclusion_terms:
        if keyword.lower() in text_lower:
            logger.debug(f"Exclusion détectée: '{keyword}' dans texte")
            return True
    
    return False
```

### Fonction `_get_exclusion_terms()` (ligne 24-35)

```python
def _get_exclusion_terms() -> List[str]:
    if not _exclusion_scopes_cache:
        return EXCLUSION_KEYWORDS  # Fallback hardcodé
    
    # Combine SEULEMENT 4 scopes:
    terms = []
    for scope_name in ['hr_content', 'financial_generic', 
                       'hr_recruitment_terms', 'financial_reporting_terms']:
        scope_terms = _exclusion_scopes_cache.get(scope_name, [])
        terms.extend(scope_terms)
    
    return terms if terms else EXCLUSION_KEYWORDS
```

---

## ✅ DÉCOUVERTE IMPORTANTE

**LE FILTRAGE EST DÉJÀ ACTIF POUR LES PURE PLAYERS !**

Le code appelle `_contains_exclusion_keywords(text)` qui :
1. Charge les scopes depuis S3 ✓
2. Combine 4 scopes : `hr_content`, `financial_generic`, `hr_recruitment_terms`, `financial_reporting_terms` ✓
3. Fait un substring match simple : `keyword.lower() in text_lower` ✓
4. Retourne `True` si match → Item EXCLU ✓

**Le problème n'est PAS le code, c'est les KEYWORDS !**

---

## 📊 ÉVALUATION DES OPTIONS

### Option 1 : Enrichir les 4 scopes utilisés (CANONICAL SEULEMENT)

**Action** :
- Ajouter keywords dans `hr_content`, `financial_generic`, `hr_recruitment_terms`, `financial_reporting_terms`
- Keywords à ajouter :
  - Conférences : "BIO International Convention", "Bio Europe Spring", "TIDES Asia", "booth", "register now"
  - Rapports financiers : "publishes interim report", "financial calendar", "consolidated half-year"
  - Corporate : "chief strategy officer", "chief financial officer", "index inclusion", "MSCI"

**Avantages** :
- ✅ Pas de modification code
- ✅ Déploiement immédiat (upload S3)
- ✅ Rollback facile
- ✅ Conforme Q context

**Inconvénients** :
- ⚠️ Matching simple (substring) peut avoir faux positifs
- ⚠️ Pas de patterns regex
- ⚠️ Pas de logique conditionnelle

**Faisabilité** : ✅ IMMÉDIATE  
**Risque** : Très faible  
**Impact estimé** : 7-10 items filtrés sur 17 (40-60%)

---

### Option 2 : Ajouter scopes dans `_get_exclusion_terms()` (CODE MINIMAL)

**Action** :
- Modifier ligne 30 pour inclure plus de scopes :
```python
for scope_name in ['hr_content', 'financial_generic', 
                   'hr_recruitment_terms', 'financial_reporting_terms',
                   'event_generic', 'esg_generic', 'corporate_noise_terms']:  # ← AJOUT
```

**Avantages** :
- ✅ Modification code MINIMALE (1 ligne)
- ✅ Permet d'utiliser TOUS les scopes de `exclusion_scopes.yaml`
- ✅ Pas de duplication de keywords

**Inconvénients** :
- ❌ Nécessite modification code
- ❌ Nécessite rebuild + redeploy
- ❌ Test requis

**Faisabilité** : ✅ FACILE (1 ligne)  
**Risque** : Faible  
**Impact estimé** : 10-14 items filtrés sur 17 (60-80%)

---

### Option 3 : Ajouter logique conditionnelle (CODE AVANCÉ)

**Action** :
- Modifier `_contains_exclusion_keywords()` pour supporter patterns regex
- Ajouter logique `exclusion_logic` (ex: "keyword_match AND no_trademark")

**Avantages** :
- ✅ Filtrage intelligent
- ✅ Moins de faux positifs

**Inconvénients** :
- ❌ Modification code importante
- ❌ Complexité accrue
- ❌ Tests approfondis requis

**Faisabilité** : ⚠️ COMPLEXE  
**Risque** : Moyen  
**Impact estimé** : 14-17 items filtrés sur 17 (80-100%)

---

## 🎯 RECOMMANDATION

### Approche hybride : Option 1 + Option 2

**Phase 1 (Immédiat)** : Enrichir les 4 scopes existants
- Ajouter keywords dans `hr_content`, `financial_generic`, etc.
- Upload S3
- Test immédiat
- **Durée** : 15 min
- **Risque** : Très faible

**Phase 2 (Si Phase 1 insuffisante)** : Ajouter scopes dans code
- Modifier ligne 30 de `ingestion_profiles.py`
- Rebuild + redeploy
- Test E2E
- **Durée** : 30 min
- **Risque** : Faible

---

## 📋 DÉCISION

**OPTION 1 SUFFIT** si les keywords sont bien choisis.

**Preuve** : Le code APPELLE DÉJÀ `_contains_exclusion_keywords()` pour les pure players. Il suffit d'enrichir les keywords.

**Test à faire** :
1. Ajouter keywords spécifiques dans les 4 scopes
2. Upload S3
3. Tester avec v24
4. Si <20 items → Succès
5. Si toujours 24 items → Passer à Option 2

---

## ✅ CONCLUSION

**Réponse** : **CANONICAL SEULEMENT** (Option 1)

Le code est DÉJÀ prêt. Il faut juste enrichir les keywords dans les 4 scopes utilisés :
- `hr_content`
- `financial_generic`
- `hr_recruitment_terms`
- `financial_reporting_terms`

**Pas besoin de toucher au code** pour un premier test.

Si insuffisant, modification code MINIMALE (1 ligne) pour ajouter plus de scopes.
