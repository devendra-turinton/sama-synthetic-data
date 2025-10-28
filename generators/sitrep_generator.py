# import os
# import json
# import logging
# from typing import Dict, List, Any
# from datetime import datetime

# from utils.anthropic_client import AnthropicClient
# from utils.formation_code_generator import FormationCodeGenerator
# from config import OUTPUT_DIR

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# class SitrepGenerator:
#     """Generate Situation Reports (SITREP) - Strategic level assessments"""
    
#     def __init__(self):
#         self.client = AnthropicClient()
#         self.formation_gen = FormationCodeGenerator()
#         self.formation_gen.initialize_default_units()
    
#     def generate_sitrep_data(self, 
#                             scenario: Dict[str, Any], 
#                             reference_data: Dict[str, Any],
#                             enemy_activity_data: List[Dict[str, Any]],
#                             batch_size: int = 7) -> List[Dict[str, Any]]:
#         """Generate SITREP data - one per day summarizing all activity"""
        
#         logger.info(f"Generating SITREP data for scenario: {scenario['scenario_name']}")
        
#         all_sitrep_records = []
#         timeline = scenario.get("timeline", [])
#         record_id = 1
#         sitrep_number = 1
        
#         # Process day by day (one SITREP per day)
#         for i in range(0, len(timeline), batch_size):
#             batch_timeline = timeline[i:i+batch_size]
            
#             # Group enemy activities by date
#             batch_dates = [day["date"] for day in batch_timeline]
#             batch_activities_by_date = {}
            
#             for date in batch_dates:
#                 batch_activities_by_date[date] = [
#                     activity for activity in enemy_activity_data
#                     if activity.get("upload_time", "").startswith(date)
#                 ]
            
#             prompt = self._create_sitrep_prompt(
#                 scenario=scenario,
#                 batch_timeline=batch_timeline,
#                 activities_by_date=batch_activities_by_date,
#                 reference_data=reference_data,
#                 start_sitrep_number=sitrep_number
#             )
            
#             logger.info(f"Generating SITREP batch {i//batch_size + 1} for {len(batch_timeline)} days")
            
#             try:
#                 batch_response = self.client.generate_structured_data(prompt)
#                 batch_records = batch_response.get("sitrep_records", [])
                
#                 # Add IDs, formation info, and SITREP numbers
#                 for record in batch_records:
#                     record["id"] = record_id
#                     record_id += 1
                    
#                     # SITREPs come from Division or Corps HQ
#                     unit_info = self.formation_gen.get_random_unit_by_level("Battalion")
#                     if unit_info:
#                         # Override with Division HQ
#                         record.update({
#                             "fmn_code": unit_info["fmn_code"][:6] + "0000",  # Division level code
#                             "cmd_name": unit_info["cmd_name"],
#                             "corps_name": unit_info["corps_name"],
#                             "div_name": unit_info["div_name"],
#                             "bde_name": "",
#                             "unit_name": f"{unit_info['div_name']} Headquarters",
#                             "level": "Division"
#                         })
                    
#                     # Add SITREP number to description
#                     if "description" in record:
#                         record["description"] = f"SITREP #{sitrep_number:03d}: " + record["description"]
                    
#                     sitrep_number += 1
                
#                 all_sitrep_records.extend(batch_records)
#                 logger.info(f"Generated {len(batch_records)} SITREP records for batch")
                
#             except Exception as e:
#                 logger.error(f"Error generating SITREP batch: {str(e)}")
#                 continue
        
#         # Save generated data
#         output_path = os.path.join(OUTPUT_DIR, f"sitrep_data_{scenario['scenario_name']}.json")
#         with open(output_path, 'w') as f:
#             json.dump(all_sitrep_records, f, indent=2)
        
#         logger.info(f"SITREP data saved to: {output_path}")
#         logger.info(f"Total SITREP records: {len(all_sitrep_records)}")
        
#         return all_sitrep_records
    
