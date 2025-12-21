#!/usr/bin/env python3
"""
Quick launcher for Multi-Database Creation
Simplified interface to create all 5 intelligence databases
"""

import os
import sys
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from multi_database_dumper import MultiDatabaseDumper
from multi_db_config import get_database_info_summary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main launcher function"""
    
    print("🚀 SAMA Intelligence Databases Creator")
    print("="*60)
    
    # Show configuration summary
    summary = get_database_info_summary()
    print(f"📊 Configuration Summary:")
    print(f"   Total Databases: {summary['total_databases']}")
    print(f"   Target Host: {summary['host_config']['host']}")
    print(f"   Database Types: {', '.join(summary['database_types'])}")
    print()
    
    # Show what will be created
    print("🎯 Databases to be created:")
    for db_type, info in summary['databases'].items():
        print(f"   • {info['name']} - {info['description']}")
    print()
    
    # Confirm with user
    confirm = input("Proceed with database creation? (yes/no): ").strip().lower()
    
    if confirm not in ['yes', 'y']:
        print("❌ Operation cancelled by user")
        return 1
    
    print("\n🔄 Starting database creation process...")
    
    try:
        # Create dumper and execute
        dumper = MultiDatabaseDumper()
        success_count, failures = dumper.create_all_databases()
        
        # Results
        if success_count == summary['total_databases']:
            print("\n🎉 SUCCESS: All databases created successfully!")
            print("\nNext steps:")
            print("1. Use database_manager.py to check status")
            print("2. Connect to individual databases for queries")
            print("3. Use the databases for intelligence analysis")
            return 0
        else:
            print(f"\n⚠️  PARTIAL SUCCESS: {success_count}/{summary['total_databases']} databases created")
            print("Check the logs above for details on failures")
            return 2
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation interrupted by user")
        return 130
        
    except Exception as e:
        logger.error(f"💥 Fatal error: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)