#!/usr/bin/env python3
"""Script diagnostic pour inspecter réponse Bedrock"""

import sys
import json
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src_v2"))

from vectora_core.shared import config_loader, s3_io
from vectora_core.normalization.bedrock_client import BedrockNormalizationClient

# Test avec un item simple
test_item = {
    'title': 'Teva and MedinCell Announce FDA Submission for Once-Monthly Olanzapine LAI',
    'content': 'Teva Pharmaceuticals and MedinCell announced the submission of a New Drug Application to the FDA for their once-monthly olanzapine extended-release injectable suspension using BEPO technology.'
}

config_bucket = 'vectora-inbox-config-dev'
client_id = 'lai_weekly_v9'

# Charger configs
client_config = config_loader.load_client_config(client_id, config_bucket)
canonical_scopes = config_loader.load_canonical_scopes(config_bucket)

# Créer client Bedrock
bedrock_client = BedrockNormalizationClient(
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    region="us-east-1",
    s3_io=s3_io,
    client_config=client_config,
    canonical_scopes=canonical_scopes,
    config_bucket=config_bucket
)

# Normaliser
item_text = f"TITLE: {test_item['title']}\\n\\nCONTENT: {test_item['content']}"
result = bedrock_client.normalize_item(
    item_text=item_text,
    canonical_examples={},
    item=test_item
)

print("="*80)
print("RESULTAT NORMALISATION BEDROCK")
print("="*80)
print(json.dumps(result, indent=2, ensure_ascii=False))

print("\n" + "="*80)
print("ANALYSE")
print("="*80)
print(f"Companies detectees: {result.get('companies_detected', [])}")
print(f"Technologies detectees: {result.get('technologies_detected', [])}")
print(f"Dosing intervals detectes: {result.get('dosing_intervals_detected', [])}")
print(f"Trademarks detectes: {result.get('trademarks_detected', [])}")
