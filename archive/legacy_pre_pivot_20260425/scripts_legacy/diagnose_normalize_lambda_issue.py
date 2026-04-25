#!/usr/bin/env python3
"""
Diagnostic et correction du problème Lambda normalize_score_v2
Erreur: "No module named 'yaml'"
"""

import boto3
import json
from datetime import datetime

def diagnose_lambda_configuration():
    """Diagnostique la configuration de la Lambda normalize_score_v2"""
    
    print("[DIAGNOSTIC] Lambda normalize_score_v2-dev")
    print("=" * 60)
    
    # Client Lambda avec session
    session = boto3.Session(profile_name='rag-lai-prod')
    lambda_client = session.client('lambda', region_name='eu-west-3')
    
    function_name = 'vectora-inbox-normalize-score-v2-dev'
    
    try:
        # Configuration de la Lambda
        print("\n[CONFIG] Configuration Lambda...")
        config = lambda_client.get_function(FunctionName=function_name)
        
        print(f"Runtime: {config['Configuration']['Runtime']}")
        print(f"Handler: {config['Configuration']['Handler']}")
        print(f"Code Size: {config['Configuration']['CodeSize']} bytes")
        print(f"Timeout: {config['Configuration']['Timeout']} seconds")
        print(f"Memory: {config['Configuration']['MemorySize']} MB")
        
        # Variables d'environnement
        env_vars = config['Configuration'].get('Environment', {}).get('Variables', {})
        print(f"\n[ENV] Variables d'environnement ({len(env_vars)}):")
        for key, value in env_vars.items():
            print(f"  {key}: {value}")
        
        # Layers
        layers = config['Configuration'].get('Layers', [])
        print(f"\n[LAYERS] Lambda Layers ({len(layers)}):")
        for layer in layers:
            print(f"  - {layer['Arn']}")
            print(f"    Version: {layer.get('CodeSize', 'Unknown')} bytes")
        
        # Dernière modification
        last_modified = config['Configuration']['LastModified']
        print(f"\n[MODIFIED] Derniere modification: {last_modified}")
        
        return {
            'status': 'success',
            'config': config['Configuration'],
            'layers': layers,
            'env_vars': env_vars
        }
        
    except Exception as e:
        print(f"[ERROR] Erreur lors du diagnostic: {str(e)}")
        return {'status': 'error', 'error': str(e)}

def check_recent_logs():
    """Vérifie les logs récents pour plus de détails sur l'erreur"""
    
    print("\n[LOGS] Verification des logs CloudWatch...")
    
    session = boto3.Session(profile_name='rag-lai-prod')
    logs_client = session.client('logs', region_name='eu-west-3')
    
    log_group = '/aws/lambda/vectora-inbox-normalize-score-v2-dev'
    
    try:
        # Récupération des streams récents
        streams = logs_client.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=3
        )
        
        print(f"[STREAMS] {len(streams['logStreams'])} streams recents trouves")
        
        for stream in streams['logStreams'][:2]:  # 2 plus récents
            stream_name = stream['logStreamName']
            print(f"\n[STREAM] {stream_name}")
            
            # Récupération des événements
            events = logs_client.get_log_events(
                logGroupName=log_group,
                logStreamName=stream_name,
                limit=10
            )
            
            for event in events['events'][-5:]:  # 5 derniers événements
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                message = event['message'].strip()
                print(f"  {timestamp}: {message}")
        
        return {'status': 'success'}
        
    except Exception as e:
        print(f"[ERROR] Erreur logs: {str(e)}")
        return {'status': 'error', 'error': str(e)}

def analyze_yaml_dependency_issue():
    """Analyse le problème spécifique du module yaml"""
    
    print("\n[YAML-ISSUE] Analyse du probleme module 'yaml'...")
    
    # Problèmes possibles identifiés
    issues = [
        {
            'issue': 'PyYAML manquant dans Lambda Layer',
            'description': 'Le module PyYAML n\'est pas inclus dans les layers',
            'solution': 'Ajouter PyYAML au layer common-deps',
            'priority': 'HIGH'
        },
        {
            'issue': 'Extension C PyYAML incompatible',
            'description': 'Version PyYAML avec extensions C non compatible AWS Lambda',
            'solution': 'Utiliser PyYAML pure Python (--no-binary)',
            'priority': 'HIGH'
        },
        {
            'issue': 'Import path incorrect',
            'description': 'Code essaie d\'importer yaml mais module pas disponible',
            'solution': 'Vérifier imports dans handler.py et vectora_core',
            'priority': 'MEDIUM'
        },
        {
            'issue': 'Layer non attaché',
            'description': 'Lambda Layer avec PyYAML pas correctement attaché',
            'solution': 'Vérifier configuration layers dans Lambda',
            'priority': 'MEDIUM'
        }
    ]
    
    print(f"[ISSUES] {len(issues)} problemes potentiels identifies:")
    for i, issue in enumerate(issues, 1):
        print(f"\n  {i}. {issue['issue']} [{issue['priority']}]")
        print(f"     Description: {issue['description']}")
        print(f"     Solution: {issue['solution']}")
    
    return issues

