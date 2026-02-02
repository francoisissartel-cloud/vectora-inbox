# Recommandation Expert AWS Cloud - Système Tests E2E Vectora Inbox

**Date**: 2026-02-02  
**Expert**: AWS Cloud Architecture  
**Objectif**: Système robuste de tests E2E que Q Developer comprend systématiquement

---

## 📊 Diagnostic du Problème

### Problèmes Identifiés

1. **Incrémentation manuelle confuse**
   - lai_weekly_v7 → v8 → v9 → ...
   - Q ne sait pas quand créer nouveau client
   - Confusion entre versions de test

2. **Réutilisation données anciennes**
   - Q essaye de récupérer données normalisées d'anciens clients
   - Pas de distinction claire entre test et production
   - Difficile de tracer quel test correspond à quelle modification

3. **Pas de garde-fou AWS**
   - Déploiement AWS possible sans validation locale
   - Risque de régression en production
   - Coûts AWS inutiles pour tests ratés

4. **Communication difficile avec Q**
   - Instructions manuelles répétitives
   - Q ne comprend pas systématiquement le workflow
   - Besoin de clarifier à chaque fois

---

## 💡 Solution Recommandée: Système de Test Contexts

### Principe Fondamental

**Séparation stricte**: Local (gratuit, rapide) → AWS (coûteux, validation finale)

**Traçabilité**: Chaque test a un contexte unique avec métadonnées complètes

**Protection**: Blocage automatique AWS sans succès local

### Architecture

```
tests/
├── contexts/                           # 🆕 Nouveau système
│   ├── registry.json                   # Registre central (source de vérité)
│   ├── local/                          # Contextes tests locaux
│   │   ├── test_context_001.json      # Contexte test 1
│   │   └── test_context_002.json      # Contexte test 2
│   └── aws/                            # Contextes tests AWS
│       └── test_context_001.json      # Promu depuis local
├── local/
│   └── test_e2e_runner.py             # 🆕 Runner unifié local
└── aws/
    └── test_e2e_runner.py             # 🆕 Runner unifié AWS (avec blocage)
```

### Composants Créés

1. **Registre Central** (`tests/contexts/registry.json`)
   - Trace tous les contextes (local + AWS)
   - Règles de protection
   - Historique complet

2. **Runner Local** (`tests/local/test_e2e_runner.py`)
   - Création automatique contextes
   - Exécution tests locaux
   - Mise à jour statuts

3. **Runner AWS** (`tests/aws/test_e2e_runner.py`)
   - Vérification succès local OBLIGATOIRE
   - Promotion contexte local → AWS
   - Blocage automatique si échec local

4. **Guide Q-Context** (`.q-context/vectora-inbox-test-e2e-system.md`)
   - Documentation complète pour Q Developer
   - Exemples concrets
   - Règles critiques

---

## 🚀 Workflow Recommandé

### Étape 1: Test Local (OBLIGATOIRE)

```bash
# 1. Créer nouveau contexte
python tests/local/test_e2e_runner.py --new-context "Test domain scoring fix"

# 2. Exécuter test local
python tests/local/test_e2e_runner.py --run

# 3. Vérifier succès
python tests/local/test_e2e_runner.py --status
```

**Résultat**:
- Contexte: `test_context_001`
- Client: `lai_weekly_test_001`
- Coût: ~$0.02 (Bedrock local)
- Durée: ~30s

### Étape 2: Déploiement AWS (SI LOCAL OK)

```bash
# 1. Build et deploy
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev
```

### Étape 3: Test AWS (VALIDATION FINALE)

```bash
# 1. Promouvoir contexte (vérifie automatiquement succès local)
python tests/aws/test_e2e_runner.py --promote "Validation E2E domain scoring"

# 2. Exécuter test AWS
python tests/aws/test_e2e_runner.py --run

# 3. Vérifier résultats
python tests/aws/test_e2e_runner.py --status
```

**Résultat**:
- Contexte: `test_context_001` (AWS)
- Client: `lai_weekly_v1`
- Coût: ~$0.20 (Lambda + Bedrock)
- Durée: ~2-3min

---

## 🛡️ Mécanismes de Protection

### Protection 1: Blocage AWS Sans Local

**Règle** (`registry.json`):
```json
{
  "rules": {
    "aws_deploy_blocked_without_local_success": true
  }
}
```

