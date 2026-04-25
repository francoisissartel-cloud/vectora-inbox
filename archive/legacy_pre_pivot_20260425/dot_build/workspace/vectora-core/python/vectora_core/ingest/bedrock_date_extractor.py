"""
Extraction de dates via AWS Bedrock - Solution universelle
"""

import json
import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def extract_publication_date_with_bedrock(
    bedrock_client,
    title: str,
    content: str,
    url: str,
    model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"
) -> Dict[str, any]:
    """
    Extrait la date de publication via Bedrock.
    
    Utilise Claude Haiku (rapide et pas cher: $0.25/1M tokens)
    
    Returns:
        {
            'date': '2026-02-06',
            'confidence': 0.95,
            'source': 'bedrock_extraction'
        }
    """
    
    prompt = f"""Extract the publication date from this news article.

Title: {title[:200]}
Content: {content[:500]}
URL: {url}

Return ONLY a JSON object with this exact format:
{{
    "date": "YYYY-MM-DD",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
}}

Rules:
- Look for publication date, NOT event date
- Common patterns: "Feb 6, 2026", "2026-02-06", "6 February 2026"
- Check title first, then content, then URL
- If no date found, return {{"date": null, "confidence": 0.0}}
- Today is {datetime.now().strftime('%Y-%m-%d')}
"""

    try:
        response = bedrock_client.invoke_model(
            modelId=model_id,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 200,
                "temperature": 0,
                "messages": [{
                    "role": "user",
                    "content": prompt
                }]
            })
        )
        
        result = json.loads(response['body'].read())
        content_text = result['content'][0]['text']
        
        # Parser la réponse JSON
        date_info = json.loads(content_text)
        
        if date_info.get('date'):
            logger.info(f"Bedrock extracted date: {date_info['date']} (confidence: {date_info.get('confidence', 0)})")
            return {
                'date': date_info['date'],
                'confidence': date_info.get('confidence', 0.9),
                'source': 'bedrock_extraction',
                'reasoning': date_info.get('reasoning', '')
            }
        
        return {
            'date': None,
            'confidence': 0.0,
            'source': 'bedrock_no_date'
        }
        
    except Exception as e:
        logger.error(f"Bedrock date extraction failed: {e}")
        return {
            'date': None,
            'confidence': 0.0,
            'source': 'bedrock_error'
        }


def extract_date_hybrid(
    bedrock_client,
    item_data,
    source_config: Dict,
    raw_html: Optional[str] = None
) -> Dict[str, any]:
    """
    Approche hybride: cascade classique + Bedrock en fallback intelligent.
    
    Cascade:
    1. RSS pubDate (gratuit, rapide) - 90% fiabilité
    2. HTML meta tags (gratuit, rapide) - 85% fiabilité  
    3. Bedrock extraction (payant, lent) - 95% fiabilité
    4. Fallback date ingestion - 0% fiabilité
    """
    
    # Niveau 1: RSS pubDate (déjà implémenté)
    if hasattr(item_data, 'published_parsed') and item_data.published_parsed:
        try:
            dt = datetime(*item_data.published_parsed[:6])
            return {
                'date': dt.strftime('%Y-%m-%d'),
                'confidence': 0.90,
                'source': 'rss_parsed'
            }
        except:
            pass
    
    # Niveau 2: HTML meta tags (déjà implémenté)
    if raw_html:
        from vectora_core.ingest.content_parser import try_structured_metadata
        date = try_structured_metadata(raw_html)
        if date:
            return {
                'date': date,
                'confidence': 0.85,
                'source': 'html_metadata'
            }
    
    # Niveau 3: Bedrock extraction (NOUVEAU - pour cas difficiles)
    title = str(getattr(item_data, 'title', '')) if hasattr(item_data, 'title') else str(item_data.get('title', ''))
    content = str(getattr(item_data, 'content', '')) if hasattr(item_data, 'content') else str(item_data.get('content', ''))
    url = getattr(item_data, 'link', '') if hasattr(item_data, 'link') else item_data.get('url', '')
    
    # Seulement si on a du contenu à analyser
    if title or content:
        bedrock_result = extract_publication_date_with_bedrock(
            bedrock_client,
            title,
            content,
            url
        )
        
        if bedrock_result['date']:
            return bedrock_result
    
    # Niveau 4: Fallback
    return {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'confidence': 0.0,
        'source': 'ingestion_fallback'
    }
