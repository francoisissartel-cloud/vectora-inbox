# Architecture Vectora Ingestion Engine - Moteur d'Ingestion Continue

**Version**: 4.0  
**Date**: 2026-04-23  
**Statut**: NOUVELLE ARCHITECTURE - Ingestion Continue + Datalake Normalisé  
**Évolution**: Newsletter Workflow → Data Platform

---

## 🎯 **RÉVOLUTION ARCHITECTURALE**

### **Ancien Paradigme : Run-Based Newsletter Generation**
```
Client Config → Run Complet E2E → Newsletter Générée
```
- Workflow ponctuel pour créer une newsletter
- Ingestion à la demande sur période spécifique
- Surcharge moteur pour runs longs (6 mois, 200 jours)
- Pas de réutilisation des données entre clients

### **Nouveau Paradigme : Continuous Ingestion + Data Platform**
```
Sources Automatisées → Warehouse (Raw) → Datalake (Normalized) → Newsletter Scripts
```
- **Ingestion continue** : Sources alimentées automatiquement (hebdo/3 jours)
- **Warehouse centralisé** : Stockage raw de tous les items ingérés
- **Datalake normalisé** : Pipeline de normalisation automatique
- **Newsletter à la demande** : Query sur datalake pour générer newsletters

---

## 🏗️ **ARCHITECTURE GLOBALE**

### **Pipeline d'Ingestion Continue**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐    ┌─────────────────┐
│   SOURCES       │    │   MOTEUR         │    │    WAREHOUSE        │    │   DATALAKE      │
│   AUTOMATISÉES  │───▶│   INGESTION      │───▶│    (RAW)           │───▶│  NORMALISÉ      │
│                 │    │   CONTINUE       │    │                     │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────────┘    └─────────────────┘
│                                                                                              │
│ • RSS Feeds                                                                                  │
│ • Corporate Sites                                                                            │
│ • Press Releases                                                                             │
│ • Scheduler par source                                                                       │
│                                                                                              │
└──────────────────────────────────────────────────────────────────────────────────────────┘
                                                │
                                                ▼
                                    ┌─────────────────────┐
                                    │   NEWSLETTER        │
                                    │   SCRIPTS           │
                                    │                     │
                                    │ • Query Datalake    │
                                    │ • Sélection Items   │
                                    │ • Rédaction Auto    │
                                    └─────────────────────┘
```

### **Composants Principaux**

#### **1. Moteur d'Ingestion Continue**
- **Rôle** : Ingestion séquentielle et automatisée des sources
- **Fonctionnement** : 
  - Scheduler par source (ex: tech_sources tous les 3 jours)
  - Traitement séquentiel (une source à la fois)
  - Cache intelligent pour éviter re-ingestion
  - Alimentation continue du warehouse

#### **2. Warehouse Ingested (Raw)**
- **Rôle** : Stockage centralisé de tous les items ingérés
- **Format** : Items bruts avec métadonnées d'ingestion
- **Organisation** : Par écosystème (tech_lai_ecosystem)
- **Fonctionnalités** : Déduplication, indexation, monitoring

#### **3. Pipeline de Normalisation**
- **Rôle** : Transformation warehouse → datalake normalisé
- **Déclenchement** : Détection automatique nouveaux items
- **Traitement** : Normalisation + scoring + enrichissement
- **Output** : Items structurés dans datalake

#### **4. Datalake Normalisé**
- **Rôle** : Stockage final des items enrichis et scorés
- **Requêtes** : API pour extraction par période/secteur/client
- **Performance** : Index optimisés pour queries rapides
- **Évolutivité** : Base pour futures fonctionnalités (RAG, analytics)

---

## 📁 **STRUCTURE DES DONNÉES**

### **Warehouse Ingested (Raw)**
```
data/warehouse/ingested/
├── profiles/
│   └── tech_lai_ecosystem/
│       ├── 2026/04/23/
│       │   ├── press_corporate__medincell_items.jsonl
│       │   ├── press_sector__fiercebiotech_items.jsonl
│       │   └── metadata.json
│       ├── 2026/04/24/
│       └── index/
│           ├── by_source.json
│           ├── by_date.json
│           └── stats.json
└── config/
    ├── warehouse_config.json
    └── client_mappings.json
