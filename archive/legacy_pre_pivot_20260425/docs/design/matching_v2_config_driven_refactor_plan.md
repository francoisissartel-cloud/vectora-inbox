# Plan de Refactoring Matching V2 : Configuration-Driven

**Date :** 17 décembre 2025  
**Objectif :** Transformer le matching V2 hardcodé en moteur générique piloté par configuration  
**Client Cible :** lai_weekly_v3 (puis extensible à tous clients)  
**Environnement :** AWS rag-lai-prod (eu-west-3)  
**Statut :** 📋 **PLAN DÉTAILLÉ - PRÊT POUR VALIDATION**  

---

## 🎯 Résumé Exécutif

### Problème Identifié
- **Matching V2 techniquement fonctionnel** mais retourne 0 items matchés sur lai_weekly_v3
- **Cause racine :** Seuils hardcodés trop stricts (min_relevance_score = 0.4) dans le code Python
- **Configuration ignorée :** matching_config dans client_config non utilisée par le moteur
- **Manque de flexibilité :** Impossible d'ajuster seuils sans redéployer du code

### Solution Proposée
- **Déplacer TOUS les seuils** du code vers client_config et canonical
- **Moteur générique** appliquant les règles sans les définir
- **Mode diagnostic** pour comprendre chaque décision de matching
- **Rétrocompatibilité** assurée avec fallback sur anciens seuils

### Impact Attendu
- **Passage de 0% à 60-80%** de matching rate sur lai_weekly_v3
- **Seuils ajustables** sans redéploiement de code
- **Réutilisable** pour tous clients et domaines
- **Transparence** complète des décisions de matching

---

## Phase 0 – Cadrage & Lecture des Artefacts

### 0.1 Documents Analysés ✅
- `docs/diagnostics/matching_v2_current_behavior_lai_weekly_v3.md` : Cause racine identifiée
- `docs/design/matching_v2_thresholds_and_rules_adjustment_plan.md` : Seuils recommandés
- `docs/diagnostics/bedrock_matching_v2_production_validation_report.md` : Validation technique
- `.q-context/src_lambda_hygiene_v4.md` : Contraintes d'architecture strictes
- `client-config-examples/lai_weekly_v3.yaml` : Configuration actuelle
- `src_v2/vectora_core/normalization/bedrock_matcher.py` : Code actuel à refactorer

### 0.2 État Actuel Confirmé
- **Matching Bedrock V2 :** Techniquement OK, appels réussis
- **Seuils hardcodés :** `min_relevance_score = 0.4` ligne 183 de bedrock_matcher.py
- **Configuration présente :** matching_config dans lai_weekly_v3.yaml mais ignorée
- **Architecture V2 :** Respectée, src_v2 conforme aux règles hygiene_v4

### 0.3 Contraintes Validées
- **Aucune nouvelle dépendance** Python autorisée
- **Maximum 2-3 fichiers** modifiés dans src_v2
- **Généricité absolue :** Pas de logique spécifique lai_weekly_v3
- **Rétrocompatibilité :** Clients sans matching_config doivent fonctionner

---

## Phase 1 – Conception de la Configuration de Matching

### 1.1 Structure matching_config Étendue

**Fichier :** `client-config-examples/lai_weekly_v3.yaml`

**Section matching_config enrichie :**
```yaml
matching_config:
  # === SEUILS DE BASE (remplace hardcodé 0.4) ===
  min_domain_score: 0.25              # Seuil minimum global
  min_confidence_level: "low"         # Niveau confiance minimum (low/medium/high)
  
  # === SEUILS PAR TYPE DE DOMAINE ===
  domain_type_thresholds:
    technology: 0.30                  # Seuil pour domaines technology
    regulatory: 0.20                  # Seuil plus bas pour regulatory
    clinical: 0.35                    # Seuil pour domaines clinical (futur)
    
  # === MODE FALLBACK POUR PURE PLAYERS ===
  enable_fallback_mode: true          # Active le mode fallback
  fallback_min_score: 0.15            # Seuil très bas pour pure players
  fallback_max_domains: 1             # Max 1 domaine en fallback
  fallback_company_scopes:            # Scopes éligibles au fallback
    - "lai_companies_global"
    
  # === CONTRÔLE QUALITÉ ===
  max_domains_per_item: 2             # Limite nombre domaines matchés
  require_high_confidence_for_multiple: false  # Permissif pour démarrage
  
  # === MODE DIAGNOSTIC ===
  enable_diagnostic_mode: true        # Active logs détaillés
  store_rejection_reasons: true       # Stocke pourquoi items rejetés
```

