#!/usr/bin/env python3
import json

with open('curated_items_e2e.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

print("=== SYNTHESE E2E TEST VECTORA INBOX LAI_WEEKLY_V3 ===")
print(f"Items traités: {len(items)}")

# Scores
scores = [item.get('scoring_results', {}).get('final_score', 0) for item in items]
scores.sort(reverse=True)
print(f"Scores - Max: {max(scores):.1f}, Min: {min(scores):.1f}, Moy: {sum(scores)/len(scores):.1f}")
print(f"Scores > 10: {len([s for s in scores if s > 10])}")

# Entités
companies = set()
trademarks = set()
molecules = set()
for item in items:
    entities = item.get('normalized_content', {}).get('entities', {})
    companies.update(entities.get('companies', []))
    trademarks.update(entities.get('trademarks', []))
    molecules.update(entities.get('molecules', []))

print(f"Entités - Companies: {len(companies)}, Trademarks: {len(trademarks)}, Molecules: {len(molecules)}")
print(f"Companies: {list(companies)}")
print(f"Trademarks: {list(trademarks)}")
print(f"Molecules: {list(molecules)}")

# Matching
matched_count = sum(1 for item in items if item.get('matching_results', {}).get('matched_domains'))
print(f"Items matchés: {matched_count}/{len(items)} ({matched_count/len(items)*100:.1f}%)")

# Top items
print("\nTOP 5 ITEMS:")
items_sorted = sorted(items, key=lambda x: x.get('scoring_results', {}).get('final_score', 0), reverse=True)
for i, item in enumerate(items_sorted[:5], 1):
    score = item.get('scoring_results', {}).get('final_score', 0)
    title = item.get('title', '')[:60]
    print(f"{i}. Score: {score:.1f} - {title}")