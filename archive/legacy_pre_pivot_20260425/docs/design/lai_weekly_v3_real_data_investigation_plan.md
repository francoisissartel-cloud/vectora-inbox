# Plan d'Enquête : lai_weekly_v3 Workflow avec Données Réelles

**Date :** 18 décembre 2025  
**Objectif :** Comprendre précisément le comportement du workflow Vectora Inbox V2 pour lai_weekly_v3 sur données réelles  
**Mode :** 100% lecture seule - AUCUNE modification autorisée  

---

## 1. Cadrage & Périmètre

### 1.1 Comportement Métier Attendu

**Lambda ingest_v2 :**
- Doit ingérer les sources définies dans client_config lai_weekly_v3
- Uniquement pour les clients avec `active: true`
- Génère des fichiers dans `s3://vectora-inbox-data-dev/ingested/lai_weekly_v3/YYYY/MM/DD/items.json`

**Lambda normalize_score_v2 :**
- Trouve les clients actifs via client_config
- Localise le dernier run ingestion pour lai_weekly_v3
- Normalise + matche + score UNIQUEMENT ce dernier run
- Utilise les seuils configurés dans `matching_config` (pas hardcodés 0.4)

### 1.2 Configuration S3 Attendue
- **Bucket data :** `vectora-inbox-data-dev`
- **Bucket config :** `vectora-inbox-config-dev`
- **Client config :** `clients/lai_weekly_v3.yaml`
- **Pattern ingestion :** `ingested/lai_weekly_v3/YYYY/MM/DD/items.json`
- **Pattern curated :** `clients/lai_weekly_v3/normalized/YYYYMMDD_HHMMSS_normalized_items.json`

### 1.3 Questions Métier à Résoudre
1. **Détection clients actifs :** normalize_score_v2 détecte-t-il bien `active: true` ?
2. **Source des données :** Utilise-t-il le dernier run ingestion réel ou des données synthétiques ?
3. **Seuils de matching :** Les seuils config-driven sont-ils appliqués ou reste-t-il du hardcodé 0.4 ?

---

## 2. Analyse Statique du Code (src_v2)

### 2.1 Fonction de Sélection des Clients
- **Fichier cible :** `src_v2/lambda_normalize_score_v2/handler.py`
- **À identifier :**
  - Comment l'event est parsé (client_id explicite vs auto-scan)
  - Lecture du client_config depuis S3
  - Filtrage sur `active: true`

### 2.2 Localisation des Fichiers d'Entrée
- **À analyser :**
  - Pattern de clé S3 pour trouver le "dernier run"
  - Logique de tri par timestamp/date
  - Gestion des cas où aucun fichier n'existe

### 2.3 Logique de Matching
- **À chercher :**
  - Fonctions qui lisent `matching_config` dans client_config
  - Toute occurrence de seuils hardcodés (0.4, 0.3, etc.)
  - Comparaison avec les seuils configurés dans lai_weekly_v3.yaml

### 2.4 Implications Pratiques
- **À documenter :**
  - Ce que le code est censé faire étape par étape
  - Points de défaillance potentiels
  - Écarts entre intention et implémentation

---

## 3. Inspection S3 - Données RÉELLES

### 3.1 Fichiers Ingestion lai_weekly_v3
- **Commande :** Lister `s3://vectora-inbox-data-dev/ingested/lai_weekly_v3/`
- **À vérifier :**
  - Derniers fichiers produits par ingest_v2 (chemins exacts, timestamps)
  - Nombre d'items par fichier
  - Contenu des items (titres, sources, entreprises)

### 3.2 Validation du Contenu Réel
- **À confirmer :**
  - Présence de MedinCell, Nanexa, DelSiTech (vs Novartis, Roche)
  - Sources réelles (press_corporate__medincell, etc.)
  - Timestamps récents (pas de données anciennes/test)

### 3.3 Fichiers de Sortie Curated
- **À lister :** `s3://vectora-inbox-data-dev/clients/lai_weekly_v3/normalized/`
- **À analyser :**
  - Correspondance avec les fichiers d'entrée
  - Nombre d'items traités vs ingérés
  - Métadonnées de processing

---

## 4. Observation Comportement Réel normalize_score_v2

### 4.1 Invocation Lambda
- **Script :** `scripts/invoke_normalize_score_v2_lambda.py`
- **Payload :** `{"client_id": "lai_weekly_v3"}`
- **Lambda :** `vectora-inbox-normalize-score-v2-dev`

