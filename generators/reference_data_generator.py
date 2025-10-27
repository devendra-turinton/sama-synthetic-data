import os
import json
import logging
from typing import Dict, List, Any

from utils.anthropic_client import AnthropicClient
from config import OUTPUT_DIR

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ReferenceDataGenerator:
    """Generate reference data for the SAMA database."""
    
    def __init__(self):
        self.client = AnthropicClient()
    
    def generate_activity_classification(self) -> Dict[str, Any]:
        """Generate activity classification hierarchy."""
        
        prompt = """
        Generate a comprehensive military activity classification hierarchy for an intelligence system.
        
        The classification should include three levels:
        1. activity_type (main categories)
        2. activity_sub_type (subcategories under each type)
        3. activity_classification (specific classifications under each sub-type)
        
        Each classification should include:
        - id: A unique identifier (integer)
        - name: Descriptive name of the category
        - description: Detailed explanation
        - img_path: A placeholder path to a symbol (format: /symbols/activity/{type}/{subtype}/{classification}.svg)
        
        The activities should cover the full spectrum of military operations relevant to border monitoring, including:
        - Movement activities (foot patrols, vehicle movements, etc.)
        - Construction activities (defensive positions, infrastructure, etc.)
        - Combat activities (firing, engagement, etc.)
        - Intelligence activities (reconnaissance, surveillance, etc.)
        - Support activities (logistics, communications, etc.)
        
        Format the response as a JSON object with this structure:
        {
          "activity_types": [
            {
              "id": 1,
              "name": "MOVEMENT",
              "description": "Description of movement activity",
              "img_path": "/symbols/activity/movement.svg",
              "activity_sub_types": [
                {
                  "id": 101,
                  "name": "FOOT_PATROL",
                  "description": "Description of foot patrol",
                  "img_path": "/symbols/activity/movement/foot_patrol.svg",
                  "activity_classifications": [
                    {
                      "id": 10101,
                      "name": "RECONNAISSANCE_PATROL",
                      "description": "Description of reconnaissance patrol",
                      "img_path": "/symbols/activity/movement/foot_patrol/reconnaissance.svg"
                    },
                    // More classifications...
                  ]
                },
                // More sub-types...
              ]
            },
            // More activity types...
          ]
        }
        
        CREATE AT LEAST 5 ACTIVITY TYPES, WITH AT LEAST 3 SUB-TYPES EACH, AND AT LEAST 2 CLASSIFICATIONS PER SUB-TYPE.
        ONLY RETURN THE JSON OBJECT WITH NO ADDITIONAL TEXT OR EXPLANATIONS.
        """
        
        logger.info("Generating activity classification hierarchy...")
        
        response = self.client.generate_structured_data(prompt)
        
        output_path = os.path.join(OUTPUT_DIR, "activity_classification.json")
        with open(output_path, 'w') as f:
            json.dump(response, f, indent=2)
        
        logger.info(f"Activity classification saved to: {output_path}")
        
        return response
    
    def generate_target_classification(self) -> Dict[str, Any]:
        """Generate target classification hierarchy."""
        
        prompt = """
        Generate a comprehensive military target classification hierarchy for an intelligence system.
        
        The classification should include three levels:
        1. target_type (main categories)
        2. target_sub_type (subcategories under each type)
        3. target_classification (specific classifications under each sub-type)
        
        Each classification should include:
        - id: A unique identifier (integer)
        - name: Descriptive name of the category
        - description: Detailed explanation
        - img_path: A placeholder path to a symbol (format: /symbols/target/{type}/{subtype}/{classification}.svg)
        
        The targets should cover all potential military and related entities relevant to border monitoring, including:
        - Personnel (infantry, special forces, civilian, etc.)
        - Vehicles (armored, transport, logistics, etc.)
        - Aircraft (helicopters, drones, fighters, etc.)
        - Installations (command posts, radar sites, artillery positions, etc.)
        - Vessels (patrol boats, fishing boats, etc.)
        
        Format the response as a JSON object with this structure:
        {
          "target_types": [
            {
              "id": 1,
              "name": "PERSONNEL",
              "description": "Human military or civilian personnel",
              "img_path": "/symbols/target/personnel.svg",
              "target_sub_types": [
                {
                  "id": 101,
                  "name": "INFANTRY",
                  "description": "Ground combat troops",
                  "img_path": "/symbols/target/personnel/infantry.svg",
                  "target_classifications": [
                    {
                      "id": 10101,
                      "name": "LIGHT_INFANTRY",
                      "description": "Light infantry units",
                      "img_path": "/symbols/target/personnel/infantry/light_infantry.svg"
                    },
                    // More classifications...
                  ]
                },
                // More sub-types...
              ]
            },
            // More target types...
          ]
        }
        
        SPECIFICALLY INCLUDE CLASSIFICATIONS FOR PAKISTANI AND CHINESE MILITARY EQUIPMENT AND UNITS.
        CREATE AT LEAST 5 TARGET TYPES, WITH AT LEAST 3 SUB-TYPES EACH, AND AT LEAST 2 CLASSIFICATIONS PER SUB-TYPE.
        ONLY RETURN THE JSON OBJECT WITH NO ADDITIONAL TEXT OR EXPLANATIONS.
        """
        
        logger.info("Generating target classification hierarchy...")
        
        response = self.client.generate_structured_data(prompt)
        
        output_path = os.path.join(OUTPUT_DIR, "target_classification.json")
        with open(output_path, 'w') as f:
            json.dump(response, f, indent=2)
        
        logger.info(f"Target classification saved to: {output_path}")
        
        return response
    
    def generate_incident_classification(self) -> Dict[str, Any]:
        """Generate incident classification hierarchy."""
        
        prompt = """
        Generate a comprehensive military incident classification hierarchy for an intelligence system.
        
        The classification should include three levels:
        1. incident_type (main categories)
        2. incident_sub_type (subcategories under each type)
        3. incident_classification (specific classifications under each sub-type)
        
        Each classification should include:
        - id: A unique identifier (integer)
        - name: Descriptive name of the category
        - description: Detailed explanation
        - img_path: A placeholder path to a symbol (format: /symbols/incident/{type}/{subtype}/{classification}.svg)
        
        The incidents should cover all potential military incidents relevant to border monitoring, including:
        - Border violations (incursions, crossings, etc.)
        - Ceasefire violations (different types of firing incidents)
        - Confrontations (face-offs, stone pelting, physical altercations)
        - Intelligence activities (reconnaissance, surveillance, etc.)
        - Construction incidents (infrastructure development)
        - Force posturing (exercises, deployments, etc.)
        
        Format the response as a JSON object with this structure:
        {
          "incident_types": [
            {
              "id": 1,
              "name": "BORDER_VIOLATION",
              "description": "Any crossing or violation of the established border",
              "img_path": "/symbols/incident/border_violation.svg",
              "incident_sub_types": [
                {
                  "id": 101,
                  "name": "TROOP_INCURSION",
                  "description": "Military personnel crossing the border",
                  "img_path": "/symbols/incident/border_violation/troop_incursion.svg",
                  "incident_classifications": [
                    {
                      "id": 10101,
                      "name": "ARMED_INCURSION",
                      "description": "Armed troops crossing the border",
                      "img_path": "/symbols/incident/border_violation/troop_incursion/armed.svg"
                    },
                    // More classifications...
                  ]
                },
                // More sub-types...
              ]
            },
            // More incident types...
          ]
        }
        
        INCLUDE INCIDENTS SPECIFIC TO BOTH INDIA-PAKISTAN AND INDIA-CHINA BORDERS.
        CREATE AT LEAST 5 INCIDENT TYPES, WITH AT LEAST 3 SUB-TYPES EACH, AND AT LEAST 2 CLASSIFICATIONS PER SUB-TYPE.
        ONLY RETURN THE JSON OBJECT WITH NO ADDITIONAL TEXT OR EXPLANATIONS.
        """
        
        logger.info("Generating incident classification hierarchy...")
        
        response = self.client.generate_structured_data(prompt)
        
        output_path = os.path.join(OUTPUT_DIR, "incident_classification.json")
        with open(output_path, 'w') as f:
            json.dump(response, f, indent=2)
        
        logger.info(f"Incident classification saved to: {output_path}")
        
        return response
    
    def generate_all_reference_data(self) -> Dict[str, Any]:
        """Generate all reference data classification hierarchies."""
        
        reference_data = {
            "activity_classification": self.generate_activity_classification(),
            "target_classification": self.generate_target_classification(),
            "incident_classification": self.generate_incident_classification()
        }
        
        # Save combined reference data
        output_path = os.path.join(OUTPUT_DIR, "reference_data_complete.json")
        with open(output_path, 'w') as f:
            json.dump(reference_data, f, indent=2)
        
        logger.info(f"Complete reference data saved to: {output_path}")
        
        return reference_data