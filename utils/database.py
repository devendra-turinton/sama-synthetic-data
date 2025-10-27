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
    
    def export_to_sql(self, table: str, data_records: List[Dict[str, Any]], output_file: str):
        """Export data to SQL INSERT statements file"""
        if not data_records:
            logger.warning(f"No data records to export for table {table}")
            return
        
        try:
            # Field mapping for database column names
            field_mappings = {
                "elint": {
                    "Date": "date",
                    "date": "observation_date"
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
                    "level": "hierarchy_level"
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
                    "bg": "bearing",
                    "rg": "range_km",
                    "long": "longitude",
                    "lat": "latitude",
                    "ht": "height",
                    "e": "easting",
                    "n": "northing",
                    "input": "input_method",
                    "level": "hierarchy_level",
                    "str": "strength"
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
                f.write(f"-- Total records: {len(data_records)}\n\n")
                
                for record in data_records:
                    # Map field names
                    mapped_record = {}
                    for key, value in record.items():
                        db_column = mapping.get(key, key)
                        # Skip non-database fields
                        if db_column in ['correlation_id', 'confidence_level', 'sources_corroborated']:
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
                            # Truncate very long descriptions for SQL
                            if len(value_str) > 5000:
                                value_str = value_str[:5000] + "..."
                            values.append(f"'{value_str}'")
                    
                    insert_statement = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(values)});\n"
                    f.write(insert_statement)
                
                f.write(f"\n-- End of {table} inserts\n")
            
            logger.info(f"Successfully exported {len(data_records)} records to {output_file}")
        except Exception as e:
            logger.error(f"Error exporting data to {output_file}: {str(e)}")
            raise
    
    def validate_data_integrity(self, data_dict: Dict[str, List]) -> Dict[str, Any]:
        """Validate generated data for consistency and integrity"""
        validation_report = {
            "errors": [],
            "warnings": [],
            "stats": {}
        }
        
        try:
            # Check for correlation consistency
            elint_data = data_dict.get("elint", [])
            imint_data = data_dict.get("imint", [])
            tacint_data = data_dict.get("tacint", [])
            enemy_activity = data_dict.get("enemy_activity", [])
            
            # Collect all correlation IDs
            elint_corr_ids = set(r.get("correlation_id") for r in elint_data if r.get("correlation_id"))
            imint_corr_ids = set(r.get("correlation_id") for r in imint_data if r.get("correlation_id"))
            tacint_corr_ids = set(r.get("correlation_id") for r in tacint_data if r.get("correlation_id"))
            enemy_corr_ids = set(r.get("correlation_id") for r in enemy_activity if r.get("correlation_id"))
            
            all_corr_ids = elint_corr_ids | imint_corr_ids | tacint_corr_ids
            
            # Check if enemy activities reference valid correlations
            orphaned_enemy_activities = enemy_corr_ids - all_corr_ids
            if orphaned_enemy_activities:
                validation_report["warnings"].append(
                    f"Found {len(orphaned_enemy_activities)} enemy activity records with invalid correlation IDs"
                )
            
            # Check for formation code validity (should be 10 chars)
            for table_name, records in data_dict.items():
                invalid_fmn_codes = [
                    r.get("id") for r in records 
                    if r.get("fmn_code") and len(str(r.get("fmn_code"))) != 10
                ]
                if invalid_fmn_codes:
                    validation_report["errors"].append(
                        f"{table_name}: {len(invalid_fmn_codes)} records with invalid formation codes"
                    )
            
            # Statistics
            validation_report["stats"] = {
                "total_correlation_groups": len(all_corr_ids),
                "elint_records": len(elint_data),
                "imint_records": len(imint_data),
                "tacint_records": len(tacint_data),
                "enemy_activity_records": len(enemy_activity),
                "sitrep_records": len(data_dict.get("sitrep", [])),
                "correlation_coverage": {
                    "elint": len(elint_corr_ids),
                    "imint": len(imint_corr_ids),
                    "tacint": len(tacint_corr_ids),
                    "enemy_activity": len(enemy_corr_ids)
                }
            }
            
            logger.info("Data validation complete")
            
        except Exception as e:
            validation_report["errors"].append(f"Validation error: {str(e)}")
        
        return validation_report