# import os
# import json
# import logging
# from typing import Dict, List, Any

# from utils.anthropic_client import AnthropicClient
# from utils.formation_code_generator import FormationCodeGenerator
# from config import OUTPUT_DIR

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# class EnemyActivityGenerator:
#     """Generate Enemy Activity data by fusing multiple intelligence sources"""
    
#     def __init__(self):
#         self.client = AnthropicClient()
#         self.formation_gen = FormationCodeGenerator()
#         self.formation_gen.initialize_default_units()
    
#     def generate_enemy_activity_data(self, 
#                                     scenario: Dict[str, Any], 
#                                     reference_data: Dict[str, Any],
#                                     elint_data: List[Dict[str, Any]],
#                                     imint_data: List[Dict[str, Any]],
#                                     tacint_data: List[Dict[str, Any]],
#                                     batch_size: int = 10) -> List[Dict[str, Any]]:
#         """Generate Enemy Activity by correlating and fusing intelligence sources"""
        
#         logger.info(f"Generating Enemy Activity data with intelligence fusion for scenario: {scenario['scenario_name']}")
        
#         all_enemy_activity_records = []
#         record_id = 1
        
#         # Group all intelligence by correlation_id
#         correlation_groups = self._group_by_correlation(elint_data, imint_data, tacint_data)
        
#         logger.info(f"Found {len(correlation_groups)} correlation groups for fusion")
        
#         # Process correlation groups in batches
#         correlation_ids = list(correlation_groups.keys())
        
#         for i in range(0, len(correlation_ids), batch_size):
#             batch_ids = correlation_ids[i:i+batch_size]
#             batch_groups = {cid: correlation_groups[cid] for cid in batch_ids}
            
#             prompt = self._create_fusion_prompt(
#                 scenario=scenario,
#                 correlation_groups=batch_groups,
#                 reference_data=reference_data
#             )
            
#             logger.info(f"Generating Enemy Activity batch {i//batch_size + 1} with {len(batch_groups)} fusion groups")
            
#             try:
#                 batch_response = self.client.generate_structured_data(prompt)
#                 batch_records = batch_response.get("enemy_activity_records", [])
                
#                 # Add IDs and formation info
#                 for record in batch_records:
#                     record["id"] = record_id
#                     record_id += 1
                    
#                     # Get fusion cell unit
#                     unit_info = self.formation_gen.generate_support_unit("NC", "14", "intelligence")
#                     unit_info["unit_name"] = "Intelligence Fusion Cell"
#                     unit_info["level"] = "Division"
                    
#                     record.update({
#                         "fmn_code": unit_info["fmn_code"],
#                         "cmd_name": unit_info["cmd_name"],
#                         "corps_name": unit_info["corps_name"],
#                         "div_name": unit_info["div_name"],
#                         "bde_name": unit_info["bde_name"],
#                         "unit_name": unit_info["unit_name"],
#                         "level": unit_info["level"]
#                     })
                
#                 all_enemy_activity_records.extend(batch_records)
#                 logger.info(f"Generated {len(batch_records)} Enemy Activity records for batch")
                
#             except Exception as e:
#                 logger.error(f"Error generating Enemy Activity batch: {str(e)}")
#                 continue
        
#         # Save generated data
#         output_path = os.path.join(OUTPUT_DIR, f"enemy_activity_data_{scenario['scenario_name']}.json")
#         with open(output_path, 'w') as f:
#             json.dump(all_enemy_activity_records, f, indent=2)
        
#         logger.info(f"Enemy Activity data saved to: {output_path}")
#         logger.info(f"Total Enemy Activity records: {len(all_enemy_activity_records)}")
        
#         return all_enemy_activity_records
    
#     def _group_by_correlation(self, elint_data: List, imint_data: List, tacint_data: List) -> Dict:
#         """Group intelligence records by correlation_id"""
#         correlation_groups = {}
        
#         # Group ELINT
#         for record in elint_data:
#             corr_id = record.get("correlation_id")
#             if corr_id:
#                 if corr_id not in correlation_groups:
#                     correlation_groups[corr_id] = {"elint": [], "imint": [], "tacint": []}
#                 correlation_groups[corr_id]["elint"].append(record)
        
