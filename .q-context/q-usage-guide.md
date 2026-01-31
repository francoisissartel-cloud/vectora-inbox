# Guide d'Utilisation des Templates de Plans

**Date**: 2026-01-30  
**Objectif**: Expliquer comment utiliser efficacement les templates avec Q Developer

---

## 🎯 Comment Ça Marche ?

### Q Developer Applique Automatiquement les Règles

**✅ Q lit automatiquement** :
- `.q-context/vectora-inbox-development-rules.md`
- `.q-context/q-planning-rules.md`
- Tous les autres documents dans `.q-context/`

**✅ Q applique automatiquement** :
- Les règles de gouvernance
- Les workflows standardisés
- Les templates de plans
- Les patterns d'exécution

**Vous n'avez PAS besoin de** :
- Rappeler les règles à Q
- Mentionner les templates
- Expliquer le workflow

---

## 📝 Comment Prompter Q Developer

### Prompts Simples qui Déclenchent un Plan

**Pour développement** :
```
Ajoute une fonction pour extraire les dates relatives.
```

**Pour correction bug** :
```
Le matching Bedrock échoue avec des timeouts. Corrige ça.
```

**Pour diagnostic** :
```
Diagnostique pourquoi les scores sont tous à zéro.
```

**Pour déploiement** :
```
La version 1.2.4 fonctionne bien en dev. Promeus en stage.
```

### Q Répond Automatiquement

**Q va automatiquement** :
1. **Analyser** la complexité de votre demande
2. **Décider** s'il faut un plan (selon les règles)
3. **Choisir** le bon template
4. **Créer** le plan dans le bon dossier
5. **Proposer** l'exécution phase par phase

**Exemple de réponse Q** :
```
Je vais créer un plan de développement pour ajouter l'extraction de dates relatives.

**Analyse** :
- Modification code: src_v2/vectora_core/
- Tests requis: Oui  
- Déploiement: dev → stage
- Complexité: Moyenne

Je crée le plan dans `docs/plans/plan_extraction_dates_relatives_20260130.md`

[Q crée le plan automatiquement]

Plan créé. Souhaitez-vous que je commence par la Phase 0 (Cadrage) ?
```

---

## 🚀 Workflow d'Exécution

### 1. Vous Promptez Simplement

```
Ajoute une nouvelle fonctionnalité de validation des emails.
```

### 2. Q Crée le Plan Automatiquement

Q va :
- Analyser votre demande
- Créer un plan dans `docs/plans/`
- Vous présenter le plan
- Demander votre validation

### 3. Exécution Phase par Phase

**Q exécute UNE phase à la fois** :

```
## ✅ Phase 0 - Cadrage Terminée

**Résultats** :
- Analyse d'impact effectuée
- Prérequis validés
- Risques identifiés

**Prêt pour Phase 1 - Préparation** ?
```

**Vous répondez** : `Oui` ou `Continue`

### 6. Q Continue Automatiquement

Q respecte automatiquement :
- Le workflow (Build → Deploy Dev → Test → Promote Stage)
- Les règles d'hygiène
- Le versioning
- Les scripts standardisés
- **La création de rapport final dans `docs/reports/`**

---

## 🎛️ Contrôle et Personnalisation

### Vous Pouvez Toujours

**Modifier le plan** :
```
Modifie le plan : je veux tester en stage avant de commiter.
```

**Sauter des phases** :
```
Skip la phase de tests locaux, je les ai déjà faits.
```

**Arrêter à tout moment** :
```
Stop. Je veux revoir le plan.
```

**Demander des détails** :
```
Explique-moi la Phase 3 en détail.
```

### Q S'Adapte Automatiquement

Q va :
- Modifier le plan selon vos demandes
- Respecter vos préférences
- Maintenir la cohérence avec la gouvernance
- Vous alerter en cas de risque

---

## 🔧 Cas d'Usage Fréquents

### Développement Simple

**Vous** : `Ajoute une validation dans le parser HTML.`

**Q fait automatiquement** :
1. Crée plan simple (3-4 phases)
2. Modifie le code
3. Teste localement
4. Déploie dev
5. Teste dev
6. Commit
7. **Crée rapport final**

### Développement Complexe

**Vous** : `Refactorise l'architecture de matching pour supporter plusieurs modèles Bedrock.`

**Q fait automatiquement** :
1. Crée plan détaillé (6+ phases)
2. Analyse d'impact approfondie
3. Backup/snapshot
4. Modifications par étapes
5. Tests complets
6. Déploiement progressif dev → stage
7. Documentation

### Diagnostic

**Vous** : `Les newsletters ne se génèrent plus depuis hier.`

**Q fait automatiquement** :
1. Crée plan diagnostic
2. Reproduit le problème
3. Analyse logs et métriques
4. Identifie cause racine
5. Propose solutions
6. Plan de correction

### Déploiement

**Vous** : `Deploy la version 1.3.0 en stage.`

**Q fait automatiquement** :
1. Vérifie que dev fonctionne
2. Crée plan de promotion
3. Promote vers stage
4. Teste stage
5. Valide métriques
6. Confirme succès

