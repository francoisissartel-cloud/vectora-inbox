# Vectora Inbox LAI Weekly v2 - Plan d'Exécution Corrections Qualité

**Date** : 2025-12-11  
**Objectif** : Implémenter les corrections P0 pour améliorer le ratio signal/noise de 20% à 60-80%  
**Mode** : Exécution autonome par phases

---

## Contexte

**Problème identifié** : Newsletter Run #2 avec 80% de bruit (HR/finance) et signal LAI majeur manquant (Nanexa/Moderna)

**Corrections P0** : Modifications configuration uniquement (30 minutes)
- Filtrer bruit HR/finance via exclusion_scopes
- Réduire pure_player_bonus déséquilibré  
- Ajouter termes LAI manquants (PharmaShell, drug delivery)
- Capturer trademarks LAI

**Impact attendu** : Newsletter Run #3 avec 60-80% signaux LAI authentiques

---

## Phase 1 : Enrichissement Technology Scopes

### Objectif
Capturer la news Nanexa/Moderna en ajoutant les termes LAI manquants identifiés lors du trace.

### Fichier cible
`canonical/scopes/technology_scopes.yaml`

### Modifications
```yaml
# Dans lai_keywords.technology_terms_high_precision, ajouter :
- "PharmaShell"
- "drug delivery"
- "controlled release"
- "sustained release"
- "extended release"
- "modified release"
- "atomic layer deposition"
```

### Validation
- PharmaShell® (Nanexa) détecté comme technologie LAI
- "drug delivery" générique reconnu
- "atomic layer deposition" (demande spécifique) ajouté

---

## Phase 2 : Ajout Exclusions HR/Finance

### Objectif
Éliminer le bruit HR/finance qui représente 60% des items newsletter actuels.

### Fichier cible
`canonical/scopes/exclusion_scopes.yaml`

### Modifications
```yaml
# Nouvelles sections à ajouter
hr_recruitment_terms:
  - "hiring"
  - "seeks"
  - "recruiting"
  - "job opening"
  - "career opportunities"
  - "position available"
  - "we are looking for"
  - "join our team"

financial_reporting_terms:
  - "financial results"
  - "earnings"
  - "consolidated results"
  - "interim report"
  - "quarterly results"
  - "half-year results"
  - "revenue"
  - "guidance"
  - "financial performance"
```

### Validation
- DelSiTech HR items (2x) filtrés
- MedinCell financial results filtré

---

## Phase 3 : Rééquilibrage Scoring

### Objectif
Réduire le pure_player_bonus qui permet aux items sans signaux LAI de dominer la newsletter.

### Fichier cible
`canonical/scoring/scoring_rules.yaml`

### Modifications
```yaml
# Ajustement du bonus pure player
pure_player_bonus: 2.0  # Réduit de 5.0 à 2.0

# Rééquilibrage compensatoire (si ces paramètres existent)
technology_bonus: 3.0   # Augmenté
molecule_bonus: 4.0     # Augmenté  
partnership_bonus: 3.0  # Augmenté
regulatory_bonus: 4.0   # Augmenté
```

### Validation
- Items pure players sans signaux LAI descendent sous seuil newsletter
- Items avec signaux LAI authentiques remontent

---

## Phase 4 : Déploiement AWS

### Objectif
Synchroniser les modifications canonical vers l'environnement DEV AWS.

### Actions
1. **Package canonical** : Créer archive avec modifications
2. **Upload S3** : Synchroniser vers bucket canonical DEV
3. **Invalidation cache** : Forcer rechargement configuration
4. **Validation déploiement** : Vérifier prise en compte modifications

### Commandes
```powershell
# Package et déploiement (à adapter selon scripts existants)
.\scripts\deploy-canonical-dev.ps1
```

---

## Phase 5 : Test Run #3

### Objectif
Valider l'impact des corrections via un run complet lai_weekly_v2.

