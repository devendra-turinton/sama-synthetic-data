#!/usr/bin/env python3
"""
Multi-Database Manager for SAMA Intelligence Databases
Provides management utilities for the 5 separate intelligence databases

Capabilities:
- Database status checking
- Data verification and statistics
- Cross-database queries
- Database cleanup and maintenance
- Connection testing
"""

import os
import sys
import json
import logging
import psycopg2
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DB_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configurations
DATABASE_CONFIGS = {
    "elint": {
        "db_name": "elint_intelligence_db",
        "description": "Electronic Intelligence Database",
        "primary_table": "elint",
        "color": "🟦"  # Blue
    },
    "imint": {
        "db_name": "imint_intelligence_db", 
        "description": "Imagery Intelligence Database",
        "primary_table": "imint_data",
        "color": "🟩"  # Green
    },
    "tacint": {
        "db_name": "tacint_intelligence_db",
        "description": "Tactical Intelligence Database", 
        "primary_table": "tac_int",
        "color": "🟨"  # Yellow
    },
    "enemy_activity": {
        "db_name": "enemy_activity_db",
        "description": "Enemy Activity Analysis Database",
        "primary_table": "en_activity",
        "color": "🟥"  # Red
    },
    "sitrep": {
        "db_name": "sitrep_intelligence_db",
        "description": "Situation Reports Database",
        "primary_table": "e_sitrep_mst",
        "color": "🟪"  # Purple
    }
}

