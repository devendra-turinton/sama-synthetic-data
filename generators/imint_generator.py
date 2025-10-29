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

SATELLITES: CARTOSAT-3 (0.25m resolution), RISAT-2 (SAR, all-weather)
PAKISTANI EQUIPMENT: Al-Khalid MBT, T-59/69 tanks, M113 APCs, 130mm artillery

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
  "long": 75.7534,
  "lat": 34.4248,
  "ht": 3375,
  "e": 384235,
  "n": 3817142,
  "zone": "43S",
  "input": "Satellite pass #CS3-14256",
  "description": "PROBABLE convoy of armored vehicles...",
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
        logger.info("GENERATING IMINT DATA")
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
            prompt = self._create_compact_prompt(date, correlation_packages)
            
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
    
    def _create_compact_prompt(self, date: str, correlation_packages: List[Dict]) -> str:
        """Create compact prompt"""
        
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
                "image_quality": imint_obs["observable_details"].get("image_quality", "good")
            })
        
        prompt = f"""Date: {date}

Generate EXACTLY {len(events_summary)} IMINT records for these satellite observations:
{json.dumps(events_summary, indent=1)}

Each record must include ALL fields with realistic values:
- Date: "{date}"
- time: (observation time from event)
- pre: "PRIORITY", "ROUTINE", or "IMMEDIATE"
- tgt_type: e.g., "VEHICLE", "PERSONNEL", "INSTALLATION"
- tgt_sub_type: e.g., "ARMORED", "INFANTRY", "COMMAND_POST"
- tgt_cl: e.g., "MAIN_BATTLE_TANK", "LIGHT_INFANTRY", "HQ_FACILITY"
- activity_type: e.g., "MOVEMENT", "COMBAT", "CONSTRUCTION"
- activity_sub_type: e.g., "VEHICULAR", "DIRECT_FIRE", "DEFENSIVE_POSITION"
- activity_cl: e.g., "TACTICAL_DEPLOYMENT", "ENGAGEMENT", "FORTIFICATION"
- Incident_type: e.g., "FORCE_POSTURING", "BORDER_VIOLATION"
- Incident_sub_type: e.g., "EQUIPMENT_BUILDUP", "TROOP_INCURSION"
- Incident_cl: e.g., "ARMOR_CONCENTRATION", "ARMED_INCURSION"
- source_agency: "CARTOSAT-3" or "RISAT-2"
- grading: "A1", "A2", "B1", "B2", or "C3"
- str: (count range like "10-12 vehicles")
- long: (76.0-76.6)
- lat: (34.4-34.7)
- ht: (3000-5000)
- e: (383000-385000)
- n: (3815000-3820000)
- zone: "43S"
- input: (e.g., "Satellite pass #CS3-14256")
- description: (2-3 sentences, overhead perspective, include weather)
- upload_time: "{date} HH:MM" (30 min after observation)
- correlation_id: (CRITICAL - MUST match corr_id from event)

Return JSON: {{"imint_records": [... {len(events_summary)} records with correlation_id ...]}}"""
        
        return prompt