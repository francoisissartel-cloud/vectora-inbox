#!/usr/bin/env python3
"""
Warehouse d'items ingérés - Résolution du problème de cache hits
Stockage chronologique avec déduplication et reconstitution par client
"""

import json
# import jsonlines  # Remplacé par une implémentation simple
import logging
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional, Set
from dataclasses import asdict

logger = logging.getLogger(__name__)

class SimpleJSONLines:
    """Implémentation simple de jsonlines sans dépendance externe"""
    
    def __init__(self, file_path, mode='r'):
        self.file_path = file_path
        self.mode = mode
        self.file = None
    
    def __enter__(self):
        self.file = open(self.file_path, self.mode, encoding='utf-8')
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            self.file.close()
    
    def write(self, obj):
        """Écrire un objet JSON sur une ligne"""
        if self.mode not in ['w', 'a']:
            raise ValueError("File not opened for writing")
        json.dump(obj, self.file, ensure_ascii=False)
        self.file.write('\n')
    
    def __iter__(self):
        """Itérer sur les lignes JSON"""
        if self.mode not in ['r']:
            raise ValueError("File not opened for reading")
        
        for line in self.file:
            line = line.strip()
            if line:
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue

def jsonlines_open(file_path, mode='r'):
    """Fonction utilitaire pour ouvrir un fichier jsonlines"""
    return SimpleJSONLines(file_path, mode)

class MockStructuredItem:
    """Item mock pour les tests"""
    def __init__(self, item_id, source_key, title, content, published_at, content_hash=None):
        self.item_id = item_id
        self.source_key = source_key
        self.title = title
        self.content = content
        self.published_at = published_at
        self.url = f"https://example.com/{item_id}"
        self.content_hash = content_hash
        self.run_id = "test_run"

