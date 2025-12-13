# Vectora Inbox — LAI Runtime Phase 4: Guide d'Exécution

**Date:** 2025-01-XX  
**Phase:** 4/4 — Test End-to-End & Métriques  
**Statut:** ✅ PRÊT POUR EXÉCUTION

---

## Objectif de la Phase 4

Valider l'ensemble des corrections apportées dans les Phases 2 et 3 en :
1. Déployant la solution complète en DEV
2. Exécutant un run complet lai_weekly
3. Mesurant les métriques finales
4. Décidant du GO/NO-GO pour PROD

---

## Prérequis

### Vérifications Avant Déploiement

✅ **Phase 2 implémentée:**
- Filtrage generic_terms
- Veto negative_terms
- Logs de traçabilité

✅ **Phase 3 implémentée:**
- Règle fallback durcie (min_matches: 2)
- Seuils adaptatifs par company type
- Bonus scoring amélioré

✅ **Environnement DEV prêt:**
- Lambda engine déployable
- Config canonical uploadable
- Accès S3 et CloudWatch

---

## Étape 1: Déploiement Complet

### Option A: Script Automatisé (Recommandé)

```powershell
.\scripts\deploy_phase4_complete.ps1
```

Ce script exécute automatiquement :
1. Upload de la config canonical
2. Repackage de la Lambda
3. Déploiement sur AWS
4. Vérification du déploiement
5. Exécution de l'engine lai_weekly

### Option B: Déploiement Manuel

```powershell
# 1. Upload config
aws s3 cp canonical/matching/domain_matching_rules.yaml s3://vectora-inbox-config-dev/canonical/matching/

# 2. Package Lambda
python scripts/package_lambda.py

# 3. Deploy Lambda
python scripts/deploy_lambda.py --env dev

# 4. Vérifier
aws lambda get-function --function-name vectora-inbox-engine-dev

# 5. Exécuter engine
python scripts/run_engine.py --env dev --client lai_weekly
```

### Vérification du Déploiement

```powershell
# Vérifier la Lambda
aws lambda get-function --function-name vectora-inbox-engine-dev --query 'Configuration.[FunctionName,LastModified,CodeSize]'

# Vérifier la config canonical
aws s3 ls s3://vectora-inbox-config-dev/canonical/matching/
```

---

## Étape 2: Analyse des Résultats

### 2.1. Télécharger la Newsletter

```powershell
aws s3 cp s3://vectora-inbox-newsletters-dev/lai_weekly/latest/newsletter.json .
```

### 2.2. Analyser les Métriques Automatiques

```powershell
python scripts/analyze_newsletter_phase4.py newsletter.json
```

**Sortie attendue:**
```
📊 MÉTRIQUES GLOBALES
   Total items: X
   Pure players: X (X%)
   Hybrid: X (X%)
   Other: X (X%)

🎯 OBJECTIFS MVP
   LAI precision: À valider manuellement (objectif ≥80%)
   Pure player %: X% (objectif ≥50%) ✅/❌
   False positives: À valider manuellement (objectif 0)

✅ PURE PLAYERS DÉTECTÉS (X)
   1. MedinCell (score: X) - [titre]...
   2. Camurus (score: X) - [titre]...

⚠️  HYBRID DÉTECTÉS (X)
   1. Pfizer (score: X, conf: medium) - [titre]...
```

### 2.3. Vérifier les Logs CloudWatch

**Logs Phase 2 (Filtrage):**
```powershell
aws logs tail /aws/lambda/vectora-inbox-engine-dev --since 1h --filter-pattern "[SIGNAL_SUMMARY]"
aws logs tail /aws/lambda/vectora-inbox-engine-dev --since 1h --filter-pattern "[NEGATIVE_VETO]"
```

**Logs Phase 3 (Pure_Player):**
```powershell
aws logs tail /aws/lambda/vectora-inbox-engine-dev --since 1h --filter-pattern "[COMPANY_TYPE]"
aws logs tail /aws/lambda/vectora-inbox-engine-dev --since 1h --filter-pattern "[SCORING]"
```

---

## Étape 3: Validation Manuelle

### 3.1. Utiliser le Template de Validation

1. Ouvrir `vectora_inbox_lai_runtime_phase4_validation_template.md`
2. Pour chaque item de la newsletter :
   - Copier le titre, company, score
   - Classifier : ✅ Vrai Positif / ❌ Faux Positif
   - Justifier la classification

### 3.2. Critères de Classification

**✅ Vrai Positif LAI:**
- Mentionne explicitement LAI (long-acting, depot, sustained-release, etc.)
- Concerne une company du scope LAI
- Information pertinente pour la veille LAI
- Exemples : approbation FDA LAI, résultats essai clinique LAI, partenariat LAI