#     def _create_sitrep_prompt(self, 
#                              scenario: Dict[str, Any],
#                              batch_timeline: List[Dict[str, Any]],
#                              activities_by_date: Dict[str, List],
#                              reference_data: Dict[str, Any],
#                              start_sitrep_number: int) -> str:
#         """Create prompt for generating daily SITREPs"""
        
#         # Prepare daily summaries
#         daily_summaries = []
#         for day in batch_timeline:
#             date = day["date"]
#             activities = activities_by_date.get(date, [])
            
#             daily_summaries.append({
#                 "date": date,
#                 "day_number": day["day"],
#                 "phase": day.get("phase", ""),
#                 "timeline_events": day.get("events", []),
#                 "enemy_activities_count": len(activities),
#                 "enemy_activities_summary": [
#                     {
#                         "time": a.get("upload_time", ""),
#                         "activity_type": a.get("activity_type", ""),
#                         "target_type": a.get("tgt_type", ""),
#                         "strength": a.get("strength", ""),
#                         "location": a.get("input_method", ""),
#                         "confidence": a.get("confidence_level", ""),
#                         "description_excerpt": a.get("description", "")[:200]
#                     }
#                     for a in activities[:5]  # Limit to top 5 for context
#                 ]
#             })
        
#         prompt = f"""
# Generate daily SITUATION REPORTS (SITREPs) for the Kargil War at Division/Corps level.

# SCENARIO: {scenario['scenario_description']}

# YOUR ROLE: You are a DIVISION/CORPS OPERATIONS OFFICER preparing formal daily situation reports for higher command. SITREPs are strategic-level assessments that:
# 1. Summarize all enemy activity for the day
# 2. Assess enemy intentions and capabilities
# 3. Report friendly force posture and actions
# 4. Provide commander's assessment
# 5. Make recommendations

# DAILY INTELLIGENCE SUMMARIES:
# {json.dumps(daily_summaries, indent=2)}

# SITREP FORMAT AND RULES:

# **Structure:**
# 1. **Enemy Situation**: Summarize all enemy activities, grouped by type/significance
# 2. **Intelligence Assessment**: What do these activities mean? What is enemy intent?
# 3. **Friendly Forces**: Our posture, actions taken, current status
# 4. **Commander's Assessment**: Overall situation evaluation
# 5. **Recommendations**: Proposed actions or alerts

# **Writing Style:**
# - Formal military language
# - Past tense for completed actions, present tense for current status
# - Clear, concise, actionable
# - Use military terminology correctly
# - Reference specific units and locations

# **DO NOT:**
# - Mention intelligence sources by name in the narrative (no "ELINT reports" or "TACINT observed")
# - Simply list activities without analysis
# - Use uncertain language in the title/opening (be authoritative in assessment)

# **DO:**
# - Synthesize multiple activities into coherent narrative
# - Provide strategic context and implications
# - Include both enemy AND friendly force information
# - Give clear commander's assessment
# - Make actionable recommendations

# EXAMPLE SITREP:
# {{
#   "Incident_date": "1999-06-15",
#   "time": "18:00",
#   "pre": "PRIORITY",
#   "Incident_type": "FORCE_POSTURING",
#   "Incident_sub_type": "COORDINATED_OPERATION",
#   "Incident_cl": "BORDER_PRESSURE",
#   "source": "Division Intelligence Summary",
#   "str_own": "One infantry brigade (3 battalions), two BSF battalions, artillery support",
#   "str_en": "One armored company (12 MBTs), one infantry battalion, supporting elements",
#   "long": 75.7530,
#   "lat": 34.4248,
#   "ht": 3376,
#   "e": 384239,
#   "n": 592141,
#   "zone": "43S",
#   "Incident_states": "ONGOING",
#   "description": "Pakistani forces conducted coordinated pressure operation along Line of Control in Drass sector during period 0800-1700 hours. Primary activity consisted of armored company (12 Al-Khalid MBTs) redeployment from reserve positions to forward staging area vicinity Point 5140, accompanied by increased tactical communications and supporting infantry movements. \\n\\nINTELLIGENCE ASSESSMENT: Activity pattern indicates deliberate operational preparation rather than routine positioning. Armor concentration provides rapid escalation capability and suggests potential for limited offensive action within 24-48 hours. Assessment based on multi-source intelligence correlation with high confidence. \\n\\nFRIENDLY FORCES: 28 Mountain Brigade has reinforced forward defensive positions at Point 5140. Artillery batteries brought to immediate readiness state. Air support coordinated with Western Air Command, Mirage 2000 on standby. BSF observation posts maintaining continuous surveillance. No engagement between forces at this time. \\n\\nCOMMANDER'S ASSESSMENT: Current Pakistani posturing assessed as probe of Indian defensive posture and demonstration of escalation capability. While immediate assault not imminent, force disposition enables rapid offensive action if ordered. Situation warrants sustained heightened alert but does not require immediate preemptive action. \\n\\nRECOMMENDATIONS: Maintain current alert status. Continue intensive surveillance. Brief air assets for potential close air support missions. Monitor for additional indicators of attack preparation (artillery positioning, logistics buildup). Situation update required every 6 hours.",
#   "upload_time": "1999-06-15 18:30"
# }}

