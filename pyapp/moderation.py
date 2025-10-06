import os
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, List
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from .moderation_engine import ModerationEngine
from .database import VideoDatabase

router = APIRouter(prefix="/moderation", tags=["moderation"])
templates = Jinja2Templates(directory="templates")

# Initialize components
moderation_engine = ModerationEngine()
video_db = VideoDatabase()

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Web Interface Routes
@router.get("/", response_class=HTMLResponse)
async def moderation_dashboard(request: Request):
    """Main dashboard for video moderation system."""
    stats = moderation_engine.get_moderation_statistics()
    recent_decisions = moderation_engine.get_recent_decisions(5)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": stats,
        "recent_decisions": recent_decisions
    })

@router.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    """Video upload page."""
    return templates.TemplateResponse("upload.html", {"request": request})

@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Configuration settings page."""
    current_config = moderation_engine._get_default_moderation_config()
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "config": current_config
    })

@router.get("/results", response_class=HTMLResponse)
async def results_page(request: Request):
    """Results and analytics page."""
    all_results = video_db.get_all_results()
    stats = moderation_engine.get_moderation_statistics()
    
    return templates.TemplateResponse("results.html", {
        "request": request,
        "results": all_results,
        "stats": stats
    })

# API Routes
@router.post("/api/analyze")
async def analyze_video(
    video: UploadFile = File(...),
    watermark: Optional[str] = Form(None),
    config: Optional[str] = Form(None),
):
    """
    Analyze uploaded video for content violations.
    """
    try:
        # Validate file type
        if not video.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        file_ext = os.path.splitext(video.filename)[1].lower()
        supported_formats = ['.mp4', '.mov', '.avi', '.wmv', '.mkv', '.flv']
        
        if file_ext not in supported_formats:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file format. Supported formats: {', '.join(supported_formats)}"
            )
        
        # Save uploaded file
        file_id = str(uuid.uuid4())
        file_name = f"{file_id}_{video.filename}"
        file_path = os.path.join(UPLOAD_DIR, file_name)
        
        with open(file_path, "wb") as f:
            content = await video.read()
            f.write(content)
        
        # Parse configuration
        moderation_config = moderation_engine._get_default_moderation_config()
        if config:
            try:
                custom_config = json.loads(config)
                moderation_config.update(custom_config)
            except json.JSONDecodeError:
                pass  # Use default config if parsing fails
        
        # Perform moderation analysis
        result = moderation_engine.moderate_video(file_path, moderation_config)
        
        # Add file metadata
        result.update({
            "file_id": file_id,
            "original_filename": video.filename,
            "file_size": len(content),
            "content_type": video.content_type,
            "watermark": watermark
        })
        
        # Store result in database
        video_db.store_result(result)
        
        # Clean up file if rejected (optional)
        if result["decision"] == "rejected" and moderation_config.get("delete_rejected_files", False):
            try:
                os.remove(file_path)
            except:
                pass  # Ignore cleanup errors
        
        return JSONResponse(content={
            "success": True,
            "file_id": file_id,
            "decision": result["decision"],
            "confidence": result["confidence"],
            "reasoning": result["reasoning"],
            "violations": result["violations"],
            "processing_time": result["processing_time"]
        })
        
    except Exception as e:
        # Clean up file on error
        if 'file_path' in locals() and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/api/result/{file_id}")
async def get_analysis_result(file_id: str):
    """Get detailed analysis result for a specific file."""
    result = video_db.get_result_by_id(file_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    
    return JSONResponse(content=result)

@router.get("/api/results")
async def list_results(
    decision: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """List analysis results with optional filtering."""
    results = video_db.get_results(
        decision_filter=decision,
        limit=limit,
        offset=offset
    )
    
    return JSONResponse(content={
        "results": results,
        "total": len(results)
    })

@router.get("/api/statistics")
async def get_statistics():
    """Get moderation statistics and metrics."""
    stats = moderation_engine.get_moderation_statistics()
    return JSONResponse(content=stats)

@router.post("/api/settings")
async def update_settings(
    nudity_sensitivity: Optional[str] = Form("moderate"),
    copyright_threshold: Optional[int] = Form(60),
    fraud_sensitivity: Optional[str] = Form("strict"),
    reject_poor_quality: Optional[bool] = Form(False),
    blur_faces: Optional[bool] = Form(True),
    blur_violence: Optional[bool] = Form(True),
    delete_rejected_files: Optional[bool] = Form(False)
):
    """Update moderation configuration settings."""
    try:
        new_config = {
            "nudity_sensitivity": nudity_sensitivity,
            "copyright_threshold": copyright_threshold,
            "fraud_sensitivity": fraud_sensitivity,
            "reject_poor_quality": reject_poor_quality,
            "blur_faces": blur_faces,
            "blur_violence": blur_violence,
            "delete_rejected_files": delete_rejected_files
        }
        
        updated_config = moderation_engine.update_config(new_config)
        
        return JSONResponse(content={
            "success": True,
            "message": "Settings updated successfully",
            "config": updated_config
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")

@router.get("/api/config")
async def get_current_config():
    """Get current moderation configuration."""
    config = moderation_engine._get_default_moderation_config()
    return JSONResponse(content=config)

@router.delete("/api/result/{file_id}")
async def delete_result(file_id: str):
    """Delete a specific analysis result and associated file."""
    try:
        result = video_db.get_result_by_id(file_id)
        if not result:
            raise HTTPException(status_code=404, detail="Result not found")
        
        # Delete file if it exists
        if "video_path" in result:
            try:
                os.remove(result["video_path"])
            except:
                pass  # Ignore file deletion errors
        
        # Delete from database
        video_db.delete_result(file_id)
        
        return JSONResponse(content={
            "success": True,
            "message": "Result deleted successfully"
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete result: {str(e)}")

@router.post("/api/export")
async def export_results(format: str = Form("json")):
    """Export analysis results in specified format."""
    try:
        if format.lower() == "json":
            data = moderation_engine.export_decisions()
            return JSONResponse(content={
                "success": True,
                "data": data,
                "format": format
            })
        else:
            raise HTTPException(status_code=400, detail="Unsupported export format")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.post("/api/clear-history")
async def clear_history():
    """Clear all moderation history."""
    try:
        moderation_engine.clear_history()
        video_db.clear_all_results()
        
        return JSONResponse(content={
            "success": True,
            "message": "History cleared successfully"
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear history: {str(e)}")

# Health check endpoint
@router.get("/api/health")
async def health_check():
    """Health check endpoint for the moderation system."""
    return JSONResponse(content={
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "moderation_engine": "operational",
            "video_analyzer": "operational",
            "database": "operational"
        }
    })