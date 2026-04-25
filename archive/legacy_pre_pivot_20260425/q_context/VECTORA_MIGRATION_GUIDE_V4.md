# Guide de Transition : Newsletter Engine → Ingestion Engine

**Version**: 4.0  
**Date**: 2026-04-23  
**Objectif**: Guide pratique pour migrer vers l'architecture d'ingestion continue  
**Audience**: Développeurs et AI assistants

---

## 🎯 **COMPRÉHENSION DE LA TRANSITION**

### **Changement de Paradigme Fondamental**

#### **AVANT : Run-Based Newsletter Workflow**
```
1. Client demande newsletter sur période X
2. Moteur ingère TOUTES les sources pour période X
3. Normalise + Score + Sélectionne
4. Génère newsletter
5. FIN (données perdues)
```

**Problèmes identifiés :**
- Surcharge moteur pour périodes longues (200 jours)
- Re-ingestion inutile des mêmes données
- Pas de réutilisation entre clients
- Workflow séquentiel lourd

#### **APRÈS : Continuous Ingestion + Data Platform**
```
1. Sources ingérées automatiquement (schedule)
2. Warehouse alimenté en continu
3. Pipeline normalisation automatique → Datalake
4. Newsletter = Query datalake + Sélection + Rédaction
5. Données persistantes et réutilisables
```

**Avantages obtenus :**
- Moteur jamais surchargé (une source à la fois)
- Données toujours disponibles
- Newsletter générée en < 30 secondes
- Base pour évolutions futures (RAG, analytics)

---

## 🏗️ **ARCHITECTURE EXISTANTE À RÉUTILISER**

### **Composants V3 Conservés**

#### **1. Moteur d'Ingestion V3** (`src_v3/vectora_core/ingest/`)
```python
# RÉUTILISÉ AVEC ADAPTATION
IngestionOrchestratorV3  → ContinuousIngestionEngine
SourceRouter            → SingleSourceProcessor  
FilterEngineV3          → (inchangé)
RSSParserV3            → (inchangé)
HTMLParserV3           → (inchangé)
```

#### **2. Système Warehouse** (`src_v3/vectora_core/warehouse/`)
```python
# ÉTENDU POUR INGESTION CONTINUE
IngestedWarehouse       → ContinuousWarehouse
ClientMappingManager    → EcosystemMappingManager
DeduplicationManager    → (inchangé)
```

#### **3. Moteur de Normalisation** (`src_v3/vectora_core/normalization/`)
```python
# ADAPTÉ POUR TRAITEMENT BATCH
BedrockNormalizer       → BatchNormalizer
DomainScorer           → (inchangé)
```

#### **4. Configuration Canonical** (`canonical/`)
```yaml
# ÉTENDU AVEC NOUVEAUX CONCEPTS
sources/               → + continuous_sources_config.yaml
ingestion/            → + scheduling_config.yaml
scopes/               → (inchangé)
prompts/              → (inchangé)
```

### **Nouveaux Composants à Créer**

#### **1. Scheduler d'Ingestion Continue**
```python
# NOUVEAU : src_v3/vectora_core/continuous/scheduler.py
class ContinuousIngestionScheduler:
    """Gère l'ingestion automatique des sources"""
    
    def __init__(self, ecosystem_config):
        self.ecosystem = ecosystem_config
        self.warehouse = ContinuousWarehouse(ecosystem_config.ecosystem_id)
        self.ingestion_engine = ContinuousIngestionEngine()
    
    def run_daily_cycle(self):
        """Cycle quotidien d'ingestion"""
        sources_today = self.get_scheduled_sources_for_today()
        
        for source in sources_today:
            try:
                # Utilise le moteur V3 existant pour une seule source
                items = self.ingestion_engine.process_single_source(source)
                self.warehouse.store_items(source.source_key, items)
                self.log_success(source, len(items))
            except Exception as e:
                self.log_error(source, e)
                self.schedule_retry(source)
```

#### **2. Pipeline de Normalisation Automatique**
```python
# NOUVEAU : src_v3/vectora_core/continuous/normalization_pipeline.py
class AutoNormalizationPipeline:
    """Pipeline automatique warehouse → datalake"""
    
    def __init__(self, ecosystem_config):
        self.ecosystem = ecosystem_config
        self.warehouse = ContinuousWarehouse(ecosystem_config.ecosystem_id)
        self.normalizer = BatchNormalizer()  # Adapté du moteur V3
        self.datalake = NormalizedDatalake(ecosystem_config.ecosystem_id)
    
    def run_normalization_cycle(self):
        """Cycle de normalisation (toutes les 6h)"""
        # 1. Détecter nouveaux items dans warehouse
        new_items = self.warehouse.get_unnormalized_items()
        
        if not new_items:
            return
        
        # 2. Normaliser par batch
        for batch in self.create_batches(new_items, batch_size=50):
            normalized_batch = self.normalizer.normalize_batch(batch)
            self.datalake.store_normalized_items(normalized_batch)
            self.warehouse.mark_as_normalized(batch)
```

