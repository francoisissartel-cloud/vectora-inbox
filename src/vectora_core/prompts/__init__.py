"""
Module de gestion des prompts canonicalisés pour Vectora Inbox.

Ce module fournit le PromptLoader pour charger les prompts depuis
les fichiers YAML canonicalisés avec cache et fallback.
"""

from .loader import PromptLoader, get_prompt_loader

__all__ = ['PromptLoader', 'get_prompt_loader']