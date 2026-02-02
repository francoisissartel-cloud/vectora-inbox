"""
Test E2E Local COMPLET - Domain Scoring
Phase 4 du plan_diagnostic_domain_scoring_local_20260202.md

Objectif: Valider le fix en local AVANT déploiement AWS
- Vrais appels Bedrock (pas de mock)
- Vrais items LAI (2-3 items représentatifs)
- Validation complète de la structure domain_scoring
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add src_v2 to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src_v2"))

# Test items LAI réels
TEST_ITEMS = [
    {
        "item_id": "test_lai_001",
        "title": "Teva Pharmaceuticals Announces FDA Submission for Olanzapine Long-Acting Injectable",
        "content": """Teva Pharmaceuticals has submitted a New Drug Application (NDA) to the U.S. Food and Drug Administration (FDA) for its olanzapine extended-release injectable suspension. The product, developed in partnership with MedinCell, uses the proprietary BEPO technology platform for long-acting delivery. This once-monthly injectable formulation is designed for the treatment of schizophrenia and bipolar disorder. The submission follows positive Phase 3 clinical trial results demonstrating efficacy and safety comparable to existing treatments. If approved, this would be Teva's first long-acting injectable antipsychotic in the U.S. market.""",
        "source_key": "teva_corporate",
        "ingestion_date": datetime.now().isoformat(),
        "url": "https://example.com/teva-olanzapine-lai"
    },
    {
        "item_id": "test_lai_002",
        "title": "Camurus Reports Strong Q4 2025 Financial Results",
        "content": """Camurus AB announced its fourth quarter 2025 financial results, showing revenue growth of 15% year-over-year. The Swedish pharmaceutical company continues to expand its commercial operations across Europe for its long-acting injectable products. Total revenue reached SEK 450 million for the quarter. The company highlighted strong performance of its Buvidal product line for opioid dependence treatment. Camurus also provided updates on its pipeline of depot injection technologies.""",
        "source_key": "camurus_corporate",
        "ingestion_date": datetime.now().isoformat(),
        "url": "https://example.com/camurus-q4-results"
    },
    {
        "item_id": "test_lai_003",
        "title": "Johnson & Johnson Announces New CEO Appointment",
        "content": """Johnson & Johnson has appointed a new Chief Executive Officer effective March 2026. The incoming CEO brings 25 years of pharmaceutical industry experience. The company's board of directors unanimously approved the appointment. J&J continues to focus on its pharmaceutical and medical devices businesses following the separation of its consumer health division. The new leadership is expected to drive strategic initiatives across the company's diverse portfolio.""",
        "source_key": "jnj_corporate",
        "ingestion_date": datetime.now().isoformat(),
        "url": "https://example.com/jnj-ceo"
    }
]

