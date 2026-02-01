# Format de Réponse Initiale Obligatoire - Q Developer

**Date** : 2026-01-30  
**Version** : 1.0  
**Statut** : RÈGLE CRITIQUE - Application Obligatoire

---

## 🎯 RÈGLE CRITIQUE

**Q Developer DOIT TOUJOURS commencer par ce format lors de la première réponse à un prompt utilisateur.**

**Objectif** : Validation explicite du plan AVANT toute action pour éviter les dérives et garantir l'alignement avec la gouvernance.

---

## 📋 FORMAT OBLIGATOIRE DE PREMIÈRE RÉPONSE

```markdown
## 🎯 ANALYSE DE VOTRE DEMANDE

**Votre demande** : [Reformulation claire et concise du prompt utilisateur]

**Type de tâche identifié** : [Développement / Diagnostic / Test E2E / Déploiement / Configuration / Documentation]

---

## 📚 RÈGLES ET GOUVERNANCE APPLIQUÉES

**Règles de développement** :
- `.q-context/vectora-inbox-development-rules.md`
  - Architecture : 3 Lambdas V2 (ingest-v2, normalize-score-v2, newsletter-v2)
  - Code source : `src_v2/` uniquement (JAMAIS archive/_src/)
  - Hygiène repo : Temporaires dans `.tmp/`, builds dans `.build/`
  - [Autres règles spécifiques applicables]

**Gouvernance** :
- `.q-context/vectora-inbox-governance.md`
  - Workflow : Repo Local → Build → Deploy Dev → Test → Promote Stage
  - Versioning obligatoire (fichier VERSION à incrémenter)
  - Scripts standardisés uniquement (JAMAIS de commandes AWS manuelles)
  - [Autres règles de gouvernance applicables]

**Workflows** :
- `.q-context/vectora-inbox-workflows.md` ou `docs/workflows/developpement_standard.md`
  - Scénario applicable : [Scénario X : Nom du scénario]
  - Durée estimée : [XX minutes]

**Templates** :
- [Si applicable] `.q-context/templates/[nom-template].md`
- [Si test E2E] `docs/templates/TEMPLATE_TEST_E2E_STANDARD.md`

---

## 🔍 ANALYSE TECHNIQUE

**Fichiers à analyser** :
- `[chemin/fichier1]` - [Raison : comprendre architecture actuelle]
- `[chemin/fichier2]` - [Raison : identifier dépendances]
- `[chemin/fichier3]` - [Raison : valider conformité]

**Fichiers à modifier** :
- `[chemin/fichier1]` - [Nature : ajout fonction X]
- `[chemin/fichier2]` - [Nature : correction bug Y]
- `[chemin/fichier3]` - [Nature : mise à jour config Z]

**Fichiers à créer** :
- `[chemin/nouveau_fichier1]` - [Raison : nouveau module]
- `[chemin/nouveau_fichier2]` - [Raison : documentation]

**Fichiers à NE PAS toucher** :
- `archive/_src/` - [Raison : code legacy archivé]
- `[autres fichiers sensibles]` - [Raison]

---

## 🌍 ENVIRONNEMENT CIBLE

**Environnement** : [dev / stage / prod]  
**Région AWS principale** : eu-west-3 (Paris)  
**Région Bedrock** : us-east-1 (Virginie du Nord)  
**Profil AWS** : rag-lai-prod  
**Compte AWS** : 786469175371

**Ressources AWS impactées** :
- **Lambdas** : [Liste des Lambdas concernées]
- **Buckets S3** : [Liste des buckets concernés]
- **Layers** : [Liste des layers concernées]
- **Stacks CloudFormation** : [Si applicable]

**Commandes AWS prévues** :
- [Commande 1 avec --env et --profile explicites]
- [Commande 2 avec --env et --profile explicites]

---

## 📝 LIVRABLES PRÉVUS

**Documents à créer** :
- **[Type]** : `[chemin/fichier.md]`
  - Contenu : [Description du contenu]
  - Raison : [Pourquoi ce document]

**Artefacts à générer** :
- **[Type]** : `[chemin/fichier.zip]`
  - Contenu : [Description de l'artefact]
  - Utilisation : [Comment sera utilisé]

**Modifications VERSION** :
- `[COMPOSANT]_VERSION` : [X.Y.Z] → [X.Y.Z+1]
- Type d'incrémentation : [MAJOR / MINOR / PATCH]
- Justification : [Raison de l'incrémentation]

---

## ⚠️ POINTS DE VIGILANCE

**Risques identifiés** :
- **[Risque 1]** : [Description]
  - Mitigation : [Comment éviter/gérer]
- **[Risque 2]** : [Description]
  - Mitigation : [Comment éviter/gérer]

**Validations requises** :
- [ ] [Validation 1 : ex. Tests unitaires passent]
- [ ] [Validation 2 : ex. Build réussit]
- [ ] [Validation 3 : ex. Aucun fichier temporaire à la racine]

**Checkpoints de sécurité** :
- [ ] Environnement explicitement spécifié (dev/stage/prod)
- [ ] Aucune modification directe AWS sans scripts
- [ ] Versioning incrémenté avant build
- [ ] Tests en dev avant promotion stage

---

## 🚀 PLAN D'EXÉCUTION

**Phase 1 : [Nom de la phase]**
- [Action 1 détaillée]
- [Action 2 détaillée]
- Durée estimée : [X minutes]

**Phase 2 : [Nom de la phase]**
- [Action 1 détaillée]
- [Action 2 détaillée]
- Durée estimée : [X minutes]

**Phase 3 : [Nom de la phase]**
- [Action 1 détaillée]
- [Action 2 détaillée]
- Durée estimée : [X minutes]

**Durée totale estimée** : [XX minutes]

---

## ✅ VALIDATION AVANT EXÉCUTION

**Confirmez-vous que je peux procéder avec ce plan ?**

**Options de réponse** :
- ✅ **OUI** - Procéder avec ce plan tel quel
- ⚠️ **MODIFIER** - Ajuster [préciser : environnement / règles / fichiers / autre]
- ❌ **ANNULER** - Ne pas exécuter cette demande

**Si vous choisissez MODIFIER, précisez** :
- Quel élément ajuster ?
- Quelle modification souhaitée ?

---

**Attente de votre validation explicite avant de procéder.**
```

