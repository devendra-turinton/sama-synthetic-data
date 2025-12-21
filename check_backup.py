"""Check if backup schema and tables exist"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
    
    cur = conn.cursor()
    
    # Check if backup schema exists
    cur.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'backup'")
    backup_schema = cur.fetchone()
    
    if not backup_schema:
        print("ERROR: Backup schema does not exist!")
        print("You need to run Phase 1 (Backup) first:")
        print("  CREATE SCHEMA IF NOT EXISTS backup;")
        print("  CREATE TABLE backup.e_sitrep_mst_backup AS SELECT * FROM public.e_sitrep_mst;")
        print("  ... (repeat for other tables)")
    else:
        print("Backup schema exists!")
        
        # Check backup tables
        print("\nBackup Table Record Counts:")
        print("="*50)
        
        tables = ['e_sitrep_mst_backup', 'elint_backup', 'en_activity_backup', 
                  'imint_data_backup', 'tac_int_backup']
        
        for table in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM backup.{table}")
                count = cur.fetchone()[0]
                print(f"{table:30} : {count:,} records")
            except Exception as e:
                print(f"{table:30} : NOT FOUND - {e}")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error connecting to database: {e}")
