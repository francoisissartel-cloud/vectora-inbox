#!/usr/bin/env python3
"""
Script de test local pour valider la détection de l'article Pfizer
avec la configuration lai_weekly_v3.1_debug (période étendue).

Usage: python test_lai_v3_1_debug_local.py
"""

import json
import boto3
from datetime import datetime, timedelta
import os
from pathlib import Path

def test_lai_v3_1_debug():
    """Test local de la configuration v3.1_debug avec période étendue"""
    
    print("=" * 80)
    print("TEST LAI WEEKLY v3.1 DEBUG - PÉRIODE ÉTENDUE")
    print("=" * 80)
    print()
    
    # Configuration
    client_id = "lai_weekly_v3.1_debug"
    lambda_name = "vectora-inbox-ingest-v2-dev"  # Adapter selon votre environnement
    region = "eu-west-3"
    
    print(f"🎯 OBJECTIF: Tester si l'article Pfizer du 9 mars 2026 sera détecté")
    print(f"📅 PÉRIODE: 60 jours (au lieu de 7)")
    print(f"🔍 MOTS-CLÉS ATTENDUS: 'once-monthly', 'subcutaneous'")
    print(f"📋 CLIENT: {client_id}")
    print()
    
    # Payload pour l'invocation
    payload = {\n        \"client_id\": client_id,\n        \"mode\": \"test\",\n        \"environment\": \"dev\",\n        \"force_refresh\": True,\n        \"debug\": True,\n        \"notes\": f\"Test période étendue - Article Pfizer 9 mars - {datetime.now().isoformat()}\"\n    }\n    \n    print(\"📤 PAYLOAD:\")\n    print(json.dumps(payload, indent=2))\n    print()\n    \n    # Vérification de la configuration\n    config_path = Path(\"config/clients/lai_weekly_v3.1_debug.yaml\")\n    if not config_path.exists():\n        print(f\"❌ ERREUR: Configuration non trouvée: {config_path}\")\n        return False\n    \n    print(f\"✅ Configuration trouvée: {config_path}\")\n    print()\n    \n    # Test d'invocation (commenté pour test local)\n    print(\"🚀 INVOCATION LAMBDA...\")\n    \n    try:\n        # Client Lambda\n        lambda_client = boto3.client('lambda', region_name=region)\n        \n        # Invocation\n        print(f\"   Invocation de {lambda_name}...\")\n        response = lambda_client.invoke(\n            FunctionName=lambda_name,\n            InvocationType='RequestResponse',\n            Payload=json.dumps(payload)\n        )\n        \n        # Lecture de la réponse\n        response_payload = json.loads(response['Payload'].read())\n        \n        print(f\"✅ Invocation réussie! Status: {response['StatusCode']}\")\n        print()\n        \n        # Analyse de la réponse\n        print(\"📊 ANALYSE DE LA RÉPONSE:\")\n        print(\"-\" * 40)\n        \n        if 'run_id' in response_payload:\n            run_id = response_payload['run_id']\n            print(f\"🆔 Run ID: {run_id}\")\n            \n            # Sauvegarde de la réponse\n            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')\n            output_file = f\"output/lai_v3.1_debug_test_{timestamp}.json\"\n            \n            os.makedirs(\"output\", exist_ok=True)\n            with open(output_file, 'w', encoding='utf-8') as f:\n                json.dump(response_payload, f, indent=2, ensure_ascii=False)\n            \n            print(f\"💾 Réponse sauvegardée: {output_file}\")\n            \n            # Instructions pour vérifier les résultats\n            print()\n            print(\"🔍 VÉRIFICATION DES RÉSULTATS:\")\n            print(\"-\" * 40)\n            print(f\"1. Vérifier le dossier: output/runs/{run_id}/\")\n            print(f\"2. Chercher l'article Pfizer dans ingested_items.json\")\n            print(f\"3. Hash cible: sha256:41a2561b3026a6287d28406eb89460ed5a184666b060602b0f3745891a2ff33c\")\n            print(f\"4. Vérifier que lai_keyword_filter.passed = true\")\n            print(f\"5. Vérifier que lai_keyword_filter.keywords_found contient 'once-monthly'\")\n            \n        else:\n            print(\"❌ Pas de run_id dans la réponse\")\n            print(\"Réponse complète:\")\n            print(json.dumps(response_payload, indent=2, ensure_ascii=False))\n        \n        return True\n        \n    except Exception as e:\n        print(f\"❌ ERREUR lors de l'invocation: {str(e)}\")\n        print()\n        print(\"💡 ALTERNATIVES:\")\n        print(\"1. Vérifier les credentials AWS\")\n        print(\"2. Vérifier le nom de la lambda\")\n        print(\"3. Vérifier la région\")\n        print(\"4. Tester en mode local si disponible\")\n        return False\n\ndef analyze_previous_run():\n    \"\"\"Analyse le run précédent pour comparaison\"\"\"\n    \n    print(\"\\n\" + \"=\" * 80)\n    print(\"ANALYSE DU RUN PRÉCÉDENT (période 7 jours)\")\n    print(\"=\" * 80)\n    \n    previous_run_path = Path(\"output/runs/lai_weekly__20260420_184149_2bcc04d5\")\n    \n    if not previous_run_path.exists():\n        print(\"❌ Run précédent non trouvé\")\n        return\n    \n    # Analyse des items rejetés\n    rejected_file = previous_run_path / \"rejected_items.json\"\n    if rejected_file.exists():\n        with open(rejected_file, 'r', encoding='utf-8') as f:\n            rejected_items = json.load(f)\n        \n        target_hash = \"sha256:41a2561b3026a6287d28406eb89460ed5a184666b060602b0f3745891a2ff33c\"\n        \n        pfizer_article = None\n        for item in rejected_items:\n            if item.get('content_hash') == target_hash:\n                pfizer_article = item\n                break\n        \n        if pfizer_article:\n            print(\"✅ Article Pfizer trouvé dans les rejets (période 7 jours)\")\n            print(f\"   Titre: {pfizer_article['title']}\")\n            print(f\"   Date: {pfizer_article['published_at']}\")\n            \n            filter_analysis = pfizer_article.get('filter_analysis', {})\n            period_filter = filter_analysis.get('period_filter', {})\n            lai_filter = filter_analysis.get('lai_keyword_filter', {})\n            \n            print(f\"   Filtre période: {period_filter.get('passed', 'N/A')} (raison: {period_filter.get('reason', 'N/A')})\")\n            print(f\"   Filtre LAI: {lai_filter.get('passed', 'N/A')} (mots-clés: {lai_filter.get('keywords_found', [])})\")\n            print(f\"   Jours d'âge: {period_filter.get('days_ago', 'N/A')}\")\n        else:\n            print(\"❌ Article Pfizer non trouvé dans les rejets\")\n    else:\n        print(\"❌ Fichier rejected_items.json non trouvé\")\n\nif __name__ == \"__main__\":\n    # Analyse du run précédent\n    analyze_previous_run()\n    \n    # Test avec la nouvelle configuration\n    success = test_lai_v3_1_debug()\n    \n    if success:\n        print(\"\\n🎉 Test lancé avec succès!\")\n        print(\"\\n📋 PROCHAINES ÉTAPES:\")\n        print(\"1. Attendre la fin du run\")\n        print(\"2. Comparer les résultats avec le run précédent\")\n        print(\"3. Vérifier si l'article Pfizer est maintenant ingéré\")\n    else:\n        print(\"\\n❌ Échec du test\")