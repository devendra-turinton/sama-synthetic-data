import logging
from typing import Dict, List, Any, Set
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataValidator:
    """Validate generated intelligence data for consistency and completeness"""
    
    def __init__(self):
        self.validation_results = {
            "errors": [],
            "warnings": [],
            "info": []
        }
    
    def validate_correlation_consistency(self, 
                                        elint_data: List[Dict],
                                        imint_data: List[Dict],
                                        tacint_data: List[Dict],
                                        enemy_activity_data: List[Dict]) -> Dict[str, Any]:
        """Validate that correlation IDs are consistent across all sources"""
        
        logger.info("Validating correlation consistency...")
        
        # Collect correlation IDs from each source
        elint_corrs = set(r.get("correlation_id") for r in elint_data if r.get("correlation_id"))
        imint_corrs = set(r.get("correlation_id") for r in imint_data if r.get("correlation_id"))
        tacint_corrs = set(r.get("correlation_id") for r in tacint_data if r.get("correlation_id"))
        enemy_corrs = set(r.get("correlation_id") for r in enemy_activity_data if r.get("correlation_id"))
        
        all_source_corrs = elint_corrs | imint_corrs | tacint_corrs
        
        # Check for records without correlation IDs
        missing_corr_counts = {
            "ELINT": len([r for r in elint_data if not r.get("correlation_id")]),
            "IMINT": len([r for r in imint_data if not r.get("correlation_id")]),
            "TACINT": len([r for r in tacint_data if not r.get("correlation_id")]),
            "ENEMY_ACTIVITY": len([r for r in enemy_activity_data if not r.get("correlation_id")])
        }
        
        for source, count in missing_corr_counts.items():
            if count > 0:
                self.validation_results["errors"].append(
                    f"{source}: {count} records missing correlation_id"
                )
        
        # Check for orphaned enemy activity records
        orphaned_enemy = enemy_corrs - all_source_corrs
        if orphaned_enemy:
            self.validation_results["warnings"].append(
                f"Found {len(orphaned_enemy)} enemy activity records with correlation IDs not in source data: {orphaned_enemy}"
            )
        
        # Check coverage
        coverage_stats = {
            "total_unique_correlations": len(all_source_corrs),
            "elint_coverage": len(elint_corrs),
            "imint_coverage": len(imint_corrs),
            "tacint_coverage": len(tacint_corrs),
            "enemy_activity_coverage": len(enemy_corrs),
            "full_coverage": len(elint_corrs & imint_corrs & tacint_corrs),
            "partial_coverage": len(all_source_corrs) - len(elint_corrs & imint_corrs & tacint_corrs)
        }
        
        self.validation_results["info"].append(f"Correlation coverage: {coverage_stats}")
        
        logger.info(f"✓ Correlation validation complete: {coverage_stats['total_unique_correlations']} unique correlations")
        
        return coverage_stats
    
    def validate_formation_codes(self, *datasets) -> Dict[str, Any]:
        """Validate formation codes are 10 characters and properly formatted"""
        
        logger.info("Validating formation codes...")
        
        invalid_codes = defaultdict(list)
        
        for dataset in datasets:
            for record in dataset:
                fmn_code = record.get("fmn_code")
                if fmn_code:
                    fmn_str = str(fmn_code)
                    if len(fmn_str) != 10:
                        invalid_codes["wrong_length"].append(fmn_str)
                    elif not fmn_str.isalnum():
                        invalid_codes["invalid_format"].append(fmn_str)
        
        if invalid_codes:
            for error_type, codes in invalid_codes.items():
                self.validation_results["errors"].append(
                    f"Formation codes with {error_type}: {len(codes)} records"
                )
        else:
            logger.info("✓ All formation codes are valid")
        
        return dict(invalid_codes)
    
    def validate_temporal_consistency(self, *datasets) -> Dict[str, Any]:
        """Validate that timestamps are logical and within expected ranges"""
        
        logger.info("Validating temporal consistency...")
        
        temporal_issues = []
        
        for dataset in datasets:
            for record in dataset:
                # Check date format
                date_field = record.get("date") or record.get("Date") or record.get("observation_date") or record.get("Incident_date")
                if date_field:
                    try:
                        from datetime import datetime
                        parsed_date = datetime.strptime(date_field, "%Y-%m-%d")
                        # Check if date is within Kargil War period (May-August 1999)
                        if parsed_date.year != 1999 or parsed_date.month < 5 or parsed_date.month > 8:
                            temporal_issues.append(f"Date outside Kargil period: {date_field}")
                    except ValueError:
                        temporal_issues.append(f"Invalid date format: {date_field}")
        
        if temporal_issues:
            self.validation_results["warnings"].extend(temporal_issues[:10])  # Limit to first 10
        else:
            logger.info("✓ Temporal consistency validated")
        
        return {"issues": len(temporal_issues)}
    
    def validate_geographic_bounds(self, *datasets) -> Dict[str, Any]:
        """Validate that coordinates are within Kargil sector bounds"""
        
        logger.info("Validating geographic bounds...")
        
        # Kargil sector bounds
        lat_min, lat_max = 34.2, 34.9
        long_min, long_max = 75.5, 76.7
        
        out_of_bounds = []
        
        for dataset in datasets:
            for record in dataset:
                lat = record.get("lat") or record.get("latitude")
                long = record.get("long") or record.get("longitude")
                
                if lat and long:
                    try:
                        lat_val = float(lat)
                        long_val = float(long)
                        
                        if not (lat_min <= lat_val <= lat_max and long_min <= long_val <= long_max):
                            out_of_bounds.append({
                                "lat": lat_val,
                                "long": long_val,
                                "record_id": record.get("id")
                            })
                    except (ValueError, TypeError):
                        pass
        
        if out_of_bounds:
            self.validation_results["warnings"].append(
                f"Found {len(out_of_bounds)} records with coordinates outside Kargil sector"
            )
        else:
            logger.info("✓ All coordinates within valid bounds")
        
        return {"out_of_bounds_count": len(out_of_bounds)}
    
    def validate_required_fields(self, dataset: List[Dict], required_fields: List[str], dataset_name: str) -> Dict[str, Any]:
        """Validate that all required fields are present and non-null"""
        
        logger.info(f"Validating required fields for {dataset_name}...")
        
        missing_fields = defaultdict(int)
        
        for record in dataset:
            for field in required_fields:
                if field not in record or record[field] is None or record[field] == "":
                    missing_fields[field] += 1
        
        if missing_fields:
            for field, count in missing_fields.items():
                self.validation_results["errors"].append(
                    f"{dataset_name}: {count} records missing required field '{field}'"
                )
        else:
            logger.info(f"✓ All required fields present in {dataset_name}")
        
        return dict(missing_fields)
    
    def generate_report(self) -> str:
        """Generate a comprehensive validation report"""
        
        report = []
        report.append("="*80)
        report.append("DATA VALIDATION REPORT")
        report.append("="*80)
        
        if self.validation_results["errors"]:
            report.append("\n❌ ERRORS:")
            for error in self.validation_results["errors"]:
                report.append(f"  - {error}")
        
        if self.validation_results["warnings"]:
            report.append("\n⚠️  WARNINGS:")
            for warning in self.validation_results["warnings"]:
                report.append(f"  - {warning}")
        
        if self.validation_results["info"]:
            report.append("\nℹ️  INFO:")
            for info in self.validation_results["info"]:
                report.append(f"  - {info}")
        
        if not self.validation_results["errors"] and not self.validation_results["warnings"]:
            report.append("\n✅ ALL VALIDATIONS PASSED")
        
        report.append("="*80)
        
        return "\n".join(report)