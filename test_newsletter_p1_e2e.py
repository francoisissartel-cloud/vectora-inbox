#!/usr/bin/env python3
"""
Test Newsletter P1 E2E - Phase 4 avec données AWS réelles

Ce script teste la newsletter P1 avec les données normalisées du 12/12
pour valider le déploiement AWS et la configuration hybride.
"""

import json
import logging
import os
import sys
from datetime import datetime

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from vectora_core.newsletter import assembler

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_p1_environment():
    """Configure l'environnement P1 hybride"""
    os.environ["BEDROCK_REGION_NEWSLETTER"] = "eu-west-3"
    os.environ["BEDROCK_MODEL_ID_NEWSLETTER"] = "eu.anthropic.claude-sonnet-4-5-20250929-v1:0"
    os.environ["BEDROCK_REGION_NORMALIZATION"] = "us-east-1"
    os.environ["BEDROCK_MODEL_ID_NORMALIZATION"] = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
    os.environ["NEWSLETTERS_BUCKET"] = "vectora-inbox-newsletters-dev"
    logger.info("✅ Environnement P1 hybride configuré")

def load_test_data():
    """Charge les données normalisées du 12/12"""
    with open("items_normalized_p1_test.json", "r", encoding="utf-8") as f:
        items = json.load(f)
    
    logger.info(f"📊 {len(items)} items normalisés chargés")
    
    # Analyser les items gold
    gold_items = []
    for item in items:
        title = item.get('title', '').lower()
        if ('nanexa' in title and 'moderna' in title) or 'uzedy' in title or ('medicell' in title and 'malaria' in title):
            gold_items.append(item['title'][:100])
    
    logger.info(f"🎯 {len(gold_items)} items gold détectés:")
    for item in gold_items:
        logger.info(f"   • {item}")
    
    return items

def load_client_config():
    """Charge la configuration lai_weekly_v3"""
    config = {
        "client_profile": {
            "name": "LAI Intelligence Weekly v3 P1 Test",
            "client_id": "lai_weekly_v3",
            "language": "en",
            "tone": "executive",
            "voice": "concise"
        },
        "newsletter_layout": {
            "sections": [
                {
                    "id": "top_signals",
                    "title": "Top Signals – LAI Ecosystem",
                    "source_domains": ["tech_lai_ecosystem", "regulatory_lai"],
                    "max_items": 5,
                    "sort_by": "score_desc"
                },
                {
                    "id": "partnerships_deals",
                    "title": "Partnerships & Deals",
                    "source_domains": ["tech_lai_ecosystem"],
                    "max_items": 5,
                    "filter_event_types": ["partnership", "corporate_move"],
                    "sort_by": "date_desc"
                },
                {
                    "id": "regulatory_updates",
                    "title": "Regulatory Updates",
                    "source_domains": ["regulatory_lai"],
                    "max_items": 5,
                    "filter_event_types": ["regulatory"],
                    "sort_by": "score_desc"
                },
                {
                    "id": "clinical_updates",
                    "title": "Clinical Updates",
                    "source_domains": ["tech_lai_ecosystem"],
                    "max_items": 8,
                    "filter_event_types": ["clinical_update"],
                    "sort_by": "date_desc"
                }
            ]
        },
        "newsletter_delivery": {
            "format": "markdown",
            "include_tldr": True,
            "include_intro": True
        }
    }
    return config

