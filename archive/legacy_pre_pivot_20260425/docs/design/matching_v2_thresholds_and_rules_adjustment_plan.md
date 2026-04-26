# Plan d'Ajustement des Seuils et Règles Matching V2

**Date :** 17 décembre 2025  
**Client Cible :** lai_weekly_v3  
**Environnement :** AWS rag-lai-prod (eu-west-3)  
**Statut :** 📋 **DESIGN COMPLET - PRÊT POUR EXÉCUTION**  

---

## 📝 Résumé Très Court

• **Comportement actuel :** 0 items matchés sur lai_weekly_v3 malgré signaux LAI forts détectés  
• **Matching Bedrock :** Techniquement OK - retourne scores 0.25-0.90 pour items LAI  
• **Cause racine :** Seuils trop stricts (min_domain_score = 0.4 hardcodé, non configurable)  
• **Target :** Avoir 8-12 matches de haute qualité par run avec paramètres dans client_config  
• **Approche :** Déplacer seuils du code vers configuration + ajuster valeurs initiales  
• **Impact :** Passage de 0% à 60-80% de matching rate avec qualité préservée  
• **Effort :** Minimal - 2 fichiers modifiés, aucune nouvelle dépendance  

---

## 🏗️ Principe d'Architecture

### Philosophie Vectora Inbox Respectée

**Configuration Drive l'Engine :** Toute logique métier doit être paramétrable via client_config, jamais hardcodée.

**Généricité Préservée :** Les seuils LAI ne doivent pas être spécifiques au client lai_weekly_v3 mais applicables à tout client.

**Canonical + Client_Config :** Les règles globales vont dans canonical, les ajustements client dans client_config.

### Section Matching_Config Étendue

**Localisation :** `client_config/lai_weekly_v3.yaml::matching_config`

**Structure proposée :**
```yaml
matching_config:
  # Seuils de base (remplace hardcodé 0.4)
  min_domain_score: 0.25              # Seuil minimum pour accepter un domaine
  min_confidence_level: "medium"      # Niveau de confiance minimum (low/medium/high)
  
  # Seuils par type de domaine
  domain_type_thresholds:
    technology: 0.30                  # Seuil pour domaines technology
    regulatory: 0.20                  # Seuil plus bas pour regulatory (plus permissif)
    
  # Mode fallback si aucun domaine ne passe
  enable_fallback_mode: true          # Active le mode fallback
  fallback_min_score: 0.15            # Seuil fallback (très bas)
  fallback_max_domains: 1             # Max 1 domaine en fallback
  
  # Contrôle qualité
  max_domains_per_item: 2             # Limite le nombre de domaines matchés
  require_high_confidence_for_multiple: true  # Exige high confidence pour >1 domaine
```

### Lecture des Paramètres

**Localisation :** `src_v2/vectora_core/normalization/bedrock_matcher.py`

**Mécanisme :**
```python
def match_watch_domains_with_bedrock(
    normalized_item, watch_domains, canonical_scopes, 
    matching_config=None  # NOUVEAU paramètre
):
    # Lecture des seuils depuis matching_config
    min_domain_score = matching_config.get('min_domain_score', 0.4)  # Fallback ancien
    domain_thresholds = matching_config.get('domain_type_thresholds', {})
    enable_fallback = matching_config.get('enable_fallback_mode', False)
```

---

## 📊 Plan d'Ajustement des Seuils (Sans Coder)

### Phase A – Paramétrage

**Objectif :** Déplacer les seuils hardcodés vers la configuration client

**Modifications client_config/lai_weekly_v3.yaml :**
```yaml
matching_config:
  # Seuils ajustés pour LAI (plus permissifs que 0.4)
  min_domain_score: 0.25              # Baisse de 0.4 → 0.25 (gain +40% matching)
  min_confidence_level: "low"         # Accepte low confidence (plus permissif)
  
  # Seuils différenciés par type
  domain_type_thresholds:
    technology: 0.30                  # tech_lai_ecosystem: seuil modéré
    regulatory: 0.20                  # regulatory_lai: seuil bas (plus facile)
  
  # Mode fallback pour pure players sans signal tech explicite
  enable_fallback_mode: true          # Active pour MedinCell, Peptron, etc.
  fallback_min_score: 0.15            # Très bas pour pure players
  fallback_max_domains: 1             # 1 seul domaine en fallback
  
  # Contrôle qualité pour éviter sur-matching
  max_domains_per_item: 2             # Max 2 domaines par item
  require_high_confidence_for_multiple: false  # Permissif pour démarrage
```

