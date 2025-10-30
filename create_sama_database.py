import os
import re
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASSWORD')
OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'data/output')

def create_database():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname='postgres',
            user=DB_USER,
            password=DB_PASS
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
        exists = cursor.fetchone()
        if not exists:
            print(f"Creating database '{DB_NAME}'...")
            cursor.execute(f"CREATE DATABASE {DB_NAME}")
            print(f"✓ Database '{DB_NAME}' created.")
        else:
            print(f"Database '{DB_NAME}' already exists.")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error creating database: {e}")

def get_table_columns_from_sql(sql_file):
    with open(sql_file, 'r', encoding='utf-8') as f:
        for line in f:
            match = re.match(r"INSERT INTO ([^( ]+) \(([^)]+)\)", line)
            if match:
                table = match.group(1)
                columns = [col.strip() for col in match.group(2).split(',')]
                return table, columns
    return None, None

def create_tables_from_sql_files(conn, sql_files):
    cursor = conn.cursor()
    for sql_file in sql_files:
        file_path = os.path.join(OUTPUT_DIR, sql_file)
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue
        table, columns = get_table_columns_from_sql(file_path)
        if table and columns:
            print(f"Creating table {table} with columns: {columns}")
            cursor.execute(f'DROP TABLE IF EXISTS {table} CASCADE;')
            col_defs = ', '.join([f'"{col}" TEXT' for col in columns])
            cursor.execute(f'CREATE TABLE {table} ({col_defs});')
        else:
            print(f"Could not parse columns for {sql_file}")
    cursor.close()
    print("All tables dropped and recreated.")

def execute_sql_file(cursor, file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        sql = f.read()
        cursor.execute(sql)

def import_sql_files(conn, sql_files):
    cursor = conn.cursor()
    for sql_file in sql_files:
        file_path = os.path.join(OUTPUT_DIR, sql_file)
        if os.path.exists(file_path):
            print(f"Executing {file_path}...")
            try:
                execute_sql_file(cursor, file_path)
                print(f"✓ Executed {sql_file}")
            except Exception as e:
                print(f"✗ Error executing {sql_file}: {e}")
        else:
            print(f"File not found: {file_path}")
    cursor.close()
    print("All SQL files processed.")

def main():
    # Find all .sql files in the output directory
    sql_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.sql')]
    create_database()
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    conn.autocommit = True
    create_tables_from_sql_files(conn, sql_files)
    import_sql_files(conn, sql_files)
    conn.close()

if __name__ == "__main__":
    main()