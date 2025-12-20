"""
Client Bedrock spécialisé pour la normalisation des items.

Ce module fournit une interface robuste pour les appels Bedrock
avec gestion des erreurs, retry automatique et prompts canoniques.

CORRECTION BEDROCK V2 : Utilise exactement la même logique que V1 qui fonctionne.
"""

import json
import logging
import os
import time
import random
from typing import Dict, Any, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def get_bedrock_client():
    """
    Retourne un client boto3 Bedrock Runtime (COPIE EXACTE DE V1).
    
    Returns:
        Client boto3 bedrock-runtime configuré
    """
    region = os.environ.get('BEDROCK_REGION', 'us-east-1')
    return boto3.client('bedrock-runtime', region_name=region)


def call_bedrock_with_retry(
    model_id: str,
    request_body: Dict[str, Any],
    max_retries: int = 3,
    base_delay: float = 0.5
) -> str:
    """API Bedrock unifiée avec retry automatique (COPIE EXACTE DE LA LOGIQUE V1).
    
    Args:
        model_id: Identifiant du modèle Bedrock
        request_body: Corps de la requête (format Claude Messages API)
        max_retries: Nombre maximum de tentatives
        base_delay: Délai de base pour le backoff
    
    Returns:
        Texte de réponse de Bedrock
    """
    # Créer le client à chaque appel comme V1
    client = get_bedrock_client()
    
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Appel à Bedrock (tentative {attempt + 1}/{max_retries + 1})")
            
            response = client.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            
            # Extraction du texte de réponse exactement comme V1
            content = response_body.get('content', [])
            if content and len(content) > 0:
                response_text = content[0].get('text', '')
            else:
                response_text = ''
            
            logger.info("Réponse Bedrock reçue avec succès")
            return response_text
        
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            
            # Vérifier si c'est une erreur de throttling (exactement comme V1)
            if error_code == 'ThrottlingException' or 'throttl' in error_code.lower():
                if attempt < max_retries:
                    # Calculer le délai avec backoff exponentiel + jitter (comme V1)
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 0.1)
                    logger.warning(
                        f"ThrottlingException détectée (tentative {attempt + 1}/{max_retries + 1}). "
                        f"Retry dans {delay:.2f}s..."
                    )
                    time.sleep(delay)
                    continue
                else:
                    logger.error(
                        f"ThrottlingException - Échec après {max_retries + 1} tentatives. "
                        f"Abandon de l'appel Bedrock."
                    )
                    raise
            else:
                # Autre type d'erreur : ne pas retry (comme V1)
                logger.error(f"Erreur Bedrock non-throttling ({error_code}): {e}")
                raise
        
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'appel Bedrock: {e}")
            raise
    
    # Ne devrait jamais arriver ici
    raise Exception("Échec de l'appel Bedrock après tous les retries")


# Alias pour compatibilité avec bedrock_matcher.py
_call_bedrock_with_retry = call_bedrock_with_retry


