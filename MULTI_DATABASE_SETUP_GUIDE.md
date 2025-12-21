# SAMA Multi-Database Setup Guide

## Overview

This guide explains how to set up **5 separate PostgreSQL databases** on Azure, each containing one type of intelligence data from the Kargil War 1999 scenario.

## Database Architecture

### 5 Intelligence Databases

| Database Name | Table | Description | Data Type |
|---------------|-------|-------------|-----------|
| `elint_intelligence_db` | `elint` | Electronic Intelligence Database | SIGINT/Communications Intercepts |
| `imint_intelligence_db` | `imint_data` | Imagery Intelligence Database | Satellite/Aerial Imagery Analysis |
| `tacint_intelligence_db` | `tac_int` | Tactical Intelligence Database | Ground-based Tactical Reports |
| `enemy_activity_db` | `en_activity` | Enemy Activity Database | Fused Intelligence Reports |
| `sitrep_intelligence_db` | `e_sitrep_mst` | Situation Report Database | Operational Situation Reports |

## Quick Setup

### 1. Prerequisites

Ensure you have the required SQL data files in `data/output/`:
```
elint_kargil_war_1999_inserts.sql
imint_data_kargil_war_1999_inserts.sql
tac_int_kargil_war_1999_inserts.sql
en_activity_kargil_war_1999_inserts.sql
e_sitrep_mst_kargil_war_1999_inserts.sql
```

### 2. Environment Setup

Your `.env` file should contain:
```bash
DB_HOST=insights-db.postgres.database.azure.com
DB_PORT=5432
DB_USER=turintonadmin
DB_PASSWORD=Passw0rd123!
OUTPUT_DIR=data/output
```

### 3. Create All Databases

**Quick Run:**
```bash
python run_multi_database_creation.py
```

**Direct Execution:**
```bash
python create_multi_databases.py
```

### 4. Verify Setup

```bash
# Check database status
python manage_intelligence_databases.py --status

# Show sample data
python manage_intelligence_databases.py --sample
```

## Scripts Description

### `create_multi_databases.py`
Main script that creates 5 separate databases and imports respective data.

**Features:**
- Automatic database creation on Azure PostgreSQL
- Table schema extraction from SQL files  
- Batch data import with error handling
- Comprehensive logging and progress tracking

### `manage_intelligence_databases.py` 
Database management and monitoring utilities.

**Features:**
- Database status monitoring
- Record count and size reporting
- Sample data viewing
- Database cleanup operations

### `run_multi_database_creation.py`
Simple runner script for easy execution.

## Database Schema

Each database contains one table with fields relevant to its intelligence type:

### Common Fields (All Tables)
- `observation_date` - Date of intelligence collection
- `observation_time` - Time of collection  
- `longitude`, `latitude` - Geographic coordinates
- `location_name` - Named location
- `description` - Detailed intelligence report

### ELINT Specific Fields
- `frequency` - Signal frequency
- `emitter_type` - Type of electronic emitter
- `enemy_unit` - Intercepted unit identification

### IMINT Specific Fields
- `image_type` - Type of imagery
- `weather_conditions` - Visibility conditions
- `target_identification` - Objects identified

## Usage Examples

### Check Database Status
```bash
python manage_intelligence_databases.py --status
```

### View Sample Data
```bash
# All databases
python manage_intelligence_databases.py --sample

# Specific database
python manage_intelligence_databases.py --sample-db elint_intelligence_db
```

### Connect to Individual Database
```python
import psycopg2

conn = psycopg2.connect(
    host="insights-db.postgres.database.azure.com",
    port=5432,
    dbname="elint_intelligence_db",  # or other database name
    user="turintonadmin", 
    password="Passw0rd123!"
)

cursor = conn.cursor()
cursor.execute("SELECT * FROM elint WHERE observation_date = '1999-05-08'")
data = cursor.fetchall()
```

## Expected Data Volume

Based on Kargil War 1999 scenario (92 days, 6 observations per day):

| Database | Records | Focus |
|----------|---------|-------|
| ELINT | ~274 | Radio/Communications intercepts |
| IMINT | ~276 | Satellite/aerial imagery analysis |  
| TACINT | ~276 | Ground reconnaissance reports |
| Enemy Activity | ~276 | Fused intelligence assessments |
| SITREP | ~276 | Operational situation reports |

**Total**: ~1,378 intelligence records across all databases

## Benefits of Multi-Database Architecture

1. **Data Isolation**: Each intelligence type is completely separated
2. **Security**: Independent access control per database
3. **Performance**: Optimized queries per intelligence domain
4. **Scalability**: Individual databases can be scaled independently
5. **Maintenance**: Specialized backup and maintenance strategies

## Troubleshooting

### Common Issues

1. **Connection Errors**: Check Azure PostgreSQL firewall settings
2. **Authentication Failures**: Verify `.env` credentials  
3. **Missing SQL Files**: Run `python main.py` first to generate data
4. **Permission Errors**: Ensure user has CREATE DATABASE privileges

### Database Cleanup
```bash
python manage_intelligence_databases.py --drop-all
```
⚠️ **Warning**: This permanently deletes all databases!

## Integration

Each database can be used independently:
- **ELINT Service** → `elint_intelligence_db`
- **IMINT Service** → `imint_intelligence_db`  
- **TACINT Service** → `tacint_intelligence_db`
- **Activity Analysis** → `enemy_activity_db`
- **Reporting Service** → `sitrep_intelligence_db`

Perfect for microservices architecture with specialized intelligence processing services.