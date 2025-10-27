from typing import Dict, List, Any
import os
import json
import logging
from datetime import datetime, timedelta
import random

from utils.anthropic_client import AnthropicClient
from config import SCENARIOS, GEOGRAPHIC_AREAS, OUTPUT_DIR

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ScenarioGenerator:
    def __init__(self):
        self.client = AnthropicClient()
        self.scenarios = SCENARIOS
        self.geographic_areas = GEOGRAPHIC_AREAS
    
    def generate_scenario_timeline(self, scenario_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a detailed timeline for a military scenario."""
        
        prompt = self._create_scenario_prompt(scenario_config)
        
        logger.info(f"Generating timeline for scenario: {scenario_config['name']}")
        
        response = self.client.generate_structured_data(prompt)
        
        # Save the scenario to file
        output_path = os.path.join(OUTPUT_DIR, f"scenario_{scenario_config['name']}.json")
        with open(output_path, 'w') as f:
            json.dump(response, f, indent=2)
        
        logger.info(f"Scenario timeline saved to: {output_path}")
        
        return response
    
    def _create_scenario_prompt(self, scenario_config: Dict[str, Any]) -> str:
        """Create a detailed prompt for scenario generation."""
        
        # Get geographic information
        area_name = scenario_config["area"]
        geographic_info = self.geographic_areas.get(area_name, {})
        
        # Create datetime range
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=scenario_config["duration_days"])
        
        prompt = f"""
        Generate a detailed military intelligence scenario timeline for the following scenario:
        
        SCENARIO NAME: {scenario_config['name']}
        DESCRIPTION: {scenario_config['description']}
        DURATION: {scenario_config['duration_days']} days
        DATE RANGE: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}
        BORDER REGION: {scenario_config['border']}
        GEOGRAPHIC AREA: {area_name}
        
        Additional geographic details:
        {json.dumps(geographic_info, indent=2)}
        
        TASK:
        Create a comprehensive military intelligence scenario with a detailed timeline of events.
        The scenario should include realistic progression of military activities with specific details
        about units, equipment, locations, and timing.
        
        Your output should be a JSON object with the following structure:
        {{
            "scenario_name": "name_of_scenario",
            "scenario_description": "detailed description of the overall scenario",
            "start_date": "YYYY-MM-DD",
            "end_date": "YYYY-MM-DD",
            "geographic_focus": {{
                "border": "india_pakistan or india_china or both",
                "region": "specific region name",
                "center_coordinates": [longitude, latitude]
            }},
            "adversary_units": [
                {{
                    "unit_name": "name of military unit",
                    "formation_level": "battalion/brigade/etc",
                    "strength": "approximate troop count",
                    "equipment": ["list", "of", "primary", "equipment"]
                }}
                // More units...
            ],
            "timeline": [
                {{
                    "day": 1,
                    "date": "YYYY-MM-DD",
                    "events": [
                        {{
                            "time": "HH:MM",
                            "event_type": "movement/firing/construction/etc",
                            "actor": "specific unit responsible",
                            "location": [longitude, latitude],
                            "description": "detailed description of the event",
                            "observable_by": ["ELINT", "IMINT", "TACINT"] // Which intelligence sources could detect this
                        }}
                        // More events for the day...
                    ]
                }}
                // More days...
            ]
        }}
        
        IMPORTANT CONSIDERATIONS:
        1. Make events highly specific with realistic military details
        2. Include proper military terminology and equipment designations
        3. Ensure geographic coordinates are realistic for the specified border region
        4. Create a logical progression of events that tells a coherent story
        5. Include a mix of different activity types (movements, surveillance, construction, confrontation)
        6. Specify which intelligence source(s) would be able to detect each event
        7. Include specific unit names and hierarchies that are realistic for:
           - Pakistan: X Corps, IV Corps, II Corps, Pakistan Rangers, SSG
           - China: Western Theater Command, Tibet Military District units
        
        DO NOT INCLUDE ANY EXPLANATORY TEXT - ONLY OUTPUT THE JSON OBJECT.
        """
        
        return prompt