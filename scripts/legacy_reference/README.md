# scripts/legacy_reference/

Code V2/V3 conservé comme **référence fonctionnelle** pour le développement V1 (Niveaux 1 et 2).

## Pourquoi c'est ici

Ces scripts viennent du moteur V2/V3 pré-pivot. Ils contiennent de la logique métier réutilisable :
- `ingestion/` : orchestration de l'ingestion locale (fetch, parse, filtrage)
- `discovery/` : exploration automatique d'une source candidate
- `validation/` : tests et garde-fous
- `src_v3/` : moteur d'ingestion complet V3 — modules `ingest/`, `shared/`, `warehouse/` (récupérés le 2026-04-25 depuis `C:\Users\franc\OneDrive\Bureau\vectora-inbox\src_v3\vectora_core\`, sans `s3_io.py` qui dépendait d'AWS)
- `canonical_v3/ingestion/` : fichiers de configuration YAML V3 manquants du repo actuel — `filter_rules_v3.yaml`, `source_configs_v3.yaml`, `ingestion_profiles_v3_ref.yaml` (récupérés le 2026-04-25 depuis `C:\Users\franc\OneDrive\Bureau\vectora-inbox\canonical\ingestion\`)

Ils ne doivent **pas être exécutés tels quels** : conventions V2/V3 (watch_domains, bedrock, etc.) qui contredisent le pivot V1 datalake/local-first.

## Comment les utiliser

Au moment du Niveau 1 (Fondations) puis Niveau 2 (Cœur) :
- Lire les algorithmes ici pour ne pas réinventer la roue
- Réécrire dans `src_vectora_inbox_v1/` en suivant le design canonique (`docs/architecture/datalake_v1_design.md`)
- Adapter le vocabulaire (`watch_domains` → `ecosystems`, `bedrock` → `anthropic`, etc.)

## Quand supprimer ce dossier

Une fois le Niveau 2 terminé et la nouvelle base stable, ce dossier pourra être archivé ou supprimé (la logique aura été reprise dans `src_vectora_inbox_v1/`).
