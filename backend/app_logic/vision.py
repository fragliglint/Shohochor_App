import time
import logging
import numpy as np
import cv2
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
from ultralytics import YOLO
import easyocr

from .config import AppConfig

logger = logging.getLogger(__name__)

class DetectionEngine:
    """Centralized detection engine."""
    
    @staticmethod
    def yolo_infer_image(
        model: YOLO,
        pil_img: Image.Image,
        conf: float,
        iou: float,
        imgsz: int,
        classes: Optional[List[int]] = None,
        device: str = "cpu"
    ) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """Run YOLO inference with optimized parameters."""
        img_np = np.array(pil_img)
        
        try:
            results = model.predict(
                source=img_np,
                conf=conf,
                iou=iou,
                imgsz=int(imgsz),
                device=device,
                classes=classes,
                verbose=False,
                augment=False
            )
            
            if not results:
                return img_np, []
            
            res = results[0]
            annotated_bgr = res.plot()
            annotated_rgb = annotated_bgr[:, :, ::-1]
            dets: List[Dict[str, Any]] = []
            names = res.names
            
            if getattr(res, "boxes", None) is not None and len(res.boxes) > 0:
                for b in res.boxes:
                    cls_id = int(b.cls.item())
                    if isinstance(names, dict):
                        cls_name = names.get(cls_id, str(cls_id))
                    else:
                        cls_name = str(cls_id)
                    conf_val = float(b.conf.item())
                    xyxy = b.xyxy[0].tolist()
                    dets.append({
                        "class_id": cls_id,
                        "class_name": cls_name,
                        "confidence": conf_val,
                        "box_xyxy": [round(v, 2) for v in xyxy],
                    })
            
            return annotated_rgb, dets
            
        except Exception as e:
            logger.error(f"Inference error: {e}")
            return img_np, []

class ObjectTracker:
    def __init__(self, max_distance: float = 50.0) -> None:
        self.tracked_objects: Dict[int, Dict[str, Any]] = {}
        self.next_id = 0
        self.max_distance = max_distance
        self.frame_width = 640
        
    def update(
        self,
        current_detections: List[Dict[str, Any]],
        frame_width: int
    ) -> List[str]:
        """Update object tracks with improved movement analysis."""
        self.frame_width = frame_width
        movement_alerts: List[str] = []
        
        for det in current_detections:
            x_center = (det["box_xyxy"][0] + det["box_xyxy"][2]) / 2
            y_center = (det["box_xyxy"][1] + det["box_xyxy"][3]) / 2
            width = det["box_xyxy"][2] - det["box_xyxy"][0]
            height = det["box_xyxy"][3] - det["box_xyxy"][1]
            
            best_match_id = self._find_best_match(
                det["class_name"], x_center, y_center
            )
            
            if best_match_id is not None:
                # Update existing track
                movement_alert = self._update_track(
                    best_match_id, x_center, y_center, width, height
                )
                if movement_alert:
                    movement_alerts.append(f"{det['class_name']} is {movement_alert}")
            else:
                # Create new track
                self._create_new_track(
                    det["class_name"], x_center, y_center, width, height
                )
        
        self._cleanup_old_tracks()
        return movement_alerts
    
    def _find_best_match(
        self,
        class_name: str,
        x_center: float,
        y_center: float
    ) -> Optional[int]:
        """Find best matching track for detection."""
        best_match_id = None
        min_distance = float('inf')
        
        for obj_id, track in self.tracked_objects.items():
            if track["class_name"] != class_name:
                continue
                
            last_x, last_y = track["position"]
            distance = np.sqrt((x_center - last_x)**2 + (y_center - last_y)**2)
            
            # Adaptive distance threshold based on object size
            size_factor = np.sqrt(track["size"][0] * track["size"][1]) / 100
            adaptive_threshold = self.max_distance * max(size_factor, 1.0)
            
            if distance < min_distance and distance < adaptive_threshold:
                min_distance = distance
                best_match_id = obj_id
        
        return best_match_id
    
    def _update_track(
        self,
        track_id: int,
        x_center: float,
        y_center: float,
        width: float,
        height: float
    ) -> Optional[str]:
        """Update track and analyze movement."""
        track = self.tracked_objects[track_id]
        track["position"] = (x_center, y_center)
        track["size"] = (width, height)
        track["last_seen"] = time.time()
        
        # Analyze movement with improved logic
        if track["movement_history"]:
            movement_alert = self._analyze_movement_improved(
                track, x_center, y_center, width, height
            )
            track["movement_history"].append(
                (x_center, y_center, width, height, time.time())
            )
            
            # Keep limited history
            if len(track["movement_history"]) > 10:
                track["movement_history"] = track["movement_history"][-10:]
            
            return movement_alert
        else:
            track["movement_history"] = [
                (x_center, y_center, width, height, time.time())
            ]
            return None
    
    def _create_new_track(
        self,
        class_name: str,
        x_center: float,
        y_center: float,
        width: float,
        height: float
    ) -> None:
        """Create a new object track."""
        self.tracked_objects[self.next_id] = {
            "class_name": class_name,
            "position": (x_center, y_center),
            "size": (width, height),
            "first_seen": time.time(),
            "last_seen": time.time(),
            "movement_history": []
        }
        self.next_id += 1
    
    def _analyze_movement_improved(
        self,
        track: Dict[str, Any],
        x_center: float,
        y_center: float,
        width: float,
        height: float
    ) -> Optional[str]:
        """Improved movement analysis with velocity estimation."""
        if len(track["movement_history"]) < 2:
            return None
        
        # Get recent positions with timestamps
        (last_x, last_y, last_w, last_h,
         last_time) = track["movement_history"][-1]
        current_time = time.time()
        time_diff = current_time - last_time
        
        if time_diff < 0.1:
            return None
        
        dx = x_center - last_x
        
        # Calculate velocity (pixels per second)
        velocity_x = dx / time_diff
        
        # Size change analysis
        current_area = width * height
        last_area = last_w * last_h
        area_change = current_area - last_area
        
        # Movement detection with velocity thresholds
        velocity_threshold = self.frame_width * 0.02
        
        if abs(velocity_x) > velocity_threshold:
            direction = "left" if velocity_x < 0 else "right"
            
            if area_change > current_area * 0.1:
                return f"moving closer from your {direction}"
            elif area_change < -current_area * 0.1:
                return f"moving away to your {direction}"
            else:
                return f"crossing from {direction}"
        
        return None
    
    def _cleanup_old_tracks(self) -> None:
        """Remove tracks not seen recently."""
        current_time = time.time()
        self.tracked_objects = {
            k: v for k, v in self.tracked_objects.items()
            if current_time - v["last_seen"] < 5.0
        }

