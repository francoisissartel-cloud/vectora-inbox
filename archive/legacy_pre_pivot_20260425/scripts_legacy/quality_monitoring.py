#!/usr/bin/env python3
"""
Script de monitoring automatique des corrections VectoraInbox
Publie les métriques et vérifie les alarmes de qualité
"""
import boto3
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any

def run_quality_monitoring(client_id: str, profile: str = 'rag-lai-prod', verbose: bool = False):
    """Exécute le monitoring complet de qualité"""
    
    print(f"[MONITORING] Demarrage monitoring qualite - {client_id}")
    print(f"[MONITORING] Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 1. Publication des métriques
    print("\\n[STEP 1] Publication des metriques CloudWatch...")
    
    try:
        from publish_quality_metrics import publish_quality_metrics
        metrics_success = publish_quality_metrics(client_id, profile)
        
        if metrics_success:
            print("[OK] Metriques publiees avec succes")
        else:
            print("[ERROR] Echec publication metriques")
            return False
            
    except Exception as e:
        print(f"[ERROR] Erreur publication metriques: {e}")
        return False
    
    # 2. Vérification des alarmes
    print("\\n[STEP 2] Verification des alarmes...")
    
    session = boto3.Session(profile_name=profile)
    cloudwatch = session.client('cloudwatch')
    
    try:
        response = cloudwatch.describe_alarms(
            AlarmNamePrefix=f'VectoraInbox-{client_id}'
        )
        
        alarms = response.get('MetricAlarms', [])
        
        if not alarms:
            print("[WARN] Aucune alarme configuree - Executer create_quality_alarms.py")
            return True
        
        alarm_states = {
            'OK': 0,
            'ALARM': 0,
            'INSUFFICIENT_DATA': 0
        }
        
        critical_alarms = []
        
        for alarm in alarms:
            state = alarm['StateValue']
            alarm_states[state] = alarm_states.get(state, 0) + 1
            
            if verbose:
                print(f"   {alarm['AlarmName']}: {state}")
            
            if state == 'ALARM':
                severity = 'High' if 'Failure' in alarm['AlarmName'] or 'High' in alarm['AlarmName'] else 'Medium'
                critical_alarms.append({
                    'name': alarm['AlarmName'],
                    'description': alarm['AlarmDescription'],
                    'severity': severity,
                    'state_reason': alarm.get('StateReason', 'Unknown')
                })
        
        print(f"[INFO] Etat des alarmes: OK={alarm_states['OK']}, ALARM={alarm_states['ALARM']}, INSUFFICIENT_DATA={alarm_states['INSUFFICIENT_DATA']}")
        
        if critical_alarms:
            print(f"\\n[ALERT] {len(critical_alarms)} alarmes critiques detectees:")
            for alarm in critical_alarms:
                print(f"   [ALARM] {alarm['name']}")
                print(f"           {alarm['description']}")
                print(f"           Severite: {alarm['severity']}")
                print(f"           Raison: {alarm['state_reason']}")
            
            return False
        else:
            print("[OK] Aucune alarme critique")
            
    except Exception as e:
        print(f"[ERROR] Erreur verification alarmes: {e}")
        return False
    
    # 3. Génération du rapport de monitoring
    print("\\n[STEP 3] Generation rapport monitoring...")
    
    try:
        report = generate_monitoring_report(client_id, profile)
        
        # Sauvegarder le rapport
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"monitoring_reports/quality_report_{client_id}_{timestamp}.json"
        
        import os
        os.makedirs('monitoring_reports', exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"[OK] Rapport sauvegarde: {report_file}")
        
        # Afficher résumé
        print("\\n[SUMMARY] Resume monitoring:")
        print(f"   Client: {report['client_id']}")
        print(f"   Timestamp: {report['timestamp']}")
        print(f"   Metriques: {len(report['metrics'])} publiees")
        print(f"   Alarmes: {report['alarms']['total']} configurees")
        print(f"   Status global: {report['overall_status']}")
        
        return report['overall_status'] == 'OK'
        
    except Exception as e:
        print(f"[ERROR] Erreur generation rapport: {e}")
        return False

def generate_monitoring_report(client_id: str, profile: str) -> Dict[str, Any]:
    """Génère un rapport détaillé du monitoring"""
    
    session = boto3.Session(profile_name=profile)
    s3 = session.client('s3')
    cloudwatch = session.client('cloudwatch')
    
    report = {
        'client_id': client_id,
        'timestamp': datetime.now().isoformat(),
        'metrics': {},
        'alarms': {},
        'data_quality': {},
        'overall_status': 'OK'
    }
    
    # Récupérer les métriques actuelles
    try:
        today = datetime.now()
        date_path = today.strftime('%Y/%m/%d')
        
        # Données ingérées
        response = s3.get_object(
            Bucket='vectora-inbox-data-dev',
            Key=f'ingested/{client_id}/{date_path}/items.json'
        )
        ingested_items = json.loads(response['Body'].read())
        
        # Données curées
        response = s3.get_object(
            Bucket='vectora-inbox-data-dev',
            Key=f'curated/{client_id}/{date_path}/items.json'
        )
        curated_items = json.loads(response['Body'].read())
        
        # Newsletter
        response = s3.get_object(
            Bucket='vectora-inbox-newsletters-dev',
            Key=f'{client_id}/{date_path}/newsletter.json'
        )
        newsletter = json.loads(response['Body'].read())
        
        # Calculer les métriques
        total_items = len(ingested_items)
        real_dates = sum(1 for item in ingested_items 
                        if item.get('published_at', '')[:10] != item.get('ingested_at', '')[:10])
        
        avg_word_count = sum(len(item.get('content', '').split()) for item in ingested_items) / total_items
        
        enriched_items = sum(1 for item in ingested_items if len(item.get('content', '').split()) > 50)
        enrichment_rate = (enriched_items / total_items * 100) if total_items > 0 else 0
        
        sections = newsletter.get('sections', [])
        filled_sections = sum(1 for s in sections if len(s.get('items', [])) > 0)
        
        report['metrics'] = {
            'total_items': total_items,
            'real_dates_count': real_dates,
            'real_dates_rate': (real_dates / total_items * 100) if total_items > 0 else 0,
            'avg_word_count': avg_word_count,
            'enrichment_rate': enrichment_rate,
            'newsletter_sections_filled': filled_sections,
            'newsletter_sections_total': len(sections)
        }
        
        # Évaluer la qualité
        quality_issues = []
        
        if report['metrics']['real_dates_rate'] < 20:
            quality_issues.append('Taux de dates reelles trop bas')
        
        if report['metrics']['avg_word_count'] < 25:
            quality_issues.append('Word count moyen insuffisant')
        
        if report['metrics']['enrichment_rate'] < 15:
            quality_issues.append('Taux d\'enrichissement faible')
        
        if report['metrics']['newsletter_sections_filled'] < 2:
            quality_issues.append('Distribution newsletter desequilibree')
        
        report['data_quality'] = {
            'issues': quality_issues,
            'score': max(0, 100 - len(quality_issues) * 25)
        }
        
        if quality_issues:
            report['overall_status'] = 'DEGRADED' if len(quality_issues) <= 2 else 'CRITICAL'
        
    except Exception as e:
        report['data_quality'] = {'error': str(e)}
        report['overall_status'] = 'ERROR'
    
    # État des alarmes
    try:
        response = cloudwatch.describe_alarms(
            AlarmNamePrefix=f'VectoraInbox-{client_id}'
        )
        
        alarms = response.get('MetricAlarms', [])
        alarm_states = {}
        
        for alarm in alarms:
            state = alarm['StateValue']
            alarm_states[state] = alarm_states.get(state, 0) + 1
        
        report['alarms'] = {
            'total': len(alarms),
            'states': alarm_states,
            'critical_count': alarm_states.get('ALARM', 0)
        }
        
        if alarm_states.get('ALARM', 0) > 0:
            report['overall_status'] = 'CRITICAL'
        
    except Exception as e:
        report['alarms'] = {'error': str(e)}
    
    return report

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python quality_monitoring.py <client_id> [profile] [--verbose]")
        print("Exemple: python quality_monitoring.py lai_weekly_v4 rag-lai-prod --verbose")
        sys.exit(1)
    
    client_id = sys.argv[1]
    profile = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else 'rag-lai-prod'
    verbose = '--verbose' in sys.argv
    
    success = run_quality_monitoring(client_id, profile, verbose)
    
    if success:
        print("\\n[SUCCESS] Monitoring execute avec succes")
        sys.exit(0)
    else:
        print("\\n[FAILURE] Problemes detectes lors du monitoring")
        sys.exit(1)