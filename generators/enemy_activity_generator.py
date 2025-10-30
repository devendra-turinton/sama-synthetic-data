import os
import json
import logging
import asyncio
import random
from typing import Dict, List, Any
from datetime import datetime, timedelta

from utils.async_anthropic_client import AsyncAnthropicClient
from utils.correlation_manager import CorrelationManager
from config import (OUTPUT_DIR, OBSERVING_UNITS, FORMATION_MAPPING,
                   ANTHROPIC_API_KEY, MODEL_CONFIG, MILITARY_INTELLIGENCE_LANGUAGE)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnemyActivityGenerator:
    """
    Generate INDEPENDENT Enemy Activity observations from various sensor types.
    
    This is NOT fusion/correlation - each record represents an independent sensor observation
    of enemy activity. Multiple sensors can observe the same event (linked by correlation_id)
    but each generates its own independent perspective.
    
    Sensor Types:
    - GROUND_SURVEILLANCE_RADAR: Ground-based radar detecting movement
    - SEISMIC_SENSOR: Seismic detection of vehicle/troop movement
    - THERMAL_SENSOR: Thermal imaging arrays
    """
    
    SYSTEM_PROMPT = """You are generating independent sensor observations of enemy activity.

CRITICAL RULES:
1. Each record represents ONE SENSOR'S independent observation
2. DO NOT reference or cite other intelligence sources (ELINT, IMINT, TACINT)
3. Generate from THIS SENSOR'S perspective ONLY
4. Sensor types: GROUND_SURVEILLANCE_RADAR, SEISMIC_SENSOR,THERMAL_SENSOR
5. Each sensor has its own capabilities and limitations
6. ALWAYS provide realistic coordinates (lat 34.4-34.8, long 75.7-76.5)
7. ALWAYS include correlation_id field matching the event
8. Descriptions should reflect sensor-specific detection methods

SENSOR CAPABILITIES:

GROUND_SURVEILLANCE_RADAR:
- Detects movement via radar reflection
- Range: 10-20km
- Can detect: vehicles, groups of personnel, equipment
- Cannot identify specific equipment types (just "tracked vehicles", "wheeled vehicles")
- Provides bearing, range, speed, direction
- Example: "Ground surveillance radar detected multiple large tracked vehicles moving at bearing 275°..."

SEISMIC_SENSOR:
- Detects ground vibrations from vehicle/troop movement
- Range: 5-15km depending on terrain
- Can detect: vehicle movement, heavy equipment, large troop formations
- Provides: approximate location, vibration intensity, movement pattern
- Example: "Seismic sensors detected strong ground vibrations consistent with heavy tracked vehicle movement..."


THERMAL_SENSOR:
- Thermal imaging arrays detecting heat signatures
- Range: 3-10km
- Can detect: vehicle heat signatures, personnel groups, equipment
- Provides: thermal signatures, approximate count, heat intensity
- Example: "Thermal sensor array detected multiple high-intensity heat signatures consistent with vehicle engines..."

DESCRIPTION STRUCTURE (100-150 words):
1. Sensor identification and detection time
2. What the sensor detected (from its perspective only)
3. Technical measurements (bearing, range, intensity, etc.)
4. Sensor-specific details (radar return, seismic pattern, sound frequency, etc.)
5. Inferred activity type (based on sensor signature)
6. Assessment of confidence (based on sensor data quality)

EXAMPLE RECORD:
{
  "sensor_type": "GROUND_SURVEILLANCE_RADAR",
  "sensor_id": "GSR-14-CORPS-03",
  "tgt_type": "VEHICLE",
  "tgt_sub_type": "TRACKED_VEHICLE",
  "tgt_cl": "ARMORED_VEHICLE",
  "activity_type": "MOVEMENT",
  "activity_sub_type": "VEHICULAR",
  "activity_cl": "TACTICAL_DEPLOYMENT",
  "bearing": "275",
  "range_km": "12.5",
  "str": "Multiple tracked vehicles, estimated 10-15 units",
  "long": 76.1158,
  "lat": 34.5447,
  "ht": 4590,
  "e": 384251,
  "n": 3817136,
  "zone": "43S",
  "input_method": "Ground surveillance radar detection",
  "description": "Ground surveillance radar GSR-14-CORPS-03 detected multiple large tracked vehicles at bearing 275 degrees, range 12.5 kilometers from sensor location at 08:20 hours local time. Radar return signatures indicate 10-15 tracked vehicles moving in coordinated formation with spacing consistent with military tactical movement. Target velocity approximately 15-20 kilometers per hour across terrain toward grid reference 384251 3817136 at elevation 4590 meters in Tololing sector. Radar cross-section analysis suggests heavy armored vehicles based on reflection intensity and profile. Movement pattern indicates deliberate tactical displacement rather than administrative movement. Signal strength and Doppler analysis confirm targets are large metallic vehicles in column formation. Weather conditions clear, no atmospheric interference affecting detection. Assessed as probable enemy armored company conducting tactical movement based on number of vehicles, formation discipline, and movement toward known conflict area. Confidence level high based on clear radar returns and consistent tracking over 15-minute observation period.",
  "upload_time": "1999-06-15 08:30",
  "correlation_id": "CORR_0042"
}

FORMAT: Return JSON with "enemy_activity_records" array.
CRITICAL: Each record is INDEPENDENT - do not reference other intelligence sources!"""
    
    def __init__(self, correlation_manager: CorrelationManager):
        self.async_client = AsyncAnthropicClient(
            api_key=ANTHROPIC_API_KEY,
            model=MODEL_CONFIG["model"],
            max_tokens=MODEL_CONFIG["max_tokens"],
            temperature=MODEL_CONFIG["temperature"],
            max_concurrent=5  # Limit concurrent API calls
        )
        self.correlation_manager = correlation_manager
        self.unit_fmn_codes = OBSERVING_UNITS["FUSION"]  # Reusing for sensor units
        
        # Sensor types to generate
        self.sensor_types = [
            "GROUND_SURVEILLANCE_RADAR",
            "SEISMIC_SENSOR",
            "THERMAL_SENSOR"
        ]
    
    def generate_enemy_activity_data(self, scenario: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate independent enemy activity sensor observations - ASYNC"""
        
        logger.info("="*80)
        logger.info("GENERATING ENEMY ACTIVITY DATA (Independent Sensor Observations)")
        logger.info("="*80)
        
        # Run async generation
        loop = asyncio.get_event_loop()
        all_records = loop.run_until_complete(self._generate_async(scenario))
        
        # Save output
        output_path = os.path.join(OUTPUT_DIR, f"enemy_activity_data_{scenario['scenario_name']}.json")
        with open(output_path, 'w') as f:
            json.dump(all_records, f, indent=2)
        
        logger.info(f"✓ Enemy Activity generation complete: {len(all_records)} records")
        logger.info(f"✓ Saved to: {output_path}")
        
        return all_records
    
    async def _generate_async(self, scenario: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Async generation of all enemy activity records"""
        
        timeline = scenario.get("timeline", [])
        total_days = len(timeline)
        
        # Collect all generation tasks
        tasks = []
        
        for day_idx, day in enumerate(timeline, 1):
            date = day["date"]
            events = day.get("events", [])
            
            logger.info(f"Queuing day {day_idx}/{total_days}: {date} ({len(events)} events)")
            
            # Get events with correlation packages
            correlation_packages = []
            for event in events:
                correlation_id = event.get("correlation_id")
                if correlation_id:
                    corr_pkg = self.correlation_manager.get_correlation_package(correlation_id)
                    if corr_pkg:
                        # Check if ANY sensor type should observe this
                        # For now, we'll generate for events that have observable activity
                        if event.get("event_type") in ["movement", "firing", "construction", 
                                                       "reconnaissance", "engagement", "deployment"]:
                            correlation_packages.append(corr_pkg)
            
            if not correlation_packages:
                logger.warning(f"No observable events for {date}, skipping")
                continue
            
            # Create task for this day
            task = self._generate_day_async(date, correlation_packages)
            tasks.append(task)
        
        # Execute all tasks concurrently with progress tracking
        logger.info(f"Executing {len(tasks)} day generation tasks concurrently...")
        
        all_records = []
        for completed_task in asyncio.as_completed(tasks):
            day_records = await completed_task
            all_records.extend(day_records)
            logger.info(f"  ✓ Completed 1 day: {len(day_records)} records generated")
        
        return all_records
    
    async def _generate_day_async(self, date: str, correlation_packages: List[Dict]) -> List[Dict[str, Any]]:
        """Generate enemy activity records for one day asynchronously"""
        
        # For each event, generate 1-2 sensor observations
        tasks = []
        
        for pkg in correlation_packages:
            # Randomly select 1-2 sensor types for this event
            num_sensors = random.randint(1, 2)
            selected_sensors = random.sample(self.sensor_types, num_sensors)
            
            for sensor_type in selected_sensors:
                task = self._generate_single_observation_async(date, pkg, sensor_type)
                tasks.append(task)
        
        # Execute all observations for this day
        day_records = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and None values
        valid_records = []
        for record in day_records:
            if isinstance(record, Exception):
                logger.error(f"Error generating record: {record}")
            elif record is not None:
                valid_records.append(record)
        
        return valid_records
    
    async def _generate_single_observation_async(self, date: str, 
                                                 correlation_pkg: Dict[str, Any],
                                                 sensor_type: str) -> Dict[str, Any]:
        """Generate a single sensor observation asynchronously"""
        
        gt = correlation_pkg["ground_truth"]
        
        # Calculate sensor detection time (varies by sensor)
        sensor_time_offset = self._get_sensor_time_offset(sensor_type)
        detection_time = self.correlation_manager.apply_time_adjustment(
            gt["time"], 
            sensor_time_offset
        )
        
        # Create prompt
        prompt = self._create_sensor_observation_prompt(
            date, gt, sensor_type, detection_time, correlation_pkg["correlation_id"]
        )
        
        try:
            response = await self.async_client.generate_structured_data(
                prompt,
                system_prompt=self.SYSTEM_PROMPT
            )
            
            records = response.get("enemy_activity_records", [])
            
            if not records:
                logger.warning(f"No record generated for {correlation_pkg['correlation_id']}")
                return None
            
            record = records[0]  # Take first record
            
            # Validate correlation_id
            if not record.get("correlation_id"):
                record["correlation_id"] = correlation_pkg["correlation_id"]
            
            # Add metadata
            record["sensor_type"] = sensor_type
            record["sensor_id"] = self._get_sensor_id(sensor_type)
            
            # Add unit information
            fmn_code = self.unit_fmn_codes[0]
            unit_info = FORMATION_MAPPING[fmn_code].copy()
            unit_info["fmn_code"] = fmn_code
            record.update(unit_info)
            
            return record
            
        except Exception as e:
            logger.error(f"Error generating observation for {correlation_pkg['correlation_id']}: {e}")
            return None
    
    def _get_sensor_time_offset(self, sensor_type: str) -> int:
        """Get time offset for sensor detection (minutes relative to ground truth)"""
        
        offsets = {
            "GROUND_SURVEILLANCE_RADAR": random.randint(-5, 10),  # Slightly before to slightly after
            "SEISMIC_SENSOR": random.randint(-3, 5),  # Quick detection
            "THERMAL_SENSOR": random.randint(-5, 10)  # Can detect prep or ongoing
        }
        
        return offsets.get(sensor_type, 0)
    
    def _get_sensor_id(self, sensor_type: str) -> str:
        """Generate sensor ID based on type"""
        
        sensor_ids = {
            "GROUND_SURVEILLANCE_RADAR": f"GSR-14-CORPS-{random.randint(1, 5):02d}",
            "SEISMIC_SENSOR": f"SEISMIC-ARRAY-{random.randint(1, 8):02d}",
            "THERMAL_SENSOR": f"THERMAL-ARRAY-{random.randint(1, 7):02d}"
        }
        
        return sensor_ids.get(sensor_type, "SENSOR-UNKNOWN")
    
    def _create_sensor_observation_prompt(self, date: str, ground_truth: Dict[str, Any],
                                         sensor_type: str, detection_time: str,
                                         correlation_id: str) -> str:
        """Create prompt for independent sensor observation"""
        
        # Get sensor-specific capabilities
        sensor_capabilities = self._get_sensor_capabilities(sensor_type)
        
        # Get equipment context samples
        equipment_pak = random.sample(
            MILITARY_INTELLIGENCE_LANGUAGE.get('equipment_specifics_pakistan', []),
            min(2, len(MILITARY_INTELLIGENCE_LANGUAGE.get('equipment_specifics_pakistan', [])))
        )
        
        prompt = f"""Date: {date}
Sensor Type: {sensor_type}
Detection Time: {detection_time}

GROUND TRUTH EVENT (for reference - sensor doesn't know all these details):
- Actor: {ground_truth.get('actor')}
- Activity: {ground_truth.get('event_type')}
- Location: {ground_truth.get('location_name')}
- Equipment: {', '.join(ground_truth.get('equipment_involved', []))}
- Strength: {ground_truth.get('strength', '')}

SENSOR CAPABILITIES:
{sensor_capabilities}

EQUIPMENT CONTEXT (general knowledge):
{chr(10).join(['• ' + e for e in equipment_pak])}

Generate EXACTLY 1 independent sensor observation record from THIS SENSOR'S PERSPECTIVE ONLY.

CRITICAL REQUIREMENTS:
1. This sensor operates INDEPENDENTLY - it does NOT know what ELINT, IMINT, or TACINT detected
2. Generate observation based ONLY on what THIS SENSOR TYPE can detect
3. Use sensor-specific language and measurements
4. DO NOT cite or reference other intelligence sources
5. Sensor detected this activity at {detection_time} hours

REQUIRED FIELDS:
- sensor_type: "{sensor_type}"
- sensor_id: (will be added automatically)
- tgt_type: "VEHICLE" | "PERSONNEL" | "INSTALLATION" | "EQUIPMENT"
- tgt_sub_type: based on sensor capability (e.g., "TRACKED_VEHICLE", "WHEELED_VEHICLE", "PERSONNEL_GROUP")
- tgt_cl: based on sensor capability (e.g., "ARMORED_VEHICLE", "TRANSPORT", "INFANTRY")
- activity_type: "MOVEMENT" | "COMBAT" | "CONSTRUCTION" | "RECONNAISSANCE"
- activity_sub_type: e.g., "VEHICULAR" | "FOOT_PATROL" | "DEFENSIVE_POSITION"
- activity_cl: e.g., "TACTICAL_DEPLOYMENT" | "PATROL" | "FORTIFICATION"
- bearing: (0-360 degrees, e.g., "275")
- range_km: (detection range based on sensor type, e.g., "12.5")
- str: (estimated strength from sensor perspective, e.g., "Multiple tracked vehicles, estimated 10-15 units")
- long: (from ground truth location: {ground_truth.get('location', [0, 0])[0]})
- lat: (from ground truth location: {ground_truth.get('location', [0, 0])[1]})
- ht: (height from location, or 3000-5000)
- e: (easting 383000-385000)
- n: (northing 3815000-3820000)
- zone: "43S"
- input_method: (sensor-specific method, e.g., "Ground surveillance radar detection")
- description: (100-150 words, sensor-specific perspective, see structure below)
- upload_time: "{date} {detection_time}" format with +10-20 min processing delay
- correlation_id: "{correlation_id}"

DESCRIPTION STRUCTURE (100-150 words):
1. Sensor identification and detection time: "[Sensor type] [sensor_id] detected [activity] at [time] hours..."
2. Technical measurements: "At bearing [X] degrees, range [Y] kilometers from sensor location..."
3. Sensor-specific details: For radar: "Radar return signatures indicate..." / For seismic: "Seismic vibration patterns show..." / etc.
4. What sensor detected: Based on sensor capabilities, describe what it CAN detect (not full picture)
5. Inferred activity type: "Movement pattern indicates [type of activity] based on [sensor signature]..."
6. Confidence assessment: "Assessed as [confidence level] based on [sensor data quality]..."

CRITICAL: Write ONLY from this sensor's perspective. Do NOT reference ELINT, IMINT, TACINT, or other sensors!

EXAMPLE (use as template):
{{
  "sensor_type": "{sensor_type}",
  "tgt_type": "VEHICLE",
  "tgt_sub_type": "TRACKED_VEHICLE",
  "tgt_cl": "ARMORED_VEHICLE",
  "activity_type": "MOVEMENT",
  "activity_sub_type": "VEHICULAR",
  "activity_cl": "TACTICAL_DEPLOYMENT",
  "bearing": "275",
  "range_km": "12.5",
  "str": "Multiple tracked vehicles, estimated 10-15 units",
  "long": {ground_truth.get('location', [76.1, 34.5])[0]},
  "lat": {ground_truth.get('location', [76.1, 34.5])[1]},
  "ht": 4590,
  "e": 384251,
  "n": 3817136,
  "zone": "43S",
  "input_method": "{sensor_type.replace('_', ' ').title()} detection",
  "description": "Write sensor-specific description here from THIS SENSOR'S PERSPECTIVE ONLY. 100-150 words. Include sensor identification, detection time, technical measurements, sensor-specific signatures, what was detected, inferred activity, and confidence based on sensor data quality.",
  "upload_time": "{date} {detection_time}",
  "correlation_id": "{correlation_id}"
}}

Return JSON: {{"enemy_activity_records": [... 1 record ...]}}

Generate the independent sensor observation now:"""
        
        return prompt
    
    def _get_sensor_capabilities(self, sensor_type: str) -> str:
        """Get sensor-specific capabilities description"""
        
        capabilities = {
            "GROUND_SURVEILLANCE_RADAR": """Ground Surveillance Radar Capabilities:
- Detection Range: 10-20 kilometers
- Can Detect: Vehicle movement, size/type (tracked vs wheeled), formation, speed, direction
- Cannot Detect: Specific equipment models, visual details, personnel faces
- Measurements: Bearing, range, velocity, radar cross-section
- Output: Radar return strength, Doppler shift, target profile
- Limitations: Cannot identify specific vehicle models, affected by terrain masking""",
            
            "SEISMIC_SENSOR": """Seismic Sensor Capabilities:
- Detection Range: 5-15 kilometers (varies by terrain)
- Can Detect: Ground vibrations from vehicles/equipment, heavy movement, construction
- Cannot Detect: Airborne activity, stationary targets, light personnel movement
- Measurements: Vibration intensity, frequency, pattern, approximate location
- Output: Seismic signature strength, vibration pattern analysis
- Limitations: Cannot identify specific equipment, approximate location only""",            
            
            "THERMAL_SENSOR": """Thermal Sensor Capabilities:
- Detection Range: 3-10 kilometers
- Can Detect: Heat signatures from vehicles/equipment/personnel, engine heat, thermal patterns
- Cannot Detect: Cold/ambient temperature objects, specific equipment models
- Measurements: Thermal signature intensity, heat pattern, approximate count
- Output: Thermal image, heat intensity levels, signature classification
- Limitations: Cannot identify specific equipment, only heat signatures"""
        }
        
        return capabilities.get(sensor_type, "Unknown sensor capabilities")