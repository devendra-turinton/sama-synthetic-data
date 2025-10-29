import os
import json
import logging
import random
from typing import Dict, List, Any

from utils.anthropic_client import AnthropicClient
from utils.correlation_manager import CorrelationManager
from config import (OUTPUT_DIR, OBSERVING_UNITS, FORMATION_MAPPING,
                   ANTHROPIC_API_KEY, MODEL_CONFIG, MILITARY_INTELLIGENCE_LANGUAGE,
                   GEOGRAPHIC_AREAS_ENHANCED)

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
- Use formal military incident reporting language
- Include tactical context and actions taken

INCIDENT REPORTING RULES:
1. Focus on specific incidents (border violations, confrontations, engagements, buildups, ceasefire violations)
2. Include both str_own (friendly forces at incident location) and str_en (enemy forces involved)
3. Describe THIS SPECIFIC INCIDENT ONLY, not a day's summary or multiple incidents
4. Use formal incident reporting language with proper military terminology
5. Include tactical details: initial detection, force deployment, current status, actions taken
6. ALWAYS provide realistic coordinates (lat 34.4-34.8, long 75.7-76.5)
7. ALWAYS provide realistic non-zero values for all fields
8. Use specific location names from the Kargil sector
9. Reference specific Indian Army units deployed in response
10. Include time of initial detection, response time, and current incident status

INCIDENT CATEGORIES:
- BORDER_VIOLATION: Unauthorized crossing of Line of Control (troop/vehicle/aerial incursion)
- FORCE_POSTURING: Military buildup, equipment deployment, tactical positioning
- CEASEFIRE_VIOLATION: Exchange of fire (small arms, artillery, mortar fire)
- CONFRONTATION: Face-to-face encounters, standoffs, physical altercations
- INTELLIGENCE_ACTIVITY: Reconnaissance, surveillance, probing operations

FRIENDLY FORCE REPORTING (str_own):
- Specify Indian Army units by designation: "18 Grenadiers Charlie Company", "2 Rajputana Rifles platoon"
- Include supporting elements: "BSF Battalion 125 observation element", "192 Mountain Regiment artillery battery"
- Note unit strength: "One infantry company (120 personnel)", "Platoon-strength element (35 soldiers)"

ENEMY FORCE REPORTING (str_en):
- Specify Pakistani units when known: "12th Northern Light Infantry Bravo Company", "5th NLI battalion elements"
- Include equipment specifics: "10-12 Al-Khalid MBTs", "3x 130mm M-46 field guns", "Company-strength with supporting mortars"
- Use count ranges: "approximately 100-120 personnel", "8-10 armored vehicles"

INCIDENT STATUS:
- ONGOING: Incident still developing, forces in contact, situation not resolved
- COMPLETED: Incident concluded, forces disengaged, situation stabilized

EXAMPLE FULL REPORT:
{
  "Incident_date": "1999-06-15",
  "time": "08:15",
  "pre": "PRIORITY",
  "Incident_type": "BORDER_VIOLATION",
  "Incident_sub_type": "TROOP_INCURSION",
  "Incident_cl": "ARMORED_COLUMN",
  "source": "70 Infantry Brigade Intelligence Section",
  "str_own": "18 Grenadiers Charlie Company (120 personnel), BSF Battalion 125 observation element, 192 Mountain Regiment artillery battery on standby",
  "str_en": "Pakistani 12th Northern Light Infantry armored company, 10-12 Al-Khalid main battle tanks with supporting infantry estimated 80-100 personnel",
  "long": 76.1158,
  "lat": 34.5447,
  "ht": 4590,
  "e": 384251,
  "n": 3817136,
  "zone": "43S",
  "Incident_states": "ONGOING",
  "description": "Pakistani armored company from 12th Northern Light Infantry comprising 10-12 Al-Khalid main battle tanks with supporting infantry crossed Line of Control at Tololing Summit at 08:15 hours local time. Initial detection by BSF Observation Post Delta-7 at 08:10 hours, immediately reported to 70 Infantry Brigade headquarters. Indian forces responded by deploying 18 Grenadiers Charlie Company (120 personnel) to defensive positions along ridgeline with interlocking fields of fire. 192 Mountain Regiment artillery battery placed on standby for immediate fire support mission. Incident status ONGOING as of 08:45 hours, opposing forces in visual contact at range 1.2 kilometers. Pakistani forces established hasty defensive positions on dominant terrain. No exchange of fire reported to this time. Indian forces maintaining defensive posture with observation and reporting of enemy movements. Brigade commander has authorized rules of engagement for defensive fire if approached within 500 meters. Additional reinforcements from 2 Rajputana Rifles moving to support positions, estimated arrival 09:30 hours.",
  "upload_time": "1999-06-15 08:45"
}

