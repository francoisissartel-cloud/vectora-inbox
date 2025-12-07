# Exemples de calcul de score

## Introduction

Ce document fournit des **exemples concrets** de calcul de score pour des items fictifs, afin de rendre la logique de scoring intuitive et compréhensible.

Le scoring utilise les règles définies dans `scoring_rules.yaml`. L'objectif est de **prioriser les items les plus pertinents** pour qu'ils apparaissent en haut de la newsletter.

**Note :** Les exemples ci-dessous sont **qualitatifs** et visent à illustrer la logique. Les valeurs numériques exactes peuvent varier selon l'implémentation.

---

## Exemple 1 : Item à score élevé

### Contexte de l'item

- **Titre** : "Camurus Announces Positive Phase 3 Results for Brixadi in Opioid Use Disorder"
- **Type d'événement** : `clinical_update`
- **Date** : 2 jours (récent)
- **Domaine** : `tech_lai_ecosystem` (priorité `high`)
- **Entreprise détectée** : Camurus (compétiteur clé pour le client)
- **Molécule détectée** : Brixadi, buprenorphine (molécule clé)
- **Type de source** : `press_corporate` (communiqué officiel)

### Calcul du score (pas-à-pas)

1. **Poids du type d'événement** : `clinical_update` → **5 points**
   - Les résultats cliniques sont très importants pour la veille

2. **Priorité du domaine** : `high` → **×3 multiplicateur**
   - Le domaine LAI est prioritaire pour ce client

3. **Bonus compétiteur clé** : Camurus est un compétiteur clé → **+2 points**
   - L'item mentionne une entreprise stratégique

4. **Bonus molécule clé** : Brixadi est une molécule clé → **+1.5 points**
   - L'item mentionne un produit important

5. **Récence** : 2 jours → **facteur de récence élevé (~0.9)**
   - L'item est très récent, donc peu de décroissance

6. **Type de source** : `press_corporate` → **×2 multiplicateur**
   - Source officielle, donc fiable

### Score final estimé

```
Score de base = event_type_weight × domain_priority
              = 5 × 3 = 15

Bonus = competitor_bonus + molecule_bonus
      = 2 + 1.5 = 3.5

Facteur récence = 0.9 (peu de décroissance)

Facteur source = 2 (corporate)

Score final ≈ (15 + 3.5) × 0.9 × 2 ≈ 33 points
```

**Résultat :** Cet item aura un **score très élevé** et apparaîtra en haut de la newsletter.

---

## Exemple 2 : Item à score moyen

### Contexte de l'item

- **Titre** : "Alkermes and Partner Announce Strategic Collaboration for Mental Health"
- **Type d'événement** : `partnership`
- **Date** : 1 jour (très récent)
- **Domaine** : `tech_lai_ecosystem` (priorité `high`)
- **Entreprise détectée** : Alkermes (compétiteur clé)
- **Molécule détectée** : aucune
- **Type de source** : `press_sector` (presse spécialisée)

### Calcul du score (pas-à-pas)

1. **Poids du type d'événement** : `partnership` → **6 points**
   - Les partenariats sont très importants (score élevé)

2. **Priorité du domaine** : `high` → **×3 multiplicateur**

3. **Bonus compétiteur clé** : Alkermes est un compétiteur clé → **+2 points**

4. **Bonus molécule clé** : aucune molécule mentionnée → **0 point**

5. **Récence** : 1 jour → **facteur de récence maximal (~1.0)**

6. **Type de source** : `press_sector` → **×1.5 multiplicateur**
   - Presse spécialisée, fiable mais moins que corporate

### Score final estimé

```
Score de base = 6 × 3 = 18

Bonus = 2 + 0 = 2

Facteur récence = 1.0 (très récent)

Facteur source = 1.5 (sector)

Score final ≈ (18 + 2) × 1.0 × 1.5 ≈ 30 points
```

**Résultat :** Cet item aura un **score élevé** et apparaîtra dans le top de la newsletter, mais légèrement en dessous de l'exemple 1.

---

## Exemple 3 : Item à score faible

### Contexte de l'item

- **Titre** : "Generic Pharma Reports Q4 Financial Results"
- **Type d'événement** : `financial_results`
- **Date** : 10 jours (ancien)
- **Domaine** : `tech_lai_ecosystem` (priorité `low`)
- **Entreprise détectée** : Generic Pharma (pas un compétiteur clé)
- **Molécule détectée** : aucune
- **Type de source** : `press_generic` (presse généraliste)

### Calcul du score (pas-à-pas)

1. **Poids du type d'événement** : `financial_results` → **3 points**
   - Les résultats financiers sont moins prioritaires que le clinique/réglementaire

