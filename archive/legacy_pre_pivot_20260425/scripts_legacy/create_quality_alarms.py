#!/usr/bin/env python3
"""
Script de configuration des alarmes CloudWatch pour surveiller la qualité
Détecte les régressions dans les corrections déployées
"""
import boto3
import json
from typing import List, Dict, Any

def create_quality_alarms(client_id: str, profile: str = 'rag-lai-prod'):
    """Crée les alarmes CloudWatch pour surveiller la qualité"""
    
    session = boto3.Session(profile_name=profile)
    cloudwatch = session.client('cloudwatch')
    sns = session.client('sns')
    
    # Configuration des alarmes
    alarms_config = [
        {
            'name': f'VectoraInbox-{client_id}-DateExtractionFailure',
            'description': 'Taux de dates fallback trop élevé - Régression extraction dates',
            'metric_name': 'DatesFallbackRate',
            'threshold': 80.0,
            'comparison': 'GreaterThanThreshold',
            'severity': 'High'
        },
        {
            'name': f'VectoraInbox-{client_id}-LowWordCount',
            'description': 'Word count moyen trop bas - Régression enrichissement contenu',
            'metric_name': 'AvgWordCount',
            'threshold': 25.0,
            'comparison': 'LessThanThreshold',
            'severity': 'Medium'
        },
        {
            'name': f'VectoraInbox-{client_id}-HighHallucinations',
            'description': 'Trop d\'hallucinations détectées - Régression anti-hallucination',
            'metric_name': 'AvgHallucinationsPerItem',
            'threshold': 8.0,
            'comparison': 'GreaterThanThreshold',
            'severity': 'High'
        },
        {
            'name': f'VectoraInbox-{client_id}-PoorDistribution',
            'description': 'Distribution newsletter déséquilibrée - Régression sélection',
            'metric_name': 'NewsletterDistributionRate',
            'threshold': 40.0,
            'comparison': 'LessThanThreshold',
            'severity': 'Medium'
        },
        {
            'name': f'VectoraInbox-{client_id}-LowEnrichment',
            'description': 'Taux d\'enrichissement trop bas - Régression enrichissement',
            'metric_name': 'ContentEnrichmentRate',
            'threshold': 15.0,
            'comparison': 'LessThanThreshold',
            'severity': 'Low'
        }
    ]
    
    created_alarms = []
    
    for alarm_config in alarms_config:
        try:
            # Créer l'alarme
            cloudwatch.put_metric_alarm(
                AlarmName=alarm_config['name'],
                AlarmDescription=alarm_config['description'],
                ActionsEnabled=True,
                MetricName=alarm_config['metric_name'],
                Namespace='VectoraInbox/Quality',
                Statistic='Average',
                Dimensions=[
                    {'Name': 'ClientId', 'Value': client_id},
                    {'Name': 'Environment', 'Value': 'dev'}
                ],
                Period=3600,  # 1 heure
                EvaluationPeriods=2,  # 2 périodes consécutives
                Threshold=alarm_config['threshold'],
                ComparisonOperator=alarm_config['comparison'],
                TreatMissingData='notBreaching'
            )
            
            created_alarms.append(alarm_config['name'])
            print(f"[OK] Alarme creee: {alarm_config['name']}")
            print(f"   Metrique: {alarm_config['metric_name']}")
            print(f"   Seuil: {alarm_config['threshold']} ({alarm_config['comparison']})")
            print(f"   Severite: {alarm_config['severity']}")
            print()
            
        except Exception as e:
            print(f"[ERROR] Erreur creation alarme {alarm_config['name']}: {e}")
    
    print(f"[OK] {len(created_alarms)} alarmes CloudWatch creees avec succes")
    
    # Créer un dashboard CloudWatch pour visualiser les métriques
    try:
        dashboard_body = {
            "widgets": [
                {
                    "type": "metric",
                    "x": 0, "y": 0, "width": 12, "height": 6,
                    "properties": {
                        "metrics": [
                            ["VectoraInbox/Quality", "RealDatesRate", "ClientId", client_id, "Environment", "dev"],
                            [".", "DatesFallbackRate", ".", ".", ".", "."]
                        ],
                        "period": 3600,
                        "stat": "Average",
                        "region": "eu-west-3",
                        "title": "Extraction Dates - Corrections Phase 1"
                    }
                },
                {
                    "type": "metric",
                    "x": 12, "y": 0, "width": 12, "height": 6,
                    "properties": {
                        "metrics": [
                            ["VectoraInbox/Quality", "AvgWordCount", "ClientId", client_id, "Environment", "dev"],
                            [".", "ContentEnrichmentRate", ".", ".", ".", "."]
                        ],
                        "period": 3600,
                        "stat": "Average",
                        "region": "eu-west-3",
                        "title": "Enrichissement Contenu - Corrections Phase 1"
                    }
                },
                {
                    "type": "metric",
                    "x": 0, "y": 6, "width": 12, "height": 6,
                    "properties": {
                        "metrics": [
                            ["VectoraInbox/Quality", "AvgHallucinationsPerItem", "ClientId", client_id, "Environment", "dev"]
                        ],
                        "period": 3600,
                        "stat": "Average",
                        "region": "eu-west-3",
                        "title": "Anti-Hallucinations - Corrections Phase 2"
                    }
                },
                {
                    "type": "metric",
                    "x": 12, "y": 6, "width": 12, "height": 6,
                    "properties": {
                        "metrics": [
                            ["VectoraInbox/Quality", "NewsletterSectionsFilled", "ClientId", client_id, "Environment", "dev"],
                            [".", "NewsletterDistributionRate", ".", ".", ".", "."]
                        ],
                        "period": 3600,
                        "stat": "Average",
                        "region": "eu-west-3",
                        "title": "Distribution Newsletter - Corrections Phase 3"
                    }
                }
            ]
        }
        
        cloudwatch.put_dashboard(
            DashboardName=f'VectoraInbox-Quality-{client_id}',
            DashboardBody=json.dumps(dashboard_body)
        )
        
        print(f"[OK] Dashboard CloudWatch cree: VectoraInbox-Quality-{client_id}")
        
    except Exception as e:
        print(f"[WARN] Erreur creation dashboard: {e}")
    
    return created_alarms

