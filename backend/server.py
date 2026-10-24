import asyncio
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.config import load_config, save_config, AppConfig, CaptureRegion
from backend.capture import capture_region, get_screen_size
from backend.ocr_engine import GameOCREngine
from backend.translator import LearningTranslator

app = FastAPI(title="Game Lingo Overlay API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
config: AppConfig = load_config()
ocr_engine: Optional[GameOCREngine] = None
translator: Optional[LearningTranslator] = None

# Connected WebSocket clients (the overlay web windows)
active_connections: List[WebSocket] = []

last_detected_text: str = ""

def get_ocr_engine() -> GameOCREngine:
    global ocr_engine
    if ocr_engine is None:
        ocr_engine = GameOCREngine()
    return ocr_engine

def get_translator() -> LearningTranslator:
    global translator
    if translator is None:
        translator = LearningTranslator(source=config.source_lang, target=config.target_lang)
    return translator

async def broadcast_event(data: dict):
    disconnected = []
    for conn in active_connections:
        try:
            await conn.send_json(data)
        except Exception:
            disconnected.append(conn)
    for conn in disconnected:
        if conn in active_connections:
            active_connections.remove(conn)

def process_screen_capture(reg: Optional[CaptureRegion] = None) -> dict:
    global last_detected_text
    region = reg or config.region
    engine = get_ocr_engine()
    trans = get_translator()

    # Capture region
    img = capture_region(region.left, region.top, region.width, region.height)
    ocr_result = engine.extract_text(img)
    full_text = ocr_result["full_text"]

    if not full_text.strip():
        return {
            "status": "empty",
            "message": "No text detected in selected region",
            "ocr": ocr_result,
            "analysis": None
        }

    analysis = trans.analyze_learning_block(full_text)
    last_detected_text = full_text

    return {
        "status": "success",
        "ocr": ocr_result,
        "analysis": analysis
    }

@app.get("/api/config")
def get_current_config():
    return config

@app.post("/api/config")
def update_current_config(new_config: AppConfig):
    global config
    config = new_config
    save_config(config)
    return {"status": "ok", "config": config}

@app.get("/api/screen")
def get_screen_info():
    w, h = get_screen_size()
    return {"width": w, "height": h, "current_region": config.region}

@app.post("/api/capture")
async def trigger_capture():
    res = process_screen_capture()
    await broadcast_event({"type": "translation_update", "payload": res})
    return res

class DirectAnalyzeRequest(BaseModel):
    text: str

@app.post("/api/analyze-text")
async def analyze_text(req: DirectAnalyzeRequest):
    trans = get_translator()
    analysis = trans.analyze_learning_block(req.text)
    payload = {
        "status": "success",
        "ocr": {"full_text": req.text, "confidence": 1.0, "lines": [req.text]},
        "analysis": analysis
    }
    await broadcast_event({"type": "translation_update", "payload": payload})
    return payload

@app.get("/api/vocab")
def get_vocabulary():
    trans = get_translator()
    return {"count": len(trans.cache), "words": trans.cache}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    # Send initial status & config
    await websocket.send_json({"type": "init", "config": config.model_dump()})

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            if action == "capture":
                res = process_screen_capture()
                await broadcast_event({"type": "translation_update", "payload": res})
            elif action == "update_region":
                region_data = data.get("region", {})
                config.region = CaptureRegion(**region_data)
                save_config(config)
                await broadcast_event({"type": "config_update", "config": config.model_dump()})
            elif action == "analyze_text":
                text = data.get("text", "")
                trans = get_translator()
                analysis = trans.analyze_learning_block(text)
                payload = {
                    "status": "success",
                    "ocr": {"full_text": text, "confidence": 1.0, "lines": [text]},
                    "analysis": analysis
                }
                await broadcast_event({"type": "translation_update", "payload": payload})
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)

# Auto-capture background loop
auto_detect_task = None

async def auto_detect_loop():
    while True:
        try:
            if config.auto_detect:
                engine = get_ocr_engine()
                img = capture_region(config.region.left, config.region.top, config.region.width, config.region.height)
                ocr_result = engine.extract_text(img)
                text = ocr_result["full_text"].strip()
                global last_detected_text
                if text and text != last_detected_text:
                    res = process_screen_capture()
                    await broadcast_event({"type": "translation_update", "payload": res})
        except Exception as e:
            print(f"[AutoDetect] Error in loop: {e}")
        await asyncio.sleep(max(0.5, config.auto_detect_interval_sec))

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(auto_detect_loop())

# Mount frontend static files
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
