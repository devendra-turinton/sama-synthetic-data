"""Fix elint table and retry migration"""
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

# Step 1: Fix elint table
print("="*80)
print("Step 1: Fixing elint table constraint...")
print("="*80)

cmd = [
    PSQL_PATH, "-h", DB_HOST, "-p", DB_PORT, "-U", DB_USER, "-d", DB_NAME,
    "-f", os.path.join(SQL_DIR, "fix_elint_table.sql"),
    "-v", "ON_ERROR_STOP=1"
]

try:
    result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
    print("SUCCESS - elint table recreated\n")
except subprocess.CalledProcessError as e:
    print(f"FAILED: {e.stderr}")
    sys.exit(1)

# Step 2: Re-run data migration
print("="*80)
print("Step 2: Re-running data migration...")
print("="*80)

cmd = [
    PSQL_PATH, "-h", DB_HOST, "-p", DB_PORT, "-U", DB_USER, "-d", DB_NAME,
    "-f", os.path.join(SQL_DIR, "04_migrate_data_final.sql"),
    "-v", "ON_ERROR_STOP=1"
]

try:
    result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
    print("SUCCESS - Data migration completed!\n")
    if result.stdout:
        # Only show summary lines
        lines = result.stdout.split('\n')
        for line in lines:
            if 'INSERT' in line:
                print(line)
except subprocess.CalledProcessError as e:
    print(f"FAILED: {e.stderr}")
    sys.exit(1)

print("\n" + "="*80)
print("Migration completed! Running validation...")
print("="*80 + "\n")

# Step 3: Validate
cmd = [
    PSQL_PATH, "-h", DB_HOST, "-p", DB_PORT, "-U", DB_USER, "-d", DB_NAME,
    "-f", os.path.join(SQL_DIR, "05_validation.sql")
]

subprocess.run(cmd, env=env)