### 1.2 Canonical matching_rules.yaml (Optionnel)

**Fichier :** `canonical/matching/matching_rules.yaml`

**Règles génériques réutilisables :**
```yaml
# Règles de matching génériques Vectora Inbox
matching_rules:
  # Seuils par défaut pour tous clients
  default_thresholds:
    min_domain_score: 0.4             # Seuil conservateur par défaut
    min_confidence_level: "medium"
    
  # Seuils recommandés par vertical
  vertical_presets:
    lai:                              # Long-Acting Injectables
      min_domain_score: 0.25
      domain_type_thresholds:
        technology: 0.30
        regulatory: 0.20
      enable_fallback_mode: true
      
    oncology:                         # Oncologie
      min_domain_score: 0.35
      domain_type_thresholds:
        clinical: 0.40
        regulatory: 0.25
      enable_fallback_mode: false
      
  # Règles de fallback par type de scope
  fallback_rules:
    pure_player_detection:
      min_company_mentions: 1         # Au moins 1 company du scope
      max_fallback_score: 0.35        # Score max pour activer fallback
      
  # Règles de diagnostic
  diagnostic_config:
    log_all_evaluations: true         # Log toutes évaluations Bedrock
    include_rejection_details: true   # Détails des rejets
    max_reasoning_length: 200         # Limite taille reasoning
```

### 1.3 Paramètres de Matching Introduits

**Paramètres critiques à implémenter :**

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `min_domain_score` | float | 0.4 | Seuil minimum global (remplace hardcodé) |
| `domain_type_thresholds` | dict | {} | Seuils spécifiques par type domaine |
| `enable_fallback_mode` | bool | false | Active mode fallback pure players |
| `fallback_min_score` | float | 0.15 | Seuil fallback très permissif |
| `max_domains_per_item` | int | 3 | Limite domaines matchés par item |
| `enable_diagnostic_mode` | bool | false | Active logs détaillés |

---

## Phase 2 – Refactor du Moteur de Matching

### 2.1 Fichiers Code à Modifier

**Fichier 1 :** `src_v2/vectora_core/normalization/bedrock_matcher.py`
- **Fonction principale :** `match_watch_domains_with_bedrock()` - Ajouter paramètre matching_config
- **Fonction critique :** `_parse_bedrock_matching_response()` - Remplacer seuil hardcodé
- **Nouvelles fonctions :** `_apply_matching_policy()`, `_apply_fallback_matching()`

**Fichier 2 :** `src_v2/vectora_core/normalization/__init__.py`
- **Fonction :** `run_normalize_score_for_client()` - Passer matching_config au matcher
- **Ligne ~89 :** Transmission matching_config depuis client_config

### 2.2 Nouvelle Fonction apply_matching_policy()

**Signature et logique :**
```python
def _apply_matching_policy(
    item: Dict[str, Any], 
    domain_evaluations: List[Dict], 
    watch_domains: List[Dict],
    matching_config: Dict[str, Any],
    canonical_scopes: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Applique la politique de matching configurée à un item.
    
    Returns:
        {
            "matched_domains": ["tech_lai_ecosystem"],
            "domain_relevance": {
                "tech_lai_ecosystem": {
                    "score": 0.75,
                    "threshold": 0.30,
                    "decision": "matched",
                    "reason": "Score 0.75 > seuil technology 0.30"
                },
                "regulatory_lai": {
                    "score": 0.18,
                    "threshold": 0.20,
                    "decision": "rejected",
                    "reason": "Score 0.18 < seuil regulatory 0.20"
                }
            },
            "fallback_applied": false,
            "diagnostic_info": {...}
        }
    """
```

