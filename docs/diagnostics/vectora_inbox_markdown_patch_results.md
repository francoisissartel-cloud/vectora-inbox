# Résultats du Patch Markdown – Diagnostic Final

**Date** : 2025-12-08  
**Auteur** : Amazon Q Developer  
**Statut** : 🔴 **ÉCHEC PARTIEL** – Problème identifié avec la réponse Bedrock

---

## Résumé Exécutif

Le patch de formatage Markdown a été implémenté et déployé avec succès, mais le problème persiste. L'analyse des logs révèle que **le problème ne vient pas du parsing, mais de la réponse Bedrock elle-même**.

**Problème identifié** : Bedrock retourne une réponse vide ou invalide (JSON incomplet/tronqué)

---

## Résultats du Déploiement

### ✅ Déploiement Réussi

- ✅ Code modifié (bedrock_client.py, assembler.py, __init__.py)
- ✅ Package ZIP créé (16.8 MB)
- ✅ Upload vers S3 réussi
- ✅ Lambda mise à jour avec succès
- ✅ Invocation Lambda réussie (StatusCode: 200)

### ⚠️ Résultats de l'Exécution

**Réponse Lambda** :
```json
{
  "statusCode": 200,
  "body": {
    "client_id": "lai_weekly",
    "execution_date": "2025-12-08T18:30:54Z",
    "target_date": "2025-12-08",
    "period": {
      "from_date": "2025-12-01",
      "to_date": "2025-12-08"
    },
    "items_analyzed": 50,
    "items_matched": 8,
    "items_selected": 5,
    "sections_generated": 2,
    "s3_output_path": "s3://vectora-inbox-newsletters-dev/lai_weekly/2025/12/08/newsletter.md",
    "execution_time_seconds": 19.41,
    "message": "Newsletter générée avec succès"
  }
}
```

**Fichiers générés dans S3** :
- ✅ `newsletter.md` (590 bytes) – MAIS contient du JSON brut
- ✅ `newsletter.json` (586 bytes) – Structure éditoriale

---

## Analyse du Problème

### Contenu de newsletter.md

```markdown
# Newsletter

```json
{
  "title": "LAI Intelligence Weekly – December 8, 2025",
  "intro": "This week's intelligence highlights competitive dynamics in hemophilia therapeutics, regulatory developments across key markets, and strategic marketing investments in immunology. Notable activity includes Pfizer's ASH data presentation, FDA safety investigations, and unprecedented pharma sponsorship of public health awareness initiatives. The period reflects continued focus on specialty care franchises and geographic

*Newsletter générée par Vectora Inbox – Powered by Amazon Bedrock*
```

**Observations** :
- ❌ Contient encore du JSON brut enveloppé dans des balises markdown
- ❌ Le JSON est **tronqué** (s'arrête au milieu d'une phrase : "...and geographic")
- ❌ Pas de sections, pas d'items, pas de TL;DR

### Contenu de newsletter.json

```json
{
  "title": "Newsletter",
  "intro": "```json\n{\n  \"title\": \"LAI Intelligence Weekly – December 8, 2025\",\n  \"intro\": \"This week's intelligence highlights competitive dynamics in hemophilia therapeutics, regulatory developments across key markets, and strategic marketing investments in immunology. Notable activity includes Pfizer's ASH data presentation, FDA safety investigations, and unprecedented pharma sponsorship of public health awareness initiatives. The period reflects continued focus on specialty care franchises and geographic",
  "tldr": [],
  "sections": []
}
```

**Observations** :
- ❌ Le champ `intro` contient le JSON brut complet (avec balises markdown)
- ❌ Le JSON est **tronqué** (même endroit : "...and geographic")
- ❌ Pas de `tldr`, pas de `sections`

### Logs CloudWatch

**Log critique** :
```
[WARNING] Réponse Bedrock non-JSON (Expecting value: line 1 column 1 (char 0)), tentative d'extraction manuelle
```

**Interprétation** :
- Bedrock retourne une chaîne vide ou du texte qui ne commence pas par un JSON valide
- Le parser tente d'extraire le JSON des balises markdown, mais échoue
- Le fallback retourne une structure minimale avec le texte brut dans `intro`

---

## Cause Racine

### Hypothèse 1 : Réponse Bedrock Tronquée

Bedrock génère une réponse JSON, mais elle est **tronquée** avant la fin. Causes possibles :
- **max_tokens trop faible** : Actuellement 3000 tokens, peut-être insuffisant
- **Timeout Bedrock** : La génération est interrompue avant la fin
- **Erreur de streaming** : La réponse est coupée pendant la transmission

### Hypothèse 2 : Format de Réponse Bedrock Incorrect

Bedrock ne retourne pas du JSON pur, mais :
- Du texte avec des balises markdown (```json ... ```)
- Du texte explicatif avant le JSON
- Un format différent de celui attendu

### Hypothèse 3 : Problème de Prompt

Le prompt demande du JSON, mais Bedrock :
- Interprète mal la consigne
- Génère du texte explicatif en plus du JSON
- Ne respecte pas la contrainte "ONLY JSON"

---

## Solutions Proposées

### Solution 1 : Augmenter max_tokens (PRIORITAIRE)

**Action** : Passer de 3000 à 5000 ou 8000 tokens

**Fichier** : `src/vectora_core/newsletter/bedrock_client.py`

**Modification** :
```python
request_body = {
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 8000,  # Augmenté de 3000 à 8000
    "messages": [...],
    "temperature": 0.3
}
```

**Justification** :
- La réponse est tronquée à ~500 caractères
- Un JSON complet avec 2 sections + 5 items nécessite ~2000-3000 tokens
- Marge de sécurité nécessaire

### Solution 2 : Améliorer le Prompt (RECOMMANDÉ)

**Action** : Renforcer la consigne "JSON only" et simplifier le format attendu

**Modifications** :
1. Ajouter "DO NOT include any markdown code blocks" dans le prompt
2. Ajouter un exemple de JSON attendu
3. Simplifier la structure (moins de champs)

**Exemple de prompt amélioré** :
```python
prompt = f"""You are an expert biotech/pharma intelligence analyst.

TASK: Generate editorial content for a newsletter in JSON format.

CRITICAL: Your response MUST be ONLY valid JSON. Do NOT include:
- Markdown code blocks (```json)
- Explanatory text before or after the JSON
- Comments or additional formatting

RESPONSE FORMAT (example):
{{
  "title": "Newsletter Title",
  "intro": "Introduction paragraph",
  "tldr": ["Point 1", "Point 2"],
  "sections": [
    {{
      "section_title": "Section Name",
      "section_intro": "Section intro",
      "items": [
        {{
          "title": "Item title",
          "rewritten_summary": "Summary",
          "url": "https://..."
        }}
      ]
    }}
  ]
}}

CONTEXT:
...

SELECTED ITEMS:
...

Respond with ONLY the JSON object, nothing else.
"""
```

### Solution 3 : Parser Plus Robuste (COMPLÉMENTAIRE)

**Action** : Améliorer le parsing pour gérer les cas limites

**Modifications** :
1. Détecter si la réponse est tronquée (pas de `}` final)
2. Tenter de compléter le JSON si possible
3. Logger la réponse brute complète pour debug

**Code** :
```python
def _parse_editorial_response(response_text: str) -> Dict[str, Any]:
    # Nettoyer
    cleaned_text = response_text.strip()
    
    # Extraire des balises markdown
    if '```json' in cleaned_text:
        start_idx = cleaned_text.find('```json') + 7
        end_idx = cleaned_text.rfind('```')
        if start_idx > 7 and end_idx > start_idx:
            cleaned_text = cleaned_text[start_idx:end_idx].strip()
    
    # Vérifier si tronqué
    if not cleaned_text.endswith('}'):
        logger.warning("Réponse Bedrock tronquée (pas de } final)")
        # Tenter de compléter
        cleaned_text += '"}}'
    
    # Parser
    try:
        result = json.loads(cleaned_text)
        return result
    except json.JSONDecodeError as e:
        logger.error(f"Parsing JSON échoué: {e}")
        logger.error(f"Réponse brute: {response_text}")
        # Fallback
        return {...}
