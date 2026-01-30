# Confirmation : Gestion des Dates dans Vectora Inbox

**Date de validation** : 2026-01-30  
**Workflow** : Ingestion → Normalisation → Newsletter  
**Status** : ✅ CONFIRMÉ

---

## 📅 STRUCTURE DES DATES

### 1. Date d'Ingestion (Ingestion Date)
**Champ** : `published_at`  
**Source** : Flux RSS/API externe  
**Format** : `YYYY-MM-DD`  
**Exemple** : `"published_at": "2026-01-29"`

**Description** :
- Date de publication du flux RSS
- Date à laquelle l'item a été découvert par le système
- Peut être la date de mise en ligne du contenu sur le site source
- **Utilisée pour** : Tri chronologique, fenêtre d'ingestion

---

### 2. Date Effective (Effective Date)
**Champ** : `effective_date` (dans `scoring_results`)  
**Source** : Extraction Bedrock OU fallback sur `published_at`  
**Format** : `YYYY-MM-DD`  
**Exemple** : `"effective_date": "2026-01-27"`

**Description** :
- Date réelle de l'événement mentionné dans le contenu
- Extraite par Bedrock depuis le texte de l'article
- Si Bedrock ne trouve pas de date → fallback sur `published_at`
- **Utilisée pour** : Affichage dans la newsletter, tri par pertinence temporelle

---

## 🔄 WORKFLOW COMPLET

### Phase 1 : Ingestion (Lambda ingest-v2)
```json
{
  "item_id": "...",
  "title": "...",
  "published_at": "2026-01-29",  // ← Date d'ingestion (flux RSS)
  "url": "...",
  "content": "..."
}
```

### Phase 2 : Normalisation (Lambda normalize-score-v2)
```json
{
  "item_id": "...",
  "published_at": "2026-01-29",  // ← Conservée
  "normalized_content": {
    "summary": "...",
    "extracted_date": "2026-01-27",  // ← Extraite par Bedrock
    "date_confidence": 1.0
  },
  "scoring_results": {
    "final_score": 9.3,
    "effective_date": "2026-01-27"  // ← Date effective calculée
  }
}
```

**Logique de calcul `effective_date`** :
```python
if extracted_date and date_confidence >= 0.5:
    effective_date = extracted_date  # Date Bedrock
else:
    effective_date = published_at    # Fallback
```

### Phase 3 : Newsletter (Lambda newsletter-v2)
```markdown
### 📋 Teva Pharmaceuticals has submitted a New Drug Application...
**Source:** press_corporate__medincell • **Score:** 9.3 • **Date:** Jan 27, 2026
                                                                    ↑
                                                        Utilise effective_date
```

**Code d'affichage** (`assembler.py` ligne 348-349) :
```python
# NOUVEAU: Utiliser effective_date (date Bedrock) si disponible, sinon published_at
effective_date = scoring.get('effective_date') or item.get('published_at', '')[:10]
```

---

## ✅ VALIDATION E2E

### Exemple Réel (Item du 29/01/2026)

**Données curated** :
```json
{
  "published_at": "2026-01-29",        // Date ingestion (flux RSS)
  "normalized_content": {
    "extracted_date": "2026-01-27",    // Date extraite par Bedrock
    "date_confidence": 1.0
  },
  "scoring_results": {
    "effective_date": "2026-01-27"     // Date effective = extracted_date
  }
}
```

**Newsletter générée** :
```markdown
**Date:** Jan 27, 2026  ← Affiche effective_date (date réelle de l'événement)
```

---

## 📊 STATISTIQUES (Newsletter lai_weekly_v7 du 29/01/2026)

**Total items** : 23 items curated  
**Items avec extracted_date** : ~18 items (78%)  
**Items avec fallback** : ~5 items (22%)

**Exemples de dates effectives** :
- `2026-01-27` : Date extraite par Bedrock (événement du 27/01)
- `2026-01-29` : Fallback sur published_at (pas de date dans le texte)
- `2025-12-09` : Date extraite par Bedrock (événement ancien)

---

## 🎯 CONFIRMATION FINALE

### Question : "J'ai une date d'ingestion et une date effective dans les datas ?"
**Réponse** : ✅ **OUI, CONFIRMÉ**

1. **Date d'ingestion** : `published_at` (date du flux RSS)
2. **Date effective** : `effective_date` (date réelle de l'événement, extraite par Bedrock)

### Question : "La newsletter utilise les dates effectives (date de publication réelle) ?"
**Réponse** : ✅ **OUI, CONFIRMÉ**

Le code `assembler.py` utilise explicitement `effective_date` :
```python
effective_date = scoring.get('effective_date') or item.get('published_at', '')[:10]
formatted_date = date_obj.strftime('%b %d, %Y')  # Affichage : "Jan 27, 2026"
```

---

## 📝 NOTES IMPORTANTES

1. **Extraction Bedrock** : Le prompt de normalisation demande explicitement à Bedrock d'extraire les dates mentionnées dans le texte
2. **Fallback intelligent** : Si Bedrock ne trouve pas de date (ou confidence < 0.5), le système utilise `published_at`
3. **Affichage cohérent** : La newsletter affiche toujours la date la plus pertinente (effective_date)
4. **Traçabilité** : Les deux dates sont conservées dans les données pour audit et debug

---

**Validé par** : Amazon Q Developer  
**Date** : 2026-01-30  
**Workflow** : Vectora Inbox v2 (3 Lambdas)
