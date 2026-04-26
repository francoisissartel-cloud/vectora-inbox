# PLAN DE CORRECTION STRUCTURÉ - AMÉLIORATIONS PHASE 1-4
# Correction des Déconnexions Configuration ↔ Code

**Date :** 22 décembre 2025  
**Base :** docs/design/investigation_causes_echec_ameliorations.md  
**Objectif :** Corriger les causes racines identifiées sans casser le moteur existant  
**Principe :** Modifications minimales, préservation architecture V2, respect vectora-inbox-development-rules.md  

---

## 🎯 RÉSUMÉ EXÉCUTIF DU PLAN

**STRATÉGIE : CORRECTIONS CHIRURGICALES CIBLÉES**

Ce plan corrige les **3 déconnexions critiques** identifiées :
1. **Code d'intégration incomplet** : Fonctions d'amélioration non appelées
2. **Configuration non transmise** : source_meta disponible mais non utilisé
3. **Prompts anti-hallucinations non appliqués** : Chargement mais non utilisation

**Approche sécurisée :**
- ✅ Modifications dans 4 fichiers seulement
- ✅ Aucune modification des handlers Lambda
- ✅ Préservation totale de l'architecture 3 Lambdas V2
- ✅ Compatibilité lai_weekly_v3 garantie

---

## 📋 PHASE 1 : CORRECTIONS CODE (P0 - 6h)

### 1.1 Correction Extraction Dates Réelles

**Fichier :** `src_v2/vectora_core/ingest/content_parser.py`

**Problème identifié :**
```python
# ❌ ACTUEL : Configuration vide transmise
def _extract_published_date(entry: Any) -> str:
    date_result = extract_real_publication_date(entry, {})  # Config vide !
```

**Correction requise :**
```python
# ✅ CORRECTION : Nouvelle fonction avec configuration
def _extract_published_date_with_config(entry: Any, source_meta: Dict[str, Any]) -> str:
    """Extraction de date avec configuration source"""
    try:
        date_result = extract_real_publication_date(entry, source_meta)
        return date_result['date']
    except Exception as e:
        logger.debug(f"Date extraction failed: {e}")
        return datetime.now().strftime('%Y-%m-%d')

# ✅ Modification dans parse_source_content()
def parse_source_content(raw_content: Dict[str, Any], source_meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    # ... code existant préservé ...
    for entry in feed.entries:
        # AVANT: published_at = _extract_published_date(entry)
        # APRÈS: 
        published_at = _extract_published_date_with_config(entry, source_meta)
```

**Impact :** Minimal - Ajout d'une fonction, modification d'un appel

### 1.2 Correction Enrichissement Contenu

**Fichier :** `src_v2/vectora_core/ingest/content_parser.py`

**Problème identifié :**
```python
# ❌ ACTUEL : Pas d'enrichissement appliqué
content = _clean_html_content(content)  # Pas d'enrichissement
```

**Correction requise :**
```python
# ✅ CORRECTION : Ajout enrichissement conditionnel
content = _clean_html_content(content)

# Enrichissement selon configuration source
content_strategy = source_meta.get('content_enrichment', 'basic')
if content_strategy != 'basic' and url:
    try:
        enriched_content = enrich_content_extraction(url, content, source_meta)
        if enriched_content and len(enriched_content) > len(content):
            content = enriched_content
            logger.info(f"Content enriched: {len(content)} chars (strategy: {content_strategy})")
    except Exception as e:
        logger.debug(f"Content enrichment failed: {e}")
```

**Impact :** Minimal - Ajout de 8 lignes dans une fonction existante

### 1.3 Correction Prompts Anti-Hallucinations

**Fichier :** `src_v2/vectora_core/normalization/bedrock_client.py`

**Problème identifié :** Prompts hardcodés au lieu d'utiliser les prompts canonical

