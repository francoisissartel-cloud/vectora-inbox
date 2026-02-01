# Règles de Planification pour Q Developer

**Date**: 2026-01-30  
**Version**: 1.0  
**Objectif**: Standardiser la création et l'exécution de plans avec Q Developer

---

## 🎯 Principe Fondamental

**Q Developer DOIT TOUJOURS créer un plan structuré avant toute modification complexe**

**Définition "modification complexe"**:
- Modification > 3 fichiers
- Déploiement AWS
- Changement architecture
- Correction bug critique
- Nouvelle fonctionnalité
- Diagnostic de problème

---

## 📋 Règles Obligatoires pour Q Developer

### 1. Déclenchement Automatique de Plan

**Q DOIT créer un plan quand l'utilisateur demande**:
- ✅ "Ajoute une nouvelle fonctionnalité..."
- ✅ "Corrige le bug..."
- ✅ "Déploie vers..."
- ✅ "Diagnostique le problème..."
- ✅ "Modifie l'architecture..."
- ✅ "Améliore la performance..."

**Q PEUT proposer un plan pour**:
- Modifications moyennes (2-3 fichiers)
- Changements de configuration
- Optimisations

### 2. Utilisation des Templates

**Q DOIT utiliser les templates standardisés**:
- `.q-context/templates/plan-development-template.md` pour développement
- `.q-context/templates/plan-diagnostic-template.md` pour diagnostic
- `.q-context/templates/plan-investigation-template.md` pour investigation

**Q DOIT**:
- Copier le template approprié
- Remplir TOUS les champs [TITRE], [DATE], etc.
- Adapter les phases selon le contexte
- **TOUJOURS inclure phases Git/Versioning/Tests** (voir section 2.1)
- Estimer les durées réalistes

### 2.1. Phases Git/Versioning/Tests OBLIGATOIRES

**CHAQUE plan de développement DOIT inclure ces phases**:

**Phase N-2: Versioning**
- Analyser type de changement (MAJOR/MINOR/PATCH)
- Incrémenter VERSION
- Documenter la raison
- Durée: 2 min

**Phase N-1: Commit Git**
- Préparer message commit (Conventional Commits)
- Lister fichiers modifiés
- Donner commandes git exactes
- Durée: 3 min

**Phase N: Tests & Validation**
- Build artefacts
- Deploy dev
- Tests E2E
- Validation résultats
- Durée: 10-15 min

**Phase N+1: Tag & Promotion (si succès)**
- Créer tag Git
- Promouvoir vers stage
- Tests stage
- Durée: 5-10 min

**Phase N+2: Rollback (si échec)**
- Détecter problème
- Proposer rollback
- Exécuter rollback
- Valider restauration
- Durée: 2-5 min

### 3. Emplacement des Plans et Rapports

**Q DOIT créer les plans dans**:
- `docs/plans/` pour les plans de développement
- `docs/diagnostics/` pour les plans de diagnostic

**Q DOIT créer les rapports finaux dans**:
- `docs/reports/development/` pour les rapports de développement
- `docs/reports/diagnostics/` pour les rapports de diagnostic
- `docs/reports/deployments/` pour les rapports de déploiement

**Convention nommage**:
```
# Plans
docs/plans/plan_[OBJECTIF]_[DATE].md
docs/diagnostics/diagnostic_[PROBLEME]_[DATE].md

# Rapports
docs/reports/development/report_[OBJECTIF]_[DATE].md
docs/reports/diagnostics/report_[PROBLEME]_[DATE].md
docs/reports/deployments/report_deploy_[VERSION]_[ENV]_[DATE].md
```

**Exemples**:
```
# Plans
docs/plans/plan_nouvelle_fonction_extraction_dates_20260130.md
docs/diagnostics/diagnostic_bedrock_timeout_20260130.md

# Rapports
docs/reports/development/report_extraction_dates_relatives_20260130.md
docs/reports/diagnostics/report_bedrock_timeout_resolution_20260130.md
docs/reports/deployments/report_deploy_v124_stage_20260130.md
```

### 4. Exécution Phase par Phase

**Q DOIT**:
- Exécuter UNE SEULE phase à la fois
- Présenter les résultats de la phase
- Demander validation utilisateur avant phase suivante
- Utiliser le format checkpoint standardisé

