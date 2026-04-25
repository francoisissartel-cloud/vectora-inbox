#!/usr/bin/env python3
"""
Helper pour configurer les selectors CSS d'une nouvelle source HTML.
Usage: python analyze_html_source.py <url>
"""

import sys
import requests
from bs4 import BeautifulSoup

def analyze_source(url):
    print(f"\n=== ANALYSE SOURCE: {url} ===\n")
    
    r = requests.get(url, headers={'User-Agent': 'Vectora-Inbox/2.0'}, timeout=15)
    print(f"Status: {r.status_code}")
    
    if r.status_code != 200:
        print("ERREUR: Impossible d'accéder à la source")
        return
    
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # 1. Chercher les containers courants
    print("\n1. CONTAINERS POTENTIELS:")
    containers_tests = [
        ("article", "Balises <article>"),
        ("div.post", "Divs avec class 'post'"),
        ("div.news-item", "Divs avec class 'news-item'"),
        ("div[class*='news']", "Divs avec 'news' dans class"),
        ("div.views-row", "Drupal views-row"),
        ("a[href*='/news/']", "Liens vers /news/"),
        ("a[href*='/press']", "Liens vers /press"),
    ]
    
    best_selector = None
    best_count = 0
    
    for selector, desc in containers_tests:
        elements = soup.select(selector)
        count = len(elements)
        print(f"  {desc:30} ({selector:30}): {count:3} trouvés")
        if count > best_count and count < 100:
            best_count = count
            best_selector = selector
    
    if not best_selector:
        print("\n  ⚠ Aucun container trouvé - site probablement en JavaScript")
        return
    
    print(f"\n  -> Meilleur selector: {best_selector} ({best_count} items)")
    
    # 2. Analyser la structure du premier container
    print("\n2. STRUCTURE DU PREMIER CONTAINER:")
    containers = soup.select(best_selector)
    if containers:
        first = containers[0]
        
        # Titre
        title_selectors = ["h1 a", "h2 a", "h3 a", "h4 a", "a"]
        for sel in title_selectors:
            elem = first.select_one(sel)
            if elem:
                print(f"  Titre: {sel:20} -> {elem.get_text(strip=True)[:60]}")
                break
        
        # Lien
        link = first.select_one("a[href]") if first.name != 'a' else first
        if link:
            print(f"  Lien:  a[href]:15 -> {link.get('href', '')[:60]}")
        
        # Date
        date_selectors = ["time", "span.date", "div.date", "span[class*='date']"]
        for sel in date_selectors:
            elem = first.select_one(sel)
            if elem:
                print(f"  Date:  {sel:20} -> {elem.get_text(strip=True)[:30]}")
                break
        
        # Description
        desc_selectors = ["p", "div.excerpt", "div.summary", "div[class*='desc']"]
        for sel in desc_selectors:
            elem = first.select_one(sel)
            if elem:
                print(f"  Desc:  {sel:20} -> {elem.get_text(strip=True)[:60]}")
                break
    
    # 3. Générer la config YAML
    print("\n3. CONFIG YAML SUGGÉRÉE:")
    print(f"""
  source_key_here:
    container_selector: "{best_selector}"
    title_selector: "h2 a, h3 a"  # À ajuster
    link_selector: "a[href]"
    date_selector: "time, span.date"  # À ajuster
    description_selector: "p, div.excerpt"  # À ajuster
    max_items: 50
    notes: "À compléter"
""")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_html_source.py <url>")
        print("\nExemples:")
        print("  python analyze_html_source.py https://www.medincell.com/news/")
        print("  python analyze_html_source.py https://camurus.com/media/press-releases/")
        sys.exit(1)
    
    analyze_source(sys.argv[1])
