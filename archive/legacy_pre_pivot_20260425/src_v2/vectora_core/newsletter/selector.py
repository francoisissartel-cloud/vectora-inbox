"""
Module selector - Sélection déterministe et intelligente des items
Version 2.0 - Politique de sélection simplifiée et sécurisée
"""
import logging
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

class NewsletterSelector:
    """Sélecteur d'items pour newsletter avec politique intelligente"""
    
    def __init__(self, client_config):
        self.client_config = client_config
        self.selection_config = client_config.get('newsletter_selection', {})
        self.newsletter_layout = client_config.get('newsletter_layout', {})
        self.critical_event_types = self.selection_config.get('critical_event_types', [])
        self.max_items_total = self.selection_config.get('max_items_total', 15)
    
    def select_items(self, curated_items):
        """Point d'entrée principal pour la sélection"""
        logger.info(f"Starting selection from {len(curated_items)} curated items")
        
        # Étape 1: Filtrage par matching
        matched_items = self._filter_by_matching(curated_items)
        logger.info(f"After matching filter: {len(matched_items)} items")
        
        # Étape 2: Déduplication
        deduplicated_items = self._deduplicate_items(matched_items)
        logger.info(f"After deduplication: {len(deduplicated_items)} items")
        
        # Étape 3: Distribution en sections
        sections_items = self._distribute_to_sections(deduplicated_items)
        
        # Étape 4: Trimming intelligent si nécessaire
        final_selection = self._apply_intelligent_trimming(sections_items)
        
        # Génération des métadonnées
        metadata = self._generate_selection_metadata(
            curated_items, matched_items, deduplicated_items, final_selection
        )
        
        return {
            'sections': final_selection,
            'metadata': metadata
        }
    
    def _filter_by_matching(self, items):
        """Filtre strict : seuls les items matchés passent"""
        return [
            item for item in items 
            if item.get('matching_results', {}).get('matched_domains', [])
        ]
    
    def _deduplicate_items(self, items):
        """Déduplication intelligente avec priorité aux événements critiques"""
        groups = defaultdict(list)
        
        for item in items:
            signature = self._create_item_signature(item)
            groups[signature].append(item)
        
        deduplicated = []
        for group_items in groups.values():
            if len(group_items) == 1:
                deduplicated.append(group_items[0])
            else:
                best_item = self._select_best_duplicate(group_items)
                deduplicated.append(best_item)
                logger.debug(f"Deduplicated group of {len(group_items)} items")
        
        return deduplicated
    
    def _create_item_signature(self, item):
        """Crée une signature pour détecter les doublons - Version corrigée"""
        import hashlib
        
        normalized = item.get('normalized_content', {})
        entities = normalized.get('entities', {})
        
        # Utiliser molécules et indications pour différencier (vs trademarks)
        companies = tuple(sorted(entities.get('companies', [])))
        molecules = tuple(sorted(entities.get('molecules', [])))
        indications = tuple(sorted(entities.get('indications', [])))
        event_type = normalized.get('event_classification', {}).get('primary_type', '')
        
        # Hash du titre pour différencier news distinctes
        title = item.get('title', '')
        title_hash = hashlib.md5(title.encode('utf-8')).hexdigest()[:8]
        
        return (companies, molecules, indications, event_type, title_hash)
    
    def _select_best_duplicate(self, duplicates):
        """Sélectionne le meilleur item parmi les doublons"""
        # 1. Priorité aux événements critiques
        critical_items = [item for item in duplicates if self._is_critical_event(item)]
        if critical_items:
            return max(critical_items, key=lambda x: self._get_effective_score(x))
        
        # 2. Sinon, meilleur effective_score
        return max(duplicates, key=lambda x: self._get_effective_score(x))
    
    def _is_critical_event(self, item):
        """Vérifie si un item est un événement critique"""
        event_type = item.get('normalized_content', {}).get('event_classification', {}).get('primary_type', '')
        return event_type in self.critical_event_types
    
    def _get_effective_score(self, item):
        """Calcule l'effective_score selon l'algorithme défini"""
        final_score = item.get('scoring_results', {}).get('final_score', 0)
        if final_score > 0:
            return final_score
        
        # REMOVED: Fallback to lai_relevance_score (deprecated)
        # Now only use final_score from scoring_results
        return 0
    
    def _distribute_to_sections(self, items):
        """Distribue les items selon la configuration des sections avec stratégie spécialisée"""
        sections = self.newsletter_layout.get('sections', [])
        distribution_strategy = self.newsletter_layout.get('distribution_strategy', 'default')
        
        if distribution_strategy == 'specialized_with_fallback':
            return self._distribute_items_specialized_with_fallback(items, sections)
        else:
            return self._distribute_items_default(items, sections)
    
    def _distribute_items_specialized_with_fallback(self, items, sections):
        """Distribution spécialisée avec logs de debug renforcés"""
        
        logger.info(f"Starting specialized distribution with {len(items)} items")
        logger.info(f"Distribution strategy: specialized_with_fallback")
        
        sections_items = {}
        remaining_items = items.copy()
        
        # Phase 1: Distribution dans sections spécialisées (priority < 999)
        specialized_sections = [s for s in sections if s.get('priority', 999) < 999]
        logger.info(f"Specialized sections: {[s.get('id') for s in specialized_sections]}")
        
        for section in sorted(specialized_sections, key=lambda s: s.get('priority', 999)):
            section_id = section.get('id')
            event_types = section.get('filter_event_types', [])
            max_items = section.get('max_items', 5)
            
            logger.info(f"Processing section {section_id}: event_types={event_types}, max_items={max_items}")
            
            # Matching par event_type
            matching_items = [
                item for item in remaining_items 
                if self._item_matches_section_event_type(item, event_types)
            ]
            
            # Tri par score ou date selon config
            sort_by = section.get('sort_by', 'score_desc')
            matching_items = self._sort_items(matching_items, sort_by)
            
            # Sélection
            selected = matching_items[:max_items]
            sections_items[section_id] = {
                'title': section.get('title', section_id),
                'items': selected
            }
            
            # Retirer les items sélectionnés
            remaining_items = [item for item in remaining_items if item not in selected]
            
            logger.info(f"Section {section_id}: selected {len(selected)} items from {len(matching_items)} candidates")
        
        # Phase 2: Filet de sécurité 'others' (priority = 999)
        others_section = next((s for s in sections if s.get('priority', 999) == 999), None)
        if others_section:
            logger.info(f"Others section found: {others_section.get('id')}")
            if remaining_items:
                logger.info(f"Using others section for {len(remaining_items)} remaining items")
                section_id = others_section.get('id')
                max_others = others_section.get('max_items', 8)
                
                # Tri par score pour 'others'
                remaining_items = self._sort_items(remaining_items, 'score_desc')
                selected_others = remaining_items[:max_others]
                
                sections_items[section_id] = {
                    'title': others_section.get('title', section_id),
                    'items': selected_others
                }
                
                # Log pour debugging
                logger.info(f"Section 'others' utilisée : {len(remaining_items)} items restants, "
                           f"{len(selected_others)} sélectionnés")
            else:
                logger.info("No remaining items for others section")
        else:
            logger.warning("No others section configured (priority=999)")
        
        # Monitoring de la qualité de distribution
        self._monitor_distribution_quality(sections_items)
        
        return sections_items
    
    def _distribute_items_default(self, items, sections):
        """Distribution par défaut (ancienne logique)"""
        sections_items = {}
        used_items = set()
        
        for section in sections:
            section_id = section.get('id')
            section_items = []
            
            for item in items:
                if item.get('item_id') in used_items:
                    continue
                
                if self._item_matches_section(item, section):
                    section_items.append(item)
            
            # Tri selon sort_by
            sort_by = section.get('sort_by', 'score_desc')
            section_items = self._sort_items(section_items, sort_by)
            
            # Application max_items
            max_items = section.get('max_items', 5)
            section_items = section_items[:max_items]
            
            # Marquer comme utilisés
            for item in section_items:
                used_items.add(item.get('item_id'))
            
            sections_items[section_id] = {
                'title': section.get('title', section_id),
                'items': section_items
            }
            
            logger.info(f"Section {section_id}: selected {len(section_items)} items")
        
        return sections_items
    
    def _item_matches_section_event_type(self, item, event_types):
        """Vérifie si un item correspond aux types d'événements d'une section"""
        if not event_types or '*' in event_types:
            return True
        
        event_type = item.get('normalized_content', {}).get('event_classification', {}).get('primary_type', '')
        return event_type in event_types
    
    def _monitor_distribution_quality(self, sections_items):
        """Monitoring de la qualité de distribution"""
        others_count = len(sections_items.get('others', {}).get('items', []))
        total_items = sum(len(section['items']) for section in sections_items.values())
        
        others_ratio = others_count / total_items if total_items > 0 else 0
        
        # Alert si trop d'items en 'others' (signe de problème de distribution)
        if others_ratio > 0.4:  # Plus de 40% en 'others'
            logger.warning(f"Distribution quality issue: {others_ratio:.1%} items in 'others' section")
        
        logger.info(f"Distribution quality: {others_count} items in 'others' ({others_ratio:.1%})")
        
        return {
            'others_count': others_count,
            'others_ratio': others_ratio,
            'distribution_quality': 'good' if others_ratio < 0.3 else 'needs_review'
        }
    
    def _item_matches_section(self, item, section):
        """Vérifie si un item correspond aux critères d'une section"""
        # Filtrage par domaine
        source_domains = section.get('source_domains', [])
        matched_domains = item.get('matching_results', {}).get('matched_domains', [])
        
        if not any(domain in source_domains for domain in matched_domains):
            return False
        
        # Filtrage par event_types si spécifié
        filter_event_types = section.get('filter_event_types')
        if filter_event_types:
            event_type = item.get('normalized_content', {}).get('event_classification', {}).get('primary_type', '')
            if event_type not in filter_event_types:
                return False
        
        return True
    
    def _sort_items(self, items, sort_by):
        """Tri des items selon le critère spécifié"""
        if sort_by == 'score_desc':
            return sorted(items, key=lambda x: self._get_effective_score(x), reverse=True)
        elif sort_by == 'date_desc':
            return sorted(items, key=lambda x: x.get('published_at', ''), reverse=True)
        else:
            return items
    
    def _apply_intelligent_trimming(self, sections_items):
        """Applique une politique de trimming intelligente"""
        total_items = sum(len(section['items']) for section in sections_items.values())
        
        if total_items <= self.max_items_total:
            return sections_items
        
        logger.warning(f"Trimming required: {total_items} > {self.max_items_total}")
        
        # 1. Identifier les événements critiques
        critical_items = []
        regular_items = []
        
        for section_id, section_data in sections_items.items():
            for item in section_data['items']:
                if self._is_critical_event(item):
                    critical_items.append((item, section_id))
                else:
                    regular_items.append((item, section_id))
        
        # 2. Toujours garder les événements critiques
        final_selection = critical_items[:]
        remaining_slots = self.max_items_total - len(critical_items)
        
        # 3. Compléter avec les meilleurs items réguliers
        regular_items.sort(key=lambda x: self._get_effective_score(x[0]), reverse=True)
        final_selection.extend(regular_items[:remaining_slots])
        
        # 4. Redistribuer dans les sections
        return self._redistribute_to_sections(final_selection)
    
    def _redistribute_to_sections(self, selected_items):
        """Redistribue les items sélectionnés dans leurs sections d'origine"""
        sections = self.newsletter_layout.get('sections', [])
        final_sections = {}
        
        # Initialiser les sections
        for section in sections:
            section_id = section.get('id')
            final_sections[section_id] = {
                'title': section.get('title', section_id),
                'items': []
            }
        
        # Redistribuer les items
        for item, original_section in selected_items:
            if original_section in final_sections:
                final_sections[original_section]['items'].append(item)
        
        return final_sections
    
    def _generate_selection_metadata(self, curated_items, matched_items, deduplicated_items, final_selection):
        """Génère les métadonnées de sélection"""
        total_selected = sum(len(section['items']) for section in final_selection.values())
        critical_events_count = sum(
            1 for section in final_selection.values() 
            for item in section['items'] 
            if self._is_critical_event(item)
        )
        
        section_fill_rates = {}
        for section_id, section_data in final_selection.items():
            section_config = next(
                (s for s in self.newsletter_layout.get('sections', []) if s.get('id') == section_id), 
                {}
            )
            max_items = section_config.get('max_items', 5)
            fill_rate = len(section_data['items']) / max_items if max_items > 0 else 0
            section_fill_rates[section_id] = round(fill_rate, 2)
        
        return {
            'total_items_processed': len(curated_items),
            'items_after_matching_filter': len(matched_items),
            'items_after_deduplication': len(deduplicated_items),
            'items_selected': total_selected,
            'trimming_applied': total_selected < len(deduplicated_items),
            'critical_events_preserved': critical_events_count,
            'matching_efficiency': round(total_selected / len(matched_items), 2) if matched_items else 0,
            'section_fill_rates': section_fill_rates,
            'selection_policy_version': '2.0'
        }

# Fonction de compatibilité avec l'ancienne API
def select_and_deduplicate_items(curated_items, client_config):
    """Point d'entrée de compatibilité avec l'ancienne API"""
    selector = NewsletterSelector(client_config)
    result = selector.select_items(curated_items)
    return result['sections']