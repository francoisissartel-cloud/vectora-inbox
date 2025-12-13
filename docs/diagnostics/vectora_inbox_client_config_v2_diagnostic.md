# Diagnostic Vectora Inbox - Configuration Client v2

## Résumé Exécutif

Ce diagnostic analyse l'état actuel du système de configuration client de Vectora Inbox et propose une évolution vers un template v2 plus robuste et explicite. L'analyse porte sur le pipeline complet : ingestion → normalisation → matching → scoring → newsletter.

### État Actuel vs Cible

**État actuel** : Configuration fonctionnelle mais avec des zones d'ambiguïté sur l'utilisation des `technology_profiles`, des `trademark_scopes`, et des `ingestion_profiles`.

**Cible v2** : Configuration explicite et documentée, avec une articulation claire entre les différents niveaux (canonical, client_config, runtime).

---

## 1. Analyse du Pipeline Actuel (lai_weekly.yaml)

### 1.1 Configuration Source → Ingestion

**Flux actuel** :
```
client_config.source_bouquets_enabled → source_catalog.yaml → ingestion_profiles.yaml → ingestion effective
```

**Exemple concret pour LAI Weekly** :
1. `lai_weekly.yaml` déclare : `source_bouquets_enabled: ["lai_press_mvp", "lai_corporate_mvp"]`
2. `source_catalog.yaml` définit ces bouquets :
   - `lai_corporate_mvp` : 5 sources corporate (MedinCell, Camurus, etc.) avec `ingestion_profile: "corporate_pure_player_broad"`
   - `lai_press_mvp` : 3 sources presse (FierceBiotech, etc.) avec `ingestion_profile: "press_technology_focused"`
3. `ingestion_profiles.yaml` définit les critères de pré-filtrage :
   - `corporate_pure_player_broad` : ingère quasiment tout (stratégie `broad_ingestion`)
   - `press_technology_focused` : ingère seulement si signaux LAI détectés (stratégie `multi_signal_ingestion`)

**✅ Points forts** :
- Séparation claire entre bouquets (réutilisables) et profils d'ingestion (logique métier)
- Profils d'ingestion bien documentés avec rationale métier
- Articulation cohérente entre source_type et ingestion_profile

**⚠️ Points d'amélioration** :
- Les `ingestion_profiles` référencent des scopes (ex: `lai_keywords.core_phrases`) mais la connexion avec `technology_profiles` n'est pas explicite
- Pas de mécanisme pour override les profils d'ingestion au niveau client

### 1.2 Configuration Watch Domains → Matching

**Flux actuel** :
```
client_config.watch_domains → scopes (company/molecule/technology/trademark) → domain_matching_rules.yaml → sélection items
```

**Exemple concret pour LAI Weekly** :
1. `lai_weekly.yaml` définit un domaine `tech_lai_ecosystem` avec :
   - `technology_scope: "lai_keywords"`
   - `company_scope: "lai_companies_global"`
   - `molecule_scope: "lai_molecules_global"`
2. `technology_scopes.yaml` définit `lai_keywords` avec `_metadata.profile: technology_complex`
3. `domain_matching_rules.yaml` définit le profil `technology_complex` avec des règles sophistiquées

**✅ Points forts** :
- Logique de matching déclarative et configurable
- Profil `technology_complex` bien conçu pour gérer la complexité LAI
- Règles modulaires par type de domaine (technology, indication, regulatory)

**⚠️ Points d'amélioration** :
- La connexion entre `_metadata.profile: technology_complex` et son utilisation effective n'est pas documentée dans le client_config
- Pas de `trademark_scope` déclaré dans `lai_weekly.yaml` alors que `trademark_scopes.yaml` existe
- Les règles de matching ne mentionnent pas explicitement comment les trademarks sont traités

### 1.3 Configuration Matching → Scoring → Newsletter

**Flux actuel** :
```
items matchés → scoring_rules.yaml → sélection finale → newsletter_layout
```

**Exemple concret pour LAI Weekly** :
1. Items matchés par `domain_matching_rules.yaml`
2. Scoring selon `scoring_rules.yaml` avec bonus pour `pure_player_scope: "lai_companies_mvp_core"`
3. Sélection selon `newsletter_layout` (max 5 items pour "top_signals", max 3 pour "partnerships_deals")

**✅ Points forts** :
- Scoring rules bien structurées avec poids métier explicites
- Bonus pour pure players aligné avec la stratégie LAI
- Newsletter layout simple et efficace

**⚠️ Points d'amélioration** :
- Pas de bonus explicite pour les trademarks dans `scoring_rules.yaml`
- Les `match_confidence_multiplier` et `signal_quality_weight` sont définis mais leur utilisation n'est pas documentée

---

## 2. Analyse des Technology Profiles (Simple vs Complex)

### 2.1 Définition Actuelle

Dans `technology_scopes.yaml` :
```yaml
lai_keywords:
  _metadata:
    profile: technology_complex
    description: "Long-Acting Injectables - requires multiple signal types for matching"
```

Dans `domain_matching_rules.yaml` :
```yaml
technology_profiles:
  technology_complex:
    signal_requirements:
      high_precision_signals: [core_phrases, technology_terms_high_precision]
      supporting_signals: [route_admin_terms, interval_patterns]
      # ... logique sophistiquée
```

### 2.2 Utilisation Effective

**✅ Ce qui fonctionne** :
- Le profil `technology_complex` est bien défini avec une logique multi-signaux
- La catégorisation des signaux (high_precision, supporting, context) est pertinente
- Les règles de combinaison sont explicites

