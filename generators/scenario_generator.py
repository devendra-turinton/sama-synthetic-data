import os
import json
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any

from utils.anthropic_client import AnthropicClient
from utils.correlation_manager import CorrelationManager
from utils.narrative_state_manager import NarrativeStateManager
from config import (
    OUTPUT_DIR, 
    KARGIL_SCENARIO, 
    KARGIL_HISTORICAL_TIMELINE,
    GEOGRAPHIC_AREAS_ENHANCED, 
    DAILY_TIME_SLOTS, 
    PAKISTANI_EQUIPMENT,
    MILITARY_INTELLIGENCE_LANGUAGE,
    ANTHROPIC_API_KEY, 
    MODEL_CONFIG
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScenarioGenerator:
    """Generate complete Kargil War timeline with enhanced historical accuracy and narrative progression"""
    
    def __init__(self, correlation_manager: CorrelationManager):
        self.client = AnthropicClient(
            api_key=ANTHROPIC_API_KEY,
            model=MODEL_CONFIG["model"],
            max_tokens=MODEL_CONFIG["max_tokens"],
            temperature=MODEL_CONFIG["temperature"]
        )
        self.correlation_manager = correlation_manager
        self.narrative_manager = NarrativeStateManager()
        self.scenario_config = KARGIL_SCENARIO
        self.time_slots = DAILY_TIME_SLOTS
        self.pakistani_equipment = PAKISTANI_EQUIPMENT
    
    def generate_complete_timeline(self) -> Dict[str, Any]:
        """Generate complete 92-day Kargil War timeline with historical accuracy"""
        
        logger.info("="*80)
        logger.info("GENERATING KARGIL WAR TIMELINE (92 DAYS) - ENHANCED VERSION")
        logger.info("="*80)
        
        start_date = datetime.strptime(self.scenario_config["start_date"], "%Y-%m-%d")
        end_date = datetime.strptime(self.scenario_config["end_date"], "%Y-%m-%d")
        total_days = (end_date - start_date).days + 1
        
        logger.info(f"Period: {start_date.date()} to {end_date.date()}")
        logger.info(f"Total days: {total_days}")
        logger.info(f"Expected events: {total_days * 6} (6 per day)")
        logger.info(f"Using enhanced historical timeline and geographic database")
        
        complete_timeline = []
        current_date = start_date
        day_number = 1
        
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            
            # Get historical data for this specific date
            historical_data = KARGIL_HISTORICAL_TIMELINE.get(date_str, {})
            phase = historical_data.get("phase", "unknown")
            
            logger.info(f"\nDay {day_number}/{total_days}: {date_str} - {phase}")
            logger.info(f"  Key Event: {historical_data.get('key_event', 'Regular operations')}")
            logger.info(f"  Intensity: {historical_data.get('intensity', 'unknown')}")
            
            # Check if this is a major event day requiring special handling
            is_major_event = historical_data.get('key_event_type') in [
                'major_battle', 'major_victory', 'major_discovery', 'operation_launch', 'war_end'
            ]
            
            # Generate events for this day
            if is_major_event:
                logger.info(f"  >>> MAJOR EVENT DAY - Using enhanced generation")
                day_events = self._generate_major_event_day(
                    current_date, date_str, historical_data, day_number
                )
            else:
                day_events = self._generate_standard_day(
                    current_date, date_str, historical_data, day_number
                )
            
            # Validate and enhance events
            day_events = self._validate_and_enhance_events(day_events, date_str, day_number)
            
            # Create correlation packages for each event
            for event in day_events:
                event["date"] = date_str
                event["day_number"] = day_number
                
                # Create correlation package (this assigns correlation_id)
                corr_pkg = self.correlation_manager.create_correlation_package(event)
                event["correlation_id"] = corr_pkg["correlation_id"]
            
            # Update narrative state
            self.narrative_manager.update_from_day(date_str, day_events)
            
            complete_timeline.append({
                "day": day_number,
                "date": date_str,
                "phase": phase,
                "historical_context": historical_data,
                "events": day_events
            })
            
            # Log statistics periodically
            if day_number % 10 == 0:
                stats = self.narrative_manager.get_statistics()
                logger.info(f"\n  --- Progress Stats (Day {day_number}) ---")
                logger.info(f"  Total events generated: {stats['total_events']}")
                logger.info(f"  Unique locations used: {stats['unique_locations_used']}")
                logger.info(f"  Ongoing battles: {stats['ongoing_battles']}")
            
            current_date += timedelta(days=1)
            day_number += 1
        
        # Create scenario package
        scenario = {
            "scenario_name": self.scenario_config["name"],
            "scenario_description": self.scenario_config["description"],
            "start_date": self.scenario_config["start_date"],
            "end_date": self.scenario_config["end_date"],
            "total_days": total_days,
            "total_events": sum(len(day["events"]) for day in complete_timeline),
            "phases": self.scenario_config["phases"],
            "geographic_focus": "Enhanced - 100+ locations across Kargil sector",
            "timeline": complete_timeline,
            "generation_metadata": {
                "enhanced_features": [
                    "Historical timeline integration",
                    "Progressive narrative system",
                    "100+ unique locations",
                    "Authentic military language",
                    "Major event multi-turn generation"
                ],
                "narrative_statistics": self.narrative_manager.get_statistics()
            }
        }
        
        # Save scenario
        output_path = os.path.join(OUTPUT_DIR, f"scenario_{self.scenario_config['name']}.json")
        with open(output_path, 'w') as f:
            json.dump(scenario, f, indent=2)
        
        # Save narrative state
        narrative_state_path = os.path.join(OUTPUT_DIR, f"narrative_state_{self.scenario_config['name']}.json")
        self.narrative_manager.save_to_file(narrative_state_path)
        
        logger.info(f"\n✓ Timeline generated: {scenario['total_events']} events")
        logger.info(f"✓ Saved to: {output_path}")
        logger.info(f"✓ Narrative state saved to: {narrative_state_path}")
        
        return scenario
    
    def _generate_standard_day(self, current_date: datetime, date_str: str, 
                               historical_data: Dict[str, Any], day_number: int) -> List[Dict[str, Any]]:
        """Generate events for a standard (non-major) day"""
        
        # Get progressive context
        progressive_context = self.narrative_manager.get_progressive_context(date_str, day_number)
        
        # Get underused locations
        preferred_historical_locations = historical_data.get('primary_locations', [])
        underused_locations = self.narrative_manager.get_underused_locations(
            historical_data.get('phase', 'unknown'),
            preferred_historical_locations
        )
        
        # Create enhanced prompt
        prompt = self._create_enhanced_day_prompt(
            date_str,
            historical_data,
            progressive_context,
            underused_locations,
            day_number,
            is_major_event=False
        )
        
        try:
            response = self.client.generate_structured_data(prompt)
            events = response.get("events", [])
            
            # Ensure exactly 6 events
            if len(events) < 6:
                logger.warning(f"Only {len(events)} events generated for {date_str}, padding to 6")
                while len(events) < 6:
                    events.append(self._create_routine_event(self.time_slots[len(events)], historical_data))
            elif len(events) > 6:
                logger.warning(f"{len(events)} events generated for {date_str}, truncating to 6")
                events = events[:6]
            
            # Assign time slots
            for i, event in enumerate(events):
                event["time"] = self.time_slots[i]
            
            return events
            
        except Exception as e:
            logger.error(f"Error generating events for {date_str}: {e}")
            # Return routine events as fallback
            return [self._create_routine_event(slot, historical_data) for slot in self.time_slots]
    
    def _generate_major_event_day(self, current_date: datetime, date_str: str,
                                  historical_data: Dict[str, Any], day_number: int) -> List[Dict[str, Any]]:
        """
        Use multi-turn generation for major historical events
        to ensure maximum detail and accuracy
        """
        
        logger.info(f"  Generating MAJOR EVENT day with multi-turn approach")
        
        # Turn 1: Get strategic overview
        strategic_prompt = f"""You are a military historian analyzing the Kargil War.

Date: {date_str} (Day {day_number} of the war)
Major Event: {historical_data.get('key_event')}
Phase: {historical_data.get('phase')}

Provide a strategic overview of this major event:
1. Strategic significance and why this was a turning point
2. Forces involved on both sides (specific units, not generic)
3. Objectives for each side
4. The overall tactical situation before this event
5. Weather and terrain factors

Be specific with unit names, locations, and equipment. Use 200-250 words.
"""
        
        try:
            strategic_context = self.client.generate_text(strategic_prompt)
            logger.debug(f"  Strategic context generated: {len(strategic_context)} chars")
        except Exception as e:
            logger.error(f"  Error generating strategic context: {e}")
            strategic_context = f"Major operation: {historical_data.get('key_event')}"
        
        # Turn 2: Get tactical details
        tactical_prompt = f"""Strategic Context: {strategic_context}

Now provide tactical-level details for {historical_data.get('key_event')}:

1. Specific units involved (battalion, company level with designations)
2. Equipment used by each side (types and quantities)
3. Terrain features affecting the operation
4. Timeline of key tactical events throughout the day
5. Casualties or tactical results (if applicable)
6. Notable tactical innovations or actions

Focus on the six time periods: 00:00, 04:00, 08:00, 12:00, 16:00, 20:00 hours.
Be very specific with unit names, equipment types, and locations. Use 250-300 words.
"""
        
        try:
            tactical_context = self.client.generate_text(tactical_prompt)
            logger.debug(f"  Tactical context generated: {len(tactical_context)} chars")
        except Exception as e:
            logger.error(f"  Error generating tactical context: {e}")
            tactical_context = "Tactical operations throughout the day"
        
        # Get progressive context
        progressive_context = self.narrative_manager.get_progressive_context(date_str, day_number)
        
        # Get locations
        preferred_locations = historical_data.get('primary_locations', [])
        underused_locations = self.narrative_manager.get_underused_locations(
            historical_data.get('phase', 'unknown'),
            preferred_locations
        )
        
        # Turn 3: Generate 6 detailed events using full context
        events_prompt = self._create_major_event_prompt(
            date_str,
            historical_data,
            strategic_context,
            tactical_context,
            progressive_context,
            underused_locations,
            day_number
        )
        
        try:
            response = self.client.generate_structured_data(events_prompt)
            events = response.get("events", [])
            
            # Ensure 6 events
            if len(events) != 6:
                logger.warning(f"  Expected 6 events, got {len(events)}")
                if len(events) < 6:
                    while len(events) < 6:
                        events.append(self._create_routine_event(self.time_slots[len(events)], historical_data))
                else:
                    events = events[:6]
            
            # Assign time slots
            for i, event in enumerate(events):
                event["time"] = self.time_slots[i]
            
            logger.info(f"  ✓ Major event day generated with {len(events)} detailed events")
            return events
            
        except Exception as e:
            logger.error(f"  Error in major event generation: {e}")
            # Fallback to standard generation
            return self._generate_standard_day(current_date, date_str, historical_data, day_number)
    
    def _create_enhanced_day_prompt(self, date_str: str, historical_data: Dict[str, Any],
                                   progressive_context: Dict[str, Any], 
                                   underused_locations: List[Dict[str, Any]],
                                   day_number: int, is_major_event: bool = False) -> str:
        """Create enhanced prompt with all context"""
        
        # Select random military language examples
        movement_samples = random.sample(
            MILITARY_INTELLIGENCE_LANGUAGE['movement_descriptions'], 
            min(4, len(MILITARY_INTELLIGENCE_LANGUAGE['movement_descriptions']))
        )
        tactical_samples = random.sample(
            MILITARY_INTELLIGENCE_LANGUAGE['tactical_activities'], 
            min(4, len(MILITARY_INTELLIGENCE_LANGUAGE['tactical_activities']))
        )
        unit_comp_samples = random.sample(
            MILITARY_INTELLIGENCE_LANGUAGE['unit_compositions'], 
            min(3, len(MILITARY_INTELLIGENCE_LANGUAGE['unit_compositions']))
        )
        pak_units = random.sample(
            MILITARY_INTELLIGENCE_LANGUAGE['pakistani_units'], 
            min(5, len(MILITARY_INTELLIGENCE_LANGUAGE['pakistani_units']))
        )
        ind_units = random.sample(
            MILITARY_INTELLIGENCE_LANGUAGE['indian_units'], 
            min(5, len(MILITARY_INTELLIGENCE_LANGUAGE['indian_units']))
        )
        equipment_pak = random.sample(
            MILITARY_INTELLIGENCE_LANGUAGE['equipment_specifics_pakistan'], 
            min(3, len(MILITARY_INTELLIGENCE_LANGUAGE['equipment_specifics_pakistan']))
        )
        assessment_samples = random.sample(
            MILITARY_INTELLIGENCE_LANGUAGE['intelligence_assessments'], 
            min(3, len(MILITARY_INTELLIGENCE_LANGUAGE['intelligence_assessments']))
        )
        
        # Format location information
        location_list = []
        for loc in underused_locations[:15]:
            location_list.append({
                "name": loc.get('name'),
                "lat": loc.get('lat'),
                "long": loc.get('long'),
                "height": loc.get('height'),
                "features": loc.get('features', [])[:2],  # First 2 features
                "usage_count": loc.get('usage_count', 0),
                "priority": loc.get('priority', False)
            })
        
        prompt = f"""=== INTELLIGENCE EVENT GENERATION FOR KARGIL WAR ===
DATE: {date_str} (Day {day_number} of 92-day war)
Phase: {historical_data.get('phase', 'Unknown').upper()}

=== HISTORICAL CONTEXT FOR THIS SPECIFIC DATE ===
Key Event Today: {historical_data.get('key_event', 'Regular operations continue')}
Narrative Theme: {historical_data.get('narrative_theme', 'Ongoing operations')}
Tactical Situation: {historical_data.get('tactical_situation', 'Operational tempo maintained')}
Intensity Level: {historical_data.get('intensity', 'medium').upper()}

Primary Pakistani Actors Today:
{json.dumps(historical_data.get('primary_actors_pakistan', []), indent=2)}

Primary Indian Actors Today:
{json.dumps(historical_data.get('primary_actors_india', []), indent=2)}

Weather: {historical_data.get('weather_conditions', 'Clear conditions')}
Equipment Focus: {', '.join(historical_data.get('equipment_focus', ['Standard infantry equipment']))}

Contested Locations: {', '.join(historical_data.get('contested_locations', [])) if historical_data.get('contested_locations') else 'None'}

=== PROGRESSIVE NARRATIVE CONTEXT ===
Total Events Generated So Far: {progressive_context.get('total_events_so_far', 0)}
Ongoing Operations: {', '.join(progressive_context.get('ongoing_operations', [])) if progressive_context.get('ongoing_operations') else 'None'}

Recent Activity Summary:
{chr(10).join(progressive_context.get('previous_days_summary', [])) if progressive_context.get('previous_days_summary') else 'Beginning of timeline'}

Last 6 Events (for continuity):
{json.dumps(progressive_context.get('recent_events_summary', []), indent=2) if day_number > 1 else 'No previous events - this is Day 1'}

=== LOCATIONS TO USE (PRIORITIZE UNDERUSED) ===
Use these specific locations - each event MUST use a DIFFERENT location:
{json.dumps(location_list, indent=2)}

=== MILITARY LANGUAGE REQUIREMENTS ===
You MUST use authentic military intelligence language throughout all descriptions.

Movement Description Styles (use similar language):
{chr(10).join(['• ' + m for m in movement_samples])}

Tactical Activities (incorporate these types):
{chr(10).join(['• ' + t for t in tactical_samples])}

Unit Composition Examples (be THIS specific):
{chr(10).join(['• ' + u for u in unit_comp_samples])}

Pakistani Units (use ACTUAL unit names, not "Pakistani forces"):
{chr(10).join(['• ' + p for p in pak_units])}

Indian Units (use ACTUAL unit names, not "Indian forces"):
{chr(10).join(['• ' + i for i in ind_units])}

Equipment Specificity Examples:
{chr(10).join(['• ' + e for e in equipment_pak])}

Intelligence Assessment Styles:
{chr(10).join(['• ' + a for a in assessment_samples])}

=== CRITICAL GENERATION REQUIREMENTS ===

1. Generate EXACTLY 6 unique events that fit today's historical context
2. Each event MUST use a DIFFERENT location from the list above (no repeats within the day)
3. Each description MUST be 150-250 words (not 50 words!)
4. Use SPECIFIC unit names from the lists above (NEVER use "Pakistani forces" or "Indian forces")
5. Include SPECIFIC equipment with quantities (e.g., "3x Al-Khalid MBT, 2x M113 APC")
6. Include tactical assessment: "Assessed intent:" or "Tactical assessment:" in each description
7. Use MILITARY TERMINOLOGY throughout (phase line, assembly area, fire support, etc.)
8. Descriptions must tell a coherent story across the 6 time slots
9. Make each description UNIQUE - vary sentence structure, vocabulary, and perspective
10. Include coordinates, grid references, or ranges where appropriate

=== EVENT STRUCTURE ===
Each event must include:
- time: (will be assigned - use placeholder "00:00")
- event_type: "movement" | "firing" | "construction" | "reconnaissance" | "engagement" | "logistics" | "deployment"
- actor: SPECIFIC unit name from lists above (with full designation)
- location: [longitude, latitude] from location data above
- location_name: Exact name from location list above
- description: 150-250 words, military language, tactical details, assessment
- observable_by: ["ELINT", "IMINT", "TACINT"] or subset based on activity
- equipment_involved: [specific equipment with quantities]
- strength: Specific unit composition (e.g., "reinforced rifle company, 135 personnel, 3 platoons")
- significance: "routine" | "important" | "critical"

=== EXAMPLE FORMAT (DO NOT COPY - USE AS STYLE GUIDE) ===
{{
  "time": "00:00",
  "event_type": "movement",
  "actor": "Pakistani 12th Northern Light Infantry - Bravo Company",
  "location": [76.1158, 34.5447],
  "location_name": "Tololing Summit",
  "description": "At 0820 hours, Pakistani 12th Northern Light Infantry Bravo Company (reinforced rifle company, estimated 135 personnel) completed tactical occupation of Tololing Summit defensive positions at elevation 4590 meters. Unit composition observed via CARTOSAT-3 overhead imagery: 3 rifle platoons deployed in mutually supporting sangars with interlocking fields of fire, integral 60mm mortar section (2 tubes) emplaced on reverse slope for indirect fire support, 12.7mm DShK heavy machine gun detachment positioned covering primary approach routes from assembly area Alpha. Defensive positions demonstrate professional military engineering with overhead cover utilizing pre-positioned timber and sandbags, suggests detailed reconnaissance and logistics preparation conducted during infiltration phase. Supply caches identified at grid reference 384251 3817142 include ammunition, rations for 7-10 days sustained operations, and medical supplies. Communications intercept confirms TRC-20H tactical radio net active on VHF frequencies coordinating with battalion headquarters. Assessed intent: establish dominating observation post controlling Drass-Kargil road corridor (NH 1D) to enable interdiction of Indian logistics and provide early warning of counter-movement operations. Tactical assessment: methodically executed occupation during limited visibility period 0600-0820 hours demonstrates sound tactical discipline and professional small-unit leadership. Position provides 360-degree observation with dead ground approaches exploitable for future assault operations.",
  "observable_by": ["ELINT", "IMINT", "TACINT"],
  "equipment_involved": ["G3A3 7.62mm rifles", "2x 60mm mortars with 150 rounds", "1x 12.7mm DShK HMG", "TRC-20H tactical radios", "Engineering stores"],
  "strength": "Reinforced rifle company (135 personnel, 3 rifle platoons, 1 weapons section)",
  "significance": "critical"
}}

=== GENERATE 6 EVENTS NOW ===
Return ONLY valid JSON with "events" array containing EXACTLY 6 events.
Each event MUST:
- Be historically accurate for {date_str}
- Use a DIFFERENT location (no location used twice)
- Have 150-250 word description with military language
- Include specific units, equipment, and tactical assessment
- Tell part of today's coherent operational story

{{
  "events": [
    ... your 6 detailed events here ...
  ]
}}
"""
        
        return prompt
    
    def _create_major_event_prompt(self, date_str: str, historical_data: Dict[str, Any],
                                  strategic_context: str, tactical_context: str,
                                  progressive_context: Dict[str, Any],
                                  underused_locations: List[Dict[str, Any]],
                                  day_number: int) -> str:
        """Create enhanced prompt for major event days with multi-turn context"""
        
        # Get base prompt
        base_prompt = self._create_enhanced_day_prompt(
            date_str, historical_data, progressive_context, 
            underused_locations, day_number, is_major_event=True
        )
        
        # Enhance with strategic and tactical context
        enhanced_prompt = f"""=== MAJOR HISTORICAL EVENT - ENHANCED GENERATION ===

{base_prompt}

=== ADDITIONAL STRATEGIC CONTEXT ===
{strategic_context}

=== ADDITIONAL TACTICAL CONTEXT ===
{tactical_context}

=== MAJOR EVENT SPECIFIC REQUIREMENTS ===
Since this is a MAJOR HISTORICAL EVENT, your 6 events should follow this structure:

Event 1 (00:00): Preparation/Setup phase - Forces moving into position, final preparations
Event 2 (04:00): Pre-dawn activities - Final coordination, reconnaissance, movement completion
Event 3 (08:00): Initial action - Main operation begins, first contact or initial strikes
Event 4 (12:00): Peak intensity - Main engagement, critical tactical developments
Event 5 (16:00): Evolution/Response - Tactical adjustments, reinforcements, counter-actions
Event 6 (20:00): Consolidation/Assessment - Results, aftermath, position securing

Each description MUST be 200-250 words for major events (longer than standard days).
Use ALL the strategic and tactical context provided above.
Describe this major event as if you're creating an official military historical record.

Generate the 6 events now:
"""
        
        return enhanced_prompt
    
    def _create_routine_event(self, time_slot: str, historical_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a routine/low-activity event as fallback"""
        
        # Select random location from underused
        underused = self.narrative_manager.get_underused_locations(
            historical_data.get('phase', 'unknown')
        )
        
        if underused:
            location_data = random.choice(underused[:10])
            location_name = location_data.get('name', 'Kargil Sector')
            location_coords = [location_data.get('long', 76.1315), location_data.get('lat', 34.5535)]
        else:
            location_name = "Kargil Sector"
            location_coords = [76.1315, 34.5535]
        
        # Select random unit
        actors = historical_data.get('primary_actors_pakistan', ['Pakistani XII Corps - Various Units'])
        actor = random.choice(actors) if actors else 'Pakistani XII Corps - Various Units'
        
        return {
            "time": time_slot,
            "event_type": "routine",
            "actor": actor,
            "location": location_coords,
            "location_name": location_name,
            "description": f"Routine patrol and defensive positioning activities conducted by {actor} in {location_name} area. Unit maintained established defensive positions with standard communication checks, observation activities, and perimeter security. Weather conditions: {historical_data.get('weather_conditions', 'Typical for season')}. No significant tactical developments during this period. Position strength and readiness maintained per standard operating procedures.",
            "observable_by": ["ELINT", "TACINT"],
            "equipment_involved": ["Standard infantry equipment", "Communications gear"],
            "strength": "patrol-sized element",
            "significance": "routine"
        }
    
    def _validate_and_enhance_events(self, events: List[Dict[str, Any]], 
                                    date_str: str, day_number: int) -> List[Dict[str, Any]]:
        """Validate generated events and enhance if needed"""
        
        validated_events = []
        used_locations = set()
        
        for idx, event in enumerate(events):
            # Validate required fields
            if not event.get('description'):
                logger.warning(f"Event {idx} missing description on {date_str}")
                event['description'] = "Event description not available"
            
            # Check description length
            desc_length = len(event.get('description', ''))
            if desc_length < 150:
                logger.warning(f"Event {idx} description too short ({desc_length} chars) on {date_str}")
            
            # Check location uniqueness within day
            location_name = event.get('location_name', f'Location_{idx}')
            if location_name in used_locations:
                logger.warning(f"Duplicate location {location_name} in day {date_str}")
            used_locations.add(location_name)
            
            # Validate coordinates
            location = event.get('location', [76.1, 34.5])
            if not isinstance(location, list) or len(location) != 2:
                logger.warning(f"Invalid location format for event {idx} on {date_str}")
                event['location'] = [76.1315, 34.5535]
            
            # Ensure actor is not generic
            actor = event.get('actor', '')
            if actor.lower() in ['pakistani forces', 'indian forces', 'forces', 'troops']:
                logger.warning(f"Generic actor '{actor}' in event {idx} on {date_str}")
            
            validated_events.append(event)
        
        return validated_events