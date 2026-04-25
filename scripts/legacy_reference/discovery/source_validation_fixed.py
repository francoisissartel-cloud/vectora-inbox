#!/usr/bin/env python3
"""
Source Validation Script - Vectora Inbox V3
Valide et affine les configurations générées par source_discovery.py

Usage:
    python scripts/discovery/source_validation.py --source press_corporate__taiwan_liposome
    python scripts/discovery/source_validation.py --batch --confidence-min 50
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
from source_discovery import SourceDiscovery

# Désactiver les warnings SSL
urllib3.disable_warnings()

# Configuration
TIMEOUT = 15
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
MIN_ARTICLES_TO_VALIDATE = 3
MAX_ARTICLES_TO_TEST = 10

class SourceValidator:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        self.session.verify = False
        
        self.discovery = SourceDiscovery()
        
    def validate_source_config(self, source_key):
        """Valider une configuration de source générée par discovery"""
        print(f"\n=== VALIDATION DE {source_key} ===")
        
        # 1. Récupérer l'analyse discovery
        discovery_results = self.discovery.analyze_source(source_key)
        base_config = discovery_results['recommended_config']
        
        print(f"Configuration de base (confiance: {discovery_results['confidence_score']}%):")
        print(f"  news_url: {base_config['news_url']}")
        print(f"  ingestion_profile: {base_config['ingestion_profile']}")
        
        # 2. Tester l'extraction d'articles
        validation_results = {
            'source_key': source_key,
            'base_config': base_config,
            'base_confidence': discovery_results['confidence_score'],
            'validation_date': datetime.now().isoformat(),
            'tests': {}
        }
        
        # Test 1: Extraction d'articles
        articles_test = self._test_article_extraction(base_config)
        validation_results['tests']['article_extraction'] = articles_test
        
        # Test 2: Validation des titres
        titles_test = self._test_title_extraction(articles_test.get('sample_articles', []))
        validation_results['tests']['title_extraction'] = titles_test
        
        # Test 3: Validation des dates
        dates_test = self._test_date_extraction(articles_test.get('sample_articles', []))
        validation_results['tests']['date_extraction'] = dates_test
        
        # Test 4: Qualité du contenu
        content_test = self._test_content_quality(articles_test.get('sample_articles', []))
        validation_results['tests']['content_quality'] = content_test
        
        # 3. Affiner la configuration
        refined_config = self._refine_configuration(base_config, validation_results)
        validation_results['refined_config'] = refined_config
        
        # 4. Score de validation final
        final_score = self._calculate_validation_score(validation_results)
        validation_results['validation_score'] = final_score
        validation_results['validation_status'] = 'PASSED' if final_score >= 70 else 'FAILED'
        
        return validation_results
    
    def _test_article_extraction(self, config):
        """Tester l'extraction d'articles avec la configuration"""
        print("\n--- Test extraction d'articles ---")
        
        try:
            response = self.session.get(config['news_url'], timeout=TIMEOUT)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            articles_found = []
            
            # Extraction selon le profil
            if config['ingestion_profile'] in ['rss_full', 'rss_with_fetch']:
                # Test RSS
                articles_found = self._extract_rss_articles(config['news_url'])
            else:
                # Test HTML
                articles_found = self._extract_html_articles(soup, config)
            
            # Analyser quelques articles
            sample_articles = []
            for article_url in articles_found[:MAX_ARTICLES_TO_TEST]:
                article_data = self._analyze_article_content(article_url)
                if article_data:
                    sample_articles.append(article_data)
            
            result = {
                'success': True,
                'total_articles_found': len(articles_found),
                'sample_articles': sample_articles,
                'articles_analyzed': len(sample_articles)
            }
            
            print(f"  OK {len(articles_found)} articles trouves, {len(sample_articles)} analyses")
            return result
            
        except Exception as e:
            print(f"  ERREUR extraction: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _extract_html_articles(self, soup, config):
        """Extraire les articles HTML selon la configuration"""
        articles = []
        
        selectors = config.get('listing_selectors', {})
        
        if 'url_pattern' in selectors:
            # Méthode par pattern d'URL
            pattern = selectors['url_pattern']
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if pattern in href:
                    full_url = urljoin(config['news_url'], href)
                    articles.append(full_url)
        
        elif 'container' in selectors:
            # Méthode par container CSS
            containers = soup.select(selectors['container'])
            for container in containers:
                link = container.find('a') if selectors.get('link') == 'a' else container
                if link and link.get('href'):
                    full_url = urljoin(config['news_url'], link.get('href'))
                    articles.append(full_url)
        
        return list(set(articles))  # Dédupliquer
    
    def _extract_rss_articles(self, rss_url):
        """Extraire les articles d'un flux RSS"""
        try:
            response = self.session.get(rss_url, timeout=TIMEOUT)
            soup = BeautifulSoup(response.text, 'xml')
            
            articles = []
            for item in soup.find_all(['item', 'entry']):
                link_elem = item.find(['link', 'id'])
                if link_elem:
                    articles.append(link_elem.get_text(strip=True))
            
            return articles
        except:
            return []
    
    def _analyze_article_content(self, article_url):
        """Analyser le contenu d'un article individuel"""
        try:
            response = self.session.get(article_url, timeout=TIMEOUT)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraction du titre avec diagnostic détaillé
            title_analysis = self._analyze_title_extraction(soup, article_url)
            
            # Extraction du contenu
            content = ''
            content_length = 0
            for selector in ['article', '.content', '.news-content', 'main', '.post-content']:
                elem = soup.select_one(selector)
                if elem:
                    content = elem.get_text(strip=True)
                    content_length = len(content)
                    break
            
            # Si pas de contenu spécifique, prendre le body
            if content_length < 200:
                body = soup.find('body')
                if body:
                    content = body.get_text(strip=True)
                    content_length = len(content)
            
            # Extraction de date
            date_found = self._extract_article_date(soup, response.text)
            
            return {
                'url': article_url,
                'title': title_analysis['best_title'][:200] if title_analysis['best_title'] else '',
                'title_analysis': title_analysis,  # Diagnostic détaillé
                'content_length': content_length,
                'has_good_content': content_length > 500,
                'date_found': date_found,
                'has_date': bool(date_found)
            }
            
        except Exception as e:
            return {
                'url': article_url,
                'error': str(e),
                'content_length': 0,
                'has_good_content': False,
                'has_date': False,
                'title_analysis': {'issue': 'fetch_error'}
            }
    
    def _analyze_title_extraction(self, soup, article_url):
        """Analyser en détail l'extraction de titre pour diagnostiquer les problèmes"""
        # Sélecteurs de titre par ordre de priorité (comme dans le parser)
        title_selectors = ['title', 'h1', '.title', '.post-title', '.article-title', '.entry-title']
        
        analysis = {
            'selectors_tested': [],
            'best_title': '',
            'best_selector': '',
            'title_length': 0,
            'issues': [],
            'recommendations': []
        }
        
        # Tester chaque sélecteur
        for selector in title_selectors:
            elem = soup.select_one(selector)
            if elem:
                title = elem.get_text(strip=True)
                title_length = len(title)
                
                selector_result = {
                    'selector': selector,
                    'title': title[:100] + '...' if len(title) > 100 else title,
                    'length': title_length,
                    'valid': title_length > 5  # Nouvelle limite
                }
                analysis['selectors_tested'].append(selector_result)
                
                # Premier titre valide devient le meilleur
                if title_length > 5 and not analysis['best_title']:
                    analysis['best_title'] = title
                    analysis['best_selector'] = selector
                    analysis['title_length'] = title_length
        
        # Détecter les problèmes courants
        if not analysis['best_title']:
            analysis['issues'].append('no_valid_title')
            analysis['recommendations'].append('Aucun titre valide trouvé - vérifier la structure HTML')
        
        # Détecter les titres génériques (comme Taiwan Liposome)
        if analysis['best_title']:
            generic_patterns = ['goldennet', 'search', 'home', 'welcome', 'untitled']
            if any(pattern in analysis['best_title'].lower() for pattern in generic_patterns):
                analysis['issues'].append('generic_title')
                analysis['recommendations'].append(f"Titre générique détecté: '{analysis['best_title']}' - privilégier <title> ou ajuster sélecteurs")
        
        # Détecter si tous les titres sont identiques (problème Taiwan Liposome)
        h1_titles = [r for r in analysis['selectors_tested'] if r['selector'] == 'h1']
        title_titles = [r for r in analysis['selectors_tested'] if r['selector'] == 'title']
        
        if h1_titles and title_titles:
            h1_title = h1_titles[0]['title']
            title_title = title_titles[0]['title']
            
            if len(h1_title) < 15 and len(title_title) > 20:
                analysis['issues'].append('h1_too_short_title_better')
                analysis['recommendations'].append(f"H1 trop court ({len(h1_title)} chars), <title> plus informatif ({len(title_title)} chars) - privilégier <title>")
        
        return analysis
        """Extraire la date d'un article"""
        # Patterns de date
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # 2024-01-15
            r'(\d{2}/\d{2}/\d{4})',  # 01/15/2024
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}',  # Jan 15, 2024
            r'(\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})'  # 15 Jan 2024
        ]
        
        # 1. Chercher dans JSON-LD
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    date = data.get('datePublished') or data.get('dateCreated')
                    if date:
                        return date
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            date = item.get('datePublished') or item.get('dateCreated')
                            if date:
                                return date
            except:
                continue
        
        # 2. Chercher dans les meta tags
        for meta in soup.find_all('meta'):
            if meta.get('property') in ['article:published_time', 'datePublished']:
                return meta.get('content')
            if meta.get('name') in ['date', 'publish-date', 'publication-date']:
                return meta.get('content')
        
        # 3. Chercher dans le texte
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    def _test_title_extraction(self, sample_articles):
        """Tester l'extraction des titres et détecter les problèmes"""
        print("\n--- Test extraction des titres ---")
        
        if not sample_articles:
            print("  ERREUR Aucun article a tester")
            return {'success': False, 'valid_titles': 0, 'total_articles': 0}
        
        valid_titles = 0
        title_issues = []
        generic_titles = 0
        
        for article in sample_articles:
            title_analysis = article.get('title_analysis', {})
            
            if title_analysis.get('best_title'):
                valid_titles += 1
            
            # Compter les problèmes
            issues = title_analysis.get('issues', [])
            if 'generic_title' in issues:
                generic_titles += 1
            
            title_issues.extend(issues)
        
        total_articles = len(sample_articles)
        success_rate = (valid_titles / total_articles) * 100
        
        # Détecter les problèmes systémiques
        systemic_issues = []
        if generic_titles > total_articles * 0.5:  # Plus de 50% de titres génériques
            systemic_issues.append('generic_titles_pattern')
        
        if 'h1_too_short_title_better' in title_issues:
            systemic_issues.append('h1_inadequate_title_better')
        
        result = {
            'success': success_rate >= 70,  # Au moins 70% des articles doivent avoir un titre valide
            'valid_titles': valid_titles,
            'total_articles': total_articles,
            'success_rate': success_rate,
            'generic_titles': generic_titles,
            'systemic_issues': systemic_issues,
            'recommendations': self._generate_title_recommendations(systemic_issues, sample_articles)
        }
        
        print(f"  {'OK' if result['success'] else 'ATTENTION'} {valid_titles}/{total_articles} titres valides ({success_rate:.1f}%)")
        
        if generic_titles > 0:
            print(f"  ATTENTION {generic_titles} titres génériques détectés")
        
        for issue in systemic_issues:
            if issue == 'generic_titles_pattern':
                print(f"  PROBLEME Titres génériques systémiques - ajuster configuration")
            elif issue == 'h1_inadequate_title_better':
                print(f"  PROBLEME H1 inadéquat, <title> meilleur - privilégier <title>")
        
        return result
    
    def _generate_title_recommendations(self, systemic_issues, sample_articles):
        """Générer des recommandations pour les problèmes de titre"""
        recommendations = []
        
        if 'generic_titles_pattern' in systemic_issues:
            recommendations.append({
                'issue': 'generic_titles',
                'description': 'Titres génériques détectés (ex: goldennet, search)',
                'solution': 'Modifier parser pour privilégier <title> ou ajuster sélecteurs',
                'config_change': 'title_selectors: ["title", "h1", ".title"]'
            })
        
        if 'h1_inadequate_title_better' in systemic_issues:
            recommendations.append({
                'issue': 'h1_too_short',
                'description': 'H1 trop court, <title> plus informatif',
                'solution': 'Réorganiser ordre des sélecteurs pour privilégier <title>',
                'config_change': 'title_selectors: ["title", "h1"] + réduire min_length à 5'
            })
        
        return recommendations
        """Tester l'extraction des dates"""
        print("\n--- Test extraction des dates ---")
        
        if not sample_articles:
            print("  ERREUR Aucun article a tester")
            return {'success': False, 'dates_found': 0, 'total_articles': 0}
        
        dates_found = sum(1 for article in sample_articles if article.get('has_date'))
        total_articles = len(sample_articles)
        success_rate = (dates_found / total_articles) * 100
        
        result = {
            'success': success_rate >= 50,  # Au moins 50% des articles doivent avoir une date
            'dates_found': dates_found,
            'total_articles': total_articles,
            'success_rate': success_rate
        }
        
        print(f"  {'OK' if result['success'] else 'ERREUR'} {dates_found}/{total_articles} dates trouvees ({success_rate:.1f}%)")
        return result
    
    def _test_content_quality(self, sample_articles):
        """Tester la qualité du contenu extrait"""
        print("\n--- Test qualite du contenu ---")
        
        if not sample_articles:
            print("  ERREUR Aucun article a tester")
            return {'success': False, 'good_content': 0, 'total_articles': 0}
        
        good_content = sum(1 for article in sample_articles if article.get('has_good_content'))
        total_articles = len(sample_articles)
        success_rate = (good_content / total_articles) * 100
        
        avg_length = sum(article.get('content_length', 0) for article in sample_articles) / total_articles
        
        result = {
            'success': success_rate >= 70,  # Au moins 70% des articles doivent avoir un bon contenu
            'good_content': good_content,
            'total_articles': total_articles,
            'success_rate': success_rate,
            'average_content_length': int(avg_length)
        }
        
        print(f"  {'OK' if result['success'] else 'ERREUR'} {good_content}/{total_articles} articles avec bon contenu ({success_rate:.1f}%)")
        print(f"  Longueur moyenne: {int(avg_length)} caracteres")
        return result
    
    def _refine_configuration(self, base_config, validation_results):
        """Affiner la configuration basée sur les résultats de validation"""
        print("\n--- Affinement de la configuration ---")
        
        refined_config = base_config.copy()
        
        # Affiner les sélecteurs si nécessaire
        articles_test = validation_results['tests'].get('article_extraction', {})
        if articles_test.get('success') and articles_test.get('sample_articles'):
            # Analyser les patterns d'URL des articles trouvés
            article_urls = [a['url'] for a in articles_test['sample_articles']]
            refined_pattern = self._detect_best_url_pattern(article_urls)
            
            if refined_pattern and refined_pattern != base_config.get('listing_selectors', {}).get('url_pattern'):
                print(f"  AFFINE Pattern URL affine: {refined_pattern}")
                if 'listing_selectors' not in refined_config:
                    refined_config['listing_selectors'] = {}
                refined_config['listing_selectors']['url_pattern'] = refined_pattern
        
        # Affiner la stratégie de date
        dates_test = validation_results['tests'].get('date_extraction', {})
        if dates_test.get('success_rate', 0) < 50:
            print("  AFFINE Strategie de date changee vers json_ld")
            refined_config['date_selectors']['strategy'] = 'json_ld'
        
        return refined_config
    
    def _detect_best_url_pattern(self, article_urls):
        """Détecter le meilleur pattern d'URL pour les articles"""
        patterns = {}
        
        for url in article_urls:
            path = urlparse(url).path
            
            # Analyser les segments du path
            segments = [s for s in path.split('/') if s]
            
            # Chercher des patterns communs
            for i, segment in enumerate(segments):
                if segment in ['detail', 'press-release', 'news', 'article']:
                    # Construire le pattern jusqu'à ce segment
                    pattern_parts = segments[:i+1]
                    pattern = '/' + '/'.join(pattern_parts) + '/'
                    patterns[pattern] = patterns.get(pattern, 0) + 1
        
        # Retourner le pattern le plus fréquent
        if patterns:
            return max(patterns.keys(), key=lambda k: patterns[k])
        
        return None
    
    def _calculate_validation_score(self, validation_results):
        """Calculer le score de validation final"""
        score = validation_results['base_confidence']  # Score de base du discovery
        
        tests = validation_results['tests']
        
        # Bonus/malus selon les tests
        if tests.get('article_extraction', {}).get('success'):
            articles_found = tests['article_extraction'].get('total_articles_found', 0)
            if articles_found >= 5:
                score += 20
            elif articles_found >= 1:
                score += 10
        else:
            score -= 30
        
        if tests.get('date_extraction', {}).get('success'):
            score += 15
        else:
            score -= 10
        
        if tests.get('content_quality', {}).get('success'):
            score += 15
        else:
            score -= 10
        
        return min(max(score, 0), 100)  # Entre 0 et 100
    
    def generate_validation_report(self, validation_results):
        """Générer un rapport de validation"""
        source_key = validation_results['source_key']
        status = validation_results['validation_status']
        score = validation_results['validation_score']
        
        report = f"""
=== RAPPORT DE VALIDATION ===
Source: {source_key}
Statut: {status}
Score: {score}%

TESTS EFFECTUES:
"""
        
        tests = validation_results['tests']
        
        # Test extraction
        if 'article_extraction' in tests:
            test = tests['article_extraction']
            report += f"• Extraction d'articles: {'OK' if test.get('success') else 'ERREUR'}\n"
            report += f"  Articles trouves: {test.get('total_articles_found', 0)}\n"
            report += f"  Articles analyses: {test.get('articles_analyzed', 0)}\n"
        
        # Test dates
        if 'date_extraction' in tests:
            test = tests['date_extraction']
            report += f"• Extraction des dates: {'OK' if test.get('success') else 'ERREUR'}\n"
            report += f"  Taux de succes: {test.get('success_rate', 0):.1f}%\n"
        
        # Test contenu
        if 'content_quality' in tests:
            test = tests['content_quality']
            report += f"• Qualite du contenu: {'OK' if test.get('success') else 'ERREUR'}\n"
            report += f"  Longueur moyenne: {test.get('average_content_length', 0)} chars\n"
        
        # Configuration finale
        config = validation_results.get('refined_config', {})
        report += f"""
CONFIGURATION FINALE:
  news_url: {config.get('news_url', '')}
  ingestion_profile: {config.get('ingestion_profile', '')}
  listing_selectors: {config.get('listing_selectors', {})}
  date_selectors: {config.get('date_selectors', {})}

RECOMMANDATION: {'INTEGRER LA SOURCE' if status == 'PASSED' else 'CORRIGER LES PROBLEMES'}
"""
        
        return report

def main():
    parser = argparse.ArgumentParser(description='Source Validation Tool')
    parser.add_argument('--source', help='Source key to validate')
    parser.add_argument('--batch', action='store_true', help='Validate multiple sources')
    parser.add_argument('--confidence-min', type=int, default=50, help='Minimum confidence score for batch validation')
    parser.add_argument('--output', help='Output file for results')
    
    args = parser.parse_args()
    
    validator = SourceValidator()
    
    if args.source:
        # Valider une source spécifique
        results = validator.validate_source_config(args.source)
        
        # Afficher le rapport
        report = validator.generate_validation_report(results)
        print(report)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
                
    elif args.batch:
        print("VALIDATION PAR LOT - TODO: A implementer")
        
    else:
        print("ERREUR: Specifiez --source ou --batch")

if __name__ == '__main__':
    main()