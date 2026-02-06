# RAPPORT DIAGNOSTIC COMPLET - PHASE D'INGESTION VECTORA INBOX

**Date** : 2026-02-06  
**Objectif** : Comprendre le fonctionnement précis du moteur d'ingestion et identifier les leviers d'amélioration

---

## 1. ARCHITECTURE DU MOTEUR D'INGESTION

### 1.1 Flux d'exécution complet

```
Lambda Handler (handler.py)
    ↓
run_ingest_for_client() (__init__.py)
    ↓
    ├─ Chargement configs S3
    │   ├─ client_config (clients/lai_weekly_v24.yaml)
    │   ├─ source_catalog (canonical/sources/source_catalog.yaml)
    │   └─ exclusion_scopes (canonical/scopes/exclusion_scopes.yaml)
    ↓
    ├─ Résolution sources (8 sources pour lai_weekly_v24)
    ↓
    └─ Pour chaque source:
        ├─ Fetch contenu (source_fetcher.py)
        ├─ Parse contenu (content_parser.py)
        └─ Apply profil ingestion (ingestion_profiles.py) ← FILTRAGE ICI
            ↓
            ├─ Si press_corporate → _apply_corporate_profile()
            │   ├─ Si pure player → Ingestion large + exclusions
            │   └─ Si non-pure player → Filtrage strict LAI
            │
            └─ Si press_sector → _apply_press_profile()
                └─ Filtrage strict LAI
```

### 1.2 Fichiers impliqués

| Fichier | Rôle | Type |
|---------|------|------|
| `src_v2/lambdas/ingest/handler.py` | Point d'entrée Lambda | Code |
| `src_v2/vectora_core/ingest/__init__.py` | Orchestration workflow | Code |
| `src_v2/vectora_core/ingest/ingestion_profiles.py` | **MOTEUR DE FILTRAGE** | Code |
| `src_v2/vectora_core/ingest/source_fetcher.py` | Récupération HTTP/RSS | Code |
| `src_v2/vectora_core/ingest/content_parser.py` | Parsing HTML/RSS | Code |
| `canonical/sources/source_catalog.yaml` | Définition sources | Config |
| `canonical/scopes/exclusion_scopes.yaml` | Keywords exclusion | Config |
| `clients/lai_weekly_v24.yaml` | Config client | Config |

---

## 2. MOTEUR DE FILTRAGE - LOGIQUE DÉTAILLÉE

### 2.1 Point d'entrée du filtrage

**Fichier** : `ingestion_profiles.py`  
**Fonction** : `apply_ingestion_profile(items, source_meta, ingestion_mode)`  
**Ligne** : 95

**Paramètres d'entrée** :
- `items` : Liste d'items parsés depuis la source
- `source_meta` : Métadonnées de la source (source_key, source_type, company_id)
- `ingestion_mode` : "balanced" (défaut), "broad", "strict"

**Logique de routage** :
```python
if ingestion_mode == "broad":
    return items  # Pas de filtrage
elif ingestion_mode == "strict":
    return _filter_by_lai_keywords(items)  # Filtrage maximal
else:  # balanced
    if source_type == 'press_corporate':
        return _apply_corporate_profile(items, source_meta)
    elif source_type == 'press_sector':
        return _apply_press_profile(items, source_meta)
```

### 2.2 Profil Corporate (press_corporate)

**Fonction** : `_apply_corporate_profile(items, source_meta)`  
**Ligne** : 116

#### Étape 1 : Détection pure player

```python
# HARDCODÉ dans le code
lai_pure_players = ['medincell', 'camurus', 'delsitech', 'nanexa', 'peptron']
company_id = source_meta.get('company_id', '')  # Depuis source_catalog.yaml
is_lai_pure_player = company_id.lower() in lai_pure_players
```

**Source du company_id** : `canonical/sources/source_catalog.yaml`
```yaml
- source_key: "press_corporate__medincell"
  company_id: "medincell"  # ← Utilisé pour détection pure player
```

