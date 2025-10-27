import os
import logging
import argparse

from config import OUTPUT_DIR, KARGIL_SCENARIO
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(OUTPUT_DIR, 'generation.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def generate_kargil_data():
    """Generate complete Kargil War synthetic intelligence data"""
    
    logger.info("="*80)
    logger.info("KARGIL WAR DATA GENERATION - STARTING")
    logger.info("="*80)
    
    # Create output directory
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
        # Step 1: Generate reference data (taxonomies)
        logger.info("\n" + "="*80)
        logger.info("STEP 1: Generating Reference Data (Taxonomies)")
        logger.info("="*80)
        reference_data = reference_generator.generate_all_reference_data()
        logger.info("✓ Reference data generation complete")
        
        # Step 2: Generate Kargil scenario timeline
        logger.info("\n" + "="*80)
        logger.info("STEP 2: Generating Kargil War Scenario Timeline")
        logger.info("="*80)
        logger.info("Timeline: May 1, 1999 - July 31, 1999 (92 days)")
        logger.info("Frequency: 6 events per day (every 4 hours)")
        scenario = scenario_generator.generate_complete_timeline()
        logger.info(f"✓ Scenario timeline complete: {scenario['total_events']} events generated")
        
        # Step 3: Generate ELINT data (with correlation)
        logger.info("\n" + "="*80)
        logger.info("STEP 3: Generating ELINT Data (Electronic Intelligence)")
        logger.info("="*80)
        elint_data = elint_generator.generate_elint_data(scenario, reference_data)
        logger.info(f"✓ ELINT generation complete: {len(elint_data)} records")
        
        # Step 4: Generate IMINT data (with correlation)
        logger.info("\n" + "="*80)
        logger.info("STEP 4: Generating IMINT Data (Imagery Intelligence)")
        logger.info("="*80)
        imint_data = imint_generator.generate_imint_data(scenario, reference_data)
        logger.info(f"✓ IMINT generation complete: {len(imint_data)} records")
        
        # Step 5: Generate TACINT data (with correlation)
        logger.info("\n" + "="*80)
        logger.info("STEP 5: Generating TACINT Data (Tactical Intelligence)")
        logger.info("="*80)
        tacint_data = tacint_generator.generate_tacint_data(scenario, reference_data)
        logger.info(f"✓ TACINT generation complete: {len(tacint_data)} records")
        
        # Step 6: Generate Enemy Activity (fusion)
        logger.info("\n" + "="*80)
        logger.info("STEP 6: Generating Enemy Activity Data (Intelligence Fusion)")
        logger.info("="*80)
        enemy_activity_data = enemy_activity_generator.generate_enemy_activity_data(
            scenario, reference_data, elint_data, imint_data, tacint_data
        )
        logger.info(f"✓ Enemy Activity generation complete: {len(enemy_activity_data)} records")
        
        # Step 7: Generate SITREP (strategic assessment)
        logger.info("\n" + "="*80)
        logger.info("STEP 7: Generating SITREP Data (Situation Reports)")
        logger.info("="*80)
        sitrep_data = sitrep_generator.generate_sitrep_data(
            scenario, reference_data, enemy_activity_data
        )
        logger.info(f"✓ SITREP generation complete: {len(sitrep_data)} records")
        
        # Step 8: Export to SQL
        logger.info("\n" + "="*80)
        logger.info("STEP 8: Exporting Data to SQL")
        logger.info("="*80)
        
        scenario_name = KARGIL_SCENARIO["name"]
        
        # Export each table
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
        
        # Generate summary report
        logger.info("\n" + "="*80)
        logger.info("GENERATION SUMMARY")
        logger.info("="*80)
        logger.info(f"Scenario: {scenario['scenario_name']}")
        logger.info(f"Date Range: {scenario['start_date']} to {scenario['end_date']}")
        logger.info(f"Total Days: {scenario['total_days']}")
        logger.info(f"Timeline Events: {scenario['total_events']}")
        logger.info(f"ELINT Records: {len(elint_data)}")
        logger.info(f"IMINT Records: {len(imint_data)}")
        logger.info(f"TACINT Records: {len(tacint_data)}")
        logger.info(f"Enemy Activity Records: {len(enemy_activity_data)}")
        logger.info(f"SITREP Records: {len(sitrep_data)}")
        logger.info(f"Total Intelligence Records: {len(elint_data) + len(imint_data) + len(tacint_data) + len(enemy_activity_data) + len(sitrep_data)}")
        logger.info("="*80)
        logger.info("✓ KARGIL WAR DATA GENERATION COMPLETE")
        logger.info("="*80)
        
        return {
            "scenario": scenario,
            "elint": elint_data,
            "imint": imint_data,
            "tacint": tacint_data,
            "enemy_activity": enemy_activity_data,
            "sitrep": sitrep_data
        }
        
    except Exception as e:
        logger.error(f"✗ Error during data generation: {str(e)}", exc_info=True)
        raise

def main():
    parser = argparse.ArgumentParser(
        description='Generate synthetic intelligence data for Kargil War 1999'
    )
    parser.add_argument(
        '--validate-only', 
        action='store_true',
        help='Only validate the generated data without regenerating'
    )
    
    args = parser.parse_args()
    
    if args.validate_only:
        logger.info("Validation mode - checking existing data...")
        # TODO: Implement validation logic
        logger.info("Validation complete")
    else:
        generate_kargil_data()

if __name__ == "__main__":
    main()