**Logique de décision :**
1. **Lecture seuils :** Depuis matching_config avec fallback sur défauts
2. **Évaluation par domaine :** Appliquer seuil spécifique au type ou seuil global
3. **Mode fallback :** Si aucun domaine matché ET conditions remplies
4. **Contrôle qualité :** Limiter nombre domaines, vérifier confiance
5. **Diagnostic :** Stocker raison de chaque décision

### 2.3 Suppression des Seuils Hardcodés

**Avant (ligne 183) :**
```python
min_relevance_score = 0.4  # SEUIL CRITIQUE HARDCODÉ
```

**Après :**
```python
# Lecture depuis configuration avec fallback sécurisé
min_domain_score = matching_config.get('min_domain_score', 0.4)
domain_thresholds = matching_config.get('domain_type_thresholds', {})
enable_fallback = matching_config.get('enable_fallback_mode', False)
```

### 2.4 Champ matched_domains Détaillé

**Structure enrichie pour chaque item :**
```python
item["matching_results"] = {
    "matched_domains": ["tech_lai_ecosystem"],
    "domain_evaluations": {
        "tech_lai_ecosystem": {
            "bedrock_score": 0.75,
            "threshold_applied": 0.30,
            "threshold_source": "domain_type_thresholds.technology",
            "decision": "matched",
            "confidence": "high",
            "reasoning": "Strong LAI technology signals: Extended-Release Injectable, MedinCell",
            "matched_entities": {
                "companies": ["MedinCell"],
                "technologies": ["Extended-Release Injectable"]
            }
        }
    },
    "fallback_info": {
        "applied": false,
        "reason": "Primary matching succeeded"
    },
    "policy_applied": {
        "min_domain_score": 0.25,
        "domain_type_thresholds": {"technology": 0.30, "regulatory": 0.20},
        "enable_fallback_mode": true
    }
}
```

---

## Phase 3 – Tests Locaux

### 3.1 Script de Test Local

**Fichier :** `scripts/test_matching_v2_config_driven.py`

**Fonctionnalités :**
- Charger échantillon items du dernier run lai_weekly_v3
- Appliquer nouvelle logique de matching avec différents seuils
- Générer rapport comparatif avant/après
- Tester mode fallback et diagnostic

**Scénarios de test :**
1. **Seuils actuels (0.4) :** Reproduire 0 items matchés
2. **Seuils ajustés (0.25) :** Valider 8-12 items matchés
3. **Mode fallback :** Tester pure players (MedinCell facility, Peptron Q3)
4. **Seuils par type :** Vérifier technology vs regulatory
5. **Mode diagnostic :** Valider logs détaillés

### 3.2 Données de Test

**Source :** Dernier run d'ingestion lai_weekly_v3 (15 items)

**Items critiques à tester :**
- **MedinCell+Teva partnership :** Doit matcher tech_lai_ecosystem + regulatory_lai
- **UZEDY® FDA approval :** Doit matcher regulatory_lai (score élevé)
- **MedinCell facility :** Doit matcher via fallback (pure player)
- **Monthly injection trial :** Doit matcher avec seuil 0.30 technology
- **Generic biotech funding :** Doit être rejeté (bruit)

### 3.3 Rapport de Tests Locaux

**Fichier généré :** `docs/diagnostics/matching_v2_config_driven_local_tests.md`

**Contenu attendu :**
- Distribution des scores par configuration testée
- Nombre d'items matchés par domaine et par seuil
- Exemples détaillés avec reasoning Bedrock
- Validation du mode fallback
- Recommandations de seuils finaux

---

## Phase 4 – Déploiement AWS

### 4.1 Stratégie de Déploiement

**Lambda cible :** `vectora-inbox-normalize-score-v2-dev`
**Région :** eu-west-3
**Profil :** rag-lai-prod

**Respect strict src_lambda_hygiene_v4.md :**
- Aucune nouvelle dépendance Python
- Modification de 2 fichiers maximum dans src_v2
- Utilisation des Lambda Layers existantes
- Taille package < 5MB

### 4.2 Packaging et Déploiement

