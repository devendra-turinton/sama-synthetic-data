import os
import json
import logging
from typing import Dict, List, Any

from utils.anthropic_client import AnthropicClient
from utils.correlation_manager import CorrelationManager
from config import (OUTPUT_DIR, OBSERVING_UNITS, FORMATION_MAPPING,
                   ANTHROPIC_API_KEY, MODEL_CONFIG)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SitrepGenerator:
    """Generate Electronic Situation Reports (e_sitrep_mst) - Incident-based reporting"""
    
    SYSTEM_PROMPT = """You are a Battalion/Brigade commander reporting Electronic Situation Reports (e_sitrep).

CRITICAL: e_sitrep is INCIDENT-BASED reporting, NOT daily summaries!
- Generate ONE e_sitrep per significant incident/event
- Each report focuses on ONE specific incident
- Include both enemy AND friendly force information for that incident
- Report incident state (ONGOING or COMPLETED)

RULES:
1. Focus on specific incidents (border violations, confrontations, engagements, buildups)
2. Include both str_own (friendly forces) and str_en (enemy forces) for the incident
3. Describe the specific incident, not a day's summary
4. Use formal incident reporting language
5. Include tactical details relevant to this specific incident
6. ALWAYS provide realistic coordinates (lat 34.4-34.8, long 75.7-76.5)
7. ALWAYS provide realistic non-zero values

EXAMPLE:
{
  "Incident_date": "1999-06-15",
  "time": "08:15",
  "pre": "PRIORITY",
  "Incident_type": "BORDER_VIOLATION",
  "Incident_sub_type": "TROOP_INCURSION",
  "Incident_cl": "ARMORED_COLUMN",
  "source": "Battalion observation post",
  "str_own": "One infantry company, BSF platoon",
  "str_en": "Pakistani armored company, 10-12 tanks",
  "long": 75.7530,
  "lat": 34.4248,
  "ht": 3376,
  "e": 384239,
  "n": 3817141,
  "zone": "43S",
  "Incident_states": "ONGOING",
  "description": "Pakistani armored company crossed LoC at Point 5140 at 08:15 hours. BSF observation post detected movement and alerted battalion. Indian forces deployed one infantry company to defensive positions. Incident ongoing, forces in visual contact. Artillery on standby.",
  "upload_time": "1999-06-15 08:45"
}

FORMAT: JSON with "sitrep_records" array.
IMPORTANT: Generate incident reports based on significant events, typically 3-6 per day."""
    
    def __init__(self, correlation_manager: CorrelationManager):
        self.client = AnthropicClient(
            api_key=ANTHROPIC_API_KEY,
            model=MODEL_CONFIG["model"],
            max_tokens=MODEL_CONFIG["max_tokens"],
            temperature=MODEL_CONFIG["temperature"]
        )
        self.correlation_manager = correlation_manager
        self.unit_fmn_codes = OBSERVING_UNITS["SITREP"]
        self.unit_rotation_index = 0
    
    def generate_sitrep_data(self,
                            scenario: Dict[str, Any],
                            enemy_activity_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate incident-based e_sitrep records"""
        
        logger.info("="*80)
        logger.info("GENERATING E_SITREP DATA (INCIDENT REPORTS)")
        logger.info("="*80)
        
        all_sitreps = []
        timeline = scenario.get("timeline", [])
        record_id = 1
        
        total_days = len(timeline)
        
        for day_idx, day in enumerate(timeline, 1):
            date = day["date"]
            events = day.get("events", [])
            
            logger.info(f"Processing day {day_idx}/{total_days}: {date} ({len(events)} events)")
            
            # Get enemy activities for this date (for context)
            day_activities = [
                a for a in enemy_activity_data
                if a.get("upload_time", "").startswith(date)
            ]
            
            # Filter significant events for sitrep reporting
            significant_events = [
                e for e in events
                if e.get("significance") in ["important", "critical"]
            ]
            
            # If no significant events, take first 3-4 events
            if not significant_events:
                significant_events = events[:4]
            
            if not significant_events:
                logger.warning(f"No events for {date}, skipping")
                continue
            
            prompt = self._create_incident_sitrep_prompt(date, significant_events, day_activities)
            
            try:
                response = self.client.generate_structured_data(
                    prompt,
                    system_prompt=self.SYSTEM_PROMPT
                )
                sitreps = response.get("sitrep_records", [])
                
                if not isinstance(sitreps, list):
                    logger.error(f"Invalid sitrep response format: {type(sitreps)}")
                    continue
                
                for record in sitreps:
                    if not isinstance(record, dict):
                        logger.warning(f"Skipping non-dict sitrep record: {type(record)}")
                        continue
                    
                    # Add metadata
                    record["id"] = record_id
                    record_id += 1
                    
                    # Add unit info (rotate through brigade HQs)
                    fmn_code = self.unit_fmn_codes[self.unit_rotation_index % len(self.unit_fmn_codes)]
                    self.unit_rotation_index += 1
                    
                    unit_info = FORMATION_MAPPING[fmn_code].copy()
                    unit_info["fmn_code"] = fmn_code
                    unit_info["level"] = "Brigade"
                    record.update(unit_info)
                    
                    all_sitreps.append(record)
                
                logger.info(f"  ✓ Generated {len(sitreps)} e_sitrep records")
                
            except Exception as e:
                logger.error(f"Error generating e_sitrep for {date}: {e}", exc_info=True)
                continue
        
        # Save output
        output_path = os.path.join(OUTPUT_DIR, f"sitrep_data_{scenario['scenario_name']}.json")
        with open(output_path, 'w') as f:
            json.dump(all_sitreps, f, indent=2)
        
        logger.info(f"✓ e_sitrep generation complete: {len(all_sitreps)} records")
        logger.info(f"✓ Saved to: {output_path}")
        
        return all_sitreps
    
    def _create_incident_sitrep_prompt(self, date: str, events: List[Dict],
                                       enemy_activities: List[Dict]) -> str:
        """Create prompt for incident-based e_sitrep generation"""
        
        # Summarize significant events
        event_summaries = []
        for event in events:
            event_summaries.append({
                "time": event.get("time"),
                "event_type": event.get("event_type"),
                "actor": event.get("actor"),
                "location_name": event.get("location_name"),
                "equipment": event.get("equipment_involved", []),
                "strength": event.get("strength", ""),
                "significance": event.get("significance", "routine"),
                "description": event.get("description", "")[:100]
            })
        
        prompt = f"""Date: {date}

Significant incidents/events today requiring e_sitrep reporting:
{json.dumps(event_summaries, indent=1)}

Generate {len(event_summaries)} Electronic Situation Reports (e_sitrep), one for each significant incident.

Each e_sitrep record must include:
- Incident_date: "{date}"
- time: (incident time, e.g., "08:15")
- pre: "PRIORITY", "IMMEDIATE", or "ROUTINE"
- Incident_type: e.g., "BORDER_VIOLATION", "FORCE_POSTURING", "CEASEFIRE_VIOLATION"
- Incident_sub_type: e.g., "TROOP_INCURSION", "EQUIPMENT_BUILDUP", "ARTILLERY_FIRE"
- Incident_cl: e.g., "ARMED_INCURSION", "ARMOR_CONCENTRATION", "INDIRECT_FIRE"
- source: "Battalion observation post" or "Brigade intelligence"
- str_own: (friendly forces at incident, e.g., "One infantry company, BSF platoon")
- str_en: (enemy forces at incident, e.g., "Pakistani armored company, 10-12 tanks")
- long: (76.0-76.6)
- lat: (34.4-34.7)
- ht: (3000-5000)
- e: (383000-385000)
- n: (3815000-3820000)
- zone: "43S"
- Incident_states: "ONGOING" or "COMPLETED"
- description: (Describe THIS SPECIFIC INCIDENT - what happened, when, where, current status, actions taken. 3-4 sentences. Focus on ONE incident, not the whole day.)
- upload_time: "{date} HH:MM" format (shortly after incident)

CRITICAL REQUIREMENTS:
1. Each e_sitrep reports ONE SPECIFIC INCIDENT, not a daily summary
2. Include both friendly (str_own) and enemy (str_en) forces
3. Mark status correctly (ONGOING if still developing, COMPLETED if resolved)
4. upload_time format: "YYYY-MM-DD HH:MM"

DESCRIPTION EXAMPLE:
"Pakistani armored company of 10-12 Al-Khalid tanks crossed Line of Control at Point 5140 at 08:15 hours. BSF observation post Delta-7 detected movement and alerted 70 Infantry Brigade. Indian forces deployed one infantry company from 18 Grenadiers to defensive positions with artillery support on standby. Incident ongoing, opposing forces in visual contact at 1.2km range. No exchange of fire reported."

Return JSON: {{"sitrep_records": [... {len(event_summaries)} incident reports ...]}}"""
        
        return prompt