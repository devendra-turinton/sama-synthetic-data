import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

from utils.anthropic_client import AnthropicClient
from config import OUTPUT_DIR, KARGIL_SCENARIO, GEOGRAPHIC_AREAS, DAILY_TIME_SLOTS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KargilScenarioGenerator:
    """Generate Kargil War scenario with historical accuracy and 6 events per day"""
    
    def __init__(self):
        self.client = AnthropicClient()
        self.scenario_config = KARGIL_SCENARIO
        self.geographic_areas = GEOGRAPHIC_AREAS
        self.time_slots = DAILY_TIME_SLOTS
    
    def generate_complete_timeline(self) -> Dict[str, Any]:
        """Generate complete Kargil War timeline with all phases"""
        
        logger.info("Generating complete Kargil War timeline...")
        
        # Calculate date range
        start_date = datetime.strptime(self.scenario_config["start_date"], "%Y-%m-%d")
        end_date = datetime.strptime(self.scenario_config["post_war_end"], "%Y-%m-%d")
        total_days = (end_date - start_date).days + 1
        
        logger.info(f"Timeline span: {total_days} days from {start_date.date()} to {end_date.date()}")
        
        # Generate timeline day by day
        complete_timeline = []
        current_date = start_date
        
        while current_date <= end_date:
            day_number = (current_date - start_date).days + 1
            phase = self._get_phase_for_date(current_date)
            
            logger.info(f"Generating events for Day {day_number}: {current_date.date()} ({phase})")
            
            day_events = self._generate_day_events(current_date, phase, day_number)
            
            complete_timeline.append({
                "day": day_number,
                "date": current_date.strftime("%Y-%m-%d"),
                "phase": phase,
                "events": day_events
            })
            
            current_date += timedelta(days=1)
        
        # Create complete scenario package
        scenario = {
            "scenario_name": self.scenario_config["name"],
            "scenario_description": self.scenario_config["description"],
            "start_date": self.scenario_config["start_date"],
            "end_date": self.scenario_config["post_war_end"],
            "total_days": total_days,
            "total_events": sum(len(day["events"]) for day in complete_timeline),
            "geographic_focus": self.geographic_areas["kargil_sector"],
            "timeline": complete_timeline,
            "phases": self.scenario_config["phases"]
        }
        
        # Save scenario
        output_path = os.path.join(OUTPUT_DIR, f"scenario_{self.scenario_config['name']}.json")
        with open(output_path, 'w') as f:
            json.dump(scenario, f, indent=2)
        
        logger.info(f"Complete scenario saved to: {output_path}")
        logger.info(f"Total events generated: {scenario['total_events']}")
        
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
    
    def _generate_day_events(self, date: datetime, phase: str, day_number: int) -> List[Dict[str, Any]]:
        """Generate 6 events for a single day (one per 4-hour time slot)"""
        
        phase_data = self.scenario_config["phases"].get(phase, {})
        activity_level = phase_data.get("activity_level", "medium")
        
        # Check if this day has any key historical events
        date_str = date.strftime("%Y-%m-%d")
        key_events_today = [
            event for event in phase_data.get("key_events", [])
            if event["date"] == date_str
        ]
        
        prompt = self._create_day_events_prompt(date, phase, phase_data, key_events_today, activity_level)
        
        try:
            response = self.client.generate_structured_data(prompt)
            events = response.get("events", [])
            
            # Ensure we have exactly 6 events (one per time slot)
            if len(events) < 6:
                logger.warning(f"Only {len(events)} events generated for {date_str}, expected 6")
                # Pad with low-activity events if needed
                while len(events) < 6:
                    events.append(self._create_null_event(self.time_slots[len(events)]))
            elif len(events) > 6:
                events = events[:6]
            
            # Ensure events have correct time slots
            for i, event in enumerate(events):
                event["time"] = self.time_slots[i]
                event["day_number"] = day_number
            
            return events
            
        except Exception as e:
            logger.error(f"Error generating events for {date_str}: {str(e)}")
            # Return minimal events on error
            return [self._create_null_event(slot) for slot in self.time_slots]
    
    def _create_day_events_prompt(self, date: datetime, phase: str, 
                                  phase_data: Dict, key_events: List, 
                                  activity_level: str) -> str:
        """Create prompt for generating a day's events"""
        
        date_str = date.strftime("%Y-%m-%d")
        day_name = date.strftime("%A")
        
        key_positions = self.geographic_areas["kargil_sector"]["key_positions"]
        
        prompt = f"""
Generate 6 realistic military intelligence events for the Kargil War on {date_str} ({day_name}).

HISTORICAL CONTEXT:
- Date: {date_str}
- Phase: {phase}
- Phase Description: {phase_data.get('description', '')}
- Activity Level: {activity_level}

KEY EVENTS TODAY:
{json.dumps(key_events, indent=2) if key_events else "No major historical events recorded for this specific date"}

TIME SLOTS (Generate exactly ONE event per slot):
{json.dumps(self.time_slots, indent=2)}

KEY GEOGRAPHIC POSITIONS:
{json.dumps(key_positions, indent=2)}

ACTIVITY LEVEL GUIDANCE:
- low: Mostly reconnaissance, minimal movement, routine patrols
- low_to_medium: Some movement, intelligence gathering, positioning
- medium: Regular combat activity, troop movements, artillery exchanges
- medium_to_high: Increased combat operations, multiple engagements
- high: Major operations, heavy fighting, significant troop movements
- very_high: Intense combat, multiple simultaneous operations, air strikes

TASK:
Generate exactly 6 events, one for each time slot. Events should:
1. Be historically plausible for the Kargil War
2. Match the activity level for this phase
3. Include specific military units (Pakistani or Indian)
4. Use realistic equipment (T-59 tanks, 130mm artillery, Mirage 2000 aircraft, etc.)
5. Reference specific geographic positions from the key positions list
6. Specify which intelligence sources can observe each event

IMPORTANT CORRELATION RULES:
- Events in the same day should be RELATED (tell a coherent story)
- Early events can lead to later events (e.g., morning troop movement leads to afternoon engagement)
- Multiple events can describe THE SAME INCIDENT from different angles/times
- Example: 08:00 "Artillery barrage detected", 12:00 "Ground assault begins", 16:00 "Battle outcome assessment"

FORMAT YOUR RESPONSE AS JSON:
{{
  "events": [
    {{
      "time": "00:00",
      "event_type": "movement|firing|construction|reconnaissance|engagement|logistics",
      "actor": "specific Pakistani/Indian unit name",
      "location": [longitude, latitude],
      "location_name": "Tiger Hill|Tololing|Point 5140|etc",
      "description": "Detailed description of the event with military specifics",
      "observable_by": ["ELINT", "IMINT", "TACINT"],
      "equipment_involved": ["specific equipment names"],
      "strength": "approximate number of troops/vehicles",
      "significance": "routine|important|critical"
    }},
    // ... 5 more events for remaining time slots
  ]
}}

ONLY RETURN THE JSON OBJECT WITH NO ADDITIONAL TEXT.
"""
        
        return prompt
    
    def _create_null_event(self, time_slot: str) -> Dict[str, Any]:
        """Create a minimal 'no significant activity' event"""
        return {
            "time": time_slot,
            "event_type": "routine",
            "actor": "Various units",
            "location": [76.1315, 34.5535],
            "location_name": "Kargil Sector",
            "description": "Routine patrol and defensive positioning. No significant enemy activity observed.",
            "observable_by": ["TACINT"],
            "equipment_involved": [],
            "strength": "patrol-sized",
            "significance": "routine"
        }