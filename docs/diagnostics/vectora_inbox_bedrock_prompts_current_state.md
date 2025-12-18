
# Diagnostic - État Actuel des Prompts Bedrock dans Vectora Inbox

**Date** : 2025-12-12  
**Objectif** : Inventaire complet des prompts Bedrock hardcodés dans le code  
**Scope** : Analyse de tous les appels Bedrock dans les Lambdas ingest-normalize et engine  

---

## 🔍 Vue d'Ensemble des Appels Bedrock

### Lambdas Concernées
1. **vectora-inbox-ingest-normalize** : Normalisation et extraction d'entités
2. **vectora-inbox-engine** : Génération éditoriale de newsletters

### Modèles Bedrock Utilisés
- **Normalisation** : `us.anthropic.claude-sonnet-4-5-20250929-v1:0` (us-east-1)
- **Newsletter** : `eu.anthropic.claude-sonnet-4-5-20250929-v1:0` (eu-west-3)
- **Configuration hybride P1** : Régions différentes pour optimiser les performances

---

## 📋 Inventaire Détaillé des Prompts

### 1. NORMALISATION - Extraction d'Entités LAI

**📁 Fichier** : `src/vectora_core/normalization/bedrock_client.py`  
**🔧 Fonction** : `_build_normalization_prompt()`  
**🚀 Lambda** : vectora-inbox-ingest-normalize  
**📊 Complexité** : ⭐⭐⭐⭐⭐ (Très élevée - 200+ lignes)

#### Type de Tâche
- **Extraction d'entités** : companies, molecules, technologies, trademarks, indications
- **Classification d'événements** : clinical_update, partnership, regulatory, etc.
- **Scoring LAI** : relevance score 0-10 pour Long-Acting Injectable
- **Résumé automatique** : 2-3 phrases de synthèse
- **Évaluation domaines** : matching avec watch_domains

#### Variables Injectées
```python
variables = {
    'item_text': f"{title} {raw_text}",  # Texte complet à analyser
    'canonical_examples': {
        'companies': ['Pfizer', 'Moderna', 'BioNTech', ...],  # 50 exemples max
        'molecules': ['adalimumab', 'rituximab', ...],         # 30 exemples max  
        'technologies': ['PLGA', 'microspheres', ...]         # 20 exemples max
    },
    'domain_contexts': [                                       # Optionnel
        {
            'domain_id': 'lai_psychiatry',
            'description': 'Long-acting injectable antipsychotics',
            'example_entities': {...},
            'context_phrases': [...]
        }
    ]
}
```

#### Prompt Actuel (Extrait Représentatif)
```python
def _build_normalization_prompt(item_text, canonical_examples, domain_contexts=None):
    # Section LAI spécialisée HARDCODÉE
    lai_section = """
LAI TECHNOLOGY FOCUS:
Detect these LAI (Long-Acting Injectable) technologies:
- Extended-Release Injectable
- Long-Acting Injectable  
- Depot Injection
- Once-Monthly Injection
- Microspheres
- PLGA
- In-Situ Depot
- Hydrogel
- Subcutaneous Injection
- Intramuscular Injection

TRADEMARKS to detect:
- UZEDY, PharmaShell, SiliaShell, BEPO, Aristada, Abilify Maintena

Normalize: 'extended-release injectable' → 'Extended-Release Injectable'
"""

    # Tâches HARDCODÉES (10 tâches spécifiques)
    tasks = [
        "1. Generate a concise summary (2-3 sentences) explaining the key information",
        "2. Classify the event type among: clinical_update, partnership, regulatory, scientific_paper, corporate_move, financial_results, safety_signal, manufacturing_supply, other",
        "3. Extract ALL pharmaceutical/biotech company names mentioned",
        "4. Extract ALL drug/molecule names mentioned (including brand names, generic names)",
        "5. Extract ALL technology keywords mentioned - FOCUS on LAI technologies listed above",
        "6. Extract ALL trademark names mentioned (especially those with ® or ™ symbols)",
        "7. Extract ALL therapeutic indications mentioned",
        "8. Evaluate LAI relevance (0-10 score): How relevant is this content to Long-Acting Injectable technologies?",
        "9. Detect anti-LAI signals: Does the content mention oral routes (tablets, capsules, pills)?",
        "10. Assess pure player context: Is this about a LAI-focused company without explicit LAI mentions?"
    ]

    # Format JSON HARDCODÉ
    json_example = {
        "summary": "...",
        "event_type": "...",
        "companies_detected": ["...", "..."],
        "molecules_detected": ["...", "..."],
        "technologies_detected": ["...", "..."],
        "trademarks_detected": ["...", "..."],
        "indications_detected": ["...", "..."],
        "lai_relevance_score": 0,
        "anti_lai_detected": False,
        "pure_player_context": False,
        "domain_relevance": []  # Si domain_contexts fourni
    }

    prompt = f"""Analyze the following biotech/pharma news item and extract structured information.

TEXT TO ANALYZE:
{item_text}

EXAMPLES OF ENTITIES TO DETECT:
- Companies: {', '.join(companies_ex)}
- Molecules/Drugs: {', '.join(molecules_ex)}
- Technologies: {', '.join(technologies_ex)}{lai_section}{domain_section}

TASK:
{chr(10).join(tasks)}

IMPORTANT:
- Extract the EXACT company names as they appear in the text
- Include ALL companies mentioned, not just those in the examples
- Be comprehensive in entity extraction
- For domain evaluation, consider the overall context and relevance

RESPONSE FORMAT (JSON only):
{json.dumps(json_example, indent=2)}

Respond with ONLY the JSON, no additional text."""

    return prompt
```

