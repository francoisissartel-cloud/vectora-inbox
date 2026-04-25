# scripts/legacy_reference/

Code V2/V3 conservé comme **référence fonctionnelle** pour le développement V1 (Niveaux 1 et 2).

## Pourquoi c'est ici

Ces scripts viennent du moteur V2/V3 pré-pivot. Ils contiennent de la logique métier réutilisable :
- `ingestion/` : orchestration de l'ingestion locale (fetch, parse, filtrage)
- `discovery/` : exploration automatique d'une source candidate
- `validation/` : tests et garde-fous

Ils ne doivent **pas être exécutés tels quels** : conventions V2/V3 (watch_domains, bedrock, etc.) qui contredisent le pivot V1 datalake/local-first.

## Comment les utiliser

Au moment du Niveau 1 (Fondations) puis Niveau 2 (Cœur) :
- Lire les algorithmes ici pour ne pas réinventer la roue
- Réécrire dans `src_vectora_inbox_v1/` en suivant le design canonique (`docs/architecture/datalake_v1_design.md`)
- Adapter le vocabulaire (`watch_domains` → `ecosystems`, `bedrock` → `anthropic`, etc.)

## Quand supprimer ce dossier

Une fois le Niveau 2 terminé et la nouvelle base stable, ce dossier pourra être archivé ou supprimé (la logique aura été reprise dans `src_vectora_inbox_v1/`).
