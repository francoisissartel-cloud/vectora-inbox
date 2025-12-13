"""
Tests unitaires pour le refactoring du parser HTML corporate.

Ces tests valident les améliorations apportées au parser générique
et aux extracteurs spécifiques.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from vectora_core.ingestion.parser import (
    _find_article_containers,
    _extract_date_from_element,
    _parse_date_string,
    _resolve_url,
    _extract_item_from_element
)
from vectora_core.ingestion.html_extractor import ConfigurableHTMLExtractor
from vectora_core.ingestion.metrics_collector import IngestionMetrics, create_source_metrics


class TestGenericParserImprovements(unittest.TestCase):
    """Tests pour les améliorations du parser générique."""
    
    def setUp(self):
        """Configuration des tests."""
        try:
            from bs4 import BeautifulSoup
            self.BeautifulSoup = BeautifulSoup
        except ImportError:
            self.skipTest("BeautifulSoup non installé")
    
    def test_find_article_containers_extended_heuristics(self):
        """Test des heuristiques étendues pour trouver les conteneurs d'articles."""
        html = """
        <html>
            <body>
                <article>Article 1</article>
                <div class="news-item">News 1</div>
                <div class="press-release">Press 1</div>
                <li class="post-item">Post 1</li>
                <section class="news-section">Section 1</section>
                <div class="unrelated">Not news</div>
            </body>
        </html>
        """
        
        soup = self.BeautifulSoup(html, 'html.parser')
        containers = _find_article_containers(soup)
        
        # Doit trouver 5 conteneurs (article, news-item, press-release, post-item, news-section)
        self.assertEqual(len(containers), 5)
        
        # Vérifier les types d'éléments trouvés
        tags = [c.name for c in containers]
        self.assertIn('article', tags)
        self.assertIn('div', tags)
        self.assertIn('li', tags)
        self.assertIn('section', tags)
    
    def test_extract_date_from_element_multiple_patterns(self):
        """Test de l'extraction de dates avec différents patterns."""
        # Test avec attribut datetime
        html_datetime = '<time datetime="2025-01-15">January 15, 2025</time>'
        soup = self.BeautifulSoup(html_datetime, 'html.parser')
        date = _extract_date_from_element(soup.find('time'))
        self.assertEqual(date, '2025-01-15')
        
        # Test avec texte contenant une date ISO
        html_iso = '<div>Published on 2025-01-15 at 10:00</div>'
        soup = self.BeautifulSoup(html_iso, 'html.parser')
        date = _extract_date_from_element(soup.find('div'))
        self.assertEqual(date, '2025-01-15')
        
        # Test avec format US
        html_us = '<span>January 15, 2025</span>'
        soup = self.BeautifulSoup(html_us, 'html.parser')
        date = _extract_date_from_element(soup.find('span'))
        # Doit parser correctement (dépend de dateutil si disponible)
        self.assertRegex(date, r'\\d{4}-\\d{2}-\\d{2}')
    
    def test_parse_date_string_formats(self):
        """Test du parsing de chaînes de dates avec différents formats."""
        # Format ISO
        self.assertEqual(_parse_date_string('2025-01-15'), '2025-01-15')
        
        # Format avec heure
        self.assertEqual(_parse_date_string('2025-01-15T10:30:00'), '2025-01-15')
        
        # Format DD/MM/YYYY
        result = _parse_date_string('15/01/2025')
        self.assertIsNotNone(result)
        self.assertRegex(result, r'\\d{4}-\\d{2}-\\d{2}')
        
        # Chaîne vide
        self.assertIsNone(_parse_date_string(''))
        self.assertIsNone(_parse_date_string(None))
    
    def test_resolve_url_relative_absolute(self):
        """Test de la résolution des URLs relatives et absolues."""
        base_url = 'https://example.com'
        
        # URL absolue (pas de modification)
        absolute_url = 'https://other.com/page'
        self.assertEqual(_resolve_url(absolute_url, base_url), absolute_url)
        
        # URL relative avec /
        relative_url = '/news/article-1'
        expected = 'https://example.com/news/article-1'
        self.assertEqual(_resolve_url(relative_url, base_url), expected)
        
        # URL relative sans /
        relative_url2 = 'news/article-2'
        expected2 = 'https://example.com/news/article-2'
        self.assertEqual(_resolve_url(relative_url2, base_url), expected2)
        
        # URL vide
        self.assertEqual(_resolve_url('', base_url), '')
        self.assertEqual(_resolve_url(None, base_url), '')
    
    def test_extract_item_from_element_improved(self):
        """Test de l'extraction d'item avec les améliorations."""
        html = """
        <article>
            <h3><a href="/news/article-1">Test Article Title</a></h3>
            <time datetime="2025-01-15">January 15, 2025</time>
            <p class="description">This is a test article description.</p>
        </article>
        """
        
        soup = self.BeautifulSoup(html, 'html.parser')
        article = soup.find('article')
        
        item = _extract_item_from_element(
            article, 
            'test_source', 
            'press_corporate', 
            'https://example.com'
        )
        
        self.assertIsNotNone(item)
        self.assertEqual(item['title'], 'Test Article Title')
        self.assertEqual(item['url'], 'https://example.com/news/article-1')
        self.assertEqual(item['published_at'], '2025-01-15')
        self.assertEqual(item['raw_text'], 'This is a test article description.')
        self.assertEqual(item['source_key'], 'test_source')
        self.assertEqual(item['source_type'], 'press_corporate')


