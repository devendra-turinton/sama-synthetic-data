"""Complete migration with all fixes"""
import os
import subprocess
import sys
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
PSQL_PATH = r"C:\Program Files\PostgreSQL\17\bin\psql.exe"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQL_DIR = os.path.join(BASE_DIR, "sql")

env = os.environ.copy()
if DB_PASSWORD:
    env['PGPASSWORD'] = DB_PASSWORD

print("="*80)
print("COMPLETE DATABASE MIGRATION")
print("="*80)
print(f"Database: {DB_NAME}@{DB_HOST}\n")

# Step 1: Fix all table schemas
print("Step 1: Recreating all tables with correct schema...")
cmd = [PSQL_PATH, "-h", DB_HOST, "-p", DB_PORT, "-U", DB_USER, "-d", DB_NAME,
       "-f", os.path.join(SQL_DIR, "fix_all_tables.sql"), "-v", "ON_ERROR_STOP=1"]

try:
    subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
    print("SUCCESS - All tables recreated\n")
except subprocess.CalledProcessError as e:
    print(f"FAILED: {e.stderr}")
    sys.exit(1)

# Step 2: Migrate data
print("Step 2: Migrating data from backup tables...")
cmd = [PSQL_PATH, "-h", DB_HOST, "-p", DB_PORT, "-U", DB_USER, "-d", DB_NAME,
       "-f", os.path.join(SQL_DIR, "04_migrate_data_final.sql"), "-v", "ON_ERROR_STOP=1"]

try:
    result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
    print("SUCCESS - Data migrated!\n")
    # Show INSERT counts
    for line in result.stdout.split('\n'):
        if 'INSERT' in line:
            print(f"  {line}")
except subprocess.CalledProcessError as e:
    print(f"FAILED: {e.stderr}")
    sys.exit(1)

# Step 3: Validate
print("\nStep 3: Validating migration...")
cmd = [PSQL_PATH, "-h", DB_HOST, "-p", DB_PORT, "-U", DB_USER, "-d", DB_NAME,
       "-c", "SELECT 'e_sitrep_mst' AS table_name, COUNT(*) FROM public.e_sitrep_mst UNION ALL SELECT 'elint', COUNT(*) FROM public.elint UNION ALL SELECT 'en_activity', COUNT(*) FROM public.en_activity UNION ALL SELECT 'imint_data', COUNT(*) FROM public.imint_data UNION ALL SELECT 'tac_int', COUNT(*) FROM public.tac_int;"]

result = subprocess.run(cmd, env=env, capture_output=True, text=True)
print(result.stdout)

print("="*80)
print("MIGRATION COMPLETED SUCCESSFULLY!")
print("="*80)
