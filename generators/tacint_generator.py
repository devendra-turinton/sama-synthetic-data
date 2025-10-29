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


class TacintGenerator:
    """Generate TACINT (Tactical Intelligence) data with proper correlation"""
    
    SYSTEM_PROMPT = """You are a ground observer (BSF/Army) reporting tactical intelligence.

CRITICAL RULES:
1. Ground-level perspective - describe what you SEE and HEAR
2. Report 10-45 minutes AFTER observing (reporting delay)
3. Narrative style - write like a soldier's field report
4. Include sensory details (sounds, visual cues, environmental conditions)
5. Grading: A1 (reliable, confirmed) to C3 (fairly reliable, possible)
6. Observation distance affects detail (closer = more detail)
7. ALWAYS provide realistic coordinates (lat 34.4-34.8, long 75.7-76.5)
8. ALWAYS provide realistic non-zero values for all fields
9. CRITICAL: Include correlation_id field in EVERY record

OBSERVATION METHODS:
- < 2km: Binoculars, clear identification
- 2-4km: Spotting scope, probable identification
- > 4km: Thermal imaging, difficult identification

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
  "long": 75.7528,
  "lat": 34.4246,
  "ht": 3378,
  "e": 384242,
  "n": 3817138,
  "zone": "43S",
  "input": "Visual observation with thermal imaging",
  "description": "Column of tracked vehicles observed at 10:40 hours...",
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
        logger.info("GENERATING TACINT DATA")
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
            prompt = self._create_compact_prompt(date, correlation_packages)
            
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
    
    def _create_compact_prompt(self, date: str, correlation_packages: List[Dict]) -> str:
        """Create compact prompt"""
        
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
                "grading": tacint_obs["observable_details"].get("grading", "A2")
            })
        
        prompt = f"""Date: {date}

Generate EXACTLY {len(events_summary)} TACINT records for these ground observations:
{json.dumps(events_summary, indent=1)}

Each record must include ALL fields with realistic values:
- Date: "{date}"
- time: (reporting time from event)
- pre: "PRIORITY", "ROUTINE", or "IMMEDIATE"
- tgt_type: e.g., "VEHICLE", "PERSONNEL"
- tgt_sub_type: e.g., "ARMORED", "INFANTRY"
- tgt_cl: e.g., "MAIN_BATTLE_TANK", "LIGHT_INFANTRY"
- activity_type: e.g., "MOVEMENT", "COMBAT"
- activity_sub_type: e.g., "VEHICULAR", "DIRECT_FIRE"
- activity_cl: e.g., "TACTICAL_DEPLOYMENT", "ENGAGEMENT"
- Incident_type: e.g., "BORDER_VIOLATION", "FORCE_POSTURING"
- Incident_sub_type: e.g., "TROOP_INCURSION", "EQUIPMENT_BUILDUP"
- Incident_cl: e.g., "ARMED_INCURSION", "ARMOR_CONCENTRATION"
- source_agency: (BSF OP name from config)
- grading: Use from event summary
- str: (count with qualifier like "approximately 11-13 vehicles")
- long: (76.0-76.6)
- lat: (34.4-34.7)
- ht: (3000-5000)
- e: (383000-385000)
- n: (3815000-3820000)
- zone: "43S"
- input: (observation method from summary)
- description: (narrative style, 3-4 sentences with sensory details)
- upload_time: "{date} HH:MM" (from reporting time)
- correlation_id: (CRITICAL - MUST match corr_id)

Return JSON: {{"tacint_records": [... {len(events_summary)} records with correlation_id ...]}}"""
        
        return prompt