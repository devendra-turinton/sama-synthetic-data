import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CorrelationManager:
    """
    Centralized correlation manager to ensure consistent correlation IDs
    across all intelligence sources.
    
    This is the SINGLE SOURCE OF TRUTH for correlation relationships.
    """
    
    def __init__(self):
        self.correlation_id_counter = 0
        self.correlation_registry = {}  # correlation_id -> full correlation package
        self.event_to_correlation = {}  # event_id -> correlation_id
        
    def create_correlation_package(self, ground_truth_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a NEW correlation package for a ground truth event.
        This assigns a unique correlation ID that will be shared across all sources.
        """
        self.correlation_id_counter += 1
        correlation_id = f"CORR_{self.correlation_id_counter:04d}"
        
        # Create event identifier
        event_id = f"{ground_truth_event.get('date')}_{ground_truth_event.get('time')}"
        
        # Determine which sources can observe this event
        observable_by = ground_truth_event.get("observable_by", ["ELINT", "IMINT", "TACINT"])
        
        # Create correlation package
        correlation_package = {
            "correlation_id": correlation_id,
            "event_id": event_id,
            "ground_truth": ground_truth_event,
            "source_observations": {}
        }
        
        # Generate source-specific observation metadata
        for source in observable_by:
            if source == "ELINT":
                correlation_package["source_observations"]["ELINT"] = self._create_elint_observation(
                    ground_truth_event, correlation_id
                )
            elif source == "IMINT":
                correlation_package["source_observations"]["IMINT"] = self._create_imint_observation(
                    ground_truth_event, correlation_id
                )
            elif source == "TACINT":
                correlation_package["source_observations"]["TACINT"] = self._create_tacint_observation(
                    ground_truth_event, correlation_id
                )
        
        # Register in central registry
        self.correlation_registry[correlation_id] = correlation_package
        self.event_to_correlation[event_id] = correlation_id
        
        logger.debug(f"Created correlation package: {correlation_id} for event {event_id}")
        
        return correlation_package
    
    def _create_elint_observation(self, event: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Create ELINT-specific observation metadata"""
        # ELINT typically detects 10-15 minutes BEFORE physical movement
        time_offset_minutes = random.randint(-15, -10)
        
        return {
            "correlation_id": correlation_id,
            "time_offset_minutes": time_offset_minutes,
            "detection_type": "electronic_signature",
            "observable_details": {
                "communications": event.get("event_type") in ["movement", "deployment", "attack", "logistics"],
                "radar": event.get("event_type") in ["aircraft", "missile", "artillery"],
                "can_identify_equipment": False,
                "can_count_strength": False,
                "location_accuracy": "medium"
            }
        }
    
    def _create_imint_observation(self, event: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Create IMINT-specific observation metadata"""
        # IMINT depends on satellite pass timing
        time_offset_minutes = random.randint(20, 35)
        cloud_cover = random.randint(5, 40)
        
        return {
            "correlation_id": correlation_id,
            "time_offset_minutes": time_offset_minutes,
            "detection_type": "satellite_imagery",
            "observable_details": {
                "can_see_vehicles": True,
                "can_see_personnel": cloud_cover < 30,
                "can_identify_equipment": cloud_cover < 35,
                "can_count_strength": True,
                "location_accuracy": "high",
                "weather_factor": f"{cloud_cover}% cloud cover",
                "image_quality": "excellent" if cloud_cover < 15 else "good" if cloud_cover < 30 else "fair"
            }
        }
    
    def _create_tacint_observation(self, event: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Create TACINT-specific observation metadata"""
        # TACINT reports 10-45 minutes AFTER event
        time_offset_minutes = random.randint(10, 45)
        observer_distance_km = random.uniform(1.5, 4.5)
        
        return {
            "correlation_id": correlation_id,
            "time_offset_minutes": time_offset_minutes,
            "detection_type": "ground_observation",
            "observable_details": {
                "can_see_vehicles": True,
                "can_see_personnel": True,
                "can_identify_equipment": observer_distance_km < 3.0,
                "can_count_strength": True,
                "location_accuracy": "high",
                "observer_distance_km": round(observer_distance_km, 1),
                "observation_method": self._get_observation_method(observer_distance_km),
                "grading": self._get_tacint_grading(observer_distance_km)
            }
        }
    
    def _get_observation_method(self, distance_km: float) -> str:
        """Get realistic observation method based on distance"""
        if distance_km < 1.5:
            return "Direct visual observation"
        elif distance_km < 2.5:
            return "Visual observation with binoculars"
        elif distance_km < 3.5:
            return "Observation through spotting scope"
        else:
            return "Thermal imaging and long-range optics"
    
    def _get_tacint_grading(self, distance_km: float) -> str:
        """Get TACINT grading based on observation distance"""
        if distance_km < 2.0:
            return "A1"  # Reliable source, confirmed information
        elif distance_km < 3.0:
            return "A2"  # Reliable source, probably true
        elif distance_km < 4.0:
            return "B2"  # Usually reliable source, probably true
        else:
            return "C3"  # Fairly reliable source, possibly true
    
    def get_correlation_package(self, correlation_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a correlation package by ID"""
        return self.correlation_registry.get(correlation_id)
    
    def get_all_correlation_ids(self) -> List[str]:
        """Get all registered correlation IDs"""
        return list(self.correlation_registry.keys())
    
    def get_correlation_for_event(self, event_id: str) -> Optional[str]:
        """Get correlation ID for a specific event"""
        return self.event_to_correlation.get(event_id)
    
    def apply_time_adjustment(self, base_time_str: str, offset_minutes: int) -> str:
        """Apply time offset to base time"""
        try:
            base_time = datetime.strptime(base_time_str, "%H:%M")
            adjusted_time = base_time + timedelta(minutes=offset_minutes)
            return adjusted_time.strftime("%H:%M")
        except Exception as e:
            logger.warning(f"Error adjusting time {base_time_str} by {offset_minutes}: {e}")
            return base_time_str
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get correlation statistics"""
        total_correlations = len(self.correlation_registry)
        
        source_coverage = {
            "ELINT": 0,
            "IMINT": 0,
            "TACINT": 0
        }
        
        for corr_pkg in self.correlation_registry.values():
            for source in corr_pkg["source_observations"].keys():
                source_coverage[source] += 1
        
        return {
            "total_correlations": total_correlations,
            "source_coverage": source_coverage,
            "average_sources_per_event": sum(source_coverage.values()) / max(total_correlations, 1)
        }
    
    def save_to_file(self, filepath: str):
        """Save correlation registry to file"""
        try:
            with open(filepath, 'w') as f:
                json.dump({
                    "correlation_registry": self.correlation_registry,
                    "event_to_correlation": self.event_to_correlation,
                    "statistics": self.get_statistics()
                }, f, indent=2)
            logger.info(f"Correlation registry saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving correlation registry: {e}")