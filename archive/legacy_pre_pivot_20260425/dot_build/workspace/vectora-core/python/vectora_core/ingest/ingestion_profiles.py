"""
Profils d'ingestion pour Vectora Inbox V2.

Ce module implémente la logique des profils d'ingestion définis dans canonical.
Il permet de différencier le traitement entre sources corporate et presse.

Responsabilités :
- Appliquer les profils d'ingestion selon le type de source
- Filtrer la presse sectorielle par mots-clés LAI
- Ingestion large pour les pure players LAI
- Exclusion du bruit (RH, événements génériques)
"""

from typing import Any, Dict, List, Optional
import logging
import re

logger = logging.getLogger(__name__)

# Variables globales pour scopes chargés depuis S3
_exclusion_scopes_cache = None
_pure_players_cache = None
_hybrid_players_cache = None
_lai_keywords_cache = None

# Matrice de décision pour filtrage (Phase 4 refactoring)
FILTER_MATRIX = {
    # (source_type, company_type, ingestion_mode) -> (apply_exclusions, require_lai)
    ('press_corporate', 'pure_player', 'balanced'): (True, False),
    ('press_corporate', 'hybrid_player', 'balanced'): (True, True),
    ('press_corporate', 'unknown', 'balanced'): (True, True),
    ('press_sector', '*', 'balanced'): (True, True),
    ('*', '*', 'broad'): (False, False),
    ('*', '*', 'strict'): (True, True),
}

def initialize_exclusion_scopes(s3_io, config_bucket: str):
    """Charge les exclusion_scopes depuis S3 (appelé au démarrage)."""
    global _exclusion_scopes_cache
    
    try:
        scopes = s3_io.read_yaml_from_s3(config_bucket, 'canonical/scopes/exclusion_scopes.yaml')
        _exclusion_scopes_cache = scopes or {}
        logger.info(f"Exclusion scopes chargés: {len(_exclusion_scopes_cache)} catégories")
        
        # Log détaillé des scopes chargés
        for scope_name, scope_terms in _exclusion_scopes_cache.items():
            if isinstance(scope_terms, list):
                logger.debug(f"Scope '{scope_name}': {len(scope_terms)} termes")
    except Exception as e:
        logger.error(f"Échec chargement exclusion_scopes: {e}")
        raise RuntimeError(f"Impossible de charger exclusion_scopes depuis S3: {e}")

def initialize_company_scopes(s3_io, config_bucket: str):
    """Charge les company scopes depuis S3 (appelé au démarrage)."""
    global _pure_players_cache, _hybrid_players_cache
    
    try:
        scopes = s3_io.read_yaml_from_s3(config_bucket, 'canonical/scopes/company_scopes.yaml')
        
        pure_players = scopes.get('lai_companies_pure_players', [])
        _pure_players_cache = [company.lower() for company in pure_players]
        
        hybrid_players = scopes.get('lai_companies_hybrid', [])
        _hybrid_players_cache = [company.lower() for company in hybrid_players]
        
        logger.info(f"Company scopes: {len(_pure_players_cache)} pure players, {len(_hybrid_players_cache)} hybrid players")
    except Exception as e:
        logger.error(f"Échec chargement company_scopes: {e}")
        raise RuntimeError(f"Impossible de charger company_scopes depuis S3: {e}")

def initialize_lai_keywords(s3_io, config_bucket: str):
    """Charge les LAI keywords depuis S3 (appelé au démarrage)."""
    global _lai_keywords_cache
    
    try:
        # Charger technology_scopes.yaml et trademark_scopes.yaml
        tech_scopes = s3_io.read_yaml_from_s3(config_bucket, 'canonical/scopes/technology_scopes.yaml')
        trademark_scopes = s3_io.read_yaml_from_s3(config_bucket, 'canonical/scopes/trademark_scopes.yaml')
        
        keywords = []
        # Ajouter core_phrases, technology_terms_high_precision, interval_patterns
        lai_keywords_section = tech_scopes.get('lai_keywords', {})
        for scope in ['core_phrases', 'technology_terms_high_precision', 'interval_patterns']:
            keywords.extend(lai_keywords_section.get(scope, []))
        
        # Ajouter trademarks
        keywords.extend(trademark_scopes.get('lai_trademarks_global', []))
        
        _lai_keywords_cache = keywords
        logger.info(f"LAI keywords: {len(_lai_keywords_cache)} termes chargés")
    except Exception as e:
        logger.error(f"Échec chargement LAI keywords: {e}")
        raise RuntimeError(f"Impossible de charger LAI keywords depuis S3: {e}")