#### Problèmes Identifiés
- **Logique LAI hardcodée** : Liste des technologies LAI non configurable
- **Tâches figées** : 10 tâches spécifiques non paramétrables
- **Format JSON rigide** : Structure de réponse non adaptable
- **Duplication avec scopes** : Technologies LAI répétées entre prompt et canonical/scopes/
- **Maintenance complexe** : Modification nécessite redéploiement Lambda

---

### 2. NEWSLETTER - Génération Éditoriale

**📁 Fichier** : `src/vectora_core/newsletter/bedrock_client.py`  
**🔧 Fonction** : `_build_ultra_compact_prompt()` (P1 optimisé)  
**🚀 Lambda** : vectora-inbox-engine  
**📊 Complexité** : ⭐⭐⭐ (Moyenne - optimisé P1)

#### Type de Tâche
- **Génération de titre** : Newsletter title avec date
- **Introduction** : Paragraphe d'accroche (1 phrase en P1)
- **TL;DR** : Liste de bullet points (2 points en P1)
- **Sections intro** : Texte d'introduction par section
- **Reformulation items** : Réécriture des résumés d'items (2 phrases en P1)

#### Variables Injectées
```python
variables = {
    'client_name': 'LAI Weekly',           # Nom du client
    'target_date': '2025-12-12',          # Date de référence
    'sections_data': [                     # Sections avec items
        {
            'title': 'Clinical Updates',
            'items': [
                {
                    'title': 'Nanexa and Moderna...',
                    'summary': 'Partnership for PharmaShell...',
                    'url': 'https://...'
                }
            ]
        }
    ]
}
```

#### Prompt Actuel (Version P1 Ultra-Compacte)
```python
def _build_ultra_compact_prompt(sections_data, client_profile, target_date):
    """P1: Prompt ultra-réduit (-80% tokens vs version initiale)"""
    
    client_name = client_profile.get('name', 'LAI Weekly')
    
    # Items ultra-compacts (2 par section max)
    items_text = ""
    for section in sections_data:
        items_text += f"\n{section['title']}:\n"
        for item in section['items'][:2]:  # P1: Réduction 3→2 items
            title = item.get('title', '')[:60]  # P1: Réduction 100→60 chars
            summary = item.get('summary', '')[:80]  # P1: Réduction 200→80 chars
            items_text += f"• {title}: {summary}\n"
    
    # P1: Prompt ultra-minimal HARDCODÉ
    return f"""JSON newsletter for {client_name} - {target_date}:

{items_text}

Output:
{{"title":"{client_name} – {target_date}","intro":"1 sentence","tldr":["point1","point2"],"sections":[{{"section_title":"name","section_intro":"1 sentence","items":[{{"title":"title","rewritten_summary":"2 sentences","url":"#"}}]}}]}}

Rules: JSON only, concise, preserve names."""
```

#### Évolution des Prompts Newsletter
**Version initiale** (avant P1) : ~500 lignes avec instructions détaillées  
**Version P1 actuelle** : ~50 lignes ultra-optimisée pour réduire les coûts Bedrock  

#### Problèmes Identifiés
- **Format JSON hardcodé** : Structure de réponse figée dans le prompt
- **Optimisations P1 rigides** : Limites (2 items, 60 chars) non configurables
- **Instructions minimales** : Risque de qualité éditoriale réduite
- **Pas de personnalisation** : Tone et style non adaptables par client

---

### 3. DOMAINES - Évaluation Contextuelle

