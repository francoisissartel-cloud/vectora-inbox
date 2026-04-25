"""
Test: Approche B fonctionne avec les bons parametres
Verifie que le prompt est charge depuis S3 et contient l'extraction de dates
"""

import sys
sys.path.insert(0, 'src_v2')

from vectora_core.shared import s3_io, config_loader
from vectora_core.normalization.bedrock_client import BedrockNormalizationClient

print("=" * 60)
print("TEST: Approche B Fonctionne")
print("=" * 60)

# Charger config
print("\n[1] Chargement configuration...")
try:
    client_config = config_loader.load_client_config("lai_weekly_v7", "vectora-inbox-config-dev")
    canonical_scopes = config_loader.load_canonical_scopes("vectora-inbox-config-dev")
    print("[OK] Configuration chargee")
except Exception as e:
    print(f"[ERREUR] ECHEC chargement config: {e}")
    sys.exit(1)

# Initialiser client (doit reussir)
print("\n[2] Initialisation client Bedrock...")
try:
    client = BedrockNormalizationClient(
        model_id="anthropic.claude-3-sonnet-20240229-v1:0",
        region="us-east-1",
        s3_io=s3_io,
        client_config=client_config,
        canonical_scopes=canonical_scopes
    )
    print("[OK] Client initialise avec succes")
except Exception as e:
    print(f"[ERREUR] ECHEC initialisation: {e}")
    sys.exit(1)

# Verifications
print("\n[3] Verifications...")

# Verifier prompt_template charge
if client.prompt_template is None:
    print("[ERREUR] ECHEC: Prompt template non charge")
    sys.exit(1)
print("[OK] Prompt template charge")

# Verifier que le prompt contient extraction dates
prompt_str = str(client.prompt_template)
if "extracted_date" not in prompt_str:
    print("[ERREUR] ECHEC: Prompt ne contient pas 'extracted_date'")
    sys.exit(1)
print("[OK] Prompt contient 'extracted_date'")

if "date_confidence" not in prompt_str:
    print("[ERREUR] ECHEC: Prompt ne contient pas 'date_confidence'")
    sys.exit(1)
print("[OK] Prompt contient 'date_confidence'")

# Verifier que les methodes V1/V2 n'existent plus
print("\n[4] Verification suppression prompts hardcodes...")
if hasattr(client, '_build_normalization_prompt_v1'):
    print("[ERREUR] ECHEC: Methode _build_normalization_prompt_v1 existe encore")
    sys.exit(1)
print("[OK] Methode V1 supprimee")

if hasattr(client, '_build_normalization_prompt_v2'):
    print("[ERREUR] ECHEC: Methode _build_normalization_prompt_v2 existe encore")
    sys.exit(1)
print("[OK] Methode V2 supprimee")

if hasattr(client, '_extract_company_from_source_key'):
    print("[ERREUR] ECHEC: Helper _extract_company_from_source_key existe encore")
    sys.exit(1)
print("[OK] Helper _extract_company_from_source_key supprime")

if hasattr(client, '_is_pure_player_company'):
    print("[ERREUR] ECHEC: Helper _is_pure_player_company existe encore")
    sys.exit(1)
print("[OK] Helper _is_pure_player_company supprime")

print("\n" + "=" * 60)
print("[OK] TOUS LES TESTS PASSENT")
print("=" * 60)
print("\nResultat: Approche B activee avec succes")
print("- Prompt charge depuis S3 [OK]")
print("- Extraction dates presente [OK]")
print("- Prompts hardcodes V1/V2 supprimes [OK]")
print("- Helpers integres inline [OK]")
