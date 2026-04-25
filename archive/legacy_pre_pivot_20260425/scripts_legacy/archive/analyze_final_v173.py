import json
from datetime import datetime, timedelta

# Charger les items
with open('data/test_v173_v2.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

print(f"=== ANALYSE FINALE v1.7.3 ===\n")
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

# Taux de fallback
fallbacks = [i for i in items if i.get('date_extraction', {}).get('date_source') == 'ingestion_fallback']
fallback_rate = (len(fallbacks) / len(items)) * 100

print(f"\n=== METRIQUES ===")
print(f"Taux de fallback: {fallback_rate:.1f}%")
print(f"Taux d'extraction reussi: {100 - fallback_rate:.1f}%")

# Vérifier fenêtre temporelle
cutoff = datetime(2026, 2, 10) - timedelta(days=30)
print(f"\nDate cutoff (30 jours): {cutoff.strftime('%Y-%m-%d')}")

dates_distribution = {}
for item in items:
    d = item['published_at']
    dates_distribution[d] = dates_distribution.get(d, 0) + 1

print(f"\nDates uniques: {len(dates_distribution)}")
for d in sorted(dates_distribution.keys()):
    count = dates_distribution[d]
    dt = datetime.strptime(d, '%Y-%m-%d')
    in_window = dt >= cutoff
    status = "OK" if in_window else "HORS"
    print(f"  {d}: {count} items [{status}]")

hors_fenetre = sum(1 for i in items if datetime.strptime(i['published_at'], '%Y-%m-%d') < cutoff)
print(f"\nItems hors fenetre (devraient etre 0): {hors_fenetre}")

# Exemples d'extraction réussie
print(f"\n=== EXEMPLES EXTRACTION REUSSIE ===")
success_items = [i for i in items if i.get('date_extraction', {}).get('date_source') != 'ingestion_fallback'][:3]
for item in success_items:
    print(f"\nSource: {item['source_key']}")
    print(f"Titre: {item['title'][:80]}")
    print(f"Date: {item['published_at']}")
    print(f"Extraction: {item['date_extraction']['date_source']} (confidence: {item['date_extraction']['confidence']})")

print(f"\n=== VALIDATION CRITERES ===")
print(f"Fallback rate < 20%: {'OK' if fallback_rate < 20 else 'ECHEC'} ({fallback_rate:.1f}%)")
print(f"Items hors fenetre = 0: {'OK' if hors_fenetre == 0 else 'ECHEC'} ({hors_fenetre})")
print(f"Dates extraites > 80%: {'OK' if (100 - fallback_rate) > 80 else 'ECHEC'} ({100 - fallback_rate:.1f}%)")