**📁 Fichier** : `src/vectora_core/normalization/domain_context_builder.py`  
**🔧 Fonction** : Construction dynamique dans `_build_normalization_prompt()`  
**🚀 Lambda** : vectora-inbox-ingest-normalize  
**📊 Complexité** : ⭐⭐⭐⭐ (Élevée - logique dynamique)

#### Type de Tâche
- **Évaluation de relevance** : Score 0.0-1.0 par domaine
- **Classification binaire** : is_on_domain true/false
- **Justification** : Explication en 2 phrases max

#### Construction Dynamique du Prompt
```python
# Dans _build_normalization_prompt()
domain_section = ""
if domain_contexts:
    domain_section = "\n\nDOMAINS TO EVALUATE:\n"
    for i, domain in enumerate(domain_contexts, 1):
        domain_section += f"{i}. {domain.domain_id} ({domain.domain_type}):\n"
        domain_section += f"   Description: {domain.description}\n"
        
        # Ajouter les exemples d'entités DYNAMIQUEMENT
        if domain.example_entities:
            for entity_type, examples in domain.example_entities.items():
                if examples:
                    domain_section += f"   {entity_type.title()}: {', '.join(examples[:5])}\n"
        
        # Ajouter les phrases de contexte DYNAMIQUEMENT
        if domain.context_phrases:
            domain_section += f"   Context: {'; '.join(domain.context_phrases)}\n"
        domain_section += "\n"

# Tâche ajoutée dynamiquement
if domain_contexts:
    tasks.append("7. For EACH domain listed above, evaluate:")
    tasks.append("   - is_on_domain: true if the article is relevant to this domain, false otherwise")
    tasks.append("   - relevance_score: 0.0-1.0 score indicating how relevant the article is to this domain")
    tasks.append("   - reason: Brief explanation (max 2 sentences) of why it is or isn't relevant")
```

#### Problèmes Identifiés
- **Construction complexe** : Logique de construction éparpillée
- **Tâches conditionnelles** : Instructions ajoutées dynamiquement
- **Format JSON variable** : Structure dépendante de la présence de domaines

---

## 🔄 Analyse des Duplications et Patterns

### Duplications Identifiées

#### 1. Instructions JSON Communes
```python
# Répété dans normalisation ET newsletter
"RESPONSE FORMAT (JSON only):"
"Respond with ONLY the JSON, no additional text."
```

#### 2. Exemples d'Entités
```python
# Logique similaire dans les deux prompts
companies_ex = canonical_examples.get('companies', [])[:20]
molecules_ex = canonical_examples.get('molecules', [])[:20]
technologies_ex = canonical_examples.get('technologies', [])[:15]
```

#### 3. Configuration Bedrock
```python
# Paramètres répétés
request_body = {
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 1000,  # Varie selon le prompt
    "temperature": 0.0,  # Varie selon le prompt
    "messages": [{"role": "user", "content": prompt}]
}
```

### Patterns Communs

#### 1. Retry Logic
```python
# Identique dans bedrock_client.py (normalisation) et newsletter/bedrock_client.py
def _call_bedrock_with_retry(model_id, request_body, max_retries=3):
    for attempt in range(max_retries + 1):
        try:
            # Appel Bedrock
        except ClientError as e:
            if error_code == 'ThrottlingException':
                # Backoff exponentiel
```

#### 2. Response Parsing
```python
# Pattern similaire pour parser les réponses JSON
def _parse_bedrock_response(response_text):
    try:
        result = json.loads(response_text)
        # Validation et fallback
    except json.JSONDecodeError:
        # Extraction manuelle
```

---

## 🎯 Prompts Critiques Métier

### 1. LAI Technology Focus (CRITIQUE ⭐⭐⭐⭐⭐)
**Impact** : Cœur métier de Vectora Inbox  
**Fréquence d'ajustement** : Élevée (nouvelles technologies, trademarks)  
**Complexité** : Technologies hardcodées, normalisation des termes  

```python
# Section la plus critique à externaliser
lai_section = """
LAI TECHNOLOGY FOCUS:
Detect these LAI (Long-Acting Injectable) technologies:
- Extended-Release Injectable    # ← Ajustements fréquents
- Long-Acting Injectable
- Depot Injection
- Once-Monthly Injection
- Microspheres                   # ← Nouvelles technologies
- PLGA
- In-Situ Depot
- Hydrogel
- Subcutaneous Injection
- Intramuscular Injection

TRADEMARKS to detect:
- UZEDY, PharmaShell, SiliaShell, BEPO, Aristada, Abilify Maintena  # ← Nouveaux trademarks

Normalize: 'extended-release injectable' → 'Extended-Release Injectable'  # ← Règles de normalisation
"""
```

