import json
from pathlib import Path
from pydantic import BaseModel

CONFIG_FILE = Path(__file__).resolve().parent.parent / "config.json"

class CaptureRegion(BaseModel):
    # Normalized or absolute coordinates
    # Default is typical dialogue area (centered at bottom or top-center of a 1920x1080 screen)
    left: int = 400
    top: int = 700
    width: int = 1120
    height: int = 260

class AppConfig(BaseModel):
    region: CaptureRegion = CaptureRegion()
    source_lang: str = "en"
    target_lang: str = "es"
    theme: str = "void" # void (Hollow Knight), dark-glass, high-contrast
    auto_detect: bool = False
    auto_detect_interval_sec: float = 1.0
    overlay_opacity: float = 0.92
    font_size: int = 18
    show_pronunciation: bool = True

def load_config() -> AppConfig:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return AppConfig(**data)
        except Exception as e:
            print(f"[Config] Error loading config: {e}. Using defaults.")
    return AppConfig()

def save_config(config: AppConfig) -> None:
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config.model_dump(), f, indent=2)
    except Exception as e:
        print(f"[Config] Error saving config: {e}")
