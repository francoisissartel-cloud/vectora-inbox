import json

with open('temp_items_v13.json', encoding='utf-8') as f:
    items_v13 = json.load(f)

with open('temp_items_v14.json', encoding='utf-8') as f:
    items_v14 = json.load(f)

print(f'V13: {len(items_v13)} items')
print(f'V14: {len(items_v14)} items\n')

print('=== COMPARISON V13 vs V14 ===\n')

# Comparer les 5 premiers items
for i in range(min(5, len(items_v13), len(items_v14))):
    item_v13 = items_v13[i]
    item_v14 = items_v14[i]
    
    print(f'--- ITEM {i+1}: {item_v13.get("title", "")[:60]}... ---')
    
    # V13
    ds_v13 = item_v13.get('domain_scoring', {})
    print(f'V13: score={ds_v13.get("score")}, relevant={ds_v13.get("is_relevant")}')
    print(f'     signals={ds_v13.get("signals_detected", {})}')
    
    # V14
    ds_v14 = item_v14.get('domain_scoring', {})
    print(f'V14: score={ds_v14.get("score")}, relevant={ds_v14.get("is_relevant")}')
    print(f'     signals={ds_v14.get("signals_detected", {})}')
    
    # Différence
    score_diff = ds_v14.get("score", 0) - ds_v13.get("score", 0)
    print(f'     DIFF: {score_diff:+.1f} points')
    print()

# Stats globales
v13_relevant = sum(1 for item in items_v13 if item.get('domain_scoring', {}).get('is_relevant'))
v14_relevant = sum(1 for item in items_v14 if item.get('domain_scoring', {}).get('is_relevant'))

v13_avg_score = sum(item.get('domain_scoring', {}).get('score', 0) for item in items_v13) / len(items_v13)
v14_avg_score = sum(item.get('domain_scoring', {}).get('score', 0) for item in items_v14) / len(items_v14)

print('=== GLOBAL STATS ===')
print(f'V13: {v13_relevant}/{len(items_v13)} relevant ({v13_relevant/len(items_v13)*100:.1f}%), avg score={v13_avg_score:.1f}')
print(f'V14: {v14_relevant}/{len(items_v14)} relevant ({v14_relevant/len(items_v14)*100:.1f}%), avg score={v14_avg_score:.1f}')