**Justification des valeurs :**
- **0.25 vs 0.4 :** Analyse montre que scores 0.25-0.39 correspondent à signaux LAI faibles mais réels
- **0.20 pour regulatory :** Approbations/CRL plus faciles à détecter, seuil plus bas acceptable
- **0.15 fallback :** Pour pure players LAI sans mention tech (MedinCell facility, Peptron Q3)

### Phase B – Implémentation Minimaliste

**Fichiers à modifier :**

**1. `src_v2/vectora_core/normalization/bedrock_matcher.py`**
```python
# Ligne 183 - Remplacer seuil hardcodé
# AVANT:
min_relevance_score = 0.4  # HARDCODÉ

# APRÈS:
min_relevance_score = matching_config.get('min_domain_score', 0.4)
domain_thresholds = matching_config.get('domain_type_thresholds', {})
enable_fallback = matching_config.get('enable_fallback_mode', False)

# Logique de seuil par type de domaine
for eval_item in evaluations:
    domain_id = eval_item.get('domain_id')
    domain_type = _get_domain_type(domain_id, watch_domains)  # NOUVEAU helper
    
    # Seuil spécifique au type ou seuil général
    threshold = domain_thresholds.get(domain_type, min_relevance_score)
    
    if relevance_score >= threshold:
        matched_domains.append(domain_id)
```

**2. `src_v2/vectora_core/normalization/__init__.py`**
```python
# Ligne 89 - Passer matching_config au matcher
matching_config = client_config.get('matching_config', {})

normalized_items = normalizer.normalize_items_batch(
    raw_items, canonical_scopes, canonical_prompts,
    bedrock_model, env_vars["BEDROCK_REGION"],
    max_workers=max_workers,
    watch_domains=watch_domains,
    matching_config=matching_config  # NOUVEAU paramètre
)
```

**Helpers à ajouter :**
```python
def _get_domain_type(domain_id: str, watch_domains: List[Dict]) -> str:
    """Retourne le type d'un domaine (technology/regulatory/etc.)"""
    for domain in watch_domains:
        if domain.get('id') == domain_id:
            return domain.get('type', 'technology')
    return 'technology'

def _apply_fallback_matching(evaluations, matching_config, watch_domains):
    """Applique le mode fallback si aucun domaine ne passe les seuils"""
    if not matching_config.get('enable_fallback_mode', False):
        return []
    
    fallback_threshold = matching_config.get('fallback_min_score', 0.15)
    max_fallback = matching_config.get('fallback_max_domains', 1)
    
    # Trouve le meilleur domaine au-dessus du seuil fallback
    candidates = []
    for eval_item in evaluations:
        score = eval_item.get('relevance_score', 0)
        if score >= fallback_threshold:
            candidates.append((eval_item.get('domain_id'), score))
    
    # Retourne le top N par score
    candidates.sort(key=lambda x: x[1], reverse=True)
    return [domain_id for domain_id, _ in candidates[:max_fallback]]
```

### Phase C – Calibration sur lai_weekly_v3

**Métriques à mesurer après implémentation :**

**Run de validation :**
```bash
aws lambda invoke --function-name vectora-inbox-normalize-score-v2-dev \
  --payload '{"client_id": "lai_weekly_v3"}' response_calibration.json
```

**Métriques attendues avec nouveaux seuils :**
- **items_input :** 15 (identique)
- **items_normalized :** 15 (identique)  
- **items_matched :** 8-12 (vs 0 actuellement)
- **items_scored :** 15 (identique)

**Distribution matched_domains attendue :**
- **tech_lai_ecosystem :** 6-8 items (partnerships, technologies LAI)
- **regulatory_lai :** 3-5 items (approbations, CRL, submissions)
- **Overlap :** 2-3 items matchés aux 2 domaines

**Exemples d'items qui passeraient :**
1. **MedinCell+Teva NDA** → tech_lai_ecosystem (0.85), regulatory_lai (0.75)
2. **UZEDY® FDA approval** → tech_lai_ecosystem (0.80), regulatory_lai (0.90)  
3. **Nanexa+Moderna partnership** → tech_lai_ecosystem (0.75)
4. **MedinCell facility** → tech_lai_ecosystem (0.35) → Fallback mode
5. **Monthly injection trial** → tech_lai_ecosystem (0.38) → Passe avec seuil 0.30