def list_existing_alarms(client_id: str, profile: str = 'rag-lai-prod'):
    """Liste les alarmes existantes pour le client"""
    
    session = boto3.Session(profile_name=profile)
    cloudwatch = session.client('cloudwatch')
    
    try:
        response = cloudwatch.describe_alarms(
            AlarmNamePrefix=f'VectoraInbox-{client_id}'
        )
        
        alarms = response.get('MetricAlarms', [])
        
        if alarms:
            print(f"[INFO] Alarmes existantes pour {client_id}:")
            for alarm in alarms:
                state = alarm['StateValue']
                state_icon = "[OK]" if state == "OK" else "[ALARM]" if state == "ALARM" else "[UNKNOWN]"
                print(f"   {state_icon} {alarm['AlarmName']} - {state}")
        else:
            print(f"[INFO] Aucune alarme existante pour {client_id}")
            
        return alarms
        
    except Exception as e:
        print(f"[ERROR] Erreur listage alarmes: {e}")
        return []

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python create_quality_alarms.py <client_id> [profile] [--list-only]")
        sys.exit(1)
    
    client_id = sys.argv[1]
    profile = 'rag-lai-prod'
    list_only = False
    
    if len(sys.argv) > 2:
        if sys.argv[2] == '--list-only':
            list_only = True
        else:
            profile = sys.argv[2]
    
    if len(sys.argv) > 3 and sys.argv[3] == '--list-only':
        list_only = True
    
    if list_only:
        list_existing_alarms(client_id, profile)
    else:
        print(f"[CONFIG] Configuration des alarmes CloudWatch pour {client_id}")
        print("=" * 60)
        
        # Lister les alarmes existantes
        existing = list_existing_alarms(client_id, profile)
        
        if existing:
            print(f"\n[WARN] {len(existing)} alarmes existantes trouvees.")
            response = input("Voulez-vous les remplacer ? (y/N): ")
            if response.lower() != 'y':
                print("Operation annulee.")
                sys.exit(0)
        
        print("\n[START] Creation des nouvelles alarmes...")
        created = create_quality_alarms(client_id, profile)
        
        if created:
            print(f"\n[OK] Configuration terminee - {len(created)} alarmes actives")
            print("\n[INFO] Accedez au dashboard CloudWatch:")
            print(f"   https://eu-west-3.console.aws.amazon.com/cloudwatch/home?region=eu-west-3#dashboards:name=VectoraInbox-Quality-{client_id}")
        else:
            print("\n[ERROR] Echec de la configuration")
            sys.exit(1)