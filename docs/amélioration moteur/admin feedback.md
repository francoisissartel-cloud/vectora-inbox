phase ingestion:


⚠️ **Observation :** Date de publication identique pour tous les items
- Raison probable : Scraping de pages "news" sans date explicite
- Impact : Tri par date difficile en Phase 3
- Recommandation : Améliorer l'extraction de dates réelles


cest important d'avoir la date reelle de la news. il faut investiguer comment avoir cela.



### ⚠️ Items Courts (10/15)
**Impact :** Normalisation Bedrock difficile sur contenu limité
**Recommandation :** Surveiller la qualité des résumés générés

je veux comprendre comment avoir plus de contenu ingeré par news pour mieux nourrir bedrock pour les phases suivantes.


phase normalize: 

#### ❌ Surprises Négatives
- **Malaria Grant** : Score plus faible que prédit
  - Raison : Event type "financial_results" pénalisé vs "regulatory"

une grant est un financement qui doit etre traité comme un funding, comme une levee de fond et comme un deal, donc dans partnership. 

il faut extraire plus de contenu de la news dans la phase de normalization pour permettre a la lambda newsletter de decrire en 5 a 8 lignes la news: quoi ou comment quand.

attention aux dates de la news: il faut bien indiquer quand la news a été publiée: date réelle, pour que la lambda newsletter puisse indiquer la date relle de la news.


probleme hallucination a regler: 
### ⚠️ Item #6 : Drug Delivery Conference

#### Données Brutes
```
ID: press_corporate__delsitech_20251222_e3d7ad
Titre: "Partnership Opportunities in Drug Delivery 2025 Boston, October 27-28"
Contenu: 13 mots
Source: Delsitech
```

#### Transformation Normalisation
```json
{
  "summary": "The text is about an upcoming conference on partnership opportunities in drug delivery technologies, with a focus on long-acting injectable (LAI) technologies. No specific companies, drugs, or indications are mentioned.",
  "entities": {
    "technologies": ["Extended-Release Injectable", "Long-Acting Injectable", "Depot Injection", "Once-Monthly Injection", "Microspheres", "PLGA", "In-Situ Depot", "Hydrogel", "Subcutaneous Injection", "Intramuscular Injection"],
    "trademarks": ["UZEDY", "PharmaShell", "SiliaShell", "BEPO", "Aristada", "Abilify Maintena"]
  },
  "event_classification": {
    "primary_type": "other",
    "confidence": 0.8
  },
  "lai_relevance_score": 10
}
```

#### Évaluation Qualité
⚠️ **MOYEN - Matching discutable**
- ⚠️ **Pertinence LAI** : Conference générale, pas d'info spécifique
- ❌ **Normalisation** : Bedrock a "halluciné" les technologies LAI
- ❌ **Matching** : Score 0.9 trop élevé pour contenu générique
- ✅ **Scoring** : 3.1 approprié (pénalisé par event_type "other")
- ✅ **Newsletter** : Exclusion justifiée

#### Problème Identifié
- **Hallucination Bedrock** : Technologies et trademarks non présents dans le contenu original
- **Matching trop permissif** : Score 0.9 pour contenu générique
- **Recommandation** : Améliorer les prompts pour éviter les hallucinations

je veux une solution pour que cela ne se reproduise plus.

phase redaction newsletter:

### ⚠️ Observation Critique : Concentration en top_signals

**Problème identifié :** Tous les items sélectionnés sont dans top_signals
- **Cause :** Filtrage par event_types trop restrictif dans les autres sections
- **Impact :** Newsletter moins structurée, sections vides

je propose de désactiver la section top_signals, pour forcer la distribution dans les autres sections.


Ensuite je veux que le scope de cette newsletter soit ecrit quelque part ( tout a la fin) avec: quelles types de sources ingerées ( par exemple veille press biopharmaceutique (X sources), veille corporate du secteur des LAI (X companies), PubMed (si activé) etc. Je ne veux pas un détail source par source mais je veux donner une vue globale: quelles types de sources, combien approximativement de target dans ce type de source, quelle fenetre de periode de recherche). Je pense qu'on peut utiliser client_config pour aider le LMM a ecrire une ou deux lignes pour parler de cela a la fin de la newsletter.



ensuite une section qui est non alimentée ne doit pas etre rédigée par bedrock: si il n'y a rien dans une section il suffit de ne pas mentionner cette section pour un run donné. cest plus professionnel que decrire un titre de section avec du vide.


