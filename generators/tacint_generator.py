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


class TacintGenerator:
    """Generate TACINT (Tactical Intelligence) data with proper correlation"""
    
    SYSTEM_PROMPT = """You are a ground observer (BSF/Army forward post) reporting tactical intelligence.

CRITICAL RULES:
1. Ground-level perspective - describe what you SEE and HEAR from your observation post
2. Report 10-45 minutes AFTER observing (reporting delay for verification and communication)
3. Narrative style - write like a soldier's field report with sensory details
4. Include environmental conditions (visibility, weather, terrain obscuration)
5. Grading system: 
   - A1: Completely reliable source, confirmed by observer
   - A2: Usually reliable source, confirmed
   - B1: Fairly reliable source, probably true
   - B2: Fairly reliable source, possibly true
   - C3: Not usually reliable source, doubtfully true
6. Observation distance affects detail quality:
   - <2km: Clear identification with binoculars
   - 2-4km: Probable identification with spotting scope
   - >4km: Possible identification with thermal imaging
7. ALWAYS provide realistic coordinates (lat 34.4-34.8, long 75.7-76.5)
8. ALWAYS provide realistic non-zero values for all fields
9. CRITICAL: Include correlation_id field in EVERY record
10. Use specific location names from provided location data
11. Include sensory details: sounds of engines, dust clouds, visual cues

OBSERVATION METHODS BY DISTANCE:
- <1km: Naked eye observation, individual soldier identification possible
- 1-2km: Binoculars (Carl Zeiss 10x50), clear vehicle/equipment identification
- 2-4km: Spotting scope (20-60x), probable vehicle type identification
- >4km: Thermal imagers (Simrad LP7), heat signatures only, difficult precise identification

BSF/ARMY OBSERVATION CAPABILITIES:
- Visual observation (daytime, weather-dependent)
- Thermal imaging (day/night, weather-independent)
- Laser rangefinders (accurate distance measurement)
- Sound detection (vehicle engines, artillery fire, construction activity)
- Seismic sensors (vehicle movement detection)

EXAMPLE RECORD:
{
  "Date": "1999-06-15",
  "time": "10:55",
  "pre": "IMMEDIATE",
  "tgt_type": "VEHICLE",
  "tgt_sub_type": "ARMORED",
  "tgt_cl": "MAIN_BATTLE_TANK",
  "activity_type": "MOVEMENT",
  "activity_sub_type": "VEHICULAR",
  "activity_cl": "TACTICAL_DEPLOYMENT",
  "Incident_type": "BORDER_VIOLATION",
  "Incident_sub_type": "TROOP_INCURSION",
  "Incident_cl": "ARMORED_COLUMN",
  "source_agency": "BSF Observation Post Delta-7",
  "grading": "A2",
  "str": "11-13 vehicles",
  "long": 76.1158,
  "lat": 34.5447,
  "ht": 4590,
  "e": 384251,
  "n": 3817136,
  "zone": "43S",
  "input": "Visual observation with thermal imaging assist",
  "description": "Column of tracked armored vehicles first observed at 1040 hours from BSF Observation Post Delta-7 at range 2.8 kilometers utilizing Carl Zeiss 20x60 spotting scope with laser rangefinder. Counted 11-13 main battle tanks moving in tactical column formation along Tololing ridgeline, heading northeast toward Indian forward positions. Vehicle identification probable as Al-Khalid MBT based on distinctive hull profile and turret configuration visible through optics. Diesel engine sounds audible, characteristic of heavy tracked vehicles. Large dust cloud created by vehicle movement despite recent snow, indicating significant weight and track pressure. Thermal imaging confirms heat signatures consistent with recently operated armored vehicles. Weather conditions clear visibility, light winds from southwest. Vehicles maintaining tactical spacing of approximately 50 meters between each tank. Column movement deliberate and coordinated, suggesting professional military unit conducting tactical deployment. Lead vehicle equipped with mine plow attachment. Supporting infantry not observed, movement appears to be armor-only at this time. Assessment: Pakistani armored company moving into assault positions. Threat level assessed as immediate. BSF post has alerted brigade headquarters and artillery support is being requested.",
  "upload_time": "1999-06-15 11:12",
  "correlation_id": "CORR_0042"
}

FORMAT: Return JSON with "tacint_records" array.
CRITICAL: Every record MUST include correlation_id field!"""
    
    def __init__(self, correlation_manager: CorrelationManager):
        self.client = AnthropicClient(
            api_key=ANTHROPIC_API_KEY,
            model=MODEL_CONFIG["model"],
            max_tokens=MODEL_CONFIG["max_tokens"],
            temperature=MODEL_CONFIG["temperature"]
        )
        self.correlation_manager = correlation_manager
        self.unit_fmn_codes = OBSERVING_UNITS["TACINT"]
        self.unit_rotation_index = 0
    
    def generate_tacint_data(self, scenario: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate TACINT data for complete scenario"""
        
        logger.info("="*80)
        logger.info("GENERATING TACINT DATA (Tactical Intelligence)")
        logger.info("="*80)
        
        all_tacint_records = []
        timeline = scenario.get("timeline", [])
        record_id = 1
        
        total_days = len(timeline)
        
        for day_idx, day in enumerate(timeline, 1):
            date = day["date"]
            events = day.get("events", [])
            
            logger.info(f"Processing day {day_idx}/{total_days}: {date} ({len(events)} events)")
            
            # Get correlation packages
            correlation_packages = []
            for event in events:
                correlation_id = event.get("correlation_id")
                if correlation_id:
                    corr_pkg = self.correlation_manager.get_correlation_package(correlation_id)
                    if corr_pkg and "TACINT" in corr_pkg["source_observations"]:
                        correlation_packages.append(corr_pkg)
            
            if not correlation_packages:
                logger.warning(f"No TACINT-observable events for {date}, skipping")
                continue
            
            # Generate records
            prompt = self._create_enhanced_tacint_prompt(date, correlation_packages)
            
            try:
                batch_response = self.client.generate_structured_data(
                    prompt,
                    system_prompt=self.SYSTEM_PROMPT
                )
                batch_records = batch_response.get("tacint_records", [])
                
                expected_count = len(correlation_packages)
                if len(batch_records) != expected_count:
                    logger.warning(
                        f"Expected {expected_count} TACINT records for {date}, "
                        f"got {len(batch_records)}"
                    )
                
                valid_records = []
                for idx, record in enumerate(batch_records[:expected_count]):
                    # Validate correlation_id
                    if not record.get("correlation_id"):
                        logger.error(f"TACINT record {idx} missing correlation_id!")
                        if idx < len(correlation_packages):
                            record["correlation_id"] = correlation_packages[idx]["correlation_id"]
                            logger.info(f"  Assigned correlation_id: {record['correlation_id']}")
                    
                    # Validate and clean
                    record = self._validate_and_clean_record(record)
                    
                    # Add metadata
                    record["id"] = record_id
                    record_id += 1
                    
                    # Add unit information (rotate through multiple BSF posts)
                    fmn_code = self.unit_fmn_codes[self.unit_rotation_index % len(self.unit_fmn_codes)]
                    self.unit_rotation_index += 1
                    
                    unit_info = FORMATION_MAPPING[fmn_code].copy()
                    unit_info["fmn_code"] = fmn_code
                    record.update(unit_info)
                    
                    valid_records.append(record)
                
                all_tacint_records.extend(valid_records)
                logger.info(f"  ✓ Generated {len(valid_records)} TACINT records")
                
            except Exception as e:
                logger.error(f"Error generating TACINT for {date}: {e}", exc_info=True)
                continue
        
        # Save output
        output_path = os.path.join(OUTPUT_DIR, f"tacint_data_{scenario['scenario_name']}.json")
        with open(output_path, 'w') as f:
            json.dump(all_tacint_records, f, indent=2)
        
        logger.info(f"✓ TACINT generation complete: {len(all_tacint_records)} records")
        logger.info(f"✓ Saved to: {output_path}")
        
        return all_tacint_records
    
    def _create_enhanced_tacint_prompt(self, date: str, correlation_packages: List[Dict]) -> str:
        """Create enhanced prompt with ground observer perspective"""
        
        events_summary = []
        for pkg in correlation_packages:
            gt = pkg["ground_truth"]
            tacint_obs = pkg["source_observations"]["TACINT"]
            
            adjusted_time = self.correlation_manager.apply_time_adjustment(
                gt["time"],
                tacint_obs["time_offset_minutes"]
            )
            
            events_summary.append({
                "corr_id": pkg["correlation_id"],
                "reporting_time": adjusted_time,
                "actor": gt["actor"],
                "activity": gt["event_type"],
                "location": gt["location"],
                "location_name": gt.get("location_name", ""),
                "equipment": gt.get("equipment_involved", []),
                "strength": gt.get("strength", ""),
                "observer_distance": tacint_obs["observable_details"].get("observer_distance_km", 2.5),
                "observation_method": tacint_obs["observable_details"].get("observation_method", "Binoculars"),
                "grading": tacint_obs["observable_details"].get("grading", "A2"),
                "description_context": gt.get("description", "")[:200]
            })
        
        # Get observation method samples
        observation_methods = random.sample(
            MILITARY_INTELLIGENCE_LANGUAGE.get('observation_methods', []),
            min(3, len(MILITARY_INTELLIGENCE_LANGUAGE.get('observation_methods', [])))
        )
        
        equipment_pak = random.sample(
            MILITARY_INTELLIGENCE_LANGUAGE.get('equipment_specifics_pakistan', []),
            min(2, len(MILITARY_INTELLIGENCE_LANGUAGE.get('equipment_specifics_pakistan', [])))
        )
        
        prompt = f"""Date: {date}

Generate EXACTLY {len(events_summary)} TACINT (Tactical Intelligence) records for these ground observations:

EVENTS TO GENERATE TACINT FOR:
{json.dumps(events_summary, indent=1)}

OBSERVATION METHOD EXAMPLES (use similar style):
{chr(10).join(['• ' + om for om in observation_methods])}

EQUIPMENT CONTEXT (for visual identification):
{chr(10).join(['• ' + e for e in equipment_pak])}

Each record must include ALL fields with realistic values:

REQUIRED FIELDS:
- Date: "{date}"
- time: (reporting time from event, format "HH:MM")
- pre: "PRIORITY" | "ROUTINE" | "IMMEDIATE"
- tgt_type: "VEHICLE" | "PERSONNEL" | "INSTALLATION" | "EQUIPMENT"
- tgt_sub_type: e.g., "ARMORED" | "INFANTRY" | "COMMAND_POST" | "ARTILLERY"
- tgt_cl: e.g., "MAIN_BATTLE_TANK" | "LIGHT_INFANTRY" | "HQ_FACILITY" | "FIELD_GUN"
- activity_type: "MOVEMENT" | "COMBAT" | "CONSTRUCTION" | "RECONNAISSANCE" | "LOGISTICS"
- activity_sub_type: e.g., "VEHICULAR" | "DIRECT_FIRE" | "DEFENSIVE_POSITION" | "PATROL"
- activity_cl: e.g., "TACTICAL_DEPLOYMENT" | "ENGAGEMENT" | "FORTIFICATION" | "RECONNAISSANCE_PATROL"
- Incident_type: "BORDER_VIOLATION" | "FORCE_POSTURING" | "CEASEFIRE_VIOLATION" | "CONFRONTATION"
- Incident_sub_type: e.g., "TROOP_INCURSION" | "EQUIPMENT_BUILDUP" | "ARTILLERY_FIRE"
- Incident_cl: e.g., "ARMED_INCURSION" | "ARMOR_CONCENTRATION" | "INDIRECT_FIRE"
- source_agency: (BSF Observation Post name - use unit_name from formation mapping)
- grading: Use from event summary (A1, A2, B1, B2, or C3)
- str: (count with qualifier like "approximately 11-13 vehicles" or "company-strength, 100-120 personnel")
- long: (use from location above, or 76.0-76.6)
- lat: (use from location above, or 34.4-34.7)
- ht: (use from location or 3000-5000)
- e: (easting in meters 383000-385000)
- n: (northing in meters 3815000-3820000)
- zone: "43S"
- input: (observation method from summary, e.g., "Visual observation with Carl Zeiss 20x60 spotting scope")
- description: (150-250 words, narrative ground observer style with sensory details)
- upload_time: "{date} HH:MM" (from reporting time)
- correlation_id: (CRITICAL - MUST match corr_id)

DESCRIPTION REQUIREMENTS (150-250 words):
1. Start with initial observation: "[Equipment/activity type] first observed at [time] from [observation post name]..."
2. Include range and observation method: "at range [X.X] kilometers utilizing [equipment]..."
3. Provide count and identification: "Counted [range] [equipment] based on [visual characteristics]..."
4. Describe what was seen: "Vehicle identification [confirmed/probable/possible] as [type] based on [features]..."
5. Include sensory details: Sounds (engine noise, weapons fire), visuals (dust clouds, muzzle flashes), environmental (weather, terrain)
6. Describe tactical disposition: "positioned in [formation], oriented [direction]..."
7. Note movement or activity details: "moving at [speed], maintaining spacing of..."
8. Include supporting observations: thermal signatures, track patterns, associated equipment
9. Assess tactical significance: "movement suggests [tactical purpose]..."
10. Conclude with threat assessment: "Assessment: [evaluation]. Threat level: [level]. [Action taken]"
11. Use narrative soldier's report style, not clinical analytical language
12. Ground-level perspective only - describe what observer can actually see

TACTICAL OBSERVER LANGUAGE TO USE:
- "First observed at [time] from [observation post]"
- "Range determined by laser rangefinder as [distance]"
- "Counted approximately [range] [equipment type]"
- "Visual identification [confirmed/probable/possible] as [equipment]"
- "Diesel engine sounds audible from [distance]"
- "Dust cloud/snow disturbance indicates [activity]"
- "Thermal signatures consistent with [equipment type]"
- "Weather conditions: [visibility description]"
- "Maintaining tactical spacing of approximately [distance]"
- "Movement appears deliberate and coordinated"
- "Assessment: [tactical evaluation]"
- "BSF post has alerted [higher headquarters]"

CRITICAL REQUIREMENTS:
1. MUST include correlation_id field matching corr_id from events
2. Use count ranges with qualifiers ("approximately", "estimated")
3. Ground-level perspective ONLY - describe what observer sees from their position
4. Include sensory details (sounds, visual cues, environmental conditions)
5. Grading reflects observer confidence and source reliability
6. Descriptions must be 150-250 words in narrative soldier report style
7. Use exact location name from event data
8. Observer distance affects identification confidence (closer = more certain)
9. upload_time reflects reporting delay (10-45 min after observation)
10. Include specific observation equipment used

EXAMPLE (use as style guide):
{{
  "Date": "{date}",
  "time": "10:55",
  "pre": "IMMEDIATE",
  "tgt_type": "VEHICLE",
  "tgt_sub_type": "ARMORED",
  "tgt_cl": "MAIN_BATTLE_TANK",
  "activity_type": "MOVEMENT",
  "activity_sub_type": "VEHICULAR",
  "activity_cl": "TACTICAL_DEPLOYMENT",
  "Incident_type": "BORDER_VIOLATION",
  "Incident_sub_type": "TROOP_INCURSION",
  "Incident_cl": "ARMORED_COLUMN",
  "source_agency": "BSF Observation Post Delta-7",
  "grading": "A2",
  "str": "11-13 vehicles",
  "long": 76.1158,
  "lat": 34.5447,
  "ht": 4590,
  "e": 384251,
  "n": 3817136,
  "zone": "43S",
  "input": "Visual observation with Carl Zeiss 20x60 spotting scope and laser rangefinder",
  "description": "Column of tracked armored vehicles first observed at 1040 hours from BSF Observation Post Delta-7 at range 2.8 kilometers utilizing Carl Zeiss 20x60 spotting scope with integrated laser rangefinder. Counted approximately 11-13 main battle tanks moving in tactical column formation along Tololing Summit ridgeline, heading northeast toward Indian forward positions. Vehicle identification assessed as probable Al-Khalid MBT based on distinctive hull profile, turret configuration, and exhaust positioning visible through optical magnification. Diesel engine sounds clearly audible despite distance, characteristic deep rumble of heavy tracked vehicles with multi-fuel engines. Large dust cloud created by vehicle movement despite recent snow cover, indicating significant vehicle weight and track pressure exceeding 15 tons per square meter. Thermal imaging supplementary observation confirms heat signatures consistent with recently operated armored vehicles, engine compartments showing elevated thermal returns. Weather conditions provide clear visibility with light variable winds from southwest, temperature approximately 5 degrees Celsius. Vehicles maintaining tactical spacing of approximately 50 meters between each tank, standard Pakistani Army armor doctrine for mountain operations. Column movement deliberate and coordinated with visible hand/flag signals between vehicle commanders, suggesting professional military unit conducting tactical deployment. Lead vehicle equipped with mine plow attachment visible through optics. Supporting infantry not observed, movement appears to be armor-only element at this time. Assessment: Pakistani armored company, likely from 12th Northern Light Infantry attached armor, moving into assault staging positions. Threat level assessed as immediate to Indian forward positions. BSF observation post has alerted 70 Infantry Brigade headquarters via secure radio and artillery fire support is being coordinated.",
  "upload_time": "1999-06-15 11:12",
  "correlation_id": "CORR_0042"
}}

Return JSON: {{"tacint_records": [... {len(events_summary)} records with correlation_id ...]}}

Generate the {len(events_summary)} TACINT records now:"""
        
        return prompt
    
    def _validate_and_clean_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean TACINT record"""
        
        # Ensure zone is string
        if "zone" in record:
            record["zone"] = str(record["zone"])
        
        # Validate coordinates
        if "lat" in record:
            lat = float(record["lat"])
            if not (34.2 <= lat <= 34.9):
                logger.warning(f"Latitude {lat} outside Kargil sector")
        
        if "long" in record:
            long_val = float(record["long"])
            if not (75.5 <= long_val <= 76.7):
                logger.warning(f"Longitude {long_val} outside Kargil sector")
        
        # Validate description length
        desc = record.get("description", "")
        if len(desc) < 150:
            logger.warning(f"TACINT description too short: {len(desc)} chars")
        
        # Validate grading
        valid_gradings = ["A1", "A2", "B1", "B2", "C3"]
        if record.get("grading") not in valid_gradings:
            logger.warning(f"Invalid grading: {record.get('grading')}, defaulting to B2")
            record["grading"] = "B2"
        
        return record