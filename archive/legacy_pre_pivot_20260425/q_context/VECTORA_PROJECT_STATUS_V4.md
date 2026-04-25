# Vectora Inbox - État du Projet et Roadmap V4

**Version**: 4.0  
**Date**: 2026-04-23  
**Statut**: TRANSITION ARCHITECTURALE - Newsletter Engine → Ingestion Engine  
**Audience**: Équipe de développement et AI assistants

---

## 🎯 **SYNTHÈSE EXÉCUTIVE**

### **Révélation Architecturale**
Vous venez de comprendre que l'approche actuelle (runs d'ingestion ponctuels pour générer des newsletters) n'est pas optimale. La bonne approche est de créer un **moteur d'ingestion continue** qui alimente un **datalake normalisé**, puis de générer les newsletters en queryant ce datalake.

### **Transformation Fondamentale**
```
AVANT: Client Config → Run E2E → Newsletter
APRÈS: Sources Continues → Warehouse → Datalake → Newsletter Scripts
```

Cette transformation change Vectora Inbox d'un "newsletter generator" en une véritable "data platform" pour l'écosystème LAI.

---

## 📊 **ÉTAT ACTUEL DU PROJET**

### **Ce Qui Existe et Fonctionne (V3)**

#### **✅ Moteur d'Ingestion V3** (`src_v3/vectora_core/ingest/`)
- **IngestionOrchestratorV3** : Pipeline complet d'ingestion
- **SourceRouter** : Résolution bouquets → sources
- **FilterEngineV3** : Filtrage configurable
- **RSSParserV3 / HTMLParserV3** : Parsing multi-format
- **Cache client-spécifique** : Évite faux négatifs

**Status** : ✅ Opérationnel, testé, prêt à adapter

#### **✅ Système Warehouse** (`src_v3/vectora_core/warehouse/`)
- **IngestedWarehouse** : Stockage items ingérés
- **DeduplicationManager** : Évite doublons
- **ClientMappingManager** : Mapping clients/écosystèmes

**Status** : ✅ Fonctionnel, base solide pour extension

#### **✅ Moteur de Normalisation** (`src_v3/vectora_core/normalization/`)
- **BedrockNormalizer** : Normalisation LLM
- **DomainScorer** : Scoring par domaine
- **Extraction entités** : Companies, molecules, technologies

**Status** : ✅ Opérationnel, prêt à adapter pour traitement batch

#### **✅ Configuration Canonical** (`canonical/`)
- **Sources V3** : Catalog + configs + candidates (180+ sources)
- **Scopes LAI** : Companies, molecules, technologies, trademarks
- **Profils d'ingestion** : RSS, HTML, filtres
- **Prompts Bedrock** : Normalisation, scoring, éditorial

**Status** : ✅ Riche et mature, base excellente pour extension

#### **✅ Scripts et Outils** (`scripts/`)
- **Discovery** : Validation automatique nouvelles sources
- **Validation** : Tests de performance et qualité
- **Backup** : Gestion des sauvegardes
- **Monitoring** : Métriques et alertes

**Status** : ✅ Écosystème d'outils mature

### **Ce Qui Manque pour V4 (Ingestion Continue)**

#### **❌ Scheduler d'Ingestion Continue**
```python
# À CRÉER : src_v3/vectora_core/continuous/scheduler.py
class ContinuousIngestionScheduler:
    """Gère l'ingestion automatique des sources selon schedule"""
```

#### **❌ Pipeline de Normalisation Automatique**
```python
# À CRÉER : src_v3/vectora_core/continuous/normalization_pipeline.py
class AutoNormalizationPipeline:
    """Pipeline automatique warehouse → datalake normalisé"""
```

#### **❌ Datalake Normalisé**
```python
# À CRÉER : src_v3/vectora_core/datalake/
class NormalizedDatalake:
    """Stockage et query des items normalisés"""
```

#### **❌ API de Query Newsletter**
```python
# À CRÉER : src_v3/vectora_core/newsletter/generator_v4.py
class NewsletterGeneratorV4:
    """Génération newsletter basée sur query datalake"""
```

