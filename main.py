# import os
# import logging
# import argparse

# from config import OUTPUT_DIR, KARGIL_SCENARIO
# from generators.scenario_generator import KargilScenarioGenerator
# from generators.reference_data_generator import ReferenceDataGenerator
# from generators.elint_generator import ElintGenerator
# from generators.imint_generator import ImintGenerator
# from generators.tacint_generator import TacintGenerator
# from generators.enemy_activity_generator import EnemyActivityGenerator
# from generators.sitrep_generator import SitrepGenerator
# from utils.database import DatabaseManager

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler(os.path.join(OUTPUT_DIR, 'generation.log')),
#         logging.StreamHandler()
#     ]
# )
# logger = logging.getLogger(__name__)

# def generate_kargil_data():
#     """Generate complete Kargil War synthetic intelligence data"""
    
#     logger.info("="*80)
#     logger.info("KARGIL WAR DATA GENERATION - STARTING")
#     logger.info("="*80)
    
#     # Create output directory
#     os.makedirs(OUTPUT_DIR, exist_ok=True)
    
#     # Initialize generators
#     logger.info("Initializing generators...")
#     scenario_generator = KargilScenarioGenerator()
#     reference_generator = ReferenceDataGenerator()
#     elint_generator = ElintGenerator()
#     imint_generator = ImintGenerator()
#     tacint_generator = TacintGenerator()
#     enemy_activity_generator = EnemyActivityGenerator()
#     sitrep_generator = SitrepGenerator()
#     db_manager = DatabaseManager()
    
#     try:
#         # Step 1: Generate reference data (taxonomies)
#         logger.info("\n" + "="*80)
#         logger.info("STEP 1: Generating Reference Data (Taxonomies)")
#         logger.info("="*80)
#         reference_data = reference_generator.generate_all_reference_data()
#         logger.info("✓ Reference data generation complete")
        
#         # Step 2: Generate Kargil scenario timeline
#         logger.info("\n" + "="*80)
#         logger.info("STEP 2: Generating Kargil War Scenario Timeline")
#         logger.info("="*80)
#         logger.info("Timeline: May 1, 1999 - July 31, 1999 (92 days)")
#         logger.info("Frequency: 6 events per day (every 4 hours)")
#         scenario = scenario_generator.generate_complete_timeline()
#         logger.info(f"✓ Scenario timeline complete: {scenario['total_events']} events generated")
        
#         # Step 3: Generate ELINT data (with correlation)
#         logger.info("\n" + "="*80)
#         logger.info("STEP 3: Generating ELINT Data (Electronic Intelligence)")
#         logger.info("="*80)
#         elint_data = elint_generator.generate_elint_data(scenario, reference_data)
#         logger.info(f"✓ ELINT generation complete: {len(elint_data)} records")
        
#         # Step 4: Generate IMINT data (with correlation)
#         logger.info("\n" + "="*80)
#         logger.info("STEP 4: Generating IMINT Data (Imagery Intelligence)")
#         logger.info("="*80)
#         imint_data = imint_generator.generate_imint_data(scenario, reference_data)
#         logger.info(f"✓ IMINT generation complete: {len(imint_data)} records")
        
#         # Step 5: Generate TACINT data (with correlation)
#         logger.info("\n" + "="*80)
#         logger.info("STEP 5: Generating TACINT Data (Tactical Intelligence)")
#         logger.info("="*80)
#         tacint_data = tacint_generator.generate_tacint_data(scenario, reference_data)
#         logger.info(f"✓ TACINT generation complete: {len(tacint_data)} records")
        
#         # Step 6: Generate Enemy Activity (fusion)
#         logger.info("\n" + "="*80)
#         logger.info("STEP 6: Generating Enemy Activity Data (Intelligence Fusion)")
#         logger.info("="*80)
#         enemy_activity_data = enemy_activity_generator.generate_enemy_activity_data(
#             scenario, reference_data, elint_data, imint_data, tacint_data
#         )
#         logger.info(f"✓ Enemy Activity generation complete: {len(enemy_activity_data)} records")
        
