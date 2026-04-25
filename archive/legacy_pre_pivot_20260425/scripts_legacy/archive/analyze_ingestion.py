"""
Analyse détaillée des résultats d'ingestion - Phase 6
Affiche toutes les statistiques: dates, contenu, sources, types, etc.
"""
import json
import sys
from pathlib import Path
from collections import Counter
from datetime import datetime

def analyze_ingestion(output_file: str):
    """Analyse complète des résultats d'ingestion"""
    
    if not Path(output_file).exists():
        print(f"ERREUR: Fichier non trouvé: {output_file}")
        return False
    
    with open(output_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Support both formats: {"items": [...]} or [...]
    if isinstance(data, list):
        items = data
    else:
        items = data.get('items', [])
    total = len(items)
    
    if total == 0:
        print("ERREUR: Aucun item trouvé")
        return False
    
    print("\n" + "="*80)
    print("ANALYSE DETAILLEE INGESTION - PHASE 6")
    print("="*80)
    print(f"Fichier: {output_file}")
    print(f"Date analyse: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total items: {total}")
    print("="*80)
    
    # 1. SOURCES
    print("\n[1] SOURCES")
    print("-"*80)
    sources = Counter(item.get('source_key', 'unknown') for item in items)
    for source, count in sources.most_common():
        pct = count / total * 100
        print(f"  {source:40s}: {count:4d} items ({pct:5.1f}%)")
    
    # 2. TYPES DE SOURCES
    print("\n[2] TYPES DE SOURCES")
    print("-"*80)
    source_types = Counter(item.get('source_type', 'unknown') for item in items)
    for stype, count in source_types.most_common():
        pct = count / total * 100
        print(f"  {stype:40s}: {count:4d} items ({pct:5.1f}%)")
    
    # 3. EXTRACTION DATES
    print("\n[3] EXTRACTION DATES - SOURCES")
    print("-"*80)
    date_sources = Counter(
        item.get('date_extraction', {}).get('date_source', 'unknown') 
        for item in items
    )
    for source, count in date_sources.most_common():
        pct = count / total * 100
        check = "OK" if source not in ['fallback', 'ingestion_fallback'] else "!!"
        print(f"  [{check}] {source:35s}: {count:4d} items ({pct:5.1f}%)")
    
    fallback_count = sum(
        count for source, count in date_sources.items() 
        if 'fallback' in source
    )
    fallback_pct = fallback_count / total * 100
    print(f"\n  TOTAL FALLBACK: {fallback_count} items ({fallback_pct:.1f}%)")
    if fallback_pct < 10:
        print(f"  OBJECTIF ATTEINT: < 10% fallback")
    else:
        print(f"  OBJECTIF NON ATTEINT: >= 10% fallback")
    
    # 4. CONFIANCE EXTRACTION DATES
    print("\n[4] CONFIANCE EXTRACTION DATES")
    print("-"*80)
    confidences = [
        item.get('date_extraction', {}).get('confidence', 0) 
        for item in items
    ]
    avg_conf = sum(confidences) / len(confidences)
    print(f"  Moyenne:  {avg_conf:.3f}")
    print(f"  Min:      {min(confidences):.3f}")
    print(f"  Max:      {max(confidences):.3f}")
    print(f"  Médiane:  {sorted(confidences)[len(confidences)//2]:.3f}")
    
    # Distribution par tranches
    conf_ranges = {
        '0.90-1.00 (Excellent)': sum(1 for c in confidences if c >= 0.90),
        '0.80-0.89 (Bon)': sum(1 for c in confidences if 0.80 <= c < 0.90),
        '0.60-0.79 (Moyen)': sum(1 for c in confidences if 0.60 <= c < 0.80),
        '0.01-0.59 (Faible)': sum(1 for c in confidences if 0 < c < 0.60),
        '0.00 (Fallback)': sum(1 for c in confidences if c == 0)
    }
    print("\n  Distribution:")
    for range_name, count in conf_ranges.items():
        pct = count / total * 100
        print(f"    {range_name:25s}: {count:4d} items ({pct:5.1f}%)")
    
    # 5. DATES DE PUBLICATION
    print("\n[5] DATES DE PUBLICATION")
    print("-"*80)
    pub_dates = [item.get('published_at', '') for item in items if item.get('published_at')]
    if pub_dates:
        pub_dates_sorted = sorted(pub_dates)
        print(f"  Plus ancienne: {pub_dates_sorted[0]}")
        print(f"  Plus récente:  {pub_dates_sorted[-1]}")
        
        # Distribution par mois
        months = Counter(date[:7] for date in pub_dates if len(date) >= 7)
        print(f"\n  Distribution par mois (top 10):")
        for month, count in months.most_common(10):
            pct = count / len(pub_dates) * 100
            print(f"    {month}: {count:4d} items ({pct:5.1f}%)")
    
    # 6. CONTENU - TAILLE
    print("\n[6] TAILLE DU CONTENU")
    print("-"*80)
    content_lengths = [len(item.get('content', '')) for item in items]
    word_counts = [item.get('metadata', {}).get('word_count', 0) for item in items]
    
    print(f"  Caractères:")
    print(f"    Moyenne:  {sum(content_lengths) / len(content_lengths):.0f} chars")
    print(f"    Min:      {min(content_lengths)} chars")
    print(f"    Max:      {max(content_lengths)} chars")
    print(f"    Médiane:  {sorted(content_lengths)[len(content_lengths)//2]} chars")
    
    print(f"\n  Mots:")
    print(f"    Moyenne:  {sum(word_counts) / len(word_counts):.0f} mots")
    print(f"    Min:      {min(word_counts)} mots")
    print(f"    Max:      {max(word_counts)} mots")
    print(f"    Médiane:  {sorted(word_counts)[len(word_counts)//2]} mots")
    
    # Distribution par taille
    size_ranges = {
        '< 500 chars': sum(1 for l in content_lengths if l < 500),
        '500-1000 chars': sum(1 for l in content_lengths if 500 <= l < 1000),
        '1000-2000 chars': sum(1 for l in content_lengths if 1000 <= l < 2000),
        '2000-3000 chars': sum(1 for l in content_lengths if 2000 <= l < 3000),
        '>= 3000 chars': sum(1 for l in content_lengths if l >= 3000)
    }
    print(f"\n  Distribution par taille:")
    for range_name, count in size_ranges.items():
        pct = count / total * 100
        print(f"    {range_name:20s}: {count:4d} items ({pct:5.1f}%)")
    
    # 7. TYPES DE CONTENU
    print("\n[7] TYPES DE CONTENU")
    print("-"*80)
    content_types = Counter(
        item.get('metadata', {}).get('content_type', 'html') 
        for item in items
    )
    for ctype, count in content_types.most_common():
        pct = count / total * 100
        print(f"  {ctype:40s}: {count:4d} items ({pct:5.1f}%)")
    
    # 8. LANGUES
    print("\n[8] LANGUES")
    print("-"*80)
    languages = Counter(item.get('language', 'unknown') for item in items)
    for lang, count in languages.most_common():
        pct = count / total * 100
        print(f"  {lang:40s}: {count:4d} items ({pct:5.1f}%)")
    
    # 9. EFFECTIVE DATES
    print("\n[9] EFFECTIVE DATES (dates événements)")
    print("-"*80)
    eff_dates = [item.get('effective_date') for item in items]
    with_eff = sum(1 for d in eff_dates if d)
    without_eff = sum(1 for d in eff_dates if not d)
    print(f"  Avec effective_date:    {with_eff:4d} items ({with_eff/total*100:5.1f}%)")
    print(f"  Sans effective_date:    {without_eff:4d} items ({without_eff/total*100:5.1f}%)")
    
    # 10. URLS
    print("\n[10] URLS - PATTERNS")
    print("-"*80)
    urls = [item.get('url', '') for item in items]
    domains = Counter(url.split('/')[2] if len(url.split('/')) > 2 else 'unknown' for url in urls if url)
    print(f"  Top 10 domaines:")
    for domain, count in domains.most_common(10):
        pct = count / len(urls) * 100
        print(f"    {domain:50s}: {count:4d} ({pct:5.1f}%)")
    
    # Détection PDF dans URLs
    pdf_urls = sum(1 for url in urls if '.pdf' in url.lower())
    print(f"\n  URLs PDF détectées: {pdf_urls} items ({pdf_urls/total*100:.1f}%)")
    
    # 11. ITEMS PAR SOURCE (détaillé)
    print("\n[11] DETAIL PAR SOURCE")
    print("-"*80)
    for source in sources.most_common(5):
        source_name = source[0]
        source_items = [item for item in items if item.get('source_key') == source_name]
        print(f"\n  Source: {source_name} ({len(source_items)} items)")
        
        # Date sources pour cette source
        src_date_sources = Counter(
            item.get('date_extraction', {}).get('date_source', 'unknown')
            for item in source_items
        )
        print(f"    Extraction dates:")
        for ds, count in src_date_sources.most_common(3):
            print(f"      - {ds}: {count} items")
        
        # Taille moyenne
        src_lengths = [len(item.get('content', '')) for item in source_items]
        print(f"    Taille moyenne: {sum(src_lengths)/len(src_lengths):.0f} chars")
        
        # Type contenu
        src_types = Counter(
            item.get('metadata', {}).get('content_type', 'html')
            for item in source_items
        )
        print(f"    Types: {dict(src_types)}")
    
    # 12. QUALITE GLOBALE
    print("\n[12] SCORE QUALITE GLOBALE")
    print("-"*80)
    
    score = 0
    max_score = 100
    
    # Critère 1: Fallback < 10% (30 points)
    if fallback_pct < 10:
        score += 30
        print(f"  [OK] Fallback < 10%: +30 points")
    else:
        points = max(0, 30 - int(fallback_pct - 10) * 2)
        score += points
        print(f"  [!!] Fallback {fallback_pct:.1f}%: +{points} points")
    
    # Critère 2: Confiance moyenne > 0.70 (30 points)
    if avg_conf > 0.70:
        score += 30
        print(f"  [OK] Confiance > 0.70: +30 points")
    else:
        points = int(avg_conf * 30 / 0.70)
        score += points
        print(f"  [!!] Confiance {avg_conf:.2f}: +{points} points")
    
    # Critère 3: Taille contenu moyenne > 500 chars (20 points)
    avg_length = sum(content_lengths) / len(content_lengths)
    if avg_length > 500:
        score += 20
        print(f"  [OK] Taille moyenne > 500 chars: +20 points")
    else:
        points = int(avg_length * 20 / 500)
        score += points
        print(f"  [!!] Taille moyenne {avg_length:.0f} chars: +{points} points")
    
    # Critère 4: Diversité sources (20 points)
    if len(sources) >= 5:
        score += 20
        print(f"  [OK] Diversite sources >= 5: +20 points")
    else:
        points = len(sources) * 4
        score += points
        print(f"  [!!] Diversite sources {len(sources)}: +{points} points")
    
    print(f"\n  SCORE FINAL: {score}/{max_score} points")
    if score >= 80:
        print(f"  QUALITE: EXCELLENTE")
    elif score >= 60:
        print(f"  QUALITE: BONNE")
    elif score >= 40:
        print(f"  QUALITE: MOYENNE")
    else:
        print(f"  QUALITE: FAIBLE")
    
    # 13. RECOMMANDATIONS
    print("\n[13] RECOMMANDATIONS")
    print("-"*80)
    if fallback_pct >= 10:
        print(f"  - Améliorer extraction dates (actuellement {fallback_pct:.1f}% fallback)")
    if avg_conf < 0.70:
        print(f"  - Augmenter confiance extraction (actuellement {avg_conf:.2f})")
    if avg_length < 500:
        print(f"  - Enrichir contenu (actuellement {avg_length:.0f} chars en moyenne)")
    if len(sources) < 5:
        print(f"  - Ajouter plus de sources (actuellement {len(sources)} sources)")
    if score >= 80:
        print(f"  - Aucune amélioration majeure nécessaire")
    
    print("\n" + "="*80)
    print("FIN DE L'ANALYSE")
    print("="*80 + "\n")
    
    return score >= 60

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_ingestion.py <output_file.json>")
        sys.exit(1)
    
    output_file = sys.argv[1]
    success = analyze_ingestion(output_file)
    sys.exit(0 if success else 1)
