import os
import json
import logging
from typing import Dict, Any

from utils.anthropic_client import AnthropicClient
from config import OUTPUT_DIR, ANTHROPIC_API_KEY, MODEL_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReferenceDataGenerator:
    """Generate military classification reference data"""
    
    def __init__(self):
        self.client = AnthropicClient(
            api_key=ANTHROPIC_API_KEY,
            model=MODEL_CONFIG["model"],
            max_tokens=MODEL_CONFIG["max_tokens"],
            temperature=MODEL_CONFIG["temperature"]
        )
    
    def generate_all_reference_data(self) -> Dict[str, Any]:
        """Generate all reference data, with fallback to cached or minimal data"""
        
        reference_data_path = os.path.join(OUTPUT_DIR, "reference_data_complete.json")
        
        # Try to load cached reference data
        if os.path.exists(reference_data_path):
            logger.info("Loading cached reference data...")
            try:
                with open(reference_data_path, 'r') as f:
                    reference_data = json.load(f)
                logger.info("✓ Reference data loaded from cache")
                return reference_data
            except Exception as e:
                logger.warning(f"Failed to load cached data: {e}")
        
        # Generate new reference data
        logger.info("Generating new reference data...")
        
        try:
            reference_data = {
                "activity_classification": self.generate_activity_classification(),
                "target_classification": self.generate_target_classification(),
                "incident_classification": self.generate_incident_classification()
            }
            
            # Save for future use
            with open(reference_data_path, 'w') as f:
                json.dump(reference_data, f, indent=2)
            
            logger.info("✓ Reference data generated and cached")
            return reference_data
            
        except Exception as e:
            logger.error(f"Failed to generate reference data: {e}")
            logger.info("Using minimal fallback reference data...")
            return self._get_fallback_reference_data()
    

    def generate_activity_classification(self) -> Dict[str, Any]:
      """Generate activity classification hierarchy"""
      
      # ULTRA EXPLICIT prompt
      prompt = """YOUR RESPONSE MUST START WITH { AND END WITH }

  DO NOT write "Here is the JSON:" or any other text before the JSON.
  DO NOT write any explanations after the JSON.

  Generate this exact structure (replace my examples with your content):

  {"activity_types":[{"id":1,"name":"MOVEMENT","description":"Troop and equipment movement operations","img_path":"/symbols/activity/movement.svg","activity_sub_types":[{"id":101,"name":"FOOT_PATROL","description":"Infantry movement on foot","img_path":"/symbols/activity/movement/foot_patrol.svg","activity_classifications":[{"id":10101,"name":"RECONNAISSANCE_PATROL","description":"Small unit reconnaissance mission","img_path":"/symbols/activity/movement/foot_patrol/reconnaissance.svg"},{"id":10102,"name":"COMBAT_PATROL","description":"Armed patrol seeking engagement","img_path":"/symbols/activity/movement/foot_patrol/combat.svg"}]},{"id":102,"name":"VEHICULAR","description":"Vehicle-based movement","img_path":"/symbols/activity/movement/vehicular.svg","activity_classifications":[{"id":10201,"name":"TACTICAL_DEPLOYMENT","description":"Tactical vehicle deployment","img_path":"/symbols/activity/movement/vehicular/tactical.svg"},{"id":10202,"name":"LOGISTICS_CONVOY","description":"Supply and logistics movement","img_path":"/symbols/activity/movement/vehicular/logistics.svg"}]}]}]}

  Generate 5 activity types: MOVEMENT, COMBAT, CONSTRUCTION, RECONNAISSANCE, LOGISTICS
  Each with 3 sub-types
  Each sub-type with 2-3 classifications

  Your response must be valid JSON starting with { and ending with }. NO OTHER TEXT."""
      
      try:
          response = self.client.generate_structured_data(prompt)
          logger.info("✓ Activity classification generated")
          return response
      except Exception as e:
          logger.error(f"Failed to generate activity classification: {e}")
          return {
              "activity_types": [
                  {
                      "id": 1,
                      "name": "MOVEMENT",
                      "description": "Troop and equipment movement",
                      "img_path": "/symbols/activity/movement.svg",
                      "activity_sub_types": [
                          {
                              "id": 101,
                              "name": "VEHICULAR",
                              "description": "Vehicle-based movement",
                              "img_path": "/symbols/activity/movement/vehicular.svg",
                              "activity_classifications": [
                                  {
                                      "id": 10101,
                                      "name": "TACTICAL_DEPLOYMENT",
                                      "description": "Tactical vehicle deployment",
                                      "img_path": "/symbols/activity/movement/vehicular/tactical.svg"
                                  }
                              ]
                          }
                      ]
                  }
              ]
          }


    def generate_target_classification(self) -> Dict[str, Any]:
        """Generate target classification hierarchy"""
        
        prompt = """Generate military target classification hierarchy for Kargil War.

Include these main types:
1. PERSONNEL (infantry, special forces, support troops)
2. VEHICLE (armored, transport, logistics)
3. AIRCRAFT (fighters, helicopters, UAVs)
4. INSTALLATION (command posts, radar sites, artillery positions)
5. EQUIPMENT (weapons, communications, supplies)

Must include Pakistani equipment:
- Al-Khalid MBT, T-59/T-69 tanks
- F-16, Mirage III/V aircraft
- 130mm artillery, 122mm howitzers

Return ONLY valid JSON in format:
{
  "target_types": [
    {
      "id": 1,
      "name": "VEHICLE",
      "description": "Military vehicles",
      "img_path": "/symbols/target/vehicle.svg",
      "target_sub_types": [
        {
          "id": 101,
          "name": "ARMORED",
          "description": "Armored fighting vehicles",
          "img_path": "/symbols/target/vehicle/armored.svg",
          "target_classifications": [
            {
              "id": 10101,
              "name": "MAIN_BATTLE_TANK",
              "description": "Main battle tanks like Al-Khalid",
              "img_path": "/symbols/target/vehicle/armored/mbt.svg"
            }
          ]
        }
      ]
    }
  ]
}

Generate at least 5 target types, 3 sub-types each, 2 classifications per sub-type."""
        
        try:
            response = self.client.generate_structured_data(prompt)
            logger.info("✓ Target classification generated")
            return response
        except Exception as e:
            logger.error(f"Failed to generate target classification: {e}")
            return {"target_types": []}
    
    def generate_incident_classification(self) -> Dict[str, Any]:
        """Generate incident classification hierarchy"""
        
        prompt = """
        Generate military incident classification hierarchy for Kargil War e_sitrep reporting.

        Include these main types:
        1. BORDER_VIOLATION (troop incursion, vehicle crossing, aerial intrusion)
        2. CEASEFIRE_VIOLATION (small arms fire, artillery fire, mortar fire)
        3. CONFRONTATION (face-off, stone pelting, physical altercation)
        4. FORCE_POSTURING (equipment buildup, troop deployment, exercises)
        5. INTELLIGENCE_ACTIVITY (reconnaissance, surveillance, probing)

        STRICTLY FOLLOW THESE RULES FOR THE JSON OUTPUT:
        - Return ONLY a single, valid JSON object, no explanations, markdown, code blocks, or extra text before or after the JSON.
        - The JSON must be minified (no extra whitespace or indentation).
        - Do not include any trailing commas, comments, or omitted punctuation.
        - Double-check that all brackets, braces, and commas are present and correct.
        - Ensure all string values are properly quoted and terminated.
        - Do not use '//' or any other comment syntax in the output.
        - Do not include any fields with unterminated strings.
        - Do not include any extra fields or text outside the JSON object.
        - If you are unsure, validate the JSON before returning.

        Return ONLY valid JSON in format:
        {
          "incident_types": [
            {
              "id": 1,
              "name": "BORDER_VIOLATION",
              "description": "Crossing or violation of established border",
              "img_path": "/symbols/incident/border_violation.svg",
              "incident_sub_types": [
                {
                  "id": 101,
                  "name": "TROOP_INCURSION",
                  "description": "Military personnel crossing border",
                  "img_path": "/symbols/incident/border_violation/troop_incursion.svg",
                  "incident_classifications": [
                    {
                      "id": 10101,
                      "name": "ARMED_INCURSION",
                      "description": "Armed troops crossing border",
                      "img_path": "/symbols/incident/border_violation/troop_incursion/armed.svg"
                    }
                  ]
                }
              ]
            }
          ]
        }

        Generate at least 5 incident types, 3 sub-types each, 2 classifications per sub-type.
        """
        
        try:
            response = self.client.generate_structured_data(prompt)
            logger.info("✓ Incident classification generated")
            return response
        except Exception as e:
            logger.error(f"Failed to generate incident classification: {e}")
            return {"incident_types": []}
    
    def _get_fallback_reference_data(self) -> Dict[str, Any]:
        """Minimal fallback reference data if generation fails"""
        return {
            "activity_classification": {
                "activity_types": [
                    {
                        "id": 1,
                        "name": "MOVEMENT",
                        "description": "Troop and equipment movement",
                        "img_path": "/symbols/activity/movement.svg",
                        "activity_sub_types": [
                            {
                                "id": 101,
                                "name": "VEHICULAR",
                                "description": "Vehicle-based movement",
                                "img_path": "/symbols/activity/movement/vehicular.svg",
                                "activity_classifications": [
                                    {
                                        "id": 10101,
                                        "name": "TACTICAL_DEPLOYMENT",
                                        "description": "Tactical vehicle deployment",
                                        "img_path": "/symbols/activity/movement/vehicular/tactical.svg"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            },
            "target_classification": {
                "target_types": [
                    {
                        "id": 1,
                        "name": "VEHICLE",
                        "description": "Military vehicles",
                        "img_path": "/symbols/target/vehicle.svg",
                        "target_sub_types": [
                            {
                                "id": 101,
                                "name": "ARMORED",
                                "description": "Armored vehicles",
                                "img_path": "/symbols/target/vehicle/armored.svg",
                                "target_classifications": [
                                    {
                                        "id": 10101,
                                        "name": "MAIN_BATTLE_TANK",
                                        "description": "Main battle tanks",
                                        "img_path": "/symbols/target/vehicle/armored/mbt.svg"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            },
            "incident_classification": {
                "incident_types": [
                    {
                        "id": 1,
                        "name": "BORDER_VIOLATION",
                        "description": "Border crossing incidents",
                        "img_path": "/symbols/incident/border_violation.svg",
                        "incident_sub_types": [
                            {
                                "id": 101,
                                "name": "TROOP_INCURSION",
                                "description": "Troop border crossings",
                                "img_path": "/symbols/incident/border_violation/troop.svg",
                                "incident_classifications": [
                                    {
                                        "id": 10101,
                                        "name": "ARMED_INCURSION",
                                        "description": "Armed border crossing",
                                        "img_path": "/symbols/incident/border_violation/troop/armed.svg"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }