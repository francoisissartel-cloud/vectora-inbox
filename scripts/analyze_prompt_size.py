#!/usr/bin/env python3
"""
Analyse la taille des prompts Bedrock et estime les coûts
"""

import yaml
from pathlib import Path

def count_tokens_approx(text):
    """Approximation: 1 token ≈ 4 caractères pour Claude"""
    if isinstance(text, int):
        return text // 4
    return len(str(text)) // 4

def analyze_file(filepath):
    """Analyse un fichier YAML"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        data = yaml.safe_load(content)
    
    return {
        'size_bytes': len(content),
        'size_chars': len(content),
        'tokens_approx': count_tokens_approx(content),
        'data': data
    }

def main():
    repo_root = Path(__file__).parent.parent
    canonical_dir = repo_root / "canonical"
    
    print("="*80)
    print("ANALYSE TAILLE PROMPTS BEDROCK")
    print("="*80)
    print()
    
    # Analyser lai_domain_definition
    print("[1/3] Analyse lai_domain_definition.yaml...")
    domain_def_path = canonical_dir / "domains" / "lai_domain_definition.yaml"
    domain_def = analyze_file(domain_def_path)
    
    print(f"   Taille: {domain_def['size_bytes']:,} bytes")
    print(f"   Caracteres: {domain_def['size_chars']:,}")
    print(f"   Tokens (approx): {domain_def['tokens_approx']:,}")
    print()
    
    # Analyser lai_domain_scoring prompt
    print("[2/3] Analyse lai_domain_scoring.yaml...")
    scoring_path = canonical_dir / "prompts" / "domain_scoring" / "lai_domain_scoring.yaml"
    scoring = analyze_file(scoring_path)
    
    print(f"   Taille: {scoring['size_bytes']:,} bytes")
    print(f"   Caracteres: {scoring['size_chars']:,}")
    print(f"   Tokens (approx): {scoring['tokens_approx']:,}")
    print()
    
    # Calculer taille totale d'un prompt complet
    print("[3/3] Calcul prompt complet...")
    
    # Prompt = system + user_template + domain_definition + item data
    system_size = len(scoring['data'].get('system_instructions', ''))
    user_template_size = len(scoring['data'].get('user_template', ''))
    
    # Item data moyen (estimé)
    item_data_avg = 500  # Title + summary + entities
    
    # Total INPUT tokens
    total_input_chars = system_size + user_template_size + domain_def['size_chars'] + item_data_avg
    total_input_tokens = count_tokens_approx(total_input_chars)
    
    # OUTPUT tokens (réponse JSON)
    output_tokens_avg = 300  # JSON response
    
    print(f"   System instructions: {count_tokens_approx(system_size):,} tokens")
    print(f"   User template: {count_tokens_approx(user_template_size):,} tokens")
    print(f"   Domain definition: {domain_def['tokens_approx']:,} tokens")
    print(f"   Item data (avg): {count_tokens_approx(item_data_avg):,} tokens")
    print(f"   ---")
    print(f"   TOTAL INPUT: {total_input_tokens:,} tokens")
    print(f"   TOTAL OUTPUT: {output_tokens_avg:,} tokens")
    print()
    
    # Calcul des coûts
    print("="*80)
    print("ESTIMATION COUTS BEDROCK (Claude 3.5 Sonnet)")
    print("="*80)
    print()
    
    # Prix Claude 3.5 Sonnet (eu-west-3)
    price_input_per_1k = 0.003  # $3 per 1M tokens = $0.003 per 1K
    price_output_per_1k = 0.015  # $15 per 1M tokens = $0.015 per 1K
    
    cost_per_call_input = (total_input_tokens / 1000) * price_input_per_1k
    cost_per_call_output = (output_tokens_avg / 1000) * price_output_per_1k
    cost_per_call_total = cost_per_call_input + cost_per_call_output
    
    print(f"Prix par appel:")
    print(f"   Input:  ${cost_per_call_input:.6f} ({total_input_tokens:,} tokens)")
    print(f"   Output: ${cost_per_call_output:.6f} ({output_tokens_avg:,} tokens)")
    print(f"   TOTAL:  ${cost_per_call_total:.6f}")
    print()
    
    # Scénarios
    print("Scénarios mensuels:")
    print()
    
    scenarios = [
        ("Newsletter hebdo (30 items/semaine)", 30 * 4),
        ("Newsletter quotidienne (50 items/jour)", 50 * 30),
        ("Veille intensive (200 items/jour)", 200 * 30),
    ]
    
    for name, items_per_month in scenarios:
        # 2 appels Bedrock par item (normalization + scoring)
        calls_per_month = items_per_month * 2
        cost_per_month = calls_per_month * cost_per_call_total
        
        print(f"{name}:")
        print(f"   Items/mois: {items_per_month:,}")
        print(f"   Appels Bedrock: {calls_per_month:,}")
        print(f"   Cout: ${cost_per_month:.2f}/mois")
        print()
    
    # Latence
    print("="*80)
    print("ESTIMATION LATENCE")
    print("="*80)
    print()
    
    # Claude 3.5 Sonnet: ~50-100 tokens/sec
    tokens_per_sec = 75  # Moyenne
    
    input_time = total_input_tokens / tokens_per_sec
    output_time = output_tokens_avg / tokens_per_sec
    total_time = input_time + output_time
    
    print(f"Temps de traitement par appel:")
    print(f"   Input processing: {input_time:.2f}s")
    print(f"   Output generation: {output_time:.2f}s")
    print(f"   TOTAL: {total_time:.2f}s")
    print()
    
    print(f"Temps pour 30 items (workflow complet):")
    print(f"   Normalization (30 appels): {30 * total_time:.1f}s ({30 * total_time / 60:.1f} min)")
    print(f"   Scoring (30 appels): {30 * total_time:.1f}s ({30 * total_time / 60:.1f} min)")
    print(f"   TOTAL: {60 * total_time:.1f}s ({60 * total_time / 60:.1f} min)")
    print()
    
    # Recommandations
    print("="*80)
    print("RECOMMANDATIONS")
    print("="*80)
    print()
    
    if total_input_tokens > 10000:
        print("[WARNING] Prompt tres volumineux (>10K tokens)")
        print("   - Risque: Latence elevee")
        print("   - Risque: Couts eleves")
        print("   - Solution: Optimiser le canonical")
    elif total_input_tokens > 5000:
        print("[ATTENTION] Prompt volumineux (>5K tokens)")
        print("   - Impact modere sur latence et couts")
        print("   - Acceptable pour usage production")
    else:
        print("[OK] Taille de prompt raisonnable (<5K tokens)")
        print("   - Latence acceptable")
        print("   - Couts optimises")
    
    print()
    
    # Optimisations possibles
    print("OPTIMISATIONS POSSIBLES:")
    print()
    print("1. Reduire lai_domain_definition.yaml:")
    print("   - Garder seulement les termes essentiels")
    print("   - Supprimer les exemples redondants")
    print("   - Reduction possible: 30-40%")
    print()
    print("2. Utiliser embeddings pour matching:")
    print("   - Remplacer listes par recherche semantique")
    print("   - Reduction: 60-70%")
    print("   - Mais: complexite accrue")
    print()
    print("3. Cache Bedrock (Prompt Caching):")
    print("   - Cacher lai_domain_definition (change rarement)")
    print("   - Reduction cout: 90% sur input tokens caches")
    print("   - Disponible sur Claude 3.5 Sonnet")

if __name__ == "__main__":
    main()
