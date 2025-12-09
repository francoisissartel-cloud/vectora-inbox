# Instructions – Patch Formatage Markdown Newsletter

**Date** : 2025-12-08  
**Auteur** : Amazon Q Developer  
**Statut** : PRÊT POUR EXÉCUTION

---

## Résumé

Ce patch corrige le problème de formatage de la newsletter. La newsletter générée contenait du JSON brut au lieu d'un Markdown lisible.

**Problème** : `newsletter.md` contient du JSON brut enveloppé dans des balises markdown  
**Solution** : Amélioration du parsing de la réponse Bedrock + écriture de `newsletter.json` pour debug

---

## Modifications Apportées

### 1. Code Modifié

- ✅ `src/vectora_core/newsletter/bedrock_client.py` : Amélioration du parsing (extraction des balises markdown)
- ✅ `src/vectora_core/newsletter/assembler.py` : Retour du contenu éditorial JSON
- ✅ `src/vectora_core/__init__.py` : Écriture de `newsletter.md` ET `newsletter.json`

### 2. Scripts Créés

- ✅ `scripts/redeploy-engine-markdown-patch.ps1` : Repackage et redéploiement de la Lambda
- ✅ `scripts/test-engine-markdown-patch.ps1` : Test et validation du patch

### 3. Documentation

- ✅ `docs/design/vectora_inbox_newsletter_formatting_patch.md` : Plan de patch détaillé
- ✅ `docs/diagnostics/vectora_inbox_engine_markdown_patch.md` : Diagnostic du patch
- ✅ `CHANGELOG.md` : Mise à jour avec le statut du patch

---

## Étapes d'Exécution

### Étape 1 : Redéployer la Lambda Engine

```powershell
# Depuis la racine du projet
cd c:\Users\franc\OneDrive\Bureau\vectora-inbox

# Exécuter le script de redéploiement
.\scripts\redeploy-engine-markdown-patch.ps1
```

**Durée estimée** : 2-3 minutes

**Résultat attendu** :
- Package ZIP créé (~17 MB)
- Upload vers S3 réussi
- Lambda mise à jour avec succès

### Étape 2 : Tester la Lambda

```powershell
# Exécuter le script de test
.\scripts\test-engine-markdown-patch.ps1
```

**Durée estimée** : 30-40 secondes

**Résultat attendu** :
- ✅ Réponse Lambda avec `statusCode: 200`
- ✅ Newsletter téléchargée depuis S3
- ✅ Vérification automatique : pas de JSON brut dans le Markdown
- ✅ Aperçu de la newsletter affiché dans le terminal

### Étape 3 : Vérifier les Fichiers Générés

Après le test, vous devriez avoir les fichiers suivants :

```
newsletter-patch.md          # Newsletter en Markdown lisible
newsletter-patch.json        # Structure éditoriale JSON (pour debug)
out-engine-patch.json        # Réponse de la Lambda
test-event-engine-patch.json # Payload de test
```

**Vérifications manuelles** :

