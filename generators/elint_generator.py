import os
import json
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from utils.anthropic_client import AnthropicClient
from config import OUTPUT_DIR

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ElintGenerator:
    """Generate ELINT (Electronic Intelligence) data for the SAMA database."""
    
    def __init__(self):
        self.client = AnthropicClient()
    
    def generate_elint_data(self, 
                           scenario: Dict[str, Any], 
                           reference_data: Dict[str, Any],
                           batch_size: int = 10) -> List[Dict[str, Any]]:
        """Generate ELINT data based on scenario and reference data."""
        
        logger.info(f"Generating ELINT data for scenario: {scenario['scenario_name']}")
        
        all_elint_records = []
        timeline = scenario.get("timeline", [])
        
        # Process in batches to manage context length
        for i in range(0, len(timeline), batch_size):
            batch_timeline = timeline[i:i+batch_size]
            
            prompt = self._create_elint_generation_prompt(
                scenario=scenario,
                batch_timeline=batch_timeline,
                reference_data=reference_data
            )
            
            logger.info(f"Generating ELINT batch {i//batch_size + 1}/{(len(timeline) + batch_size - 1)//batch_size}")
            
            try:
                batch_response = self.client.generate_structured_data(prompt)
                batch_records = batch_response.get("elint_records", [])
                all_elint_records.extend(batch_records)
                
                logger.info(f"Generated {len(batch_records)} ELINT records for batch")
            except Exception as e:
                logger.error(f"Error generating ELINT batch: {str(e)}")
                continue
        
        # Save the generated ELINT data
        output_path = os.path.join(OUTPUT_DIR, f"elint_data_{scenario['scenario_name']}.json")
        with open(output_path, 'w') as f:
            json.dump(all_elint_records, f, indent=2)
        
        logger.info(f"ELINT data saved to: {output_path}")
        
        return all_elint_records
    
    def _create_elint_generation_prompt(self, 
                                    scenario: Dict[str, Any], 
                                    batch_timeline: List[Dict[str, Any]],
                                    reference_data: Dict[str, Any]) -> str:
        """Create a prompt for generating ELINT data from scenario timeline."""
        
        # Extract relevant events that could be detected by ELINT
        elint_detectable_events = []
        
        for day in batch_timeline:
            day_events = day.get("events", [])
            for event in day_events:
                if "ELINT" in event.get("observable_by", []):
                    elint_detectable_events.append({
                        "day": day["day"],
                        "date": day["date"],
                        "time": event["time"],
                        "event_type": event["event_type"],
                        "actor": event["actor"],
                        "location": event["location"],
                        "description": event["description"]
                    })
        
        # Create the prompt with a complete example record
        prompt = f"""
        Generate realistic ELINT (Electronic Intelligence) data for a military intelligence database based on the following scenario and events.
        
        SCENARIO OVERVIEW:
        {scenario['scenario_description']}
        
        ELINT-DETECTABLE EVENTS:
        {json.dumps(elint_detectable_events, indent=2)}
        
        TASK:
        Create realistic ELINT records for the above events. Each ELINT record should represent an electronic emission detection that corresponds to one or more of the events.
        
        EXAMPLE OF A COMPLETE ELINT RECORD:
        {{
        "id": 1,
        "date": "2025-10-15",
        "from_time": "09:15",
        "to_time": "09:48",
        "en": "X Corps",
        "location": "Neelum Valley",
        "range": "12.5",
        "emitter_type": "COMMUNICATIONS",
        "emitter_name": "TRC-20H Tactical Radio",
        "frequency": "320.5 MHz",
        "long": 74.8123,
        "lat": 34.0921,
        "ht": 1425,
        "e": 384251,
        "n": 592136,
        "zone": "43S",
        "description": "Encrypted burst transmission detected from Pakistani military communications network. Signal pattern consistent with operational command traffic. Transmission duration and signal strength suggest battalion-level coordination.",
        "fmn_code": 1032451298,
        "cmd_name": "Northern Command",
        "corps_name": "XIV Corps",
        "div_name": "19 Infantry Division",
        "bde_name": "28 Mountain Brigade",
        "unit_name": "Electronic Warfare Unit 112",
        "level": "Brigade"
        }}
        
        FORMAT THE RESPONSE AS A JSON OBJECT:
        {{
        "elint_records": [
            // Generate multiple detailed ELINT records like the example above
        ]
        }}
        
        IMPORTANT CONSIDERATIONS:
        1. Create REALISTIC emission details for military equipment
        2. Include both communication and radar emissions where appropriate
        3. For Pakistani units, use equipment like TRC-20H, HF/VHF radios, JY-27A radars
        4. For Chinese units, use equipment like Type 305/306 radars, GLD-09 systems, BeiDou communications
        5. Match the emission types to the activities (e.g., movement should have command communications)
        6. Include technical details like frequency bands, emission patterns, signal characteristics
        7. Ensure coordinates match the event but add slight variations for realism
        8. Generate proper Indian military unit information for the detecting units
        9. Some events may generate multiple ELINT records, others might generate none
        
        ONLY RETURN THE JSON OBJECT WITH NO ADDITIONAL TEXT OR EXPLANATIONS.
        """
        
        return prompt