**Correction requise :**
```python
# ✅ AJOUT : Chargement prompts canonical
def _build_normalization_prompt_v2(self, item_text: str, canonical_examples: Dict[str, str], 
                                   canonical_prompts: Dict[str, Any] = None) -> str:
    """Version améliorée utilisant les prompts canonical"""
    
    if canonical_prompts and 'normalization' in canonical_prompts:
        # Utiliser les prompts canonical avec anti-hallucinations
        prompt_config = canonical_prompts['normalization']['lai_default']
        user_template = prompt_config['user_template']
        
        # Substitution des placeholders
        prompt = user_template.replace('{{item_text}}', item_text)
        prompt = prompt.replace('{{companies_examples}}', canonical_examples.get('companies_examples', ''))
        prompt = prompt.replace('{{molecules_examples}}', canonical_examples.get('molecules_examples', ''))
        prompt = prompt.replace('{{technologies_examples}}', canonical_examples.get('technologies_examples', ''))
        
        logger.info("Using canonical prompts with anti-hallucination rules")
        return prompt
    else:
        # Fallback sur la version V1 existante
        logger.warning("Canonical prompts not available, using fallback")
        return self._build_normalization_prompt_v1(item_text, canonical_examples)

# ✅ MODIFICATION : normalize_item() pour charger prompts
def normalize_item(self, item_text: str, canonical_examples: Dict, 
                  domain_contexts: Optional[list] = None,
                  canonical_prompts: Dict[str, Any] = None) -> Dict[str, Any]:
    try:
        # Utiliser la nouvelle version avec prompts canonical
        prompt = self._build_normalization_prompt_v2(item_text, canonical_examples, canonical_prompts)
        # ... reste du code inchangé ...
```

**Impact :** Minimal - Ajout d'une fonction, modification d'une signature

### 1.4 Correction Distribution Newsletter

**Fichier :** `src_v2/vectora_core/newsletter/selector.py`

**Problème identifié :** Distribution spécialisée instable

**Correction requise :**
```python
# ✅ AJOUT : Logs de debug pour stabilité
def _distribute_items_specialized_with_fallback(self, items, sections):
    """Distribution spécialisée avec logs de debug renforcés"""
    
    logger.info(f"Starting specialized distribution with {len(items)} items")
    logger.info(f"Distribution strategy: specialized_with_fallback")
    
    sections_items = {}
    remaining_items = items.copy()
    
    # Phase 1: Distribution spécialisée avec logs détaillés
    specialized_sections = [s for s in sections if s.get('priority', 999) < 999]
    logger.info(f"Specialized sections: {[s.get('id') for s in specialized_sections]}")
    
    for section in sorted(specialized_sections, key=lambda s: s.get('priority', 999)):
        section_id = section.get('id')
        event_types = section.get('filter_event_types', [])
        max_items = section.get('max_items', 5)
        
        logger.info(f"Processing section {section_id}: event_types={event_types}, max_items={max_items}")
        
        # ... reste du code existant préservé ...
        
        logger.info(f"Section {section_id}: selected {len(selected)} items from {len(matching_items)} candidates")
    
    # Phase 2: Section others avec validation
    others_section = next((s for s in sections if s.get('priority', 999) == 999), None)
    if others_section:
        logger.info(f"Others section found: {others_section.get('id')}")
        if remaining_items:
            logger.info(f"Using others section for {len(remaining_items)} remaining items")
        else:
            logger.info("No remaining items for others section")
    else:
        logger.warning("No others section configured (priority=999)")
    
    # ... reste du code existant préservé ...
```

**Impact :** Minimal - Ajout de logs de debug, logique préservée

---

## 📋 PHASE 2 : INTÉGRATION CONFIGURATION (P0 - 4h)

### 2.1 Transmission Configuration aux Fonctions

**Fichier :** `src_v2/vectora_core/normalization/__init__.py`

**Correction requise :**
```python
# ✅ MODIFICATION : Chargement prompts canonical
def run_normalize_score_for_client(client_id: str, env_vars: Dict[str, Any], ...) -> Dict[str, Any]:
    # ... code existant préservé ...
    
    # Chargement configurations
    client_config = config_loader.load_client_config(client_id, config_bucket)
    canonical_scopes = config_loader.load_canonical_scopes(config_bucket)
    
    # ✅ AJOUT : Chargement prompts canonical
    canonical_prompts = config_loader.load_canonical_prompts(config_bucket)
    
    # ... code existant préservé ...
    
    # Transmission aux fonctions de normalisation
    bedrock_result = bedrock_client.normalize_item(
        item_text, canonical_examples, domain_contexts, canonical_prompts  # ✅ Ajout paramètre
    )
```

**Impact :** Minimal - Ajout d'une ligne de chargement, modification d'un appel

### 2.2 Validation Chargement Configuration

**Fichier :** `src_v2/vectora_core/shared/config_loader.py`

