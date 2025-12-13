#!/usr/bin/env python3
"""
Script de test pour le système LLM Domain Gating.

Ce script teste le nouveau système d'évaluation de domaines par Bedrock
en lançant un run complet pour lai_weekly_v2.
"""

import json
import logging
import sys
import os
from datetime import datetime, timedelta

# Ajouter le répertoire src au path pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from vectora_core import run_ingest_normalize_for_client, run_engine_for_client

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_llm_domain_gating():
    """Test complet du système LLM Domain Gating avec lai_weekly_v2."""
    
    # Configuration de test
    client_id = "lai_weekly_v2"
    period_days = 7  # 1 semaine
    
    # Variables d'environnement simulées (à adapter selon votre environnement)
    env_vars = {
        "ENV": "dev",
        "PROJECT_NAME": "vectora-inbox",
        "CONFIG_BUCKET": "vectora-inbox-config-dev",
        "DATA_BUCKET": "vectora-inbox-data-dev", 
        "NEWSLETTERS_BUCKET": "vectora-inbox-newsletters-dev",
        "BEDROCK_MODEL_ID": "anthropic.claude-3-sonnet-20240229-v1:0",
        "LOG_LEVEL": "INFO"
    }
    
    logger.info("=== Test LLM Domain Gating - Démarrage ===")
    logger.info(f"Client: {client_id}")
    logger.info(f"Période: {period_days} jours")
    
    try:
        # Phase 1: Ingestion + Normalisation avec évaluation de domaines
        logger.info("\n--- Phase 1: Ingestion + Normalisation ---")
        
        ingest_result = run_ingest_normalize_for_client(
            client_id=client_id,
            period_days=period_days,
            env_vars=env_vars
        )
        
        logger.info("Résultats de l'ingestion:")
        logger.info(f"  - Sources traitées: {ingest_result.get('sources_processed', 0)}")
        logger.info(f"  - Items ingérés: {ingest_result.get('items_ingested', 0)}")
        logger.info(f"  - Items filtrés: {ingest_result.get('items_filtered', 0)}")
        logger.info(f"  - Items normalisés: {ingest_result.get('items_normalized', 0)}")
        logger.info(f"  - Temps d'exécution: {ingest_result.get('execution_time_seconds', 0)}s")
        
        if ingest_result.get('items_normalized', 0) == 0:
            logger.warning("Aucun item normalisé - arrêt du test")
            return
        
        # Phase 2: Engine (Matching + Scoring + Newsletter)
        logger.info("\n--- Phase 2: Engine (Matching + Scoring + Newsletter) ---")
        
        engine_result = run_engine_for_client(
            client_id=client_id,
            period_days=period_days,
            env_vars=env_vars
        )
        
        logger.info("Résultats du moteur:")
        logger.info(f"  - Items analysés: {engine_result.get('items_analyzed', 0)}")
        logger.info(f"  - Items matchés: {engine_result.get('items_matched', 0)}")
        logger.info(f"  - Items sélectionnés: {engine_result.get('items_selected', 0)}")
        logger.info(f"  - Sections générées: {engine_result.get('sections_generated', 0)}")
        logger.info(f"  - Newsletter S3: {engine_result.get('s3_output_path', 'N/A')}")
        logger.info(f"  - Temps d'exécution: {engine_result.get('execution_time_seconds', 0)}s")
        
        # Analyse des résultats
        logger.info("\n--- Analyse des Résultats ---")
        
        items_normalized = ingest_result.get('items_normalized', 0)
        items_matched = engine_result.get('items_matched', 0)
        items_selected = engine_result.get('items_selected', 0)
        
        if items_normalized > 0:
            match_rate = (items_matched / items_normalized) * 100
            selection_rate = (items_selected / items_normalized) * 100
            
            logger.info(f"  - Taux de matching: {match_rate:.1f}% ({items_matched}/{items_normalized})")
            logger.info(f"  - Taux de sélection: {selection_rate:.1f}% ({items_selected}/{items_normalized})")
            
            if match_rate > 0:
                logger.info("✅ Le système détecte des items pertinents")
            else:
                logger.warning("⚠️  Aucun item matché - vérifier la configuration des domaines")
                
            if selection_rate > 0:
                logger.info("✅ Des items sont sélectionnés pour la newsletter")
            else:
                logger.warning("⚠️  Aucun item sélectionné - vérifier les seuils de scoring")
        
        # Recommandations
        logger.info("\n--- Recommandations ---")
        
        if match_rate < 10:
            logger.info("📋 Recommandation: Ajuster les contextes de domaines ou les seuils de pertinence")
        elif match_rate > 80:
            logger.info("📋 Recommandation: Les domaines sont peut-être trop larges, considérer un affinement")
        else:
            logger.info("📋 Le taux de matching semble équilibré")
            
        if selection_rate < 5:
            logger.info("📋 Recommandation: Réduire les seuils de scoring ou ajuster les multiplicateurs")
        elif selection_rate > 50:
            logger.info("📋 Recommandation: Augmenter les seuils pour plus de sélectivité")
        else:
            logger.info("📋 Le taux de sélection semble approprié")
        
        logger.info("\n=== Test LLM Domain Gating - Terminé avec succès ===")
        
        # Retourner un résumé
        return {
            "success": True,
            "ingest_result": ingest_result,
            "engine_result": engine_result,
            "analysis": {
                "match_rate_percent": match_rate,
                "selection_rate_percent": selection_rate,
                "items_normalized": items_normalized,
                "items_matched": items_matched,
                "items_selected": items_selected
            }
        }
        
    except Exception as e:
        logger.error(f"Erreur lors du test: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }

def analyze_domain_relevance_scores(data_bucket: str, client_id: str):
    """
    Analyse les scores domain_relevance dans les items normalisés.
    
    Args:
        data_bucket: Bucket S3 des données
        client_id: ID du client
    """
    logger.info("\n--- Analyse des Scores Domain Relevance ---")
    
    try:
        from vectora_core.storage import s3_client
        from datetime import datetime, timedelta
        
        # Chercher les items des derniers jours
        today = datetime.now()
        for i in range(7):  # 7 derniers jours
            date = today - timedelta(days=i)
            year, month, day = date.strftime('%Y'), date.strftime('%m'), date.strftime('%d')
            
            key = f"normalized/{client_id}/{year}/{month}/{day}/items.json"
            
            try:
                items = s3_client.read_json_from_s3(data_bucket, key)
                if not items:
                    continue
                    
                logger.info(f"Analyse de {len(items)} items du {date.strftime('%Y-%m-%d')}")
                
                # Analyser les domain_relevance
                items_with_relevance = 0
                total_evaluations = 0
                on_domain_count = 0
                relevance_scores = []
                
                for item in items:
                    domain_relevance = item.get('domain_relevance', [])
                    if domain_relevance:
                        items_with_relevance += 1
                        total_evaluations += len(domain_relevance)
                        
                        for eval_data in domain_relevance:
                            if eval_data.get('is_on_domain'):
                                on_domain_count += 1
                                score = eval_data.get('relevance_score', 0)
                                relevance_scores.append(score)
                                
                                logger.info(f"  ✅ {eval_data.get('domain_id')}: {score:.2f} - {eval_data.get('reason', '')[:100]}")
                
                if items_with_relevance > 0:
                    logger.info(f"  📊 Items avec évaluation: {items_with_relevance}/{len(items)}")
                    logger.info(f"  📊 Évaluations 'on_domain': {on_domain_count}/{total_evaluations}")
                    
                    if relevance_scores:
                        avg_score = sum(relevance_scores) / len(relevance_scores)
                        max_score = max(relevance_scores)
                        min_score = min(relevance_scores)
                        logger.info(f"  📊 Scores de pertinence: moy={avg_score:.2f}, max={max_score:.2f}, min={min_score:.2f}")
                
                break  # Analyser seulement le premier jour trouvé
                
            except Exception as e:
                logger.debug(f"Pas de données pour {key}: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse: {e}")

if __name__ == "__main__":
    # Lancer le test
    result = test_llm_domain_gating()
    
    if result and result.get("success"):
        # Analyser les scores si le test a réussi
        env_vars = {
            "DATA_BUCKET": "vectora-inbox-data-dev"
        }
        analyze_domain_relevance_scores(env_vars["DATA_BUCKET"], "lai_weekly_v2")
        
        # Sauvegarder les résultats
        with open("test_llm_domain_gating_results.json", "w") as f:
            json.dump(result, f, indent=2)
        
        print("\n✅ Test terminé avec succès - Résultats sauvegardés dans test_llm_domain_gating_results.json")
    else:
        print("\n❌ Test échoué")
        sys.exit(1)