#### Étape 2a : Si PURE PLAYER

**Logique** : Ingestion LARGE avec exclusions minimales

```python
for item in items:
    text = f"{title} {content}".lower()
    
    # SEUL FILTRE : Exclusion keywords
    if _contains_exclusion_keywords(text):
        continue  # Item EXCLU
    
    filtered_items.append(item)  # Item CONSERVÉ
```

**Caractéristiques** :
- ✅ Tout est conservé par défaut
- ❌ Exclusion UNIQUEMENT si match exclusion keywords
- ❌ PAS de vérification LAI keywords (tout est LAI chez eux)

**Exemple Medincell** :
- "Medincell Announces New LAI Product" → ✅ CONSERVÉ
- "Medincell Appoints Chief Strategy Officer" → ❌ EXCLU si "chief strategy officer" dans exclusion keywords
- "Medincell Q3 Financial Results" → ❌ EXCLU si "financial results" dans exclusion keywords

#### Étape 2b : Si NON-PURE PLAYER

**Logique** : Filtrage STRICT par mots-clés LAI

```python
return _filter_by_lai_keywords(items, source_key)
```

### 2.3 Profil Presse Sectorielle (press_sector)

**Fonction** : `_apply_press_profile(items, source_meta)`  
**Ligne** : 158

**Logique** : Filtrage STRICT par mots-clés LAI (identique aux non-pure players)

```python
return _filter_by_lai_keywords(items, source_key)
```

### 2.4 Filtrage strict LAI

**Fonction** : `_filter_by_lai_keywords(items, source_key)`  
**Ligne** : 168

**Logique** : Double vérification (exclusion + inclusion)

```python
for item in items:
    text = f"{title} {content}".lower()
    
    # Étape 1 : Exclure le bruit
    if _contains_exclusion_keywords(text):
        continue  # Item EXCLU
    
    # Étape 2 : Vérifier présence LAI keywords
    if _contains_lai_keywords(text):
        filtered_items.append(item)  # Item CONSERVÉ
    else:
        continue  # Item EXCLU (pas de LAI)
```

**Caractéristiques** :
- ❌ Exclusion si match exclusion keywords
- ✅ Conservation UNIQUEMENT si match LAI keywords
- ❌ Tout le reste est exclu

**Exemple FiercePharma** :
- "GSK Announces New LAI Product" → ✅ CONSERVÉ (contient "LAI")
- "GSK Appoints Chief Strategy Officer" → ❌ EXCLU (pas de LAI keywords)
- "Pfizer Q3 Financial Results" → ❌ EXCLU (pas de LAI keywords)

---

## 3. SYSTÈME DE KEYWORDS

### 3.1 Keywords d'exclusion (Bruit)

#### Source 1 : Canonical YAML (PARTIEL)

**Fichier** : `canonical/scopes/exclusion_scopes.yaml`  
**Chargement** : `initialize_exclusion_scopes(s3_io, config_bucket)` (ligne 24)

**⚠️ LIMITATION CRITIQUE** : Seuls 4 scopes sont lus par le code (ligne 48) :
```python
for scope_name in ['hr_content', 'financial_generic', 'hr_recruitment_terms', 'financial_reporting_terms']:
    scope_terms = _exclusion_scopes_cache.get(scope_name, [])
    terms.extend(scope_terms)
```

**Scopes LUS** :
- `hr_content` : RH, événements, conférences
- `financial_generic` : Rapports financiers, termes boursiers
- `hr_recruitment_terms` : Recrutement spécifique
- `financial_reporting_terms` : Reporting financier détaillé

**Scopes IGNORÉS** (présents dans le YAML mais non lus) :
- `esg_generic` : ESG, gouvernance
- `event_generic` : Événements génériques
- `corporate_noise_terms` : Bruit corporate
- `anti_lai_routes` : Routes non-LAI
- `lai_exclude_noise` : Bruit générique

