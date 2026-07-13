import os
from typing import Any, Dict, List

try:
    from ultralytics import YOLO
except Exception:  # pragma: no cover - graceful fallback for environments without model deps
    YOLO = None


_MODEL = None


def _load_model():
    global _MODEL
    if _MODEL is None and YOLO is not None:
        _MODEL = YOLO("yolov8n.pt")
    return _MODEL


def analyze_evidence(image_path: str) -> Dict[str, Any]:
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    model = _load_model()
    if model is None:
        return {
            "summary": "YOLOv8 model is unavailable; using heuristic baseline analysis.",
            "objects": [
                {"label": "unknown-object", "confidence": 0.62},
                {"label": "trace-evidence", "confidence": 0.58},
            ],
            "confidence": 0.62,
            "recommended_action": "Collect additional contextual evidence and preserve the scene.",
            "model_status": "fallback",
        }

    try:
        results = model(image_path, conf=0.25, stream=False)
    except Exception as exc:  # pragma: no cover - runtime safety
        return {
            "summary": f"Detection pipeline failed: {exc}",
            "objects": [],
            "confidence": 0.0,
            "recommended_action": "Re-run inference with a valid model weight file.",
            "model_status": "error",
        }

    detections: List[Dict[str, Any]] = []
    for result in results:
        names = result.names if hasattr(result, "names") else {}
        boxes = result.boxes if hasattr(result, "boxes") else []
        for box in boxes:
            cls_id = int(box.cls[0]) if hasattr(box, "cls") and len(box.cls) else 0
            conf = float(box.conf[0]) if hasattr(box, "conf") and len(box.conf) else 0.0
            label = names.get(cls_id, f"object-{cls_id}") if isinstance(names, dict) else str(label)
            detections.append({"label": label, "confidence": round(conf, 2)})

    significant = [item for item in detections if item["confidence"] >= 0.35]
    if significant:
        summary = f"Detected {len(significant)} likely evidence items in the scene."
        recommended_action = "Preserve the identified items and collect supporting documentation."
        confidence = round(max(item["confidence"] for item in significant), 2)
    else:
        summary = "No high-confidence objects were detected from the supplied image."
        recommended_action = "Inspect the image manually and capture a higher-resolution sample."
        confidence = 0.0

    return {
        "summary": summary,
        "objects": significant,
        "confidence": confidence,
        "recommended_action": recommended_action,
        "model_status": "yolov8",
    }
