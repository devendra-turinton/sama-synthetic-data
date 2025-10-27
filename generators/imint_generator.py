import os
import json
import logging
from typing import Dict, List, Any

from utils.anthropic_client import AnthropicClient
from utils.event_correlation_engine import EventCorrelationEngine
from utils.formation_code_generator import FormationCodeGenerator
from config import OUTPUT_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImintGenerator:
    """Generate IMINT data with realistic correlation to ground truth events"""
    
    def __init__(self):
        self.client = AnthropicClient()
        self.correlation_engine = EventCorrelationEngine()
        self.formation_gen = FormationCodeGenerator()
        self.formation_gen.initialize_default_units()
    
    def generate_imint_data(self, 
                           scenario: Dict[str, Any], 
                           reference_data: Dict[str, Any],
                           batch_size: int = 5) -> List[Dict[str, Any]]:
        """Generate correlated IMINT data"""
        
        logger.info(f"Generating correlated IMINT data for scenario: {scenario['scenario_name']}")
        
        all_imint_records = []
        timeline = scenario.get("timeline", [])
        record_id = 1
        
        # Process in batches
        for i in range(0, len(timeline), batch_size):
            batch_timeline = timeline[i:i+batch_size]
            
            # Create correlation packages for all events in batch
            correlation_packages = []
            for day in batch_timeline:
                for event in day.get("events", []):
                    if "IMINT" in event.get("observable_by", []):
                        corr_pkg = self.correlation_engine.create_correlated_event(event)
                        corr_pkg["date"] = day["date"]
                        correlation_packages.append(corr_pkg)
            
            if not correlation_packages:
                continue
            
            prompt = self._create_correlated_imint_prompt(
                scenario=scenario,
                correlation_packages=correlation_packages,
                reference_data=reference_data
            )
            
            logger.info(f"Generating IMINT batch {i//batch_size + 1} with {len(correlation_packages)} correlated events")
            
            try:
                batch_response = self.client.generate_structured_data(prompt)
                batch_records = batch_response.get("imint_records", [])
                
                # Add IDs and formation info
                for record in batch_records:
                    record["id"] = record_id
                    record_id += 1
                    
                    # Get imagery analysis unit
                    unit_info = self.formation_gen.generate_support_unit("NC", "14", "intelligence")
                    unit_info["unit_name"] = "Imagery Analysis Cell 06"
                    record.update({
                        "fmn_code": unit_info["fmn_code"],
                        "cmd_name": unit_info["cmd_name"],
                        "corps_name": unit_info["corps_name"],
                        "div_name": unit_info["div_name"],
                        "bde_name": unit_info["bde_name"],
                        "unit_name": unit_info["unit_name"],
                        "level": "Division"
                    })
                
                all_imint_records.extend(batch_records)
                logger.info(f"Generated {len(batch_records)} IMINT records for batch")
                
            except Exception as e:
                logger.error(f"Error generating IMINT batch: {str(e)}")
                continue
        
        # Save generated data
        output_path = os.path.join(OUTPUT_DIR, f"imint_data_{scenario['scenario_name']}.json")
        with open(output_path, 'w') as f:
            json.dump(all_imint_records, f, indent=2)
        
        logger.info(f"IMINT data saved to: {output_path}")
        logger.info(f"Total IMINT records: {len(all_imint_records)}")
        
        return all_imint_records
    
    def _create_correlated_imint_prompt(self, 
                                       scenario: Dict[str, Any],
                                       correlation_packages: List[Dict[str, Any]],
                                       reference_data: Dict[str, Any]) -> str:
        """Create prompt for generating correlated IMINT records"""
        
        # Extract IMINT observable events
        imint_observable_events = []
        for pkg in correlation_packages:
            gt = pkg["ground_truth"]
            imint_obs = pkg["source_observations"].get("IMINT", {})
            
            if imint_obs:
                imint_observable_events.append({
                    "correlation_id": pkg["correlation_id"],
                    "date": pkg["date"],
                    "base_time": gt["time"],
                    "time_offset_minutes": imint_obs["time_offset_minutes"],
                    "actual_time": self.correlation_engine.get_time_adjusted_datetime(
                        gt["time"], 
                        imint_obs["time_offset_minutes"]
                    ),
                    "event_type": gt["event_type"],
                    "actor": gt["actor"],
                    "location": gt["location"],
                    "location_name": gt.get("location_name", ""),
                    "equipment": gt.get("equipment_involved", []),
                    "strength": gt.get("strength", ""),
                    "description": gt["description"],
                    "imint_specific": imint_obs["observable_details"]
                })
        
        prompt = f"""
Generate realistic IMINT (Imagery Intelligence) records for the Kargil War based on satellite imagery observations.

SCENARIO: {scenario['scenario_description']}

YOUR ROLE: You are analyzing satellite imagery from CARTOSAT, RISAT, or commercial satellites. You see the battlefield from OVERHEAD perspective only.

CORRELATED EVENTS TO OBSERVE:
{json.dumps(imint_observable_events, indent=2)}

CRITICAL IMINT OBSERVATION RULES:
1. OVERHEAD PERSPECTIVE: Describe only what's visible from directly above
2. WEATHER CONSTRAINTS: Include cloud cover, visibility conditions affecting image quality
3. CONFIDENCE QUALIFIERS: Use "CONFIRMED", "PROBABLE", "POSSIBLE" based on image quality
4. PHYSICAL DETAILS: Focus on vehicle types, formations, positions, infrastructure
5. COUNT ACCURACY: Give ranges for counts (e.g., "10-12 vehicles" not exact "11")
6. LOCATION PRECISION: GPS-quality coordinates (±50m accuracy)
7. NO ELECTRONIC INFO: Cannot detect radio signals, only physical presence

WEATHER/IMAGE QUALITY FROM CORRELATION DATA:
{imint_observable_events[0]['imint_specific']['weather_factor'] if imint_observable_events and 'imint_specific' in imint_observable_events[0] else '20% cloud cover'}

REALISTIC SATELLITE PLATFORMS:
- CARTOSAT-3 (0.25m resolution, optical)
- RISAT-2 (1m resolution, SAR - works through clouds)
- Commercial: WorldView, GeoEye

PAKISTANI EQUIPMENT VISIBLE FROM ABOVE:
- Armor: Al-Khalid MBT, T-59/69 tanks, M113 APCs
- Artillery: 130mm guns, 122mm howitzers
- Vehicles: Toyota Hilux, military trucks
- Aircraft: F-16, Mirage III/V

EXAMPLE IMINT RECORD:
{{
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
  "n": 592142,
  "zone": "43S",
  "input": "Satellite pass #CS3-14256",
  "description": "PROBABLE convoy of Al-Khalid MBTs observed in tactical column formation moving northeast along mountain road. Vehicle spacing approximately 50m consistent with tactical deployment. Cloud cover at 25% with good visibility in target area. Vehicle count: 10-12 based on thermal signatures. Formation pattern suggests company-sized armored element. POSSIBLE support vehicles observed at column rear. Image resolution sufficient for vehicle type identification. Assessment: Deliberate tactical movement rather than routine patrol based on formation discipline and direction of travel.",
  "upload_time": "1999-06-15 11:15",
  "correlation_id": "CORR_0042"
}}

GENERATE IMINT RECORDS:
- Create ONE record per correlated event
- Use ACTUAL_TIME (adjusted for satellite pass timing)
- Describe ONLY what's visible in satellite imagery
- Include realistic weather/visibility constraints
- Use confidence qualifiers (CONFIRMED/PROBABLE/POSSIBLE)
- Give vehicle/personnel count ranges, not exact numbers
- Include technical details (satellite name, pass number, resolution notes)
- Reference correlation_id for tracking

FORMAT AS JSON:
{{
  "imint_records": [
    // Array of IMINT records following the example format
  ]
}}

ONLY RETURN THE JSON OBJECT WITH NO ADDITIONAL TEXT.
"""
        
        return prompt