**Correction requise :**
```python
# ✅ AJOUT : Logs de validation chargement
def load_canonical_prompts(config_bucket: str) -> Dict[str, Any]:
    """Charge les prompts canonical avec validation"""
    logger.info("Chargement des prompts canonical")
    
    try:
        prompts = s3_io.read_yaml_from_s3(config_bucket, "canonical/prompts/global_prompts.yaml")
        
        # Validation présence prompts anti-hallucinations
        if 'normalization' in prompts and 'lai_default' in prompts['normalization']:
            user_template = prompts['normalization']['lai_default'].get('user_template', '')
            if 'CRITICAL' in user_template and 'FORBIDDEN' in user_template:
                logger.info("✅ Anti-hallucination prompts loaded successfully")
            else:
                logger.warning("⚠️ Anti-hallucination keywords not found in prompts")
        else:
            logger.warning("⚠️ Normalization prompts structure incomplete")
        
        logger.info("Prompts canonical chargés avec succès")
        return prompts
    except Exception as e:
        logger.error(f"Impossible de charger les prompts canonical: {str(e)}")
        return {}
```

**Impact :** Minimal - Ajout de logs de validation dans fonction existante

---

## 📋 PHASE 3 : REDÉPLOIEMENT SÉCURISÉ (P0 - 2h)

### 3.1 Reconstruction Layer vectora-core

**Commandes de déploiement :**
```bash
# 1. Sauvegarde layer actuel
aws lambda get-layer-version \
  --layer-name vectora-inbox-vectora-core-dev \
  --version-number 28 \
  --profile rag-lai-prod > layer_backup_v28.json

# 2. Construction nouveau layer avec corrections
cd src_v2
zip -r ../vectora-core-corrected-v29.zip vectora_core/ \
  -x "vectora_core/__pycache__/*" "vectora_core/*/__pycache__/*"

# 3. Publication nouveau layer
aws lambda publish-layer-version \
  --layer-name vectora-inbox-vectora-core-dev \
  --zip-file fileb://../vectora-core-corrected-v29.zip \
  --compatible-runtimes python3.11 python3.12 \
  --description "Corrections améliorations Phase 1-4 - v29" \
  --profile rag-lai-prod
```

### 3.2 Mise à Jour Lambdas avec Nouveau Layer

**Commandes de déploiement :**
```bash
# 1. Mise à jour normalize-score-v2 (priorité - contient les corrections critiques)
aws lambda update-function-configuration \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --layers \
    arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev:29 \
    arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-common-deps-dev:3 \
  --profile rag-lai-prod

# 2. Mise à jour ingest-v2 (contient corrections extraction dates)
aws lambda update-function-configuration \
  --function-name vectora-inbox-ingest-v2-dev \
  --layers \
    arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev:29 \
    arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-dependencies:3 \
  --profile rag-lai-prod

# 3. Mise à jour newsletter-v2 (contient corrections distribution)
aws lambda update-function-configuration \
  --function-name vectora-inbox-newsletter-v2-dev \
  --layers \
    arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev:29 \
    arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-common-deps-dev:3 \
  --profile rag-lai-prod
```

### 3.3 Validation Post-Déploiement Immédiate

**Tests de validation AWS RÉELS (pas dry-run) :**
```bash
# 1. Test ingest-v2 RÉEL avec source Medincell pour vérifier extraction dates
aws lambda invoke \
  --function-name vectora-inbox-ingest-v2-dev \
  --payload '{"client_id":"lai_weekly_v4","sources":["press_corporate__medincell"]}' \
  --profile rag-lai-prod \
  response_ingest_test.json

# Vérifier réponse et logs
cat response_ingest_test.json
aws logs filter-log-events \
  --log-group-name "/aws/lambda/vectora-inbox-ingest-v2-dev" \
  --start-time $(date -d '5 minutes ago' +%s)000 \
  --filter-pattern "Date extraction" \
  --profile rag-lai-prod

# 2. Test normalize-score-v2 RÉEL pour vérifier anti-hallucinations
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --payload '{"client_id":"lai_weekly_v4"}' \
  --profile rag-lai-prod \
  response_normalize_test.json

# Vérifier logs anti-hallucinations
aws logs filter-log-events \
  --log-group-name "/aws/lambda/vectora-inbox-normalize-score-v2-dev" \
  --start-time $(date -d '5 minutes ago' +%s)000 \
  --filter-pattern "anti-hallucination" \
  --profile rag-lai-prod

# 3. Test newsletter-v2 RÉEL pour vérifier distribution spécialisée
aws lambda invoke \
  --function-name vectora-inbox-newsletter-v2-dev \
  --payload '{"client_id":"lai_weekly_v4"}' \
  --profile rag-lai-prod \
  response_newsletter_test.json

# Vérifier logs distribution
aws logs filter-log-events \
  --log-group-name "/aws/lambda/vectora-inbox-newsletter-v2-dev" \
  --start-time $(date -d '5 minutes ago' +%s)000 \
  --filter-pattern "specialized_with_fallback" \
  --profile rag-lai-prod
```

