#!/usr/bin/env python3
"""
Script de test local pour la génération de newsletter.

Ce script teste la génération de newsletter avec des données simulées
pour valider les corrections Phase 1 sans dépendre de la normalisation.
"""

import json
import os
import sys
from datetime import datetime, timedelta

# Ajouter le chemin vers vectora_core
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from vectora_core.newsletter import assembler


def create_mock_scored_items():
    """Crée des items simulés avec scores pour tester la newsletter."""
    
    # Items gold simulés basés sur les objectifs P0
    mock_items = [
        {
            "title": "Nanexa and Moderna Announce PharmaShell® Technology Partnership",
            "summary": "Nanexa AB announces strategic partnership with Moderna to develop PharmaShell® technology for extended-release injectable formulations. The collaboration focuses on mRNA vaccine delivery systems with sustained release profiles.",
            "url": "https://nanexa.com/press-release-moderna-partnership",
            "date": "2025-12-10",
            "source_key": "press_corporate__nanexa",
            "matched_domains": ["lai_technology", "partnerships"],
            "score": 0.95,
            "event_type": "partnership"
        },
        {
            "title": "UZEDY® (aripiprazole) Extended-Release Injectable Shows Positive Phase 3 Results",
            "summary": "Teva Pharmaceutical announces positive Phase 3 clinical trial results for UZEDY®, a novel extended-release injectable formulation of aripiprazole for schizophrenia treatment. The LAI formulation demonstrates improved patient compliance and reduced injection frequency.",
            "url": "https://tevapharm.com/uzedy-phase3-results",
            "date": "2025-12-09",
            "source_key": "press_sector__fiercepharma",
            "matched_domains": ["lai_technology", "clinical_trials"],
            "score": 0.92,
            "event_type": "clinical_results"
        },
        {
            "title": "MedinCell Receives €2.5M Grant for Malaria Prevention LAI Development",
            "summary": "MedinCell secures €2.5 million grant from Global Health Initiative to advance development of long-acting injectable malaria prevention treatment using BEPO® technology. The project targets underserved populations in endemic regions.",
            "url": "https://medincell.com/malaria-grant-announcement",
            "date": "2025-12-08",
            "source_key": "press_corporate__medincell",
            "matched_domains": ["lai_technology", "funding"],
            "score": 0.88,
            "event_type": "funding"
        },
        {
            "title": "DelSiTech Announces New Hiring Initiative for R&D Team",
            "summary": "DelSiTech Ltd announces expansion of R&D team with 15 new positions focused on silica-based drug delivery systems. The company seeks experienced scientists in pharmaceutical formulation and materials science.",
            "url": "https://delsitech.com/hiring-rd-expansion",
            "date": "2025-12-07",
            "source_key": "press_corporate__delsitech",
            "matched_domains": ["corporate_news"],
            "score": 0.25,  # Bruit HR - devrait être filtré
            "event_type": "hiring"
        },
        {
            "title": "MedinCell Reports Q4 Financial Results and Revenue Growth",
            "summary": "MedinCell announces Q4 2024 financial results showing 23% revenue growth driven by BEPO® technology licensing deals. The company reports strong cash position and increased R&D investments in LAI platforms.",
            "url": "https://medincell.com/q4-financial-results",
            "date": "2025-12-06",
            "source_key": "press_corporate__medincell",
            "matched_domains": ["corporate_news"],
            "score": 0.35,  # Bruit financier - devrait être filtré
            "event_type": "financial_results"
        }
    ]
    
    return mock_items


