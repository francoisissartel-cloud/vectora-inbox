#!/usr/bin/env python3
"""
Générateur de prompt flat pour LAI domain scoring v3.0
Consolide technology_scopes, trademark_scopes, exclusion_scopes en un prompt flat résolu.
"""

import yaml
from datetime import datetime
from pathlib import Path

def build_lai_scoring_prompt():
    """Génère le prompt YAML pour Bedrock scoring LAI."""
    
    base_path = Path(__file__).parent.parent.parent
    
    # Charger les scopes
    tech_path = base_path / "canonical/scopes/technology_scopes.yaml"
    trademark_path = base_path / "canonical/scopes/trademark_scopes.yaml"
    exclusion_path = base_path / "canonical/scopes/exclusion_scopes.yaml"
    
    tech = yaml.safe_load(tech_path.read_text(encoding='utf-8'))
    trademarks = yaml.safe_load(trademark_path.read_text(encoding='utf-8'))
    exclusions = yaml.safe_load(exclusion_path.read_text(encoding='utf-8'))
    
    # Extraire les termes
    lai_core = tech['lai_keywords']['core_phrases']
    lai_tech = tech['lai_keywords']['technology_terms_high_precision']
    lai_intervals = tech['lai_keywords']['interval_patterns']
    lai_trademarks = trademarks['lai_trademarks_global']
    lai_exclusions = exclusions['lai_exclude_noise'] + exclusions.get('anti_lai_routes', [])
    
    # Construire le prompt YAML
    prompt = f"""# LAI Domain Scoring Prompt v3.0 - Auto-generated
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Sources: technology_scopes.yaml, trademark_scopes.yaml, exclusion_scopes.yaml

metadata:
  prompt_id: "lai_domain_scoring"
  version: "3.0"
  created_date: "{datetime.now().strftime('%Y-%m-%d')}"
  description: "Flat prompt version - no company type distinction, simplified rules"
  auto_generated: true

system_instructions: |
  You are evaluating if a pharma/biotech news item is relevant to Long-Acting Injectables (LAI).
  
  LAI DEFINITION:
  Injectable pharmaceutical formulations providing sustained drug release over weeks to months 
  after a single injection. Improves patient adherence and therapeutic outcomes.
  
  Key characteristics:
  - Extended release: weeks to months duration
  - Injectable routes: SC, IM, intravitreal, intratumoral
  - Technologies: microspheres, depots, hydrogels, PEGylation, Fc fusion
  - Dosing: weekly, monthly, quarterly, semi-annual
  
  MATCHING LOGIC (simplified - NO company type distinction):
  
  1. STRONG SIGNALS (1+ detected = relevant)
     - Core LAI terms: {', '.join(lai_core)}
     - LAI trademarks: {', '.join(lai_trademarks)}
  
  2. MEDIUM SIGNALS (2+ detected = relevant)
     - Technology families: {', '.join(lai_tech)}
     - Dosing intervals: {', '.join(lai_intervals)}
  
  3. EXCLUSIONS (1+ detected = reject)
     - Anti-LAI terms: {', '.join(lai_exclusions)}
  
  SCORING RULES:
  - Base score by event_type:
    * partnership: 60
    * regulatory: 70
    * clinical_update: 50
    * corporate_move: 40
    * financial_results: 0 (only score if 2+ LAI signals)
    * other: 20
  
  - Entity boosts:
    * +20 if trademark detected
    * +15 if dosing_interval detected
    * +10 if technology_family detected
  
  - Recency boost:
    * +10 if item < 7 days old
    * +5 if item < 30 days old
  
  - Threshold: score >= 50 = relevant
  
  CRITICAL RULES:
  1. IGNORE company type (pure_player vs hybrid) - focus ONLY on LAI signals
  2. Manufacturing news WITHOUT LAI technology → REJECT
  3. Financial results WITHOUT 2+ LAI signals → REJECT
  4. Be conservative: when in doubt, REJECT
  5. Only detect signals EXPLICITLY present in the item data

user_template: |
  Evaluate this normalized item for LAI domain relevance and score it.

  NORMALIZED ITEM:
  Title: {{{{item_title}}}}
  Summary: {{{{item_summary}}}}
  Event Type: {{{{item_event_type}}}}
  Date: {{{{item_effective_date}}}}
  
  Entities Detected:
  - Companies: {{{{item_companies}}}}
  - Molecules: {{{{item_molecules}}}}
  - Technologies: {{{{item_technologies}}}}
  - Trademarks: {{{{item_trademarks}}}}
  - Indications: {{{{item_indications}}}}
  - Dosing Intervals: {{{{item_dosing_intervals}}}}

  RESPONSE FORMAT (JSON only, no additional text):
  {{
    "is_relevant": true,
    "score": 75,
    "reasoning": "Trademark UZEDY detected + microsphere technology + partnership event"
  }}

  If NOT relevant:
  {{
    "is_relevant": false,
    "score": 0,
    "reasoning": "Exclusion detected: oral tablet. Not LAI-relevant."
  }}

bedrock_config:
  max_tokens: 1000
  temperature: 0.0
  anthropic_version: "bedrock-2023-05-31"

validation_rules:
  - "Score must be 0-100"
  - "Reasoning must be concise and factual"
"""
    
    # Sauvegarder au bon endroit
    output_path = base_path / "canonical/prompts/domain_scoring/lai_domain_scoring.yaml"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(prompt, encoding='utf-8')
    
    print(f"[OK] Prompt YAML genere: {output_path.relative_to(base_path)}")
    print(f"[STATS] Termes:")
    print(f"  - Core LAI: {len(lai_core)}")
    print(f"  - Trademarks: {len(lai_trademarks)}")
    print(f"  - Technology: {len(lai_tech)}")
    print(f"  - Intervals: {len(lai_intervals)}")
    print(f"  - Exclusions: {len(lai_exclusions)}")
    print(f"  - TOTAL: {len(lai_core) + len(lai_trademarks) + len(lai_tech) + len(lai_intervals) + len(lai_exclusions)}")
    
    # Estimer tokens
    token_estimate = len(prompt) // 4
    print(f"[INFO] Taille prompt: {len(prompt)} chars (~{token_estimate} tokens)")
    
    return prompt

if __name__ == "__main__":
    build_lai_scoring_prompt()