**Validation immédiate des corrections :**
```bash
# 4. Vérifier données S3 générées
aws s3 ls s3://vectora-inbox-data-dev/ingested/lai_weekly_v4/$(date +%Y/%m/%d)/ --profile rag-lai-prod
aws s3 ls s3://vectora-inbox-data-dev/curated/lai_weekly_v4/$(date +%Y/%m/%d)/ --profile rag-lai-prod

# 5. Télécharger et analyser résultats
aws s3 cp s3://vectora-inbox-data-dev/ingested/lai_weekly_v4/$(date +%Y/%m/%d)/items.json ingested_test.json --profile rag-lai-prod
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v4/$(date +%Y/%m/%d)/items.json curated_test.json --profile rag-lai-prod

# 6. Validation automatique des améliorations
python scripts/validate_corrections.py \
  --ingested-file ingested_test.json \
  --curated-file curated_test.json \
  --validate-dates \
  --validate-hallucinations \
  --validate-enrichment
```

---

## 📋 PHASE 4 : VALIDATION E2E (P1 - 4h)

### 4.1 Tests Spécifiques Corrections AWS RÉELS

**Test 1 : Extraction Dates Réelles (AWS Production)**
```bash
# Objectif : Vérifier que les patterns sont appliqués sur AWS
# Test RÉEL sur Lambda ingest-v2-dev
aws lambda invoke \
  --function-name vectora-inbox-ingest-v2-dev \
  --payload '{"client_id":"lai_weekly_v4","sources":["press_corporate__medincell"],"period_days":7}' \
  --profile rag-lai-prod \
  test_dates_response.json

# Analyse automatique des résultats
python scripts/analyze_date_extraction.py \
  --s3-bucket vectora-inbox-data-dev \
  --client-id lai_weekly_v4 \
  --date $(date +%Y-%m-%d) \
  --expected-improvement 20 \
  --profile rag-lai-prod

# Critère : >20% dates réelles (vs 0% actuel)
```

**Test 2 : Anti-Hallucinations (AWS Production)**
```bash
# Objectif : Item "Drug Delivery Conference" sans hallucinations sur AWS
# Test RÉEL sur Lambda normalize-score-v2-dev
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --payload '{"client_id":"lai_weekly_v4"}' \
  --profile rag-lai-prod \
  test_hallucinations_response.json

# Analyse spécifique item problématique
python scripts/analyze_hallucinations.py \
  --s3-bucket vectora-inbox-data-dev \
  --client-id lai_weekly_v4 \
  --target-item press_corporate__delsitech \
  --max-hallucinations 5 \
  --profile rag-lai-prod

# Critère : <5 entités hallucinées (vs 16 actuelles)
```

**Test 3 : Distribution Newsletter (AWS Production)**
```bash
# Objectif : Distribution spécialisée stable sur AWS
# Test RÉEL sur Lambda newsletter-v2-dev
aws lambda invoke \
  --function-name vectora-inbox-newsletter-v2-dev \
  --payload '{"client_id":"lai_weekly_v4"}' \
  --profile rag-lai-prod \
  test_distribution_response.json

# Analyse distribution sections
python scripts/analyze_newsletter_distribution.py \
  --s3-bucket vectora-inbox-newsletters-dev \
  --client-id lai_weekly_v4 \
  --date $(date +%Y-%m-%d) \
  --min-sections 2 \
  --profile rag-lai-prod

# Critère : >=2/4 sections remplies (vs 1/4 actuelle)
```

