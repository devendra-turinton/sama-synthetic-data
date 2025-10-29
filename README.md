# SAMA - Synthetic Army Military Analytics

Complete intelligence data generation system for the 1999 Kargil War, producing realistic, correlated military intelligence across multiple sources.

## Features

- **92-day Complete Timeline**: Full Kargil War period (May 8 - August 7, 1999)
- **Correlated Intelligence**: ELINT, IMINT, and TACINT with shared correlation IDs
- **Intelligence Fusion**: Multi-source fusion with confidence levels
- **Situation Reporting**: Incident-based e_sitrep records
- **Data Validation**: Comprehensive validation and error checking
- **SQL Export**: Ready-to-import database inserts

## System Architecture
```
Ground Truth Events (552 events, 6/day)
           ↓
    Correlation Manager (assigns correlation IDs)
           ↓
    ┌──────────┼──────────┐
    ↓          ↓          ↓
  ELINT      IMINT     TACINT
 (radio)   (satellite) (ground)
 -10 min    +25 min    +35 min
    └──────────┼──────────┘
           ↓
    Intelligence Fusion
   (Enemy Activity Records)
           ↓
    Situation Reports
      (e_sitrep)
```

## Installation

1. **Clone Repository**
```bash
git clone <repository-url>
cd sama_project
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your API key and database credentials
```

4. **Create Database** (optional, for SQL import)
```bash
psql -U postgres
CREATE DATABASE sama_db;
\c sama_db
\i schema.sql
```

## Usage

### Generate Complete Dataset
```bash
python main.py
```

This will:
1. Generate reference data (classification hierarchies)
2. Create 92-day timeline with 552 ground truth events
3. Assign correlation IDs to all events
4. Generate ELINT data (~552 records)
5. Generate IMINT data (~552 records)
6. Generate TACINT data (~552 records)
7. Fuse intelligence into Enemy Activity records
8. Generate situation reports (e_sitrep)
9. Validate all data
10. Export to JSON and SQL files

### Expected Output

**Total Records**: ~2,760 intelligence records

- Ground Truth Events: 552
- ELINT Records: ~552
- IMINT Records: ~552
- TACINT Records: ~552
- Enemy Activity (Fused): ~552
- SITREP Records: ~300

**Generation Time**: 2-4 hours (depending on API speed)

## Output Files

All files saved to `data/output/`:

**JSON Files:**
- `scenario_kargil_war_1999.json` - Complete timeline
- `correlation_registry.json` - Correlation mapping
- `elint_data_kargil_war_1999.json` - ELINT records
- `imint_data_kargil_war_1999.json` - IMINT records
- `tacint_data_kargil_war_1999.json` - TACINT records
- `enemy_activity_data_kargil_war_1999.json` - Fused records
- `sitrep_data_kargil_war_1999.json` - Situation reports

**SQL Files:**
- `elint_kargil_war_1999_inserts.sql`
- `imint_data_kargil_war_1999_inserts.sql`
- `tac_int_kargil_war_1999_inserts.sql`
- `en_activity_kargil_war_1999_inserts.sql`
- `e_sitrep_mst_kargil_war_1999_inserts.sql`

## Data Correlation

All intelligence sources observe the **same ground truth events** with realistic timing offsets:

**Example Event**: Pakistani tank movement at 08:00

- **ELINT** detects at 07:50 (-10 min) - radio communications before movement
- **IMINT** observes at 08:25 (+25 min) - satellite pass
- **TACINT** reports at 08:35 (+35 min) - ground observer sees and reports

All three records share **correlation_id: "CORR_0042"**

**Fusion** combines at 09:00:
```
"CONFIRMED Pakistani armored movement. Corroborated by 
ELINT (07:50), IMINT (08:25), TACINT (08:35). All sources 
confirm Al-Khalid MBT. Assessment: Tactical deployment."
```

## Database Import
```bash
# Import reference data first
psql -U postgres -d sama_db -f data/output/reference_inserts.sql

# Import operational data
psql -U postgres -d sama_db -f data/output/elint_kargil_war_1999_inserts.sql
psql -U postgres -d sama_db -f data/output/imint_data_kargil_war_1999_inserts.sql
psql -U postgres -d sama_db -f data/output/tac_int_kargil_war_1999_inserts.sql
psql -U postgres -d sama_db -f data/output/en_activity_kargil_war_1999_inserts.sql
psql -U postgres -d sama_db -f data/output/e_sitrep_mst_kargil_war_1999_inserts.sql
```

## Configuration

Edit `config.py`:
```python
# Switch between production and test mode
PRODUCTION_MODE = True  # False for single-day test

# Adjust model settings
MODEL_CONFIG = {
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 4000,
    "temperature": 0.3,
}
```

## Data Validation

The system performs comprehensive validation:

✅ **Correlation Consistency**: All records have valid correlation IDs
✅ **Formation Codes**: 10-character codes with proper hierarchy
✅ **Geographic Bounds**: Coordinates within Kargil sector
✅ **Temporal Consistency**: Dates within war period
✅ **Required Fields**: All mandatory fields present

## Troubleshooting

**API Rate Limits**:
- System includes exponential backoff
- Generation will automatically retry
- Average: ~0.5 requests/second

**Validation Errors**:
- Review errors in log file
- Check correlation_registry.json for missing IDs
- Verify formation codes in config.py

**Memory Issues**:
- Process runs in batches
- Peak memory: ~2GB
- Reduce batch_size in generators if needed

## Project Structure
```
sama_project/
├── config.py                   # Configuration
├── main.py                     # Main orchestrator
├── schema.sql                  # Database schema
├── requirements.txt            # Dependencies
├── .env                        # Environment variables
├── utils/
│   ├── anthropic_client.py    # LLM client
│   ├── correlation_manager.py # Correlation tracking
│   ├── database.py            # Database operations
│   └── validation.py          # Data validation
├── generators/
│   ├── reference_data_generator.py
│   ├── scenario_generator.py
│   ├── elint_generator.py
│   ├── imint_generator.py
│   ├── tacint_generator.py
│   ├── enemy_activity_generator.py
│   └── sitrep_generator.py
└── data/
    └── output/                # Generated files
```

## License

[Your License Here]

## Contact

[Your Contact Information]