def generate_fix_recommendations():
    """Génère des recommandations de correction"""
    
    print("\n[FIXES] Recommandations de correction...")
    
    fixes = [
        {
            'step': 1,
            'action': 'Vérifier contenu Lambda Layer common-deps',
            'command': 'aws lambda get-layer-version --layer-name vectora-inbox-common-deps --version-number X',
            'expected': 'PyYAML présent dans le layer'
        },
        {
            'step': 2,
            'action': 'Recréer layer avec PyYAML pure Python',
            'command': 'pip install --no-binary PyYAML PyYAML==6.0.1 -t layer/',
            'expected': 'PyYAML sans extensions C'
        },
        {
            'step': 3,
            'action': 'Redéployer Lambda avec layer corrigé',
            'command': 'aws lambda update-function-configuration --layers arn:aws:lambda:...',
            'expected': 'Lambda avec layer PyYAML fonctionnel'
        },
        {
            'step': 4,
            'action': 'Tester import yaml',
            'command': 'aws lambda invoke --payload \'{"test": "yaml_import"}\'',
            'expected': 'Pas d\'erreur ImportModuleError'
        }
    ]
    
    for fix in fixes:
        print(f"\n  Etape {fix['step']}: {fix['action']}")
        print(f"    Commande: {fix['command']}")
        print(f"    Attendu: {fix['expected']}")
    
    return fixes

def create_test_payload():
    """Crée un payload de test minimal pour valider la correction"""
    
    test_payload = {
        'client_id': 'lai_weekly_v3',
        'test_mode': True,
        'items_limit': 1
    }
    
    with open('test_normalize_minimal.json', 'w') as f:
        json.dump(test_payload, f, indent=2)
    
    print(f"\n[TEST] Payload de test cree: test_normalize_minimal.json")
    print(f"Contenu: {json.dumps(test_payload, indent=2)}")
    
    return test_payload

def main():
    """Fonction principale de diagnostic"""
    
    print("DIAGNOSTIC Lambda normalize_score_v2 - Erreur 'No module named yaml'")
    print("=" * 80)
    
    # Diagnostic configuration
    config_result = diagnose_lambda_configuration()
    
    # Vérification logs
    logs_result = check_recent_logs()
    
    # Analyse problème yaml
    yaml_issues = analyze_yaml_dependency_issue()
    
    # Recommandations de correction
    fixes = generate_fix_recommendations()
    
    # Payload de test
    test_payload = create_test_payload()
    
    # Résumé
    print("\n" + "=" * 80)
    print("[RESUME] Diagnostic termine")
    
    if config_result['status'] == 'success':
        layers_count = len(config_result.get('layers', []))
        print(f"[OK] Configuration Lambda lue - {layers_count} layers detectes")
    else:
        print(f"[ERROR] Probleme configuration: {config_result.get('error')}")
    
    print(f"[ISSUES] {len(yaml_issues)} problemes potentiels identifies")
    print(f"[FIXES] {len(fixes)} etapes de correction proposees")
    
    print("\n[NEXT-STEPS] Prochaines actions:")
    print("1. Verifier contenu des Lambda Layers")
    print("2. Recreer layer avec PyYAML pure Python si necessaire")
    print("3. Redeployer Lambda avec layer corrige")
    print("4. Tester avec payload minimal")
    print("5. Relancer test end-to-end complet")
    
    # Sauvegarde diagnostic
    diagnostic_result = {
        'diagnostic_date': datetime.now().isoformat(),
        'lambda_config': config_result,
        'logs_check': logs_result,
        'yaml_issues': yaml_issues,
        'fix_recommendations': fixes,
        'test_payload': test_payload
    }
    
    with open('normalize_lambda_diagnostic.json', 'w') as f:
        json.dump(diagnostic_result, f, indent=2)
    
    print(f"\n[SAVE] Diagnostic sauvegarde: normalize_lambda_diagnostic.json")

if __name__ == "__main__":
    main()