1. Ouvrir `newsletter-patch.md` et vérifier :
   - ✅ Titre de la newsletter (# ...)
   - ✅ Introduction (paragraphe)
   - ✅ TL;DR (## TL;DR avec bullet points)
   - ✅ Sections (## Section Name)
   - ✅ Items (** Item Title ** avec résumé et lien)
   - ❌ PAS de JSON brut ou de balises ```json

2. Ouvrir `newsletter-patch.json` et vérifier :
   - ✅ Structure JSON valide
   - ✅ Champs : title, intro, tldr, sections
   - ✅ Sections avec items

### Étape 4 : Vérifier dans S3

```powershell
# Lister les fichiers dans S3
aws s3 ls s3://vectora-inbox-newsletters-dev/lai_weekly/2025/12/08/ `
  --profile rag-lai-prod `
  --region eu-west-3
```

**Résultat attendu** :
```
newsletter.md
newsletter.json
```

### Étape 5 : Consulter les Logs CloudWatch

```powershell
# Afficher les logs des 10 dernières minutes
aws logs tail /aws/lambda/vectora-inbox-engine-dev `
  --since 10m `
  --format detailed `
  --profile rag-lai-prod `
  --region eu-west-3
```

**Logs attendus** :
```
[INFO] Détection de balises markdown JSON, extraction...
[INFO] JSON parsé avec succès : 2 sections
[INFO] Assemblage du Markdown final
[INFO] Markdown assemblé : XXXX caractères
[INFO] Écriture de la newsletter dans s3://...
[INFO] Écriture du JSON éditorial dans s3://...
```

---

## Critères de Succès

### ✅ Succès Complet

- ✅ Newsletter Markdown lisible (pas de JSON brut)
- ✅ Structure Markdown conforme (titre, intro, TL;DR, sections, items)
- ✅ Fichier JSON éditorial créé pour debug
- ✅ Pas de régression dans le workflow
- ✅ Temps d'exécution acceptable (<30 secondes)

### ⚠️ Succès Partiel

- ✅ Newsletter générée mais format incomplet
- ⚠️ Certaines sections manquantes
- ⚠️ Logs avec warnings

### ❌ Échec

- ❌ Newsletter contient encore du JSON brut
- ❌ Erreur lors de l'invocation Lambda
- ❌ Fichiers non créés dans S3

---

## En Cas de Problème

### Problème 1 : Newsletter contient encore du JSON brut

**Diagnostic** :
```powershell
# Télécharger la newsletter
aws s3 cp s3://vectora-inbox-newsletters-dev/lai_weekly/2025/12/08/newsletter.md newsletter-debug.md

# Afficher le contenu
Get-Content newsletter-debug.md
```

**Solution** :
- Vérifier les logs CloudWatch pour voir si le parsing a fonctionné
- Vérifier que la réponse Bedrock est bien parsée (logs : "JSON parsé avec succès")
- Si le problème persiste, consulter `newsletter.json` pour voir la structure brute

### Problème 2 : Erreur lors du redéploiement

**Diagnostic** :
```powershell
# Vérifier l'état de la Lambda
aws lambda get-function --function-name vectora-inbox-engine-dev --profile rag-lai-prod --region eu-west-3
```

**Solution** :
- Vérifier que le package ZIP a été créé correctement
- Vérifier que l'upload S3 a réussi
- Réessayer le redéploiement

### Problème 3 : Erreur lors de l'invocation Lambda

**Diagnostic** :
```powershell
# Consulter les logs CloudWatch
aws logs tail /aws/lambda/vectora-inbox-engine-dev --since 10m --format detailed
```

**Solution** :
- Vérifier les logs pour identifier l'erreur
- Vérifier que les items normalisés existent dans S3
- Vérifier que les configurations sont correctes

---

## Rollback

En cas de problème majeur, vous pouvez revenir à la version précédente :

```powershell
# Télécharger l'ancienne version (si sauvegardée)
aws s3 cp s3://vectora-inbox-lambda-code-dev/lambda/engine/previous.zip lambda-engine-rollback.zip

# Mettre à jour la Lambda
aws lambda update-function-code `
  --function-name vectora-inbox-engine-dev `
  --zip-file fileb://lambda-engine-rollback.zip `
  --profile rag-lai-prod `
  --region eu-west-3
```

---

## Prochaines Étapes Après Validation

Une fois le patch validé :

1. **Mettre à jour le CHANGELOG** :
   - Changer le statut de AMBER → GREEN
   - Ajouter la date de validation

2. **Créer un diagnostic final** :
   - Compléter `docs/diagnostics/vectora_inbox_engine_markdown_patch.md`
   - Ajouter les résultats du test
   - Ajouter des captures d'écran si nécessaire

3. **Préparer le déploiement STAGE** :
   - Dupliquer l'infrastructure en STAGE
   - Tester avec d'autres clients (si disponibles)
   - Valider la qualité éditoriale

---

## Résumé des Commandes

```powershell
# 1. Redéployer
.\scripts\redeploy-engine-markdown-patch.ps1

# 2. Tester
.\scripts\test-engine-markdown-patch.ps1

# 3. Vérifier S3
aws s3 ls s3://vectora-inbox-newsletters-dev/lai_weekly/2025/12/08/ --profile rag-lai-prod --region eu-west-3

# 4. Consulter les logs
aws logs tail /aws/lambda/vectora-inbox-engine-dev --since 10m --format detailed --profile rag-lai-prod --region eu-west-3
```

---

**Bonne chance ! 🚀**

Si vous rencontrez un problème, consultez les logs CloudWatch et le fichier `newsletter.json` pour débugger.
