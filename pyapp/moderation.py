import os
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException

from .auth import get_current_user
from .db import videos, plugin_settings

router = APIRouter(prefix="/api/v1/moderation", tags=["moderation"])

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def analyze_stub(file_path: str, watermark: Optional[str], config: dict):
    lower = file_path.lower()
    nudity_score = 0.2
    copyright_score = 0.2
    fraud_score = 0.2
    blur = False
    if "nsfw" in lower or "nude" in lower:
        nudity_score = 0.9
    if "pirated" in lower or "copyright" in lower:
        copyright_score = 0.85
    if "scam" in lower or "fraud" in lower:
        fraud_score = 0.8
    if watermark and watermark.lower() in ["platformx", "justdial"]:
        blur = True
    return {
        "nudity": {"score": nudity_score},
        "copyright": {"score": copyright_score},
        "fraud": {"score": fraud_score},
        "blur": blur
    }

def decide(analysis: dict, config: dict):
    nudity_limit = {"lenient": 0.95, "moderate": 0.8, "strict": 0.6}.get(config.get("nuditySensitivity", "moderate"), 0.8)
    fraud_limit = {"lenient": 0.95, "moderate": 0.8, "strict": 0.6}.get(config.get("fraudSensitivity", "moderate"), 0.8)
    copyright_limit = config.get("copyrightThreshold", 50) / 100.0
    reasons = []
    if analysis["nudity"]["score"] >= nudity_limit:
        reasons.append("nudity")
    if analysis["fraud"]["score"] >= fraud_limit:
        reasons.append("fraud")
    if analysis["copyright"]["score"] >= copyright_limit:
        reasons.append("copyright")
    decision = "rejected" if reasons else "approved"
    return decision, ", ".join(reasons)

@router.post("/analyze")
async def analyze(
    user = Depends(get_current_user),
    video: UploadFile = File(...),
    watermark: Optional[str] = Form(None),
    config: Optional[str] = Form(None),
):
    # Save file
    file_name = f"{int(datetime.utcnow().timestamp())}-{video.filename}"
    file_path = os.path.join(UPLOAD_DIR, file_name)
    with open(file_path, "wb") as f:
        f.write(await video.read())

    # Resolve config and default settings
    user_settings = plugin_settings.find_one({"owner": user["id"]})
    cfg = {"nuditySensitivity": "moderate", "fraudSensitivity": "moderate", "copyrightThreshold": 50}
    if user_settings:
        cfg.update({
            "nuditySensitivity": user_settings.get("nuditySensitivity", cfg["nuditySensitivity"]),
            "fraudSensitivity": user_settings.get("fraudSensitivity", cfg["fraudSensitivity"]),
            "copyrightThreshold": user_settings.get("copyrightThreshold", cfg["copyrightThreshold"]),
        })
    if config:
        import json
        try:
            cfg.update(json.loads(config))
        except Exception:
            pass

    analysis = analyze_stub(file_path, watermark, cfg)
    decision, reason = decide(analysis, cfg)
    doc = {
        "owner": user["id"],
        "filePath": file_path,
        "originalName": video.filename,
        "mimeType": video.content_type,
        "sizeBytes": None,
        "watermark": watermark,
        "config": cfg,
        "analysis": analysis,
        "decision": decision,
        "reason": reason,
        "logs": [{"message": f"Decision: {decision} - {reason}", "at": datetime.utcnow()}],
        "createdAt": datetime.utcnow(),
    }
    inserted = videos.insert_one(doc)
    return {"id": str(inserted.inserted_id), "decision": decision, "reason": reason, "analysis": analysis}

@router.get("/{id}")
def get_result(id: str, user = Depends(get_current_user)):
    from bson import ObjectId
    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")
    doc = videos.find_one({"_id": oid, "owner": user["id"]})
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    doc["id"] = str(doc.pop("_id"))
    return doc

@router.get("")
def list_mod(user = Depends(get_current_user), decision: Optional[str] = None):
    q = {"owner": user["id"]}
    if decision:
        q["decision"] = decision
    items = []
    for d in videos.find(q).sort("createdAt", -1).limit(100):
        d["id"] = str(d.pop("_id"))
        items.append(d)
    return items

@router.post("/settings")
def save_settings(
    user = Depends(get_current_user),
    nuditySensitivity: Optional[str] = Form(None),
    fraudSensitivity: Optional[str] = Form(None),
    copyrightThreshold: Optional[int] = Form(None),
):
    doc = {
        "owner": user["id"],
        "nuditySensitivity": nuditySensitivity or "moderate",
        "fraudSensitivity": fraudSensitivity or "moderate",
        "copyrightThreshold": (copyrightThreshold if isinstance(copyrightThreshold, int) else 50),
        "updatedAt": datetime.utcnow(),
    }
    plugin_settings.update_one({"owner": user["id"]}, {"$set": doc}, upsert=True)
    return doc