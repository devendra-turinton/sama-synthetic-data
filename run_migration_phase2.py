"""Run only Phase 2: Data Migration"""
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
MIGRATE_SQL = os.path.join(SQL_DIR, "04_migrate_data_final.sql")

print("="*80)
print("PHASE 2: Data Migration")
print("="*80)
print(f"Database: {DB_NAME}@{DB_HOST}")
print(f"User: {DB_USER}\n")

env = os.environ.copy()
if DB_PASSWORD:
    env['PGPASSWORD'] = DB_PASSWORD

cmd = [
    PSQL_PATH,
    "-h", DB_HOST,
    "-p", DB_PORT,
    "-U", DB_USER,
    "-d", DB_NAME,
    "-f", MIGRATE_SQL,
    "-v", "ON_ERROR_STOP=1"
]

try:
    result = subprocess.run(
        cmd,
        env=env,
        capture_output=True,
        text=True,
        check=True
    )
    
    print("SUCCESS - Data migration completed!")
    if result.stdout:
        print("\nOutput:")
        print(result.stdout)
    
except subprocess.CalledProcessError as e:
    print("FAILED - Data migration encountered errors")
    if e.stdout:
        print(f"\nOutput:\n{e.stdout}")
    if e.stderr:
        print(f"\nError details:\n{e.stderr}")
    sys.exit(1)