**Format checkpoint obligatoire**:
```
## ✅ Phase [N] Terminée

**Résultats**:
- [Résultat 1]
- [Résultat 2]

**Livrables**:
- [Livrable 1] ✅
- [Livrable 2] ✅

**Prêt pour Phase [N+1]** : [Description phase suivante]

**Souhaitez-vous continuer ?**
```

### 6. Création de Rapports Finaux

**Q DOIT créer un rapport final** à la fin de chaque plan contenant :
- Résumé exécutif
- Objectifs atteints vs prévus
- Durées réelles vs estimées
- Problèmes rencontrés et solutions
- Leçons apprises
- Recommandations pour l'avenir
- Métriques et KPIs

**Format rapport obligatoire** :
```markdown
# Rapport Final - [TITRE]

**Date**: [DATE]
**Plan source**: [LIEN_VERS_PLAN]
**Durée totale**: [X heures] (estimé: [Y heures])
**Statut**: [Succès/Partiel/Échec]

## Résumé Exécutif
[Résumé en 2-3 phrases]

## Objectifs et Résultats
- [Objectif 1]: ✅/❌ [Résultat]
- [Objectif 2]: ✅/❌ [Résultat]

## Métriques
| Phase | Durée Estimée | Durée Réelle | Écart |
|-------|----------------|-----------------|-------|
| Phase 1 | [X min] | [Y min] | [+/- Z min] |

## Leçons Apprises
- [Leçon 1]
- [Leçon 2]

## Recommandations
- [Recommandation 1]
- [Recommandation 2]
```

### 5. Gestion des Erreurs

**En cas de problème, Q DOIT**:
1. **STOP immédiat** de l'exécution
2. **Diagnostic rapide** (< 5 min)
3. **Proposition** : rollback ou correction
4. **Attendre** validation utilisateur

**Q NE DOIT JAMAIS**:
- Continuer en cas d'erreur
- Modifier le plan sans validation
- Ignorer les checkpoints

---

## 🚀 Patterns d'Exécution

### Pattern "Plan Simple" (< 1h)

```
1. Créer plan dans docs/plans/
2. Présenter plan à l'utilisateur
3. Attendre validation
4. Exécuter phases de développement
5. Phase Versioning (OBLIGATOIRE)
6. Phase Commit Git (OBLIGATOIRE)
7. Phase Tests & Validation (OBLIGATOIRE)
8. Phase Tag & Promotion (si succès)
9. Phase Rollback (si échec)
10. Finaliser et documenter
```

### Pattern "Plan Complexe" (> 1h)

```
1. Créer plan détaillé dans docs/plans/
2. Présenter vue d'ensemble
3. Demander validation du plan complet
4. Exécuter Phase 0 (cadrage)
5. Checkpoint et validation
6. Continuer phases de développement
7. Phase Versioning (OBLIGATOIRE)
8. Phase Commit Git (OBLIGATOIRE)
9. Phase Tests & Validation (OBLIGATOIRE)
10. Phase Tag & Promotion (si succès)
11. Phase Rollback (si échec)
12. Documentation finale
```

### Pattern "Diagnostic"

```
1. Créer plan diagnostic dans docs/diagnostics/
2. Phase 0: Reproduction problème
3. Phase 1: Investigation
4. Phase 2: Diagnostic
5. Phase 3: Évaluation risques
6. Phase 4: Recommandations
7. Phase 5: Questions ouvertes
```

---

## 📝 Templates de Communication

### Proposition de Plan

```
Je vais créer un plan structuré pour [OBJECTIF].

**Type de plan**: [Développement/Diagnostic]
**Complexité estimée**: [Faible/Moyenne/Élevée]
**Durée estimée**: [X heures]
**Phases prévues**: [N phases]

Le plan sera créé dans `docs/plans/plan_[OBJECTIF]_[DATE].md`

Souhaitez-vous que je procède ?
```

### Checkpoint Standard

