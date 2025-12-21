"""
Quick runner script for creating multiple intelligence databases
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from create_multi_databases import main

if __name__ == "__main__":
    print("🚀 Starting SAMA Multi-Database Creation Process...")
    print("This will create 5 separate intelligence databases on Azure PostgreSQL")
    print("=" * 80)
    
    success = main()
    
    if success:
        print("\n🎉 All databases created successfully!")
        print("Use 'python manage_intelligence_databases.py --status' to check database status")
    else:
        print("\n❌ Database creation failed. Check logs for details.")
        sys.exit(1)