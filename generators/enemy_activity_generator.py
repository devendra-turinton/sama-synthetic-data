import os
import json
import logging
from typing import Dict, List, Any

from utils.anthropic_client import AnthropicClient
from utils.correlation_manager import CorrelationManager
from config import (OUTPUT_DIR, OBSERVING_UNITS, FORMATION_MAPPING,
                   ANTHROPIC_API_KEY, MODEL_CONFIG)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnemyActivityGenerator:
    """Generate Enemy Activity by fusing ELINT, IMINT, and TACINT sources"""
    
    SYSTEM_PROMPT = """You are an Intelligence Fusion Analyst correlating multiple sources.

FUSION RULES:
1. CONFIDENCE LEVELS:
   - CONFIRMED: All 3 sources agree
   - HIGH CONFIDENCE: 2 sources with strong evidence
   - PROBABLE: 2 sources with some uncertainty
   - POSSIBLE: Only 1 source

2. RESOLVING CONFLICTS:
   - Strength: Average across sources (IMINT most accurate for counts)
   - Equipment ID: TACINT/IMINT trump ELINT (visual beats electronic inference)
   - Timing: Use earliest detection time (usually ELINT)
   - Location: Use IMINT coordinates (most accurate GPS)

3. DESCRIPTION MUST:
   - Start with confidence level
   - Cite ALL sources with specific times
   - Highlight agreements AND discrepancies
   - Provide intelligence assessment
   - Use format: "CONFIRMED activity. Corroborated by ELINT (time), IMINT (time), TACINT (time). All sources agree on..."

4. ALWAYS provide realistic values for all fields (no zeros)

EXAMPLE:
"CONFIRMED Pakistani armored company movement toward Point 5140. Activity detected by ELINT at 07:50 (encrypted TRC-20H tactical communications indicating battalion-level coordination), corroborated by IMINT satellite pass at 08:35 (imagery confirms 10-12 Al-Khalid main battle tanks in tactical column formation), and verified by TACINT ground observation at 08:55 from BSF OP Delta-7 (visual identification of 11-13 tanks at 2.8km range). All three sources independently confirm equipment type as Al-Khalid MBT with consistent location coordinates. Assessment: Deliberate tactical deployment, high probability of staging for assault operations."

FORMAT: JSON with "enemy_activity_records" array.
IMPORTANT: Generate one fused record per correlation group."""
    
    def __init__(self, correlation_manager: CorrelationManager):
        self.client = AnthropicClient(
            api_key=ANTHROPIC_API_KEY,
            model=MODEL_CONFIG["model"],
            max_tokens=MODEL_CONFIG["max_tokens"],
            temperature=MODEL_CONFIG["temperature"]
        )
        self.correlation_manager = correlation_manager
        self.unit_fmn_codes = OBSERVING_UNITS["FUSION"]
    
    def generate_enemy_activity_data(self,
                                     scenario: Dict[str, Any],
                                     elint_data: List[Dict[str, Any]],
                                     imint_data: List[Dict[str, Any]],
                                     tacint_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate fused Enemy Activity records"""
        
        logger.info("="*80)
        logger.info("GENERATING ENEMY ACTIVITY (INTELLIGENCE FUSION)")
        logger.info("="*80)
        
        # Group all intelligence by correlation_id
        correlation_groups = self._group_by_correlation(elint_data, imint_data, tacint_data)
        
        logger.info(f"Found {len(correlation_groups)} correlation groups for fusion")
        
        if not correlation_groups:
            logger.warning("No correlation groups found! Check that correlation_ids are present in source data.")
            return []
        
        all_enemy_activity_records = []
        record_id = 1
        
        # Process in batches to manage token limits
        batch_size = 10
        correlation_ids = list(correlation_groups.keys())
        
        for batch_start in range(0, len(correlation_ids), batch_size):
            batch_ids = correlation_ids[batch_start:batch_start + batch_size]
            batch_groups = {cid: correlation_groups[cid] for cid in batch_ids}
            
            logger.info(f"Processing fusion batch: {len(batch_groups)} correlation groups")
            
            prompt = self._create_fusion_prompt(batch_groups)
            
            try:
                response = self.client.generate_structured_data(
                    prompt,
                    system_prompt=self.SYSTEM_PROMPT
                )
                records = response.get("enemy_activity_records", [])
                
                # Validate and enhance records
                for record in records:
                    # Validate correlation_id exists
                    if not record.get("correlation_id"):
                        logger.error("Fused record missing correlation_id!")
                        continue
                    
                    # Add metadata
                    record["id"] = record_id
                    record_id += 1
                    
                    # Add fusion cell unit info
                    fmn_code = self.unit_fmn_codes[0]
                    unit_info = FORMATION_MAPPING[fmn_code].copy()
                    unit_info["fmn_code"] = fmn_code
                    record.update(unit_info)
                    
                    all_enemy_activity_records.append(record)
                
                logger.info(f"  ✓ Fused {len(records)} Enemy Activity records")
                
            except Exception as e:
                logger.error(f"Error in fusion batch: {e}", exc_info=True)
                continue
        
        # Save output
        output_path = os.path.join(OUTPUT_DIR, f"enemy_activity_data_{scenario['scenario_name']}.json")
        with open(output_path, 'w') as f:
            json.dump(all_enemy_activity_records, f, indent=2)
        
        logger.info(f"✓ Enemy Activity fusion complete: {len(all_enemy_activity_records)} records")
        logger.info(f"✓ Saved to: {output_path}")
        
        return all_enemy_activity_records
    
    def _group_by_correlation(self, elint: List[Dict], imint: List[Dict], 
                             tacint: List[Dict]) -> Dict[str, Dict]:
        """Group intelligence records by correlation_id"""
        
        groups = {}
        
        # Group ELINT
        for record in elint:
            cid = record.get("correlation_id")
            if cid:
                if cid not in groups:
                    groups[cid] = {"elint": [], "imint": [], "tacint": []}
                groups[cid]["elint"].append(record)
        
        # Group IMINT
        for record in imint:
            cid = record.get("correlation_id")
            if cid:
                if cid not in groups:
                    groups[cid] = {"elint": [], "imint": [], "tacint": []}
                groups[cid]["imint"].append(record)
        
        # Group TACINT
        for record in tacint:
            cid = record.get("correlation_id")
            if cid:
                if cid not in groups:
                    groups[cid] = {"elint": [], "imint": [], "tacint": []}
                groups[cid]["tacint"].append(record)
        
        # Log fusion statistics
        full_coverage = 0
        partial_coverage = 0
        
        for cid, sources in groups.items():
            source_count = sum(1 for s in [sources["elint"], sources["imint"], sources["tacint"]] if s)
            if source_count == 3:
                full_coverage += 1
            elif source_count >= 2:
                partial_coverage += 1
        
        logger.info(f"  Full coverage (3 sources): {full_coverage}")
        logger.info(f"  Partial coverage (2 sources): {partial_coverage}")
        logger.info(f"  Single source: {len(groups) - full_coverage - partial_coverage}")
        
        return groups
    
    def _create_fusion_prompt(self, correlation_groups: Dict[str, Dict]) -> str:
        """Create fusion prompt with source summaries"""
        
        # Summarize each correlation group compactly
        group_summaries = []
        
        for corr_id, sources in correlation_groups.items():
            summary = {
                "correlation_id": corr_id,
                "source_count": sum(1 for s in [sources["elint"], sources["imint"], sources["tacint"]] if s),
                "sources_present": []
            }
            
            # ELINT summary
            if sources["elint"]:
                e = sources["elint"][0]
                summary["sources_present"].append("ELINT")
                summary["elint"] = {
                    "time": e.get("from_time", ""),
                    "emitter": e.get("emitter_type", ""),
                    "description_excerpt": e.get("description", "")[:150]
                }
            
            # IMINT summary
            if sources["imint"]:
                i = sources["imint"][0]
                summary["sources_present"].append("IMINT")
                summary["imint"] = {
                    "time": i.get("time", ""),
                    "strength": i.get("str", ""),
                    "target": i.get("tgt_cl", ""),
                    "description_excerpt": i.get("description", "")[:150]
                }
            
            # TACINT summary
            if sources["tacint"]:
                t = sources["tacint"][0]
                summary["sources_present"].append("TACINT")
                summary["tacint"] = {
                    "time": t.get("time", ""),
                    "strength": t.get("str", ""),
                    "grading": t.get("grading", ""),
                    "source": t.get("source_agency", ""),
                    "description_excerpt": t.get("description", "")[:150]
                }
            
            group_summaries.append(summary)
        
        prompt = f"""Fuse intelligence from multiple sources for {len(group_summaries)} correlation groups:

{json.dumps(group_summaries, indent=1)}

For EACH correlation group, generate ONE Enemy Activity record that synthesizes all sources.

Each record must include:
- correlation_id: (from correlation group)
- sensor_type: "MULTI-SOURCE-FUSION"
- sensor_id: "FUSION-CELL-14-CORPS"
- tgt_type, tgt_sub_type, tgt_cl: (synthesized from sources)
- activity_type, activity_sub_type, activity_cl: (synthesized from sources)
- bearing: (0-360 degrees, e.g., "275")
- range_km: (detection range, e.g., "8.5")
- strength: (synthesized from all sources, e.g., "Company-strength (12 Al-Khalid MBTs)")
- long: (use IMINT coordinates if available, 76.0-76.6)
- lat: (use IMINT coordinates if available, 34.4-34.7)
- ht: (3000-5000)
- e: (383000-385000)
- n: (3815000-3820000)
- zone: "43S"
- input_method: "Multi-source intelligence fusion"
- description: (CRITICAL - MUST cite ALL sources with times, highlight agreements, assess significance, 4-6 sentences)
- upload_time: "YYYY-MM-DD HH:MM" format (e.g., "1999-06-15 09:30")
- confidence_level: "CONFIRMED"/"HIGH CONFIDENCE"/"PROBABLE"/"POSSIBLE"
- sources_corroborated: (comma-separated list, e.g., "ELINT, IMINT, TACINT")

DESCRIPTION FORMAT EXAMPLE:
"CONFIRMED Pakistani armored company movement. Corroborated by ELINT at 07:50 (encrypted tactical communications), IMINT at 08:35 (satellite imagery confirming 10-12 Al-Khalid tanks), and TACINT at 08:55 (BSF visual confirmation of 11-13 tanks). All sources agree on equipment type and tactical formation. Movement pattern indicates deliberate operational deployment. ASSESSMENT: High probability of staging for assault operations against Indian positions."

CRITICAL: 
1. Description MUST cite ALL available sources with their detection times
2. Highlight where sources AGREE (equipment, activity type)
3. Note any DISCREPANCIES (different counts, timing variations)
4. Provide tactical ASSESSMENT of significance
5. upload_time format: "YYYY-MM-DD HH:MM"

Return JSON: {{"enemy_activity_records": [... {len(group_summaries)} records ...]}}"""
        
        return prompt