**Commandes de déploiement :**
```bash
# 1. Validation locale
cd src_v2
python -m py_compile vectora_core/normalization/bedrock_matcher.py
python -m py_compile vectora_core/normalization/__init__.py

# 2. Création package
zip -r ../matching-v2-config-driven.zip . -x "*.pyc" "__pycache__/*"

# 3. Déploiement Lambda
aws lambda update-function-code \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --zip-file fileb://matching-v2-config-driven.zip \
  --region eu-west-3 --profile rag-lai-prod

# 4. Mise à jour configuration client
aws s3 cp client-config-examples/lai_weekly_v3.yaml \
  s3://vectora-inbox-config-dev/clients/lai_weekly_v3.yaml \
  --region eu-west-3 --profile rag-lai-prod
```

### 4.3 Variables d'Environnement

**Variables Lambda inchangées :**
- `BEDROCK_MODEL_ID` : Modèle Bedrock pour matching
- `BEDROCK_REGION` : Région Bedrock (us-east-1)
- `CONFIG_BUCKET` : Bucket configuration
- `DATA_BUCKET` : Bucket données

**Aucune nouvelle variable requise** - Configuration via client_config uniquement

---

## Phase 5 – Tests en Situation Réelle + Diagnostics

### 5.1 Test de Validation Production

**Commande de test :**
```bash
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --payload '{"client_id": "lai_weekly_v3", "period_days": 30}' \
  --region eu-west-3 --profile rag-lai-prod \
  response_config_driven.json
```

**Métriques attendues :**
- `items_input` : 15 (identique)
- `items_normalized` : 15 (identique)
- `items_matched` : 8-12 (vs 0 actuellement)
- `items_scored` : 15 (identique)

### 5.2 Analyse des Logs CloudWatch

**Groupe de logs :** `/aws/lambda/vectora-inbox-normalize-score-v2-dev`

**Patterns à rechercher :**
- `"Configuration matching chargée"` : Validation lecture config
- `"Seuil appliqué pour domaine"` : Application seuils par type
- `"Mode fallback activé"` : Détection pure players
- `"Matching policy applied"` : Décisions détaillées

### 5.3 Validation des Résultats

**Critères de succès :**
1. **Items matchés > 0 :** Objectif 8-12 items sur 15
2. **Distribution équilibrée :** 60% tech_lai_ecosystem, 40% regulatory_lai
3. **Qualité préservée :** Top items LAI tous matchés
4. **Fallback fonctionnel :** Pure players détectés
5. **Diagnostic complet :** Reasoning disponible pour chaque décision

### 5.4 Rapport de Production

**Fichier :** `docs/diagnostics/matching_v2_config_driven_production_report.md`

**Structure du rapport :**
```markdown
# Rapport Production : Matching V2 Configuration-Driven

## Métriques Globales
- Items traités : 15/15
- Items matchés : 10/15 (66.7%)
- Domaines actifs : 2/2

## Distribution par Domaine
- tech_lai_ecosystem : 8 items (53%)
- regulatory_lai : 5 items (33%)
- Overlap : 3 items (20%)

## Analyse des Seuils
- Seuil global (0.25) : 7 items passés
- Seuil technology (0.30) : 6 items passés
- Seuil regulatory (0.20) : 4 items passés
- Mode fallback : 3 items récupérés

## Exemples Détaillés
[Items avec matched_domains complet et reasoning]

## Recommandations
[Ajustements de seuils si nécessaire]
```

---

## Phase 6 – Synthèse & Recommandations

### 6.1 Validation des Objectifs

**Objectifs techniques :**
- ✅ Seuils déplacés du code vers configuration
- ✅ Moteur générique réutilisable
- ✅ Mode diagnostic opérationnel
- ✅ Rétrocompatibilité assurée

**Objectifs métier :**
- ✅ Matching rate > 0% (objectif 60-80%)
- ✅ Qualité des matches préservée
- ✅ Pure players LAI détectés
- ✅ Ajustements possibles sans redéploiement

### 6.2 Métriques de Validation

**Métriques techniques :**
- Temps d'exécution : Identique (aucun appel Bedrock supplémentaire)
- Taille package : < 5MB (conformité hygiene_v4)
- Fichiers modifiés : 2 exactement
- Nouvelles dépendances : 0

