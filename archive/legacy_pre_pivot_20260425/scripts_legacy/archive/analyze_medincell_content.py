import json
import re

items = json.load(open('data/test_v174.json', 'r', encoding='utf-8'))
med = [i for i in items if 'medincell' in i['source_key']][0]

print("=== ANALYSE CONTENU MEDINCELL ENRICHI ===\n")
print(f"Title: {med['title'][:100]}")
print(f"Content length: {len(med['content'])} chars")
print(f"Date source: {med.get('date_extraction', {}).get('date_source')}")
print(f"Published: {med['published_at']}\n")

# Afficher les 1000 premiers chars
print("=== DEBUT DU CONTENU ===")
with open('data/medincell_content_sample.txt', 'w', encoding='utf-8') as f:
    f.write(med['content'][:1000])
print("Sauvegarde dans data/medincell_content_sample.txt")

# Chercher des dates
patterns = [
    (r'(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})', 'DD Month YYYY'),
    (r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})', 'Month DD, YYYY'),
    (r'(\d{4}-\d{2}-\d{2})', 'YYYY-MM-DD'),
    (r'(\d{1,2}/\d{1,2}/\d{4})', 'DD/MM/YYYY'),
]

print("\n=== RECHERCHE DE DATES ===")
for pattern, desc in patterns:
    matches = re.findall(pattern, med['content'], re.IGNORECASE)
    if matches:
        print(f"{desc}: {matches[:3]}")
    else:
        print(f"{desc}: Aucune")
