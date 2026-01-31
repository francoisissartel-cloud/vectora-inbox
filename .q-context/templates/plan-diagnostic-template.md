# Plan de Diagnostic - [PROBLÈME]

**Date**: YYYY-MM-DD  
**Symptôme**: [Description précise du problème observé]  
**Impact**: [Critique/Majeur/Mineur]  
**Urgence**: [Immédiate/Élevée/Normale]  
**Environnements affectés**: [dev/stage/prod]

---

## 🎯 Contexte du Problème

**Quand**: [Moment d'apparition du problème]  
**Où**: [Composants/environnements affectés]  
**Qui**: [Utilisateurs/processus impactés]  
**Fréquence**: [Systématique/Intermittent/Ponctuel]

**Symptômes observés**:
- [Symptôme 1]
- [Symptôme 2]
- [Symptôme 3]

---

## 📋 Plan d'Investigation

### Phase 0: Cadrage ⏱️ [X min]
- [ ] Reproduction du problème en environnement contrôlé
- [ ] Collecte exhaustive des symptômes
- [ ] Définition précise du périmètre d'investigation
- [ ] Priorisation selon impact métier

**Livrables Phase 0**:
- [ ] Problème reproductible
- [ ] Périmètre défini
- [ ] Impact quantifié

**✋ CHECKPOINT**: Validation utilisateur avant Phase 1

---

### Phase 1: Investigation ⏱️ [X min]
- [ ] Analyse logs système (`.tmp/logs/`, CloudWatch)
- [ ] Vérification configuration (client config, canonical)
- [ ] Tests ciblés sur composants suspects
- [ ] Analyse métriques et performance

**Sources à analyser**:
- [ ] Logs Lambda (`/aws/lambda/vectora-inbox-*`)
- [ ] Logs applicatifs (`.tmp/logs/`)
- [ ] Métriques CloudWatch
- [ ] Configuration S3 (`vectora-inbox-config-{env}`)
- [ ] Données S3 (`vectora-inbox-data-{env}`)

**Livrables Phase 1**:
- [ ] Logs analysés et synthétisés
- [ ] Tests ciblés effectués
- [ ] Première hypothèse formulée

**✋ CHECKPOINT**: Validation utilisateur avant Phase 2

---

### Phase 2: Diagnostic ⏱️ [X min]
- [ ] Identification cause racine probable
- [ ] Validation hypothèse par tests
- [ ] Évaluation impact complet
- [ ] Définition scénarios de résolution

**Méthodes de validation**:
- [ ] Tests de régression
- [ ] Comparaison avec environnement sain
- [ ] Analyse différentielle (avant/après)
- [ ] Validation avec données réelles

**Livrables Phase 2**:
- [ ] Cause racine identifiée
- [ ] Impact évalué
- [ ] Scénarios de résolution définis

**✋ CHECKPOINT**: Validation utilisateur avant Phase 3

---

### Phase 3: Évaluation Risques ⏱️ [X min]
- [ ] Risques de non-action (dégradation, impact métier)
- [ ] Risques des solutions proposées
- [ ] Analyse coût/bénéfice des options
- [ ] Priorisation des actions correctives

**Matrice des risques**:
| Solution | Probabilité Succès | Impact Positif | Risques | Effort |
|----------|-------------------|----------------|---------|--------|
| Option 1 | [%] | [Impact] | [Risques] | [Effort] |
| Option 2 | [%] | [Impact] | [Risques] | [Effort] |

**Livrables Phase 3**:
- [ ] Matrice risques/bénéfices
- [ ] Recommandation priorisée

**✋ CHECKPOINT**: Validation utilisateur avant Phase 4

---

### Phase 4: Recommandations ⏱️ [X min]
- [ ] Solution recommandée avec justification
- [ ] Solutions alternatives documentées
- [ ] Plan de mise en œuvre détaillé
- [ ] Estimation effort et délais

**Solution recommandée**:
- **Description**: [Solution détaillée]
- **Justification**: [Pourquoi cette solution]
- **Effort estimé**: [Temps/ressources]
- **Risques**: [Risques identifiés]

**Solutions alternatives**:
1. **Option A**: [Description, avantages, inconvénients]
2. **Option B**: [Description, avantages, inconvénients]

**Livrables Phase 4**:
- [ ] Plan d'action détaillé
- [ ] Estimation effort
- [ ] Alternatives documentées

**✋ CHECKPOINT**: Validation utilisateur avant Phase 5

---

### Phase 5: Questions Ouvertes ⏱️ [X min]
- [ ] Points nécessitant clarification
- [ ] Informations manquantes pour décision
- [ ] Validations techniques nécessaires
- [ ] Approbations métier requises

**Questions en suspens**:
1. [Question 1 - qui peut répondre]
2. [Question 2 - qui peut répondre]
3. [Question 3 - qui peut répondre]

**Informations manquantes**:
- [ ] [Information 1 - source]
- [ ] [Information 2 - source]

**Livrables Phase 5**:
- [ ] Liste questions/actions
- [ ] Responsables identifiés
- [ ] Délais de réponse
- [ ] **Rapport diagnostic final dans `docs/reports/diagnostics/`**

---

## 🔍 Analyse Technique Détaillée

### Composants Analysés
- [ ] **Lambdas**: [État, logs, métriques]
- [ ] **S3**: [Buckets, données, permissions]
- [ ] **Bedrock**: [Appels, erreurs, quotas]
- [ ] **Configuration**: [Client config, canonical]
- [ ] **Infrastructure**: [CloudFormation, IAM]

### Tests Effectués
- [ ] **Test 1**: [Description, résultat]
- [ ] **Test 2**: [Description, résultat]
- [ ] **Test 3**: [Description, résultat]

### Métriques Clés
| Métrique | Valeur Normale | Valeur Observée | Écart |
|----------|----------------|-----------------|-------|
| [Métrique 1] | [Normal] | [Observé] | [Écart] |
| [Métrique 2] | [Normal] | [Observé] | [Écart] |

---

## 🚨 Plan d'Action Immédiat

**Si problème critique**:
1. **Mesures d'urgence** (< 15 min)
2. **Communication stakeholders**
3. **Mise en place monitoring renforcé**
4. **Exécution solution temporaire si disponible**

**Commandes d'urgence**:
```bash
# Diagnostic rapide
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7 --debug

# Rollback si nécessaire
python scripts/deploy/rollback.py --env [ENV] --to-version [VERSION]

# Monitoring
tail -f .tmp/logs/debug_*.txt
```

---

## 📊 Suivi et Validation

**Critères de résolution**:
- [ ] [Critère 1 - mesurable]
- [ ] [Critère 2 - mesurable]
- [ ] [Critère 3 - mesurable]

**Plan de validation post-correction**:
- [ ] Tests de non-régression
- [ ] Monitoring 48h
- [ ] Validation utilisateurs
- [ ] Métriques de performance

**Indicateurs de succès**:
- [ ] Problème ne se reproduit plus
- [ ] Métriques revenues à la normale
- [ ] Aucun effet de bord détecté
- [ ] Utilisateurs satisfaits

---

## 📝 Documentation et Apprentissage

**Cause racine finale**: [À compléter après résolution]

**Leçons apprises**:
- [Leçon 1]
- [Leçon 2]

**Améliorations préventives**:
- [ ] [Amélioration 1 - monitoring]
- [ ] [Amélioration 2 - tests]
- [ ] [Amélioration 3 - documentation]

**Actions de suivi**:
- [ ] Mise à jour documentation
- [ ] Amélioration monitoring
- [ ] Formation équipe si nécessaire

---

**Diagnostic créé le**: [DATE]  
**Dernière mise à jour**: [DATE]  
**Statut**: [En cours/Résolu/Escaladé]  
**Responsable**: [Nom]