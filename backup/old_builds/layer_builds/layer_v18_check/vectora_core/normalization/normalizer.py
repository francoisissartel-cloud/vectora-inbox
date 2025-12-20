"""
Module de normalisation des items via Bedrock.

Ce module gère l'extraction d'entités, la classification d'événements
et la génération de résumés pour les items ingérés avec parallélisation.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Dict, Any

from .bedrock_client import BedrockNormalizationClient

logger = logging.getLogger(__name__)


def normalize_items_batch(
    raw_items: List[Dict[str, Any]], 
    canonical_scopes: Dict[str, Any],
    canonical_prompts: Dict[str, Any],
    bedrock_model: str,
    bedrock_region: str,
    max_workers: int = 1,
    watch_domains: List[Dict[str, Any]] = None,
    matching_config: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    Normalise une liste d'items via Bedrock avec parallélisation contrôlée.
    NOUVEAU: Support du matching Bedrock par domaines.
    
    Args:
        raw_items: Items bruts à normaliser
        canonical_scopes: Scopes canonical pour exemples
        canonical_prompts: Prompts canonical
        bedrock_model: Modèle Bedrock à utiliser
        bedrock_region: Région Bedrock
        max_workers: Nombre maximum de workers parallèles
        watch_domains: Domaines de veille pour matching Bedrock (NOUVEAU)
    
    Returns:
        Liste des items normalisés avec matching Bedrock
    """
    logger.info(f"Normalisation V2 de {len(raw_items)} items via Bedrock (workers: {max_workers})")
    
    if not raw_items:
        logger.warning("Aucun item à normaliser")
        return []
    
    # Préparation des exemples d'entités enrichis
    examples = _prepare_canonical_examples_enhanced(canonical_scopes)
    
    # Statistiques détaillées
    stats = {
        "total": len(raw_items),
        "success": 0,
        "failed": 0,
        "throttled": 0,
        "start_time": datetime.now()
    }
    
    normalized_items = []
    
    if max_workers == 1:
        # Mode séquentiel pour éviter le throttling
        normalized_items = _normalize_sequential(
            raw_items, examples, bedrock_model, bedrock_region, stats, 
            canonical_scopes, watch_domains, matching_config, canonical_prompts
        )
    else:
        # Mode parallèle contrôlé
        normalized_items = _normalize_parallel(
            raw_items, examples, bedrock_model, bedrock_region, max_workers, stats,
            canonical_scopes, watch_domains, matching_config
        )
    
    # Statistiques finales
    processing_time = (datetime.now() - stats["start_time"]).total_seconds()
    logger.info(
        f"Normalisation V2 terminée: {stats['success']} succès, {stats['failed']} échecs, "
        f"{stats['throttled']} throttling, {processing_time:.1f}s"
    )
    
    return normalized_items


