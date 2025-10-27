import os
import json
import logging
import psycopg2
from typing import Dict, List, Any

from config import DB_CONFIG, OUTPUT_DIR

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manage database operations for SAMA data."""
    
    def __init__(self, config: Dict[str, Any] = DB_CONFIG):
        self.config = config
    
    def get_connection(self):
        """Get a connection to the PostgreSQL database."""
        try:
            conn = psycopg2.connect(**self.config)
            return conn
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}")
            raise
    
    def execute_script(self, script_path: str):
        """Execute a SQL script file."""
        try:
            with open(script_path, 'r') as f:
                script = f.read()
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(script)
            conn.commit()
            
            cursor.close()
            conn.close()
            
            logger.info(f"Successfully executed script: {script_path}")
        except Exception as e:
            logger.error(f"Error executing script {script_path}: {str(e)}")
            raise
    
    def export_to_sql(self, table: str, data_records: List[Dict[str, Any]], output_file: str):
        """Export data to SQL INSERT statements file."""
        if not data_records:
            logger.warning(f"No data records to export for table {table}")
            return
        
        try:
            with open(output_file, 'w') as f:
                f.write(f"-- INSERT statements for table {table}\n\n")
                
                for record in data_records:
                    columns = list(record.keys())
                    values = []
                    
                    for value in record.values():
                        if value is None:
                            values.append("NULL")
                        elif isinstance(value, (int, float)):
                            values.append(str(value))
                        else:
                            # Escape single quotes in string values
                            value_str = str(value).replace("'", "''")
                            values.append(f"'{value_str}'")
                    
                    insert_statement = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(values)});\n"
                    f.write(insert_statement)
            
            logger.info(f"Successfully exported {len(data_records)} records to {output_file}")
        except Exception as e:
            logger.error(f"Error exporting data to {output_file}: {str(e)}")
            raise
