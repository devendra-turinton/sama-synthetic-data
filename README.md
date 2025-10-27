# Kargil War Data Generation - Complete Implementation Guide

## Overview
Complete end-to-end implementation for generating realistic, correlated synthetic intelligence data for the Kargil War (May-July 1999).

---

## Changes Summary

### 1. **Configuration (`config.py`)**
**Changes:**
- Added `KARGIL_SCENARIO` with complete historical timeline
- Defined 5 phases: pre-infiltration, discovery, major operations, conclusion, post-war
- Added geographic positions for key locations (Tiger Hill, Tololing, Point 5140, etc.)
- Added `INDIAN_FORMATIONS` structure with realistic Kargil-era units
- Added `DAILY_TIME_SLOTS` for 6 observations per day
- Upgraded model to `claude-sonnet-4` for better quality

**Key Features:**
- 92-day timeline (May 1 - July 31, 1999)
- 6 time slots per day (every 4 hours)
- Historical accuracy with key events mapped
- Formation hierarchy structure for fmn_code generation

---

### 2. **New Utility: Formation Code Generator (`utils/formation_code_generator.py`)**
**Purpose:** Generate unique 10-character alphanumeric formation codes

**Key Methods:**
- `generate_unit_hierarchy()` - Create 3 battalions per brigade
- `generate_support_unit()` - Create BSF, intelligence units
- `decode_formation_code()` - Parse 10-char codes
- `initialize_default_units()` - Setup Kargil-specific units

**Formation Code Format:**
```
[CMD(2)][CORPS(2)][DIV(2)][BDE(2)][UNIT(2)]
Example: NC140870A1
  NC = Northern Command
  14 = XIV Corps
  08 = 8 Mountain Division
  70 = 70 Infantry Brigade
  A1 = Battalion A1
```

---

### 3. **New Utility: Event Correlation Engine (`utils/event_correlation_engine.py`)**
**Purpose:** Correlate ground truth events across multiple intelligence sources

**Key Features:**
- Time offset simulation (ELINT -15min, IMINT ±30min, TACINT +10-45min)
- Location variance (±50m to ±500m depending on source)
- Strength estimation variance
- Source-specific observation limitations
- Confidence level calculation

**Correlation Flow:**
```
Ground Truth Event
  ├─> ELINT Observation (electronic signature, -15min)
  ├─> IMINT Observation (satellite imagery, ±30min)
  └─> TACINT Observation (ground report, +10-45min)
```

---

### 4. **Updated: Scenario Generator (`generators/scenario_generator.py`)**
**Changed to:** `KargilScenarioGenerator`

**Key Changes:**
- Generates 92-day timeline instead of variable duration
- Creates exactly 6 events per day (one per 4-hour slot)
- Uses historical Kargil phases and key events
- Events tagged with `observable_by: ["ELINT", "IMINT", "TACINT"]`
- Related events tell coherent daily story

**Output:**
- Complete historical timeline JSON
- ~550 ground truth events (92 days × 6 events)

---

