# Vectora Inbox - Plan Phase 2 : Canonicalisation Prompts Newsletter & Matching

**Date** : 2025-12-12  
**Version** : 1.0  
**Scope** : Extension canonicalisation aux prompts newsletter et matching/scoring uniquement

---

## Phase 0 – Analyse & Plan Phase 2 (TERMINÉ)

### Inventaire des prompts Bedrock identifiés

#### 1. Prompts Newsletter (src/vectora_core/newsletter/bedrock_client.py)

**Fonction principale** : `_build_ultra_compact_prompt()`
- **Type** : Génération éditoriale newsletter
- **Structure attendue** : JSON avec title, intro, tldr, sections
- **Paramètres clés** : sections_data, client_profile, target_date
- **Usage** : Génération de texte éditorial via Bedrock pour newsletter finale

**Prompt actuel** : Ultra-compact (-80% tokens vs version initiale)
```python
def _build_ultra_compact_prompt(sections_data, client_profile, target_date):
    # Prompt inline hardcodé dans le code
    return f"""JSON newsletter for {client_name} - {target_date}:
    {items_text}
    Output: {{"title":"{client_name} – {target_date}",...}}
    Rules: JSON only, concise, preserve names."""
```

#### 2. Prompts Matching/Scoring (ANALYSE)

