import sys
import yaml
sys.path.append('src_v2')

from vectora_core.normalization.bedrock_matcher import match_item_to_domains_bedrock
from vectora_core.shared import config_loader

# Charger les prompts canoniques
with open('canonical/prompts/global_prompts.yaml', 'r', encoding='utf-8') as f:
    canonical_prompts = yaml.safe_load(f)

print(f"Prompts chargés: {list(canonical_prompts.keys())}")
print(f"Matching prompts: {list(canonical_prompts.get('matching', {}).keys())}")

# Item test simple
test_item = {
    "title": "Nanexa and Moderna Partnership",
    "normalized_content": {
        "entities": {
            "companies": ["Nanexa", "Moderna"],
            "technologies": ["PharmaShell"]
        }
    }
}

# Configuration test
watch_domains = [
    {
        "id": "tech_lai_ecosystem",
        "type": "technology",
        "company_scope": "lai_companies_global",
        "min_domain_score": 0.25
    }
]

# Configuration matching
matching_config = {
    "min_domain_score": 0.25
}

# Test
result = match_item_to_domains_bedrock(
    test_item, watch_domains, {}, matching_config, canonical_prompts, 
    "anthropic.claude-3-sonnet-20240229-v1:0"
)

print(f"Résultat: {result}")