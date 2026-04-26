"""
Orchestrateur V3 - Pipeline complet d'ingestion
Assemble tous les modules pour exécuter le pipeline séquentiel complet.

Pipeline :
1. Générer run_id
2. Charger configs (canonical + client)
3. Résoudre sources via source_router
4. Pour chaque source : fetch → parse → rapport
5. Agréger items bruts
6. Appliquer filtres
7. Déduplication + validation
8. Écrire outputs
9. Générer run_manifest
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from .config_loader_v3 import CanonicalConfig
from .source_router import SourceRouter
from .fetcher import Fetcher
from .parser_rss import RSSParserV3
from .parser_html import HTMLParserV3
from .filter_engine import FilterEngineV3
from .models import StructuredItem, SourceReport, RunManifest, DebugReport
from ..shared.utils import generate_run_id, validate_item_v3, performance_timer, calculate_content_hash
from ..shared.s3_io import S3Manager
from ..shared.url_cache import URLCache
from ..shared.client_url_cache import ClientSpecificUrlCache

logger = logging.getLogger(__name__)


class IngestionOrchestratorV3:
    """Orchestrateur principal du pipeline d'ingestion V3"""
    
    def __init__(self, environment: str = "local"):
        self.environment = environment
        self.s3_manager = S3Manager() if environment != "local" else None
        
        # Composants du pipeline
        self.canonical_config: Optional[CanonicalConfig] = None
        self.source_router: Optional[SourceRouter] = None
        self.fetcher: Optional[Fetcher] = None
        self.filter_engine: Optional[FilterEngineV3] = None
        self.url_cache: Optional[URLCache] = None
        
        # État du run
        self.run_id: Optional[str] = None
        self.client_config: Optional[Dict[str, Any]] = None
        self.run_started_at: Optional[str] = None
        
        # Statistiques de cache
        self.cache_stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "urls_cached": 0
        }
        
        logger.info(f"IngestionOrchestrator initialized for environment: {environment}")
    
    @performance_timer
    def execute_full_pipeline(self, client_id: str, **kwargs) -> RunManifest:
        """
        Exécute le pipeline complet d'ingestion V3
        
        Args:
            client_id: ID du client (ex: lai_weekly_v3.1)
            **kwargs: Paramètres optionnels (period_days, ingestion_mode, sources, dry_run)
        
        Returns:
            RunManifest complet du run
        """
        self.run_started_at = datetime.utcnow().isoformat() + "Z"
        self.run_id = generate_run_id(client_id)
        
        logger.info(f"Starting full pipeline - run_id: {self.run_id}")
        
        try:
            # 1. Charger les configurations
            self._load_configurations(client_id, **kwargs)
            
            # 2. Initialiser les composants (avec client_id pour le cache)
            self._initialize_components(client_id)
            
            # 3. Résoudre les sources
            resolved_sources = self._resolve_sources(**kwargs)
            
            # 4. Traiter chaque source
            all_items, source_reports = self._process_all_sources(resolved_sources)
            
            # 5. Appliquer les filtres
            filtered_items, rejected_items = self._apply_filters(all_items)
            
            # 5.1. Mettre à jour les compteurs items_passed_filters dans les source_reports
            self._update_source_reports_filter_counts(source_reports, filtered_items)
            
            # 6. Déduplication et validation
            final_items = self._deduplicate_and_validate(filtered_items)
            
            # 7. Écrire les outputs STANDARDS (existant)
            output_paths = self._write_outputs(final_items, rejected_items, source_reports)
            
            # 8. NOUVEAU: Exécution des DEUX ACTIONS automatiques warehouse
            warehouse_stats = self._feed_warehouse_and_reconstitute(final_items, client_id)
            
            # 9. Générer le run_manifest (enrichi avec stats warehouse)
            run_manifest = self._generate_run_manifest(
                source_reports, final_items, rejected_items, output_paths, warehouse_stats
            )
            
            logger.info(f"Pipeline completed successfully - {len(final_items)} final items")
            return run_manifest
            
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
            # Générer un manifest d'échec
            return self._generate_failure_manifest(str(e))
    
    def _load_configurations(self, client_id: str, **kwargs):
        """Charge les configurations canonical et client"""
        logger.info("Loading configurations...")
        
        # Charger canonical config
        from .config_loader_v3 import load_from_local, load_from_s3
        
        if self.environment == "local":
            self.canonical_config = load_from_local("canonical")
        else:
            self.canonical_config = load_from_s3("vectora-config")
        
        # Charger client config
        self.client_config = self._load_client_config(client_id)
        
        # VALIDATION OBLIGATOIRE : La période DOIT être dans le client config
        period_days = self.client_config.get('ingestion', {}).get('default_period_days')
        if period_days is None:
            raise ValueError(
                f"ERREUR: Période manquante dans le client config.\n"
                f"Ajoutez dans le fichier client config :\n"
                f"  ingestion:\n"
                f"    default_period_days: <nombre_de_jours>\n"
                f"Client ID: {client_id}"
            )
        
        if not isinstance(period_days, int) or period_days <= 0:
            raise ValueError(
                f"ERREUR: Période invalide dans le client config: {period_days}\n"
                f"La valeur doit être un entier positif.\n"
                f"Client ID: {client_id}"
            )
        
        # Override avec les autres paramètres (SAUF period_days qui est interdit)
        if 'ingestion_mode' in kwargs:
            self.client_config.setdefault('ingestion', {})['ingestion_mode'] = kwargs['ingestion_mode']
        
        logger.info(f"Configurations loaded - mode: {self.client_config.get('ingestion', {}).get('ingestion_mode', 'balanced')}, period: {period_days} days")
    
    def _load_client_config(self, client_id: str) -> Dict[str, Any]:
        """Charge la configuration client"""
        if self.environment == "local":
            # Essayer d'abord client-config-examples/production/
            config_path = Path(f"client-config-examples/production/{client_id}.yaml")
            if config_path.exists():
                import yaml
                with open(config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            
            # Puis config/clients/
            config_path = Path(f"config/clients/{client_id}.yaml")
            if config_path.exists():
                import yaml
                with open(config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
        else:
            # Charger depuis S3
            if self.s3_manager:
                return self.s3_manager.load_client_config(client_id)
        
        # ERREUR : Config client non trouvée
        raise FileNotFoundError(
            f"ERREUR: Configuration client non trouvée pour '{client_id}'.\n"
            f"Vérifiez que le fichier existe dans :\n"
            f"  - client-config-examples/production/{client_id}.yaml\n"
            f"  - config/clients/{client_id}.yaml"
        )
    
    def _initialize_components(self, client_id: str):
        """Initialise tous les composants du pipeline"""
        logger.info("Initializing pipeline components...")
        
        self.source_router = SourceRouter(self.canonical_config)
        self.fetcher = Fetcher()
        self.filter_engine = FilterEngineV3(self.canonical_config, self.client_config)
        
        # Initialiser le cache URL si activé
        ingestion_config = self.client_config.get('ingestion', {})
        if ingestion_config.get('use_url_cache', False):
            # Utiliser le cache client-spécifique
            client_id = self.client_config.get('client_id') or client_id or 'unknown'
            self.url_cache = ClientSpecificUrlCache(client_id)
            # Nettoyer les entrées expirées
            self.url_cache.cleanup_expired_entries(self.client_config)
            logger.info(f"Client-specific URL cache initialized for {client_id} and cleaned")
        else:
            logger.info("URL cache disabled")
    
    def _resolve_sources(self, **kwargs) -> List:
        """Résout les sources à traiter"""
        logger.info("Resolving sources...")
        
        # Récupérer la période depuis le client config
        period_days = self.client_config.get('ingestion', {}).get('default_period_days')
        
        # Sources spécifiques ou bouquets
        if 'sources' in kwargs and kwargs['sources']:
            # Sources spécifiques passées en paramètre
            source_keys = kwargs['sources'] if isinstance(kwargs['sources'], list) else [kwargs['sources']]
            resolved_sources = self.source_router.resolve_specific_sources(source_keys, period_days)
        else:
            # Bouquets depuis client_config ou paramètres
            if 'source_bouquets' in kwargs and kwargs['source_bouquets']:
                bouquets = kwargs['source_bouquets']
            else:
                bouquets = self.client_config.get('ingestion', {}).get('source_bouquets', ['lai_full_mvp'])
            resolved_sources = self.source_router.resolve_sources_from_bouquets(bouquets, period_days)
        
        logger.info(f"Resolved {len(resolved_sources)} sources for processing")
        return resolved_sources
    
    @performance_timer
    def _process_all_sources(self, resolved_sources: List) -> Tuple[List[StructuredItem], List[SourceReport]]:
        """Traite toutes les sources résolues"""
        logger.info(f"Processing {len(resolved_sources)} sources...")
        
        all_items = []
        source_reports = []
        
        for resolved_source in resolved_sources:
            try:
                items, report = self._process_single_source(resolved_source)
                all_items.extend(items)
                source_reports.append(report)
                
                logger.info(f"Source {resolved_source.source_key}: {len(items)} items, status: {report.status}")
                
            except Exception as e:
                logger.error(f"Failed to process source {resolved_source.source_key}: {str(e)}")
                # Créer un rapport d'échec
                error_report = SourceReport(
                    source_key=resolved_source.source_key,
                    status="failed",
                    ingestion_profile_used=resolved_source.ingestion_profile,
                    items_found=0,
                    items_with_date=0,
                    items_with_content=0,
                    items_passed_filters=0,
                    avg_date_confidence=0.0,
                    fetch_time_seconds=0.0,
                    parse_time_seconds=0.0,
                    filter_time_seconds=0.0,
                    errors=[str(e)]
                )
                source_reports.append(error_report)
        
        logger.info(f"All sources processed - total items: {len(all_items)}")
        return all_items, source_reports
    
    @performance_timer
    def _process_single_source(self, resolved_source) -> Tuple[List[StructuredItem], SourceReport]:
        """Traite une source individuelle (logique simplifiée)"""
        
        logger.info(f"Processing source: {resolved_source.source_key}")
        return self._process_single_source_original(resolved_source)
    
    def _process_single_source_original(self, resolved_source) -> Tuple[List[StructuredItem], SourceReport]:
        """Traite une source individuelle (logique originale)"""
        
        # Initialiser le rapport
        report = SourceReport(
            source_key=resolved_source.source_key,
            status="success",
            ingestion_profile_used=resolved_source.ingestion_profile,
            items_found=0,
            items_with_date=0,
            items_with_content=0,
            items_passed_filters=0,
            avg_date_confidence=0.0,
            fetch_time_seconds=0.0,
            parse_time_seconds=0.0,
            filter_time_seconds=0.0
        )
        
        # Parse selon le profil
        with performance_timer() as parse_timer:
            items = self._parse_source_content(resolved_source)
        
        report.parse_time_seconds = parse_timer.duration
        report.items_found = len(items)
        
        if not items:
            report.status = "skipped"
            report.errors.append("No items found after parsing")
            return [], report
        
        # Analyser la qualité
        self._analyze_source_quality(items, report)
        
        return items, report
    
    def _create_item_cache_entry(self, item: StructuredItem) -> Dict[str, Any]:
        """Crée une entrée de cache pour un item individuel"""
        
        return {
            "status": "processed",
            "rejection_reason": None,
            "content_hash": item.content_hash or calculate_content_hash(item.content or ""),
            "source_key": item.source_key,
            "title": item.title,
            "published_at": item.published_at,
            "filter_results": {}  # Sera rempli après filtrage si nécessaire
        }
    
    def _parse_source_content(self, resolved_source) -> List[StructuredItem]:
        """Parse le contenu selon le profil de la source"""
        
        profile = resolved_source.ingestion_profile
        
        if profile in ['rss_full', 'rss_with_fetch']:
            parser = RSSParserV3(self.canonical_config, self.fetcher, self.url_cache)
            # Pour RSS, utiliser parse_rss_source qui gère le fetch en interne
            result = parser.parse_rss_source(resolved_source, self.run_id, self.client_config)
            
            # Mettre à jour les stats de cache si disponibles
            if hasattr(parser, 'cache_stats'):
                for key, value in parser.cache_stats.items():
                    self.cache_stats[key] = self.cache_stats.get(key, 0) + value
            
            return result.items if result.success else []
        
        elif profile in ['html_generic', 'html_pdf']:
            parser = HTMLParserV3(self.fetcher, self.url_cache)
            result = parser.parse_html_source(resolved_source, self.run_id, self.client_config)
            
            # Mettre à jour les stats de cache
            if hasattr(parser, 'cache_stats'):
                for key, value in parser.cache_stats.items():
                    self.cache_stats[key] = self.cache_stats.get(key, 0) + value
            
            return result.items if result.success else []
        
        else:
            logger.error(f"Unknown ingestion profile: {profile}")
            return []
    
    def _analyze_source_quality(self, items: List[StructuredItem], report: SourceReport):
        """Analyse la qualité des items d'une source"""
        
        if not items:
            return
        
        # Compter les items avec date/contenu
        items_with_date = sum(1 for item in items if item.published_at)
        items_with_content = sum(1 for item in items if item.content and len(item.content.strip()) > 100)
        
        report.items_with_date = items_with_date
        report.items_with_content = items_with_content
        
        # Calculer la confiance moyenne des dates
        date_confidences = []
        for item in items:
            if item.date_extraction and 'confidence' in item.date_extraction:
                date_confidences.append(item.date_extraction['confidence'])
        
        if date_confidences:
            report.avg_date_confidence = sum(date_confidences) / len(date_confidences)
        
        # Détecter les problèmes de qualité
        if report.avg_date_confidence < 0.6:
            report.add_quality_issue(
                "low_date_confidence",
                f"Average date confidence is low: {report.avg_date_confidence:.2f}"
            )
        
        if items_with_content / len(items) < 0.8:
            report.add_quality_issue(
                "low_content_extraction",
                f"Only {items_with_content}/{len(items)} items have substantial content"
            )
    
    @performance_timer
    def _apply_filters(self, items: List[StructuredItem]) -> Tuple[List[StructuredItem], List[StructuredItem]]:
        """Applique les filtres sur tous les items"""
        logger.info(f"Applying filters to {len(items)} items...")
        
        company_id = self.client_config.get('company_id')
        accepted_items, rejected_items = self.filter_engine.filter_items(items, company_id)
        
        logger.info(f"Filter results: {len(accepted_items)} accepted, {len(rejected_items)} rejected")
        return accepted_items, rejected_items
    
    def _deduplicate_and_validate(self, items: List[StructuredItem]) -> List[StructuredItem]:
        """Déduplication par content_hash et validation finale"""
        logger.info(f"Deduplicating and validating {len(items)} items...")
        
        # Déduplication par content_hash
        seen_hashes = set()
        deduplicated_items = []
        
        for item in items:
            if not item.content_hash:
                item.content_hash = calculate_content_hash(item.content)
            
            if item.content_hash not in seen_hashes:
                seen_hashes.add(item.content_hash)
                deduplicated_items.append(item)
        
        # Validation finale
        validated_items = []
        for item in deduplicated_items:
            if validate_item_v3(item):
                validated_items.append(item)
            else:
                logger.warning(f"Item validation failed: {item.item_id}")
        
        logger.info(f"Final items after dedup+validation: {len(validated_items)}")
        return validated_items
    
    def _update_source_reports_filter_counts(self, source_reports: List[SourceReport], filtered_items: List[StructuredItem]):
        """Met à jour les compteurs items_passed_filters dans les source_reports"""
        logger.info("Updating source reports with filter counts...")
        
        # Compter les items filtrés par source
        source_counts = {}
        for item in filtered_items:
            source_key = item.source_key
            source_counts[source_key] = source_counts.get(source_key, 0) + 1
        
        # Mettre à jour les rapports
        for report in source_reports:
            report.items_passed_filters = source_counts.get(report.source_key, 0)
            logger.debug(f"Source {report.source_key}: {report.items_passed_filters} items passed filters")
        
        logger.info(f"Updated filter counts for {len(source_reports)} source reports")
    
    def _feed_warehouse_and_reconstitute(self, final_items: List[StructuredItem], client_id: str) -> Dict[str, Any]:
        """
        Exécution séquentielle des deux actions post-run warehouse
        
        Args:
            final_items: Items ingested du run actuel (après filtres + déduplication)
            client_id: ID du client (ex: test_medincell, lai_weekly_v2.4)
        
        Returns:
            Statistiques warehouse pour le manifest
        """
        logger.info(f"Starting warehouse actions for client {client_id}")
        
        try:
            # Résoudre l'écosystème depuis watch_domains
            ecosystem = self._resolve_ecosystem(self.client_config)
            
            # ACTION 1 : Alimenter le warehouse (même si pas de nouveaux items)
            added_count = 0
            if final_items:
                added_count = self._action_1_feed_warehouse(final_items, ecosystem)
            else:
                logger.info("No new items to add to warehouse")
            
            # ACTION 2 : Reconstituer l'input complet (TOUJOURS, même si pas de nouveaux items)
            from ..warehouse import IngestedWarehouse
            warehouse = IngestedWarehouse(ecosystem)
            complete_count, input_path = self._action_2_reconstitute_input(warehouse, client_id)
            
            warehouse_stats = {
                "ecosystem": ecosystem,
                "items_added": added_count,
                "complete_items_available": complete_count,
                "normalize_input_path": input_path
            }
            
            logger.info(f"Warehouse actions completed: {added_count} added, {complete_count} available")
            return warehouse_stats
            
        except Exception as e:
            logger.error(f"Warehouse actions failed: {str(e)}", exc_info=True)
            return {
                "ecosystem": "unknown",
                "items_added": 0,
                "complete_items_available": 0,
                "normalize_input_path": None,
                "error": str(e)
            }
    
    def _resolve_ecosystem(self, client_config: Dict[str, Any]) -> str:
        """
        Résoudre l'écosystème depuis watch_domains du client
        
        Args:
            client_config: Configuration complète du client
        
        Returns:
            Nom de l'écosystème warehouse (ex: "tech_lai_ecosystem")
        """
        watch_domains = client_config.get("watch_domains", [])
        if not watch_domains:
            raise ValueError(f"No watch_domains configured for client")
        
        # Prendre le premier watch_domain comme écosystème warehouse
        ecosystem = watch_domains[0]["id"]
        
        logger.info(f"Resolved ecosystem: {ecosystem}")
        return ecosystem
    
    def _action_1_feed_warehouse(self, final_items: List[StructuredItem], ecosystem: str) -> int:
        """
        Action 1 : Alimenter le warehouse de l'écosystème
        
        Args:
            final_items: Items ingested du run actuel
            ecosystem: Nom de l'écosystème (ex: "tech_lai_ecosystem")
        
        Returns:
            Nombre d'items ajoutés (après déduplication)
        """
        from ..warehouse import IngestedWarehouse
        
        warehouse = IngestedWarehouse(ecosystem)
        
        # Ajouter avec déduplication par content_hash
        added_count = warehouse.add_items_with_deduplication(final_items, self.run_id)
        
        # Mettre à jour warehouse_stats.json
        warehouse.update_stats()
        
        logger.info(f"Warehouse {ecosystem} updated: {added_count} new items added")
        return added_count
    
    def _action_2_reconstitute_input(self, warehouse, client_id: str) -> Tuple[int, str]:
        """
        Action 2 : Reconstituer l'input complet pour normalize_score
        
        Args:
            warehouse: Instance du warehouse de l'écosystème
            client_id: ID du client pour filtrage sources et période
        
        Returns:
            (nombre_items_complets, chemin_fichier_normalize_input)
        """
        # Paramètres du client
        period_days = self.client_config["ingestion"]["default_period_days"]
        
        # Résoudre sources du client
        client_sources = self._resolve_client_sources(client_id)
        
        # Reconstituer depuis le warehouse
        complete_items = warehouse.get_items_for_client_period(
            client_sources=client_sources,
            period_days=period_days,
            reference_date=datetime.now()
        )
        
        # Écrire l'input complet pour normalize_score
        output_path = f"output/runs/{self.run_id}/normalize_input.json"
        self._write_normalize_input(complete_items, output_path)
        
        logger.info(f"Reconstitution for {client_id}:")
        logger.info(f"  - Period: {period_days} days")
        logger.info(f"  - Sources: {len(client_sources)} sources")
        logger.info(f"  - Total items: {len(complete_items)}")
        logger.info(f"  - Output: {output_path}")
        
        return len(complete_items), output_path
    
    def _resolve_client_sources(self, client_id: str) -> List[str]:
        """
        Résoudre les sources du client depuis client_mappings.json
        
        Args:
            client_id: ID du client (ex: "test_medincell")
        
        Returns:
            Liste des sources du client (ex: ["press_corporate__medincell"])
        """
        from ..warehouse import ClientMappingManager
        
        mapping_manager = ClientMappingManager()
        sources = mapping_manager.get_sources_for_client(client_id)
        
        if not sources:
            # Fallback: déduire depuis les bouquets du client_config
            bouquets = self.client_config.get('ingestion', {}).get('source_bouquets', [])
            sources = self._resolve_sources_from_bouquets(bouquets)
        
        if not sources:
            # Fallback final: sources par défaut selon le client
            sources = self._get_default_sources_for_client(client_id)
        
        logger.info(f"Client {client_id} sources: {len(sources)} sources")
        return sources
    
    def _resolve_sources_from_bouquets(self, bouquets: List[str]) -> List[str]:
        """Résoudre les sources depuis les bouquets (logique simplifiée)"""
        # Mapping bouquet → sources (adapté selon la configuration réelle)
        bouquet_mapping = {
            'test_medincell_only': ['press_corporate__medincell'],
            'lai_full_mvp': [
                'press_corporate__medincell',
                'press_corporate__camurus',
                'press_corporate__nanexa',
                'press_corporate__pfizer',
                'press_sector__fiercepharma',
                'press_sector__endpoints_news'
            ]
        }
        
        all_sources = []
        for bouquet in bouquets:
            sources = bouquet_mapping.get(bouquet, [])
            all_sources.extend(sources)
        
        return list(set(all_sources))  # Déduplication
    
    def _get_default_sources_for_client(self, client_id: str) -> List[str]:
        """Sources par défaut selon le client"""
        if 'medincell' in client_id.lower():
            return ['press_corporate__medincell']
        elif 'camurus' in client_id.lower():
            return ['press_corporate__camurus']
        elif 'nanexa' in client_id.lower():
            return ['press_corporate__nanexa']
        elif 'lai' in client_id.lower() or 'mvp' in client_id.lower():
            return [
                'press_corporate__medincell',
                'press_corporate__camurus',
                'press_corporate__nanexa',
                'press_sector__fiercepharma',
                'press_sector__endpoints_news'
            ]
        else:
            return []
    
    def _write_normalize_input(self, complete_items: List[Dict[str, Any]], output_path: str):
        """Écrire l'input complet au format attendu par normalize_score"""
        
        # Créer le dossier si nécessaire
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Écrire le fichier
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(complete_items, f, indent=2, ensure_ascii=False)
        
        logger.info(f"normalize_input.json written: {len(complete_items)} items")
    
    def _write_outputs(self, final_items: List[StructuredItem], rejected_items: List[StructuredItem], 
                      source_reports: List[SourceReport]) -> Dict[str, str]:
        """Écrit tous les fichiers de sortie"""
        logger.info("Writing output files...")
        
        output_paths = {}
        
        if self.environment == "local":
            # Écriture locale
            output_dir = Path(f"output/runs/{self.run_id}")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Items finaux
            items_path = output_dir / "ingested_items.json"
            with open(items_path, 'w', encoding='utf-8') as f:
                json.dump([item.__dict__ for item in final_items], f, indent=2, ensure_ascii=False)
            output_paths["ingested_items"] = str(items_path)
            
            # Items rejetés
            rejected_path = output_dir / "rejected_items.json"
            with open(rejected_path, 'w', encoding='utf-8') as f:
                json.dump([item.__dict__ for item in rejected_items], f, indent=2, ensure_ascii=False)
            output_paths["rejected_items"] = str(rejected_path)
            
        else:
            # Écriture S3
            client_id = self.client_config.get('client_id', 'unknown')
            
            # Items finaux
            s3_path = f"ingested/{client_id}/{self.run_id}/items_filtered.json"
            self.s3_manager.write_json(s3_path, [item.__dict__ for item in final_items])
            output_paths["ingested_items"] = s3_path
            
            # Items rejetés
            rejected_s3_path = f"ingested/{client_id}/{self.run_id}/rejected_items.json"
            self.s3_manager.write_json(rejected_s3_path, [item.__dict__ for item in rejected_items])
            output_paths["rejected_items"] = rejected_s3_path
        
        logger.info(f"Output files written: {list(output_paths.keys())}")
        return output_paths
    
    def _generate_run_manifest(self, source_reports: List[SourceReport], final_items: List[StructuredItem],
                              rejected_items: List[StructuredItem], output_paths: Dict[str, str], 
                              warehouse_stats: Dict[str, Any] = None) -> RunManifest:
        """Génère le run_manifest complet avec le reporter enrichi"""
        
        from .enhanced_run_reporter import EnhancedRunReporter
        
        reporter = EnhancedRunReporter(
            run_id=self.run_id,
            client_config=self.client_config,
            run_started_at=self.run_started_at
        )
        
        # Générer le manifest enrichi
        enhanced_manifest = reporter.generate_enhanced_manifest(
            source_reports=source_reports,
            final_items=final_items,
            rejected_items=rejected_items,
            output_paths=output_paths
        )
        
        # Ajouter les statistiques de cache avec information sur l'état du cache
        if hasattr(self, 'cache_stats'):
            enhanced_manifest.cache_stats = self.cache_stats
            # Ajouter l'information sur l'état réel du cache
            enhanced_manifest.cache_stats['cache_configured'] = self.url_cache is not None
        
        # NOUVEAU: Ajouter les statistiques warehouse
        if warehouse_stats:
            enhanced_manifest.warehouse_stats = warehouse_stats
            # Ajouter normalize_input_path dans les outputs
            if warehouse_stats.get("normalize_input_path"):
                output_paths["normalize_input"] = warehouse_stats["normalize_input_path"]
        
        # Écrire les outputs enrichis (debug report amélioré inclus)
        if self.environment == "local":
            output_dir = Path(f"output/runs/{self.run_id}")
            output_dir.mkdir(parents=True, exist_ok=True)
            enhanced_output_paths = reporter.write_enhanced_outputs(
                enhanced_manifest, final_items, rejected_items, output_dir
            )
            # Fusionner les chemins
            output_paths.update(enhanced_output_paths)
        
        return enhanced_manifest
    
    def _generate_failure_manifest(self, error_message: str) -> RunManifest:
        """Génère un manifest en cas d'échec du pipeline"""
        
        return RunManifest(
            run_id=self.run_id or "unknown",
            client_id=self.client_config.get('client_id', 'unknown') if self.client_config else "unknown",
            run_date=datetime.utcnow().strftime('%Y-%m-%d'),
            run_started_at=self.run_started_at or datetime.utcnow().isoformat() + "Z",
            run_completed_at=datetime.utcnow().isoformat() + "Z",
            period_days=0,
            ingestion_mode="unknown",
            from_date="",
            to_date="",
            s3_paths={},
            source_reports=[],
            stats={"error": error_message},
            status="failed",
            human_summary=f"Pipeline failed: {error_message}"
        )


# Fonction d'entrée principale pour les tests
def run_ingestion_v3(client_id: str, run_id: str = None, client_config_path: str = None,
                     canonical_base_path: str = "canonical", local_mode: bool = True,
                     config_overrides: Dict[str, Any] = None, source_bouquets: List[str] = None,
                     specific_sources: List[str] = None, **kwargs) -> Dict[str, Any]:
    """
    Point d'entrée principal pour l'ingestion V3
    
    Args:
        client_id: ID du client
        run_id: ID du run (généré automatiquement si non fourni)
        client_config_path: Chemin vers le config client
        canonical_base_path: Chemin vers les fichiers canonical
        local_mode: Mode local (True) ou AWS (False)
        config_overrides: Overrides de configuration
        source_bouquets: Bouquets de sources spécifiques
        specific_sources: Sources spécifiques à traiter
        **kwargs: Autres paramètres
    
    Returns:
        Dict avec status, run_manifest, et autres métadonnées
    """
    
    try:
        # Initialiser l'orchestrateur
        environment = "local" if local_mode else "aws"
        orchestrator = IngestionOrchestratorV3(environment=environment)
        
        # Préparer les paramètres
        params = {
            "client_id": client_id
        }
        
        # Ajouter les paramètres optionnels
        if config_overrides:
            params.update(config_overrides.get("ingestion", {}))
        
        if source_bouquets:
            params["source_bouquets"] = source_bouquets
        
        if specific_sources:
            params["sources"] = specific_sources
        
        # Ajouter les autres kwargs
        params.update(kwargs)
        
        # Exécuter le pipeline
        run_manifest = orchestrator.execute_full_pipeline(**params)
        
        # Retourner le résultat
        return {
            "status": "success" if run_manifest.status != "failed" else "failed",
            "run_manifest": run_manifest.__dict__,
            "run_id": run_manifest.run_id,
            "total_items": len(run_manifest.source_reports) if run_manifest.source_reports else 0
        }
        
    except Exception as e:
        logger.error(f"run_ingestion_v3 failed: {str(e)}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "run_id": run_id or "unknown"
        }