from pyapp.main import app

# This file provides the app object for Render deployment
# The Procfile will use uvicorn to run the FastAPI app

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
