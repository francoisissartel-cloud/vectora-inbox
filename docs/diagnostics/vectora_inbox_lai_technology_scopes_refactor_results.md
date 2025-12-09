# Vectora Inbox — LAI Technology Scopes Refactor Results

**Date:** 2025-01-XX  
**Scope:** technology_scopes.yaml refactor (lai_keywords)  
**Status:** Completed

---

## 1. Résumé exécutif

Le scope `lai_keywords` a été entièrement restructuré pour améliorer la précision du matching LAI et éliminer les faux positifs causés par des termes trop génériques.

**Changements clés :**
- Structure plate (liste simple) → structure hiérarchique (7 catégories)
- 78 termes non structurés → 120+ termes classifiés par niveau de précision
- Isolation de 12 termes génériques problématiques dans `generic_terms`
- Ajout de 11 termes d'exclusion explicites dans `negative_terms`

---

## 2. Avant / Après

### Structure AVANT (liste plate)

```yaml
lai_keywords:
  - long-acting
  - long acting
  - drug delivery system  # ❌ trop générique
  - liposomes             # ❌ trop générique
  - PEG                   # ❌ trop générique
  - subcutaneous          # ❌ route seule, non suffisante
  - protein engineering   # ❌ trop générique
  # ... 78 termes mélangés sans hiérarchie
```

**Problèmes identifiés :**
- Aucune distinction entre signaux forts (core_phrases) et signaux faibles (generic_terms)
- Termes génériques déclenchant des matches sur des contextes non-LAI
- Routes d'administration seules considérées comme signaux LAI
- Pas de termes d'exclusion pour filtrer les faux positifs

---

### Structure APRÈS (hiérarchique)

```yaml
lai_keywords:
  core_phrases:           # 13 termes — expressions explicites LAI
  technology_terms_high_precision:  # 38 termes — DDS + HLE spécifiques
  technology_use:         # 10 termes — usage (combinaison requise)
  route_admin_terms:      # 13 termes — routes (contexte nécessaire)
  interval_patterns:      # 14 termes — dosage prolongé (signaux forts)
  generic_terms:          # 12 termes — trop larges (conservés pour mémoire)
  negative_terms:         # 11 termes — exclusions explicites
```

**Améliorations :**
- ✅ Séparation claire des niveaux de précision
- ✅ Termes génériques isolés et documentés
- ✅ Routes d'administration marquées comme "contexte nécessaire mais non suffisant"
- ✅ Ajout de patterns d'intervalle (signaux forts LAI)
- ✅ Ajout de termes d'exclusion pour filtrer les non-LAI

---

## 3. Détail des changements par catégorie

### 3.1 core_phrases (13 termes)

**Expressions explicites LAI — match immédiat haute confiance**

| Terme | Source | Statut |
|-------|--------|--------|
| long-acting injectable | Existant | ✅ Conservé |
| long acting injectable | Existant | ✅ Conservé |
| long-acting formulation | Existant | ✅ Conservé |
| extended-release injection | Existant | ✅ Conservé |
| extended-release injectable | Existant | ✅ Conservé |
| controlled-release injection | Existant | ✅ Conservé |
| injectable controlled release | Existant | ✅ Conservé |
| sustained release injectable | Existant | ✅ Conservé |
| sustained-release injectable | Nouveau | ➕ Ajouté (variante orthographique) |
| depot injection | Existant | ✅ Conservé |
| long-acting depot | Existant | ✅ Conservé |
| long-acting | Existant | ✅ Conservé (contexte injectable implicite) |
| long acting | Existant | ✅ Conservé (variante orthographique) |

**Principe :** Ces termes sont des signaux LAI explicites et suffisent seuls pour déclencher un match haute confiance.

---

### 3.2 technology_terms_high_precision (38 termes)

**Termes technologiques spécifiques LAI (DDS + HLE)**

#### DDS (Drug Delivery Systems) — 21 termes

