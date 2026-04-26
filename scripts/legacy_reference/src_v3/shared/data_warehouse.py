#!/usr/bin/env python3
"""
Système de Data Warehouse pour Vectora Inbox
Gestion intelligente du stockage et retrieval des données d'ingestion
"""

import json
import jsonlines
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import hashlib
import logging

logger = logging.getLogger(__name__)

@dataclass
class QueryFilter:
    """Filtre pour les requêtes de données"""
    companies: Optional[List[str]] = None
    sources: Optional[List[str]] = None
    source_types: Optional[List[str]] = None
    clients: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    status: Optional[str] = None  # 'ingested' or 'rejected'
    limit: Optional[int] = None

class DataWarehouse:
    """Gestionnaire du Data Warehouse Vectora"""
    
    def __init__(self, base_path: str = "data/warehouse"):
        self.base_path = Path(base_path)
        self.ingested_path = self.base_path / "ingested"
        self.rejected_path = self.base_path / "rejected"
        self.metadata_path = self.base_path / "metadata"
        self.indexes_path = Path("data/indexes")
        
        # Créer les dossiers si nécessaire
        self._ensure_directories()
        
    def _ensure_directories(self):
        """Crée la structure de dossiers nécessaire"""
        directories = [
            self.ingested_path / "by_date",
            self.ingested_path / "by_source" / "corporate",
            self.ingested_path / "by_source" / "press",
            self.ingested_path / "by_company",
            self.ingested_path / "by_client",
            self.rejected_path / "by_reason",
            self.rejected_path / "by_date",
            self.rejected_path / "by_source",
            self.metadata_path,
            self.indexes_path
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def store_run_results(self, run_id: str, ingested_items: List[Dict], 
                         rejected_items: List[Dict], client_id: str):
        """
        Stocke les résultats d'un run dans le warehouse
        """
        logger.info(f"Stockage des résultats du run {run_id}")
        
        # Traiter les items ingérés
        for item in ingested_items:
            self._store_item(item, "ingested", run_id, client_id)
        
        # Traiter les items rejetés
        for item in rejected_items:
            self._store_item(item, "rejected", run_id, client_id)
        
        # Mettre à jour les métadonnées
        self._update_run_metadata(run_id, len(ingested_items), len(rejected_items), client_id)
        
        # Mettre à jour les index
        self._update_indexes()
        
        logger.info(f"Stockage terminé: {len(ingested_items)} ingérés, {len(rejected_items)} rejetés")
    
    def _store_item(self, item: Dict, status: str, run_id: str, client_id: str):
        """Stocke un item individuel dans toutes les structures nécessaires"""
        
        # Enrichir l'item avec les métadonnées
        enriched_item = self._enrich_item(item, status, run_id, client_id)
        
        # Déterminer les chemins de stockage
        pub_date = self._parse_date(item.get('publication_date'))
        source_key = item.get('source_key', 'unknown')
        company_id = item.get('company_id')
        
        base_path = self.ingested_path if status == "ingested" else self.rejected_path
        
        # 1. Stockage par date
        if pub_date:
            date_path = base_path / "by_date" / str(pub_date.year) / f"{pub_date.month:02d}"
            date_path.mkdir(parents=True, exist_ok=True)
            date_file = date_path / f"{source_key}_{pub_date.strftime('%Y%m%d')}.jsonl"
            self._append_to_jsonl(date_file, enriched_item)
        
        # 2. Stockage par source
        source_type = item.get('source_type', 'unknown')
        source_category = "corporate" if "corporate" in source_type else "press"
        source_path = base_path / "by_source" / source_category
        source_file = source_path / f"{source_key}.jsonl"
        self._append_to_jsonl(source_file, enriched_item)
        
        # 3. Stockage par company (si applicable)
        if company_id:
            company_path = base_path / "by_company"
            company_file = company_path / f"{company_id}.jsonl"
            self._append_to_jsonl(company_file, enriched_item)
        
        # 4. Stockage par client
        client_path = base_path / "by_client" / client_id
        client_path.mkdir(parents=True, exist_ok=True)
        
        # Organiser par trimestre pour éviter des fichiers trop gros
        if pub_date:
            quarter = f"{pub_date.year}_Q{(pub_date.month-1)//3 + 1}"
            client_file = client_path / f"{quarter}.jsonl"
            self._append_to_jsonl(client_file, enriched_item)
        
        # 5. Stockage par raison de rejet (si rejeté)
        if status == "rejected":
            filter_analysis = item.get('filter_analysis', {})
            for filter_name, filter_data in filter_analysis.items():
                if isinstance(filter_data, dict) and not filter_data.get('passed', True):
                    reason = filter_data.get('reason', 'unknown')
                    reason_path = self.rejected_path / "by_reason" / filter_name
                    reason_path.mkdir(parents=True, exist_ok=True)
                    reason_file = reason_path / f"{reason}.jsonl"
                    self._append_to_jsonl(reason_file, enriched_item)
    
    def _enrich_item(self, item: Dict, status: str, run_id: str, client_id: str) -> Dict:
        """Enrichit un item avec les métadonnées nécessaires"""
        enriched = item.copy()
        
        # Générer un ID unique si pas présent
        if 'item_id' not in enriched:
            content_hash = hashlib.sha256(
                (item.get('url', '') + item.get('title', '')).encode()
            ).hexdigest()[:12]
            enriched['item_id'] = f"{item.get('source_key', 'unknown')}_{content_hash}"
        
        # Ajouter les métadonnées de run
        enriched.update({
            'run_id': run_id,
            'ingestion_date': datetime.now().isoformat(),
            'client_id': client_id,
            'status': status,
            'warehouse_version': '1.0'
        })
        
        return enriched
    
    def _append_to_jsonl(self, file_path: Path, item: Dict):
        """Ajoute un item à un fichier JSONL"""
        with jsonlines.open(file_path, mode='a') as writer:
            writer.write(item)
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse une date string en datetime"""
        if not date_str:
            return None
        
        try:
            # Essayer plusieurs formats
            formats = [
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            return None
        except Exception:
            return None
    
    def query(self, filter_obj: QueryFilter) -> List[Dict]:
        """
        Requête intelligente sur le warehouse
        """
        results = []
        
        # Déterminer les fichiers à scanner selon les filtres
        files_to_scan = self._get_relevant_files(filter_obj)
        
        for file_path in files_to_scan:
            if not file_path.exists():
                continue
                
            with jsonlines.open(file_path) as reader:
                for item in reader:
                    if self._matches_filter(item, filter_obj):
                        results.append(item)
                        
                        # Appliquer la limite si spécifiée
                        if filter_obj.limit and len(results) >= filter_obj.limit:
                            return results
        
        return results
    
    def _get_relevant_files(self, filter_obj: QueryFilter) -> List[Path]:
        """Détermine les fichiers les plus pertinents à scanner selon les filtres"""
        files = []
        
        # Stratégie de sélection des fichiers selon les filtres
        if filter_obj.companies:
            # Scan par company est le plus efficace
            base_path = self.ingested_path if filter_obj.status != "rejected" else self.rejected_path
            for company in filter_obj.companies:
                company_file = base_path / "by_company" / f"{company}.jsonl"
                if company_file.exists():
                    files.append(company_file)
        
        elif filter_obj.sources:
            # Scan par source
            base_path = self.ingested_path if filter_obj.status != "rejected" else self.rejected_path
            for source in filter_obj.sources:
                # Chercher dans corporate et press
                for category in ["corporate", "press"]:
                    source_file = base_path / "by_source" / category / f"{source}.jsonl"
                    if source_file.exists():
                        files.append(source_file)
        
        elif filter_obj.date_from or filter_obj.date_to:
            # Scan par date - plus complexe mais efficace pour les requêtes temporelles
            files.extend(self._get_date_range_files(filter_obj))
        
        else:
            # Scan général - moins efficace mais nécessaire
            base_path = self.ingested_path if filter_obj.status != "rejected" else self.rejected_path
            files.extend(base_path.rglob("*.jsonl"))
        
        return files
    
    def _get_date_range_files(self, filter_obj: QueryFilter) -> List[Path]:
        """Récupère les fichiers dans une plage de dates"""
        files = []
        base_path = self.ingested_path if filter_obj.status != "rejected" else self.rejected_path
        date_path = base_path / "by_date"
        
        if not date_path.exists():
            return files
        
        # Déterminer la plage d'années et mois à scanner
        start_date = filter_obj.date_from or datetime(2020, 1, 1)
        end_date = filter_obj.date_to or datetime.now()
        
        current = start_date.replace(day=1)
        while current <= end_date:
            month_path = date_path / str(current.year) / f"{current.month:02d}"
            if month_path.exists():
                files.extend(month_path.glob("*.jsonl"))
            
            # Passer au mois suivant
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
        
        return files
    
    def _matches_filter(self, item: Dict, filter_obj: QueryFilter) -> bool:
        """Vérifie si un item correspond aux filtres"""
        
        # Filtre par companies
        if filter_obj.companies:
            if item.get('company_id') not in filter_obj.companies:
                return False
        
        # Filtre par sources
        if filter_obj.sources:
            if item.get('source_key') not in filter_obj.sources:
                return False
        
        # Filtre par type de source
        if filter_obj.source_types:
            if item.get('source_type') not in filter_obj.source_types:
                return False
        
        # Filtre par clients
        if filter_obj.clients:
            if item.get('client_id') not in filter_obj.clients:
                return False
        
        # Filtre par status
        if filter_obj.status:
            if item.get('status') != filter_obj.status:
                return False
        
        # Filtre par date
        if filter_obj.date_from or filter_obj.date_to:
            item_date = self._parse_date(item.get('publication_date'))
            if not item_date:
                return False
            
            if filter_obj.date_from and item_date < filter_obj.date_from:
                return False
            
            if filter_obj.date_to and item_date > filter_obj.date_to:
                return False
        
        return True
    
    def _update_run_metadata(self, run_id: str, ingested_count: int, 
                           rejected_count: int, client_id: str):
        """Met à jour les métadonnées de run"""
        metadata = {
            'run_id': run_id,
            'client_id': client_id,
            'timestamp': datetime.now().isoformat(),
            'ingested_count': ingested_count,
            'rejected_count': rejected_count,
            'total_count': ingested_count + rejected_count
        }
        
        runs_index_file = self.metadata_path / "runs_index.jsonl"
        self._append_to_jsonl(runs_index_file, metadata)
    
    def _update_indexes(self):
        """Met à jour les index pour optimiser les requêtes futures"""
        # TODO: Implémenter la mise à jour des index
        # Cela pourrait inclure des index par date, source, company, etc.
        pass
    
    # Méthodes de requête simplifiées
    def get_company_news(self, company_id: str, year: Optional[int] = None, 
                        status: str = "ingested") -> List[Dict]:
        """Récupère toutes les news d'une company"""
        filter_obj = QueryFilter(
            companies=[company_id],
            status=status
        )
        
        if year:
            filter_obj.date_from = datetime(year, 1, 1)
            filter_obj.date_to = datetime(year, 12, 31, 23, 59, 59)
        
        return self.query(filter_obj)
    
    def get_recent_news(self, days: int = 14, client_id: Optional[str] = None, 
                       status: str = "ingested") -> List[Dict]:
        """Récupère les news récentes"""
        filter_obj = QueryFilter(
            date_from=datetime.now() - timedelta(days=days),
            status=status
        )
        
        if client_id:
            filter_obj.clients = [client_id]
        
        return self.query(filter_obj)
    
    def get_source_news(self, source_keys: List[str], date_from: Optional[datetime] = None,
                       date_to: Optional[datetime] = None, status: str = "ingested") -> List[Dict]:
        """Récupère les news par source sur une période"""
        filter_obj = QueryFilter(
            sources=source_keys,
            date_from=date_from,
            date_to=date_to,
            status=status
        )
        
        return self.query(filter_obj)
    
    def get_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques globales du warehouse"""
        stats = {
            'total_runs': 0,
            'total_ingested': 0,
            'total_rejected': 0,
            'companies': set(),
            'sources': set(),
            'clients': set(),
            'date_range': {'earliest': None, 'latest': None}
        }
        
        runs_index_file = self.metadata_path / "runs_index.jsonl"
        if runs_index_file.exists():
            with jsonlines.open(runs_index_file) as reader:
                for run_metadata in reader:
                    stats['total_runs'] += 1
                    stats['total_ingested'] += run_metadata.get('ingested_count', 0)
                    stats['total_rejected'] += run_metadata.get('rejected_count', 0)
        
        # Convertir les sets en listes pour la sérialisation JSON
        stats['companies'] = list(stats['companies'])
        stats['sources'] = list(stats['sources'])
        stats['clients'] = list(stats['clients'])
        
        return stats


# Utilitaires pour l'intégration
def integrate_warehouse_to_run(run_result: Dict, client_id: str):
    """Intègre automatiquement les résultats d'un run dans le warehouse"""
    warehouse = DataWarehouse()
    
    # Charger les items depuis les fichiers de résultats
    run_id = run_result.get('run_id')
    if not run_id:
        logger.warning("Pas de run_id trouvé, impossible d'intégrer au warehouse")
        return
    
    base_path = Path("output/runs") / run_id
    
    ingested_items = []
    rejected_items = []
    
    # Charger les items ingérés
    ingested_file = base_path / "ingested_items.json"
    if ingested_file.exists():
        with open(ingested_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                ingested_items = data
            elif isinstance(data, dict) and 'items' in data:
                ingested_items = data['items']
    
    # Charger les items rejetés
    rejected_file = base_path / "rejected_items.json"
    if rejected_file.exists():
        with open(rejected_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                rejected_items = data
            elif isinstance(data, dict) and 'items' in data:
                rejected_items = data['items']
    
    # Stocker dans le warehouse
    warehouse.store_run_results(run_id, ingested_items, rejected_items, client_id)
    
    logger.info(f"Run {run_id} intégré au warehouse: {len(ingested_items)} ingérés, {len(rejected_items)} rejetés")