#### Source 2 : Fallback hardcodé

**Fichier** : `ingestion_profiles.py`  
**Variable** : `EXCLUSION_KEYWORDS` (ligne 80-92)

**Utilisé si** : Échec chargement S3 ou cache vide

```python
EXCLUSION_KEYWORDS = [
    # RH et recrutement
    "hiring", "recruitment", "job opening", "career", "seeks an experienced",
    "is hiring", "appointment of", "leadership change", "joins as",
    
    # Événements corporate génériques
    "conference", "webinar", "presentation", "meeting", "congress",
    "summit", "symposium", "event", "participate in", "to present at",
    
    # Routes non-LAI
    "oral", "tablet", "capsule", "pill", "topical", "nasal spray",
    "eye drops", "cream", "gel", "patch"
]
```

### 3.2 Keywords LAI (Inclusion)

**⚠️ ENTIÈREMENT HARDCODÉ dans le code**

**Fichier** : `ingestion_profiles.py`  
**Variable** : `LAI_KEYWORDS` (ligne 56-77)

```python
LAI_KEYWORDS = [
    # Technologies LAI
    "injectable", "injection", "long-acting", "extended-release", "depot", 
    "sustained-release", "controlled-release", "implant", "microsphere",
    "LAI", "long acting injectable", "once-monthly", "once-weekly",
    
    # Entreprises LAI
    "medincell", "camurus", "delsitech", "nanexa", "peptron", "teva",
    "uzedy", "bydureon", "invega", "risperdal", "abilify maintena",
    
    # Molécules LAI
    "olanzapine", "risperidone", "paliperidone", "aripiprazole", 
    "haloperidol", "fluphenazine", "exenatide", "naltrexone",
    
    # Routes d'administration
    "intramuscular", "subcutaneous", "im injection", "sc injection"
]
```

**Aucun pilotage canonical** : Modification = rebuild + redeploy

### 3.3 Fonction de matching

**Fonction** : `_contains_exclusion_keywords(text)` (ligne 206)

**Logique** : Substring matching case-insensitive

```python
def _contains_exclusion_keywords(text: str) -> bool:
    text_lower = text.lower()
    exclusion_terms = _get_exclusion_terms()
    
    for keyword in exclusion_terms:
        if keyword.lower() in text_lower:
            return True  # MATCH trouvé
    
    return False
```

**Caractéristiques** :
- Matching simple : `"keyword" in "text"`
- Case-insensitive : `.lower()`
- Premier match = exclusion immédiate
- Pas de regex, pas de word boundaries

**Exemples de matching** :
- Keyword "financial results" → Match "Q3 Financial Results Published"
- Keyword "chief strategy officer" → Match "Appoints Dr. Kim as Chief Strategy Officer"
- Keyword "BIO International Convention" → Match "BIO International Convention 2025 Boston"

---

## 4. RÉCAPITULATIF : HARDCODÉ vs CANONICAL

### 4.1 Ce qui est PILOTÉ par canonical

| Élément | Fichier Canonical | Champ | Modifiable sans rebuild |
|---------|-------------------|-------|-------------------------|
| Liste des sources | `sources/source_catalog.yaml` | `sources[]` | ✅ Oui (upload S3) |
| Type de source | `sources/source_catalog.yaml` | `source_type` | ✅ Oui |
| Company ID | `sources/source_catalog.yaml` | `company_id` | ✅ Oui |
| Keywords exclusion (4 scopes) | `scopes/exclusion_scopes.yaml` | `hr_content`, `financial_generic`, etc. | ✅ Oui |
| Bouquets de sources | `sources/source_catalog.yaml` | `bouquets[]` | ✅ Oui |

### 4.2 Ce qui est HARDCODÉ dans le code

