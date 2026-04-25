import json

with open('items_ingested_v1.9_stable_reference.json', encoding='utf-8') as f:
    items = json.load(f)

print(f"=== ANALYSE DETAILLEE - {len(items)} items ===\n")

sources = {}
for item in items:
    source = item.get('source_key', 'unknown')
    if source not in sources:
        sources[source] = []
    sources[source].append(item)

for source, source_items in sorted(sources.items()):
    print(f"\n{'='*60}")
    print(f"SOURCE: {source} ({len(source_items)} items)")
    print('='*60)
    
    for i, item in enumerate(source_items, 1):
        title = item.get('title', '')
        content = item.get('content', '')
        effective_date = item.get('effective_date', '')
        confidence = item.get('date_extraction', {}).get('confidence', 0)
        
        print(f"\nItem {i}:")
        print(f"  Titre: {title[:80]}{'...' if len(title) > 80 else ''}")
        print(f"  Titre longueur: {len(title)} chars")
        print(f"  Contenu longueur: {len(content)} chars")
        print(f"  Date effective: {effective_date}")
        print(f"  Confiance date: {confidence}")
        print(f"  Titre OK: {'OUI' if len(title) > 10 else 'NON'}")
        print(f"  Contenu OK: {'OUI' if len(content) > 50 else 'NON'}")
        print(f"  Date OK: {'OUI' if effective_date and len(effective_date) == 10 else 'NON'}")
        print(f"  Confiance OK: {'OUI' if confidence >= 0.60 else 'NON'}")

print(f"\n\n{'='*60}")
print("RESUME PAR SOURCE")
print('='*60)
for source, source_items in sorted(sources.items()):
    print(f"{source}: {len(source_items)} items")
