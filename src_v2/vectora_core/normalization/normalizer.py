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


def validate_bedrock_response(bedrock_response: Dict[str, Any], original_content: str) -> Dict[str, Any]:
    """
    Validation post-Bedrock pour détecter hallucinations
    """
    entities = bedrock_response.get('entities', {})
    content_lower = original_content.lower()
    
    # Validation technologies
    technologies = entities.get('technologies', [])
    validated_technologies = []
    
    for tech in technologies:
        if any(keyword.lower() in content_lower 
              for keyword in get_technology_keywords(tech)):
            validated_technologies.append(tech)
        else:
            logger.warning(f"Possible hallucination: {tech} not found in content")
    
    # Validation companies
    companies = entities.get('companies', [])
    validated_companies = []
    
    for company in companies:
        # Vérifier si le nom de la société apparaît dans le contenu
        company_keywords = [company.lower(), company.replace(' ', '').lower()]
        if any(keyword in content_lower for keyword in company_keywords):
            validated_companies.append(company)
        else:
            logger.warning(f"Possible hallucination: {company} not found in content")
    
    # Mettre à jour la réponse avec les entités validées
    bedrock_response['companies_detected'] = validated_companies
    bedrock_response['technologies_detected'] = validated_technologies
    
    return bedrock_response


def get_technology_keywords(tech: str) -> List[str]:
    """
    Retourne les mots-clés associés à une technologie pour validation
    """
    tech_keywords = {
        'Extended-Release Injectable': ['extended-release', 'extended release', 'injectable'],
        'Long-Acting Injectable': ['long-acting', 'long acting', 'injectable', 'lai'],
        'Depot Injection': ['depot', 'injection'],
        'Once-Monthly Injection': ['once-monthly', 'monthly', 'injection'],
        'Microspheres': ['microsphere', 'microspheres'],
        'PLGA': ['plga', 'poly(lactic-co-glycolic acid)'],
        'In-Situ Depot': ['in-situ', 'depot'],
        'Hydrogel': ['hydrogel', 'hydrogels'],
        'Subcutaneous Injection': ['subcutaneous', 'injection'],
        'Intramuscular Injection': ['intramuscular', 'injection']
    }
    
    return tech_keywords.get(tech, [tech.lower()])