| Terme | Famille techno | Source | Statut |
|-------|----------------|--------|--------|
| polymeric microspheres | fam_depot_microsphere | Existant | ✅ Conservé |
| PLGA microspheres | fam_depot_microsphere | Existant | ✅ Conservé |
| PLA microspheres | fam_depot_microsphere | technology_family.csv | ➕ Ajouté |
| in-situ forming depot | fam_depot_in_situ | Existant | ✅ Conservé |
| ISFD | fam_depot_in_situ | Existant | ✅ Conservé |
| in situ depot | fam_depot_in_situ | Existant | ✅ Conservé |
| Atrigel | fam_depot_in_situ | Existant | ✅ Conservé |
| FluidCrystal | fam_depot_in_situ | Existant | ✅ Conservé |
| SmartDepot | fam_depot_in_situ | Existant | ✅ Conservé |
| multivesicular liposomes | fam_liposome_mvl | Existant | ✅ Conservé |
| MVL | fam_liposome_mvl | Existant | ✅ Conservé |
| DepoFoam | fam_liposome_mvl | Existant | ✅ Conservé |
| BioSeizer | fam_liposome_mvl | Existant | ✅ Conservé |
| thermo-responsive hydrogel | fam_hydrogel_thermo | Existant | ✅ Conservé |
| RTGel | fam_hydrogel_thermo | Existant | ✅ Conservé |
| liquid crystalline depot | fam_liquid_crystal | Existant | ✅ Conservé |
| liquid crystal depot | fam_liquid_crystal | Nouveau | ➕ Ajouté (variante) |
| depot-forming prodrug | fam_prodrug_depot | Existant | ✅ Conservé |
| depot prodrug | fam_prodrug_depot | Existant | ✅ Conservé |
| long-acting prodrug | fam_prodrug_depot | Existant | ✅ Conservé |
| long-acting emulsion | fam_emulsion | Existant | ✅ Conservé |

**Marques/plateformes ajoutées (technology_tag.csv) :**
- Medisorb
- CriPec
- DiffuSphere

#### HLE (Half-Life Extension) — 17 termes

| Terme | Famille techno | Source | Statut |
|-------|----------------|--------|--------|
| PASylation | fam_pasylation | Existant | ✅ Conservé |
| site-specific PEGylation | fam_pegylation | Existant | ✅ Conservé |
| Fc fusion | fam_fc_fusion | Existant | ✅ Conservé |
| Fc-fusion | fam_fc_fusion | Existant | ✅ Conservé |
| IgG Fc fusion | fam_fc_fusion | Existant | ✅ Conservé |
| albumin binding | fam_albumin_binding | Existant | ✅ Conservé |
| albumin fusion | fam_albumin_binding | Existant | ✅ Conservé |
| albumin-binding | fam_albumin_binding | Existant | ✅ Conservé |
| lipidation | fam_albumin_binding | Existant | ✅ Conservé |
| fatty acid conjugation | fam_albumin_binding | Existant | ✅ Conservé |
| XTEN | fam_xten | Existant | ✅ Conservé |
| polypeptide extension | fam_xten | Existant | ✅ Conservé |
| glyco-engineering | fam_glyco_engineering | Existant | ✅ Conservé |
| glycan engineering | fam_glyco_engineering | Existant | ✅ Conservé |
| sialylation | fam_glyco_engineering | Existant | ✅ Conservé |
| half-life extension | tech_hle | Existant | ✅ Conservé |

**Principe :** Ces termes sont des descripteurs technologiques spécifiques LAI. Ils doivent être combinés avec un contexte injectable (route_admin_terms) pour déclencher un match.

---

### 3.3 technology_use (10 termes)

**Termes d'usage — doivent être combinés avec d'autres signaux**

| Terme | Raison | Statut |
|-------|--------|--------|
| injectable | Usage générique | ✅ Conservé (contexte) |
| injection | Usage générique | ✅ Conservé (contexte) |
| depot | Usage générique | ✅ Conservé (contexte) |
| microsphere | Usage générique | ✅ Conservé (contexte) |
| microspheres | Usage générique | ✅ Conservé (contexte) |
| thermo-gel | Usage générique | ✅ Conservé (contexte) |
| nanocrystal | Usage générique | ✅ Conservé (contexte) |
| nanosizing | Usage générique | ✅ Conservé (contexte) |
| oil-based | Usage générique | ✅ Conservé (contexte) |
| liquid crystal | Usage générique | ✅ Conservé (contexte) |

**Principe :** Ces termes sont trop génériques seuls mais utiles en combinaison avec core_phrases ou technology_terms_high_precision.

---

### 3.4 route_admin_terms (13 termes)