**Résultat** : Aucun prompt Bedrock identifié dans le matching/scoring
- `src/vectora_core/matching/matcher.py` : Logique déterministe (intersections d'ensembles)
- `src/vectora_core/scoring/scorer.py` : Calculs numériques (pas d'appel Bedrock)

**Conclusion** : Phase 2B (matching/scoring) = N/A

---

## Plan Phase 2 : Scope Réduit

### Phase 2A : Prompts Newsletter (SEUL BLOC À IMPLÉMENTER)

#### Objectif
Externaliser le prompt newsletter hardcodé vers `canonical/prompts/global_prompts.yaml`

#### Prompts à canonicaliser
1. **newsletter.editorial_generation** : Prompt principal de génération éditoriale

#### Structure YAML proposée
```yaml
newsletter:
  editorial_generation:
    system_instructions: |
      You are an expert newsletter editor for biotech/pharma intelligence.
      Generate concise, professional content in JSON format.
      
    user_template: |
      JSON newsletter for {{client_name}} - {{target_date}}:
      
      {{items_text}}
      
      Output:
      {"title":"{{client_name}} – {{target_date}}","intro":"1 sentence","tldr":["point1","point2"],"sections":[{"section_title":"name","section_intro":"1 sentence","items":[{"title":"title","rewritten_summary":"2 sentences","url":"#"}]}]}
      
      Rules: JSON only, concise, preserve names.
      
    bedrock_config:
      max_tokens: 4000
      temperature: 0.2
      anthropic_version: "bedrock-2023-05-31"
```

#### Extension PromptLoader
- Réutiliser `src/vectora_core/prompts/loader.py` existant
- Méthode : `get_prompt("newsletter.editorial_generation")`
- Pas de modification du loader nécessaire

#### Feature Flag
- **Option 1** : Réutiliser `USE_CANONICAL_PROMPTS` existant
- **Option 2** : Créer `USE_CANONICAL_PROMPTS_NEWSLETTER` dédié
- **Choix** : Option 1 (simplicité)

#### Intégration Code
Modifier `src/vectora_core/newsletter/bedrock_client.py::_build_ultra_compact_prompt()` :
```python
def _build_ultra_compact_prompt(sections_data, client_profile, target_date):
    # Tentative prompt canonicalisé
    if os.environ.get('USE_CANONICAL_PROMPTS', 'false').lower() == 'true':
        prompt_loader = get_prompt_loader(config_bucket)
        canonical_prompt = prompt_loader.get_prompt("newsletter.editorial_generation")
        if canonical_prompt:
            return _build_prompt_from_canonical(canonical_prompt, sections_data, client_profile, target_date)
    
    # Fallback : prompt hardcodé actuel
    return _build_hardcoded_prompt(sections_data, client_profile, target_date)
```

#### Tests Locaux
Script : `scripts/test_canonical_prompts_newsletter_v1.py`
- Charger items normalisés gold (Nanexa/Moderna, UZEDY, MedinCell)
- Générer newsletter avec prompt hardcodé vs YAML
- Vérifier structure JSON valide et contenu cohérent

#### Tests AWS DEV
- Pattern d'invocation : `lai_weekly_v3` complet (ingestion + engine + newsletter)
- Période : 7 jours standard
- Commande : AWS CLI avec payload JSON + encodage base64

#### Critères de Succès
- Pas de régression : newsletter générée sans erreur
- Structure JSON identique
- Contenu éditorial cohérent (mêmes sections, items principaux)
- Performance similaire (latence Bedrock)

### Phase 2B : Prompts Matching/Scoring (N/A)

**Statut** : Non applicable
**Raison** : Aucun prompt Bedrock identifié dans le matching/scoring
**Documentation** : Matching = logique déterministe, Scoring = calculs numériques

---

## Exclusions Explicites

### Phase 2C – Optimisations d'architecture (EXCLU)
- Pas de refactoring architectural général
- Pas d'optimisation des performances Bedrock
- Pas de migration vers d'autres modèles

### Phase 2D – Préparation multi-client (EXCLU)
- Pas de support multi-client
- Pas de prompts par client
- Pas de templates dynamiques avancés

---

## Planning d'Exécution

### Phase 1 : Implémentation Locale (Newsletter)
1. Mise à jour `canonical/prompts/global_prompts.yaml`
2. Modification `bedrock_client.py` avec feature flag + fallback
3. Tests locaux avec script dédié
4. Documentation résultats

### Phase 2 : Déploiement AWS DEV
1. Re-package et déploiement Lambda engine
2. Synchronisation prompts YAML vers S3
3. Configuration feature flag en DEV
4. Run réel `lai_weekly_v3` complet

### Phase 3 : Validation & Synthèse
1. Diagnostic complet (logs, outputs, performance)
2. Comparaison pré/post canonicalisation
3. Recommandations finales

---

## Livrables Attendus

### Documentation
- `docs/diagnostics/vectora_inbox_canonical_prompts_phase2_newsletter_local_results.md`
- `docs/diagnostics/vectora_inbox_canonical_prompts_phase2_real_run_results.md`
- `docs/diagnostics/vectora_inbox_canonical_prompts_phase2_executive_summary.md`

### Code
- `canonical/prompts/global_prompts.yaml` (mise à jour)
- `src/vectora_core/newsletter/bedrock_client.py` (modification)
- `scripts/test_canonical_prompts_newsletter_v1.py` (nouveau)

### Tests
- Tests locaux newsletter (hardcodé vs YAML)
- Run AWS DEV réel avec validation complète

---

## Risques & Mitigations

### Risques Identifiés
1. **Régression newsletter** : Prompt YAML différent du hardcodé
2. **Erreur parsing JSON** : Template YAML mal formaté
3. **Performance dégradée** : Overhead chargement YAML

### Mitigations
1. **Fallback robuste** : Retour automatique au prompt hardcodé
2. **Tests exhaustifs** : Validation structure JSON + contenu
3. **Monitoring** : Logs détaillés + métriques performance

---

## Critères de Validation Finale

### Technique
- [ ] Newsletter générée sans erreur
- [ ] Structure JSON identique
- [ ] Pas de régression performance (< +10% latence)
- [ ] Feature flag fonctionnel (on/off)

### Métier
- [ ] Contenu éditorial cohérent
- [ ] Mêmes sections principales
- [ ] Items gold présents (Nanexa/Moderna, UZEDY, MedinCell)
- [ ] Style et tone préservés

### Opérationnel
- [ ] Déploiement AWS DEV réussi
- [ ] Run `lai_weekly_v3` complet OK
- [ ] Logs CloudWatch propres
- [ ] Outputs S3 conformes

---

**Phase 0 TERMINÉE - Passage en Phase 1**