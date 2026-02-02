"""
Audit du blueprint pour détecter les divergences avec le code/infra.

Vérifie :
- Lambdas dans blueprint vs handlers dans src_v2/
- Versions dans blueprint vs VERSION
- Client de référence dans blueprint vs client configs
- Date last_updated (alerte si > 30 jours)

Usage:
    python scripts/maintenance/audit_blueprint.py
"""

import yaml
import os
from pathlib import Path
from datetime import datetime, timedelta

def load_blueprint():
    """Charge le blueprint YAML."""
    blueprint_path = Path('docs/architecture/blueprint-v2-ACTUAL-2026.yaml')
    if not blueprint_path.exists():
        print("❌ Blueprint introuvable")
        return None
    
    with open(blueprint_path) as f:
        return yaml.safe_load(f)

def load_version_file():
    """Charge le fichier VERSION."""
    version_path = Path('VERSION')
    if not version_path.exists():
        print("❌ Fichier VERSION introuvable")
        return {}
    
    versions = {}
    with open(version_path) as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=')
                versions[key] = value
    return versions

def check_versions(blueprint, version_file):
    """Vérifie la cohérence des versions."""
    issues = []
    
    blueprint_versions = blueprint.get('versioning', {}).get('current_versions', {})
    
    # Mapping des clés
    version_mapping = {
        'VECTORA_CORE_VERSION': 'vectora_core',
        'COMMON_DEPS_VERSION': 'common_deps',
        'INGEST_VERSION': 'ingest',
        'NORMALIZE_VERSION': 'normalize',
        'NEWSLETTER_VERSION': 'newsletter',
        'CANONICAL_VERSION': 'canonical'
    }
    
    for version_key, blueprint_key in version_mapping.items():
        if version_key in version_file:
            version_value = version_file[version_key]
            blueprint_value = blueprint_versions.get(blueprint_key)
            
            if blueprint_value != version_value:
                issues.append(
                    f"Version mismatch: {version_key} = {version_value} (VERSION) "
                    f"vs {blueprint_value} (blueprint)"
                )
    
    return issues

def check_lambdas(blueprint):
    """Vérifie la cohérence des Lambdas."""
    issues = []
    
    # Handlers dans le code
    handlers_in_code = []
    lambdas_dir = Path('src_v2/lambdas')
    if lambdas_dir.exists():
        for handler_file in lambdas_dir.rglob('handler.py'):
            handlers_in_code.append(handler_file.parent.name)
    
    # Lambdas dans le blueprint
    lambdas_in_blueprint = []
    for lambda_def in blueprint.get('architecture', {}).get('lambdas', []):
        lambda_id = lambda_def.get('id', '').replace('_v2', '')
        lambdas_in_blueprint.append(lambda_id)
    
    # Vérifier handlers dans code mais pas dans blueprint
    for handler in handlers_in_code:
        if handler not in lambdas_in_blueprint:
            issues.append(f"Lambda handler exists in code but not in blueprint: {handler}")
    
    # Vérifier Lambdas dans blueprint mais pas dans code
    for lambda_id in lambdas_in_blueprint:
        if lambda_id not in handlers_in_code:
            issues.append(f"Lambda in blueprint but handler not found in code: {lambda_id}")
    
    return issues

def check_client_reference(blueprint):
    """Vérifie le client de référence."""
    issues = []
    
    client_ref = blueprint.get('client_reference', {})
    client_id = client_ref.get('client_id')
    
    if client_id:
        # Vérifier que le fichier config existe
        config_path = Path(f'client-config-examples/{client_id}.yaml')
        if not config_path.exists():
            issues.append(
                f"Client de référence {client_id} spécifié dans blueprint "
                f"mais fichier config introuvable: {config_path}"
            )
    
    return issues

def check_last_updated(blueprint):
    """Vérifie la date de dernière mise à jour."""
    warnings = []
    
    last_updated_str = blueprint.get('metadata', {}).get('last_updated')
    if last_updated_str:
        try:
            last_updated = datetime.strptime(last_updated_str, '%Y-%m-%d')
            days_ago = (datetime.now() - last_updated).days
            
            if days_ago > 30:
                warnings.append(
                    f"Blueprint pas mis à jour depuis {days_ago} jours "
                    f"(dernière mise à jour: {last_updated_str})"
                )
        except ValueError:
            warnings.append(f"Format de date invalide: {last_updated_str}")
    
    return warnings

def main():
    """Fonction principale d'audit."""
    print("🔍 Audit du blueprint Vectora Inbox\n")
    
    # Charger les données
    blueprint = load_blueprint()
    if not blueprint:
        return False
    
    version_file = load_version_file()
    
    # Collecter les issues
    all_issues = []
    all_warnings = []
    
    # Vérifications
    print("Vérification des versions...")
    all_issues.extend(check_versions(blueprint, version_file))
    
    print("Vérification des Lambdas...")
    all_issues.extend(check_lambdas(blueprint))
    
    print("Vérification du client de référence...")
    all_issues.extend(check_client_reference(blueprint))
    
    print("Vérification de la date de mise à jour...")
    all_warnings.extend(check_last_updated(blueprint))
    
    # Afficher les résultats
    print("\n" + "="*60)
    
    if all_issues:
        print("\n❌ DIVERGENCES CRITIQUES DÉTECTÉES:\n")
        for issue in all_issues:
            print(f"  • {issue}")
    
    if all_warnings:
        print("\n⚠️  AVERTISSEMENTS:\n")
        for warning in all_warnings:
            print(f"  • {warning}")
    
    if not all_issues and not all_warnings:
        print("\n✅ Blueprint à jour - Aucune divergence détectée")
        return True
    
    print("\n" + "="*60)
    
    if all_issues:
        print("\n📝 ACTION REQUISE:")
        print("  Mettre à jour docs/architecture/blueprint-v2-ACTUAL-2026.yaml")
        print("  Guide: docs/architecture/BLUEPRINT_MAINTENANCE.md")
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
