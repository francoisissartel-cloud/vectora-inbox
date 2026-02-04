import json

with open('temp_items_v14.json', encoding='utf-8') as f:
    items = json.load(f)

print(f'Total items: {len(items)}\n')

item = items[0]

print('=== TOP-LEVEL KEYS ===')
for key in sorted(item.keys()):
    print(f'  - {key}')

print('\n=== CHECKING FOR ENTITY FIELDS ===')
entity_fields = ['companies_detected', 'technologies_detected', 'dosing_intervals_detected', 
                 'entities_detected', 'companies', 'technologies']
for field in entity_fields:
    if field in item:
        print(f'[OK] {field}: {item[field]}')
    else:
        print(f'[MISSING] {field}')

print('\n=== METADATA CONTENT ===')
if 'metadata' in item:
    print(f'Metadata keys: {list(item["metadata"].keys())}')
    for key in item['metadata'].keys():
        if 'compan' in key.lower() or 'tech' in key.lower() or 'entity' in key.lower():
            print(f'  {key}: {item["metadata"][key]}')

print('\n=== NORMALIZED_CONTENT SAMPLE ===')
if 'normalized_content' in item:
    nc = item['normalized_content']
    print(f'Type: {type(nc)}')
    if isinstance(nc, str):
        print(f'Length: {len(nc)}')
        print(f'First 300 chars: {nc[:300]}')
    elif isinstance(nc, dict):
        print(f'Keys: {list(nc.keys())}')
        for key in nc.keys():
            if 'compan' in key.lower() or 'tech' in key.lower() or 'entity' in key.lower():
                print(f'  {key}: {nc[key]}')

print('\n=== DOMAIN_SCORING ===')
if 'domain_scoring' in item:
    ds = item['domain_scoring']
    print(f'is_relevant: {ds.get("is_relevant")}')
    print(f'score: {ds.get("score")}')
    print(f'signals_detected: {ds.get("signals_detected")}')
    print(f'score_breakdown: {ds.get("score_breakdown")}')