```

### **Datalake Normalisé**
```
data/datalake/normalized/
├── tech_lai_ecosystem/
│   ├── 2026/04/
│   │   ├── items_normalized.parquet
│   │   ├── entities_extracted.parquet
│   │   └── scores_computed.parquet
│   ├── indexes/
│   │   ├── by_company.json
│   │   ├── by_technology.json
│   │   ├── by_event_type.json
│   │   └── by_score_range.json
│   └── aggregates/
│       ├── monthly_stats.json
│       └── trending_topics.json
└── config/
    └── datalake_schema.json
```

---

## 🔄 **WORKFLOW D'INGESTION CONTINUE**

### **Configuration des Sources**
```yaml
# canonical/ingestion/continuous_sources_config.yaml
continuous_ingestion:
  ecosystems:
    tech_lai_ecosystem:
      description: "Écosystème technologique LAI"
      sources:
        - source_key: press_corporate__medincell
          schedule: "every_3_days"
          priority: high
          enabled: true
        - source_key: press_sector__fiercebiotech
          schedule: "daily"
          priority: medium
          enabled: true
      
  scheduling:
    max_concurrent_sources: 1  # Séquentiel pour éviter surcharge
    retry_failed_after: "6_hours"
    cache_ttl_days: 7
    
  warehouse:
    ecosystem: tech_lai_ecosystem
    retention_days: 730
    deduplication_method: content_hash
```

### **Scheduler d'Ingestion**
```python
class ContinuousIngestionScheduler:
    """Scheduler pour ingestion continue des sources"""
    
    def run_daily_cycle(self):
        """Cycle quotidien d'ingestion"""
        # 1. Identifier sources à traiter aujourd'hui
        sources_to_process = self.get_scheduled_sources()
        
        # 2. Traitement séquentiel
        for source in sources_to_process:
            try:
                self.process_source(source)
                self.update_warehouse(source.items)
                self.trigger_normalization_if_needed()
            except Exception as e:
                self.log_error(source, e)
                self.schedule_retry(source)
    
    def process_source(self, source_config):
        """Traite une source individuelle"""
        # Utilise le moteur d'ingestion V3 existant
        # Mais pour une seule source à la fois
        pass
```

### **Pipeline de Normalisation Automatique**
```python
class AutoNormalizationPipeline:
    """Pipeline automatique warehouse → datalake"""
    
    def detect_new_items(self):
        """Détecte les nouveaux items dans le warehouse"""
        # Scan warehouse pour items non encore normalisés
        pass
    
    def normalize_batch(self, items):
        """Normalise un batch d'items"""
        # Utilise le moteur de normalisation V3 existant
        # Bedrock + scoring + enrichissement
        pass
    
    def update_datalake(self, normalized_items):
        """Met à jour le datalake avec items normalisés"""
        # Stockage optimisé + mise à jour index
        pass
```

---

## 🎛️ **CONFIGURATION CANONICAL ADAPTÉE**

### **Source Configs pour Ingestion Continue**
```yaml
# canonical/ingestion/source_configs_continuous.yaml
press_corporate__medincell:
  validated: true
  continuous_ingestion:
    enabled: true
    schedule: "every_3_days"
    priority: high
  
  # Config technique inchangée
  news_url: "https://www.medincell.com/news/"
  ingestion_profile: html_generic
  listing_selectors:
    container: "article.masonry-blog-item"
  date_selectors:
    css: "span.meta-date.date.published"
```

### **Ecosystem Configs**
```yaml
# canonical/ecosystems/tech_lai_ecosystem.yaml
ecosystem_id: tech_lai_ecosystem
description: "Écosystème technologique Long-Acting Injectables"

# Sources appartenant à cet écosystème
source_bouquets:
  - lai_corporate_continuous
  - lai_press_continuous
  - lai_research_continuous

# Configuration warehouse
warehouse:
  retention_days: 730
  max_items: 100000
  deduplication_method: content_hash

# Configuration datalake
datalake:
  normalization_schedule: "every_6_hours"
  scoring_model: lai_domain_scoring
  index_update_frequency: real_time

# Clients utilisant cet écosystème
clients:
  - lai_weekly
  - mvp_test_30days
  - test_medincell