#### **❌ Configuration Écosystèmes**
```yaml
# À CRÉER : canonical/ecosystems/tech_lai_ecosystem.yaml
# Configuration des écosystèmes et scheduling
```

---

## 🏗️ **ARCHITECTURE CIBLE V4**

### **Flux de Données Complet**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           INGESTION CONTINUE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Sources (180+)     Scheduler        Moteur V3         Warehouse            │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐      │
│  │ MedinCell   │──▶│ every_3_days│──▶│ Ingest      │──▶│ Raw Items   │      │
│  │ FierceBio   │   │ daily       │   │ Parse       │   │ Deduplicated│      │
│  │ Endpoints   │   │ weekly      │   │ Filter      │   │ Indexed     │      │
│  │ ...         │   │ ...         │   │ Cache       │   │ ...         │      │
│  └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        NORMALISATION AUTOMATIQUE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Détection          Normalisation      Scoring           Datalake           │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐      │
│  │ New Items   │──▶│ Bedrock     │──▶│ Domain      │──▶│ Normalized  │      │
│  │ Queue       │   │ Entities    │   │ Scoring     │   │ Indexed     │      │
│  │ Batch       │   │ Events      │   │ Enriched    │   │ Queryable   │      │
│  │ ...         │   │ ...         │   │ ...         │   │ ...         │      │
│  └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        NEWSLETTER À LA DEMANDE                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Client Config      Query API         Sélection        Newsletter          │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐      │
│  │ lai_weekly  │──▶│ Query 7days │──▶│ Top Items   │──▶│ Markdown    │      │
│  │ mvp_test    │   │ Filter LAI  │   │ Sections    │   │ HTML        │      │
│  │ Period      │   │ Score > 0.3 │   │ Editorial   │   │ Email       │      │
│  │ ...         │   │ ...         │   │ ...         │   │ ...         │      │
│  └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### **Avantages de l'Architecture V4**

#### **Performance**
- ✅ **Ingestion séquentielle** : Une source à la fois, pas de surcharge
- ✅ **Newsletter rapide** : < 30 secondes (query datalake vs 15 min ingestion)
- ✅ **Cache efficace** : Pas de re-ingestion inutile
- ✅ **Scalabilité** : Ajout facile nouvelles sources

#### **Flexibilité**
- ✅ **Période flexible** : Newsletter sur n'importe quelle période
- ✅ **Multi-clients** : Même datalake pour tous les clients
- ✅ **Données fraîches** : Ingestion continue automatique
- ✅ **Requêtes complexes** : Analytics et tendances possibles

#### **Évolutivité**
- ✅ **Base RAG** : Datalake comme knowledge base
- ✅ **Analytics** : Trending topics, competitive intelligence
- ✅ **Multi-écosystèmes** : Extension siRNA, cell therapy, etc.
- ✅ **API publique** : Monétisation des données enrichies

---

## 🛠️ **PLAN DE DÉVELOPPEMENT V4**

### **Phase 1 : Infrastructure Continue (Semaines 1-2)**

#### **Objectifs**
- Créer le scheduler d'ingestion continue
- Adapter le warehouse pour ingestion automatique
- Tester avec sources pilotes

#### **Livrables**
- [ ] `ContinuousIngestionScheduler` opérationnel
- [ ] Configuration `tech_lai_ecosystem.yaml`
- [ ] Test ingestion MedinCell + FierceBiotech automatique
- [ ] Monitoring et logs

#### **Critères de Succès**
- Sources ingérées selon schedule configuré
- Warehouse alimenté automatiquement
- Pas de surcharge système (une source à la fois)

### **Phase 2 : Pipeline Normalisation (Semaines 3-4)**

#### **Objectifs**
- Créer le pipeline automatique warehouse → datalake
- Adapter le moteur de normalisation pour traitement batch
- Implémenter le datalake normalisé

#### **Livrables**
- [ ] `AutoNormalizationPipeline` fonctionnel
- [ ] `NormalizedDatalake` avec indexation
- [ ] Détection automatique nouveaux items
- [ ] Tests de normalisation batch

#### **Critères de Succès**
- Items normalisés automatiquement (< 6h après ingestion)
- Datalake indexé et queryable
- Performance équivalente à V3

