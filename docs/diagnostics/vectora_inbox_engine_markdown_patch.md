# Diagnostic – Patch Formatage Markdown Newsletter

**Date** : 2025-12-08  
**Auteur** : Amazon Q Developer  
**Statut** : EN COURS  
**Version** : 1.0

---

## Résumé Exécutif

Ce document décrit le patch appliqué pour corriger le problème de formatage de la newsletter. Le problème initial était que la newsletter contenait du JSON brut au lieu d'un Markdown lisible.

**Statut** : 🟡 **EN COURS** – Patch implémenté, en attente de validation

---

## 1. Problème Initial

### 1.1 Description

La Lambda `vectora-inbox-engine-dev` générait une newsletter contenant du JSON brut au lieu d'un Markdown structuré et lisible.

**Fichier concerné** : `s3://vectora-inbox-newsletters-dev/lai_weekly/2025/12/08/newsletter.md`

**Contenu problématique** :
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

**Hypothèse** : La réponse Bedrock contient du JSON enveloppé dans des balises markdown (```json ... ```), et le parser ne les retirait pas correctement.

**Modules concernés** :
- `src/vectora_core/newsletter/bedrock_client.py` : Parsing de la réponse Bedrock
- `src/vectora_core/newsletter/formatter.py` : Génération du Markdown
- `src/vectora_core/newsletter/assembler.py` : Orchestration
- `src/vectora_core/__init__.py` : Écriture dans S3

---

## 2. Solution Implémentée

### 2.1 Modifications dans bedrock_client.py

**Fonction modifiée** : `_parse_editorial_response()`

**Changements** :
- Ajout de la détection et extraction des balises markdown (```json ... ```)
- Nettoyage de la réponse avant parsing JSON
- Amélioration des logs pour traçabilité

**Code ajouté** :
```python
# Nettoyer la réponse : retirer les balises markdown si présentes
cleaned_text = response_text.strip()

# Si la réponse contient des balises ```json ... ```, les extraire
if '```json' in cleaned_text:
    logger.info("Détection de balises markdown JSON, extraction...")
    start_idx = cleaned_text.find('```json') + 7
    end_idx = cleaned_text.rfind('```')
    if start_idx > 7 and end_idx > start_idx:
        cleaned_text = cleaned_text[start_idx:end_idx].strip()
elif '```' in cleaned_text:
    logger.info("Détection de balises markdown génériques, extraction...")
    start_idx = cleaned_text.find('```') + 3
    end_idx = cleaned_text.rfind('```')
    if start_idx > 3 and end_idx > start_idx:
        cleaned_text = cleaned_text[start_idx:end_idx].strip()
```

### 2.2 Modifications dans assembler.py

**Fonction modifiée** : `generate_newsletter()`

**Changements** :
- Signature modifiée pour retourner également le contenu éditorial JSON
- Nouveau retour : `Tuple[str, Dict[str, Any], Dict[str, Any]]`
  - `str` : Markdown
  - `Dict[str, Any]` : Stats
  - `Dict[str, Any]` : Editorial content (JSON)

**Bénéfice** : Permet de conserver le JSON éditorial pour debug et traçabilité

### 2.3 Modifications dans __init__.py

**Fonction modifiée** : `run_engine_for_client()` et `_write_newsletter_to_s3()`

**Changements** :
- Récupération du contenu éditorial depuis `generate_newsletter()`
- Écriture de deux fichiers dans S3 :
  - `newsletter.md` : Markdown lisible
  - `newsletter.json` : Structure éditoriale JSON (pour debug)

**Code ajouté** :
```python
# Écrire aussi le JSON éditorial si fourni
if editorial_content:
    json_key = f"{client_id}/{year}/{month}/{day}/newsletter.json"
    logger.info(f"Écriture du JSON éditorial dans s3://{newsletters_bucket}/{json_key}")
    s3_client.write_json_to_s3(newsletters_bucket, json_key, editorial_content)