---

## 🔒 RÈGLES D'APPLICATION

### Quand Utiliser ce Format

**✅ TOUJOURS utiliser pour** :
- Première réponse à un nouveau prompt utilisateur
- Début d'une nouvelle session de chat
- Demande impliquant des modifications de code
- Demande impliquant des déploiements AWS
- Demande impliquant des modifications de configuration
- Demande de création de documentation

**⚠️ Peut être allégé pour** :
- Questions simples de clarification
- Demandes de lecture seule (afficher un fichier)
- Continuation d'un plan déjà validé

### Adaptation du Format

**Le format DOIT être adapté selon le contexte** :

**Pour un développement** :
- Détailler les fichiers `src_v2/` concernés
- Préciser l'incrémentation VERSION
- Lister les tests à exécuter

**Pour un déploiement** :
- Détailler l'environnement cible (dev/stage/prod)
- Lister toutes les commandes AWS avec --env et --profile
- Préciser les ressources AWS impactées

**Pour un test E2E** :
- Référencer le template `docs/templates/TEMPLATE_TEST_E2E_STANDARD.md`
- Préciser la baseline de comparaison
- Lister les métriques à collecter

**Pour une configuration** :
- Préciser les fichiers canonical/ ou client-config-examples/ concernés
- Détailler les commandes S3 sync
- Lister les environnements à synchroniser

---

## 📊 EXEMPLE CONCRET

### Prompt Utilisateur

```
Ajoute une fonction pour extraire les dates relatives dans les contenus ingérés.
```

### Réponse Q Developer (Format Obligatoire)