### 4.2 Monitoring en Temps Réel
- **À observer :**
  - Objets S3 lus comme input (chemins réels dans logs)
  - Nombre d'items normalisés/matchés/scorés
  - Objets S3 écrits comme output (chemins exacts)
  - Durée d'exécution et erreurs éventuelles

### 4.3 Logs CloudWatch
- **À analyser :**
  - Logs de la Lambda pendant l'exécution
  - Messages de debug sur la sélection des fichiers
  - Seuils appliqués pour le matching
  - Erreurs ou warnings

---

## 5. Analyse des Items Traités

### 5.1 Inventaire Complet
- **Pour chaque item traité :**
  - Titre, source, client_id, watch_domain
  - Provenance : fichier ingestion réel vs dataset synthétique
  - Scores de matching par domaine
  - Décision finale (accepté/rejeté)

### 5.2 Détection de Données Synthétiques
- **Si items synthétiques détectés :**
  - Fichier source exact (chemin repo/S3)
  - Moment du workflow où il est choisi
  - Raison du choix (fallback, configuration, bug)

### 5.3 Validation de la Cohérence
- **À vérifier :**
  - Tous les items viennent du même run ingestion
  - Pas de mélange données réelles/synthétiques
  - Correspondance avec le client_config lai_weekly_v3

---

## 6. Investigation Seuils (hardcodé 0.4 vs config 0.2)

### 6.1 Analyse du Layer vectora-core
- **À examiner :**
  - Code embarqué dans le layer utilisé par normalize_score_v2
  - Recherche de toute valeur 0.4 utilisée comme seuil
  - Comparaison avec les seuils dans lai_weekly_v3.yaml

### 6.2 Validation via Logs CloudWatch
- **À chercher :**
  - Messages de log indiquant les seuils appliqués
  - Seuils pour tech_lai_ecosystem et regulatory_lai
  - Confirmation de l'utilisation des seuils configurés

### 6.3 Test de Cohérence
- **À vérifier :**
  - Les résultats de matching correspondent aux seuils configurés
  - Pas d'incohérence entre config et comportement observé
  - Mode fallback activé ou non

---

## 7. Synthèse & Réponses aux Questions Métier

### 7.1 Question 1 : Dernier Run Ingestion Réel
- **À prouver :**
  - normalize_score_v2 lit bien le dernier run ingestion du client actif
  - Chemins S3 exacts + correspondance des items
  - OU explication de quel autre chemin est utilisé

### 7.2 Question 2 : Items Synthétiques vs Réels
- **À expliquer :**
  - Pourquoi le précédent rapport E2E utilisait Novartis, Roche, etc.
  - Fichier source de ces items synthétiques
  - Étape du workflow où ils sont injectés

### 7.3 Question 3 : Seuils Config-Driven
- **À confirmer :**
  - Les seuils matching_config sont-ils appliqués pour ce run réel ?
  - Reste-t-il du hardcodé 0.4 en production ?
  - Preuve via logs et résultats de matching

---

## 8. Livrable Final

### 8.1 Rapport de Diagnostic
- **Fichier :** `docs/diagnostics/lai_weekly_v3_real_data_investigation_report.md`
- **Contenu :**
  - Résumé exécutif (10-15 lignes)
  - Description du flux réel ingest → normalize → match → score
  - Tableaux de métriques détaillés
  - Liste des items traités avec provenance
  - Analyse des seuils appliqués
  - Réponses claires aux 3 questions métier

### 8.2 Preuves Documentées
- **À inclure :**
  - Captures d'écran des logs CloudWatch
  - Listings S3 avec timestamps
  - Extraits de code pertinents
  - Comparaisons config vs comportement observé

---

## Contraintes de Sécurité

⚠️ **INTERDIT de modifier :**
- `/src`, `/src_v2`
- `/canonical/*`
- `client-config-examples/*`
- Fichiers client_config sur S3
- Lambda Layers et configuration des Lambdas

✅ **AUTORISÉ :**
- Lecture de tous les fichiers et logs
- Listing et lecture d'objets S3
- Invocation des Lambdas existantes
- Création du rapport de diagnostic uniquement

---

**Début d'exécution prévu :** Immédiatement après validation du plan  
**Durée estimée :** 60-90 minutes  
**Livrable :** Rapport complet avec preuves documentées