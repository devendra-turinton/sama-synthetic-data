#!/usr/bin/env python3
"""
Database Configuration for Multi-Database Setup
Centralizes configuration for all intelligence databases
"""

from typing import Dict, List
import os
from config import DB_CONFIG

# Enhanced Database Configurations for 5 Intelligence Types
INTELLIGENCE_DATABASES = {
    "elint": {
        "db_name": "elint_intelligence_db",
        "description": "Electronic Intelligence Database", 
        "primary_table": "elint",
        "data_file": "elint_data_kargil_war_1999.json",
        "color_emoji": "🔵",  # Blue circle
        "intelligence_type": "ELINT",
        "source_description": "Electronic Intelligence - Radio/Radar Emissions",
        "typical_sensors": ["Radio Intercept", "Radar Warning Receivers", "SIGINT Equipment"],
        "data_characteristics": {
            "temporal_resolution": "Real-time to minutes",
            "spatial_accuracy": "Kilometer level",
            "typical_volume": "High frequency, continuous collection",
            "classification": "CONFIDENTIAL to SECRET"
        }
    },
    
    "imint": {
        "db_name": "imint_intelligence_db", 
        "description": "Imagery Intelligence Database",
        "primary_table": "imint_data", 
        "data_file": "imint_data_kargil_war_1999.json",
        "color_emoji": "🟢",  # Green circle
        "intelligence_type": "IMINT",
        "source_description": "Imagery Intelligence - Satellite/Aerial Imagery",
        "typical_sensors": ["CARTOSAT", "RISAT", "Commercial Satellites", "UAV Cameras"],
        "data_characteristics": {
            "temporal_resolution": "Hours to days (revisit time)",
            "spatial_accuracy": "Meter to sub-meter level",
            "typical_volume": "Medium frequency, weather dependent", 
            "classification": "CONFIDENTIAL to SECRET"
        }
    },
    
    "tacint": {
        "db_name": "tacint_intelligence_db",
        "description": "Tactical Intelligence Database", 
        "primary_table": "tac_int",
        "data_file": "tacint_data_kargil_war_1999.json",
        "color_emoji": "🟡",  # Yellow circle
        "intelligence_type": "TACINT", 
        "source_description": "Tactical Intelligence - Ground Observations",
        "typical_sensors": ["Ground Observers", "Patrol Reports", "Forward Posts", "BSF Units"],
        "data_characteristics": {
            "temporal_resolution": "Real-time to hours",
            "spatial_accuracy": "Meter level (direct observation)",
            "typical_volume": "Variable, mission dependent",
            "classification": "CONFIDENTIAL to SECRET"
        }
    },
    
    "enemy_activity": {
        "db_name": "enemy_activity_db",
        "description": "Enemy Activity Analysis Database",
        "primary_table": "en_activity", 
        "data_file": "enemy_activity_data_kargil_war_1999.json",
        "color_emoji": "🔴",  # Red circle
        "intelligence_type": "FUSION",
        "source_description": "Fused Intelligence - Multi-source Analysis", 
        "typical_sensors": ["All Source Fusion", "Intelligence Analysis", "Pattern Recognition"],
        "data_characteristics": {
            "temporal_resolution": "Analysis dependent (minutes to hours)",
            "spatial_accuracy": "Best available from contributing sources",
            "typical_volume": "Lower frequency, high confidence",
            "classification": "SECRET to TOP SECRET"
        }
    },
    
    "sitrep": {
        "db_name": "sitrep_intelligence_db",
        "description": "Situation Reports Database",
        "primary_table": "e_sitrep_mst",
        "data_file": "sitrep_data_kargil_war_1999.json", 
        "color_emoji": "🟣",  # Purple circle
        "intelligence_type": "SITREP",
        "source_description": "Situation Reports - Command Assessment",
        "typical_sensors": ["Command Posts", "Intelligence Staff", "Operations Centers"],
        "data_characteristics": {
            "temporal_resolution": "Periodic (scheduled reporting)",
            "spatial_accuracy": "Area level (operational significance)",
            "typical_volume": "Regular intervals (daily/periodic)",
            "classification": "CONFIDENTIAL to SECRET"
        }
    }
}

# Database Connection Templates
def get_database_config(db_type: str, base_config: Dict = None) -> Dict[str, str]:
    """Get database connection config for specific intelligence type"""
    if base_config is None:
        base_config = DB_CONFIG
    
    if db_type not in INTELLIGENCE_DATABASES:
        raise ValueError(f"Unknown database type: {db_type}")
    
    db_config = base_config.copy()
    db_config['database'] = INTELLIGENCE_DATABASES[db_type]['db_name']
    
    return db_config

