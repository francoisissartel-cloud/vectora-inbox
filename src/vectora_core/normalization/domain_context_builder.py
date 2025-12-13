"""
Domain Context Builder for LLM Domain Gating.

Constructs compact domain representations from client_config.watch_domains 
and canonical scopes for injection into Bedrock normalization prompts.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class DomainContext:
    """Compact representation of a domain for LLM evaluation."""
    domain_id: str
    domain_type: str
    priority: str
    description: str
    example_entities: Dict[str, List[str]]
    context_phrases: List[str]

class DomainContextBuilder:
    """Builds domain contexts from client config and canonical scopes."""
    
    def __init__(self, canonical_scopes: Dict[str, Any]):
        """
        Initialize with loaded canonical scopes.
        
        Args:
            canonical_scopes: Dictionary containing all canonical scope data
        """
        self.canonical_scopes = canonical_scopes
        
    def build_domain_contexts(self, watch_domains: List[Dict[str, Any]]) -> List[DomainContext]:
        """
        Build domain contexts for all watch_domains.
        
        Args:
            watch_domains: List of domain configurations from client_config
            
        Returns:
            List of DomainContext objects ready for LLM injection
        """
        contexts = []
        
        for domain_config in watch_domains:
            try:
                context = self._build_single_domain_context(domain_config)
                contexts.append(context)
                logger.info(f"Built context for domain: {context.domain_id}")
            except Exception as e:
                logger.error(f"Failed to build context for domain {domain_config.get('id', 'unknown')}: {e}")
                
        return contexts
    
    def _build_single_domain_context(self, domain_config: Dict[str, Any]) -> DomainContext:
        """Build context for a single domain."""
        domain_id = domain_config["id"]
        domain_type = domain_config["type"]
        priority = domain_config.get("priority", "medium")
        
        # Extract example entities from referenced scopes
        example_entities = {}
        context_phrases = []
        
        # Companies
        if "company_scope" in domain_config:
            companies = self._get_scope_examples(domain_config["company_scope"], "company_scopes", limit=10)
            if companies:
                example_entities["companies"] = companies
                
        # Molecules  
        if "molecule_scope" in domain_config:
            molecules = self._get_scope_examples(domain_config["molecule_scope"], "molecule_scopes", limit=8)
            if molecules:
                example_entities["molecules"] = molecules
                
        # Technologies
        if "technology_scope" in domain_config:
            technologies = self._get_technology_examples(domain_config["technology_scope"])
            if technologies:
                example_entities["technologies"] = technologies
                context_phrases.extend(self._get_technology_context_phrases(domain_config["technology_scope"]))
                
        # Indications
        if "indication_scope" in domain_config:
            indications = self._get_scope_examples(domain_config["indication_scope"], "indication_scopes", limit=8)
            if indications:
                example_entities["indications"] = indications
        
        # Build description
        description = self._build_domain_description(domain_type, domain_config, example_entities)
        
        return DomainContext(
            domain_id=domain_id,
            domain_type=domain_type,
            priority=priority,
            description=description,
            example_entities=example_entities,
            context_phrases=context_phrases
        )
    
    def _get_scope_examples(self, scope_key: str, scope_category: str, limit: int = 10) -> List[str]:
        """Get example entities from a scope."""
        try:
            scope_data = self.canonical_scopes.get(scope_category, {}).get(scope_key, [])
            if isinstance(scope_data, list):
                return scope_data[:limit]
            return []
        except Exception as e:
            logger.warning(f"Could not load scope {scope_key} from {scope_category}: {e}")
            return []
    
    def _get_technology_examples(self, scope_key: str, limit: int = 12) -> List[str]:
        """Get technology examples, handling complex technology scopes."""
        try:
            scope_data = self.canonical_scopes.get("technology_scopes", {}).get(scope_key, {})
            
            if isinstance(scope_data, dict):
                # Complex technology scope with categories
                examples = []
                
                # Core phrases (highest priority)
                core_phrases = scope_data.get("core_phrases", [])
                examples.extend(core_phrases[:6])
                
                # High precision terms
                high_precision = scope_data.get("technology_terms_high_precision", [])
                examples.extend(high_precision[:4])
                
                # Interval patterns (specific to LAI)
                intervals = scope_data.get("interval_patterns", [])
                examples.extend(intervals[:2])
                
                return examples[:limit]
            elif isinstance(scope_data, list):
                return scope_data[:limit]
                
            return []
        except Exception as e:
            logger.warning(f"Could not load technology scope {scope_key}: {e}")
            return []
    
    def _get_technology_context_phrases(self, scope_key: str) -> List[str]:
        """Get context phrases for technology domains."""
        try:
            scope_data = self.canonical_scopes.get("technology_scopes", {}).get(scope_key, {})
            
            if isinstance(scope_data, dict):
                metadata = scope_data.get("_metadata", {})
                description = metadata.get("description", "")
                if description:
                    return [description]
                    
            return []
        except Exception as e:
            logger.warning(f"Could not load technology context for {scope_key}: {e}")
            return []
    
    def _build_domain_description(self, domain_type: str, domain_config: Dict[str, Any], 
                                 example_entities: Dict[str, List[str]]) -> str:
        """Build a concise domain description for LLM context."""
        
        # Base descriptions by type
        type_descriptions = {
            "technology": "Technology domain focusing on specific formulations, delivery systems, or therapeutic approaches",
            "indication": "Therapeutic indication domain covering specific diseases or medical conditions", 
            "regulatory": "Regulatory domain covering approvals, guidelines, and compliance matters",
            "default": "General surveillance domain"
        }
        
        base_desc = type_descriptions.get(domain_type, type_descriptions["default"])
        
        # Add entity context
        entity_context = []
        if "companies" in example_entities:
            entity_context.append(f"Key companies: {', '.join(example_entities['companies'][:3])}")
        if "technologies" in example_entities:
            entity_context.append(f"Key technologies: {', '.join(example_entities['technologies'][:3])}")
            
        # Add notes if available
        notes = domain_config.get("notes", "")
        
        parts = [base_desc]
        if entity_context:
            parts.append(". " + "; ".join(entity_context))
        if notes:
            parts.append(f". {notes}")
            
        return "".join(parts)