#### **3. API de Query Datalake**
```python
# NOUVEAU : src_v3/vectora_core/datalake/query_api.py
class DatalakeQueryAPI:
    """API pour requêter le datalake normalisé"""
    
    def __init__(self, ecosystem_id):
        self.ecosystem_id = ecosystem_id
        self.datalake = NormalizedDatalake(ecosystem_id)
    
    def query_for_newsletter(self, client_config, period_days=7):
        """Query optimisée pour génération newsletter"""
        return self.datalake.query_items(
            period_days=period_days,
            watch_domains=client_config.watch_domains,
            min_score=client_config.newsletter_selection.min_domain_score,
            max_items=client_config.newsletter_selection.max_items_total
        )
```

#### **4. Générateur Newsletter V4**
```python
# NOUVEAU : src_v3/vectora_core/newsletter/generator_v4.py
class NewsletterGeneratorV4:
    """Générateur newsletter basé sur datalake"""
    
    def __init__(self, ecosystem_id):
        self.query_api = DatalakeQueryAPI(ecosystem_id)
        self.selector = NewsletterSelector()  # Réutilise V3
        self.editor = NewsletterEditor()      # Réutilise V3
    
    def generate_newsletter(self, client_config):
        """Génère newsletter en queryant le datalake"""
        # 1. Query datalake (rapide)
        items = self.query_api.query_for_newsletter(client_config)
        
        # 2. Sélection finale (réutilise logique V3)
        selected_items = self.selector.select_items(items, client_config)
        
        # 3. Rédaction (réutilise logique V3)
        newsletter = self.editor.generate_newsletter(selected_items, client_config)
        
        return newsletter
```

---

## 📁 **NOUVELLE STRUCTURE DE FICHIERS**

### **Extension de src_v3/**
```
src_v3/vectora_core/
├── ingest/                    # EXISTANT - Adapté
│   ├── __init__.py           # IngestionOrchestratorV3 → ContinuousIngestionEngine
│   ├── source_router.py      # Adapté pour source unique
│   ├── filter_engine.py      # Inchangé
│   └── ...
├── warehouse/                 # EXISTANT - Étendu
│   ├── __init__.py           # Étendu pour ingestion continue
│   ├── ingested_warehouse.py # Adapté pour continuous
│   └── ...
├── normalization/            # EXISTANT - Adapté
│   ├── __init__.py          # Étendu pour traitement batch
│   ├── normalizer.py        # BatchNormalizer
│   └── ...
├── newsletter/               # EXISTANT - Étendu
│   ├── __init__.py          # Inchangé
│   ├── generator_v4.py      # NOUVEAU - Basé sur datalake
│   └── ...
├── continuous/               # NOUVEAU - Composants continus
│   ├── __init__.py
│   ├── scheduler.py         # Scheduler ingestion
│   ├── normalization_pipeline.py
│   └── ecosystem_manager.py
├── datalake/                 # NOUVEAU - Gestion datalake
│   ├── __init__.py
│   ├── query_api.py         # API de requête
│   ├── normalized_storage.py
│   └── indexing.py
└── shared/                   # EXISTANT - Inchangé
    └── ...
```

### **Extension de canonical/**
```
canonical/
├── sources/                  # EXISTANT - Étendu
│   ├── source_catalog_v3.yaml        # Existant
│   ├── source_configs_v3.yaml        # Existant
│   └── continuous_sources_config.yaml # NOUVEAU
├── ingestion/               # EXISTANT - Étendu
│   ├── ingestion_profiles_v3.yaml    # Existant
│   ├── filter_rules_v3.yaml          # Existant
│   └── scheduling_config.yaml        # NOUVEAU
├── ecosystems/              # NOUVEAU - Définitions écosystèmes
│   ├── tech_lai_ecosystem.yaml
│   ├── sirna_ecosystem.yaml
│   └── ecosystem_templates.yaml
├── scopes/                  # EXISTANT - Inchangé
├── prompts/                 # EXISTANT - Inchangé
└── datalake/               # NOUVEAU - Schémas datalake
    ├── schema_definitions.yaml
    └── index_configurations.yaml
```

