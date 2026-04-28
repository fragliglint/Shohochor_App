import time
import uuid
import logging
import cv2
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from .config import AppConfig

logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self) -> None:
        self.sessions_dir = Path("detection_sessions")
        self.sessions_dir.mkdir(exist_ok=True)
        self.current_session: Optional[Dict[str, Any]] = None
        self._cleanup_old_sessions()
        
    def _cleanup_old_sessions(self) -> None:
        """Clean up session images older than 10 minutes to save memory."""
        try:
            current_time = time.time()
            # Delete images older than 10 minutes (600 seconds)
            for image_file in self.sessions_dir.glob("*.jpg"):
                if image_file.stat().st_mtime < (current_time - 600):
                    image_file.unlink()
                    logger.info(f"Deleted old image: {image_file.name}")
            
            # Also delete JSON files older than 24 hours
            for session_file in self.sessions_dir.glob("*.json"):
                if session_file.stat().st_mtime < (current_time - 24 * 3600):
                    session_file.unlink()
        except Exception as e:
            logger.warning(f"Session cleanup failed: {e}")
    
    def create_session(self) -> str:
        session_id = str(uuid.uuid4())[:8]
        self.current_session = {
            "id": session_id,
            "start_time": datetime.now(),
            "detections": [],
            "alerts": [],
            "feedback": [],
            "location_data": []
        }
        return session_id
    
    def save_detection(
        self,
        frame: np.ndarray,
        detections: List[Dict[str, Any]],
        alert_text: str = ""
    ) -> bool:
        """Save detection with optimized storage."""
        if not self.current_session:
            self.create_session()
            
        # Limit session size
        if len(self.current_session["detections"]) >= AppConfig.MAX_SESSION_DETECTIONS:
            self.current_session["detections"].pop(0)
        
        detection_id = len(self.current_session["detections"])
        timestamp = datetime.now()
        
        thumb_path = None
        try:
            # Save compressed thumbnail
            thumb_path = self.sessions_dir / f"{self.current_session['id']}_{detection_id:06d}.jpg"
            success, encoded_img = cv2.imencode(
                '.jpg',
                cv2.cvtColor(frame, cv2.COLOR_RGB2BGR),
                [cv2.IMWRITE_JPEG_QUALITY, 70]
            )
            if success:
                encoded_img.tofile(str(thumb_path))
        except Exception as e:
            logger.error(f"Failed to save thumbnail: {e}")
        
        detection_record = {
            "id": detection_id,
            "timestamp": timestamp,
            "detections": detections,
            "alert": alert_text,
            "thumbnail": str(thumb_path) if thumb_path else None,
            "object_count": len(detections),
            "critical_objects": [
                d for d in detections
                if self._is_critical_object(d["class_name"])
            ]
        }
        
        self.current_session["detections"].append(detection_record)
        
        if alert_text:
            self.current_session["alerts"].append({
                "timestamp": timestamp,
                "alert": alert_text,
                "detection_id": detection_id
            })
        
        # Auto cleanup after each detection to keep memory low
        self._cleanup_old_sessions()
        
        return True
    
    def _is_critical_object(self, class_name: str) -> bool:
        """Check if object is critical."""
        class_lower = class_name.lower()
        return any(
            crit in class_lower
            for crit in AppConfig.CRITICAL_OBJECTS.keys()
        )
    
    def save_feedback(
        self,
        detection_id: int,
        feedback_type: str,
        user_comment: str = ""
    ) -> bool:
        if not self.current_session:
            return False
            
        feedback_record = {
            "timestamp": datetime.now(),
            "detection_id": detection_id,
            "type": feedback_type,
            "comment": user_comment
        }
        
        self.current_session["feedback"].append(feedback_record)
        return True
    
    def get_session_summary(self) -> Optional[Dict[str, Any]]:
        if not self.current_session:
            return None
            
        detections = self.current_session["detections"]
        if not detections:
            return None
            
        total_objects = sum(d["object_count"] for d in detections)
        critical_count = sum(len(d["critical_objects"]) for d in detections)
        alert_count = len(self.current_session["alerts"])
        
        duration = datetime.now() - self.current_session["start_time"]
        
        return {
            "session_id": self.current_session["id"],
            "duration": str(duration).split('.')[0],
            "total_detections": len(detections),
            "total_objects": total_objects,
            "critical_objects": critical_count,
            "alerts_triggered": alert_count,
            "feedback_count": len(self.current_session["feedback"])
        }
