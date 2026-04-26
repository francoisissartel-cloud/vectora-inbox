"""
Watch Domain Resolver - Utilitaire pour résoudre le watch_domain depuis la config client
Utilisé par le nouveau système de cache par watch_domain
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class WatchDomainResolver:
    """Résolveur pour mapper client_id → watch_domain_id"""
    
    def __init__(self, config_base_paths: List[str] = None):
        """
        Args:
            config_base_paths: Chemins de base pour chercher les configs clients
        """
        self.config_base_paths = config_base_paths or [
            "config/clients",
            "client-config-examples/production"
        ]
        
        # Cache des résolutions pour éviter les re-lectures
        self._resolution_cache = {}
        
        logger.info(f"WatchDomainResolver initialized with paths: {self.config_base_paths}")
    
    def resolve_watch_domain(self, client_id: str) -> str:
        """
        Résout le watch_domain_id depuis la configuration client
        
        Args:
            client_id: ID du client (ex: "mvp_test_100days")
            
        Returns:
            watch_domain_id (ex: "tech_lai_ecosystem")
            
        Raises:
            ValueError: Si le client_config n'est pas trouvé ou watch_domain manquant
        """
        # Vérifier le cache
        if client_id in self._resolution_cache:
            return self._resolution_cache[client_id]
        
        # Charger la configuration client
        client_config = self._load_client_config(client_id)
        
        # Extraire le watch_domain
        watch_domains = client_config.get('watch_domains', [])
        if not watch_domains:
            raise ValueError(
                f"No watch_domains configured for client '{client_id}'. "
                f"Add watch_domains section to client config."
            )
        
        # Prendre le premier watch_domain comme écosystème principal
        primary_watch_domain = watch_domains[0]
        watch_domain_id = primary_watch_domain.get('id')
        
        if not watch_domain_id:
            raise ValueError(
                f"watch_domains[0].id is missing for client '{client_id}'. "
                f"Ensure watch_domains[0] has an 'id' field."
            )
        
        # Mettre en cache et retourner
        self._resolution_cache[client_id] = watch_domain_id
        logger.info(f"Resolved client '{client_id}' → watch_domain '{watch_domain_id}'")
        
        return watch_domain_id
    
    def resolve_multiple_clients(self, client_ids: List[str]) -> Dict[str, str]:
        """
        Résout les watch_domains pour plusieurs clients
        
        Args:
            client_ids: Liste des IDs clients
            
        Returns:
            Dict mapping client_id → watch_domain_id
        """
        results = {}
        errors = {}
        
        for client_id in client_ids:
            try:
                watch_domain_id = self.resolve_watch_domain(client_id)
                results[client_id] = watch_domain_id
            except Exception as e:
                errors[client_id] = str(e)
                logger.error(f"Failed to resolve watch_domain for '{client_id}': {e}")
        
        if errors:
            logger.warning(f"Resolution errors for {len(errors)} clients: {errors}")
        
        return results
    
    def get_clients_by_watch_domain(self, client_ids: List[str]) -> Dict[str, List[str]]:
        """
        Groupe les clients par watch_domain
        
        Args:
            client_ids: Liste des IDs clients
            
        Returns:
            Dict mapping watch_domain_id → [client_ids]
        """
        client_mappings = self.resolve_multiple_clients(client_ids)
        
        # Grouper par watch_domain
        watch_domain_groups = {}
        for client_id, watch_domain_id in client_mappings.items():
            if watch_domain_id not in watch_domain_groups:
                watch_domain_groups[watch_domain_id] = []
            watch_domain_groups[watch_domain_id].append(client_id)
        
        return watch_domain_groups
    
    def validate_watch_domain_consistency(self, client_ids: List[str]) -> Dict[str, Any]:
        """
        Valide la cohérence des watch_domains entre clients
        
        Args:
            client_ids: Liste des IDs clients à valider
            
        Returns:
            Rapport de validation avec recommandations
        """
        watch_domain_groups = self.get_clients_by_watch_domain(client_ids)
        
        validation_report = {
            "total_clients": len(client_ids),
            "total_watch_domains": len(watch_domain_groups),
            "watch_domain_groups": watch_domain_groups,
            "recommendations": []
        }
        
        # Analyser la distribution
        for watch_domain_id, clients in watch_domain_groups.items():
            client_count = len(clients)
            
            if client_count == 1:
                validation_report["recommendations"].append({
                    "type": "isolated_client",
                    "watch_domain": watch_domain_id,
                    "clients": clients,
                    "message": f"Client '{clients[0]}' is alone in watch_domain '{watch_domain_id}'. "
                              f"Consider grouping with other clients or using client-specific cache."
                })
            elif client_count > 10:
                validation_report["recommendations"].append({
                    "type": "large_group",
                    "watch_domain": watch_domain_id,
                    "clients": clients,
                    "message": f"Watch_domain '{watch_domain_id}' has {client_count} clients. "
                              f"Consider splitting into smaller groups for better performance."
                })
        
        return validation_report
    
    def _load_client_config(self, client_id: str) -> Dict[str, Any]:
        """Charge la configuration d'un client depuis les chemins configurés"""
        
        for base_path in self.config_base_paths:
            config_path = Path(base_path) / f"{client_id}.yaml"
            
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f)
                        logger.debug(f"Loaded client config from: {config_path}")
                        return config
                except Exception as e:
                    logger.warning(f"Failed to load config from {config_path}: {e}")
                    continue
        
        # Config non trouvée
        raise FileNotFoundError(
            f"Client config not found for '{client_id}'. "
            f"Searched in: {[str(Path(p) / f'{client_id}.yaml') for p in self.config_base_paths]}"
        )
    
    def clear_cache(self):
        """Vide le cache de résolution (utile pour les tests)"""
        self._resolution_cache.clear()
        logger.debug("Resolution cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du cache de résolution"""
        return {
            "cached_resolutions": len(self._resolution_cache),
            "cache_entries": dict(self._resolution_cache)
        }


# Utilitaires de convenance
def resolve_watch_domain_for_client(client_id: str) -> str:
    """
    Fonction utilitaire pour résoudre rapidement un watch_domain
    
    Args:
        client_id: ID du client
        
    Returns:
        watch_domain_id
    """
    resolver = WatchDomainResolver()
    return resolver.resolve_watch_domain(client_id)


def get_watch_domain_groups(client_ids: List[str]) -> Dict[str, List[str]]:
    """
    Fonction utilitaire pour grouper des clients par watch_domain
    
    Args:
        client_ids: Liste des IDs clients
        
    Returns:
        Dict mapping watch_domain_id → [client_ids]
    """
    resolver = WatchDomainResolver()
    return resolver.get_clients_by_watch_domain(client_ids)


# Exemple d'utilisation
if __name__ == "__main__":
    # Test avec les clients existants
    resolver = WatchDomainResolver()
    
    test_clients = [
        "lai_weekly_v3.1",
        "mvp_test_100days", 
        "mvp_test_30days",
        "test_camurus",
        "test_medincell",
        "test_nanexa"
    ]
    
    print("=== Test WatchDomainResolver ===")
    
    # Test résolution individuelle
    for client_id in test_clients:
        try:
            watch_domain = resolver.resolve_watch_domain(client_id)
            print(f"[OK] {client_id} -> {watch_domain}")
        except Exception as e:
            print(f"[ERROR] {client_id} -> ERROR: {e}")
    
    # Test groupement
    print("\n=== Groupement par Watch Domain ===")
    groups = resolver.get_clients_by_watch_domain(test_clients)
    for watch_domain, clients in groups.items():
        print(f"[WD] {watch_domain}: {len(clients)} clients")
        for client in clients:
            print(f"   - {client}")
    
    # Test validation
    print("\n=== Validation de Cohérence ===")
    validation = resolver.validate_watch_domain_consistency(test_clients)
    print(f"Total clients: {validation['total_clients']}")
    print(f"Total watch_domains: {validation['total_watch_domains']}")
    
    if validation['recommendations']:
        print("Recommandations:")
        for rec in validation['recommendations']:
            print(f"  - {rec['type']}: {rec['message']}")
    else:
        print("[OK] Configuration coherente, aucune recommandation")