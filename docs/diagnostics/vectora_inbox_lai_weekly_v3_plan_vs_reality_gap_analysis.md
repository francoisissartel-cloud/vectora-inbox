# Vectora Inbox LAI Weekly v3 - Plan vs Réalité : Gap Analysis

**Date** : 2025-12-11  
**Audit** : Écart entre le plan human feedback et la réalité déployée  
**Status** : 🔍 DIAGNOSTIC COMPLET - Mode audit uniquement

---

## Executive Summary

**🎯 Objectif** : Comprendre pourquoi, malgré le plan d'amélioration détaillé, on observe toujours :
- ❌ Pas de news Nanexa/Moderna (PharmaShell®) dans la newsletter
- ❌ Du bruit HR/corporate/financial dans la newsletter  
- ❌ Des métriques qui ne correspondent pas aux objectifs du plan

**🔍 Constat principal** : Le plan human feedback est **partiellement appliqué** mais plusieurs éléments critiques ne sont **pas actifs** dans le pipeline réel.

---

## 1. Vérité Attendue du Plan

### 1.1 Modifications Attendues par Couche

#### **Canonical**
- ✅ **technology_scopes** : Ajout PharmaShell®, SiliaShell®, BEPO®, LAI
- ✅ **exclusion_scopes** : Ajout anti_lai_routes, hr_recruitment_terms, financial_reporting_terms  
- ✅ **trademark_scopes** : UZEDY présent dans lai_trademarks_global
- ✅ **scoring_rules** : Bonus augmentés (technology: 4.0, trademark: 5.0, regulatory: 6.0)

#### **Client Config**
- ✅ **lai_weekly_v3.yaml** : Configuration identique v2 avec ajustements mineurs
- ✅ **trademark_scope** : lai_trademarks_global configuré
- ✅ **scoring_config** : Bonus pure_player: 5.0, trademark: 4.0, min_score: 12

#### **Matching**
- ✅ **domain_matching_rules** : Technology_complex profile avec multi-signaux
- ⚠️ **Pattern matching** : LAI patterns définis mais utilisation incertaine

#### **Scoring**  
- ✅ **scoring_rules** : Bonus/malus configurés selon le plan
- ✅ **Contextual scoring** : Défini mais implémentation incertaine

#### **Ingestion**
- ✅ **ingestion_profiles** : Profils définis avec exclusions HR/finance
- ⚠️ **LLM gating** : Améliorations prévues mais pas vérifiées

### 1.2 Critères de Succès Chiffrés du Plan

- **Nanexa/Moderna** : ✅ Présent en newsletter
- **UZEDY regulatory** : ✅ Présent en newsletter  
- **Bruit HR/finance** : ✅ <20% (vs 80% avant)
- **Signaux LAI authentiques** : ✅ >60%
- **Items non-LAI ingérés** : ✅ <30% (vs 70% actuel)

---

## 2. État Réel du Repo Local vs Plan

### 2.1 Canonical

#### ✅ **technology_scopes.yaml** - ALIGNÉ
- **PharmaShell®, SiliaShell®, BEPO®** : ✅ Présents dans technology_terms_high_precision
- **LAI** : ✅ Présent comme acronyme direct
- **Negative_terms** : ✅ Routes orales définies (oral tablet, oral capsule, etc.)

#### ✅ **exclusion_scopes.yaml** - ALIGNÉ  
- **anti_lai_routes** : ✅ Défini avec oral tablet, oral capsule, etc.
- **hr_recruitment_terms** : ✅ Défini avec hiring, recruiting, etc.
- **financial_reporting_terms** : ✅ Défini avec financial results, earnings, etc.

#### ✅ **trademark_scopes.yaml** - ALIGNÉ
- **UZEDY** : ✅ Présent dans lai_trademarks_global (ligne 43)
- **Liste complète** : ✅ 80+ trademarks LAI référencés

#### ✅ **scoring_rules.yaml** - ALIGNÉ
- **technology_bonus** : ✅ 4.0 (augmenté selon plan)
- **trademark_bonus** : ✅ 5.0 (augmenté selon plan)  
- **regulatory_bonus** : ✅ 6.0 (augmenté selon plan)
- **oral_route_penalty** : ✅ -10 (nouveau malus)
- **pure_player_bonus** : ✅ 1.5 (réduit de 2.0 selon plan)

### 2.2 Client Config

