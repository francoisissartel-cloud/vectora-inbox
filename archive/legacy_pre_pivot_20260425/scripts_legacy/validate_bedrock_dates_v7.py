#!/usr/bin/env python3
import json

with open('items_curated_v7.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

total = len(items)
with_extracted_date = 0
high_confidence = 0
using_bedrock_date = 0
fallback_used = 0

print(f"\n{'='*60}")
print(f"ANALYSE EXTRACTION DATES - lai_weekly_v7")
print(f"{'='*60}\n")

for item in items:
    nc = item.get('normalized_content', {})
    sr = item.get('scoring_results', {})
    
    extracted_date = nc.get('extracted_date')
    date_confidence = nc.get('date_confidence', 0.0)
    effective_date = sr.get('effective_date')
    published_at = item.get('published_at')
    
    if extracted_date:
        with_extracted_date += 1
        if date_confidence > 0.8:
            high_confidence += 1
    
    if effective_date and effective_date != published_at:
        using_bedrock_date += 1
    elif effective_date == published_at:
        fallback_used += 1

pct_extracted = (with_extracted_date / total * 100) if total > 0 else 0
pct_high_conf = (high_confidence / total * 100) if total > 0 else 0
pct_bedrock = (using_bedrock_date / total * 100) if total > 0 else 0
pct_fallback = (fallback_used / total * 100) if total > 0 else 0

print(f"Total items: {total}")
print(f"\nMétriques Extraction Dates:")
print(f"  - Dates Bedrock extraites: {with_extracted_date}/{total} ({pct_extracted:.1f}%)")
print(f"  - Haute confiance (>0.8): {high_confidence}/{total} ({pct_high_conf:.1f}%)")
print(f"  - Effective_date = Bedrock: {using_bedrock_date}/{total} ({pct_bedrock:.1f}%)")
print(f"  - Dates fallback utilisées: {fallback_used}/{total} ({pct_fallback:.1f}%)")

print(f"\n{'='*60}")
print(f"OBJECTIF: >95% dates extraites")
print(f"RÉSULTAT: {pct_extracted:.1f}% - {'✅ SUCCÈS' if pct_extracted >= 95 else '❌ ÉCHEC' if pct_extracted < 80 else '⚠️ PARTIEL'}")
print(f"{'='*60}\n")

print("Échantillon 5 premiers items:\n")
for i, item in enumerate(items[:5], 1):
    nc = item.get('normalized_content', {})
    sr = item.get('scoring_results', {})
    print(f"{i}. {item.get('title', 'N/A')[:60]}")
    print(f"   Published_at: {item.get('published_at')}")
    print(f"   Extracted_date: {nc.get('extracted_date')} (conf: {nc.get('date_confidence', 0):.2f})")
    print(f"   Effective_date: {sr.get('effective_date')}")
    print()