### **Extension de data/**
```
data/
├── warehouse/               # EXISTANT - Étendu
│   ├── ingested/           # Structure existante
│   └── continuous/         # NOUVEAU - Données continues
│       ├── schedules.json
│       ├── processing_queue.jsonl
│       └── stats/
├── datalake/               # NOUVEAU - Datalake normalisé
│   ├── normalized/
│   │   └── tech_lai_ecosystem/
│   │       ├── 2026/04/
│   │       └── indexes/
│   └── config/
└── cache/                  # EXISTANT - Inchangé
```

---

## 🔧 **ÉTAPES DE MIGRATION PRATIQUES**

### **Phase 1 : Préparation Infrastructure (Semaine 1)**

#### **Étape 1.1 : Créer les nouveaux modules**
```bash
# Créer la structure continuous/
mkdir -p src_v3/vectora_core/continuous
touch src_v3/vectora_core/continuous/__init__.py
touch src_v3/vectora_core/continuous/scheduler.py
touch src_v3/vectora_core/continuous/normalization_pipeline.py

# Créer la structure datalake/
mkdir -p src_v3/vectora_core/datalake
touch src_v3/vectora_core/datalake/__init__.py
touch src_v3/vectora_core/datalake/query_api.py

# Créer la structure ecosystems/
mkdir -p canonical/ecosystems
touch canonical/ecosystems/tech_lai_ecosystem.yaml
```

#### **Étape 1.2 : Adapter le warehouse existant**
```python
# Modifier src_v3/vectora_core/warehouse/ingested_warehouse.py
class IngestedWarehouse:
    # Ajouter méthodes pour ingestion continue
    def store_continuous_items(self, source_key: str, items: List[Dict]):
        """Stockage pour ingestion continue"""
        pass
    
    def get_unnormalized_items(self, limit: int = 1000):
        """Récupère items pas encore normalisés"""
        pass
    
    def mark_as_normalized(self, items: List[Dict]):
        """Marque items comme normalisés"""
        pass
```

#### **Étape 1.3 : Configuration écosystème pilote**
```yaml
# canonical/ecosystems/tech_lai_ecosystem.yaml
ecosystem_id: tech_lai_ecosystem
description: "Écosystème technologique Long-Acting Injectables"

continuous_ingestion:
  enabled: true
  sources:
    - source_key: press_corporate__medincell
      schedule: every_3_days
      priority: high
    - source_key: press_sector__fiercebiotech  
      schedule: daily
      priority: medium

warehouse:
  retention_days: 730
  max_items: 100000

datalake:
  normalization_schedule: every_6_hours
  index_update_frequency: real_time
```

### **Phase 2 : Implémentation Scheduler (Semaine 2)**

#### **Étape 2.1 : Créer le scheduler de base**
```python
# src_v3/vectora_core/continuous/scheduler.py
class ContinuousIngestionScheduler:
    def __init__(self, ecosystem_config_path: str):
        self.config = self.load_ecosystem_config(ecosystem_config_path)
        self.warehouse = IngestedWarehouse(self.config.ecosystem_id)
        # Réutilise le moteur V3 existant
        self.ingestion_engine = IngestionOrchestratorV3()
    
    def get_sources_for_today(self) -> List[Dict]:
        """Détermine quelles sources traiter aujourd'hui"""
        # Logique de scheduling basée sur config
        pass
    
    def process_single_source(self, source_config: Dict):
        """Traite une seule source (adaptation du moteur V3)"""
        # Utilise IngestionOrchestratorV3 mais pour une seule source
        pass
```

#### **Étape 2.2 : Script de test scheduler**
```python
# scripts/continuous/test_scheduler.py
def test_scheduler():
    scheduler = ContinuousIngestionScheduler("canonical/ecosystems/tech_lai_ecosystem.yaml")
    
    # Test avec une source pilote
    sources_today = scheduler.get_sources_for_today()
    print(f"Sources à traiter aujourd'hui: {len(sources_today)}")
    
    for source in sources_today[:1]:  # Test avec une seule source
        items = scheduler.process_single_source(source)
        print(f"Source {source['source_key']}: {len(items)} items ingérés")

if __name__ == "__main__":
    test_scheduler()
```

### **Phase 3 : Pipeline Normalisation (Semaine 3)**

