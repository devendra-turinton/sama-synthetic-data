# Multi-Database Intelligence System

This directory contains scripts to create and manage 5 separate PostgreSQL databases for different intelligence data types on Azure PostgreSQL.

## Overview

Instead of storing all intelligence data in a single database, this system creates specialized databases for each intelligence discipline:

| Database | Intelligence Type | Primary Table | Description |
|----------|------------------|---------------|-------------|
| `elint_intelligence_db` | 🔵 ELINT | `elint` | Electronic Intelligence - Radio/Radar emissions |
| `imint_intelligence_db` | 🟢 IMINT | `imint_data` | Imagery Intelligence - Satellite/aerial imagery |
| `tacint_intelligence_db` | 🟡 TACINT | `tac_int` | Tactical Intelligence - Ground observations |
| `enemy_activity_db` | 🔴 FUSION | `en_activity` | Fused Intelligence - Multi-source analysis |
| `sitrep_intelligence_db` | 🟣 SITREP | `e_sitrep_mst` | Situation Reports - Command assessments |

## Quick Start

### 1. Create All Databases

Run the simplified launcher:

```bash
python create_intelligence_databases.py
```

This will:
- Show configuration summary
- Ask for confirmation
- Create all 5 databases
- Create schemas and indexes
- Load reference data
- Load intelligence data

### 2. Check Database Status

Use the database manager:

```bash
python database_manager.py
```

Select option 1 to check status of all databases.

## Detailed Scripts

### `multi_database_dumper.py`
Main script that creates all databases, schemas, and loads data.

**Features:**
- Creates separate databases on Azure PostgreSQL
- Sets up complete schemas with foreign keys
- Loads reference classification data
- Imports intelligence data from JSON files
- Creates optimized indexes
- Comprehensive error handling and logging

**Usage:**
```python
from multi_database_dumper import MultiDatabaseDumper
dumper = MultiDatabaseDumper()
success_count, failures = dumper.create_all_databases()
```

### `database_manager.py`
Interactive management tool for all intelligence databases.

**Features:**
- Database status checking
- Cross-database statistics
- Connection testing
- Database cleanup (deletion)
- Export database information to JSON

**Usage:**
```bash
python database_manager.py
```

### `multi_db_config.py`
Configuration file containing all database definitions, schemas, and metadata.

**Features:**
- Centralized database configurations
- Complete SQL schemas for all tables
- Intelligence type descriptions and characteristics
- Helper functions for database operations

## Database Architecture

### Each Database Contains:

1. **Reference Tables** (identical in all databases):
   - `activity_type`, `activity_sub_type`, `activity_classification`
   - `target_type`, `target_sub_type`, `target_classification`
   - `esitrep_type`, `esitrep_sub_type`, `esitrep_classification`

2. **Primary Intelligence Table** (unique per database):
   - Specific schema optimized for each intelligence type
   - Foreign key relationships to reference tables
   - Specialized indexes for common query patterns

3. **Indexes**:
   - Geographic indexes (longitude, latitude)
   - Temporal indexes (dates, times)
   - Formation hierarchy indexes
   - Composite indexes for common queries

### Schema Highlights

#### ELINT Database (`elint`)
- Focus on electronic emissions
- Fields: frequency, emitter_type, enemy_unit
- Specialized for signal intelligence

#### IMINT Database (`imint_data`)
- Focus on imagery analysis
- Fields: source_agency (CARTOSAT, RISAT), grading
- Foreign keys to all classification tables

#### TACINT Database (`tac_int`)
- Focus on ground observations
- Fields: source_agency (BSF, patrols), grading
- Real-time tactical reporting

#### Enemy Activity Database (`en_activity`)
- Focus on fused intelligence
- Fields: sensor_type, bearing, range_km
- Multi-source correlation

#### SITREP Database (`e_sitrep_mst`)
- Focus on situation reports
- Fields: incident_status, str_own, str_en
- Command-level assessments

## Connection Examples

### Connect to Specific Database

```python
import psycopg2
from multi_db_config import get_database_config

# Connect to ELINT database
config = get_database_config('elint')
conn = psycopg2.connect(**config)

# Query ELINT data
cursor = conn.cursor()
cursor.execute("SELECT * FROM elint WHERE frequency LIKE '%.5%' LIMIT 10")
results = cursor.fetchall()
```

### Cross-Database Analysis

```python
from multi_db_config import get_all_database_configs

configs = get_all_database_configs()

# Connect to multiple databases for correlation analysis
elint_conn = psycopg2.connect(**configs['elint'])
imint_conn = psycopg2.connect(**configs['imint'])
tacint_conn = psycopg2.connect(**configs['tacint'])

# Perform cross-source queries...
```

## Data Files Required

The system expects these JSON data files in the `data/output/` directory:

- `elint_data_kargil_war_1999.json`
- `imint_data_kargil_war_1999.json`
- `tacint_data_kargil_war_1999.json`
- `enemy_activity_data_kargil_war_1999.json`
- `sitrep_data_kargil_war_1999.json`
- `reference_data_complete.json`

Generate these files first by running the main data generator:

```bash
python main.py
```

## Environment Configuration

Ensure your `.env` file has the correct Azure PostgreSQL settings:

```env
DB_HOST=insights-db.postgres.database.azure.com
DB_NAME=integrated_intel_sources  # Note: This is overridden per database
DB_USER=turintonadmin
DB_PASSWORD=your_password
DB_PORT=5432
```

## Security Considerations

- Each database can have separate access controls
- Intelligence disciplines can be compartmentalized
- Different security classifications per database
- Audit trails per intelligence type
- Backup strategies per database importance

## Performance Benefits

- **Specialized Indexes**: Each database has indexes optimized for its query patterns
- **Reduced Table Size**: Smaller tables improve query performance
- **Parallel Operations**: Multiple databases can be queried simultaneously
- **Isolation**: Heavy queries on one intelligence type don't affect others
- **Scalability**: Individual databases can be scaled independently

## Maintenance

### Check All Database Sizes

```bash
python database_manager.py
# Select option 1 (Check Database Status)
```

### Export Database Information

```bash
python database_manager.py
# Select option 4 (Export Database Info)
```

### Clean Up Databases (DANGER!)

```bash
python database_manager.py
# Select option 5 (Cleanup Databases)
# Type 'DELETE' to confirm
```

## Troubleshooting

### Common Issues

1. **Connection Errors**: Check `.env` file and Azure PostgreSQL firewall
2. **Schema Errors**: Ensure reference data is loaded first
3. **Data Loading Errors**: Check JSON file format and required fields
4. **Permission Errors**: Verify database user has CREATE DATABASE privileges

### Logs

All operations create detailed logs. Check the console output and any generated log files for specific error messages.

### Database Status

Use the database manager to check which databases are accessible and their current state:

```bash
python database_manager.py
```

This will show:
- Database online/offline status
- Record counts per database
- Database sizes
- Latest record timestamps

## Future Enhancements

- **Replication**: Set up read replicas for analytics
- **Partitioning**: Implement time-based partitioning for large datasets
- **Federation**: Create federated queries across all databases
- **Monitoring**: Add automated monitoring and alerting
- **Backup**: Implement automated backup strategies per database