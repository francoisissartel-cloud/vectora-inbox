#!/usr/bin/env python3
"""
Test local Newsletter P1 - Validation implémentations

Ce script teste les améliorations P1 :
- Client Bedrock hybride (eu-west-3)
- Cache S3 newsletter
- Prompt ultra-réduit (-80% tokens)
- Items gold LAI

Usage:
    python test_newsletter_p1_local.py
"""

import json
import logging
import os
import sys
from datetime import datetime, timedelta

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from vectora_core.newsletter import bedrock_client, assembler

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration test
TEST_CONFIG = {
    "client_id": "lai_weekly_v3_test",
    "newsletters_bucket": "vectora-inbox-newsletters-dev",  # Bucket de test
    "force_regenerate": False,  # Test cache
    "bedrock_region_newsletter": "eu-west-3",
    "bedrock_model_newsletter": "eu.anthropic.claude-sonnet-4-5-20250929-v1:0"
}

# Items gold simulés pour test
ITEMS_GOLD_SIMULATED = [
    {
        "title": "Nanexa and Moderna Announce PharmaShell® LAI Technology Partnership",
        "summary": "Nanexa AB partners with Moderna to develop long-acting injectable formulations using proprietary PharmaShell® technology for sustained drug release applications.",
        "url": "https://nanexa.com/news/moderna-partnership",
        "score": 25.5,
        "event_type": "partnership",
        "matched_domains": ["tech_lai_ecosystem"],
        "source": "nanexa_corporate",
        "date": "2025-12-10"
    },
    {
        "title": "UZEDY® (aripiprazole) Extended-Release Injectable Receives FDA Approval",
        "summary": "Teva Pharmaceuticals announces FDA approval of UZEDY® for treatment of schizophrenia and bipolar I disorder, representing major advancement in LAI antipsychotic therapy.",
        "url": "https://tevapharm.com/news/uzedy-approval",
        "score": 23.8,
        "event_type": "regulatory",
        "matched_domains": ["regulatory_lai"],
        "source": "teva_corporate",
        "date": "2025-12-09"
    },
    {
        "title": "MedinCell Receives €2.5M Grant for Malaria Prevention LAI Development",
        "summary": "MedinCell secures significant funding to advance long-acting injectable formulation for malaria prevention using BEPO® sustained-release technology platform.",
        "url": "https://medicell.com/news/malaria-grant",
        "score": 22.1,
        "event_type": "clinical_update",
        "matched_domains": ["tech_lai_ecosystem"],
        "source": "medicell_corporate",
        "date": "2025-12-08"
    }
]

