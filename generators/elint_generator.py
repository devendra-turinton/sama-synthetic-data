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


class ElintGenerator:
    """Generate ELINT (Electronic Intelligence) data with proper correlation"""
    
    # System prompt - sent once, reused for all calls
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

PAKISTANI EQUIPMENT SIGNATURES:
- Communications: TRC-20H Tactical Radio (VHF), HF/VHF Command Nets
- Radars: AN/TPS-43 (surveillance), Crotale Fire Control

EXAMPLE RECORD:
{
  "date": "1999-06-15",
  "from_time": "08:05",
  "to_time": "08:48",
  "en": "Pakistani XII Corps",
  "location": "Drass Sector",
  "range": "12.5",
  "emitter_type": "COMMUNICATIONS",
  "emitter_name": "TRC-20H Tactical Radio",
  "frequency": "345.2",
  "long": 75.7523,
  "lat": 34.4251,
  "ht": 3380,
  "e": 384251,
  "n": 3817136,
  "zone": "43S",
  "description": "Encrypted VHF burst transmissions detected...",
  "correlation_id": "CORR_0042"
}

FORMAT: Return JSON with "elint_records" array containing EXACTLY 6 records.
CRITICAL: Every record MUST include the correlation_id field!"""
    
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
        logger.info("GENERATING ELINT DATA")
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
            prompt = self._create_compact_prompt(date, correlation_packages)
            
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
    
    def _create_compact_prompt(self, date: str, correlation_packages: List[Dict]) -> str:
        """Create minimal prompt with event summaries"""
        
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
                "equipment": gt.get("equipment_involved", [])
            })
        
        prompt = f"""Date: {date}

Generate EXACTLY {len(events_summary)} ELINT records for these electronic detections:
{json.dumps(events_summary, indent=1)}

Each record must include ALL fields with realistic values (NO ZEROS, NO NULLS):
- date: "{date}"
- from_time: (detection start, e.g., "08:05")
- to_time: (detection end, e.g., "08:35")
- en: (enemy unit, e.g., "Pakistani XII Corps")
- location: (area name, e.g., "Drass Sector")
- range: (SINGLE number, detection range in km, e.g., "12.5")
- emitter_type: "COMMUNICATIONS" or "RADAR"
- emitter_name: (e.g., "TRC-20H Tactical Radio")
- frequency: (SINGLE number in MHz, e.g., "345.2" NOT "345.2,5.9")
- long: (longitude 75.7-76.5, e.g., 76.1234)
- lat: (latitude 34.4-34.8, e.g., 34.5123)
- ht: (height in meters 3000-5000, e.g., 3350)
- e: (easting in meters 383000-385000, e.g., 384250)
- n: (northing in meters 3815000-3820000, e.g., 3817000)
- zone: "43S"
- description: (2-3 sentences, technical ELINT language)
- correlation_id: (CRITICAL - MUST match corr_id from event above)

CRITICAL REQUIREMENTS:
1. MUST include correlation_id field in EVERY record
2. Use ONLY SINGLE numeric values (no commas, no lists)
3. NO visual descriptions (can't see tanks, only electronic signals)
4. Technical language only

Return JSON: {{"elint_records": [... {len(events_summary)} records with correlation_id ...]}}"""
        
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
        
        return record