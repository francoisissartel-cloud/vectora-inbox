"""
Test E2E Local - Domain Scoring

Objectif: Valider le domain scoring en local AVANT déploiement AWS
- Charger config client lai_weekly_v9
- Charger canonical prompts et scopes
- Normaliser 2-3 items avec domain scoring activé
- Vérifier présence de domain_scoring dans les résultats
"""

import sys
import os
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add src_v2 to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src_v2"))

def test_e2e_domain_scoring_local():
    """Test E2E complet avec domain scoring"""
    from vectora_core.shared import config_loader
    from vectora_core.normalization import normalizer
    
    logger.info("=" * 80)
    logger.info("TEST E2E LOCAL - DOMAIN SCORING")
    logger.info("=" * 80)
    
    # Configuration
    config_bucket = 'vectora-inbox-config-dev'
    bedrock_model = "anthropic.claude-3-sonnet-20240229-v1:0"
    bedrock_region = "us-east-1"
    
    # Items de test (2 items réels du LAI)
    test_items = [
        {
            "item_id": "test_001",
            "title": "Teva Pharmaceuticals Announces FDA Submission for Olanzapine Long-Acting Injectable",
            "content": "Teva Pharmaceuticals has submitted a New Drug Application to the U.S. FDA for its olanzapine extended-release injectable suspension. The product uses MedinCell's BEPO technology platform for long-acting delivery.",
            "source_key": "test_source",
            "ingestion_date": "2026-02-02T10:00:00Z",
            "url": "https://example.com/test1"
        },
        {
            "item_id": "test_002",
            "title": "Camurus Reports Q4 Financial Results",
            "content": "Camurus AB announced its fourth quarter financial results showing revenue growth. The company continues to expand its commercial operations in Europe.",
            "source_key": "test_source",
            "ingestion_date": "2026-02-02T11:00:00Z",
            "url": "https://example.com/test2"
        }
    ]
    
    try:
        # Étape 1: Charger canonical prompts
        logger.info("Étape 1: Chargement des prompts canonical...")
        canonical_prompts = config_loader.load_canonical_prompts(config_bucket)
        
        if not canonical_prompts:
            logger.error("❌ FAIL: Prompts canonical vides")
            return False
        
        if 'domain_scoring' not in canonical_prompts:
            logger.error("❌ FAIL: 'domain_scoring' manquant dans prompts")
            return False
        
        if 'lai_domain_scoring' not in canonical_prompts['domain_scoring']:
            logger.error("❌ FAIL: 'lai_domain_scoring' manquant")
            return False
        
        logger.info("✅ Prompts canonical chargés")
        logger.info(f"   Catégories: {list(canonical_prompts.keys())}")
        
        # Étape 2: Charger canonical scopes
        logger.info("Étape 2: Chargement des scopes canonical...")
        canonical_scopes = config_loader.load_canonical_scopes(config_bucket)
        
        if not canonical_scopes:
            logger.error("❌ FAIL: Scopes canonical vides")
            return False
        
        if 'domains' not in canonical_scopes:
            logger.error("❌ FAIL: 'domains' manquant dans scopes")
            return False
        
        if 'lai_domain_definition' not in canonical_scopes['domains']:
            logger.error("❌ FAIL: 'lai_domain_definition' manquant")
            return False
        
        logger.info("✅ Scopes canonical chargés")
        logger.info(f"   Scopes: {len([k for k in canonical_scopes.keys() if k != 'domains'])} scopes")
        logger.info(f"   Domains: {list(canonical_scopes['domains'].keys())}")
        
        # Étape 3: Normaliser items avec domain scoring
        logger.info("Étape 3: Normalisation avec domain scoring...")
        logger.info(f"   Items à traiter: {len(test_items)}")
        logger.info(f"   Domain scoring: ACTIVÉ")
        
        normalized_items = normalizer.normalize_items_batch(
            raw_items=test_items,
            canonical_scopes=canonical_scopes,
            canonical_prompts=canonical_prompts,
            bedrock_model=bedrock_model,
            bedrock_region=bedrock_region,
            enable_domain_scoring=True
        )
        
        logger.info(f"✅ Normalisation terminée: {len(normalized_items)} items")
        
        # Étape 4: Validation des résultats
        logger.info("Étape 4: Validation des résultats...")
        
        success = True
        for i, item in enumerate(normalized_items, 1):
            logger.info(f"\n--- Item {i}/{len(normalized_items)} ---")
            logger.info(f"  ID: {item.get('item_id')}")
            logger.info(f"  Title: {item.get('title', '')[:60]}...")
            
            # Vérifier has_domain_scoring
            has_scoring = item.get('has_domain_scoring', False)
            logger.info(f"  has_domain_scoring: {has_scoring}")
            
            if not has_scoring:
                logger.error(f"  ❌ FAIL: has_domain_scoring=False")
                success = False
                continue
            
            # Vérifier section domain_scoring
            domain_scoring = item.get('domain_scoring')
            if not domain_scoring:
                logger.error(f"  ❌ FAIL: domain_scoring section manquante")
                success = False
                continue
            
            # Vérifier champs requis
            required_fields = ['is_relevant', 'score', 'confidence', 'reasoning']
            missing_fields = [f for f in required_fields if f not in domain_scoring]
            
            if missing_fields:
                logger.error(f"  ❌ FAIL: Champs manquants: {missing_fields}")
                success = False
                continue
            
            # Afficher résultats
            logger.info(f"  ✅ Domain scoring présent:")
            logger.info(f"     is_relevant: {domain_scoring.get('is_relevant')}")
            logger.info(f"     score: {domain_scoring.get('score')}")
            logger.info(f"     confidence: {domain_scoring.get('confidence')}")
            logger.info(f"     reasoning: {domain_scoring.get('reasoning', '')[:80]}...")
            
            if 'signals_detected' in domain_scoring:
                signals = domain_scoring['signals_detected']
                logger.info(f"     signals: {len(signals)} signal(s)")
        
        # Résumé final
        logger.info("\n" + "=" * 80)
        if success:
            logger.info("✅ TEST E2E RÉUSSI")
            logger.info(f"   {len(normalized_items)}/{len(test_items)} items avec domain_scoring")
            logger.info("   Prêt pour déploiement AWS")
        else:
            logger.error("❌ TEST E2E ÉCHOUÉ")
            logger.error("   NE PAS DÉPLOYER EN AWS")
        logger.info("=" * 80)
        
        return success
        
    except Exception as e:
        logger.error(f"❌ TEST E2E ÉCHOUÉ avec exception: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    logger.info("Démarrage test E2E local - Domain Scoring")
    logger.info("")
    
    success = test_e2e_domain_scoring_local()
    
    sys.exit(0 if success else 1)
