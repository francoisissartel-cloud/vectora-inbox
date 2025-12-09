# Plan de Correction – Tuning Bedrock Output

**Date** : 2025-12-08  
**Auteur** : Amazon Q Developer  
**Statut** : EN COURS  
**Version** : 1.0

---

## 1. Résumé du Problème

### 1.1 Symptômes

- ❌ **JSON tronqué** : La réponse Bedrock s'arrête au milieu d'une phrase ("...and geographic")
- ❌ **Parsing impossible** : `json.JSONDecodeError` car le JSON est incomplet
- ❌ **Markdown non exploitable** : Le fichier `newsletter.md` contient du JSON brut tronqué au lieu d'un Markdown structuré
- ❌ **Sections vides** : Les champs `tldr` et `sections` sont vides dans le JSON parsé

### 1.2 Logs Clés

```
[WARNING] Réponse Bedrock non-JSON (Expecting value: line 1 column 1 (char 0)), tentative d'extraction manuelle
[ERROR] Réponse brute complète: {...truncated at "...and geographic"}
[ERROR] Longueur de la réponse: ~500 caractères
```

### 1.3 Contexte

- **Newsletter** : `lai_weekly` avec 2 sections, ~5 items
- **Modèle** : Claude Sonnet 4.5 via inference profile `eu.anthropic.claude-sonnet-4-5-20250929-v1:0`
- **Configuration actuelle** : `max_tokens=3000`
- **Réponse attendue** : JSON structuré avec titre, intro, TL;DR, 2 sections avec 5 items

---

## 2. Hypothèse et Décisions de Design

### 2.1 Hypothèse Principale

**`max_tokens=3000` est insuffisant** pour générer un JSON structuré complet contenant :
- Titre (~50 tokens)
- Introduction (~100 tokens)
- TL;DR (3-5 bullets, ~150 tokens)
- 2 sections avec intro (~100 tokens chacune)
- 5 items avec résumés réécrits (~200 tokens par item = 1000 tokens)
- Structure JSON (clés, guillemets, accolades, ~200 tokens)

**Total estimé** : ~2000-2500 tokens minimum, mais avec marge de sécurité nécessaire.

### 2.2 Décision : Augmenter max_tokens

**Action** : Passer de `max_tokens=3000` à `max_tokens=8000`

**Justification** :
- Permet de générer des réponses complètes même avec des newsletters plus longues
- Marge de sécurité pour éviter les troncatures
- Coût acceptable car fréquence faible (1 newsletter / client / période)

### 2.3 Décision : Renforcer le Prompt

**Action** : Améliorer le prompt pour :
- Forcer un JSON compact et concis
- Limiter la verbosité des résumés (2-3 phrases max)
- Rappeler explicitement : "Réponds uniquement avec un JSON valide, sans texte avant/après"