def _get_exclusion_terms() -> List[str]:
    """Retourne la liste combinée des termes d'exclusion depuis S3."""
    if not _exclusion_scopes_cache:
        raise RuntimeError("Exclusion scopes non initialisés")
    
    # Combiner tous les scopes d'exclusion pertinents
    terms = []
    for scope_name in ['hr_content', 'financial_generic', 'hr_recruitment_terms', 'financial_reporting_terms', 
                       'esg_generic', 'event_generic', 'corporate_noise_terms', 'anti_lai_routes']:
        scope_terms = _exclusion_scopes_cache.get(scope_name, [])
        if isinstance(scope_terms, list):
            terms.extend(scope_terms)
    
    return terms

def _is_pure_player(company_id: str) -> bool:
    """Vérifie si l'entreprise est un pure player LAI."""
    if not _pure_players_cache:
        raise RuntimeError("Company scopes non initialisés")
    return company_id.lower() in _pure_players_cache

def _is_hybrid_player(company_id: str) -> bool:
    """Vérifie si l'entreprise est un hybrid player."""
    if not _hybrid_players_cache:
        raise RuntimeError("Company scopes non initialisés")
    return company_id.lower() in _hybrid_players_cache


def apply_ingestion_profile(items: List[Dict[str, Any]], source_meta: Dict[str, Any], ingestion_mode: str = "balanced") -> List[Dict[str, Any]]:
    """
    Applique le profil d'ingestion approprié selon le type de source.
    
    Matrice de décision (Phase 4 - simplifiée):
    | source_type      | company_type  | ingestion_mode | apply_exclusions | require_lai |
    |------------------|---------------|----------------|------------------|-------------|
    | press_corporate  | pure_player   | balanced       | YES              | NO          |
    | press_corporate  | hybrid_player | balanced       | YES              | YES         |
    | press_corporate  | unknown       | balanced       | YES              | YES         |
    | press_sector     | *             | balanced       | YES              | YES         |
    | *                | *             | broad          | NO               | NO          |
    | *                | *             | strict         | YES              | YES         |
    
    Args:
        items: Liste d'items bruts à filtrer
        source_meta: Métadonnées de la source (source_key, source_type, etc.)
        ingestion_mode: Mode d'ingestion (strict/balanced/broad)
    
    Returns:
        Liste d'items filtrés selon le profil avec métriques d'exclusion
    """
    if not items:
        return []
    
    source_type = source_meta.get('source_type', '')
    source_key = source_meta.get('source_key', '')
    company_id = source_meta.get('company_id', '')
    
    logger.info(f"Application du profil d'ingestion pour {source_key} (type: {source_type}, mode: {ingestion_mode})")
    
    # Déterminer company_type
    if _is_pure_player(company_id):
        company_type = 'pure_player'
    elif _is_hybrid_player(company_id):
        company_type = 'hybrid_player'
    else:
        company_type = 'unknown'
    
    # Résoudre règles de filtrage via matrice
    filter_key = (source_type, company_type, ingestion_mode)
    apply_exclusions, require_lai = _get_filter_rules(filter_key)
    
    logger.info(f"{source_key}: company_type={company_type}, exclusions={apply_exclusions}, lai_required={require_lai}")
    
    # Appliquer filtrage selon règles
    if not apply_exclusions and not require_lai:
        # Mode broad: tout passe
        logger.info(f"Mode broad: ingestion large pour {source_key}")
        return items
    elif apply_exclusions and not require_lai:
        # Pure player: exclusions seules
        return _filter_with_metrics(items, source_key, exclusions_only=True)
    else:
        # Hybrid/unknown/press: exclusions + LAI
        return _filter_with_metrics(items, source_key, exclusions_only=False)


def _get_filter_rules(filter_key: tuple) -> tuple:
    """
    Résout les règles de filtrage via la matrice de décision.
    
    Args:
        filter_key: (source_type, company_type, ingestion_mode)
    
    Returns:
        (apply_exclusions, require_lai)
    """
    # Recherche exacte
    if filter_key in FILTER_MATRIX:
        return FILTER_MATRIX[filter_key]
    
    # Recherche avec wildcards
    source_type, company_type, ingestion_mode = filter_key
    
    # Essayer avec wildcard sur company_type
    wildcard_key = (source_type, '*', ingestion_mode)
    if wildcard_key in FILTER_MATRIX:
        return FILTER_MATRIX[wildcard_key]
    
    # Essayer avec wildcard sur source_type et company_type
    wildcard_key = ('*', '*', ingestion_mode)
    if wildcard_key in FILTER_MATRIX:
        return FILTER_MATRIX[wildcard_key]
    
    # Défaut: strict (exclusions + LAI)
    logger.warning(f"Aucune règle trouvée pour {filter_key}, défaut: strict")
    return (True, True)