def test_newsletter_p1_e2e():
    """Test E2E newsletter P1 avec données AWS réelles"""
    logger.info("🚀 Démarrage test Newsletter P1 E2E")
    
    try:
        # Configuration
        setup_p1_environment()
        
        # Chargement données
        items = load_test_data()
        client_config = load_client_config()
        
        # Paramètres test
        target_date = "2025-12-12"
        from_date = "2025-12-05"
        to_date = "2025-12-12"
        
        # Test génération P1
        logger.info("📝 Génération newsletter P1...")
        start_time = datetime.now()
        
        newsletter_md, stats, editorial_content = assembler.generate_newsletter(
            scored_items=items,
            client_config=client_config,
            bedrock_model_id="eu.anthropic.claude-sonnet-4-5-20250929-v1:0",
            target_date=target_date,
            from_date=from_date,
            to_date=to_date,
            client_id="lai_weekly_v3",
            newsletters_bucket="vectora-inbox-newsletters-dev",
            force_regenerate=True  # Premier test
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Analyse résultats
        logger.info(f"⏱️ Durée génération : {duration:.2f}s")
        logger.info(f"📊 Items sélectionnés : {stats.get('items_selected', 0)}")
        logger.info(f"📄 Sections générées : {stats.get('sections_generated', 0)}")
        logger.info(f"📝 Newsletter taille : {len(newsletter_md)} caractères")
        
        # Validation items gold
        items_gold_detected = []
        newsletter_lower = newsletter_md.lower()
        if "nanexa" in newsletter_lower and "moderna" in newsletter_lower:
            items_gold_detected.append("Nanexa/Moderna")
        if "uzedy" in newsletter_lower:
            items_gold_detected.append("UZEDY®")
        if "medicell" in newsletter_lower and "malaria" in newsletter_lower:
            items_gold_detected.append("MedinCell malaria")
        
        logger.info(f"🎯 Items gold dans newsletter : {items_gold_detected}")
        
        # Validation structure
        has_title = "title" in editorial_content
        has_intro = "intro" in editorial_content
        has_sections = len(editorial_content.get("sections", [])) > 0
        has_tldr = len(editorial_content.get("tldr", [])) > 0
        
        logger.info(f"🏗️ Structure : title={has_title}, intro={has_intro}, sections={has_sections}, tldr={has_tldr}")
        
        # Test cache (2ème run)
        logger.info("🔄 Test cache (2ème run)...")
        start_time_cache = datetime.now()
        
        newsletter_md_cache, stats_cache, editorial_content_cache = assembler.generate_newsletter(
            scored_items=items,
            client_config=client_config,
            bedrock_model_id="eu.anthropic.claude-sonnet-4-5-20250929-v1:0",
            target_date=target_date,
            from_date=from_date,
            to_date=to_date,
            client_id="lai_weekly_v3",
            newsletters_bucket="vectora-inbox-newsletters-dev",
            force_regenerate=False  # Test cache
        )
        
        end_time_cache = datetime.now()
        duration_cache = (end_time_cache - start_time_cache).total_seconds()
        
        logger.info(f"⚡ Durée cache : {duration_cache:.2f}s")
        cache_hit = duration_cache < duration / 2
        logger.info(f"💾 Cache efficace : {cache_hit}")
        
        # Sauvegarde résultats
        with open("newsletter_p1_e2e_result.md", "w", encoding="utf-8") as f:
            f.write(newsletter_md)
        
        with open("newsletter_p1_e2e_editorial.json", "w", encoding="utf-8") as f:
            json.dump(editorial_content, f, indent=2, ensure_ascii=False)
        
        # Évaluation finale
        success_criteria = [
            duration < 60,  # Performance
            stats.get('items_selected', 0) > 0,  # Items sélectionnés
            len(items_gold_detected) >= 1,  # Au moins 1 item gold
            has_title and has_intro and has_sections,  # Structure
            cache_hit  # Cache efficace
        ]
        
        success_rate = sum(success_criteria) / len(success_criteria) * 100
        
        logger.info("=" * 60)
        logger.info("📊 RÉSULTATS TEST P1 E2E")
        logger.info(f"⏱️ Performance : {duration:.2f}s ({'✅' if duration < 60 else '❌'})")
        logger.info(f"📊 Items sélectionnés : {stats.get('items_selected', 0)} ({'✅' if stats.get('items_selected', 0) > 0 else '❌'})")
        logger.info(f"🎯 Items gold : {len(items_gold_detected)} ({'✅' if len(items_gold_detected) >= 1 else '❌'})")
        logger.info(f"🏗️ Structure complète : {'✅' if has_title and has_intro and has_sections else '❌'}")
        logger.info(f"💾 Cache efficace : {'✅' if cache_hit else '❌'}")
        logger.info(f"🎯 Taux de réussite : {success_rate:.1f}%")
        
        if success_rate >= 80:
            logger.info("✅ TEST P1 E2E : RÉUSSI")
            logger.info("🚀 Newsletter P1 validée pour production")
            return True
        else:
            logger.warning("⚠️ TEST P1 E2E : PARTIEL")
            logger.info("🔧 Ajustements nécessaires")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur test P1 E2E : {e}")
        return False

if __name__ == "__main__":
    success = test_newsletter_p1_e2e()
    sys.exit(0 if success else 1)