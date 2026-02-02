"""
Test unitaire pour config_loader - Domain Scoring

Objectif: Identifier pourquoi le chargement des prompts domain_scoring échoue
"""

import sys
import os
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add src_v2 to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src_v2"))

def test_load_canonical_prompts_domain_scoring():
    """Test chargement prompts domain_scoring depuis S3"""
    from vectora_core.shared import config_loader
    
    logger.info("=" * 80)
    logger.info("TEST: load_canonical_prompts - Domain Scoring")
    logger.info("=" * 80)
    
    bucket_name = 'vectora-inbox-config-dev'
    
    try:
        logger.info(f"Loading canonical prompts from bucket: {bucket_name}")
        prompts = config_loader.load_canonical_prompts(bucket_name)
        
        # Vérifications de base
        logger.info(f"✓ Prompts loaded successfully")
        logger.info(f"  Type: {type(prompts)}")
        logger.info(f"  Is None: {prompts is None}")
        
        if prompts is None:
            logger.error("❌ FAIL: prompts is None")
            return False
        
        # Vérifier structure
        logger.info(f"  Top-level keys: {list(prompts.keys())}")
        
        # Vérifier domain_scoring
        if 'domain_scoring' not in prompts:
            logger.error("❌ FAIL: 'domain_scoring' not in prompts")
            logger.info(f"  Available keys: {list(prompts.keys())}")
            return False
        
        logger.info(f"✓ 'domain_scoring' key found")
        logger.info(f"  Type: {type(prompts['domain_scoring'])}")
        logger.info(f"  Keys: {list(prompts['domain_scoring'].keys()) if prompts['domain_scoring'] else 'None'}")
        
        # Vérifier lai_domain_scoring
        if 'lai_domain_scoring' not in prompts['domain_scoring']:
            logger.error("❌ FAIL: 'lai_domain_scoring' not in prompts['domain_scoring']")
            logger.info(f"  Available keys: {list(prompts['domain_scoring'].keys())}")
            return False
        
        logger.info(f"✓ 'lai_domain_scoring' key found")
        
        lai_scoring = prompts['domain_scoring']['lai_domain_scoring']
        if lai_scoring is None:
            logger.error("❌ FAIL: lai_domain_scoring is None")
            return False
        
        logger.info(f"  Type: {type(lai_scoring)}")
        logger.info(f"  Keys: {list(lai_scoring.keys())[:5]}...")  # First 5 keys
        
        # Vérifier contenu
        required_keys = ['system_prompt', 'user_prompt_template']
        for key in required_keys:
            if key not in lai_scoring:
                logger.error(f"❌ FAIL: '{key}' not in lai_domain_scoring")
                return False
            logger.info(f"✓ '{key}' found")
        
        logger.info("=" * 80)
        logger.info("✅ TEST PASSED: Domain scoring prompts loaded successfully")
        logger.info("=" * 80)
        return True
        
    except Exception as e:
        logger.error(f"❌ TEST FAILED with exception: {e}", exc_info=True)
        return False


