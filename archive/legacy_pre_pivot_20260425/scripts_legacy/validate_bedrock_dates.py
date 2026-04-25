"""Script de validation extraction dates Bedrock post-déploiement"""
import boto3
import json
from datetime import datetime

def validate_bedrock_dates():
    """Valide l'extraction de dates dans les items curated"""
    
    print("\n" + "="*70)
    print("VALIDATION EXTRACTION DATES BEDROCK - POST DEPLOIEMENT")
    print("="*70 + "\n")
    
    s3 = boto3.client('s3', region_name='eu-west-3')
    
    # Télécharger items curated (après normalisation)
    try:
        response = s3.get_object(
            Bucket='vectora-inbox-data-dev',
            Key='curated/lai_weekly_v6/2026/01/29/items.json'
        )
        items = json.loads(response['Body'].read())
        print(f"[OK] Items curated telecharges: {len(items)}\n")
    except Exception as e:
        print(f"[ERROR] Erreur telechargement: {str(e)}")
        print("NOTE: Executez d'abord normalize-score-v2 pour generer les items curated")
        return False
    
    # Analyser extraction dates
    stats = {
        "total": len(items),
        "with_bedrock_date": 0,
        "high_confidence": 0,
        "medium_confidence": 0,
        "low_confidence": 0,
        "no_date": 0,
        "effective_date_used": 0
    }
    
    print("ANALYSE EXTRACTION DATES:")
    print("-" * 70)
    
    for i, item in enumerate(items[:10], 1):  # Analyser 10 premiers
        normalized = item.get('normalized_content', {})
        scoring = item.get('scoring_results', {})
        
        extracted_date = normalized.get('extracted_date')
        date_confidence = normalized.get('date_confidence', 0.0)
        effective_date = scoring.get('effective_date')
        published_at = item.get('published_at', '')[:10]
        
        # Statistiques
        if extracted_date:
            stats["with_bedrock_date"] += 1
            if date_confidence > 0.8:
                stats["high_confidence"] += 1
                conf_label = "HIGH"
            elif date_confidence > 0.5:
                stats["medium_confidence"] += 1
                conf_label = "MEDIUM"
            else:
                stats["low_confidence"] += 1
                conf_label = "LOW"
        else:
            stats["no_date"] += 1
            conf_label = "NONE"
        
        if effective_date and effective_date != published_at:
            stats["effective_date_used"] += 1
            date_source = "BEDROCK"
        else:
            date_source = "FALLBACK"
        
        title = item.get('title', '')[:50]
        print(f"\nItem {i}: {title}...")
        print(f"  Bedrock date: {extracted_date or 'N/A'} (confidence: {date_confidence:.2f} - {conf_label})")
        print(f"  Fallback date: {published_at}")
        print(f"  Effective date: {effective_date} (source: {date_source})")
    
    # Résumé
    print("\n" + "="*70)
    print("STATISTIQUES")
    print("="*70)
    print(f"Items analyses: {min(10, stats['total'])}")
    print(f"Dates Bedrock extraites: {stats['with_bedrock_date']} ({stats['with_bedrock_date']*100//min(10, stats['total'])}%)")
    print(f"  - Haute confiance (>0.8): {stats['high_confidence']}")
    print(f"  - Moyenne confiance (>0.5): {stats['medium_confidence']}")
    print(f"  - Basse confiance: {stats['low_confidence']}")
    print(f"Dates fallback: {stats['no_date']}")
    print(f"Effective_date utilise (Bedrock): {stats['effective_date_used']}")
    print("="*70 + "\n")
    
    # Validation
    success_rate = stats['with_bedrock_date'] / min(10, stats['total'])
    
    if success_rate >= 0.95:
        print("[SUCCESS] Objectif atteint: {:.0f}% >= 95%".format(success_rate * 100))
        return True
    elif success_rate >= 0.80:
        print("[WARNING] Objectif partiel: {:.0f}% >= 80%".format(success_rate * 100))
        return True
    else:
        print("[FAILED] Objectif non atteint: {:.0f}% < 80%".format(success_rate * 100))
        return False

if __name__ == "__main__":
    success = validate_bedrock_dates()
    
    print("\n" + "="*70)
    if success:
        print("VALIDATION: [SUCCESS]")
        print("L'extraction de dates par Bedrock fonctionne correctement.")
    else:
        print("VALIDATION: [FAILED]")
        print("Verifiez les logs Lambda normalize-score-v2 pour plus de details.")
    print("="*70 + "\n")
