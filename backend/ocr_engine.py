from typing import List, Dict, Any, Optional
import numpy as np
import cv2
from PIL import Image
from rapidocr_onnxruntime import RapidOCR

class GameOCREngine:
    def __init__(self):
        # Initialize RapidOCR with default english/multilingual models
        self.ocr = RapidOCR()

    def preprocess_image(self, pil_image: Image.Image) -> np.ndarray:
        """
        Preprocesses game screenshots for maximum text clarity.
        Hollow Knight & most games use light text on dark or semi-transparent boxes.
        """
        np_img = np.array(pil_image)
        if len(np_img.shape) == 2:
            gray = np_img
        elif np_img.shape[2] == 4:
            # RGBA
            gray = cv2.cvtColor(np_img, cv2.COLOR_RGBA2GRAY)
        else:
            gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)

        # Enhance contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Convert back to 3-channel for RapidOCR
        return cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

    def extract_text(self, pil_image: Image.Image) -> Dict[str, Any]:
        """
        Extracts raw text, line blocks, and confidence scores from image.
        """
        processed_img = self.preprocess_image(pil_image)
        results, elapse_list = self.ocr(processed_img)

        if not results:
            # Fallback with raw image if preprocessing was too aggressive
            raw_bgr = cv2.cvtColor(np.array(pil_image.convert("RGB")), cv2.COLOR_RGB2BGR)
            results, elapse_list = self.ocr(raw_bgr)

        if not results:
            return {
                "full_text": "",
                "lines": [],
                "confidence": 0.0
            }

        lines = []
        confidences = []
        for item in results:
            # item structure: [box_points, text, confidence]
            box, text, score = item
            clean_text = text.strip()
            if clean_text:
                lines.append(clean_text)
                confidences.append(float(score))

        full_text = " ".join(lines)
        avg_confidence = float(np.mean(confidences)) if confidences else 0.0

        return {
            "full_text": full_text,
            "lines": lines,
            "confidence": round(avg_confidence, 2)
        }