### Actions
1. **Lancement run** : Exécuter pipeline complet
2. **Analyse newsletter** : Vérifier présence signaux LAI
3. **Validation métriques** : Confirmer réduction bruit

### Critères de succès
- ✅ **Nanexa/Moderna présent** en position #1-2
- ✅ **Bruit HR éliminé** (0% au lieu de 40%)
- ✅ **Bruit finance réduit** (<10% au lieu de 20%)
- ✅ **Signaux LAI** >60% (au lieu de 20%)

---

## Phase 6 : Documentation Résultats

### Objectif
Documenter l'impact des corrections pour validation et suivi.

### Livrables
- `docs/diagnostics/vectora_inbox_lai_weekly_v2_run3_results.md`
- Comparaison Run #2 vs Run #3
- Métriques signal/noise avant/après
- Recommandations Phase P1 si nécessaire

---

## Séquence d'Exécution

### Étape 1 : Modifications Canonical (10 minutes)
1. Modifier `technology_scopes.yaml`
2. Modifier `exclusion_scopes.yaml` 
3. Modifier `scoring_rules.yaml`
4. Commit modifications

### Étape 2 : Déploiement AWS (10 minutes)
1. Package canonical
2. Upload S3 DEV
3. Validation déploiement

### Étape 3 : Test & Validation (30 minutes)
1. Lancer Run #3
2. Analyser newsletter générée
3. Documenter résultats

### Étape 4 : Rapport Final (10 minutes)
1. Synthèse impact corrections
2. Recommandations suite si nécessaire

---

## Points de Contrôle

### Validation Technique
- [ ] Modifications canonical appliquées
- [ ] Déploiement AWS réussi
- [ ] Run #3 exécuté sans erreur
- [ ] Newsletter générée

### Validation Qualité
- [ ] Nanexa/Moderna présent dans newsletter
- [ ] Bruit HR/finance éliminé/réduit
- [ ] Ratio signal/noise >60%
- [ ] Newsletter utilisable pour veille LAI

### Validation Métier
- [ ] Items pertinents pour secteur LAI
- [ ] Équilibre pure players / hybrid companies
- [ ] Signaux majeurs captés
- [ ] Cohérence temporelle

---

## Rollback Plan

### En cas d'échec
1. **Sauvegarde** : Configurations originales sauvegardées
2. **Restauration** : Rollback canonical vers version précédente
3. **Re-déploiement** : Restaurer état Run #2
4. **Analyse** : Investigation causes échec

### Critères d'échec
- Newsletter vide ou erreur génération
- Perte signaux LAI authentiques existants
- Dégradation qualité globale
- Erreurs pipeline

---

## Métriques de Succès

### Quantitatives
- **Signaux LAI authentiques** : ≥60% (était 20%)
- **Bruit HR** : ≤10% (était 40%)
- **Bruit finance** : ≤10% (était 20%)
- **Items newsletter** : 5 items (stable)

### Qualitatives
- **Nanexa/Moderna** : Présent et bien positionné
- **MedinCell/Teva** : Maintenu (signal authentique)
- **Utilisabilité** : Newsletter exploitable pour veille
- **Cohérence** : Items pertinents secteur LAI

---

## Prochaines Étapes (Post-P0)

### Si succès P0
- **Phase P1** : Améliorations structurelles (Bedrock prompt, matching discriminant)
- **Corrections sources** : Camurus, Peptron
- **Monitoring** : Métriques qualité continues

### Si échec partiel P0
- **Diagnostic approfondi** : Investigation causes
- **Ajustements fins** : Calibrage paramètres
- **Tests itératifs** : Validation progressive

---

## Conclusion

**Plan d'exécution** : 4 phases techniques + 2 phases validation en 1 heure total.

**Objectif critique** : Newsletter Run #3 avec Nanexa/Moderna présent et bruit HR/finance éliminé.

**Validation** : Si succès, newsletter LAI Weekly v2 devient opérationnelle pour veille sectorielle.

**Prêt pour exécution autonome** : Toutes les modifications sont spécifiées et les critères de succès définis.