class SceneAnalyzer:
    def __init__(self) -> None:
        self.scene_history: List[Dict[str, Any]] = []
        self.scene_confidences: Dict[str, float] = {}
        
    def analyze_scene(
        self,
        detections: List[Dict[str, Any]],
        frame: np.ndarray,
        frame_count: int
    ) -> Dict[str, Any]:
        """Enhanced scene analysis with confidence scoring."""
        scene_info: Dict[str, Any] = {
            "type": "unknown",
            "density": "low",
            "visibility": "good",
            "hazards": [],
            "summary": "",
            "confidence": 0.0
        }
        
        # Analyze object density with improved logic
        object_count = len(detections)
        scene_info["density"] = self._analyze_density(object_count, frame.shape)
        
        # Enhanced visibility analysis
        scene_info["visibility"] = self._analyze_visibility(frame)
        if scene_info["visibility"] == "low":
            scene_info["hazards"].append("low_visibility")
        
        # Improved scene type classification
        scene_type, confidence = self._classify_scene_type(detections)
        scene_info["type"] = scene_type
        scene_info["confidence"] = confidence
        
        # Generate intelligent scene summary
        scene_info["summary"] = self._generate_scene_summary(scene_info, detections)
        
        # Update history with size limit
        self.scene_history.append(scene_info)
        if len(self.scene_history) > 30:
            self.scene_history.pop(0)
            
        return scene_info
    
    def _analyze_density(
        self,
        object_count: int,
        frame_shape: Tuple[int, int, int]
    ) -> str:
        """Analyze object density relative to frame size."""
        frame_area = frame_shape[0] * frame_shape[1]
        density_ratio = object_count / (frame_area / 10000)
        
        if density_ratio > 2.0:
            return "high"
        elif density_ratio > 1.0:
            return "medium"
        else:
            return "low"
    
    def _analyze_visibility(self, frame: np.ndarray) -> str:
        """Enhanced visibility analysis."""
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        gray_float = np.asarray(gray, dtype=float)
        brightness = float(np.mean(gray_float))
        contrast = float(np.std(gray_float, ddof=0))
        
        if brightness < 50 and contrast < 30:
            return "very low"
        elif brightness < 80:
            return "low"
        elif brightness > 220 and contrast < 40:
            return "very high"
        elif brightness > 180:
            return "high"
        else:
            return "good"
    
    def _classify_scene_type(
        self,
        detections: List[Dict[str, Any]]
    ) -> Tuple[str, float]:
        """Classify scene type with confidence scoring."""
        object_classes = [det["class_name"].lower() for det in detections]
        scores: Dict[str, float] = {}
        
        for scene_type, indicators in AppConfig.SCENE_TYPES.items():
            score = sum(
                1 for obj in object_classes
                if any(indicator in obj for indicator in indicators)
            )
            scores[scene_type] = score / max(len(indicators), 1)
        
        if not scores:
            return "unknown", 0.0
        
        best_scene = max(scores.items(), key=lambda x: x[1])
        
        # Only return if confidence is reasonable
        if best_scene[1] > 0.3:
            return best_scene[0], best_scene[1]
        else:
            return "unknown", best_scene[1]
    
    def _generate_scene_summary(
        self,
        scene_info: Dict[str, Any],
        detections: List[Dict[str, Any]]
    ) -> str:
        """Generate natural language scene summary."""
        parts = []
        
        # Scene context
        if scene_info["density"] == "high":
            parts.append("Crowded area with multiple objects")
        elif scene_info["density"] == "medium":
            parts.append("Moderate traffic area")
        else:
            parts.append("Clear path with few obstacles")
        
        # Critical objects
        critical_objs = [
            det["class_name"] for det in detections
            if any(
                crit in det["class_name"].lower()
                for crit in AppConfig.CRITICAL_OBJECTS.keys()
            )
        ]
        if critical_objs:
            parts.append(f"Watch for {', '.join(set(critical_objs))}")
        
        # Visibility conditions
        if scene_info["visibility"] in ["low", "very low"]:
            parts.append("Low visibility conditions, proceed carefully")
        elif scene_info["visibility"] == "very high":
            parts.append("Bright conditions, watch for glare")
        
        # Scene type context
        if scene_info["type"] == "indoor":
            parts.append("Indoor environment detected")
        elif scene_info["type"] == "transport":
            parts.append("Transportation area, watch for vehicles")
        elif scene_info["type"] == "hazard":
            parts.append("Potential hazard area, be cautious")
        
        return ". ".join(parts) if parts else "Environment appears normal"

