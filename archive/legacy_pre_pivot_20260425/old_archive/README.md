# Archive - Code Legacy

**Statut** : Code historique - Référence uniquement

## Contenu

- `_src/` : Architecture legacy (avant migration V2)
  - Contient 180MB+ de dépendances tierces
  - Violations des règles d'hygiène
  - Stubs et contournements non conformes

## Règles

- ❌ **NE JAMAIS utiliser ce code pour développement**
- ✅ Conservé uniquement pour référence historique
- ✅ Peut être supprimé si plus nécessaire
- ⚠️ Si besoin de référence, consulter `src_v2/` à la place

## Architecture de Référence

**Utiliser** : `src_v2/` (Architecture 3 Lambdas V2 validée)

**Ne pas utiliser** : `archive/_src/` (Architecture legacy obsolète)