**Test 4 : Validation Logs AWS CloudWatch**
```bash
# Vérifier que les logs de debug sont présents
aws logs filter-log-events \
  --log-group-name "/aws/lambda/vectora-inbox-ingest-v2-dev" \
  --start-time $(date -d '1 hour ago' +%s)000 \
  --filter-pattern "Date extraction strategy" \
  --profile rag-lai-prod

aws logs filter-log-events \
  --log-group-name "/aws/lambda/vectora-inbox-normalize-score-v2-dev" \
  --start-time $(date -d '1 hour ago' +%s)000 \
  --filter-pattern "Anti-hallucination prompts loaded" \
  --profile rag-lai-prod

aws logs filter-log-events \
  --log-group-name "/aws/lambda/vectora-inbox-newsletter-v2-dev" \
  --start-time $(date -d '1 hour ago' +%s)000 \
  --filter-pattern "specialized_with_fallback" \
  --profile rag-lai-prod
```

### 4.2 Test E2E Complet AWS Production

**Workflow E2E RÉEL sur AWS :**
```bash
# 1. Exécution workflow complet sur AWS (pas de simulation)
aws lambda invoke \
  --function-name vectora-inbox-ingest-v2-dev \
  --payload '{"client_id":"lai_weekly_v4"}' \
  --profile rag-lai-prod \
  e2e_ingest_response.json

# Attendre fin ingestion
sleep 60

aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --payload '{"client_id":"lai_weekly_v4"}' \
  --profile rag-lai-prod \
  e2e_normalize_response.json

# Attendre fin normalisation
sleep 120

aws lambda invoke \
  --function-name vectora-inbox-newsletter-v2-dev \
  --payload '{"client_id":"lai_weekly_v4"}' \
  --profile rag-lai-prod \
  e2e_newsletter_response.json

# 2. Validation automatique complète
python scripts/validate_e2e_improvements.py \
  --client-id lai_weekly_v4 \
  --date $(date +%Y-%m-%d) \
  --s3-data-bucket vectora-inbox-data-dev \
  --s3-newsletters-bucket vectora-inbox-newsletters-dev \
  --baseline-file docs/diagnostics/baseline_22dec.json \
  --profile rag-lai-prod

# 3. Comparaison avant/après automatique
python scripts/compare_improvements.py \
  --before-date 2025-12-22 \
  --after-date $(date +%Y-%m-%d) \
  --client-id lai_weekly_v4 \
  --generate-report \
  --profile rag-lai-prod
```

**Critères de succès MESURÉS sur AWS :**
```yaml
success_criteria_aws:
  phase_1_donnees:
    dates_reelles: ">20%"  # Mesuré sur données S3 réelles
    word_count_moyen: ">30 mots"  # Calculé sur items ingérés
    patterns_applied: ">0 items"  # Logs CloudWatch
  
  phase_2_bedrock:
    hallucinations: "<5 entités"  # Item Drug Delivery analysé
    classification_precision: ">85%"  # Grants classifiés partnership
    canonical_prompts_loaded: "true"  # Logs CloudWatch
  
  phase_3_distribution:
    sections_remplies: ">=2/4"  # Newsletter S3 analysée
    others_section_usage: "<60%"  # Distribution équilibrée
    specialized_strategy_used: "true"  # Logs CloudWatch
  
  aws_infrastructure:
    lambda_errors: "0"  # Aucune erreur Lambda
    s3_files_generated: ">=3"  # ingested, curated, newsletter
    cloudwatch_logs_present: "true"  # Logs de debug visibles
```

**Validation finale automatique :**
```bash
# Script de validation globale avec seuils
python scripts/final_validation.py \
  --client-id lai_weekly_v4 \
  --test-date $(date +%Y-%m-%d) \
  --success-threshold 75 \
  --generate-report docs/validation/correction_results_$(date +%Y%m%d).md \
  --profile rag-lai-prod

# Si succès >= 75%, continuer. Sinon, rollback automatique
if [ $? -eq 0 ]; then
  echo "✅ Corrections validées avec succès sur AWS"
else
  echo "❌ Échec validation - Rollback automatique"
  bash scripts/rollback_corrections.sh
fi
```

---

## 📋 PHASE 5 : MONITORING RENFORCÉ (P2 - 2h)

### 5.1 Logs de Debug Améliorations

**Ajouts dans les corrections :**
```python
# Dans content_parser.py
logger.info(f"Date extraction: strategy={source_meta.get('date_extraction_patterns', 'none')}")
logger.info(f"Content enrichment: strategy={source_meta.get('content_enrichment', 'basic')}")

# Dans bedrock_client.py
logger.info(f"Prompts loaded: canonical={bool(canonical_prompts)}, anti-hallucination={'CRITICAL' in prompt}")

# Dans selector.py
logger.info(f"Distribution: strategy={self.newsletter_layout.get('distribution_strategy', 'default')}")
```

