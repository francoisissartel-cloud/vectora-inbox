"""
Générateur de configurations client pour tests E2E.
"""

import yaml
from pathlib import Path
from datetime import datetime


def generate_test_config(
    template_path: str,
    client_id: str,
    context_id: str,
    purpose: str,
    environment: str,
    promoted_from: str = None
) -> dict:
    """
    Génère config test depuis template.
    
    Args:
        template_path: Chemin vers template YAML
        client_id: ID client (ex: lai_weekly_test_001 ou lai_weekly_v1)
        context_id: ID contexte test (ex: test_context_001)
        purpose: Description du test
        environment: local, aws_dev, aws_stage
        promoted_from: Client ID source (pour promotion AWS)
    
    Returns:
        dict: Configuration générée
    """
    with open(template_path) as f:
        config_str = f.read()
    
    # Remplacements
    replacements = {
        "{{CLIENT_ID}}": client_id,
        "{{NAME}}": f"LAI Weekly - {context_id} ({environment})",
        "{{CONTEXT_ID}}": context_id,
        "{{PURPOSE}}": purpose,
        "{{ENVIRONMENT}}": environment,
        "{{DATE}}": datetime.now().isoformat(),
        "{{PROMOTED_FROM}}": promoted_from or "null"
    }
    
    for key, value in replacements.items():
        config_str = config_str.replace(key, str(value))
    
    return yaml.safe_load(config_str)


def save_config(config: dict, output_path: str):
    """Sauvegarde config YAML."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