def create_mock_client_config():
    """Crée une configuration client simulée."""
    
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
    """Test principal de génération de newsletter."""
    
    print("🧪 Test Newsletter Generation - Phase 1 Validation")
    print("=" * 60)
    
    # Configuration
    mock_items = create_mock_scored_items()
    client_config = create_mock_client_config()
    
    # Paramètres de test
    bedrock_model_id = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
    target_date = "2025-12-12"
    from_date = "2025-12-05"
    to_date = "2025-12-12"
    
    print(f"📊 Items de test : {len(mock_items)}")
    print(f"📅 Période : {from_date} à {to_date}")
    print(f"🤖 Modèle Bedrock : {bedrock_model_id}")
    print()
    
    # Vérifier les variables d'environnement
    bedrock_region = os.environ.get('BEDROCK_REGION', 'us-east-1')
    print(f"🌍 Région Bedrock : {bedrock_region}")
    
    if not os.environ.get('AWS_PROFILE'):
        print("⚠️  AWS_PROFILE non défini - utilisation du profil par défaut")
    else:
        print(f"🔑 Profil AWS : {os.environ.get('AWS_PROFILE')}")
    
    print()
    
    try:
        # Test de génération
        print("🚀 Génération de la newsletter...")
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
        
        print(f"✅ Newsletter générée en {duration:.2f}s")
        print()
        
        # Analyser les résultats
        print("📊 Statistiques :")
        print(f"  - Items sélectionnés : {stats.get('items_selected', 0)}")
        print(f"  - Sections générées : {stats.get('sections_generated', 0)}")
        print(f"  - Taille newsletter : {len(newsletter_md)} caractères")
        print()
        
        # Vérifier si c'est un fallback
        is_fallback = "mode dégradé" in newsletter_md or "fallback mode" in newsletter_md
        
        if is_fallback:
            print("⚠️  FALLBACK DÉTECTÉ - Newsletter générée en mode dégradé")
            print("   Cause probable : Erreur Bedrock ou parsing JSON")
        else:
            print("✅ Newsletter générée par Bedrock (pas de fallback)")
        
        print()
        
        # Analyser le contenu éditorial
        if editorial_content:
            print("📝 Contenu éditorial :")
            print(f"  - Titre : {editorial_content.get('title', 'N/A')}")
            print(f"  - Intro : {len(editorial_content.get('intro', ''))} caractères")
            print(f"  - TL;DR : {len(editorial_content.get('tldr', []))} points")
            print(f"  - Sections : {len(editorial_content.get('sections', []))}")
            
            # Vérifier les items gold
            sections = editorial_content.get('sections', [])
            gold_items_found = []
            
            for section in sections:
                for item in section.get('items', []):
                    title = item.get('title', '')
                    if 'PharmaShell' in title or 'Nanexa' in title:
                        gold_items_found.append('Nanexa/Moderna PharmaShell®')
                    elif 'UZEDY' in title:
                        gold_items_found.append('UZEDY® Extended-Release Injectable')
                    elif 'MedinCell' in title and 'malaria' in title.lower():
                        gold_items_found.append('MedinCell malaria grant')
            
            if gold_items_found:
                print(f"  - Items gold détectés : {', '.join(gold_items_found)}")
            else:
                print("  - ⚠️  Aucun item gold détecté dans la newsletter")
        
        print()
        
        # Sauvegarder les résultats
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Newsletter markdown
        newsletter_file = f"newsletter_test_phase1_{timestamp}.md"
        with open(newsletter_file, 'w', encoding='utf-8') as f:
            f.write(newsletter_md)
        print(f"💾 Newsletter sauvegardée : {newsletter_file}")
        
        # Contenu éditorial JSON
        if editorial_content:
            editorial_file = f"newsletter_editorial_phase1_{timestamp}.json"
            with open(editorial_file, 'w', encoding='utf-8') as f:
                json.dump(editorial_content, f, indent=2, ensure_ascii=False)
            print(f"💾 Contenu éditorial sauvegardé : {editorial_file}")
        
        # Statistiques
        test_results = {
            "test_date": datetime.now().isoformat(),
            "duration_seconds": duration,
            "stats": stats,
            "is_fallback": is_fallback,
            "newsletter_size": len(newsletter_md),
            "editorial_content_available": bool(editorial_content),
            "gold_items_found": gold_items_found if 'gold_items_found' in locals() else [],
            "bedrock_model": bedrock_model_id,
            "bedrock_region": bedrock_region
        }
        
        results_file = f"newsletter_test_results_phase1_{timestamp}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, indent=2, ensure_ascii=False)
        print(f"💾 Résultats de test sauvegardés : {results_file}")
        
        print()
        print("🎯 Résumé du test :")
        
        if is_fallback:
            print("❌ ÉCHEC - Newsletter en mode fallback")
            print("   → Vérifier la connectivité Bedrock et les quotas")
        elif stats.get('items_selected', 0) == 0:
            print("⚠️  PARTIEL - Aucun item sélectionné")
            print("   → Vérifier la logique de sélection des sections")
        elif not editorial_content:
            print("⚠️  PARTIEL - Pas de contenu éditorial")
            print("   → Vérifier le parsing JSON de la réponse Bedrock")
        else:
            print("✅ SUCCÈS - Newsletter générée avec contenu éditorial")
            print("   → Corrections Phase 1 validées localement")
        
        return not is_fallback and stats.get('items_selected', 0) > 0
        
    except Exception as e:
        print(f"❌ ERREUR lors de la génération : {e}")
        print(f"   Type : {type(e).__name__}")
        
        # Log détaillé pour debug
        import traceback
        print("\n🔍 Stack trace complète :")
        traceback.print_exc()
        
        return False


if __name__ == "__main__":
    # Configuration des variables d'environnement pour le test
    os.environ.setdefault('BEDROCK_REGION', 'us-east-1')
    os.environ.setdefault('AWS_PROFILE', 'rag-lai-prod')
    
    success = test_newsletter_generation()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Test Phase 1 Newsletter : RÉUSSI")
        exit(0)
    else:
        print("💥 Test Phase 1 Newsletter : ÉCHEC")
        exit(1)