class TextReader:
    def __init__(self) -> None:
        self.reader: Optional[Any] = None
        self._initialized = False
        
    def initialize(self) -> bool:
        """Lazy initialization of OCR reader."""
        if not self._initialized:
            try:
                self.reader = easyocr.Reader(['en', 'bn'])
                self._initialized = True
            except Exception as e:
                logger.error(f"OCR initialization failed: {e}")
                return False
        return self._initialized
    
    def extract_text(
        self,
        frame: np.ndarray,
        detection_boxes: Optional[List] = None
    ) -> List[str]:
        """Extract text with optimized performance."""
        if not self.initialize():
            return []
        
        try:
            texts = []
            
            if detection_boxes:
                # Extract text from detection areas only
                for box in detection_boxes:
                    x1, y1, x2, y2 = map(int, box)
                    # Ensure valid ROI
                    if x2 > x1 and y2 > y1 and x1 >= 0 and y1 >= 0:
                        roi = frame[y1:y2, x1:x2]
                        if roi.size > 100:
                            roi_texts = self.reader.readtext(
                                roi, detail=1, paragraph=False
                            )
                            for (bbox, text, conf) in roi_texts:
                                if conf > 0.4:
                                    texts.append(text.strip())
            else:
                # Extract from entire frame but with lower frequency
                results = self.reader.readtext(frame, detail=1, paragraph=False)
                texts = [
                    text.strip() for (bbox, text, conf) in results
                    if conf > 0.4
                ]
            
            return list(set(texts))
            
        except Exception as e:
            logger.error(f"OCR extraction error: {e}")
            return []
