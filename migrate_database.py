"""
Database Migration Script - Migrate from text-based schema to properly typed schema
Executes the 3-phase migration:
1. Create corrected schema
2. Migrate data from backup tables
3. Validate migration
"""

import os
import subprocess
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database configuration from .env
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "integrated_intel_sources")
DB_USER = os.getenv("DB_USER", "turintonadmin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
PSQL_PATH = r"C:\Program Files\PostgreSQL\17\bin\psql.exe"

# SQL files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQL_DIR = os.path.join(BASE_DIR, "sql")

SCHEMA_SQL = os.path.join(SQL_DIR, "03_create_corrected_schema_v2.sql")
MIGRATE_SQL = os.path.join(SQL_DIR, "04_migrate_data_final.sql")
VALIDATE_SQL = os.path.join(SQL_DIR, "05_validation.sql")


def run_sql_file(sql_file, description):
    """Execute a SQL file using psql"""
    print(f"\n{'='*80}")
    print(f"PHASE: {description}")
    print(f"{'='*80}\n")
    
    env = os.environ.copy()
    if DB_PASSWORD:
        env['PGPASSWORD'] = DB_PASSWORD
    
    cmd = [
        PSQL_PATH,
        "-h", DB_HOST,
        "-p", DB_PORT,
        "-U", DB_USER,
        "-d", DB_NAME,
        "-f", sql_file,
        "-v", "ON_ERROR_STOP=1"  # Stop on first error
    ]
    
    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        
        print("SUCCESS")
        if result.stdout:
            print(result.stdout)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print("FAILED")
        print(f"Error: {e}")
        if e.stdout:
            print(f"Output:\n{e.stdout}")
        if e.stderr:
            print(f"Error details:\n{e.stderr}")
        return False


def main():
    print("""
================================================================================
                   DATABASE MIGRATION TOOL                                    
              Text Schema --> Properly Typed Schema                             
================================================================================
    """)
    
    # Check if psql exists
    if not os.path.exists(PSQL_PATH):
        print(f"ERROR: PostgreSQL psql not found at {PSQL_PATH}")
        print("Please update PSQL_PATH in the script.")
        sys.exit(1)
    
    # Check if SQL files exist
    for sql_file in [SCHEMA_SQL, MIGRATE_SQL, VALIDATE_SQL]:
        if not os.path.exists(sql_file):
            print(f"ERROR: SQL file not found: {sql_file}")
            sys.exit(1)
    
    print(f"Database: {DB_NAME}@{DB_HOST}:{DB_PORT}")
    print(f"User: {DB_USER}")
    print()
    
    if not DB_PASSWORD:
        print("ERROR: DB_PASSWORD not found in .env file")
        print("Please add DB_PASSWORD to your .env file")
        sys.exit(1)
    
    # Phase 1: Create corrected schema
    print("Starting Phase 1: Schema Creation...")
    if not run_sql_file(SCHEMA_SQL, "Create Corrected Schema"):
        print("\nERROR: Migration failed at Phase 1 (Schema Creation)")
        sys.exit(1)
    
    # Phase 2: Migrate data
    print("\nStarting Phase 2: Data Migration...")
    if not run_sql_file(MIGRATE_SQL, "Migrate Data from Backup"):
        print("\nERROR: Migration failed at Phase 2 (Data Migration)")
        sys.exit(1)
    
    # Phase 3: Validate
    print("\nStarting Phase 3: Validation...")
    if not run_sql_file(VALIDATE_SQL, "Validate Migration"):
        print("\nERROR: Migration failed at Phase 3 (Validation)")
        sys.exit(1)
    
    print(f"\n{'='*80}")
    print("SUCCESS - MIGRATION COMPLETED!")
    print(f"{'='*80}\n")
    print("Summary:")
    print("- Phase 1: Schema created with proper data types (UUID, DATE, TIME, NUMERIC, INTEGER)")
    print("- Phase 2: Data migrated from text-based backup tables")
    print("- Phase 3: Validation completed")
    print()
    print("Next steps:")
    print("1. Review the validation output above")
    print("2. Test queries against the new schema")
    print("3. Update your application to use the new data types")
    print("4. (Optional) Drop backup schema after verification")


if __name__ == "__main__":
    main()
