"""
Module newsletter - Point d'entrée principal
Orchestration de la génération de newsletter
"""
import logging
from datetime import datetime, timedelta
from ..shared import config_loader, s3_io, utils
from . import selector, assembler, bedrock_editor

logger = logging.getLogger(__name__)

def run_newsletter_for_client(client_id, env_vars, target_date=None, force_regenerate=False):
    """
    Génère une newsletter pour un client donné
    
    Args:
        client_id: Identifiant du client
        env_vars: Variables d'environnement (buckets, Bedrock config)
        target_date: Date cible (défaut: aujourd'hui)
        force_regenerate: Force la régénération même si existe
    
    Returns:
        dict: Résultat de la génération avec métriques
    """
    logger.info(f"Starting newsletter generation for client: {client_id}")
    
    try:
        # 1. Chargement configuration client
        client_config = config_loader.load_client_config(
            client_id, env_vars["CONFIG_BUCKET"]
        )
        
        # 2. Détermination période et mode de lecture
        if not target_date:
            target_date = datetime.now().strftime("%Y-%m-%d")
        
        # Nouveau : support du mode latest_run_only
        newsletter_mode = client_config.get('pipeline', {}).get('newsletter_mode', 'period_based')
        
        # 3. Chargement items curated selon le mode
        if newsletter_mode == 'latest_run_only':
            # Mode cohérent : un seul dossier (dernier run)
            curated_items = s3_io.load_curated_items_single_date(
                client_id, env_vars["DATA_BUCKET"], target_date
            )
            logger.info(f"Using latest_run_only mode for {target_date}")
        else:
            # Mode legacy : période glissante (rétrocompatibilité)
            period_days = client_config.get('pipeline', {}).get('default_period_days', 30)
            from_date = (datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=period_days)).strftime("%Y-%m-%d")
            curated_items = s3_io.load_curated_items(
                client_id, env_vars["DATA_BUCKET"], from_date, target_date
            )
            logger.info(f"Using period_based mode from {from_date} to {target_date}")
        
        if not curated_items:
            logger.warning(f"No curated items found for {client_id} on {target_date} (mode: {newsletter_mode})")
            return {
                "client_id": client_id,
                "status": "no_items",
                "items_processed": 0,
                "newsletter_generated": False,
                "newsletter_mode": newsletter_mode
            }
        
        # 4. Sélection et déduplication des items
        selection_result = selector.NewsletterSelector(client_config).select_items(curated_items)
        selected_items = selection_result['sections']
        selection_metadata = selection_result['metadata']
        
        # 5. Chargement canonical scopes pour Approche B
        canonical_scopes = config_loader.load_canonical_scopes(env_vars["CONFIG_BUCKET"])
        
        # 6. Calcul des dates de période pour newsletter
        from datetime import datetime, timedelta
        target_dt = datetime.strptime(target_date, "%Y-%m-%d")
        week_end_dt = target_dt
        week_start_dt = target_dt - timedelta(days=6)
        week_start = week_start_dt.strftime("%b %d, %Y")
        week_end = week_end_dt.strftime("%b %d, %Y")
        
        # 7. Génération contenu éditorial via Bedrock (Approche B)
        editorial_content = bedrock_editor.generate_editorial_content(
            selected_items, client_config, env_vars, s3_io, canonical_scopes, week_start, week_end
        )
        
        # 8. Assemblage newsletter finale
        newsletter_result = assembler.assemble_newsletter(
            selected_items, editorial_content, client_config, target_date
        )
        
        # 9. Sauvegarde S3
        s3_paths = s3_io.save_newsletter(
            newsletter_result, client_id, target_date, env_vars["NEWSLETTERS_BUCKET"]
        )
        
        logger.info(f"Newsletter generated successfully for {client_id}")
        
        return {
            "client_id": client_id,
            "status": "success",
            "target_date": target_date,
            "items_processed": len(curated_items),
            "items_selected": selection_metadata.get('items_selected', 0),
            "newsletter_generated": True,
            "s3_paths": s3_paths,
            "bedrock_calls": editorial_content.get("bedrock_calls", {}),
            "processing_time": utils.get_processing_time(),
            "selection_metadata": selection_metadata
        }
        
    except Exception as e:
        logger.error(f"Newsletter generation failed for {client_id}: {str(e)}")
        raise