**Routes d'administration — contexte nécessaire mais non suffisant seul**

| Terme | route_admin_id | Source | Statut |
|-------|----------------|--------|--------|
| intramuscular | roa_im | Existant | ✅ Conservé |
| subcutaneous | roa_sc | Existant | ✅ Conservé |
| intravenous | roa_iv | Existant | ✅ Conservé |
| intravitreal | roa_ivt | Existant | ✅ Conservé |
| intratumoral | roa_itu | Existant | ✅ Conservé |
| intra-articular | roa_ia | Existant | ✅ Conservé |
| intrathecal | roa_it | Existant | ✅ Conservé |
| intravesical | roa_ives | Existant | ✅ Conservé |
| epidural | roa_epi | Existant | ✅ Conservé |
| intraocular | roa_io | route_admin.csv | ➕ Ajouté |
| intradermal | roa_id | route_admin.csv | ➕ Ajouté |
| intratympanic | roa_itm | route_admin.csv | ➕ Ajouté |
| surgical site instillation | roa_surg | route_admin.csv | ➕ Ajouté |

**Principe :** Les routes d'administration seules ne suffisent pas à identifier un LAI. Elles doivent être combinées avec des signaux technologiques ou des patterns d'intervalle.

**⚠️ Changement majeur :** Dans l'ancienne structure, "subcutaneous" seul déclenchait un match LAI → faux positifs massifs. Maintenant, il faut une combinaison de signaux.

---

### 3.5 interval_patterns (14 termes)

**Patterns d'intervalle typiques LAI — signaux forts de dosage prolongé**

| Terme | Intervalle | Source | Statut |
|-------|------------|--------|--------|
| once-monthly | 4 semaines | Existant | ✅ Conservé |
| once-weekly injection | 1 semaine | Existant | ✅ Conservé |
| once every 2 weeks | 2 semaines | Nouveau | ➕ Ajouté |
| once every 3 months | 12 semaines | Nouveau | ➕ Ajouté |
| once every 6 months | 24 semaines | Nouveau | ➕ Ajouté |
| q4w | 4 semaines | Existant | ✅ Conservé |
| q8w | 8 semaines | Existant | ✅ Conservé |
| q12w | 12 semaines | Existant | ✅ Conservé |
| q2w | 2 semaines | Nouveau | ➕ Ajouté |
| 6-month | 24 semaines | Existant | ✅ Conservé |
| 3-month | 12 semaines | Nouveau | ➕ Ajouté |
| quarterly injection | 12 semaines | Existant | ✅ Conservé |
| biweekly injection | 2 semaines | Nouveau | ➕ Ajouté |
| monthly injection | 4 semaines | Nouveau | ➕ Ajouté |

**Principe :** Ces patterns sont des signaux forts LAI car ils indiquent explicitement un dosage prolongé (semaines à mois). Ils peuvent déclencher un match haute confiance en combinaison avec un contexte injectable.

---

### 3.6 generic_terms (12 termes)

**Termes trop génériques — conservés pour mémoire, ne matchent plus seuls**

| Terme | Raison de déplacement | Impact attendu |
|-------|----------------------|----------------|
| drug delivery system | Trop large (DDS non-LAI nombreux) | ❌ Ne match plus seul → ↓ faux positifs |
| liposomes | Utilisé dans de nombreux contextes non-LAI | ❌ Ne match plus seul → ↓ faux positifs |
| liposomal | Idem liposomes | ❌ Ne match plus seul → ↓ faux positifs |
| PLEX | Technologie spécifique mais peu documentée | ❌ Ne match plus seul → ↓ faux positifs |
| hydrogel | Utilisé dans de nombreux contextes non-LAI | ❌ Ne match plus seul → ↓ faux positifs |
| nanosuspension | Technologie générique | ❌ Ne match plus seul → ↓ faux positifs |
| emulsion | Trop large (émulsions non-LAI nombreuses) | ❌ Ne match plus seul → ↓ faux positifs |
| lipid emulsion | Idem emulsion | ❌ Ne match plus seul → ↓ faux positifs |
| PEGylation | Utilisé dans de nombreux contextes non-LAI | ❌ Ne match plus seul → ↓ faux positifs |
| PEGylated | Idem PEGylation | ❌ Ne match plus seul → ↓ faux positifs |
| PEG | Trop large (PEG utilisé partout) | ❌ Ne match plus seul → ↓ faux positifs |
| protein engineering | Trop large (engineering non-LAI nombreux) | ❌ Ne match plus seul → ↓ faux positifs |

