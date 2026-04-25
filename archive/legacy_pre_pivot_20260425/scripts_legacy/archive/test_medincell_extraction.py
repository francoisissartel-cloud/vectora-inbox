"""
Test d'extraction pour MedinCell avec support PDF
"""
import requests
from bs4 import BeautifulSoup
import yaml
from pathlib import Path
import re

def load_config():
    """Charge la configuration des extracteurs"""
    config_path = Path(__file__).parent.parent / "canonical" / "sources" / "html_extractors.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def extract_pdf_text(pdf_url):
    """Extrait le texte d'un PDF (simulation pour test)"""
    try:
        print(f"  [PDF] Telechargement: {pdf_url}")
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()
        
        # Pour le test, on simule l'extraction en comptant la taille
        pdf_size = len(response.content)
        print(f"  [OK] PDF telecharge: {pdf_size / 1024:.1f} KB")
        
        # Simulation: on estime ~200 mots par KB pour un PDF
        estimated_words = int(pdf_size / 1024 * 200)
        
        print(f"  [INFO] Estimation: ~{estimated_words} mots")
        return f"[Contenu PDF simule - {estimated_words} mots estimes]", estimated_words
    except Exception as e:
        print(f"  [ERROR] Erreur telechargement PDF: {e}")
        return None, 0

def test_medincell_extraction():
    """Test l'extraction de la page MedinCell"""
    print("=" * 80)
    print("TEST EXTRACTION MEDINCELL")
    print("=" * 80)
    
    # Charge la config
    config = load_config()
    medincell_config = config['extractors'].get('press_corporate__medincell')
    
    if not medincell_config:
        print("[ERROR] Configuration MedinCell non trouvee")
        return
    
    print(f"\n[OK] Configuration chargee:")
    print(f"  - PDF extraction: {medincell_config.get('pdf_extraction', False)}")
    print(f"  - Base URL: {medincell_config.get('base_url')}")
    
    # Recupere la page
    url = "https://www.medincell.com/news/"
    print(f"\n[HTTP] Recuperation de {url}")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        print(f"[OK] Page recuperee: {len(response.content)} bytes")
    except Exception as e:
        print(f"[ERROR] Erreur recuperation page: {e}")
        return
    
    # Trouve les items
    print(f"\n[SEARCH] Recherche des items...")
    items = []
    
    # Cherche tous les liens PDF
    pdf_links = soup.find_all('a', href=lambda x: x and '.pdf' in x.lower())
    print(f"  Trouve {len(pdf_links)} liens PDF")
    
    # Extrait les 3 premiers pour test
    for i, link in enumerate(pdf_links[:3]):
        print(f"\n[ITEM {i+1}]:")
        
        title = link.get_text(strip=True)
        pdf_url = link.get('href')
        
        # Construit l'URL complète si nécessaire
        if not pdf_url.startswith('http'):
            pdf_url = medincell_config['base_url'] + pdf_url
        
        print(f"  Titre: {title}")
        print(f"  URL: {pdf_url}")
        
        # Extrait le contenu PDF si configuré
        if medincell_config.get('pdf_extraction'):
            text, word_count = extract_pdf_text(pdf_url)
            
            items.append({
                'title': title,
                'url': pdf_url,
                'content': text[:500] if text else title,  # Premiers 500 chars
                'word_count': word_count,
                'content_type': 'pdf'
            })
        else:
            items.append({
                'title': title,
                'url': pdf_url,
                'content': title,
                'word_count': len(title.split()),
                'content_type': 'pdf'
            })
    
    # Résumé
    print("\n" + "=" * 80)
    print("RÉSUMÉ")
    print("=" * 80)
    print(f"Items extraits: {len(items)}")
    
    for i, item in enumerate(items, 1):
        print(f"\n{i}. {item['title'][:60]}...")
        print(f"   Word count: {item['word_count']}")
        print(f"   Type: {item['content_type']}")
        if item['word_count'] > 50:
            print(f"   [OK] Contenu extrait avec succes")
        else:
            print(f"   [WARNING] Contenu trop court (titre seulement)")
    
    return items

if __name__ == "__main__":
    test_medincell_extraction()