def get_all_database_configs(base_config: Dict = None) -> Dict[str, Dict[str, str]]:
    """Get all database connection configs"""
    if base_config is None:
        base_config = DB_CONFIG
    
    configs = {}
    for db_type in INTELLIGENCE_DATABASES.keys():
        configs[db_type] = get_database_config(db_type, base_config)
    
    return configs

# SQL Schema Templates
COMMON_REFERENCE_SCHEMA = """
-- =============================================================================
-- REFERENCE DATA TABLES (Common to All Intelligence Databases)
-- =============================================================================

-- Activity Classification Hierarchy
CREATE TABLE IF NOT EXISTS activity_type (
    id INTEGER PRIMARY KEY,
    activity_type VARCHAR(255) NOT NULL UNIQUE,
    img_path VARCHAR(255),
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100),
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activity_sub_type (
    id INTEGER PRIMARY KEY,
    activity_type_id INTEGER NOT NULL REFERENCES activity_type(id) ON DELETE CASCADE,
    activity_sub_type VARCHAR(255) NOT NULL,
    img_path VARCHAR(255),
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100),
    updated_at TIMESTAMP,
    UNIQUE(activity_type_id, activity_sub_type)
);

CREATE TABLE IF NOT EXISTS activity_classification (
    id INTEGER PRIMARY KEY,
    activity_type_id INTEGER NOT NULL REFERENCES activity_type(id) ON DELETE CASCADE,
    activity_sub_type_id INTEGER NOT NULL REFERENCES activity_sub_type(id) ON DELETE CASCADE,
    activity_classification VARCHAR(255) NOT NULL,
    img_path VARCHAR(255),
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100),
    updated_at TIMESTAMP,
    UNIQUE(activity_sub_type_id, activity_classification)
);

-- Target Classification Hierarchy  
CREATE TABLE IF NOT EXISTS target_type (
    id INTEGER PRIMARY KEY,
    target_type VARCHAR(255) NOT NULL UNIQUE,
    img_path VARCHAR(255),
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100),
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS target_sub_type (
    id INTEGER PRIMARY KEY,
    target_type_id INTEGER NOT NULL REFERENCES target_type(id) ON DELETE CASCADE,
    target_sub_type VARCHAR(255) NOT NULL,
    img_path VARCHAR(255),
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100),
    updated_at TIMESTAMP,
    UNIQUE(target_type_id, target_sub_type)
);

CREATE TABLE IF NOT EXISTS target_classification (
    id INTEGER PRIMARY KEY,
    target_type_id INTEGER NOT NULL REFERENCES target_type(id) ON DELETE CASCADE,
    target_sub_type_id INTEGER NOT NULL REFERENCES target_sub_type(id) ON DELETE CASCADE,
    target_classification VARCHAR(255) NOT NULL,
    img_path VARCHAR(255),
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100),
    updated_at TIMESTAMP,
    UNIQUE(target_sub_type_id, target_classification)
);

-- Incident Classification Hierarchy
CREATE TABLE IF NOT EXISTS esitrep_type (
    id INTEGER PRIMARY KEY,
    incident_type VARCHAR(255) NOT NULL UNIQUE,
    img_path VARCHAR(255),
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100),
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS esitrep_sub_type (
    id INTEGER PRIMARY KEY,
    incident_type_id INTEGER NOT NULL REFERENCES esitrep_type(id) ON DELETE CASCADE,
    incident_sub_type VARCHAR(255) NOT NULL,
    img_path VARCHAR(255),
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100),
    updated_at TIMESTAMP,
    UNIQUE(incident_type_id, incident_sub_type)
);

CREATE TABLE IF NOT EXISTS esitrep_classification (
    id INTEGER PRIMARY KEY,
    incident_type_id INTEGER NOT NULL REFERENCES esitrep_type(id) ON DELETE CASCADE,
    incident_sub_type_id INTEGER NOT NULL REFERENCES esitrep_sub_type(id) ON DELETE CASCADE,
    incident_classification VARCHAR(255) NOT NULL,
    img_path VARCHAR(255),
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100),
    updated_at TIMESTAMP,
    UNIQUE(incident_sub_type_id, incident_classification)
);

-- Indexes for Reference Tables
CREATE INDEX IF NOT EXISTS idx_activity_sub_type_type ON activity_sub_type(activity_type_id);
CREATE INDEX IF NOT EXISTS idx_activity_classification_subtype ON activity_classification(activity_sub_type_id);
CREATE INDEX IF NOT EXISTS idx_target_sub_type_type ON target_sub_type(target_type_id);
CREATE INDEX IF NOT EXISTS idx_target_classification_subtype ON target_classification(target_sub_type_id);
CREATE INDEX IF NOT EXISTS idx_esitrep_sub_type_type ON esitrep_sub_type(incident_type_id);
CREATE INDEX IF NOT EXISTS idx_esitrep_classification_subtype ON esitrep_classification(incident_sub_type_id);
"""