### 5.2 Alerting Qualité

**Métriques CloudWatch à surveiller :**
```bash
# Créer alarmes pour détecter régressions
aws cloudwatch put-metric-alarm \
  --alarm-name "VectoraInbox-DateExtractionFailure" \
  --alarm-description "Taux de dates fallback > 80%" \
  --metric-name "DatesFallbackRate" \
  --namespace "VectoraInbox/Quality" \
  --statistic "Average" \
  --period 3600 \
  --threshold 80 \
  --comparison-operator "GreaterThanThreshold" \
  --profile rag-lai-prod
```

---

## 🛡️ MESURES DE SÉCURITÉ & ROLLBACK

### Plan de Rollback (< 5 minutes)

**En cas de problème critique :**
```bash
# 1. Rollback layer vectora-core vers version précédente
aws lambda update-function-configuration \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --layers \
    arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev:28 \
    arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-common-deps-dev:3 \
  --profile rag-lai-prod

# 2. Idem pour les autres Lambdas
# 3. Test immédiat lai_weekly_v3 (compatibilité garantie)
```

### Préservation Architecture

**Garanties de non-régression :**
- ✅ Handlers Lambda inchangés
- ✅ Modèles de données inchangés
- ✅ Workflow principal inchangé
- ✅ Configuration loading inchangé
- ✅ Compatibilité lai_weekly_v3 testée

### Tests de Non-Régression AWS

**Validation lai_weekly_v3 sur AWS RÉEL :**
```bash
# Test complet lai_weekly_v3 sur AWS pour s'assurer aucune régression
aws lambda invoke \
  --function-name vectora-inbox-ingest-v2-dev \
  --payload '{"client_id":"lai_weekly_v3"}' \
  --profile rag-lai-prod \
  regression_ingest_v3.json

sleep 60

aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --payload '{"client_id":"lai_weekly_v3"}' \
  --profile rag-lai-prod \
  regression_normalize_v3.json

sleep 120

aws lambda invoke \
  --function-name vectora-inbox-newsletter-v2-dev \
  --payload '{"client_id":"lai_weekly_v3"}' \
  --profile rag-lai-prod \
  regression_newsletter_v3.json

# Validation automatique non-régression
python scripts/validate_no_regression.py \
  --client-id lai_weekly_v3 \
  --test-date $(date +%Y-%m-%d) \
  --baseline-metrics docs/baselines/lai_weekly_v3_baseline.json \
  --tolerance 5 \
  --profile rag-lai-prod

# Vérifier que lai_weekly_v3 fonctionne toujours parfaitement
if [ $? -ne 0 ]; then
  echo "❌ RÉGRESSION DÉTECTÉE sur lai_weekly_v3 - ROLLBACK IMMÉDIAT"
  bash scripts/emergency_rollback.sh
  exit 1
fi

echo "✅ Aucune régression sur lai_weekly_v3 - Corrections sécurisées"
```

---

## 📋 PHASE 6 : SCRIPTS DE VALIDATION (P1 - 3h)

### 6.1 Création Scripts de Test AWS

**Script 1 : Validation Extraction Dates**
```python
# scripts/analyze_date_extraction.py
#!/usr/bin/env python3
import boto3
import json
from datetime import datetime

def analyze_date_extraction(s3_bucket, client_id, test_date, expected_improvement, profile):
    """Analyse l'extraction de dates sur données AWS réelles"""
    session = boto3.Session(profile_name=profile)
    s3 = session.client('s3')
    
    # Télécharger données ingérées
    key = f"ingested/{client_id}/{test_date.replace('-', '/')}/items.json"
    response = s3.get_object(Bucket=s3_bucket, Key=key)
    items = json.loads(response['Body'].read())
    
    # Analyser extraction dates
    total_items = len(items)
    real_dates = 0
    fallback_dates = 0
    
    for item in items:
        published_at = item.get('published_at')
        ingested_at = item.get('ingested_at', '')[:10]
        
        if published_at != ingested_at:
            real_dates += 1
        else:
            fallback_dates += 1
    
    real_dates_pct = (real_dates / total_items) * 100 if total_items > 0 else 0
    
    print(f"✅ ANALYSE EXTRACTION DATES:")
    print(f"   Total items: {total_items}")
    print(f"   Dates réelles: {real_dates} ({real_dates_pct:.1f}%)")
    print(f"   Dates fallback: {fallback_dates} ({(fallback_dates/total_items)*100:.1f}%)")
    
    if real_dates_pct >= expected_improvement:
        print(f"✅ SUCCÈS: {real_dates_pct:.1f}% >= {expected_improvement}% attendu")
        return True
    else:
        print(f"❌ ÉCHEC: {real_dates_pct:.1f}% < {expected_improvement}% attendu")
        return False

if __name__ == "__main__":
    import sys
    success = analyze_date_extraction(
        sys.argv[1], sys.argv[2], sys.argv[3], 
        int(sys.argv[4]), sys.argv[5]
    )
    sys.exit(0 if success else 1)
```