class DatabaseManager:
    """Manager for multiple intelligence databases"""
    
    def __init__(self, base_config: Dict[str, str] = None):
        self.base_config = base_config or DB_CONFIG.copy()
        
    def check_all_databases_status(self):
        """Check status of all intelligence databases"""
        logger.info("="*80)
        logger.info("🔍 INTELLIGENCE DATABASES STATUS CHECK")
        logger.info("="*80)
        logger.info(f"🏠 Host: {self.base_config['host']}")
        logger.info(f"👤 User: {self.base_config['user']}")
        logger.info("="*80)
        
        status_results = {}
        
        for db_type, config in DATABASE_CONFIGS.items():
            logger.info(f"\n{config['color']} {config['description']}")
            logger.info(f"   Database: {config['db_name']}")
            
            try:
                status = self._check_database_status(config['db_name'], config['primary_table'])
                status_results[db_type] = status
                
                if status['accessible']:
                    logger.info(f"   Status: ✅ ONLINE")
                    logger.info(f"   Size: {status['size']}")
                    logger.info(f"   Tables: {status['table_count']}")
                    logger.info(f"   Records: {status['record_count']:,}")
                    logger.info(f"   Latest Record: {status['latest_record']}")
                else:
                    logger.error(f"   Status: ❌ OFFLINE - {status['error']}")
                    
            except Exception as e:
                logger.error(f"   Status: 💥 ERROR - {str(e)}")
                status_results[db_type] = {"accessible": False, "error": str(e)}
        
        # Summary
        online_count = sum(1 for s in status_results.values() if s.get('accessible', False))
        total_records = sum(s.get('record_count', 0) for s in status_results.values())
        
        logger.info("\n" + "="*80)
        logger.info("📊 SUMMARY")
        logger.info("="*80)
        logger.info(f"Online Databases: {online_count}/{len(DATABASE_CONFIGS)}")
        logger.info(f"Total Records: {total_records:,}")
        
        if online_count == len(DATABASE_CONFIGS):
            logger.info("🎉 ALL DATABASES ARE ONLINE!")
        else:
            logger.warning(f"⚠️  {len(DATABASE_CONFIGS) - online_count} database(s) offline")
            
        logger.info("="*80)
        
        return status_results
    
    def _check_database_status(self, db_name: str, primary_table: str) -> Dict[str, Any]:
        """Check status of a single database"""
        try:
            # Connect to database
            db_config = self.base_config.copy()
            db_config['database'] = db_name
            
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            
            # Get database size
            cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
            size = cursor.fetchone()[0]
            
            # Get table count
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """)
            table_count = cursor.fetchone()[0]
            
            # Get record count from primary table
            cursor.execute(f"SELECT COUNT(*) FROM {primary_table}")
            record_count = cursor.fetchone()[0]
            
            # Get latest record (try different date columns)
            latest_record = "N/A"
            date_columns = ["observation_date", "incident_date", "created_at", "upload_time"]
            
            for date_col in date_columns:
                try:
                    cursor.execute(f"""
                        SELECT {date_col} FROM {primary_table} 
                        WHERE {date_col} IS NOT NULL 
                        ORDER BY {date_col} DESC 
                        LIMIT 1
                    """)
                    result = cursor.fetchone()
                    if result:
                        latest_record = str(result[0])
                        break
                except:
                    continue
            
            cursor.close()
            conn.close()
            
            return {
                "accessible": True,
                "size": size,
                "table_count": table_count,
                "record_count": record_count,
                "latest_record": latest_record
            }
            
        except Exception as e:
            return {
                "accessible": False,
                "error": str(e)
            }
    
    def get_cross_database_statistics(self):
        """Get statistics across all databases"""
        logger.info("="*80)
        logger.info("📈 CROSS-DATABASE ANALYTICS")
        logger.info("="*80)
        
        stats = {}
        total_records = 0
        
        for db_type, config in DATABASE_CONFIGS.items():
            try:
                db_stats = self._get_database_statistics(config['db_name'], config['primary_table'])
                stats[db_type] = db_stats
                total_records += db_stats.get('record_count', 0)
                
                logger.info(f"\n{config['color']} {config['description']}")
                logger.info(f"   Records: {db_stats.get('record_count', 0):,}")
                logger.info(f"   Date Range: {db_stats.get('date_range', 'N/A')}")
                logger.info(f"   Locations: {db_stats.get('unique_locations', 0):,}")
                logger.info(f"   Units: {db_stats.get('unique_units', 0):,}")
                
            except Exception as e:
                logger.error(f"   Error getting stats for {config['db_name']}: {str(e)}")
                stats[db_type] = {"error": str(e)}
        
        # Cross-database insights
        logger.info("\n📊 INSIGHTS:")
        logger.info(f"   Total Intelligence Records: {total_records:,}")
        
        # Calculate coverage by source
        coverage_stats = {}
        for db_type, db_stats in stats.items():
            if 'record_count' in db_stats and db_stats['record_count'] > 0:
                coverage_stats[db_type] = db_stats['record_count']
        
        if coverage_stats:
            logger.info("   Coverage by Source:")
            for source, count in sorted(coverage_stats.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_records) * 100 if total_records > 0 else 0
                logger.info(f"     {source.upper():<15}: {count:>6,} records ({percentage:5.1f}%)")
        
        logger.info("="*80)
        
        return stats
    
    def _get_database_statistics(self, db_name: str, primary_table: str) -> Dict[str, Any]:
        """Get detailed statistics for a database"""
        try:
            db_config = self.base_config.copy()
            db_config['database'] = db_name
            
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            
            stats = {}
            
            # Record count
            cursor.execute(f"SELECT COUNT(*) FROM {primary_table}")
            stats['record_count'] = cursor.fetchone()[0]
            
            # Date range (try multiple date columns)
            date_columns = ["observation_date", "incident_date"]
            for date_col in date_columns:
                try:
                    cursor.execute(f"""
                        SELECT MIN({date_col}), MAX({date_col}) 
                        FROM {primary_table} 
                        WHERE {date_col} IS NOT NULL
                    """)
                    min_date, max_date = cursor.fetchone()
                    if min_date and max_date:
                        stats['date_range'] = f"{min_date} to {max_date}"
                        break
                except:
                    continue
            
            # Unique locations
            try:
                cursor.execute(f"""
                    SELECT COUNT(DISTINCT CONCAT(ROUND(longitude::numeric, 4), ',', ROUND(latitude::numeric, 4)))
                    FROM {primary_table} 
                    WHERE longitude IS NOT NULL AND latitude IS NOT NULL
                """)
                stats['unique_locations'] = cursor.fetchone()[0]
            except:
                stats['unique_locations'] = 0
            
            # Unique units
            try:
                cursor.execute(f"""
                    SELECT COUNT(DISTINCT unit_name) 
                    FROM {primary_table} 
                    WHERE unit_name IS NOT NULL
                """)
                stats['unique_units'] = cursor.fetchone()[0]
            except:
                stats['unique_units'] = 0
            
            cursor.close()
            conn.close()
            
            return stats
            
        except Exception as e:
            raise Exception(f"Failed to get statistics for {db_name}: {str(e)}")
    
    def test_all_connections(self):
        """Test connections to all databases"""
        logger.info("="*80)
        logger.info("🔌 CONNECTION TESTING")
        logger.info("="*80)
        
        connection_results = {}
        
        for db_type, config in DATABASE_CONFIGS.items():
            logger.info(f"\n{config['color']} Testing {config['description']}...")
            
            try:
                start_time = datetime.now()
                
                db_config = self.base_config.copy()
                db_config['database'] = config['db_name']
                
                conn = psycopg2.connect(**db_config)
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                conn.close()
                
                end_time = datetime.now()
                connection_time = (end_time - start_time).total_seconds() * 1000
                
                logger.info(f"   ✅ Connected successfully ({connection_time:.2f}ms)")
                connection_results[db_type] = {
                    "success": True,
                    "response_time_ms": connection_time
                }
                
            except Exception as e:
                logger.error(f"   ❌ Connection failed: {str(e)}")
                connection_results[db_type] = {
                    "success": False,
                    "error": str(e)
                }
        
        # Summary
        successful_connections = sum(1 for r in connection_results.values() if r.get('success', False))
        avg_response_time = sum(r.get('response_time_ms', 0) for r in connection_results.values() if r.get('success', False))
        
        if successful_connections > 0:
            avg_response_time /= successful_connections
        
        logger.info(f"\n📊 Connection Summary:")
        logger.info(f"   Successful: {successful_connections}/{len(DATABASE_CONFIGS)}")
        if successful_connections > 0:
            logger.info(f"   Avg Response: {avg_response_time:.2f}ms")
        
        logger.info("="*80)
        
        return connection_results
    
    def cleanup_databases(self, confirm: bool = False):
        """Clean up (drop) all intelligence databases"""
        if not confirm:
            logger.warning("⚠️  This will DELETE all intelligence databases!")
            logger.warning("⚠️  Use cleanup_databases(confirm=True) to proceed")
            return False
        
        logger.info("="*80)
        logger.info("🗑️  DATABASE CLEANUP (DELETION)")
        logger.info("="*80)
        logger.warning("⚠️  PROCEEDING WITH DATABASE DELETION!")
        
        try:
            admin_config = self.base_config.copy()
            admin_config['database'] = 'postgres'
            
            conn = psycopg2.connect(**admin_config)
            conn.autocommit = True
            cursor = conn.cursor()
            
            deleted_count = 0
            
            for db_type, config in DATABASE_CONFIGS.items():
                try:
                    logger.info(f"\n🗑️  Dropping {config['db_name']}...")
                    cursor.execute(f"DROP DATABASE IF EXISTS {config['db_name']}")
                    logger.info(f"   ✅ Deleted successfully")
                    deleted_count += 1
                    
                except Exception as e:
                    logger.error(f"   ❌ Failed to delete: {str(e)}")
            
            cursor.close()
            conn.close()
            
            logger.info(f"\n📊 Cleanup Summary: {deleted_count}/{len(DATABASE_CONFIGS)} databases deleted")
            logger.info("="*80)
            
            return deleted_count == len(DATABASE_CONFIGS)
            
        except Exception as e:
            logger.error(f"💥 Cleanup failed: {str(e)}")
            return False
    
    def export_database_info(self, output_file: str = None):
        """Export database information to JSON"""
        if not output_file:
            output_file = f"intelligence_databases_info_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        logger.info(f"📄 Exporting database information to: {output_file}")
        
        try:
            # Collect all information
            info = {
                "export_timestamp": datetime.now().isoformat(),
                "host_info": {
                    "host": self.base_config['host'],
                    "port": self.base_config['port'],
                    "user": self.base_config['user']
                },
                "databases": {}
            }
            
            for db_type, config in DATABASE_CONFIGS.items():
                try:
                    status = self._check_database_status(config['db_name'], config['primary_table'])
                    stats = self._get_database_statistics(config['db_name'], config['primary_table']) if status['accessible'] else {}
                    
                    info["databases"][db_type] = {
                        "config": config,
                        "status": status,
                        "statistics": stats
                    }
                    
                except Exception as e:
                    info["databases"][db_type] = {
                        "config": config,
                        "error": str(e)
                    }
            
            # Write to file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(info, f, indent=2, default=str)
            
            logger.info(f"✅ Database information exported successfully")
            return output_file
            
        except Exception as e:
            logger.error(f"❌ Failed to export database info: {str(e)}")
            return None


def main():
    """Main execution with interactive menu"""
    
    manager = DatabaseManager()
    
    while True:
        print("\n" + "="*60)
        print("🎛️  SAMA INTELLIGENCE DATABASE MANAGER")
        print("="*60)
        print("1. 📊 Check Database Status")
        print("2. 📈 Get Cross-Database Statistics") 
        print("3. 🔌 Test All Connections")
        print("4. 📄 Export Database Info")
        print("5. 🗑️  Cleanup Databases (DANGER!)")
        print("6. 🚪 Exit")
        print("="*60)
        
        try:
            choice = input("Select option (1-6): ").strip()
            
            if choice == '1':
                manager.check_all_databases_status()
            
            elif choice == '2':
                manager.get_cross_database_statistics()
            
            elif choice == '3':
                manager.test_all_connections()
            
            elif choice == '4':
                output_file = manager.export_database_info()
                if output_file:
                    print(f"📁 Info exported to: {output_file}")
            
            elif choice == '5':
                confirm = input("⚠️  Type 'DELETE' to confirm database deletion: ").strip()
                if confirm == 'DELETE':
                    manager.cleanup_databases(confirm=True)
                else:
                    print("❌ Deletion cancelled")
            
            elif choice == '6':
                print("👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid choice. Please select 1-6.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"💥 Error: {str(e)}")


if __name__ == "__main__":
    main()