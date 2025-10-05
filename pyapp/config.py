import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    NODE_ENV: str = os.getenv("NODE_ENV", "development")
    PORT: int = int(os.getenv("PORT", "3001"))
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017/justdial_project1")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-in-prod-please")
    JWT_EXPIRES_IN: int = int(os.getenv("JWT_EXPIRES_IN_SECONDS", "86400"))  # 24h
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")

settings = Settings()