#         # Group IMINT
#         for record in imint_data:
#             corr_id = record.get("correlation_id")
#             if corr_id:
#                 if corr_id not in correlation_groups:
#                     correlation_groups[corr_id] = {"elint": [], "imint": [], "tacint": []}
#                 correlation_groups[corr_id]["imint"].append(record)
        
#         # Group TACINT
#         for record in tacint_data:
#             corr_id = record.get("correlation_id")
#             if corr_id:
#                 if corr_id not in correlation_groups:
#                     correlation_groups[corr_id] = {"elint": [], "imint": [], "tacint": []}
#                 correlation_groups[corr_id]["tacint"].append(record)
        
#         return correlation_groups
    
#     def _create_fusion_prompt(self, 
#                              scenario: Dict[str, Any],
#                              correlation_groups: Dict[str, Any],
#                              reference_data: Dict[str, Any]) -> str:
#         """Create prompt for intelligence fusion"""
        
#         # Prepare correlation groups for prompt
#         fusion_data = []
#         for corr_id, sources in correlation_groups.items():
#             fusion_data.append({
#                 "correlation_id": corr_id,
#                 "elint_observations": sources["elint"],
#                 "imint_observations": sources["imint"],
#                 "tacint_observations": sources["tacint"],
#                 "source_count": len([s for s in [sources["elint"], sources["imint"], sources["tacint"]] if s])
#             })
        
#         prompt = f"""
# Generate Enemy Activity records by FUSING multiple intelligence sources for the Kargil War.

# SCENARIO: {scenario['scenario_description']}

# YOUR ROLE: You are an INTELLIGENCE FUSION ANALYST. Your job is to:
# 1. Correlate observations from ELINT, IMINT, and TACINT
# 2. Resolve conflicts between sources
# 3. Create higher-confidence assessments when sources agree
# 4. Produce comprehensive enemy activity reports

# CORRELATED INTELLIGENCE GROUPS:
# {json.dumps(fusion_data, indent=2)}

# FUSION ANALYSIS RULES:

# **Confidence Levels:**
# - CONFIRMED: All 3 sources agree (ELINT + IMINT + TACINT)
# - HIGH CONFIDENCE: 2 sources agree with strong evidence
# - PROBABLE: 2 sources agree with some uncertainty
# - POSSIBLE: Only 1 source, or sources conflict

# **Resolving Conflicts:**
# - Strength counts: Average across sources (IMINT most accurate for counts)
# - Equipment ID: TACINT and IMINT trump ELINT (visual confirmation beats electronic inference)
# - Timing: Use earliest detection time (usually ELINT)
# - Location: Use IMINT coordinates (most accurate GPS)

# **Description Style:**
# Your descriptions must:
# 1. Start with confidence level (CONFIRMED/HIGH CONFIDENCE/PROBABLE/POSSIBLE)
# 2. State the activity clearly
# 3. Cite specific sources that corroborate: "Corroborated by ELINT detection at 08:15, IMINT satellite pass at 08:35, and TACINT ground observation at 08:50"
# 4. Highlight agreements: "All sources confirm Al-Khalid tank identification"
# 5. Note discrepancies: "TACINT reports 11-13 vehicles, IMINT confirms 10-12, assessment: 12 vehicles"
# 6. Provide intelligence assessment of significance

# **Do NOT say:** "Activity observed by multiple assets"
# **DO say:** "CONFIRMED Pakistani armored company movement. Corroborated by ELINT (TRC-20H communications 08:15), IMINT (satellite imagery 08:35 confirming 10-12 Al-Khalid MBTs), and TACINT (BSF OP Delta-7 visual confirmation 08:50 of 11-13 tanks). All sources agree on equipment type and tactical formation. Assessment: Deliberate operational deployment."

