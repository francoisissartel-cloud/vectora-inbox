#!/usr/bin/env python3
import json
import yaml

# Charger le prompt LAI
with open('lai_prompt_s3.yaml', 'r', encoding='utf-8') as f:
    prompt_template = yaml.safe_load(f)

# Simuler un item
item_text = """TITLE: Medincell Partner Teva Pharmaceuticals Announces NDA Submission

CONTENT: December 9, 2025 - Teva Pharmaceuticals announced the submission of a New Drug Application to the U.S. FDA for olanzapine extended-release injectable suspension."""

# Construire le prompt
user_template = prompt_template['user_template']
prompt = user_template.replace('{{item_text}}', item_text)

# Remplacer les références par des exemples
prompt = prompt.replace('{{ref:lai_keywords.core_phrases}}', 'long-acting injectable, extended-release')
prompt = prompt.replace('{{ref:lai_keywords.technology_terms_high_precision}}', 'depot injection, microspheres')
prompt = prompt.replace('{{ref:lai_companies_global}}', 'MedinCell, Camurus, Teva')
prompt = prompt.replace('{{ref:lai_molecules_global}}', 'olanzapine, buprenorphine')
prompt = prompt.replace('{{ref:lai_trademarks_global}}', 'UZEDY, Aristada')
prompt = prompt.replace('{{ref:lai_keywords.negative_terms}}', 'oral tablet, capsule')

print("="*60)
print("PROMPT CONSTRUIT:")
print("="*60)
print(prompt)
print("\n" + "="*60)
print("VÉRIFICATION:")
print("="*60)
print(f"- 'extracted_date' présent: {'extracted_date' in prompt}")
print(f"- 'date_confidence' présent: {'date_confidence' in prompt}")
print(f"- 'Extract publication date' présent: {'Extract publication date' in prompt}")
print(f"- Format JSON exemple présent: {'{' in prompt and 'extracted_date' in prompt}")
