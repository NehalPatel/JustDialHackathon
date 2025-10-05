from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import bcrypt
import jwt

from .config import settings
from .db import users

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
security = HTTPBearer()

def create_token(payload: dict) -> str:
    exp = datetime.utcnow() + timedelta(seconds=settings.JWT_EXPIRES_IN)
    to_encode = {**payload, "exp": exp}
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm="HS256")

def get_current_user(token: HTTPAuthorizationCredentials = Depends(security)):
    try:
        data = jwt.decode(token.credentials, settings.JWT_SECRET, algorithms=["HS256"])
        user = users.find_one({"_id": data.get("sub")})
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"id": user["_id"], "email": user["email"], "firstName": user.get("firstName"), "lastName": user.get("lastName")}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/register")
def register(email: str, password: str, firstName: str, lastName: str):
    if users.find_one({"email": email}):
        raise HTTPException(status_code=409, detail="Email already registered")
    salt = bcrypt.gensalt()
    pw_hash = bcrypt.hashpw(password.encode(), salt)
    doc = {"email": email, "password": pw_hash, "firstName": firstName, "lastName": lastName, "createdAt": datetime.utcnow()}
    inserted = users.insert_one(doc)
    return {"id": inserted.inserted_id, "email": email}

@router.post("/login")
def login(email: str, password: str):
    user = users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not bcrypt.checkpw(password.encode(), user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token({"sub": user["_id"], "email": email})
    return {"token": token}