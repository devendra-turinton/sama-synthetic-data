import os
import json
import logging
import psycopg2
from typing import Dict, List, Any

from config import DB_CONFIG, OUTPUT_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manage database operations for SAMA data"""
    
    def __init__(self, config: Dict[str, Any] = DB_CONFIG):
        self.config = config
    
    def get_connection(self):
        """Get a connection to the PostgreSQL database"""
        try:
            conn = psycopg2.connect(**self.config)
            return conn
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}")
            raise
    
    def execute_script(self, script_path: str):
        """Execute a SQL script file"""
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
    
    def export_to_sql(self, table: str, data_records: List[Dict[str, Any]], 
                     output_file: str, batch_size: int = 100):
        """Export data to SQL INSERT statements file with batching"""
        
        if not data_records:
            logger.warning(f"No data records to export for table {table}")
            return
        
        try:
            # Enhanced field mapping
            field_mappings = {
                "elint": {
                    "Date": "observation_date",
                    "date": "observation_date",
                    "long": "longitude",
                    "lat": "latitude",
                    "ht": "height",
                    "e": "easting",
                    "n": "northing",
                    "en": "enemy_unit",
                    "location": "location_name",
                    "range": "range_km",
                    "level": "hierarchy_level"
                },
                "imint_data": {
                    "Date": "observation_date",
                    "time": "observation_time",
                    "pre": "precedence",
                    "Incident_type": "incident_type",
                    "Incident_sub_type": "incident_sub_type",
                    "Incident_cl": "incident_cl",
                    "long": "longitude",
                    "lat": "latitude",
                    "ht": "height",
                    "e": "easting",
                    "n": "northing",
                    "input": "input_method",
                    "level": "hierarchy_level",
                    "str": "strength"
                },
                "tac_int": {
                    "Date": "observation_date",
                    "time": "observation_time",
                    "pre": "precedence",
                    "Incident_type": "incident_type",
                    "Incident_sub_type": "incident_sub_type",
                    "Incident_cl": "incident_cl",
                    "long": "longitude",
                    "lat": "latitude",
                    "ht": "height",
                    "e": "easting",
                    "n": "northing",
                    "input": "input_method",
                    "level": "hierarchy_level",
                    "str": "strength"
                },
                "en_activity": {
                    "bearing": "bearing",
                    "range_km": "range_km",
                    "long": "longitude",
                    "lat": "latitude",
                    "ht": "height",
                    "e": "easting",
                    "n": "northing",
                    "input_method": "input_method",
                    "level": "hierarchy_level",
                    "strength": "strength"
                },
                "e_sitrep_mst": {
                    "Incident_date": "incident_date",
                    "time": "incident_time",
                    "pre": "precedence",
                    "Incident_type": "incident_type",
                    "Incident_sub_type": "incident_sub_type",
                    "Incident_cl": "incident_cl",
                    "Incident_states": "incident_status",
                    "long": "longitude",
                    "lat": "latitude",
                    "ht": "height",
                    "e": "easting",
                    "n": "northing",
                    "level": "hierarchy_level"
                }
            }
            
            mapping = field_mappings.get(table, {})
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"-- INSERT statements for table {table}\n")
                f.write(f"-- Generated: {os.path.basename(output_file)}\n")
                f.write(f"-- Total records: {len(data_records)}\n")
                f.write(f"-- Date: {json.dumps(data_records[0].get('date') or data_records[0].get('Date') or data_records[0].get('Incident_date') or 'N/A')}\n\n")
                
                # Process in batches
                for batch_start in range(0, len(data_records), batch_size):
                    batch_records = data_records[batch_start:batch_start + batch_size]
                    
                    for record in batch_records:
                        # Map field names
                        mapped_record = {}
                        for key, value in record.items():
                            db_column = mapping.get(key, key)
                            
                            # Skip non-database fields
                            if db_column in ['correlation_id', 'confidence_level', 'sources_corroborated', 
                                           'day_number', 'significance', 'observable_by', 'event_type']:
                                continue
                            
                            mapped_record[db_column] = value
                        
                        columns = list(mapped_record.keys())
                        values = []
                        
                        for value in mapped_record.values():
                            if value is None or value == "":
                                values.append("NULL")
                            elif isinstance(value, bool):
                                values.append("TRUE" if value else "FALSE")
                            elif isinstance(value, (int, float)):
                                values.append(str(value))
                            else:
                                # Escape single quotes and handle special characters
                                value_str = str(value).replace("'", "''").replace("\\", "\\\\")
                                # Truncate very long descriptions
                                if len(value_str) > 5000:
                                    value_str = value_str[:5000] + "..."
                                values.append(f"'{value_str}'")
                        
                        insert_statement = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(values)});\n"
                        f.write(insert_statement)
                    
                    f.write(f"\n-- Batch {batch_start // batch_size + 1} complete\n\n")
                
                f.write(f"\n-- End of {table} inserts\n")
            
            logger.info(f"✓ Exported {len(data_records)} records to {output_file}")
            
        except Exception as e:
            logger.error(f"Error exporting data to {output_file}: {str(e)}", exc_info=True)
            raise