def test_load_canonical_scopes_domains():
    """Test chargement domains depuis S3"""
    from vectora_core.shared import config_loader
    
    logger.info("=" * 80)
    logger.info("TEST: load_canonical_scopes - Domains")
    logger.info("=" * 80)
    
    bucket_name = 'vectora-inbox-config-dev'
    
    try:
        logger.info(f"Loading canonical scopes from bucket: {bucket_name}")
        scopes = config_loader.load_canonical_scopes(bucket_name)
        
        # Vérifications de base
        logger.info(f"✓ Scopes loaded successfully")
        logger.info(f"  Type: {type(scopes)}")
        logger.info(f"  Is None: {scopes is None}")
        
        if scopes is None:
            logger.error("❌ FAIL: scopes is None")
            return False
        
        # Vérifier structure
        logger.info(f"  Top-level keys: {list(scopes.keys())}")
        
        # Vérifier domains
        if 'domains' not in scopes:
            logger.error("❌ FAIL: 'domains' not in scopes")
            logger.info(f"  Available keys: {list(scopes.keys())}")
            return False
        
        logger.info(f"✓ 'domains' key found")
        logger.info(f"  Type: {type(scopes['domains'])}")
        logger.info(f"  Keys: {list(scopes['domains'].keys()) if scopes['domains'] else 'None'}")
        
        # Vérifier lai_domain_definition
        if 'lai_domain_definition' not in scopes['domains']:
            logger.error("❌ FAIL: 'lai_domain_definition' not in scopes['domains']")
            logger.info(f"  Available keys: {list(scopes['domains'].keys())}")
            return False
        
        logger.info(f"✓ 'lai_domain_definition' key found")
        
        lai_domain = scopes['domains']['lai_domain_definition']
        if lai_domain is None:
            logger.error("❌ FAIL: lai_domain_definition is None")
            return False
        
        logger.info(f"  Type: {type(lai_domain)}")
        logger.info(f"  Keys: {list(lai_domain.keys())[:5]}...")  # First 5 keys
        
        # Vérifier contenu
        required_keys = ['domain_name', 'domain_description']
        for key in required_keys:
            if key not in lai_domain:
                logger.error(f"❌ FAIL: '{key}' not in lai_domain_definition")
                return False
            logger.info(f"✓ '{key}' found")
        
        logger.info("=" * 80)
        logger.info("✅ TEST PASSED: Domain definition loaded successfully")
        logger.info("=" * 80)
        return True
        
    except Exception as e:
        logger.error(f"❌ TEST FAILED with exception: {e}", exc_info=True)
        return False


def test_config_loader_structure():
    """Test structure complète retournée par config_loader"""
    from vectora_core.shared import config_loader
    
    logger.info("=" * 80)
    logger.info("TEST: Config Loader Structure")
    logger.info("=" * 80)
    
    bucket_name = 'vectora-inbox-config-dev'
    
    try:
        # Load both
        prompts = config_loader.load_canonical_prompts(bucket_name)
        scopes = config_loader.load_canonical_scopes(bucket_name)
        
        logger.info("Structure Analysis:")
        logger.info(f"  Prompts type: {type(prompts)}")
        logger.info(f"  Prompts keys: {list(prompts.keys()) if prompts else 'None'}")
        
        if prompts and 'domain_scoring' in prompts:
            logger.info(f"  Domain scoring keys: {list(prompts['domain_scoring'].keys())}")
        
        logger.info(f"  Scopes type: {type(scopes)}")
        logger.info(f"  Scopes keys: {list(scopes.keys()) if scopes else 'None'}")
        
        if scopes and 'domains' in scopes:
            logger.info(f"  Domains keys: {list(scopes['domains'].keys())}")
        
        logger.info("=" * 80)
        logger.info("✅ TEST PASSED: Structure analysis complete")
        logger.info("=" * 80)
        return True
        
    except Exception as e:
        logger.error(f"❌ TEST FAILED with exception: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    logger.info("Starting config_loader domain scoring tests...")
    logger.info("")
    
    results = []
    
    # Test 1: Load prompts
    results.append(("Load Canonical Prompts", test_load_canonical_prompts_domain_scoring()))
    logger.info("")
    
    # Test 2: Load scopes
    results.append(("Load Canonical Scopes", test_load_canonical_scopes_domains()))
    logger.info("")
    
    # Test 3: Structure
    results.append(("Config Loader Structure", test_config_loader_structure()))
    logger.info("")
    
    # Summary
    logger.info("=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    logger.info("=" * 80)
    if all_passed:
        logger.info("✅ ALL TESTS PASSED")
    else:
        logger.info("❌ SOME TESTS FAILED")
    logger.info("=" * 80)
    
    sys.exit(0 if all_passed else 1)
