"""Quick script to check if migration is complete"""
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
    
    # Check table counts
    print("\nTable Record Counts:")
    print("="*50)
    
    tables = ['e_sitrep_mst', 'elint', 'en_activity', 'imint_data', 'tac_int']
    for table in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM public.{table}")
            count = cur.fetchone()[0]
            print(f"{table:20} : {count:,} records")
        except Exception as e:
            print(f"{table:20} : NOT FOUND or ERROR")
    
    # Check data types
    print("\n\nSample Data Types (e_sitrep_mst):")
    print("="*50)
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'e_sitrep_mst' 
        AND table_schema = 'public'
        ORDER BY ordinal_position 
        LIMIT 10
    """)
    
    for row in cur.fetchall():
        print(f"{row[0]:25} : {row[1]}")
    
    cur.close()
    conn.close()
    print("\n\nMigration status check complete!")
    
except Exception as e:
    print(f"Error connecting to database: {e}")
