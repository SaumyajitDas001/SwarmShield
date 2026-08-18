import hmac
from datetime import datetime, timedelta, timezone
from typing import Annotated
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from .config import settings

security = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


def create_token(email: str, role: str = "ADMIN") -> TokenResponse:
    payload = {"sub": email, "role": role, "exp": datetime.now(timezone.utc) + timedelta(hours=8)}
    return TokenResponse(access_token=jwt.encode(payload, settings.jwt_secret, algorithm="HS256"))


def authenticate(data: LoginRequest) -> TokenResponse:
    valid_email = hmac.compare_digest(data.email, settings.admin_email)
    valid_password = hmac.compare_digest(data.password, settings.admin_password)
    if not (valid_email and valid_password): raise HTTPException(401, "Invalid credentials")
    return create_token(data.email)


def current_user(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)]) -> dict:
    if credentials is None: raise HTTPException(401, "Authentication required")
    try: return jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError: raise HTTPException(401, "Invalid or expired token")


def require_roles(*roles: str):
    def checker(user: Annotated[dict, Depends(current_user)]) -> dict:
        if user.get("role") not in roles: raise HTTPException(403, "Insufficient permissions")
        return user
    return checker
