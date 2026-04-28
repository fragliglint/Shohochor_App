import torch
import logging
from ultralytics import YOLO
from typing import Optional

logger = logging.getLogger(__name__)

class DeviceManager:
    """Manage device selection and optimization."""
    
    @staticmethod
    def get_device_str_for_yolo() -> str:
        """Get optimal device string for YOLO."""
        if torch.cuda.is_available():
            return "cuda"
        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            return "mps"
        return "cpu"
    
    @staticmethod
    def get_device_human() -> str:
        """Get human-readable device name."""
        if torch.cuda.is_available():
            return "GPU (CUDA)"
        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            return "GPU (MPS)"
        return "CPU"
    
    @staticmethod
    def load_model(weights_path: str) -> Optional[YOLO]:
        """Load YOLO model with error handling."""
        try:
            # In a real backend, we might check file existence differently or download it
            model = YOLO(weights_path)
            logger.info(
                f"Model loaded successfully on {DeviceManager.get_device_human()}"
            )
            return model
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return None
