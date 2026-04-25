import json
import sys

if len(sys.argv) < 2:
    print("Usage: python test_by_source.py <file.json>")
    sys.exit(1)

with open(sys.argv[1], encoding='utf-8') as f:
    data = json.load(f)

items = data if isinstance(data, list) else data.get('items', [])

# Grouper par source
by_source = {}
for item in items:
    source = item.get('source_key', 'unknown')
    if source not in by_source:
        by_source[source] = []
    by_source[source].append(item)

print("="*80)
print("TESTS PAR SOURCE")
print("="*80)

for source, source_items in sorted(by_source.items()):
    print(f"\n{source}: {len(source_items)} items")
    
    # Stats
    fallback = sum(1 for i in source_items if i.get('date_extraction', {}).get('date_source') in ['fallback', 'ingestion_fallback'])
    avg_conf = sum(i.get('date_extraction', {}).get('confidence', 0) for i in source_items) / len(source_items)
    avg_length = sum(len(i.get('content', '')) for i in source_items) / len(source_items)
    
    print(f"  Fallback: {fallback}/{len(source_items)} ({fallback/len(source_items)*100:.0f}%)")
    print(f"  Confiance: {avg_conf:.2f}")
    print(f"  Taille: {avg_length:.0f} chars")

print("\n" + "="*80)
