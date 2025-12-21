"""
Database Cleanup Script - Drops old databases with long names
"""
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
import logging

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

# Old database names to drop
OLD_DATABASE_NAMES = [
    'elint_intelligence_db',
    'imint_intelligence_db',
    'tacint_intelligence_db',
    'enemy_activity_db', 
    'sitrep_intelligence_db'
]

def drop_database(db_name):
    """Drop a database if it exists"""
    try:
        # Connect to postgres database to drop other databases
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
        
        if exists:
            logger.info(f"Dropping database '{db_name}'...")
            
            # Terminate any active connections
            cursor.execute(f"""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = '{db_name}' AND pid <> pg_backend_pid()
            """)
            
            # Drop the database
            cursor.execute(f"DROP DATABASE {db_name}")
            logger.info(f"✓ Database '{db_name}' dropped successfully")
        else:
            logger.info(f"Database '{db_name}' does not exist - skipping")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error dropping database '{db_name}': {e}")
        return False

def main():
    """Drop all old databases"""
    logger.info("="*80)
    logger.info("CLEANING UP OLD INTELLIGENCE DATABASES")
    logger.info("="*80)
    
    success_count = 0
    
    for db_name in OLD_DATABASE_NAMES:
        if drop_database(db_name):
            success_count += 1
    
    logger.info("="*80)
    logger.info(f"CLEANUP SUMMARY: {success_count}/{len(OLD_DATABASE_NAMES)} databases processed")
    logger.info("="*80)
    
    return success_count

if __name__ == "__main__":
    main()