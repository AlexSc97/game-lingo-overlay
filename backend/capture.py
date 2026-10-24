from typing import Optional, Tuple
from PIL import Image
import numpy as np

try:
    import mss
    HAS_MSS = True
except ImportError:
    HAS_MSS = False

from PIL import ImageGrab

def get_screen_size() -> Tuple[int, int]:
    """Returns primary monitor (width, height)."""
    if HAS_MSS:
        with mss.mss() as sct:
            mon = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
            return mon["width"], mon["height"]
    im = ImageGrab.grab()
    return im.size

def capture_region(left: int, top: int, width: int, height: int) -> Image.Image:
    """Captures a specific screen bounding box and returns a PIL Image."""
    if HAS_MSS:
        with mss.mss() as sct:
            bbox = {"left": int(left), "top": int(top), "width": int(width), "height": int(height)}
            sct_img = sct.grab(bbox)
            # Convert mss screen grab (BGRA) to PIL Image (RGB)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            return img
    else:
        bbox = (left, top, left + width, top + height)
        return ImageGrab.grab(bbox=bbox)