# EXAMPLE ENEMY ACTIVITY RECORD:
# {{
#   "sensor_type": "MULTI-SOURCE-FUSION",
#   "sensor_id": "FUSION-CELL-14-CORPS",
#   "tgt_type": "VEHICLE",
#   "tgt_sub_type": "ARMORED",
#   "tgt_cl": "MAIN_BATTLE_TANK",
#   "activity_type": "MOVEMENT",
#   "activity_sub_type": "VEHICULAR",
#   "activity_cl": "TACTICAL_DEPLOYMENT",
#   "bearing": "275",
#   "range_km": "8.5",
#   "strength": "Company-strength (12 Al-Khalid MBTs)",
#   "long": 75.7531,
#   "lat": 34.4247,
#   "ht": 3376,
#   "e": 384238,
#   "n": 592140,
#   "zone": "43S",
#   "input_method": "Multi-source intelligence fusion",
#   "description": "CONFIRMED Pakistani armored company movement toward Point 5140 sector. Activity detected by ELINT at 08:15 hours (encrypted TRC-20H tactical communications indicating battalion-level coordination), corroborated by IMINT satellite pass at 08:35 (imagery confirms 10-12 Al-Khalid main battle tanks in tactical column formation), and verified by TACINT ground observation at 08:50 from BSF OP Delta-7 (visual identification of 11-13 tanks at 2.8km range). All three sources independently confirm equipment type as Al-Khalid MBT with consistent location coordinates (±100m variance). Movement pattern and formation discipline indicate deliberate tactical deployment rather than routine patrol. INTELLIGENCE ASSESSMENT: High probability of staging for assault operations against Indian positions at Point 5140. Recommend heightened alert status and artillery preparation. THREAT LEVEL: HIGH.",
#   "upload_time": "1999-06-15 09:30",
#   "correlation_id": "CORR_0042",
#   "confidence_level": "CONFIRMED",
#   "sources_corroborated": "ELINT, IMINT, TACINT"
# }}

# GENERATE ENEMY ACTIVITY RECORDS:
# - Create ONE fused record per correlation group
# - Synthesize information from all available sources
# - Use the BEST data from each source (IMINT for counts, ELINT for timing, TACINT for details)
# - Explicitly cite which sources corroborate the assessment
# - Include confidence level based on source agreement
# - Provide intelligence assessment of significance
# - Use coordinates from IMINT (most accurate)
# - Include correlation_id for tracking

# FORMAT AS JSON:
# {{
#   "enemy_activity_records": [
#     // Array of fused Enemy Activity records
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

