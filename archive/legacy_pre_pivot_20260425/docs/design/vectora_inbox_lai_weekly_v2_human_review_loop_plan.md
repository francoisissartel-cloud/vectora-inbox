# Vectora Inbox LAI Weekly v2 - Plan de Boucle de Revue Humaine

**Date** : 2025-12-11  
**Objectif** : Mise en place d'une boucle de calibrage humain pour améliorer la qualité de Vectora Inbox

---

## Objectif de la Boucle de Revue

### Problème
Le moteur Vectora Inbox génère des newsletters avec un ratio signal/noise variable. Les corrections automatiques (P0/P1) améliorent la situation mais ne capturent pas toutes les nuances métier.

### Solution
Boucle de feedback humain régulière pour :
- **Valider** les décisions du moteur (inclusion/exclusion items)
- **Identifier** les patterns de bruit non détectés
- **Calibrer** les paramètres canonical/matching/scoring
- **Améliorer** la pertinence LAI de façon itérative

---

## Source de Données

### Run de Référence
**Dernier run effectif** : lai_weekly_v2 en environnement DEV
- Newsletter générée (items inclus)
- Items normalisés complets (candidats potentiels)
- Logs de matching et scoring
- Décisions d'inclusion/exclusion du moteur

### Données Techniques Utilisées
- `items_normalized_lai_weekly_v2_runX.json` (items post-Bedrock)
- `newsletter-lai-weekly-v2.md` (newsletter finale)
- Logs engine (matching domains, scores, décisions)
- Configuration canonical active (scopes, rules, profils)

---

## Structure du Document de Revue

### Table A : Items Inclus dans Newsletter
**Contenu** : Tous les items présents dans la dernière newsletter
**Objectif** : Valider la pertinence des items sélectionnés
**Colonnes techniques** : source, date, titre, score, domaines matchés, signaux LAI
**Colonnes humaines** : label LAI, garder/exclure, priorité, commentaires

### Table B : Items LAI Candidats Non Retenus  
**Contenu** : Top 20 items matchés sur tech_lai_ecosystem mais exclus de newsletter
**Objectif** : Identifier les faux négatifs (signaux LAI manqués)
**Critères sélection** : Score élevé mais sous seuil newsletter, signaux LAI partiels

### Table C : Corporate Pure Players Non Retenus (Optionnel)
**Contenu** : Items pure players (MedinCell, Nanexa, DelSiTech) potentiellement pertinents
**Objectif** : Calibrer le traitement des pure players
**Critères sélection** : Source corporate pure player, contenu non-HR/finance

---

## Processus de Revue

### Étape 1 : Génération Document (Automatique)
- **Qui** : Agent IA
- **Action** : Analyse dernier run, extraction items, création tables
- **Livrable** : `vectora_inbox_lai_weekly_v2_human_review_sheet.md`
- **Durée** : 10 minutes

### Étape 2 : Annotation Humaine (Manuel)
- **Qui** : Expert métier LAI
- **Action** : Remplir colonnes humaines pour chaque item
  - `human_label` : LAI-strong, LAI-weak, non-LAI, noise-HR, noise-finance
  - `human_keep_in_newsletter` : yes/no
  - `human_priority` : high/medium/low  
  - `human_comments` : justification, contexte métier
- **Durée** : 30-45 minutes

### Étape 3 : Analyse & Ajustements (Automatique)
- **Qui** : Agent IA
- **Action** : Analyse annotations, identification patterns, propositions ajustements
- **Livrable** : Plan de corrections canonical/matching/scoring
- **Durée** : 15 minutes

---

## Utilisation des Annotations

### Patterns d'Amélioration Détectés
- **Faux positifs** : Items inclus mais annotés "non-LAI" → Renforcer exclusions
- **Faux négatifs** : Items exclus mais annotés "LAI-strong" → Enrichir scopes/ajuster seuils
- **Bruit récurrent** : Patterns HR/finance non filtrés → Nouvelles exclusions
- **Signaux manqués** : Technologies/trademarks non détectés → Enrichir scopes

### Ajustements Proposés
- **exclusion_scopes.yaml** : Nouveaux termes de bruit identifiés
- **technology_scopes.yaml** : Termes LAI manqués dans annotations
- **scoring_rules.yaml** : Ajustement poids selon priorités humaines
- **matching rules** : Seuils et logique selon feedback

---

## Fréquence et Évolution

### Phase Initiale (MVP)
- **Fréquence** : Après chaque run significatif (corrections majeures)
- **Scope** : 25-30 items total (newsletter + candidats)
- **Focus** : Calibrage de base signal/noise

### Phase Mature
- **Fréquence** : Hebdomadaire ou bi-hebdomadaire
- **Scope** : 15-20 items (focus sur cas limites)
- **Focus** : Optimisation fine, nouveaux patterns

### Automatisation Progressive
- **Learning** : Patterns humains → règles automatiques
- **Validation** : Prédiction annotations vs réalité
- **Réduction** : Moins d'items à annoter au fil du temps

---

## Métriques de Succès

### Qualité Newsletter
- **Accord humain-moteur** : >80% sur décisions inclusion/exclusion
- **Signaux LAI authentiques** : >70% items newsletter
- **Bruit résiduel** : <20% items newsletter

### Efficacité Processus
- **Temps annotation** : <30 minutes par session
- **Implémentation ajustements** : <2 heures post-annotation
- **Stabilité** : Moins d'ajustements nécessaires au fil du temps

---

## Conclusion

**Boucle de revue humaine** = Mécanisme de calibrage continu pour transformer Vectora Inbox d'un outil technique en assistant de veille LAI fiable.

**Investissement** : 1h/semaine expert métier → Newsletter LAI opérationnelle et auto-améliorante.

**ROI** : Veille LAI professionnelle vs outil inutilisable sans calibrage humain.