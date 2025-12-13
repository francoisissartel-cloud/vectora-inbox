#!/usr/bin/env python3
"""
Script de test local simplifie pour la generation de newsletter.
"""

import json
import os
import sys
from datetime import datetime, timedelta

# Ajouter le chemin vers vectora_core
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from vectora_core.newsletter import assembler


def create_mock_scored_items():
    """Cree des items simules avec scores pour tester la newsletter."""
    
    mock_items = [
        {
            "title": "Nanexa and Moderna Announce PharmaShell Technology Partnership",
            "summary": "Nanexa AB announces strategic partnership with Moderna to develop PharmaShell technology for extended-release injectable formulations.",
            "url": "https://nanexa.com/press-release-moderna-partnership",
            "date": "2025-12-10",
            "source_key": "press_corporate__nanexa",
            "matched_domains": ["lai_technology", "partnerships"],
            "score": 0.95,
            "event_type": "partnership"
        },
        {
            "title": "UZEDY (aripiprazole) Extended-Release Injectable Shows Positive Phase 3 Results",
            "summary": "Teva Pharmaceutical announces positive Phase 3 clinical trial results for UZEDY, a novel extended-release injectable formulation.",
            "url": "https://tevapharm.com/uzedy-phase3-results",
            "date": "2025-12-09",
            "source_key": "press_sector__fiercepharma",
            "matched_domains": ["lai_technology", "clinical_trials"],
            "score": 0.92,
            "event_type": "clinical_results"
        },
        {
            "title": "MedinCell Receives 2.5M Grant for Malaria Prevention LAI Development",
            "summary": "MedinCell secures 2.5 million grant to advance development of long-acting injectable malaria prevention treatment using BEPO technology.",
            "url": "https://medincell.com/malaria-grant-announcement",
            "date": "2025-12-08",
            "source_key": "press_corporate__medincell",
            "matched_domains": ["lai_technology", "funding"],
            "score": 0.88,
            "event_type": "funding"
        }
    ]
    
    return mock_items


def create_mock_client_config():
    """Cree une configuration client simulee."""
    
    return {
        "client_profile": {
            "name": "LAI Weekly Intelligence",
            "language": "en",
            "tone": "executive",
            "voice": "concise"
        },
        "newsletter_layout": {
            "sections": [
                {
                    "id": "lai_technology",
                    "title": "LAI Technology & Innovation",
                    "source_domains": ["lai_technology", "partnerships", "clinical_trials"],
                    "max_items": 3,
                    "filter_event_types": ["partnership", "clinical_results", "technology"]
                },
                {
                    "id": "funding_deals",
                    "title": "Funding & Business Development",
                    "source_domains": ["funding", "partnerships"],
                    "max_items": 2,
                    "filter_event_types": ["funding", "partnership", "acquisition"]
                }
            ]
        },
        "newsletter_delivery": {
            "include_tldr": True
        }
    }


