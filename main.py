import os
import logging
import argparse
from typing import Dict, List, Any

from config import SCENARIOS, OUTPUT_DIR
from generators.scenario_generator import ScenarioGenerator
from generators.reference_data_generator import ReferenceDataGenerator
from generators.elint_generator import ElintGenerator
from generators.imint_generator import ImintGenerator
from generators.tacint_generator import TacintGenerator
from generators.enemy_activity_generator import EnemyActivityGenerator
from generators.sitrep_generator import SitrepGenerator
from utils.database import DatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_data(scenario_name: str = None):
    """Generate synthetic data for SAMA."""
    
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Initialize generators
    scenario_generator = ScenarioGenerator()
    reference_generator = ReferenceDataGenerator()
    elint_generator = ElintGenerator()
    imint_generator = ImintGenerator()
    tacint_generator = TacintGenerator()
    enemy_activity_generator = EnemyActivityGenerator()
    sitrep_generator = SitrepGenerator()
    db_manager = DatabaseManager()
    
    # Generate reference data
    logger.info("Generating reference data...")
    reference_data = reference_generator.generate_all_reference_data()
    
    # Process scenarios
    if scenario_name:
        # Find the specific scenario
        scenario_config = next((s for s in SCENARIOS if s["name"] == scenario_name), None)
        if not scenario_config:
            logger.error(f"Scenario '{scenario_name}' not found")
            return
        
        scenarios_to_process = [scenario_config]
    else:
        scenarios_to_process = SCENARIOS
    
    for scenario_config in scenarios_to_process:
        scenario_name = scenario_config["name"]
        logger.info(f"Processing scenario: {scenario_name}")
        
        # Generate scenario timeline
        scenario = scenario_generator.generate_scenario_timeline(scenario_config)
        
        # Generate ELINT data
        elint_data = elint_generator.generate_elint_data(scenario, reference_data)
        
        # Generate IMINT data
        imint_data = imint_generator.generate_imint_data(scenario, reference_data)
        
        # Generate TACINT data
        tacint_data = tacint_generator.generate_tacint_data(scenario, reference_data)
        
        # Generate enemy activity data
        enemy_activity_data = enemy_activity_generator.generate_enemy_activity_data(
            scenario, reference_data, elint_data, imint_data, tacint_data
        )
        
        # Generate SITREP data
        sitrep_data = sitrep_generator.generate_sitrep_data(
            scenario, reference_data, enemy_activity_data
        )
        
        # Export data to SQL
        db_manager.export_all_data_to_sql(scenario_name)
    
    logger.info("Data generation complete!")

def main():
    parser = argparse.ArgumentParser(description='Generate synthetic data for SAMA.')
    parser.add_argument('--scenario', type=str, help='Specific scenario name to generate data for')
    args = parser.parse_args()
    
    generate_data(args.scenario)

if __name__ == "__main__":
    main()