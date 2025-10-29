import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

from utils.anthropic_client import AnthropicClient
from utils.correlation_manager import CorrelationManager
from config import (OUTPUT_DIR, KARGIL_SCENARIO, GEOGRAPHIC_AREAS, 
                   DAILY_TIME_SLOTS, PAKISTANI_EQUIPMENT, ANTHROPIC_API_KEY, MODEL_CONFIG)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScenarioGenerator:
    """Generate complete Kargil War timeline with all phases"""
    
    def __init__(self, correlation_manager: CorrelationManager):
        self.client = AnthropicClient(
            api_key=ANTHROPIC_API_KEY,
            model=MODEL_CONFIG["model"],
            max_tokens=MODEL_CONFIG["max_tokens"],
            temperature=MODEL_CONFIG["temperature"]
        )
        self.correlation_manager = correlation_manager
        self.scenario_config = KARGIL_SCENARIO
        self.geographic_areas = GEOGRAPHIC_AREAS
        self.time_slots = DAILY_TIME_SLOTS
        self.pakistani_equipment = PAKISTANI_EQUIPMENT
    
    def generate_complete_timeline(self) -> Dict[str, Any]:
        """Generate complete 92-day Kargil War timeline"""
        
        logger.info("="*80)
        logger.info("GENERATING KARGIL WAR TIMELINE (92 DAYS)")
        logger.info("="*80)
        
        start_date = datetime.strptime(self.scenario_config["start_date"], "%Y-%m-%d")
        end_date = datetime.strptime(self.scenario_config["end_date"], "%Y-%m-%d")
        total_days = (end_date - start_date).days + 1
        
        logger.info(f"Period: {start_date.date()} to {end_date.date()}")
        logger.info(f"Total days: {total_days}")
        logger.info(f"Expected events: {total_days * 6} (6 per day)")
        
        complete_timeline = []
        current_date = start_date
        day_number = 1
        
        while current_date <= end_date:
            phase = self._get_phase_for_date(current_date)
            phase_data = self.scenario_config["phases"].get(phase, {})
            
            logger.info(f"Day {day_number}/{total_days}: {current_date.date()} - {phase}")
            
            # Generate events for this day
            day_events = self._generate_day_events(
                current_date, 
                phase, 
                phase_data, 
                day_number
            )
            
            # Create correlation packages for each event
            for event in day_events:
                event["date"] = current_date.strftime("%Y-%m-%d")
                event["day_number"] = day_number
                
                # Create correlation package (this assigns correlation_id)
                corr_pkg = self.correlation_manager.create_correlation_package(event)
                event["correlation_id"] = corr_pkg["correlation_id"]
            
            complete_timeline.append({
                "day": day_number,
                "date": current_date.strftime("%Y-%m-%d"),
                "phase": phase,
                "events": day_events
            })
            
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
            "geographic_focus": self.geographic_areas["kargil_sector"],
            "timeline": complete_timeline
        }
        
        # Save scenario
        output_path = os.path.join(OUTPUT_DIR, f"scenario_{self.scenario_config['name']}.json")
        with open(output_path, 'w') as f:
            json.dump(scenario, f, indent=2)
        
        logger.info(f"✓ Timeline generated: {scenario['total_events']} events")
        logger.info(f"✓ Saved to: {output_path}")
        
        return scenario
    
    def _get_phase_for_date(self, date: datetime) -> str:
        """Determine which phase a date falls into"""
        date_str = date.strftime("%Y-%m-%d")
        
        for phase_name, phase_data in self.scenario_config["phases"].items():
            phase_start = datetime.strptime(phase_data["start"], "%Y-%m-%d")
            phase_end = datetime.strptime(phase_data["end"], "%Y-%m-%d")
            
            if phase_start <= date <= phase_end:
                return phase_name
        
        return "unknown"
    
    def _generate_day_events(self, date: datetime, phase: str, 
                            phase_data: Dict, day_number: int) -> List[Dict[str, Any]]:
        """Generate 6 events for a single day"""
        
        activity_level = phase_data.get("activity_level", "medium")
        date_str = date.strftime("%Y-%m-%d")
        
        # Check for key historical events on this date
        key_events_today = [
            event for event in phase_data.get("key_events", [])
            if event.get("date") == date_str
        ]
        
        # Create prompt
        prompt = self._create_day_events_prompt(
            date, phase, phase_data, key_events_today, activity_level
        )
        
        try:
            response = self.client.generate_structured_data(prompt)
            events = response.get("events", [])
            
            # Ensure exactly 6 events
            if len(events) < 6:
                logger.warning(f"Only {len(events)} events generated for {date_str}, padding to 6")
                while len(events) < 6:
                    events.append(self._create_routine_event(self.time_slots[len(events)]))
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
            return [self._create_routine_event(slot) for slot in self.time_slots]
    
    def _create_day_events_prompt(self, date: datetime, phase: str,
                                  phase_data: Dict, key_events: List,
                                  activity_level: str) -> str:
        """Create prompt for generating day's events"""
        
        date_str = date.strftime("%Y-%m-%d")
        day_name = date.strftime("%A")
        
        key_positions = self.geographic_areas["kargil_sector"]["key_positions"]
        
        # Build equipment lists
        equipment_str = ", ".join(
            self.pakistani_equipment["armor"][:3] + 
            self.pakistani_equipment["artillery"][:2]
        )
        
        prompt = f"""Generate 6 realistic military events for the Kargil War on {date_str} ({day_name}).

CONTEXT:
Phase: {phase}
Description: {phase_data.get('description', '')}
Activity Level: {activity_level}

{"KEY HISTORICAL EVENTS TODAY:" if key_events else ""}
{json.dumps(key_events, indent=2) if key_events else ""}

TIME SLOTS (generate ONE event per slot):
{json.dumps(self.time_slots, indent=2)}

LOCATIONS (use these):
{json.dumps(key_positions, indent=2)}

PAKISTANI EQUIPMENT:
{equipment_str}

ACTIVITY LEVEL GUIDANCE:
- low: Reconnaissance, minimal movement, routine patrols
- low_to_medium: Positioning, intelligence gathering, limited movement
- medium: Regular activity, troop movements, artillery exchanges
- medium_to_high: Increased operations, multiple engagements
- very_high: Major combat, heavy fighting, simultaneous operations

CRITICAL REQUIREMENTS:
1. Events must be RELATED (tell a coherent operational story)
2. Early events can lead to later events (morning prep → afternoon action → evening assessment)
3. Use specific Pakistani military units (XII Corps, 12 Armoured Regiment, etc.)
4. Include realistic equipment and strength estimates
5. Reference specific geographic positions from the locations list
6. Specify which intelligence sources can observe: ["ELINT", "IMINT", "TACINT"]

OBSERVABLE BY RULES:
- ELINT: Can observe communications, electronic emissions (movement, deployment, attacks)
- IMINT: Can observe physical activity from overhead (vehicles, troops, positions)
- TACINT: Can observe ground-level activity (patrols, movements, engagements)
- Most events observable by all three sources
- Only communications/electronic: ["ELINT"]
- Only physical/visual: ["IMINT", "TACINT"]

Return ONLY valid JSON:
{{
  "events": [
    {{
      "time": "00:00",
      "event_type": "movement|firing|construction|reconnaissance|engagement|logistics|deployment",
      "actor": "Pakistani XII Corps - Specific Unit Name",
      "location": [longitude, latitude],
      "location_name": "Tiger Hill|Tololing|Point 5140|etc",
      "description": "Detailed description with military specifics",
      "observable_by": ["ELINT", "IMINT", "TACINT"],
      "equipment_involved": ["specific equipment names"],
      "strength": "12 tanks|battalion-strength|company-sized element",
      "significance": "routine|important|critical"
    }},
    ... 5 more events
  ]
}}"""
        
        return prompt
    
    def _create_routine_event(self, time_slot: str) -> Dict[str, Any]:
        """Create a routine/low-activity event as fallback"""
        return {
            "time": time_slot,
            "event_type": "routine",
            "actor": "Pakistani XII Corps - Various Units",
            "location": [76.1315, 34.5535],
            "location_name": "Kargil Sector",
            "description": "Routine patrol and defensive positioning. Maintaining established positions with standard communication checks and observation activities.",
            "observable_by": ["ELINT", "TACINT"],
            "equipment_involved": [],
            "strength": "patrol-sized element",
            "significance": "routine"
        }