```

### 2.4 Aucune Modification dans formatter.py

Le code du formatter était déjà correct. Le problème venait du parsing de la réponse Bedrock, pas de la génération du Markdown.

---

## 3. Déploiement du Patch

### 3.1 Repackaging

**Script** : `scripts/redeploy-engine-markdown-patch.ps1`

**Étapes** :
1. Création du répertoire de build
2. Copie du code source (vectora_core + handler.py)
3. Installation des dépendances
4. Création du package ZIP
5. Upload vers S3
6. Mise à jour de la Lambda

**Commande** :
```powershell
.\scripts\redeploy-engine-markdown-patch.ps1
```

### 3.2 Validation

**Script** : `scripts/test-engine-markdown-patch.ps1`

**Vérifications** :
1. Invocation de la Lambda avec `client_id=lai_weekly` et `period_days=7`
2. Vérification du statut de la réponse (200)
3. Téléchargement de la newsletter depuis S3
4. Vérification que le contenu est du Markdown (pas de JSON brut)
5. Vérification de la structure Markdown (titres, sections, items)

**Commande** :
```powershell
.\scripts\test-engine-markdown-patch.ps1
```

---

## 4. Résultats Attendus

### 4.1 Format Markdown Attendu

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

---

*Newsletter générée par Vectora Inbox – Powered by Amazon Bedrock*
```

### 4.2 Fichiers S3 Générés

**Emplacement** : `s3://vectora-inbox-newsletters-dev/lai_weekly/2025/12/08/`

**Fichiers** :
1. `newsletter.md` : Markdown lisible (OBLIGATOIRE)
2. `newsletter.json` : Structure éditoriale JSON (OPTIONNEL, pour debug)

---

## 5. Métriques de Succès

### Critères de Validation

- ✅ Newsletter Markdown lisible (pas de JSON brut)
- ✅ Structure Markdown conforme (titre, intro, TL;DR, sections, items)
- ✅ Fichier JSON éditorial créé pour debug
- ✅ Pas de régression dans le workflow (matching, scoring, Bedrock)
- ✅ Temps d'exécution acceptable (<30 secondes)
- ✅ Logs CloudWatch détaillés

### Tests à Effectuer

1. **Test nominal** : `lai_weekly` avec `period_days=7`
2. **Test sans items** : Vérifier la newsletter minimale
3. **Test avec erreur Bedrock** : Vérifier le fallback
4. **Test de charge** : Plusieurs invocations successives

---

## 6. Logs CloudWatch

### Logs Attendus

**Parsing de la réponse Bedrock** :
```
[INFO] Détection de balises markdown JSON, extraction...
[INFO] JSON parsé avec succès : 2 sections
```

**Génération du Markdown** :
```
[INFO] Assemblage du Markdown final
[INFO] Markdown assemblé : 1234 caractères
```

**Écriture dans S3** :
```
[INFO] Écriture de la newsletter dans s3://vectora-inbox-newsletters-dev/lai_weekly/2025/12/08/newsletter.md
[INFO] Fichier texte écrit avec succès : 1234 caractères
[INFO] Écriture du JSON éditorial dans s3://vectora-inbox-newsletters-dev/lai_weekly/2025/12/08/newsletter.json
[INFO] Fichier JSON écrit avec succès : 567 caractères
```

---

## 7. Rollback Plan

En cas de problème :

1. **Revenir à la version précédente** :
   ```powershell
   # Télécharger l'ancienne version depuis S3
   aws s3 cp s3://vectora-inbox-lambda-code-dev/lambda/engine/previous.zip lambda-engine-rollback.zip
   
   # Mettre à jour la Lambda
   aws lambda update-function-code --function-name vectora-inbox-engine-dev --zip-file fileb://lambda-engine-rollback.zip
   ```

2. **Désactiver l'écriture du JSON** : Commenter l'écriture de `newsletter.json` si elle cause des problèmes

3. **Fallback Bedrock** : Le code a déjà un fallback en cas d'échec Bedrock

---

## 8. Prochaines Étapes

### Court Terme

1. ✅ Implémenter le patch
2. ⏳ Repackager et redéployer la Lambda
3. ⏳ Tester avec `lai_weekly`
4. ⏳ Vérifier le format Markdown
5. ⏳ Valider les logs CloudWatch

### Moyen Terme

1. Tester avec d'autres clients (si disponibles)
2. Ajuster les prompts Bedrock si nécessaire
3. Améliorer la qualité éditoriale
4. Créer des tests unitaires pour le parsing

### Long Terme

1. Monitoring de la qualité des newsletters
2. Feedback utilisateur sur le format
3. Optimisation des prompts Bedrock
4. Préparation STAGE/PROD

---

## 9. Conclusion

Le patch implémente une solution robuste pour corriger le problème de formatage Markdown. Les modifications sont minimales et ciblées, avec un impact limité sur le reste du code.

**Statut actuel** : 🟡 **EN COURS** – Patch implémenté, en attente de validation

**Prochaine action** : Exécuter `.\scripts\redeploy-engine-markdown-patch.ps1` puis `.\scripts\test-engine-markdown-patch.ps1`

---

**Auteur** : Amazon Q Developer  
**Date de création** : 2025-12-08  
**Version** : 1.0