2. **Priorité du domaine** : `low` → **×1 multiplicateur**
   - Le domaine est périphérique pour ce client

3. **Bonus compétiteur clé** : Generic Pharma n'est pas un compétiteur clé → **0 point**

4. **Bonus molécule clé** : aucune molécule mentionnée → **0 point**

5. **Récence** : 10 jours → **facteur de récence faible (~0.4)**
   - Demi-vie de 7 jours → décroissance significative

6. **Type de source** : `press_generic` → **×1 multiplicateur**
   - Source généraliste, moins fiable

### Score final estimé

```
Score de base = 3 × 1 = 3

Bonus = 0 + 0 = 0

Facteur récence = 0.4 (ancien)

Facteur source = 1 (generic)

Score final ≈ (3 + 0) × 0.4 × 1 ≈ 1.2 points
```

**Résultat :** Cet item aura un **score très faible** et sera probablement exclu de la newsletter (en dessous du seuil `min_score: 10`).

---

## Exemple 4 : Item à score moyen-élevé (réglementaire)

### Contexte de l'item

- **Titre** : "FDA Approves New Long-Acting Injectable for Schizophrenia"
- **Type d'événement** : `regulatory`
- **Date** : 3 jours (récent)
- **Domaine** : `regulatory_lai` (priorité `high`)
- **Entreprise détectée** : aucune (FDA, pas une entreprise)
- **Molécule détectée** : aucune (nom de molécule non mentionné dans le titre)
- **Type de source** : `press_sector` (presse spécialisée)

### Calcul du score (pas-à-pas)

1. **Poids du type d'événement** : `regulatory` → **5 points**
   - Les approbations réglementaires sont très importantes

2. **Priorité du domaine** : `high` → **×3 multiplicateur**

3. **Bonus compétiteur clé** : aucune entreprise mentionnée → **0 point**

4. **Bonus molécule clé** : aucune molécule mentionnée → **0 point**

5. **Récence** : 3 jours → **facteur de récence élevé (~0.8)**

6. **Type de source** : `press_sector` → **×1.5 multiplicateur**

### Score final estimé

```
Score de base = 5 × 3 = 15

Bonus = 0 + 0 = 0

Facteur récence = 0.8

Facteur source = 1.5

Score final ≈ (15 + 0) × 0.8 × 1.5 ≈ 18 points
```

**Résultat :** Cet item aura un **score moyen-élevé** et apparaîtra dans la newsletter, même sans mention d'entreprise ou de molécule clé (le type d'événement et la priorité du domaine suffisent).

---

## Synthèse des exemples

| Exemple | Type d'événement | Récence | Domaine | Compétiteur | Molécule | Source | Score estimé | Inclusion ? |
|---------|------------------|---------|---------|-------------|----------|--------|--------------|-------------|
| 1       | clinical_update  | 2j      | high    | Oui         | Oui      | corporate | ~33 | ✅ Oui (top) |
| 2       | partnership      | 1j      | high    | Oui         | Non      | sector    | ~30 | ✅ Oui (top) |
| 3       | financial_results| 10j     | low     | Non         | Non      | generic   | ~1  | ❌ Non (< seuil) |
| 4       | regulatory       | 3j      | high    | Non         | Non      | sector    | ~18 | ✅ Oui |

---

## Principes clés du scoring

1. **Le type d'événement est le facteur principal** : `clinical_update`, `regulatory`, `partnership` ont des poids élevés.

2. **La récence compte beaucoup** : un item ancien (>7 jours) voit son score divisé par 2 ou plus.

3. **Les compétiteurs et molécules clés boostent le score** : mentionner une entreprise ou un produit stratégique augmente la pertinence.

4. **La priorité du domaine module le score** : un domaine `high` triple le score de base.

5. **Le type de source affecte la fiabilité** : une source corporate ou sector est plus valorisée qu'une source générique.

6. **Le seuil de sélection filtre les items faibles** : seuls les items avec un score ≥ 10 sont inclus dans la newsletter.

---

## Comment ajuster le scoring ?

Si vous trouvez que certains items sont trop/pas assez valorisés, vous pouvez ajuster les poids dans `scoring_rules.yaml` :

- **Augmenter le poids d'un type d'événement** : si vous voulez plus de `partnership`, augmentez `partnership: 6` → `partnership: 7`
- **Modifier la demi-vie de récence** : si vous voulez valoriser davantage les items récents, réduisez `recency_decay_half_life_days: 7` → `recency_decay_half_life_days: 5`
- **Ajuster les bonus** : si les compétiteurs clés sont très importants, augmentez `competitor_company_bonus: 2` → `competitor_company_bonus: 3`

---

**Ce document est destiné aux développeurs et administrateurs de Vectora Inbox pour comprendre intuitivement la logique de scoring.**