### **Phase 3 : Newsletter V4 (Semaines 5-6)**

#### **Objectifs**
- Créer l'API de query datalake
- Adapter le générateur newsletter pour query rapide
- Migrer les configs clients existantes

#### **Livrables**
- [ ] `DatalakeQueryAPI` optimisée
- [ ] `NewsletterGeneratorV4` basé sur datalake
- [ ] Migration configs clients V3 → V4
- [ ] Tests comparatifs V3/V4

#### **Critères de Succès**
- Newsletter générée en < 30 secondes
- Qualité équivalente à V3 (> 90% items identiques)
- Flexibilité période (7 jours, 30 jours, 6 mois)

### **Phase 4 : Production et Monitoring (Semaines 7-8)**

#### **Objectifs**
- Déployer l'ingestion continue en production
- Créer monitoring et alertes
- Migrer tous les clients existants

#### **Livrables**
- [ ] Scheduler en production (cron/systemd)
- [ ] Dashboard monitoring temps réel
- [ ] Migration complète clients
- [ ] Documentation utilisateur

#### **Critères de Succès**
- Ingestion continue stable (> 95% uptime)
- Newsletters générées à la demande
- Clients migrés sans régression

---

## 📋 **RÉUTILISATION DE L'EXISTANT**

### **Composants V3 à Adapter (Pas Réécrire)**

#### **Moteur d'Ingestion V3** → **Ingestion Continue**
```python
# ADAPTATION, pas réécriture
class ContinuousIngestionEngine:
    def __init__(self):
        # Réutilise TOUT le moteur V3
        self.orchestrator = IngestionOrchestratorV3()
        self.source_router = SourceRouter()
        self.filter_engine = FilterEngineV3()
    
    def process_single_source(self, source_key):
        """Nouvelle méthode : traite UNE source au lieu d'un bouquet"""
        # Adaptation mineure du workflow existant
```

#### **Moteur Normalisation V3** → **Pipeline Batch**
```python
# ADAPTATION, pas réécriture
class BatchNormalizer:
    def __init__(self):
        # Réutilise TOUT le moteur V3
        self.normalizer = BedrockNormalizer()
        self.scorer = DomainScorer()
    
    def normalize_batch(self, items):
        """Nouvelle méthode : traite batch au lieu de run complet"""
        # Même logique, différent input
```

#### **Configuration Canonical** → **Extension Écosystèmes**
```yaml
# EXTENSION, pas remplacement
canonical/
├── sources/              # EXISTANT - Inchangé
├── scopes/              # EXISTANT - Inchangé  
├── prompts/             # EXISTANT - Inchangé
└── ecosystems/          # NOUVEAU - Extension
    └── tech_lai_ecosystem.yaml
```

### **Avantage de la Réutilisation**
- ✅ **Pas de régression** : Même qualité garantie
- ✅ **Développement rapide** : 80% du code existe déjà
- ✅ **Risque minimal** : Composants éprouvés
- ✅ **Migration douce** : V3 et V4 coexistent

---

## 🎯 **MÉTRIQUES DE SUCCÈS V4**

### **Performance**
- **Temps ingestion source** : < 2 minutes (vs 10-30 min run complet V3)
- **Temps génération newsletter** : < 30 secondes (vs 5-15 min V3)
- **Fréquence ingestion** : Respect des schedules (daily, every_3_days)
- **Utilisation ressources** : < 1GB RAM (vs 2-4GB runs longs V3)

### **Qualité**
- **Items identiques V3/V4** : > 95%
- **Scores identiques** : > 90% (variations mineures acceptables)
- **Sélection newsletter** : > 90% items identiques
- **Taux succès normalisation** : > 98%

### **Fiabilité**
- **Uptime ingestion continue** : > 95%
- **Cohérence datalake** : 100% (pas de corruption)
- **Gestion erreurs** : Recovery automatique < 6h
- **Monitoring** : Alertes temps réel sur échecs

### **Évolutivité**
- **Ajout nouvelles sources** : < 1 jour (vs 1 semaine V3)
- **Extension écosystèmes** : siRNA, cell therapy prêts
- **API publique** : Base pour monétisation
- **RAG ready** : Datalake comme knowledge base

