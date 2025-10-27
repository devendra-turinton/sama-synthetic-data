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

class ElintGenerator:
    """Generate ELINT data with realistic correlation to ground truth events"""
    
    def __init__(self):
        self.client = AnthropicClient()
        self.correlation_engine = EventCorrelationEngine()
        self.formation_gen = FormationCodeGenerator()
        self.formation_gen.initialize_default_units()
    
    def generate_elint_data(self, 
                           scenario: Dict[str, Any], 
                           reference_data: Dict[str, Any],
                           batch_size: int = 5) -> List[Dict[str, Any]]:
        """Generate correlated ELINT data"""
        
        logger.info(f"Generating correlated ELINT data for scenario: {scenario['scenario_name']}")
        
        all_elint_records = []
        timeline = scenario.get("timeline", [])
        record_id = 1
        
        # Process in batches
        for i in range(0, len(timeline), batch_size):
            batch_timeline = timeline[i:i+batch_size]
            
            # Create correlation packages for all events in batch
            correlation_packages = []
            for day in batch_timeline:
                for event in day.get("events", []):
                    if "ELINT" in event.get("observable_by", []):
                        corr_pkg = self.correlation_engine.create_correlated_event(event)
                        corr_pkg["date"] = day["date"]
                        correlation_packages.append(corr_pkg)
            
            if not correlation_packages:
                continue
            
            prompt = self._create_correlated_elint_prompt(
                scenario=scenario,
                correlation_packages=correlation_packages,
                reference_data=reference_data
            )
            
            logger.info(f"Generating ELINT batch {i//batch_size + 1} with {len(correlation_packages)} correlated events")
            
            try:
                batch_response = self.client.generate_structured_data(prompt)
                batch_records = batch_response.get("elint_records", [])
                
                # Add IDs and formation info
                for record in batch_records:
                    record["id"] = record_id
                    record_id += 1
                    
                    # Get a random intelligence unit for attribution
                    unit_info = self.formation_gen.generate_support_unit("NC", "14", "intelligence")
                    record.update({
                        "fmn_code": unit_info["fmn_code"],
                        "cmd_name": unit_info["cmd_name"],
                        "corps_name": unit_info["corps_name"],
                        "div_name": unit_info["div_name"],
                        "bde_name": unit_info["bde_name"],
                        "unit_name": unit_info["unit_name"],
                        "level": unit_info["level"]
                    })
                
                all_elint_records.extend(batch_records)
                logger.info(f"Generated {len(batch_records)} ELINT records for batch")
                
            except Exception as e:
                logger.error(f"Error generating ELINT batch: {str(e)}")
                continue
        
        # Save generated data
        output_path = os.path.join(OUTPUT_DIR, f"elint_data_{scenario['scenario_name']}.json")
        with open(output_path, 'w') as f:
            json.dump(all_elint_records, f, indent=2)
        
        logger.info(f"ELINT data saved to: {output_path}")
        logger.info(f"Total ELINT records: {len(all_elint_records)}")
        
        return all_elint_records
    
    def _create_correlated_elint_prompt(self, 
                                       scenario: Dict[str, Any],
                                       correlation_packages: List[Dict[str, Any]],
                                       reference_data: Dict[str, Any]) -> str:
        """Create prompt for generating correlated ELINT records"""
        
        # Extract just the info needed for ELINT perspective
        elint_observable_events = []
        for pkg in correlation_packages:
            gt = pkg["ground_truth"]
            elint_obs = pkg["source_observations"].get("ELINT", {})
            
            if elint_obs:
                elint_observable_events.append({
                    "correlation_id": pkg["correlation_id"],
                    "date": pkg["date"],
                    "base_time": gt["time"],
                    "time_offset_minutes": elint_obs["time_offset_minutes"],
                    "actual_time": self.correlation_engine.get_time_adjusted_datetime(
                        gt["time"], 
                        elint_obs["time_offset_minutes"]
                    ),
                    "event_type": gt["event_type"],
                    "actor": gt["actor"],
                    "location": gt["location"],
                    "location_name": gt.get("location_name", ""),
                    "equipment": gt.get("equipment_involved", []),
                    "strength": gt.get("strength", ""),
                    "description": gt["description"],
                    "elint_specific": elint_obs["observable_details"]
                })
        
        prompt = f"""
Generate realistic ELINT (Electronic Intelligence) records for the Kargil War based on correlated ground truth events.

SCENARIO: {scenario['scenario_description']}

YOUR ROLE: You are an ELINT sensor system detecting electronic emissions. You CANNOT see physical objects, personnel, or equipment directly. You can ONLY detect:
- Radio communications (tactical, strategic, command nets)
- Radar emissions (surveillance, fire control, air defense)
- Electronic warfare systems
- Navigation systems

CORRELATED EVENTS TO OBSERVE:
{json.dumps(elint_observable_events, indent=2)}

CRITICAL ELINT OBSERVATION RULES:
1. TIMING: Your detection occurs {elint_observable_events[0]['time_offset_minutes'] if elint_observable_events else -10} minutes BEFORE physical activity (electronic prep precedes movement)
2. DESCRIPTION STYLE: Use TECHNICAL language - "VHF burst transmission", "encrypted tactical net", "fire control radar active"
3. NO VISUAL DETAILS: You CANNOT mention seeing tanks, troops, or physical objects - only electronic signatures
4. EQUIPMENT INFERENCE: Identify equipment types by their electronic signatures (e.g., "Signal pattern consistent with TRC-20H tactical radio")
5. STRENGTH ESTIMATION: Infer strength from communication volume/patterns, not direct counts
6. LOCATION: Provide coordinates from radio direction finding (triangulation) - medium accuracy (±500m)

REALISTIC PAKISTANI MILITARY EQUIPMENT EMISSIONS:
- Communications: TRC-20H Tactical Radio (VHF), HF/VHF Command Nets
- Radars: AN/TPS-43 (surveillance), Crotale Fire Control
- Chinese Equipment: Type 305/306 radars, GLD-09 laser systems

EXAMPLE ELINT RECORD:
{{
  "date": "1999-06-15",
  "from_time": "08:15",
  "to_time": "08:48",
  "en": "Pakistani XII Corps",
  "location": "Drass Sector",
  "range": "12.5",
  "emitter_type": "COMMUNICATIONS",
  "emitter_name": "TRC-20H Tactical Radio",
  "frequency": "345.2 MHz",
  "long": 75.7523,
  "lat": 34.4251,
  "ht": 3380,
  "e": 384251,
  "n": 592136,
  "zone": "43S",
  "description": "Encrypted VHF burst transmissions detected on Pakistani military frequency 345.2 MHz. Signal strength and modulation pattern consistent with TRC-20H tactical radio system. Traffic analysis indicates battalion-level command communications. Transmission duration 33 minutes suggests operational coordination rather than routine traffic. Direction finding places emitter in Drass sector, likely Pakistani forward operating base. Signal quality: strong, encryption: military-grade.",
  "correlation_id": "CORR_0042"
}}

GENERATE ELINT RECORDS:
- Create ONE record per correlated event
- Use the ACTUAL_TIME provided (already adjusted for ELINT detection timing)
- Maintain consistency with ground truth BUT express through electronic signatures only
- Include correlation_id for tracking
- Use realistic Pakistani military communications equipment
- Add technical ELINT-specific details (frequency, modulation, signal strength)

FORMAT AS JSON:
{{
  "elint_records": [
    // Array of ELINT records following the example format
  ]
}}

ONLY RETURN THE JSON OBJECT WITH NO ADDITIONAL TEXT.
"""
        
        return prompt