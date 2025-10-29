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


class ImintGenerator:
    """Generate IMINT (Imagery Intelligence) data with proper correlation"""
    
    SYSTEM_PROMPT = """You are an IMINT (Imagery Intelligence) analyst reviewing satellite imagery.

CRITICAL RULES:
1. Overhead perspective ONLY - describe what's visible from directly above
2. Include weather constraints (cloud cover affects image quality)
3. Use confidence qualifiers: CONFIRMED/PROBABLE/POSSIBLE based on image quality
4. Count ranges, NOT exact numbers (e.g., "10-12 vehicles")
5. GPS-quality coordinates (±50m accuracy)
6. NO electronic signals - only physical observations
7. ALWAYS provide realistic coordinates within Kargil sector (lat 34.4-34.8, long 75.7-76.5)
8. ALWAYS provide realistic non-zero values for all fields
9. CRITICAL: Include correlation_id field in EVERY record
10. Use specific location names from provided location data
11. Include technical imagery analysis terminology

SATELLITES: 
- CARTOSAT-3 (0.25m resolution, optical, weather-dependent)
- RISAT-2 (3m resolution, SAR radar, all-weather)

PAKISTANI EQUIPMENT VISIBLE FROM OVERHEAD:
- Al-Khalid MBT, T-59/69 tanks (distinctive thermal/visual signature)
- M113 APCs, Talha APCs (tracked vehicles, box-shaped)
- 130mm M-46 artillery, 122mm D-30 howitzers (towed artillery pieces)
- Supply vehicles, ammunition trucks (wheeled transport)
- Defensive positions, sangars, bunkers (overhead cover visible)

IMAGERY ANALYSIS TERMINOLOGY:
- "Overhead imagery reveals [count range] [equipment type]"
- "Thermal signature consistent with [equipment class]"
- "Vehicle spacing and formation indicates [tactical purpose]"
- "Defensive positions show evidence of [construction details]"
- "Track patterns suggest [movement type]"
- "Image resolution [X.Xm] permits [level of identification]"
- "Cloud cover [percentage] partially obscured [area]"
- "SAR imagery penetrated cloud cover to reveal [observation]"
- "Change detection analysis comparing [date] shows [development]"

EXAMPLE RECORD:
{
  "Date": "1999-06-15",
  "time": "10:35",
  "pre": "PRIORITY",
  "tgt_type": "VEHICLE",
  "tgt_sub_type": "ARMORED",
  "tgt_cl": "MAIN_BATTLE_TANK",
  "activity_type": "MOVEMENT",
  "activity_sub_type": "VEHICULAR",
  "activity_cl": "TACTICAL_DEPLOYMENT",
  "Incident_type": "FORCE_POSTURING",
  "Incident_sub_type": "EQUIPMENT_BUILDUP",
  "Incident_cl": "ARMOR_CONCENTRATION",
  "source_agency": "CARTOSAT-3",
  "grading": "B2",
  "str": "10-12 vehicles",
  "long": 76.1158,
  "lat": 34.5447,
  "ht": 4590,
  "e": 384251,
  "n": 3817136,
  "zone": "43S",
  "input": "Satellite pass #CS3-14256",
  "description": "CARTOSAT-3 overhead imagery (0.25m resolution) from satellite pass #CS3-14256 at 1035 hours reveals probable armored vehicle concentration in Tololing Summit area. Image analysis identifies 10-12 tracked vehicles with thermal and visual signatures consistent with main battle tanks, likely Al-Khalid or T-series variants. Vehicles positioned in tactical column formation with approximately 50-meter spacing, oriented northeast along ridgeline. Defensive positions visible with overhead cover indicating prepared firing positions. Weather conditions 20% cloud cover, excellent visibility. Track patterns in surrounding terrain suggest recent tactical movement from western approach. Vehicle disposition and spacing indicates battalion-strength armored element staged for offensive operations. Change detection analysis comparing imagery from 48 hours prior shows fresh vehicle tracks and new defensive works construction. Assessment: PROBABLE Pakistani armored company conducting tactical deployment in preparation for assault operations.",
  "upload_time": "1999-06-15 11:15",
  "correlation_id": "CORR_0042"
}

FORMAT: Return JSON with "imint_records" array.
CRITICAL: Every record MUST include correlation_id field!"""
    
    def __init__(self, correlation_manager: CorrelationManager):
        self.client = AnthropicClient(
            api_key=ANTHROPIC_API_KEY,
            model=MODEL_CONFIG["model"],
            max_tokens=MODEL_CONFIG["max_tokens"],
            temperature=MODEL_CONFIG["temperature"]
        )
        self.correlation_manager = correlation_manager
        self.unit_fmn_codes = OBSERVING_UNITS["IMINT"]
        self.unit_rotation_index = 0
    
    def generate_imint_data(self, scenario: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate IMINT data for complete scenario"""
        
        logger.info("="*80)
        logger.info("GENERATING IMINT DATA (Imagery Intelligence)")
        logger.info("="*80)
        
        all_imint_records = []
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
                    if corr_pkg and "IMINT" in corr_pkg["source_observations"]:
                        correlation_packages.append(corr_pkg)
            
            if not correlation_packages:
                logger.warning(f"No IMINT-observable events for {date}, skipping")
                continue
            
            # Generate records
            prompt = self._create_enhanced_imint_prompt(date, correlation_packages)
            
            try:
                batch_response = self.client.generate_structured_data(
                    prompt,
                    system_prompt=self.SYSTEM_PROMPT
                )
                batch_records = batch_response.get("imint_records", [])
                
                expected_count = len(correlation_packages)
                if len(batch_records) != expected_count:
                    logger.warning(
                        f"Expected {expected_count} IMINT records for {date}, "
                        f"got {len(batch_records)}"
                    )
                
                valid_records = []
                for idx, record in enumerate(batch_records[:expected_count]):
                    # Validate correlation_id
                    if not record.get("correlation_id"):
                        logger.error(f"IMINT record {idx} missing correlation_id!")
                        if idx < len(correlation_packages):
                            record["correlation_id"] = correlation_packages[idx]["correlation_id"]
                            logger.info(f"  Assigned correlation_id: {record['correlation_id']}")
                    
                    # Validate and clean
                    record = self._validate_and_clean_record(record)
                    
                    # Add metadata
                    record["id"] = record_id
                    record_id += 1
                    
                    # Add unit information
                    fmn_code = self.unit_fmn_codes[self.unit_rotation_index % len(self.unit_fmn_codes)]
                    self.unit_rotation_index += 1
                    
                    unit_info = FORMATION_MAPPING[fmn_code].copy()
                    unit_info["fmn_code"] = fmn_code
                    record.update(unit_info)
                    
                    valid_records.append(record)
                
                all_imint_records.extend(valid_records)
                logger.info(f"  ✓ Generated {len(valid_records)} IMINT records")
                
            except Exception as e:
                logger.error(f"Error generating IMINT for {date}: {e}", exc_info=True)
                continue
        
        # Save output
        output_path = os.path.join(OUTPUT_DIR, f"imint_data_{scenario['scenario_name']}.json")
        with open(output_path, 'w') as f:
            json.dump(all_imint_records, f, indent=2)
        
        logger.info(f"✓ IMINT generation complete: {len(all_imint_records)} records")
        logger.info(f"✓ Saved to: {output_path}")
        
        return all_imint_records
    
    def _create_enhanced_imint_prompt(self, date: str, correlation_packages: List[Dict]) -> str:
        """Create enhanced prompt with imagery analysis terminology"""
        
        events_summary = []
        for pkg in correlation_packages:
            gt = pkg["ground_truth"]
            imint_obs = pkg["source_observations"]["IMINT"]
            
            adjusted_time = self.correlation_manager.apply_time_adjustment(
                gt["time"],
                imint_obs["time_offset_minutes"]
            )
            
            events_summary.append({
                "corr_id": pkg["correlation_id"],
                "observation_time": adjusted_time,
                "actor": gt["actor"],
                "activity": gt["event_type"],
                "location": gt["location"],
                "location_name": gt.get("location_name", ""),
                "equipment": gt.get("equipment_involved", []),
                "strength": gt.get("strength", ""),
                "weather": imint_obs["observable_details"].get("weather_factor", "20% cloud cover"),
                "image_quality": imint_obs["observable_details"].get("image_quality", "good"),
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

Generate EXACTLY {len(events_summary)} IMINT (Imagery Intelligence) records for these satellite observations:

EVENTS TO GENERATE IMINT FOR:
{json.dumps(events_summary, indent=1)}

OBSERVATION METHOD EXAMPLES (use similar technical language):
{chr(10).join(['• ' + om for om in observation_methods])}

EQUIPMENT CONTEXT (for identification):
{chr(10).join(['• ' + e for e in equipment_pak])}

Each record must include ALL fields with realistic values:

REQUIRED FIELDS:
- Date: "{date}"
- time: (observation time from event, format "HH:MM")
- pre: "PRIORITY" | "ROUTINE" | "IMMEDIATE"
- tgt_type: "VEHICLE" | "PERSONNEL" | "INSTALLATION" | "EQUIPMENT"
- tgt_sub_type: e.g., "ARMORED" | "INFANTRY" | "COMMAND_POST" | "ARTILLERY"
- tgt_cl: e.g., "MAIN_BATTLE_TANK" | "LIGHT_INFANTRY" | "HQ_FACILITY" | "FIELD_GUN"
- activity_type: "MOVEMENT" | "COMBAT" | "CONSTRUCTION" | "RECONNAISSANCE" | "LOGISTICS"
- activity_sub_type: e.g., "VEHICULAR" | "DIRECT_FIRE" | "DEFENSIVE_POSITION" | "PATROL"
- activity_cl: e.g., "TACTICAL_DEPLOYMENT" | "ENGAGEMENT" | "FORTIFICATION" | "RECONNAISSANCE_PATROL"
- Incident_type: "FORCE_POSTURING" | "BORDER_VIOLATION" | "CEASEFIRE_VIOLATION" | "CONFRONTATION"
- Incident_sub_type: e.g., "EQUIPMENT_BUILDUP" | "TROOP_INCURSION" | "ARTILLERY_FIRE"
- Incident_cl: e.g., "ARMOR_CONCENTRATION" | "ARMED_INCURSION" | "INDIRECT_FIRE"
- source_agency: "CARTOSAT-3" or "RISAT-2"
- grading: "A1" | "A2" | "B1" | "B2" | "C3" (based on image quality and confidence)
- str: (count range like "10-12 vehicles" or "company-strength, approximately 120 personnel")
- long: (use from location above, or 76.0-76.6)
- lat: (use from location above, or 34.4-34.7)
- ht: (use from location or 3000-5000)
- e: (easting in meters 383000-385000)
- n: (northing in meters 3815000-3820000)
- zone: "43S"
- input: (e.g., "Satellite pass #CS3-14256" or "RISAT-2 SAR acquisition #RS2-08942")
- description: (150-250 words, overhead perspective, imagery analysis terminology)
- upload_time: "{date} HH:MM" (30-60 min after observation for processing time)
- correlation_id: (CRITICAL - MUST match corr_id from event)

DESCRIPTION REQUIREMENTS (150-250 words):
1. Start with satellite/sensor identification: "[Satellite name] overhead imagery ([resolution]) from satellite pass #[ID]..."
2. Include observation time and conditions: "at [time] hours reveals..."
3. Describe what's visible from overhead: "Image analysis identifies [count range] [equipment type]..."
4. Include confidence level: "CONFIRMED" | "PROBABLE" | "POSSIBLE"
5. Describe vehicle/equipment signatures: "thermal and visual signatures consistent with..."
6. Include tactical disposition: "positioned in [formation type] with [spacing] spacing..."
7. Describe terrain context: "oriented [direction] along [terrain feature]..."
8. Note supporting evidence: "Defensive positions visible with..." or "Track patterns suggest..."
9. Weather impact: "Weather conditions [percentage] cloud cover, [visibility]..."
10. Change detection if relevant: "Change detection analysis comparing imagery from [timeframe] shows..."
11. Tactical assessment: "Vehicle disposition indicates..." or "Assessment: [confidence] [activity type]..."
12. Use ONLY overhead perspective - no ground-level observations

TECHNICAL IMAGERY TERMINOLOGY TO USE:
- "Overhead imagery reveals [observation]"
- "Image analysis identifies [equipment] with [signature type] signatures"
- "[Resolution] resolution permits [identification level]"
- "Thermal signature consistent with [equipment class]"
- "Vehicle spacing and formation indicates [tactical purpose]"
- "Defensive positions show evidence of [construction details]"
- "Track patterns in terrain suggest [movement activity]"
- "Weather conditions [percentage] cloud cover"
- "SAR imagery penetrated cloud cover to reveal [observation]"
- "Change detection analysis comparing [period] shows [change]"
- "Tactical disposition consistent with [unit type] deployment"
- "Overhead cover visible on [number] positions"

CRITICAL REQUIREMENTS:
1. MUST include correlation_id field matching corr_id from events
2. Use count ranges, not exact numbers (e.g., "10-12" not "11")
3. ONLY overhead perspective - cannot see faces, uniforms, or ground-level details
4. Include weather impact on image quality
5. Descriptions must be 150-250 words
6. Use exact location name from event data
7. Grading reflects image quality: A1/A2 = confirmed, B1/B2 = probable, C3 = possible
8. upload_time accounts for processing delay (30-60 min after observation)

EXAMPLE (use as style guide):
{{
  "Date": "{date}",
  "time": "10:35",
  "pre": "PRIORITY",
  "tgt_type": "VEHICLE",
  "tgt_sub_type": "ARMORED",
  "tgt_cl": "MAIN_BATTLE_TANK",
  "activity_type": "MOVEMENT",
  "activity_sub_type": "VEHICULAR",
  "activity_cl": "TACTICAL_DEPLOYMENT",
  "Incident_type": "FORCE_POSTURING",
  "Incident_sub_type": "EQUIPMENT_BUILDUP",
  "Incident_cl": "ARMOR_CONCENTRATION",
  "source_agency": "CARTOSAT-3",
  "grading": "B2",
  "str": "10-12 vehicles",
  "long": 76.1158,
  "lat": 34.5447,
  "ht": 4590,
  "e": 384251,
  "n": 3817136,
  "zone": "43S",
  "input": "Satellite pass #CS3-14256",
  "description": "CARTOSAT-3 overhead imagery (0.25m resolution) from satellite pass #CS3-14256 at 1035 hours reveals probable armored vehicle concentration in Tololing Summit area at elevation 4590 meters. Image analysis identifies 10-12 tracked vehicles with thermal and visual signatures consistent with main battle tanks, likely Al-Khalid or T-series variants based on hull dimensions and turret configuration visible in overhead perspective. Vehicles positioned in tactical column formation with approximately 50-meter spacing, oriented northeast along ridgeline toward Indian positions. Defensive positions visible with overhead cover indicating prepared firing positions and ammunition storage. Weather conditions 20% cloud cover, excellent visibility across target area. Track patterns in surrounding terrain suggest recent tactical movement from western approach routes, with vehicle traces visible in snow and loose soil. Vehicle disposition and spacing indicates battalion-strength armored element staged for offensive operations. Change detection analysis comparing imagery from 48 hours prior shows fresh vehicle tracks and new defensive works construction including sandbagged positions and probable command post locations. Assessment: PROBABLE Pakistani armored company conducting tactical deployment in preparation for assault operations against Indian forward positions.",
  "upload_time": "1999-06-15 11:15",
  "correlation_id": "CORR_0042"
}}

Return JSON: {{"imint_records": [... {len(events_summary)} records with correlation_id ...]}}

Generate the {len(events_summary)} IMINT records now:"""
        
        return prompt
    
    def _validate_and_clean_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean IMINT record"""
        
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
            logger.warning(f"IMINT description too short: {len(desc)} chars")
        
        return record