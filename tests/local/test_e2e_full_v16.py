#!/usr/bin/env python3
"""
Test E2E Complet V16 - Données Fraîches avec Analyse Détaillée Item par Item

Objectif: Valider les améliorations V16 vs V15 avec vraies données RSS
- Ingestion complète (vraies sources)
- Normalisation avec nouveaux prompts
- Domain scoring
- Analyse détaillée à chaque étape
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add src_v2 to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src_v2"))

def run_full_e2e_test_v16():
    """Test E2E complet avec données fraîches"""
    from vectora_core.shared import config_loader, s3_io
    from vectora_core.ingest import run_ingest_for_client
    from vectora_core.normalization import normalizer
    
    logger.info("="*80)
    logger.info("TEST E2E COMPLET V16 - DONNEES FRAICHES")
    logger.info("="*80)
    logger.info("Workflow: Ingest -> Normalize -> Score -> Analyze")
    logger.info("")
    
    # Configuration
    config_bucket = 'vectora-inbox-config-dev'
    data_bucket = 'vectora-inbox-data-dev'
    client_id = 'lai_weekly_v9'  # Client de référence
    bedrock_model = "anthropic.claude-3-sonnet-20240229-v1:0"
    bedrock_region = "us-east-1"
    
    env_vars = {
        'CONFIG_BUCKET': config_bucket,
        'DATA_BUCKET': data_bucket
    }
    
    start_time = datetime.now()
    results = {
        'test_date': start_time.isoformat(),
        'client_id': client_id,
        'version': 'V16',
        'stages': {}
    }
    
    try:
        # ========== ÉTAPE 1: INGESTION ==========
        logger.info("\n" + "="*80)
        logger.info("ETAPE 1/3: INGESTION (Données fraîches)")
        logger.info("="*80)
        
        ingest_result = run_ingest_for_client(
            client_id=client_id,
            period_days=7,
            ingestion_mode='balanced',
            env_vars=env_vars
        )
        
        results['stages']['ingestion'] = {
            'status': ingest_result.get('status'),
            'items_ingested': ingest_result.get('items_final', 0),
            'sources_processed': ingest_result.get('sources_processed', 0),
            'execution_time': ingest_result.get('execution_time_seconds', 0)
        }
        
        logger.info(f"[OK] Ingestion terminee:")
        logger.info(f"   Items ingeres: {ingest_result.get('items_final', 0)}")
        logger.info(f"   Sources: {ingest_result.get('sources_processed', 0)}")
        logger.info(f"   Temps: {ingest_result.get('execution_time_seconds', 0):.1f}s")
        
        # Charger items ingérés
        s3_key = ingest_result.get('s3_output_path', '').replace(f's3://{data_bucket}/', '')
        ingested_items = s3_io.read_json_from_s3(data_bucket, s3_key)
        
        if not ingested_items:
            logger.error("[ERROR] Aucun item ingere")
            return False
        
        logger.info(f"\n[DETAIL] Items ingeres par source:")
        sources_count = {}
        for item in ingested_items:
            source = item.get('source_key', 'unknown')
            sources_count[source] = sources_count.get(source, 0) + 1
        
        for source, count in sorted(sources_count.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"   {source}: {count} items")
        
        # ========== ÉTAPE 2: NORMALISATION + SCORING ==========
        logger.info("\n" + "="*80)
        logger.info("ETAPE 2/3: NORMALISATION + DOMAIN SCORING")
        logger.info("="*80)
        logger.info(f"Items a normaliser: {len(ingested_items)}")
        logger.info("Appels Bedrock: 2 par item (normalization + domain_scoring)")
        logger.info("")
        
        # Charger configs
        client_config = config_loader.load_client_config(client_id, config_bucket)
        canonical_scopes = config_loader.load_canonical_scopes(config_bucket)
        canonical_prompts = config_loader.load_canonical_prompts(config_bucket)
        
        # Normaliser avec domain scoring
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
        
        results['stages']['normalization'] = {
            'items_normalized': len(normalized_items),
            'items_with_domain_scoring': sum(1 for i in normalized_items if i.get('has_domain_scoring'))
        }
        
        logger.info(f"[OK] Normalisation terminee:")
        logger.info(f"   Items normalises: {len(normalized_items)}")
        logger.info(f"   Items avec domain_scoring: {results['stages']['normalization']['items_with_domain_scoring']}")
        
        # ========== ÉTAPE 3: ANALYSE DÉTAILLÉE ==========
        logger.info("\n" + "="*80)
        logger.info("ETAPE 3/3: ANALYSE DETAILLEE ITEM PAR ITEM")
        logger.info("="*80)
        
        analysis = analyze_items_detailed(normalized_items)
        results['analysis'] = analysis
        
        # Afficher résumé
        print_analysis_summary(analysis)
        
        # Afficher top items
        print_top_items(normalized_items, analysis)
        
        # Sauvegarder résultats complets
        output_dir = project_root / ".tmp" / "e2e_v16_full"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarder items normalisés
        with open(output_dir / "normalized_items.json", 'w', encoding='utf-8') as f:
            json.dump(normalized_items, f, indent=2, ensure_ascii=False)
        
        # Sauvegarder résultats
        results['duration_seconds'] = (datetime.now() - start_time).total_seconds()
        with open(output_dir / "test_results.json", 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Générer rapport markdown
        generate_markdown_report(results, normalized_items, analysis, output_dir)
        
        logger.info(f"\n[OK] Resultats sauvegardes dans: {output_dir}")
        logger.info(f"   - normalized_items.json")
        logger.info(f"   - test_results.json")
        logger.info(f"   - detailed_report.md")
        
        # Verdict final
        logger.info("\n" + "="*80)
        logger.info("VERDICT FINAL")
        logger.info("="*80)
        
        relevant_rate = analysis['relevant_rate']
        target_rate = 54.0
        
        if relevant_rate >= target_rate:
            logger.info(f"[OK] Taux de pertinence: {relevant_rate:.1f}% >= {target_rate}%")
            logger.info("[OK] QUALITE AMELIOREE - PRET POUR PHASE 2")
            return True
        else:
            logger.warning(f"[WARN] Taux de pertinence: {relevant_rate:.1f}% < {target_rate}%")
            logger.warning("[WARN] QUALITE INSUFFISANTE - CORRIGER AVANT PHASE 2")
            return False
        
    except Exception as e:
        logger.error(f"[ERROR] Test echoue: {e}", exc_info=True)
        return False

def analyze_items_detailed(items: List[Dict]) -> Dict[str, Any]:
    """Analyse détaillée des items normalisés"""
    analysis = {
        'total_items': len(items),
        'items_relevant': 0,
        'items_not_relevant': 0,
        'items_no_scoring': 0,
        'relevant_rate': 0.0,
        'avg_score': 0.0,
        'companies_detected': 0,
        'technologies_detected': 0,
        'dosing_intervals_detected': 0,
        'confidence_distribution': {'high': 0, 'medium': 0, 'low': 0},
        'event_types': {},
        'sources': {},
        'items_by_score': {
            '80-100': 0,
            '60-79': 0,
            '40-59': 0,
            '20-39': 0,
            '0-19': 0
        }
    }
    
    total_score = 0
    
    for item in items:
        source = item.get('source_key', 'unknown')
        analysis['sources'][source] = analysis['sources'].get(source, 0) + 1
        
        # Domain scoring
        if not item.get('has_domain_scoring'):
            analysis['items_no_scoring'] += 1
            continue
        
        ds = item.get('domain_scoring', {})
        is_relevant = ds.get('is_relevant', False)
        score = ds.get('score', 0)
        confidence = ds.get('confidence', 'low')
        
        if is_relevant:
            analysis['items_relevant'] += 1
        else:
            analysis['items_not_relevant'] += 1
        
        total_score += score
        analysis['confidence_distribution'][confidence] += 1
        
        # Score buckets
        if score >= 80:
            analysis['items_by_score']['80-100'] += 1
        elif score >= 60:
            analysis['items_by_score']['60-79'] += 1
        elif score >= 40:
            analysis['items_by_score']['40-59'] += 1
        elif score >= 20:
            analysis['items_by_score']['20-39'] += 1
        else:
            analysis['items_by_score']['0-19'] += 1
        
        # Event types
        event_type = item.get('normalized_content', {}).get('event_classification', {}).get('primary_type', 'unknown')
        analysis['event_types'][event_type] = analysis['event_types'].get(event_type, 0) + 1
        
        # Entities
        entities = item.get('normalized_content', {}).get('entities', {})
        if entities.get('companies'):
            analysis['companies_detected'] += 1
        if entities.get('technologies'):
            analysis['technologies_detected'] += 1
        if entities.get('dosing_intervals'):
            analysis['dosing_intervals_detected'] += 1
    
    # Calculs
    items_with_scoring = analysis['total_items'] - analysis['items_no_scoring']
    if items_with_scoring > 0:
        analysis['relevant_rate'] = (analysis['items_relevant'] / items_with_scoring) * 100
        analysis['avg_score'] = total_score / items_with_scoring
    
    return analysis

def print_analysis_summary(analysis: Dict):
    """Affiche le résumé de l'analyse"""
    logger.info("\n[RESUME] Analyse globale:")
    logger.info(f"   Total items: {analysis['total_items']}")
    logger.info(f"   Items relevant: {analysis['items_relevant']} ({analysis['relevant_rate']:.1f}%)")
    logger.info(f"   Items non relevant: {analysis['items_not_relevant']}")
    logger.info(f"   Score moyen: {analysis['avg_score']:.1f}/100")
    logger.info(f"   Companies detectees: {analysis['companies_detected']} items")
    logger.info(f"   Technologies detectees: {analysis['technologies_detected']} items")
    logger.info(f"   Dosing intervals detectes: {analysis['dosing_intervals_detected']} items")
    
    logger.info(f"\n[DISTRIBUTION] Scores:")
    for bucket, count in sorted(analysis['items_by_score'].items(), reverse=True):
        pct = (count / analysis['total_items']) * 100 if analysis['total_items'] > 0 else 0
        logger.info(f"   {bucket}: {count} items ({pct:.1f}%)")
    
    logger.info(f"\n[DISTRIBUTION] Event types:")
    for event_type, count in sorted(analysis['event_types'].items(), key=lambda x: x[1], reverse=True):
        logger.info(f"   {event_type}: {count} items")

