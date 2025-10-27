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

class EnemyActivityGenerator:
    """Generate Enemy Activity data for the SAMA database by synthesizing intelligence from multiple sources."""
    
    def __init__(self):
        self.client = AnthropicClient()
    
    def generate_enemy_activity_data(self, 
                                    scenario: Dict[str, Any], 
                                    reference_data: Dict[str, Any],
                                    elint_data: List[Dict[str, Any]],
                                    imint_data: List[Dict[str, Any]],
                                    tacint_data: List[Dict[str, Any]],
                                    batch_size: int = 10) -> List[Dict[str, Any]]:
        """Generate Enemy Activity data by correlating multiple intelligence sources."""
        
        logger.info(f"Generating Enemy Activity data for scenario: {scenario['scenario_name']}")
        
        all_enemy_activity_records = []
        timeline = scenario.get("timeline", [])
        
        # Process in batches to manage context length
        for i in range(0, len(timeline), batch_size):
            batch_timeline = timeline[i:i+batch_size]
            
            # Find relevant intelligence for this batch of days
            batch_dates = [day["date"] for day in batch_timeline]
            
            batch_elint = [record for record in elint_data if record.get("date") in batch_dates]
            batch_imint = [record for record in imint_data if record.get("Date") in batch_dates]
            batch_tacint = [record for record in tacint_data if record.get("Date") in batch_dates]
            
            prompt = self._create_enemy_activity_generation_prompt(
                scenario=scenario,
                batch_timeline=batch_timeline,
                batch_elint=batch_elint,
                batch_imint=batch_imint,
                batch_tacint=batch_tacint,
                reference_data=reference_data
            )
            
            logger.info(f"Generating Enemy Activity batch {i//batch_size + 1}/{(len(timeline) + batch_size - 1)//batch_size}")
            
            try:
                batch_response = self.client.generate_structured_data(prompt)
                batch_records = batch_response.get("enemy_activity_records", [])
                all_enemy_activity_records.extend(batch_records)
                
                logger.info(f"Generated {len(batch_records)} Enemy Activity records for batch")
            except Exception as e:
                logger.error(f"Error generating Enemy Activity batch: {str(e)}")
                continue
        
        # Save the generated Enemy Activity data
        output_path = os.path.join(OUTPUT_DIR, f"enemy_activity_data_{scenario['scenario_name']}.json")
        with open(output_path, 'w') as f:
            json.dump(all_enemy_activity_records, f, indent=2)
        
        logger.info(f"Enemy Activity data saved to: {output_path}")
        
        return all_enemy_activity_records
    
    def _create_enemy_activity_generation_prompt(self, 
                                            scenario: Dict[str, Any], 
                                            batch_timeline: List[Dict[str, Any]],
                                            batch_elint: List[Dict[str, Any]],
                                            batch_imint: List[Dict[str, Any]],
                                            batch_tacint: List[Dict[str, Any]],
                                            reference_data: Dict[str, Any]) -> str:
        """Create a prompt for generating Enemy Activity data by correlating intel sources."""
        
        # Create a condensed summary of intelligence for the prompt
        # (limit size to avoid exceeding context window)
        elint_summary = batch_elint[:5]
        imint_summary = batch_imint[:5]
        tacint_summary = batch_tacint[:5]
        
        # Create the prompt with a complete example record
        prompt = f"""
        Generate Enemy Activity data for a military intelligence database by synthesizing and correlating multiple intelligence sources.
        
        SCENARIO OVERVIEW:
        {scenario['scenario_description']}
        
        INTELLIGENCE SOURCES AVAILABLE:
        
        1. ELINT SAMPLE DATA (Electronic Intelligence):
        {json.dumps(elint_summary, indent=2)}
        
        2. IMINT SAMPLE DATA (Imagery Intelligence):
        {json.dumps(imint_summary, indent=2)}
        
        3. TACINT SAMPLE DATA (Tactical Intelligence):
        {json.dumps(tacint_summary, indent=2)}
        
        TIMELINE EVENTS FOR THIS PERIOD:
        {json.dumps(batch_timeline, indent=2)}
        
        TASK:
        Create Enemy Activity records that synthesize and correlate the available intelligence sources. Each Enemy Activity record represents a comprehensive assessment of enemy activities based on sensor data and multi-source intelligence fusion.
        
        EXAMPLE OF A COMPLETE ENEMY ACTIVITY RECORD:
        {{
        "id": 1,
        "sensor_type": "INTEGRATED",
        "sensor_id": "MULTI-SOURCE",
        "tgt_type": "VEHICLE",
        "tgt_sub_type": "ARMORED",
        "tgt_cl": "MAIN_BATTLE_TANK",
        "activity_type": "MOVEMENT",
        "activity_sub_type": "VEHICULAR",
        "activity_cl": "TACTICAL_DEPLOYMENT",
        "bg": "275",
        "rg": "8.5",
        "str": "Company-strength (12-15 vehicles)",
        "long": 74.7982,
        "lat": 34.0815,
        "ht": 1280,
        "e": 384120,
        "n": 592015,
        "zone": "43S",
        "input": "ELINT/IMINT/TACINT correlation",
        "description": "CONFIRMED movement of Pakistani armored company (12-15 Al-Khalid MBTs) along valley approach toward LoC. Movement preceded by increased command communications (TRC-20H transmissions) and followed by special forces reconnaissance element crossing LoC. Activity pattern consistent with deliberate tactical positioning rather than routine exercise. Equipment identification confirmed by multiple intelligence sources with high confidence. Movement direction indicates potential staging for border operation.",
        "fmn_code": 1032451298,
        "cmd_name": "Northern Command",
        "corps_name": "XIV Corps",
        "div_name": "19 Infantry Division",
        "bde_name": "28 Mountain Brigade",
        "unit_name": "Intelligence Fusion Cell",
        "upload_time": "2025-10-15 14:30",
        "level": "Division"
        }}
        
        FORMAT THE RESPONSE AS A JSON OBJECT:
        {{
        "enemy_activity_records": [
            // Generate multiple detailed Enemy Activity records like the example above
        ]
        }}
        
        IMPORTANT CONSIDERATIONS:
        1. Create coherent synthesis of multiple intelligence sources
        2. Resolve contradictions between different intelligence sources where they exist
        3. Create more comprehensive and confident assessments where multiple sources corroborate
        4. Include appropriate uncertainty language where intelligence is limited
        5. Ensure the activity records represent a coherent narrative that aligns with the scenario
        6. Focus on creating a realistic intelligence fusion product
        7. Some activities may combine insights from multiple intelligence sources
        
        CREATE APPROXIMATELY 15-20 ENEMY ACTIVITY RECORDS FOR THIS BATCH.
        ONLY RETURN THE JSON OBJECT WITH NO ADDITIONAL TEXT OR EXPLANATIONS.
        """
        
        return prompt