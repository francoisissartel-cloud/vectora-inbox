import json
from datetime import datetime, timedelta

# Charger les items
with open('data/test_v173.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

print(f"=== ANALYSE EXTRACTION DATES v1.7.3 ===\n")
print(f"Total items: {len(items)}\n")

# Statistiques par source
by_source = {}
for item in items:
    source = item.get('date_extraction', {}).get('date_source', 'unknown')
    by_source[source] = by_source.get(source, 0) + 1

print("Distribution par source d'extraction:")
for source, count in sorted(by_source.items(), key=lambda x: -x[1]):
    pct = (count / len(items)) * 100
    print(f"  {source}: {count} ({pct:.1f}%)")

print(f"\n=== ANALYSE DÉTAILLÉE ===\n")

# Analyser les fallbacks
fallbacks = [i for i in items if i.get('date_extraction', {}).get('date_source') == 'ingestion_fallback']
print(f"Items en fallback: {len(fallbacks)}")

if fallbacks:
    print("\nExemples de titres en fallback:")
    for item in fallbacks[:5]:
        title = item['title'][:100]
        content = item['content'][:100]
        print(f"\n  Source: {item['source_key']}")
        print(f"  Titre: {title}")
        print(f"  Contenu: {content}")

# Vérifier fenêtre temporelle
cutoff = datetime(2026, 2, 10) - timedelta(days=30)
print(f"\n=== FILTRE TEMPOREL ===")
print(f"Date cutoff (30 jours): {cutoff.strftime('%Y-%m-%d')}")

dates_distribution = {}
for item in items:
    d = item['published_at']
    dates_distribution[d] = dates_distribution.get(d, 0) + 1

print(f"\nDates uniques: {len(dates_distribution)}")
for d in sorted(dates_distribution.keys()):
    count = dates_distribution[d]
    dt = datetime.strptime(d, '%Y-%m-%d')
    in_window = dt >= cutoff
    status = "✓ OK" if in_window else "✗ HORS"
    print(f"  {d}: {count} items [{status}]")

hors_fenetre = sum(1 for i in items if datetime.strptime(i['published_at'], '%Y-%m-%d') < cutoff)
print(f"\nItems hors fenêtre (devraient être filtrés): {hors_fenetre}")

# Taux de succès
success_rate = ((len(items) - len(fallbacks)) / len(items)) * 100
print(f"\n=== RÉSUMÉ ===")
print(f"Taux d'extraction réussi: {success_rate:.1f}%")
print(f"Taux de fallback: {(len(fallbacks) / len(items)) * 100:.1f}%")
print(f"Items à filtrer: {hors_fenetre}")
