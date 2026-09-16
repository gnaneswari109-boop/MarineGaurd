from abc import ABC, abstractmethod
from pathlib import Path
import hashlib
from typing import Any

class ModelAdapter(ABC):
    @abstractmethod
    def detect(self, image: Any) -> list[dict]: ...

class DemoModel(ModelAdapter):
    """Stable image-dependent detections for a transparent prototype demo."""
    def detect(self, image: Any) -> list[dict]:
        h, w = image.shape[:2]
        seed = int(hashlib.sha256(image.tobytes()).hexdigest()[:8], 16)
        base = [("Ghost Net", .94, .17, .25, .32, .21), ("Artificial Debris", .81, .58, .55, .18, .14),
                ("Pipe", .77, .32, .70, .42, .08), ("Natural Formation", .63, .72, .18, .16, .13)]
        shift = ((seed % 13) - 6) / 250
        return [{"object_class": c, "raw_confidence": conf, "x": max(0, (x+shift)*w), "y": y*h, "w": bw*w, "h": bh*h}
                for c, conf, x, y, bw, bh in base]

class YOLOModel(ModelAdapter):
    def __init__(self, weights: Path):
        from ultralytics import YOLO
        self.model = YOLO(str(weights))
    def detect(self, image: Any) -> list[dict]:
        result = self.model(image, verbose=False)[0]
        return [{"object_class": result.names[int(b.cls[0])], "raw_confidence": float(b.conf[0]), "x": float(b.xyxy[0][0]), "y": float(b.xyxy[0][1]), "w": float(b.xyxy[0][2]-b.xyxy[0][0]), "h": float(b.xyxy[0][3]-b.xyxy[0][1])} for b in result.boxes]

def get_model() -> tuple[ModelAdapter, str]:
    weights = Path(__file__).resolve().parents[3] / "models" / "best.pt"
    if weights.exists():
        try: return YOLOModel(weights), "YOLO"
        except Exception: pass
    return DemoModel(), "Demo Model"