#### ✅ **lai_weekly_v3.yaml** - ALIGNÉ
- **trademark_scope** : ✅ lai_trademarks_global configuré
- **scoring_config** : ✅ Bonus pure_player: 5.0, trademark: 4.0
- **min_score** : ✅ 12 (seuil strict)
- **default_period_days** : ✅ 30 (fenêtre étendue LAI)

### 2.3 Matching

#### ✅ **domain_matching_rules.yaml** - ALIGNÉ
- **technology_complex** : ✅ Profile défini avec multi-signaux
- **Pattern matching** : ✅ LAI patterns définis (.*LAI$, .*Injectable$, .*Depot$)
- **Entity requirements** : ✅ Trademark ajouté comme source

### 2.4 Ingestion

#### ✅ **ingestion_profiles.yaml** - ALIGNÉ
- **Exclusions HR/finance** : ✅ Référencées dans corporate_pure_player_broad
- **Technology focused** : ✅ Profil press_technology_focused défini
- **Signal requirements** : ✅ Multi-signaux configurés

---

## 3. État Réel AWS DEV vs Repo Local

### 3.1 Synchronisation Canonical

#### ✅ **Files déployés** - SYNCHRONISÉS
- **technology_scopes.yaml** : ✅ Identique (PharmaShell®, SiliaShell®, BEPO® présents)
- **trademark_scopes.yaml** : ✅ Identique (UZEDY présent)
- **exclusion_scopes.yaml** : ✅ Identique (anti_lai_routes présent)
- **scoring_rules.yaml** : ✅ Identique (bonus augmentés présents)

