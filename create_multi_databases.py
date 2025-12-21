"""
Multi-Database Creator for SAMA Intelligence Data
Dumps each of the 5 intelligence tables into separate PostgreSQL databases on Azure
"""

import os
import re
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection parameters
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASSWORD')
OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'data/output')

# Define the 5 databases and their corresponding tables
DATABASE_CONFIG = {
    'elint': {
        'table': 'elint',
        'sql_file': 'elint_kargil_war_1999_inserts.sql',
        'description': 'Electronic Intelligence Database'
    },
    'imint_data': {
        'table': 'imint_data',
        'sql_file': 'imint_data_kargil_war_1999_inserts.sql',
        'description': 'Imagery Intelligence Database'
    },
    'tac_int': {
        'table': 'tac_int',
        'sql_file': 'tac_int_kargil_war_1999_inserts.sql',
        'description': 'Tactical Intelligence Database'
    },
    'en_activity': {
        'table': 'en_activity',
        'sql_file': 'en_activity_kargil_war_1999_inserts.sql',
        'description': 'Enemy Activity Database'
    },
    'e_sitrep_mst': {
        'table': 'e_sitrep_mst',
        'sql_file': 'e_sitrep_mst_kargil_war_1999_inserts.sql',
        'description': 'Situation Report Database'
    }
}

def create_database(db_name):
    """Create a single database if it doesn't exist"""
    try:
        # Connect to postgres database to create new database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname='postgres',
            user=DB_USER,
            password=DB_PASS
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        exists = cursor.fetchone()
        
        if not exists:
            logger.info(f"Creating database '{db_name}'...")
            cursor.execute(f"CREATE DATABASE {db_name}")
            logger.info(f"✓ Database '{db_name}' created successfully.")
        else:
            logger.info(f"Database '{db_name}' already exists.")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error creating database '{db_name}': {e}")
        return False

def get_table_columns_from_sql(sql_file):
    """Extract table name and columns from SQL INSERT file"""
    try:
        with open(sql_file, 'r', encoding='utf-8') as f:
            for line in f:
                # Look for INSERT INTO statement
                match = re.match(r"INSERT INTO ([^( ]+) \(([^)]+)\)", line)
                if match:
                    table = match.group(1)
                    columns = [col.strip() for col in match.group(2).split(',')]
                    return table, columns
        return None, None
    except Exception as e:
        logger.error(f"Error reading SQL file '{sql_file}': {e}")
        return None, None

def create_table_in_database(db_name, table_name, columns):
    """Create table structure in specified database"""
    try:
        # Connect to the specific database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=db_name,
            user=DB_USER,
            password=DB_PASS
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        logger.info(f"Creating table '{table_name}' in database '{db_name}'...")
        
        # Drop table if exists and create new one
        cursor.execute(f'DROP TABLE IF EXISTS {table_name} CASCADE;')
        
        # Create table with all columns as TEXT for simplicity
        col_defs = ', '.join([f'"{col}" TEXT' for col in columns])
        cursor.execute(f'CREATE TABLE {table_name} ({col_defs});')
        
        logger.info(f"✓ Table '{table_name}' created with {len(columns)} columns")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error creating table '{table_name}' in database '{db_name}': {e}")
        return False

def execute_sql_file_in_database(db_name, sql_file):
    """Execute SQL INSERT file in specified database"""
    try:
        # Connect to the specific database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=db_name,
            user=DB_USER,
            password=DB_PASS
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        logger.info(f"Importing data from '{sql_file}' into database '{db_name}'...")
        
        # Read and execute SQL file
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
            cursor.execute(sql_content)
        
        logger.info(f"✓ Successfully imported data from '{sql_file}'")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error importing data from '{sql_file}' to database '{db_name}': {e}")
        return False

def get_record_count(db_name, table_name):
    """Get the number of records in a table"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=db_name,
            user=DB_USER,
            password=DB_PASS
        )
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        return count
        
    except Exception as e:
        logger.error(f"Error getting record count from '{table_name}' in '{db_name}': {e}")
        return 0

def main():
    """Main function to create multiple databases and import data"""
    
    logger.info("="*80)
    logger.info("SAMA MULTI-DATABASE CREATOR")
    logger.info("Creating 5 separate intelligence databases on Azure PostgreSQL")
    logger.info("="*80)
    
    # Check if output directory exists
    if not os.path.exists(OUTPUT_DIR):
        logger.error(f"Output directory not found: {OUTPUT_DIR}")
        return False
    
    success_count = 0
    total_records = 0
    
    # Process each database
    for db_name, config in DATABASE_CONFIG.items():
        logger.info(f"\n📊 Processing {config['description']} ({db_name})...")
        
        sql_file_path = os.path.join(OUTPUT_DIR, config['sql_file'])
        
        # Check if SQL file exists
        if not os.path.exists(sql_file_path):
            logger.error(f"  ❌ SQL file not found: {sql_file_path}")
            continue
        
        # Step 1: Create database
        if not create_database(db_name):
            logger.error(f"  ❌ Failed to create database: {db_name}")
            continue
        
        # Step 2: Extract table schema from SQL file
        table_name, columns = get_table_columns_from_sql(sql_file_path)
        if not table_name or not columns:
            logger.error(f"  ❌ Failed to extract schema from: {config['sql_file']}")
            continue
        
        logger.info(f"  📋 Table: {table_name} ({len(columns)} columns)")
        
        # Step 3: Create table structure
        if not create_table_in_database(db_name, table_name, columns):
            logger.error(f"  ❌ Failed to create table structure")
            continue
        
        # Step 4: Import data
        if not execute_sql_file_in_database(db_name, sql_file_path):
            logger.error(f"  ❌ Failed to import data")
            continue
        
        # Step 5: Verify data import
        record_count = get_record_count(db_name, table_name)
        logger.info(f"  ✅ Successfully imported {record_count} records")
        
        success_count += 1
        total_records += record_count
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("MULTI-DATABASE CREATION SUMMARY")
    logger.info("="*80)
    logger.info(f"✅ Databases successfully created: {success_count}/5")
    logger.info(f"📊 Total records imported: {total_records}")
    logger.info("")
    
    if success_count == 5:
        logger.info("🎉 All intelligence databases created successfully!")
        logger.info("📍 Azure PostgreSQL Host: " + DB_HOST)
        logger.info("🗄️  Database Names:")
        for db_name, config in DATABASE_CONFIG.items():
            logger.info(f"   - {db_name} ({config['description']})")
    else:
        logger.warning(f"⚠️  Only {success_count} out of 5 databases were created successfully.")
    
    logger.info("="*80)
    return success_count == 5

if __name__ == "__main__":
    success = main()
    if success:
        exit(0)
    else:
        exit(1)