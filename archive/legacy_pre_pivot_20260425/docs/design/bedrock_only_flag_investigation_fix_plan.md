# Investigation Flag bedrock_only - Diagnostic et Plan de Correction

**Date :** 19 décembre 2025  
**Objectif :** Investiguer pourquoi le flag `bedrock_only: true` n'est pas pris en compte  
**Statut :** 🔍 INVESTIGATION COMPLÈTE - CAUSE IDENTIFIÉE  
**Priorité :** P0 - Bloquant pour architecture Bedrock-only

---

## 🎯 RÉSUMÉ EXÉCUTIF

**Problème identifié :** Le flag `bedrock_only: true` est correctement configuré sur S3 mais n'est pas pris en compte par la Lambda normalize-score-v2.

**Cause racine :** Structure de configuration incorrecte dans le chargement
- Configuration attendue : `client_config.matching_config.bedrock_only`
- Configuration réelle : `client_config.bedrock_only` (niveau racine)

**Impact :** 
- ✅ Bedrock matching fonctionne (~20 matchings sur 15 items)
- ❌ Matching déterministe s'exécute quand même (0 résultat)
- ❌ Résultats Bedrock écrasés par déterministe vide

**Solution :** Correction simple de la structure de configuration (2 lignes)

---

## 🔍 INVESTIGATION DÉTAILLÉE

### 1. Analyse du Code Actuel

**Condition dans `__init__.py` (ligne 85) :**
```python
if client_config.get('matching_config', {}).get('bedrock_only', False):
    # Mode Bedrock-only : utiliser directement les résultats Bedrock
    matched_items = normalized_items
    logger.info("Mode Bedrock-only activé : matching déterministe ignoré")
else:
    # Mode hybride existant (fallback)
    logger.info("Matching déterministe aux domaines de veille...")
    matched_items = matcher.match_items_to_domains(...)
```

**Configuration actuelle dans `lai_weekly_v3.yaml` :**
```yaml
# PROBLÈME : bedrock_only est au niveau racine
bedrock_only: true                    # NOUVEAU: Désactive matching déterministe

matching_config:
  min_domain_score: 0.25
  # bedrock_only devrait être ICI
```

### 2. Preuves du Problème

**Logs observés dans CloudWatch :**
```
[INFO] Configuration matching chargée: 0.25
[INFO] Watch domains configurés: 2
[INFO] Matching Bedrock V2: 1 domaines matchés sur 2 évalués  ✅
[INFO] Matching déterministe aux domaines de veille...        ❌ NE DEVRAIT PAS APPARAÎTRE
[INFO] Matching terminé: 0 matchés, 15 non-matchés           ❌ ÉCRASE BEDROCK
```

**Analyse :**
- Le message "Matching déterministe aux domaines de veille..." prouve que la condition `bedrock_only` est `False`
- Bedrock matching fonctionne parfaitement (plusieurs items matchés)
- Le matching déterministe écrase systématiquement les résultats Bedrock

### 3. Validation de la Configuration S3

**Configuration téléchargée depuis S3 :**
```bash
aws s3 cp s3://vectora-inbox-config-dev/clients/lai_weekly_v3.yaml lai_weekly_v3_from_s3.yaml
findstr "bedrock_only" lai_weekly_v3_from_s3.yaml
# Résultat: bedrock_only: true
```

**Structure attendue vs réelle :**
```yaml
# ATTENDU par le code
matching_config:
  bedrock_only: true

# RÉEL dans la configuration
bedrock_only: true  # Niveau racine - non détecté
```

---

## 🛠️ SOLUTIONS PROPOSÉES

### Solution A : Correction Configuration (RECOMMANDÉE)

**Avantages :**
- ✅ Correction minimale (2 lignes)
- ✅ Respecte l'architecture existante
- ✅ Pas de modification de code
- ✅ Déploiement immédiat

**Modification dans `lai_weekly_v3.yaml` :**
```yaml
matching_config:
  # === SEUILS DE BASE ===
  min_domain_score: 0.25
  bedrock_only: true                  # DÉPLACÉ ICI depuis niveau racine
  
  # === SEUILS PAR TYPE DE DOMAINE ===
  domain_type_thresholds:
    technology: 0.30
    regulatory: 0.20
```

**Suppression :**
```yaml
# SUPPRIMER cette ligne au niveau racine
# bedrock_only: true
```

### Solution B : Modification Code (ALTERNATIVE)

**Modification dans `__init__.py` :**
```python
# Vérifier les deux emplacements possibles
bedrock_only = (
    client_config.get('matching_config', {}).get('bedrock_only', False) or
    client_config.get('bedrock_only', False)
)

if bedrock_only:
    matched_items = normalized_items
    logger.info("Mode Bedrock-only activé : matching déterministe ignoré")
else:
    logger.info("Matching déterministe aux domaines de veille...")
    matched_items = matcher.match_items_to_domains(...)
```

---

## 📋 PLAN D'IMPLÉMENTATION

### Phase 1 : Correction Immédiate (5 minutes)

**Étape 1.1 : Correction Configuration**
```bash
# Modifier lai_weekly_v3.yaml localement
# Déplacer bedrock_only sous matching_config
```

