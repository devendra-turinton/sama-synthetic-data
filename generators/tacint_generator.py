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

class TacintGenerator:
    """Generate TACINT (Tactical Intelligence) data for the SAMA database."""
    
    def __init__(self):
        self.client = AnthropicClient()
    
    def generate_tacint_data(self, 
                            scenario: Dict[str, Any], 
                            reference_data: Dict[str, Any],
                            batch_size: int = 10) -> List[Dict[str, Any]]:
        """Generate TACINT data based on scenario and reference data."""
        
        logger.info(f"Generating TACINT data for scenario: {scenario['scenario_name']}")
        
        all_tacint_records = []
        timeline = scenario.get("timeline", [])
        
        # Process in batches to manage context length
        for i in range(0, len(timeline), batch_size):
            batch_timeline = timeline[i:i+batch_size]
            
            prompt = self._create_tacint_generation_prompt(
                scenario=scenario,
                batch_timeline=batch_timeline,
                reference_data=reference_data
            )
            
            logger.info(f"Generating TACINT batch {i//batch_size + 1}/{(len(timeline) + batch_size - 1)//batch_size}")
            
            try:
                batch_response = self.client.generate_structured_data(prompt)
                batch_records = batch_response.get("tacint_records", [])
                all_tacint_records.extend(batch_records)
                
                logger.info(f"Generated {len(batch_records)} TACINT records for batch")
            except Exception as e:
                logger.error(f"Error generating TACINT batch: {str(e)}")
                continue
        
        # Save the generated TACINT data
        output_path = os.path.join(OUTPUT_DIR, f"tacint_data_{scenario['scenario_name']}.json")
        with open(output_path, 'w') as f:
            json.dump(all_tacint_records, f, indent=2)
        
        logger.info(f"TACINT data saved to: {output_path}")
        
        return all_tacint_records
    
    def _create_tacint_generation_prompt(self, 
                                        scenario: Dict[str, Any], 
                                        batch_timeline: List[Dict[str, Any]],
                                        reference_data: Dict[str, Any]) -> str:
        """Create a prompt for generating TACINT data from scenario timeline."""
        
        # Extract relevant events that could be detected by TACINT
        tacint_detectable_events = []
        
        for day in batch_timeline:
            day_events = day.get("events", [])
            for event in day_events:
                if "TACINT" in event.get("observable_by", []):
                    tacint_detectable_events.append({
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
        Generate realistic TACINT (Tactical Intelligence) data for a military intelligence database based on the following scenario and events.
        
        SCENARIO OVERVIEW:
        {scenario['scenario_description']}
        
        TACINT-DETECTABLE EVENTS:
        {json.dumps(tacint_detectable_events, indent=2)}
        
        TASK:
        Create realistic TACINT records for the above events. Each TACINT record should represent human-sourced intelligence from ground observation posts, patrols, or field units that corresponds to one or more of the events.
        
        EXAMPLE OF A COMPLETE TACINT RECORD:
        {{
        "id": 1,
        "Date": "2025-10-15",
        "time": "11:15",
        "pre": "IMMEDIATE",
        "tgt_type": "PERSONNEL",
        "tgt_sub_type": "INFANTRY",
        "tgt_cl": "SPECIAL_FORCES",
        "activity_type": "MOVEMENT",
        "activity_sub_type": "FOOT_PATROL",
        "activity_cl": "RECONNAISSANCE",
        "Incident_type": "BORDER_VIOLATION",
        "Incident_sub_type": "TROOP_INCURSION",
        "Incident_cl": "ARMED_SQUAD",
        "source_agency": "BSF Observation Post Delta-7",
        "grading": "A2",
        "str": "6-8 personnel",
        "long": 74.8045,
        "lat": 34.0896,
        "ht": 1350,
        "e": 384190,
        "n": 592105,
        "zone": "43S",
        "input": "Visual observation with thermal imaging",
        "description": "Squad-sized element observed crossing LoC at 11:15 hours. Personnel equipped with tactical gear and assault rifles consistent with Pakistani SSG equipment. Movement pattern indicates trained special forces utilizing terrain for concealment. Observed for approximately 12 minutes before losing visual contact in dense vegetation. Weather conditions: clear visibility, light wind from southwest.",
        "fmn_code": 1032451298,
        "cmd_name": "Northern Command",
        "corps_name": "XIV Corps",
        "div_name": "19 Infantry Division",
        "bde_name": "28 Mountain Brigade",
        "unit_name": "Border Security Force Post Delta-7",
        "upload_time": "2025-10-15 11:42",
        "level": "Battalion"
        }}
        
        FORMAT THE RESPONSE AS A JSON OBJECT:
        {{
        "tacint_records": [
            // Generate multiple detailed TACINT records like the example above
        ]
        }}
        
        IMPORTANT CONSIDERATIONS:
        1. Create realistic ground-level observations with appropriate limitations (line of sight, visibility conditions)
        2. Include human observer elements like uncertainty, subjective descriptions, and limited technical knowledge
        3. Use appropriate military terminology for field reports
        4. Vary reliability grading based on observer experience, conditions, and distance
        5. Some observations may be partial or contain misidentifications
        6. Generate realistic Indian border units as observers (BSF, Army forward posts)
        7. Include appropriate tactical details visible from ground level
        8. Ensure descriptions use language typical of field reports
        9. Use realistic limitations in observations (e.g., "observed from 2km distance through binoculars")
        
        ONLY RETURN THE JSON OBJECT WITH NO ADDITIONAL TEXT OR EXPLANATIONS.
        """
        
        return prompt