FORMAT: JSON with "sitrep_records" array.
IMPORTANT: Generate incident reports based on significant events, typically 3-6 per day depending on operational tempo."""
    
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
            
            prompt = self._create_enhanced_sitrep_prompt(date, significant_events, day_activities, day)
            
            try:
                response = self.client.generate_structured_data(
                    prompt,
                    system_prompt=self.SYSTEM_PROMPT
                )
                sitreps = response.get("sitrep_records", [])
                
                if not isinstance(sitreps, list):
                    logger.error(f"Invalid sitrep response format: {type(sitreps)}")
                    continue
                
                valid_records = []
                for record in sitreps:
                    if not isinstance(record, dict):
                        logger.warning(f"Skipping non-dict sitrep record: {type(record)}")
                        continue
                    
                    # Validate description length
                    desc = record.get("description", "")
                    if len(desc) < 100:
                        logger.warning(f"SITREP description too short: {len(desc)} chars")
                    
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
                    
                    valid_records.append(record)
                
                all_sitreps.extend(valid_records)
                logger.info(f"  ✓ Generated {len(valid_records)} e_sitrep records")
                
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
    
    def _create_enhanced_sitrep_prompt(self, date: str, events: List[Dict],
                                       enemy_activities: List[Dict],
                                       day_context: Dict[str, Any]) -> str:
        """Create enhanced prompt for incident-based e_sitrep generation"""
        
        # Summarize significant events with full context
        event_summaries = []
        for event in events:
            event_summaries.append({
                "time": event.get("time"),
                "event_type": event.get("event_type"),
                "actor": event.get("actor"),
                "location": event.get("location"),
                "location_name": event.get("location_name"),
                "equipment": event.get("equipment_involved", []),
                "strength": event.get("strength", ""),
                "significance": event.get("significance", "routine"),
                "description_excerpt": event.get("description", "")[:150]
            })
        
        # Get Indian Army units for friendly force reporting
        indian_units = random.sample(
            MILITARY_INTELLIGENCE_LANGUAGE.get('indian_units', []),
            min(5, len(MILITARY_INTELLIGENCE_LANGUAGE.get('indian_units', [])))
        )
        
        # Get Pakistani units for enemy force reporting
        pak_units = random.sample(
            MILITARY_INTELLIGENCE_LANGUAGE.get('pakistani_units', []),
            min(5, len(MILITARY_INTELLIGENCE_LANGUAGE.get('pakistani_units', [])))
        )
        
        # Get tactical assessment language
        assessments = random.sample(
            MILITARY_INTELLIGENCE_LANGUAGE.get('intelligence_assessments', []),
            min(3, len(MILITARY_INTELLIGENCE_LANGUAGE.get('intelligence_assessments', [])))
        )
        
        # Historical context for the day
        historical_context = day_context.get("historical_context", {})
        phase = historical_context.get("phase", "unknown")
        key_event = historical_context.get("key_event", "Operational activities continue")
        
        prompt = f"""Date: {date}
Phase: {phase}
Historical Context: {key_event}

Significant incidents/events today requiring e_sitrep reporting:
{json.dumps(event_summaries, indent=1)}

INDIAN ARMY UNITS AVAILABLE FOR DEPLOYMENT (use specific unit names in str_own):
{chr(10).join(['• ' + u for u in indian_units])}

PAKISTANI UNITS IDENTIFIED (use specific unit names in str_en):
{chr(10).join(['• ' + u for u in pak_units])}

TACTICAL ASSESSMENT LANGUAGE (use similar style):
{chr(10).join(['• ' + a for a in assessments])}