#         # Step 7: Generate SITREP (strategic assessment)
#         logger.info("\n" + "="*80)
#         logger.info("STEP 7: Generating SITREP Data (Situation Reports)")
#         logger.info("="*80)
#         sitrep_data = sitrep_generator.generate_sitrep_data(
#             scenario, reference_data, enemy_activity_data
#         )
#         logger.info(f"✓ SITREP generation complete: {len(sitrep_data)} records")
        
#         # Step 8: Export to SQL
#         logger.info("\n" + "="*80)
#         logger.info("STEP 8: Exporting Data to SQL")
#         logger.info("="*80)
        
#         scenario_name = KARGIL_SCENARIO["name"]
        
#         # Export each table
#         tables_data = [
#             ("elint", elint_data),
#             ("imint_data", imint_data),
#             ("tac_int", tacint_data),
#             ("en_activity", enemy_activity_data),
#             ("e_sitrep_mst", sitrep_data)
#         ]
        
#         for table_name, data in tables_data:
#             if data:
#                 output_file = os.path.join(OUTPUT_DIR, f"{table_name}_{scenario_name}_inserts.sql")
#                 db_manager.export_to_sql(table_name, data, output_file)
#                 logger.info(f"✓ Exported {table_name}: {len(data)} records")
        
#         # Generate summary report
#         logger.info("\n" + "="*80)
#         logger.info("GENERATION SUMMARY")
#         logger.info("="*80)
#         logger.info(f"Scenario: {scenario['scenario_name']}")
#         logger.info(f"Date Range: {scenario['start_date']} to {scenario['end_date']}")
#         logger.info(f"Total Days: {scenario['total_days']}")
#         logger.info(f"Timeline Events: {scenario['total_events']}")
#         logger.info(f"ELINT Records: {len(elint_data)}")
#         logger.info(f"IMINT Records: {len(imint_data)}")
#         logger.info(f"TACINT Records: {len(tacint_data)}")
#         logger.info(f"Enemy Activity Records: {len(enemy_activity_data)}")
#         logger.info(f"SITREP Records: {len(sitrep_data)}")
#         logger.info(f"Total Intelligence Records: {len(elint_data) + len(imint_data) + len(tacint_data) + len(enemy_activity_data) + len(sitrep_data)}")
#         logger.info("="*80)
#         logger.info("✓ KARGIL WAR DATA GENERATION COMPLETE")
#         logger.info("="*80)
        
#         return {
#             "scenario": scenario,
#             "elint": elint_data,
#             "imint": imint_data,
#             "tacint": tacint_data,
#             "enemy_activity": enemy_activity_data,
#             "sitrep": sitrep_data
#         }
        
#     except Exception as e:
#         logger.error(f"✗ Error during data generation: {str(e)}", exc_info=True)
#         raise

# def main():
#     parser = argparse.ArgumentParser(
#         description='Generate synthetic intelligence data for Kargil War 1999'
#     )
#     parser.add_argument(
#         '--validate-only', 
#         action='store_true',
#         help='Only validate the generated data without regenerating'
#     )
    
#     args = parser.parse_args()
    
#     if args.validate_only:
#         logger.info("Validation mode - checking existing data...")
#         # TODO: Implement validation logic
#         logger.info("Validation complete")
#     else:
#         generate_kargil_data()

# if __name__ == "__main__":
#     main()

import os
import json
import logging