class BedrockNormalizationClient:
    """Client Bedrock robuste pour la normalisation des items."""
    
    def __init__(self, model_id: str, region: str = "us-east-1"):
        """
        Initialise le client Bedrock avec la même logique que V1.
        
        Args:
            model_id: Identifiant du modèle Bedrock
            region: Région AWS pour Bedrock
        """
        self.region = region
        self.model_id = model_id
        
        logger.info(f"Client Bedrock initialisé : modèle={self.model_id}, région={region}")
    
    def normalize_item(self, item_text: str, canonical_examples: Dict, 
                      domain_contexts: Optional[list] = None) -> Dict[str, Any]:
        """
        Normalise un item via Bedrock avec retry automatique (UTILISE LA LOGIQUE V1).
        
        Args:
            item_text: Texte de l'item à normaliser
            canonical_examples: Exemples depuis canonical scopes
            domain_contexts: Contextes de domaines (optionnel)
        
        Returns:
            Résultat de normalisation avec champs LAI
        """
        try:
            # Construction du prompt avec la logique V1
            prompt = self._build_normalization_prompt_v1(item_text, canonical_examples, domain_contexts)
            
            # Appel Bedrock avec retry (COPIE EXACTE DE V1)
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.0
            }
            
            response_text = call_bedrock_with_retry(self.model_id, request_body)
            result = self._parse_bedrock_response_v1(response_text)
            return result
            
        except Exception as e:
            logger.error(f"Erreur finale lors de l'appel à Bedrock: {e}")
            return self._create_fallback_result()
    
    def _build_normalization_prompt_v1(
        self,
        item_text: str,
        canonical_examples: Dict[str, str],
        domain_contexts: list = None
    ) -> str:
        """
        COPIE EXACTE DE LA FONCTION V1 qui fonctionne.
        
        Args:
            item_text: Texte à analyser
            canonical_examples: Exemples d'entités depuis les scopes
            domain_contexts: Contextes de domaine (optionnel)
        
        Returns:
            Prompt formaté pour Bedrock
        """
        # Limiter les exemples pour ne pas surcharger le prompt
        companies_ex = canonical_examples.get('companies_examples', 'MedinCell, Camurus, DelSiTech')[:500]
        molecules_ex = canonical_examples.get('molecules_examples', 'buprenorphine, naloxone, olanzapine')[:300]
        technologies_ex = canonical_examples.get('technologies_examples', 'long-acting injectable, depot injection, microspheres')[:400]
        
        # Section LAI spécialisée simplifiée (Correction P0-1)
        lai_section = "\n\nLAI TECHNOLOGY FOCUS:\n"
        lai_section += "Detect these LAI (Long-Acting Injectable) technologies:\n"
        lai_section += "- Extended-Release Injectable\n"
        lai_section += "- Long-Acting Injectable\n"
        lai_section += "- Depot Injection\n"
        lai_section += "- Once-Monthly Injection\n"
        lai_section += "- Microspheres\n"
        lai_section += "- PLGA\n"
        lai_section += "- In-Situ Depot\n"
        lai_section += "- Hydrogel\n"
        lai_section += "- Subcutaneous Injection\n"
        lai_section += "- Intramuscular Injection\n"
        lai_section += "\nTRADEMARKS to detect:\n"
        lai_section += "- UZEDY, PharmaShell, SiliaShell, BEPO, Aristada, Abilify Maintena\n"
        lai_section += "\nNormalize: 'extended-release injectable' → 'Extended-Release Injectable'\n"
        
        # Tâches simplifiées avec focus LAI (Correction P0-1)
        tasks = [
            "1. Generate a concise summary (2-3 sentences) explaining the key information",
            "2. Classify the event type among: clinical_update, partnership, regulatory, scientific_paper, corporate_move, financial_results, safety_signal, manufacturing_supply, other",
            "3. Extract ALL pharmaceutical/biotech company names mentioned",
            "4. Extract ALL drug/molecule names mentioned (including brand names, generic names)",
            "5. Extract ALL technology keywords mentioned - FOCUS on LAI technologies listed above",
            "6. Extract ALL trademark names mentioned (especially those with ® or ™ symbols)",
            "7. Extract ALL therapeutic indications mentioned",
            "8. Evaluate LAI relevance (0-10 score): How relevant is this content to Long-Acting Injectable technologies?",
            "9. Detect anti-LAI signals: Does the content mention oral routes (tablets, capsules, pills)?",
            "10. Assess pure player context: Is this about a LAI-focused company without explicit LAI mentions?"
        ]
        
        # Format JSON de réponse avec champs LAI (Correction P0-1)
        json_example = {
            "summary": "...",
            "event_type": "...",
            "companies_detected": ["...", "..."],
            "molecules_detected": ["...", "..."],
            "technologies_detected": ["...", "..."],
            "trademarks_detected": ["...", "..."],
            "indications_detected": ["...", "..."],
            "lai_relevance_score": 0,
            "anti_lai_detected": False,
            "pure_player_context": False
        }
        
        prompt = f"""Analyze the following biotech/pharma news item and extract structured information.

TEXT TO ANALYZE:
{item_text}

EXAMPLES OF ENTITIES TO DETECT:
- Companies: {companies_ex}
- Molecules/Drugs: {molecules_ex}
- Technologies: {technologies_ex}{lai_section}

TASK:
{chr(10).join(tasks)}

IMPORTANT:
- Extract the EXACT company names as they appear in the text (e.g., "WuXi AppTec", "Agios", "Pfizer")
- Include ALL companies mentioned, not just those in the examples
- Be comprehensive in entity extraction

RESPONSE FORMAT (JSON only):
{json.dumps(json_example, indent=2)}

Respond with ONLY the JSON, no additional text."""
        
        return prompt
    
    def _call_bedrock_with_retry_v1(
        self,
        model_id: str,
        request_body: Dict[str, Any],
        max_retries: int = 3,
        base_delay: float = 0.5
    ) -> str:
        """Méthode de compatibilité - délègue vers l'API unifiée."""
        return call_bedrock_with_retry(model_id, request_body, max_retries, base_delay)
    
    def _parse_bedrock_response_v1(self, response_text: str) -> Dict[str, Any]:
        """COPIE EXACTE DE LA FONCTION V1 qui fonctionne."""
        try:
            # Tenter de parser directement comme JSON
            result = json.loads(response_text)
            
            # Valider la structure
            if not isinstance(result, dict):
                raise ValueError("La réponse n'est pas un dictionnaire")
            
            # S'assurer que les champs obligatoires existent (avec champs LAI)
            result.setdefault('summary', '')
            result.setdefault('event_type', 'other')
            result.setdefault('companies_detected', [])
            result.setdefault('molecules_detected', [])
            result.setdefault('technologies_detected', [])
            result.setdefault('trademarks_detected', [])
            result.setdefault('indications_detected', [])
            result.setdefault('lai_relevance_score', 0)
            result.setdefault('anti_lai_detected', False)
            result.setdefault('pure_player_context', False)
            result.setdefault('domain_relevance', [])
            
            return result
        
        except json.JSONDecodeError:
            logger.warning("Réponse Bedrock non-JSON, tentative d'extraction manuelle")
            # Fallback : retourner une structure vide avec champs LAI
            return {
                'summary': response_text[:200] if response_text else '',
                'event_type': 'other',
                'companies_detected': [],
                'molecules_detected': [],
                'technologies_detected': [],
                'trademarks_detected': [],
                'indications_detected': [],
                'lai_relevance_score': 0,
                'anti_lai_detected': False,
                'pure_player_context': False,
                'domain_relevance': []
            }
    
    def _create_fallback_result(self) -> Dict[str, Any]:
        """Crée un résultat de fallback en cas d'échec total."""
        return {
            "summary": "",
            "event_type": "other",
            "companies_detected": [],
            "molecules_detected": [],
            "technologies_detected": [],
            "trademarks_detected": [],
            "indications_detected": [],
            "lai_relevance_score": 0,
            "anti_lai_detected": False,
            "pure_player_context": False
        }