class IngestedWarehouse:
    """Gestionnaire du warehouse d'items ingérés pour un écosystème"""
    
    def __init__(self, ecosystem: str):
        self.ecosystem = ecosystem
        self.warehouse_path = Path(f"data/warehouse/ingested/profiles/{ecosystem}")
        self.items_file = self.warehouse_path / "ingested_items.jsonl"
        self.stats_file = self.warehouse_path / "warehouse_stats.json"
        self.last_update_file = self.warehouse_path / "last_update.json"
        self.date_index_file = self.warehouse_path / "indexes" / "by_date.json"
        self.hash_index_file = self.warehouse_path / "indexes" / "by_content_hash.json"
        
        self._ensure_structure()
        logger.info(f"IngestedWarehouse initialized for ecosystem: {ecosystem}")
    
    def _ensure_structure(self):
        """Créer la structure si elle n'existe pas"""
        self.warehouse_path.mkdir(parents=True, exist_ok=True)
        (self.warehouse_path / "indexes").mkdir(exist_ok=True)
        
        # Initialiser fichiers si inexistants
        if not self.stats_file.exists():
            self._init_stats_file()
        if not self.date_index_file.exists():
            self._init_date_index()
        if not self.hash_index_file.exists():
            self._init_hash_index()
        if not self.last_update_file.exists():
            self._init_last_update_file()
        if not self.items_file.exists():
            self.items_file.touch()
    
    def _init_stats_file(self):
        """Initialiser le fichier de stats"""
        initial_stats = {
            "ecosystem": self.ecosystem,
            "last_updated": datetime.now().isoformat(),
            "total_items": 0,
            "date_range": {"first_item": None, "last_item": None},
            "by_year": {},
            "by_source_type": {"press_corporate": 0, "press_sector": 0, "regulatory": 0},
            "by_company": {},
            "recent_activity": {"last_7_days": 0, "last_30_days": 0, "last_90_days": 0}
        }
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(initial_stats, f, indent=2, ensure_ascii=False)
    
    def _init_date_index(self):
        """Initialiser l'index temporel"""
        initial_index = {
            "index_version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "dates": {}
        }
        with open(self.date_index_file, 'w', encoding='utf-8') as f:
            json.dump(initial_index, f, indent=2, ensure_ascii=False)
    
    def _init_hash_index(self):
        """Initialiser l'index de déduplication"""
        initial_index = {
            "index_version": "1.0", 
            "last_updated": datetime.now().isoformat(),
            "hashes": {}
        }
        with open(self.hash_index_file, 'w', encoding='utf-8') as f:
            json.dump(initial_index, f, indent=2, ensure_ascii=False)
    
    def _init_last_update_file(self):
        """Initialiser le fichier last_update"""
        initial_update = {
            "last_updated": datetime.now().isoformat(),
            "ecosystem": self.ecosystem,
            "last_run_id": None,
            "items_added_last_update": 0
        }
        with open(self.last_update_file, 'w', encoding='utf-8') as f:
            json.dump(initial_update, f, indent=2, ensure_ascii=False)
    
    def add_items_with_deduplication(self, items: List, run_id: str) -> int:
        """
        Ajouter items avec déduplication par content_hash
        
        Args:
            items: Liste d'objets StructuredItem
            run_id: ID du run d'ingestion
            
        Returns:
            Nombre d'items ajoutés (après déduplication)
        """
        if not items:
            logger.info("No items to add to warehouse")
            return 0
        
        logger.info(f"Adding {len(items)} items to warehouse {self.ecosystem}")
        
        # Charger index hash existant
        hash_index = self._load_hash_index()
        added_count = 0
        
        for item in items:
            # Assurer que l'item a un content_hash
            if not hasattr(item, 'content_hash') or not item.content_hash:
                item.content_hash = self._calculate_content_hash(item)
            
            if item.content_hash in hash_index['hashes']:
                # Item déjà présent → mettre à jour métadonnées
                self._update_item_metadata(item.content_hash, run_id)
                logger.debug(f"Item deduplicated: {getattr(item, 'item_id', 'unknown')}")
            else:
                # Nouvel item → ajouter au warehouse
                line_number = self._append_item_to_jsonl(item, run_id)
                self._update_indexes(item, line_number, run_id)
                added_count += 1
                logger.debug(f"Item added to warehouse: {getattr(item, 'item_id', 'unknown')}")
        
        # Mettre à jour last_update
        self._update_last_update(run_id, added_count)
        
        logger.info(f"Warehouse updated: {added_count} new items added, {len(items) - added_count} deduplicated")
        return added_count
    
    def _calculate_content_hash(self, item) -> str:
        """Calculer le hash du contenu d'un item"""
        import hashlib
        
        # Utiliser URL + titre pour le hash si pas de contenu
        content = getattr(item, 'content', '') or ''
        url = getattr(item, 'url', '') or ''
        title = getattr(item, 'title', '') or ''
        
        hash_input = f"{url}|{title}|{content}"
        return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
    
    def _append_item_to_jsonl(self, item, run_id: str) -> int:
        """Ajouter un item au fichier JSONL et retourner le numéro de ligne"""
        # Convertir l'item en dict
        if hasattr(item, '__dict__'):
            item_dict = item.__dict__.copy()
        else:
            item_dict = asdict(item) if hasattr(item, '__dataclass_fields__') else dict(item)
        
        # Enrichir avec métadonnées warehouse
        item_dict.update({
            'warehouse_ingested_at': datetime.now().isoformat(),
            'warehouse_run_id': run_id,
            'warehouse_ecosystem': self.ecosystem
        })
        
        # Compter les lignes existantes pour obtenir le numéro
        line_number = self._count_lines_in_jsonl() + 1
        
        # Ajouter au fichier JSONL
        with jsonlines_open(self.items_file, mode='a') as writer:
            writer.write(item_dict)
        
        return line_number
    
    def _count_lines_in_jsonl(self) -> int:
        """Compter le nombre de lignes dans le fichier JSONL"""
        if not self.items_file.exists():
            return 0
        
        count = 0
        try:
            with jsonlines_open(self.items_file, mode='r') as reader:
                for _ in reader:
                    count += 1
        except Exception as e:
            logger.warning(f"Error counting lines in JSONL: {e}")
            return 0
        
        return count
    
    def _update_indexes(self, item, line_number: int, run_id: str):
        """Mettre à jour les index temporel et hash"""
        # Index temporel
        published_date = getattr(item, 'published_at', None)
        if published_date:
            # Convertir en string de date si nécessaire
            if isinstance(published_date, datetime):
                date_str = published_date.strftime('%Y-%m-%d')
            elif isinstance(published_date, date):
                date_str = published_date.strftime('%Y-%m-%d')
            else:
                date_str = str(published_date)[:10]  # Prendre les 10 premiers caractères
            
            self._update_date_index(date_str, line_number)
        
        # Index hash
        self._update_hash_index(item.content_hash, {
            "line_number": line_number,
            "item_id": getattr(item, 'item_id', 'unknown'),
            "first_seen": published_date.isoformat() if isinstance(published_date, (datetime, date)) else str(published_date),
            "run_id": run_id,
            "source_key": getattr(item, 'source_key', 'unknown')
        })
    
    def _update_date_index(self, date_str: str, line_number: int):
        """Mettre à jour l'index temporel"""
        date_index = self._load_date_index()
        
        if date_str not in date_index['dates']:
            date_index['dates'][date_str] = []
        
        date_index['dates'][date_str].append(line_number)
        date_index['last_updated'] = datetime.now().isoformat()
        
        with open(self.date_index_file, 'w', encoding='utf-8') as f:
            json.dump(date_index, f, indent=2, ensure_ascii=False)
    
    def _update_hash_index(self, content_hash: str, metadata: Dict[str, Any]):
        """Mettre à jour l'index de déduplication"""
        hash_index = self._load_hash_index()
        
        hash_index['hashes'][content_hash] = metadata
        hash_index['last_updated'] = datetime.now().isoformat()
        
        with open(self.hash_index_file, 'w', encoding='utf-8') as f:
            json.dump(hash_index, f, indent=2, ensure_ascii=False)
    
    def _update_item_metadata(self, content_hash: str, run_id: str):
        """Mettre à jour les métadonnées d'un item existant"""
        hash_index = self._load_hash_index()
        
        if content_hash in hash_index['hashes']:
            hash_index['hashes'][content_hash]['last_seen_run_id'] = run_id
            hash_index['hashes'][content_hash]['last_seen_at'] = datetime.now().isoformat()
            
            with open(self.hash_index_file, 'w', encoding='utf-8') as f:
                json.dump(hash_index, f, indent=2, ensure_ascii=False)
    
    def _update_last_update(self, run_id: str, items_added: int):
        """Mettre à jour le fichier last_update"""
        update_info = {
            "last_updated": datetime.now().isoformat(),
            "ecosystem": self.ecosystem,
            "last_run_id": run_id,
            "items_added_last_update": items_added
        }
        
        with open(self.last_update_file, 'w', encoding='utf-8') as f:
            json.dump(update_info, f, indent=2, ensure_ascii=False)
    
    def _load_date_index(self) -> Dict[str, Any]:
        """Charger l'index temporel"""
        try:
            with open(self.date_index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading date index: {e}")
            return {"index_version": "1.0", "last_updated": datetime.now().isoformat(), "dates": {}}
    
    def _load_hash_index(self) -> Dict[str, Any]:
        """Charger l'index de déduplication"""
        try:
            with open(self.hash_index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading hash index: {e}")
            return {"index_version": "1.0", "last_updated": datetime.now().isoformat(), "hashes": {}}
    
    def get_items_for_client_period(self, client_sources: List[str], 
                                   period_days: int, 
                                   reference_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Reconstituer items pour un client dans sa période
        
        Args:
            client_sources: Liste des sources du client
            period_days: Nombre de jours de la période
            reference_date: Date de référence (défaut: maintenant)
            
        Returns:
            Liste d'items reconstitués pour le client
        """
        if reference_date is None:
            reference_date = datetime.now()
        
        # Calculer fenêtre temporelle
        from_date = (reference_date - timedelta(days=period_days)).date()
        
        logger.info(f"Reconstituting items for client sources {client_sources} from {from_date} to {reference_date.date()}")
        
        # Lire items dans la période via index temporel
        items_in_period = self._get_items_since_date(from_date)
        
        # Filtrer par sources client
        client_items = [
            item for item in items_in_period 
            if item.get('source_key') in client_sources
        ]
        
        # Déduplication finale par content_hash
        deduplicated_items = self._deduplicate_by_hash(client_items)
        
        logger.info(f"Reconstituted {len(deduplicated_items)} items for client (from {len(items_in_period)} in period)")
        return deduplicated_items
    
    def _get_items_since_date(self, from_date: date) -> List[Dict[str, Any]]:
        """Récupérer items depuis une date via index temporel"""
        date_index = self._load_date_index()
        line_numbers = []
        
        for date_str, lines in date_index['dates'].items():
            try:
                item_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                if item_date >= from_date:
                    line_numbers.extend(lines)
            except ValueError:
                logger.warning(f"Invalid date format in index: {date_str}")
                continue
        
        return self._load_items_by_line_numbers(line_numbers)
    
    def _load_items_by_line_numbers(self, line_numbers: List[int]) -> List[Dict[str, Any]]:
        """Charger items par numéros de ligne"""
        if not line_numbers:
            return []
        
        items = []
        line_numbers_set = set(line_numbers)
        
        try:
            with jsonlines_open(self.items_file, mode='r') as reader:
                for line_num, item in enumerate(reader, 1):
                    if line_num in line_numbers_set:
                        items.append(item)
        except Exception as e:
            logger.error(f"Error loading items by line numbers: {e}")
            return []
        
        return items
    
    def _deduplicate_by_hash(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Déduplication finale par content_hash"""
        seen_hashes = set()
        deduplicated = []
        
        for item in items:
            content_hash = item.get('content_hash')
            if content_hash and content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                deduplicated.append(item)
        
        return deduplicated
    
    def update_stats(self):
        """Mettre à jour warehouse_stats.json"""
        logger.info("Updating warehouse stats...")
        
        stats = self._calculate_warehouse_stats()
        
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Warehouse stats updated: {stats['total_items']} total items")
    
    def _calculate_warehouse_stats(self) -> Dict[str, Any]:
        """Calculer toutes les stats du warehouse"""
        all_items = self._load_all_items()
        
        if not all_items:
            return {
                "ecosystem": self.ecosystem,
                "last_updated": datetime.now().isoformat(),
                "total_items": 0,
                "date_range": {"first_item": None, "last_item": None},
                "by_year": {},
                "by_source_type": {"press_corporate": 0, "press_sector": 0, "regulatory": 0},
                "by_company": {},
                "recent_activity": {"last_7_days": 0, "last_30_days": 0, "last_90_days": 0}
            }
        
        stats = {
            "ecosystem": self.ecosystem,
            "last_updated": datetime.now().isoformat(),
            "total_items": len(all_items),
            "date_range": self._calculate_date_range(all_items),
            "by_year": self._group_by_year(all_items),
            "by_source_type": self._group_by_source_type(all_items),
            "by_company": self._group_by_company(all_items),
            "recent_activity": self._calculate_recent_activity(all_items)
        }
        
        return stats
    
    def _load_all_items(self) -> List[Dict[str, Any]]:
        """Charger tous les items du warehouse"""
        items = []
        
        try:
            with jsonlines_open(self.items_file, mode='r') as reader:
                for item in reader:
                    items.append(item)
        except Exception as e:
            logger.error(f"Error loading all items: {e}")
            return []
        
        return items
    
    def _calculate_date_range(self, items: List[Dict[str, Any]]) -> Dict[str, Optional[str]]:
        """Calculer la plage de dates des items"""
        dates = []
        
        for item in items:
            published_at = item.get('published_at')
            if published_at:
                try:
                    if isinstance(published_at, str):
                        date_obj = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    else:
                        date_obj = published_at
                    dates.append(date_obj.date())
                except Exception:
                    continue
        
        if not dates:
            return {"first_item": None, "last_item": None}
        
        dates.sort()
        return {
            "first_item": dates[0].isoformat(),
            "last_item": dates[-1].isoformat()
        }
    
    def _group_by_year(self, items: List[Dict[str, Any]]) -> Dict[str, int]:
        """Grouper items par année"""
        by_year = {}
        
        for item in items:
            published_at = item.get('published_at')
            if published_at:
                try:
                    if isinstance(published_at, str):
                        date_obj = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    else:
                        date_obj = published_at
                    year = str(date_obj.year)
                    by_year[year] = by_year.get(year, 0) + 1
                except Exception:
                    continue
        
        return by_year
    
    def _group_by_source_type(self, items: List[Dict[str, Any]]) -> Dict[str, int]:
        """Grouper items par type de source"""
        by_source_type = {"press_corporate": 0, "press_sector": 0, "regulatory": 0}
        
        for item in items:
            source_key = item.get('source_key', '')
            if 'press_corporate' in source_key:
                by_source_type['press_corporate'] += 1
            elif 'press_sector' in source_key:
                by_source_type['press_sector'] += 1
            elif 'regulatory' in source_key:
                by_source_type['regulatory'] += 1
        
        return by_source_type
    
    def _group_by_company(self, items: List[Dict[str, Any]]) -> Dict[str, int]:
        """Grouper items par company"""
        by_company = {}
        
        for item in items:
            source_key = item.get('source_key', '')
            # Extraire le nom de la company depuis source_key
            if '__' in source_key:
                company = source_key.split('__')[1]
                by_company[company] = by_company.get(company, 0) + 1
        
        return by_company
    
    def _calculate_recent_activity(self, items: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculer l'activité récente"""
        now = datetime.now()
        recent_activity = {"last_7_days": 0, "last_30_days": 0, "last_90_days": 0}
        
        for item in items:
            published_at = item.get('published_at')
            if published_at:
                try:
                    if isinstance(published_at, str):
                        date_obj = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    else:
                        date_obj = published_at
                    
                    days_ago = (now - date_obj).days
                    
                    if days_ago <= 7:
                        recent_activity['last_7_days'] += 1
                    if days_ago <= 30:
                        recent_activity['last_30_days'] += 1
                    if days_ago <= 90:
                        recent_activity['last_90_days'] += 1
                        
                except Exception:
                    continue
        
        return recent_activity