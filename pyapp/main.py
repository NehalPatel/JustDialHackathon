from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from .config import settings
from .moderation import router as moderation_router

app = FastAPI(title="Video Auto-Moderation System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for the web interface
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    """Redirect root URL to the main moderation dashboard."""
    return RedirectResponse(url="/moderation/", status_code=302)

@app.get("/health")
def health():
    return {
        "status": "OK",
        "message": "Video Auto-Moderation System is running",
        "environment": settings.NODE_ENV,
    }

app.include_router(moderation_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("pyapp.main:app", host="0.0.0.0", port=settings.PORT, reload=True)