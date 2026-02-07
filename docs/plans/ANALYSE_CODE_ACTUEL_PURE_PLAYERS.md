# Analyse: Filtrage Pure Players - Code Actuel

**Date**: 2026-02-06  
**Conclusion**: ✅ **Le code actuel fait DÉJÀ ce qui est demandé**

---

## 🎯 Objectif Demandé

> "Toutes les news des pure_players doivent être ingérées, à l'exception du bruit évident. Donc pas de filtre LAI keywords pour les pure_players."

---

## ✅ Code Actuel: CONFORME

### Fichier: `src_v2/vectora_core/ingest/ingestion_profiles.py`

**Fonction `_apply_corporate_profile` (lignes 120-150)**:

```python
if is_lai_pure_player:
    logger.info(f"Pure player LAI détecté : {company_id} - ingestion large avec exclusions minimales")
    
    for item in items:
        # Exclure SEULEMENT le bruit évident
        if _contains_exclusion_keywords(text):
            excluded_count += 1
            continue
        
        # ✅ PAS de filtrage LAI keywords
        filtered_items.append(item)
    
    return filtered_items
else:
    # Entreprise non-LAI : filtrage LAI keywords
    return _filter_by_lai_keywords(items, source_key)
```

### Comportement Actuel

| Type Source | Pure Player? | Filtrage LAI Keywords | Exclusions Bruit |
|-------------|--------------|----------------------|------------------|
| Corporate | ✅ Oui | ❌ NON | ✅ OUI |
| Corporate | ❌ Non | ✅ OUI | ✅ OUI |
| Presse | N/A | ✅ OUI | ✅ OUI |

**✅ C'est exactement ce qui est demandé!**

---

## 🔍 Alors Pourquoi v24 → v25 a Perdu des Items?

### Hypothèses à Vérifier

#### 1. **Exclusions Trop Larges** (114 keywords)
Les exclusions dans `exclusion_scopes.yaml` filtrent peut-être trop:
- `hr_content`: 60+ termes
- `financial_generic`: 30+ termes
- `event_generic`: 20+ termes

**Action**: Analyser les logs pour voir quels items sont exclus et pourquoi.

#### 2. **Sources RSS Ont Moins de Contenu**
Les flux RSS eux-mêmes ont peut-être moins d'items ce jour-là.

**Action**: Comparer le nombre d'items parsés (avant filtrage) v24 vs v25.

#### 3. **Filtre Temporel Trop Strict**
Items exclus car considérés "trop anciens" (period_days).

**Action**: Vérifier les dates de publication des items exclus.

#### 4. **Problème d'Extraction de Contenu**
Le content enrichment (PDFs, HTML) peut échouer et produire du contenu vide.

**Action**: Vérifier les logs d'extraction de contenu.

---

## 📋 Plan d'Action Diagnostic

### Étape 1: Analyser les Logs Lambda v25

```bash
# Télécharger les logs du dernier run v25
aws logs tail /aws/lambda/vectora-inbox-ingest-v2-dev \
  --since 2h \
  --filter-pattern "lai_weekly_v25" \
  --profile rag-lai-prod \
  --region eu-west-3 > .tmp/logs_v25.txt

# Chercher les patterns clés:
grep "Pure player LAI détecté" .tmp/logs_v25.txt
grep "MATCH EXCLUSION" .tmp/logs_v25.txt
grep "items conservés" .tmp/logs_v25.txt
```

### Étape 2: Comparer Items Parsés vs Filtrés

```bash
# Ajouter logs dans content_parser.py pour voir items parsés AVANT filtrage
# Comparer:
# - Items parsés (avant profil)
# - Items après profil
# - Items après filtre temporel
```

### Étape 3: Tester avec Exclusions Réduites

Créer une version minimaliste de `exclusion_scopes.yaml`:

```yaml
# Version minimaliste pour test
hr_content:
  - job opening
  - we are hiring
  - career opportunity

financial_generic:
  - quarterly earnings
  - financial results
  - interim report

event_generic:
  - conference announcement
  - save the date
```

Upload et tester:
```bash
aws s3 cp canonical/scopes/exclusion_scopes_minimal.yaml \
  s3://vectora-inbox-config-dev/canonical/scopes/exclusion_scopes.yaml \
  --profile rag-lai-prod
```

---

## 🎯 Recommandation Finale

### Option 1: Diagnostic Approfondi (Recommandé)
1. Analyser les logs v25 pour identifier où les items sont perdus
2. Comparer avec v24 pour voir la différence
3. Ajuster les exclusions si nécessaire

### Option 2: Réduire les Exclusions (Quick Win)
Tester avec une liste d'exclusions minimaliste (10-15 termes au lieu de 114).

### Option 3: Mode Broad Temporaire
Forcer `ingestion_mode: "broad"` pour v26 et comparer:

```bash
python scripts/invoke/invoke_ingest_v2.py \
  --client-id lai_weekly_v26 \
  --env dev \
  --ingestion-mode broad
```

---

## 📝 Conclusion

**Le code actuel est CORRECT et fait ce qui est demandé.**

Le problème v24 → v25 vient probablement:
1. Des **exclusions trop larges** (114 keywords)
2. Ou des **sources RSS avec moins de contenu**
3. Ou du **filtre temporel trop strict**

**Pas besoin de modifier le code pour le filtrage LAI keywords des pure players.**

---

**Statut**: ✅ Code conforme, diagnostic nécessaire  
**Action**: Analyser logs v25 pour identifier cause réelle  
**Temps estimé**: 15 minutes diagnostic