**Justification** :
- Réduit le risque de dépassement même avec `max_tokens=8000`
- Améliore la qualité éditoriale (concision)
- Évite les balises markdown (```json) qui compliquent le parsing

---

## 3. Risques et Impacts

### 3.1 Risques

**Coût** : Augmentation du coût par appel Bedrock (~2.5x si on utilise les 8000 tokens)
- **Impact** : Faible car fréquence faible (1 newsletter / client / semaine)
- **Estimation** : ~$0.024 par newsletter (vs ~$0.009 actuellement) avec Claude Sonnet 4.5

**Latence** : Temps de génération légèrement plus long
- **Impact** : Faible (+2-3 secondes estimées)
- **Acceptable** : Temps total reste sous 30 secondes

**Verbosité** : Risque de réponses trop longues si le prompt n'est pas assez strict
- **Mitigation** : Renforcer les consignes de concision dans le prompt

### 3.2 Impacts Positifs

- ✅ JSON complet et valide
- ✅ Markdown structuré et lisible
- ✅ Newsletter exploitable par le client
- ✅ Pas de régression sur les autres composants

---

## 4. Plan d'Exécution

### Phase 1 – Tuning Bedrock

**Objectif** : Corriger la configuration Bedrock pour obtenir des réponses complètes

**Tâches** :
1. Mettre à jour `max_tokens` de 3000 à 8000 dans `bedrock_client.py`
2. Améliorer le prompt pour :
   - Renforcer la consigne "JSON only, no markdown blocks"
   - Limiter la longueur des résumés (2-3 phrases max)
   - Ajouter un exemple de JSON compact
3. Vérifier que `generate_editorial_content()` gère correctement les erreurs

**Fichiers modifiés** :
- `src/vectora_core/newsletter/bedrock_client.py`

**Durée estimée** : 10 minutes

---

### Phase 2 – Implémentation & Déploiement

**Objectif** : Déployer le patch en DEV

**Tâches** :
1. Rebuild du package Lambda engine :
   ```powershell
   cd src/lambdas/engine
   Remove-Item -Recurse -Force package -ErrorAction SilentlyContinue
   mkdir package
   pip install -r ../../../requirements.txt -t package/
   Copy-Item handler.py package/
   Copy-Item -Recurse ../../vectora_core package/
   cd package
   Compress-Archive -Path * -DestinationPath ../engine-latest.zip -Force
   ```

2. Upload vers S3 :
   ```powershell
   aws s3 cp engine-latest.zip s3://vectora-inbox-lambda-code-dev/lambda/engine/latest.zip --profile rag-lai-prod --region eu-west-3
   ```

3. Mise à jour de la Lambda :
   ```powershell
   aws lambda update-function-code --function-name vectora-inbox-engine-dev --s3-bucket vectora-inbox-lambda-code-dev --s3-key lambda/engine/latest.zip --profile rag-lai-prod --region eu-west-3
   ```

**Durée estimée** : 5 minutes

---

### Phase 3 – Test End-to-End de Validation

**Objectif** : Valider que le problème est résolu

**Tâches** :
1. Invoquer la Lambda avec le payload de test :
   ```json
   {
     "client_id": "lai_weekly",
     "period_days": 7
   }
   ```

2. Vérifier la réponse Lambda :
   - `statusCode: 200`
   - `items_selected > 0`
   - `sections_generated > 0`
   - `s3_output_path` présent

3. Télécharger et inspecter `newsletter.md` depuis S3 :
   - Vérifier que le fichier contient du Markdown structuré (pas de JSON brut)
   - Vérifier la présence de : titre, intro, TL;DR, sections, items
   - Vérifier que le texte n'est pas tronqué

4. Consulter les logs CloudWatch :
   - Vérifier l'absence d'erreur de parsing JSON
   - Vérifier que la réponse Bedrock est complète
   - Noter la longueur de la réponse (en caractères)

**Critères de succès** :
- ✅ JSON parsé sans erreur
- ✅ Markdown structuré et complet
- ✅ Pas de troncature visible
- ✅ Temps d'exécution < 30 secondes

**Durée estimée** : 10 minutes

---

### Phase 4 – Plan B en Cas d'Échec

**Si le JSON est encore tronqué ou invalide** :

**Option A** : Augmenter encore `max_tokens` (8000 → 12000)
- Tester si le problème persiste
- Analyser la longueur réelle nécessaire

**Option B** : Réduire le contenu demandé
- Limiter le nombre d'items par section (5 → 3)
- Raccourcir les résumés (2-3 phrases → 1-2 phrases)
- Supprimer le TL;DR si nécessaire

**Option C** : Appels Bedrock multiples
- Générer le titre + intro dans un premier appel
- Générer chaque section dans un appel séparé
- Assembler les résultats
- **Inconvénient** : Coût et latence plus élevés

**Option D** : Changer de modèle
- Tester avec Claude Sonnet 3.5 (plus rapide, moins verbeux)
- Tester avec Claude Haiku (plus économique)

---

## 5. Métriques de Validation

### 5.1 Métriques Techniques

- **Longueur de la réponse Bedrock** : Doit être > 1500 caractères (actuellement ~500)
- **Validité du JSON** : Parsing sans erreur
- **Complétude du JSON** : Présence de tous les champs (title, intro, tldr, sections)
- **Temps d'exécution** : < 30 secondes (actuellement ~20s)

### 5.2 Métriques Qualitatives

- **Lisibilité du Markdown** : Structure claire (titres, sections, items)
- **Qualité éditoriale** : Textes cohérents et concis
- **Respect du ton** : Ton professionnel et factuel
- **Pas d'hallucination** : Noms et faits exacts

---

## 6. Documentation Post-Exécution

### 6.1 Diagnostic de Résultats

Créer `docs/diagnostics/vectora_inbox_bedrock_output_tuning_results.md` avec :
- Changements effectués (max_tokens, prompt)
- Résultats des tests (JSON valide, Markdown complet)
- Chemin S3 de la newsletter générée
- Temps d'exécution
- Extrait du Markdown (titre + première section)
- Logs CloudWatch pertinents

### 6.2 Mise à Jour du CHANGELOG

Ajouter une entrée dans `CHANGELOG.md` :
```markdown
## [2025-12-08] – Correction Bedrock Output Tuning

### Fixed
- **Problème de JSON tronqué** : Augmentation de `max_tokens` de 3000 à 8000
- **Markdown non exploitable** : Amélioration du prompt pour forcer un JSON compact
- **Parsing JSON** : Gestion robuste des réponses Bedrock

### Changed
- `bedrock_client.py` : `max_tokens=8000` (était 3000)
- Prompt Bedrock : Consignes renforcées pour JSON compact et concis

### Status
- Lambda `vectora-inbox-engine-dev` : 🟢 **GREEN** (fonctionnel de bout en bout)
```

---

## 7. Conclusion

Ce plan de correction vise à résoudre le problème de JSON tronqué en augmentant `max_tokens` et en renforçant le prompt. L'approche est conservatrice (pas de refonte majeure) et réversible (facile de revenir en arrière si nécessaire).

**Statut attendu après exécution** : 🟢 **GREEN** – Lambda engine opérationnelle avec newsletters complètes et lisibles.

---

**Auteur** : Amazon Q Developer  
**Date de création** : 2025-12-08  
**Version** : 1.0