**❌ Faux Positif:**
- Forme galénique non-LAI (oral, topical, IV, etc.)
- Mention LAI trop faible ou hors contexte
- Company hors scope LAI
- Information non pertinente
- Exemples : oral tablet, topical cream, IV infusion

### 3.3. Calculer les Métriques Finales

**LAI precision:**
```
LAI precision = (Nombre de vrais positifs / Total items) × 100
```

**Pure player %:**
```
Calculé automatiquement par le script analyze_newsletter_phase4.py
```

**False positives:**
```
Nombre de faux positifs identifiés manuellement
```

---

## Étape 4: Décision GO/NO-GO

### Critères de Décision

| Décision | Critères | Action |
|----------|----------|--------|
| 🟢 **GREEN (GO PROD)** | 3/3 objectifs atteints | Déployer en PROD |
| 🟡 **AMBER (ITERATION)** | 2/3 objectifs atteints | Itération mineure |
| 🔴 **RED (NO-GO)** | <2 objectifs atteints | Refonte nécessaire |

### Objectifs MVP

| Métrique | Objectif | Mesure |
|----------|----------|--------|
| LAI precision | ≥80% | Validation manuelle |
| Pure player % | ≥50% | Script automatique |
| False positives | 0 | Validation manuelle |

---

## Étape 5: Documentation des Résultats

### 5.1. Créer le Rapport Final

Créer `vectora_inbox_lai_runtime_phase4_final_results.md` avec :
- Métriques calculées
- Décision GO/NO-GO
- Observations et recommandations
- Prochaines étapes

### 5.2. Mettre à Jour le CHANGELOG

Ajouter une section Phase 4 dans `CHANGELOG.md` :
```markdown
### Phase 4 — Test End-to-End & Métriques (2025-01-XX)

#### Results
- LAI precision: X%
- Pure player %: X%
- False positives: X

#### Decision
- 🟢/🟡/🔴 [GREEN/AMBER/RED]

#### Next Steps
- [ACTIONS À PRENDRE]
```

---

## Troubleshooting

### Problème: Aucun item dans la newsletter

**Cause possible:** Matching trop strict après Phase 2+3

**Actions:**
1. Vérifier les logs `[SIGNAL_SUMMARY]` pour voir les signaux comptés
2. Vérifier les logs `[NEGATIVE_VETO]` pour voir les rejets
3. Ajuster les seuils si nécessaire

### Problème: Pure player % < 50%

**Cause possible:** Bonus scoring non appliqué

**Actions:**
1. Vérifier les logs `[SCORING]` et `[SCORING_FALLBACK]`
2. Vérifier que les scopes pure_player sont bien chargés
3. Vérifier que les companies sont bien détectées par Bedrock

### Problème: Trop de faux positifs

**Cause possible:** Filtrage insuffisant

**Actions:**
1. Vérifier que generic_terms sont bien exclus
2. Vérifier que negative_terms sont bien appliqués
3. Durcir davantage la règle de fallback (min_matches: 3)

---

## Checklist de Validation

### Avant Exécution
- [ ] Phase 2 implémentée et testée
- [ ] Phase 3 implémentée et testée
- [ ] Environnement DEV prêt
- [ ] Accès AWS configuré

### Pendant Exécution
- [ ] Config canonical uploadée
- [ ] Lambda déployée avec succès
- [ ] Engine exécuté sans erreur
- [ ] Newsletter générée

### Après Exécution
- [ ] Newsletter téléchargée
- [ ] Métriques automatiques calculées
- [ ] Logs CloudWatch vérifiés
- [ ] Validation manuelle complétée
- [ ] Métriques finales calculées
- [ ] Décision GO/NO-GO prise
- [ ] Documentation complétée
- [ ] CHANGELOG mis à jour

---

## Prochaines Étapes Selon Décision

### Si GREEN (GO PROD)
1. Créer un backup de la config DEV
2. Déployer en PROD
3. Monitorer les premiers runs PROD
4. Documenter les leçons apprises

### Si AMBER (ITERATION)
1. Identifier les ajustements nécessaires
2. Planifier une itération mineure (Phase 4.1)
3. Retester après ajustements
4. Réévaluer la décision

### Si RED (NO-GO)
1. Analyser les root causes des échecs
2. Planifier une refonte (Phase 5)
3. Documenter les leçons apprises
4. Réévaluer l'approche globale

---

## Contacts & Support

**Questions techniques:** [CONTACT]  
**Validation métier:** [CONTACT]  
**Décision GO/NO-GO:** [CONTACT]

---

**Statut:** ✅ PRÊT POUR EXÉCUTION  
**Prochaine étape:** Exécuter `.\scripts\deploy_phase4_complete.ps1`
