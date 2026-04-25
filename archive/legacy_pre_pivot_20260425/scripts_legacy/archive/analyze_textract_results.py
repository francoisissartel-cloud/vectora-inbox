import json
from datetime import datetime, timedelta

# Charger items
items = json.load(open('data/test_v175.json', 'r', encoding='utf-8'))

print("=== ANALYSE EFFICACITE TEXTRACT v1.7.5 ===")
print(f"\nTotal items: {len(items)}\n")

# 1. Distribution extraction dates
by_source = {}
for item in items:
    src = item.get('date_extraction', {}).get('date_source', 'unknown')
    by_source[src] = by_source.get(src, 0) + 1

print("1. EXTRACTION DATES:")
for src, count in sorted(by_source.items(), key=lambda x: -x[1]):
    pct = count * 100 / len(items)
    print(f"   {src}: {count} ({pct:.1f}%)")

fallback = by_source.get('ingestion_fallback', 0)
fallback_rate = fallback * 100 / len(items)
print(f"\n   Fallback rate: {fallback_rate:.1f}%")
print(f"   Target: <20% | {'OK' if fallback_rate < 20 else 'ECHEC'}")

# 2. Contenu PDFs
print("\n2. CONTENU PDFs:")
pdf_sources = ['medincell', 'pfizer', 'nanexa']
pdf_items = [i for i in items if any(s in i['source_key'] for s in pdf_sources)]

if pdf_items:
    avg_length = sum(len(i['content']) for i in pdf_items) / len(pdf_items)
    print(f"   Items PDF: {len(pdf_items)}")
    print(f"   Longueur moyenne: {avg_length:.0f} chars")
    print(f"   Target: >1000 chars | {'OK' if avg_length > 1000 else 'ECHEC'}")
    
    # Exemple
    example = pdf_items[0]
    print(f"\n   Exemple: {example['source_key']}")
    print(f"   - Titre: {example['title'][:60]}...")
    print(f"   - Contenu: {len(example['content'])} chars")
    print(f"   - Date: {example['published_at']}")
    print(f"   - Source: {example.get('date_extraction', {}).get('date_source')}")
else:
    print("   Aucun item PDF trouve")

# 3. Dates extraites depuis PDFs
print("\n3. DATES EXTRAITES PDFs:")
pdf_with_dates = [
    i for i in pdf_items 
    if i.get('date_extraction', {}).get('date_source') in ['title_content_extraction', 'html_metadata']
]
pdf_date_rate = len(pdf_with_dates) * 100 / len(pdf_items) if pdf_items else 0
print(f"   PDFs avec date extraite: {len(pdf_with_dates)}/{len(pdf_items)}")
print(f"   Taux: {pdf_date_rate:.1f}%")
print(f"   Target: >80% | {'OK' if pdf_date_rate > 80 else 'ECHEC'}")

# 4. Filtrage temporel
print("\n4. FILTRAGE TEMPOREL:")
cutoff = datetime(2026, 2, 10) - timedelta(days=30)
hors_fenetre = sum(
    1 for i in items 
    if datetime.strptime(i['published_at'], '%Y-%m-%d') < cutoff
)
print(f"   Date cutoff: {cutoff.strftime('%Y-%m-%d')}")
print(f"   Items hors fenetre: {hors_fenetre}")
print(f"   Target: 0 | {'OK' if hors_fenetre == 0 else 'ECHEC'}")

# 5. Comparaison v1.7.4 vs v1.7.5
print("\n5. COMPARAISON v1.7.4 -> v1.7.5:")
try:
    items_v174 = json.load(open('data/test_v174.json', 'r', encoding='utf-8'))
    fallback_v174 = sum(
        1 for i in items_v174 
        if i.get('date_extraction', {}).get('date_source') == 'ingestion_fallback'
    )
    fallback_rate_v174 = fallback_v174 * 100 / len(items_v174)
    
    print(f"   v1.7.4 Fallback: {fallback_rate_v174:.1f}%")
    print(f"   v1.7.5 Fallback: {fallback_rate:.1f}%")
    improvement = fallback_rate_v174 - fallback_rate
    print(f"   Amelioration: {improvement:.1f} points")
    print(f"   Target: >50 points | {'OK' if improvement > 50 else 'ECHEC'}")
except:
    print("   Pas de donnees v1.7.4 pour comparaison")

# 6. Resume GO/NO-GO
print("\n" + "="*50)
print("RESUME GO/NO-GO")
print("="*50)

criteria = [
    ("Fallback rate < 20%", fallback_rate < 20),
    ("Contenu PDF > 1000 chars", avg_length > 1000 if pdf_items else False),
    ("Dates PDFs > 80%", pdf_date_rate > 80),
    ("Items hors fenêtre = 0", hors_fenetre == 0),
]

for criterion, passed in criteria:
    status = "OK" if passed else "KO"
    print(f"{status} {criterion}")

success_rate = sum(1 for _, p in criteria if p) / len(criteria) * 100
print(f"\nTaux de succes: {success_rate:.0f}%")

if success_rate >= 75:
    print("\nDECISION: GO PRODUCTION")
else:
    print("\nDECISION: ANALYSE REQUISE")
