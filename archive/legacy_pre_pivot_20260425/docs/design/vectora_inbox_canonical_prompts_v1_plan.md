# Plan Vectora Inbox - Prompts Canonicalisés V1

**Date** : 2025-12-12  
**Objectif** : Mettre en place une V1 MINIMALE de prompts canonicalisés pour Bedrock  
**Scope** : Normalisation LAI uniquement (pas de refactoring complet)  

---

## 🎯 Philosophie V1

### Principes de Base
- **1 seul fichier global** : `canonical/prompts/global_prompts.yaml` (pas de prompts par client)
- **PromptLoader simple** : Cache + fallback robuste vers prompts hardcodés
- **Feature flag** : `USE_CANONICAL_PROMPTS=true/false` pour activer/désactiver
- **Approche progressive** : Commencer par normalisation LAI, étendre ensuite

### Objectifs V1
1. **Édition facile** : Prompts dans fichiers YAML lisibles
2. **Fallback robuste** : Pas de régression si YAML indisponible
3. **Test ciblé** : Validation sur normalisation LAI uniquement
4. **Déploiement sûr** : Feature flag pour rollback instantané

---

## 📁 Structure Minimale Proposée

### Fichier `canonical/prompts/global_prompts.yaml`

```yaml
# Prompts canonicalisés Vectora Inbox V1
# Date: 2025-12-12
# Scope: Normalisation LAI uniquement

normalization:
  lai_default:
    # Instructions système pour le modèle
    system_instructions: |
      You are a specialized AI assistant for biotech/pharma news analysis.
      Focus on Long-Acting Injectable (LAI) technologies and related entities.
      
    # Template utilisateur avec placeholders
    user_template: |
      Analyze the following biotech/pharma news item and extract structured information.

      TEXT TO ANALYZE:
      {{item_text}}

      EXAMPLES OF ENTITIES TO DETECT:
      - Companies: {{companies_examples}}
      - Molecules/Drugs: {{molecules_examples}}
      - Technologies: {{technologies_examples}}

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

      TASK:
      1. Generate a concise summary (2-3 sentences) explaining the key information
      2. Classify the event type among: clinical_update, partnership, regulatory, scientific_paper, corporate_move, financial_results, safety_signal, manufacturing_supply, other
      3. Extract ALL pharmaceutical/biotech company names mentioned
      4. Extract ALL drug/molecule names mentioned (including brand names, generic names)
      5. Extract ALL technology keywords mentioned - FOCUS on LAI technologies listed above
      6. Extract ALL trademark names mentioned (especially those with ® or ™ symbols)
      7. Extract ALL therapeutic indications mentioned
      8. Evaluate LAI relevance (0-10 score): How relevant is this content to Long-Acting Injectable technologies?
      9. Detect anti-LAI signals: Does the content mention oral routes (tablets, capsules, pills)?
      10. Assess pure player context: Is this about a LAI-focused company without explicit LAI mentions?

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

    # Configuration Bedrock
    bedrock_config:
      max_tokens: 1000
      temperature: 0.0
      anthropic_version: "bedrock-2023-05-31"

# Placeholder pour futurs prompts (Phase 2)
newsletter:
  # À implémenter en Phase 2
  editorial_generation:
    system_instructions: "TBD"
    user_template: "TBD"
    bedrock_config:
      max_tokens: 4000
      temperature: 0.2

matching:
  # À implémenter en Phase 2
  relevance_scoring:
    system_instructions: "TBD"
    user_template: "TBD"
```

---

## 🏗️ Plan d'Implémentation par Phases

### **Phase 1 – Implémentation Locale** (2h)

#### Objectifs
- Créer le PromptLoader minimal
- Migrer le prompt de normalisation LAI vers YAML
- Implémenter le feature flag
- Tests locaux de validation

#### Fichiers à Créer/Modifier
1. **`canonical/prompts/global_prompts.yaml`** (nouveau)
   - Contenu du prompt de normalisation LAI actuel
   - Configuration Bedrock associée

2. **`src/vectora_core/prompts/loader.py`** (nouveau)
   - Classe `PromptLoader` avec cache et fallback
   - Méthodes : `get_prompt()`, `_load_from_s3()`, `_load_from_local()`

3. **`src/vectora_core/normalization/bedrock_client.py`** (modification)
   - Intégration du PromptLoader
   - Feature flag `USE_CANONICAL_PROMPTS`
   - Fallback vers prompt hardcodé existant

#### Critères de Succès Phase 1
- ✅ YAML chargé correctement en local
- ✅ Feature flag fonctionne (on/off)
- ✅ Fallback robuste si YAML indisponible
- ✅ Pas de régression sur prompt existant

#### Tests Prévus
- **Script** : `scripts/test_canonical_prompts_v1.py`
- **Validation** : 3-5 items de test (Nanexa/Moderna, UZEDY, etc.)
- **Comparaison** : Comportement avant/après activation
- **Métriques** : Structure des champs normalisés identique

---

### **Phase 2 – Déploiement AWS DEV** (1h)

#### Objectifs
- Synchroniser YAML vers S3 config bucket
- Déployer Lambdas avec PromptLoader
- Configurer `USE_CANONICAL_PROMPTS=true` en DEV
- Validation end-to-end

#### Actions de Déploiement
1. **Synchronisation Config**
   ```bash
   aws s3 cp canonical/prompts/global_prompts.yaml s3://vectora-inbox-config-dev/canonical/prompts/
   ```

2. **Déploiement Lambdas**
   - Package et déploie `vectora-inbox-ingest-normalize-dev`
   - Mise à jour variables d'environnement : `USE_CANONICAL_PROMPTS=true`

3. **Test End-to-End**
   ```bash
   aws lambda invoke --function-name vectora-inbox-ingest-normalize-dev \
     --payload '{"client_id":"lai_weekly_v3","period_days":1}' \
     --cli-binary-format raw-in-base64-out out-test-canonical.json
   ```

#### Critères de Succès Phase 2
- ✅ YAML accessible depuis Lambda via S3
- ✅ Normalisation fonctionne avec prompts canonicalisés
- ✅ Pas d'erreurs Bedrock supplémentaires
- ✅ Performance maintenue (pas de régression latence)

---

### **Phase 3 – Validation Réelle** (1h)

#### Objectifs
- Run réel lai_weekly_v3 avec prompts canonicalisés
- Comparaison qualité avant/après
- Diagnostic complet et recommandations

#### Run Réel
```bash
# Ingestion + normalisation
aws lambda invoke --function-name vectora-inbox-ingest-normalize-dev \
  --payload '{"client_id":"lai_weekly_v3","period_days":7}' \
  --cli-binary-format raw-in-base64-out out-canonical-ingest.json

# Engine + newsletter
aws lambda invoke --function-name vectora-inbox-engine-dev \
  --payload '{"client_id":"lai_weekly_v3","period_days":7}' \
  --cli-binary-format raw-in-base64-out out-canonical-engine.json
```

#### Évaluation Qualité
- **Entités LAI** : Nanexa/Moderna, UZEDY, MedinCell détectés ?
- **Stabilité** : Pas de crash, erreurs Bedrock normales
- **Latence** : Temps de traitement comparable
- **Structure** : Champs normalisés cohérents

#### Critères de Succès Phase 3
- ✅ Qualité normalisation ≥ version hardcodée
- ✅ Entités LAI-strong détectées (Nanexa/Moderna, UZEDY)
- ✅ Pas de régression sur items existants
- ✅ Newsletter générée sans erreur

---

### **Phase 4 – Documentation & Plan Phase 2** (30min)

#### Livrables
1. **`docs/diagnostics/vectora_inbox_canonical_prompts_v1_normalization_results.md`**
   - Métriques avant/après
   - Items LAI-strong récupérés/perdus
   - Recommandations

2. **`docs/diagnostics/vectora_inbox_canonical_prompts_v1_executive_summary.md`**
   - Synthèse exécutive
   - Stabilité et qualité
   - Recommandation pour activation permanente

3. **`docs/design/vectora_inbox_canonical_prompts_phase2_plan.md`** (si succès)
   - Extension aux prompts newsletter
   - Extension aux prompts matching/scoring
   - Stratégie de déploiement progressive

---

## ⚠️ Risques et Mitigations

### Risques Identifiés
1. **Régression qualité** : Prompt YAML différent du hardcodé
2. **Erreurs S3** : YAML inaccessible en runtime
3. **Performance** : Latence supplémentaire pour chargement
4. **Parsing YAML** : Erreurs de format ou placeholders

### Mesures de Mitigation
1. **Tests exhaustifs** : Validation sur dataset historique
2. **Fallback robuste** : Retour automatique vers prompt hardcodé
3. **Cache local** : Éviter rechargement S3 à chaque appel
4. **Feature flag** : Désactivation instantanée si problème
5. **Monitoring** : Logs détaillés pour debugging

### Critères d'Arrêt
- Régression >10% sur détection entités LAI
- Erreurs Bedrock >20% vs baseline
- Latence >50% vs baseline
- Échec parsing YAML >5% des cas

---

## 🎯 Métriques de Succès V1

### Métriques Techniques
- **Disponibilité** : YAML chargé >99% des appels
- **Performance** : Latence <+10% vs prompt hardcodé
- **Stabilité** : Taux d'erreur <5%
- **Fallback** : Activation automatique si YAML indisponible

### Métriques Qualité
- **Entités LAI** : Détection ≥ niveau actuel
- **Structure JSON** : Champs normalisés cohérents
- **Nanexa/Moderna** : Détecté avec score >8
- **UZEDY** : Détecté avec trademark reconnu

### Métriques Métier
- **Édition prompts** : Temps de modification <5min
- **Déploiement** : Mise à jour sans redéploiement Lambda
- **Rollback** : Retour version précédente <1min
- **Maintenance** : Prompts versionnés et documentés

---

## 🚀 Prochaines Étapes

### Validation Immédiate
1. **Revue technique** : Validation approche PromptLoader
2. **Approbation** : Accord pour exécution Phase 1
3. **Calendrier** : Planification 4h total (2h+1h+1h+30min)

### Post-V1 (si succès)
1. **Phase 2** : Extension prompts newsletter et matching
2. **Prompts par client** : Si besoin de personnalisation
3. **Versioning** : Gestion versions prompts avec rollback
4. **A/B Testing** : Comparaison prompts différents

---

**Ce plan permet de tester la canonicalisation des prompts de manière progressive et sûre, en commençant par la normalisation LAI qui est critique pour la qualité du signal.**