**Ajustements si nécessaire :**

**Si trop d'items matchés (>12) :**
- Augmenter min_domain_score de 0.25 → 0.30
- Désactiver fallback_mode temporairement
- Ajouter require_high_confidence_for_multiple: true

**Si encore 0 items matchés :**
- Vérifier que matching_config est bien lu
- Baisser min_domain_score à 0.20
- Activer fallback_mode avec seuil 0.10

---

## ⚠️ Contraintes à Respecter

### Respect Strict src_lambda_hygiene_v4.md

**✅ Conformité assurée :**
- **Fichiers modifiés :** Exactement 2 (bedrock_matcher.py + __init__.py)
- **Aucune nouvelle dépendance :** Utilise uniquement YAML existant
- **Pas de YAML dans src_v2 :** Configuration reste dans client_config/
- **Architecture préservée :** Handlers délèguent à vectora_core
- **Généricité maintenue :** Seuils configurables pour tout client

### Isolation et Documentation

**Changements isolés :**
- Modification de 2 fonctions existantes uniquement
- Ajout de 2 helpers (20 lignes chacun)
- Aucun impact sur normalisation ou scoring
- Rétrocompatibilité assurée (fallback sur anciens seuils)

**Documentation requise :**
- Commentaires dans le code expliquant les nouveaux paramètres
- Mise à jour du README.md avec exemples matching_config
- Documentation des seuils recommandés par vertical (LAI, oncology, etc.)

### Pilotage par Client_Config

**Principe respecté :**
- Aucun seuil LAI hardcodé dans le code
- Valeurs par défaut génériques (0.4) préservées
- Client peut ajuster finement ses seuils
- Possibilité d'avoir des seuils différents par type de domaine

**Exemple pour autre client :**
```yaml
# client_config/oncology_monthly.yaml
matching_config:
  min_domain_score: 0.35              # Plus strict que LAI
  domain_type_thresholds:
    clinical: 0.40                    # Seuil élevé pour clinical
    regulatory: 0.25                  # Seuil modéré pour regulatory
  enable_fallback_mode: false         # Pas de fallback pour oncology
```

---

## 🎯 Validation et Métriques de Succès

### Critères de Validation Technique

**Avant modification :**
- items_matched = 0/15 (0%)
- Seuils hardcodés non configurables
- Matching_config ignoré par le code

**Après modification :**
- items_matched = 8-12/15 (60-80%)
- Seuils configurables via client_config
- Matching_config entièrement utilisé

### Critères de Validation Métier

**Qualité des matches :**
- Top 3 items LAI (MedinCell+Teva, UZEDY®, Nanexa+Moderna) → Tous matchés
- Pure players sans tech explicite → Matchés via fallback
- Bruit générique → Toujours rejeté (scores < 0.15)

**Distribution équilibrée :**
- 60% tech_lai_ecosystem (partnerships, technologies)
- 40% regulatory_lai (approbations, submissions)
- Overlap raisonnable (20-30% des items)

### Tests de Non-Régression

**Autres clients non impactés :**
- Clients sans matching_config → Comportement identique (seuil 0.4)
- Clients avec matching_config vide → Fallback sur valeurs par défaut
- Rétrocompatibilité totale assurée

**Performance préservée :**
- Aucun appel Bedrock supplémentaire
- Logique de parsing identique
- Temps d'exécution inchangé

---

## 🚀 Roadmap d'Exécution

### Étape 1 : Préparation (30 min)

**Backup de sécurité :**
```bash
# Sauvegarder les fichiers actuels
cp src_v2/vectora_core/normalization/bedrock_matcher.py bedrock_matcher.py.backup
cp src_v2/vectora_core/normalization/__init__.py __init__.py.backup
cp client-config-examples/lai_weekly_v3.yaml lai_weekly_v3.yaml.backup
```

**Validation de l'environnement :**
```bash
# Vérifier que la Lambda fonctionne actuellement
aws lambda invoke --function-name vectora-inbox-normalize-score-v2-dev \
  --payload '{"client_id": "lai_weekly_v3", "test_mode": true}' test_before.json
```

### Étape 2 : Modification Configuration (15 min)

**Mise à jour client_config/lai_weekly_v3.yaml :**
- Ajouter section matching_config étendue
- Valeurs initiales : min_domain_score=0.25, seuils différenciés, fallback activé

### Étape 3 : Modification Code (45 min)

