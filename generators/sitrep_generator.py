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

class SitrepGenerator:
    """Generate Situation Report (SITREP) data for the SAMA database."""
    
    def __init__(self):
        self.client = AnthropicClient()
    
    def generate_sitrep_data(self, 
                            scenario: Dict[str, Any], 
                            reference_data: Dict[str, Any],
                            enemy_activity_data: List[Dict[str, Any]],
                            batch_size: int = 5) -> List[Dict[str, Any]]:
        """Generate SITREP data based on scenario and enemy activity data."""
        
        logger.info(f"Generating SITREP data for scenario: {scenario['scenario_name']}")
        
        all_sitrep_records = []
        timeline = scenario.get("timeline", [])
        
        # Group by day and create SITREPs for each day or significant event cluster
        # Process in smaller batches as SITREPs are higher-level summaries
        for i in range(0, len(timeline), batch_size):
            batch_timeline = timeline[i:i+batch_size]
            
            # Find relevant enemy activity for this batch of days
            batch_dates = [day["date"] for day in batch_timeline]
            
            # Filter enemy activities relevant to this batch
            # Note: This assumes enemy_activity_data has a date field. If not, adjust accordingly.
            batch_activities = [
                record for record in enemy_activity_data 
                if record.get("upload_time", "").split()[0] in batch_dates
            ]
            
            prompt = self._create_sitrep_generation_prompt(
                scenario=scenario,
                batch_timeline=batch_timeline,
                batch_activities=batch_activities,
                reference_data=reference_data
            )
            
            logger.info(f"Generating SITREP batch {i//batch_size + 1}/{(len(timeline) + batch_size - 1)//batch_size}")
            
            try:
                batch_response = self.client.generate_structured_data(prompt)
                batch_records = batch_response.get("sitrep_records", [])
                all_sitrep_records.extend(batch_records)
                
                logger.info(f"Generated {len(batch_records)} SITREP records for batch")
            except Exception as e:
                logger.error(f"Error generating SITREP batch: {str(e)}")
                continue
        
        # Save the generated SITREP data
        output_path = os.path.join(OUTPUT_DIR, f"sitrep_data_{scenario['scenario_name']}.json")
        with open(output_path, 'w') as f:
            json.dump(all_sitrep_records, f, indent=2)
        
        logger.info(f"SITREP data saved to: {output_path}")
        
        return all_sitrep_records
    
    def _create_sitrep_generation_prompt(self, 
                                        scenario: Dict[str, Any], 
                                        batch_timeline: List[Dict[str, Any]],
                                        batch_activities: List[Dict[str, Any]],
                                        reference_data: Dict[str, Any]) -> str:
        """Create a prompt for generating SITREP data from scenario timeline and enemy activities."""
        
        # Create the prompt with a complete example record
        prompt = f"""
        Generate Situation Report (SITREP) data for a military intelligence database based on the following scenario, timeline, and enemy activities.
        
        SCENARIO OVERVIEW:
        {scenario['scenario_description']}
        
        TIMELINE FOR THIS PERIOD:
        {json.dumps(batch_timeline, indent=2)}
        
        ENEMY ACTIVITIES FOR THIS PERIOD:
        {json.dumps(batch_activities[:10], indent=2)}  # Limit to avoid exceeding context window
        
        TASK:
        Create comprehensive Situation Reports (SITREPs) that synthesize all available intelligence into strategic assessments. Each SITREP represents a formal situation report capturing both enemy and friendly force information.
        
        EXAMPLE OF A COMPLETE SITREP RECORD:
        {{
        "id": 1,
        "Incident_date": "2025-10-15",
        "time": "18:00",
        "pre": "PRIORITY",
        "Incident_type": "FORCE_POSTURING",
        "Incident_sub_type": "COORDINATED_OPERATION",
        "Incident_cl": "BORDER_PRESSURE",
        "source": "MULTI-SOURCE INTELLIGENCE",
        "str_own": "One infantry brigade, two BSF battalions",
        "str_en": "One armored company, one SSG platoon, supporting elements",
        "long": 74.7985,
        "lat": 34.0850,
        "ht": 1320,
        "e": 384150,
        "n": 592050,
        "zone": "43S",
        "Incident_states": "ONGOING",
        "description": "SITREP #241: Pakistani forces conducting coordinated operation along LoC in Neelum Valley sector. Activity began 09:15 with command communications followed by armored company movement toward forward staging area. SSG elements crossed LoC at 11:15 in probable reconnaissance mission. Pattern indicates deliberate pressure operation rather than routine activity.\\n\\nAssessment: Pakistani X Corps implementing limited probe of Indian defensive posture, likely in response to recent counterterrorism operations. Current activity assessed as posturing rather than preparation for significant incursion. However, armor positioning provides rapid escalation capability if desired.\\n\\nFriendly forces maintain full surveillance and defensive posture. 28 Mountain Brigade has reinforced forward positions and heightened alert status. Air support on standby. No current engagement between forces.",
        "fmn_code": 1032451298,
        "cmd_name": "Northern Command",
        "corps_name": "XIV Corps",
        "div_name": "19 Infantry Division",
        "bde_name": "28 Mountain Brigade",
        "unit_name": "Division Headquarters",
        "upload_time": "2025-10-15 18:30",
        "level": "Division"
        }}
        
        FORMAT THE RESPONSE AS A JSON OBJECT:
        {{
        "sitrep_records": [
            // Generate multiple detailed SITREP records like the example above
        ]
        }}
        
        IMPORTANT CONSIDERATIONS:
        1. Create higher-level strategic assessments that synthesize multiple intelligence sources
        2. Include both enemy and friendly force information
        3. Make comprehensive evaluations of the overall situation
        4. Group related incidents into coherent situational reports
        5. Include commander's assessment or implications in the descriptions
        6. Use appropriate military terminology for formal SITREPs
        7. Create one SITREP per significant situation (approximately 1-2 per day)
        8. Ensure SITREPs represent different echelons of command (Brigade, Division, Corps)
        
        ONLY RETURN THE JSON OBJECT WITH NO ADDITIONAL TEXT OR EXPLANATIONS.
        """
        
        return prompt