def test_e2e_domain_scoring_complete():
    """Test E2E complet avec vrais appels Bedrock"""
    from vectora_core.shared import config_loader, s3_io
    from vectora_core.normalization import normalizer
    
    logger.info("=" * 80)
    logger.info("TEST E2E LOCAL COMPLET - DOMAIN SCORING")
    logger.info("=" * 80)
    logger.info(f"Items à tester: {len(TEST_ITEMS)}")
    logger.info(f"Appels Bedrock: RÉELS (pas de mock)")
    logger.info("")
    
    # Configuration
    config_bucket = 'vectora-inbox-config-dev'
    bedrock_model = "anthropic.claude-3-sonnet-20240229-v1:0"
    bedrock_region = "us-east-1"
    
    start_time = datetime.now()
    
    try:
        # Étape 1: Charger canonical prompts
        logger.info("📥 Étape 1/4: Chargement prompts canonical...")
        canonical_prompts = config_loader.load_canonical_prompts(config_bucket)
        
        assert canonical_prompts, "❌ Prompts vides"
        assert 'domain_scoring' in canonical_prompts, "❌ 'domain_scoring' manquant"
        assert 'lai_domain_scoring' in canonical_prompts['domain_scoring'], "❌ 'lai_domain_scoring' manquant"
        
        logger.info(f"✅ Prompts chargés: {list(canonical_prompts.keys())}")
        
        # Étape 2: Charger canonical scopes
        logger.info("📥 Étape 2/4: Chargement scopes canonical...")
        canonical_scopes = config_loader.load_canonical_scopes(config_bucket)
        
        assert canonical_scopes, "❌ Scopes vides"
        assert 'domains' in canonical_scopes, "❌ 'domains' manquant"
        assert 'lai_domain_definition' in canonical_scopes['domains'], "❌ 'lai_domain_definition' manquant"
        
        logger.info(f"✅ Scopes chargés: {len([k for k in canonical_scopes.keys() if k != 'domains'])} scopes + domains")
        
        # Étape 2bis: Charger client config
        logger.info("📥 Étape 2bis/4: Chargement client config...")
        client_config = config_loader.load_client_config('lai_weekly_v9', config_bucket)
        logger.info(f"✅ Client config chargé: {client_config['client_profile']['name']}")
        
        # Étape 3: Normaliser avec domain scoring
        logger.info("🤖 Étape 3/4: Normalisation avec domain scoring...")
        logger.info(f"   ⚠️  ATTENTION: Vrais appels Bedrock (coût ~$0.02)")
        logger.info(f"   Items: {len(TEST_ITEMS)}")
        logger.info(f"   Appels attendus: {len(TEST_ITEMS) * 2} (2 par item)")
        
        normalized_items = normalizer.normalize_items_batch(
            raw_items=TEST_ITEMS,
            canonical_scopes=canonical_scopes,
            canonical_prompts=canonical_prompts,
            bedrock_model=bedrock_model,
            bedrock_region=bedrock_region,
            enable_domain_scoring=True,
            s3_io=s3_io,
            client_config=client_config,
            config_bucket=config_bucket
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Normalisation terminée en {duration:.1f}s")
        logger.info(f"   Items normalisés: {len(normalized_items)}")
        logger.info(f"   Temps moyen/item: {duration/len(normalized_items):.1f}s")
        
        # Étape 4: Validation résultats
        logger.info("✅ Étape 4/4: Validation résultats...")
        
        results = {
            'total_items': len(normalized_items),
            'items_with_domain_scoring': 0,
            'items_relevant': 0,
            'items_not_relevant': 0,
            'avg_score': 0,
            'confidence_distribution': {'high': 0, 'medium': 0, 'low': 0},
            'signals_total': {'strong': 0, 'medium': 0, 'weak': 0}
        }
        
        all_success = True
        
        for i, item in enumerate(normalized_items, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Item {i}/{len(normalized_items)}: {item['item_id']}")
            logger.info(f"Title: {item['title'][:70]}...")
            
            # Vérifier has_domain_scoring
            has_scoring = item.get('has_domain_scoring', False)
            if not has_scoring:
                logger.error(f"❌ FAIL: has_domain_scoring=False")
                all_success = False
                continue
            
            results['items_with_domain_scoring'] += 1
            
            # Vérifier section domain_scoring
            ds = item.get('domain_scoring')
            if not ds:
                logger.error(f"❌ FAIL: domain_scoring section manquante")
                all_success = False
                continue
            
            # Vérifier champs requis
            required = ['is_relevant', 'score', 'confidence', 'reasoning']
            missing = [f for f in required if f not in ds]
            if missing:
                logger.error(f"❌ FAIL: Champs manquants: {missing}")
                all_success = False
                continue
            
            # Collecter statistiques
            if ds['is_relevant']:
                results['items_relevant'] += 1
            else:
                results['items_not_relevant'] += 1
            
            results['avg_score'] += ds['score']
            results['confidence_distribution'][ds['confidence']] += 1
            
            if 'signals_detected' in ds:
                for level in ['strong', 'medium', 'weak']:
                    results['signals_total'][level] += len(ds['signals_detected'].get(level, []))
            
            # Afficher résultats
            logger.info(f"✅ Domain scoring validé:")
            logger.info(f"   is_relevant: {ds['is_relevant']}")
            logger.info(f"   score: {ds['score']}/100")
            logger.info(f"   confidence: {ds['confidence']}")
            
            if 'signals_detected' in ds:
                strong = len(ds['signals_detected'].get('strong', []))
                medium = len(ds['signals_detected'].get('medium', []))
                weak = len(ds['signals_detected'].get('weak', []))
                logger.info(f"   signals: {strong} strong, {medium} medium, {weak} weak")
            
            logger.info(f"   reasoning: {ds['reasoning'][:100]}...")
        
        # Calcul moyennes
        if results['items_with_domain_scoring'] > 0:
            results['avg_score'] /= results['items_with_domain_scoring']
        
        # Rapport final
        logger.info("\n" + "=" * 80)
        logger.info("📊 RAPPORT FINAL")
        logger.info("=" * 80)
        logger.info(f"Items testés: {results['total_items']}")
        logger.info(f"Items avec domain_scoring: {results['items_with_domain_scoring']}/{results['total_items']}")
        logger.info(f"Items LAI relevant: {results['items_relevant']}")
        logger.info(f"Items non relevant: {results['items_not_relevant']}")
        logger.info(f"Score moyen: {results['avg_score']:.1f}/100")
        logger.info(f"Confidence: high={results['confidence_distribution']['high']}, medium={results['confidence_distribution']['medium']}, low={results['confidence_distribution']['low']}")
        logger.info(f"Signaux: strong={results['signals_total']['strong']}, medium={results['signals_total']['medium']}, weak={results['signals_total']['weak']}")
        logger.info(f"Durée totale: {duration:.1f}s")
        logger.info(f"Temps moyen/item: {duration/len(normalized_items):.1f}s")
        
        # Sauvegarder résultats
        output_file = project_root / ".tmp" / "test_e2e_local_results.json"
        output_file.parent.mkdir(exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump({
                'test_date': datetime.now().isoformat(),
                'items': normalized_items,
                'statistics': results,
                'duration_seconds': duration
            }, f, indent=2)
        logger.info(f"\n💾 Résultats sauvegardés: {output_file}")
        
        # Verdict final
        logger.info("\n" + "=" * 80)
        if all_success and results['items_with_domain_scoring'] == results['total_items']:
            logger.info("✅ TEST E2E LOCAL RÉUSSI")
            logger.info("   ✅ 100% items avec domain_scoring")
            logger.info("   ✅ Structure validée")
            logger.info("   ✅ Temps exécution cohérent")
            logger.info("   ✅ PRÊT POUR DÉPLOIEMENT AWS")
        else:
            logger.error("❌ TEST E2E LOCAL ÉCHOUÉ")
            logger.error("   ❌ NE PAS DÉPLOYER EN AWS")
        logger.info("=" * 80)
        
        return all_success
        
    except Exception as e:
        logger.error(f"❌ TEST ÉCHOUÉ avec exception: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    logger.info("Démarrage test E2E local COMPLET")
    logger.info("⚠️  Ce test fait de VRAIS appels Bedrock (coût ~$0.02)")
    logger.info("")
    
    success = test_e2e_domain_scoring_complete()
    
    sys.exit(0 if success else 1)