**Métriques métier :**
- Taux de matching : 60-80% (vs 0% avant)
- Précision : > 90% (pas de faux positifs)
- Rappel : > 80% (capture signaux LAI faibles)
- Flexibilité : Seuils ajustables par client

### 6.3 Recommandations Finales

**Pour lai_weekly_v3 :**
- Seuils initiaux validés : min_domain_score=0.25, technology=0.30, regulatory=0.20
- Mode fallback activé pour pure players
- Mode diagnostic activé pour calibration continue

**Pour autres clients :**
- Template matching_config réutilisable
- Presets par vertical dans canonical
- Documentation des seuils recommandés

**Évolutions futures :**
- Seuils adaptatifs basés sur historique
- Machine learning pour optimisation automatique
- Intégration feedback humain pour amélioration continue

---

## 🔒 Garanties de Conformité

### Respect src_lambda_hygiene_v4.md

**✅ Architecture 3 Lambdas V2 :**
- Modification uniquement de normalize_score_v2
- Aucun impact sur ingest_v2 ou newsletter_v2
- Handlers délèguent à vectora_core

**✅ Aucune nouvelle dépendance :**
- Utilisation uniquement de YAML existant
- Pas de nouvelle lib Python
- Réutilisation infrastructure Bedrock

**✅ Configuration pilote l'engine :**
- Aucun seuil hardcodé dans le code final
- Logique métier dans client_config
- Généricité absolue préservée

**✅ Pas d'usine à gaz :**
- 2 fichiers modifiés maximum
- Fonctions simples et testables
- Pas de sur-architecture

### Isolation et Sécurité

**Changements isolés :**
- Impact limité au matching uniquement
- Normalisation et scoring inchangés
- Rétrocompatibilité totale

**Tests de non-régression :**
- Clients sans matching_config : Comportement identique
- Fallback sur seuils par défaut
- Validation sur autres clients

---

## 📋 Checklist de Validation

### Avant Exécution
- [ ] Documents obligatoires lus et analysés
- [ ] Contraintes hygiene_v4 comprises et respectées
- [ ] Architecture V2 confirmée dans src_v2
- [ ] Environnement AWS validé (eu-west-3, rag-lai-prod)

### Phase 1 - Configuration
- [ ] matching_config étendu dans lai_weekly_v3.yaml
- [ ] Seuils LAI calibrés (0.25, 0.30, 0.20)
- [ ] Mode fallback configuré
- [ ] Mode diagnostic activé

### Phase 2 - Code
- [ ] Paramètre matching_config ajouté à match_watch_domains_with_bedrock()
- [ ] Seuil hardcodé 0.4 supprimé
- [ ] Fonction _apply_matching_policy() implémentée
- [ ] Champ matched_domains enrichi avec diagnostic

### Phase 3 - Tests Locaux
- [ ] Script de test créé et fonctionnel
- [ ] 15 items lai_weekly_v3 testés
- [ ] Rapport local généré avec recommandations
- [ ] Mode fallback validé

### Phase 4 - Déploiement
- [ ] Package créé (< 5MB)
- [ ] Lambda déployée sans erreur
- [ ] Configuration client uploadée sur S3
- [ ] Variables d'environnement vérifiées

### Phase 5 - Production
- [ ] Test complet exécuté
- [ ] Métriques validées (items_matched > 0)
- [ ] Logs CloudWatch analysés
- [ ] Rapport production généré

### Phase 6 - Synthèse
- [ ] Objectifs techniques atteints
- [ ] Objectifs métier validés
- [ ] Recommandations documentées
- [ ] Plan d'évolution défini

---

## 🏁 Rappel Important

**Ce plan ne modifie encore aucun fichier de code. Il doit être validé avant exécution.**

**Validation requise sur :**
1. **Structure matching_config** proposée
2. **Seuils initiaux** pour lai_weekly_v3
3. **Approche technique** de refactoring
4. **Stratégie de déploiement** et tests

**Une fois validé, l'exécution des phases 1-5 peut commencer immédiatement.**

---

**Plan complet et détaillé - Prêt pour validation et exécution**  
**Effort estimé total : 4-5 heures (toutes phases)**  
**Impact attendu : Transformation complète du matching V2 en moteur configuration-driven**