def print_top_items(items: List[Dict], analysis: Dict):
    """Affiche les top items relevant et non relevant"""
    # Trier par score
    items_sorted = sorted(
        [i for i in items if i.get('has_domain_scoring')],
        key=lambda x: x.get('domain_scoring', {}).get('score', 0),
        reverse=True
    )
    
    logger.info("\n" + "="*80)
    logger.info("TOP 5 ITEMS RELEVANT (Score le plus eleve)")
    logger.info("="*80)
    
    for i, item in enumerate(items_sorted[:5], 1):
        ds = item.get('domain_scoring', {})
        logger.info(f"\n[{i}] {item.get('title', '')[:70]}...")
        logger.info(f"   Source: {item.get('source_key')}")
        logger.info(f"   Score: {ds.get('score')}/100 (confidence: {ds.get('confidence')})")
        logger.info(f"   Event: {item.get('normalized_content', {}).get('event_classification', {}).get('primary_type')}")
        
        signals = ds.get('signals_detected', {})
        strong = len(signals.get('strong', []))
        medium = len(signals.get('medium', []))
        weak = len(signals.get('weak', []))
        logger.info(f"   Signals: {strong} strong, {medium} medium, {weak} weak")
        logger.info(f"   Reasoning: {ds.get('reasoning', '')[:100]}...")
    
    logger.info("\n" + "="*80)
    logger.info("TOP 5 ITEMS NON RELEVANT (Correctement rejetes)")
    logger.info("="*80)
    
    items_rejected = [i for i in items_sorted if not i.get('domain_scoring', {}).get('is_relevant')]
    for i, item in enumerate(items_rejected[:5], 1):
        ds = item.get('domain_scoring', {})
        logger.info(f"\n[{i}] {item.get('title', '')[:70]}...")
        logger.info(f"   Source: {item.get('source_key')}")
        logger.info(f"   Score: {ds.get('score')}/100")
        logger.info(f"   Reasoning: {ds.get('reasoning', '')[:100]}...")

