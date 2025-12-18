# Résumé : Blocage AWS CLI Windows - Matching V2

**Date :** 17 décembre 2025  
**Statut :** 🔴 BLOCAGE TECHNIQUE - Solution de contournement requise

---

## 🎯 Contexte

Le refactoring du matching V2 en moteur configuration-driven est **techniquement complet et déployé avec succès** (Phases 1-4). La validation production finale est bloquée par un problème d'encodage JSON de l'AWS CLI sous Windows.

---

## ❌ Problème Actuel

**Symptôme :** Impossible d'invoquer la Lambda `vectora-inbox-normalize-score-v2-dev` depuis Windows avec un payload JSON via AWS CLI

**Cause racine :** Encodage du payload JSON dans l'AWS CLI sous Windows (PowerShell/cmd.exe)
- Échappement des guillemets problématique
- Encodage UTF-8 vs UTF-16
- Différences de comportement shell Windows vs Unix

**Impact :** Validation production bloquée, impossible de tester la Lambda déployée

---

## 🔧 Configuration Cible Validée

- **Lambda :** `vectora-inbox-normalize-score-v2-dev`
- **Région :** `eu-west-3`
- **Profil AWS :** `rag-lai-prod`
- **Événement minimal accepté :**
  - Auto-scan : `{}`
  - Client spécifique : `{"client_id": "lai_weekly_v3"}`

---

## 📋 Contraintes

1. **Hygiène V4 stricte :** Respect absolu de `src_lambda_hygiene_v4.md`
2. **Pas de modification dans `/src_v2`** : Le moteur est déployé et fonctionnel
3. **Pas de nouvelle dépendance exotique** : Utiliser uniquement boto3 (standard AWS)
4. **Simplicité et durabilité** : Solution réutilisable pour tous les tests futurs
5. **Travail uniquement dans `/scripts` et `/docs`**

---

## ✅ Solution Cible

**Approche 1 (Recommandée) :** Script Python boto3
- Invocation Lambda via SDK Python
- Pas de problème d'encodage
- Paramétrable et réutilisable
- Fonctionne sur Windows/Linux/Mac

**Approche 2 (Alternative) :** AWS CLI avec fichier payload
- Payload JSON stocké dans un fichier
- Utilisation de `--cli-binary-format raw-in-base64-out` et `fileb://`
- Commande robuste et documentée

**Approche 3 (Fallback) :** Console AWS
- Interface web pour invocation manuelle
- Pas de script, mais fonctionnel

---

## 🎯 Objectif

Créer un chemin de test standard qui permette de :
1. Invoquer `vectora-inbox-normalize-score-v2-dev` en 1 commande depuis Windows
2. Passer `{"client_id": "lai_weekly_v3"}` proprement
3. Afficher les résultats de façon lisible
4. Ne plus jamais se battre avec l'encodage JSON de l'AWS CLI

---

**Prochaine étape :** Implémentation du plan de contournement (script Python + documentation)
