import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any
from .config import AppConfig

class LiveLocationManager:
    """Manage live location tracking."""
    
    def __init__(self) -> None:
        self.current_location: Optional[Dict[str, float]] = None
        self.location_history: List[Dict[str, Any]] = []
        self.max_history = 100
        
    def update_location(self, lat: float, lng: float, accuracy: float = 100.0, mock: bool = False) -> None:
        """Update current location."""
        self.current_location = {
            "lat": lat,
            "lng": lng,
            "accuracy": accuracy,
            "timestamp": datetime.now(),
            "mock": mock
        }
        
        # Add to history
        self.location_history.append(self.current_location.copy())
        
        # Maintain history size
        if len(self.location_history) > self.max_history:
            self.location_history.pop(0)
    
    def get_current_location(self) -> Optional[Dict[str, Any]]:
        """Get current location with fallback."""
        if self.current_location:
            return self.current_location
        
        # Fallback to Dhaka coordinates
        return {
            "lat": 23.8103,
            "lng": 90.4125,
            "accuracy": 1000,
            "timestamp": datetime.now(),
            "mock": True
        }

class MapManager:
    def __init__(self) -> None:
        self.locations: List[Dict[str, Any]] = []
        self.hazard_spots: List[Dict[str, Any]] = []
        self.max_locations = 100
        
    def add_detection_location(
        self,
        detection_data: List[Dict[str, Any]],
        gps_data: Optional[Dict[str, float]] = None
    ) -> bool:
        """Add detection location with optimized storage."""
        if gps_data is None:
            # Generate realistic mock GPS coordinates around Dhaka if none provided
            gps_data = {
                "lat": 23.8103 + (np.random.random() - 0.5) * 0.02,
                "lng": 90.4125 + (np.random.random() - 0.5) * 0.02
            }
        
        location_record = {
            "timestamp": datetime.now(),
            "gps": gps_data,
            "detections": detection_data,
            "critical_objects": [
                d for d in detection_data
                if any(
                    crit in d["class_name"].lower()
                    for crit in AppConfig.CRITICAL_OBJECTS.keys()
                )
            ]
        }
        
        self.locations.append(location_record)
        
        # Maintain size limit
        if len(self.locations) > self.max_locations:
            self.locations.pop(0)
        
        # Update hazard spots for critical objects
        if location_record["critical_objects"]:
            hazard_record = {
                "location": gps_data,
                "type": "critical",
                "objects": [
                    obj["class_name"]
                    for obj in location_record["critical_objects"]
                ],
                "timestamp": datetime.now(),
                "count": len(location_record["critical_objects"])
            }
            self.hazard_spots.append(hazard_record)
            
            # Limit hazard spots
            if len(self.hazard_spots) > 50:
                self.hazard_spots.pop(0)
        
        return True
    
    def get_map_data(self) -> Dict[str, Any]:
        """Get optimized map data for visualization."""
        recent_locations = self.locations[-50:]
        
        return {
            "detection_points": recent_locations,
            "hazard_spots": self.hazard_spots[-20:],
            "clusters": self._cluster_locations(recent_locations)
        }
    
    def _cluster_locations(
        self,
        locations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Simple location clustering."""
        if len(locations) < 3:
            return []
        
        # Mock clustering - in production, use DBSCAN or similar
        return [{
            "center": {"lat": 23.8103, "lng": 90.4125},
            "count": len(locations),
            "type": "detection_cluster",
            "radius": 0.01
        }]