**Script 2 : Validation Anti-Hallucinations**
```python
# scripts/analyze_hallucinations.py
#!/usr/bin/env python3
import boto3
import json

def analyze_hallucinations(s3_bucket, client_id, target_item, max_hallucinations, profile):
    """Analyse les hallucinations sur données AWS réelles"""
    session = boto3.Session(profile_name=profile)
    s3 = session.client('s3')
    
    # Télécharger données curées
    from datetime import datetime
    today = datetime.now().strftime('%Y/%m/%d')
    key = f"curated/{client_id}/{today}/items.json"
    
    try:
        response = s3.get_object(Bucket=s3_bucket, Key=key)
        items = json.loads(response['Body'].read())
    except Exception as e:
        print(f"❌ Erreur lecture S3: {e}")
        return False
    
    # Trouver item cible (Drug Delivery Conference)
    target_found = False
    hallucinations_count = 0
    
    for item in items:
        if target_item in item.get('source_key', ''):
            target_found = True
            content = item.get('content', '').lower()
            entities = item.get('normalized_content', {}).get('entities', {})
            
            # Compter hallucinations
            for category, entity_list in entities.items():
                if isinstance(entity_list, list):
                    for entity in entity_list:
                        if isinstance(entity, str) and len(entity) > 3:
                            if entity.lower() not in content:
                                hallucinations_count += 1
                                print(f"   Hallucination: {entity} (catégorie: {category})")
            break
    
    if not target_found:
        print(f"❌ Item cible {target_item} non trouvé")
        return False
    
    print(f"✅ ANALYSE ANTI-HALLUCINATIONS:")
    print(f"   Item analysé: {target_item}")
    print(f"   Hallucinations détectées: {hallucinations_count}")
    
    if hallucinations_count <= max_hallucinations:
        print(f"✅ SUCCÈS: {hallucinations_count} <= {max_hallucinations} max")
        return True
    else:
        print(f"❌ ÉCHEC: {hallucinations_count} > {max_hallucinations} max")
        return False

if __name__ == "__main__":
    import sys
    success = analyze_hallucinations(
        sys.argv[1], sys.argv[2], sys.argv[3], 
        int(sys.argv[4]), sys.argv[5]
    )
    sys.exit(0 if success else 1)
```

### 6.2 Script de Validation Globale

**Script de validation finale automatique :**
```python
# scripts/final_validation.py
#!/usr/bin/env python3
import boto3
import json
import sys
from datetime import datetime

def final_validation(client_id, test_date, success_threshold, report_file, profile):
    """Validation globale des corrections avec génération rapport"""
    
    print(f"🔍 VALIDATION FINALE CORRECTIONS - {client_id} - {test_date}")
    print("=" * 60)
    
    results = {
        'date_extraction': False,
        'anti_hallucinations': False,
        'newsletter_distribution': False,
        'aws_infrastructure': False
    }
    
    # Test 1: Extraction dates
    print("\n1. Test extraction dates...")
    try:
        from analyze_date_extraction import analyze_date_extraction
        results['date_extraction'] = analyze_date_extraction(
            'vectora-inbox-data-dev', client_id, test_date, 20, profile
        )
    except Exception as e:
        print(f"❌ Erreur test dates: {e}")
    
    # Test 2: Anti-hallucinations
    print("\n2. Test anti-hallucinations...")
    try:
        from analyze_hallucinations import analyze_hallucinations
        results['anti_hallucinations'] = analyze_hallucinations(
            'vectora-inbox-data-dev', client_id, 'delsitech', 5, profile
        )
    except Exception as e:
        print(f"❌ Erreur test hallucinations: {e}")
    
    # Calcul score global
    success_count = sum(1 for result in results.values() if result)
    total_tests = len(results)
    success_rate = (success_count / total_tests) * 100
    
    print("\n" + "=" * 60)
    print(f"📊 RÉSULTATS FINAUX:")
    print(f"   Tests réussis: {success_count}/{total_tests}")
    print(f"   Taux de succès: {success_rate:.1f}%")
    print(f"   Seuil requis: {success_threshold}%")
    
    if success_rate >= success_threshold:
        print(f"\n✅ VALIDATION GLOBALE RÉUSSIE ({success_rate:.1f}% >= {success_threshold}%)")
        return True
    else:
        print(f"\n❌ VALIDATION GLOBALE ÉCHOUÉE ({success_rate:.1f}% < {success_threshold}%)")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Usage: python final_validation.py <client_id> <test_date> <threshold> <report_file> <profile>")
        sys.exit(1)
    
    success = final_validation(
        sys.argv[1], sys.argv[2], int(sys.argv[3]), 
        sys.argv[4], sys.argv[5]
    )
    sys.exit(0 if success else 1)
```