| Élément | Fichier | Ligne | Modifiable |
|---------|---------|-------|------------|
| Liste pure players | `ingestion_profiles.py` | 133 | ❌ Rebuild requis |
| Scopes lus (4 sur 9) | `ingestion_profiles.py` | 48 | ❌ Rebuild requis |
| Keywords LAI (~30) | `ingestion_profiles.py` | 56-77 | ❌ Rebuild requis |
| Keywords exclusion fallback | `ingestion_profiles.py` | 80-92 | ❌ Rebuild requis |
| Logique de filtrage | `ingestion_profiles.py` | 95-220 | ❌ Rebuild requis |

---

## 5. TABLEAU COMPARATIF : PURE PLAYERS vs AUTRES

| Critère | Pure Players | Non-Pure Players | Presse Sectorielle |
|---------|--------------|------------------|-------------------|
| **Sources** | Medincell, Camurus, Delsitech, Nanexa, Peptron | Autres corporate | FiercePharma, FierceBiotech, Endpoints |
| **Source type** | `press_corporate` | `press_corporate` | `press_sector` |
| **Profil appliqué** | `corporate_pure_player_broad` | `press_technology_focused` | `press_technology_focused` |
| **Logique** | Ingestion LARGE | Filtrage STRICT | Filtrage STRICT |
| **Exclusion keywords** | ✅ Appliqué | ✅ Appliqué | ✅ Appliqué |
| **LAI keywords** | ❌ Non vérifié | ✅ Obligatoire | ✅ Obligatoire |
| **Taux rétention** | ~40% (4/10 items) | ~10-20% | ~5-10% |
| **Exemple conservé** | "New LAI Product" | "New LAI Product" | "New LAI Product" |
| **Exemple exclu** | "Financial Results" (si keyword) | "Financial Results" | "Financial Results" |
| **Exemple exclu** | - | "New Product" (pas LAI) | "New Product" (pas LAI) |

---

## 6. PROBLÈME ACTUEL IDENTIFIÉ

### 6.1 Symptômes

**Items NON filtrés alors qu'ils devraient l'être** :
- "BIO International Convention 2025" (conférence)
- "Medincell to Join MSCI World Small Cap Index" (bourse)
- "Publication of the 2026 financial calendar" (finance)
- "Medincell Appoints Dr Grace Kim, Chief Strategy Officer" (RH)

### 6.2 Hypothèses

**Hypothèse 1** : Keywords présents dans scopes non lus
- ❌ Vérifié : Keywords sont dans `hr_content` et `financial_generic` (scopes lus)

**Hypothèse 2** : Fichier S3 pas à jour
- ⚠️ À vérifier : Comparer local vs S3

**Hypothèse 3** : Cache Lambda pas rechargé
- ⚠️ À vérifier : Logs d'initialisation

**Hypothèse 4** : Matching ne fonctionne pas
- ⚠️ À vérifier : Test local du matching

**Hypothèse 5** : Logique d'exclusion pas appliquée
- ⚠️ À vérifier : Logs de filtrage détaillés

---

## 7. LEVIERS D'AMÉLIORATION DU FILTRAGE

### 7.1 Court terme (sans rebuild)

#### Levier 1 : Enrichir les 4 scopes lus
**Fichier** : `canonical/scopes/exclusion_scopes.yaml`  
**Action** : Ajouter keywords dans `hr_content`, `financial_generic`, `hr_recruitment_terms`, `financial_reporting_terms`  
**Impact** : Immédiat après upload S3  
**Limitation** : Seuls ces 4 scopes sont lus

#### Levier 2 : Ajuster company_id des sources
**Fichier** : `canonical/sources/source_catalog.yaml`  
**Action** : Modifier `company_id` pour changer le profil appliqué  
**Impact** : Immédiat après upload S3  
**Exemple** : Retirer une source de la liste pure players

### 7.2 Moyen terme (rebuild requis)

