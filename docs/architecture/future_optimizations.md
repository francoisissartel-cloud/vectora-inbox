# Optimisations et évolutions futures — Vectora Inbox V1

**Statut** : différées consciemment. À reprendre quand l'expérience MVP aura apporté des données concrètes ou quand le besoin sera réel.

Ce document est la **mémoire des décisions reportées**. Aucun élément ici ne doit être implémenté en MVP. Si quelque chose y est ajouté, c'est pour s'en souvenir, pas pour planifier.

---

## 1. Cache : invalidation intelligente par signature de filtre

**Idée** : invalider automatiquement les entrées du cache d'URL quand les fichiers canonical de filtres changent (plutôt que par TTL temporel ou rebuild manuel).

**Mécanisme proposé** :
- Calculer une `filter_signature = sha256(technology_scopes.yaml + exclusion_scopes.yaml + filter_rules.yaml)`
- Stocker cette signature dans chaque entrée du cache
- Au moment du lookup, comparer la signature actuelle avec celle du cache : si différente, ré-évaluer l'item au lieu de faire confiance au cache

**Bénéfice** : tu modifies `lai_keywords` pour ajouter un mot-clé, le cache est implicitement invalidé pour les rejets `no_lai_signal` sans avoir à `--rebuild-cache`.

**Pourquoi différé** : ajoute de la complexité. Pour le MVP, un `--rebuild-cache` manuel après modification des filtres est acceptable.

**Quand le reprendre** : si tu te retrouves à modifier les scopes/filtres souvent et à oublier de rebuild, ou si un autre client utilise le moteur et oublie aussi.

---

## 2. Multi-tagging d'écosystème suggéré par le LLM

**Idée** : pendant la normalisation, demander au LLM de proposer **des écosystèmes additionnels** au-delà de celui d'origine. Ex : un item ingéré comme LAI peut aussi concerner siRNA s'il en parle.

**Mécanisme proposé** :
- Étendre le prompt `generic_normalization` pour produire `suggested_ecosystems: [tech_sirna_ecosystem]` quand pertinent
- Stocker dans `curation.suggested_ecosystems`
- Une étape de revue (manuelle ou par seuil de confiance) ajoute le tag à l'item

**Pourquoi différé** : Frank n'aura qu'un seul écosystème (LAI) pendant des années. Dès qu'un 2e écosystème actif apparaîtra, ce sera utile.

**Quand le reprendre** : à l'introduction du 2e écosystème.

---

## 3. Re-curation lors d'un changement de prompt

**Idée** : quand le prompt de normalisation évolue (v2.0 → v2.1), pouvoir re-curer sélectivement les items déjà curés avec l'ancien prompt.

**Mécanisme proposé** :
- Chaque item curated stocke `curation.prompt_version`
- Commande `python re_curate.py --since 2026-01-01` ou `--prompt-version-below 2.1`
- Le script re-met les items concernés en `pending`, le pipeline les retraite

**Pourquoi différé** : aucun item curated n'existe aujourd'hui. La décision (datalake homogène vs hétérogène) sera plus simple avec une première expérience pratique.

**Quand le reprendre** : à la première vraie évolution du prompt après la mise en production du curated.

---

## 4. Parallélisation de l'ingestion par source

**Idée** : l'orchestrateur peut traiter plusieurs sources en parallèle (`--parallel 3`).

**Pourquoi différé** : en MVP avec 6-10 sources, le séquentiel est suffisant et plus facile à débugger. Économise complexité du logging concurrent, locks d'écriture sur le datalake, gestion des erreurs partielles.

**Quand le reprendre** : si le run total dépasse 30 min et que c'est gênant. Probable si tu passes à 30+ sources.

---

## 5. Parallélisation des appels LLM

**Idée** : normaliser plusieurs items en parallèle (`max_workers > 1`).

**Pourquoi différé** : le code V2 supporte déjà ça (`max_workers` paramètre), mais en MVP local, séquentiel = simple + moins de risque de throttling Anthropic.

**Quand le reprendre** : si le run de normalisation dépasse 1h. Avec 100 items à 3s par item, ça tient sous 5 min en séquentiel.

---

## 6. Migration vers AWS / S3

**Idée** : remplacer le backend de stockage local par S3 pour industrialisation.

**Mécanisme proposé** :
- L'abstraction `datalake/storage.py` a une interface unique
- Une implémentation `LocalStorage` (MVP) et une `S3Storage` (futur)
- Switch via config : `storage.backend: local | s3`

**Pourquoi différé** : Frank veut tout local-first pour le MVP. La migration S3 viendra avec l'industrialisation.

**Quand le reprendre** : quand le datalake fait > 1 Go ou quand plusieurs personnes doivent y accéder.

---

## 7. Backend vectoriel pour RAG

**Idée** : produire des embeddings sur les items curated et les stocker dans une base vectorielle (Chroma, Qdrant, pgvector) pour le futur RAG.

**Pourquoi différé** : le RAG n'est pas un consommateur immédiat. Quand il existera, c'est lui qui décidera des chunks et embeddings, pas le datalake.

**Quand le reprendre** : à la conception du consommateur RAG.

---

## 8. Politique de retention / purge

**Idée** : purger automatiquement les items de plus de N années.

**Pourquoi différé** : Frank a explicitement dit "on ne purge rien". Volume non problématique avant longtemps.

**Quand le reprendre** : si > 100k items et coût de stockage perçu.

---

## 9. Scheduler automatique (cron / APScheduler / Airflow)

**Idée** : lancer les ingestions automatiquement selon `schedule.frequency` du client_config.

**Pourquoi différé** : la section `schedule` est déjà dans le client_config mais inactive. Frank veut tout manuel en MVP pour ne pas s'endormir avec un truc qui tourne.

**Quand le reprendre** : quand le moteur a 2-3 mois de fiabilité prouvée et qu'attendre devient pénible.

---

## 10. Dashboard HTML pour stats

**Idée** : transformer les `stats/reports/*.md` en pages HTML interactives avec graphiques.

**Pourquoi différé** : MD lisible à l'œil suffit en MVP. Un graphique d'évolution ne change pas la décision opérationnelle.

**Quand le reprendre** : quand le datalake aura des consommateurs externes qui veulent un dashboard.

---

## ✅ 11. Repo hors OneDrive — RÉALISÉ (Sprint 003, 2026-04-26)

**Idée** : déplacer le repo de `C:\Users\franc\OneDrive\Bureau\vectora-inbox - claude\` vers `C:\Users\franc\dev\vectora-inbox-claude\` pour éviter les conflits de sync OneDrive avec Git (lock `.git/index.lock`, fichiers fantômes, latences).

**Pourquoi différé initialement** : techniquement non bloquant en Phase 2 (ménage/audit). Devenu bloquant pour le Niveau 1 (développement actif).

**Réalisé** : Sprint 003 — déménagement effectué par Frank depuis VS Code/PowerShell, Cowork remonté sur le nouveau chemin. Voir `docs/runbooks/move_repo_out_of_onedrive.md`.

---

*Mis à jour à chaque fois qu'une décision est consciemment reportée.*
