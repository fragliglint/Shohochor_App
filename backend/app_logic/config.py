from typing import Dict, List

class AppConfig:
    """Centralized configuration management."""
    
    CRITICAL_OBJECTS = {
        "fire": "Fire detected! Move away immediately!",
        "knife": "Sharp object detected! Be careful!",
        "gun": "Weapon detected! Seek safety!",
        "car": "Vehicle approaching! Move aside!",
        "bus": "Bus approaching! Move aside!",
        "truck": "Large vehicle! Move aside!",
        "stairs": "Stairs ahead, proceed with caution"
    }

    PRIORITY_LEVELS = {
        "high": ["fire", "knife", "gun", "car", "bus", "truck"],
        "medium": ["stairs", "bicycle", "motorcycle", "person"],
        "low": ["tree", "bench", "sign", "building"]
    }

    SCENE_TYPES = {
        "indoor": ["room", "hallway", "stairs", "elevator"],
        "outdoor": ["street", "park", "crosswalk", "building"],
        "transport": ["car", "bus", "bicycle", "motorcycle"],
        "hazard": ["fire", "water", "construction", "dark"]
    }

    EN_TO_BN = {
        "Bench": "টি বেঞ্চ", "Bicycle": "টি সাইকেল", "Bike": "টি বাইক",
        "Boat": "টি নৌকা", "Bus": "টি বাস", "CNG": "টি সিএনজি",
        "Car": "টি গাড়ি", "Cat": "টি বিড়াল",
        "Construction Element": "টি নির্মাণ উপকরণ",
        "Construction Vehicle": "টি নির্মাণ যানবাহন",
        "Crosswalk": "টি জেব্রা ক্রসিং",
        "Divider": "টি ডিভাইডার", "Dog": "টি কুকুর",
        "Dustbin": "টি ডাস্টবিন",
        "Fence": "টি বেড়া", "Footpath": "টি পথচারী ফটক",
        "Garbage": "টি আবর্জনা",
        "Garbage Vehicle": "টি আবর্জনা গাড়ি", "Manhole": "টি ম্যানহোল",
        "Over Bridge": "টি ওভার ব্রিজ", "Person": "জন ব্যক্তি",
        "Planter": "টি গাছের টব", "Pole": "টি খুঁটি", "Pond": "টি পুকুর",
        "Pothole": "টি গর্ত", "Rickshaw": "টি রিকশা",
        "Road Block": "টি রোড ব্লক",
        "Shop": "টি দোকান", "Stairs": "টি সিঁড়ি",
        "Street Vendor": "টি টং",
        "Traffic Light": "টি ট্রাফিক লাইট", "Tree": "টি গাছ",
        "Truck": "টি ট্রাক",
        "Wall": "টি দেওয়াল", "Watery Road": "টি পানিবাহী রাস্তা"
    }
    
    # Performance settings
    MAX_HISTORY_LENGTH = 1000
    MAX_SESSION_DETECTIONS = 500
    FRAME_SKIP_INTERVAL = 3
    AUDIO_MIN_INTERVAL = 3.0
