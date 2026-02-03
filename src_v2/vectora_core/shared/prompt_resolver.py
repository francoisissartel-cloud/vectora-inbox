"""
Module de résolution des prompts pré-construits avec références dynamiques.

Résout les références {{ref:scope_name}} vers les scopes canonical.
Approche B: Configuration > Code
"""

import logging
import re
import yaml
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def load_prompt_template(prompt_type: str, vertical: str, s3_io, config_bucket: str) -> Optional[Dict[str, Any]]:
    """
    Charge un prompt template depuis canonical/prompts/.
    
    Args:
        prompt_type: Type de prompt (normalization, matching)
        vertical: Verticale métier (lai, gene_therapy, etc.)
        s3_io: Module s3_io pour accès S3
        config_bucket: Bucket S3 de configuration
    
    Returns:
        Dict contenant le prompt template ou None si non trouvé
    """
    try:
        # Chemin du prompt spécifique
        prompt_key = f"canonical/prompts/{prompt_type}/{vertical}.yaml"
        prompt_data = s3_io.read_yaml_from_s3(config_bucket, prompt_key)
        
        if prompt_data:
            logger.info(f"Prompt template chargé: {prompt_key}")
            return prompt_data
        
        # Fallback sur global_prompts.yaml
        logger.warning(f"Prompt {prompt_key} non trouvé, fallback sur global_prompts.yaml")
        return None
        
    except Exception as e:
        logger.error(f"Erreur chargement prompt template: {e}")
        return None


def resolve_references(template: str, canonical_scopes: Dict[str, Any]) -> str:
    """
    Résout les références {{ref:scope_name}} dans un template.
    
    Args:
        template: Template avec références {{ref:}}
        canonical_scopes: Scopes canonical chargés
    
    Returns:
        Template avec références résolues
    """
    # Pattern pour détecter {{ref:scope.path}}
    pattern = r'\{\{ref:([^}]+)\}\}'
    
    def replace_ref(match):
        ref_path = match.group(1)
        value = _resolve_scope_path(ref_path, canonical_scopes)
        return _format_scope_value(value)
    
    return re.sub(pattern, replace_ref, template)


def _resolve_scope_path(path: str, scopes: Dict[str, Any]) -> Any:
    """Résout un chemin de scope (ex: company_scopes.lai_companies_global)."""
    parts = path.split('.')
    
    # Cas 1: Scope direct (ex: lai_companies_global)
    if len(parts) == 1:
        scope_name = parts[0]
        # Chercher dans toutes les catégories
        for category in scopes.values():
            if isinstance(category, dict) and scope_name in category:
                return category[scope_name]
        logger.warning(f"Scope direct non trouvé: {scope_name}")
        return f"[SCOPE_NOT_FOUND: {path}]"
    
    # Cas 2: Path avec catégorie (ex: company_scopes.lai_companies_global)
    # Format: category_name.scope_name
    if len(parts) == 2:
        category_name, scope_name = parts
        # Chercher la catégorie
        if category_name in scopes:
            category = scopes[category_name]
            if isinstance(category, dict) and scope_name in category:
                logger.info(f"Scope résolu: {path}")
                return category[scope_name]
        logger.warning(f"Scope path non trouvé: {path} (catégorie={category_name}, scope={scope_name})")
        return f"[SCOPE_NOT_FOUND: {path}]"
    
    # Cas 3: Path imbriqué profond (ex: lai_keywords.core_phrases.terms)
    value = scopes
    for part in parts:
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            # Chercher dans toutes les catégories
            found = False
            for category in scopes.values():
                if isinstance(category, dict) and part in category:
                    value = category[part]
                    found = True
                    break
            if not found:
                logger.warning(f"Scope path non trouvé: {path}")
                return f"[SCOPE_NOT_FOUND: {path}]"
    
    return value


def _format_scope_value(value: Any) -> str:
    """Formate une valeur de scope pour insertion dans prompt."""
    if isinstance(value, list):
        return '\n'.join(f"- {item}" for item in value)
    elif isinstance(value, dict):
        return '\n'.join(f"- {k}: {v}" for k, v in value.items())
    else:
        return str(value)


def build_prompt(prompt_template: Dict[str, Any], canonical_scopes: Dict[str, Any], 
                 variables: Dict[str, str]) -> str:
    """
    Construit le prompt final avec résolution des références et substitution des variables.
    
    Args:
        prompt_template: Template de prompt chargé
        canonical_scopes: Scopes canonical
        variables: Variables à substituer ({{item_text}}, etc.)
    
    Returns:
        Prompt final prêt pour Bedrock
    """
    # Récupérer le user_template
    user_template = prompt_template.get('user_template', '')
    
    # Étape 1: Résoudre les références {{ref:}}
    resolved = resolve_references(user_template, canonical_scopes)
    
    # Étape 2: Substituer les variables {{variable}}
    for var_name, var_value in variables.items():
        placeholder = f"{{{{{var_name}}}}}"
        resolved = resolved.replace(placeholder, var_value)
    
    return resolved
