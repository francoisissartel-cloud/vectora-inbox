import json

with open('curated_items_post_correction.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

print(f"=== ANALYSE POST-CORRECTION ===")
print(f"Items analysés: {len(items)}")

# Analyse des final_score
scores = []
items_with_score = 0
items_with_matched_domains = 0
items_with_errors = 0

for item in items:
    scoring_results = item.get("scoring_results", {})
    final_score = scoring_results.get("final_score", 0)
    matched_domains = item.get("matching_results", {}).get("matched_domains", [])
    
    if "error" in scoring_results:
        items_with_errors += 1
        print(f"Erreur: {item.get('item_id')} - {scoring_results.get('error')}")
    
    if matched_domains:
        items_with_matched_domains += 1
        
    if final_score > 0:
        items_with_score += 1
        scores.append(final_score)

print(f"\nRésultats:")
print(f"   Items avec matched_domains: {items_with_matched_domains}")
print(f"   Items avec final_score > 0: {items_with_score}")
print(f"   Items avec erreurs: {items_with_errors}")

if scores:
    print(f"   Score min: {min(scores):.1f}")
    print(f"   Score max: {max(scores):.1f}")
    print(f"   Score moyen: {sum(scores)/len(scores):.1f}")
    
    # Items sélectionnables
    selectable = [s for s in scores if s >= 12]
    print(f"   Items sélectionnables (>= 12): {len(selectable)}")

# Validation correction
correction_success = (items_with_score > 0 and items_with_errors == 0)
print(f"\nCORRECTION: {'RÉUSSIE' if correction_success else 'ÉCHOUÉE'}")

# Détail des items avec matched_domains
print(f"\nDétail items matchés:")
for item in items:
    matched_domains = item.get("matching_results", {}).get("matched_domains", [])
    final_score = item.get("scoring_results", {}).get("final_score", 0)
    lai_score = item.get("normalized_content", {}).get("lai_relevance_score", 0)
    
    if matched_domains:
        title = item.get("title", "")[:50]
        print(f"   {title}... | LAI:{lai_score} → Final:{final_score:.1f}")