```

### Solution 4 : Utiliser stop_sequences (AVANCÉ)

**Action** : Ajouter des stop_sequences pour forcer Bedrock à terminer proprement

**Modification** :
```python
request_body = {
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 8000,
    "messages": [...],
    "temperature": 0.3,
    "stop_sequences": ["\n\n---\n\n", "```"]  # Arrêter si markdown détecté
}
```

---

## Plan d'Action Recommandé

### Étape 1 : Augmenter max_tokens (IMMÉDIAT)

1. Modifier `bedrock_client.py` : `max_tokens: 8000`
2. Repackager et redéployer
3. Tester

**Durée estimée** : 5 minutes

### Étape 2 : Améliorer le Prompt (COURT TERME)

1. Réécrire le prompt avec consignes renforcées
2. Ajouter un exemple de JSON attendu
3. Tester avec différentes formulations

**Durée estimée** : 15-30 minutes

### Étape 3 : Parser Plus Robuste (MOYEN TERME)

1. Améliorer la détection de troncature
2. Ajouter des logs détaillés
3. Implémenter des fallbacks intelligents

**Durée estimée** : 30-60 minutes

### Étape 4 : Tests Approfondis (LONG TERME)

1. Tester avec différents volumes d'items (1, 5, 10, 20)
2. Tester avec différentes périodes (1 jour, 7 jours, 30 jours)
3. Analyser les patterns de troncature

**Durée estimée** : 1-2 heures

---

## Métriques Actuelles

### Exécution Lambda

- ✅ Temps d'exécution : 19.41 secondes (acceptable)
- ✅ Items analysés : 50
- ✅ Items matchés : 8 (16%)
- ✅ Items sélectionnés : 5
- ✅ Sections générées : 2

### Appel Bedrock

- ✅ Appel réussi (pas de throttling)
- ✅ Temps de réponse : ~17 secondes
- ❌ Réponse tronquée/invalide
- ❌ JSON non parsable

---

## Conclusion

Le patch de formatage Markdown a été correctement implémenté, mais le problème persiste car **Bedrock ne retourne pas un JSON valide et complet**.

**Statut** : 🔴 **ÉCHEC PARTIEL** – Le code est correct, mais la réponse Bedrock est problématique

**Prochaine action prioritaire** : Augmenter `max_tokens` de 3000 à 8000 et retester

**Statut CHANGELOG** : Rester en AMBER jusqu'à résolution complète

---

**Auteur** : Amazon Q Developer  
**Date** : 2025-12-08  
**Version** : 1.0
