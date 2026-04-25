"""
Test: Validation que l'Approche B est OBLIGATOIRE
Verifie que le client Bedrock refuse de s'initialiser sans les parametres requis
"""

import sys
sys.path.insert(0, 'src_v2')

from vectora_core.normalization.bedrock_client import BedrockNormalizationClient

print("=" * 60)
print("TEST: Approche B Obligatoire - Validation Parametres")
print("=" * 60)

# Test 1: Erreur si s3_io manquant
print("\n[Test 1] s3_io manquant...")
try:
    client = BedrockNormalizationClient(
        model_id="test",
        region="us-east-1",
        s3_io=None,
        client_config={"bedrock_config": {"normalization_prompt": "lai"}},
        canonical_scopes={}
    )
    print("[ERREUR] ECHEC: Devrait lever ValueError")
    sys.exit(1)
except ValueError as e:
    if "s3_io est requis" in str(e):
        print(f"[OK] SUCCES: {e}")
    else:
        print(f"[ERREUR] ECHEC: Mauvais message: {e}")
        sys.exit(1)

# Test 2: Erreur si client_config manquant
print("\n[Test 2] client_config manquant...")
try:
    client = BedrockNormalizationClient(
        model_id="test",
        region="us-east-1",
        s3_io="mock_s3_io",
        client_config=None,
        canonical_scopes={}
    )
    print("[ERREUR] ECHEC: Devrait lever ValueError")
    sys.exit(1)
except ValueError as e:
    if "client_config est requis" in str(e):
        print(f"[OK] SUCCES: {e}")
    else:
        print(f"[ERREUR] ECHEC: Mauvais message: {e}")
        sys.exit(1)

# Test 3: Erreur si canonical_scopes manquant
print("\n[Test 3] canonical_scopes manquant...")
try:
    client = BedrockNormalizationClient(
        model_id="test",
        region="us-east-1",
        s3_io="mock_s3_io",
        client_config={"bedrock_config": {"normalization_prompt": "lai"}},
        canonical_scopes=None
    )
    print("[ERREUR] ECHEC: Devrait lever ValueError")
    sys.exit(1)
except ValueError as e:
    if "canonical_scopes est requis" in str(e):
        print(f"[OK] SUCCES: {e}")
    else:
        print(f"[ERREUR] ECHEC: Mauvais message: {e}")
        sys.exit(1)

# Test 4: Erreur si normalization_prompt manquant
print("\n[Test 4] normalization_prompt manquant...")
try:
    # Mock s3_io pour passer la validation initiale
    class MockS3IO:
        pass
    
    client = BedrockNormalizationClient(
        model_id="test",
        region="us-east-1",
        s3_io=MockS3IO(),
        client_config={"bedrock_config": {}},
        canonical_scopes={"test": "value"}
    )
    print("[ERREUR] ECHEC: Devrait lever ValueError")
    sys.exit(1)
except ValueError as e:
    if "normalization_prompt" in str(e):
        print(f"[OK] SUCCES: {e}")
    else:
        print(f"[ERREUR] ECHEC: Mauvais message: {e}")
        sys.exit(1)

print("\n" + "=" * 60)
print("[OK] TOUS LES TESTS PASSENT")
print("=" * 60)
print("\nResultat: Approche B est OBLIGATOIRE")
print("- s3_io requis [OK]")
print("- client_config requis [OK]")
print("- canonical_scopes requis [OK]")
print("- normalization_prompt requis [OK]")