### 5. **Updated: ELINT Generator (`generators/elint_generator.py`)**
**Key Changes:**
- Accepts correlation packages instead of raw events
- Applies ELINT-specific time offsets
- Generates technical electronic signatures only
- NO visual details (can't see tanks/troops)
- Uses realistic Pakistani equipment (TRC-20H, AN/TPS-43)

**Critical Rules:**
- Detect 5-15 minutes BEFORE physical activity
- Technical language: "VHF burst transmission", "encrypted tactical net"
- Infer strength from communication volume
- Location accuracy: ±500m (triangulation)

---

### 6. **Updated: IMINT Generator (`generators/imint_generator.py`)**
**Key Changes:**
- Accepts correlation packages
- Applies satellite pass timing variations
- Includes weather/cloud cover constraints
- Overhead perspective only
- Confidence qualifiers (CONFIRMED/PROBABLE/POSSIBLE)

**Critical Rules:**
- Describe only overhead view
- Vehicle count ranges (10-12, not exact 11)
- Weather constraints affect image quality
- GPS-quality coordinates (±50m)
- Cannot detect electronic signals

---

### 7. **Updated: TACINT Generator (`generators/tacint_generator.py`)**
**Key Changes:**
- Accepts correlation packages
- Ground-level observer perspective
- Reporting delay 10-45 minutes
- Includes sensory details (sights, sounds)
- Grading system (A1-A5, 1-5)

**Critical Rules:**
- Write in narrative style (soldier's report)
- Include observation distance and method
- Human limitations (line of sight, weather)
- Count ranges with uncertainty qualifiers
- Distance affects detail level

---

### 8. **Updated: Enemy Activity Generator (`generators/enemy_activity_generator.py`)**
**Key Changes:**
- FUSION layer - correlates all three sources
- Groups by correlation_id
- Resolves conflicts between sources
- Produces high-confidence assessments
- Explicitly cites sources

**Description Format:**
```
"CONFIRMED Pakistani armored company movement. 
Corroborated by ELINT (TRC-20H communications 08:15), 
IMINT (satellite imagery 08:35 confirming 10-12 Al-Khalid MBTs), 
and TACINT (BSF OP Delta-7 visual confirmation 08:50).
All sources agree on equipment type. Assessment: ..."
```

**Confidence Levels:**
- CONFIRMED: All 3 sources agree
- HIGH CONFIDENCE: 2 sources with strong evidence
- PROBABLE: 2 sources with uncertainty
- POSSIBLE: Only 1 source

---

### 9. **Updated: SITREP Generator (`generators/sitrep_generator.py`)**
**Key Changes:**
- One SITREP per day (evening report at 18:00)
- Strategic-level assessment from Division/Corps HQ
- Includes both enemy AND friendly forces
- Commander's assessment and recommendations
- Numbered sequentially (SITREP #001, #002, etc.)

**SITREP Structure:**
1. Enemy Situation summary
2. Intelligence Assessment (enemy intent)
3. Friendly Forces posture
4. Commander's Assessment
5. Recommendations

**Critical Rule:** NO mention of specific intelligence sources in narrative

---

### 10. **Updated: Main Pipeline (`main.py`)**
**Execution Flow:**
```
Step 1: Generate Reference Data (taxonomies)
Step 2: Generate Kargil Timeline (92 days, 6 events/day)
Step 3: Generate ELINT (with correlation)
Step 4: Generate IMINT (with correlation)
Step 5: Generate TACINT (with correlation)
Step 6: Generate Enemy Activity (fusion)
Step 7: Generate SITREP (strategic assessment)
Step 8: Export all to SQL
```

**Logging:** Comprehensive progress tracking with summary report

---

### 11. **Updated: Database Schema (`schema.sql`)**
**Key Improvements:**
- Proper foreign key constraints on reference tables
- UNIQUE constraints prevent duplicates
- CASCADE deletes maintain referential integrity
- Comprehensive indexes for performance
- Standardized column naming
- BIGINT for 10-char formation codes

---

### 12. **Updated: Database Manager (`utils/database.py`)**
**New Features:**
- Field name mapping for database compatibility
- Handles correlation_id (metadata, not stored)
- Data validation method
- Special character escaping
- Truncation of long descriptions

---

## Data Flow Architecture

```
┌─────────────────────┐
│  Kargil Scenario    │
│  Timeline Generator │
│  (Ground Truth)     │
└──────────┬──────────┘
           │ 552 events with observable_by tags
           ↓
┌──────────────────────────────────────┐
│   Event Correlation Engine           │
│   Creates correlation packages       │
└──────────┬───────────────────────────┘
           │
     ┌─────┴─────┬─────────┐
     ↓           ↓         ↓
┌─────────┐ ┌─────────┐ ┌─────────┐
│ ELINT   │ │ IMINT   │ │ TACINT  │
│ -15 min │ │ ±30 min │ │ +15 min │
└────┬────┘ └────┬────┘ └────┬────┘
     │           │            │
     └───────────┴────────────┘
                 │
                 ↓
         ┌──────────────┐
         │ Enemy        │
         │ Activity     │
         │ (Fusion)     │
         └──────┬───────┘
                │
                ↓
         ┌──────────────┐
         │ SITREP       │
         │ (Strategic)  │
         └──────────────┘
```

---

## Expected Output

### Records per Table (approximate):
- **ELINT**: ~400 records (not all events have electronic signatures)
- **IMINT**: ~450 records (satellite passes depend on weather)
- **TACINT**: ~500 records (most events observable from ground)
- **Enemy Activity**: ~350 records (fusion of correlated observations)
- **SITREP**: ~92 records (one per day)
- **Total**: ~1,800 intelligence records

### File Structure:
```
data/output/
├── scenario_kargil_war_1999.json
├── reference_data_complete.json
├── elint_data_kargil_war_1999.json
├── imint_data_kargil_war_1999.json
├── tacint_data_kargil_war_1999.json
├── enemy_activity_data_kargil_war_1999.json
├── sitrep_data_kargil_war_1999.json
├── elint_kargil_war_1999_inserts.sql
├── imint_data_kargil_war_1999_inserts.sql
├── tac_int_kargil_war_1999_inserts.sql
├── en_activity_kargil_war_1999_inserts.sql
├── e_sitrep_mst_kargil_war_1999_inserts.sql
└── generation.log
```

---

## Correlation Example

### Ground Truth Event (June 15, 1999, 08:20)
```json
{
  "time": "08:20",
  "event_type": "movement",
  "actor": "Pakistani XII Corps - 12 Armoured Regiment",
  "location": [75.7530, 34.4248],
  "equipment_involved": ["Al-Khalid MBT"],
  "strength": "12 tanks",
  "description": "Armored company movement toward Point 5140"
}
```

### Correlated Observations

**ELINT (08:05 - 15 minutes before):**
```json
{
  "time": "08:05",
  "emitter_type": "COMMUNICATIONS",
  "frequency": "345.2 MHz",
  "description": "Encrypted VHF burst transmissions detected. Signal pattern consistent with TRC-20H tactical radio. Battalion-level command communications. Direction finding indicates Drass sector.",
  "correlation_id": "CORR_0156"
}
```

**IMINT (08:35 - during event):**
```json
{
  "time": "08:35",
  "description": "PROBABLE convoy of 10-12 armored vehicles moving northeast. Vehicle spacing consistent with tactical deployment. Cloud cover 20%. Image quality sufficient for probable Al-Khalid tank identification.",
  "str": "10-12 vehicles",
  "correlation_id": "CORR_0156"
}
```

**TACINT (08:55 - 35 minutes after):**
```json
{
  "time": "08:55",
  "description": "Column of 11-13 tracked armored vehicles observed at 08:40 hours from BSF OP Delta-7 at range 2.8km. Visual identification confirms Al-Khalid MBTs based on turret profile. Heavy engine noise audible. Tactical formation with 50m spacing.",
  "str": "11-13 vehicles",
  "grading": "A2",
  "correlation_id": "CORR_0156"
}
```

**Enemy Activity (09:15 - after fusion):**
```json
{
  "time": "09:15",
  "description": "CONFIRMED Pakistani armored company (12 Al-Khalid MBTs) tactical movement toward Point 5140. Corroborated by ELINT detection at 08:05 (tactical communications), IMINT satellite pass at 08:35 (imagery confirms 10-12 tanks), and TACINT ground observation at 08:55 from BSF OP Delta-7 (visual confirmation of 11-13 tanks). All sources independently confirm equipment type and tactical formation. Assessment: Deliberate operational deployment. Threat level: HIGH.",
  "strength": "Company-strength (12 Al-Khalid MBTs)",
  "confidence_level": "CONFIRMED",
  "correlation_id": "CORR_0156"
}
```

**SITREP (18:00 - evening report):**
```json
{
  "time": "18:00",
  "description": "SITREP #045: Pakistani forces conducted coordinated operations in Drass sector during period 0800-1700 hours. Primary activity consisted of armored company redeployment from reserve to forward positions vicinity Point 5140, accompanied by increased tactical communications and supporting infantry movements.\n\nINTELLIGENCE ASSESSMENT: Activity pattern indicates deliberate operational preparation. Armor concentration provides rapid escalation capability. Assessment based on multi-source intelligence with high confidence.\n\nFRIENDLY FORCES: 28 Mountain Brigade reinforced forward positions. Artillery at readiness. Air support on standby.\n\nCOMMANDER'S ASSESSMENT: Current posturing assessed as probe of defensive posture. Immediate assault not imminent but force disposition enables rapid action. Sustained heightened alert warranted.\n\nRECOMMENDATIONS: Maintain alert status. Continue intensive surveillance. Brief air assets for potential CAS missions."
}
```

---

## Key Differences from Previous Implementation

| Aspect | Old Implementation | New Implementation |
|--------|-------------------|-------------------|
| **Scenario** | Generic 5 scenarios | Single Kargil War scenario (historical) |
| **Timeline** | Variable days | Fixed 92 days (May 1 - July 31, 1999) |
| **Event Frequency** | Unspecified | Exactly 6 events per day (every 4 hours) |
| **Correlation** | None - independent generation | Full correlation with correlation_id tracking |
| **Source Descriptions** | Generic | Source-specific (ELINT=technical, IMINT=overhead, TACINT=narrative) |
| **Time Offsets** | Not implemented | Realistic offsets (ELINT early, TACINT late) |
| **Formation Codes** | Random integers | Structured 10-char codes (hierarchical) |
| **Enemy Activity** | Independent records | Fusion of correlated sources with citations |
| **SITREP** | Combined observations | Strategic assessment, no source mentions |
| **Data Volume** | Unclear | ~1,800 total records across 5 tables |

---

## Installation & Usage

### 1. Setup Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install anthropic python-dotenv psycopg2-binary

# Create .env file
cat > .env << EOF
ANTHROPIC_API_KEY=your_api_key_here
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sama_db
DB_USER=postgres
DB_PASSWORD=your_password
EOF
```

### 2. Create Database Schema
```bash
# Connect to PostgreSQL
psql -U postgres -d sama_db -f schema.sql
```

### 3. Generate Data
```bash
# Generate complete Kargil War dataset
python main.py

# This will take approximately 2-3 hours depending on API rate limits
# Progress is logged to both console and data/output/generation.log
```

### 4. Verify Output
```bash
# Check generated files
ls -lh data/output/

# Expected files:
# - scenario_kargil_war_1999.json (~500KB)
# - elint_data_kargil_war_1999.json (~2MB)
# - imint_data_kargil_war_1999.json (~3MB)
# - tacint_data_kargil_war_1999.json (~3MB)
# - enemy_activity_data_kargil_war_1999.json (~2MB)
# - sitrep_data_kargil_war_1999.json (~1MB)
# - 5 SQL insert files (~5-10MB total)
```

### 5. Load into Database
```bash
# Execute SQL inserts
psql -U postgres -d sama_db -f data/output/elint_kargil_war_1999_inserts.sql
psql -U postgres -d sama_db -f data/output/imint_data_kargil_war_1999_inserts.sql
psql -U postgres -d sama_db -f data/output/tac_int_kargil_war_1999_inserts.sql
psql -U postgres -d sama_db -f data/output/en_activity_kargil_war_1999_inserts.sql
psql -U postgres -d sama_db -f data/output/e_sitrep_mst_kargil_war_1999_inserts.sql
```

---

## Validation & Quality Checks

### 1. Correlation Consistency
```python
# Check that correlated observations exist
python -c "
import json
with open('data/output/elint_data_kargil_war_1999.json') as f:
    elint = json.load(f)
with open('data/output/enemy_activity_data_kargil_war_1999.json') as f:
    enemy = json.load(f)

elint_corrs = {r['correlation_id'] for r in elint if 'correlation_id' in r}
enemy_corrs = {r['correlation_id'] for r in enemy if 'correlation_id' in r}

print(f'ELINT correlations: {len(elint_corrs)}')
print(f'Enemy Activity correlations: {len(enemy_corrs)}')
print(f'Orphaned: {len(enemy_corrs - elint_corrs)}')
"
```

### 2. Formation Code Validation
```sql
-- Check formation code uniqueness
SELECT fmn_code, COUNT(*) 
FROM en_activity 
GROUP BY fmn_code 
HAVING COUNT(*) > 1;

-- Should return empty result

-- Check formation code format (10 characters)
SELECT COUNT(*) 
FROM en_activity 
WHERE LENGTH(fmn_code::TEXT) != 10;

-- Should return 0
```

### 3. Temporal Consistency
```sql
-- Check for records outside expected date range
SELECT COUNT(*) 
FROM elint 
WHERE observation_date NOT BETWEEN '1999-05-01' AND '1999-07-31';

-- Should return 0
```

### 4. Geographic Consistency
```sql
-- Check that correlated observations are within 1km of each other
SELECT 
    e.correlation_id,
    e.longitude AS elint_long,
    i.longitude AS imint_long,
    ABS(e.longitude - i.longitude) AS long_diff
FROM elint e
JOIN imint_data i ON e.correlation_id = i.correlation_id
WHERE ABS(e.longitude - i.longitude) > 0.01;  -- ~1km

-- Should return few or no results
```

---

## Troubleshooting

### Issue: API Rate Limits
**Symptom:** Errors about rate limiting from Anthropic API  
**Solution:** 
```python
# Add retry logic in anthropic_client.py
import time
from anthropic import RateLimitError

def generate_with_retry(self, prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            return self.generate_structured_data(prompt)
        except RateLimitError:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 60
                logger.warning(f"Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
```

### Issue: JSON Parsing Errors
**Symptom:** `JSONDecodeError` in logs  
**Solution:**
- Check `generation.log` for the actual response
- Claude sometimes adds markdown formatting
- The client already strips ```json blocks, but may need adjustment

### Issue: Missing Correlation IDs
**Symptom:** Enemy Activity records missing correlation_id  
**Solution:**
- Verify that Claude includes correlation_id in generated JSON
- Check prompts explicitly request correlation_id field
- May need to add post-processing to extract from descriptions

### Issue: Unrealistic Data
**Symptom:** Sources describe events identically  
**Solution:**
- Review correlation engine parameters
- Increase variance in time offsets and locations
- Enhance source-specific prompt instructions

---

## Future Enhancements

1. **Multi-Scenario Support**: Extend to other historical conflicts
2. **Real-time Generation**: Stream data generation for live simulations
3. **Interactive Validation**: Web UI for reviewing and correcting generated data
4. **Advanced Correlation**: Machine learning for more sophisticated correlation patterns
5. **Multi-language Support**: Generate intelligence in Hindi, Urdu for realism
6. **Media Attachments**: Generate synthetic satellite images, audio recordings
7. **Network Analysis**: Add inter-unit communication patterns
8. **Predictive Analytics**: Use generated data to train ML models for pattern detection

---

## Credits & References

- **Historical Sources**: Kargil War official reports, Operation Vijay documentation
- **Military Equipment**: Jane's Defence publications, SIPRI databases
- **Geographic Data**: Indian Survey maps, Google Earth coordinates
- **Formation Structure**: Indian Army organization manuals

---

## License & Usage

This synthetic data generation system is designed for:
- ✅ Training and development of military intelligence systems
- ✅ Testing AI/ML models for intelligence analysis
- ✅ Educational purposes and research
- ❌ NOT for operational military use
- ❌ NOT a substitute for real intelligence data

All generated data is SYNTHETIC and should be treated as training data only.

---

## Summary Checklist

- [x] Updated config.py with Kargil scenario
- [x] Created FormationCodeGenerator utility
- [x] Created EventCorrelationEngine utility
- [x] Updated ScenarioGenerator → KargilScenarioGenerator
- [x] Updated ElintGenerator with correlation
- [x] Updated ImintGenerator with correlation
- [x] Updated TacintGenerator with correlation
- [x] Updated EnemyActivityGenerator with fusion
- [x] Updated SitrepGenerator with strategic assessment
- [x] Updated main.py pipeline
- [x] Updated database schema
- [x] Updated database.py with field mappings
- [x] Created comprehensive documentation

**Status:** ✅ Ready for implementation