def _filter_with_metrics(items: List[Dict[str, Any]], source_key: str, exclusions_only: bool = False) -> List[Dict[str, Any]]:
    """
    Filtre items avec métriques d'exclusion détaillées.
    
    Args:
        items: Items à filtrer
        source_key: Clé de la source
        exclusions_only: Si True, appliquer uniquement exclusions (pure player)
    
    Returns:
        Items filtrés avec métadonnées d'exclusion
    """
    filtered = []
    exclusion_stats = {
        'hr_content': 0,
        'financial_generic': 0,
        'esg_generic': 0,
        'event_generic': 0,
        'corporate_noise': 0,
        'no_lai_keywords': 0,
        'other': 0
    }
    
    for item in items:
        title = item.get('title', '')
        content = item.get('content', '')
        full_text = f"{title} {content}".lower()
        
        # Vérifier exclusions sur titre
        exclusion_reason, exclusion_terms = _check_exclusions(title)
        if exclusion_reason:
            item['filtering'] = {
                'excluded': True,
                'exclusion_reason': exclusion_reason,
                'exclusion_terms_matched': exclusion_terms
            }
            exclusion_stats[exclusion_reason] += 1
            logger.debug(f"[{source_key}] Exclu ({exclusion_reason}): {title[:60]}")
            continue
        
        # Si exclusions_only, garder l'item
        if exclusions_only:
            item['filtering'] = {'excluded': False, 'exclusion_reason': None}
            filtered.append(item)
            continue
        
        # Vérifier LAI keywords sur titre + contenu
        lai_keywords_found = _find_lai_keywords(full_text)
        if lai_keywords_found:
            item['filtering'] = {
                'excluded': False,
                'exclusion_reason': None,
                'lai_keywords_found': lai_keywords_found
            }
            filtered.append(item)
        else:
            item['filtering'] = {
                'excluded': True,
                'exclusion_reason': 'no_lai_keywords',
                'exclusion_terms_matched': []
            }
            exclusion_stats['no_lai_keywords'] += 1
            logger.debug(f"[{source_key}] Exclu (no LAI): {title[:60]}")
    
    # Log stats
    total_excluded = len(items) - len(filtered)
    if total_excluded > 0:
        logger.info(f"{source_key}: {len(filtered)}/{len(items)} conservés, exclusions: {exclusion_stats}")
    
    return filtered


def _check_exclusions(text: str) -> tuple:
    """
    Vérifie exclusions et retourne raison + termes matchés.
    
    Returns:
        (exclusion_reason, exclusion_terms) ou (None, [])
    """
    if not text or len(text.strip()) < 10:
        return (None, [])
    
    text_lower = text.lower()
    
    # Vérifier chaque catégorie d'exclusion
    exclusion_categories = {
        'hr_content': ['hr_content', 'hr_recruitment_terms'],
        'financial_generic': ['financial_generic', 'financial_reporting_terms'],
        'esg_generic': ['esg_generic'],
        'event_generic': ['event_generic'],
        'corporate_noise': ['corporate_noise_terms', 'anti_lai_routes']
    }
    
    for reason, scope_names in exclusion_categories.items():
        for scope_name in scope_names:
            scope_terms = _exclusion_scopes_cache.get(scope_name, [])
            for term in scope_terms:
                if term and term.lower() in text_lower:
                    return (reason, [term])
    
    return (None, [])


def _find_lai_keywords(text: str) -> List[str]:
    """
    Trouve les LAI keywords présents dans le texte.
    
    Returns:
        Liste des keywords trouvés (max 5 pour logs)
    """
    if not _lai_keywords_cache:
        raise RuntimeError("LAI keywords non initialisés")
    
    text_lower = text.lower()
    found = []
    
    for keyword in _lai_keywords_cache:
        if keyword.lower() in text_lower:
            found.append(keyword)
            if len(found) >= 5:  # Limiter pour logs
                break
    
    return found


    # DEPRECATED: Utiliser apply_ingestion_profile() avec matrice
    logger.warning("_apply_corporate_profile() deprecated, use apply_ingestion_profile()")
    return apply_ingestion_profile(items, source_meta, 'balanced')