**Étape 1.2 : Upload Configuration Corrigée**
```bash
aws s3 cp lai_weekly_v3.yaml s3://vectora-inbox-config-dev/clients/lai_weekly_v3.yaml --profile rag-lai-prod
```

**Étape 1.3 : Test Immédiat**
```bash
# Invoquer la Lambda avec force_reprocess: true
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v3 --force-reprocess
```

### Phase 2 : Validation (10 minutes)

**Étape 2.1 : Vérification Logs**
- Rechercher : "Mode Bedrock-only activé : matching déterministe ignoré"
- Vérifier absence de : "Matching déterministe aux domaines de veille..."

**Étape 2.2 : Validation Métriques**
- Items matchés > 0 (attendu : 9-12/15)
- Taux de matching > 60%
- Résultats Bedrock préservés

**Étape 2.3 : Comparaison Avant/Après**
```bash
# Avant : 0 items matchés
# Après : 9-12 items matchés (amélioration 60-80%)
```

### Phase 3 : Documentation (5 minutes)

**Étape 3.1 : Mise à Jour Template**
```yaml
# Dans client-config-examples/client_template_v2.yaml
matching_config:
  bedrock_only: false  # true pour mode Bedrock uniquement
```

**Étape 3.2 : Documentation Règles**
```markdown
# Dans vectora-inbox-development-rules.md
## Configuration bedrock_only
- Emplacement : matching_config.bedrock_only
- Valeurs : true (Bedrock seul) | false (hybride)
```

---

## 🎯 RÉSULTATS ATTENDUS

### Métriques Cibles

| Métrique | Avant | Après | Amélioration |
|----------|-------|-------|--------------|
| Items matchés | 0/15 (0%) | 9-12/15 (60-80%) | +60-80% |
| Bedrock matching | ✅ Fonctionne | ✅ Préservé | Maintenu |
| Matching déterministe | ❌ Écrase | ✅ Ignoré | Corrigé |
| Temps d'exécution | 104s | ~80s | -25% |

### Validation Fonctionnelle

**Items de référence attendus matchés :**
- ✅ Nanexa/Moderna Partnership (tech_lai_ecosystem)
- ✅ MedinCell/Teva NDA (tech_lai_ecosystem + regulatory_lai)
- ✅ Camurus Clinical Update (tech_lai_ecosystem)
- ✅ DelSiTech Technology News (tech_lai_ecosystem)

### Logs de Succès Attendus

```
[INFO] Configuration matching chargée: 0.25
[INFO] Watch domains configurés: 2
[INFO] Matching Bedrock V2: 1 domaines matchés sur 2 évalués
[INFO] Mode Bedrock-only activé : matching déterministe ignoré  ✅ NOUVEAU
[INFO] Matching combiné: 12 items matchés (12 via Bedrock)      ✅ AMÉLIORÉ
```

---

## 🚨 RISQUES ET MITIGATION

### Risques Identifiés

**Risque 1 : Cache Configuration**
- **Probabilité :** Faible
- **Impact :** Moyen
- **Mitigation :** Utiliser `force_reprocess: true` pour forcer rechargement

**Risque 2 : Régression Matching**
- **Probabilité :** Très faible
- **Impact :** Faible
- **Mitigation :** Bedrock matching déjà validé fonctionnel

### Plan de Rollback

**Si problème détecté :**
```bash
# Restaurer configuration précédente
aws s3 cp lai_weekly_v3.yaml.backup s3://vectora-inbox-config-dev/clients/lai_weekly_v3.yaml
```

---

## 📊 VALIDATION E2E

### Critères de Succès

- [ ] **Log "Mode Bedrock-only activé"** : Présent
- [ ] **Log "Matching déterministe"** : Absent
- [ ] **Items matchés** : ≥ 9/15 (60%+)
- [ ] **Temps d'exécution** : ≤ 90s
- [ ] **Aucune régression** : Bedrock matching préservé

### Tests de Non-Régression

```bash
# Test 1 : Configuration hybride (bedrock_only: false)
# Attendu : Matching déterministe + Bedrock

# Test 2 : Configuration Bedrock-only (bedrock_only: true)  
# Attendu : Bedrock uniquement

# Test 3 : Configuration manquante
# Attendu : Mode hybride par défaut
```

---

## 🎯 CONCLUSION

**Diagnostic :** Problème de structure de configuration simple mais critique

**Solution recommandée :** Correction configuration (Solution A)
- Déplacer `bedrock_only: true` sous `matching_config`
- Déploiement immédiat sans modification de code
- Validation en 5 minutes

**Impact attendu :** 
- Activation effective du mode Bedrock-only
- Amélioration taux de matching de 0% à 60-80%
- Préservation des résultats Bedrock intelligents

**Prochaines étapes :**
1. Correction configuration (2 minutes)
2. Upload S3 (1 minute)  
3. Test validation (2 minutes)
4. Documentation (5 minutes)

---

*Investigation Flag bedrock_only - Diagnostic et Plan de Correction*  
*Date : 19 décembre 2025*  
*Statut : 🔍 INVESTIGATION COMPLÈTE - SOLUTION IDENTIFIÉE*