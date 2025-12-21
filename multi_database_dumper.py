#!/usr/bin/env python3
"""
Multi-Database Dumper for SAMA Intelligence Data
Creates 5 separate databases for each intelligence table type on Azure PostgreSQL

Tables to be distributed:
1. elint_db - Electronic Intelligence
2. imint_db - Imagery Intelligence  
3. tacint_db - Tactical Intelligence
4. enemy_activity_db - Enemy Activity Data
5. sitrep_db - Situation Reports

Each database will contain:
- One primary intelligence table
- All necessary reference data tables (for foreign key integrity)
- Proper indexes and constraints
"""

import os
import sys
import json
import logging
import psycopg2
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import OUTPUT_DIR, DB_CONFIG
from utils.database import DatabaseManager
from multi_db_config import (
    INTELLIGENCE_DATABASES as DATABASE_CONFIGS,
    get_complete_schema_for_table,
    get_database_info_summary
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MultiDatabaseDumper:
    """
    Manages creation and population of multiple intelligence databases
    """
    
    def __init__(self, base_config: Dict[str, str] = None):
        self.base_config = base_config or DB_CONFIG.copy()
        self.admin_connection = None
        
    def create_all_databases(self):
        """Create all 5 intelligence databases"""
        logger.info("="*80)
        logger.info("MULTI-DATABASE CREATION STARTED")
        logger.info("="*80)
        logger.info(f"Azure Host: {self.base_config['host']}")
        logger.info(f"Total Databases to Create: {len(DATABASE_CONFIGS)}")
        logger.info("="*80)
        
        success_count = 0
        failed_databases = []
        
        for db_type, config in DATABASE_CONFIGS.items():
            try:
                logger.info(f"\n🔄 Processing {config['description']}")
                logger.info(f"   {config['color_emoji']} Intelligence Type: {config['intelligence_type']}")
                logger.info(f"   Database Name: {config['db_name']}")
                logger.info(f"   Primary Table: {config['primary_table']}")
                
                # Step 1: Create database
                if self._create_database(config['db_name']):
                    logger.info(f"   ✅ Database created: {config['db_name']}")
                    
                    # Step 2: Create schema in database
                    if self._create_schema_in_database(config['db_name'], config['primary_table']):
                        logger.info(f"   ✅ Schema created for: {config['primary_table']}")
                        
                        # Step 3: Load reference data
                        if self._load_reference_data(config['db_name']):
                            logger.info(f"   ✅ Reference data loaded")
                            
                            # Step 4: Load intelligence data
                            if self._load_intelligence_data(config['db_name'], config):
                                logger.info(f"   ✅ Intelligence data loaded")
                                success_count += 1
                                logger.info(f"   🎉 {config['description']} - COMPLETED SUCCESSFULLY")
                            else:
                                failed_databases.append(f"{db_type} - Data loading failed")
                        else:
                            failed_databases.append(f"{db_type} - Reference data loading failed")
                    else:
                        failed_databases.append(f"{db_type} - Schema creation failed")
                else:
                    failed_databases.append(f"{db_type} - Database creation failed")
                    
            except Exception as e:
                logger.error(f"   ❌ Failed to process {config['description']}: {str(e)}")
                failed_databases.append(f"{db_type} - {str(e)}")
        
        # Final summary
        logger.info("\n" + "="*80)
        logger.info("MULTI-DATABASE CREATION SUMMARY")
        logger.info("="*80)
        logger.info(f"✅ Successfully Created: {success_count}/{len(DATABASE_CONFIGS)} databases")
        
        if failed_databases:
            logger.error(f"❌ Failed Databases ({len(failed_databases)}):")
            for failure in failed_databases:
                logger.error(f"   - {failure}")
        
        if success_count == len(DATABASE_CONFIGS):
            logger.info("🎉 ALL DATABASES CREATED SUCCESSFULLY!")
        else:
            logger.warning(f"⚠️  {len(failed_databases)} database(s) had issues")
            
        logger.info("="*80)
        
        return success_count, failed_databases
    
    def _create_database(self, db_name: str) -> bool:
        """Create a new database on Azure PostgreSQL"""
        try:
            # Connect to postgres database to create new database
            admin_config = self.base_config.copy()
            admin_config['database'] = 'postgres'  # Connect to default postgres DB
            
            conn = psycopg2.connect(**admin_config)
            conn.autocommit = True
            cursor = conn.cursor()
            
            # Check if database already exists
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            if cursor.fetchone():
                logger.info(f"   📋 Database {db_name} already exists, dropping and recreating...")
                cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")
            
            # Create new database
            cursor.execute(f"CREATE DATABASE {db_name}")
            
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"   ❌ Failed to create database {db_name}: {str(e)}")
            return False
    
    def _create_schema_in_database(self, db_name: str, primary_table: str) -> bool:
        """Create schema in the specified database"""
        try:
            # Connect to the new database
            db_config = self.base_config.copy()
            db_config['database'] = db_name
            
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            
            # Use the enhanced schema from multi_db_config
            schema_sql = get_complete_schema_for_table(primary_table)
            
            # Execute schema creation (may contain multiple statements)
            statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement.strip():
                    cursor.execute(statement)
            
            conn.commit()
            
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"   ❌ Failed to create schema in {db_name}: {str(e)}")
            return False
    

    
    def _load_reference_data(self, db_name: str) -> bool:
        """Load reference data into database"""
        try:
            # Load reference data from file
            reference_file = os.path.join(OUTPUT_DIR, "reference_data_complete.json")
            if not os.path.exists(reference_file):
                logger.warning(f"   ⚠️  Reference data file not found: {reference_file}")
                return True  # Continue without reference data
            
            with open(reference_file, 'r', encoding='utf-8') as f:
                reference_data = json.load(f)
            
            # Connect to database
            db_config = self.base_config.copy()
            db_config['database'] = db_name
            
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            
            # Insert reference data
            self._insert_reference_data(cursor, reference_data)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"   ❌ Failed to load reference data into {db_name}: {str(e)}")
            return False
    
    def _insert_reference_data(self, cursor, reference_data: Dict):
        """Insert reference data using cursor"""
        try:
            # Activity types
            activity_data = reference_data.get("activity_classification", {})
            for activity_type in activity_data.get("activity_types", []):
                cursor.execute("""
                    INSERT INTO activity_type (id, activity_type) 
                    VALUES (%s, %s) ON CONFLICT (id) DO NOTHING
                """, (activity_type["id"], activity_type["name"]))
                
                for sub_type in activity_type.get("sub_types", []):
                    cursor.execute("""
                        INSERT INTO activity_sub_type (id, activity_type_id, activity_sub_type)
                        VALUES (%s, %s, %s) ON CONFLICT (id) DO NOTHING
                    """, (sub_type["id"], activity_type["id"], sub_type["name"]))
                    
                    for classification in sub_type.get("classifications", []):
                        cursor.execute("""
                            INSERT INTO activity_classification (id, activity_type_id, activity_sub_type_id, activity_classification)
                            VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO NOTHING
                        """, (classification["id"], activity_type["id"], sub_type["id"], classification["name"]))
            
            # Target types  
            target_data = reference_data.get("target_classification", {})
            for target_type in target_data.get("target_types", []):
                cursor.execute("""
                    INSERT INTO target_type (id, target_type) 
                    VALUES (%s, %s) ON CONFLICT (id) DO NOTHING
                """, (target_type["id"], target_type["name"]))
                
                for sub_type in target_type.get("sub_types", []):
                    cursor.execute("""
                        INSERT INTO target_sub_type (id, target_type_id, target_sub_type)
                        VALUES (%s, %s, %s) ON CONFLICT (id) DO NOTHING
                    """, (sub_type["id"], target_type["id"], sub_type["name"]))
                    
                    for classification in sub_type.get("classifications", []):
                        cursor.execute("""
                            INSERT INTO target_classification (id, target_type_id, target_sub_type_id, target_classification)
                            VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO NOTHING
                        """, (classification["id"], target_type["id"], sub_type["id"], classification["name"]))
            
            # Incident types
            incident_data = reference_data.get("incident_classification", {})
            for incident_type in incident_data.get("incident_types", []):
                cursor.execute("""
                    INSERT INTO esitrep_type (id, incident_type) 
                    VALUES (%s, %s) ON CONFLICT (id) DO NOTHING
                """, (incident_type["id"], incident_type["name"]))
                
                for sub_type in incident_type.get("sub_types", []):
                    cursor.execute("""
                        INSERT INTO esitrep_sub_type (id, incident_type_id, incident_sub_type)
                        VALUES (%s, %s, %s) ON CONFLICT (id) DO NOTHING
                    """, (sub_type["id"], incident_type["id"], sub_type["name"]))
                    
                    for classification in sub_type.get("classifications", []):
                        cursor.execute("""
                            INSERT INTO esitrep_classification (id, incident_type_id, incident_sub_type_id, incident_classification)
                            VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO NOTHING
                        """, (classification["id"], incident_type["id"], sub_type["id"], classification["name"]))
                        
        except Exception as e:
            logger.error(f"Error inserting reference data: {str(e)}")
            raise
    
    def _load_intelligence_data(self, db_name: str, config: Dict) -> bool:
        """Load intelligence data into database"""
        try:
            # Load data from JSON file
            data_file = os.path.join(OUTPUT_DIR, config["data_file"])
            if not os.path.exists(data_file):
                logger.warning(f"   ⚠️  Data file not found: {data_file}")
                return True  # Continue without data
            
            with open(data_file, 'r', encoding='utf-8') as f:
                data_records = json.load(f)
            
            if not data_records:
                logger.warning(f"   ⚠️  No data records found in {data_file}")
                return True
            
            # Connect to database
            db_config = self.base_config.copy()
            db_config['database'] = db_name
            
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            
            # Insert data using specialized method for each table type
            insert_method = getattr(self, f"_insert_{config['primary_table']}_data", None)
            if insert_method:
                insert_method(cursor, data_records)
            else:
                logger.error(f"   ❌ No insert method found for {config['primary_table']}")
                return False
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"   📊 Inserted {len(data_records)} records into {config['primary_table']}")
            return True
            
        except Exception as e:
            logger.error(f"   ❌ Failed to load intelligence data into {db_name}: {str(e)}")
            return False
    
    def _insert_elint_data(self, cursor, records: List[Dict]):
        """Insert ELINT data"""
        for record in records:
            cursor.execute("""
                INSERT INTO elint (
                    observation_date, from_time, to_time, enemy_unit, location_name,
                    range_km, emitter_type, emitter_name, frequency, longitude, 
                    latitude, height, easting, northing, zone, description,
                    fmn_code, cmd_name, corps_name, div_name, bde_name, unit_name, hierarchy_level
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                record.get("date"), record.get("from_time"), record.get("to_time"),
                record.get("enemy_unit"), record.get("location"),
                record.get("range"), record.get("emitter_type"), record.get("emitter_name"),
                record.get("frequency"), record.get("long"), record.get("lat"),
                record.get("ht"), record.get("e"), record.get("n"), record.get("zone"),
                record.get("description"), record.get("fmn_code"), record.get("cmd_name"),
                record.get("corps_name"), record.get("div_name"), record.get("bde_name"),
                record.get("unit_name"), record.get("level")
            ))
    
    def _insert_imint_data_data(self, cursor, records: List[Dict]):
        """Insert IMINT data"""
        for record in records:
            cursor.execute("""
                INSERT INTO imint_data (
                    observation_date, observation_time, precedence, source_agency, grading,
                    strength, longitude, latitude, height, easting, northing, zone,
                    input_method, description, fmn_code, cmd_name, corps_name, div_name,
                    bde_name, unit_name, hierarchy_level, upload_time
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                record.get("Date"), record.get("time"), record.get("pre"),
                record.get("source_agency"), record.get("grading"), record.get("str"),
                record.get("long"), record.get("lat"), record.get("ht"),
                record.get("e"), record.get("n"), record.get("zone"),
                record.get("input"), record.get("description"), record.get("fmn_code"),
                record.get("cmd_name"), record.get("corps_name"), record.get("div_name"),
                record.get("bde_name"), record.get("unit_name"), record.get("level"),
                record.get("upload_time")
            ))
    
    def _insert_tac_int_data(self, cursor, records: List[Dict]):
        """Insert TACINT data"""
        for record in records:
            cursor.execute("""
                INSERT INTO tac_int (
                    observation_date, observation_time, precedence, source_agency, grading,
                    strength, longitude, latitude, height, easting, northing, zone,
                    input_method, description, fmn_code, cmd_name, corps_name, div_name,
                    bde_name, unit_name, hierarchy_level, upload_time
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                record.get("Date"), record.get("time"), record.get("pre"),
                record.get("source_agency"), record.get("grading"), record.get("str"),
                record.get("long"), record.get("lat"), record.get("ht"),
                record.get("e"), record.get("n"), record.get("zone"),
                record.get("input"), record.get("description"), record.get("fmn_code"),
                record.get("cmd_name"), record.get("corps_name"), record.get("div_name"),
                record.get("bde_name"), record.get("unit_name"), record.get("level"),
                record.get("upload_time")
            ))
    
    def _insert_en_activity_data(self, cursor, records: List[Dict]):
        """Insert Enemy Activity data"""
        for record in records:
            cursor.execute("""
                INSERT INTO en_activity (
                    sensor_type, sensor_id, bearing, range_km, strength,
                    longitude, latitude, height, easting, northing, zone,
                    input_method, description, fmn_code, cmd_name, corps_name,
                    div_name, bde_name, unit_name, hierarchy_level, upload_time
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                record.get("sensor_type"), record.get("sensor_id"), record.get("bearing"),
                record.get("range_km"), record.get("strength"), record.get("long"),
                record.get("lat"), record.get("ht"), record.get("e"), record.get("n"),
                record.get("zone"), record.get("input_method"), record.get("description"),
                record.get("fmn_code"), record.get("cmd_name"), record.get("corps_name"),
                record.get("div_name"), record.get("bde_name"), record.get("unit_name"),
                record.get("level"), record.get("upload_time")
            ))
    
    def _insert_e_sitrep_mst_data(self, cursor, records: List[Dict]):
        """Insert SITREP data"""
        for record in records:
            cursor.execute("""
                INSERT INTO e_sitrep_mst (
                    incident_date, incident_time, precedence, source, str_own, str_en,
                    longitude, latitude, height, easting, northing, zone,
                    incident_status, description, fmn_code, cmd_name, corps_name,
                    div_name, bde_name, unit_name, hierarchy_level, upload_time
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                record.get("Incident_date"), record.get("time"), record.get("pre"),
                record.get("source"), record.get("str_own"), record.get("str_en"),
                record.get("long"), record.get("lat"), record.get("ht"),
                record.get("e"), record.get("n"), record.get("zone"),
                record.get("Incident_states"), record.get("description"), record.get("fmn_code"),
                record.get("cmd_name"), record.get("corps_name"), record.get("div_name"),
                record.get("bde_name"), record.get("unit_name"), record.get("level"),
                record.get("upload_time")
            ))
    
    def list_created_databases(self):
        """List all databases that were created"""
        logger.info("\n" + "="*80)
        logger.info("CREATED DATABASE INVENTORY")
        logger.info("="*80)
        
        try:
            admin_config = self.base_config.copy()
            admin_config['database'] = 'postgres'
            
            conn = psycopg2.connect(**admin_config)
            cursor = conn.cursor()
            
            # Get all databases matching our naming pattern
            cursor.execute("""
                SELECT datname, pg_size_pretty(pg_database_size(datname)) as size
                FROM pg_database 
                WHERE datname LIKE '%intelligence%' OR datname LIKE '%enemy_activity%' OR datname LIKE '%sitrep%'
                ORDER BY datname
            """)
            
            databases = cursor.fetchall()
            
            for db_name, size in databases:
                logger.info(f"📊 {db_name:<30} | Size: {size}")
                
                # Get table info for each database
                try:
                    db_config = self.base_config.copy()
                    db_config['database'] = db_name
                    db_conn = psycopg2.connect(**db_config)
                    db_cursor = db_conn.cursor()
                    
                    db_cursor.execute("""
                        SELECT table_name, 
                               (SELECT COUNT(*) FROM information_schema.columns 
                                WHERE table_name = t.table_name AND table_schema = 'public') as column_count
                        FROM information_schema.tables t
                        WHERE table_schema = 'public' 
                        AND table_type = 'BASE TABLE'
                        ORDER BY table_name
                    """)
                    
                    tables = db_cursor.fetchall()
                    for table_name, col_count in tables:
                        logger.info(f"   └── {table_name:<25} ({col_count} columns)")
                    
                    db_cursor.close()
                    db_conn.close()
                    
                except Exception as e:
                    logger.warning(f"   └── Could not access table info: {str(e)}")
                
                logger.info("")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to list databases: {str(e)}")
        
        logger.info("="*80)


def main():
    """Main execution function"""
    
    logger.info("🚀 Multi-Database Dumper for SAMA Intelligence Data")
    logger.info("📍 Target: Azure PostgreSQL (Turinton Host)")
    logger.info("🎯 Objective: Create 5 separate intelligence databases\n")
    
    try:
        # Initialize dumper
        dumper = MultiDatabaseDumper()
        
        # Create all databases
        success_count, failures = dumper.create_all_databases()
        
        # List created databases
        dumper.list_created_databases()
        
        if success_count == len(DATABASE_CONFIGS):
            logger.info("🎉 ALL DATABASES SUCCESSFULLY CREATED!")
            return 0
        else:
            logger.error("❌ SOME DATABASES FAILED TO CREATE")
            return 1
            
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Operation interrupted by user")
        return 130
        
    except Exception as e:
        logger.error(f"💥 Fatal error: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)