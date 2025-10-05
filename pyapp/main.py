from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .auth import router as auth_router
from .moderation import router as moderation_router

app = FastAPI(title="JustDial Project 1 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {
        "status": "OK",
        "message": "JustDial Project 1 FastAPI is running",
        "environment": settings.NODE_ENV,
    }

app.include_router(auth_router)
app.include_router(moderation_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("pyapp.main:app", host="0.0.0.0", port=settings.PORT, reload=True)