# Specific Table Schemas
TABLE_SCHEMAS = {
    "elint": """
-- Electronic Intelligence Table
CREATE TABLE IF NOT EXISTS elint (
    id SERIAL PRIMARY KEY,
    observation_date DATE,
    from_time TIME,
    to_time TIME,
    enemy_unit VARCHAR(255),  -- Enemy corps/formation detected
    location_name VARCHAR(255), -- Human readable location name
    range_km VARCHAR(100),     -- Range to target
    emitter_type VARCHAR(255), -- Type of electronic emitter
    emitter_name VARCHAR(255), -- Specific emitter designation
    frequency VARCHAR(100),    -- Frequency observed
    longitude DOUBLE PRECISION,
    latitude DOUBLE PRECISION,
    height DOUBLE PRECISION,
    easting DOUBLE PRECISION,
    northing DOUBLE PRECISION,
    zone VARCHAR(50),
    description TEXT,
    -- Formation hierarchy (observing unit)
    fmn_code BIGINT,           -- 10-digit formation code
    cmd_name VARCHAR(255),     -- Command name
    corps_name VARCHAR(255),   -- Corps name
    div_name VARCHAR(255),     -- Division name
    bde_name VARCHAR(255),     -- Brigade name
    unit_name VARCHAR(255),    -- Unit name
    hierarchy_level VARCHAR(100), -- Level in hierarchy
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ELINT-specific indexes
CREATE INDEX IF NOT EXISTS idx_elint_location ON elint(longitude, latitude);
CREATE INDEX IF NOT EXISTS idx_elint_date ON elint(observation_date);
CREATE INDEX IF NOT EXISTS idx_elint_frequency ON elint(frequency);
CREATE INDEX IF NOT EXISTS idx_elint_emitter_type ON elint(emitter_type);
CREATE INDEX IF NOT EXISTS idx_elint_fmn_code ON elint(fmn_code);
CREATE INDEX IF NOT EXISTS idx_elint_enemy_unit ON elint(enemy_unit);
""",

    "imint_data": """
-- Imagery Intelligence Table  
CREATE TABLE IF NOT EXISTS imint_data (
    id SERIAL PRIMARY KEY,
    observation_date DATE,
    observation_time TIME,
    precedence VARCHAR(50),    -- Message precedence (FLASH, IMMEDIATE, etc.)
    -- Foreign key references to classification tables
    tgt_type_id INTEGER REFERENCES target_type(id),
    tgt_sub_type_id INTEGER REFERENCES target_sub_type(id),
    tgt_cl_id INTEGER REFERENCES target_classification(id),
    activity_type_id INTEGER REFERENCES activity_type(id),
    activity_sub_type_id INTEGER REFERENCES activity_sub_type(id),
    activity_cl_id INTEGER REFERENCES activity_classification(id),
    incident_type_id INTEGER REFERENCES esitrep_type(id),
    incident_sub_type_id INTEGER REFERENCES esitrep_sub_type(id),
    incident_cl_id INTEGER REFERENCES esitrep_classification(id),
    -- Source and assessment information
    source_agency VARCHAR(255), -- CARTOSAT, RISAT, Commercial, etc.
    grading VARCHAR(50),       -- Reliability grading (A1, B2, C3, etc.)
    strength VARCHAR(255),     -- Force strength assessment
    -- Geographic information
    longitude DOUBLE PRECISION,
    latitude DOUBLE PRECISION,
    height DOUBLE PRECISION,
    easting DOUBLE PRECISION,
    northing DOUBLE PRECISION,
    zone VARCHAR(50),
    input_method VARCHAR(255), -- How imagery was collected
    description TEXT,
    -- Formation hierarchy (reporting unit)
    fmn_code BIGINT,
    cmd_name VARCHAR(255),
    corps_name VARCHAR(255),
    div_name VARCHAR(255),
    bde_name VARCHAR(255),
    unit_name VARCHAR(255),
    upload_time TIMESTAMP,
    hierarchy_level VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- IMINT-specific indexes
CREATE INDEX IF NOT EXISTS idx_imint_data_location ON imint_data(longitude, latitude);
CREATE INDEX IF NOT EXISTS idx_imint_data_date ON imint_data(observation_date);
CREATE INDEX IF NOT EXISTS idx_imint_data_source ON imint_data(source_agency);
CREATE INDEX IF NOT EXISTS idx_imint_data_grading ON imint_data(grading);
CREATE INDEX IF NOT EXISTS idx_imint_data_fmn_code ON imint_data(fmn_code);
CREATE INDEX IF NOT EXISTS idx_imint_composite_date_location ON imint_data(observation_date, longitude, latitude);
""",

    "tac_int": """
-- Tactical Intelligence Table
CREATE TABLE IF NOT EXISTS tac_int (
    id SERIAL PRIMARY KEY,
    observation_date DATE,
    observation_time TIME,
    precedence VARCHAR(50),
    -- Foreign key references to classification tables
    tgt_type_id INTEGER REFERENCES target_type(id),
    tgt_sub_type_id INTEGER REFERENCES target_sub_type(id),
    tgt_cl_id INTEGER REFERENCES target_classification(id),
    activity_type_id INTEGER REFERENCES activity_type(id),
    activity_sub_type_id INTEGER REFERENCES activity_sub_type(id),
    activity_cl_id INTEGER REFERENCES activity_classification(id),
    incident_type_id INTEGER REFERENCES esitrep_type(id),
    incident_sub_type_id INTEGER REFERENCES esitrep_sub_type(id),
    incident_cl_id INTEGER REFERENCES esitrep_classification(id),
    -- Source and assessment information
    source_agency VARCHAR(255), -- BSF, Army Patrol, etc.
    grading VARCHAR(50),       -- Source reliability and information credibility
    strength VARCHAR(255),     -- Observed force strength
    -- Geographic information
    longitude DOUBLE PRECISION,
    latitude DOUBLE PRECISION,
    height DOUBLE PRECISION,
    easting DOUBLE PRECISION,
    northing DOUBLE PRECISION,
    zone VARCHAR(50),
    input_method VARCHAR(255), -- Visual observation, patrol report, etc.
    description TEXT,
    -- Formation hierarchy (observing unit)
    fmn_code BIGINT,
    cmd_name VARCHAR(255),
    corps_name VARCHAR(255),
    div_name VARCHAR(255),
    bde_name VARCHAR(255),
    unit_name VARCHAR(255),
    upload_time TIMESTAMP,
    hierarchy_level VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TACINT-specific indexes
CREATE INDEX IF NOT EXISTS idx_tac_int_location ON tac_int(longitude, latitude);
CREATE INDEX IF NOT EXISTS idx_tac_int_date ON tac_int(observation_date);
CREATE INDEX IF NOT EXISTS idx_tac_int_source ON tac_int(source_agency);
CREATE INDEX IF NOT EXISTS idx_tac_int_grading ON tac_int(grading);
CREATE INDEX IF NOT EXISTS idx_tac_int_fmn_code ON tac_int(fmn_code);
CREATE INDEX IF NOT EXISTS idx_tac_int_composite_date_grading ON tac_int(observation_date, grading);
""",

    "en_activity": """
-- Enemy Activity Table (Fused Intelligence)
CREATE TABLE IF NOT EXISTS en_activity (
    id SERIAL PRIMARY KEY,
    sensor_type VARCHAR(255),  -- Type of contributing sensor
    sensor_id VARCHAR(255),    -- Specific sensor identifier
    -- Foreign key references to classification tables
    tgt_type_id INTEGER REFERENCES target_type(id),
    tgt_sub_type_id INTEGER REFERENCES target_sub_type(id),
    tgt_cl_id INTEGER REFERENCES target_classification(id),
    activity_type_id INTEGER REFERENCES activity_type(id),
    activity_sub_type_id INTEGER REFERENCES activity_sub_type(id),
    activity_cl_id INTEGER REFERENCES activity_classification(id),
    -- Measurement data
    bearing VARCHAR(255),      -- Bearing to target
    range_km VARCHAR(255),     -- Range to target in kilometers
    strength VARCHAR(255),     -- Assessed enemy strength
    -- Geographic information
    longitude DOUBLE PRECISION,
    latitude DOUBLE PRECISION,
    height DOUBLE PRECISION,
    easting DOUBLE PRECISION,
    northing DOUBLE PRECISION,
    zone VARCHAR(50),
    input_method VARCHAR(255), -- Fusion methodology
    description TEXT,
    -- Formation hierarchy (analyzing unit)
    fmn_code BIGINT,
    cmd_name VARCHAR(255),
    corps_name VARCHAR(255),
    div_name VARCHAR(255),
    bde_name VARCHAR(255),
    unit_name VARCHAR(255),
    upload_time TIMESTAMP,
    hierarchy_level VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Enemy Activity-specific indexes
CREATE INDEX IF NOT EXISTS idx_en_activity_location ON en_activity(longitude, latitude);
CREATE INDEX IF NOT EXISTS idx_en_activity_upload_time ON en_activity(upload_time);
CREATE INDEX IF NOT EXISTS idx_en_activity_sensor_type ON en_activity(sensor_type);
CREATE INDEX IF NOT EXISTS idx_en_activity_fmn_code ON en_activity(fmn_code);
CREATE INDEX IF NOT EXISTS idx_en_activity_composite_time_location ON en_activity(upload_time, longitude, latitude);
""",

    "e_sitrep_mst": """
-- Electronic Situation Report Master Table
CREATE TABLE IF NOT EXISTS e_sitrep_mst (
    id SERIAL PRIMARY KEY,
    incident_date DATE,
    incident_time TIME,
    precedence VARCHAR(50),    -- Report precedence
    -- Foreign key references to incident classification
    incident_type_id INTEGER REFERENCES esitrep_type(id),
    incident_sub_type_id INTEGER REFERENCES esitrep_sub_type(id),
    incident_cl_id INTEGER REFERENCES esitrep_classification(id),
    -- Force assessment
    source VARCHAR(255),       -- Source of the report
    str_own VARCHAR(255),      -- Own forces strength
    str_en VARCHAR(255),       -- Enemy forces strength
    -- Geographic information
    longitude DOUBLE PRECISION,
    latitude DOUBLE PRECISION,
    height DOUBLE PRECISION,
    easting DOUBLE PRECISION,
    northing DOUBLE PRECISION,
    zone VARCHAR(50),
    incident_status VARCHAR(100), -- ONGOING, COMPLETED, DEVELOPING
    description TEXT,
    -- Formation hierarchy (reporting unit)
    fmn_code BIGINT,
    cmd_name VARCHAR(255),
    corps_name VARCHAR(255),
    div_name VARCHAR(255),
    bde_name VARCHAR(255),
    unit_name VARCHAR(255),
    upload_time TIMESTAMP,
    hierarchy_level VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SITREP-specific indexes
CREATE INDEX IF NOT EXISTS idx_e_sitrep_mst_location ON e_sitrep_mst(longitude, latitude);
CREATE INDEX IF NOT EXISTS idx_e_sitrep_mst_date ON e_sitrep_mst(incident_date);
CREATE INDEX IF NOT EXISTS idx_e_sitrep_mst_status ON e_sitrep_mst(incident_status);
CREATE INDEX IF NOT EXISTS idx_e_sitrep_mst_fmn_code ON e_sitrep_mst(fmn_code);
CREATE INDEX IF NOT EXISTS idx_e_sitrep_mst_composite_date_status ON e_sitrep_mst(incident_date, incident_status);
"""
}

def get_complete_schema_for_table(table_name: str) -> str:
    """Get complete schema (reference + specific table) for a table"""
    if table_name not in TABLE_SCHEMAS:
        raise ValueError(f"Unknown table: {table_name}")
    
    return COMMON_REFERENCE_SCHEMA + "\n" + TABLE_SCHEMAS[table_name]

def get_database_info_summary() -> Dict:
    """Get summary information about all configured databases"""
    return {
        "total_databases": len(INTELLIGENCE_DATABASES),
        "database_types": list(INTELLIGENCE_DATABASES.keys()),
        "host_config": {
            "host": DB_CONFIG.get('host', 'Not configured'),
            "port": DB_CONFIG.get('port', 'Not configured'),
            "user": DB_CONFIG.get('user', 'Not configured')
        },
        "databases": {
            db_type: {
                "name": config["db_name"],
                "description": config["description"],
                "intelligence_type": config["intelligence_type"],
                "primary_table": config["primary_table"]
            }
            for db_type, config in INTELLIGENCE_DATABASES.items()
        }
    }

# Export the main configuration for backward compatibility
DATABASE_CONFIGS = INTELLIGENCE_DATABASES