---

## 🚨 **RISQUES ET MITIGATIONS**

### **Risques Identifiés**

#### **1. Complexité Migration**
- **Risque** : Beaucoup de composants à adapter simultanément
- **Mitigation** : Migration phase par phase avec validation continue
- **Indicateur** : Tests V3/V4 comparatifs à chaque étape

#### **2. Régression Qualité**
- **Risque** : Différences subtiles entre V3 et V4
- **Mitigation** : Réutilisation maximale composants V3 éprouvés
- **Indicateur** : > 95% items identiques entre V3/V4

#### **3. Performance Datalake**
- **Risque** : Queries lentes si mal optimisées
- **Mitigation** : Design index dès le début, tests de charge
- **Indicateur** : Newsletter < 30 secondes même avec 6 mois de données

#### **4. Fiabilité Pipeline Continu**
- **Risque** : Échecs en cascade si pipeline fragile
- **Mitigation** : Gestion erreurs robuste, monitoring complet
- **Indicateur** : Recovery automatique < 6h, uptime > 95%

### **Plan de Contingence**
- **Rollback V3** : Maintien V3 en parallèle pendant migration
- **Tests A/B** : Comparaison qualité V3/V4 en continu
- **Migration progressive** : Client par client, pas big bang
- **Monitoring renforcé** : Alertes sur toutes les métriques critiques

---

## 🎓 **APPRENTISSAGES ET ÉVOLUTIONS**

### **Ce Que Cette Architecture Permet**

#### **Court Terme (3-6 mois)**
- **Newsletter ultra-rapide** : Génération en secondes vs minutes
- **Flexibilité période** : 7 jours, 30 jours, 6 mois à la demande
- **Stabilité système** : Pas de surcharge sur runs longs
- **Multi-clients efficace** : Même datalake pour tous

#### **Moyen Terme (6-12 mois)**
- **Analytics avancées** : Trending topics, competitive intelligence
- **Extension écosystèmes** : siRNA, cell therapy, gene therapy
- **API publique** : Monétisation des données enrichies
- **Alertes temps réel** : Notifications sur événements critiques

#### **Long Terme (1-2 ans)**
- **RAG spécialisé LAI** : Datalake comme knowledge base
- **Recherche sémantique** : Q&A contextuel sur corpus LAI
- **Prédictions ML** : Modèles sur historique datalake
- **Marketplace data** : Plateforme de données biotech

### **Valeur Stratégique**
Cette transformation change Vectora Inbox d'un "outil de newsletter" en une véritable **plateforme de données LAI**. Le datalake normalisé devient un actif stratégique réutilisable pour de multiples produits futurs.

---

## 📞 **SUPPORT ET RESSOURCES**

### **Documentation Créée**
- **`VECTORA_INGESTION_ENGINE_ARCHITECTURE.md`** : Architecture complète V4
- **`VECTORA_MIGRATION_GUIDE_V4.md`** : Guide pratique de migration
- **Ce document** : État projet et roadmap

### **Documentation Existante à Consulter**
- **`VECTORA_INBOX_V3_ARCHITECTURE.md`** : Architecture V3 actuelle
- **`VECTORA_INBOX_V3_PRINCIPLES.md`** : Principes de développement
- **`CONTEXTE_BUSINESS_VECTORA.md`** : Vision métier et objectifs

### **Prochaines Étapes Immédiates**
1. **Lire** la documentation architecture V4 complète
2. **Comprendre** le plan de migration détaillé
3. **Commencer** par Phase 1 : Infrastructure Continue
4. **Tester** avec sources pilotes (MedinCell, FierceBiotech)

### **Critères de Démarrage**
- [ ] Architecture V4 comprise
- [ ] Plan de migration validé
- [ ] Environnement de développement prêt
- [ ] Backup V3 créé

---

**Synthèse créée le** : 2026-04-23  
**Version** : 4.0  
**Statut** : ROADMAP DÉFINIE - Prêt pour développement V4  
**Objectif** : Transformation Newsletter Engine → Data Platform LAI