Generate {len(event_summaries)} Electronic Situation Reports (e_sitrep), one for each significant incident.

Each e_sitrep record must include ALL fields with realistic values:

REQUIRED FIELDS:
- Incident_date: "{date}"
- time: (incident time from event, format "HH:MM")
- pre: "PRIORITY" | "IMMEDIATE" | "ROUTINE"
- Incident_type: "BORDER_VIOLATION" | "FORCE_POSTURING" | "CEASEFIRE_VIOLATION" | "CONFRONTATION" | "INTELLIGENCE_ACTIVITY"
- Incident_sub_type: e.g., "TROOP_INCURSION" | "EQUIPMENT_BUILDUP" | "ARTILLERY_FIRE" | "ARMED_STANDOFF" | "RECONNAISSANCE"
- Incident_cl: e.g., "ARMED_INCURSION" | "ARMOR_CONCENTRATION" | "INDIRECT_FIRE" | "PHYSICAL_CONFRONTATION" | "PROBING_OPERATION"
- source: (reporting unit, e.g., "70 Infantry Brigade Intelligence Section" | "Battalion observation post" | "Brigade tactical operations center")
- str_own: (DETAILED friendly forces, use SPECIFIC unit names from list above, include strength numbers and supporting elements)
  Example: "18 Grenadiers Charlie Company (120 personnel), BSF Battalion 125 observation element, 192 Mountain Regiment artillery battery on standby"
- str_en: (DETAILED enemy forces, use SPECIFIC Pakistani unit names from list above, include equipment and estimated strength)
  Example: "Pakistani 12th Northern Light Infantry armored company, 10-12 Al-Khalid main battle tanks with supporting infantry estimated 80-100 personnel"
- long: (use from event location, or 76.0-76.6)
- lat: (use from event location, or 34.4-34.7)
- ht: (use from event location or 3000-5000)
- e: (easting in meters 383000-385000)
- n: (northing in meters 3815000-3820000)
- zone: "43S"
- Incident_states: "ONGOING" | "COMPLETED"
- description: (150-200 words, formal incident report, see structure below)
- upload_time: "{date} HH:MM" format (shortly after incident, typically +30 min)

DESCRIPTION STRUCTURE (150-200 words, 4-6 sentences):

Sentence 1: Incident identification with specific units and location
  Example: "Pakistani armored company from 12th Northern Light Infantry comprising 10-12 Al-Khalid main battle tanks with supporting infantry crossed Line of Control at Tololing Summit at 08:15 hours local time."

Sentence 2: Initial detection and reporting chain
  Example: "Initial detection by BSF Observation Post Delta-7 at 08:10 hours, immediately reported to 70 Infantry Brigade headquarters with priority classification."

Sentence 3-4: Indian force response and deployment
  Example: "Indian forces responded by deploying 18 Grenadiers Charlie Company (120 personnel) to defensive positions along ridgeline with interlocking fields of fire. 192 Mountain Regiment artillery battery placed on standby for immediate fire support mission with pre-plotted defensive fire concentrations."

Sentence 5: Current tactical situation
  Example: "Incident status ONGOING as of [time] hours, opposing forces in visual contact at range 1.2 kilometers. Pakistani forces established hasty defensive positions on dominant terrain. No exchange of fire reported to this time."

Sentence 6: Current Indian posture and next actions
  Example: "Indian forces maintaining defensive posture with continuous observation and reporting of enemy movements. Brigade commander has authorized rules of engagement for defensive fire if approached within 500 meters. Additional reinforcements from 2 Rajputana Rifles moving to support positions, estimated arrival [time] hours."