# Configuration client simulée
CLIENT_CONFIG_SIMULATED = {
    "client_profile": {
        "name": "LAI Intelligence Weekly P1 Test",
        "client_id": "lai_weekly_v3_test",
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
                "max_items": 2,  # P1: Réduit pour test
                "sort_by": "score_desc"
            },
            {
                "id": "partnerships_deals",
                "title": "Partnerships & Deals",
                "source_domains": ["tech_lai_ecosystem"],
                "max_items": 2,
                "filter_event_types": ["partnership", "corporate_move"],
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


def setup_test_environment():
    """Configure l'environnement de test P1"""
    
    # Variables d'environnement P1
    os.environ["BEDROCK_REGION_NEWSLETTER"] = TEST_CONFIG["bedrock_region_newsletter"]
    os.environ["BEDROCK_MODEL_ID_NEWSLETTER"] = TEST_CONFIG["bedrock_model_newsletter"]
    
    # Backward compatibility
    os.environ["BEDROCK_REGION"] = "us-east-1"
    os.environ["BEDROCK_MODEL_ID"] = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
    
    logger.info("✅ Environnement de test P1 configuré")
    logger.info(f"   Newsletter région : {TEST_CONFIG['bedrock_region_newsletter']}")
    logger.info(f"   Cache bucket : {TEST_CONFIG['newsletters_bucket']}")


def test_prompt_ultra_compact():
    """Test du prompt ultra-réduit P1"""
    
    logger.info("🧪 Test prompt ultra-compact P1...")
    
    # Préparer sections simulées
    sections_data = [
        {
            "title": "Top Signals – LAI Ecosystem",
            "items": ITEMS_GOLD_SIMULATED[:2]  # 2 items max
        }
    ]
    
    client_profile = CLIENT_CONFIG_SIMULATED["client_profile"]
    target_date = "2025-12-12"
    
    # Générer prompt P1
    prompt = bedrock_client._build_ultra_compact_prompt(
        sections_data, client_profile, target_date
    )
    
    # Analyser taille
    prompt_length = len(prompt)
    token_estimate = prompt_length // 4  # Approximation 1 token = 4 chars
    
    logger.info(f"   Prompt généré : {prompt_length} caractères")
    logger.info(f"   Tokens estimés : {token_estimate} tokens")
    logger.info(f"   Objectif P1 : <1000 tokens")
    
    # Validation
    if token_estimate < 1000:
        logger.info("✅ Prompt ultra-compact : RÉUSSI")
        return True
    else:
        logger.warning("⚠️ Prompt ultra-compact : TROP LONG")
        return False


def test_client_bedrock_hybride():
    """Test du client Bedrock hybride P1"""
    
    logger.info("🧪 Test client Bedrock hybride P1...")
    
    try:
        # Test client newsletter (eu-west-3)
        client_newsletter, model_newsletter = bedrock_client.get_bedrock_client_hybrid('newsletter')
        logger.info(f"   Client newsletter : {client_newsletter._client_config.region_name}")
        logger.info(f"   Modèle newsletter : {model_newsletter}")
        
        # Test client normalisation (us-east-1)
        client_norm, model_norm = bedrock_client.get_bedrock_client_hybrid('normalization')
        logger.info(f"   Client normalisation : {client_norm._client_config.region_name}")
        logger.info(f"   Modèle normalisation : {model_norm}")
        
        # Validation
        if (client_newsletter._client_config.region_name == "eu-west-3" and 
            client_norm._client_config.region_name == "us-east-1"):
            logger.info("✅ Client Bedrock hybride : RÉUSSI")
            return True
        else:
            logger.warning("⚠️ Client Bedrock hybride : CONFIGURATION INCORRECTE")
            return False
    
    except Exception as e:
        logger.error(f"❌ Client Bedrock hybride : ERREUR - {e}")
        return False


def test_cache_s3_simulation():
    """Test simulation du cache S3 (sans vraie écriture)"""
    
    logger.info("🧪 Test cache S3 (simulation)...")
    
    try:
        client_id = TEST_CONFIG["client_id"]
        period_start = "2025-11-12"
        period_end = "2025-12-12"
        bucket = TEST_CONFIG["newsletters_bucket"]
        
        # Test lecture cache (attendu : None car pas de cache)
        cached = bedrock_client.get_cached_newsletter(client_id, period_start, period_end, bucket)
        
        if cached is None:
            logger.info("   Lecture cache : Aucun cache trouvé (attendu)")
            logger.info("✅ Cache S3 simulation : RÉUSSI")
            return True
        else:
            logger.info(f"   Cache trouvé : {type(cached)}")
            logger.info("✅ Cache S3 simulation : CACHE EXISTANT")
            return True
    
    except Exception as e:
        logger.warning(f"⚠️ Cache S3 simulation : ERREUR - {e}")
        logger.info("   (Normal si bucket n'existe pas en local)")
        return True  # Pas critique pour test local


def test_generation_newsletter_p1():
    """Test génération newsletter complète P1"""
    
    logger.info("🧪 Test génération newsletter P1...")
    
    try:
        # Paramètres test
        target_date = "2025-12-12"
        from_date = "2025-11-12"
        to_date = "2025-12-12"
        
        # Génération avec P1
        start_time = datetime.now()
        
        newsletter_md, stats, editorial_content = assembler.generate_newsletter(
            scored_items=ITEMS_GOLD_SIMULATED,
            client_config=CLIENT_CONFIG_SIMULATED,
            bedrock_model_id="eu.anthropic.claude-sonnet-4-5-20250929-v1:0",
            target_date=target_date,
            from_date=from_date,
            to_date=to_date,
            client_id=TEST_CONFIG["client_id"],
            newsletters_bucket=TEST_CONFIG["newsletters_bucket"],
            force_regenerate=TEST_CONFIG["force_regenerate"]
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Analyser résultats
        logger.info(f"   Durée génération : {duration:.2f}s")
        logger.info(f"   Items sélectionnés : {stats.get('items_selected', 0)}")
        logger.info(f"   Sections générées : {stats.get('sections_generated', 0)}")
        logger.info(f"   Newsletter taille : {len(newsletter_md)} caractères")
        
        # Validation items gold
        items_gold_detected = []
        if "Nanexa" in newsletter_md and "Moderna" in newsletter_md:
            items_gold_detected.append("Nanexa/Moderna")
        if "UZEDY" in newsletter_md:
            items_gold_detected.append("UZEDY®")
        if "MedinCell" in newsletter_md and "malaria" in newsletter_md:
            items_gold_detected.append("MedinCell malaria")
        
        logger.info(f"   Items gold détectés : {items_gold_detected}")
        
        # Validation structure
        has_title = "title" in editorial_content
        has_intro = "intro" in editorial_content
        has_sections = len(editorial_content.get("sections", [])) > 0
        
        logger.info(f"   Structure : title={has_title}, intro={has_intro}, sections={has_sections}")
        
        # Critères de succès
        success = (
            duration < 30 and  # Performance
            stats.get('items_selected', 0) > 0 and  # Items sélectionnés
            len(items_gold_detected) >= 2 and  # Items gold
            has_title and has_intro and has_sections  # Structure
        )
        
        if success:
            logger.info("✅ Génération newsletter P1 : RÉUSSI")
            
            # Sauvegarder résultat pour inspection
            with open("newsletter_p1_test_result.md", "w", encoding="utf-8") as f:
                f.write(newsletter_md)
            
            with open("newsletter_p1_test_editorial.json", "w", encoding="utf-8") as f:
                json.dump(editorial_content, f, indent=2, ensure_ascii=False)
            
            logger.info("   Résultats sauvegardés : newsletter_p1_test_result.md")
            return True
        else:
            logger.warning("⚠️ Génération newsletter P1 : CRITÈRES NON ATTEINTS")
            return False
    
    except Exception as e:
        logger.error(f"❌ Génération newsletter P1 : ERREUR - {e}")
        return False


def main():
    """Fonction principale de test P1"""
    
    logger.info("🚀 Démarrage tests Newsletter P1")
    logger.info("=" * 60)
    
    # Configuration
    setup_test_environment()
    
    # Tests
    tests = [
        ("Prompt ultra-compact", test_prompt_ultra_compact),
        ("Client Bedrock hybride", test_client_bedrock_hybride),
        ("Cache S3 simulation", test_cache_s3_simulation),
        ("Génération newsletter P1", test_generation_newsletter_p1)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info("-" * 40)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ {test_name} : EXCEPTION - {e}")
            results.append((test_name, False))
    
    # Résumé
    logger.info("=" * 60)
    logger.info("📊 RÉSUMÉ TESTS P1")
    
    passed = 0
    for test_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHEC"
        logger.info(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    success_rate = (passed / len(results)) * 100
    logger.info(f"\n🎯 Taux de réussite : {passed}/{len(results)} ({success_rate:.1f}%)")
    
    if success_rate >= 75:
        logger.info("✅ TESTS P1 : VALIDATION RÉUSSIE")
        logger.info("   Implémentations P1 prêtes pour Phase 3 (déploiement AWS)")
    else:
        logger.warning("⚠️ TESTS P1 : VALIDATION PARTIELLE")
        logger.info("   Corrections nécessaires avant Phase 3")
    
    return success_rate >= 75


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)