def normalize_items_batch(
    raw_items: List[Dict[str, Any]], 
    canonical_scopes: Dict[str, Any],
    canonical_prompts: Dict[str, Any],
    bedrock_model: str,
    bedrock_region: str,
    max_workers: int = 1,
    watch_domains: List[Dict[str, Any]] = None,
    matching_config: Dict[str, Any] = None,
    s3_io = None,
    client_config: Dict[str, Any] = None,
    config_bucket: str = None,
    enable_domain_scoring: bool = False
) -> List[Dict[str, Any]]:
    """
    Normalise une liste d'items via Bedrock avec parallélisation contrôlée.
    NOUVEAU: Support du matching Bedrock par domaines + Approche B + Domain Scoring.
    
    Args:
        raw_items: Items bruts à normaliser
        canonical_scopes: Scopes canonical pour exemples
        canonical_prompts: Prompts canonical
        bedrock_model: Modèle Bedrock à utiliser
        bedrock_region: Région Bedrock
        max_workers: Nombre maximum de workers parallèles
        watch_domains: Domaines de veille pour matching Bedrock
        matching_config: Configuration matching
        s3_io: Module s3_io pour Approche B
        client_config: Configuration client pour Approche B
        config_bucket: Bucket S3 de configuration
        enable_domain_scoring: Active le 2ème appel Bedrock pour domain scoring
    
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
            canonical_scopes, watch_domains, matching_config, canonical_prompts,
            s3_io, client_config, config_bucket, enable_domain_scoring
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
    canonical_prompts: Dict[str, Any] = None,
    s3_io = None,
    client_config: Dict[str, Any] = None,
    config_bucket: str = None,
    enable_domain_scoring: bool = False
) -> List[Dict[str, Any]]:
    """Normalisation séquentielle pour éviter le throttling.
    NOUVEAU: Support du matching Bedrock par domaines + Approche B + Domain Scoring.
    """
    
    # VALIDATION: Paramètres requis pour Approche B
    if not s3_io:
        raise ValueError("s3_io est requis pour Approche B")
    if not client_config:
        raise ValueError("client_config est requis pour Approche B")
    if not canonical_scopes:
        raise ValueError("canonical_scopes est requis pour Approche B")
    if not config_bucket:
        raise ValueError("config_bucket est requis pour Approche B")
    
    logger.info("✅ Paramètres Approche B validés: s3_io, client_config, canonical_scopes, config_bucket")
    
    # Initialisation du client Bedrock avec support Approche B
    bedrock_client = BedrockNormalizationClient(
        bedrock_model, bedrock_region, s3_io, client_config, canonical_scopes, config_bucket
    )
    
    normalized_items = []
    
    for i, item in enumerate(raw_items):
        try:
            # Construction du texte à analyser
            item_text = _build_item_text(item)
            
            # Normalisation via Bedrock avec prompts canonical
            normalization_result = bedrock_client.normalize_item(
                item_text, examples, canonical_prompts=canonical_prompts,
                item_source_key=item.get('source_key'), item=item
            )
            
            # NOUVEAU: Validation post-processing pour éviter les hallucinations
            normalization_result = validate_bedrock_response(normalization_result, item_text)
            
            # NOUVEAU: Matching Bedrock systématique (CORRIGÉ)
            from .bedrock_matcher import match_item_to_domains_bedrock
            
            # Construction de l'item temporaire pour le matching
            temp_item = _enrich_item_with_normalization(item, normalization_result)
            
            # Matching Bedrock systématique (même avec domaines vides)
            bedrock_matching_result = match_item_to_domains_bedrock(
                temp_item, watch_domains or [], canonical_scopes, matching_config or {},
                canonical_prompts or {}, bedrock_model
            )
            
            # NOUVEAU: Domain scoring (2ème appel Bedrock) - CONDITIONNEL
            domain_scoring_result = None
            if enable_domain_scoring:
                logger.info("Domain scoring activé - exécution du 2ème appel Bedrock")
                try:
                    from .bedrock_domain_scorer import score_item_for_domain
                    
                    # Charger domain definition
                    domain_definition = canonical_scopes.get('domains', {}).get('lai_domain_definition', {})
                    if domain_definition:
                        domain_scoring_prompt = canonical_prompts.get('domain_scoring', {}).get('lai_domain_scoring', {})
                        if domain_scoring_prompt:
                            domain_scoring_result = score_item_for_domain(
                                temp_item, domain_definition, canonical_scopes,
                                bedrock_client, domain_scoring_prompt
                            )
                            logger.info(f"Domain scoring: is_relevant={domain_scoring_result.get('is_relevant')}, score={domain_scoring_result.get('score')}")
                        else:
                            logger.warning("Prompt domain_scoring/lai_domain_scoring non trouvé")
                    else:
                        logger.warning("Domain definition lai_domain_definition non trouvée")
                except Exception as e:
                    logger.error(f"Erreur domain scoring: {str(e)}")
            else:
                logger.debug("Domain scoring désactivé (enable_domain_scoring=False)")
            
            # Enrichissement de l'item avec les résultats (normalisation + matching + domain scoring)
            normalized_item = _enrich_item_with_normalization(item, normalization_result, bedrock_matching_result, domain_scoring_result)
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
    bedrock_matching_result: Dict[str, Any] = None,
    domain_scoring_result: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Enrichit un item original avec les résultats de normalisation LAI.
    NOUVEAU: Support des résultats de matching Bedrock + extraction date + domain scoring.
    """
    # Copie de l'item original
    enriched_item = original_item.copy()
    
    # Ajout du timestamp de normalisation
    enriched_item["normalized_at"] = datetime.now().isoformat() + "Z"
    
    # Extraction et validation de la date Bedrock
    extracted_date = normalization_result.get('extracted_date')
    date_confidence = normalization_result.get('date_confidence', 0.0)
    
    if extracted_date:
        try:
            datetime.strptime(extracted_date, '%Y-%m-%d')
            logger.info(f"Date extracted by Bedrock: {extracted_date} (confidence: {date_confidence})")
        except ValueError:
            logger.warning(f"Invalid date format from Bedrock: {extracted_date}")
            extracted_date = None
            date_confidence = 0.0
    
    # Calcul de effective_date (date unique pour tout le pipeline)
    published_at = original_item.get('published_at', '')
    
    # Logique de sélection: prioriser Bedrock si confiance > 0.7
    if extracted_date and date_confidence > 0.7:
        effective_date = extracted_date
        date_source = 'bedrock'
    else:
        effective_date = published_at[:10] if published_at else None
        date_source = 'published_at'
    
    # Ajouter au niveau racine
    enriched_item['effective_date'] = effective_date
    enriched_item['date_metadata'] = {
        'source': date_source,
        'bedrock_date': extracted_date,
        'bedrock_confidence': date_confidence,
        'published_at': published_at
    }
    
    # Construction de la section normalized_content (générique)
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
        # Date extraite par Bedrock
        "extracted_date": extracted_date,
        "date_confidence": date_confidence,
        # Métadonnées de normalisation
        "normalization_metadata": {
            "bedrock_model": "claude-3-5-sonnet",
            "canonical_version": "2.0",
            "processing_time_ms": 0
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
    
    # NOUVEAU: Ajout des résultats de domain scoring (2ème appel Bedrock)
    if domain_scoring_result:
        enriched_item["domain_scoring"] = {
            "is_relevant": domain_scoring_result.get('is_relevant', False),
            "score": domain_scoring_result.get('score', 0),
            "confidence": domain_scoring_result.get('confidence', 'low'),
            "signals_detected": domain_scoring_result.get('signals_detected', {}),
            "score_breakdown": domain_scoring_result.get('score_breakdown'),
            "reasoning": domain_scoring_result.get('reasoning', '')
        }
        enriched_item["has_domain_scoring"] = True
    else:
        enriched_item["has_domain_scoring"] = False
    
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
        # Métadonnées indiquant l'échec
        "normalization_metadata": {
            "bedrock_model": "fallback",
            "canonical_version": "2.0",
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