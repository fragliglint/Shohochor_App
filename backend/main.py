import io
import logging
import time
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import numpy as np
import cv2

from app_logic import (
    AppConfig,
    DeviceManager,
    DetectionEngine,
    ObjectTracker,
    SceneAnalyzer,
    TextReader,
    TTSManager,
    AlertGenerator,
    EmergencyHandler,
    SessionManager,
    LiveLocationManager,
    MapManager,
    AnalyticsDashboard
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state
class AppState:
    model = None
    object_tracker = ObjectTracker()
    scene_analyzer = SceneAnalyzer()
    text_reader = TextReader()
    session_manager = SessionManager()
    analytics = AnalyticsDashboard()
    location_manager = LiveLocationManager()
    map_manager = MapManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # Load custom model
    AppState.model = DeviceManager.load_model("best.pt") 
    if not AppState.model:
        logger.warning("YOLO model failed to load. Inference will fail.")
    
    logger.info("Initializing OCR...")
    AppState.text_reader.initialize()
    
    yield
    # Shutdown
    logger.info("Shutting down...")

app = FastAPI(title="Shohochor API", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Shohochor API is running"}

@app.get("/health")
async def health_check():
    """Simple health check endpoint for connectivity testing."""
    return {
        "status": "ok",
        "message": "Backend is reachable!",
        "timestamp": time.time()
    }

@app.get("/test")
async def test_page():
    """HTML test page for browser-based connectivity testing."""
    from fastapi.responses import HTMLResponse
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Shohochor Backend Test</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 600px;
                margin: 50px auto;
                padding: 20px;
                background: #1a1a1a;
                color: #fff;
            }
            .success { color: #4ade80; font-size: 24px; font-weight: bold; }
            .info { background: #334155; padding: 15px; border-radius: 8px; margin: 20px 0; }
            button {
                background: #3b82f6;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 16px;
                cursor: pointer;
                margin: 10px 5px;
            }
            button:active { background: #2563eb; }
        </style>
    </head>
    <body>
        <h1>✅ Backend Connected!</h1>
        <p class="success">If you can see this page, your phone CAN reach the backend!</p>
        
        <div class="info">
            <h3>Connection Info:</h3>
            <p><strong>Backend URL:</strong> http://10.109.219.57:8000</p>
            <p><strong>Time:</strong> <span id="time"></span></p>
        </div>
        
        <button onclick="testAPI()">Test API Endpoint</button>
        <button onclick="location.reload()">Refresh</button>
        
        <div id="result" style="margin-top: 20px;"></div>
        
        <script>
            document.getElementById('time').textContent = new Date().toLocaleString();
            
            async function testAPI() {
                const result = document.getElementById('result');
                result.innerHTML = '<p>Testing /health endpoint...</p>';
                try {
                    const response = await fetch('/health');
                    const data = await response.json();
                    result.innerHTML = '<p class="success">✅ API Test Successful!</p><pre>' + JSON.stringify(data, null, 2) + '</pre>';
                } catch (error) {
                    result.innerHTML = '<p style="color: red;">❌ API Test Failed: ' + error.message + '</p>';
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/location/address")
async def get_address_from_coords(lat: float, lon: float, lang: str = "en"):
    """
    Reverse geocoding: Convert GPS coordinates to human-readable address.
    Uses Nominatim (OpenStreetMap) - free, no API key needed.
    """
    try:
        import httpx
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&accept-language={lang}"
        headers = {'User-Agent': 'Shohochor/1.0'}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10.0)
            data = response.json()
            
        address = data.get('display_name', 'Location unknown')
        
        # Extract meaningful parts for natural speech
        addr_parts = data.get('address', {})
        road = addr_parts.get('road', '')
        neighbourhood = addr_parts.get('neighbourhood', addr_parts.get('suburb', ''))
        city = addr_parts.get('city', addr_parts.get('state_district', ''))
        
        # Build natural address
        speech_parts = [p for p in [road, neighbourhood, city] if p]
        natural_address = ', '.join(speech_parts) if speech_parts else address.split(',')[0]
        
        return {
            "address": natural_address,
            "full_address": address,
            "coordinates": {"lat": lat, "lon": lon}
        }
    except Exception as e:
        logger.error(f"Reverse geocoding failed: {e}")
        return {"address": f"Latitude {lat:.4f}, Longitude {lon:.4f}"}

@app.post("/infer/frame")
async def infer_frame(
    file: UploadFile = File(...),
    conf: float = 0.25,
    iou: float = 0.45,
    voice_enabled: bool = True,
    lang: str = "en"  # "en" or "bn"
):
    if not AppState.model:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        contents = await file.read()
        pil_img = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # Inference
        annotated_img, detections = DetectionEngine.yolo_infer_image(
            model=AppState.model,
            pil_img=pil_img,
            conf=conf,
            iou=iou,
            imgsz=640,
            device=DeviceManager.get_device_str_for_yolo()
        )
        
        # Object Tracking
        movement_alerts = AppState.object_tracker.update(detections, pil_img.width)
        
        # Scene Analysis
        scene_info = AppState.scene_analyzer.analyze_scene(
            detections, np.array(pil_img), 1
        )
        
        # Alert Generation
        english_alert, bangla_alert = AlertGenerator.generate_intelligent_alert(
            detections,
            pil_img.width,
            pil_img.height,
            movement_alerts,
            scene_info["summary"],
            [] # User priorities could be passed in request
        )
        
        alert_text = english_alert if lang == "en" else bangla_alert
        
        # Emergency Check
        emergency_msg = EmergencyHandler.check_emergency(detections)
        if emergency_msg:
            alert_text = emergency_msg # Override with emergency
        
        # TTS Generation (Optional - client can do it, but we provide URL or bytes if needed)
        # For now, we'll just return the text and let the client handle TTS or request audio separately
        # If we wanted to return audio, we could return a base64 string or a separate endpoint
        
        # Save to session (async)
        # We need a session ID. For now, we'll just log it or save to a default session
        # In a real app, pass session_id in headers
        AppState.session_manager.save_detection(
            np.array(pil_img), detections, alert_text
        )
        
        # Update Analytics
        AppState.analytics.update_analytics(detections, scene_info, alert_text)
        
        return JSONResponse({
            "detections": detections,
            "alert_text": alert_text,
            "scene_summary": scene_info["summary"],
            "emergency": bool(emergency_msg),
            "movement_alerts": movement_alerts
        })
        
    except Exception as e:
        logger.error(f"Inference failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/session/save")
async def save_session_data(data: Dict[str, Any]):
    # Endpoint to save manual feedback or extra data
    return {"status": "success"}

@app.get("/tts")
async def get_tts(text: str, lang: str = "en"):
    try:
        audio_bytes = TTSManager.generate_speech(text, lang)
        # Return as streaming response or base64
        # For simplicity, let's return base64 in JSON or raw bytes
        # Returning raw bytes is better for media players
        from fastapi.responses import Response
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
