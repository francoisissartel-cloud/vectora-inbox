suite au test_e2e_v15_rapport_ingestion_normalisation_scoring.md, voila mes feedback. je veux que Q analyse mes retours et propose des stratégies pour améliorer vectora-inbox, en respect de Q context.


## ❌ PROBLÈMES IDENTIFIÉS

### 🔴 Problème 1: Perte Pure Player Company (CRITIQUE)

**Impact**: Régression majeure

**Preuve**:
- **0 companies** détectées dans normalized_content.entities.companies
- Affecte TOUS les items (Nanexa, MedinCell, Camurus, Delsitech)

**Conséquence**:
- Perte du boost pure_player_company (+25 points)
- Items pure players sous-scorés

**Action requise**: Corriger prompt generic_normalization.yaml

retour admin: il faut comprendre ce qui s'est passé entre les deux run et corriger ce probleme


### 🔴 Problème 2: Faux Négatif Quince (PERSISTANT)

**Impact**: Item pertinent rejeté

**Preuve**:
- Item: "Quince's steroid therapy for rare disease fails..."
- Titre complet contient: "once-monthly treatment"
- Score: **0** (rejeté)
- Reasoning: "No LAI signals detected"

**Cause**: "once-monthly" dans le titre NON détecté par normalisation

**Action requise**: Améliorer extraction dosing_intervals depuis titre

retour admin: ok avec action requise



### 🟡 Problème 3: Faux Positif Eli Lilly Manufacturing

**Impact**: Item non pertinent matché

**Preuve**:
- Item: "Lilly rounds out quartet of new US plants..."
- Score: **65** (matché)
- Signals: hybrid_company + "injectables and devices"

**Cause**: "injectables and devices" détecté comme signal LAI

**Action requise**: Ajouter aux exclusions manufacturing

retour admin: je ne comprends pas, il me semble qu'on avait validé que un hybrid player doit avoir des strong signalpour etre matché, ou sont les strong signals?



le système a rejeté 5. MedinCell malaria grant - Pas de signaux LAI; retour admin: cest un evenement important qui devrait matcher: medincell est un pure player lai, et un grant est un event de type funding, donc doit etre traité comme partnership. je veux capter tous les events partnerhsips des pure players meme sans signal LAI;



retour admin sur tous les autres items rejetés: pourquoi continue t on a ingerer ces items? je pensais avec plan_amelioration_canonical_e2e_v13_FINAL_2026-02-03.md que on allait améliorer la pahse ingestion en evitant d"ingerer du bruit évident, comme des sujets RH ou financials pures. 


