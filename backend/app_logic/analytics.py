import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
from .config import AppConfig

logger = logging.getLogger(__name__)

class AnalyticsDashboard:
    def __init__(self) -> None:
        self.data_history: List[Dict[str, Any]] = []
        
    def update_analytics(
        self,
        detection_data: List[Dict[str, Any]],
        scene_data: Dict[str, Any],
        alert_data: str
    ) -> bool:
        """Update analytics with size limits."""
        record = {
            "timestamp": datetime.now(),
            "object_count": len(detection_data),
            "critical_count": len([
                d for d in detection_data
                if any(
                    crit in d["class_name"].lower()
                    for crit in AppConfig.CRITICAL_OBJECTS.keys()
                )
            ]),
            "scene_type": scene_data.get("type", "unknown"),
            "density": scene_data.get("density", "low"),
            "alert_triggered": bool(alert_data),
            "visibility": scene_data.get("visibility", "good")
        }
        
        self.data_history.append(record)
        
        # Maintain size limit
        if len(self.data_history) > AppConfig.MAX_HISTORY_LENGTH:
            self.data_history = self.data_history[-AppConfig.MAX_HISTORY_LENGTH:]
        
        return True
    
    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get summary of analytics data."""
        if not self.data_history:
            return {}
            
        df = pd.DataFrame(self.data_history)
        return {
            "total_records": len(df),
            "avg_object_count": float(df["object_count"].mean()),
            "total_critical_alerts": int(df["critical_count"].sum()),
            "scene_types": df["scene_type"].value_counts().to_dict()
        }