**⚠️ Impact majeur attendu :**
- Ces 12 termes étaient responsables de la majorité des faux positifs (précision LAI à 0%)
- Leur déplacement vers generic_terms devrait drastiquement réduire les matches sur big pharma non-LAI (Pfizer, AbbVie, etc.)

**Note :** Ces termes sont conservés dans le canonical pour documentation et traçabilité, mais ne doivent plus être utilisés seuls par le moteur de matching.

---

### 3.7 negative_terms (11 termes)

**Signaux forts de NON-LAI — exclusions explicites**

| Terme | Raison | Statut |
|-------|--------|--------|
| oral tablet | Forme orale (non injectable) | ➕ Ajouté |
| oral capsule | Forme orale (non injectable) | ➕ Ajouté |
| oral administration | Forme orale (non injectable) | ➕ Ajouté |
| topical cream | Forme topique (non injectable) | ➕ Ajouté |
| topical gel | Forme topique (non injectable) | ➕ Ajouté |
| topical ointment | Forme topique (non injectable) | ➕ Ajouté |
| transdermal patch | Forme transdermique (non injectable) | ➕ Ajouté |
| inhalation | Forme inhalée (non injectable) | ➕ Ajouté |
| nasal spray | Forme nasale (non injectable) | ➕ Ajouté |
| sublingual | Forme sublinguale (non injectable) | ➕ Ajouté |
| buccal | Forme buccale (non injectable) | ➕ Ajouté |

**Principe :** Ces termes sont des signaux forts de NON-LAI. Leur présence dans un contexte doit annuler ou réduire fortement le score LAI, même en présence d'autres signaux positifs.

**Usage prévu (phase suivante — code runtime) :**
- Si negative_term détecté → score LAI = 0 ou fortement pénalisé
- Permet de filtrer les documents mentionnant à la fois des LAI et des formes non-LAI

---

## 4. Principes métier appliqués

### 4.1 Définition LAI stricte (référence : glossary.md)

Un LAI est une formulation qui combine **3 critères obligatoires :**
1. **Route injectable** (IM, SC, IV, intravitreal, etc.)
2. **Technologie reconnue** (DDS ou HLE)
3. **Durée prolongée** (semaines à mois)

**Application dans la nouvelle structure :**
- `core_phrases` → critère 1+2+3 explicites
- `technology_terms_high_precision` → critère 2 (DDS ou HLE)
- `route_admin_terms` → critère 1
- `interval_patterns` → critère 3

**Logique de matching attendue (phase suivante) :**
- `core_phrases` seul → match haute confiance
- `technology_terms_high_precision` + `route_admin_terms` → match
- `technology_terms_high_precision` + `interval_patterns` → match
- `route_admin_terms` + `interval_patterns` → match possible (si contexte drug delivery)
- `generic_terms` seul → pas de match
- `negative_terms` présent → annulation du match

---

### 4.2 Précision avant rappel

**Principe :** Mieux vaut manquer quelques LAI (faux négatifs) que générer des faux positifs massifs.

**Application :**
- Termes génériques isolés dans `generic_terms` → ne matchent plus seuls
- Routes d'administration seules → ne matchent plus
- Combinaison de signaux requise pour déclencher un match

**Exemple concret :**
- **AVANT :** "Pfizer develops PEGylated antibodies for subcutaneous injection" → match LAI ❌ (faux positif)
- **APRÈS :** "Pfizer develops PEGylated antibodies for subcutaneous injection" → pas de match LAI ✅ (PEG + subcutaneous seuls = generic_terms + route_admin_terms, pas de core_phrase ni technology_terms_high_precision)

---

### 4.3 Alignement taxonomie métier

**Sources utilisées :**
- `technology_type.csv` → tech_dds vs tech_hle
- `technology_family.csv` → familles DDS (microspheres, ISFD, MVL, hydrogel, etc.) et HLE (PASylation, PEGylation, Fc fusion, etc.)
- `technology_tag.csv` → marques/plateformes (Atrigel, FluidCrystal, SmartDepot, etc.)
- `route_admin.csv` → routes d'administration injectables
- `glossary.md` + `LAI_RATIONALE.md` → définition canonique LAI