CRITICAL REQUIREMENTS:
1. Each e_sitrep reports ONE SPECIFIC INCIDENT ONLY, not a daily summary or multiple incidents
2. Include BOTH detailed friendly forces (str_own) AND enemy forces (str_en) with specific unit names
3. Use SPECIFIC Indian Army unit names from the list provided (e.g., "18 Grenadiers Charlie Company" NOT "one infantry company")
4. Use SPECIFIC Pakistani unit names from the list provided (e.g., "12th Northern Light Infantry Bravo Company" NOT "Pakistani forces")
5. Include strength numbers: "120 personnel", "10-12 tanks", "company-strength (100-120 personnel)"
6. Mark incident status correctly: ONGOING (still developing, forces in contact) or COMPLETED (resolved, forces disengaged)
7. Description must be 150-200 words in formal military incident reporting style
8. Include tactical details: detection time, response time, current positions, ranges, actions taken
9. Use exact location name from event data
10. upload_time format: "YYYY-MM-DD HH:MM"
11. Report friendly force actions: deployment, positioning, support elements, reinforcements
12. Include rules of engagement, alert status changes, or tactical decisions made

DESCRIPTION LANGUAGE GUIDELINES:
- Start: "Pakistani [specific unit] comprising [equipment/strength] crossed/engaged/deployed..."
- Detection: "Initial detection by [unit] at [time] hours, immediately reported to [headquarters]"
- Response: "Indian forces responded by deploying [specific unit] ([strength]) to [tactical action]"
- Support: "[Artillery/other support] placed on standby for [mission type]"
- Status: "Incident status [ONGOING/COMPLETED] as of [time] hours, opposing forces [situation]"
- Posture: "Indian forces maintaining [posture] with [actions]. [Higher commander] has authorized [decision]"
- Follow-on: "Additional [units] moving to [action], estimated arrival [time]"

EXAMPLE RECORD (use as template):
{{
  "Incident_date": "{date}",
  "time": "08:15",
  "pre": "PRIORITY",
  "Incident_type": "BORDER_VIOLATION",
  "Incident_sub_type": "TROOP_INCURSION",
  "Incident_cl": "ARMORED_COLUMN",
  "source": "70 Infantry Brigade Intelligence Section",
  "str_own": "18 Grenadiers Charlie Company (120 personnel), BSF Battalion 125 observation element (25 personnel), 192 Mountain Regiment artillery battery (6x 155mm Bofors guns) on standby",
  "str_en": "Pakistani 12th Northern Light Infantry armored company, 10-12 Al-Khalid main battle tanks with supporting infantry estimated 80-100 personnel, 2x 60mm mortar section",
  "long": 76.1158,
  "lat": 34.5447,
  "ht": 4590,
  "e": 384251,
  "n": 3817136,
  "zone": "43S",
  "Incident_states": "ONGOING",
  "description": "Pakistani armored company from 12th Northern Light Infantry comprising 10-12 Al-Khalid main battle tanks with supporting infantry estimated 80-100 personnel and integral 60mm mortar section crossed Line of Control at Tololing Summit at 08:15 hours local time. Initial detection by BSF Observation Post Delta-7 at 08:10 hours utilizing thermal imaging equipment, immediately reported to 70 Infantry Brigade headquarters with priority classification due to armor threat. Indian forces responded within 15 minutes by deploying 18 Grenadiers Charlie Company (120 personnel) to prepared defensive positions along ridgeline with interlocking fields of fire and natural defilade. 192 Mountain Regiment artillery battery (6x 155mm Bofors FH-77B howitzers) placed on standby alert for immediate fire support mission with pre-plotted defensive fire concentrations registered on likely enemy approach routes and assembly areas. Incident status ONGOING as of 08:45 hours with opposing forces in visual contact at range 1.2 kilometers. Pakistani forces have established hasty defensive positions utilizing natural terrain on dominant high ground with overhead cover visible. No exchange of fire reported to this time, both forces maintaining tactical discipline. Indian forces maintaining defensive posture with continuous observation via thermal imagers and laser rangefinders, reporting all enemy movements to brigade tactical operations center. Brigade commander has authorized rules of engagement permitting defensive fire if Pakistani forces approach within 500 meters of Indian positions or demonstrate hostile intent through weapons orientation. Additional reinforcements from 2 Rajputana Rifles Delta Company moving to support positions on southern flank, estimated time of arrival 09:30 hours with 81mm mortar section for additional indirect fire support.",
  "upload_time": "1999-06-15 08:45"
}}

Return JSON: {{"sitrep_records": [... {len(event_summaries)} detailed incident reports ...]}}

Generate the {len(event_summaries)} comprehensive incident reports now:"""
        
        return prompt