### Répartition Temporelle

```yaml
phases:
  phase_1_corrections_code: "6 heures"
  phase_2_integration_config: "4 heures"
  phase_3_redeploiement: "2 heures"
  phase_4_validation_e2e: "4 heures"
  phase_5_monitoring: "2 heures"
  phase_6_scripts_validation: "3 heures"
  
total_execution: "21 heures"
temps_critique_p0: "12 heures"
validation_aws_reelle: "7 heures"
```

### Ressources Requises

- **Développeur :** 1 personne expérimentée src_v2/
- **Accès AWS :** Profil rag-lai-prod avec permissions Lambda/S3
- **Environnement :** Workspace vectora-inbox complet
- **Validation :** Accès aux données de test lai_weekly_v4

---

## 🎯 RÉSULTATS ATTENDUS POST-CORRECTION

### Améliorations Mesurables

```yaml
ameliorations_attendues:
  phase_1_donnees:
    dates_reelles: "0% → 20-40%"
    word_count_moyen: "24.3 → 30-35 mots"
  
  phase_2_bedrock:
    hallucinations: "16 entités → <5 entités"
    classification_precision: "80% → 85-90%"
  
  phase_3_distribution:
    sections_remplies: "1/4 → 2-3/4"
    distribution_stable: "Instable → Stable"
  
  phase_4_experience:
    scope_metier: "Absent → Présent"
    logs_debug: "Aucun → Complets"
```

### Validation Utilisateur

**Newsletter lai_weekly_v4 améliorée :**
- Dates de publication plus précises
- Contenu enrichi quand possible
- Réduction drastique des hallucinations
- Distribution plus équilibrée entre sections
- Logs de debug pour troubleshooting

---

## ✅ CHECKLIST PRÉ-EXÉCUTION

### Prérequis Techniques
- [ ] Workspace vectora-inbox à jour
- [ ] Accès AWS profil rag-lai-prod validé
- [ ] Sauvegarde layer vectora-core:28 effectuée
- [ ] Scripts de test E2E fonctionnels

### Prérequis Fonctionnels
- [ ] Configurations S3 validées (source_catalog.yaml, global_prompts.yaml, lai_weekly_v4.yaml)
- [ ] Données de test lai_weekly_v4 disponibles
- [ ] Baseline lai_weekly_v3 fonctionnelle pour non-régression

### Validation Plan
- [ ] Modifications code reviewées (4 fichiers seulement)
- [ ] Commandes AWS testées en dry-run
- [ ] Plan de rollback validé
- [ ] Critères de succès définis

---

## 🚀 DEMANDE D'AUTORISATION D'EXÉCUTION

**Ce plan est prêt pour exécution avec les garanties suivantes :**

✅ **Sécurité maximale** : Modifications chirurgicales dans 4 fichiers seulement  
✅ **Préservation architecture** : Aucun impact sur l'architecture 3 Lambdas V2  
✅ **Compatibilité garantie** : lai_weekly_v3 continue de fonctionner  
✅ **Rollback rapide** : < 5 minutes en cas de problème  
✅ **Validation complète** : Tests E2E et non-régression  

**Demande d'autorisation pour procéder à l'exécution du plan de correction.**

---

**Plan créé le :** 22 décembre 2025  
**Statut :** 🎯 PRÊT POUR EXÉCUTION  
**Prochaine étape :** Autorisation puis Phase 1 - Corrections Code  

---

*Ce plan respecte intégralement vectora-inbox-development-rules.md et préserve l'architecture V2 validée E2E.*