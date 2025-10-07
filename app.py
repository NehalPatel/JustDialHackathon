import os
from pyapp.main import app

# This file is needed for Render to find the FastAPI app
# when using gunicorn as the WSGI server

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
