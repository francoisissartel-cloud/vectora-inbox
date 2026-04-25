#!/usr/bin/env python3
"""
Script de monitoring pour vérifier la conformité "Real Data Only".

Ce script vérifie que la Lambda normalize_score_v2 traite uniquement
des données réelles et alerte en cas de détection de données synthétiques.

Usage:
    python scripts/monitor_real_data_compliance.py
"""

import boto3
import json
import sys
from datetime import datetime, timedelta

# Configuration
LAMBDA_NAME = "vectora-inbox-normalize-score-v2-dev"
LOG_GROUP = "/aws/lambda/vectora-inbox-normalize-score-v2-dev"
REGION = "eu-west-3"
PROFILE = "rag-lai-prod"

# Seuils d'alerte
MIN_ITEMS_EXPECTED = 10  # Minimum d'items attendus pour lai_weekly_v3
SYNTHETIC_ITEMS_THRESHOLD = 0  # Tolérance zéro pour les items synthétiques


def get_recent_executions(hours=24):
    """Récupère les exécutions récentes de la Lambda."""
    session = boto3.Session(profile_name=PROFILE, region_name=REGION)
    logs_client = session.client('logs')
    
    # Timestamp de début (dernières X heures)
    start_time = int((datetime.now() - timedelta(hours=hours)).timestamp() * 1000)
    
    try:
        # Rechercher les logs de fin d'exécution
        response = logs_client.filter_log_events(
            logGroupName=LOG_GROUP,
            startTime=start_time,
            filterPattern='items_input'
        )
        
        executions = []
        for event in response.get('events', []):
            message = event['message']
            # Parser le JSON dans le message
            if 'items_input' in message:
                try:
                    # Extraire le dict JSON du message
                    start_idx = message.find('{')
                    if start_idx != -1:
                        json_str = message[start_idx:]
                        data = json.loads(json_str)
                        executions.append({
                            'timestamp': datetime.fromtimestamp(event['timestamp'] / 1000),
                            'data': data
                        })
                except json.JSONDecodeError:
                    continue
        
        return executions
    
    except Exception as e:
        print(f"Erreur lors de la récupération des logs: {e}")
        return []


def check_synthetic_data_indicators(execution):
    """Vérifie les indicateurs de données synthétiques."""
    data = execution['data']
    stats = data.get('statistics', {})
    
    alerts = []
    
    # Vérification 1: Nombre d'items suspect (exactement 5)
    items_input = stats.get('items_input', 0)
    if items_input == 5:
        alerts.append({
            'severity': 'WARNING',
            'message': f"Nombre d'items suspect: {items_input} (possible données synthétiques)"
        })
    
    # Vérification 2: Nombre d'items trop faible
    if items_input < MIN_ITEMS_EXPECTED:
        alerts.append({
            'severity': 'WARNING',
            'message': f"Nombre d'items inférieur au minimum attendu: {items_input} < {MIN_ITEMS_EXPECTED}"
        })
    
    # Vérification 3: Vérifier le chemin source
    source_path = data.get('last_run_path', '')
    if 'test' in source_path.lower() or 'synthetic' in source_path.lower():
        alerts.append({
            'severity': 'CRITICAL',
            'message': f"Chemin de données de test détecté: {source_path}"
        })
    
    return alerts


def generate_compliance_report(executions):
    """Génère un rapport de conformité."""
    print("=" * 70)
    print("RAPPORT DE CONFORMITE - Real Data Only")
    print("=" * 70)
    print(f"Periode analysee: Dernieres 24 heures")
    print(f"Nombre d'executions: {len(executions)}")
    print()
    
    if not executions:
        print("Aucune execution trouvee dans la periode")
        return True
    
    # Statistiques globales
    total_items = 0
    total_alerts = 0
    critical_alerts = 0
    
    for i, execution in enumerate(executions, 1):
        timestamp = execution['timestamp']
        data = execution['data']
        stats = data.get('statistics', {})
        
        items_input = stats.get('items_input', 0)
        total_items += items_input
        
        print(f"Execution #{i} - {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Client: {data.get('client_id', 'N/A')}")
        print(f"  Items traites: {items_input}")
        print(f"  Source: {data.get('last_run_path', 'N/A')}")
        
        # Vérifier les alertes
        alerts = check_synthetic_data_indicators(execution)
        if alerts:
            total_alerts += len(alerts)
            for alert in alerts:
                if alert['severity'] == 'CRITICAL':
                    critical_alerts += 1
                print(f"  [{alert['severity']}] {alert['message']}")
        else:
            print("  [OK] Aucune anomalie detectee")
        
        print()
    
    # Résumé
    print("=" * 70)
    print("RESUME")
    print("=" * 70)
    print(f"Total items traites: {total_items}")
    print(f"Moyenne items/execution: {total_items/len(executions):.1f}")
    print(f"Alertes WARNING: {total_alerts - critical_alerts}")
    print(f"Alertes CRITICAL: {critical_alerts}")
    
    if critical_alerts > 0:
        print()
        print("STATUT: ECHEC - Donnees synthetiques detectees!")
        return False
    elif total_alerts > 0:
        print()
        print("STATUT: AVERTISSEMENT - Anomalies detectees")
        return True
    else:
        print()
        print("STATUT: SUCCES - Conformite totale")
        return True


def main():
    """Fonction principale."""
    print("Monitoring de conformite Real Data Only")
    print()
    
    try:
        # Récupérer les exécutions récentes
        executions = get_recent_executions(hours=24)
        
        # Générer le rapport
        success = generate_compliance_report(executions)
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"Erreur fatale: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())