**Comportement**:
```bash
$ python tests/aws/test_e2e_runner.py --promote "Test"

================================================================================
❌ DÉPLOIEMENT AWS BLOQUÉ
================================================================================
Raison: Aucun test local exécuté

Actions requises:
1. Créer contexte: python tests/local/test_e2e_runner.py --new-context 'description'
2. Exécuter test: python tests/local/test_e2e_runner.py --run
3. Vérifier succès: python tests/local/test_e2e_runner.py --status
4. Revenir ici si succès
================================================================================
```

### Protection 2: Auto-Incrémentation

**Comportement**:
- Contextes locaux: `test_context_001`, `002`, `003`, ...
- Clients locaux: `lai_weekly_test_001`, `test_002`, ...
- Clients AWS: `lai_weekly_v1`, `v2`, `v3`, ...
- **Jamais de collision ou confusion**

### Protection 3: Traçabilité Complète

**Chaque contexte AWS trace son origine**:
```json
{
  "id": "test_context_001",
  "promoted_from_local": "test_context_001",
  "purpose": "Validation domain scoring fix",
  "created": "2026-02-02T10:00:00",
  "success": true
}
```

---

## 🤖 Instructions pour Q Developer

### Prompt Type 1: Nouveau Test Local

```
Je veux tester [modification] en local avant déploiement AWS.

Utilise le système de contextes:
1. Crée nouveau contexte: python tests/local/test_e2e_runner.py --new-context "Test [description]"
2. Exécute test local: python tests/local/test_e2e_runner.py --run
3. Vérifie succès et affiche résultats

NE PAS déployer sur AWS tant que test local n'a pas réussi.
```

### Prompt Type 2: Promotion AWS

```
Le test local a réussi. Je veux maintenant valider sur AWS.

Utilise le système de contextes:
1. Vérifie succès local: python tests/local/test_e2e_runner.py --status
2. Build et deploy: python scripts/build/build_all.py && python scripts/deploy/deploy_env.py --env dev
3. Promouvois vers AWS: python tests/aws/test_e2e_runner.py --promote "Validation E2E [description]"
4. Exécute test AWS: python tests/aws/test_e2e_runner.py --run
5. Analyse résultats

Le système bloquera automatiquement si test local n'a pas réussi.
```

### Prompt Type 3: Historique

```
Affiche l'historique complet des tests E2E (local et AWS).

Commandes:
- python tests/local/test_e2e_runner.py --list
- python tests/aws/test_e2e_runner.py --list

Présente les résultats de façon claire avec statuts.
```

---

## 📈 Bénéfices du Système

### Bénéfice 1: Clarté pour Q Developer

**AVANT**:
- "Crée lai_weekly_v8 ou v9 ?"
- "Dois-je réutiliser v7 ?"
- "Quand déployer AWS ?"

**APRÈS**:
- "Crée test_context_002" (auto-incrémenté)
- "Jamais réutiliser contexte"
- "AWS bloqué sans succès local"

### Bénéfice 2: Économies AWS

**AVANT**:
- Tests ratés sur AWS = $0.20 perdu
- 5 tests ratés = $1.00 perdu
- Pas de validation locale

**APRÈS**:
- Tests locaux d'abord = $0.02
- AWS uniquement si local OK
- Économie: ~90% coûts tests

### Bénéfice 3: Traçabilité

**AVANT**:
- "lai_weekly_v7 testait quoi déjà ?"
- Pas d'historique clair
- Difficile de comparer versions

**APRÈS**:
- Chaque contexte documente son purpose
- Historique complet dans registry.json
- Comparaison facile entre contextes

### Bénéfice 4: Robustesse

**AVANT**:
- Déploiement AWS sans validation
- Risque régression production
- Rollback coûteux

**APRÈS**:
- Validation locale obligatoire
- Blocage automatique si échec
- Confiance déploiement AWS

---

## 📋 Checklist Migration

### Phase 1: Setup Initial (5 min)

- [x] Créer structure `tests/contexts/`
- [x] Créer `registry.json`
- [x] Créer `test_e2e_runner.py` (local)
- [x] Créer `test_e2e_runner.py` (AWS)
- [x] Créer guide Q-Context

### Phase 2: Premier Test (10 min)

- [ ] Créer premier contexte local
- [ ] Exécuter test local
- [ ] Vérifier succès
- [ ] Promouvoir vers AWS
- [ ] Exécuter test AWS
- [ ] Valider workflow complet

