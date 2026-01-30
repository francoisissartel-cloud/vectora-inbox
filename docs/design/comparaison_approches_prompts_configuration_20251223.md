# Comparaison des Approches de Gestion des Prompts Bedrock - Vectora Inbox

**Date**: 2025-12-23  
**Auteur**: Amazon Q Developer  
**Objectif**: Analyser et comparer les différentes approches pour gérer les prompts Bedrock

---

## 🎯 CONTEXTE ET OBJECTIFS

### Problème à Résoudre

Le système actuel souffre de **hardcoding LAI** dans les prompts Bedrock, rendant impossible l'adaptation à d'autres verticales sans modifier le code Python.

### Objectifs Métier

1. **Généricité**: Support multi-verticales (LAI, Gene Therapy, Cell Therapy, etc.)
2. **Simplicité**: Ajustements sans modifier le code Python
3. **Puissance**: Pilotage fin du comportement du moteur
4. **Maintenabilité**: Règles métier centralisées et lisibles
5. **Performance**: Temps de réponse acceptable

### Deux Approches Proposées

**Approche A**: **Prompts Dynamiques** - Construction en temps réel depuis watch_domains + canonical  
**Approche B**: **Prompts Pré-construits** - Prompts figés par client dans canonical, avec références

---

## 📊 APPROCHE A: PROMPTS DYNAMIQUES (TEMPS RÉEL)

### Principe

Les prompts sont **construits à la volée** à chaque run en analysant:
- `client_config.yaml` (watch_domains)
- `canonical/scopes/*.yaml` (entités, technologies)
- `canonical/prompts/global_prompts.yaml` (templates génériques)

### Architecture

```
Runtime (chaque appel Bedrock)
    ↓
1. Charger client_config.yaml
    ↓
2. Analyser watch_domains
    ↓
3. Détecter verticale (LAI, Gene Therapy, etc.)
    ↓
4. Extraire exemples depuis canonical_scopes
    ↓
5. Construire description technologies
    ↓
6. Substituer variables dans template générique
    ↓
7. Prompt final → Bedrock
```

### Exemple de Flux

**Pour lai_weekly_v5**:

```python
# 1. Charger config
client_config = load_yaml("clients/lai_weekly_v5.yaml")
watch_domains = client_config['watch_domains']
# → [{'id': 'tech_lai_ecosystem', 'technology_scope': 'lai_keywords', ...}]

# 2. Détecter verticale
technology_scope = watch_domains[0]['technology_scope']  # 'lai_keywords'
vertical = detect_vertical(technology_scope)  # → 'LAI'

# 3. Charger scopes
canonical_scopes = load_yaml("canonical/scopes/technology_scopes.yaml")
lai_keywords = canonical_scopes['lai_keywords']
# → {'core_phrases': [...], 'negative_terms': [...]}

# 4. Construire description
tech_description = build_technology_focus_description(lai_keywords, vertical)
# → "LAI TECHNOLOGY FOCUS:\nDetect these technologies:\n- long-acting injectable\n..."

# 5. Extraire exemples
companies = extract_companies_examples(watch_domains, canonical_scopes)
# → "MedinCell, Camurus, DelSiTech, Nanexa, Peptron"

# 6. Substituer dans template
template = canonical_prompts['normalization']['generic_biotech']['user_template']
prompt = template.replace('{{technology_focus_description}}', tech_description)
prompt = prompt.replace('{{companies_examples}}', companies)
# etc.

# 7. Appeler Bedrock
response = bedrock.invoke_model(prompt)
```

### Fichiers Impliqués

**Nouveau module**:
- `src_v2/vectora_core/shared/prompt_builder.py` (200-300 lignes)

**Modifications**:
- `src_v2/vectora_core/normalization/bedrock_client.py` (remplacer hardcoding)
- `canonical/prompts/global_prompts.yaml` (template générique avec variables)

**Aucune modification**:
- `client-config-examples/*.yaml` (déjà bien conçus)
- `canonical/scopes/*.yaml` (déjà bien conçus)

### Avantages

✅ **Flexibilité Maximale**:
- Ajout d'une verticale = créer scopes + client_config (10 minutes)
- Aucune modification de code Python
- Adaptation automatique aux changements de scopes

