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

class ImintGenerator:
    """Generate IMINT (Imagery Intelligence) data for the SAMA database."""
    
    def __init__(self):
        self.client = AnthropicClient()
    
    def generate_imint_data(self, 
                           scenario: Dict[str, Any], 
                           reference_data: Dict[str, Any],
                           batch_size: int = 10) -> List[Dict[str, Any]]:
        """Generate IMINT data based on scenario and reference data."""
        
        logger.info(f"Generating IMINT data for scenario: {scenario['scenario_name']}")
        
        all_imint_records = []
        timeline = scenario.get("timeline", [])
        
        # Process in batches to manage context length
        for i in range(0, len(timeline), batch_size):
            batch_timeline = timeline[i:i+batch_size]
            
            prompt = self._create_imint_generation_prompt(
                scenario=scenario,
                batch_timeline=batch_timeline,
                reference_data=reference_data
            )
            
            logger.info(f"Generating IMINT batch {i//batch_size + 1}/{(len(timeline) + batch_size - 1)//batch_size}")
            
            try:
                batch_response = self.client.generate_structured_data(prompt)
                batch_records = batch_response.get("imint_records", [])
                all_imint_records.extend(batch_records)
                
                logger.info(f"Generated {len(batch_records)} IMINT records for batch")
            except Exception as e:
                logger.error(f"Error generating IMINT batch: {str(e)}")
                continue
        
        # Save the generated IMINT data
        output_path = os.path.join(OUTPUT_DIR, f"imint_data_{scenario['scenario_name']}.json")
        with open(output_path, 'w') as f:
            json.dump(all_imint_records, f, indent=2)
        
        logger.info(f"IMINT data saved to: {output_path}")
        
        return all_imint_records
    
    def _create_imint_generation_prompt(self, 
                                    scenario: Dict[str, Any], 
                                    batch_timeline: List[Dict[str, Any]],
                                    reference_data: Dict[str, Any]) -> str:
        """Create a prompt for generating IMINT data from scenario timeline."""
        
        # Extract relevant events that could be detected by IMINT
        imint_detectable_events = []
        
        for day in batch_timeline:
            day_events = day.get("events", [])
            for event in day_events:
                if "IMINT" in event.get("observable_by", []):
                    imint_detectable_events.append({
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
        Generate realistic IMINT (Imagery Intelligence) data for a military intelligence database based on the following scenario and events.
        
        SCENARIO OVERVIEW:
        {scenario['scenario_description']}
        
        IMINT-DETECTABLE EVENTS:
        {json.dumps(imint_detectable_events, indent=2)}
        
        TASK:
        Create realistic IMINT records for the above events. Each IMINT record should represent satellite or aerial imagery intelligence that corresponds to one or more of the events.
        
        EXAMPLE OF A COMPLETE IMINT RECORD:
        {{
        "id": 1,
        "Date": "2025-10-15",
        "time": "10:30",
        "pre": "PRIORITY",
        "tgt_type": "VEHICLE",
        "tgt_sub_type": "ARMORED",
        "tgt_cl": "MAIN_BATTLE_TANK",
        "activity_type": "MOVEMENT",
        "activity_sub_type": "VEHICULAR",
        "activity_cl": "COLUMN",
        "Incident_type": "FORCE_POSTURING",
        "Incident_sub_type": "EQUIPMENT_BUILDUP",
        "Incident_cl": "ARMOR_CONCENTRATION",
        "source_agency": "CARTOSAT-3",
        "grading": "B2",
        "str": "12-15 vehicles",
        "long": 74.7982,
        "lat": 34.0815,
        "ht": 1280,
        "e": 384120,
        "n": 592015,
        "zone": "43S",
        "input": "Satellite pass #CS3-82431",
        "description": "PROBABLE convoy of Al-Khalid MBTs observed moving in tactical formation along valley road network. Formation consistent with armored company movement. Cloud cover at 20% with good visibility conditions. Vehicle spacing and pattern suggest operational rather than training movement. POSSIBLE support vehicles observed at tail of column.",
        "fmn_code": 1032451298,
        "cmd_name": "Northern Command",
        "corps_name": "XIV Corps",
        "div_name": "19 Infantry Division",
        "bde_name": "28 Mountain Brigade",
        "unit_name": "Imagery Analysis Cell 06",
        "upload_time": "2025-10-15 12:45",
        "level": "Division"
        }}
        
        FORMAT THE RESPONSE AS A JSON OBJECT:
        {{
        "imint_records": [
            // Generate multiple detailed IMINT records like the example above
        ]
        }}
        
        IMPORTANT CONSIDERATIONS:
        1. Focus on observable physical characteristics visible in satellite/aerial imagery
        2. Include realistic limitations like weather conditions, cloud cover, resolution constraints
        3. Use appropriate confidence levels in descriptions (e.g., "PROBABLE armor convoy" rather than certainties)
        4. Match the description detail to what would actually be visible from satellite/aerial platforms
        5. For Pakistani/Chinese forces, include realistic equipment identification as would be seen from above
        6. Include appropriate source agencies like CARTOSAT, RISAT, or drone platforms
        7. Ensure grading reflects image quality and interpretation confidence
        8. Ensure coordinates match the event but add slight variations for realism
        9. Generate proper Indian military unit information for the analyzing units
        
        ONLY RETURN THE JSON OBJECT WITH NO ADDITIONAL TEXT OR EXPLANATIONS.
        """
        
        return prompt