```markdown
## 🎯 ANALYSE DE VOTRE DEMANDE

**Votre demande** : Ajouter une fonction d'extraction de dates relatives (ex: "hier", "la semaine dernière") dans le module d'ingestion pour enrichir les métadonnées des items.

**Type de tâche identifié** : Développement - Nouvelle fonctionnalité

---

## 📚 RÈGLES ET GOUVERNANCE APPLIQUÉES

**Règles de développement** :
- `.q-context/vectora-inbox-development-rules.md`
  - Architecture : 3 Lambdas V2 (modification dans vectora_core/shared)
  - Code source : `src_v2/` uniquement
  - Hygiène repo : Temporaires dans `.tmp/`, builds dans `.build/`
  - Handlers minimalistes : Logique dans vectora_core

**Gouvernance** :
- `.q-context/vectora-inbox-governance.md`
  - Workflow : Repo Local → Build → Deploy Dev → Test → Promote Stage
  - Versioning obligatoire : Incrémenter VECTORA_CORE_VERSION
  - Scripts standardisés : `scripts/build/build_all.py` puis `scripts/deploy/deploy_env.py`

**Workflows** :
- `docs/workflows/developpement_standard.md`
  - Scénario applicable : Scénario 1 - Nouvelle Fonctionnalité
  - Durée estimée : 30-60 minutes

---

## 🔍 ANALYSE TECHNIQUE

**Fichiers à analyser** :
- `src_v2/vectora_core/shared/utils.py` - Comprendre utilitaires existants
- `src_v2/vectora_core/ingest/__init__.py` - Identifier où intégrer la fonction
- `src_v2/lambdas/ingest/handler.py` - Valider que handler délègue bien à vectora_core

**Fichiers à modifier** :
- `src_v2/vectora_core/shared/utils.py` - Ajout fonction `extract_relative_dates(text: str) -> dict`
- `src_v2/vectora_core/ingest/__init__.py` - Intégration de l'extraction dans le workflow
- `VERSION` - Incrémenter VECTORA_CORE_VERSION de 1.2.3 à 1.3.0 (MINOR)

**Fichiers à créer** :
- `tests/unit/test_extract_relative_dates.py` - Tests unitaires de la nouvelle fonction
- `docs/design/plan_extraction_dates_relatives_20260130.md` - Documentation de la fonctionnalité

**Fichiers à NE PAS toucher** :
- `archive/_src/` - Code legacy archivé
- `src_v2/lambdas/ingest/handler.py` - Handler reste minimaliste

---

## 🌍 ENVIRONNEMENT CIBLE

**Environnement** : dev (puis promotion vers stage après validation)  
**Région AWS principale** : eu-west-3 (Paris)  
**Profil AWS** : rag-lai-prod  
**Compte AWS** : 786469175371

**Ressources AWS impactées** :
- **Lambdas** : vectora-inbox-ingest-v2-dev (via layer vectora-core)
- **Layers** : vectora-inbox-vectora-core-dev (rebuild nécessaire)
- **Buckets S3** : vectora-inbox-lambda-code-dev (stockage layer)

**Commandes AWS prévues** :
```bash
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev
python scripts/invoke/invoke_ingest_v2.py --client-id lai_weekly_v7
```

---

## 📝 LIVRABLES PRÉVUS

**Documents à créer** :
- **Plan de développement** : `docs/design/plan_extraction_dates_relatives_20260130.md`
  - Contenu : Spécifications, architecture, tests
  - Raison : Traçabilité de la fonctionnalité

**Artefacts à générer** :
- **Layer vectora-core** : `.build/layers/vectora-core-1.3.0.zip`
  - Contenu : vectora_core/ avec nouvelle fonction
  - Utilisation : Déploiement sur Lambda ingest-v2-dev

**Modifications VERSION** :
- `VECTORA_CORE_VERSION` : 1.2.3 → 1.3.0
- Type d'incrémentation : MINOR (nouvelle fonctionnalité)
- Justification : Ajout fonction extract_relative_dates (non breaking)

---

## ⚠️ POINTS DE VIGILANCE

**Risques identifiés** :
- **Parsing dates ambiguës** : "hier" peut être ambigu selon le contexte
  - Mitigation : Utiliser dateparser avec locale fr_FR et fallback
- **Performance** : Extraction sur tous les items peut ralentir ingestion
  - Mitigation : Rendre optionnel via config client (enable_relative_dates: true)

**Validations requises** :
- [ ] Tests unitaires passent (test_extract_relative_dates.py)
- [ ] Build layer réussit sans erreur
- [ ] Test E2E sur lai_weekly_v7 en dev
- [ ] Aucun fichier temporaire à la racine après build

**Checkpoints de sécurité** :
- [ ] Environnement dev explicitement spécifié
- [ ] VERSION incrémentée AVANT build
- [ ] Tests en dev AVANT promotion stage
- [ ] Scripts standardisés utilisés (pas de commandes AWS manuelles)

---

## 🚀 PLAN D'EXÉCUTION

**Phase 1 : Développement (15 min)**
- Créer fonction `extract_relative_dates()` dans `src_v2/vectora_core/shared/utils.py`
- Intégrer dans workflow ingestion (`src_v2/vectora_core/ingest/__init__.py`)
- Créer tests unitaires (`tests/unit/test_extract_relative_dates.py`)

**Phase 2 : Build & Deploy Dev (10 min)**
- Incrémenter VERSION : VECTORA_CORE_VERSION=1.3.0
- Build layer : `python scripts/build/build_all.py`
- Deploy dev : `python scripts/deploy/deploy_env.py --env dev`

**Phase 3 : Tests & Validation (15 min)**
- Test E2E : `python scripts/invoke/invoke_ingest_v2.py --client-id lai_weekly_v7`
- Vérifier extraction dates dans items.json S3
- Valider aucune régression sur items existants

**Phase 4 : Documentation (10 min)**
- Créer plan de développement dans `docs/design/`
- Mettre à jour README si nécessaire

**Durée totale estimée** : 50 minutes

---

## ✅ VALIDATION AVANT EXÉCUTION

**Confirmez-vous que je peux procéder avec ce plan ?**

**Options de réponse** :
- ✅ **OUI** - Procéder avec ce plan tel quel
- ⚠️ **MODIFIER** - Ajuster [préciser : environnement / règles / fichiers / autre]
- ❌ **ANNULER** - Ne pas exécuter cette demande

**Si vous choisissez MODIFIER, précisez** :
- Quel élément ajuster ?
- Quelle modification souhaitée ?

---

**Attente de votre validation explicite avant de procéder.**
```

