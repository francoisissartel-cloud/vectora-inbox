#!/usr/bin/env python3
"""
Test E2E Simplifié V16 - Avec Données de Test Réelles

Utilise les données de test existantes pour valider les améliorations V16
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src_v2"))

def run_e2e_test_with_real_data():
    """Test E2E avec données réelles"""
    from vectora_core.shared import config_loader, s3_io
    from vectora_core.normalization import normalizer
    
    logger.info("="*80)
    logger.info("TEST E2E V16 - DONNEES REELLES (17 DEC 2025)")
    logger.info("="*80)
    
    # Charger données de test
    test_data_path = project_root / "tests" / "data_snapshots" / "real_ingested_items_17dec.json"
    with open(test_data_path, 'r', encoding='utf-8') as f:
        ingested_items = json.load(f)
    
    logger.info(f"Items charges: {len(ingested_items)}")
    
    # Configuration
    config_bucket = 'vectora-inbox-config-dev'
    client_id = 'lai_weekly_v9'
    bedrock_model = "anthropic.claude-3-sonnet-20240229-v1:0"
    bedrock_region = "us-east-1"
    
    # Charger configs
    logger.info("Chargement configurations...")
    client_config = config_loader.load_client_config(client_id, config_bucket)
    canonical_scopes = config_loader.load_canonical_scopes(config_bucket)
    canonical_prompts = config_loader.load_canonical_prompts(config_bucket)
    
    # Normaliser
    logger.info(f"\nNormalisation de {len(ingested_items)} items...")
    logger.info("ATTENTION: Vrais appels Bedrock (~$0.15)")
    
    normalized_items = normalizer.normalize_items_batch(
        raw_items=ingested_items,
        canonical_scopes=canonical_scopes,
        canonical_prompts=canonical_prompts,
        bedrock_model=bedrock_model,
        bedrock_region=bedrock_region,
        enable_domain_scoring=True,
        s3_io=s3_io,
        client_config=client_config,
        config_bucket=config_bucket,
        max_workers=1
    )
    
    logger.info(f"Normalisation terminee: {len(normalized_items)} items")
    
    # Analyse détaillée
    logger.info("\n" + "="*80)
    logger.info("ANALYSE DETAILLEE ITEM PAR ITEM")
    logger.info("="*80)
    
    results = []
    for i, item in enumerate(normalized_items, 1):
        ds = item.get('domain_scoring', {})
        entities = item.get('normalized_content', {}).get('entities', {})
        
        result = {
            'num': i,
            'title': item.get('title', '')[:80],
            'source': item.get('source_key', ''),
            'is_relevant': ds.get('is_relevant', False),
            'score': ds.get('score', 0),
            'confidence': ds.get('confidence', 'N/A'),
            'event_type': item.get('normalized_content', {}).get('event_classification', {}).get('primary_type', 'N/A'),
            'companies': len(entities.get('companies', [])),
            'technologies': len(entities.get('technologies', [])),
            'dosing': len(entities.get('dosing_intervals', [])),
            'signals_strong': len(ds.get('signals_detected', {}).get('strong', [])),
            'signals_medium': len(ds.get('signals_detected', {}).get('medium', [])),
            'reasoning': ds.get('reasoning', '')[:100]
        }
        results.append(result)
        
        # Afficher
        status = "[OK]" if result['is_relevant'] else "[NO]"
        logger.info(f"\n{status} Item {i}/{len(normalized_items)}: {result['title']}")
        logger.info(f"    Score: {result['score']}/100 | Event: {result['event_type']} | Confidence: {result['confidence']}")
        logger.info(f"    Entities: {result['companies']} companies, {result['technologies']} tech, {result['dosing']} dosing")
        logger.info(f"    Signals: {result['signals_strong']} strong, {result['signals_medium']} medium")
        logger.info(f"    Reasoning: {result['reasoning']}...")
    
    # Statistiques
    logger.info("\n" + "="*80)
    logger.info("STATISTIQUES GLOBALES")
    logger.info("="*80)
    
    total = len(results)
    relevant = sum(1 for r in results if r['is_relevant'])
    relevant_pct = (relevant / total * 100) if total > 0 else 0
    avg_score = sum(r['score'] for r in results) / total if total > 0 else 0
    
    companies_detected = sum(1 for r in results if r['companies'] > 0)
    tech_detected = sum(1 for r in results if r['technologies'] > 0)
    dosing_detected = sum(1 for r in results if r['dosing'] > 0)
    
    logger.info(f"Total items: {total}")
    logger.info(f"Items relevant: {relevant} ({relevant_pct:.1f}%)")
    logger.info(f"Score moyen: {avg_score:.1f}/100")
    logger.info(f"Companies detectees: {companies_detected} items")
    logger.info(f"Technologies detectees: {tech_detected} items")
    logger.info(f"Dosing intervals detectes: {dosing_detected} items")
    
    # Sauvegarder
    output_dir = project_root / ".tmp" / "e2e_v16_simple"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "results.json", 'w', encoding='utf-8') as f:
        json.dump({
            'test_date': datetime.now().isoformat(),
            'total_items': total,
            'items_relevant': relevant,
            'relevant_rate': relevant_pct,
            'avg_score': avg_score,
            'companies_detected': companies_detected,
            'technologies_detected': tech_detected,
            'dosing_detected': dosing_detected,
            'items': results
        }, f, indent=2, ensure_ascii=False)
    
    # Rapport markdown
    generate_report(results, total, relevant, relevant_pct, avg_score, output_dir)
    
    logger.info(f"\n[OK] Resultats sauvegardes: {output_dir}")
    logger.info(f"    - results.json")
    logger.info(f"    - report.md")
    
    # Verdict
    logger.info("\n" + "="*80)
    logger.info("VERDICT")
    logger.info("="*80)
    
    if relevant_pct >= 54.0:
        logger.info(f"[OK] Taux pertinence: {relevant_pct:.1f}% >= 54%")
        logger.info("[OK] QUALITE AMELIOREE - GO POUR PHASE 2")
        return True
    else:
        logger.warning(f"[WARN] Taux pertinence: {relevant_pct:.1f}% < 54%")
        logger.warning("[WARN] QUALITE INSUFFISANTE")
        return False

def generate_report(results, total, relevant, relevant_pct, avg_score, output_dir):
    """Génère rapport markdown"""
    report = f"""# Test E2E V16 - Rapport Détaillé

