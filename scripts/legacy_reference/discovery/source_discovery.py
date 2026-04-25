#!/usr/bin/env python3
"""
Source Discovery Script - Vectora Inbox V3
Analyse automatique des sources candidates pour proposer la meilleure configuration d'ingestion.

Usage:
    python scripts/discovery/source_discovery.py --source press_corporate__taiwan_liposome
    python scripts/discovery/source_discovery.py --company lidds
    python scripts/discovery/source_discovery.py --batch --limit 10
"""

import argparse
import requests
import yaml
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime, timedelta
import json
from pathlib import Path
import time
import logging
import urllib3

# Désactiver les warnings SSL
urllib3.disable_warnings()

# Configuration
TIMEOUT = 15
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
MAX_ARTICLES_TO_ANALYZE = 5

class SourceDiscovery:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        self.session.verify = False  # Pour éviter les problèmes SSL
        
        # Charger les sources candidates
        self.candidates = self._load_candidates()
        
        # Patterns de détection
        self.news_url_patterns = [
            '/news/', '/press/', '/media/', '/investor/', '/press-releases/', 
            '/newsroom/', '/announcements/', '/updates/',
            '/en/news/', '/en/press/', '/en/media/', '/en/investor/'
        ]
        
        self.rss_patterns = [
            '/rss', '/feed', '/rss.xml', '/feed.xml', '/atom.xml',
            '/news/rss', '/press/rss', '/rss/news'
        ]
        
        self.date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # 2024-01-15
            r'(\d{2}/\d{2}/\d{4})',  # 01/15/2024
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}',  # Jan 15, 2024
            r'(\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})'  # 15 Jan 2024
        ]

    def _load_candidates(self):
        """Charger les sources candidates"""
        candidates_path = Path("canonical/sources/source_candidates_v3.yaml")
        with open(candidates_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return {c['source_key']: c for c in data['candidates']}

    def analyze_source(self, source_key):
        """Analyser une source candidate complète"""
        if source_key not in self.candidates:
            raise ValueError(f"Source {source_key} non trouvée dans les candidates")
            
        candidate = self.candidates[source_key]
        homepage_url = candidate['homepage_url']
        
        print(f"\nANALYSE DE {source_key}")
        print(f"Homepage: {homepage_url}")
        
        results = {
            'source_key': source_key,
            'homepage_url': homepage_url,
            'analysis_date': datetime.now().isoformat(),
            'connectivity': self._test_connectivity(homepage_url),
            'rss_feeds': self._discover_rss_feeds(homepage_url),
            'news_sections': self._discover_news_sections(homepage_url),
            'recommended_config': None,
            'confidence_score': 0
        }
        
        # Analyser les sections news trouvées
        if results['news_sections']:
            best_section = max(results['news_sections'], key=lambda x: x['score'])
            results['article_analysis'] = self._analyze_articles(best_section['url'])
            
        # Générer la recommandation
        results['recommended_config'] = self._generate_config_recommendation(results)
        
        return results

    def _test_connectivity(self, url):
        """Tester la connectivité du site"""
        try:
            response = self.session.get(url, timeout=TIMEOUT)
            return {
                'accessible': True,
                'status_code': response.status_code,
                'final_url': response.url,
                'ssl_valid': response.url.startswith('https://'),
                'redirected': response.url != url
            }
        except Exception as e:
            return {
                'accessible': False,
                'error': str(e),
                'ssl_valid': False
            }

    def _discover_rss_feeds(self, base_url):
        """Découvrir les flux RSS disponibles"""
        feeds_found = []
        
        # Test des URLs RSS communes
        for pattern in self.rss_patterns:
            rss_url = urljoin(base_url, pattern)
            try:
                response = self.session.get(rss_url, timeout=TIMEOUT)
                if response.status_code == 200 and 'xml' in response.headers.get('content-type', ''):
                    # Analyser le contenu RSS
                    content_sample = response.text[:1000]
                    feeds_found.append({
                        'url': rss_url,
                        'content_length': len(response.text),
                        'has_full_content': len(content_sample) > 500,  # Heuristique simple
                        'entries_estimated': content_sample.count('<item>') + content_sample.count('<entry>')
                    })
            except:
                continue
                
        return feeds_found

    def _discover_news_sections(self, base_url):
        """Découvrir les sections news du site"""
        sections_found = []
        
        for pattern in self.news_url_patterns:
            news_url = urljoin(base_url, pattern)
            try:
                response = self.session.get(news_url, timeout=TIMEOUT)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Scoring de la section
                    score = self._score_news_section(soup, response.text)
                    
                    if score > 0:
                        sections_found.append({
                            'url': news_url,
                            'score': score,
                            'links_found': len(soup.find_all('a')),
                            'has_dates': bool(re.search('|'.join(self.date_patterns), response.text)),
                            'content_length': len(response.text)
                        })
            except:
                continue
                
        return sorted(sections_found, key=lambda x: x['score'], reverse=True)

    def _score_news_section(self, soup, text):
        """Scorer une section news potentielle"""
        score = 0
        
        # Présence de mots-clés news
        news_keywords = ['press release', 'news', 'announcement', 'media', '2024', '2025', '2026']
        for keyword in news_keywords:
            if keyword.lower() in text.lower():
                score += 10
                
        # Présence de dates récentes
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Vérifier si la date est récente (derniers 2 ans)
                    if '2024' in str(match) or '2025' in str(match) or '2026' in str(match):
                        score += 20
                except:
                    continue
                    
        # Nombre de liens (indicateur de listing)
        links = soup.find_all('a', href=True)
        if len(links) > 5:
            score += min(len(links), 50)  # Cap à 50 points
            
        return score

    def _analyze_articles(self, news_url):
        """Analyser la structure des articles"""
        try:
            response = self.session.get(news_url, timeout=TIMEOUT)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Trouver des liens d'articles
            article_links = []
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if any(pattern in href for pattern in ['/detail/', '/press-release/', '/news/', '/article/']):
                    full_url = urljoin(news_url, href)
                    article_links.append(full_url)
                    
            # Analyser quelques articles
            articles_analyzed = []
            for article_url in article_links[:MAX_ARTICLES_TO_ANALYZE]:
                article_analysis = self._analyze_single_article(article_url)
                if article_analysis:
                    articles_analyzed.append(article_analysis)
                    
            return {
                'total_links_found': len(article_links),
                'articles_analyzed': len(articles_analyzed),
                'sample_articles': articles_analyzed,
                'url_patterns_detected': self._detect_url_patterns(article_links)
            }
            
        except Exception as e:
            return {'error': str(e)}

    def _analyze_single_article(self, article_url):
        """Analyser un article individuel"""
        try:
            response = self.session.get(article_url, timeout=TIMEOUT)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraction de date
            date_found = None
            for pattern in self.date_patterns:
                match = re.search(pattern, response.text, re.IGNORECASE)
                if match:
                    date_found = match.group(0)
                    break
                    
            # Extraction de contenu
            content_length = 0
            for selector in ['article', '.content', '.news-content', 'main']:
                elements = soup.select(selector)
                if elements:
                    content_length = len(elements[0].get_text(strip=True))
                    break
                    
            return {
                'url': article_url,
                'title': soup.find('title').get_text(strip=True) if soup.find('title') else '',
                'date_found': date_found,
                'content_length': content_length,
                'has_good_content': content_length > 200
            }
            
        except Exception as e:
            return {'url': article_url, 'error': str(e)}

    def _detect_url_patterns(self, urls):
        """Détecter les patterns d'URL des articles"""
        patterns = {}
        for url in urls:
            path = urlparse(url).path
            if '/detail/' in path:
                patterns['/detail/'] = patterns.get('/detail/', 0) + 1
            elif '/press-release/' in path:
                patterns['/press-release/'] = patterns.get('/press-release/', 0) + 1
            elif '/news/' in path and path.count('/') > 2:
                patterns['/news/'] = patterns.get('/news/', 0) + 1
                
        return patterns

    def _generate_config_recommendation(self, analysis):
        """Générer la recommandation de configuration"""
        config = {
            'validated': False,
            'validated_date': None,
            'news_url': '',
            'ingestion_profile': 'html_generic',
            'listing_selectors': {},
            'date_selectors': {'strategy': 'text_extraction'},
            'extraction_notes': f"AUTO-GENERATED by discovery script on {datetime.now().strftime('%Y-%m-%d')}"
        }
        
        confidence = 0
        
        # Choix du profil d'ingestion
        if analysis['rss_feeds']:
            best_rss = max(analysis['rss_feeds'], key=lambda x: x['content_length'])
            if best_rss['has_full_content']:
                config['ingestion_profile'] = 'rss_full'
                config['news_url'] = best_rss['url']
                confidence += 40
            else:
                config['ingestion_profile'] = 'rss_with_fetch'
                config['news_url'] = best_rss['url']
                confidence += 30
        elif analysis['news_sections']:
            best_section = max(analysis['news_sections'], key=lambda x: x['score'])
            config['news_url'] = best_section['url']
            config['ingestion_profile'] = 'html_generic'
            confidence += 20
            
            # Configuration des selectors
            if 'article_analysis' in analysis and analysis['article_analysis'].get('url_patterns_detected'):
                patterns = analysis['article_analysis']['url_patterns_detected']
                most_common_pattern = max(patterns.keys(), key=lambda k: patterns[k])
                config['listing_selectors']['url_pattern'] = most_common_pattern
                confidence += 20
            else:
                config['listing_selectors'] = {
                    'container': 'a',
                    'link': 'a'
                }
                confidence += 10
                
        # Ajuster la stratégie de date si nécessaire
        if analysis.get('article_analysis', {}).get('sample_articles'):
            dates_found = sum(1 for a in analysis['article_analysis']['sample_articles'] if a.get('date_found'))
            if dates_found > 0:
                confidence += 20
            else:
                config['date_selectors']['strategy'] = 'json_ld'  # Fallback
                
        analysis['confidence_score'] = min(confidence, 100)
        return config

    def generate_yaml_config(self, analysis):
        """Générer la configuration YAML prête à copier"""
        config = analysis['recommended_config']
        source_key = analysis['source_key']
        
        yaml_config = f"""
  {source_key}:
    validated: {str(config['validated']).lower()}
    validated_date: {config['validated_date']}
    news_url: "{config['news_url']}"
    ingestion_profile: {config['ingestion_profile']}"""
        
        if config['listing_selectors']:
            yaml_config += "\n    listing_selectors:"
            for key, value in config['listing_selectors'].items():
                yaml_config += f'\n      {key}: "{value}"'
                
        yaml_config += f"""
    date_selectors:
      strategy: {config['date_selectors']['strategy']}
    extraction_notes: >
      {config['extraction_notes']}
      Confidence: {analysis['confidence_score']}%
      Analysis: {len(analysis.get('news_sections', []))} news sections found, {len(analysis.get('rss_feeds', []))} RSS feeds found."""
        
        return yaml_config

def main():
    parser = argparse.ArgumentParser(description='Source Discovery Tool')
    parser.add_argument('--source', help='Source key to analyze')
    parser.add_argument('--company', help='Company ID to analyze')
    parser.add_argument('--batch', action='store_true', help='Analyze multiple sources')
    parser.add_argument('--limit', type=int, default=10, help='Limit for batch processing')
    parser.add_argument('--output', help='Output file for results')
    
    args = parser.parse_args()
    
    discovery = SourceDiscovery()
    
    if args.source:
        # Analyser une source spécifique
        results = discovery.analyze_source(args.source)
        
        print(f"\nRESULTATS POUR {args.source}")
        print(f"Connectivité: {'OK' if results['connectivity']['accessible'] else 'ERREUR'}")
        print(f"Flux RSS trouvés: {len(results['rss_feeds'])}")
        print(f"Sections news trouvées: {len(results['news_sections'])}")
        print(f"Confiance: {results['confidence_score']}%")
        
        if results['recommended_config']:
            print(f"\nCONFIGURATION RECOMMANDÉE:")
            print(discovery.generate_yaml_config(results))
            
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
                
    elif args.batch:
        # Traitement par lot
        print(f"ANALYSE PAR LOT ({args.limit} sources)")
        # TODO: Implémenter le traitement par lot
        
    else:
        print("ERREUR: Spécifiez --source ou --batch")

if __name__ == '__main__':
    main()