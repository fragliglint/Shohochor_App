from typing import Dict, List, Any

class PremiumThemeEngine:
    """Premium theme engine with 8 beautiful glassmorphic themes."""
    
    THEMES = {
        "cyber_nexus": {
            "name": "Cyber Nexus",
            "primary": "#00f5ff",
            "secondary": "#7b61ff",
            "accent": "#ff2a6d",
            "background": "#0a0a1f",
            "card_bg": "rgba(16, 18, 63, 0.7)",
            "sidebar_bg": "rgba(10, 12, 45, 0.8)",
            "text_primary": "#ffffff",
            "text_secondary": "#b4b9ff",
            "success": "#00ff9d",
            "warning": "#ffcc00",
            "error": "#ff2a6d",
            "border_radius": "16px",
            "shadow": "0 20px 60px rgba(0, 245, 255, 0.15)",
            "gradient": "linear-gradient(135deg, #00f5ff 0%, #7b61ff 50%, #ff2a6d 100%)",
            "backdrop": "blur(20px)",
            "border": "1px solid rgba(255, 255, 255, 0.1)"
        },
        "deep_space": {
            "name": "Deep Space",
            "primary": "#8b5cf6",
            "secondary": "#06b6d4",
            "accent": "#f59e0b",
            "background": "#030712",
            "card_bg": "rgba(17, 24, 39, 0.8)",
            "sidebar_bg": "rgba(3, 7, 18, 0.9)",
            "text_primary": "#f8fafc",
            "text_secondary": "#cbd5e1",
            "success": "#10b981",
            "warning": "#f59e0b",
            "error": "#ef4444",
            "border_radius": "20px",
            "shadow": "0 25px 50px rgba(139, 92, 246, 0.2)",
            "gradient": "linear-gradient(135deg, #8b5cf6 0%, #06b6d4 100%)",
            "backdrop": "blur(25px)",
            "border": "1px solid rgba(255, 255, 255, 0.08)"
        },
        "neon_dream": {
            "name": "Neon Dream",
            "primary": "#ff0080",
            "secondary": "#00ffcc",
            "accent": "#ffcc00",
            "background": "#0a0014",
            "card_bg": "rgba(42, 0, 56, 0.7)",
            "sidebar_bg": "rgba(26, 0, 35, 0.9)",
            "text_primary": "#ffffff",
            "text_secondary": "#ff99e6",
            "success": "#00ff88",
            "warning": "#ffcc00",
            "error": "#ff0066",
            "border_radius": "18px",
            "shadow": "0 20px 60px rgba(255, 0, 128, 0.25)",
            "gradient": "linear-gradient(135deg, #ff0080 0%, #00ffcc 100%)",
            "backdrop": "blur(30px)",
            "border": "1px solid rgba(255, 255, 255, 0.12)"
        },
        "quantum_glass": {
            "name": "Quantum Glass",
            "primary": "#3b82f6",
            "secondary": "#10b981",
            "accent": "#f59e0b",
            "background": "#0f172a",
            "card_bg": "rgba(30, 41, 59, 0.6)",
            "sidebar_bg": "rgba(15, 23, 42, 0.8)",
            "text_primary": "#f1f5f9",
            "text_secondary": "#94a3b8",
            "success": "#10b981",
            "warning": "#f59e0b",
            "error": "#ef4444",
            "border_radius": "24px",
            "shadow": "0 30px 60px rgba(59, 130, 246, 0.15)",
            "gradient": "linear-gradient(135deg, #3b82f6 0%, #10b981 100%)",
            "backdrop": "blur(40px)",
            "border": "1px solid rgba(255, 255, 255, 0.1)"
        },
        "midnight_purple": {
            "name": "Midnight Purple",
            "primary": "#a855f7",
            "secondary": "#ec4899",
            "accent": "#f59e0b",
            "background": "#0f0519",
            "card_bg": "rgba(33, 16, 56, 0.7)",
            "sidebar_bg": "rgba(20, 8, 35, 0.9)",
            "text_primary": "#faf5ff",
            "text_secondary": "#d8b4fe",
            "success": "#10b981",
            "warning": "#f59e0b",
            "error": "#ef4444",
            "border_radius": "22px",
            "shadow": "0 25px 50px rgba(168, 85, 247, 0.2)",
            "gradient": "linear-gradient(135deg, #a855f7 0%, #ec4899 100%)",
            "backdrop": "blur(35px)",
            "border": "1px solid rgba(255, 255, 255, 0.09)"
        },
        "cyberpunk": {
            "name": "Cyberpunk",
            "primary": "#00ff9d",
            "secondary": "#ff2a6d",
            "accent": "#0055ff",
            "background": "#001122",
            "card_bg": "rgba(0, 34, 68, 0.7)",
            "sidebar_bg": "rgba(0, 17, 34, 0.9)",
            "text_primary": "#00ff9d",
            "text_secondary": "#66ffcc",
            "success": "#00ff9d",
            "warning": "#ffcc00",
            "error": "#ff2a6d",
            "border_radius": "12px",
            "shadow": "0 20px 40px rgba(0, 255, 157, 0.3)",
            "gradient": "linear-gradient(135deg, #00ff9d 0%, #0055ff 100%)",
            "backdrop": "blur(20px)",
            "border": "1px solid rgba(0, 255, 157, 0.3)"
        },
        "sunset_oasis": {
            "name": "Sunset Oasis",
            "primary": "#ff6b35",
            "secondary": "#ffa500",
            "accent": "#00ced1",
            "background": "#1a0f0f",
            "card_bg": "rgba(42, 21, 21, 0.7)",
            "sidebar_bg": "rgba(26, 15, 15, 0.9)",
            "text_primary": "#fff5f5",
            "text_secondary": "#ffd7ba",
            "success": "#00ced1",
            "warning": "#ffa500",
            "error": "#ff6b35",
            "border_radius": "20px",
            "shadow": "0 25px 50px rgba(255, 107, 53, 0.2)",
            "gradient": "linear-gradient(135deg, #ff6b35 0%, #ffa500 100%)",
            "backdrop": "blur(30px)",
            "border": "1px solid rgba(255, 255, 255, 0.1)"
        },
        "arctic_ice": {
            "name": "Arctic Ice",
            "primary": "#00b4d8",
            "secondary": "#90e0ef",
            "accent": "#ff9e00",
            "background": "#001219",
            "card_bg": "rgba(0, 42, 59, 0.7)",
            "sidebar_bg": "rgba(0, 18, 25, 0.9)",
            "text_primary": "#e9f5f9",
            "text_secondary": "#a8dadc",
            "success": "#90e0ef",
            "warning": "#ff9e00",
            "error": "#ff6b6b",
            "border_radius": "24px",
            "shadow": "0 30px 60px rgba(0, 180, 216, 0.15)",
            "gradient": "linear-gradient(135deg, #00b4d8 0%, #90e0ef 100%)",
            "backdrop": "blur(40px)",
            "border": "1px solid rgba(255, 255, 255, 0.08)"
        }
    }
    
    @staticmethod
    def get_theme(theme_name: str) -> Dict[str, Any]:
        """Get theme configuration by name."""
        return PremiumThemeEngine.THEMES.get(
            theme_name,
            PremiumThemeEngine.THEMES["cyber_nexus"]
        )
    
    @staticmethod
    def get_theme_names() -> List[str]:
        """Get list of available theme names."""
        return list(PremiumThemeEngine.THEMES.keys())