**⚠️ Ce qui manque** :
- **Question clé** : Est-ce que le fait de mettre `_metadata.profile: technology_complex` suffit à déclencher la logique dans tout le pipeline ?
- **Réponse** : Non, actuellement il faut que le runtime interprète cette métadonnée. Le client_config ne déclare pas explicitement qu'il veut utiliser le profil `technology_complex`.
- **Conséquence** : Ambiguïté sur qui décide d'utiliser quel profil (canonical vs client_config vs runtime)

### 2.3 Recommandation

Le client_config v2 devrait explicitement déclarer les profils de matching à utiliser :
```yaml
watch_domains:
  - id: "tech_lai_ecosystem"
    technology_scope: "lai_keywords"
    technology_profile: "technology_complex"  # ← Explicite
```

---

## 3. Analyse des Trademark Scopes

### 3.1 État Actuel

**Définition** : `trademark_scopes.yaml` contient `lai_trademarks_global` avec 80+ noms de marque LAI.

**Utilisation actuelle** :
- ✅ Référencés dans `ingestion_profiles.yaml` (ex: `trademark_signals` dans `press_technology_focused`)
- ❌ **PAS référencés dans `lai_weekly.yaml`** (pas de `trademark_scope` dans les watch_domains)
- ❌ **PAS de règles spécifiques dans `domain_matching_rules.yaml`**
- ❌ **PAS de bonus spécifique dans `scoring_rules.yaml`**

### 3.2 Règles Métier Manquantes

Pour respecter les exigences métier, les trademarks devraient avoir un traitement privilégié :

**Ingestion** : ✅ Partiellement implémenté
- Les profils d'ingestion incluent des `trademark_signals` avec poids élevé
- Mais pas de règle "toujours ingérer si trademark détecté"

**Matching** : ❌ Non implémenté
- Pas de règle "toujours matcher si trademark du scope détecté"
- Les trademarks ne sont pas traités comme des signaux forts dans `domain_matching_rules.yaml`

**Scoring** : ❌ Non implémenté
- Pas de `trademark_bonus` dans `scoring_rules.yaml`
- Les trademarks ne remontent pas automatiquement en tête de liste

### 3.3 Recommandation

Le client_config v2 devrait :
1. Déclarer explicitement les `trademark_scope` dans les watch_domains
2. Les règles de matching et scoring devraient traiter les trademarks comme des signaux privilégiés

---

## 4. Zones d'Ambiguïté et Fragilités

### 4.1 Connexion Canonical ↔ Client Config

**Problème** : Le client_config référence des clés de scopes (ex: `"lai_keywords"`) mais ne contrôle pas leur configuration interne.

**Exemple** : Si on change `lai_keywords._metadata.profile` de `technology_complex` à `technology_simple`, est-ce que le comportement du client change automatiquement ?

**Recommandation** : Le client_config v2 devrait être plus explicite sur les profils et comportements attendus.

### 4.2 Profils d'Ingestion vs Watch Domains

**Problème** : Double logique de filtrage pas toujours cohérente.

**Exemple** : 
- `press_technology_focused` filtre selon `lai_keywords + lai_companies + lai_trademarks`
- `watch_domains.tech_lai_ecosystem` matche selon `lai_keywords + lai_companies + lai_molecules` (pas de trademark_scope)

**Recommandation** : Aligner les scopes utilisés pour l'ingestion et le matching.

### 4.3 Runtime vs Configuration

**Problème** : Certaines logiques sont codées en dur dans le runtime plutôt que configurables.

**Exemple** : Les `match_confidence_multiplier` sont définis dans `scoring_rules.yaml` mais leur calcul dépend du code Python.

**Recommandation** : Documenter clairement ce qui est configurable vs ce qui nécessite des modifications code.

---

## 5. Propositions d'Amélioration Runtime

### 5.1 Fichiers à Modifier (Phase Ultérieure)

**Ingestion** :
- `src/vectora_core/ingestion/ingestion_profiles.py` : Implémenter la logique "toujours ingérer si trademark"
- `src/vectora_core/ingestion/signal_detection.py` : Améliorer la détection des trademarks

**Matching** :
- `src/vectora_core/matching/domain_matcher.py` : Implémenter les règles trademark privilégiées
- `src/vectora_core/matching/technology_profiles.py` : Assurer la connexion `_metadata.profile` → logique effective

**Scoring** :
- `src/vectora_core/scoring/scorer.py` : Ajouter les bonus trademark
- `src/vectora_core/scoring/signal_quality.py` : Implémenter les `signal_quality_weight`

### 5.2 Nouvelles Fonctionnalités à Développer

1. **Trademark Privilege Engine** : Logique transversale pour traiter les trademarks comme signaux forts
2. **Profile Resolution Engine** : Résolution automatique des profils depuis les métadonnées canonical
3. **Configuration Validation** : Validation de cohérence entre client_config, canonical, et runtime

---

## 6. Conclusion et Prochaines Étapes

### 6.1 État de Maturité

**Fonctionnel** : Le système actuel fonctionne pour le MVP LAI avec des résultats satisfaisants.

**Améliorable** : Plusieurs zones d'ambiguïté et de sous-utilisation des capacités (notamment trademarks).

### 6.2 Priorités pour le Template v2

1. **Expliciter les profils** : technology_profile, matching_profile dans le client_config
2. **Intégrer les trademarks** : trademark_scope dans watch_domains + règles privilégiées
3. **Documenter les connexions** : canonical → client_config → runtime
4. **Simplifier la maintenance** : template commenté et exemples clairs

### 6.3 Impact Métier

**Pour LAI** : Meilleure détection des signaux trademark, matching plus précis, scoring plus pertinent.

**Pour les futurs verticaux** : Template réutilisable et extensible, moins d'ambiguïtés, maintenance simplifiée.

---

*Diagnostic réalisé le 2024-12-19 - Base : lai_weekly.yaml + canonical v1.0.0*