#### **Étape 3.1 : Adapter le moteur de normalisation**
```python
# src_v3/vectora_core/continuous/normalization_pipeline.py
class AutoNormalizationPipeline:
    def __init__(self, ecosystem_id: str):
        self.ecosystem_id = ecosystem_id
        self.warehouse = IngestedWarehouse(ecosystem_id)
        # Réutilise le normalizer V3 existant
        from ..normalization import BedrockNormalizer
        self.normalizer = BedrockNormalizer()
    
    def run_normalization_cycle(self):
        """Cycle de normalisation automatique"""
        new_items = self.warehouse.get_unnormalized_items(limit=100)
        
        if not new_items:
            print("Pas de nouveaux items à normaliser")
            return
        
        # Normalise par batch (réutilise logique V3)
        normalized_items = []
        for batch in self.create_batches(new_items, 10):
            batch_normalized = self.normalizer.normalize_items(batch)
            normalized_items.extend(batch_normalized)
        
        # Stocke dans datalake
        self.store_to_datalake(normalized_items)
        self.warehouse.mark_as_normalized(new_items)
```

#### **Étape 3.2 : Créer le stockage datalake**
```python
# src_v3/vectora_core/datalake/normalized_storage.py
class NormalizedDatalake:
    def __init__(self, ecosystem_id: str):
        self.ecosystem_id = ecosystem_id
        self.base_path = Path(f"data/datalake/normalized/{ecosystem_id}")
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def store_normalized_items(self, items: List[Dict]):
        """Stocke items normalisés avec indexation"""
        # Stockage par date + mise à jour index
        pass
    
    def query_items(self, **filters) -> List[Dict]:
        """Query avec filtres"""
        # Implémentation query optimisée
        pass
```

### **Phase 4 : API Newsletter V4 (Semaine 4)**

#### **Étape 4.1 : Créer l'API de query**
```python
# src_v3/vectora_core/datalake/query_api.py
class DatalakeQueryAPI:
    def __init__(self, ecosystem_id: str):
        self.datalake = NormalizedDatalake(ecosystem_id)
    
    def query_for_newsletter(self, client_config: Dict, period_days: int = 7):
        """Query optimisée pour newsletter"""
        return self.datalake.query_items(
            period_days=period_days,
            watch_domains=client_config.get('watch_domains', []),
            min_score=client_config.get('newsletter_selection', {}).get('min_domain_score', 0)
        )
```

#### **Étape 4.2 : Adapter le générateur newsletter**
```python
# src_v3/vectora_core/newsletter/generator_v4.py
class NewsletterGeneratorV4:
    def __init__(self, ecosystem_id: str):
        self.query_api = DatalakeQueryAPI(ecosystem_id)
        # Réutilise les composants V3 existants
        from . import NewsletterSelector, NewsletterEditor
        self.selector = NewsletterSelector()
        self.editor = NewsletterEditor()
    
    def generate_newsletter(self, client_config: Dict):
        """Génération rapide basée sur datalake"""
        # 1. Query datalake (< 5 secondes)
        items = self.query_api.query_for_newsletter(client_config)
        
        # 2. Sélection (réutilise logique V3)
        selected = self.selector.select_items(items, client_config)
        
        # 3. Rédaction (réutilise logique V3)
        newsletter = self.editor.generate_newsletter(selected, client_config)
        
        return newsletter
```

### **Phase 5 : Scripts d'Orchestration (Semaine 5)**

#### **Étape 5.1 : Script de run continu**
```python
# scripts/continuous/run_continuous_ingestion.py
def main():
    """Script principal pour ingestion continue"""
    
    # 1. Cycle d'ingestion quotidien
    scheduler = ContinuousIngestionScheduler("canonical/ecosystems/tech_lai_ecosystem.yaml")
    scheduler.run_daily_cycle()
    
    # 2. Cycle de normalisation (si nécessaire)
    pipeline = AutoNormalizationPipeline("tech_lai_ecosystem")
    pipeline.run_normalization_cycle()
    
    print("Cycle d'ingestion continue terminé")

if __name__ == "__main__":
    main()
```

#### **Étape 5.2 : Script de génération newsletter V4**
```python
# scripts/newsletter/generate_newsletter_v4.py
def generate_newsletter_v4(client_id: str):
    """Génère newsletter avec nouvelle architecture"""
    
    # 1. Charger config client
    client_config = load_client_config(client_id)
    
    # 2. Générer newsletter (rapide)
    generator = NewsletterGeneratorV4("tech_lai_ecosystem")
    newsletter = generator.generate_newsletter(client_config)
    
    # 3. Sauvegarder
    output_path = f"output/newsletters_v4/{client_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    save_newsletter(newsletter, output_path)
    
    print(f"Newsletter générée: {output_path}")

if __name__ == "__main__":
    import sys
    generate_newsletter_v4(sys.argv[1])
```