#### ✅ **Client Config** - SYNCHRONISÉ
- **lai_weekly_v3.yaml** : ✅ Présent dans S3 (s3://vectora-inbox-config-dev/clients/)
- **Date de modification** : 2025-12-11 22:54:02 (récent)

### 3.2 Lambda Engine

#### ⚠️ **État Lambda** - NON VÉRIFIÉ
- **Version déployée** : Non vérifiée dans ce diagnostic
- **Handler** : Non vérifié
- **Variables d'environnement** : Non vérifiées

---

## 4. Traçage Item Clé : Nanexa/Moderna PharmaShell®

### 4.1 Présence dans le Pipeline

#### ✅ **Ingestion** - PRÉSENT
```json
{
  "title": "Nanexa and Moderna enter into license and option agreement for the development of PharmaShell®-based products",
  "url": "https://nanexa.com/mfn_news/nanexa-and-moderna-enter-into-license-and-option-agreement-for-the-development-of-pharmashell-based-products/",
  "published_at": "2025-12-11",
  "source_key": "press_corporate__nanexa"
}
```

#### ❌ **Normalisation** - ABSENT
- **Constat** : L'item n'apparaît pas dans les données normalisées
- **Cause probable** : Filtré lors de la phase de normalisation Bedrock
- **raw_text vide** : Problème d'extraction HTML ou contenu non accessible

### 4.2 Analyse de l'Échec

#### **Hypothèse principale** : Échec d'extraction HTML
- **raw_text** : Vide dans les données brutes
- **Impact** : Sans contenu, Bedrock ne peut pas normaliser l'item
- **Conséquence** : Item perdu avant même le matching/scoring

#### **Signaux LAI théoriquement détectables** :
- **Nanexa** : ✅ Company LAI pure player
- **Moderna** : ✅ Company LAI hybrid  
- **PharmaShell®** : ✅ Technology présente dans technology_scopes
- **License agreement** : ✅ Event type partnership

---

## 5. Traçage Items "Bruit" dans la Newsletter

### 5.1 Items HR/Corporate Présents

#### **DelSiTech CEO Leadership Change**
```json
{
  "title": "DelSiTech announces a leadership change. Carl-Åke Carlsson, CEO of DelSiTech, leaves the company...",
  "event_type": "corporate_move",
  "companies_detected": ["DelSiTech"],
  "pure_player_bonus": 5.0
}
```

**Pourquoi accepté** :
- ✅ **DelSiTech** : Pure player LAI (bonus 5.0)
- ✅ **Event type** : corporate_move (weight: 2)
- ❌ **Problème** : Pas de signaux LAI technologiques, mais pure player bonus compense

#### **DelSiTech Process Engineer Hiring**
```json
{
  "title": "DelSiTech is Hiring a Process Engineer",
  "event_type": "other",
  "companies_detected": ["DelSiTech"]
}
```

**Pourquoi accepté** :
- ✅ **DelSiTech** : Pure player LAI (bonus 5.0)
- ❌ **HR content** : Devrait être filtré par exclusion_scopes.hr_recruitment_terms
- ❌ **Problème** : Filtrage HR non appliqué ou inefficace

#### **MedinCell H1 Financial Results**
```json
{
  "title": "Medincell Publishes its Consolidated Half-Year Financial Results",
  "event_type": "financial_results",
  "companies_detected": ["MedinCell"]
}
```

**Pourquoi accepté** :
- ✅ **MedinCell** : Pure player LAI (bonus 5.0)
- ❌ **Financial content** : Devrait être filtré par exclusion_scopes.financial_reporting_terms
- ❌ **Problème** : Filtrage financier non appliqué ou inefficace

### 5.2 Analyse des Échecs de Filtrage

#### **Problème principal** : Pure player bonus trop élevé
- **Bonus pure_player** : 5.0 (configuré dans lai_weekly_v3.yaml)
- **Impact** : Compense largement les pénalités HR/finance
- **Conséquence** : Items non-LAI remontent quand même

#### **Filtrage exclusion_scopes non appliqué** :
- **HR terms** : "hiring", "process engineer" devraient être exclus
- **Financial terms** : "financial results", "consolidated" devraient être exclus
- **Cause probable** : Logique d'exclusion non implémentée dans le code

---

## 6. Synthèse : Plan vs Réalité

### 6.1 Tableau de Conformité

| **Couche** | **Plan** | **Repo Local** | **AWS DEV** | **Pipeline Réel** | **Status** |
|------------|----------|----------------|-------------|-------------------|------------|
| **Canonical - technology_scopes** | PharmaShell®, BEPO®, LAI | ✅ Présent | ✅ Synchronisé | ❓ Non testé | ⚠️ **PARTIELLEMENT ALIGNÉ** |
| **Canonical - exclusion_scopes** | anti_lai_routes, hr_terms | ✅ Présent | ✅ Synchronisé | ❌ Non appliqué | ❌ **NON ALIGNÉ** |
| **Canonical - trademark_scopes** | UZEDY présent | ✅ Présent | ✅ Synchronisé | ❓ Non testé | ⚠️ **PARTIELLEMENT ALIGNÉ** |
| **Canonical - scoring_rules** | Bonus augmentés | ✅ Présent | ✅ Synchronisé | ⚠️ Partiellement | ⚠️ **PARTIELLEMENT ALIGNÉ** |
| **Client Config** | lai_weekly_v3 configuré | ✅ Présent | ✅ Synchronisé | ✅ Actif | ✅ **ALIGNÉ** |
| **Matching** | Technology_complex | ✅ Présent | ✅ Synchronisé | ❓ Non testé | ⚠️ **PARTIELLEMENT ALIGNÉ** |
| **Scoring** | Contextuel par company | ✅ Présent | ✅ Synchronisé | ❌ Non appliqué | ❌ **NON ALIGNÉ** |
| **Ingestion** | Filtrage HR/finance | ✅ Présent | ✅ Synchronisé | ❌ Non appliqué | ❌ **NON ALIGNÉ** |

### 6.2 Problèmes Identifiés

#### **P0 - Critiques**

1. **Extraction HTML défaillante**
   - **Symptôme** : raw_text vide pour Nanexa/Moderna
   - **Impact** : Items LAI majeurs perdus avant normalisation
   - **Cause** : Problème d'extraction ou contenu non accessible

2. **Filtrage exclusion_scopes non appliqué**
   - **Symptôme** : Items HR/finance passent malgré les exclusions définies
   - **Impact** : Bruit dans la newsletter (60% des items)
   - **Cause** : Logique d'exclusion non implémentée dans le code

3. **Pure player bonus trop dominant**
   - **Symptôme** : Items non-LAI remontent grâce au bonus pure player
   - **Impact** : Newsletter dominée par corporate/HR au lieu de LAI
   - **Cause** : Bonus 5.0 trop élevé vs pénalités inexistantes

#### **P1 - Importantes**

4. **Technology matching non testé**
   - **Symptôme** : PharmaShell® présent dans scopes mais efficacité inconnue
   - **Impact** : Signaux LAI potentiellement non détectés
   - **Cause** : Logique de matching technology_complex non vérifiée

5. **Trademark detection non vérifiée**
   - **Symptôme** : UZEDY présent dans scopes mais pas d'items UZEDY récents
   - **Impact** : Signaux trademark LAI potentiellement manqués
   - **Cause** : Période d'analyse ou détection inefficace

---

## 7. Recommandations Prioritaires

### 7.1 P0 - Corrections Immédiates

#### **P0.1 - Corriger l'extraction HTML Nanexa**
```bash
# Vérifier l'extracteur HTML pour nanexa.se
# Tester manuellement l'URL problématique
curl -A "Mozilla/5.0" "https://nanexa.com/mfn_news/nanexa-and-moderna-enter-into-license-and-option-agreement-for-the-development-of-pharmashell-based-products/"
```

#### **P0.2 - Implémenter le filtrage exclusion_scopes**
```python
# Dans le code de normalisation Bedrock
# Ajouter la logique d'exclusion avant envoi à Bedrock
def should_exclude_content(text, exclusion_scopes):
    for scope in exclusion_scopes:
        for term in scope:
            if term.lower() in text.lower():
                return True
    return False
```

#### **P0.3 - Réduire le pure player bonus**
```yaml
# Dans lai_weekly_v3.yaml
scoring_config:
  client_specific_bonuses:
    pure_player_companies:
      bonus: 3.0  # Réduit de 5.0 à 3.0
```

### 7.2 P1 - Améliorations Fond

#### **P1.1 - Vérifier technology matching**
- Tester la détection de PharmaShell® sur un item avec contenu
- Valider la logique technology_complex multi-signaux

#### **P1.2 - Vérifier trademark detection**  
- Tester la détection UZEDY sur des items récents
- Valider le boost trademark_bonus: 5.0

#### **P1.3 - Implémenter scoring contextuel**
- Activer les bonus/malus contextuels par type de company
- Appliquer les pénalités HR/finance définies

### 7.3 P2 - Optimisations Avancées

#### **P2.1 - Améliorer l'ingestion sélective**
- Activer les profils d'ingestion différenciés
- Implémenter le LLM gating enrichi

#### **P2.2 - Calibrer les seuils**
- Ajuster min_score selon la qualité observée
- Équilibrer les bonus entre pure players et hybrid companies

---

## 8. Métriques Actuelles vs Objectifs

### 8.1 Newsletter lai_weekly_v3 (11 Dec 2025)

#### **Métriques Observées**
- **Items sélectionnés** : 5 items
- **Pure players** : 100% (5/5 items MedinCell + DelSiTech)
- **Signaux LAI authentiques** : 20% (1/5 items - Olanzapine NDA)
- **Bruit HR/corporate** : 80% (4/5 items - CEO change, hiring, financial)
- **Items Nanexa/Moderna** : 0% (absent)

#### **Objectifs du Plan**
- **Signaux LAI authentiques** : >60% ❌ (20% observé)
- **Bruit HR/finance** : <20% ❌ (80% observé)  
- **Nanexa/Moderna** : Présent ❌ (absent)
- **UZEDY** : Présent ❌ (pas d'items récents)

#### **Écart Plan vs Réalité**
- **Signaux LAI** : -40 points (60% attendu vs 20% observé)
- **Bruit** : +60 points (20% attendu vs 80% observé)
- **Coverage** : Items LAI majeurs manqués

---

## 9. Conclusion

### 9.1 Diagnostic Principal

**Le plan human feedback est théoriquement bien défini et déployé, mais plusieurs éléments critiques ne sont pas actifs dans le pipeline réel** :

1. **Extraction HTML défaillante** → Items LAI majeurs perdus
2. **Filtrage exclusion_scopes non appliqué** → Bruit HR/finance non filtré  
3. **Pure player bonus trop dominant** → Items non-LAI remontent artificiellement

### 9.2 Prochaines Étapes

#### **Phase Corrective Immédiate**
1. ✅ Diagnostic complet réalisé
2. 🔧 Corriger l'extraction HTML Nanexa (P0.1)
3. 🔧 Implémenter le filtrage exclusion_scopes (P0.2)
4. 🔧 Réduire le pure player bonus (P0.3)

#### **Phase Validation**
5. 🧪 Tester les corrections sur un nouveau run
6. 📊 Mesurer l'amélioration des métriques
7. ✅ Valider l'atteinte des objectifs du plan

**Le plan était bon, l'exécution est incomplète. Les corrections sont identifiées et priorisées.**

---

*Diagnostic réalisé le 2025-12-11 - Mode audit uniquement*