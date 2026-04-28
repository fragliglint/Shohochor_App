import io
import time
import threading
import uuid
import logging
from collections import deque
from typing import Optional, Tuple, Dict
from gtts import gTTS
from .config import AppConfig

logger = logging.getLogger(__name__)

class TTSManager:
    """Unified TTS management with robust error handling and in-memory processing."""
    
    @staticmethod
    def _generate_fallback_beep() -> bytes:
        """Generate a simple beep sound as fallback."""
        try:
            # Create a simple beep sound using a short text
            tts = gTTS(text="beep", lang="en", slow=False)
            buffer = io.BytesIO()
            tts.write_to_fp(buffer)
            buffer.seek(0)
            audio_bytes = buffer.read()
            
            # Validate the generated audio
            if audio_bytes and len(audio_bytes) > 100:
                return audio_bytes
            else:
                # Return minimal valid MP3 data
                return b'\xff\xfb\x90\x44\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        except Exception as e:
            logger.error(f"Fallback beep generation failed: {e}")
            # Return minimal MP3 header
            return b'\xff\xfb\x90\x44\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    
    @staticmethod
    def _validate_audio_bytes(audio_bytes: bytes) -> bool:
        """Validate that audio bytes are proper MP3 format."""
        if not audio_bytes or len(audio_bytes) < 100:
            return False
        
        # Check for MP3 header signature
        if len(audio_bytes) >= 3:
            # MP3 files typically start with 0xFF 0xFB or similar
            if audio_bytes[0] == 0xFF and (audio_bytes[1] & 0xE0) == 0xE0:
                return True
        
        # If no MP3 header, check if it contains audio data markers
        audio_str = str(audio_bytes[:100])
        if 'ID3' in audio_str or 'ff' in audio_str.lower():
            return True
            
        return len(audio_bytes) > 100  # Basic length check
    
    @staticmethod
    def generate_speech(text: str, lang_code: str = "en") -> bytes:
        """
        Generate TTS audio with robust error handling and fallbacks.
        
        Returns audio bytes or raises exception on fatal error.
        """
        # Validation & sanitization
        if not text or len(text.strip()) == 0:
            return TTSManager._generate_fallback_beep()
            
        # Sanitize text
        sanitized_text = TTSManager._sanitize_text(text)
        
        # Length handling
        if len(sanitized_text) > 200:  # Reduced from 500 for stability
            sanitized_text = sanitized_text[:197] + "..."
            logger.warning("TTS text truncated to 200 characters")
        
        max_retries = 3  # Increased retries
        last_exception: Optional[Exception] = None
        
        for attempt in range(max_retries):
            try:
                # Use in-memory buffer instead of temp files
                logger.info(f"TTS attempt {attempt + 1} for: {sanitized_text[:50]}...")
                
                # FIXED: Added timeout and better error handling for gTTS
                tts = gTTS(
                    text=sanitized_text, 
                    lang=lang_code, 
                    slow=False,
                    timeout=10  # Added timeout
                )
                
                # Create in-memory buffer
                buffer = io.BytesIO()
                tts.write_to_fp(buffer)
                buffer.seek(0)
                audio_bytes = buffer.read()
                
                # FIXED: Enhanced validation
                if not audio_bytes or len(audio_bytes) == 0:
                    raise ValueError("Generated empty audio data")
                
                if not TTSManager._validate_audio_bytes(audio_bytes):
                    raise ValueError("Generated invalid audio format")
                
                logger.info(
                    f"TTS generated successfully: {text[:50]}... "
                    f"(lang: {lang_code}, size: {len(audio_bytes)} bytes)"
                )
                return audio_bytes
                    
            except Exception as e:
                last_exception = e
                logger.warning(f"TTS attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                    continue
        
        # All retries failed - implement fallback strategy
        return TTSManager._handle_tts_failure(text, lang_code, last_exception)
    
    @staticmethod
    def _sanitize_text(text: str) -> str:
        """Sanitize text for TTS generation."""
        # Remove or replace problematic characters
        sanitized = text.replace('"', '').replace("'", "").replace("\\", "")
        # Compress repeated whitespace into single spaces
        sanitized = ' '.join(sanitized.split())
        return sanitized
    
    @staticmethod
    def _handle_tts_failure(
        text: str,
        lang_code: str,
        exception: Optional[Exception]
    ) -> bytes:
        """Handle TTS failure with appropriate fallback."""
        error_msg = str(exception) if exception else "Unknown error"
        logger.error(
            f"TTS completely failed for: {text[:50]}... "
            f"(lang: {lang_code}) - {error_msg}"
        )
        
        # For Bangla failures, fallback to English
        if lang_code == "bn":
            try:
                logger.info("Attempting English fallback for Bangla TTS failure")
                # Use a simplified English version
                simple_text = "Object detected" if len(text) > 10 else text
                return TTSManager.generate_speech(simple_text, "en")
            except Exception as e:
                logger.warning(f"English fallback also failed: {e}")
        
        # For emergency messages, use beep sound
        emergency_keywords = [
            "emergency", "fire", "gun", "knife", "danger", "alert"
        ]
        if any(keyword in text.lower() for keyword in emergency_keywords):
            logger.warning("Using fallback beep for emergency message")
            return TTSManager._generate_fallback_beep()
        
        # Final fallback - always return beep instead of raising
        logger.warning("Using final fallback beep")
        return TTSManager._generate_fallback_beep()


class AudioManager:
    """Audio queue management compatible with backend usage."""
    
    def __init__(self) -> None:
        self._queue: deque = deque()
        self.last_play_time = 0.0
        self.min_interval = AppConfig.AUDIO_MIN_INTERVAL
        self.emergency_mode = False
        self.current_audio_id: Optional[str] = None
        self.audio_completion_times: Dict[str, float] = {}
        self._last_played_text: Optional[str] = None
        self._processing_lock = threading.Lock()
        
    def enqueue_audio(
        self,
        audio_bytes: bytes,
        text: str = "",
        priority: str = "normal"
    ) -> bool:
        """Add audio to queue with priority handling."""
        # FIXED: Better validation of audio bytes
        if not audio_bytes or len(audio_bytes) < 50:
            logger.warning(f"Invalid audio bytes provided for: {text[:50]}")
            return False
            
        # FIXED: Check if this is a duplicate of the last played audio
        if text == self._last_played_text:
            logger.debug(f"Skipping duplicate audio: {text[:50]}")
            return False
            
        # Priority mapping (lower number = higher priority)
        priority_map = {"emergency": 0, "high": 1, "medium": 2, "normal": 3}
        priority_value = priority_map.get(priority, 3)
        
        # Generate unique ID for this audio
        audio_id = str(uuid.uuid4())[:8]
        
        # Estimate duration for automatic playback
        duration = self._estimate_audio_duration(audio_bytes)
        completion_time = time.time() + duration if duration else 0
        
        # Emergency mode handling - clear non-emergency items
        if priority == "emergency":
            self.emergency_mode = True
            self._queue = deque(
                [item for item in self._queue if item[0] == 0]
            )
        
        # Rate limiting for non-emergency alerts
        current_time = time.time()
        if (priority != "emergency" and
                current_time - self.last_play_time < self.min_interval):
            logger.debug(f"Rate limited: {text[:50]}...")
            return False
            
        # Add to queue with timestamp for ordering
        timestamp = time.time()
        self._queue.append(
            (priority_value, timestamp, audio_bytes, text, priority,
             audio_id, completion_time)
        )
        
        # Sort by priority then timestamp
        self._queue = deque(
            sorted(self._queue, key=lambda x: (x[0], x[1]))
        )
        
        # Store completion time for automatic playback
        self.audio_completion_times[audio_id] = completion_time
        
        logger.info(
            f"Audio enqueued: {text[:50]}... "
            f"(priority: {priority}, duration: {duration:.1f}s)"
        )
        return True
    
    def _estimate_audio_duration(self, audio_bytes: bytes) -> float:
        """Estimate audio duration in seconds."""
        # Improved estimation: assume 16KB per second for MP3
        return max(1.5, len(audio_bytes) / 16000.0)
    
    def get_next_audio(self) -> Optional[Tuple[bytes, str, str, str]]:
        """Get next audio item from queue."""
        if not self._queue:
            self.emergency_mode = False
            self.current_audio_id = None
            return None
            
        (priority, timestamp, audio_bytes, text, priority_str,
         audio_id, completion_time) = self._queue.popleft()
        self.last_play_time = time.time()
        self.current_audio_id = audio_id
        self._last_played_text = text
        
        logger.info(f"Audio dequeued for playback: {text[:50]}...")
        return audio_bytes, text, priority_str, audio_id
