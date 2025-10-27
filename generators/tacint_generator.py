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

class TacintGenerator:
    """Generate TACINT data with realistic correlation to ground truth events"""
    
    def __init__(self):
        self.client = AnthropicClient()
        self.correlation_engine = EventCorrelationEngine()
        self.formation_gen = FormationCodeGenerator()
        self.formation_gen.initialize_default_units()
    
    def generate_tacint_data(self, 
                            scenario: Dict[str, Any], 
                            reference_data: Dict[str, Any],
                            batch_size: int = 5) -> List[Dict[str, Any]]:
        """Generate correlated TACINT data"""
        
        logger.info(f"Generating correlated TACINT data for scenario: {scenario['scenario_name']}")
        
        all_tacint_records = []
        timeline = scenario.get("timeline", [])
        record_id = 1
        
        # Process in batches
        for i in range(0, len(timeline), batch_size):
            batch_timeline = timeline[i:i+batch_size]
            
            # Create correlation packages for all events in batch
            correlation_packages = []
            for day in batch_timeline:
                for event in day.get("events", []):
                    if "TACINT" in event.get("observable_by", []):
                        corr_pkg = self.correlation_engine.create_correlated_event(event)
                        corr_pkg["date"] = day["date"]
                        correlation_packages.append(corr_pkg)
            
            if not correlation_packages:
                continue
            
            prompt = self._create_correlated_tacint_prompt(
                scenario=scenario,
                correlation_packages=correlation_packages,
                reference_data=reference_data
            )
            
            logger.info(f"Generating TACINT batch {i//batch_size + 1} with {len(correlation_packages)} correlated events")
            
            try:
                batch_response = self.client.generate_structured_data(prompt)
                batch_records = batch_response.get("tacint_records", [])
                
                # Add IDs and formation info
                for record in batch_records:
                    record["id"] = record_id
                    record_id += 1
                    
                    # Get BSF or ground unit
                    unit_info = self.formation_gen.generate_support_unit("NC", "14", "bsf")
                    record.update({
                        "fmn_code": unit_info["fmn_code"],
                        "cmd_name": unit_info["cmd_name"],
                        "corps_name": unit_info["corps_name"],
                        "div_name": unit_info["div_name"],
                        "bde_name": unit_info["bde_name"],
                        "unit_name": unit_info["unit_name"],
                        "level": "Battalion"
                    })
                
                all_tacint_records.extend(batch_records)
                logger.info(f"Generated {len(batch_records)} TACINT records for batch")
                
            except Exception as e:
                logger.error(f"Error generating TACINT batch: {str(e)}")
                continue
        
        # Save generated data
        output_path = os.path.join(OUTPUT_DIR, f"tacint_data_{scenario['scenario_name']}.json")
        with open(output_path, 'w') as f:
            json.dump(all_tacint_records, f, indent=2)
        
        logger.info(f"TACINT data saved to: {output_path}")
        logger.info(f"Total TACINT records: {len(all_tacint_records)}")
        
        return all_tacint_records
    
    def _create_correlated_tacint_prompt(self, 
                                        scenario: Dict[str, Any],
                                        correlation_packages: List[Dict[str, Any]],
                                        reference_data: Dict[str, Any]) -> str:
        """Create prompt for generating correlated TACINT records"""
        
        # Extract TACINT observable events
        tacint_observable_events = []
        for pkg in correlation_packages:
            gt = pkg["ground_truth"]
            tacint_obs = pkg["source_observations"].get("TACINT", {})
            
            if tacint_obs:
                tacint_observable_events.append({
                    "correlation_id": pkg["correlation_id"],
                    "date": pkg["date"],
                    "base_time": gt["time"],
                    "time_offset_minutes": tacint_obs["time_offset_minutes"],
                    "actual_time": self.correlation_engine.get_time_adjusted_datetime(
                        gt["time"], 
                        tacint_obs["time_offset_minutes"]
                    ),
                    "event_type": gt["event_type"],
                    "actor": gt["actor"],
                    "location": gt["location"],
                    "location_name": gt.get("location_name", ""),
                    "equipment": gt.get("equipment_involved", []),
                    "strength": gt.get("strength", ""),
                    "description": gt["description"],
                    "tacint_specific": tacint_obs["observable_details"]
                })
        
        prompt = f"""
Generate realistic TACINT (Tactical Intelligence) records for the Kargil War based on ground observer reports.

SCENARIO: {scenario['scenario_description']}

YOUR ROLE: You are a GROUND OBSERVER from BSF observation posts or forward Indian Army positions. You report what you SEE, HEAR, and directly observe from your position.

CORRELATED EVENTS TO OBSERVE:
{json.dumps(tacint_observable_events, indent=2)}

CRITICAL TACINT OBSERVATION RULES:
1. GROUND-LEVEL PERSPECTIVE: You see things from mountain observation posts, not from above
2. HUMAN LIMITATIONS: Include realistic constraints - line of sight, weather, visibility, observer fatigue
3. OBSERVATION TOOLS: Binoculars, spotting scopes, thermal imaging, night vision
4. DISTANCE MATTERS: Closer observations are more detailed and confident
5. SENSORY DETAILS: Include sounds (artillery, engines), visual cues (dust, smoke), even smells
6. REPORTING DELAY: You observe first, then report (10-45 minutes after event starts)
7. GRADING SYSTEM: A1-A5 (source reliability), 1-5 (information accuracy)

GRADING EXAMPLES:
- A1: Reliable source, confirmed information
- A2: Reliable source, probably true
- B2: Usually reliable source, probably true
- C3: Fairly reliable source, possibly true
- D4: Not usually reliable source, doubtfully true

OBSERVATION METHODS BY DISTANCE:
- < 1km: Direct visual, equipment details visible, can hear voices
- 1-2.5km: Binocular observation, vehicle types identifiable, engine sounds
- 2.5-4km: Spotting scope needed, general equipment types, limited detail
- > 4km: Thermal imaging, difficult identification, count-based assessment

REALISTIC BSF/ARMY OBSERVATION POSTS:
- BSF OP Delta-7 (Forward observation, 2.5km from LoC)
- BSF OP Alpha-3 (Valley observation, 3.8km view distance)
- BSF Battalion 125 (Patrol elements)
- 18 Grenadiers Forward Post (Frontline position)

EXAMPLE TACINT RECORD:
{{
  "Date": "1999-06-15",
  "time": "10:55",
  "pre": "IMMEDIATE",
  "tgt_type": "VEHICLE",
  "tgt_sub_type": "ARMORED",
  "tgt_cl": "MAIN_BATTLE_TANK",
  "activity_type": "MOVEMENT",
  "activity_sub_type": "VEHICULAR",
  "activity_cl": "TACTICAL_DEPLOYMENT",
  "Incident_type": "BORDER_VIOLATION",
  "Incident_sub_type": "TROOP_INCURSION",
  "Incident_cl": "ARMORED_COLUMN",
  "source_agency": "BSF Observation Post Delta-7",
  "grading": "A2",
  "str": "11-13 vehicles",
  "long": 75.7528,
  "lat": 34.4246,
  "ht": 3378,
  "e": 384242,
  "n": 592138,
  "zone": "43S",
  "input": "Visual observation with thermal imaging",
  "description": "Column of tracked armored vehicles observed at 10:40 hours moving northeast along mountain road at range 2.8km. Visual identification through spotting scope confirms lead vehicles as Al-Khalid main battle tanks based on distinctive turret profile and reactive armor configuration. Count: 11-13 vehicles in tactical formation with approximately 50m spacing. Heavy engine noise audible even at this range. Column generating significant dust signature visible from OP. Weather conditions: clear visibility, light wind from southwest. Observation quality: good. Assessment: Deliberate tactical movement, not routine patrol - formation discipline and speed indicate operational deployment. Pakistani tactical markings visible on lead vehicles. Column direction suggests movement toward Point 5140 area. Continued observation maintained.",
  "upload_time": "1999-06-15 11:12",
  "correlation_id": "CORR_0042"
}}

GENERATE TACINT RECORDS:
- Create ONE record per correlated event
- Use ACTUAL_TIME (includes reporting delay after observation)
- Write in NARRATIVE style - a soldier describing what they observed
- Include sensory details (sights, sounds, environmental conditions)
- Use appropriate grading based on observation quality
- Mention observation method and distance
- Give count ranges with uncertainty qualifiers ("approximately", "estimated")
- Include realistic human observer details and limitations
- Reference correlation_id for tracking

FORMAT AS JSON:
{{
  "tacint_records": [
    // Array of TACINT records following the example format
  ]
}}

ONLY RETURN THE JSON OBJECT WITH NO ADDITIONAL TEXT.
"""
        
        return prompt