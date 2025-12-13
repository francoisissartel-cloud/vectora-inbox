# Vectora Inbox LAI Weekly v3 - Plan de Diagnostic MVP Gap Analysis

**Objectif** : Diagnostic structuré "plan vs réalité" pour identifier pourquoi le dernier run lai_weekly_v3 ne respecte pas le plan métier défini.

**Contraintes** :
- Basé UNIQUEMENT sur l'état réel du repo local et AWS DEV
- Utiliser le DERNIER run réel lai_weekly_v3 (pas de simulation)
- Si une étape AWS échoue, documenter et s'arrêter (pas de fabrication de résultats)

---

## Phase 1 – Vérification du Plan "Human Feedback"

### Objectifs
- Lire et résumer les documents de référence du plan
- Extraire la liste des items "LAI-strong" à conserver absolument
- Extraire la liste des patterns de bruit à exclure
- Créer un tableau de référence gold vs noise

### Livrables
- `docs/diagnostics/vectora_inbox_lai_weekly_v3_gold_vs_noise_reference.md`

### Actions
1. Analyser `vectora_inbox_lai_weekly_v2_human_feedback_analysis_and_improvement_plan.md`
2. Analyser `vectora_inbox_lai_weekly_v2_human_review_sheet.md`
3. Extraire les items critiques :
   - **Gold** : Nanexa/Moderna PharmaShell, UZEDY regulatory/extension, MedinCell malaria grant
   - **Noise** : HR, corporate moves, résultats financiers secs
4. Créer le tableau synthèse avec colonnes : id, source_key, date, titre, catégorie, justification

---

## Phase 2 – Vérification Implémentation Plan → Repo Local

### Objectifs
- Vérifier point par point si le plan "human feedback" est implémenté dans le repo local
- Identifier les écarts entre plan théorique et configuration locale

### Livrables
- `docs/diagnostics/vectora_inbox_lai_weekly_v3_plan_vs_repo_local.md`

### Actions
1. Vérifier `technology_scopes.yaml` : PharmaShell, UZEDY, termes LAI ajoutés ?
2. Vérifier `exclusion_scopes.yaml` : HR, finance, etc. présents ?
3. Vérifier `trademark_scopes.yaml` : UZEDY & co présents ?
4. Vérifier `domain_matching_rules.yaml` : logique LAI renforcée ?
5. Vérifier `scoring_rules.yaml` : bonus pure_player, trademark, malus finance ?
6. Pour chaque point : statut "OK en local" ou "MANQUE en local"

---

## Phase 3 – Vérification Repo Local → AWS DEV (Deployment Gap)

### Objectifs
- Comparer le repo local avec les fichiers déployés sur AWS DEV
- Identifier les écarts de déploiement
- Corriger UNIQUEMENT les écarts strictement nécessaires

### Livrables
- `docs/diagnostics/vectora_inbox_lai_weekly_v3_repo_vs_aws_dev_gap.md`

### Actions
1. Comparer avec `s3://vectora-inbox-config-dev/canonical/`
2. Comparer avec `s3://vectora-inbox-config-dev/clients/`
3. Vérifier la config des Lambdas (code package/handler)
4. Identifier les écarts critiques
5. Corriger UNIQUEMENT les écarts bloquants pour la cohérence

---

## Phase 4 – Tracing Items Clés sur le DERNIER Run Réel

### Objectifs
- Tracer les items critiques dans le dernier run lai_weekly_v3 (104 items)
- Identifier à quelle étape disparaissent les items "gold"
- Identifier pourquoi les items "noise" passent encore

### Livrables
- `docs/diagnostics/vectora_inbox_lai_weekly_v3_item_traces.md`

### Actions
1. Récupérer les artifacts du dernier run lai_weekly_v3 :
   - Items ingérés bruts
   - Items normalisés
   - Résultats matching/scoring
   - Newsletter finale
2. Tracer spécifiquement :
   - **Nanexa/Moderna PharmaShell** : où disparaît-il ?
   - **UZEDY regulatory/extension** : où disparaît-il ?
   - **MedinCell malaria grant** : où disparaît-il ?
   - **Items HR/finance** : pourquoi passent-ils ?
3. Créer tableau avec colonnes :
   - id/titre/source_key/date
   - ingéré ? normalisé ? matché ? score final ? dans newsletter ?
   - diagnostic de l'échec pour chaque étape

---

## Phase 5 – Recommandations P0 (Fonctionnalité)

### Objectifs
- Proposer 2-4 corrections P0 maximum
- Garantir que les items "gold" passent
- Éliminer les patterns de bruit les plus grossiers

### Livrables
- `docs/diagnostics/vectora_inbox_lai_weekly_v3_p0_recommendations.md`

### Actions
1. Analyser les causes racines identifiées en Phase 4
2. Proposer corrections minimales et ciblées
3. Prioriser : robustesse items "gold" > élimination bruit
4. NE PAS appliquer les corrections (juste documenter)

---

## Résumé Exécutif Final

À la fin du diagnostic, produire un résumé exécutif avec :
- Ce qui est vraiment en place vs ce que le plan promettait
- Où disparaissent les items Nanexa/UZEDY/MedinCell malaria
- Pourquoi HR/finance passent encore
- 2-4 recommandations P0 à appliquer en priorité

---

## Règles d'Exécution

1. **Pas de simulation** : Utiliser uniquement les vrais artifacts du dernier run
2. **Arrêt sur échec** : Si une étape AWS échoue, documenter et s'arrêter
3. **Annonce de phase** : Écrire explicitement "Phase X terminée, je passe à la phase suivante"
4. **AWS CLI PowerShell** : Utiliser la méthode base64 qui fonctionne (pas InvalidRequestContentException)
5. **Pas de corrections** : Documenter seulement, ne pas appliquer de changements