---

## 🧪 **TESTS ET VALIDATION**

### **Tests de Migration Progressive**

#### **Test 1 : Ingestion Continue Pilote**
```bash
# Test avec une seule source
python scripts/continuous/test_scheduler.py

# Vérifier warehouse
ls data/warehouse/ingested/profiles/tech_lai_ecosystem/

# Vérifier logs
tail -f logs/continuous_ingestion.log
```

#### **Test 2 : Pipeline Normalisation**
```bash
# Déclencher normalisation manuelle
python scripts/continuous/test_normalization.py

# Vérifier datalake
ls data/datalake/normalized/tech_lai_ecosystem/

# Comparer avec V3
python scripts/validation/compare_v3_v4_normalization.py
```

#### **Test 3 : Newsletter V4 vs V3**
```bash
# Générer newsletter V4
python scripts/newsletter/generate_newsletter_v4.py mvp_test_30days

# Générer newsletter V3 (référence)
python scripts/ingestion/run_ingestion.py mvp_test_30days

# Comparer résultats
python scripts/validation/compare_v3_v4_newsletters.py
```

### **Métriques de Validation**

#### **Performance**
- **Temps ingestion source** : < 2 minutes (vs 10-30 min pour run complet V3)
- **Temps génération newsletter** : < 30 secondes (vs 5-15 min V3)
- **Utilisation mémoire** : < 1GB (vs 2-4GB pour runs longs V3)

#### **Qualité**
- **Nombre items identiques** : > 95% entre V3 et V4
- **Scores identiques** : > 90% (petites variations acceptables)
- **Sélection newsletter** : > 90% items identiques

#### **Fiabilité**
- **Taux succès ingestion** : > 95%
- **Taux succès normalisation** : > 98%
- **Cohérence datalake** : 100% (pas de corruption)

---

## 📋 **CHECKLIST DE MIGRATION**

### **Préparatifs**
- [ ] Backup complet de l'existant
- [ ] Tests V3 de référence exécutés
- [ ] Environnement de développement préparé
- [ ] Documentation V3 comprise

### **Phase 1 : Infrastructure**
- [ ] Modules continuous/ créés
- [ ] Modules datalake/ créés
- [ ] Configuration écosystème tech_lai_ecosystem
- [ ] Warehouse adapté pour ingestion continue

### **Phase 2 : Scheduler**
- [ ] ContinuousIngestionScheduler implémenté
- [ ] Test avec source pilote réussi
- [ ] Logs et monitoring en place
- [ ] Gestion d'erreurs implémentée

### **Phase 3 : Normalisation**
- [ ] AutoNormalizationPipeline implémenté
- [ ] NormalizedDatalake créé
- [ ] Tests de normalisation batch réussis
- [ ] Index datalake fonctionnels

### **Phase 4 : Newsletter V4**
- [ ] DatalakeQueryAPI implémenté
- [ ] NewsletterGeneratorV4 créé
- [ ] Tests de génération rapide réussis
- [ ] Comparaison V3/V4 validée

### **Phase 5 : Production**
- [ ] Scripts d'orchestration créés
- [ ] Monitoring et alertes configurés
- [ ] Documentation utilisateur mise à jour
- [ ] Migration clients existants

### **Validation Finale**
- [ ] Tous les tests passent
- [ ] Performance conforme aux objectifs
- [ ] Qualité équivalente à V3
- [ ] Prêt pour déploiement production

---

## 🎯 **POINTS D'ATTENTION**

### **Risques Identifiés**
1. **Complexité migration** : Beaucoup de composants à adapter
2. **Régression qualité** : Risque de différences V3/V4
3. **Performance datalake** : Queries lentes si mal optimisées
4. **Gestion erreurs** : Pipeline continu doit être robuste

### **Mitigations**
1. **Migration progressive** : Phase par phase avec validation
2. **Tests comparatifs** : V3 comme référence de qualité
3. **Optimisation index** : Design datalake pour performance
4. **Monitoring complet** : Alertes sur tous les composants

### **Critères de Succès**
- ✅ Newsletter générée en < 30 secondes
- ✅ Qualité équivalente à V3
- ✅ Ingestion continue stable
- ✅ Base solide pour évolutions futures

---

**Guide créé le** : 2026-04-23  
**Version** : 4.0  
**Statut** : GUIDE DE MIGRATION - Architecture Ingestion Continue  
**Objectif** : Transformation pratique Newsletter Engine → Data Platform