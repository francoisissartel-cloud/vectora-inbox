#!/usr/bin/env python3
"""
Vérifie que les références {{ref:}} dans les prompts sont bien résolues
"""

import boto3
import yaml
import re

PROFILE = "rag-lai-prod"
REGION = "eu-west-3"
BUCKET = "vectora-inbox-data-dev"

def download_file(key):
    """Télécharge un fichier depuis S3"""
    session = boto3.Session(profile_name=PROFILE, region_name=REGION)
    s3 = session.client('s3')
    
    try:
        response = s3.get_object(Bucket=BUCKET, Key=key)
        content = response['Body'].read().decode('utf-8')
        return yaml.safe_load(content)
    except Exception as e:
        print(f"Erreur téléchargement {key}: {e}")
        return None

def check_references(text):
    """Cherche les références {{ref:}} non résolues"""
    pattern = r'\{\{ref:([^}]+)\}\}'
    refs = re.findall(pattern, text)
    return refs

def main():
    print("="*80)
    print("VERIFICATION RESOLUTION REFERENCES PROMPTS")
    print("="*80)
    print()
    
    # Télécharger le prompt de scoring
    print("[1/2] Téléchargement lai_domain_scoring.yaml...")
    scoring_prompt = download_file("canonical/prompts/domain_scoring/lai_domain_scoring.yaml")
    
    if not scoring_prompt:
        print("❌ Impossible de télécharger le prompt")
        return
    
    print("[OK] Prompt telecharge")
    print()
    
    # Vérifier les références dans user_template
    print("[2/2] Vérification des références...")
    user_template = scoring_prompt.get('user_template', '')
    
    refs = check_references(user_template)
    
    if refs:
        print(f"[WARNING] {len(refs)} reference(s) trouvee(s):")
        for ref in refs:
            print(f"   - {{{{ref:{ref}}}}}")
        print()
        print("Ces références doivent être résolues par prompt_resolver.py")
        print("en chargeant les fichiers canonical correspondants.")
    else:
        print("[OK] Aucune reference {{ref:}} trouvee")
        print("   Le prompt est soit inline, soit déjà résolu")
    
    print()
    
    # Télécharger lai_domain_definition
    print("[3/3] Vérification lai_domain_definition.yaml...")
    domain_def = download_file("canonical/domains/lai_domain_definition.yaml")
    
    if not domain_def:
        print("❌ Impossible de télécharger la définition")
        return
    
    # Vérifier les scope_ref
    print()
    print("Références scope_ref trouvées:")
    
    scope_refs = []
    
    def find_scope_refs(obj, path=""):
        if isinstance(obj, dict):
            if 'scope_ref' in obj:
                scope_refs.append((path, obj['scope_ref']))
            for k, v in obj.items():
                find_scope_refs(v, f"{path}.{k}" if path else k)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                find_scope_refs(item, f"{path}[{i}]")
    
    find_scope_refs(domain_def)
    
    if scope_refs:
        print(f"[WARNING] {len(scope_refs)} scope_ref trouvee(s):")
        for path, ref in scope_refs:
            print(f"   - {path}: {ref}")
        print()
        print("Ces scopes doivent être chargés depuis:")
        print("   - canonical/scopes/company_scopes.yaml")
        print("   - canonical/scopes/molecule_scopes.yaml")
        print("   - canonical/scopes/trademark_scopes.yaml")
    else:
        print("[OK] Aucun scope_ref trouve")
    
    print()
    print("="*80)
    print("CONCLUSION")
    print("="*80)
    print()
    
    if refs or scope_refs:
        print("[WARNING] Le systeme utilise des references externes")
        print("   Les 18 fichiers canonical uploadés sont NÉCESSAIRES")
        print("   pour résoudre ces références.")
        print()
        print("   Sans eux, les prompts Bedrock reçoivent:")
        print("   - [SCOPE_NOT_FOUND: xxx] au lieu des listes complètes")
        print("   - Seulement les exemples inline (5-10 items)")
        print("   - Au lieu des listes complètes (200+ items)")
    else:
        print("[OK] Le systeme fonctionne en mode standalone")
        print("   Toutes les données sont inline dans les prompts")

if __name__ == "__main__":
    main()
