"""
Multi-Database Manager for SAMA Intelligence Systems
Provides utilities to manage, monitor, and maintain the 5 intelligence databases
"""

import os
import psycopg2
from dotenv import load_dotenv
import logging
from datetime import datetime
import argparse

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection parameters
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASSWORD')

# Database configuration
INTELLIGENCE_DATABASES = {
    'elint': {
        'table': 'elint',
        'description': 'Electronic Intelligence Database',
        'data_type': 'ELINT - Signal Intelligence & Communications Intercepts'
    },
    'imint_data': {
        'table': 'imint_data',
        'description': 'Imagery Intelligence Database',
        'data_type': 'IMINT - Satellite & Aerial Imagery Analysis'
    },
    'tac_int': {
        'table': 'tac_int',
        'description': 'Tactical Intelligence Database',
        'data_type': 'TACINT - Ground-based Tactical Reports'
    },
    'en_activity': {
        'table': 'en_activity',
        'description': 'Enemy Activity Database',
        'data_type': 'Enemy Activity - Fused Intelligence Reports'
    },
    'e_sitrep_mst': {
        'table': 'e_sitrep_mst',
        'description': 'Situation Report Database',
        'data_type': 'SITREP - Operational Situation Reports'
    }
}

class DatabaseManager:
    """Manage multiple intelligence databases"""
    
    def __init__(self):
        self.host = DB_HOST
        self.port = DB_PORT
        self.user = DB_USER
        self.password = DB_PASS
    
    def connect_to_database(self, db_name):
        """Create connection to specific database"""
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=db_name,
                user=self.user,
                password=self.password
            )
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to database '{db_name}': {e}")
            return None
    
    def database_exists(self, db_name):
        """Check if database exists"""
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname='postgres',
                user=self.user,
                password=self.password
            )
            cursor = conn.cursor()
            cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
            exists = cursor.fetchone() is not None
            cursor.close()
            conn.close()
            return exists
        except Exception as e:
            logger.error(f"Error checking if database '{db_name}' exists: {e}")
            return False
    
    def get_database_size(self, db_name):
        """Get database size in MB"""
        try:
            conn = self.connect_to_database(db_name)
            if not conn:
                return 0
            
            cursor = conn.cursor()
            cursor.execute(f"SELECT pg_size_pretty(pg_database_size('{db_name}'))")
            size = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            return size
        except Exception as e:
            logger.error(f"Error getting size for database '{db_name}': {e}")
            return "Unknown"
    
    def get_table_info(self, db_name, table_name):
        """Get table information (record count, size)"""
        try:
            conn = self.connect_to_database(db_name)
            if not conn:
                return None
            
            cursor = conn.cursor()
            
            # Get record count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            record_count = cursor.fetchone()[0]
            
            # Get table size
            cursor.execute(f"SELECT pg_size_pretty(pg_total_relation_size('{table_name}'))")
            table_size = cursor.fetchone()[0]
            
            # Get column count
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
            """)
            column_count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            return {
                'record_count': record_count,
                'table_size': table_size,
                'column_count': column_count
            }
        except Exception as e:
            logger.error(f"Error getting table info for '{table_name}' in '{db_name}': {e}")
            return None
    
    def get_sample_records(self, db_name, table_name, limit=3):
        """Get sample records from table"""
        try:
            conn = self.connect_to_database(db_name)
            if not conn:
                return []
            
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
            records = cursor.fetchall()
            
            # Get column names
            cursor.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}' 
                ORDER BY ordinal_position
            """)
            columns = [row[0] for row in cursor.fetchall()]
            
            cursor.close()
            conn.close()
            
            return [dict(zip(columns, record)) for record in records]
        except Exception as e:
            logger.error(f"Error getting sample records from '{table_name}' in '{db_name}': {e}")
            return []
    
    def drop_database(self, db_name):
        """Drop a database (use with caution!)"""
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname='postgres',
                user=self.user,
                password=self.password
            )
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Terminate connections to the database
            cursor.execute(f"""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = '{db_name}' AND pid <> pg_backend_pid()
            """)
            
            cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")
            logger.info(f"✓ Database '{db_name}' dropped successfully")
            
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error dropping database '{db_name}': {e}")
            return False

