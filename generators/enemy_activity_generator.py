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
    
    SYSTEM_PROMPT = """You are an Intelligence Fusion Analyst correlating multiple intelligence sources.

FUSION RULES:
1. CONFIDENCE LEVELS:
   - CONFIRMED: All 3 sources agree on key details
   - HIGH CONFIDENCE: 2 sources with strong corroborating evidence
   - PROBABLE: 2 sources with some uncertainty or discrepancies
   - POSSIBLE: Only 1 source or conflicting evidence

2. RESOLVING CONFLICTS:
   - Strength/Count: Average across sources, IMINT most accurate for vehicle counts
   - Equipment ID: TACINT/IMINT visual identification trumps ELINT electronic inference
   - Timing: Use earliest detection time (usually ELINT 10-15 min before others)
   - Location: Use IMINT GPS coordinates (most accurate ±50m) over TACINT (±500m) or ELINT (±500m+)
   - Activity assessment: Synthesize all perspectives (electronic prep, visual confirmation, ground observation)

3. DESCRIPTION STRUCTURE (4-6 sentences, 150-200 words):
   Sentence 1: Confidence level and activity summary
   Sentence 2-3: Source citations with detection times and key observations
   Sentence 4: Agreement/discrepancy analysis across sources
   Sentence 5: Synthesized tactical picture
   Sentence 6: Intelligence assessment and significance

4. SOURCE CITATION FORMAT:
   - "Activity detected by ELINT at [time] ([specific observation]), corroborated by IMINT satellite pass at [time] ([specific observation]), and verified by TACINT ground observation at [time] ([specific observation])."
   - Always cite ALL available sources with their specific detection times
   - Highlight where sources AGREE: "All three sources independently confirm [detail]"
   - Note DISCREPANCIES: "ELINT suggests [X], while IMINT indicates [Y]"

5. TACTICAL SYNTHESIS:
   - Combine electronic preparation (ELINT), overhead view (IMINT), and ground perspective (TACINT)
   - Resolve count discrepancies: "IMINT imagery counts 10-12 vehicles, TACINT ground observation reports 11-13, assess as company-strength armored element of approximately 11-12 tanks"
   - Equipment identification: "TACINT visual identification confirms Al-Khalid MBT, corroborated by IMINT overhead signature"
   - Intent assessment: Use ELINT communications patterns + IMINT positioning + TACINT movement to infer tactical purpose

6. ALWAYS provide realistic values for all fields (no zeros, no nulls)

EXAMPLE FULL FUSION:
"CONFIRMED Pakistani armored company tactical deployment toward Point 5140. Activity detected by ELINT at 07:50 hours (encrypted TRC-20H tactical communications on frequency 47.250 MHz indicating battalion-level coordination, signal strength suggesting 12.5km range), corroborated by IMINT CARTOSAT-3 satellite pass at 08:35 hours (overhead imagery confirms 10-12 Al-Khalid main battle tanks in tactical column formation with 50-meter spacing), and verified by TACINT ground observation from BSF OP Delta-7 at 08:55 hours (visual identification of 11-13 tanks at 2.8km range using spotting scope, diesel engine sounds audible). All three sources independently confirm equipment type as Al-Khalid MBT with consistent location coordinates at Tololing Summit area (grid 384251 3817136). Minor count discrepancy (IMINT: 10-12, TACINT: 11-13) assessed as same unit with assess strength of company-sized element, approximately 11-12 vehicles. Tactical disposition indicates deliberate staging for assault operations: ELINT communications patterns show increased pre-movement coordination 10-15 minutes before physical displacement, IMINT overhead positioning confirms tactical formation oriented toward Indian positions, TACINT reports coordinated movement with professional spacing and mine plow attachment on lead vehicle. Assessment: High probability of imminent assault operations against Indian forward positions, threat level immediate, recommend artillery counter-battery preparation and forward unit alert status."

FORMAT: JSON with "enemy_activity_records" array.
IMPORTANT: Generate one fused record per correlation group, citing ALL available sources."""
    
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
            
            prompt = self._create_enhanced_fusion_prompt(batch_groups)
            
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
                    
                    # Validate description length
                    desc = record.get("description", "")
                    if len(desc) < 150:
                        logger.warning(f"Fusion description too short: {len(desc)} chars")
                    
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
        single_source = 0
        
        for cid, sources in groups.items():
            source_count = sum(1 for s in [sources["elint"], sources["imint"], sources["tacint"]] if s)
            if source_count == 3:
                full_coverage += 1
            elif source_count == 2:
                partial_coverage += 1
            else:
                single_source += 1
        
        logger.info(f"  Full coverage (3 sources): {full_coverage}")
        logger.info(f"  Partial coverage (2 sources): {partial_coverage}")
        logger.info(f"  Single source: {single_source}")
        
        return groups
    
    def _create_enhanced_fusion_prompt(self, correlation_groups: Dict[str, Dict]) -> str:
        """Create enhanced fusion prompt with detailed source information"""
        
        # Create detailed summaries for each correlation group
        group_summaries = []
        
        for corr_id, sources in correlation_groups.items():
            summary = {
                "correlation_id": corr_id,
                "source_count": sum(1 for s in [sources["elint"], sources["imint"], sources["tacint"]] if s),
                "sources_present": []
            }
            
            # ELINT summary (more detail)
            if sources["elint"]:
                e = sources["elint"][0]
                summary["sources_present"].append("ELINT")
                summary["elint"] = {
                    "detection_time": e.get("from_time", ""),
                    "emitter_type": e.get("emitter_type", ""),
                    "emitter_name": e.get("emitter_name", ""),
                    "frequency": e.get("frequency", ""),
                    "location": e.get("location", ""),
                    "range_km": e.get("range", ""),
                    "description_excerpt": e.get("description", "")[:200]
                }
            
            # IMINT summary (more detail)
            if sources["imint"]:
                i = sources["imint"][0]
                summary["sources_present"].append("IMINT")
                summary["imint"] = {
                    "observation_time": i.get("time", ""),
                    "satellite": i.get("source_agency", ""),
                    "target_type": i.get("tgt_cl", ""),
                    "activity": i.get("activity_cl", ""),
                    "strength": i.get("str", ""),
                    "grading": i.get("grading", ""),
                    "coordinates": {"lat": i.get("lat"), "long": i.get("long")},
                    "description_excerpt": i.get("description", "")[:200]
                }
            
            # TACINT summary (more detail)
            if sources["tacint"]:
                t = sources["tacint"][0]
                summary["sources_present"].append("TACINT")
                summary["tacint"] = {
                    "reporting_time": t.get("time", ""),
                    "source_post": t.get("source_agency", ""),
                    "target_type": t.get("tgt_cl", ""),
                    "activity": t.get("activity_cl", ""),
                    "strength": t.get("str", ""),
                    "grading": t.get("grading", ""),
                    "observation_method": t.get("input", ""),
                    "description_excerpt": t.get("description", "")[:200]
                }
            
            group_summaries.append(summary)
        
        prompt = f"""Fuse intelligence from multiple sources for {len(group_summaries)} correlation groups:

CORRELATION GROUPS WITH SOURCE DETAILS:
{json.dumps(group_summaries, indent=1)}

For EACH correlation group, generate ONE Enemy Activity record that comprehensively synthesizes ALL available sources.

Each fused record must include:

REQUIRED FIELDS:
- correlation_id: (from correlation group above)
- sensor_type: "MULTI-SOURCE-FUSION"
- sensor_id: "FUSION-CELL-14-CORPS"
- tgt_type: (synthesized from sources, e.g., "VEHICLE")
- tgt_sub_type: (synthesized, e.g., "ARMORED")
- tgt_cl: (synthesized, e.g., "MAIN_BATTLE_TANK")
- activity_type: (synthesized, e.g., "MOVEMENT")
- activity_sub_type: (synthesized, e.g., "VEHICULAR")
- activity_cl: (synthesized, e.g., "TACTICAL_DEPLOYMENT")
- bearing: (0-360 degrees, e.g., "275")
- range_km: (average from sources, e.g., "8.5")
- strength: (synthesized assessment, e.g., "Company-strength armored element, approximately 11-12 Al-Khalid MBTs")
- long: (use IMINT coordinates if available, else TACINT, else ELINT; range 76.0-76.6)
- lat: (use IMINT coordinates if available, else TACINT, else ELINT; range 34.4-34.7)
- ht: (use IMINT or TACINT height, 3000-5000)
- e: (easting in meters, 383000-385000)
- n: (northing in meters, 3815000-3820000)
- zone: "43S"
- input_method: "Multi-source intelligence fusion (ELINT/IMINT/TACINT)"
- description: (150-200 words, MUST cite ALL sources, see structure below)
- upload_time: "YYYY-MM-DD HH:MM" format (latest source time + 30-60 min for analysis)
- confidence_level: "CONFIRMED" | "HIGH CONFIDENCE" | "PROBABLE" | "POSSIBLE"
- sources_corroborated: (comma-separated, e.g., "ELINT, IMINT, TACINT")

DESCRIPTION STRUCTURE (150-200 words, 4-6 sentences):

Sentence 1: Confidence level + Activity summary
  Example: "CONFIRMED Pakistani armored company tactical deployment toward Point 5140 in Tololing Summit area."

Sentence 2-3: Source citations with specific times and key observations
  Example: "Activity detected by ELINT at 07:50 hours (encrypted TRC-20H tactical communications on frequency 47.250 MHz indicating battalion-level coordination, signal strength -78 dBm suggests 12.5km transmitter range), corroborated by IMINT CARTOSAT-3 satellite pass at 08:35 hours (0.25m resolution overhead imagery confirms 10-12 Al-Khalid main battle tanks in tactical column formation with 50-meter spacing, oriented northeast), and verified by TACINT ground observation from BSF Observation Post Delta-7 at 08:55 hours (visual identification of 11-13 tanks at 2.8km range using Carl Zeiss 20x60 spotting scope, diesel engine sounds audible, mine plow attachment visible on lead vehicle)."

Sentence 4: Agreement/Discrepancy analysis
  Example: "All three sources independently confirm equipment type as Al-Khalid MBT with consistent location coordinates (IMINT GPS: 76.1158°E 34.5447°N, TACINT visual: same grid reference 384251 3817136). Minor count discrepancy between IMINT (10-12 vehicles) and TACINT (11-13 vehicles) assessed as observation variance of same unit, consolidated strength assessment of company-sized armored element with approximately 11-12 main battle tanks."

Sentence 5: Synthesized tactical picture
  Example: "Tactical disposition indicates deliberate staging for assault operations: ELINT communications analysis shows increased pre-movement coordination patterns 10-15 minutes before physical displacement characteristic of Pakistani Army tactical procedures, IMINT overhead positioning confirms vehicles in attack formation oriented toward Indian forward positions, TACINT ground observation reports coordinated professional movement with standard tactical spacing and visible command/control between vehicle commanders using hand signals."

Sentence 6: Intelligence assessment and significance
  Example: "Assessment: High probability of imminent assault operations against Indian forward defensive positions at Tololing. Threat level assessed as immediate. Unit demonstrates professional military capabilities with secure communications (ELINT), proper tactical formations (IMINT), and coordinated maneuver discipline (TACINT). Recommend: Artillery counter-battery preparation, forward unit alert status upgrade, and reinforcement of defensive positions in threatened sector."

CRITICAL FUSION REQUIREMENTS:
1. MUST cite ALL available sources with their specific detection times
2. Resolve count discrepancies by averaging and explaining variance
3. Equipment ID: Use visual confirmation (TACINT/IMINT) over electronic inference (ELINT)
4. Location: Prioritize IMINT GPS coordinates (±50m) over TACINT (±500m) or ELINT (±500m+)
5. Timing: Note earliest detection (usually ELINT) and progression through sources
6. Highlight where sources AGREE on key facts (equipment, location, activity type)
7. Explain any DISCREPANCIES and provide reconciled assessment
8. Synthesize different perspectives: electronic prep (ELINT) + overhead view (IMINT) + ground observation (TACINT)
9. Provide tactical assessment combining all source insights
10. Confidence level based on source agreement: 3 sources agreeing = CONFIRMED, 2 sources = HIGH CONFIDENCE/PROBABLE, 1 source = POSSIBLE
11. upload_time format: "YYYY-MM-DD HH:MM"
12. Description must be 150-200 words

EXAMPLE RECORD (use as template):
{{
  "correlation_id": "CORR_0042",
  "sensor_type": "MULTI-SOURCE-FUSION",
  "sensor_id": "FUSION-CELL-14-CORPS",
  "tgt_type": "VEHICLE",
  "tgt_sub_type": "ARMORED",
  "tgt_cl": "MAIN_BATTLE_TANK",
  "activity_type": "MOVEMENT",
  "activity_sub_type": "VEHICULAR",
  "activity_cl": "TACTICAL_DEPLOYMENT",
  "bearing": "275",
  "range_km": "8.5",
  "strength": "Company-strength armored element, approximately 11-12 Al-Khalid MBTs with supporting logistics",
  "long": 76.1158,
  "lat": 34.5447,
  "ht": 4590,
  "e": 384251,
  "n": 3817136,
  "zone": "43S",
  "input_method": "Multi-source intelligence fusion (ELINT/IMINT/TACINT)",
  "description": "CONFIRMED Pakistani armored company tactical deployment toward Point 5140 in Tololing Summit area. Activity detected by ELINT at 07:50 hours (encrypted TRC-20H tactical communications on frequency 47.250 MHz indicating battalion-level coordination, signal strength -78 dBm suggests 12.5km transmitter range), corroborated by IMINT CARTOSAT-3 satellite pass at 08:35 hours (0.25m resolution overhead imagery confirms 10-12 Al-Khalid main battle tanks in tactical column formation with 50-meter spacing, oriented northeast), and verified by TACINT ground observation from BSF Observation Post Delta-7 at 08:55 hours (visual identification of 11-13 tanks at 2.8km range using Carl Zeiss 20x60 spotting scope, diesel engine sounds audible, mine plow attachment visible on lead vehicle). All three sources independently confirm equipment type as Al-Khalid MBT with consistent location coordinates (IMINT GPS: 76.1158°E 34.5447°N, TACINT visual: same grid 384251 3817136). Minor count discrepancy between IMINT (10-12 vehicles) and TACINT (11-13 vehicles) assessed as observation variance of same unit, consolidated strength assessment of company-sized element with approximately 11-12 main battle tanks. Tactical disposition indicates deliberate staging for assault operations: ELINT communications patterns show increased pre-movement coordination 10-15 minutes before physical displacement, IMINT overhead positioning confirms attack formation oriented toward Indian positions, TACINT reports coordinated movement with professional spacing. Assessment: High probability of imminent assault operations, threat level immediate, recommend artillery counter-battery preparation and forward unit alert.",
  "upload_time": "1999-06-15 09:30",
  "confidence_level": "CONFIRMED",
  "sources_corroborated": "ELINT, IMINT, TACINT"
}}

Return JSON: {{"enemy_activity_records": [... {len(group_summaries)} fused records ...]}}

Generate the {len(group_summaries)} comprehensive fusion records now:"""
        
        return prompt