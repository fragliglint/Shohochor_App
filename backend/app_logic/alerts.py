from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict
from .config import AppConfig
from .audio import TTSManager

class AlertGenerator:
    """Centralized alert generation with improved logic."""
    
    @staticmethod
    def get_object_position(frame_width: float, x_center: float) -> str:
        """Determine object position with improved zones."""
        if x_center < frame_width * 0.3:
            return "left"
        elif x_center > frame_width * 0.7:
            return "right"
        elif x_center < frame_width * 0.4:
            return "slightly left"
        elif x_center > frame_width * 0.6:
            return "slightly right"
        else:
            return "ahead"
    
    @staticmethod
    def estimate_distance(
        box_height: float,
        frame_height: float,
        object_type: str = "general"
    ) -> str:
        """Improved distance estimation with object type consideration."""
        if box_height == 0:
            return "unknown"
        
        ratio = box_height / frame_height
        
        # Adjust thresholds based on object type
        if object_type in ["person", "car", "bus", "truck"]:
            # Larger objects have different distance perception
            if ratio > 0.5:
                return "very close"
            elif ratio > 0.25:
                return "close"
            elif ratio > 0.12:
                return "moderate"
            else:
                return "far"
        else:
            # General objects
            if ratio > 0.6:
                return "very close"
            elif ratio > 0.3:
                return "close"
            elif ratio > 0.15:
                return "moderate"
            else:
                return "far"
    
    @staticmethod
    def get_priority_message(
        objects_detected: List[str],
        user_priorities: List[str]
    ) -> Optional[str]:
        """Get priority message with improved criticality assessment."""
        detected_lower = [obj.lower() for obj in objects_detected]
        
        # Check user priorities first
        for user_priority in user_priorities:
            if any(user_priority in obj for obj in detected_lower):
                return f"Priority object detected: {user_priority}"
        
        # Check critical objects
        for critical_obj, message in AppConfig.CRITICAL_OBJECTS.items():
            if any(critical_obj in obj for obj in detected_lower):
                return message
        
        return None
    
    @staticmethod
    def generate_intelligent_alert(
        detections: List[Dict[str, Any]],
        frame_width: int,
        frame_height: int,
        movement_alerts: List[str],
        scene_summary: str,
        user_priorities: List[str]
    ) -> Tuple[str, str]:
        """Generate intelligent alerts with spatial awareness."""
        if not detections and not movement_alerts:
            return "Path is clear", "রাস্তাটি পরিষ্কার"
        
        # Check for priority and critical objects first
        object_names = [d["class_name"] for d in detections]
        priority_msg = AlertGenerator.get_priority_message(
            object_names, user_priorities
        )
        if priority_msg:
            return priority_msg, priority_msg
        
        alert_parts = []
        
        # Include movement alerts
        if movement_alerts:
            alert_parts.extend(movement_alerts)
        
        # Group objects by position and distance
        position_groups = defaultdict(list)
        
        for det in detections:
            x_center = (det["box_xyxy"][0] + det["box_xyxy"][2]) / 2
            position = AlertGenerator.get_object_position(frame_width, x_center)
            
            box_height = det["box_xyxy"][3] - det["box_xyxy"][1]
            distance = AlertGenerator.estimate_distance(
                box_height, frame_height, det["class_name"]
            )
            
            obj_info = f"{det['class_name'].replace('_', ' ')} {distance}"
            position_groups[position].append(obj_info)
        
        # Build spatial description
        if position_groups.get("ahead"):
            alert_parts.append("Ahead: " + ", ".join(position_groups["ahead"]))
        if position_groups.get("slightly left"):
            alert_parts.append(
                "Slightly left: " + ", ".join(position_groups["slightly left"])
            )
        if position_groups.get("slightly right"):
            alert_parts.append(
                "Slightly right: " + ", ".join(position_groups["slightly right"])
            )
        if position_groups.get("left"):
            alert_parts.append("Left: " + ", ".join(position_groups["left"]))
        if position_groups.get("right"):
            alert_parts.append("Right: " + ", ".join(position_groups["right"]))
        
        # Add scene context
        if scene_summary and any(
            word in scene_summary.lower()
            for word in ["crowded", "busy", "traffic"]
        ):
            alert_parts.append("Busy area ahead, proceed with caution")
        
        english_msg = ". ".join(alert_parts) if alert_parts else "Path is clear"
        
        # Simplified Bangla translation
        bangla_msg = AlertGenerator._translate_to_bangla(english_msg)
        
        return english_msg, bangla_msg
    
    @staticmethod
    def _translate_to_bangla(english_text: str) -> str:
        """Enhanced translation to Bangla using AppConfig."""
        translations = {
            "Path is clear": "রাস্তাটি পরিষ্কার",
            "Ahead": "সামনে",
            "Left": "বামে",
            "Right": "ডানে",
            "Slightly left": "সামান্য বামে",
            "Slightly right": "সামান্য ডানে",
            "close": "কাছে",
            "far": "দূরে",
            "moderate": "মাঝারি দূরত্বে",
            "very close": "খুব কাছে",
            "is moving closer from your": "আপনার দিকে আসছে",
            "is moving away to your": "আপনার থেকে দূরে সরে যাচ্ছে",
            "crossing from": "অতিক্রম করছে",
            "Busy area ahead, proceed with caution": "সামনে ব্যস্ত এলাকা, সাবধানে চলুন",
            "Priority object detected": "জরুরী বস্তু সনাক্ত করা হয়েছে",
            "Watch for": "লক্ষ্য রাখুন",
            "Low visibility conditions": "স্বল্প দৃশ্যমানতা",
            "proceed carefully": "সাবধানে চলুন"
        }
        
        bangla_text = english_text
        
        # Apply phrase translations first
        for eng, bn in translations.items():
            bangla_text = bangla_text.replace(eng, bn)
            
        # Apply object translations from AppConfig
        # Sort by length descending to avoid partial matches
        sorted_objects = sorted(AppConfig.EN_TO_BN.keys(), key=len, reverse=True)
        
        for obj_name in sorted_objects:
            bn_name = AppConfig.EN_TO_BN[obj_name]
            # Try both original and lowercase matches
            bangla_text = bangla_text.replace(obj_name, bn_name)
            bangla_text = bangla_text.replace(obj_name.lower(), bn_name)
        
        return bangla_text

class EmergencyHandler:
    """Handle emergency protocols."""
    
    @staticmethod
    def check_emergency(detections: List[Dict[str, Any]]) -> Optional[str]:
        """Check for critical objects and return emergency message if any."""
        critical_detected = []
        for det in detections:
            if any(
                crit in det["class_name"].lower()
                for crit in ["fire", "knife", "gun"]
            ):
                critical_detected.append(det["class_name"])
        
        if critical_detected:
            return (
                f"EMERGENCY: {', '.join(critical_detected)} detected! "
                "Seek safety immediately!"
            )
        return None
