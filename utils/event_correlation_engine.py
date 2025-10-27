import random
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventCorrelationEngine:
    """
    Correlate ground truth events across multiple intelligence sources.
    Ensures realistic variations while maintaining consistency.
    """
    
    def __init__(self):
        self.correlation_id_counter = 0
    
    def create_correlated_event(self, ground_truth_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a correlation package for a single ground truth event.
        Returns event with correlation metadata for each intelligence source.
        """
        self.correlation_id_counter += 1
        correlation_id = f"CORR_{self.correlation_id_counter:04d}"
        
        # Determine which sources can observe this event
        observable_by = ground_truth_event.get("observable_by", ["ELINT", "IMINT", "TACINT"])
        
        # Create base correlation metadata
        correlation_package = {
            "correlation_id": correlation_id,
            "ground_truth": ground_truth_event,
            "source_observations": {}
        }
        
        # Generate source-specific observations
        for source in observable_by:
            if source == "ELINT":
                correlation_package["source_observations"]["ELINT"] = self._create_elint_observation(ground_truth_event, correlation_id)
            elif source == "IMINT":
                correlation_package["source_observations"]["IMINT"] = self._create_imint_observation(ground_truth_event, correlation_id)
            elif source == "TACINT":
                correlation_package["source_observations"]["TACINT"] = self._create_tacint_observation(ground_truth_event, correlation_id)
        
        return correlation_package
    
    def _create_elint_observation(self, event: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Create ELINT-specific observation with realistic limitations"""
        # ELINT typically detects 5-15 minutes BEFORE physical movement
        time_offset_minutes = random.randint(-15, -5)
        
        return {
            "correlation_id": correlation_id,
            "time_offset_minutes": time_offset_minutes,
            "detection_type": "electronic_signature",
            "confidence_modifier": "Electronic signature correlation",
            "observable_details": {
                "communications": event.get("event_type") in ["movement", "deployment", "attack"],
                "radar": event.get("event_type") in ["aircraft", "missile", "artillery"],
                "can_identify_equipment": False,  # ELINT can't see physical equipment
                "can_count_strength": False,  # Can only infer from traffic volume
                "location_accuracy": "medium"  # Triangulation gives approximate location
            },
            "description_style": "technical",  # Use signal analysis language
            "uncertainty_level": "medium"
        }
    
    def _create_imint_observation(self, event: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Create IMINT-specific observation with realistic limitations"""
        # IMINT depends on satellite pass timing (can be before, during, or after event)
        time_offset_minutes = random.randint(-30, 30)
        
        # Weather affects IMINT quality
        cloud_cover = random.randint(0, 80)
        
        return {
            "correlation_id": correlation_id,
            "time_offset_minutes": time_offset_minutes,
            "detection_type": "satellite_imagery",
            "confidence_modifier": self._get_imint_confidence(cloud_cover),
            "observable_details": {
                "can_see_vehicles": True,
                "can_see_personnel": True if cloud_cover < 30 else False,
                "can_identify_equipment": True if cloud_cover < 40 else False,
                "can_count_strength": True,
                "location_accuracy": "high",  # GPS-quality coordinates
                "weather_factor": f"{cloud_cover}% cloud cover"
            },
            "description_style": "visual",  # Describe what's visible from above
            "uncertainty_level": "low" if cloud_cover < 30 else "medium"
        }
    
    def _create_tacint_observation(self, event: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Create TACINT-specific observation with realistic limitations"""
        # TACINT typically reports 10-45 minutes AFTER event (time to observe and report)
        time_offset_minutes = random.randint(10, 45)
        
        # Observer distance affects quality
        observer_distance_km = random.uniform(1.5, 5.0)
        
        return {
            "correlation_id": correlation_id,
            "time_offset_minutes": time_offset_minutes,
            "detection_type": "ground_observation",
            "confidence_modifier": self._get_tacint_confidence(observer_distance_km),
            "observable_details": {
                "can_see_vehicles": True,
                "can_see_personnel": True,
                "can_identify_equipment": True if observer_distance_km < 3.0 else False,
                "can_count_strength": True,
                "location_accuracy": "high",  # Direct line of sight
                "observer_distance_km": round(observer_distance_km, 1),
                "observation_method": self._get_observation_method(observer_distance_km)
            },
            "description_style": "narrative",  # Human observer describing what they see
            "uncertainty_level": "low" if observer_distance_km < 2.5 else "medium"
        }
    
    def _get_imint_confidence(self, cloud_cover: int) -> str:
        """Get confidence level based on weather conditions"""
        if cloud_cover < 20:
            return "High image quality, positive identification"
        elif cloud_cover < 40:
            return "Good image quality, probable identification"
        elif cloud_cover < 60:
            return "Moderate image quality, possible identification"
        else:
            return "Poor image quality, limited identification"
    
    def _get_tacint_confidence(self, distance_km: float) -> str:
        """Get confidence level based on observer distance"""
        if distance_km < 2.0:
            return "Close observation, positive identification"
        elif distance_km < 3.5:
            return "Medium range observation, probable identification"
        else:
            return "Long range observation, possible identification"
    
    def _get_observation_method(self, distance_km: float) -> str:
        """Get realistic observation method based on distance"""
        if distance_km < 1.0:
            return "Direct visual observation"
        elif distance_km < 2.5:
            return "Visual observation with binoculars"
        elif distance_km < 4.0:
            return "Observation through spotting scope"
        else:
            return "Thermal imaging and long-range optics"
    
    def apply_location_variance(self, lat: float, long: float, source_type: str) -> tuple:
        """
        Apply realistic location variance based on source type.
        All sources should report same event within 500m radius.
        """
        variance_degrees = {
            "ELINT": 0.005,   # ~500m - triangulation accuracy
            "IMINT": 0.0005,  # ~50m - GPS-quality satellite
            "TACINT": 0.001   # ~100m - visual estimation
        }
        
        var = variance_degrees.get(source_type, 0.002)
        
        # Add random variance
        lat_offset = random.uniform(-var, var)
        long_offset = random.uniform(-var, var)
        
        return (round(lat + lat_offset, 6), round(long + long_offset, 6))
    
    def apply_strength_variance(self, actual_strength: str, source_type: str) -> str:
        """
        Apply realistic strength estimation variance.
        Example: 12 tanks might be reported as "10-14" or "approximately 12" or "dozen"
        """
        # Try to extract number from strength string
        import re
        numbers = re.findall(r'\d+', actual_strength)
        
        if not numbers:
            return actual_strength
        
        base_number = int(numbers[0])
        
        # Different sources have different precision
        if source_type == "ELINT":
            # ELINT can only infer strength from traffic volume
            strength_descriptions = [
                f"Battalion-strength communications",
                f"Company-level radio traffic",
                f"Platoon-sized element inferred from signal pattern"
            ]
            if base_number >= 50:
                return "Battalion-strength communications"
            elif base_number >= 15:
                return "Company-level radio traffic"
            else:
                return "Platoon-sized element inferred from signal pattern"
        
        elif source_type == "IMINT":
            # IMINT gives range based on count
            lower = base_number - random.randint(1, 2)
            upper = base_number + random.randint(1, 2)
            return f"{lower}-{upper} units"
        
        elif source_type == "TACINT":
            # TACINT gives estimate with qualifier
            lower = base_number - random.randint(0, 3)
            upper = base_number + random.randint(0, 3)
            qualifiers = ["approximately", "estimated", "about"]
            qualifier = random.choice(qualifiers)
            return f"{qualifier} {lower}-{upper} personnel/vehicles"
        
        return actual_strength
    
    def get_time_adjusted_datetime(self, base_time_str: str, offset_minutes: int) -> str:
        """Apply time offset to base time and return formatted string"""
        try:
            base_time = datetime.strptime(base_time_str, "%H:%M")
            adjusted_time = base_time + timedelta(minutes=offset_minutes)
            return adjusted_time.strftime("%H:%M")
        except:
            return base_time_str
    
    def create_correlation_summary(self, correlation_package: Dict[str, Any]) -> str:
        """
        Create a summary showing how sources correlate.
        Useful for Enemy Activity and SITREP descriptions.
        """
        sources = list(correlation_package["source_observations"].keys())
        correlation_id = correlation_package["correlation_id"]
        
        summary_parts = []
        for source in sources:
            obs = correlation_package["source_observations"][source]
            summary_parts.append(f"{source} ({obs['confidence_modifier']})")
        
        return f"Multi-source correlation [{correlation_id}]: {', '.join(summary_parts)}"