**Date**: {datetime.now().isoformat()}  
**Items testés**: {total}  
**Items relevant**: {relevant} ({relevant_pct:.1f}%)  
**Score moyen**: {avg_score:.1f}/100

---

## Comparaison V15 vs V16

| Métrique | V15 | V16 | Évolution |
|----------|-----|-----|-----------|
| Items ingérés | 29 | {total} | {total - 29:+d} |
| Items relevant | 12 (41%) | {relevant} ({relevant_pct:.1f}%) | {relevant_pct - 41:.1f}% |
| Score moyen | 81.7 | {avg_score:.1f} | {avg_score - 81.7:+.1f} |

---

## Détail Item par Item

"""
    
    for r in results:
        status_icon = "✅" if r['is_relevant'] else "❌"
        report += f"""
### {status_icon} Item {r['num']}: {r['title']}

- **Source**: {r['source']}
- **Score**: {r['score']}/100 (confidence: {r['confidence']})
- **Event**: {r['event_type']}
- **Entities**: {r['companies']} companies, {r['technologies']} tech, {r['dosing']} dosing
- **Signals**: {r['signals_strong']} strong, {r['signals_medium']} medium
- **Reasoning**: {r['reasoning']}...

"""
    
    report += f"""
---

## Verdict

"""
    
    if relevant_pct >= 54.0:
        report += f"""✅ **QUALITÉ AMÉLIORÉE**

Taux de pertinence: {relevant_pct:.1f}% >= 54% (objectif)

**Prêt pour Phase 2 (Deploy AWS)**
"""
    else:
        report += f"""⚠️ **QUALITÉ INSUFFISANTE**

Taux de pertinence: {relevant_pct:.1f}% < 54% (objectif)

**Corriger avant Phase 2**
"""
    
    with open(output_dir / "report.md", 'w', encoding='utf-8') as f:
        f.write(report)

if __name__ == "__main__":
    success = run_e2e_test_with_real_data()
    sys.exit(0 if success else 1)
