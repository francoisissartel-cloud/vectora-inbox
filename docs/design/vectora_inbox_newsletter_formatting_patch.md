# Plan de Patch – Formatage Markdown de la Newsletter

**Date** : 2025-12-08  
**Auteur** : Amazon Q Developer  
**Statut** : IMPLEMENTATION  
**Version** : 1.0

---

## 1. État Actuel

### 1.1 Problème Identifié

La newsletter générée contient du **JSON brut** au lieu d'un **Markdown lisible**.

**Fichier concerné** : `s3://vectora-inbox-newsletters-dev/lai_weekly/2025/12/08/newsletter.md`

**Contenu actuel** :
```markdown
# Newsletter

```json
{
  "title": "LAI Intelligence Weekly – December 8, 2025",
  "intro": "This week's intelligence highlights critical developments...",
  ...
}
```

*Newsletter générée par Vectora Inbox – Powered by Amazon Bedrock*
```

### 1.2 Cause Racine

**Module** : `src/vectora_core/newsletter/formatter.py`

**Fonction** : `assemble_markdown()`

**Problème** : La fonction reçoit déjà un `dict` Python (parsé par `bedrock_client.py`), mais le code actuel ne génère pas correctement le Markdown structuré. Le contenu éditorial est bien présent dans `editorial_content`, mais le formatage final n'est pas appliqué correctement.

### 1.3 Flux Actuel

1. **bedrock_client.py** :
   - Appelle Bedrock avec un prompt structuré
   - Reçoit une réponse JSON de Bedrock
   - Parse la réponse avec `json.loads()` → retourne un `dict`
   - ✅ **Fonctionne correctement**

2. **assembler.py** :
   - Appelle `bedrock_client.generate_editorial_content()` → reçoit un `dict`
   - Passe ce `dict` à `formatter.assemble_markdown()`
   - ✅ **Fonctionne correctement**

3. **formatter.py** :
   - Reçoit le `dict` éditorial
   - ⚠️ **Problème** : Le code actuel génère bien le Markdown, mais il semble que la structure retournée par Bedrock ne correspond pas exactement au format attendu

---

## 2. État Cible

### 2.1 Format Markdown Attendu

```markdown
# LAI Intelligence Weekly – December 8, 2025

This week's intelligence highlights critical developments in hemophilia treatment, regulatory milestones, and marketing strategies for long-acting injectables.

## TL;DR

- Hemophilia treatment advances with new gene therapy data
- Regulatory approvals accelerate for LAI formulations
- Marketing strategies evolve for patient adherence

---

## LAI Ecosystem Updates

Recent developments in long-acting injectable technologies show promising results across multiple therapeutic areas.

**Camurus Announces Positive Phase 3 Results for Brixadi**  
Camurus reported positive Phase 3 results for Brixadi in opioid use disorder, demonstrating superior efficacy compared to standard treatment.  
[Read more](https://example.com/article1)

**Alkermes Expands LAI Portfolio**  
Alkermes announced expansion of its long-acting injectable portfolio with new formulations targeting schizophrenia and bipolar disorder.  
[Read more](https://example.com/article2)

---

## Competitive Intelligence

Key competitive moves in the biotech sector this week.

**Novo Nordisk Acquires LAI Technology Platform**  
Novo Nordisk acquired a proprietary LAI technology platform to enhance its diabetes and obesity treatment portfolio.  
[Read more](https://example.com/article3)

---

*Newsletter générée par Vectora Inbox – Powered by Amazon Bedrock*
```

### 2.2 Objectifs

1. **Markdown lisible** : Structure claire avec titres, sections, bullet points
2. **Conservation du JSON** : Optionnel mais utile pour debug → `newsletter.json`
3. **Compatibilité S3** : Même prefix, même convention de nommage

---

## 3. Étapes de Patch

### Étape 1 : Diagnostic de la Réponse Bedrock

**Action** : Vérifier que `bedrock_client.py` retourne bien un `dict` structuré conforme au schéma attendu.

**Schéma attendu** :
```json
{
  "title": "Newsletter title",
  "intro": "Introduction paragraph",
  "tldr": ["Bullet 1", "Bullet 2", "Bullet 3"],
  "sections": [
    {
      "section_title": "Section name",
      "section_intro": "Section intro",
      "items": [
        {
          "title": "Item title",
          "rewritten_summary": "Summary",
          "url": "https://..."
        }
      ]
    }
  ]
}
```

**Validation** : Le code actuel de `bedrock_client.py` parse déjà correctement la réponse et retourne un `dict`. ✅

### Étape 2 : Corriger formatter.py

**Action** : S'assurer que `assemble_markdown()` génère correctement le Markdown à partir du `dict`.

