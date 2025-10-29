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


class ElintGenerator:
    """Generate ELINT (Electronic Intelligence) data with proper correlation and authentic language"""
    
    SYSTEM_PROMPT = """You are an ELINT (Electronic Intelligence) analyst generating detection records.

CRITICAL RULES:
1. Detect electronic emissions 10-15 minutes BEFORE physical activity
2. Use TECHNICAL language: "VHF burst transmission", "encrypted tactical net", "fire control radar active"
3. NO visual details - you CANNOT see tanks/troops, only electronic signatures
4. Identify equipment by electronic signature (e.g., "TRC-20H radio pattern detected")
5. Infer strength from communication volume, NOT direct observation
6. Location via triangulation (±500m accuracy)
7. ALWAYS provide realistic coordinates within Kargil sector (lat 34.4-34.8, long 75.7-76.5)
8. ALWAYS provide realistic non-zero values for all fields
9. CRITICAL: Include correlation_id field in EVERY record, matching the corr_id from input
10. Use authentic military communication terminology and technical language
11. Use specific location names from the provided location data

PAKISTANI EQUIPMENT SIGNATURES:
- Communications: TRC-20H Tactical Radio (VHF 30-76 MHz), HF Command Nets (3-30 MHz)
- Radars: AN/TPS-43 (surveillance), Crotale Fire Control, Type 305 early warning
- Data Links: Encrypted tactical data networks

TECHNICAL LANGUAGE REQUIREMENTS:
- "Intercepted encrypted voice traffic on VHF frequency XX.XXX MHz"
- "Direction finding triangulation places emission source at grid XXXXXX XXXXXXX"
- "Burst transmission pattern consistent with [equipment type] tactical radio"
- "Signal strength -XX dBm indicates transmitter range approximately XX.X kilometers"
- "Frequency hopping sequence detected across XX-XX MHz band"
- "Radio net discipline suggests [unit-level] command and control"
- "Traffic analysis indicates preparation for [tactical activity]"
- "COMSEC protocols observed include [security measures]"
- "Call sign patterns consistent with [unit type] operating procedures"

EXAMPLE RECORD:
{
  "date": "1999-06-15",
  "from_time": "08:05",
  "to_time": "08:48",
  "en": "Pakistani XII Corps - 12th Northern Light Infantry Bravo Company",
  "location": "Tololing Summit",
  "range": "12.5",
  "emitter_type": "COMMUNICATIONS",
  "emitter_name": "TRC-20H Tactical Radio",
  "frequency": "47.250",
  "long": 76.1158,
  "lat": 34.5447,
  "ht": 4590,
  "e": 384251,
  "n": 3817136,
  "zone": "43S",
  "description": "Intercepted encrypted VHF burst transmissions on frequency 47.250 MHz originating from Tololing Summit at 0805 hours local time. Direction finding analysis utilizing multiple monitoring stations (DF accuracy ±500m) places emission source at grid reference 384251 3817136, elevation 4590 meters. Signal analysis identifies emission pattern consistent with Pakistani TRC-20H tactical radio operating in secure voice mode with frequency hopping enabled. Transmission duration 43 minutes indicates sustained tactical communications, likely battalion-level coordination based on traffic volume and net discipline observed. Signal strength -78 dBm suggests transmitter operating at medium power (5-10W) at range of approximately 12.5 kilometers from primary intercept site. Communications security (COMSEC) protocols indicate professional military operation. Traffic analysis suggests preparation for tactical movement or position adjustment based on increased message frequency and call sign patterns. SIGINT assessment: Unit demonstrates secure communications capability and tactical proficiency. Intercepted traffic pattern correlates with known 12th Northern Light Infantry operating procedures.",
  "correlation_id": "CORR_0042"
}

FORMAT: Return JSON with "elint_records" array containing EXACTLY the requested number of records.
CRITICAL: Every record MUST include the correlation_id field matching the input!"""
    
    def __init__(self, correlation_manager: CorrelationManager):
        self.client = AnthropicClient(
            api_key=ANTHROPIC_API_KEY,
            model=MODEL_CONFIG["model"],
            max_tokens=MODEL_CONFIG["max_tokens"],
            temperature=MODEL_CONFIG["temperature"]
        )
        self.correlation_manager = correlation_manager
        self.unit_fmn_codes = OBSERVING_UNITS["ELINT"]
        self.unit_rotation_index = 0
    
    def generate_elint_data(self, scenario: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate ELINT data for complete scenario"""
        
        logger.info("="*80)
        logger.info("GENERATING ELINT DATA (Electronic Intelligence)")
        logger.info("="*80)
        
        all_elint_records = []
        timeline = scenario.get("timeline", [])
        record_id = 1
        
        total_days = len(timeline)
        
        for day_idx, day in enumerate(timeline, 1):
            date = day["date"]
            events = day.get("events", [])
            
            logger.info(f"Processing day {day_idx}/{total_days}: {date} ({len(events)} events)")
            
            # Get correlation packages for events
            correlation_packages = []
            for event in events:
                correlation_id = event.get("correlation_id")
                if correlation_id:
                    corr_pkg = self.correlation_manager.get_correlation_package(correlation_id)
                    if corr_pkg and "ELINT" in corr_pkg["source_observations"]:
                        correlation_packages.append(corr_pkg)
            
            if not correlation_packages:
                logger.warning(f"No ELINT-observable events for {date}, skipping")
                continue
            
            # Generate ELINT records for this day
            prompt = self._create_enhanced_elint_prompt(date, correlation_packages)
            
            try:
                batch_response = self.client.generate_structured_data(
                    prompt, 
                    system_prompt=self.SYSTEM_PROMPT
                )
                batch_records = batch_response.get("elint_records", [])
                
                # Validate record count
                expected_count = len(correlation_packages)
                if len(batch_records) != expected_count:
                    logger.warning(
                        f"Expected {expected_count} ELINT records for {date}, "
                        f"got {len(batch_records)}"
                    )
                
                # Process and validate records
                valid_records = []
                for idx, record in enumerate(batch_records[:expected_count]):
                    # Validate correlation_id exists
                    if not record.get("correlation_id"):
                        logger.error(f"ELINT record {idx} missing correlation_id!")
                        # Try to assign from correlation package
                        if idx < len(correlation_packages):
                            record["correlation_id"] = correlation_packages[idx]["correlation_id"]
                            logger.info(f"  Assigned correlation_id: {record['correlation_id']}")
                    
                    # Validate and clean numeric fields
                    record = self._validate_and_clean_record(record)
                    
                    # Add metadata
                    record["id"] = record_id
                    record_id += 1
                    
                    # Add unit information (rotate through units)
                    fmn_code = self.unit_fmn_codes[self.unit_rotation_index % len(self.unit_fmn_codes)]
                    self.unit_rotation_index += 1
                    
                    unit_info = FORMATION_MAPPING[fmn_code].copy()
                    unit_info["fmn_code"] = fmn_code
                    record.update(unit_info)
                    
                    valid_records.append(record)
                
                all_elint_records.extend(valid_records)
                logger.info(f"  ✓ Generated {len(valid_records)} ELINT records")
                
            except Exception as e:
                logger.error(f"Error generating ELINT for {date}: {e}", exc_info=True)
                continue
        
        # Save output
        output_path = os.path.join(OUTPUT_DIR, f"elint_data_{scenario['scenario_name']}.json")
        with open(output_path, 'w') as f:
            json.dump(all_elint_records, f, indent=2)
        
        logger.info(f"✓ ELINT generation complete: {len(all_elint_records)} records")
        logger.info(f"✓ Saved to: {output_path}")
        
        return all_elint_records
    
    def _create_enhanced_elint_prompt(self, date: str, correlation_packages: List[Dict]) -> str:
        """Create enhanced prompt with military language and technical details"""
        
        events_summary = []
        for pkg in correlation_packages:
            gt = pkg["ground_truth"]
            elint_obs = pkg["source_observations"]["ELINT"]
            
            adjusted_time = self.correlation_manager.apply_time_adjustment(
                gt["time"], 
                elint_obs["time_offset_minutes"]
            )
            
            events_summary.append({
                "corr_id": pkg["correlation_id"],
                "detection_time": adjusted_time,
                "actor": gt["actor"],
                "activity": gt["event_type"],
                "location": gt["location"],
                "location_name": gt.get("location_name", ""),
                "equipment": gt.get("equipment_involved", []),
                "strength": gt.get("strength", ""),
                "description_context": gt.get("description", "")[:200]
            })
        
        # Get technical language samples
        observation_methods = random.sample(
            MILITARY_INTELLIGENCE_LANGUAGE.get('observation_methods', []),
            min(3, len(MILITARY_INTELLIGENCE_LANGUAGE.get('observation_methods', [])))
        )
        
        equipment_pak = random.sample(
            MILITARY_INTELLIGENCE_LANGUAGE.get('equipment_specifics_pakistan', []),
            min(3, len(MILITARY_INTELLIGENCE_LANGUAGE.get('equipment_specifics_pakistan', [])))
        )
        
        prompt = f"""Date: {date}

Generate EXACTLY {len(events_summary)} ELINT (Electronic Intelligence) records for these electronic signal detections.

EVENTS TO GENERATE ELINT FOR:
{json.dumps(events_summary, indent=1)}

TECHNICAL REQUIREMENTS:
Each ELINT record detects electronic emissions 10-15 minutes BEFORE the physical activity described above.
Use TECHNICAL language and terminology throughout.

OBSERVATION METHOD EXAMPLES (use similar technical language):
{chr(10).join(['• ' + om for om in observation_methods])}

EQUIPMENT CONTEXT (for technical descriptions):
{chr(10).join(['• ' + e for e in equipment_pak])}

Each record must include ALL fields with realistic values (NO ZEROS, NO NULLS):

REQUIRED FIELDS:
- date: "{date}"
- from_time: (detection start time, 10-15 min BEFORE event time, format "HH:MM")
- to_time: (detection end time, format "HH:MM", typically 20-45 minutes duration)
- en: (enemy unit from actor above, be specific with full unit designation)
- location: (use location_name from event above)
- range: (SINGLE number, detection range in km, e.g., "12.5" NOT "12.5,15.2")
- emitter_type: "COMMUNICATIONS" | "RADAR" | "DATA_LINK" | "NAVIGATION"
- emitter_name: (specific equipment: "TRC-20H Tactical Radio" | "AN/TPS-43 Surveillance Radar" | "HF Command Net")
- frequency: (SINGLE number in MHz, e.g., "47.250" NOT "47.250,52.8")
- long: (longitude from location above, or nearby: 75.7-76.5)
- lat: (latitude from location above, or nearby: 34.4-34.8)
- ht: (height in meters, use from location or 3000-5000)
- e: (easting in meters 383000-385000)
- n: (northing in meters 3815000-3820000)
- zone: "43S"
- description: (150-250 words, TECHNICAL ELINT language, see requirements below)
- correlation_id: (CRITICAL - MUST match corr_id from event above)

DESCRIPTION REQUIREMENTS (150-250 words):
1. Start with technical detection details: "Intercepted encrypted VHF transmissions on frequency X.XXX MHz..."
2. Include direction finding analysis: "DF triangulation utilizing [number] monitoring stations places emission source at grid..."
3. Describe signal characteristics: "Signal pattern consistent with [equipment] tactical radio operating in..."
4. Include technical measurements: "Signal strength -XX dBm indicates transmitter range approximately X.X kilometers..."
5. Analyze communications security: "Frequency hopping enabled across XX-XX MHz band, encrypted voice mode..."
6. Assess tactical significance: "Traffic volume and net discipline suggests [unit-level] coordination..."
7. Analyze traffic patterns: "Increased message frequency characteristic of pre-[activity] coordination..."
8. Include call sign analysis: "Call sign patterns and network structure consistent with [unit] tactical communications..."
9. Add SIGINT assessment: "SIGINT assessment: Professional COMSEC practices observed. Unit demonstrates [capability]..."
10. Correlate with known operations: "Emission characteristics match known [unit] operating procedures for [operation type]..."
11. Use ONLY technical language - NO visual observations (can't see tanks, only detect signals)
12. Include specific technical terms: DF accuracy (±500m), signal strength in dBm, frequency hopping, net discipline
13. Reference the activity context but from ELINT perspective (radio traffic increases before movement)

TECHNICAL LANGUAGE TO USE:
- "Direction finding (DF) analysis utilizing multiple monitoring stations"
- "Signal strength measured at -XX dBm"
- "Burst transmission pattern detected"
- "Frequency hopping sequence observed across XX-XX MHz band"
- "Encrypted voice traffic on VHF/HF frequencies"
- "Radio net discipline suggests [unit level] command and control"
- "Traffic analysis indicates preparation for [tactical activity]"
- "COMSEC protocols observed include [specific measures]"
- "Call sign patterns consistent with [unit type]"
- "Emission pattern correlates with [equipment type] operating procedures"
- "Transmission duration XX minutes indicates sustained tactical communications"
- "Network structure consistent with [organizational level] tactical architecture"

CRITICAL REQUIREMENTS:
1. MUST include correlation_id field in EVERY record matching corr_id from events above
2. Use ONLY SINGLE numeric values (no commas, no lists) for frequency and range
3. NO visual descriptions - ELINT cannot see physical objects, only detect electronic signals
4. Use technical SIGINT terminology throughout
5. Descriptions must be 150-250 words
6. Detection time is 10-15 minutes BEFORE the event time listed above
7. Use exact location name from the event data provided

EXAMPLE (use as style guide, do not copy):
{{
  "date": "{date}",
  "from_time": "07:50",
  "to_time": "08:35",
  "en": "Pakistani XII Corps - 12th Northern Light Infantry Bravo Company",
  "location": "Tololing Summit",
  "range": "12.5",
  "emitter_type": "COMMUNICATIONS",
  "emitter_name": "TRC-20H Tactical Radio",
  "frequency": "47.250",
  "long": 76.1158,
  "lat": 34.5447,
  "ht": 4590,
  "e": 384251,
  "n": 3817136,
  "zone": "43S",
  "description": "Intercepted encrypted VHF burst transmissions on frequency 47.250 MHz originating from Tololing Summit at 0750 hours local time. Direction finding analysis utilizing three monitoring stations (DF accuracy ±500m) places emission source at grid reference 384251 3817136, elevation 4590 meters. Signal analysis identifies emission pattern consistent with Pakistani TRC-20H tactical radio operating in secure voice mode with frequency hopping capability enabled across 30-76 MHz band. Transmission duration 45 minutes indicates sustained tactical communications session, likely company-to-battalion coordination based on traffic volume patterns and net discipline observed. Signal strength measured at -78 dBm suggests transmitter operating at medium power setting (5-10W) at range of approximately 12.5 kilometers from primary intercept site. Communications security (COMSEC) protocols include voice encryption and frequency agility, indicating professional military communications discipline. Traffic analysis reveals increased message frequency and compressed transmission times characteristic of pre-movement coordination procedures. Call sign patterns and network structure consistent with 12th Northern Light Infantry battalion tactical communications architecture. SIGINT assessment: Unit demonstrates mature COMSEC practices and tactical communications proficiency. Intercepted traffic pattern and timing correlates with preparation for tactical displacement or offensive operation, as radio traffic typically increases 10-15 minutes prior to physical movement. Emission characteristics match known Pakistani Army tactical radio operating procedures for mountain warfare operations.",
  "correlation_id": "CORR_0042"
}}

Return JSON: {{"elint_records": [... {len(events_summary)} records with correlation_id ...]}}

Generate the {len(events_summary)} ELINT records now:"""
        
        return prompt
    
    def _validate_and_clean_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean ELINT record"""
        
        # Clean frequency field (common issue)
        if "frequency" in record:
            freq = str(record["frequency"])
            # Extract first number if comma-separated
            if "," in freq:
                freq = freq.split(",")[0].strip()
            record["frequency"] = freq
        
        # Clean range field
        if "range" in record:
            range_val = str(record["range"]).replace(" km", "").replace("km", "").strip()
            if "," in range_val:
                range_val = range_val.split(",")[0].strip()
            record["range"] = range_val
        
        # Ensure zone is string
        if "zone" in record:
            record["zone"] = str(record["zone"])
        
        # Validate coordinates are in expected range
        if "lat" in record:
            lat = float(record["lat"])
            if not (34.2 <= lat <= 34.9):
                logger.warning(f"Latitude {lat} outside Kargil sector, adjusting")
                record["lat"] = 34.5 + (lat % 0.5)
        
        if "long" in record:
            long_val = float(record["long"])
            if not (75.5 <= long_val <= 76.7):
                logger.warning(f"Longitude {long_val} outside Kargil sector, adjusting")
                record["long"] = 76.1 + (long_val % 0.6)
        
        # Validate description length
        desc = record.get("description", "")
        if len(desc) < 150:
            logger.warning(f"ELINT description too short: {len(desc)} chars")
        elif len(desc) > 300:
            logger.info(f"ELINT description length: {len(desc)} chars (acceptable)")
        
        return record