✅ **DRY (Don't Repeat Yourself)**:
- Un seul template générique pour toutes les verticales
- Pas de duplication de prompts
- Maintenance centralisée

✅ **Évolutivité**:
- Ajout de nouvelles variables facilement
- Extension du système sans refactoring
- Support de cas complexes (multi-domaines, hybrides)

✅ **Cohérence Garantie**:
- Prompts toujours synchronisés avec les scopes
- Pas de risque de désynchronisation
- Mise à jour des scopes = mise à jour automatique des prompts

✅ **Debugging Facilité**:
- Prompt final visible dans les logs
- Traçabilité complète de la construction
- Possibilité de logger les prompts générés

### Inconvénients

❌ **Overhead de Construction**:
- Construction du prompt à chaque appel Bedrock
- ~50-100ms par item (négligeable vs temps Bedrock ~2-5s)
- Peut être optimisé avec cache

❌ **Complexité du Code**:
- Module prompt_builder.py à maintenir
- Logique de détection de verticale
- Gestion des cas edge (scopes manquants, etc.)

❌ **Debugging Plus Complexe**:
- Prompt final pas directement visible dans les fichiers
- Nécessite de logger pour voir le prompt réel
- Erreurs de substitution possibles

❌ **Risque de Bugs**:
- Erreurs dans la logique de construction
- Variables mal substituées
- Cas edge non gérés

### Performance

**Temps de construction d'un prompt**:
- Chargement config: ~5ms (caché)
- Analyse watch_domains: ~10ms
- Extraction exemples: ~20ms
- Construction description: ~15ms
- Substitution variables: ~10ms
- **Total: ~60ms par item**

**Pour un batch de 100 items**:
- Construction prompts: 6 secondes
- Appels Bedrock: 200-500 secondes
- **Overhead: ~1-3% du temps total**

**Optimisation possible**:
- Cacher les caractéristiques détectées par client_id
- Construire une seule fois au début du batch
- **Overhead réduit à <1%**

---

## 📋 APPROCHE B: PROMPTS PRÉ-CONSTRUITS (CANONICAL)

### Principe

Les prompts sont **pré-écrits en dur** dans des fichiers canonical, un par client ou par verticale, avec des **références** aux scopes canonical pour les exemples.

### Architecture

```
Préparation (une fois, par humain)
    ↓
1. Créer prompt LAI dans canonical/prompts/lai_normalization.yaml
2. Inclure références aux scopes: {{ref:lai_companies_global}}
3. Écrire le prompt complet avec toutes les instructions
    ↓
Runtime (chaque appel Bedrock)
    ↓
4. Charger prompt pré-construit
5. Résoudre les références ({{ref:...}})
6. Substituer uniquement {{item_text}}
7. Prompt final → Bedrock
```

### Exemple de Structure

**Fichier**: `canonical/prompts/lai_normalization_prompt.yaml`

```yaml
# Prompt pré-construit pour la verticale LAI
lai_normalization:
  system_instructions: |
    You are a specialized AI assistant for biotech/pharma news analysis.
    Focus on Long-Acting Injectable (LAI) technologies and related entities.
    
  user_template: |
    Analyze this biotech/pharma news item and extract structured information.

    CRITICAL: Only extract entities that are EXPLICITLY mentioned in the text.

    TEXT TO ANALYZE:
    {{item_text}}

    LAI TECHNOLOGY FOCUS:
    Detect these Long-Acting Injectable technologies ONLY if explicitly mentioned:
    - long-acting injectable
    - extended-release injection
    - depot injection
    - once-monthly injection
    - three-month injectable
    - microspheres
    - PLGA
    - in-situ depot
    - hydrogel
    - subcutaneous injection
    - intramuscular injection

    EXAMPLES OF ENTITIES TO DETECT:
    - Companies: {{ref:lai_companies_global}}
    - Molecules: {{ref:lai_molecules_global}}
    - Technologies: {{ref:lai_keywords.core_phrases}}
    - Trademarks: {{ref:lai_trademarks_global}}

    EXCLUDE if these terms are present:
    - oral tablet
    - topical cream
    - transdermal patch

    TASK:
    1. Generate a concise summary (2-3 sentences)
    2. Classify the event type among: clinical_update, partnership, regulatory, ...
    3. Extract ALL pharmaceutical/biotech company names mentioned
    4. Extract ALL drug/molecule names mentioned
    5. Extract ALL technology keywords mentioned
    6. Extract ALL trademark names mentioned
    7. Extract ALL therapeutic indications mentioned
    8. Evaluate LAI relevance (0-10 score)
    9. Detect anti-LAI signals
    10. Assess pure player context

    RESPONSE FORMAT (JSON only):
    {
      "summary": "...",
      "event_type": "...",
      "companies_detected": ["...", "..."],
      "molecules_detected": ["...", "..."],
      "technologies_detected": ["...", "..."],
      "trademarks_detected": ["...", "..."],
      "indications_detected": ["...", "..."],
      "lai_relevance_score": 0,
      "anti_lai_detected": false,
      "pure_player_context": false
    }

    Respond with ONLY the JSON, no additional text.
```

**Fichier**: `canonical/prompts/gene_therapy_normalization_prompt.yaml`

```yaml
# Prompt pré-construit pour la verticale Gene Therapy
gene_therapy_normalization:
  system_instructions: |
    You are a specialized AI assistant for biotech/pharma news analysis.
    Focus on Gene Therapy technologies and related entities.
    
  user_template: |
    Analyze this biotech/pharma news item and extract structured information.

    CRITICAL: Only extract entities that are EXPLICITLY mentioned in the text.

    TEXT TO ANALYZE:
    {{item_text}}

    GENE THERAPY TECHNOLOGY FOCUS:
    Detect these Gene Therapy technologies ONLY if explicitly mentioned:
    - gene therapy
    - AAV vector
    - lentiviral vector
    - CRISPR-Cas9
    - gene editing
    - adeno-associated virus
    - viral vector
    - ex vivo gene therapy
    - in vivo gene therapy

    EXAMPLES OF ENTITIES TO DETECT:
    - Companies: {{ref:gene_therapy_companies_global}}
    - Molecules: {{ref:gene_therapy_molecules_global}}
    - Technologies: {{ref:gene_therapy_keywords.core_phrases}}

    EXCLUDE if these terms are present:
    - small molecule
    - traditional drug

    TASK:
    [... même structure que LAI ...]

    Evaluate Gene Therapy relevance (0-10 score)
```

### Configuration Client

**Fichier**: `client-config-examples/lai_weekly_v5.yaml`

```yaml
# Référence au prompt pré-construit
bedrock_config:
  normalization_prompt: "lai_normalization"  # Clé dans canonical/prompts/
  matching_prompt: "lai_matching"

watch_domains:
  - id: "tech_lai_ecosystem"
    technology_scope: "lai_keywords"
    company_scope: "lai_companies_global"
```

### Code de Résolution

**Nouveau module**: `src_v2/vectora_core/shared/prompt_resolver.py`

```python
def resolve_prompt_references(
    prompt_template: str,
    canonical_scopes: Dict
) -> str:
    """
    Résout les références {{ref:...}} dans un prompt pré-construit.
    
    Exemples:
        {{ref:lai_companies_global}} → "MedinCell, Camurus, DelSiTech, ..."
        {{ref:lai_keywords.core_phrases}} → "long-acting injectable, depot, ..."
    """
    import re
    
    # Pattern pour détecter {{ref:scope_name}} ou {{ref:scope_name.field}}
    pattern = r'\{\{ref:([a-z_]+)(?:\.([a-z_]+))?\}\}'
    
    def replace_ref(match):
        scope_name = match.group(1)
        field_name = match.group(2)
        
        # Charger le scope
        scope_data = canonical_scopes.get(scope_name)
        if not scope_data:
            return f"[ERROR: scope '{scope_name}' not found]"
        
        # Si field spécifié, extraire le champ
        if field_name:
            if isinstance(scope_data, dict):
                field_data = scope_data.get(field_name, [])
            else:
                return f"[ERROR: scope '{scope_name}' is not a dict]"
        else:
            field_data = scope_data
        
        # Formater en liste
        if isinstance(field_data, list):
            return ', '.join(field_data[:15])  # Max 15 exemples
        else:
            return str(field_data)
    
    # Remplacer toutes les références
    resolved = re.sub(pattern, replace_ref, prompt_template)
    return resolved
```

**Utilisation dans bedrock_client.py**:

```python
def _build_normalization_prompt_prebuilt(
    self, item_text, client_config, canonical_scopes, canonical_prompts
):
    # 1. Récupérer le nom du prompt depuis client_config
    prompt_name = client_config.get('bedrock_config', {}).get('normalization_prompt', 'lai_normalization')
    
    # 2. Charger le prompt pré-construit
    prompt_config = canonical_prompts.get(prompt_name)
    if not prompt_config:
        raise ValueError(f"Prompt '{prompt_name}' not found in canonical/prompts/")
    
    # 3. Récupérer le template
    template = prompt_config['user_template']
    
    # 4. Résoudre les références {{ref:...}}
    from ..shared.prompt_resolver import resolve_prompt_references
    resolved = resolve_prompt_references(template, canonical_scopes)
    
    # 5. Substituer {{item_text}}
    final_prompt = resolved.replace('{{item_text}}', item_text)
    
    return final_prompt
```

### Fichiers Impliqués

**Nouveaux fichiers**:
- `canonical/prompts/lai_normalization_prompt.yaml`
- `canonical/prompts/gene_therapy_normalization_prompt.yaml`
- `canonical/prompts/cell_therapy_normalization_prompt.yaml`
- `src_v2/vectora_core/shared/prompt_resolver.py` (50-100 lignes)

**Modifications**:
- `src_v2/vectora_core/normalization/bedrock_client.py` (utiliser prompt_resolver)
- `client-config-examples/*.yaml` (ajouter bedrock_config.normalization_prompt)

**Aucune modification**:
- `canonical/scopes/*.yaml` (déjà bien conçus)

### Avantages

✅ **Simplicité du Code**:
- Pas de logique complexe de construction
- Module prompt_resolver simple (~50 lignes)
- Moins de risques de bugs

✅ **Visibilité Directe**:
- Prompt complet visible dans un fichier
- Facile à lire et comprendre
- Debugging immédiat

✅ **Performance Optimale**:
- Pas de construction dynamique
- Résolution des références rapide (~10ms)
- Overhead minimal (<1%)

✅ **Contrôle Total**:
- Humain écrit le prompt exact
- Pas de "magie" de construction
- Ajustements fins possibles

✅ **Validation Facile**:
- Prompt peut être testé directement
- Copier-coller dans Bedrock Playground
- Itération rapide

### Inconvénients

❌ **Duplication de Contenu**:
- Un prompt par verticale
- Instructions répétées (CRITICAL, TASK, RESPONSE FORMAT)
- Maintenance de plusieurs fichiers

❌ **Risque de Désynchronisation**:
- Prompt peut devenir obsolète si scopes changent
- Références {{ref:...}} peuvent pointer vers scopes inexistants
- Nécessite vigilance humaine

❌ **Moins Flexible**:
- Ajout d'une verticale = écrire un nouveau prompt complet
- Changement de structure = modifier tous les prompts
- Pas d'adaptation automatique

❌ **Maintenance Plus Lourde**:
- Plusieurs prompts à maintenir
- Risque d'incohérences entre prompts
- Changement global = modifier N fichiers

❌ **Pas de Généricité**:
- Chaque verticale a son prompt
- Pas de réutilisation de logique
- Duplication des règles métier

### Performance

**Temps de résolution d'un prompt**:
- Chargement prompt: ~5ms (caché)
- Résolution références: ~10ms
- Substitution {{item_text}}: ~1ms
- **Total: ~16ms par item**

**Pour un batch de 100 items**:
- Résolution prompts: 1.6 secondes
- Appels Bedrock: 200-500 secondes
- **Overhead: <1% du temps total**

---

## ⚖️ COMPARAISON DÉTAILLÉE

### 1. Généricité

| Critère | Approche A (Dynamique) | Approche B (Pré-construit) |
|---------|------------------------|----------------------------|
| Support multi-verticales | ✅ Automatique | ⚠️ Manuel (un prompt par verticale) |
| Ajout nouvelle verticale | ✅ 10 minutes (scopes + config) | ⚠️ 30-60 minutes (écrire prompt complet) |
| Adaptation automatique | ✅ Oui | ❌ Non |
| Réutilisation de logique | ✅ Template unique | ❌ Duplication |

**Gagnant**: Approche A (Dynamique)

### 2. Simplicité

| Critère | Approche A (Dynamique) | Approche B (Pré-construit) |
|---------|------------------------|----------------------------|
| Complexité du code | ⚠️ Module prompt_builder (200-300 lignes) | ✅ Module prompt_resolver (50-100 lignes) |
| Lisibilité | ⚠️ Prompt final pas directement visible | ✅ Prompt complet visible dans fichier |
| Debugging | ⚠️ Nécessite logs | ✅ Immédiat |
| Risque de bugs | ⚠️ Logique de construction | ✅ Résolution simple |

**Gagnant**: Approche B (Pré-construit)

### 3. Maintenabilité

| Critère | Approche A (Dynamique) | Approche B (Pré-construit) |
|---------|------------------------|----------------------------|
| Nombre de fichiers | ✅ 1 template générique | ❌ N prompts (un par verticale) |
| Cohérence | ✅ Garantie (même template) | ⚠️ Risque d'incohérences |
| Changement global | ✅ Modifier 1 template | ❌ Modifier N prompts |
| Synchronisation scopes | ✅ Automatique | ⚠️ Manuelle |

**Gagnant**: Approche A (Dynamique)

### 4. Performance

| Critère | Approche A (Dynamique) | Approche B (Pré-construit) |
|---------|------------------------|----------------------------|
| Overhead par item | ⚠️ ~60ms (optimisable à ~1ms) | ✅ ~16ms |
| Overhead batch 100 items | ⚠️ 6s (optimisable à 0.1s) | ✅ 1.6s |
| % du temps total | ✅ <3% (optimisable à <1%) | ✅ <1% |
| Optimisation possible | ✅ Cache | ✅ Déjà optimal |

**Gagnant**: Approche B (Pré-construit) - mais différence négligeable

### 5. Flexibilité

| Critère | Approche A (Dynamique) | Approche B (Pré-construit) |
|---------|------------------------|----------------------------|
| Ajout de variables | ✅ Facile | ⚠️ Modifier tous les prompts |
| Cas complexes | ✅ Logique programmable | ⚠️ Limité aux références |
| Multi-domaines | ✅ Support natif | ⚠️ Complexe |
| Hybrides | ✅ Support natif | ⚠️ Complexe |

**Gagnant**: Approche A (Dynamique)

### 6. Contrôle Humain

| Critère | Approche A (Dynamique) | Approche B (Pré-construit) |
|---------|------------------------|----------------------------|
| Visibilité du prompt | ⚠️ Nécessite logs | ✅ Fichier complet |
| Ajustements fins | ⚠️ Via template + logique | ✅ Direct dans fichier |
| Test manuel | ⚠️ Générer puis tester | ✅ Copier-coller dans Playground |
| Itération | ⚠️ Modifier template + tester | ✅ Modifier fichier + tester |

**Gagnant**: Approche B (Pré-construit)

---

## 🎨 APPROCHE HYBRIDE (RECOMMANDÉE)

### Principe

Combiner les avantages des deux approches:
- **Prompts pré-construits** pour les verticales établies (LAI, Gene Therapy)
- **Construction dynamique** comme fallback pour nouveaux cas
- **Références canonical** pour éviter la duplication

### Architecture

```
Runtime
    ↓
1. Charger client_config
2. Vérifier si prompt pré-construit existe
    ↓
    OUI → Approche B (résolution références)
    NON → Approche A (construction dynamique)
    ↓
3. Prompt final → Bedrock
```

### Exemple

**Pour LAI (verticale établie)**:
- Utiliser `canonical/prompts/lai_normalization_prompt.yaml`
- Résolution rapide des références
- Prompt optimisé et testé

**Pour nouvelle verticale (ex: RNA Therapeutics)**:
- Pas de prompt pré-construit
- Construction dynamique depuis scopes
- Permet de démarrer rapidement

**Après validation**:
- Créer prompt pré-construit pour RNA Therapeutics
- Optimiser et affiner
- Basculer sur approche B

### Avantages

✅ **Meilleur des deux mondes**:
- Performance optimale pour verticales établies
- Flexibilité pour nouveaux cas
- Migration progressive

✅ **Évolutivité**:
- Démarrer avec dynamique
- Stabiliser avec pré-construit
- Pas de refactoring majeur

✅ **Pragmatisme**:
- Investissement proportionnel à la maturité
- Pas de sur-engineering
- Adaptation au besoin réel

### Implémentation

```python
def build_normalization_prompt(
    item_text, client_config, watch_domains, 
    canonical_scopes, canonical_prompts
):
    # 1. Vérifier si prompt pré-construit existe
    prompt_name = client_config.get('bedrock_config', {}).get('normalization_prompt')
    
    if prompt_name and prompt_name in canonical_prompts:
        # Approche B: Prompt pré-construit
        return build_prompt_prebuilt(
            item_text, prompt_name, canonical_scopes, canonical_prompts
        )
    else:
        # Approche A: Construction dynamique
        return build_prompt_dynamic(
            item_text, watch_domains, canonical_scopes, canonical_prompts
        )
```

---

## 📋 RECOMMANDATION FINALE

### Pour Vectora Inbox Actuel (LAI)

**Recommandation**: **Approche B (Pré-construit)** avec migration progressive

**Justification**:

1. **LAI est une verticale établie**:
   - Prompt bien défini et testé
   - Peu de changements attendus
   - Performance optimale importante

2. **Simplicité prioritaire**:
   - Solo founder doit maintenir le système
   - Debugging facile crucial
   - Moins de code = moins de bugs

3. **Visibilité nécessaire**:
   - Prompt visible pour ajustements
   - Tests manuels fréquents
   - Itération rapide

4. **Performance compte**:
   - 100-200 items par run
   - Overhead minimal souhaitable
   - Bedrock déjà coûteux

### Plan de Migration

**Phase 1** (Immédiat):
- Créer `canonical/prompts/lai_normalization_prompt.yaml`
- Implémenter `prompt_resolver.py` (50 lignes)
- Modifier `bedrock_client.py` pour utiliser prompt pré-construit
- Tester avec lai_weekly_v5

**Phase 2** (Si nouvelle verticale):
- Créer prompt pré-construit pour la nouvelle verticale
- Réutiliser la structure LAI
- Adapter les instructions spécifiques

**Phase 3** (Si besoin de généricité):
- Implémenter `prompt_builder.py` comme fallback
- Utiliser pour prototypage rapide
- Migrer vers pré-construit après validation

### Critères de Décision

**Utiliser Approche B (Pré-construit) si**:
- ✅ Verticale établie et stable
- ✅ Prompt bien défini
- ✅ Performance critique
- ✅ Debugging fréquent
- ✅ Solo founder

**Utiliser Approche A (Dynamique) si**:
- ✅ Nombreuses verticales (>5)
- ✅ Changements fréquents de structure
- ✅ Cas complexes (multi-domaines, hybrides)
- ✅ Équipe de développement
- ✅ Généricité prioritaire

**Pour Vectora Inbox**: Approche B est plus adaptée au contexte actuel.

---

## 🎯 CONCLUSION

### Synthèse

| Aspect | Approche A (Dynamique) | Approche B (Pré-construit) | Hybride |
|--------|------------------------|----------------------------|---------|
| Généricité | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Simplicité | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Maintenabilité | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Performance | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Flexibilité | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Contrôle | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **TOTAL** | **24/30** | **23/30** | **26/30** |

### Décision pour Vectora Inbox

**Approche Recommandée**: **Approche B (Pré-construit)** avec possibilité de fallback dynamique

**Raisons**:
1. Solo founder → simplicité prioritaire
2. LAI verticale établie → prompt stable
3. Performance importante → overhead minimal
4. Debugging fréquent → visibilité nécessaire
5. Migration progressive possible → pas de sur-engineering

**Prochaines Étapes**:
1. Créer `lai_normalization_prompt.yaml`
2. Implémenter `prompt_resolver.py`
3. Tester avec lai_weekly_v5
4. Documenter pour futures verticales

---

*Document de comparaison réalisé le 2025-12-23*  
*Basé sur l'analyse complète du code, des diagnostics et du contexte métier*  
*Objectif: Choisir la meilleure approche pour Vectora Inbox*