# GENERATE SITREPS:
# - Create ONE SITREP per day in the batch
# - Each SITREP summarizes ALL activities for that day
# - Include both enemy and friendly force information
# - Provide strategic assessment and recommendations
# - Use formal military SITREP format
# - Time should be 18:00 (evening SITREP) for each day
# - Number SITREPs sequentially starting from {start_sitrep_number}

# FORMAT AS JSON:
# {{
#   "sitrep_records": [
#     // Array of daily SITREP records
#   ]
# }}

# ONLY RETURN THE JSON OBJECT WITH NO ADDITIONAL TEXT.
# """
        
#         return prompt

import os
import json
import logging
from typing import Dict, List, Any

from utils.anthropic_client import AnthropicClient
from config import OUTPUT_DIR, OBSERVING_UNITS, FORMATION_MAPPING

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SitrepGenerator:
    """Generate Electronic Situation Reports (e_sitrep_mst) - Incident-based reporting"""
    
    SYSTEM_PROMPT = """You are a Battalion/Brigade commander reporting Electronic Situation Reports (e_sitrep).

CRITICAL: e_sitrep is INCIDENT-BASED reporting, NOT daily summaries!
- Generate ONE e_sitrep per significant incident/event
- Each report focuses on ONE specific incident
- Include both enemy AND friendly force information for that incident
- Report incident state (ONGOING or COMPLETED)

RULES:
- Focus on specific incidents (border violations, confrontations, engagements, buildups)
- Include both str_own (friendly forces) and str_en (enemy forces) for the incident
- Describe the specific incident, not a day's summary
- Use formal incident reporting language
- Include tactical details relevant to this specific incident

FORMAT: JSON with "sitrep_records" array.
IMPORTANT: Generate 6 records (one per significant incident)."""
    
    def __init__(self):
        self.client = AnthropicClient()
        self.unit_fmn_codes = OBSERVING_UNITS["SITREP"]
    
    def generate_sitrep_data(self, 
                            scenario: Dict[str, Any], 
                            reference_data: Dict[str, Any],
                            enemy_activity_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate incident-based e_sitrep records"""
        
        logger.info(f"Generating e_sitrep (incident reports) for: {scenario['scenario_name']}")
        
        timeline = scenario.get("timeline", [])
        
        if not timeline:
            return []
        
        all_sitreps = []
        record_id = 1
        
        for day_idx, day in enumerate(timeline):
            date = day["date"]
            events = day.get("events", [])
            
            # Get enemy activities for context (but we generate based on events)
            day_activities = [
                a for a in enemy_activity_data
                if a.get("upload_time", "").startswith(date)
            ]
            
            prompt = self._create_incident_sitrep_prompt(date, events, day_activities)
            
            logger.info(f"Generating incident e_sitrep records for {date}: {len(events)} events")
            
            try:
                response = self.client.generate_structured_data(
                    prompt, 
                    system_prompt=self.SYSTEM_PROMPT
                )
                sitreps = response.get("sitrep_records", [])
                
                # Ensure sitreps is a list of dicts
                if not isinstance(sitreps, list):
                    logger.error(f"e_sitrep response is not a list: {type(sitreps)}")
                    continue
                
                for record in sitreps:
                    if not isinstance(record, dict):
                        logger.warning(f"Skipping non-dict e_sitrep record: {type(record)}")
                        continue
                    
                    record["id"] = record_id
                    record_id += 1
                    
                    # Add unit info (Battalion/Brigade level reporting)
                    try:
                        fmn_code = self.unit_fmn_codes[0]
                        unit_info = FORMATION_MAPPING[fmn_code].copy()
                        unit_info["fmn_code"] = fmn_code
                        # Override to Battalion level (e_sitrep typically from Battalion)
                        unit_info["level"] = "Battalion"
                        record.update(unit_info)
                    except Exception as e:
                        logger.error(f"Error adding unit info to e_sitrep: {e}")
                        continue
                
                all_sitreps.extend(sitreps)
                logger.info(f"Generated {len(sitreps)} e_sitrep records for {date}")
                
            except Exception as e:
                logger.error(f"Error generating e_sitrep for {date}: {str(e)}", exc_info=True)
                continue
        
        # Save
        output_path = os.path.join(OUTPUT_DIR, f"sitrep_data_{scenario['scenario_name']}.json")
        with open(output_path, 'w') as f:
            json.dump(all_sitreps, f, indent=2)
        
        logger.info(f"e_sitrep data saved: {output_path} ({len(all_sitreps)} records)")
        return all_sitreps
    
    def _create_incident_sitrep_prompt(self, date: str, events: List[Dict], 
                                       enemy_activities: List[Dict]) -> str:
        """Create prompt for incident-based e_sitrep generation"""
        
        # Summarize events
        event_summaries = []
        for idx, event in enumerate(events):
            event_summaries.append({
                "time": event.get("time"),
                "event_type": event.get("event_type"),
                "actor": event.get("actor"),
                "location_name": event.get("location_name"),
                "description": event.get("description", "")[:100]
            })
        
        prompt = f"""Date: {date}

Incidents/Events today:
{json.dumps(event_summaries, indent=1)}

Generate 6 Electronic Situation Reports (e_sitrep), one for each significant incident.

Each e_sitrep record must include:
- Incident_date: "{date}"
- time: (incident time, e.g., "08:15")
- pre: PRIORITY/IMMEDIATE/ROUTINE
- Incident_type: (e.g., "BORDER_VIOLATION", "FORCE_POSTURING", "CEASEFIRE_VIOLATION")
- Incident_sub_type: (e.g., "TROOP_INCURSION", "EQUIPMENT_BUILDUP")
- Incident_cl: (specific classification)
- source: "Battalion observation post" or "Brigade intelligence"
- str_own: (friendly forces at incident, e.g., "One infantry company, BSF platoon")
- str_en: (enemy forces at incident, e.g., "Pakistani squad, 8-10 personnel")
- long: (76.1-76.5)
- lat: (34.4-34.7)
- ht: (3000-5000)
- e: (383000-385000)
- n: (3815000-3820000)
- zone: "43S"
- Incident_states: "ONGOING" or "COMPLETED"
- description: (Describe THIS SPECIFIC INCIDENT - what happened, when, where, current status, actions taken. 3-4 sentences. Focus on ONE incident, not the whole day.)
- upload_time: "{date} HH:MM" (shortly after incident)

CRITICAL: Each e_sitrep reports ONE SPECIFIC INCIDENT, not a daily summary!
Example description: "Pakistani squad of 8-10 personnel crossed LoC at Point 5140 at 08:15 hours. BSF observation post detected movement and alerted battalion. Indian forces deployed one infantry platoon to intercept. Incident ongoing, forces in visual contact."

Return JSON: {{"sitrep_records": [... 6 incident reports ...]}}
"""
        
        return prompt