---

## 🎯 BÉNÉFICES DE CE FORMAT

### Pour l'Utilisateur

1. **Contrôle total** : Validation explicite avant toute action
2. **Sécurité** : Détection immédiate si Q dévie des règles
3. **Traçabilité** : Historique clair des décisions et justifications
4. **Apprentissage** : Compréhension du raisonnement de Q
5. **Confiance** : Transparence totale sur les actions prévues

### Pour Q Developer

1. **Clarté** : Forcer l'analyse avant l'action
2. **Cohérence** : Référencer explicitement les règles applicables
3. **Qualité** : Réduire les erreurs par validation préalable
4. **Contexte** : Renforcer la compréhension du projet
5. **Alignement** : Garantir le respect de la gouvernance

---

## 📞 SUPPORT

**En cas de non-respect du format** :

Si Q Developer ne suit pas ce format, rappeler :
```
Merci de commencer par le format de réponse initiale obligatoire défini dans 
.q-context/q-response-format.md avant de procéder.
```

**Exceptions autorisées** :
- Questions de clarification simples
- Demandes de lecture seule
- Continuation d'un plan déjà validé

---

**Format de Réponse Initiale - Version 1.0**  
**Date** : 2026-01-30  
**Statut** : RÈGLE CRITIQUE - Application Obligatoire
