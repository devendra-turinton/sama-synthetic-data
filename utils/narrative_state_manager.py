import logging
import json
from typing import Dict, List, Any, Set
from datetime import datetime
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NarrativeStateManager:
    """
    Tracks what has happened to ensure progressive, non-repetitive narrative.
    This is the memory system that prevents duplication and creates logical story flow.
    """
    
    def __init__(self):
        # Event tracking
        self.event_history = []  # All previous events
        self.used_descriptions = set()  # Track description fingerprints to avoid repetition
        self.used_phrases = defaultdict(int)  # Track phrase usage count
        self.location_usage_count = {}  # How many times each location used
        self.unit_last_seen = {}  # Where units were last mentioned
        
        # Narrative state
        self.current_phase = None
        self.locations_contested = set()
        self.locations_captured_by_india = set()
        self.locations_captured_by_pakistan = set()
        self.major_events_occurred = []
        self.casualties_mentioned = []
        
        # Tactical state
        self.ongoing_battles = {}  # {location: {start_date, intensity, day_count}}
        self.recent_unit_activities = {}  # {unit_name: [recent activities]}
        
        # Statistics
        self.total_events_generated = 0
        self.events_by_type = defaultdict(int)
        self.events_by_location = defaultdict(int)
    
    def update_from_day(self, date: str, events: List[Dict[str, Any]]):
        """Update state after generating a day's events"""
        
        for event in events:
            # Track event
            self.event_history.append(event)
            self.total_events_generated += 1
            
            # Track event type
            event_type = event.get('event_type', 'unknown')
            self.events_by_type[event_type] += 1
            
            # Track location usage
            location = event.get('location_name', 'unknown')
            self.location_usage_count[location] = self.location_usage_count.get(location, 0) + 1
            self.events_by_location[location] += 1
            
            # Track description phrases (create fingerprint from first 50 chars)
            desc = event.get('description', '')
            if desc:
                fingerprint = desc[:50].lower().strip()
                self.used_descriptions.add(fingerprint)
                
                # Track 3-word phrases (trigrams)
                words = desc.lower().split()
                for i in range(len(words) - 2):
                    trigram = ' '.join(words[i:i+3])
                    self.used_phrases[trigram] += 1
            
            # Track unit movements
            actor = event.get('actor')
            if actor:
                if actor not in self.recent_unit_activities:
                    self.recent_unit_activities[actor] = []
                self.recent_unit_activities[actor].append({
                    'date': date,
                    'activity': event.get('event_type'),
                    'location': location,
                    'description_summary': desc[:100] if desc else ''
                })
                # Keep only last 5 activities per unit
                self.recent_unit_activities[actor] = self.recent_unit_activities[actor][-5:]
                
                # Track unit last known location
                self.unit_last_seen[actor] = {
                    'location': location,
                    'date': date,
                    'activity': event.get('event_type')
                }
            
            # Track battle status
            significance = event.get('significance', 'routine')
            if significance in ['important', 'critical'] and location != 'unknown':
                if location not in self.ongoing_battles:
                    self.mark_battle_started(location, date, significance)
                else:
                    self.update_battle_status(location, date)
        
        logger.debug(f"Updated narrative state for {date}: {len(events)} events processed")
    
    def get_progressive_context(self, current_date: str, day_number: int) -> Dict[str, Any]:
        """Build context about what has happened so far"""
        
        # Recent history (last 3 days = 18 events)
        recent_events = self.event_history[-18:] if len(self.event_history) > 18 else self.event_history
        
        # Major developments summary
        major_developments = []
        if day_number > 1:
            # Get unique recent locations
            recent_locations = [e.get('location_name') for e in recent_events]
            recent_unique = list(dict.fromkeys(recent_locations))  # Preserve order, remove dupes
            if recent_unique:
                major_developments.append(f"Recent activity concentrated in: {', '.join(recent_unique[:5])}")
            
            # Get recent event types
            recent_event_types = [e.get('event_type') for e in recent_events]
            type_counts = defaultdict(int)
            for et in recent_event_types:
                type_counts[et] += 1
            
            if type_counts:
                top_activities = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:3]
                major_developments.append(
                    f"Primary activities: {', '.join([f'{act} ({cnt})' for act, cnt in top_activities])}"
                )
        
        # Build context string
        context = {
            'day_number': day_number,
            'total_events_so_far': self.total_events_generated,
            'previous_days_summary': major_developments,
            'recent_events_summary': [
                {
                    'location': e.get('location_name'),
                    'type': e.get('event_type'),
                    'actor': e.get('actor', 'Unknown')[:50]  # Truncate long actor names
                }
                for e in recent_events[-6:] if day_number > 1
            ],
            'ongoing_operations': list(self.ongoing_battles.keys()),
            'recently_active_units': list(self.recent_unit_activities.keys())[-10:],
            'most_used_locations': self._get_top_locations(5),
            'battle_count': len(self.ongoing_battles)
        }
        
        return context
    
    def get_underused_locations(self, phase: str, historical_locations: List[str] = None) -> List[Dict[str, Any]]:
        """Return locations that haven't been used much, prioritizing historical locations"""
        
        from config import GEOGRAPHIC_AREAS_ENHANCED
        
        underused = []
        
        # Get all sub-locations from enhanced geography
        for complex_name, complex_data in GEOGRAPHIC_AREAS_ENHANCED.items():
            sub_locations = complex_data.get('sub_locations', {})
            
            for subloc_key, subloc_data in sub_locations.items():
                loc_name = subloc_data.get('name')
                usage = self.location_usage_count.get(loc_name, 0)
                
                # Prioritize locations used less than 3 times
                if usage < 3:
                    subloc_data['usage_count'] = usage
                    subloc_data['complex'] = complex_name
                    
                    # If this location is in historical_locations, mark it as priority
                    if historical_locations and loc_name in historical_locations:
                        subloc_data['priority'] = True
                    else:
                        subloc_data['priority'] = False
                    
                    underused.append(subloc_data)
        
        # Sort by priority (historical first), then by usage count
        underused.sort(key=lambda x: (not x.get('priority', False), x.get('usage_count', 0)))
        
        return underused[:20]  # Return top 20 underused locations
    
    def check_description_uniqueness(self, new_description: str) -> bool:
        """Check if description is too similar to previous ones"""
        
        if not new_description or len(new_description) < 20:
            return True  # Too short to check
        
        fingerprint = new_description[:50].lower().strip()
        
        # Check exact fingerprint match
        if fingerprint in self.used_descriptions:
            return False
        
        # Check for high phrase overlap
        new_words = set(new_description.lower().split())
        
        # Check against recent descriptions (last 50)
        recent_descriptions = list(self.used_descriptions)[-50:]
        
        for used_fingerprint in recent_descriptions:
            used_words = set(used_fingerprint.split())
            
            if len(new_words) > 0:
                overlap = len(new_words & used_words) / len(new_words)
                if overlap > 0.75:  # 75% word overlap is too similar
                    return False
        
        return True  # Unique enough
    
    def check_phrase_overuse(self, description: str) -> List[str]:
        """Check if any phrases in the description are overused"""
        
        overused_phrases = []
        words = description.lower().split()
        
        for i in range(len(words) - 2):
            trigram = ' '.join(words[i:i+3])
            usage_count = self.used_phrases.get(trigram, 0)
            
            if usage_count > 5:  # Used more than 5 times
                overused_phrases.append((trigram, usage_count))
        
        return overused_phrases
    
    def mark_battle_started(self, location: str, date: str, intensity: str):
        """Track that a battle has started at a location"""
        
        self.ongoing_battles[location] = {
            'start_date': date,
            'intensity': intensity,
            'day_count': 1,
            'events_count': 1
        }
        
        logger.info(f"Battle marked as started at {location} on {date}")
    
    def update_battle_status(self, location: str, date: str):
        """Update ongoing battle"""
        
        if location in self.ongoing_battles:
            self.ongoing_battles[location]['day_count'] += 1
            self.ongoing_battles[location]['events_count'] += 1
            
            # If battle goes on too long, mark as concluded
            if self.ongoing_battles[location]['day_count'] > 10:
                self.mark_battle_concluded(location, date, "prolonged")
    
    def mark_battle_concluded(self, location: str, date: str, reason: str = "completed"):
        """Mark battle as finished"""
        
        if location in self.ongoing_battles:
            battle_info = self.ongoing_battles[location]
            
            self.major_events_occurred.append({
                'type': 'battle_conclusion',
                'location': location,
                'date': date,
                'duration_days': battle_info['day_count'],
                'events_count': battle_info['events_count'],
                'reason': reason
            })
            
            del self.ongoing_battles[location]
            logger.info(f"Battle at {location} concluded on {date} ({reason})")
    
    def get_unit_recent_activity(self, unit_name: str) -> List[Dict[str, Any]]:
        """Get recent activities for a specific unit"""
        return self.recent_unit_activities.get(unit_name, [])
    
    def _get_top_locations(self, n: int = 5) -> List[tuple]:
        """Get top N most used locations"""
        sorted_locs = sorted(self.location_usage_count.items(), key=lambda x: x[1], reverse=True)
        return sorted_locs[:n]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about narrative state"""
        
        return {
            'total_events': self.total_events_generated,
            'unique_locations_used': len(self.location_usage_count),
            'unique_units_mentioned': len(self.recent_unit_activities),
            'ongoing_battles': len(self.ongoing_battles),
            'major_events': len(self.major_events_occurred),
            'events_by_type': dict(self.events_by_type),
            'top_5_locations': self._get_top_locations(5),
            'unique_descriptions': len(self.used_descriptions),
            'total_phrases_tracked': len(self.used_phrases)
        }
    
    def save_to_file(self, filepath: str):
        """Save narrative state to file for analysis"""
        
        try:
            state_data = {
                'statistics': self.get_statistics(),
                'ongoing_battles': self.ongoing_battles,
                'major_events': self.major_events_occurred,
                'location_usage': dict(self.location_usage_count),
                'events_by_type': dict(self.events_by_type),
                'top_overused_phrases': sorted(
                    self.used_phrases.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:20]
            }
            
            with open(filepath, 'w') as f:
                json.dump(state_data, f, indent=2)
            
            logger.info(f"Narrative state saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving narrative state: {e}")
    
    def reset(self):
        """Reset all state - use with caution"""
        
        self.__init__()
        logger.warning("Narrative state has been reset")