### 2. Event Type Classification (CRITIQUE ⭐⭐⭐⭐)
**Impact** : Scoring et sélection des items  
**Fréquence d'ajustement** : Moyenne (nouveaux types d'événements)  

```python
# Classification hardcodée
"Classify the event type among: clinical_update, partnership, regulatory, scientific_paper, corporate_move, financial_results, safety_signal, manufacturing_supply, other"
```

### 3. Editorial Tone (CRITIQUE ⭐⭐⭐)
**Impact** : Qualité perçue de la newsletter  
**Fréquence d'ajustement** : Faible (personnalisation client)  

```python
# Actuellement minimal en P1
"Rules: JSON only, concise, preserve names."
# Devrait être personnalisable par client
```

---

## 📊 Métriques de Complexité

### Lignes de Code par Prompt
| Prompt | Fonction | Lignes | Complexité |
|--------|----------|--------|------------|
| **Normalisation LAI** | `_build_normalization_prompt()` | ~200 | ⭐⭐⭐⭐⭐ |
| **Newsletter P1** | `_build_ultra_compact_prompt()` | ~50 | ⭐⭐⭐ |
| **Domaines** | Construction dynamique | ~100 | ⭐⭐⭐⭐ |

### Variables par Prompt
| Prompt | Variables Injectées | Dynamique |
|--------|-------------------|-----------|
| **Normalisation** | 3 principales + domaines optionnels | ✅ |
| **Newsletter** | 3 principales | ❌ |
| **Domaines** | Construction complète | ✅ |

### Fréquence d'Ajustement
| Prompt | Fréquence | Raison |
|--------|-----------|--------|
| **LAI Technologies** | Élevée | Nouvelles technologies, trademarks |
| **Event Types** | Moyenne | Nouveaux types d'événements |
| **Editorial Tone** | Faible | Personnalisation client |

---

## 🚨 Risques Identifiés

### 1. Maintenance Complexe
- **Redéploiement nécessaire** pour chaque ajustement de prompt
- **Tests de régression** difficiles sans versioning
- **Coordination** entre équipes métier et technique

### 2. Duplication de Logique
- **Technologies LAI** répétées entre prompt et canonical/scopes/
- **Instructions JSON** dupliquées entre normalisation et newsletter
- **Configuration Bedrock** répétée dans chaque module

### 3. Rigidité des Optimisations P1
- **Limites hardcodées** (2 items, 60 chars) non configurables
- **Trade-off qualité/coût** figé dans le code
- **Personnalisation impossible** sans modification du code

### 4. Gestion des Erreurs
- **Fallback limité** en cas d'échec de parsing JSON
- **Pas de validation** de la cohérence des prompts
- **Debugging difficile** avec prompts hardcodés

---

## 💡 Recommandations Prioritaires

### P0 - Actions Immédiates
1. **Externaliser LAI Technology Focus** : Section la plus critique et ajustée fréquemment
2. **Créer PromptLoader** : Fonction centralisée de chargement avec cache
3. **Implémenter feature flags** : Migration progressive sans risque

### P1 - Optimisations
1. **Factoriser instructions JSON** : Réduire la duplication entre prompts
2. **Paramétrer optimisations P1** : Rendre configurables les limites (items, chars)
3. **Versioning des prompts** : Permettre A/B testing et rollback

### P2 - Évolutions
1. **Personnalisation client** : Surcharge des prompts par client_id
2. **Monitoring qualité** : Métriques de performance des prompts
3. **Templates avancés** : Système de templating plus sophistiqué

---

## 📈 Impact Estimé de la Canonicalisation

### Bénéfices Attendus
- **Agilité métier** : Ajustements sans redéploiement Lambda
- **Versioning** : Historique et rollback des prompts
- **Personnalisation** : Adaptation par client
- **Maintenance** : Code plus lisible et maintenable

### Effort Estimé
- **Phase A (LAI)** : 2-3 jours (design + implémentation + tests)
- **Phase B (Newsletter)** : 1-2 jours (plus simple)
- **Phase C (Domaines)** : 2-3 jours (logique complexe)

### ROI Estimé
- **Réduction temps d'ajustement** : 80% (de 2h à 20min)
- **Réduction risque de régression** : 60% (tests automatisés)
- **Amélioration agilité métier** : Ajustements en temps réel

---

**Ce diagnostic révèle que les prompts Bedrock sont actuellement hardcodés avec une complexité élevée, particulièrement pour la normalisation LAI. La canonicalisation apporterait une agilité métier significative avec un effort d'implémentation raisonnable.**