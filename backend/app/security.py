"""鉴权工具：密码哈希（PBKDF2）+ JWT Token + FastAPI 依赖"""
import hashlib
import time
import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings
from .database import query

# ---------------- 密码 ----------------


def hash_password(password: str, salt: str | None = None) -> str:
    """PBKDF2-SHA256，存储格式: salt$hash"""
    salt = salt or uuid.uuid4().hex
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    calc = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return calc == digest


# ---------------- JWT ----------------


def create_token(user_id: int, username: str) -> str:
    payload = {
        "uid": user_id,
        "sub": username,
        "exp": int(time.time()) + settings.TOKEN_EXPIRE_HOURS * 3600,
        "iat": int(time.time()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ---------------- FastAPI 依赖 ----------------

_bearer = HTTPBearer(auto_error=False)


def _parse_user(cred: HTTPAuthorizationCredentials | None):
    if cred is None or cred.credentials is None:
        return None
    payload = decode_token(cred.credentials)
    if payload is None:
        return None
    row = query("SELECT id, username, nickname FROM users WHERE id = %s", (payload.get("uid"),), one=True)
    return row


def get_current_user(cred: HTTPAuthorizationCredentials = Depends(_bearer)) -> dict:
    """必须登录，否则 401"""
    user = _parse_user(cred)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或登录已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_optional_user(cred: HTTPAuthorizationCredentials = Depends(_bearer)) -> dict | None:
    """可选登录"""
    return _parse_user(cred)