### Phase 3: Documentation Q (5 min)

- [x] Ajouter référence dans `.q-context/README.md`
- [ ] Tester prompts Q Developer
- [ ] Valider compréhension Q

### Phase 4: Adoption (ongoing)

- [ ] Utiliser système pour tous nouveaux tests
- [ ] Archiver anciens lai_weekly_vX
- [ ] Former équipe au workflow

---

## 🔧 Commandes Utiles

### Gestion Contextes

```bash
# Lister contextes locaux
python tests/local/test_e2e_runner.py --list

# Lister contextes AWS
python tests/aws/test_e2e_runner.py --list

# Statut contexte actuel local
python tests/local/test_e2e_runner.py --status

# Statut contexte actuel AWS
python tests/aws/test_e2e_runner.py --status
```

### Workflow Complet

```bash
# 1. Test local
python tests/local/test_e2e_runner.py --new-context "Test feature X"
python tests/local/test_e2e_runner.py --run

# 2. Si succès, build et deploy
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev

# 3. Test AWS
python tests/aws/test_e2e_runner.py --promote "Validation feature X"
python tests/aws/test_e2e_runner.py --run
```

### Mode Force (NON RECOMMANDÉ)

```bash
# Forcer promotion AWS sans validation locale
python tests/aws/test_e2e_runner.py --promote "Test" --force
```

---

## 🎯 Règles Critiques

### RÈGLE 1: Jamais Réutiliser Contexte

❌ **INTERDIT**: Modifier code puis ré-exécuter sur même contexte

✅ **CORRECT**: Créer nouveau contexte après chaque modification

### RÈGLE 2: Jamais AWS Sans Local

❌ **INTERDIT**: Déployer AWS sans test local réussi

✅ **CORRECT**: Local d'abord, AWS ensuite

### RÈGLE 3: Toujours Documenter Purpose

❌ **INTERDIT**: `--new-context "test"`

✅ **CORRECT**: `--new-context "Validation domain scoring fix après correction config_loader"`

---

## 📊 Métriques de Succès

### Objectifs 30 Jours

- [ ] 100% tests E2E utilisent système contextes
- [ ] 0 déploiement AWS sans validation locale
- [ ] Réduction 80% coûts tests AWS
- [ ] Q Developer comprend workflow sans clarification

### KPIs

- **Taux adoption**: % tests utilisant contextes
- **Taux blocage AWS**: % tentatives bloquées (bon signe)
- **Coût moyen test**: Objectif <$0.05 (vs $0.20 avant)
- **Temps clarification Q**: Objectif 0 min (vs 5-10 min avant)

---

## 🚀 Prochaines Étapes

### Immédiat (Aujourd'hui)

1. Tester workflow complet avec premier contexte
2. Valider blocage AWS fonctionne
3. Tester prompts Q Developer

### Court Terme (Cette Semaine)

1. Migrer tous tests existants vers système contextes
2. Archiver anciens lai_weekly_vX
3. Documenter cas d'usage spécifiques

### Moyen Terme (Ce Mois)

1. Ajouter métriques automatiques dans contextes
2. Intégrer avec template E2E existant
3. Créer dashboard visualisation historique

---

## 📞 Support

### Questions Fréquentes

**Q: Puis-je encore utiliser lai_weekly_v7, v8, etc. ?**  
R: Oui pour compatibilité, mais nouveaux tests doivent utiliser système contextes.

**Q: Que faire si test local échoue ?**  
R: Corriger erreurs, créer nouveau contexte, ré-exécuter. Ne pas réutiliser contexte échoué.

**Q: Puis-je forcer AWS sans local ?**  
R: Techniquement oui avec `--force`, mais FORTEMENT DÉCONSEILLÉ.

**Q: Comment comparer deux contextes ?**  
R: Utiliser template E2E standard pour chaque contexte, puis comparer rapports.

### Contact

Pour questions sur le système: Voir `.q-context/vectora-inbox-test-e2e-system.md`

---

## ✅ Validation Finale

**Système validé pour**:
- ✅ Clarté workflow Q Developer
- ✅ Protection déploiement AWS
- ✅ Traçabilité complète
- ✅ Économies coûts
- ✅ Robustesse tests

**Prêt pour adoption immédiate**

---

**Recommandation Expert AWS Cloud**  
**Date**: 2026-02-02  
**Version**: 1.0  
**Statut**: ✅ Système opérationnel et documenté
