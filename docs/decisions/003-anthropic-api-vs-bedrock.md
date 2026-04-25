# 003 — Choix du LLM : Anthropic API direct vs Bedrock vs OpenAI vs LLM local

**Statut** : ✅ Accepté
**Date** : 24/04/2026
**Contexte** : Phase 1 cadrage — choix du fournisseur de LLM pour la normalisation

## Le problème

Vectora Inbox V2 utilisait **Bedrock** (Anthropic Claude via AWS) pour la normalisation des items. Avec la décision local-first (ADR 002), on doit choisir comment appeler le LLM depuis le PC de Frank, sans dépendance AWS.

## Options envisagées

| Option | Description | Avantage clé | Inconvénient clé |
|---|---|---|---|
| 1. Bedrock (boto3) | Garder Bedrock via credentials AWS sur le PC | Continuité avec V2 | Toujours dépendant d'AWS |
| 2. **Anthropic API direct** | Clé `sk-ant-...` depuis console.anthropic.com | Même modèle Claude que Bedrock | Dépendance à anthropic.com |
| 3. OpenAI API | Modèles GPT-4o | API très bien documentée | Adapter le prompt (Claude vs GPT) |
| 4. LLM local (Ollama + Llama 3 / Mistral) | 100% local, gratuit | Aucune dépendance cloud | Qualité inférieure, machine sollicitée |

## La décision

**Option 2 — Anthropic API direct (Claude Sonnet par défaut).**

## Justification

- **Même modèle que V2 (Claude Sonnet)** : le prompt `generic_normalization` V2 fonctionne tel quel, sans réécriture
- **Pas d'infra AWS** : cohérent avec ADR 002 (local-first)
- **Setup en 2 minutes** : créer une clé API depuis console.anthropic.com, la mettre dans `.env`
- **Code Python simple** : `bedrock_client.py` V2 → `anthropic_client.py` V1 = traduction directe (mêmes paramètres : modèle, max_tokens, temperature, retry/backoff)
- **Coût raisonnable** : ~0.025 USD par item LAI normalisé en Sonnet, ~0.009 USD en Haiku. MVP attendu < 5 USD/mois.
- **Portabilité préservée** : abstraction `LLMClient` permet de basculer vers Bedrock un jour si besoin

L'option 4 (LLM local) a été écartée pour le MVP : qualité d'extraction d'entités structurées (companies, molecules, technologies) significativement inférieure avec les modèles open-source actuels. À reconsidérer dans 1-2 ans.

L'option 3 (OpenAI) n'apporte pas de valeur supplémentaire vs Anthropic et nécessite une réécriture du prompt.

## Conséquences

- Frank doit créer une clé Anthropic API et la mettre dans `.env`
- La clé est gitignored (jamais commitée)
- Le coût LLM est tracé item par item (`curation_log.jsonl`)
- Un plafond de coût par run est défini dans `client_config` (`cost_cap_usd_per_run`)
- L'abstraction `normalize/llm/base.py` (interface `LLMClient`) prévoit un futur `BedrockClient` ou autre
- Le mode "économise" (bascule vers Haiku) est prévu via paramètre client_config

## Documents liés

- ADR 002 (Local-first) — origine
- `docs/architecture/datalake_v1_design.md` §6.4 (étape Normalize), §12 (structure du code)
- `CLAUDE.md` §15 (gestion des coûts)
- `.env.example` (template variables Anthropic)
- `future_optimizations.md` §6 (migration AWS un jour)
