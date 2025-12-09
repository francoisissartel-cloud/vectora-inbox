# Vectora Inbox — LAI Technology Scopes Refactor Plan

**Date:** 2025-01-XX  
**Scope:** Canonical refactor only (technology_scopes.yaml + company_scopes.yaml)  
**Status:** Design & Execution Plan

---

## 1. Contexte métier

### Objectif
Rendre le scope LAI conforme à la définition métier stricte des Long-Acting Injectables (LAI) pour améliorer la précision du matching et éliminer les faux positifs.

### Problème actuel
- **Précision LAI à 0%** dans le domaine `tech_lai_ecosystem`
- Le scope `lai_keywords` dans `technology_scopes.yaml` contient des termes trop génériques qui déclenchent des matches sur des entreprises non-LAI (Pfizer, AbbVie, etc.)
- Exemples de termes problématiques actuels :
  - `drug delivery system` (trop large)
  - `liposomes`, `liposomal` (utilisés dans de nombreux contextes non-LAI)
  - `emulsion`, `lipid emulsion` (non spécifiques LAI)
  - `PEG`, `PEGylation`, `PEGylated` (utilisés dans de nombreux contextes)
  - `subcutaneous`, `intramuscular` (routes d'administration seules, sans contexte LAI)
  - `protein engineering` (trop générique)
  - `hydrogel`, `nanosuspension`, etc. (sans contexte LAI explicite)

### Définition métier LAI (référence canonique)
D'après `glossary.md` et `LAI_RATIONALE.md` :

**Un LAI est une formulation injectable qui :**
1. Est administrée par injection (IM, SC, IV, intravitreal, intra-articular, etc.)
2. Utilise une technologie reconnue :
   - **DDS (Drug Delivery System)** : système de dépôt libérant l'API progressivement
   - **HLE (Half-Life Extension)** : stratégie moléculaire prolongeant la demi-vie systémique
3. Fournit un effet thérapeutique prolongé sur **semaines à mois** à partir d'une seule injection

**Critères d'exclusion :**
- Dispositifs implantables
- Thérapies géniques/cellulaires
- Perfusions IV simples sans dépôt ni HLE

---

## 2. Sources métier utilisées

### Fichiers canoniques
- `canonical/scopes/technology_scopes.yaml` (état actuel)
- `canonical/scopes/company_scopes.yaml` (état actuel)

### Fichiers imports (taxonomie métier)
- `canonical/imports/glossary.md` — définition canonique LAI
- `canonical/imports/LAI_RATIONALE.md` — rationale et différenciation LAI
- `canonical/imports/technology_type.csv` — tech_dds vs tech_hle
- `canonical/imports/technology_family.csv` — familles DDS et HLE
- `canonical/imports/technology_tag.csv` — tags technologiques
- `canonical/imports/route_admin.csv` — routes d'administration
- `canonical/imports/narrative_topic.csv` — topics narratifs

---

## 3. Structure cible pour le scope LAI

### Nouvelle architecture `lai_keywords`

```yaml
lai_keywords:
  core_phrases:
    # Expressions explicites LAI (haute précision)
    - "long-acting injectable"
    - "long acting injectable"
    - "extended-release injection"
    - "extended-release injectable"
    - "controlled-release injection"
    - "sustained release injectable"
    - "depot injection"
    - "long-acting depot"
    - "long-acting formulation"
    
  technology_terms_high_precision:
    # Termes technologiques spécifiques LAI (DDS + HLE)
    # DDS families
    - "polymeric microspheres"
    - "PLGA microspheres"
    - "in-situ forming depot"
    - "ISFD"
    - "in situ depot"
    - "Atrigel"
    - "FluidCrystal"
    - "SmartDepot"
    - "multivesicular liposomes"
    - "MVL"
    - "DepoFoam"
    - "BioSeizer"
    - "thermo-responsive hydrogel"
    - "RTGel"
    - "liquid crystalline depot"
    - "liquid crystal"
    - "depot-forming prodrug"
    - "depot prodrug"
    - "long-acting prodrug"
    - "long-acting emulsion"
    # HLE strategies (when combined with injection context)
    - "PASylation"
    - "site-specific PEGylation"
    - "Fc fusion"
    - "Fc-fusion"
    - "IgG Fc fusion"
    - "albumin binding"
    - "albumin fusion"
    - "albumin-binding"
    - "lipidation"
    - "fatty acid conjugation"
    - "XTEN"
    - "polypeptide extension"
    - "glyco-engineering"
    - "glycan engineering"
    - "sialylation"
    
  technology_use:
    # Termes d'usage (doivent être combinés avec d'autres signaux)
    - "injectable"
    - "injection"
    - "depot"
    - "microsphere"
    - "microspheres"
    - "thermo-gel"
    - "nanocrystal"
    - "nanosizing"
    - "oil-based"
    
  route_admin_terms:
    # Routes d'administration (contexte nécessaire mais non suffisant)
    - "intramuscular"
    - "subcutaneous"
    - "intravenous"
    - "intravitreal"
    - "intratumoral"
    - "intra-articular"
    - "intrathecal"
    - "intravesical"
    - "epidural"
    
  interval_patterns:
    # Patterns d'intervalle typiques LAI (signaux forts)
    - "once-monthly"
    - "once-weekly injection"
    - "q4w"
    - "q8w"
    - "q12w"
    - "6-month"
    - "quarterly injection"
    - "half-life extension"
    
  generic_terms:
    # Termes trop génériques (conservés pour mémoire, ne matchent plus seuls)
    - "drug delivery system"
    - "liposomes"
    - "liposomal"
    - "PLEX"
    - "hydrogel"
    - "nanosuspension"
    - "emulsion"
    - "lipid emulsion"
    - "PEGylation"
    - "PEGylated"
    - "PEG"
    - "protein engineering"
    
  negative_terms:
    # Signaux forts de NON-LAI
    - "oral tablet"
    - "oral capsule"
    - "topical cream"
    - "topical gel"
    - "transdermal patch"
    - "inhalation"
    - "nasal spray"
```

### Principes de classification

1. **core_phrases** : expressions explicites LAI → match immédiat haute confiance
2. **technology_terms_high_precision** : termes techno spécifiques DDS/HLE → match haute confiance si contexte injectable
3. **technology_use** : termes d'usage → nécessitent combinaison avec core_phrases ou technology_terms
4. **route_admin_terms** : routes d'administration → contexte nécessaire mais non suffisant seul
5. **interval_patterns** : patterns de dosage prolongé → signaux forts LAI
6. **generic_terms** : termes trop larges → ne déclenchent plus de match seuls, conservés pour documentation
7. **negative_terms** : exclusions explicites → signaux de NON-LAI

---

## 4. Plan d'exécution en 4 phases

### Phase 1 — Refactor LAI dans technology_scopes.yaml

**Objectif :** Restructurer le scope `lai_keywords` selon la nouvelle architecture.

**Actions :**
1. Lire l'état actuel de `technology_scopes.yaml`
2. Classifier chaque terme existant dans les nouvelles catégories :
   - Identifier les core_phrases
   - Extraire les technology_terms_high_precision (DDS + HLE spécifiques)
   - Isoler les technology_use (termes d'usage)
   - Séparer les route_admin_terms
   - Identifier les interval_patterns
   - Déplacer les termes génériques vers generic_terms
   - Ajouter des negative_terms
3. Enrichir avec les termes manquants issus des CSV (technology_family, technology_tag)
4. Réécrire `technology_scopes.yaml` avec la nouvelle structure
5. Créer un diagnostic détaillé avant/après

**Livrables :**
- `canonical/scopes/technology_scopes.yaml` (mis à jour)
- `docs/diagnostics/vectora_inbox_lai_technology_scopes_refactor_results.md`

---

### Phase 2 — Company scopes : pure players vs hybrid

**Objectif :** Séparer clairement les pure players LAI des entreprises hybrid/mixtes.

**Actions :**
1. Lire l'état actuel de `company_scopes.yaml`
2. Créer deux nouveaux scopes :
   - `lai_companies_pure_players` : entreprises 100% focalisées LAI
   - `lai_companies_hybrid` : big pharma/mid pharma avec activité LAI
3. Peupler `lai_companies_pure_players` avec au minimum :
   - MedinCell
   - Camurus
   - DelSiTech
   - Nanexa
   - Peptron
   - Bolder BioTechnology
   - Cristal Therapeutics
   - Durect
   - Eupraxia Pharmaceuticals
   - Foresee Pharmaceuticals
   - G2GBio
   - Hanmi Pharmaceutical
   - LIDDS
   - Taiwan Liposome
4. Peupler `lai_companies_hybrid` avec les big pharma de `lai_companies_global`
5. Documenter la relation : pure_players ⊂ global, hybrid ⊂ global
6. Conserver `lai_companies_mvp_core` et `lai_companies_global` pour compatibilité

**Livrables :**
- `canonical/scopes/company_scopes.yaml` (mis à jour)
- Documentation dans diagnostics

---

### Phase 3 — Documentation & diagnostics LAI

**Objectif :** Documenter exhaustivement les changements et leur rationale.

**Actions :**
1. Créer/compléter `docs/diagnostics/vectora_inbox_lai_technology_scopes_refactor_results.md` :
   - Tableau avant/après pour lai_keywords
   - Liste des termes supprimés (déplacés vers generic_terms)
   - Liste des termes ajoutés (technology_terms_high_precision, interval_patterns)
   - Principes métier appliqués
   - Points ambigus restants
2. Créer/compléter `docs/diagnostics/vectora_inbox_lai_mvp_matching_refactor_results.md` :
   - Section company scopes : pure_players vs hybrid
   - Usage prévu : pure players → 1 signal fort suffit ; hybrid → signaux multiples requis
3. Mettre à jour `docs/diagnostics/lai_weekly_mvp_recentrage_summary.md` si existant

**Livrables :**
- `docs/diagnostics/vectora_inbox_lai_technology_scopes_refactor_results.md`
- `docs/diagnostics/vectora_inbox_lai_mvp_matching_refactor_results.md`
- Mise à jour de synthèses existantes

---

### Phase 4 — CHANGELOG et synthèse exécutive

**Objectif :** Tracer les changements et préparer la prochaine phase (code runtime).

**Actions :**
1. Mettre à jour `CHANGELOG.md` avec une entrée datée :
   ```
   [2025-01-XX] — LAI canonical refactor (technology_scopes + company_scopes)
   
   Points clés :
   - Refonte du scope LAI (lai_keywords) avec structure core_phrases / high_precision / use / route_admin / interval / generic / negative_terms
   - Séparation des company scopes en lai_companies_pure_players et lai_companies_hybrid
   - Nettoyage des termes génériques (drug delivery system, liposomes, PEG, subcutaneous, etc.) → déplacés vers generic_terms
   - Aucune modification du code de matching à ce stade (phase "canonical only")
   ```
2. Créer/mettre à jour `docs/diagnostics/vectora_inbox_lai_mvp_matching_refactor_executive_summary.md` :
   - Résumé de la phase actuelle (canonical refactor)
   - État : canonical LAI nettoyé, moteur inchangé
   - Prochaine étape : adapter domain_matching_rules.yaml et matcher.py pour exploiter ces nouvelles structures

**Livrables :**
- `CHANGELOG.md` (mis à jour)
- `docs/diagnostics/vectora_inbox_lai_mvp_matching_refactor_executive_summary.md`

---

## 5. Contraintes et principes

### Contraintes fortes
- ✅ Aucune modification du code runtime (pas de changement dans `src/vectora_core/matching/`, `scorer.py`, etc.)
- ✅ Travail uniquement sur les fichiers canonical et docs
- ✅ Respect du format YAML existant
- ✅ Pas de casse des autres scopes non-LAI

### Principes métier
1. **Précision avant rappel** : mieux vaut manquer quelques LAI que générer des faux positifs massifs
2. **Combinaison de signaux** : les termes génériques ne doivent plus matcher seuls
3. **Alignement taxonomie** : utiliser les CSV imports comme référence métier
4. **Documentation exhaustive** : chaque décision doit être tracée et justifiée

---

## 6. Métriques de succès attendues

### Avant refactor
- Précision LAI : **0%** (trop de faux positifs)
- Termes génériques dans lai_keywords : **~30 termes problématiques**
- Séparation pure players / hybrid : **absente**

### Après refactor (attendu)
- Structure lai_keywords : **7 catégories distinctes**
- Termes génériques isolés : **~10 termes déplacés vers generic_terms**
- Termes haute précision : **~40 termes dans core_phrases + technology_terms_high_precision**
- Company scopes : **2 nouveaux scopes (pure_players, hybrid)**
- Documentation : **3+ fichiers diagnostics créés/mis à jour**

---

## 7. Prochaines étapes (hors scope de cette phase)

**Phase suivante (code runtime) :**
1. Adapter `domain_matching_rules.yaml` pour exploiter les nouvelles catégories de lai_keywords
2. Modifier `matcher.py` pour implémenter la logique de combinaison de signaux :
   - core_phrases → match immédiat
   - technology_terms_high_precision + route_admin_terms → match
   - technology_use + interval_patterns → match
   - generic_terms seuls → pas de match
3. Adapter le scoring pour différencier pure_players vs hybrid
4. Tester sur le corpus existant et mesurer la nouvelle précision LAI

---

**Fin du plan de design. Passage à l'exécution autonome des 4 phases.**