def generate_markdown_report(results: Dict, items: List[Dict], analysis: Dict, output_dir: Path):
    """Génère un rapport markdown détaillé"""
    report = f"""# Test E2E Complet V16 - Rapport Détaillé

**Date**: {results['test_date']}  
**Client**: {results['client_id']}  
**Version**: {results['version']}  
**Durée**: {results['duration_seconds']:.1f}s

---

## Résumé Exécutif

**Taux de pertinence**: {analysis['relevant_rate']:.1f}%  
**Score moyen**: {analysis['avg_score']:.1f}/100  
**Items traités**: {analysis['total_items']}

### Comparaison V15 vs V16

| Métrique | V15 | V16 | Évolution |
|----------|-----|-----|-----------|
| Items ingérés | 29 | {results['stages']['ingestion']['items_ingested']} | {results['stages']['ingestion']['items_ingested'] - 29:+d} |
| Items relevant | 12 (41%) | {analysis['items_relevant']} ({analysis['relevant_rate']:.1f}%) | {analysis['relevant_rate'] - 41:.1f}% |
| Companies détectées | 0 | {analysis['companies_detected']} | +{analysis['companies_detected']} |
| Score moyen | 81.7 | {analysis['avg_score']:.1f} | {analysis['avg_score'] - 81.7:+.1f} |

---

## Étape 1: Ingestion

**Items ingérés**: {results['stages']['ingestion']['items_ingested']}  
**Sources traitées**: {results['stages']['ingestion']['sources_processed']}  
**Temps**: {results['stages']['ingestion']['execution_time']:.1f}s

### Répartition par source

"""
    
    for source, count in sorted(analysis['sources'].items(), key=lambda x: x[1], reverse=True):
        report += f"- {source}: {count} items\n"
    
    report += f"""
---

## Étape 2: Normalisation + Scoring

**Items normalisés**: {results['stages']['normalization']['items_normalized']}  
**Items avec domain_scoring**: {results['stages']['normalization']['items_with_domain_scoring']}

---

## Étape 3: Analyse Qualité

### Distribution des scores

"""
    
    for bucket, count in sorted(analysis['items_by_score'].items(), reverse=True):
        pct = (count / analysis['total_items']) * 100 if analysis['total_items'] > 0 else 0
        report += f"- {bucket}: {count} items ({pct:.1f}%)\n"
    
    report += f"""
### Event types

"""
    
    for event_type, count in sorted(analysis['event_types'].items(), key=lambda x: x[1], reverse=True):
        report += f"- {event_type}: {count} items\n"
    
    report += f"""
### Entités détectées

- Companies: {analysis['companies_detected']} items
- Technologies: {analysis['technologies_detected']} items
- Dosing intervals: {analysis['dosing_intervals_detected']} items

---

## Verdict

"""
    
    if analysis['relevant_rate'] >= 54.0:
        report += f"""✅ **QUALITÉ AMÉLIORÉE**

Taux de pertinence: {analysis['relevant_rate']:.1f}% >= 54% (objectif)

**Prêt pour Phase 2 (Deploy AWS)**
"""
    else:
        report += f"""⚠️ **QUALITÉ INSUFFISANTE**

Taux de pertinence: {analysis['relevant_rate']:.1f}% < 54% (objectif)

**Corriger avant Phase 2**
"""
    
    # Sauvegarder
    with open(output_dir / "detailed_report.md", 'w', encoding='utf-8') as f:
        f.write(report)

if __name__ == "__main__":
    logger.info("Demarrage test E2E complet V16 avec donnees fraiches")
    logger.info("ATTENTION: Vrais appels Bedrock (cout ~$0.10-0.20)")
    logger.info("")
    
    success = run_full_e2e_test_v16()
    
    sys.exit(0 if success else 1)