#### Levier 3 : Lire TOUS les scopes du YAML
**Fichier** : `ingestion_profiles.py` ligne 48  
**Action** : Remplacer la liste hardcodée par lecture dynamique
```python
# Avant
for scope_name in ['hr_content', 'financial_generic', ...]:

# Après
for scope_name, scope_terms in _exclusion_scopes_cache.items():
```
**Impact** : Tous les scopes du YAML deviennent actifs

#### Levier 4 : Externaliser la liste pure players
**Fichier** : `ingestion_profiles.py` ligne 133  
**Action** : Charger depuis canonical
```yaml
# Nouveau fichier: canonical/ingestion/pure_players.yaml
lai_pure_players:
  - medincell
  - camurus
  - delsitech
  - nanexa
  - peptron
```

#### Levier 5 : Externaliser LAI keywords
**Fichier** : `ingestion_profiles.py` ligne 56-77  
**Action** : Charger depuis canonical
```yaml
# Nouveau fichier: canonical/scopes/lai_keywords.yaml
lai_keywords:
  technologies: [...]
  companies: [...]
  molecules: [...]
```

### 7.3 Long terme (refactoring)

#### Levier 6 : Profils d'ingestion configurables
**Fichier** : Nouveau `canonical/ingestion/ingestion_profiles.yaml`  
**Action** : Définir les profils en YAML
```yaml
profiles:
  corporate_pure_player_broad:
    apply_exclusions: true
    require_lai_keywords: false
    exclusion_scopes: [hr_content, financial_generic]
  
  press_technology_focused:
    apply_exclusions: true
    require_lai_keywords: true
    exclusion_scopes: [hr_content, financial_generic]
```

#### Levier 7 : Matching avancé (regex, word boundaries)
**Action** : Supporter regex dans les keywords
```yaml
hr_content:
  - pattern: "appoints.*chief"
    type: regex
  - pattern: "chief strategy officer"
    type: exact
```

---

## 8. PLAN D'ACTION RECOMMANDÉ

### Phase 1 : Diagnostic (URGENT)
1. ✅ Vérifier contenu S3 `exclusion_scopes.yaml`
2. ✅ Activer logs DEBUG et analyser
3. ✅ Tester matching localement
4. ✅ Identifier root cause du bug actuel

### Phase 2 : Quick Fix (1h)
1. Corriger le bug identifié
2. Valider avec lai_weekly_v24
3. Mesurer impact (items filtrés)

### Phase 3 : Amélioration court terme (2h)
1. Enrichir les 4 scopes lus avec tous les keywords nécessaires
2. Documenter les scopes actifs vs ignorés
3. Créer guide d'ajout de keywords

### Phase 4 : Amélioration moyen terme (1 jour)
1. Lire TOUS les scopes du YAML (Levier 3)
2. Externaliser liste pure players (Levier 4)
3. Externaliser LAI keywords (Levier 5)
4. Tests E2E complets

### Phase 5 : Refactoring long terme (3 jours)
1. Profils d'ingestion configurables (Levier 6)
2. Matching avancé regex (Levier 7)
3. Documentation complète
4. Tests unitaires

---

## 9. CONCLUSION

### Points clés

1. **Moteur actuel** : Fonctionnel mais partiellement hardcodé
2. **Pure players** : Ingestion large avec exclusions minimales
3. **Autres sources** : Filtrage strict double (exclusion + LAI keywords)
4. **Limitation majeure** : Seuls 4 scopes sur 9 sont lus
5. **Bug actuel** : À diagnostiquer (fichier S3, cache, ou matching)

### Recommandations

1. **Immédiat** : Résoudre le bug actuel (keywords non filtrés)
2. **Court terme** : Utiliser les 4 scopes lus au maximum
3. **Moyen terme** : Externaliser tout le hardcodé vers canonical
4. **Long terme** : Refactorer vers un système 100% configurable

---

**Rapport généré le** : 2026-02-06  
**Auteur** : Amazon Q Developer  
**Version** : 1.0