from config import OUTPUT_DIR, KARGIL_SCENARIO, TEST_MODE
from generators.scenario_generator import KargilScenarioGenerator
from generators.reference_data_generator import ReferenceDataGenerator
from generators.elint_generator import ElintGenerator
from generators.imint_generator import ImintGenerator
from generators.tacint_generator import TacintGenerator
from generators.enemy_activity_generator import EnemyActivityGenerator
from generators.sitrep_generator import SitrepGenerator
from utils.database import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(OUTPUT_DIR, 'generation.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def generate_kargil_data():
    """Generate Kargil War synthetic intelligence data"""
    
    mode_str = "TEST MODE (Single Day)" if TEST_MODE else "PRODUCTION MODE (Full 92 Days)"
    
    logger.info("="*80)
    logger.info(f"KARGIL WAR DATA GENERATION - {mode_str}")
    logger.info("="*80)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Initialize generators
    logger.info("Initializing generators...")
    scenario_generator = KargilScenarioGenerator()
    reference_generator = ReferenceDataGenerator()
    elint_generator = ElintGenerator()
    imint_generator = ImintGenerator()
    tacint_generator = TacintGenerator()
    enemy_activity_generator = EnemyActivityGenerator()
    sitrep_generator = SitrepGenerator()
    db_manager = DatabaseManager()
    
    try:
        # Step 1: Generate reference data (or load from cache)
        logger.info("\n" + "="*80)
        logger.info("STEP 1: Reference Data")
        logger.info("="*80)
        
        reference_data_path = os.path.join(OUTPUT_DIR, "reference_data_complete.json")
        if os.path.exists(reference_data_path):
            logger.info("Loading cached reference data...")
            with open(reference_data_path, 'r') as f:
                reference_data = json.load(f)
            logger.info("✓ Reference data loaded from cache")
        else:
            logger.info("Generating reference data...")
            try:
                reference_data = reference_generator.generate_all_reference_data()
                logger.info("✓ Reference data generation complete")
            except Exception as e:
                logger.error(f"Reference data generation failed after all JSON repair attempts: {str(e)}")
                logger.info("Using minimal fallback reference data...")
                reference_data = {
                    "activity_classification": {"activity_types": []},
                    "target_classification": {"target_types": []},
                    "incident_classification": {"incident_types": []}
                }
        
        # Step 2: Generate scenario timeline
        logger.info("\n" + "="*80)
        logger.info("STEP 2: Generating Scenario Timeline")
        logger.info("="*80)
        if TEST_MODE:
            logger.info("TEST MODE: Generating single day (June 15, 1999)")
            logger.info("Expected: 6 ground truth events")
        scenario = scenario_generator.generate_complete_timeline()
        logger.info(f"✓ Timeline complete: {scenario['total_events']} events")
        
        # Step 3: Generate ELINT
        logger.info("\n" + "="*80)
        logger.info("STEP 3: Generating ELINT Data")
        logger.info("="*80)
        elint_data = elint_generator.generate_elint_data(scenario, reference_data)
        logger.info(f"✓ ELINT complete: {len(elint_data)} records")
        
        # Step 4: Generate IMINT
        logger.info("\n" + "="*80)
        logger.info("STEP 4: Generating IMINT Data")
        logger.info("="*80)
        imint_data = imint_generator.generate_imint_data(scenario, reference_data)
        logger.info(f"✓ IMINT complete: {len(imint_data)} records")
        
        # Step 5: Generate TACINT
        logger.info("\n" + "="*80)
        logger.info("STEP 5: Generating TACINT Data")
        logger.info("="*80)
        tacint_data = tacint_generator.generate_tacint_data(scenario, reference_data)
        logger.info(f"✓ TACINT complete: {len(tacint_data)} records")
        
        # Step 6: Generate Enemy Activity (fusion)
        logger.info("\n" + "="*80)
        logger.info("STEP 6: Generating Enemy Activity (Fusion)")
        logger.info("="*80)
        enemy_activity_data = enemy_activity_generator.generate_enemy_activity_data(
            scenario, reference_data, elint_data, imint_data, tacint_data
        )
        logger.info(f"✓ Enemy Activity complete: {len(enemy_activity_data)} records")
        
        # Step 7: Generate SITREP
        logger.info("\n" + "="*80)
        logger.info("STEP 7: Generating SITREP Data")
        logger.info("="*80)
        sitrep_data = sitrep_generator.generate_sitrep_data(
            scenario, reference_data, enemy_activity_data
        )
        logger.info(f"✓ SITREP complete: {len(sitrep_data)} records")
        
        # Step 8: Export to SQL
        logger.info("\n" + "="*80)
        logger.info("STEP 8: Exporting to SQL")
        logger.info("="*80)
        
        scenario_name = KARGIL_SCENARIO["name"]
        tables_data = [
            ("elint", elint_data),
            ("imint_data", imint_data),
            ("tac_int", tacint_data),
            ("en_activity", enemy_activity_data),
            ("e_sitrep_mst", sitrep_data)
        ]
        
        for table_name, data in tables_data:
            if data:
                output_file = os.path.join(OUTPUT_DIR, f"{table_name}_{scenario_name}_inserts.sql")
                db_manager.export_to_sql(table_name, data, output_file)
                logger.info(f"✓ Exported {table_name}: {len(data)} records")
        
        # Generate summary
        logger.info("\n" + "="*80)
        logger.info("GENERATION SUMMARY")
        logger.info("="*80)
        logger.info(f"Mode: {mode_str}")
        logger.info(f"Scenario: {scenario['scenario_name']}")
        logger.info(f"Date Range: {scenario['start_date']} to {scenario['end_date']}")
        logger.info(f"Total Days: {scenario['total_days']}")
        logger.info(f"Timeline Events: {scenario['total_events']}")
        logger.info(f"ELINT Records: {len(elint_data)}")
        logger.info(f"IMINT Records: {len(imint_data)}")
        logger.info(f"TACINT Records: {len(tacint_data)}")
        logger.info(f"Enemy Activity Records: {len(enemy_activity_data)}")
        logger.info(f"SITREP Records: {len(sitrep_data)}")
        total_records = len(elint_data) + len(imint_data) + len(tacint_data) + len(enemy_activity_data) + len(sitrep_data)
        logger.info(f"Total Intelligence Records: {total_records}")
        
        if TEST_MODE:
            logger.info("\n" + "="*80)
            logger.info("TEST MODE VALIDATION")
            logger.info("="*80)
            logger.info("Expected for single day:")
            logger.info("  - Timeline: 6 ground truth events")
            logger.info("  - ELINT: ~4 records")
            logger.info("  - IMINT: ~5 records")
            logger.info("  - TACINT: ~6 records")
            logger.info("  - Enemy Activity: ~4 records")
            logger.info("  - SITREP: 1 record")
            logger.info("  - Total: ~20 records")
            logger.info(f"\nActual total: {total_records} records")
            
            # Validate correlation
            elint_corrs = set(r.get("correlation_id") for r in elint_data if r.get("correlation_id"))
            imint_corrs = set(r.get("correlation_id") for r in imint_data if r.get("correlation_id"))
            tacint_corrs = set(r.get("correlation_id") for r in tacint_data if r.get("correlation_id"))
            enemy_corrs = set(r.get("correlation_id") for r in enemy_activity_data if r.get("correlation_id"))
            
            logger.info(f"\nCorrelation IDs:")
            logger.info(f"  - ELINT: {len(elint_corrs)} unique IDs")
            logger.info(f"  - IMINT: {len(imint_corrs)} unique IDs")
            logger.info(f"  - TACINT: {len(tacint_corrs)} unique IDs")
            logger.info(f"  - Enemy Activity: {len(enemy_corrs)} unique IDs")
            
            if len(tacint_corrs) == 0 and len(tacint_data) > 0:
                logger.warning("TACINT has records but no correlation_ids! Checking first record...")
                if tacint_data:
                    sample = tacint_data[0]
                    logger.info(f"Sample TACINT record keys: {list(sample.keys())}")
                    logger.info(f"Sample correlation_id value: {sample.get('correlation_id', 'MISSING')}")
            
            # Check formation codes
            fmn_codes = set()
            for records in [elint_data, imint_data, tacint_data, enemy_activity_data, sitrep_data]:
                for r in records:
                    if r.get("fmn_code"):
                        fmn_codes.add(r.get("fmn_code"))
            
            logger.info(f"\nUnique Formation Codes: {len(fmn_codes)}")
            logger.info(f"Formation Codes: {fmn_codes}")
        
        logger.info("\n" + "="*80)
        logger.info("✓ DATA GENERATION COMPLETE")
        logger.info("="*80)
        
        if TEST_MODE:
            logger.info("\nNext steps:")
            logger.info("1. Review generated JSON files in data/output/")
            logger.info("2. Check correlation consistency")
            logger.info("3. Verify formation codes repeat correctly")
            logger.info("4. If validation passes, set TEST_MODE=False for full generation")
        
        return {
            "scenario": scenario,
            "elint": elint_data,
            "imint": imint_data,
            "tacint": tacint_data,
            "enemy_activity": enemy_activity_data,
            "sitrep": sitrep_data
        }
        
    except Exception as e:
        logger.error(f"✗ Error during generation: {str(e)}", exc_info=True)
        raise

def main():
    generate_kargil_data()

if __name__ == "__main__":
    main()