---

## 💡 Astuces pour Optimiser

### Soyez Précis sur l'Objectif

**✅ Bon** : `Améliore la performance du matching Bedrock en réduisant les appels API.`

**❌ Moins bon** : `Améliore la performance.`

### Mentionnez les Contraintes

**✅ Bon** : `Ajoute cette fonctionnalité mais sans casser la compatibilité avec lai_weekly_v3.`

**❌ Moins bon** : `Ajoute cette fonctionnalité.`

### Précisez l'Urgence

**✅ Bon** : `Bug critique : les scores sont tous à zéro en prod. Diagnostic urgent.`

**❌ Moins bon** : `Il y a un problème avec les scores.`

### Indiquez l'Environnement

**✅ Bon** : `Teste cette correction en dev puis promeus en stage.`

**❌ Moins bon** : `Teste cette correction.`

---

## 🚨 Gestion des Situations Spéciales

### Reprise Après Interruption

**Si votre chat Q sature**, vous pouvez :

1. **Ouvrir nouveau chat**
2. **Dire** : `Continue le plan docs/plans/plan_extraction_dates_20260130.md à partir de la Phase 3.`
3. **Q reprend automatiquement** où vous en étiez

### Modification de Plan en Cours

**Vous** : `Modifie le plan : ajoute une phase de tests de performance.`

**Q va** :
- Modifier le plan existant
- Réorganiser les phases
- Continuer l'exécution

### Rollback d'Urgence

**Vous** : `Rollback immédiat ! Il y a un problème critique.`

**Q va** :
- Arrêter l'exécution
- Diagnostiquer rapidement
- Proposer rollback
- Exécuter après votre validation

---

## 📊 Avantages de Cette Méthode

### Pour Vous

**✅ Simplicité** : Promptez naturellement, Q fait le reste  
**✅ Contrôle** : Validation à chaque étape  
**✅ Reprise** : Continuez après interruption  
**✅ Traçabilité** : Historique complet des actions  
**✅ Sécurité** : Rollback possible à tout moment  

### Pour le Projet

**✅ Qualité** : Processus standardisé et validé  
**✅ Gouvernance** : Respect automatique des règles  
**✅ Documentation** : Plans archivés pour référence  
**✅ Amélioration** : Apprentissage des patterns  
**✅ Collaboration** : Plans lisibles par l'équipe  

---

## 🎯 Exemples Concrets d'Usage

### Lundi Matin - Nouvelle Fonctionnalité

**Vous** : `Ajoute une fonction pour détecter les dates relatives dans les articles (hier, demain, la semaine prochaine).`

**Q répond** :
```
Je vais créer un plan de développement pour la détection de dates relatives.

**Analyse** :
- Modification: src_v2/vectora_core/normalization/
- Tests: Unitaires + intégration
- Déploiement: dev → stage
- Durée estimée: 2-3h

Plan créé dans docs/plans/plan_detection_dates_relatives_20260130.md

Souhaitez-vous commencer par la Phase 0 (Cadrage) ?
```

### Mercredi Après-midi - Bug Urgent

**Vous** : `Bug critique : normalize-score-v2 timeout sur tous les appels Bedrock depuis 14h.`

**Q répond** :
```
🚨 Bug critique détecté - Je crée un plan de diagnostic urgent.

**Analyse** :
- Impact: Critique (pipeline bloqué)
- Urgence: Immédiate
- Symptôme: Timeouts Bedrock

Plan diagnostic créé dans docs/diagnostics/diagnostic_bedrock_timeout_20260130.md

Je commence immédiatement la Phase 0 (Reproduction du problème) ?
```

### Vendredi Soir - Promotion Stage

**Vous** : `La version 1.4.2 fonctionne parfaitement en dev depuis 3 jours. Promeus en stage.`

**Q répond** :
```
Je vais promouvoir la version 1.4.2 vers stage.

**Vérifications** :
✅ Version 1.4.2 stable en dev
✅ Tests E2E dev passés
✅ Aucun problème reporté

Plan de promotion créé dans docs/plans/plan_promotion_v142_stage_20260130.md

Prêt à commencer la promotion ?
```

---

## ✅ Résumé : Vous N'avez Rien à Faire de Spécial !

### Q Developer Fait Tout Automatiquement

1. **Lit** vos règles dans `.q-context/`
2. **Applique** la gouvernance automatiquement
3. **Crée** les plans selon les templates
4. **Exécute** phase par phase
5. **Respecte** le workflow standard
6. **Demande** validation aux points clés

### Vous Promptez Naturellement

- `Ajoute cette fonctionnalité...`
- `Corrige ce bug...`
- `Diagnostique ce problème...`
- `Déploie cette version...`

### Q S'Occupe du Reste

- Création du plan approprié
- Exécution méthodique
- Respect de la gouvernance
- Documentation automatique
- Gestion des erreurs

**C'est aussi simple que ça !** 🚀

---

**Guide créé le**: 2026-01-30  
**Dernière mise à jour**: 2026-01-30  
**Statut**: Opérationnel