def show_database_status():
    """Display status of all intelligence databases"""
    manager = DatabaseManager()
    
    logger.info("="*100)
    logger.info("SAMA INTELLIGENCE DATABASES STATUS")
    logger.info("="*100)
    logger.info(f"Azure PostgreSQL Host: {DB_HOST}")
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")
    
    total_records = 0
    active_databases = 0
    
    for db_name, config in INTELLIGENCE_DATABASES.items():
        logger.info(f"📊 {config['description']} ({db_name})")
        logger.info(f"   Data Type: {config['data_type']}")
        
        # Check if database exists
        if manager.database_exists(db_name):
            active_databases += 1
            logger.info(f"   Status: ✅ Active")
            
            # Get database size
            db_size = manager.get_database_size(db_name)
            logger.info(f"   Database Size: {db_size}")
            
            # Get table information
            table_info = manager.get_table_info(db_name, config['table'])
            if table_info:
                logger.info(f"   Records: {table_info['record_count']:,}")
                logger.info(f"   Columns: {table_info['column_count']}")
                logger.info(f"   Table Size: {table_info['table_size']}")
                total_records += table_info['record_count']
            else:
                logger.info(f"   Records: ❌ Error accessing table")
        else:
            logger.info(f"   Status: ❌ Not Found")
        
        logger.info("")
    
    # Summary
    logger.info("="*100)
    logger.info("SUMMARY")
    logger.info("="*100)
    logger.info(f"Active Databases: {active_databases}/5")
    logger.info(f"Total Records: {total_records:,}")
    
    if active_databases == 5:
        logger.info("🎉 All intelligence databases are operational!")
    else:
        logger.warning(f"⚠️  {5 - active_databases} database(s) missing or inaccessible")
    
    logger.info("="*100)

def show_sample_data(db_name=None):
    """Display sample data from databases"""
    manager = DatabaseManager()
    
    databases_to_check = {db_name: INTELLIGENCE_DATABASES[db_name]} if db_name else INTELLIGENCE_DATABASES
    
    for db_name, config in databases_to_check.items():
        logger.info(f"\n📋 SAMPLE DATA: {config['description']}")
        logger.info("-" * 80)
        
        if manager.database_exists(db_name):
            records = manager.get_sample_records(db_name, config['table'], 2)
            
            if records:
                for i, record in enumerate(records, 1):
                    logger.info(f"Record {i}:")
                    # Show key fields only to keep output manageable
                    key_fields = ['observation_date', 'enemy_unit', 'location_name', 'description']
                    for field in key_fields:
                        if field in record and record[field]:
                            value = str(record[field])[:100] + "..." if len(str(record[field])) > 100 else record[field]
                            logger.info(f"  {field}: {value}")
                    logger.info("")
            else:
                logger.info("  ❌ No data found or error accessing table")
        else:
            logger.info(f"  ❌ Database not found")

def drop_all_databases():
    """Drop all intelligence databases (use with extreme caution!)"""
    manager = DatabaseManager()
    
    logger.warning("⚠️  WARNING: This will permanently delete all intelligence databases!")
    confirm = input("Type 'DELETE ALL DATABASES' to confirm: ")
    
    if confirm == "DELETE ALL DATABASES":
        logger.info("Dropping all intelligence databases...")
        
        for db_name in INTELLIGENCE_DATABASES.keys():
            if manager.database_exists(db_name):
                logger.info(f"Dropping {db_name}...")
                manager.drop_database(db_name)
        
        logger.info("✓ All databases dropped")
    else:
        logger.info("Operation cancelled")

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='SAMA Intelligence Database Manager')
    parser.add_argument('--status', action='store_true', help='Show database status')
    parser.add_argument('--sample', action='store_true', help='Show sample data')
    parser.add_argument('--sample-db', type=str, help='Show sample data for specific database')
    parser.add_argument('--drop-all', action='store_true', help='Drop all databases (dangerous!)')
    
    args = parser.parse_args()
    
    if args.status:
        show_database_status()
    elif args.sample:
        show_sample_data()
    elif args.sample_db:
        if args.sample_db in INTELLIGENCE_DATABASES:
            show_sample_data(args.sample_db)
        else:
            logger.error(f"Database '{args.sample_db}' not found in configuration")
    elif args.drop_all:
        drop_all_databases()
    else:
        # Default: show status
        show_database_status()

if __name__ == "__main__":
    main()