class EnemyActivityGenerator:
    """Generate Enemy Activity by fusing intelligence sources"""
    
    SYSTEM_PROMPT = """You are an Intelligence Fusion Analyst correlating multiple sources.

FUSION RULES:
1. CONFIDENCE LEVELS:
   - CONFIRMED: All 3 sources agree
   - HIGH CONFIDENCE: 2 sources with strong evidence
   - PROBABLE: 2 sources with some uncertainty
   - POSSIBLE: Only 1 source

2. RESOLVING CONFLICTS:
   - Strength: Average across sources (IMINT most accurate)
   - Equipment ID: TACINT/IMINT trump ELINT (visual beats electronic)
   - Timing: Use earliest detection
   - Location: Use IMINT coordinates (most accurate)

3. DESCRIPTION MUST:
   - Start with confidence level
   - Cite specific sources with times
   - Highlight agreements/discrepancies
   - Provide intelligence assessment

4. ALWAYS provide realistic values for all fields (no zeros)

EXAMPLE: "CONFIRMED Pakistani armored company movement. Corroborated by ELINT (08:05), IMINT (08:35, 10-12 tanks), TACINT (08:55, 11-13 tanks). All sources confirm Al-Khalid MBT. Assessment: Deliberate operational deployment."

FORMAT: JSON with "enemy_activity_records" array.
IMPORTANT: Generate 6 records per day (one per major correlation group)."""
    
    def __init__(self):
        self.client = AnthropicClient()
        self.unit_fmn_codes = OBSERVING_UNITS["FUSION"]
    
    def generate_enemy_activity_data(self, 
                                    scenario: Dict[str, Any], 
                                    reference_data: Dict[str, Any],
                                    elint_data: List[Dict[str, Any]],
                                    imint_data: List[Dict[str, Any]],
                                    tacint_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate fused Enemy Activity records"""
        
        logger.info(f"Generating Enemy Activity (fusion) for: {scenario['scenario_name']}")
        
        # Group by correlation_id
        correlation_groups = self._group_by_correlation(elint_data, imint_data, tacint_data)
        
        logger.info(f"Found {len(correlation_groups)} correlation groups")
        
        if not correlation_groups:
            logger.warning("No correlation groups found!")
            return []
        
        prompt = self._create_compact_prompt(correlation_groups)
        
        try:
            response = self.client.generate_structured_data(
                prompt, 
                system_prompt=self.SYSTEM_PROMPT
            )
            records = response.get("enemy_activity_records", [])
            
            # Add IDs and unit info
            for idx, record in enumerate(records):
                record["id"] = idx + 1
                
                fmn_code = self.unit_fmn_codes[0]  # Fusion cell
                unit_info = FORMATION_MAPPING[fmn_code].copy()
                unit_info["fmn_code"] = fmn_code
                record.update(unit_info)
            
            # Save
            output_path = os.path.join(OUTPUT_DIR, f"enemy_activity_data_{scenario['scenario_name']}.json")
            with open(output_path, 'w') as f:
                json.dump(records, f, indent=2)
            
            logger.info(f"Enemy Activity saved: {output_path} ({len(records)} records)")
            return records
            
        except Exception as e:
            logger.error(f"Error generating Enemy Activity: {str(e)}")
            return []
    
    def _group_by_correlation(self, elint, imint, tacint) -> Dict:
        """Group by correlation_id"""
        groups = {}
        
        for record in elint:
            cid = record.get("correlation_id")
            if cid:
                if cid not in groups:
                    groups[cid] = {"elint": [], "imint": [], "tacint": []}
                groups[cid]["elint"].append(record)
        
        for record in imint:
            cid = record.get("correlation_id")
            if cid:
                if cid not in groups:
                    groups[cid] = {"elint": [], "imint": [], "tacint": []}
                groups[cid]["imint"].append(record)
        
        for record in tacint:
            cid = record.get("correlation_id")
            if cid:
                if cid not in groups:
                    groups[cid] = {"elint": [], "imint": [], "tacint": []}
                groups[cid]["tacint"].append(record)
        
        return groups
    
    def _create_compact_prompt(self, correlation_groups: Dict) -> str:
        """Compact fusion prompt"""
        
        # Summarize each group compactly
        group_summaries = []
        for corr_id, sources in correlation_groups.items():
            summary = {
                "correlation_id": corr_id,
                "sources": len([s for s in [sources["elint"], sources["imint"], sources["tacint"]] if s]),
                "elint_count": len(sources["elint"]),
                "imint_count": len(sources["imint"]),
                "tacint_count": len(sources["tacint"])
            }
            
            # Extract key details from first record of each source
            if sources["elint"]:
                e = sources["elint"][0]
                summary["elint_time"] = e.get("from_time", "")
                summary["elint_desc"] = e.get("description", "")[:100]
            
            if sources["imint"]:
                i = sources["imint"][0]
                summary["imint_time"] = i.get("time", "")
                summary["imint_str"] = i.get("str", "")
                summary["imint_desc"] = i.get("description", "")[:100]
            
            if sources["tacint"]:
                t = sources["tacint"][0]
                summary["tacint_time"] = t.get("time", "")
                summary["tacint_str"] = t.get("str", "")
                summary["tacint_grading"] = t.get("grading", "")
                summary["tacint_desc"] = t.get("description", "")[:100]
            
            group_summaries.append(summary)
        
        prompt = f"""Correlation groups to fuse:
{json.dumps(group_summaries, indent=1)}

Generate Enemy Activity records (one per correlation group). Include:
- sensor_type: "MULTI-SOURCE-FUSION"
- sensor_id: "FUSION-CELL-14-CORPS"
- tgt_type, tgt_sub_type, tgt_cl
- activity_type, activity_sub_type, activity_cl
- bearing: (0-360 degrees, e.g., "275")
- range_km: (detection range, e.g., "8.5")
- strength: (synthesized from sources)
- long: (76.1-76.5)
- lat: (34.4-34.7)
- ht: (3000-5000)
- e: (383000-385000)
- n: (3815000-3820000)
- zone: "43S"
- input_method: "Multi-source intelligence fusion"
- description: (cite all sources with times, highlight agreements, provide assessment, 4-5 sentences)
- upload_time: "YYYY-MM-DD HH:MM" format (e.g., "1999-06-15 09:30")
- correlation_id
- confidence_level: CONFIRMED/HIGH CONFIDENCE/PROBABLE/POSSIBLE

IMPORTANT: upload_time MUST be in format "YYYY-MM-DD HH:MM" for proper date filtering!

Return JSON: {{"enemy_activity_records": [...]}}
"""
        
        return prompt