```

---

## 📊 **GÉNÉRATION DE NEWSLETTERS À LA DEMANDE**

### **Nouveau Workflow Newsletter**
```python
class NewsletterGenerator:
    """Générateur de newsletter basé sur datalake"""
    
    def generate_newsletter(self, client_config, period_days=7):
        """Génère newsletter en queryant le datalake"""
        
        # 1. Query datalake pour période donnée
        items = self.datalake.query_items(
            ecosystem="tech_lai_ecosystem",
            period_days=period_days,
            min_score=client_config.min_domain_score,
            watch_domains=client_config.watch_domains
        )
        
        # 2. Sélection selon critères client
        selected_items = self.selector.select_items(
            items, client_config.newsletter_selection
        )
        
        # 3. Rédaction newsletter
        newsletter = self.editor.generate_newsletter(
            selected_items, client_config.newsletter_layout
        )
        
        return newsletter
```

### **API de Query Datalake**
```python
class DatalakeQueryAPI:
    """API pour requêter le datalake normalisé"""
    
    def query_items(self, ecosystem: str, **filters) -> List[Dict]:
        """Query générique avec filtres"""
        
    def get_recent_items(self, ecosystem: str, days: int) -> List[Dict]:
        """Items récents par écosystème"""
        
    def get_company_items(self, company_id: str, period_days: int) -> List[Dict]:
        """Items d'une company sur période"""
        
    def get_trending_topics(self, ecosystem: str, period_days: int) -> List[Dict]:
        """Topics tendance par écosystème"""
        
    def search_by_keywords(self, keywords: List[str], **filters) -> List[Dict]:
        """Recherche par mots-clés"""
```

---

## 🔧 **MIGRATION DE L'EXISTANT**

### **Réutilisation des Composants V3**

#### **Moteur d'Ingestion V3 → Ingestion Continue**
```python
# Adaptation du moteur existant
class ContinuousIngestionEngine:
    def __init__(self):
        # Réutilise les composants V3 existants
        self.orchestrator = IngestionOrchestratorV3()
        self.source_router = SourceRouter()
        self.filter_engine = FilterEngineV3()
        
    def process_single_source(self, source_key: str):
        """Traite une seule source (vs bouquet complet)"""
        # Adaptation pour traitement source par source
        pass
```

#### **Moteur de Normalisation V3 → Pipeline Auto**
```python
# Adaptation du normalize_score existant
class AutoNormalizationEngine:
    def __init__(self):
        # Réutilise le moteur de normalisation V3
        self.normalizer = BedrockNormalizer()
        self.scorer = DomainScorer()
        
    def process_warehouse_batch(self, items: List[Dict]):
        """Normalise un batch depuis le warehouse"""
        # Même logique que V3 mais sur données warehouse
        pass
```

### **Configuration Client Adaptée**
```yaml
# Nouvelle structure client config
client_profile:
  client_id: "lai_weekly_v4"
  name: "LAI Weekly - Ingestion Continue"
  
# Plus de source_bouquets (géré par l'écosystème)
ecosystem_subscription:
  ecosystem_id: "tech_lai_ecosystem"
  subscription_type: "full"  # ou "filtered"

# Configuration newsletter inchangée
watch_domains:
  - id: "tech_lai_ecosystem"
    type: "technology"
    priority: "high"

newsletter_selection:
  max_items_total: 50
  min_domain_score: 0.3
  period_days: 7  # Période pour query datalake

newsletter_layout:
  # Inchangé