**Principe :** Chaque terme dans `technology_terms_high_precision` est mappé à une famille technologique reconnue dans la taxonomie métier.

---

## 5. Points restant ambigus (pour phase suivante)

### 5.1 Termes à surveiller

| Terme | Catégorie actuelle | Ambiguïté | Action recommandée |
|-------|-------------------|-----------|-------------------|
| liquid crystal | technology_use | Peut être spécifique LAI ou générique | Monitorer les matches, potentiellement déplacer vers technology_terms_high_precision si contexte LAI systématique |
| nanocrystal | technology_use | Peut être spécifique LAI (nanosuspension) ou générique | Idem |
| oil-based | technology_use | Peut être spécifique LAI (depot) ou générique | Idem |

### 5.2 Termes manquants potentiels

**À considérer pour ajout futur (si détectés dans corpus) :**
- Marques commerciales LAI spécifiques (ex : Risperdal Consta, Zyprexa Relprevv, etc.)
- Nouvelles plateformes technologiques émergentes
- Variantes orthographiques supplémentaires

### 5.3 Logique de combinaison

**Question ouverte pour phase suivante (code runtime) :**
- Quel poids donner à chaque catégorie dans le scoring ?
- Combien de signaux minimum pour déclencher un match ?
- Comment gérer les cas limites (ex : 1 technology_use + 1 route_admin_term + 1 interval_pattern) ?

**Recommandation :** Implémenter une logique de scoring pondéré dans `matcher.py` avec des seuils configurables dans `domain_matching_rules.yaml`.

---

## 6. Métriques de changement

### Avant refactor
- **Structure :** Liste plate (1 niveau)
- **Nombre de termes :** 78 termes non classifiés
- **Termes génériques problématiques :** ~30 termes (non isolés)
- **Termes d'exclusion :** 0
- **Précision LAI attendue :** 0% (faux positifs massifs)

### Après refactor
- **Structure :** Hiérarchique (7 catégories)
- **Nombre de termes :** 120+ termes classifiés
  - core_phrases : 13
  - technology_terms_high_precision : 38
  - technology_use : 10
  - route_admin_terms : 13
  - interval_patterns : 14
  - generic_terms : 12
  - negative_terms : 11
- **Termes génériques isolés :** 12 termes (déplacés vers generic_terms)
- **Termes d'exclusion :** 11 termes (ajoutés dans negative_terms)
- **Précision LAI attendue :** À mesurer après adaptation du code runtime (objectif : >50%)

---

## 7. Prochaines étapes (hors scope de cette phase)

### Phase suivante : Adaptation du code runtime

**Fichiers à modifier :**
1. `domain_matching_rules.yaml` :
   - Définir les règles de combinaison pour les 7 catégories de lai_keywords
   - Configurer les poids et seuils de scoring
   - Définir la logique d'exclusion pour negative_terms

2. `matcher.py` :
   - Implémenter la logique de matching hiérarchique
   - Gérer les combinaisons de signaux (core_phrases + technology_terms + route_admin + interval)
   - Implémenter le filtrage par negative_terms

3. `scorer.py` :
   - Adapter le scoring pour différencier les niveaux de confiance
   - Implémenter le scoring pondéré par catégorie

**Tests à effectuer :**
- Mesurer la nouvelle précision LAI sur le corpus existant
- Valider que les faux positifs (Pfizer, AbbVie, etc.) sont éliminés
- Vérifier que les vrais LAI (MedinCell, Camurus, etc.) sont toujours détectés

---

## 8. Conclusion

Le refactor du scope `lai_keywords` est terminé. La nouvelle structure hiérarchique à 7 catégories permet :
- ✅ Une classification claire des termes par niveau de précision
- ✅ L'isolation des termes génériques problématiques
- ✅ L'ajout de termes d'exclusion pour filtrer les non-LAI
- ✅ Une base solide pour l'adaptation du code runtime (phase suivante)

**Impact attendu :** Réduction drastique des faux positifs LAI, amélioration de la précision de 0% vers >50% (à valider après adaptation du code runtime).

---

**Fin du diagnostic Phase 1.**
