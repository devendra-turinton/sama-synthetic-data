import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import OUTPUT_DIR, KARGIL_SCENARIO, PRODUCTION_MODE
from utils.correlation_manager import CorrelationManager
from utils.validation import DataValidator
from utils.database import DatabaseManager
from generators.reference_data_generator import ReferenceDataGenerator
from generators.scenario_generator import ScenarioGenerator
from generators.elint_generator import ElintGenerator
from generators.imint_generator import ImintGenerator
from generators.tacint_generator import TacintGenerator
from generators.enemy_activity_generator import EnemyActivityGenerator
from generators.sitrep_generator import SitrepGenerator

# Configure comprehensive logging
log_file = os.path.join(OUTPUT_DIR, f'generation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class SAMADataGenerator:
    """
    Main orchestrator for SAMA (Synthetic Army Military Analytics) data generation.
    
    Generates complete, correlated intelligence data for the 1999 Kargil War:
    - 92 days of operations (May 8 - August 7, 1999)
    - 552 ground truth events (6 per day)
    - ~2,760 intelligence records across all sources
    - Full correlation and fusion
    """
    
    def __init__(self):
        self.correlation_manager = CorrelationManager()
        self.validator = DataValidator()
        self.db_manager = DatabaseManager()
        
        # Initialize generators with shared correlation manager
        self.reference_generator = ReferenceDataGenerator()
        self.scenario_generator = ScenarioGenerator(self.correlation_manager)
        self.elint_generator = ElintGenerator(self.correlation_manager)
        self.imint_generator = ImintGenerator(self.correlation_manager)
        self.tacint_generator = TacintGenerator(self.correlation_manager)
        self.enemy_activity_generator = EnemyActivityGenerator(self.correlation_manager)
        self.sitrep_generator = SitrepGenerator(self.correlation_manager)
        
        self.generation_start_time = None
        self.generation_stats = {}
    
    def generate_complete_dataset(self) -> Dict[str, Any]:
        """Generate complete Kargil War intelligence dataset"""
        
        self.generation_start_time = datetime.now()
        
        self._print_header()
        
        try:
            # ================================================================
            # STEP 1: REFERENCE DATA
            # ================================================================
            logger.info("\n" + "="*80)
            logger.info("STEP 1: REFERENCE DATA (Classification Hierarchies)")
            logger.info("="*80)
            
            reference_data = self.reference_generator.generate_all_reference_data()
            self.generation_stats["reference_data"] = {
                "activity_types": len(reference_data.get("activity_classification", {}).get("activity_types", [])),
                "target_types": len(reference_data.get("target_classification", {}).get("target_types", [])),
                "incident_types": len(reference_data.get("incident_classification", {}).get("incident_types", []))
            }
            logger.info("✓ Reference data ready")
            
            # ================================================================
            # STEP 2: GROUND TRUTH TIMELINE
            # ================================================================
            logger.info("\n" + "="*80)
            logger.info("STEP 2: GROUND TRUTH TIMELINE (With Correlation Assignment)")
            logger.info("="*80)
            
            scenario = self.scenario_generator.generate_complete_timeline()
            self.generation_stats["timeline"] = {
                "total_days": scenario["total_days"],
                "total_events": scenario["total_events"],
                "events_per_day": 6
            }
            logger.info(f"✓ Timeline generated: {scenario['total_events']} events with correlation IDs")
            
            # Save correlation registry
            correlation_registry_path = os.path.join(OUTPUT_DIR, "correlation_registry.json")
            self.correlation_manager.save_to_file(correlation_registry_path)
            logger.info(f"✓ Correlation registry saved: {correlation_registry_path}")
            
            # ================================================================
            # STEP 3: ELINT DATA
            # ================================================================
            logger.info("\n" + "="*80)
            logger.info("STEP 3: ELINT DATA (Electronic Intelligence)")
            logger.info("="*80)
            
            elint_data = self.elint_generator.generate_elint_data(scenario)
            self.generation_stats["elint"] = {
                "total_records": len(elint_data),
                "records_per_day": len(elint_data) / scenario["total_days"] if scenario["total_days"] > 0 else 0
            }
            logger.info(f"✓ ELINT complete: {len(elint_data)} records")
            
            # ================================================================
            # STEP 4: IMINT DATA
            # ================================================================
            logger.info("\n" + "="*80)
            logger.info("STEP 4: IMINT DATA (Imagery Intelligence)")
            logger.info("="*80)
            
            imint_data = self.imint_generator.generate_imint_data(scenario)
            self.generation_stats["imint"] = {
                "total_records": len(imint_data),
                "records_per_day": len(imint_data) / scenario["total_days"] if scenario["total_days"] > 0 else 0
            }
            logger.info(f"✓ IMINT complete: {len(imint_data)} records")
            
            # ================================================================
            # STEP 5: TACINT DATA
            # ================================================================
            logger.info("\n" + "="*80)
            logger.info("STEP 5: TACINT DATA (Tactical Intelligence)")
            logger.info("="*80)
            
            tacint_data = self.tacint_generator.generate_tacint_data(scenario)
            self.generation_stats["tacint"] = {
                "total_records": len(tacint_data),
                "records_per_day": len(tacint_data) / scenario["total_days"] if scenario["total_days"] > 0 else 0
            }
            logger.info(f"✓ TACINT complete: {len(tacint_data)} records")
            
            # ================================================================
            # STEP 6: DATA VALIDATION (Pre-Fusion)
            # ================================================================
            logger.info("\n" + "="*80)
            logger.info("STEP 6: DATA VALIDATION (Correlation Consistency)")
            logger.info("="*80)
            
            validation_results = self._validate_data(
                scenario, elint_data, imint_data, tacint_data, []
            )
            
            if validation_results["has_critical_errors"]:
                logger.error("❌ Critical validation errors detected!")
                logger.error("Review errors before proceeding to fusion")
                self._print_validation_report(validation_results)
                
                # Ask user to continue or abort
                if not self._confirm_continue_after_errors():
                    logger.error("Data generation aborted due to validation errors")
                    return self._create_failure_response(validation_results)
            else:
                logger.info("✓ Data validation passed")
            
            # ================================================================
            # STEP 7: ENEMY ACTIVITY (FUSION)
            # ================================================================
            logger.info("\n" + "="*80)
            logger.info("STEP 7: ENEMY ACTIVITY (Intelligence Fusion)")
            logger.info("="*80)
            
            enemy_activity_data = self.enemy_activity_generator.generate_enemy_activity_data(
                scenario, elint_data, imint_data, tacint_data
            )
            self.generation_stats["enemy_activity"] = {
                "total_records": len(enemy_activity_data),
                "records_per_day": len(enemy_activity_data) / scenario["total_days"] if scenario["total_days"] > 0 else 0
            }
            logger.info(f"✓ Enemy Activity fusion complete: {len(enemy_activity_data)} records")
            
            # ================================================================
            # STEP 8: SITREP DATA
            # ================================================================
            logger.info("\n" + "="*80)
            logger.info("STEP 8: SITREP DATA (Electronic Situation Reports)")
            logger.info("="*80)
            
            sitrep_data = self.sitrep_generator.generate_sitrep_data(
                scenario, enemy_activity_data
            )
            self.generation_stats["sitrep"] = {
                "total_records": len(sitrep_data),
                "records_per_day": len(sitrep_data) / scenario["total_days"] if scenario["total_days"] > 0 else 0
            }
            logger.info(f"✓ SITREP complete: {len(sitrep_data)} records")
            
            # ================================================================
            # STEP 9: FINAL VALIDATION
            # ================================================================
            logger.info("\n" + "="*80)
            logger.info("STEP 9: FINAL VALIDATION (Complete Dataset)")
            logger.info("="*80)
            
            final_validation = self._validate_data(
                scenario, elint_data, imint_data, tacint_data, 
                enemy_activity_data, sitrep_data
            )
            
            self._print_validation_report(final_validation)
            
            # ================================================================
            # STEP 10: EXPORT TO SQL
            # ================================================================
            logger.info("\n" + "="*80)
            logger.info("STEP 10: EXPORT TO SQL")
            logger.info("="*80)
            
            self._export_to_sql(
                scenario, elint_data, imint_data, tacint_data, 
                enemy_activity_data, sitrep_data
            )
            
            # ================================================================
            # GENERATION COMPLETE
            # ================================================================
            generation_time = datetime.now() - self.generation_start_time
            self.generation_stats["generation_time_seconds"] = generation_time.total_seconds()
            
            self._print_completion_summary(
                scenario, elint_data, imint_data, tacint_data, 
                enemy_activity_data, sitrep_data, generation_time
            )
            
            return {
                "status": "success",
                "scenario": scenario,
                "data": {
                    "elint": elint_data,
                    "imint": imint_data,
                    "tacint": tacint_data,
                    "enemy_activity": enemy_activity_data,
                    "sitrep": sitrep_data
                },
                "statistics": self.generation_stats,
                "validation": final_validation,
                "generation_time": str(generation_time)
            }
            
        except KeyboardInterrupt:
            logger.warning("\n\n⚠️  Generation interrupted by user")
            return {"status": "interrupted", "message": "Generation interrupted by user"}
            
        except Exception as e:
            logger.error(f"\n\n❌ CRITICAL ERROR: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "statistics": self.generation_stats
            }
    
    def _validate_data(self, scenario, elint, imint, tacint, enemy_activity=None, sitrep=None) -> Dict[str, Any]:
        """Comprehensive data validation"""
        
        validator = DataValidator()
        
        # Validate correlation consistency
        correlation_stats = validator.validate_correlation_consistency(
            elint, imint, tacint, enemy_activity or []
        )
        
        # Validate formation codes
        datasets = [elint, imint, tacint]
        if enemy_activity:
            datasets.append(enemy_activity)
        if sitrep:
            datasets.append(sitrep)
        
        validator.validate_formation_codes(*datasets)
        
        # Validate temporal consistency
        validator.validate_temporal_consistency(*datasets)
        
        # Validate geographic bounds
        validator.validate_geographic_bounds(*datasets)
        
        # Validate required fields
        validator.validate_required_fields(
            elint, 
            ["date", "correlation_id", "from_time", "frequency"],
            "ELINT"
        )
        validator.validate_required_fields(
            imint,
            ["Date", "correlation_id", "time", "str"],
            "IMINT"
        )
        validator.validate_required_fields(
            tacint,
            ["Date", "correlation_id", "time", "str"],
            "TACINT"
        )
        
        # Check for critical errors
        has_critical_errors = len(validator.validation_results["errors"]) > 0
        
        return {
            "has_critical_errors": has_critical_errors,
            "correlation_stats": correlation_stats,
            "errors": validator.validation_results["errors"],
            "warnings": validator.validation_results["warnings"],
            "info": validator.validation_results["info"]
        }
    
    def _print_validation_report(self, validation: Dict[str, Any]):
        """Print validation report"""
        
        logger.info("\n" + "-"*80)
        logger.info("VALIDATION REPORT")
        logger.info("-"*80)
        
        if validation["errors"]:
            logger.error(f"\n❌ ERRORS ({len(validation['errors'])}):")
            for error in validation["errors"][:10]:  # Show first 10
                logger.error(f"  - {error}")
            if len(validation["errors"]) > 10:
                logger.error(f"  ... and {len(validation['errors']) - 10} more errors")
        
        if validation["warnings"]:
            logger.warning(f"\n⚠️  WARNINGS ({len(validation['warnings'])}):")
            for warning in validation["warnings"][:10]:
                logger.warning(f"  - {warning}")
            if len(validation["warnings"]) > 10:
                logger.warning(f"  ... and {len(validation['warnings']) - 10} more warnings")
        
        if validation["correlation_stats"]:
            logger.info(f"\n📊 CORRELATION STATISTICS:")
            stats = validation["correlation_stats"]
            logger.info(f"  Total unique correlations: {stats.get('total_unique_correlations', 0)}")
            logger.info(f"  ELINT coverage: {stats.get('elint_coverage', 0)}")
            logger.info(f"  IMINT coverage: {stats.get('imint_coverage', 0)}")
            logger.info(f"  TACINT coverage: {stats.get('tacint_coverage', 0)}")
            logger.info(f"  Full coverage (3 sources): {stats.get('full_coverage', 0)}")
            logger.info(f"  Partial coverage (1-2 sources): {stats.get('partial_coverage', 0)}")
        
        if not validation["has_critical_errors"]:
            logger.info("\n✅ VALIDATION PASSED")
        
        logger.info("-"*80)
    
    def _confirm_continue_after_errors(self) -> bool:
        """Ask user whether to continue after validation errors"""
        
        if not sys.stdin.isatty():
            # Non-interactive mode, don't continue
            return False
        
        response = input("\nContinue despite errors? (yes/no): ").strip().lower()
        return response in ['yes', 'y']
    
    def _export_to_sql(self, scenario, elint, imint, tacint, enemy_activity, sitrep):
        """Export all data to SQL files"""
        
        scenario_name = scenario["scenario_name"]
        
        tables = [
            ("elint", elint),
            ("imint_data", imint),
            ("tac_int", tacint),
            ("en_activity", enemy_activity),
            ("e_sitrep_mst", sitrep)
        ]
        
        for table_name, data in tables:
            if data:
                output_file = os.path.join(OUTPUT_DIR, f"{table_name}_{scenario_name}_inserts.sql")
                try:
                    self.db_manager.export_to_sql(table_name, data, output_file)
                    logger.info(f"  ✓ {table_name}: {len(data)} records")
                except Exception as e:
                    logger.error(f"  ✗ {table_name}: Export failed - {str(e)}")
    
    def _print_header(self):
        """Print generation header"""
        
        mode = "PRODUCTION (92 days)" if PRODUCTION_MODE else "TEST (1 day)"
        
        logger.info("\n" + "="*80)
        logger.info("SAMA DATA GENERATION - KARGIL WAR 1999")
        logger.info("="*80)
        logger.info(f"Mode: {mode}")
        logger.info(f"Scenario: {KARGIL_SCENARIO['name']}")
        logger.info(f"Period: {KARGIL_SCENARIO['start_date']} to {KARGIL_SCENARIO['end_date']}")
        logger.info(f"Started: {self.generation_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*80 + "\n")
    
    def _print_completion_summary(self, scenario, elint, imint, tacint, 
                                 enemy_activity, sitrep, generation_time):
        """Print final completion summary"""
        
        total_records = (len(elint) + len(imint) + len(tacint) + 
                        len(enemy_activity) + len(sitrep))
        
        logger.info("\n" + "="*80)
        logger.info("✅ GENERATION COMPLETE")
        logger.info("="*80)
        logger.info(f"Scenario: {scenario['scenario_name']}")
        logger.info(f"Period: {scenario['start_date']} to {scenario['end_date']}")
        logger.info(f"Total Days: {scenario['total_days']}")
        logger.info(f"Generation Time: {generation_time}")
        logger.info("")
        logger.info("DATA SUMMARY:")
        logger.info(f"  Ground Truth Events:  {scenario['total_events']:>6}")
        logger.info(f"  ELINT Records:        {len(elint):>6}")
        logger.info(f"  IMINT Records:        {len(imint):>6}")
        logger.info(f"  TACINT Records:       {len(tacint):>6}")
        logger.info(f"  Enemy Activity:       {len(enemy_activity):>6}")
        logger.info(f"  SITREP Records:       {len(sitrep):>6}")
        logger.info(f"  ─────────────────────────────")
        logger.info(f"  TOTAL INTEL RECORDS:  {total_records:>6}")
        logger.info("")
        logger.info("CORRELATION STATISTICS:")
        corr_stats = self.correlation_manager.get_statistics()
        logger.info(f"  Total Correlations:   {corr_stats['total_correlations']:>6}")
        logger.info(f"  ELINT Coverage:       {corr_stats['source_coverage']['ELINT']:>6}")
        logger.info(f"  IMINT Coverage:       {corr_stats['source_coverage']['IMINT']:>6}")
        logger.info(f"  TACINT Coverage:      {corr_stats['source_coverage']['TACINT']:>6}")
        logger.info(f"  Avg Sources/Event:    {corr_stats['average_sources_per_event']:>6.2f}")
        logger.info("")
        logger.info("OUTPUT FILES:")
        logger.info(f"  Scenario JSON:        scenario_{scenario['scenario_name']}.json")
        logger.info(f"  Correlation Registry: correlation_registry.json")
        logger.info(f"  ELINT JSON:           elint_data_{scenario['scenario_name']}.json")
        logger.info(f"  IMINT JSON:           imint_data_{scenario['scenario_name']}.json")
        logger.info(f"  TACINT JSON:          tacint_data_{scenario['scenario_name']}.json")
        logger.info(f"  Enemy Activity JSON:  enemy_activity_data_{scenario['scenario_name']}.json")
        logger.info(f"  SITREP JSON:          sitrep_data_{scenario['scenario_name']}.json")
        logger.info(f"  SQL Files:            *_{scenario['scenario_name']}_inserts.sql")
        logger.info(f"  Generation Log:       {os.path.basename(log_file)}")
        logger.info("")
        logger.info("All files saved to: " + OUTPUT_DIR)
        logger.info("="*80 + "\n")
    
    def _create_failure_response(self, validation: Dict[str, Any]) -> Dict[str, Any]:
        """Create failure response"""
        return {
            "status": "failed",
            "reason": "validation_errors",
            "validation": validation,
            "statistics": self.generation_stats
        }


def main():
    """Main entry point"""
    
    try:
        generator = SAMADataGenerator()
        result = generator.generate_complete_dataset()
        
        if result["status"] == "success":
            logger.info("\n🎉 SUCCESS: Data generation completed successfully!")
            logger.info(f"Review output in: {OUTPUT_DIR}")
            return 0
        elif result["status"] == "interrupted":
            logger.warning("\n⚠️  Generation was interrupted")
            return 130
        else:
            logger.error(f"\n❌ FAILED: {result.get('reason', 'Unknown error')}")
            return 1
            
    except KeyboardInterrupt:
        logger.warning("\n\n⚠️  Generation interrupted by user (Ctrl+C)")
        return 130
        
    except Exception as e:
        logger.error(f"\n\n❌ FATAL ERROR: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)