class TestConfigurableHTMLExtractor(unittest.TestCase):
    """Tests pour l'extracteur HTML configurable."""
    
    def setUp(self):
        """Configuration des tests."""
        try:
            from bs4 import BeautifulSoup
            self.BeautifulSoup = BeautifulSoup
        except ImportError:
            self.skipTest("BeautifulSoup non installé")
    
    @patch('vectora_core.ingestion.html_extractor.open')
    @patch('vectora_core.ingestion.html_extractor.yaml.safe_load')
    def test_load_extractor_configs(self, mock_yaml_load, mock_open):
        """Test du chargement de la configuration des extracteurs."""
        # Mock de la configuration
        mock_config = {
            'extractors': {
                'test_source': {
                    'selectors': {
                        'container': 'div.news',
                        'item': 'article',
                        'title': 'h2 a',
                        'url': 'h2 a',
                        'date': 'time'
                    }
                }
            },
            'global_settings': {
                'default_max_items': 20
            }
        }
        
        mock_yaml_load.return_value = mock_config
        mock_open.return_value.__enter__.return_value = MagicMock()
        
        extractor = ConfigurableHTMLExtractor()
        
        self.assertEqual(len(extractor.extractors), 1)
        self.assertIn('test_source', extractor.extractors)
        self.assertEqual(extractor.global_settings['default_max_items'], 20)
    
    def test_extract_with_selector(self):
        """Test de l'extraction avec sélecteurs CSS."""
        html = """
        <div>
            <h2><a href="/article">Title</a></h2>
            <time datetime="2025-01-15">Date</time>
        </div>
        """
        
        soup = self.BeautifulSoup(html, 'html.parser')
        div = soup.find('div')
        
        extractor = ConfigurableHTMLExtractor()
        
        # Test extraction de texte
        title = extractor._extract_with_selector(div, 'h2 a', 'text')
        self.assertEqual(title, 'Title')
        
        # Test extraction d'attribut
        url = extractor._extract_with_selector(div, 'h2 a', 'href')
        self.assertEqual(url, '/article')
        
        # Test extraction d'attribut datetime
        date = extractor._extract_with_selector(div, 'time', 'datetime')
        self.assertEqual(date, '2025-01-15')
    
    def test_parse_date_with_format(self):
        """Test du parsing de date avec format spécifique."""
        extractor = ConfigurableHTMLExtractor()
        
        # Test avec format spécifique
        date = extractor._parse_date_with_format('January 15, 2025', '%B %d, %Y')
        self.assertEqual(date, '2025-01-15')
        
        # Test avec format coréen
        date = extractor._parse_date_with_format('2025.01.15', '%Y.%m.%d')
        self.assertEqual(date, '2025-01-15')
        
        # Test sans format (utilise les formats par défaut)
        date = extractor._parse_date_with_format('2025-01-15', None)
        self.assertEqual(date, '2025-01-15')


class TestIngestionMetrics(unittest.TestCase):
    """Tests pour le collecteur de métriques."""
    
    def test_create_source_metrics(self):
        """Test de la création de métriques pour une source."""
        metrics = create_source_metrics(
            source_key='test_source',
            fetch_success=True,
            parse_success=True,
            items_found=10,
            items_valid=8,
            items_with_date=6,
            execution_time=2.5,
            errors=['Warning: some items skipped']
        )
        
        self.assertEqual(metrics['pages_fetched'], 1)
        self.assertEqual(metrics['items_found'], 10)
        self.assertEqual(metrics['items_valid'], 8)
        self.assertEqual(metrics['items_with_date'], 6)
        self.assertEqual(metrics['execution_time'], 2.5)
        self.assertEqual(len(metrics['errors']), 1)
        self.assertTrue(metrics['fetch_success'])
        self.assertTrue(metrics['parse_success'])
    
    def test_metrics_collector_status_calculation(self):
        """Test du calcul de statut par le collecteur de métriques."""
        collector = IngestionMetrics()
        
        # Source OK
        collector.record_source_metrics('source_ok', {
            'fetch_success': True,
            'parse_success': True,
            'items_valid': 5,
            'errors': []
        })
        
        # Source WARNING
        collector.record_source_metrics('source_warning', {
            'fetch_success': True,
            'parse_success': True,
            'items_valid': 2,
            'errors': []
        })
        
        # Source ERROR
        collector.record_source_metrics('source_error', {
            'fetch_success': False,
            'parse_success': False,
            'items_valid': 0,
            'errors': ['HTTP error']
        })
        
        # Vérifier les statuts
        self.assertEqual(collector.get_source_metrics('source_ok')['status'], 'OK')
        self.assertEqual(collector.get_source_metrics('source_warning')['status'], 'WARNING')
        self.assertEqual(collector.get_source_metrics('source_error')['status'], 'ERROR')
    
    def test_generate_summary_report(self):
        """Test de la génération de rapport de synthèse."""
        collector = IngestionMetrics()
        
        # Ajouter quelques métriques
        collector.record_source_metrics('source1', {
            'fetch_success': True,
            'parse_success': True,
            'items_valid': 10,
            'items_with_date': 8,
            'errors': []
        })
        
        collector.record_source_metrics('source2', {
            'fetch_success': False,
            'parse_success': False,
            'items_valid': 0,
            'items_with_date': 0,
            'errors': ['HTTP error']
        })
        
        report = collector.generate_summary_report()
        
        # Vérifier la synthèse
        self.assertEqual(report['summary']['total_sources'], 2)
        self.assertEqual(report['summary']['sources_ok'], 1)
        self.assertEqual(report['summary']['sources_error'], 1)
        self.assertEqual(report['summary']['success_rate'], 50.0)
        self.assertEqual(report['summary']['total_items_extracted'], 10)
        self.assertEqual(report['summary']['total_items_with_date'], 8)


if __name__ == '__main__':
    unittest.main()