def _filter_by_exclusions_only(items: List[Dict[str, Any]], source_key: str) -> List[Dict[str, Any]]:
    # DEPRECATED: Utiliser _filter_with_metrics()
    logger.warning("_filter_by_exclusions_only() deprecated, use _filter_with_metrics()")
    return _filter_with_metrics(items, source_key, exclusions_only=True)

def _filter_by_exclusions_and_lai(items: List[Dict[str, Any]], source_key: str) -> List[Dict[str, Any]]:
    # DEPRECATED: Utiliser _filter_with_metrics()
    logger.warning("_filter_by_exclusions_and_lai() deprecated, use _filter_with_metrics()")
    return _filter_with_metrics(items, source_key, exclusions_only=False)

def _apply_press_profile(items: List[Dict[str, Any]], source_meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    # DEPRECATED: Utiliser apply_ingestion_profile() avec matrice
    logger.warning("_apply_press_profile() deprecated, use apply_ingestion_profile()")
    return apply_ingestion_profile(items, source_meta, 'balanced')

def _filter_by_lai_keywords(items: List[Dict[str, Any]], source_key: str) -> List[Dict[str, Any]]:
    # DEPRECATED: Utiliser _filter_with_metrics()
    logger.warning("_filter_by_lai_keywords() deprecated, use _filter_with_metrics()")
    return _filter_with_metrics(items, source_key, exclusions_only=False)

def _contains_lai_keywords(text: str) -> bool:
    # DEPRECATED: Utiliser _find_lai_keywords()
    logger.warning("_contains_lai_keywords() deprecated, use _find_lai_keywords()")
    return len(_find_lai_keywords(text)) > 0

def _contains_exclusion_keywords(text: str) -> bool:
    # DEPRECATED: Utiliser _check_exclusions()
    logger.warning("_contains_exclusion_keywords() deprecated, use _check_exclusions()")
    reason, _ = _check_exclusions(text)
    return reason is not None

# Garder anciennes fonctions pour compatibilité
def _apply_corporate_profile_old(items: List[Dict[str, Any]], source_meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    """OLD VERSION - Applique le profil corporate avec différenciation pure/hybrid players."""
    source_key = source_meta.get('source_key', '')
    company_id = source_meta.get('company_id', '')
    is_pure = _is_pure_player(company_id)
    is_hybrid = _is_hybrid_player(company_id)
    
    if is_pure:
        return _filter_with_metrics(items, source_key, exclusions_only=True)
    else:
        return _filter_with_metrics(items, source_key, exclusions_only=False)


def _extract_main_content(title: str, content: str) -> str:
    """
    Extrait le contenu principal en excluant les métadonnées de contact.
    
    Supprime les sections typiques de métadonnées:
    - Coordonnées (Tel, Email, etc.)
    - Informations de contact ("For more information", "Contact:", etc.)
    - Signatures ("President & CEO", "Chief...", etc.)
    
    Args:
        title: Titre de l'article
        content: Contenu complet de l'article
    
    Returns:
        Contenu principal sans les métadonnées
    """
    # Patterns de métadonnées à exclure
    metadata_patterns = [
        r'For more information.*?(?=\n\n|$)',  # Section "For more information"
        r'Contact:.*?(?=\n\n|$)',  # Section "Contact:"
        r'Tel\.?\s*[:\+].*?(?=\n|$)',  # Numéros de téléphone
        r'Email:.*?(?=\n|$)',  # Emails
        r'[\w\s]+,\s*(?:President|CEO|Chief|Director).*?(?=\n|$)',  # Signatures avec titres
    ]
    
    import re
    main_content = content
    
    # Supprimer les patterns de métadonnées
    for pattern in metadata_patterns:
        main_content = re.sub(pattern, '', main_content, flags=re.IGNORECASE | re.DOTALL)
    
    # Combiner titre et contenu nettoyé
    result = f"{title} {main_content}".strip()
    
    return result


def get_profile_stats(items_before: int, items_after: int, source_meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcule les statistiques d'application du profil.
    """
    source_key = source_meta.get('source_key', '')
    source_type = source_meta.get('source_type', '')
    
    filtered_out = items_before - items_after
    retention_rate = (items_after / items_before * 100) if items_before > 0 else 0
    
    return {
        'source_key': source_key,
        'source_type': source_type,
        'items_before': items_before,
        'items_after': items_after,
        'items_filtered_out': filtered_out,
        'retention_rate': round(retention_rate, 1)
    }