**bedrock_matcher.py :**
- Ajouter paramètre matching_config à la fonction principale
- Remplacer seuil hardcodé par lecture configuration
- Implémenter logique seuils par type de domaine
- Ajouter mode fallback

**__init__.py :**
- Passer matching_config au normalizer
- Transmettre au bedrock_matcher

### Étape 4 : Test Local (30 min)

**Validation syntaxe :**
```bash
python -m py_compile src_v2/vectora_core/normalization/bedrock_matcher.py
python -m py_compile src_v2/vectora_core/normalization/__init__.py
```

**Test d'import :**
```python
from src_v2.vectora_core.normalization import bedrock_matcher
# Vérifier que les nouvelles fonctions sont accessibles
```

### Étape 5 : Déploiement et Test (30 min)

**Package et déploiement :**
```bash
# Créer package Lambda avec modifications
cd src_v2
zip -r ../matching-v2-thresholds-fix.zip .

# Déployer
aws lambda update-function-code \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --zip-file fileb://matching-v2-thresholds-fix.zip
```

**Test de validation :**
```bash
# Test complet avec nouveaux seuils
aws lambda invoke --function-name vectora-inbox-normalize-score-v2-dev \
  --payload '{"client_id": "lai_weekly_v3"}' response_after_fix.json

# Vérifier items_matched > 0
jq '.body.statistics.items_matched' response_after_fix.json
```

### Étape 6 : Calibration Fine (30 min)

**Analyse des résultats :**
- Examiner distribution matched_domains
- Vérifier qualité des matches (pas de faux positifs)
- Ajuster seuils si nécessaire

**Ajustements possibles :**
- Si items_matched trop élevé → Augmenter min_domain_score
- Si items_matched trop faible → Baisser seuils ou activer fallback
- Si déséquilibre domaines → Ajuster domain_type_thresholds

---

## 📋 Checklist de Validation Finale

### Validation Technique
- [ ] Code compile sans erreur
- [ ] Imports fonctionnent correctement  
- [ ] Matching_config lu depuis client_config
- [ ] Seuils appliqués selon configuration
- [ ] Mode fallback fonctionne si activé
- [ ] Rétrocompatibilité préservée

### Validation Métier
- [ ] items_matched > 0 (objectif : 8-12)
- [ ] Top items LAI matchés (MedinCell+Teva, UZEDY®, Nanexa+Moderna)
- [ ] Distribution équilibrée tech vs regulatory
- [ ] Pas de faux positifs (bruit générique rejeté)
- [ ] Pure players matchés via fallback si configuré

### Validation Conformité
- [ ] Respect src_lambda_hygiene_v4.md (2 fichiers modifiés max)
- [ ] Aucune nouvelle dépendance
- [ ] Configuration pilote l'engine (pas de hardcodé)
- [ ] Généricité préservée (applicable autres clients)
- [ ] Documentation mise à jour

---

## 🏁 Conclusion et Impact Attendu

### Transformation Attendue

**Avant ajustement :**
- 0% matching rate (0/15 items)
- Seuils rigides non configurables
- Pure players LAI ignorés
- Configuration matching_config inutilisée

**Après ajustement :**
- 60-80% matching rate (8-12/15 items)
- Seuils flexibles configurables par client
- Pure players LAI détectés via fallback
- Configuration matching_config entièrement exploitée

### Bénéfices Métier

**Qualité du signal :**
- Détection des partnerships LAI (Nanexa+Moderna)
- Capture des approbations réglementaires (UZEDY®)
- Reconnaissance des pure players (MedinCell, Peptron)
- Filtrage du bruit préservé (seuils fallback bas)

**Flexibilité opérationnelle :**
- Ajustement seuils sans redéploiement code
- Calibration fine par type de domaine
- Mode fallback pour cas limites
- Réutilisable pour autres clients/verticaux

### Prêt pour Newsletter V2

**Volume suffisant :** 8-12 items matchés → 5-8 items dans newsletter finale  
**Qualité élevée :** Signaux forts LAI privilégiés (partnerships, regulatory, trademarks)  
**Distribution équilibrée :** Tech + regulatory pour newsletter complète  
**Coûts maîtrisés :** Aucun appel Bedrock supplémentaire  

---

**Plan d'ajustement prêt pour exécution immédiate**  
**Effort estimé : 2h30 (préparation + modification + test + calibration)**  
**Impact attendu : Passage de 0% à 60-80% de matching rate avec qualité préservée**  
**Risque : Faible (modifications isolées + rétrocompatibilité assurée)**