def _normalize_sequential(
    raw_items: List[Dict[str, Any]], 
    examples: Dict[str, str],
    bedrock_model: str,
    bedrock_region: str,
    stats: Dict[str, Any],
    canonical_scopes: Dict[str, Any] = None,
    watch_domains: List[Dict[str, Any]] = None,
    matching_config: Dict[str, Any] = None,
    canonical_prompts: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """Normalisation séquentielle pour éviter le throttling.
    NOUVEAU: Support du matching Bedrock par domaines.
    """
    
    # Initialisation du client Bedrock
    bedrock_client = BedrockNormalizationClient(bedrock_model, bedrock_region)
    
    normalized_items = []
    
    for i, item in enumerate(raw_items):
        try:
            # Construction du texte à analyser
            item_text = _build_item_text(item)
            
            # Normalisation via Bedrock
            normalization_result = bedrock_client.normalize_item(item_text, examples)
            
            # NOUVEAU: Matching Bedrock réel si domaines configurés
            if watch_domains and len(watch_domains) > 0:
                from .bedrock_matcher import match_item_to_domains_bedrock
                
                # Construction de l'item temporaire pour le matching
                temp_item = _enrich_item_with_normalization(item, normalization_result)
                
                # Matching Bedrock réel
                bedrock_matching_result = match_item_to_domains_bedrock(
                    temp_item, watch_domains, canonical_scopes, matching_config or {},
                    canonical_prompts or {}, bedrock_model
                )
            else:
                # Pas de domaines configurés
                bedrock_matching_result = {'matched_domains': [], 'domain_relevance': {}}
            
            # Enrichissement de l'item avec les résultats (normalisation + matching)
            normalized_item = _enrich_item_with_normalization(item, normalization_result, bedrock_matching_result)
            normalized_items.append(normalized_item)
            stats["success"] += 1
            
            # Log de progrès
            if (i + 1) % 10 == 0:
                logger.info(f"Progress: {i + 1}/{len(raw_items)} items normalisés")
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Erreur normalisation item {item.get('item_id', 'unknown')}: {error_msg}")
            
            # Comptage spécifique du throttling
            if "throttling" in error_msg.lower() or "rate limit" in error_msg.lower():
                stats["throttled"] += 1
            
            # Ajout de l'item avec normalisation de fallback
            normalized_item = _create_fallback_normalized_item(item)
            normalized_items.append(normalized_item)
            stats["failed"] += 1
    
    return normalized_items


def _normalize_parallel(
    raw_items: List[Dict[str, Any]], 
    examples: Dict[str, str],
    bedrock_model: str,
    bedrock_region: str,
    max_workers: int,
    stats: Dict[str, Any],
    canonical_scopes: Dict[str, Any] = None,
    watch_domains: List[Dict[str, Any]] = None,
    matching_config: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """Normalisation parallèle contrôlée avec gestion d'erreurs."""
    
    normalized_items = [None] * len(raw_items)  # Préserver l'ordre
    
    def normalize_single_item(item_with_index):
        """Normalise un item individuel avec son index."""
        index, item = item_with_index
        
        try:
            # Client Bedrock par worker
            bedrock_client = BedrockNormalizationClient(bedrock_model, bedrock_region)
            
            # Construction du texte à analyser
            item_text = _build_item_text(item)
            
            # Normalisation via Bedrock
            normalization_result = bedrock_client.normalize_item(item_text, examples)
            
            # Enrichissement de l'item
            normalized_item = _enrich_item_with_normalization(item, normalization_result)
            
            return index, normalized_item, "success"
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Erreur normalisation item {item.get('item_id', 'unknown')}: {error_msg}")
            
            # Création item de fallback
            normalized_item = _create_fallback_normalized_item(item)
            
            error_type = "throttled" if ("throttling" in error_msg.lower() or "rate limit" in error_msg.lower()) else "failed"
            return index, normalized_item, error_type
    
    # Exécution parallèle
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Soumission des tâches
        futures = {
            executor.submit(normalize_single_item, (i, item)): i 
            for i, item in enumerate(raw_items)
        }
        
        # Collecte des résultats
        for future in as_completed(futures):
            try:
                index, normalized_item, result_type = future.result()
                normalized_items[index] = normalized_item
                stats[result_type] += 1
                
                # Log de progrès
                completed = stats["success"] + stats["failed"] + stats["throttled"]
                if completed % 10 == 0:
                    logger.info(f"Progress: {completed}/{len(raw_items)} items traités")
                    
            except Exception as e:
                logger.error(f"Erreur dans le worker parallèle: {str(e)}")
                stats["failed"] += 1
    
    return normalized_items


def _prepare_canonical_examples_enhanced(canonical_scopes: Dict[str, Any]) -> Dict[str, str]:
    """Prépare les exemples d'entités enrichis depuis les scopes canoniques."""
    examples = {}
    
    # Exemples de sociétés (plus de scopes, plus d'exemples)
    companies = []
    company_scopes = ["lai_companies_mvp_core", "lai_companies_hybrid", "lai_companies_global"]
    
    for scope_name in company_scopes:
        scope_companies = canonical_scopes.get("companies", {}).get(scope_name, [])
        if isinstance(scope_companies, list):
            companies.extend(scope_companies[:8])  # Plus d'exemples par scope
        elif isinstance(scope_companies, dict):
            # Si c'est un dict, prendre les valeurs
            comp_values = list(scope_companies.values())
            if comp_values and isinstance(comp_values[0], list):
                for comp_list in comp_values:
                    companies.extend(comp_list[:3])
            else:
                companies.extend(comp_values[:8])
    
    examples["companies_examples"] = ", ".join(str(c) for c in companies[:20])  # Limite étendue
    
    # Exemples de molécules (plus de scopes)
    molecules = []
    molecule_scopes = ["lai_molecules_global"]
    
    for scope_name in molecule_scopes:
        scope_molecules = canonical_scopes.get("molecules", {}).get(scope_name, [])
        if isinstance(scope_molecules, list):
            molecules.extend(scope_molecules[:15])  # Plus d'exemples
        elif isinstance(scope_molecules, dict):
            # Si c'est un dict, prendre les valeurs
            mol_values = list(scope_molecules.values())
            if mol_values and isinstance(mol_values[0], list):
                for mol_list in mol_values:
                    molecules.extend(mol_list[:5])
            else:
                molecules.extend(mol_values[:15])
    
    examples["molecules_examples"] = ", ".join(str(m) for m in molecules[:15])
    
    # Exemples de technologies (enrichis)
    technologies = []
    technology_scopes = ["lai_keywords"]
    
    for scope_name in technology_scopes:
        scope_technologies = canonical_scopes.get("technologies", {}).get(scope_name, [])
        if isinstance(scope_technologies, list):
            technologies.extend(scope_technologies[:15])  # Plus d'exemples
        elif isinstance(scope_technologies, dict):
            # Si c'est un dict, prendre les valeurs
            tech_values = list(scope_technologies.values())
            if tech_values and isinstance(tech_values[0], list):
                for tech_list in tech_values:
                    technologies.extend(tech_list[:5])
            else:
                # Convertir en liste avant slicing pour éviter l'erreur TypeError
                if tech_values:
                    tech_list = list(tech_values)
                    technologies.extend(tech_list[:15])
    
    examples["technologies_examples"] = ", ".join(str(t) for t in technologies[:15])
    
    # Ajout des trademarks (nouveau)
    trademarks = []
    trademark_scopes = ["lai_trademarks_global"]
    
    for scope_name in trademark_scopes:
        scope_trademarks = canonical_scopes.get("trademarks", {}).get(scope_name, [])
        if isinstance(scope_trademarks, list):
            trademarks.extend(scope_trademarks[:10])
        elif isinstance(scope_trademarks, dict):
            # Si c'est un dict, prendre les valeurs
            tm_values = list(scope_trademarks.values())
            if tm_values and isinstance(tm_values[0], list):
                for tm_list in tm_values:
                    trademarks.extend(tm_list[:3])
            else:
                trademarks.extend(tm_values[:10])
    
    examples["trademarks_examples"] = ", ".join(str(t) for t in trademarks[:10])
    
    # Log des exemples préparés
    logger.debug(
        f"Exemples préparés: {len(companies)} companies, {len(molecules)} molecules, "
        f"{len(technologies)} technologies, {len(trademarks)} trademarks"
    )
    
    return examples


def _build_item_text(item: Dict[str, Any]) -> str:
    """Construit le texte à analyser à partir d'un item."""
    title = item.get("title", "")
    content = item.get("content", "")
    
    # Limitation de la taille pour éviter les timeouts Bedrock
    max_content_length = 3000
    if len(content) > max_content_length:
        content = content[:max_content_length] + "..."
    
    return f"TITLE: {title}\n\nCONTENT: {content}"


def _enrich_item_with_normalization(
    original_item: Dict[str, Any], 
    normalization_result: Dict[str, Any],
    bedrock_matching_result: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Enrichit un item original avec les résultats de normalisation LAI.
    NOUVEAU: Support des résultats de matching Bedrock.
    """
    # Copie de l'item original
    enriched_item = original_item.copy()
    
    # Ajout du timestamp de normalisation
    enriched_item["normalized_at"] = datetime.now().isoformat() + "Z"
    
    # Construction de la section normalized_content avec champs LAI complets
    enriched_item["normalized_content"] = {
        "summary": normalization_result.get("summary", ""),
        "entities": {
            "companies": normalization_result.get("companies_detected", []),
            "molecules": normalization_result.get("molecules_detected", []),
            "technologies": normalization_result.get("technologies_detected", []),
            "trademarks": normalization_result.get("trademarks_detected", []),
            "indications": normalization_result.get("indications_detected", [])
        },
        "event_classification": {
            "primary_type": normalization_result.get("event_type", "other"),
            "confidence": 0.8  # Valeur par défaut
        },
        # Champs LAI spécialisés restaurés
        "lai_relevance_score": normalization_result.get("lai_relevance_score", 0),
        "anti_lai_detected": normalization_result.get("anti_lai_detected", False),
        "pure_player_context": normalization_result.get("pure_player_context", False),
        # Ajout métadonnées de normalisation
        "normalization_metadata": {
            "bedrock_model": "claude-3-5-sonnet",  # Sera passé dynamiquement
            "canonical_version": "1.0",
            "processing_time_ms": 0  # Sera calculé si nécessaire
        }
    }
    
    # NOUVEAU: Ajout des résultats de matching Bedrock
    if bedrock_matching_result:
        enriched_item["matching_results"] = {
            "matched_domains": bedrock_matching_result.get('matched_domains', []),
            "domain_relevance": bedrock_matching_result.get('domain_relevance', {}),
            "bedrock_matching_used": True
        }
    else:
        enriched_item["matching_results"] = {
            "matched_domains": [],
            "domain_relevance": {},
            "bedrock_matching_used": False
        }
    
    return enriched_item


def _create_fallback_normalized_item(original_item: Dict[str, Any]) -> Dict[str, Any]:
    """Crée un item normalisé de fallback en cas d'échec Bedrock."""
    enriched_item = original_item.copy()
    
    enriched_item["normalized_at"] = datetime.now().isoformat() + "Z"
    enriched_item["normalized_content"] = {
        "summary": "",
        "entities": {
            "companies": [],
            "molecules": [],
            "technologies": [],
            "trademarks": [],
            "indications": []
        },
        "event_classification": {
            "primary_type": "other",
            "confidence": 0.0
        },
        # Champs LAI avec valeurs par défaut
        "lai_relevance_score": 0,
        "anti_lai_detected": False,
        "pure_player_context": False,
        # Métadonnées indiquant l'échec
        "normalization_metadata": {
            "bedrock_model": "fallback",
            "canonical_version": "1.0",
            "processing_time_ms": 0,
            "fallback_reason": "bedrock_failure"
        }
    }
    
    return enriched_item


# Fonction de compatibilité avec l'ancienne interface
def normalize_items(
    raw_items: List[Dict[str, Any]], 
    canonical_scopes: Dict[str, Any],
    canonical_prompts: Dict[str, Any],
    bedrock_model: str,
    bedrock_region: str,
    watch_domains: List[Dict[str, Any]] = None,
    matching_config: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """Interface de compatibilité avec l'ancienne fonction.
    NOUVEAU: Support du matching Bedrock par domaines.
    """
    return normalize_items_batch(
        raw_items, canonical_scopes, canonical_prompts, 
        bedrock_model, bedrock_region, max_workers=1, watch_domains=watch_domains,
        matching_config=matching_config
    )