def test_newsletter_generation():
    """Test principal de generation de newsletter."""
    
    print("Test Newsletter Generation - Phase 1 Validation")
    print("=" * 60)
    
    # Configuration
    mock_items = create_mock_scored_items()
    client_config = create_mock_client_config()
    
    # Parametres de test
    bedrock_model_id = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
    target_date = "2025-12-12"
    from_date = "2025-12-05"
    to_date = "2025-12-12"
    
    print(f"Items de test : {len(mock_items)}")
    print(f"Periode : {from_date} a {to_date}")
    print(f"Modele Bedrock : {bedrock_model_id}")
    print()
    
    # Verifier les variables d'environnement
    bedrock_region = os.environ.get('BEDROCK_REGION', 'us-east-1')
    print(f"Region Bedrock : {bedrock_region}")
    
    if not os.environ.get('AWS_PROFILE'):
        print("AWS_PROFILE non defini - utilisation du profil par defaut")
    else:
        print(f"Profil AWS : {os.environ.get('AWS_PROFILE')}")
    
    print()
    
    try:
        # Test de generation
        print("Generation de la newsletter...")
        start_time = datetime.now()
        
        newsletter_md, stats, editorial_content = assembler.generate_newsletter(
            mock_items,
            client_config,
            bedrock_model_id,
            target_date,
            from_date,
            to_date
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"Newsletter generee en {duration:.2f}s")
        print()
        
        # Analyser les resultats
        print("Statistiques :")
        print(f"  - Items selectionnes : {stats.get('items_selected', 0)}")
        print(f"  - Sections generees : {stats.get('sections_generated', 0)}")
        print(f"  - Taille newsletter : {len(newsletter_md)} caracteres")
        print()
        
        # Verifier si c'est un fallback
        is_fallback = "mode degrade" in newsletter_md or "fallback mode" in newsletter_md
        
        if is_fallback:
            print("FALLBACK DETECTE - Newsletter generee en mode degrade")
            print("   Cause probable : Erreur Bedrock ou parsing JSON")
        else:
            print("Newsletter generee par Bedrock (pas de fallback)")
        
        print()
        
        # Analyser le contenu editorial
        if editorial_content:
            print("Contenu editorial :")
            print(f"  - Titre : {editorial_content.get('title', 'N/A')}")
            print(f"  - Intro : {len(editorial_content.get('intro', ''))} caracteres")
            print(f"  - TL;DR : {len(editorial_content.get('tldr', []))} points")
            print(f"  - Sections : {len(editorial_content.get('sections', []))}")
            
            # Verifier les items gold
            sections = editorial_content.get('sections', [])
            gold_items_found = []
            
            for section in sections:
                for item in section.get('items', []):
                    title = item.get('title', '')
                    if 'PharmaShell' in title or 'Nanexa' in title:
                        gold_items_found.append('Nanexa/Moderna PharmaShell')
                    elif 'UZEDY' in title:
                        gold_items_found.append('UZEDY Extended-Release Injectable')
                    elif 'MedinCell' in title and 'malaria' in title.lower():
                        gold_items_found.append('MedinCell malaria grant')
            
            if gold_items_found:
                print(f"  - Items gold detectes : {', '.join(gold_items_found)}")
            else:
                print("  - Aucun item gold detecte dans la newsletter")
        
        print()
        
        # Sauvegarder les resultats
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Newsletter markdown
        newsletter_file = f"newsletter_test_phase1_{timestamp}.md"
        with open(newsletter_file, 'w', encoding='utf-8') as f:
            f.write(newsletter_md)
        print(f"Newsletter sauvegardee : {newsletter_file}")
        
        # Contenu editorial JSON
        if editorial_content:
            editorial_file = f"newsletter_editorial_phase1_{timestamp}.json"
            with open(editorial_file, 'w', encoding='utf-8') as f:
                json.dump(editorial_content, f, indent=2, ensure_ascii=False)
            print(f"Contenu editorial sauvegarde : {editorial_file}")
        
        print()
        print("Resume du test :")
        
        if is_fallback:
            print("ECHEC - Newsletter en mode fallback")
            print("   -> Verifier la connectivite Bedrock et les quotas")
        elif stats.get('items_selected', 0) == 0:
            print("PARTIEL - Aucun item selectionne")
            print("   -> Verifier la logique de selection des sections")
        elif not editorial_content:
            print("PARTIEL - Pas de contenu editorial")
            print("   -> Verifier le parsing JSON de la reponse Bedrock")
        else:
            print("SUCCES - Newsletter generee avec contenu editorial")
            print("   -> Corrections Phase 1 validees localement")
        
        return not is_fallback and stats.get('items_selected', 0) > 0
        
    except Exception as e:
        print(f"ERREUR lors de la generation : {e}")
        print(f"   Type : {type(e).__name__}")
        
        # Log detaille pour debug
        import traceback
        print("\nStack trace complete :")
        traceback.print_exc()
        
        return False


if __name__ == "__main__":
    # Configuration des variables d'environnement pour le test
    os.environ.setdefault('BEDROCK_REGION', 'us-east-1')
    os.environ.setdefault('AWS_PROFILE', 'rag-lai-prod')
    
    success = test_newsletter_generation()
    
    print("\n" + "=" * 60)
    if success:
        print("Test Phase 1 Newsletter : REUSSI")
        exit(0)
    else:
        print("Test Phase 1 Newsletter : ECHEC")
        exit(1)