**Modifications** :
- Le code actuel semble correct, mais il faut vérifier que la structure retournée par Bedrock correspond exactement au format attendu
- Ajouter des logs pour débugger la structure reçue
- Gérer les cas où certains champs sont manquants ou vides

### Étape 3 : Ajouter l'Écriture du JSON Éditorial (Optionnel)

**Action** : Dans `assembler.py`, écrire également un fichier `newsletter.json` contenant la structure éditoriale brute.

**Bénéfices** :
- Debug facilité
- Possibilité de régénérer le Markdown sans rappeler Bedrock
- Traçabilité des réponses Bedrock

**Emplacement** : `s3://vectora-inbox-newsletters-dev/<client_id>/<YYYY>/<MM>/<DD>/newsletter.json`

### Étape 4 : Mise à Jour de __init__.py

**Action** : Adapter `_write_newsletter_to_s3()` pour écrire à la fois le Markdown et le JSON.

**Modifications** :
- Ajouter un paramètre optionnel `editorial_json` à `_write_newsletter_to_s3()`
- Écrire `newsletter.json` si fourni

---

## 4. Implémentation Détaillée

### 4.1 Modifications dans formatter.py

**Changements** :
- Aucun changement majeur nécessaire, le code actuel est correct
- Ajouter des logs pour débugger la structure reçue
- Améliorer la gestion des cas limites (champs manquants)

### 4.2 Modifications dans assembler.py

**Changements** :
- Retourner également le `editorial_content` (dict JSON) en plus du Markdown
- Signature modifiée : `generate_newsletter() -> Tuple[str, Dict[str, Any], Dict[str, Any]]`
  - `str` : Markdown
  - `Dict[str, Any]` : Stats
  - `Dict[str, Any]` : Editorial content (JSON)

### 4.3 Modifications dans __init__.py

**Changements** :
- Récupérer le `editorial_content` depuis `assembler.generate_newsletter()`
- Écrire à la fois `newsletter.md` et `newsletter.json` dans S3

---

## 5. Tests de Validation

### 5.1 Test End-to-End

**Commande** :
```powershell
aws lambda invoke `
  --function-name vectora-inbox-engine-dev `
  --payload file://test-event-engine.json `
  --profile rag-lai-prod `
  --region eu-west-3 `
  out-engine-lai-weekly.json
```

**Vérifications** :
1. ✅ Réponse Lambda avec `statusCode: 200`
2. ✅ Fichier `newsletter.md` contient du Markdown lisible (pas de JSON brut)
3. ✅ Fichier `newsletter.json` contient la structure éditoriale (optionnel)
4. ✅ Pas d'erreur dans CloudWatch

### 5.2 Vérification S3

**Commandes** :
```powershell
# Télécharger la newsletter Markdown
aws s3 cp s3://vectora-inbox-newsletters-dev/lai_weekly/2025/12/08/newsletter.md newsletter.md --profile rag-lai-prod --region eu-west-3

# Télécharger le JSON éditorial (si implémenté)
aws s3 cp s3://vectora-inbox-newsletters-dev/lai_weekly/2025/12/08/newsletter.json newsletter.json --profile rag-lai-prod --region eu-west-3

# Afficher le contenu
Get-Content newsletter.md
Get-Content newsletter.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

**Résultat attendu** :
- `newsletter.md` : Markdown structuré et lisible
- `newsletter.json` : Structure JSON éditoriale brute

---

## 6. Critères de Succès

### Critères Obligatoires

- ✅ Newsletter Markdown lisible (pas de JSON brut)
- ✅ Structure Markdown conforme (titre, intro, TL;DR, sections, items)
- ✅ Pas de régression dans le workflow (matching, scoring, Bedrock)
- ✅ Temps d'exécution acceptable (<30 secondes)

### Critères Optionnels

- ✅ Fichier `newsletter.json` généré pour debug
- ✅ Logs détaillés pour traçabilité

---

## 7. Rollback Plan

En cas de problème :

1. **Revenir à la version précédente** :
   ```powershell
   # Repackager l'ancienne version
   # Redéployer la Lambda
   ```

2. **Désactiver l'écriture du JSON** : Retirer l'écriture de `newsletter.json` si elle cause des problèmes

3. **Fallback Bedrock** : Le code actuel a déjà un fallback en cas d'échec Bedrock

---

## 8. Prochaines Étapes Après le Patch

1. **Validation qualité** : Vérifier la qualité éditoriale du Markdown généré
2. **Ajustement des prompts** : Itérer sur les prompts Bedrock si nécessaire
3. **Tests avec d'autres clients** : Valider avec d'autres configurations
4. **Documentation** : Créer `vectora_inbox_engine_markdown_patch.md`
5. **CHANGELOG** : Mettre à jour le statut de AMBER → GREEN

---

**Fin du plan de patch.**

Ce plan sera maintenant exécuté pour corriger le formatage Markdown de la newsletter.