```
## ✅ Phase [N] - [NOM_PHASE] Terminée

**Durée réelle**: [X min] (estimé: [Y min])

**Résultats**:
- ✅ [Résultat 1]
- ✅ [Résultat 2]
- ⚠️ [Point d'attention si applicable]

**Livrables validés**:
- ✅ [Livrable 1]
- ✅ [Livrable 2]

**Phase suivante**: [N+1] - [NOM_PHASE_SUIVANTE]
**Objectif**: [Description courte]
**Durée estimée**: [X min]

**Prêt à continuer ?**
```

### Gestion d'Erreur

```
🚨 **ERREUR DÉTECTÉE - ARRÊT PHASE [N]**

**Problème**: [Description erreur]
**Impact**: [Critique/Majeur/Mineur]

**Options**:
1. **Rollback** vers état précédent
2. **Correction** immédiate (si simple)
3. **Investigation** approfondie

**Recommandation**: [Option recommandée]

**Que souhaitez-vous faire ?**
```

---

## 🔧 Intégration avec Gouvernance

### Respect des Règles Existantes

**Q DOIT toujours respecter**:
- Workflow standard (Build → Deploy Dev → Test → Promote Stage)
- Règles d'hygiène (fichiers temporaires dans `.tmp/`)
- Versioning obligatoire
- Scripts standardisés uniquement

### Validation Environnements

**Q DOIT demander confirmation pour**:
- Déploiement vers stage
- Déploiement vers prod
- Modifications canonical
- Changements infrastructure

### Sauvegarde et Rollback

**Q DOIT proposer backup/snapshot pour**:
- Modifications critiques
- Changements architecture
- Déploiements production
- Modifications canonical importantes

---

## 📊 Métriques et Amélioration

### Métriques à Tracker

**Par plan**:
- Durée réelle vs estimée
- Nombre de phases
- Taux de succès par phase
- Nombre d'erreurs/rollbacks

**Globalement**:
- Temps moyen par type de plan
- Taux de succès global
- Satisfaction utilisateur

### Amélioration Continue

**Q DOIT**:
- Apprendre des durées réelles pour améliorer estimations
- Identifier patterns d'erreurs récurrents
- Proposer améliorations de templates

---

## 🎯 Exemples Concrets

### Exemple 1: Nouvelle Fonctionnalité

**Prompt utilisateur**: "Ajoute une fonction pour extraire les dates relatives dans vectora_core"

**Réponse Q**:
```
Je vais créer un plan de développement pour ajouter l'extraction de dates relatives.

**Analyse**:
- Modification code: src_v2/vectora_core/
- Tests requis: Oui
- Déploiement: dev → stage
- Complexité: Moyenne

Je crée le plan dans `docs/plans/plan_extraction_dates_relatives_20260130.md`

[Création du plan basé sur template]

Plan créé. Souhaitez-vous que je commence par la Phase 0 (Cadrage) ?
```

### Exemple 2: Diagnostic Problème

**Prompt utilisateur**: "Le matching Bedrock échoue avec des timeouts"

**Réponse Q**:
```
Je vais créer un plan de diagnostic pour les timeouts Bedrock.

**Analyse**:
- Symptôme: Timeouts Bedrock
- Impact: Critique (bloque le pipeline)
- Urgence: Élevée

Je crée le diagnostic dans `docs/diagnostics/diagnostic_bedrock_timeout_20260130.md`

[Création du plan diagnostic]

Plan de diagnostic créé. Souhaitez-vous que je commence par la Phase 0 (Reproduction du problème) ?
```

---

## ✅ Checklist pour Q Developer

**Avant de créer un plan**:
- [ ] Analyser la complexité de la demande
- [ ] Choisir le bon template
- [ ] Estimer durée et risques
- [ ] Définir les phases appropriées

**Pendant l'exécution**:
- [ ] Respecter l'ordre des phases
- [ ] Utiliser les checkpoints standardisés
- [ ] Demander validation à chaque phase
- [ ] Documenter les résultats

**En cas de problème**:
- [ ] Arrêter immédiatement
- [ ] Diagnostiquer rapidement
- [ ] Proposer options claires
- [ ] Attendre validation utilisateur

**À la fin**:
- [ ] Documenter les résultats
- [ ] Mettre à jour métriques
- [ ] Proposer améliorations

---

**Règles créées le**: 2026-01-30  
**Version**: 1.0  
**Statut**: Opérationnel