```

---

## 🚀 **AVANTAGES DE LA NOUVELLE ARCHITECTURE**

### **Performance et Scalabilité**
- ✅ **Pas de surcharge** : Ingestion séquentielle (une source à la fois)
- ✅ **Cache efficace** : Évite re-ingestion inutile
- ✅ **Parallélisation** : Normalisation découplée de l'ingestion
- ✅ **Scalabilité** : Ajout facile de nouvelles sources

### **Flexibilité et Réactivité**
- ✅ **Newsletter à la demande** : Génération rapide sur n'importe quelle période
- ✅ **Données toujours fraîches** : Ingestion continue automatique
- ✅ **Multi-clients** : Même datalake pour tous les clients
- ✅ **Requêtes complexes** : Analytics et tendances possibles

### **Maintenance et Évolutivité**
- ✅ **Séparation des responsabilités** : Ingestion ≠ Newsletter
- ✅ **Monitoring granulaire** : Suivi par source et par pipeline
- ✅ **Évolution naturelle** : Base pour RAG et analytics futures
- ✅ **Coûts optimisés** : Pas de re-traitement inutile

---

## 📋 **PLAN DE MIGRATION**

### **Phase 1 : Infrastructure Warehouse (Semaine 1-2)**
- [ ] Adapter le système warehouse existant
- [ ] Créer le scheduler d'ingestion continue
- [ ] Configurer les sources pour ingestion automatique
- [ ] Tests avec sources pilotes (MedinCell, FierceBiotech)

### **Phase 2 : Pipeline de Normalisation (Semaine 3-4)**
- [ ] Adapter le moteur normalize_score pour traitement batch
- [ ] Créer la détection automatique nouveaux items
- [ ] Implémenter le pipeline warehouse → datalake
- [ ] Tests de normalisation automatique

### **Phase 3 : API Newsletter (Semaine 5-6)**
- [ ] Créer l'API de query datalake
- [ ] Adapter le générateur de newsletter
- [ ] Migrer les configs clients existantes
- [ ] Tests de génération newsletter à la demande

### **Phase 4 : Production et Monitoring (Semaine 7-8)**
- [ ] Déploiement du scheduler en production
- [ ] Monitoring et alertes
- [ ] Migration complète des clients existants
- [ ] Documentation utilisateur finale

---

## 🎯 **MÉTRIQUES DE SUCCÈS**

### **Performance Ingestion**
- **Temps traitement source** : < 2 minutes par source
- **Fréquence ingestion** : Respect des schedules configurés
- **Taux d'erreur** : < 5% des runs d'ingestion
- **Cache hit rate** : > 80% après warm-up

### **Qualité Datalake**
- **Latence normalisation** : < 6h entre ingestion et datalake
- **Complétude données** : > 95% items normalisés avec succès
- **Cohérence index** : 100% synchronisation index/données
- **Déduplication** : 0% doublons dans le datalake

### **Performance Newsletter**
- **Temps génération** : < 30 secondes pour newsletter 7 jours
- **Qualité sélection** : Même qualité qu'avec l'ancien système
- **Flexibilité** : Génération possible sur n'importe quelle période
- **Réactivité** : Newsletter avec données J-1 maximum

---

## 🔮 **ÉVOLUTIONS FUTURES**

### **Analytics et Intelligence**
- **Trending topics** : Détection automatique des sujets émergents
- **Competitive intelligence** : Analyse comparative des acteurs
- **Prédictions** : Modèles ML sur historique datalake
- **Alertes temps réel** : Notifications sur événements critiques

### **Extension Multi-Écosystèmes**
- **siRNA ecosystem** : Réplication pour autres domaines
- **Cross-ecosystem analytics** : Analyses transversales
- **Écosystèmes clients** : Création d'écosystèmes sur-mesure
- **Marketplace data** : Monétisation des données enrichies

### **RAG et Recherche Sémantique**
- **Knowledge base** : Datalake comme base de connaissances
- **Q&A contextuel** : Réponses sur corpus spécialisé
- **Recherche sémantique** : Au-delà des mots-clés
- **Insights automatiques** : Génération de rapports d'analyse

---

## 🎯 **PRINCIPES DE DESIGN**

### **1. Continuous Over Batch**
- Ingestion continue plutôt que runs ponctuels
- Pipeline temps réel plutôt que traitement différé
- Données toujours fraîches plutôt que snapshots

### **2. Separation of Concerns**
- Ingestion ≠ Normalisation ≠ Newsletter
- Chaque composant a une responsabilité claire
- Interfaces bien définies entre composants

### **3. Data as a Platform**
- Datalake comme asset central
- APIs pour accès aux données
- Réutilisation pour multiples cas d'usage

### **4. Configuration-Driven**
- Scheduling configurable par source
- Écosystèmes définis en configuration
- Pas de hardcoding dans le code

### **5. Evolutionary Architecture**
- Base solide pour évolutions futures
- Extensibilité native
- Migration progressive possible

---

**Architecture créée le** : 2026-04-23  
**Version** : 4.0  
**Statut** : NOUVELLE VISION - Moteur d'Ingestion Continue  
**Objectif** : Transformation Newsletter Engine → Data Platform